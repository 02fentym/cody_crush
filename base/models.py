from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])
    dmoj_username = models.CharField(max_length=100, blank=True, null=True)
    last_dmoj_update = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ({self.role.title()})"


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    language = models.ForeignKey("Language", on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, blank=True, related_name="enrolled_courses")
    enrollment_password = models.CharField(max_length=20, null=True, blank=True, help_text="Set a password students must enter to join.")
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title
    

class Unit(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CourseUnit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("course", "unit")
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} → {self.unit.title}"


class Topic(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="topics")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class CourseTopic(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE) # universal unit
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)  # universal topic
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('unit', 'topic')

    def __str__(self):
        return f"{self.unit.title} → {self.topic.title}"


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
    language = models.ForeignKey("Language", on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"


class TracingQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    prompt = models.TextField()
    expected_output = models.TextField()

    explanation = models.TextField()
    language = models.ForeignKey("Language", on_delete=models.SET_NULL, null=True)
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
    course_topic = models.ForeignKey(CourseTopic, on_delete=models.CASCADE)
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
    activity_completion = models.ForeignKey("ActivityCompletion", on_delete=models.CASCADE, null=True, blank=True)

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
    course_topic = models.ForeignKey(CourseTopic, on_delete=models.CASCADE)
    question_count = models.PositiveIntegerField(default=5)
    question_type = models.CharField(max_length=30, choices=Quiz.QUESTION_TYPE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    '''
    Generates text based on quiz type.
    This is used to display the quiz type in activity_block.html
    '''
    @property
    def quiz_type(self):
        if self.question_type == "multiple_choice":
            return "Multiple Choice Quiz"
        elif self.question_type == "tracing":
            return "Tracing Quiz"
        return "Unknown Quiz Type"

    def __str__(self):
        return f"Quiz Template: {self.course_topic.topic.title} ({self.question_count} questions)"


class Activity(models.Model):
    course_topic = models.ForeignKey("CourseTopic", on_delete=models.CASCADE, related_name="activities")
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def clean(self):
        allowed_models = ["lesson", "quiztemplate", "dmojexercise"]
        if self.content_type.model not in allowed_models:
            raise ValidationError("Unknown activity type.")

    def __str__(self):
        return f"{self.course_topic.topic.title} - {self.content_object.__class__.__name__}"
    

class ActivityCompletion(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.FloatField(blank=True, null=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} completed {self.activity}({self.activity.id})"
    

class DmojExercise(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    problem_code = models.CharField(max_length=100, unique=True)
    points = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.problem_code})"