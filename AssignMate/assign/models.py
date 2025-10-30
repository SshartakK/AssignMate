
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

from taggit.managers import TaggableManager


def upload_to(instance, filename):
    return f'homework_pdfs/{instance.slug}/{filename}'

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=Homework.Status.PUBLISHED,
        )

class Course(models.Model):
    class Status(models.TextChoices):
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
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def str(self):
        return f'Created by {self.creator}'

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    def __str__(self):
        return f'{self.student.username} enrolled in {self.course.title}'


class Homework(models.Model):

    class Status(models.TextChoices):
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
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                self.title,
                allow_unicode=True,
            )
        super(Homework, self).save(*args, **kwargs)

    def get_absolute_url(self):
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
        return self.title


class Comment(models.Model):
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
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.homework}'


class HomeworkSolution(models.Model):
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
        return f"{self.homework.title} - {self.student.username}"


