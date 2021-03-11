from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms import StringField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo


class RegistrationForm(FlaskForm):
    name_field = StringField('Имя:', validators=[DataRequired()])
    surname_field = StringField('Фамилия:', validators=[DataRequired()])
    birthday_field = DateField('Дата рождения:', validators=[DataRequired()])
    phone_number_field = StringField('Номер телефона: ', validators=[DataRequired()])
    email_field = EmailField('Email адрес:', validators=[DataRequired()])
    password_field = PasswordField('Введите пароль: ', validators=[DataRequired()])
    confirm_password_field = PasswordField('Подтвердите пароль: ', validators=[DataRequired(), EqualTo(password_field)])
    submit_field = SubmitField('Регистрация')
