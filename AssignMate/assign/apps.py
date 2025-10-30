"""Модуль конфигурации приложения assign."""

from django.apps import AppConfig

__all__ = [
    'AssignConfig',
]


class AssignConfig(AppConfig):
    """Класс конфигурации приложения assign."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assign'
