import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from models import global_init, create_session
from models.booking import Booking
from models.user import User

# Инициализация Flask приложения
app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = 'b01282ee6aa4e4dd09e3cf2da14c0c1a'

# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Инициализация сериализатора для подтверждения email
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# URL для подключения к PostgreSQL
db_url = 'postgresql://postgres:admin@localhost/detail'
global_init(db_url)

# Инициализация Flask-Migrate
migrate = Migrate(app, db_url)

from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Указывает маршрут для входа


@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Пожалуйста, войдите, чтобы получить доступ к этой странице.', 'warning')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.get(User, int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


def send_confirmation_email(email, confirm_url):
    sender_email = "deteyling.tsentr@mail.ru"
    sender_password = "kbDzVu3qdkQ8sya5Rqrb"
    subject = "Подтвердите ваш адрес электронной почты"
    body = f'Ваша ссылка для подтверждения: {confirm_url}'

    # Создание сообщения
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Установка соединения с сервером
        with smtplib.SMTP_SSL('smtp.mail.ru', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("Email успешно отправлен!")
    except Exception as e:
        print(f"Ошибка отправки email: {e}")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        session = create_session()
        existing_user = session.query(User).filter_by(email=email).first()
        existing_username = session.query(User).filter_by(username=username).first()

        if existing_user:
            flash('Пользователь с таким email уже существует.', 'danger')
            return redirect(url_for('register'))

        if existing_username:
            flash('Пользователь с таким именем уже существует.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password)
        session.add(new_user)
        try:
            session.commit()
            # Отправка подтверждающего письма
            token = serializer.dumps(email, salt='email-confirmation-salt')
            confirm_url = url_for('confirm_email', token=token, _external=True)
            send_confirmation_email(email, confirm_url)

            flash('Письмо с подтверждением отправлено.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            session.rollback()
            flash('Ошибка при регистрации. Пожалуйста, попробуйте снова.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        date = request.form['date']
        time = request.form['time']
        service = request.form['service']

        session = create_session()
        new_booking = Booking(name=name, email=email, date=date, time=time, service=service)
        session.add(new_booking)
        session.commit()

        return redirect(url_for('confirmation'))
    return render_template('booking.html')


@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')


@app.route('/confirm/<token>')
def confirm_email(token):
    session = create_session()
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.email_confirmed = True
            user.confirmed_on = datetime.utcnow()
            session.commit()
            flash('Ваш email подтвержден!', 'success')
        else:
            flash('Пользователь не найден.', 'danger')
        return redirect(url_for('login'))
    except (SignatureExpired, BadSignature):
        flash('Ссылка для подтверждения недействительна или устарела.', 'danger')
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']
        password = request.form['password']
        session = create_session()
        user = session.query(User).filter(
            (User.username == login_id) | (User.email == login_id)
        ).first()

        if user and check_password_hash(user.password, password):
            if user.email_confirmed:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Пожалуйста, подтвердите ваш email.', 'warning')
        else:
            flash('Неверный логин/email или пароль.', 'danger')

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
