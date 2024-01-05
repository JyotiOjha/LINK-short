from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from urllib.parse import quote

password = 'J20yoti@02'
url_encoded_password = quote(password)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:'+ url_encoded_password +'@localhost/url'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    links = db.relationship('ShortLink', backref='user', lazy=True)

class ShortLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(8), unique=True, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/')
def index():
    return render_template('login .html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login .html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
         new_username = request.form['new_username']
         new_password = request.form['new_password']

      
         existing_user = User.query.filter_by(username=new_username).first()
         if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
         else:
           
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            new_user = User(username=new_username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        links = user.links
        return render_template('dashboard.html', user=user, links=links)
    else:
        return redirect(url_for('login'))

@app.route('/generate-link', methods=['POST'])
def generate_link():
    user_id = session.get('user_id')
    if user_id:
        original_url = request.form['original_url']
        expiration_date = datetime.utcnow() + timedelta(hours=48)

        short_code = generate_short_code()
        while ShortLink.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code()

        new_link = ShortLink(original_url=original_url, short_code=short_code, expiration_date=expiration_date, user_id=user_id)
        db.session.add(new_link)
        db.session.commit()

        flash('Short link created successfully!', 'success')
    else:
        flash('Please log in to create short links.', 'danger')

    return redirect(url_for('dashboard'))

def generate_short_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

@app.route('/short-link/<code>')
def short_link(code):
    short_link = ShortLink.query.filter_by(short_code=code).first()
    if short_link:
        return redirect(short_link.original_url)
    else:
        flash('Short link not found.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/short-link-details/<code>')
def short_link_details(code):
    short_link = ShortLink.query.filter_by(short_code=code).first()
    if short_link:
        return render_template('short_link.html', short_link=short_link)
    else:
        flash('Short link not found.', 'danger')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
