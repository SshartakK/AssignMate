"""Модели для приложения assign."""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

from taggit.managers import TaggableManager

__all__ = [
    'Course',
    'Enrollment',
    'Homework',
    'Comment',
    'HomeworkSolution',
    'PublishedManager',
    'upload_to',
]


def upload_to(instance, filename):
    """Функция для загрузки файлов домашних заданий."""
    return f'homework_pdfs/{instance.slug}/{filename}'


class PublishedManager(models.Manager):
    """Менеджер моделей для фильтрации опубликованных ДЗ."""

    def get_queryset(self):
        """Расширяет get_queryset фильтром."""
        return super().get_queryset().filter(
            status=Homework.Status.PUBLISHED,
        )


class Course(models.Model):
    """Модель представляет учебный курс в системе.

    Содержит информацию о названии курса, создателе, статусе публикации
    и временных метках. Курсы могут быть в черновике или опубликованы.
    """
    class Status(models.TextChoices):
        """Класс перечисления для статусов курса.

        Определяет возможные состояния курса в системе.
        """
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=250,
        unique_for_month="publish",
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_courses',
        limit_choices_to={'profile__role': 'teacher'},
        null=True,
        blank=True,
    )
    publish = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        """Мета-класс для дополнительных настроек модели.

        Определяет порядок сортировки и индексы базы данных
        для оптимизации запросов.
        """
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта курса.

        Returns:
            str: Название курса
        """
        return self.title


class Enrollment(models.Model):
    """Модель представляет запись о зачислении студента на курс.

    Служит промежуточной моделью для связи многие-ко-многим между
    пользователями (студентами) и курсами. Хранит информацию о том,
    какие студенты на какие курсы записаны.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )

    def __str__(self):
        """Возвращает строковое представление объекта зачисления.

        Returns:
            str: Строка в формате '{username} enrolled in {course_title}'
        """
        return f'{self.student.username} enrolled in {self.course.title}'


class Homework(models.Model):
    """Модель представляет домашнее задание в системе обучения.

    Содержит информацию о задании, включая название, описание, прикрепленные файлы,
    связь с курсом и автором, статус публикации и теги для организации.
    """

    class Status(models.TextChoices):
        """Класс перечисления для статусов домашнего задания.

        Определяет возможные состояния видимости задания в системе.
        """
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=250,
        unique_for_date='publish',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'profile__role': 'teacher'},
        related_name='assign_homeworks',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='homeworks',
    )
    body = models.TextField()
    pdf = models.FileField(
        upload_to=upload_to,
        null=True,
        blank=True,
    )

    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.PUBLISHED,
    )
    tags = TaggableManager()

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        """Мета-класс для дополнительных настроек модели.

        Определяет порядок сортировки и индексы базы данных.
        """
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения объекта.

        Автоматически генерирует slug из названия, если он не указан.
        Использует slugify с поддержкой Unicode символов.
       """
        if not self.slug:
            self.slug = slugify(
                self.title,
                allow_unicode=True,
            )
        super(Homework, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Возвращает абсолютный URL для доступа к детальной странице задания.

        Используется в шаблонах, админ-панели и для перенаправлений.
        Создает URL на основе даты публикации и slug.

        Returns:
            str: Абсолютный URL вида /assign/2023/12/25/slug-homework/
        """
        return reverse(
            viewname='assign:homework_detail',
            args=[
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug,
            ],
        )

    def __str__(self):
        """Возвращает строковое представление объекта задания.

        Returns:
            str: Название домашнего задания
        """
        return self.title


class Comment(models.Model):
    """Модель представляет комментарий к домашнему заданию.

    Позволяет пользователям оставлять комментарии и обсуждения
    к конкретным домашним заданиям. Поддерживает модерацию через
    поле active для скрытия неподходящих комментариев.
    """
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        """Мета-класс для дополнительных настроек модели Comment.

        Определяет порядок сортировки и индексы базы данных
        для оптимизации производительности.
        """
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта комментария.

        Returns:
            str: Строка в формате 'Comment by {author_name} on {homework_title}'
        """
        return f'Comment by {self.name} on {self.homework}'


class HomeworkSolution(models.Model):
    """Модель представляет решение домашнего задания, отправленное студентом.

    Содержит ответ студента на домашнее задание, который может включать
    текстовый ответ и/или прикрепленный файл. Также хранит оценку и
    комментарий преподавателя после проверки работы.
    """
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='solutions',
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='homework_solutions',
    )

    answer_text = models.TextField()
    answer_pdf = models.FileField(
        upload_to='homework_solutions/',
        null=True,
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    grade = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    teacher_comment = models.TextField(
        null=True,
        blank=True,
    )

    def __str__(self):
        """Возвращает строковое представление объекта решения.

        Returns:
            str: Строка в формате '{homework_title} - {student_username}'
        """
        return f"{self.homework.title} - {self.student.username}"


