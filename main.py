from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from data.forms import *
from data.db_session import create_session, global_init
from data.__all_models import *

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        form = SearchForm()
        if form.validate_on_submit():
            session = create_session()
            user = session.query(User).filter(User.phone_number == form.number_field.data).first()
            if not user:
                return render_template('index.html', form=form, message='Пользователь не найден')
            return render_template('index.html', form=form, user=user)
        return render_template('index.html', form=form)
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        session = create_session()
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
        session = create_session()
        user = session.query(User).filter(User.email == form.email_field.data).first()
        if user and user.check_password(form.password_field.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', form=form)


@app.route('/reset_password', methods=["POST", "GET"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        session = create_session()
        user = session.query(User).filter(User.email == form.email_field.data).first()
        if user:
            if not user.check_password(form.password_field.data):
                user.set_password(form.password_field.data)
                session.commit()
                return redirect('/login')
            return render_template('reset_password.html', form=form, message="Пароль идентичен предыдущему")
        return render_template('reset_password.html', form=form, message="Пользователь не найден")
    return render_template('reset_password.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/conversation/<int:user_id>', methods=['POST', 'GET'])
@login_required
def conversation(user_id):
    form = MessageForm()
    session = create_session()
    messages = session.query(Message).filter(((Message.to_id == current_user.id) & (Message.from_id == user_id)) |
                                             ((Message.from_id == current_user.id) & (Message.to_id == user_id)))
    companion = session.query(User).filter(User.id == user_id).first()
    sender = session.query(User).filter(User.id == user_id).first()
    if form.validate_on_submit():
        msg, cnt = Message(), Content()
        cnt.content = form.message_field.data
        session.add(cnt)
        session.commit()
        msg.to_id = user_id
        msg.from_id = current_user.id
        msg.content_id = cnt.id
        if len(cnt.content) < 50:
            sender.rating += 1
        elif 50 <= len(cnt.content) < 100:
            sender.rating += 2
        elif 100 <= len(cnt.content) < 250:
            sender.rating += 3
        elif 250 <= len(cnt.content) < 500:
            sender.rating += 5
        elif 500 <= len(cnt.content):
            sender.rating += 10
        session.add(msg)
        session.commit()
        return redirect(f"/conversation/{user_id}")
    return render_template('chat.html', form=form, messages=messages, companion=companion)


@app.route('/profile/<int:user_id>')
@login_required
def show_profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    pic = session.query(Avatar).filter(Avatar.refers_to == user_id).first()
    if pic:
        profile_pic = url_for('static', filename=f"avatars/{pic.link}")
    else:
        profile_pic = url_for('static', filename='avatars/anon.png')
    return render_template('profile.html', user=user, pic=profile_pic)


@app.route('/profile/<int:user_id>/avatar', methods=['GET', 'POST'])
@login_required
def change_avatar(user_id):
    form = AvatarForm()
    session = create_session()
    if form.validate_on_submit():
        photo = form.link_field.data
        file = secure_filename(photo.filename)
        avatars = session.query(Avatar).filter(Avatar.refers_to == user_id).first()
        if avatars:
            os.remove(os.path.join(app.root_path, 'static', 'avatars', avatars.link))
            avatars.link = file
            photo.save(os.path.join(app.root_path, 'static', 'avatars', file))
            session.commit()
        else:
            avatar = Avatar()
            avatar.refers_to = user_id
            avatar.link = file
            photo.save(os.path.join(app.root_path, 'static', 'avatars', file))
            session.add(avatar)
            session.commit()
        return redirect(f'/profile/{user_id}')
    return render_template('avatar.html', form=form,)


@app.route('/profile/<int:user_id>/settings', methods=["GET", "POST"])
@login_required
def set_profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    form = SetupProfileForm()
    if request.method == "GET":
        form.name_field.data = user.name
        form.surname_field.data = user.surname
        form.birthday_field.data = user.birthday
        form.phone_number_field.data = user.phone_number
    if form.validate_on_submit():
        user.name = form.name_field.data
        user.surname = form.surname_field.data
        user.birthday = form.birthday_field.data
        user.phone_number = form.phone_number_field.data
        session.commit()
        return redirect(f'/profile/{user_id}')
    return render_template('settings.html', form=form)


@app.route('/conversations')
@login_required
def conversations():
    from itertools import groupby

    session = create_session()
    messages = session.query(Message).filter((Message.to_id == current_user.id) |
                                             (Message.from_id == current_user.id)).all()
    companions = [msg.sender for msg in messages if msg.sender != current_user]
    companions = list(reversed([user[0] for user in groupby(companions)]))
    last_messages = []
    for user in companions:
        last_messages.append(session.query(Message).filter(((Message.to_id == current_user.id) &
                                                            (Message.from_id == user.id)) |
                                                           ((Message.from_id == current_user.id) &
                                                            (Message.to_id == user.id))).all()[-1])
    return render_template('conversations.html', companions=companions, last_messages=last_messages)


if __name__ == '__main__':
    global_init('db/chats_db.sqlite')
    app.run('127.0.0.1', 8080, debug=True)
