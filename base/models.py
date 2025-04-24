from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title


class Topic(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.unit.title} - {self.title}"


class BaseQuestion(models.Model):
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE)
    prompt = models.TextField()
    explanation = models.TextField()
    language = models.CharField(
        max_length=20,
        choices=Course.LANGUAGE_CHOICES,
        default='python'
    )
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True  # Prevents this model from being created in the database

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"
    

class MultipleChoiceQuestion(BaseQuestion):
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    correct_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )


class TracingQuestion(BaseQuestion):
    expected_output = models.TextField()


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

    # Per-type question sets
    mc_questions = models.ManyToManyField(MultipleChoiceQuestion, blank=True)
    tracing_questions = models.ManyToManyField(TracingQuestion, blank=True)

    def __str__(self):
        return f"{self.topic.title} Quiz for {self.student.username}"

    def get_questions(self): # This method returns the questions based on the type of quiz
        if self.question_type == "multiple_choice":
            return self.mc_questions.all()
        elif self.question_type == "tracing":
            return self.tracing_questions.all()
        return []

    

class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    mc_question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE, null=True, blank=True)
    tracing_question = models.ForeignKey(TracingQuestion, on_delete=models.CASCADE, null=True, blank=True)

    selected_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')],
        null=True,
        blank=True
    )
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