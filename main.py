import datetime
import os
import psycopg2

from flask import Flask, render_template, redirect, url_for, abort, request, make_response, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from api import api_blueprint
from data.__all_models import *
from data.constants import *
from data.db_session import create_session, global_init
from data.forms import LoginForm, RegistrationForm, AdvertisementForm, MessageForm, AvatarForm, ResetPasswordForm, \
    SetupProfileForm, SearchForm

"""Webby v1.0"""

# создаем приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# создаем менеджер авторизации
login_manager = LoginManager()
login_manager.init_app(app)

DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL, sslmode='require')


@app.route('/favicon.ico')
def favicon():
    """Обработчик иконки страницы"""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    """Обработчик главной страницы."""
    if not current_user.is_authenticated:  # проверяем аутентифицирован ли пользователь
        return render_template('roadmap.html')  # если нет - показываем ему планы разработчиков
    # в ином случае - показываем клиенту актуальные объявления
    session = create_session()
    advertisements = session.query(Advertisement).all()[::-1][:6]  # получаем список последних 5 объявлений
    return render_template('actual_ads.html', ads=advertisements)


@app.route('/info')
def info():
    """Обработчик страницы с информацией о проекте."""
    return render_template('about.html')


@app.route('/api')
def api():
    """Обработчик страницы с информацией об API."""
    return render_template('api_info.html')


@app.route('/api/docs')
def api_docs():
    """Обработчик страницы с документацией API."""
    return render_template('api_docs.html')


@app.route('/top')
def top():
    """Обработчик странциы доски почёта."""
    session = create_session()
    users = session.query(User).order_by(User.rating.desc()).filter(User.rating > 0).limit(
        100)  # получаем список 100 пользователей, упорядоченных по рейтингу
    return render_template('top.html', top_users=users)


@login_manager.user_loader
def load_user(user_id):
    """Функция для загрузки объекта User в current_user для последующего испольования.
    :param user_id: id клиента"""
    session = create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=["POST", "GET"])
def register():
    """Обработчик страницы регистрации."""
    form = RegistrationForm()  # создаем форму регистрации
    if form.validate_on_submit():
        session = create_session()

        # создаем объект User и загружаем в него данные из формы для регистрации
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
    """Обработчик страницы авторизации."""
    form = LoginForm()  # создаем форму авторизации
    if form.validate_on_submit():
        session = create_session()
        user = session.query(User).filter(
            User.email == form.email_field.data).first()  # ищем пользователя с введенным email
        if user and user.check_password(
                form.password_field.data):  # проверяем, найден ли такой пользователь и верен ли введенный пароль
            # если все данные введены правильно - авторизируем пользователя
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        # в противном случае выводим сообщение об ошибке
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', form=form)


@app.route('/login/reset_password', methods=["POST", "GET"])
def reset_password():
    """Обработчик страницы смены пароля."""
    form = ResetPasswordForm()  # создаем форму смены пароля
    if form.validate_on_submit():
        session = create_session()
        user = session.query(User).filter(
            User.email == form.email_field.data).first()  # ищем пользователя с введенным email
        if user:  # проверяем, найден ли такой пользователь
            if not user.check_password(
                    form.password_field.data):  # проверяем, соответствует ли введенный пароль предыдущему
                user.set_password(form.password_field.data)  # если введенные данные прошли все проверки - меняем пароль
                session.commit()
                return redirect('/login')
            # если пароль идентичен предыдущему - возвращаем сообщение об ошибке
            return render_template('reset_password.html', form=form, message="Пароль идентичен предыдущему")
        # если пользователь не найден - возвращаем ошибку
        return render_template('reset_password.html', form=form, message="Пользователь не найден")
    return render_template('reset_password.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Обработчик выхода из профиля."""
    logout_user()
    return redirect('/')


def count_rating_raise(content: str) -> int:
    to_rate = len(content)
    overall_raise = 0
    for i in reversed(RATE.keys()):
        if i != 1:
            while to_rate >= i:
                overall_raise += RATE[i]
                to_rate -= i
    overall_raise += (to_rate % 10) / 10
    return overall_raise


def get_rank_by_rating(rating: int, session) -> int:
    for i in reversed(RANKS.keys()):
        if rating >= i:
            rank = session.query(Rank).filter(Rank.title == RANKS[i]).first()
            return rank.id


@app.route('/chats/<int:user_id>', methods=['POST', 'GET'])
@login_required
def chat(user_id):
    """Обработчик страницы чата с определенным полльзователем.
    :param user_id: id собеседника"""
    form = MessageForm()  # создаем форму ввода сообщения
    session = create_session()
    companion = session.query(User).filter(User.id == user_id).first()  # получаем объект собеседника по его id
    if not companion:  # проверяем, найден ли собеседник
        return abort(404)  # если нет - отображаем страницу с ошибкой 404
    # получаем список всех сообщений между клиентом и собеседником
    messages = session.query(Message).filter(((Message.to_id == current_user.id) & (Message.from_id == user_id)) |
                                             ((Message.from_id == current_user.id) & (Message.to_id == user_id))).all()
    sender = session.query(User).filter(User.id == current_user.id).first()  # получаем объект текущего пользователя
    if form.validate_on_submit():
        # создаем объект контента и заполняем его текстом сообщения
        cnt = Content()
        cnt.content = form.message_field.data
        session.add(cnt)
        session.commit()
        # рассчитываем надбавку к рейтингу
        sender.rating += count_rating_raise(cnt.content)
        sender.rating = round(sender.rating, 1)
        # присваиваем пользователю ранг, опираясь на его рейтинг
        sender.rank_id = get_rank_by_rating(sender.rating, session)
        session.commit()
        # создаем объект сообщения и заполняем все необходимые поля
        msg = Message()
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
    """Обработчик страницы со всеми чатами пользователя."""
    from itertools import groupby

    session = create_session()
    # получаем все полученные и отправленные сообщения
    messages = session.query(Message).filter((Message.to_id == current_user.id) |
                                             (Message.from_id == current_user.id)).all()
    # получаем всех собеседников клиента
    companions = sorted([msg.sender if msg.sender != current_user else msg.receiver for msg in messages],
                        key=lambda x: x.name)
    companions = list(reversed([user[0] for user in groupby(companions)]))
    last_messages = []
    for user in companions:
        # получаем последние сообщения в чатах клиента
        last_messages.append(session.query(Message).filter(((Message.to_id == current_user.id) &
                                                            (Message.from_id == user.id)) |
                                                           ((Message.from_id == current_user.id) &
                                                            (Message.to_id == user.id))).all()[-1])
    # сортируем полученные сообщения по времени отправления
    chats_list = sorted([[companions[i], last_messages[i]] for i in range(len(companions))],
                        key=lambda x: x[1].created_at)[::-1]
    return render_template('chats_list.html', chats_list=chats_list)


@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    """Обработчик страницы поиска со всеми собеседниками."""
    form = SearchForm()  # создаем форму поиска
    if form.validate_on_submit():
        session = create_session()
        # ищем пользователя по его фамилии/имени/телефонному номеру
        users = session.query(User).filter((User.name.like(f"{form.filter_field.data}%")) |
                                           (User.surname.like(f"{form.filter_field.data}%")) |
                                           (User.phone_number.like(f"{form.filter_field.data}%"))).all()
        if not users:  # проверяем, нашлись ли пользователи по введенным данным
            # если нет - даем клиенту об этом знать
            return render_template('search.html', form=form, message='Предложений по поиску нет')
        return render_template('search.html', form=form, users=users)
    return render_template('search.html', form=form)


@app.route('/profile/<int:user_id>')
@login_required
def show_profile(user_id):
    """Обработчик страницы профиля.
    :param user_id: id пользователя, чей профиль нужен клиенту"""
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()  # получаем данные профиля пользователя с указанным id
    if not user:  # проверяем, найден ли пользователь
        # если нет - показываем страницу с ошибкой
        return abort(404)
    # получаем место пользователя на доске почета
    all_users = session.query(User).order_by(User.rating.desc())
    position = 1
    for i in all_users:
        if i.id == user.id:
            break
        position += 1
    # получаем аватар пользователя
    pic = session.query(Avatar).filter(Avatar.refers_to == user_id).first()
    if pic:  # проверяем, найден ли аватар
        # если он есть - отображаем его
        profile_pic = url_for('static', filename=f"avatars/{pic.link}")
    else:
        # в противном случае - отображаем фото, установленное по умолчанию
        profile_pic = url_for('static', filename='avatars/anon.png')
    return render_template('profile.html', user=user, pic=profile_pic, today=datetime.datetime.now(), position=position)


@app.route('/profile/<int:user_id>/avatar', methods=['GET', 'POST'])
@login_required
def change_avatar(user_id):
    """Обработчик страницы смены аватара.
    :param user_id: id пользователя, чей профиль нужен клиенту"""
    if current_user.id != user_id:  # проверяем, является ли клиент владельцем профиля, аватар которого ему надо сменить
        return abort(403)  # если клиент таковым не является, показываем сообщение об ошибке
    form = AvatarForm()  # создаем форму смены аватара
    session = create_session()
    if form.validate_on_submit():
        photo = form.link_field.data  # получаем изображение
        file = secure_filename(photo.filename)  # получаем имя полученного изображения
        avatars = session.query(Avatar).filter(Avatar.refers_to == user_id).first()  # получаем объект аватара клиента
        if avatars:  # проверяем наличие аватара у клиента
            # если аватар сущетсвует - перезаписываем его полученным изображенем
            os.remove(os.path.join(app.root_path, 'static', 'avatars', avatars.link))
            avatars.link = file
            photo.save(os.path.join(app.root_path, 'static', 'avatars', file))
            session.commit()
        else:
            # если аватара не существует - создаем аватар для клиента
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
    """Обработчик страницы настройки профиля клиента.
    :param user_id: id клиента"""
    if current_user.id != user_id:  # проверяем, является ли клиент владельцем профиля который ему надо изменить
        return abort(403)  # если клиент таковым не является, показываем сообщение об ошибке
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()  # получаем объект пользователя по его id
    form = SetupProfileForm()  # создаем форму настройки профиля
    form.interests_field.choices = [(i.title, i.title) for i in session.query(Interest).all()]
    if request.method == 'GET':  # проверяем, нужно ли клиенту получить что либо с сервера
        # заполняем форму данными профиля
        form.interests_field.data = [tag.title for tag in user.interests]
        form.name_field.data = user.name
        form.surname_field.data = user.surname
        form.birthday_field.data = user.birthday
        form.phone_number_field.data = user.phone_number
    if form.validate_on_submit():
        # применяем изменения
        user.name = form.name_field.data
        user.surname = form.surname_field.data
        user.birthday = form.birthday_field.data
        user.phone_number = form.phone_number_field.data
        user.interests.clear()
        for tag in form.interests_field.data:
            tag_obj = session.query(Interest).filter(Interest.title == tag).first()
            user.interests.append(tag_obj)
        session.commit()
        return redirect(f'/profile/{user_id}')
    return render_template('profile_settings.html', form=form)


@login_required
@app.route('/advertisements/create', methods=['GET', 'POST'])
def create_advertisement():
    """Обработчик страницы создания объявления."""
    form = AdvertisementForm()  # создаем форму создания объявления
    session = create_session()
    tags = session.query(Interest).all()
    choices = [(i.title, i.title) for i in tags]
    form.tags_field.choices = choices
    if form.validate_on_submit():
        # создаем объект контента объявления и заполняем его
        cnt = Content()
        cnt.content = form.content_field.data
        session.add(cnt)
        session.commit()
        # создаем объект объявления и заполняем его
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
    """Обработчик страницы редаактирования объявления.
    :param ad_id: id объявления, которое нам надо изменить"""
    session = create_session()
    advertisement = session.query(Advertisement).filter(
        Advertisement.id == ad_id).first()  # получаем объект объявения по указанному id
    if not advertisement:  # проверяем, найдено ли такое объявление
        return abort(404)  # если объявления не найдено - показываем страницу с ошибкой
    if current_user != advertisement.author:  # проверяем, является ли клиент аавтором объявления
        return abort(403)  # если клиент не является автором - показываем страницу с ошибкой
    form = AdvertisementForm()  # создаем форму создания объявления
    form.tags_field.choices = [(i.title, i.title) for i in session.query(Interest).all()]
    if request.method == 'GET':  # проверяем, нужно ли клиенту получить что либо с сервера
        # заполняем исходные данные формы
        form.title_field.data = advertisement.title
        form.price_field.data = advertisement.price
        form.content_field.data = advertisement.content.content
        form.tags_field.data = [tag.title for tag in advertisement.interests]
    if form.validate_on_submit():
        # применяем изменения
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
    """Обработчик страницы удаления объявления.
    :param ad_id: id объявления которое надо удалить"""
    session = create_session()
    advertisement = session.query(Advertisement).filter(
        Advertisement.id == ad_id).first()  # получаем объект объявения по указанному id
    if not advertisement:  # проверяем, найдено ли такое объявление
        return abort(404)  # если объявления не найдено - показываем страницу с ошибкой
    if current_user != advertisement.author:  # проверяем, является ли клиент аавтором объявления
        return abort(403)  # если клиент не является автором - показываем страницу с ошибкой
    session.delete(advertisement)
    session.commit()
    return redirect('/')


@app.errorhandler(401)
def handle_401(error):
    """Обработчик ошибки 401.
    :param error: HTTP статус ошибки"""
    return redirect('/login')


@app.errorhandler(403)
def handle_403(error):
    """Обработчик ошибки 403.
    :param error: HTTP статус ошибки"""
    return render_template('errorhandler.html', error='Ошибка 403.', http_error=error,
                           message='Похоже вы попытались получить доступ к чему-то что вам не принадлежит.')


@app.errorhandler(404)
def handle_404(error):
    """Обработчик ошибки 404.
    :param error: HTTP статус ошибки"""
    response = make_response(render_template('errorhandler.html', error='Ошибка 404.', http_error=error,
                                             message='Похоже вы попытались получить доступ к чему-то не существующему. '
                                                     'Возможно, вы не вошли в свой аккаунт.'),
                             {'error': f'{error.code} {error.name}: {error.description}'})
    response.status = 'Not Found'
    response.status_code = 404
    return response


@app.errorhandler(405)
def handle_405(error):
    """Обработчик ошибки 405.
    :param error: HTTP статус ошибки"""
    return make_response({'error': error}, 405)


if __name__ == '__main__':
    global_init('db/chats_db.sqlite')  # инициализируем базу данных
    app.register_blueprint(api_blueprint, url_prefix='/api')  # загружаем обработчики API
    app.run()
