from flask_wtf.file import FileRequired, FileAllowed
from wtforms import PasswordField, BooleanField, SubmitField, StringField, DateField, FileField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf import FlaskForm

REQ_MESSAGE = 'Не все поля заполнены'
PSW_LEN_MESSAGE = 'Пароль должен содеражть не менее 8 символов'
PSW_EQUAL_MESSAGE = 'Пароли должны совпадать'
SUPPORTED_IMG_FORMATS = ['jpg', 'png']


class LoginForm(FlaskForm):
    email_field = EmailField('Почта:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Пароль:', validators=[DataRequired(REQ_MESSAGE)])
    remember_me = BooleanField('Запомнить меня:')
    submit_field = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    name_field = StringField('Имя:', validators=[DataRequired(REQ_MESSAGE)])
    surname_field = StringField('Фамилия:', validators=[DataRequired(REQ_MESSAGE)])
    birthday_field = DateField('Дата рождения (ГГГГ-ММ-ДД):', validators=[DataRequired(REQ_MESSAGE)])
    phone_number_field = StringField('Номер телефона: ', validators=[DataRequired(REQ_MESSAGE)])
    email_field = EmailField('Email адрес:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Пароль: ',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])
    confirm_password_field = PasswordField('Подтвердите пароль: ',
                                           validators=[EqualTo('password_field', PSW_EQUAL_MESSAGE)])
    submit_field = SubmitField('Регистрация')


class SearchForm(FlaskForm):
    number_field = StringField()
    search_field = SubmitField('Искать')


class MessageForm(FlaskForm):
    message_field = StringField()
    send_field = SubmitField('Отправить')


class AvatarForm(FlaskForm):
    link_field = FileField(f"Прикрепите файл с изображением в одном из возможных "
                           f"форматов: {', '.join(SUPPORTED_IMG_FORMATS)}",
                           validators=[FileRequired(), FileAllowed(SUPPORTED_IMG_FORMATS,
                                                                   f"Неверный формат. Доступные форматы: "
                                                                   f"{', '.join(SUPPORTED_IMG_FORMATS)}")])
    confirm_field = SubmitField('Установить')


class SetupProfileForm(FlaskForm):
    name_field = StringField('Имя:', validators=[DataRequired(REQ_MESSAGE)])
    surname_field = StringField('Фамилия:', validators=[DataRequired(REQ_MESSAGE)])
    birthday_field = DateField('Дата рождения (ГГГГ-ММ-ДД):', validators=[DataRequired(REQ_MESSAGE)])
    phone_number_field = StringField('Номер телефона:', validators=[DataRequired(REQ_MESSAGE)])
    confirm_field = SubmitField('Применить')


class ResetPasswordForm(FlaskForm):
    email_field = EmailField('Актуальный email адрес:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Новый пароль:',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])
    confirm_password_field = PasswordField('Подтвердите новый пароль:',
                                           validators=[EqualTo('password_field', PSW_EQUAL_MESSAGE)])
    submit_field = SubmitField('Сменить пароль')
