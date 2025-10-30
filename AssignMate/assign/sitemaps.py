"""Модуль с картами сайта."""

from django.contrib.sitemaps import Sitemap

from .models import Homework

__all__ = [
    'HomeworkSitemap',
]


class HomeworkSitemap(Sitemap):
    """Карта сайта для опубликованных домашних заданий."""
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        """Возвращает QuerySet объектов для включения в карту сайта.

        Метод определяет какие объекты будут представлены в sitemap.xml.
        Использует кастомный менеджер 'published' для получения только
        опубликованных домашних заданий.

        Returns:
            QuerySet: QuerySet домашних заданий со статусом PUBLISHED
        """
        return Homework.published.all()

    def lastmod(self, obj):
        """Возвращает дату последнего изменения объекта домашнего задания.

        Метод вызывается для каждого объекта в items() и возвращает
        время последнего обновления, которое сообщает поисковым системам
        когда контент был изменен в последний раз.

        Args:
            obj: Объект домашнего задания из QuerySet items()

        Returns:
            datetime: Дата и время последнего обновления домашнего задания
        """
        return obj.updated