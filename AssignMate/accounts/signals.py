"""Модуль сигналов для приложения accounts."""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Profile

__all__ = [
    'create_profile',
]


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Обработчик сигнала post_save для модели User.

    Автоматически создает объект Profile при создании нового пользователя.
    Обеспечивает согласованность данных и обязательное наличие профиля
    для каждого пользователя в системе.

    Args:
        sender (Model): Класс модели, отправившей сигнал (User)
        instance (User): Конкретный экземпляр модели, который был сохранен
        created (bool): Флаг, указывающий был ли объект создан (True)
                        или обновлен (False)
        **kwargs: Дополнительные аргументы сигнала
    """
    if created:
        Profile.objects.create(user=instance)
