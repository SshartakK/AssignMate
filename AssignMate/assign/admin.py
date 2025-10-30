"""Модуль регистрации админ-моделей."""

from django.contrib import admin

from .models import Homework, Comment, Enrollment
from .models import HomeworkSolution, Course

__all__ = [
    'HomeworkAdmin',
    'CommentAdmin',
    'EnrollmentInline',
    'CourseAdmin',
    'HomeworkSolutionAdmin',
]

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    """Класс регистрации модели Homework в админ-панели.

     Класс отображает поля: title, course, slug, author,
     publish, status.
     """
    list_display = ['title', 'course', 'slug', 'author', 'publish', 'status']
    list_filter = ['status', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    autocomplete_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Класс регистрации модели Comment в админ-панели.

     Класс отображает поля: name, email, homework,
     created, active.
     """
    list_display = ['name', 'email', 'homework', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']


@admin.register(HomeworkSolution)
class HomeworkSolutionAdmin(admin.ModelAdmin):
    """Класс регистрации модели HomeworkSolution в админ-панели.

     Класс отображает поля: homework, student, created,
     updated.
     """
    list_display = ['homework', 'student', 'created', 'updated']
    list_filter = ['created', 'updated', 'student']
    search_fields = ['answer_text', 'homework__title']


class EnrollmentInline(admin.TabularInline):
    """Класс создает inline-форму для модели Enrollment.

    Класс добавляет 1 пустую форму для создания новых записей и
    автодополнение для поля student.
    """
    model = Enrollment
    extra = 1
    autocomplete_fields = ['student']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Класс регистрации модели CourseAdmin в админ-панели.

    Класс отображает поля: title, creator, publish,
    status.
    """
    list_display = ['title', 'creator', 'publish', 'status']
    list_filter = ['status', 'publish', 'creator']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EnrollmentInline]