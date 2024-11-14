from flask import Flask, request, render_template, redirect, url_for, session, flash
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Dibutuhkan untuk manajemen session

# Memuat dataset
df = pd.read_csv('d:/Kuliah/SEM 5/Data Mining/Tugasakhir2/Updated_MovieGenre_with_Poster.csv', encoding='ISO-8859-1', on_bad_lines='skip')

# Preprocessing: ekstrak tahun dari judul dan proses genre
df['year'] = df['Title'].str.extract(r'\((\d{4})\)').astype(float)
df['parsed_genres'] = df['Genre'].str.split('|')

# Data pengguna dummy untuk simulasi
users = {'user1': 'password1', 'user2': 'password2'}

# Fungsi bantuan untuk mendapatkan rekomendasi
def get_recommendations(selected_genre=None, selected_year=None, selected_title=None):
    filtered_df = df.copy()  # Bekerja dengan salinan data untuk menghindari perubahan asli

    # Terapkan filter jika input tersedia
    if selected_genre:
        filtered_df = filtered_df[filtered_df['parsed_genres'].apply(
            lambda genres: isinstance(genres, list) and selected_genre.lower() in [g.lower() for g in genres]
        )]

    if selected_year:
        try:
            year = float(selected_year)
            filtered_df = filtered_df[filtered_df['year'] == year]
        except ValueError:
            flash("Invalid year input.", "warning")

    if selected_title:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(selected_title, case=False, na=False)]

    # Kembalikan 10 teratas berdasarkan skor IMDB
    return filtered_df[['Title', 'IMDB Score', 'year', 'Poster']].sort_values(
        by='IMDB Score', ascending=False
    ).head(10)

# Middleware untuk memastikan pengguna login
def login_required(route_func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return route_func(*args, **kwargs)
    wrapper.__name__ = route_func.__name__  # Mencegah masalah pada Flask routing
    return wrapper

# Route untuk halaman utama
@app.route('/')
@login_required
def home():
    return render_template('home.html')

# Route untuk login pengguna
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['username'] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for('home'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users:
            flash("Username already exists. Please choose another one.", "danger")
        else:
            users[username] = password  # Tambah pengguna baru ke dictionary
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))

    return render_template('register.html')

# Route untuk menerima input dan menampilkan rekomendasi
@app.route('/recommend', methods=['POST'])
@login_required
def recommend():
    selected_genre = request.form.get('movie_genre', '').strip()
    selected_year = request.form.get('movie_year', '').strip()
    selected_title = request.form.get('movie_title', '').strip()

    # Mendapatkan rekomendasi berdasarkan input pengguna
    recommendations = get_recommendations(selected_genre, selected_year, selected_title)

    if recommendations.empty:
        flash("No recommendations found. Please try different criteria.", "warning")

    return render_template('index.html', recommendations=recommendations.to_dict(orient='records'))

# Route untuk logout pengguna
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)