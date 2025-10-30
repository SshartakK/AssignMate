from django.contrib import admin
from .models import Homework, Comment, Enrollment
from .models import HomeworkSolution, Course

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'slug', 'author', 'publish', 'status']
    list_filter = ['status', 'created', 'publish', 'author'] #фильтрация в боковой панели
    search_fields = ['title', 'body'] #поля, по которым можно осуществить поиск
    prepopulated_fields = {'slug': ('title',)} #slug = title
    raw_id_fields = ['author'] #поле author отображается поисковым виджетом
    autocomplete_fields = ['author'] #критерий сортировки по статусу
    date_hierarchy = 'publish' #навигация по иерархии дат
    ordering = ['status', 'publish']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'homework', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']

@admin.register(HomeworkSolution)
class HomeworkSolutionAdmin(admin.ModelAdmin):
    list_display = ['homework', 'student', 'created', 'updated']
    list_filter = ['created', 'updated', 'student']
    search_fields = ['answer_text', 'homework__title']

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1  # Устанавливает количество форм для новых записей
    autocomplete_fields = ['student']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'publish', 'status']
    list_filter = ['status', 'publish', 'creator']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EnrollmentInline]