import os
import json
import requests
import random
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
METEOBLUE_API_KEY = os.getenv('METEOBLUE_API_KEY')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizali.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    nickname = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', backref=db.backref('quiz_results', lazy=True))


def get_weather_data(latitude, longitude):
    met_url = f"https://my.meteoblue.com/packages/basic-day?apikey={METEOBLUE_API_KEY}&lat={latitude}&lon={longitude}&asl=433&format=json&forecast_days=3"
    met_response = requests.get(met_url)
    data_cuaca = met_response.json()

    # Parsing data
    dates = data_cuaca["data_day"]["time"]
    max_temps = data_cuaca["data_day"]["temperature_max"]
    min_temps = data_cuaca["data_day"]["temperature_min"]

    # Menentukan nama hari
    def get_day_name(date_str):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A')

    # Mengisi forecast 3 hari
    weather_data = []
    for i in range(3):
        weather_data.append({
            'date': dates[i],
            'day': get_day_name(dates[i]),
            'temp_day': max_temps[i],
            'temp_night': min_temps[i]
        })
    return weather_data

# Route homepage
@app.route("/", methods=['GET', 'POST'])
def home():
    list_cuaca = []
    error = None
    city = None

    if request.method == 'POST':
        city = request.form.get('city')
        if not city:
            error = 'Tolong masukkan nama kota.'
        else:
            # Nama kota --> latitude and longitude
            url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHERMAP_API_KEY}"
            geocode_response = requests.get(url)
            geocode_data = geocode_response.json()
            
            if geocode_data:
                latitude = geocode_data[0]['lat']
                longitude = geocode_data[0]['lon']
                list_cuaca = get_weather_data(latitude, longitude)
            else:
                error = 'Kota tidak ditemukan, coba lagi.'
    else:
        # Kota default
        city = 'Jakarta'
        jakarta_lat, jakarta_lon = -6.2088, 106.8456
        list_cuaca = get_weather_data(jakarta_lat, jakarta_lon)

    return render_template("index.html", title="Home", city=city, list_cuaca=list_cuaca, error=error)

@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        flash('Anda perlu login dulu', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    total_score = 0

    if request.method == 'POST':
        # Hitung skor
        user_answers = request.form.to_dict()
        score = 0

        # Load total_score dari db
        last_result = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).first()
        if last_result:
            total_score = last_result.total_score

        # Load questions dengan urutan acak
        randomized_questions = session.get('randomized_questions')

        if not randomized_questions:
            flash('Tidak ada soal untuk dinilai. Mohon reload quiz.', 'error')
            return redirect(url_for('quiz'))

        # Check jawaban user based randomized order
        for question_index, user_answer in user_answers.items():
            question = randomized_questions[int(question_index)]
            correct_answer_index = question['answer']

            if int(user_answer) == correct_answer_index:
                score += 1

        # Update total_score
        total_score += score

        # Store result ke database
        result = QuizResult(user_id=user_id, score=score, total_score=total_score)
        db.session.add(result)
        db.session.commit()

        flash(f'Skor Anda adalah {score}!', 'success')

        session.pop('randomized_questions', None)
        return redirect(url_for('quiz'))

    else:
        # Bersihkan questions sebelumnya di GET request yang baru
        if 'randomized_questions' in session:
            session.pop('randomized_questions', None)

        last_result = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).first()
        if last_result:
            total_score = last_result.total_score
    
        questions_path = os.path.join(os.path.dirname(__file__), 'questions.json')
        try:
            with open(questions_path) as file:
                questions = json.load(file)
                randomized_questions = random.sample(questions, len(questions))
                for i, question in enumerate(randomized_questions):
                    question['index'] = i  
                    question['choices_with_index'] = list(enumerate(question['choices']))
        
                # Store randomized questions ke session
                session['randomized_questions'] = randomized_questions
        except FileNotFoundError:
            flash('Soal tidak ditemukan!', 'error')
            return redirect(url_for('home'))

    return render_template("quiz.html", questions=randomized_questions, total_score=total_score, title="Quiz")

@app.route("/leaderboard")
def leaderboard():
    if 'user_id' not in session:
        flash('You need to log in first.', 'error')
        return redirect(url_for('login'))

    leaderboard = db.session.query(User.username, QuizResult.score).join(QuizResult).order_by(QuizResult.score.desc()).all()
    return render_template("rank.html", leaderboard=leaderboard, title="Leaderboard")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        nickname = request.form['nickname']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Cek apakah kedua password sama
        if password != confirm_password:
            flash('Password tidak sama, coba lagi!', 'error')
            return redirect(url_for('register'))
        
        # Cek apakah username atau email sudah ada
        user = User.query.filter((User.username == username) | (User.nickname == nickname)).first()
        if user:
            flash('Username atau nama panggilan sudah tidak tersedia. Coba yang lain.', 'error')
            return redirect(url_for('register'))
        
        # Mengamankan password
        hashed_password = generate_password_hash(password)

        # Membuat user baru
        new_user = User(username=username, nickname=nickname, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Account Anda berhasil dibuat. Silakan login.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template("register.html", title="Register")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash('Anda sudah login.', 'info')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Username tidak ditemukan. Daftar dulu', 'error')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password salah, coba lagi.', 'error')
            return redirect(url_for('login'))
        else:
            session['user_id'] = user.id
            flash('Berhasil login.', 'success')
            return redirect(url_for('home'))

    else:
        return render_template("login.html", title="Login")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash('Anda sudah logout.', 'success')
    return redirect(url_for('login'))