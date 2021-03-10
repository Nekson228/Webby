from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class MessageForm(FlaskForm):
    message_field = StringField()
    send_field = SubmitField('Отправить')
