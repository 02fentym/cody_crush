from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Unit, Topic, Lesson, DmojExercise, Profile, CourseUnit, CourseTopic, MultipleChoiceQuestion, TracingQuestion, CodeQuestion, CodeTestCase, CourseWeighting, FillInTheBlankQuestion


class UserForm(UserCreationForm):
    dmoj_username = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'dmoj_username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Username'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'First Name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Last Name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'input input-bordered w-full mb-4',
            'placeholder': 'Email Address'
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
            'placeholder': 'DMOJ Username'
        })

        # Clean up help texts
        for field in ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']:
            self.fields[field].help_text = ''

    def clean(self):
        cleaned_data = super().clean()

        dmoj_username = cleaned_data.get('dmoj_username')
        if not dmoj_username:
            self.add_error('dmoj_username', "DMOJ username is required.")

        email = cleaned_data.get('email')
        if not email:
            self.add_error('email', "Email is required.")
        elif User.objects.filter(email__iexact=email).exists():
            self.add_error('email', "A user with this email already exists.")

        return cleaned_data


    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

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
        fields = ['title', 'description', 'unit']
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
            'unit': forms.Select(attrs={
                'class': 'select select-bordered w-full'
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


class MultipleChoiceQuestionForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = [
            "language", "prompt", "choice_a", "choice_b", "choice_c", "choice_d",
            "correct_choice", "explanation"
        ]
        widgets = {
            "language": forms.Select(attrs={"class": "select select-sm select-bordered text-sm w-auto block"}),
            "prompt": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm", "rows": 1, "style": "overflow:hidden;", }),
            "choice_a": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "choice_b": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "choice_c": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "choice_d": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "correct_choice": forms.Select(attrs={"class": "select select-sm select-bordered text-sm w-auto block"}),
            "explanation": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
        }


class TracingQuestionForm(forms.ModelForm):
    class Meta:
        model = TracingQuestion
        fields = [
            "language", "prompt", "expected_output", "explanation",
        ]
        widgets = {
            "language": forms.Select(attrs={"class": "select select-sm select-bordered text-sm auto-resize block"}),
            "prompt": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "expected_output": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "explanation": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
        }


class CodeQuestionForm(forms.ModelForm):
    class Meta:
        model = CodeQuestion
        fields = [
            "title", "prompt", "starter_code", "language", "explanation", "question_type"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-sm input-bordered text-sm block"}),
            "prompt": forms.Textarea(attrs={"id": "markdown-editor", "rows": 1, "style": "overflow:hidden; display:none;", }),
            "starter_code": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "language": forms.Select(attrs={"class": "select select-sm select-bordered text-sm auto-resize block"}),
            "explanation": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "question_type": forms.Select(attrs={"class": "select select-sm select-bordered text-sm auto-resize block"}),
        }
        

class CodeTestCaseForm(forms.ModelForm):
    class Meta:
        model = CodeTestCase
        fields = ["input_data", "expected_output", "order", "test_style"]
        widgets = {
            "input_data": forms.Textarea(attrs={
                "class": "textarea textarea-sm textarea-bordered w-full",
                "rows": 3
            }),
            "expected_output": forms.Textarea(attrs={
                "class": "textarea textarea-sm textarea-bordered w-full",
                "rows": 3
            }),
            "order": forms.NumberInput(attrs={
                "class": "input input-sm input-bordered w-full"
            }),
            "test_style": forms.Select(attrs={
                "class": "select select-sm select-bordered w-full"
            }),
        }


class CourseWeightingForm(forms.ModelForm):
    class Meta:
        model = CourseWeighting
        fields = ["activity_type", "weight"]
        widgets = {
            "activity_type": forms.TextInput(attrs={"readonly": "readonly", "class": "input input-bordered"}),
            "weight": forms.NumberInput(attrs={"class": "input input-bordered w-24"}),
        }


class FillInTheBlankQuestionForm(forms.ModelForm):
    class Meta:
        model = FillInTheBlankQuestion
        fields = [
            "language", "prompt", "expected_answer", "explanation", "case_sensitive"
        ]        
        widgets = {
            "language": forms.Select(attrs={"class": "select select-sm select-bordered text-sm auto-resize block"}),
            "prompt": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "expected_answer": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "explanation": forms.Textarea(attrs={"class": "textarea textarea-xs textarea-bordered text-sm auto-resize", "rows": 1, "style": "overflow:hidden;", }),
            "case_sensitive": forms.CheckboxInput(attrs={"class": "checkbox checkbox-primary"}),
        }