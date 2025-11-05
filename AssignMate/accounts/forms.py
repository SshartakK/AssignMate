"""Модуль форм для приложения accounts."""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Profile

__all__ = [
    'SignUpForm',
    'LoginForm',
    'UpdateUserForm',
    'UpdateProfileForm',
]


class SignUpForm(UserCreationForm):
    """Форма регистрации нового пользователя.

    Расширяет стандартную UserCreationForm, добавляя поля для личной информации
    и выбора роли пользователя в системе.

    Attributes:
        first_name (CharField): Имя пользователя
        last_name (CharField): Фамилия пользователя
        username (CharField): Уникальное имя пользователя
        email (EmailField): Электронная почта пользователя
        role (ChoiceField): Роль пользователя в системе
        password1 (CharField): Пароль (с виджетом PasswordInput)
        password2 (CharField): Подтверждение пароля
    """
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        label="I am a:",
    )
    password1 = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(),
    )
    password2 = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(),
    )

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью User
        по полям first_name, last_name, username, email и password1/2.
        """
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
        ]


class LoginForm(AuthenticationForm):
    """Форма аутентификации пользователя.

    Наследуется от стандартной AuthenticationForm и добавляет функциональность
    "запомнить меня" для продления сессии пользователя.

    Attributes:
        username (CharField): Имя пользователя с placeholder
        password (CharField): Пароль с placeholder
        remember_me (BooleanField): Флаг сохранения сессии
    """
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
    )
    password = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )
    remember_me = forms.BooleanField(required=False)

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью User
        по полям username, password и remember_me.
        """
        model = User
        fields = [
            'username',
            'password',
            'remember_me',
        ]


class UpdateUserForm(forms.ModelForm):
    """Форма обновления основных данных пользователя.

    Позволяет пользователю изменять имя пользователя и электронную почту.

    Attributes:
        username (CharField): Уникальное имя пользователя
        email (EmailField): Электронная почта пользователя
    """
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.TextInput(),
    )

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью User
        по полям username и email.
        """
        model = User
        fields = [
            'username',
            'email',
        ]


class UpdateProfileForm(forms.ModelForm):
    """Форма обновления профиля пользователя.

    Позволяет пользователю изменять аватар и биографию.

    Attributes:
        avatar (ImageField): Аватар пользователя
        bio (CharField): Биография пользователя с текстовым полем
    """
    avatar = forms.ImageField(widget=forms.FileInput())
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью Profile
        по полям avatar и bio.
        """
        model = Profile
        fields = [
            'avatar',
            'bio',
        ]