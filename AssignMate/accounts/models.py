"""Модуль моделей для БД приложения accounts."""

from django.db import models
from django.contrib.auth.models import User

from PIL import Image

__all__ = [
    'Profile',
]


class Profile(models.Model):
    """Модель профиля пользователя для расширения стандартной модели User.

    Содержит дополнительную информацию о пользователе: аватар, биографию и роль.
    Автоматически обрабатывает загружаемые изображения для оптимизации размера.

    Attributes:
        ROLE_CHOICES (list): Варианты выбора ролей пользователя
        user (OneToOneField): Связь один-к-одному с моделью User
        avatar (ImageField): Аватар пользователя со стандартным значением
        bio (TextField): Биография пользователя (опционально)
        role (CharField): Роль пользователя в системе
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        unique=True,
    )

    avatar = models.ImageField(
        default='default.jpg',
        upload_to='profile_images'
    )
    bio = models.TextField(
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
    )

    def save(self, *args, **kwargs):
        """Сохраняет объект профиля и обрабатывает изображение аватара.

        Переопределяет стандартный метод save для автоматической обработки
        загружаемых изображений. Изменяет размер аватара до 100x100 пикселей
        для оптимизации хранения и загрузки.
        """
        super().save(*args, **kwargs)

        img = Image.open(self.avatar.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.avatar.path)

    def __str__(self):
        """Строковое представление объекта профиля.

        Returns:
            str: Имя пользователя связанного объекта User.
        """
        return self.user.username