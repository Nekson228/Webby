from flask_wtf.file import FileRequired, FileAllowed
from wtforms import PasswordField, BooleanField, SubmitField, StringField, FileField, SelectMultipleField, \
    widgets, IntegerField, TextAreaField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from flask_wtf import FlaskForm

from data.db_session import create_session
from data.__all_models import *

REQ_MESSAGE = 'Не все поля заполнены'
PSW_LEN_MESSAGE = 'Пароль должен содеражть не менее 8 символов'
PSW_EQUAL_MESSAGE = 'Пароли должны совпадать'
SUPPORTED_IMG_FORMATS = ['jpg', 'png']


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    email_field = EmailField('Почта:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Пароль:', validators=[DataRequired(REQ_MESSAGE)])
    remember_me = BooleanField('Запомнить меня:')
    submit_field = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    name_field = StringField('Имя:', validators=[DataRequired(REQ_MESSAGE)])
    surname_field = StringField('Фамилия:', validators=[DataRequired(REQ_MESSAGE)])
    birthday_field = DateField('Дата рождения:', validators=[DataRequired(REQ_MESSAGE)])
    phone_number_field = StringField('Номер телефона: ', validators=[DataRequired(REQ_MESSAGE)])
    email_field = EmailField('Email адрес:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Пароль: ',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])
    confirm_password_field = PasswordField('Подтвердите пароль: ',
                                           validators=[EqualTo('password_field', PSW_EQUAL_MESSAGE)])
    submit_field = SubmitField('Регистрация')

    def validate_phone_number_field(self, field: StringField):
        session = create_session()
        if field.data in [phone[0] for phone in session.query(User.phone_number).all()]:
            raise ValidationError('Пользователь с таким номером телефона уже существует')

    def validate_email_field(self, field: EmailField):
        session = create_session()
        if field.data in [email[0] for email in session.query(User.email).all()]:
            raise ValidationError('Пользователь с таким  адресом эл. почты уже существует')


class SearchForm(FlaskForm):
    filter_field = StringField()
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
    interests_field = MultiCheckboxField('Интересы', choices=[('foo', 'bar'), ('cout', 'pep')])
    confirm_field = SubmitField('Применить')


class ResetPasswordForm(FlaskForm):
    email_field = EmailField('Актуальный email адрес:', validators=[DataRequired(REQ_MESSAGE)])
    password_field = PasswordField('Новый пароль:',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])
    confirm_password_field = PasswordField('Подтвердите новый пароль:',
                                           validators=[EqualTo('password_field', PSW_EQUAL_MESSAGE)])
    submit_field = SubmitField('Сменить пароль')


class AdvertisementForm(FlaskForm):
    title_field = StringField('Название объявления: ', validators=[DataRequired(REQ_MESSAGE)])
    price_field = IntegerField('Цена товара/услуги (в рублях): ', validators=[DataRequired(REQ_MESSAGE)])
    content_field = TextAreaField('Опишите товар/услугу: ', validators=[DataRequired(REQ_MESSAGE)],
                                  render_kw={'class': 'w-75'})
    tags_field = MultiCheckboxField('Тэги: ', choices=[('foo', 'bar'), ('cout', 'pep')])
    submit_field = SubmitField('Создать объявление')


class TokenForm(FlaskForm):
    token_field = StringField('Ваш токен:')
    get_field = SubmitField('Сгенерировать токен')
