"""Модуль с формами для приложения assign"""

from django import forms
from taggit.forms import TagField

from .models import Comment, Homework, Course, HomeworkSolution

__all__ = [
    'EmailHomeworkForm',
    'CommentForm',
    'HomeworkForm',
    'HomeworkReviewForm',
]

class EmailHomeworkForm(forms.Form):
    """Класс создает форму для email-рассылки ДЗ.

    Класс создает форму с полями:
        name - имя отправителя,
        to - адрес получателя,
        comments - комментарии.
    """
    name = forms.CharField(max_length=25)
    to = forms.EmailField()
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )


class CommentForm(forms.ModelForm):
    """Класс создает форму для добавления комментариев."""

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью Comment
        по полям name и body.
        """
        model = Comment
        fields = ['name', 'body']


class HomeworkForm(forms.ModelForm):
    """Класс создает форму для модели Homework с дополнительной логикой."""
    tags = TagField(required=False)

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью Homework
        по полям title, body, pdf, course и tags.
        """
        model = Homework
        fields = ['title', 'body', 'pdf', 'course', 'tags']

    def __init__(self, *args, **kwargs):
        """Инициализация класса с извлечением user."""
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(creator=user)


class HomeworkReviewForm(forms.ModelForm):
    """Класс создает форму для оценки и комментирования решений ДЗ преподавателем."""

    class Meta:
        """Класс конфигурации для связи формы и модели.

        Конфигурация связывает эту форму с моделью HomeworkSolution
        по полям grade и teacher_comment. И кастомизирует виджеты
        """
        model = HomeworkSolution
        fields = ['grade', 'teacher_comment']
        widgets = {
            'teacher_comment': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'grade': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }