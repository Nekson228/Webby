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
    """Класс кастомного поля со множеством чекбоксов."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    """Класс формы входа."""
    email_field = EmailField('Почта:', validators=[DataRequired(REQ_MESSAGE)])  # поле для email
    password_field = PasswordField('Пароль:', validators=[DataRequired(REQ_MESSAGE)])  # поле для пароля
    remember_me = BooleanField('Запомнить меня:')  # поле с чекбоксом для запоминания пользователя
    submit_field = SubmitField('Войти')  # кнопка для входа


class RegistrationForm(FlaskForm):
    """Класс формы регистрации."""
    name_field = StringField('Имя:', validators=[DataRequired(REQ_MESSAGE)])  # поле для имени
    surname_field = StringField('Фамилия:', validators=[DataRequired(REQ_MESSAGE)])  # поле для фамилии
    birthday_field = DateField('Дата рождения:', validators=[DataRequired(REQ_MESSAGE)])  # поле для дня рождения
    phone_number_field = StringField('Номер телефона: ',
                                     validators=[DataRequired(REQ_MESSAGE)])  # поле для номера телефона
    email_field = EmailField('Email адрес:', validators=[DataRequired(REQ_MESSAGE)])  # поле для email
    password_field = PasswordField('Пароль: ',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])  # поле для пароля
    confirm_password_field = PasswordField('Подтвердите пароль: ',
                                           validators=[EqualTo('password_field',
                                                               PSW_EQUAL_MESSAGE)])  # поле для подтверждения пароля
    submit_field = SubmitField('Регистрация')  # кнопка для входа

    def validate_phone_number_field(self, field: StringField):
        """Метод, проверяющий уникальность введенных данных в поле для телефона
        :param field: поле, которое необходимо проверить"""
        session = create_session()
        if field.data in [phone[0] for phone in session.query(User.phone_number).all()]:
            raise ValidationError('Пользователь с таким номером телефона уже существует')

    def validate_email_field(self, field: EmailField):
        """Метод, проверяющий уникальность введенных данных в поле для email
        :param field: поле, которое необходимо проверить"""
        session = create_session()
        if field.data in [email[0] for email in session.query(User.email).all()]:
            raise ValidationError('Пользователь с таким  адресом эл. почты уже существует')


class SearchForm(FlaskForm):
    """Класс формы поиска пользователя."""
    filter_field = StringField()  # поле для поисковых данных
    search_field = SubmitField('Искать')  # кнопка для поиска


class MessageForm(FlaskForm):
    """Класс формы ввода сообщения."""
    message_field = StringField()  # поле для ввода сообщения
    send_field = SubmitField('Отправить')  # кнопка для отправки


class AvatarForm(FlaskForm):
    """Класс формы загрузки аватара."""
    # поле для загрузки файла
    link_field = FileField(f"Прикрепите файл с изображением в одном из возможных "
                           f"форматов: {', '.join(SUPPORTED_IMG_FORMATS)}",
                           validators=[FileRequired(), FileAllowed(SUPPORTED_IMG_FORMATS,
                                                                   f"Неверный формат. Доступные форматы: "
                                                                   f"{', '.join(SUPPORTED_IMG_FORMATS)}")])
    confirm_field = SubmitField('Установить')  # кнопка для отправки файла


class SetupProfileForm(FlaskForm):
    """Класс формы настроек профиля."""
    name_field = StringField('Имя:', validators=[DataRequired(REQ_MESSAGE)])  # поле для имени
    surname_field = StringField('Фамилия:', validators=[DataRequired(REQ_MESSAGE)])  # поле для фамилии
    birthday_field = DateField('Дата рождения (ГГГГ-ММ-ДД):',
                               validators=[DataRequired(REQ_MESSAGE)])  # поле для дня рождения
    phone_number_field = StringField('Номер телефона:',
                                     validators=[DataRequired(REQ_MESSAGE)])  # поле для номера телефона
    interests_field = MultiCheckboxField('Интересы', choices=[('foo', 'bar'), ('cout', 'pep')])  # поле для интересов
    confirm_field = SubmitField('Применить')  # кнопка для подтверждения изменений


class ResetPasswordForm(FlaskForm):
    """Класс формы сброса пароля"""
    email_field = EmailField('Актуальный email адрес:', validators=[DataRequired(REQ_MESSAGE)])  # поле для email
    password_field = PasswordField('Новый пароль:',
                                   validators=[DataRequired(REQ_MESSAGE),
                                               Length(min=8, message=PSW_LEN_MESSAGE)])  # поле для пароля
    confirm_password_field = PasswordField('Подтвердите новый пароль:',
                                           validators=[EqualTo('password_field',
                                                               PSW_EQUAL_MESSAGE)])  # поле для подтверждения парля
    submit_field = SubmitField('Сменить пароль')  # кнопка для смены пароля


class AdvertisementForm(FlaskForm):
    """Класс формы создания/изменения объявления"""
    title_field = StringField('Название объявления: ', validators=[DataRequired(REQ_MESSAGE)])  # поле для названия
    price_field = IntegerField('Цена товара/услуги (в рублях): ',
                               validators=[DataRequired(REQ_MESSAGE)])  # поле для цены
    content_field = TextAreaField('Опишите товар/услугу: ', validators=[DataRequired(REQ_MESSAGE)],
                                  render_kw={'class': 'w-75'})  # поле для содержания
    tags_field = MultiCheckboxField('Тэги: ', choices=[('foo', 'bar'), ('cout', 'pep')])  # поле для тегов
    submit_field = SubmitField('Создать/изменить объявление')  # кнопка для создания/изменения объявления
