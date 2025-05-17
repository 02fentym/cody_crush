from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Unit, Topic, Lesson, DmojExercise, Profile, CourseUnit, CourseTopic


class UserForm(UserCreationForm):
    dmoj_username = forms.CharField(
        required=True,
        widget=forms.TextInput()
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'dmoj_username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply daisyUI/Tailwind classes
        self.fields['username'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Confirm Password'
        })
        self.fields['dmoj_username'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'DMOJ username'
        })

        # Remove verbose help text from Django's defaults
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean(self):
        cleaned_data = super().clean()
        dmoj_username = cleaned_data.get('dmoj_username')

        if not dmoj_username:
            self.add_error('dmoj_username', "DMOJ username is required.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        user.save()  # save user to get a valid user.id

        # Create and attach the profile manually
        Profile.objects.create(
            user=user,
            role='student',
            dmoj_username=self.cleaned_data['dmoj_username']
        )

        return user



class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "language", "enrollment_password"]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Course title...',
                'class': 'input input-bordered w-full'
            }),
            'language': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'enrollment_password': forms.TextInput(attrs={
                'placeholder': 'Enrollment password...',
                'class': 'input input-bordered w-full'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Brief description...',
                'class': 'textarea textarea-bordered w-full',
                'rows': 1
            }),
        }


class UnitForm(ModelForm):
    class Meta:
        model = Unit
        fields = ["title", "description"]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Unit title...',
                'class': 'input input-bordered w-full'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Brief description...',
                'class': 'textarea textarea-bordered w-full',
                'rows': 1
            }),
        }

class CourseUnitForm(forms.ModelForm):
    class Meta:
        model = CourseUnit
        fields = ["unit"]
        widgets = {
            "unit": forms.Select(attrs={"class": "select select-bordered w-full"})
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Topic title...',
                'class': 'input input-bordered w-full'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Brief description...',
                'class': 'textarea textarea-bordered w-full',
                'rows': 1
            }),
        }

class CourseTopicForm(forms.ModelForm):
    class Meta:
        model = CourseTopic
        fields = ["topic"]
        widgets = {
            "topic": forms.Select(attrs={"class": "select select-bordered w-full"})
        }


# This is a form to update the enrollment password
class EnrollmentPasswordForm(forms.Form):
    password = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "placeholder": "Enter course password",
            "class": "input input-bordered w-full"
        })
    )


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "content"]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Lesson title...',
                'class': 'input-field'
            }),
            'content': forms.Textarea(attrs={  # technically not used since replaced by JS
                'class': 'input-field',
                'rows': 1
            })
        }

class DmojForm(forms.ModelForm):
    class Meta:
        model = DmojExercise
        fields = ["url"]
        widgets = {
            "url": forms.URLInput(attrs={
                "placeholder": "https://dmoj.ca/problem/ccc07j3",
                "class": "input input-bordered w-full"
            })
        }