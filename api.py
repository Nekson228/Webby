import datetime
from functools import wraps

from flask import abort, jsonify, request, make_response
from flask.blueprints import Blueprint
from werkzeug.security import check_password_hash
import jwt

from data.db_session import create_session
from data.__all_models import *
from data.constants import SECRET_KEY

api_blueprint = Blueprint('api', __name__, template_folder='templates', static_folder='static')


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('x-access-token')
        if not token:
            abort(400)
        try:
            session = create_session()
            data = jwt.decode(token, SECRET_KEY)
            user = session.query(User).filter(User.id == data['id']).first()
        except jwt.exceptions.DecodeError and KeyError:
            return jsonify({'message': 'Token is invalid!'})
        except jwt.exceptions.ExpiredSignatureError:
            return jsonify({'message': 'Token is expired!'})

        return func(user, *args, **kwargs)

    return decorated


@api_blueprint.route('/login', methods=['GET'])
def login():
    auth_data = request.authorization
    if not auth_data or not auth_data.username or not auth_data.password:
        return jsonify({'message': 'Could not verify'})
    session = create_session()
    user = session.query(User).filter(User.email == auth_data.username).first()
    if not user:
        abort(404)
    if not check_password_hash(user.hashed_password, auth_data.password):
        return jsonify({'message': 'Incorrect password'})

    token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY)
    return jsonify({'token': token.decode('UTF-8')})


@api_blueprint.route('/users', methods=['GET'])
@token_required
def get_users(current_user: User):
    if not current_user.admin:
        abort(403)
    session = create_session()
    users = session.query(User).all()
    return jsonify({'users': [user.to_dict() for user in users]})


@api_blueprint.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_exact_user(current_user: User, user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        abort(404)
    if current_user.admin or current_user.id == user_id:
        return jsonify({f'user{user_id}': user.to_dict()})
    return jsonify({f'user{user_id}': user.to_dict() if current_user.admin or current_user.id == user_id
                    else user.to_dict(rules=('-email',))})


@api_blueprint.route('/users', methods=['POST'])
@token_required
def create_user(current_user: User):
    user_data = request.json
    if not user_data:
        abort(400)
    if not current_user.admin:
        abort(403)
    if not all((user_data.get('name'), user_data.get('surname'), user_data.get('birthday'), user_data.get('email'),
                user_data.get('phone_number'), user_data.get('password'))):
        abort(400)
    if len(user_data['password']) < 8:
        return jsonify({'message': 'Password is too short!'})
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
    user_data = request.json
    if not user_data:
        abort(400)
    if any([key not in ('name', 'surname', 'birthday', 'phone_number', 'interests') for key in user_data]):
        abort(400)
    session = create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    user.name = user_data['name'] if user_data.get('name') else user.name
    user.surname = user_data['surname'] if user_data.get('surname') else user.surname
    user.birthday = datetime.datetime.fromisoformat(user_data['birthday']) \
        if user_data.get('birthday') else user.birthday
    user.phone_number = user_data['phone_number'] if user_data.get('phone_number') else user.phone_number
    if user_data.get('interests'):
        if not user_data['interests'].get('ids'):
            abort(400)
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in user_data['interests']['ids']]
        if not all(interests):
            abort(400)
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
    session = create_session()
    messages = session.query(Message).filter(((Message.to_id == current_user.id) & (Message.from_id == user_id)) |
                                             ((Message.from_id == current_user.id) & (Message.to_id == user_id))).all()
    if not messages:
        abort(404)
    return jsonify({f'chat_with_{user_id}': [message.to_dict() for message in messages]})


@api_blueprint.route('/messages/<int:user_id>', methods=['POST'])
@token_required
def post_message(current_user: User, user_id):
    if not request.json:
        abort(400)
    msg_content = request.json.get('content')
    if not msg_content:
        abort(400)
    session = create_session()
    if user_id not in [i[0] for i in session.query(User.id).all()]:
        abort(404)
    cnt = Content()
    cnt.content = msg_content
    session.add(cnt)
    session.commit()
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
    session = create_session()
    ads = reversed(sorted(session.query(Advertisement).all(), key=lambda x: x.created_at)[:100])
    return jsonify({'ads': [ad.to_dict() for ad in ads]})


@api_blueprint.route('/users/<int:user_id>/ads', methods=['GET'])
@token_required
def get_users_ads(current_user: User, user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        abort(404)
    ads = reversed(sorted(user.advertisements, key=lambda x: x.created_at)[:100])
    return jsonify({f'user{user_id}_ads': [ad.to_dict() for ad in ads]})


@api_blueprint.route('/ads', methods=['POST'])
@token_required
def create_ad(current_user: User):
    ad_data = request.json
    if not ad_data:
        abort(400)
    if not all((ad_data.get('title'), ad_data.get('price'), ad_data.get('content'))):
        abort(400)
    content = Content()
    content.content = ad_data['content']
    session = create_session()
    session.add(content)
    session.commit()
    ad = Advertisement()
    ad.title = ad_data['title']
    if ad_data.get('interests'):
        if not ad_data['interests'].get('ids'):
            abort(400)
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in ad_data['interests']['ids']]
        if not all(interests):
            abort(400)
        ad.interests = interests
    try:
        ad.price = int(ad_data['price'])
    except TypeError:
        abort(400)
    ad.content = content
    ad.author = session.query(User).filter(User.id == current_user.id).first()
    session.add(ad)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/ads/<int:ad_id>', methods=['PUT'])
@token_required
def edit_ad(current_user: User, ad_id):
    ad_data = request.json
    if not ad_data:
        abort(400)
    if any([key not in ('title', 'content', 'price', 'interests') for key in ad_data]):
        abort(400)
    session = create_session()
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not advertisement:
        abort(404)
    if advertisement.author != current_user:
        abort(403)
    advertisement.title = ad_data['title'] if ad_data.get('title') else advertisement.title
    advertisement.content.content = ad_data['content'] if ad_data.get('content') else advertisement.content.content
    try:
        advertisement.price = int(ad_data['price']) if ad_data.get('price') else advertisement.price
    except TypeError:
        abort(400)
    if ad_data.get('interests'):
        if not ad_data['interests'].get('ids'):
            abort(400)
        interests = [session.query(Interest).filter(Interest.id == interest_id).first()
                     for interest_id in ad_data['interests']['ids']]
        if not all(interests):
            abort(400)
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
    session = create_session()
    advertisement = session.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if advertisement.author != current_user:
        abort(403)
    session.delete(advertisement)
    session.commit()
    return jsonify({'message': 'Success!'})


@api_blueprint.route('/interests', methods=['GET'])
def get_interests():
    session = create_session()
    interests = session.query(Interest).all()
    return jsonify({'interests': [interest.to_dict() for interest in interests]})


@api_blueprint.errorhandler(405)
def api_handle_405(error):
    return make_response({'error': 'Method not allowed'}, 405)


@api_blueprint.errorhandler(404)
def api_handle_404(error):
    return make_response({'error': 'Not Found'}, 404)


@api_blueprint.errorhandler(403)
def api_handle_403(error):
    return make_response({'error': 'Access Denied'}, 403)


@api_blueprint.errorhandler(400)
def api_handle_400(error):
    return make_response({'error': 'Bad Request'}, 400)
