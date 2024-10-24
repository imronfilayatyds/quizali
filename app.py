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

# Route homepage
@app.route("/")
def home():
    return render_template("index.html", title="Home")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html", title="Quiz")

@app.route("/rank")
def display_rank():
    return render_template("rank.html", title="Rank")

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

@app.route("/login")
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found', 'error')
        elif not check_password_hash(user.password, password):
            flash('Incorrect password, coba lagi', 'error')
        else:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('home'))

    else:
        return render_template("login.html", title="Login")

@app.route("/logout")
def logout():
    return render_template("index.html")