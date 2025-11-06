"""Модуль приложения."""

from django.apps import AppConfig

__all__ = [
    'AccountsConfig',
]


class AccountsConfig(AppConfig):
    """Конфигурация приложения accounts.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых
            первичных ключей.
        name (str): Имя приложения в формате Python пути.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """Инициализация приложения после загрузки."""
        import accounts.signals