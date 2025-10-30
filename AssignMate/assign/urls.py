from django.urls import path
from . import views
from .views import add_homework
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

app_name = 'assign'

urlpatterns = [
    path('AssignMate_icon.png', RedirectView.as_view(url=staticfiles_storage.url('images/AssignMate_icon.png'))),

    path('', views.courses_list,
         name='courses_list'),  # Список всех домашних заданий, доступных пользователю

    path('courses/<int:pk>/',
         views.course_detail, name='course_detail'),

    path('tag/<str:tag_slug>/',
         views.homework_list, name='homework_list_by_tag'),  # Фильтрация домашних заданий по тегу

    path('<int:year>/<int:month>/<int:day>/<str:homework_slug>/',
         views.homework_detail,
         name='homework_detail'),

    path('<int:homework_id>/share/',
         views.homework_share, name='homework_share'),  # Поделиться домашним заданием

    path('<int:homework_id>/comment/',
         views.homework_comment, name='homework_comment'),  # Комментирование домашнего задания

    path('<int:homework_id>/submit/',
         views.submit_solution, name='submit_solution'),  # Отправка решения по домашнему заданию

    path('solution/delete/<int:solution_id>/',
         views.delete_solution, name='delete_solution'),  # Удаление решения домашнего задания

    path('add_homework/',
         add_homework, name='add_homework'),

    path('homeworks/', views.homework_list, name='homework_list'),

    path('homework/<int:homework_id>/delete/',
         views.delete_homework, name='delete_homework'),

    path('homework/<int:solution_id>/review/',
         views.review_homework, name='review_homework'),
]
