from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Unit, Topic, Lesson, DmojExercise

class UserForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)
    dmoj_username = forms.CharField(required=False, help_text="Required for students only")

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role', 'dmoj_username']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        dmoj_username = cleaned_data.get('dmoj_username')

        if role == 'student' and not dmoj_username:
            self.add_error('dmoj_username', "DMOJ username is required for students.")

        if role != 'student':
            # Prevent teachers from setting a DMOJ username
            cleaned_data['dmoj_username'] = None

        return cleaned_data


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
        fields = ["title", "description"]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter unit title'}),
            'description': forms.TextInput(attrs={'placeholder': 'Enter description'}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter topic title'}),
            'description': forms.TextInput(attrs={'placeholder': 'Enter description'}),
        }


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

class DmojForm(forms.ModelForm):
    class Meta:
        model = DmojExercise
        fields = ["url"]
        widgets = {
            'url': forms.URLInput(attrs={
                'placeholder': 'https://dmoj.ca/problem/ccc07j3',
                'style': 'width:100%; padding:8px;'
            })
        }