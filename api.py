import datetime
from functools import wraps

from flask import abort, jsonify, request, make_response
from flask.blueprints import Blueprint
from werkzeug.security import check_password_hash
import jwt

from data.db_session import create_session
from data.__all_models import *
from data.constants import SECRET_KEY

# создаем blueprint для API
api_blueprint = Blueprint('api', __name__, template_folder='templates', static_folder='static')


def token_required(func):
    """Декоратор для функций, проверяющий наличие токена в запросе.
    :param func - декорируемая функция"""

    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('x-access-token')  # получаем токен из запроса
        if not token:  # проверяем наличие токена
            abort(400)  # если токена нет - возвращаем ошибку
        try:
            session = create_session()
            data = jwt.decode(token, SECRET_KEY)
            user = session.query(User).filter(
                User.id == data['id']).first()  # получаем владельца токена по его id, закодированном в токене
        except jwt.exceptions.DecodeError and KeyError:
            # если при декодинге или при получении данных из токена возникли ошибки - возвращаем сообщение о том,
            # что токен недействителен
            return jsonify({'message': 'Token is invalid!'})
        except jwt.exceptions.ExpiredSignatureError:
            # если при декодинге выяснилось, что токен просрочен - возвращаем сообщения о том, что токен просрочен
            return jsonify({'message': 'Token is expired!'})

        return func(user, *args, **kwargs)

    return decorated


@api_blueprint.route('/login', methods=['GET'])
def login():
    """Обработчик запроса на авторизацию."""
    auth_data = request.authorization  # получаем данные для входа из запроса
    # проверяем наличие и коррекность данных для входа
    if not auth_data or not auth_data.username or not auth_data.password:
        # если данные для входа отсутствуют или они некорректны - возвращаем ошибку
        return jsonify({'message': 'Could not verify'})
    session = create_session()
    # получаем объект пользователя по полученному email
    user = session.query(User).filter(User.email == auth_data.username).first()
    if not user:  # проверяем, найден ли такой пользователь
        abort(404)  # если пользователь не найден - возвращаем ошибку
    if not check_password_hash(user.hashed_password, auth_data.password):  # проверяем пароль
        return jsonify({'message': 'Incorrect password'})  # если пароль неверный - возвращаем ошибку
    # кодируем токен через ключ безопасности приложения и возвращаем его в кодировке UTF-8
    token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY)
    return jsonify({'token': token.decode('UTF-8')})


@api_blueprint.route('/users', methods=['GET'])
@token_required
def get_users(current_user: User):
    """Обработчик запроса на получение данных о всех пользователях.
    :param current_user: клиент"""
    if not current_user.admin:  # проверяем, является ли клиент администратором
        abort(403)  # если клиент таковым не является - воозвращаем сообщение об ошибке
    session = create_session()
    users = session.query(User).all()  # получаем список всех пользователей
    return jsonify({'users': [user.to_dict() for user in users]})


@api_blueprint.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_exact_user(current_user: User, user_id):
    """Обработчик запроса на получение данных об определенном пользователе.
    :param user_id: id пользователя, данные которого необхдимо получить
    :param current_user: клиент"""
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()  # получаем данные о пользователе по id
    if not user:  # проверяем сущесвует ли пользователь
        abort(404)  # если пользователя не существует - возвращаем ошибку
    if current_user.admin or current_user.id == user_id:  # проверяем, хочет ли клиент получить данные о себе
        # если это так - возвращаем все данные
        return jsonify({f'user{user_id}': user.to_dict()})
    # в противном случае - убираем персональные данные из ответа
    return jsonify({f'user{user_id}': user.to_dict() if current_user.admin or current_user.id == user_id
                    else user.to_dict(rules=('-email',))})


@api_blueprint.route('/users', methods=['POST'])
@token_required
def create_user(current_user: User):
    """Обработчик запроса на создание пользователей.
    :param current_user: клиент"""
    user_data = request.json  # получаем данные о новом пользователе из запроса
    if not user_data:  # проверяем наличие данных в запросе
        abort(400)  # если данных нет - возвращаем ошибку
    if not current_user.admin:  # проверяем, является ли клиент админом
        abort(403)  # если клиент не админ - возвращаем ошибку
    # проверяем корректность данных в запросе
    if not all((user_data.get('name'), user_data.get('surname'), user_data.get('birthday'), user_data.get('email'),
                user_data.get('phone_number'), user_data.get('password'))):
        abort(400)  # если какие-либо данные отсутствуют - возвращаем ошибку
    if len(user_data['password']) < 8:  # проверяем длину пароля
        return jsonify({'message': 'Password is too short!'})  # если длина пароля меннее 8 символов - возвращаем ошибку
    # создаем нового пользвателя и заполняем данные о нем
    user = User()
    user.name = user_data['name']
    user.surname = user_data['surname']
    user.birthday = datetime.datetime.fromisoformat(user_data['birthday'])
    user.email = user_data['email']
    user.phone_number = user_data['phone_number']
    user.set_password(user_data['password'])
    session = create_session()
    session.add(user)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/users', methods=['PUT'])
@token_required
def edit_user(current_user: User):
    """Обработчик запроса на редактирование своего профиля.
    :param current_user: клиент"""
    user_data = request.json  # получаем данные о новом пользователе из запроса
    if not user_data:  # проверяем наличие данных в запросе
        abort(400)  # если данных нет - возвращаем ошибку
    # проверяем корректность данных в запросе
    if any([key not in ('name', 'surname', 'birthday', 'phone_number', 'interests') for key in user_data]):
        # если найдены лишние ключи - возвращаем ошибку
        abort(400)
    session = create_session()
    # получаем объект пользователя клиента и заменяем старые данные новыми
    user = session.query(User).filter(User.id == current_user.id).first()
    user.name = user_data['name'] if user_data.get('name') else user.name
    user.surname = user_data['surname'] if user_data.get('surname') else user.surname
    user.birthday = datetime.datetime.fromisoformat(user_data['birthday']) \
        if user_data.get('birthday') else user.birthday
    user.phone_number = user_data['phone_number'] if user_data.get('phone_number') else user.phone_number
    if user_data.get('interests'):
        if not user_data['interests'].get('ids'):  # проверяем наличие ключа ids (id новых интересов)
            abort(400)  # если такого ключа - возвращаем ошибку
        # получаем интересы по указанным id
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in user_data['interests']['ids']]
        if not all(interests):  # проверяем, все ли интересы были найдены
            abort(400)  # есди какого-либо из интересов не существует - возвращаем ошибку
        if user_data['interests'].get('replace'):
            user.interests = interests.copy()
        elif user_data['interests'].get('extend'):
            user.interests.extend(interests)
        else:
            user.interests.extend(interests)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/messages/<int:user_id>', methods=['GET'])
@token_required
def get_chat(current_user: User, user_id):
    """Обработчик запроса на получение всех чата с пользователем.
    :param user_id: id собеседеника
    :param current_user: клиент"""
    session = create_session()
    # получаем список всех сообщений в чате между клиентом и пользователем с указанным id
    messages = session.query(Message).filter(((Message.to_id == current_user.id) & (Message.from_id == user_id)) |
                                             ((Message.from_id == current_user.id) & (Message.to_id == user_id))).all()
    if not messages:  # проверяем, были ли сообщения найдены
        abort(404)  # если сообщения не были найдены - возвращаем ошибку
    return jsonify({f'chat_with_{user_id}': [message.to_dict() for message in messages]})


@api_blueprint.route('/messages/<int:user_id>', methods=['POST'])
@token_required
def post_message(current_user: User, user_id):
    """Обработчик запроса на отправление сообщений пользователю.
    :param user_id: id собеседника
    :param current_user: клиент"""
    from main import get_rank_by_rating, count_rating_raise
    if not request.json:  # проверяем наличие данных в запросе
        abort(400)  # если данных в запросе нет - возвращаем ошибку
    msg_content = request.json.get('content')  # получаем содержание собщения в json запросе
    if not msg_content:  # проверяем налчие содержания сообщения
        abort(400)  # если содержание сообщения отсутствует - возвращаем ошибку
    session = create_session()
    if user_id not in [i[0] for i in
                       session.query(User.id).all()]:  # проверяем наличие пользователя с указанным id в бд
        abort(404)  # если такого пользователя не существует - возвращаем ошибку
    # создаем объект содержания и заполняем его
    cnt = Content()
    cnt.content = msg_content
    session.add(cnt)
    session.commit()
    sender = session.query(User).filter(User.id == current_user.id).first()  # получаем объект пользователя клиента
    # рассчитываем надбавку к рейтингу
    sender.rating += count_rating_raise(cnt.content)
    sender.rating = round(sender.rating, 1)
    # присваиваем пользователю ранг, опираясь на его рейтинг
    sender.rank_id = get_rank_by_rating(sender.rating, session)
    session.commit()
    # создаем объект сообщения и заполняем все необходимые поля
    msg = Message()
    msg.content = cnt
    msg.from_id = current_user.id
    msg.to_id = user_id
    session.add(msg)
    session.commit()
    return jsonify({'message': 'Success'})


@api_blueprint.route('/ads', methods=['GET'])
@token_required
def get_ads(current_user: User):
    """Обработчик запроса на получение актуальных объявлений.
    :param current_user: клиент"""
    session = create_session()
    # получаем 100 последних объявлений
    ads = reversed(sorted(session.query(Advertisement).all(), key=lambda x: x.created_at)[:100])
    return jsonify({'ads': [ad.to_dict() for ad in ads]})


@api_blueprint.route('/users/<int:user_id>/ads', methods=['GET'])
@token_required
def get_users_ads(current_user: User, user_id):
    """Обработчик запроса на получение актуальных объявлений пользователя.
    :param user_id: id пользователя, объявления которого нам необходимо получить
    :param current_user: клиент"""
    session = create_session()
    # получаем объект пользователя, объявления которого нам необходимо получить по его id
    user = session.query(User).filter(User.id == user_id).first()
    if not user:  # проверяем существование такого пользователя
        abort(404)  # если такого пользователя не существует - возвращаем ошибку
    # получаем 100 последних объявлений пользователя
    ads = reversed(sorted(user.advertisements, key=lambda x: x.created_at)[:100])
    return jsonify({f'user{user_id}_ads': [ad.to_dict() for ad in ads]})


@api_blueprint.route('/ads', methods=['POST'])
@token_required
def create_ad(current_user: User):
    """Обработчик запроса на создание объявлений.
    :param current_user: клиент"""
    ad_data = request.json  # получаем данные о новом объявлении из запроса
    if not ad_data:  # проверяем наличие данных в запросе
        abort(400)  # если данных нет - возвращаем ошибку
    # проверяем корректность данных в запросе
    if not all((ad_data.get('title'), ad_data.get('price'), ad_data.get('content'))):
        abort(400)  # если какие-либо данные отсутствуют - возвращаем ошибку
    # создаем объект содержания и заполняем его
    content = Content()
    content.content = ad_data['content']
    session = create_session()
    session.add(content)
    session.commit()
    # создаем объект объявления и заполняем его
    ad = Advertisement()
    ad.title = ad_data['title']
    ad.content = content
    ad.author = session.query(User).filter(User.id == current_user.id).first()
    try:
        ad.price = int(ad_data['price'])
    except TypeError:
        abort(400)  # если значение по ключу 'price' не число - возвращаем ошибку
    if ad_data.get('interests'):
        if not ad_data['interests'].get('ids'):  # проверяем наличие ключа ids (id новых интересов)
            abort(400)  # если такого ключа - возвращаем ошибку
        # получаем интересы по указанным id
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in ad_data['interests']['ids']]
        if not all(interests):  # проверяем, все ли интересы были найдены
            abort(400)  # если какого-либо из интересов не существует - возвращаем ошибку
        ad.interests = interests
    session.add(ad)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/ads/<int:ad_id>', methods=['PUT'])
@token_required
def edit_ad(current_user: User, ad_id):
    """Обработчик запроса на редактирование объявления.
    :param ad_id: id объявления, которое надо отредактировать
    :param current_user: клиент"""
    ad_data = request.json  # получаем данные о новом объявлении из запроса
    if not ad_data:  # проверяем наличие данных в запросе
        abort(400)  # если данных нет - возвращаем ошибку
    # проверяем корректность данных в запросе
    if any([key not in ('title', 'content', 'price', 'interests') for key in ad_data]):
        abort(400)  # если в запросе есть лишние ключи - возвращаем ошибку
    session = create_session()
    # получаем объект объявления которое нам надо изменить
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not advertisement:  # проверяем, найдено ли объявление
        abort(404)  # если объявление не найдено - возвращаем ошибку
    if advertisement.author != current_user:  # проверяем, является ли клиент автором объявления
        abort(403)  # если автором объявления не является клиент - возвращаем ошибку
    # изменяем необходимые поля объявления
    advertisement.title = ad_data['title'] if ad_data.get('title') else advertisement.title
    advertisement.content.content = ad_data['content'] if ad_data.get('content') else advertisement.content.content
    try:
        advertisement.price = int(ad_data['price']) if ad_data.get('price') else advertisement.price
    except TypeError:
        abort(400)  # если значение по ключу 'price' не число - возвращаем ошибку
    if ad_data.get('interests'):
        if not ad_data['interests'].get('ids'):  # проверяем наличие ключа ids (id новых интересов)
            abort(400)  # если такого ключа - возвращаем ошибку
        # получаем интересы по указанным id
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in ad_data['interests']['ids']]
        if not all(interests):  # проверяем, все ли интересы были найдены
            abort(400)  # если какого-либо из интересов не существует - возвращаем ошибку
        if ad_data['interests'].get('replace'):
            advertisement.interests = interests.copy()
        elif ad_data['interests'].get('extend'):
            advertisement.interests.extend(interests)
        else:
            advertisement.interests.extend(interests)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/ads/<int:ad_id>', methods=['DELETE'])
@token_required
def delete_ad(current_user: User, ad_id):
    """Обработчик запроса на удаление объявления.
    :param ad_id: id объявления, которое надо удалить
    :param current_user: клиент"""
    session = create_session()
    # получаем объект объявления которое нам надо удалить
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not advertisement:  # проверяем, найдено ли объявление
        abort(404)  # если объявление не найдено - возвращаем ошибку
    if advertisement.author != current_user:  # проверяем, является ли клиент автором объявления
        abort(403)  # если автором объявления не является клиент - возвращаем ошибку
    session.delete(advertisement)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/interests', methods=['GET'])
def get_interests():
    """Обработик запроса на получение всех интересов."""
    session = create_session()
    interests = session.query(Interest).all()
    return jsonify({'interests': [interest.to_dict() for interest in interests]})


@api_blueprint.errorhandler(405)
def api_handle_405(error):
    """Обработчик ошибки 405.
    :param error: HTTP статус ошибки"""
    return make_response({'error': 'Method not allowed'}, 405)


@api_blueprint.errorhandler(404)
def api_handle_404(error):
    """Обработчик ошибки 404.
    :param error: HTTP статус ошибки"""
    return make_response({'error': 'Not Found'}, 404)


@api_blueprint.errorhandler(403)
def api_handle_403(error):
    """Обработчик ошибки 403.
    :param error: HTTP статус ошибки"""
    return make_response({'error': 'Access Denied'}, 403)


@api_blueprint.errorhandler(400)
def api_handle_400(error):
    """Обработчик ошибки 400.
    :param error: HTTP статус ошибки"""
    return make_response({'error': 'Bad Request'}, 400)
