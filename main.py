from flask import Flask, render_template, redirect, url_for, abort, request, make_response
import datetime

from flask import Flask, render_template, redirect, url_for, abort, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from data.forms import *
from data.db_session import create_session, global_init
from data.__all_models import *
from data.constants import *

from api import api_blueprint

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect('/info')
    session = create_session()
    advertisements = session.query(Advertisement).all()[::-1][:6]
    return render_template('actual_ads.html', ads=advertisements)


@app.route('/info')
def info():
    return render_template('roadmap.html')


@app.route('/api')
def api():
    return render_template('api_info.html')


@app.route('/api/docs')
def api_docs():
    return render_template('api_docs.html')


@app.route('/top')
def top():
    session = create_session()
    users = session.query(User).order_by(User.rating.desc()).filter(User.rating > 0).limit(100)
    return render_template('top.html', top_users=users)


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
        user.rank = session.query(Rank).filter(Rank.id == 1).first()
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


@app.route('/login/reset_password', methods=["POST", "GET"])
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


@app.route('/chats/<int:user_id>', methods=['POST', 'GET'])
@login_required
def chat(user_id):
    form = MessageForm()
    session = create_session()
    companion = session.query(User).filter(User.id == user_id).first()
    if not companion:
        return abort(404)
    messages = session.query(Message).filter(((Message.to_id == current_user.id) & (Message.from_id == user_id)) |
                                             ((Message.from_id == current_user.id) & (Message.to_id == user_id))).all()
    sender = session.query(User).filter(User.id == current_user.id).first()
    if form.validate_on_submit():
        msg, cnt = Message(), Content()
        cnt.content = form.message_field.data
        session.add(cnt)
        session.commit()
        to_rate = len(cnt.content)
        for i in reversed(RATE.keys()):
            if i != 1:
                while to_rate >= i:
                    sender.rating += RATE[i]
                    to_rate -= i
        sender.rating += (to_rate % 10) / 10
        sender.rating = round(sender.rating, 1)
        session.commit()
        for i in reversed(RANKS.keys()):
            if sender.rating >= i:
                rank = session.query(Rank).filter(Rank.title == RANKS[i]).first()
                sender.rank_id = rank.id
                session.commit()
                break
        msg.to_id = user_id
        msg.from_id = current_user.id
        msg.content_id = cnt.id
        session.add(msg)
        session.commit()
        return redirect(f"/chats/{user_id}")
    return render_template('chats.html', form=form, messages=messages, companion=companion)


@app.route('/chats', methods=['GET', 'POST'])
@login_required
def chats():
    from itertools import groupby

    session = create_session()
    messages = session.query(Message).filter((Message.to_id == current_user.id) |
                                             (Message.from_id == current_user.id)).all()
    companions = sorted([msg.sender if msg.sender != current_user else msg.receiver for msg in messages],
                        key=lambda x: x.name)
    companions = list(reversed([user[0] for user in groupby(companions)]))
    last_messages = []
    for user in companions:
        last_messages.append(session.query(Message).filter(((Message.to_id == current_user.id) &
                                                            (Message.from_id == user.id)) |
                                                           ((Message.from_id == current_user.id) &
                                                            (Message.to_id == user.id))).all()[-1])
    chats_list = sorted([[companions[i], last_messages[i]] for i in range(len(companions))],
                        key=lambda x: x[1].created_at)[::-1]
    return render_template('chats_list.html', chats_list=chats_list)


@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    session = create_session()
    form = SearchForm()
    if form.validate_on_submit():
        users = session.query(User).filter((User.name.like(f"{form.filter_field.data}%")) |
                                           (User.surname.like(f"{form.filter_field.data}%")) |
                                           (User.phone_number.like(f"{form.filter_field.data}%"))).all()
        if not users:
            return render_template('search.html', form=form, message='Предложений по поиску нет')
        return render_template('search.html', form=form, users=users)
    return render_template('search.html', form=form)


@app.route('/profile/<int:user_id>')
@login_required
def show_profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    all_users = session.query(User).order_by(User.rating.desc())
    position = 1
    for i in all_users:
        if i.id == user.id:
            break
        position += 1
    pic = session.query(Avatar).filter(Avatar.refers_to == user_id).first()
    if pic:
        profile_pic = url_for('static', filename=f"avatars/{pic.link}")
    else:
        profile_pic = url_for('static', filename='avatars/anon.png')
    return render_template('profile.html', user=user, pic=profile_pic, today=datetime.datetime.now(), position=position)


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
    return render_template('avatar.html', form=form)


@app.route('/profile/<int:user_id>/settings', methods=["GET", "POST"])
@login_required
def set_profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    form = SetupProfileForm()
    form.interests_field.choices = [(i.title, i.title) for i in session.query(Interest).all()]
    if request.method == 'GET':
        form.interests_field.data = [tag.title for tag in user.interests]
        form.name_field.data = user.name
        form.surname_field.data = user.surname
        form.birthday_field.data = user.birthday
        form.phone_number_field.data = user.phone_number
    if form.validate_on_submit():
        user.name = form.name_field.data
        user.surname = form.surname_field.data
        user.birthday = form.birthday_field.data
        user.phone_number = form.phone_number_field.data
        user.interests.clear()
        for tag in form.interests_field.raw_data:
            tag_obj = session.query(Interest).filter(Interest.title == tag).first()
            user.interests.append(tag_obj)
        session.commit()
        return redirect(f'/profile/{user_id}')
    return render_template('profile_settings.html', form=form)


@login_required
@app.route('/advertisements/create', methods=['GET', 'POST'])
def create_advertisement():
    form = AdvertisementForm()
    session = create_session()
    tags = session.query(Interest).all()
    choices = [(i.title, i.title) for i in tags]
    form.tags_field.choices = choices
    if form.validate_on_submit():
        cnt = Content()
        cnt.content = form.content_field.data
        session.add(cnt)
        session.commit()
        ad = Advertisement()
        ad.title = form.title_field.data
        ad.author_id = current_user.id
        ad.price = form.price_field.data
        ad.content_id = cnt.id
        for tag in form.tags_field.data:
            tag_obj = session.query(Interest).filter(Interest.title == tag).first()
            ad.interests.append(tag_obj)
        session.add(ad)
        session.commit()
        return redirect('/')
    return render_template('ad_form.html', form=form)


@login_required
@app.route('/advertisements/<int:ad_id>/edit', methods=['GET', 'POST'])
def edit_advertisement(ad_id):
    session = create_session()
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not advertisement:
        return abort(404)
    if current_user != advertisement.author:
        return abort(403)
    form = AdvertisementForm()
    form.tags_field.choices = [(i.title, i.title) for i in session.query(Interest).all()]
    if request.method == 'GET':
        form.title_field.data = advertisement.title
        form.price_field.data = advertisement.price
        form.content_field.data = advertisement.content.content
        form.tags_field.data = [tag.title for tag in advertisement.interests]
    if form.validate_on_submit():
        cnt = advertisement.content
        cnt.content = form.content_field.data
        session.commit()
        advertisement.title = form.title_field.data
        advertisement.author_id = current_user.id
        advertisement.price = form.price_field.data
        advertisement.content_id = cnt.id
        advertisement.interests.clear()
        for tag in form.tags_field.raw_data:
            advertisement.interests.append(session.query(Interest).filter(Interest.title == tag).first())
        session.commit()
        return redirect('/')
    return render_template('ad_form.html', form=form)


@login_required
@app.route('/advertisements/<int:ad_id>/delete')
def delete_advertisement(ad_id):
    session = create_session()
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not advertisement:
        return abort(404)
    if current_user != advertisement.author:
        return abort(403)
    session.delete(advertisement)
    session.commit()
    return redirect('/')


@app.errorhandler(401)
def handle_401(error):
    return redirect('/login')


@app.errorhandler(403)
def handle_403(error):
    return render_template('errorhandler.html', error='Ошибка 403.', http_error=error,
                           message='Похоже вы попытались получить доступ к чему-то что вам не принадлежит.')


@app.errorhandler(404)
def handle_404(error):
    response = make_response(render_template('errorhandler.html', error='Ошибка 404.', http_error=error,
                                             message='Похоже вы попытались получить доступ к чему-то не существующему. '
                                                     'Возможно, вы не вошли в свой аккаунт.'),
                             {'error': f'{error.code} {error.name}: {error.description}'})
    response.status = 'Not Found'
    response.status_code = 404
    return response


@app.errorhandler(405)
def handle_405(error):
    return make_response({'error': error}, 405)


if __name__ == '__main__':
    global_init('db/chats_db.sqlite')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.run('127.0.0.1', 8080, debug=True)
