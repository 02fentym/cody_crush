from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])

    def __str__(self):
        return f"{self.user.username} ({self.role.title()})"


class Course(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        # Add more if needed
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')  # ← Add this
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, blank=True, related_name="enrolled_courses")
    enrollment_password = models.CharField(max_length=20, null=True, blank=True, help_text="Set a password students must enter to join.")
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title
    

class Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Topic(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.unit.title} - {self.title}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey("Quiz", on_delete=models.CASCADE, related_name="quiz_questions")

    # ContentType framework fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    question = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.quiz} → {self.question}"

    

class MultipleChoiceQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    prompt = models.TextField()
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    correct_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    explanation = models.TextField()
    language = models.CharField(
        max_length=20,
        choices=Course.LANGUAGE_CHOICES,
        default='python'
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"


class TracingQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    prompt = models.TextField()
    expected_output = models.TextField()

    explanation = models.TextField()
    language = models.CharField(
        max_length=20,
        choices=Course.LANGUAGE_CHOICES,
        default='python'
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"
    

class Quiz(models.Model):
    QUESTION_TYPE_CHOICES = [
        ("multiple_choice", "Multiple Choice"),
        ("tracing", "Tracing"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    grade = models.FloatField(null=True, blank=True)
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_questions(self):
        return [qq.question for qq in self.quiz_questions.all()]

    def __str__(self):
        return f"{self.topic.title} Quiz for {self.student.username}"


class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    quiz_question = models.ForeignKey("QuizQuestion", on_delete=models.CASCADE)

    selected_choice = models.CharField(  # used for multiple choice questions
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')],
        null=True, blank=True
    )
    text_answer = models.TextField(null=True, blank=True)  # used for all other questions

    is_correct = models.BooleanField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer by {self.quiz.student.username}"



class Lesson(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

'''
Used by the teacher to create a quiz template. This template can be used to generate quizzes for students.
The template will have a set number of questions and a type (multiple choice or tracing).
'''
class QuizTemplate(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    question_count = models.PositiveIntegerField(default=5)
    question_type = models.CharField(max_length=30, choices=Quiz.QUESTION_TYPE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz Template: {self.topic.title} ({self.question_count} questions)"


class Activity(models.Model):
    ACTIVITY_TYPES = [
        ("lesson", "Lesson"),
        ("quiz", "Quiz"),
    ]
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    # Either one of these will be set
    quiz_template = models.ForeignKey('QuizTemplate', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, null=True, blank=True)
    #exercise = models.ForeignKey('Exercise', on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        count = 0

        if self.lesson is not None:
            count += 1
        if self.quiz_template is not None:
            count += 1

        if count != 1:
            raise ValidationError("Exactly one of lesson, quiz_template must be set.")

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures clean() runs before save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.topic.title} - {self.type}"