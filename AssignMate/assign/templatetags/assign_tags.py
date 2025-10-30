from django import template
from ..models import Homework, Course
from django.utils.safestring import mark_safe
import markdown


register = template.Library()


@register.simple_tag
def total_homeworks():
    return Homework.published.count()

@register.inclusion_tag('assign/homework/latest_homeworks.html', takes_context=True)
def show_latest_homeworks(context, count=5):
    request = context['request']
    if request.user.is_authenticated:
        enrolled_courses = Course.objects.filter(enrollments__student=request.user)
        latest_homeworks = Homework.published.filter(course__in=enrolled_courses).order_by('-publish')[:count]
    else:
        latest_homeworks = Homework.published.none()  # Не возвращает домашние задания для анонимных пользователей
    return {'latest_homeworks': latest_homeworks}

@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))