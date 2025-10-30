
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.http import Http404
from django.contrib import messages

from taggit.models import Tag

from .models import Homework, HomeworkSolution, Course, Enrollment
from .forms import HomeworkForm
from .forms import EmailHomeworkForm, CommentForm, HomeworkReviewForm
from AssignMate import settings


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

    return render(
        request,
        template_name='assign/course/list.html',
        context={'courses': courses},
    )


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
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
    paginator = Paginator(homework_list, 3)
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
def homework_detail(request, year, month, day, homework_slug):
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

def homework_share(request, homework_id):
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
def homework_comment(request, homework_id):

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
def submit_solution(request, homework_id):

    homework = get_object_or_404(
        Homework,
        id=homework_id,
        status=Homework.Status.PUBLISHED,
    )

    if not is_student(request.user):
        return redirect('')

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        answer_pdf = request.FILES.get('answer_pdf', None)

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
def delete_solution(request, solution_id):
    solution = get_object_or_404(
        HomeworkSolution,
        id=solution_id,
        student=request.user,
    )

    if request.method == 'POST':
        solution.delete()
        return redirect('assign:homework_list')
    else:
        return render(
            request,
            template_name='assign/homework/confirm_delete.html',
            context={
                'solution': solution,
                'homework': solution.homework,
            },
        )


@login_required
def add_homework(request):
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
def delete_homework(request, homework_id):
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
def review_homework(request, solution_id):
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
