"""Модуль с тегами приложения assign."""

from django import template
from django.utils.safestring import mark_safe

import markdown

from assign.models import Homework, Course

__all__ = [
    'total_homeworks',
    'show_latest_homeworks',
    'markdown_format',
]

register = template.Library()


@register.simple_tag
def total_homeworks() -> int:
    return Homework.published.count()


@register.inclusion_tag(
    filename='assign/homework/latest_homeworks.html',
    takes_context=True,
)
def show_latest_homeworks(
    context,
    count: int = 5,
) -> dict:
    request = context['request']
    if request.user.is_authenticated:
        enrolled_courses = Course.objects.filter(
            enrollments__student=request.user
        )
        latest_homeworks = Homework.published.filter(
            course__in=enrolled_courses
        ).order_by('-publish')[:count]
    else:
        latest_homeworks = Homework.published.none()
    return {'latest_homeworks': latest_homeworks}


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))