from flask import Flask, render_template
from flask_login import LoginManager, login_user, logout_user, login_required
from forms.message_form import MessageForm
from forms.registration_form import RegistrationForm

from data import db_session
from data.__all_models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        pass
    return render_template('registration.html', form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    pass


@app.route('/send', methods=['POST', 'GET'])
def send():
    form = MessageForm()
    if form.validate_on_submit():
        pass
    return render_template('send.html', form=form)


if __name__ == '__main__':
    db_session.global_init('db/chats_db.sqlite')
    app.run('127.0.0.1', 8080, debug=True)
