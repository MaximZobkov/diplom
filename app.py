from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/detail'
app.config['SECRET_KEY'] = 'b01282ee6aa4e4dd09e3cf2da14c0c1a'
app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] =  465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'deteyling.tsentr@mail.ru'
app.config['MAIL_PASSWORD'] = 'QZpG00wXVNBhsuUcXGPs'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    from models import Booking
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        date = request.form['date']
        time = request.form['time']
        service = request.form['service']

        new_booking = Booking(name=name, email=email, date=date, time=time, service=service)
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('confirmation'))
    return render_template('booking.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    from models import User
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Отправка подтверждающего письма
        token = serializer.dumps(email, salt='email-confirmation-salt')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirm Your Email Address', recipients=[email])
        msg.body = f'Your confirmation link is {confirm_url}'
        mail.send(msg)

        flash('A confirmation email has been sent.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    from models import User
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
        user = User.query.filter_by(email=email).first_or_404()
        user.email_confirmed = True
        user.confirmed_on = datetime.utcnow()
        db.session.commit()
        flash('Your email has been confirmed!', 'success')
        return redirect(url_for('login'))
    except (SignatureExpired, BadSignature):
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password) and user.email_confirmed:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email, password, and email confirmation.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
