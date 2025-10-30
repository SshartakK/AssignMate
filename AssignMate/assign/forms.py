from django import forms
from .models import Comment, Homework, Course, HomeworkSolution
from taggit.forms import TagField

class EmailHomeworkForm(forms.Form):
    name = forms.CharField(max_length=25)
    to = forms.EmailField()
    comments = forms.CharField(required=False,
                               widget=forms.Textarea)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'body']

class HomeworkForm(forms.ModelForm):
    tags = TagField(required=False)

    class Meta:
        model = Homework
        fields = ['title', 'body', 'pdf', 'course', 'tags']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(creator=user)

class HomeworkReviewForm(forms.ModelForm):
    class Meta:
        model = HomeworkSolution
        fields = ['grade', 'teacher_comment']
        widgets = {
            'teacher_comment': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'grade': forms.NumberInput(attrs={'min': 0, 'max': 100})
        }