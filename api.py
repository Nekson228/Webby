import datetime
from functools import wraps

from flask import abort, jsonify, request, make_response
from flask.blueprints import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash
import jwt

from data.db_session import create_session
from data.__all_models import *
from data.constants import SECRET_KEY

api_blueprint = Blueprint('api', __name__, template_folder='templates', static_folder='static')


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.json.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'})
        try:
            session = create_session()
            data = jwt.decode(token, SECRET_KEY)
            if datetime.datetime.utcnow().timestamp() > data['exp']:
                return jsonify({'message': 'Token is expired!'})
            user = session.query(User).filter(User.id == data['id']).first()
        except jwt.exceptions.DecodeError and KeyError:
            return jsonify({'message': 'Token is invalid!'})

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
        return jsonify({'message': 'Not found'})
    if not check_password_hash(user.hashed_password, auth_data.password):
        return jsonify({'message': 'Incorrect password'})

    token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, SECRET_KEY)
    return jsonify({'token': token.decode('UTF-8')})


@api_blueprint.route('/users', methods=['GET'])
@token_required
def get_users(user):
    if not user.admin:
        return jsonify({'message': 'Forbidden'})
    session = create_session()
    users = session.query(User).all()
    return jsonify({'users': [user.to_dict() for user in users]})
