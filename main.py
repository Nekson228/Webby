from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, login_required
from data.forms import *

from data import db_session
from data.__all_models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = User()
        user.name = form.name_field.data
        user.surname = form.surname_field.data
        user.birthday = form.birthday_field.data
        user.email = form.email_field.data
        user.phone_number = form.phone_number_field.data
        user.set_password(form.password_field.data)
        session.add(user)
        session.commit()
        return redirect('/')
    return render_template('registration.html', form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email_field.data).first()
        if user and user.check_password(form.password_field.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/send', methods=['POST', 'GET'])
def send():
    form = MessageForm()
    if form.validate_on_submit():
        pass
    return render_template('send.html', form=form)


if __name__ == '__main__':
    db_session.global_init('db/chats_db.sqlite')
    app.run('127.0.0.1', 8080, debug=True)
