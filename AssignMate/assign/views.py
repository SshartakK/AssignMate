from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Homework, Comment, HomeworkSolution, Course, Enrollment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailHomeworkForm, CommentForm, HomeworkReviewForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.http import Http404
from AssignMate2 import settings
from .forms import HomeworkForm
from django.contrib import messages


def is_student(user):
    return hasattr(user, 'profile') and user.profile.role == 'student'


def is_teacher(user):
    return hasattr(user, 'profile') and user.profile.role == 'teacher'


@login_required
def courses_list(request):
    if is_teacher(request.user):
        courses = Course.objects.filter(creator=request.user)
    else:
        courses = Course.objects.filter(enrollments__student=request.user)

    return render(request, 'assign/course/list.html', {'courses': courses})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)  # использование pk как идентификатора для поиска курса
    if not (course.creator == request.user or Enrollment.objects.filter(course=course, student=request.user).exists()):
        raise Http404("You do not have permission to view this course.")
    homeworks = course.homeworks.all()
    return render(request, 'assign/course/detail.html', {'course': course, 'homeworks': homeworks})

def homework_list(request, tag_slug=None):
    if is_teacher(request.user):
        homework_list = Homework.objects.filter(author=request.user)
    else:
        enrolled_courses = Course.objects.filter(enrollments__student=request.user)
        homework_list = Homework.objects.filter(course__in=enrolled_courses)

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        homework_list = homework_list.filter(tags__in=[tag])
    paginator = Paginator(homework_list, 3)  # постраничная разбивка
    page_number = request.GET.get('page')
    try:
        homeworks = paginator.page(page_number)
    except PageNotAnInteger:
        homeworks = paginator.page(1)
    except EmptyPage:
        homeworks = paginator.page(paginator.num_pages)
    return render(request, 'assign/homework/list.html', {'page': page_number, 'homeworks': homeworks, 'tag': tag})


@login_required
def homework_detail(request, year, month, day, homework_slug):
    homework = get_object_or_404(Homework, slug=homework_slug,
                                 publish__year=year, publish__month=month, publish__day=day)
    if not (homework.course.creator == request.user or Enrollment.objects.filter(course=homework.course,
                                                                                 student=request.user).exists()):
        raise Http404("You do not have permission to view this homework.")

    # Используем функции для проверки роли пользователя

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


    return render(request, 'assign/homework/detail.html', {
        'homework': homework,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'can_submit_solution': can_submit_solution,
        'solutions': solutions,
        'is_teacher': is_teacher(request.user)  # передаем флаг в шаблон
    })

def homework_share(request, homework_id):
    # Извлечь пост по его идентификатору id
    homework = get_object_or_404(Homework,
                             id=homework_id,
                             status=Homework.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailHomeworkForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            homework_url = request.build_absolute_url(
                homework.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{homework.title}"
            message = f"Read {homework.title} at {homework_url}\n\n" \
                      f"{cd['name']}\'s ({cd['email']}) comments: {cd['comments']}"
            send_mail(subject, message, settings.EMAIL_HOST_USER,
                      [cd['to']])
            sent = True
    else:
        form = EmailHomeworkForm()
    return render(request, 'assign/homework/share.html', {'homework': homework,
                                                    'form': form,
                                                    'sent': sent})

@require_POST
def homework_comment(request, homework_id):
    homework = get_object_or_404(Homework,
                             id=homework_id,
                             status=Homework.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.homework = homework
        # Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'assign/homework/comment.html',
                  {'homework': homework,
                   'form': form,
                   'comment': comment})

@login_required
def submit_solution(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    if not is_student(request.user):
        return redirect('')  # или страница ошибки

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        answer_pdf = request.FILES.get('answer_pdf', None)

        solution = HomeworkSolution(homework=homework, student=request.user, answer_text=answer_text,
                                    answer_pdf=answer_pdf)
        solution.save()

        return redirect(homework.get_absolute_url())  # Редирект на страницу домашнего задания

    return render(request, 'assign/homework/submit_solution.html', {'homework': homework})

@login_required
def delete_solution(request, solution_id):
    solution = get_object_or_404(HomeworkSolution, id=solution_id, student=request.user)
    if request.method == 'POST':
        solution.delete()
        return redirect('assign:homework_list')  # Или другой URL, куда нужно перейти после удаления
    else:
        return render(request, 'assign/homework/confirm_delete.html', {
            'solution': solution,
            'homework': solution.homework  # Добавляем объект homework в контекст
        })


@login_required
def add_homework(request):
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_homework = form.save(commit=False)
            new_homework.author = request.user  # Установка автора
            new_homework.save()
            form.save_m2m()  # Сохранение связей многие-ко-многим, включая теги
            messages.success(request, 'Homework was added successfully!')
            return redirect(new_homework.get_absolute_url())
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = HomeworkForm(user=request.user)  # Передача пользователя в форму для инициализации

    return render(request, 'assign/homework/add_homework.html', {'form': form})

@login_required
def delete_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    course_id = homework.course.id  # сохраняем ID курса для редиректа

    if request.method == 'POST':
        if homework.author == request.user or request.user.is_superuser:
            homework.delete()
            messages.success(request, "Homework deleted successfully.")
            return redirect('assign:course_detail', pk=course_id)
        else:
            messages.error(request, "You do not have permission to delete this homework.")

    return redirect('assign:course_detail', pk=course_id)  # редирект обратно на страницу курса

@login_required
def review_homework(request, solution_id):
    solution = get_object_or_404(HomeworkSolution, pk=solution_id, homework__course__creator=request.user)

    if not is_teacher(request.user):
        raise Http404("You do not have permission to review this solution.")

    if request.method == 'POST':
        form = HomeworkReviewForm(request.POST, instance=solution)
        if form.is_valid():
            form.save()
            return redirect('assign:homework_detail', year=solution.homework.publish.year, month=solution.homework.publish.month, day=solution.homework.publish.day, homework_slug=solution.homework.slug)
    else:
        form = HomeworkReviewForm(instance=solution)

    return render(request, 'assign/homework/homework_review.html', {'form': form})
