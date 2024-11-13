import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkeyyangsangatsulit'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizali.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', backref=db.backref('quiz_results', lazy=True))

# Route homepage
@app.route("/")
def home():
    # if 'user_id' not in session:
    #     flash('You need to log in first.', 'error')
    #     return redirect(url_for('login'))
    return render_template("index.html", title="Home")

@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        flash('You need to log in first.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Calculate score based on user responses
        user_answers = request.form.to_dict()
        score = 0

        # Load questions
        with open('questions.json') as f:
            questions = json.load(f)

        # Check each question's answer
        for question_index, user_answer in user_answers.items():
            if questions[int(question_index)]['choices'].index(user_answer) == questions[int(question_index)]['answer']:
                score += 1

        # Store the result in the database
        result = QuizResult(user_id=session['user_id'], score=score)
        db.session.add(result)
        db.session.commit()

        flash(f'Your score is {score}!', 'success')
        return redirect(url_for('display_rank'))

    # Load questions and add indexed choices
    with open('questions.json') as f:
        questions = json.load(f)
        for i, question in enumerate(questions):
            question['index'] = i  # Add an index key
            question['choices_with_index'] = list(enumerate(question['choices']))

    return render_template("quiz.html", questions=questions, title="Quiz")

@app.route("/rank")
def display_rank():
    if 'user_id' not in session:
        flash('You need to log in first.', 'error')
        return redirect(url_for('login'))

    leaderboard = db.session.query(User.username, QuizResult.score).join(QuizResult).order_by(QuizResult.score.desc()).all()
    return render_template("rank.html", leaderboard=leaderboard, title="Rank")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Cek apakah kedua password sama
        if password != confirm_password:
            flash('Passwords don\'t match, coba lagi!', 'error')
            return redirect(url_for('register'))
        
        # Cek apakah username atau email sudah ada
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        
        # Mengamankan password
        hashed_password = generate_password_hash(password)

        # Membuat user baru
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Your account is created successfully. Coba login :D', 'success')
        
        return redirect(url_for('login'))
    
    return render_template("register.html", title="Register")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash('You are already logged in.', 'info')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found. Daftar dulu', 'error')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Incorrect password, coba lagi', 'error')
            return redirect(url_for('login'))
        else:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('home'))

    else:
        return render_template("login.html", title="Login")

@app.route("/logout")
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))
