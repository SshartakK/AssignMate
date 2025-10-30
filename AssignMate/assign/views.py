"""Модуль представлений приложения assign."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.http import Http404, HttpRequest, HttpResponse
from django.contrib import messages

from taggit.models import Tag
from typing import Optional

from .models import Homework, HomeworkSolution, Course, Enrollment
from .forms import HomeworkForm
from .forms import EmailHomeworkForm, CommentForm, HomeworkReviewForm
from AssignMate import settings

__all__ = [
    'is_student',
    'is_teacher',
    'courses_list',
    'course_detail',
    'homework_list',
    'homework_detail',
    'homework_share',
    'homework_comment',
    'add_homework',
    'submit_solution',
    'delete_solution',
    'review_homework',
    'delete_homework',
]

def is_student(user) -> bool:
    """Проверяет, является ли пользователь студентом на основе его профиля.

    Args:
        user: Объект пользователя для проверки

    Returns:
        bool: True если пользователь существует, имеет профиль и роль 'student',
              False в противном случае
    """
    return hasattr(user, 'profile') and user.profile.role == 'student'


def is_teacher(user) -> bool:
    """Проверяет, является ли пользователь преподавателем на основе его профиля.

    Args:
        user: Объект пользователя для проверки

    Returns:
        bool: True если пользователь существует, имеет профиль и роль 'teacher',
              False в противном случае
    """
    return hasattr(user, 'profile') and user.profile.role == 'teacher'


@login_required
def courses_list(request: HttpRequest) -> HttpResponse:
    """Представление для отображения списка курсов пользователя.

    Возвращает разные наборы курсов в зависимости от роли пользователя:
    - Для преподавателей: курсы, которые они создали
    - Для студентов: курсы, на которые они записаны

    Args:
        request: Запрос, содержащий информацию о пользователе

    Returns:
        HttpResponse: Отрендеренный шаблон со списком курсов
    """
    if is_teacher(request.user):
        courses = Course.objects.filter(creator=request.user)
    else:
        courses = Course.objects.filter(enrollments__student=request.user)

    return render(
        request,
        template_name='assign/course/list.html',
        context={'courses': courses},
    )


@login_required
def course_detail(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """Представление для отображения детальной информации о курсе и его домашних заданиях.

    Показывает подробную информацию о конкретном курсе и список всех домашних заданий,
    связанных с этим курсом. Осуществляет проверку прав доступа - курс могут просматривать
    только его создатель (преподаватель) или записанные на курс студенты.

    Args:
        request: Запрос, содержащий метаданные и данные пользователя
        pk: Первичный ключ (ID) курса для отображения

    Returns:
        HttpResponse: Отрендеренный шаблон с детальной информацией о курсе и списком заданий

    Raises:
        Http404: Если курс не существует или у пользователя нет прав для его просмотра
    """
    course = get_object_or_404(
        Course,
        pk=pk,
    )
    if not (course.creator == request.user or Enrollment.objects.filter(
        course=course,
        student=request.user,
    ).exists()):
        raise Http404("You do not have permission to view this course.")
    homeworks = course.homeworks.all()

    return render(
        request,
        template_name='assign/course/detail.html',
        context={
            'course': course,
            'homeworks': homeworks
        },
    )


def homework_list(
    request: HttpRequest,
    tag_slug: Optional[str] = None,
) -> HttpResponse:
    """Представление для отображения списка домашних заданий с пагинацией и фильтрацией по тегам.

    Возвращает разные наборы домашних заданий в зависимости от роли пользователя:
    - Для преподавателей: все задания, которые они создали
    - Для студентов: задания только с курсов, на которые они записаны

    Поддерживает фильтрацию по тегам и пагинацию результатов.

    Args:
        request: Объект HTTP запроса Django
        tag_slug: Необязательный slug тега для фильтрации заданий. Defaults to None.

    Returns:
        HttpResponse: Отрендеренный шаблон со списком домашних заданий
    """
    if is_teacher(request.user):
        homework_list = Homework.objects.filter(author=request.user)
    else:
        enrolled_courses = Course.objects.filter(enrollments__student=request.user)
        homework_list = Homework.objects.filter(course__in=enrolled_courses)

    tag = None
    if tag_slug:
        tag = get_object_or_404(
            Tag,
            slug=tag_slug,
        )
        homework_list = homework_list.filter(tags__in=[tag])

    paginator = Paginator(
        homework_list,
        per_page=3,
    )
    page_number = request.GET.get('page')
    try:
        homeworks = paginator.page(page_number)
    except PageNotAnInteger:
        homeworks = paginator.page(1)
    except EmptyPage:
        homeworks = paginator.page(paginator.num_pages)

    return render(
        request,
        template_name='assign/homework/list.html',
        context={
            'page': page_number,
            'homeworks': homeworks,
            'tag': tag,
        },
    )


@login_required
def homework_detail(
    request: HttpRequest,
    year: int,
    month: int,
    day: int,
    homework_slug: str
) -> HttpResponse:
    """Представление для отображения детальной страницы домашнего задания.

    Показывает полную информацию о домашнем задании, включая описание,
    прикрепленные файлы, комментарии и решения. Осуществляет проверку прав доступа -
    задание могут просматривать только создатель курса (преподаватель) или
    записанные на курс студенты.

    Args:
        request: Объект HTTP запроса
        year: Год публикации задания
        month: Месяц публикации задания
        day: День публикации задания
        homework_slug: Уникальный идентификатор задания

    Returns:
        HttpResponse: Отрендеренный шаблон с детальной информацией о задании

    Raises:
        Http404: Если задание не существует или у пользователя нет прав для просмотра
    """
    homework = get_object_or_404(
        Homework,
        slug=homework_slug,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    if not (homework.course.creator == request.user or Enrollment.objects.filter(
        course=homework.course,
        student=request.user
    ).exists()):
        raise Http404("You do not have permission to view this homework.")

    if is_teacher(request.user):
        solutions = homework.solutions.all()
    else:
        solutions = homework.solutions.filter(student=request.user)

    can_submit_solution = is_student(request.user) and not solutions.exists()
    comments = homework.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.homework = homework
            new_comment.save()
    else:
        comment_form = CommentForm()

    return render(
        request,
        template_name='assign/homework/detail.html',
        context={
            'homework': homework,
            'comments': comments,
            'new_comment': new_comment,
            'comment_form': comment_form,
            'can_submit_solution': can_submit_solution,
            'solutions': solutions,
            'is_teacher': is_teacher(request.user),
        },
    )


def homework_share(
    request: HttpRequest,
    homework_id: int,
) -> HttpResponse:
    """Представление для отправки домашнего задания по электронной почте.

    Позволяет пользователям делиться домашними заданиями с другими людьми
    через email. Генерирует email с ссылкой на задание и дополнительными
    комментариями от отправителя.

    Args:
        request: Объект HTTP запроса
        homework_id: ID домашнего задания для отправки

    Returns:
        HttpResponse: Отрендеренный шаблон с формой отправки email

    Raises:
        Http404: Если задание с указанным ID не существует или не опубликовано
    """
    homework = get_object_or_404(
        Homework,
        id=homework_id,
        status=Homework.Status.PUBLISHED,
    )
    sent = False

    if request.method == 'POST':
        form = EmailHomeworkForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            homework_url = request.build_absolute_url(
                homework.get_absolute_url(),
            )
            subject = f"{cd['name']} recommends you read " \
                      f"{homework.title}"
            message = f"Read {homework.title} at {homework_url}\n\n" \
                      f"{cd['name']}\'s ({cd['email']}) comments: {cd['comments']}"
            send_mail(subject, message, settings.EMAIL_HOST_USER,
                      [cd['to']])
            sent = True
    else:
        form = EmailHomeworkForm()

    return render(
        request,
        template_name='assign/homework/share.html',
        context={
            'homework': homework,
            'form': form,
            'sent': sent,
        },
    )


@require_POST
def homework_comment(
    request: HttpRequest,
    homework_id: int,
) -> HttpResponse:
    """Представление для обработки добавления комментариев к домашнему заданию.

    Обрабатывает только POST запросы для создания новых комментариев
    к опубликованным домашним заданиям. После успешного сохранения комментария
    возвращает частичный шаблон для AJAX обновления или отображения результата.

    Args:
        request: Объект HTTP запроса Django
        homework_id: ID домашнего задания для которого добавляется комментарий

    Returns:
        HttpResponse: Отрендеренный шаблон с результатом операции
    """
    homework = get_object_or_404(
        Homework,
        id=homework_id,
        status=Homework.Status.PUBLISHED,
    )
    comment = None
    form = CommentForm(data=request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.homework = homework
        comment.save()

    return render(
        request,
        template_name='assign/homework/comment.html',
        context={
            'homework': homework,
            'form': form,
            'comment': comment,
        },
    )


@login_required
def submit_solution(
    request: HttpRequest,
    homework_id: int,
) -> HttpResponse:
    """Представление для отправки решения домашнего задания студентом.

    Позволяет студентам отправлять текстовые решения и/или прикреплять PDF файлы
    к опубликованным домашним заданиям. Проверяет права доступа и валидирует
    данные перед сохранением решения.

    Args:
        request: Объект HTTP запроса
        homework_id: ID домашнего задания для которого отправляется решение

    Returns:
        HttpResponse:
            - При GET: Отрендеренный шаблон формы отправки решения
            - При POST: Перенаправление на страницу задания после успешной отправки
            - При нарушении прав: Перенаправление на главную страницу
    """
    homework = get_object_or_404(
        Homework,
        id=homework_id,
        status=Homework.Status.PUBLISHED,
    )

    if not is_student(request.user):
        return redirect('')

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        answer_pdf = request.FILES.get(
            key='answer_pdf',
            default=None,
        )
        solution = HomeworkSolution(
            homework=homework,
            student=request.user,
            answer_text=answer_text,
            answer_pdf=answer_pdf,
        )
        solution.save()

        return redirect(homework.get_absolute_url())

    return render(
        request,
        template_name='assign/homework/submit_solution.html',
        context={'homework': homework},
    )


@login_required
def delete_solution(
    request: HttpRequest,
    solution_id: int,
) -> HttpResponse:
    """Представление для удаления решения домашнего задания.

    Позволяет студентам удалять свои отправленные решения.

    Args:
        request: Объект HTTP запроса
        solution_id: ID решения домашнего задания для удаления

    Returns:
        HttpResponse:
            - При GET: Отрендеренный шаблон подтверждения удаления
            - При POST: Перенаправление на список домашних заданий после удаления
    """
    solution = get_object_or_404(
        HomeworkSolution,
        id=solution_id,
        student=request.user,
    )

    if request.method == 'POST':
        solution.delete()
        return redirect('assign:homework_list')

    return render(
        request,
        template_name='assign/homework/confirm_delete.html',
        context={
            'solution': solution,
            'homework': solution.homework,
        },
    )


@login_required
def add_homework(request: HttpRequest) -> HttpResponse:
    """Представление для создания нового домашнего задания.

    Позволяет преподавателям создавать новые домашние задания через веб-интерфейс.
    Обрабатывает как GET запросы (отображение пустой формы), так и POST запросы
    (обработка отправленной формы). Включает валидацию данных, обработку файлов
    и систему уведомлений для пользователя.

    Args:
        request: Объект HTTP запроса

    Returns:
        HttpResponse:
            - При GET: Отрендеренный шаблон формы создания задания
            - При POST: Перенаправление на детальную страницу задания при успехе
            - При ошибках: Повторное отображение формы с сообщениями об ошибках
    """
    if request.method == 'POST':
        form = HomeworkForm(
            data=request.POST,
            files=request.FILES,
            user=request.user,
        )

        if form.is_valid():
            new_homework = form.save(commit=False)
            new_homework.author = request.user
            new_homework.save()
            form.save_m2m()
            messages.success(
                request,
                message='Homework was added successfully!',
            )
            return redirect(new_homework.get_absolute_url())
        else:
            messages.error(
                request,
                message='Please correct the error below.',
            )
    else:
        form = HomeworkForm(user=request.user)

    return render(
        request,
        template_name='assign/homework/add_homework.html',
        context={'form': form},
    )


@login_required
def delete_homework(
    request: HttpRequest,
    homework_id: int,
) -> HttpResponse:
    """Представление для удаления домашнего задания.

    Позволяет создателю курса или суперпользователю удалять домашние задания.
    Реализует проверку прав доступа и двухэтапный процесс удаления через POST запрос.
    После успешного удаления перенаправляет на страницу курса с сообщением об успехе.

    Args:
        request: Объект HTTP запроса
        homework_id: ID домашнего задания для удаления

    Returns:
        HttpResponse:
            - При POST с правами: Перенаправление на страницу курса с сообщением об успехе
            - При POST без прав: Перенаправление на страницу курса с сообщением об ошибке
            - При GET: Перенаправление на страницу курса без выполнения удаления
    """
    homework = get_object_or_404(
        Homework,
        id=homework_id,
        course__creator=request.user,
    )
    course_id = homework.course.id

    if request.method == 'POST':
        if homework.author == request.user or request.user.is_superuser:
            homework.delete()
            messages.success(
                request,
                message='Homework deleted successfully.',
            )
            return redirect(
                to='assign:course_detail',
                pk=course_id,
            )
        else:
            messages.error(
                request,
                message='You do not have permission to delete this homework.',
            )

    return redirect(
        to='assign:course_detail',
        pk=course_id,
    )


@login_required
def review_homework(
    request: HttpRequest,
    solution_id: int,
) -> HttpResponse:
    """Представление для проверки и оценки решения домашнего задания преподавателем.

    Позволяет преподавателям просматривать решения студентов, выставлять оценки
    и оставлять комментарии. Обеспечивает проверку прав доступа - только создатель курса
    может проверять решения заданий своего курса.

    Args:
        request: Объект HTTP запроса
        solution_id: ID решения домашнего задания для проверки

    Returns:
        HttpResponse:
            - При GET: Отрендеренный шаблон формы оценки решения
            - При POST: Перенаправление на страницу задания после успешной оценки

    Raises:
        Http404: Если решение не существует или пользователь не является создателем курса
        Http404: Если пользователь не имеет роли преподавателя
    """
    solution = get_object_or_404(
        HomeworkSolution,
        pk=solution_id,
        homework__course__creator=request.user,
    )

    if not is_teacher(request.user):
        raise Http404("You do not have permission to review this solution.")

    if request.method == 'POST':
        form = HomeworkReviewForm(request.POST, instance=solution)
        if form.is_valid():
            form.save()
            return redirect(
                to='assign:homework_detail',
                year=solution.homework.publish.year,
                month=solution.homework.publish.month,
                day=solution.homework.publish.day,
                homework_slug=solution.homework.slug,
            )
    else:
        form = HomeworkReviewForm(instance=solution)

    return render(
        request,
        template_name='assign/homework/homework_review.html',
        context={'form': form},
    )
