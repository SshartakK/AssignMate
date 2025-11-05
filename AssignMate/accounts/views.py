"""Модуль представлений приложения accounts."""

from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin

from .forms import SignUpForm, LoginForm, UpdateUserForm, UpdateProfileForm
from .models import Profile

__all__ = [
    'SignUpView',
    'CustomLoginView',
    'view_profile',
    'edit_profile',
    'ChangePasswordView',
]


class SignUpView(generic.CreateView):
    """Представление для регистрации новых пользователей.

    Наследуется от Django generic CreateView и предоставляет функциональность
    для создания новых учетных записей пользователей с автоматическим
    созданием связанного профиля.

    Attributes:
        form_class (Form): Класс формы для регистрации
        success_url (str): URL для перенаправления после успешной регистрации
        initial (dict): Начальные значения для формы
        template_name (str): Путь к шаблону страницы регистрации
    """
    form_class = SignUpForm
    success_url = reverse_lazy("login")
    initial = None
    template_name = 'registration/signup.html'

    def dispatch(self, request, *args, **kwargs):
        """Обрабатывает входящий запрос перед вызовом основного метода.

        Args:
            request (HttpRequest): Входящий HTTP-запрос.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            HttpResponse: Перенаправление на главную страницу для аутентифицированных
                         пользователей или вызов родительского метода dispatch.
        """
        if request.user.is_authenticated:
            return redirect(to='/')

        return super(SignUpView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Обрабатывает GET-запрос для отображения формы регистрации.

        Args:
            request (HttpRequest): Входящий HTTP-запрос.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            HttpResponse: Рендеринг страницы с формой регистрации.
        """
        form = self.form_class(initial=self.initial)
        return render(
            request,
            self.template_name,
            context={'form': form},
        )

    def post(self, request, *args, **kwargs):
        """Обрабатывает POST-запрос с данными формы регистрации.

        Валидирует данные формы, создает пользователя и связанный профиль,
        отображает сообщение об успехе и перенаправляет на страницу входа.

        Args:
            request (HttpRequest): Входящий HTTP-запрос с данными формы.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            HttpResponse: Перенаправление на страницу входа при успешной регистрации
                         или повторное отображение формы с ошибками валидации.
        """
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save()
            role = request.POST.get(
                key='role',
                default='student',
            )
            Profile.objects.create(
                user=user,
                role=role,
            )
            messages.success(
                request,
                message=f'Account created for {user.username}',
            )
            return redirect('login')

        return render(
            request,
            self.template_name,
            context={'form': form},
        )


class CustomLoginView(LoginView):
    """Кастомное представление для аутентификации пользователей.

    Расширяет стандартное LoginView Django, добавляя функциональность
    "запомнить меня" для управления длительностью сессии.

    Attributes:
        form_class (Form): Класс формы для аутентификации.
    """
    form_class = LoginForm

    def form_valid(self, form):
        """Обрабатывает валидную форму аутентификации.

        Настраивает время жизни сессии в зависимости от выбора
        опции "запомнить меня" в форме.

        Args:
            form (AuthenticationForm): Валидная форма аутентификации.

        Returns:
            HttpResponse: Результат выполнения родительского метода form_valid.
        """
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        return super(CustomLoginView, self).form_valid(form)


@login_required
def view_profile(request):
    """Отображает профиль текущего аутентифицированного пользователя.

    Args:
        request (HttpRequest): Входящий HTTP-запрос.

    Returns:
        HttpResponse: Рендеринг страницы профиля с данными пользователя.
    """
    return render(
        request,
        template_name='registration/profile.html',
        context={'user': request.user},
    )


@login_required
def edit_profile(request):
    """Обрабатывает редактирование профиля пользователя.

    Поддерживает как GET (отображение формы) так и POST (обработка данных)
    запросы для обновления данных пользователя и его профиля.

    Args:
        request (HttpRequest): Входящий HTTP-запрос.

    Returns:
        HttpResponse: При GET - форма редактирования, при успешном POST -
                     перенаправление на просмотр профиля с сообщением об успехе.
    """
    if request.method == 'POST':
        user_form = UpdateUserForm(
            request.POST,
            instance=request.user,
        )
        profile_form = UpdateProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(
                request,
                message='Your profile is updated successfully',
            )
            return redirect(to='view-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(
        request,
        template_name='registration/edit_profile.html',
        context={'user_form': user_form, 'profile_form': profile_form},
    )


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    """Представление для изменения пароля пользователя.

    Наследуется от стандартного PasswordChangeView Django с добавлением
    функциональности отображения сообщений об успехе через SuccessMessageMixin.

    Attributes:
        template_name (str): Путь к шаблону страницы изменения пароля.
        success_message (str): Сообщение об успешном изменении пароля.
        success_url (str): URL для перенаправления после успешного изменения.
    """
    template_name = 'registration/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-profile')
