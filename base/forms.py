from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Unit, Topic, Lesson

class UserForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role']


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "language", "enrollment_password"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 1,
                "style": "padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;"
            }),
            # you can also set rows/style on title or password if you like
        }


class UnitForm(ModelForm):
    class Meta:
        model = Unit
        fields = ["title"]


class TopicForm(ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "description"]


# This is a form to update the enrollment password
class EnrollmentPasswordForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["enrollment_password"]
        widgets = {
            "enrollment_password": forms.TextInput(attrs={
                "placeholder": "Enter password",
                "style": "padding:4px 8px; border:1px solid #ccc; border-radius:4px;"
            }),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "id": "id_content",     # This is what Toast UI JS expects
                "style": "display:none;"  # Hide it from the user
            })
        }
