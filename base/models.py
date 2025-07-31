from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from base.constants import ACTIVITY_TYPE_DISPLAY, QUESTION_TYPE_CHOICES


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])
    theme = models.CharField(max_length=20, default="light")
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
    order = models.PositiveIntegerField(default=1)

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
    course = models.ForeignKey(Course, on_delete=models.CASCADE) # specific course
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE) # universal unit
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)  # universal topic
    order = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'unit', 'topic')

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
    

class FillInTheBlankQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    prompt = models.TextField(
        help_text="Use [blank] to indicate where the missing word or phrase should go."
    )
    expected_answer = models.CharField(max_length=255)

    explanation = models.TextField()
    language = models.ForeignKey("Language", on_delete=models.SET_NULL, null=True)

    case_sensitive = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def is_correct(self, answer):
        if self.case_sensitive:
            return answer.strip() == self.expected_answer.strip()
        return answer.strip().lower() == self.expected_answer.strip().lower()

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"

    
class Quiz(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey("Activity", on_delete=models.CASCADE)
    activity_completion = models.OneToOneField("ActivityCompletion", on_delete=models.SET_NULL, null=True, blank=True)
    course_topic = models.ForeignKey(CourseTopic, on_delete=models.CASCADE)
    grade = models.FloatField(null=True, blank=True)
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_questions(self):
        return [qq.question for qq in self.quiz_questions.all()]

    def __str__(self):
        return f"{self.course_topic.topic.title} Quiz for {self.student.username}"


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
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES)
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
    weight = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    allow_resubmission = models.BooleanField(default=True, help_text="Allow students to retry this activity after submitting")

    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = [("course_topic", "order")]
        ordering = ["order"]

    def clean(self):
        allowed_models = ["lesson", "quiztemplate", "dmojexercise", "codequestion"]
        if self.content_type.model not in allowed_models:
            raise ValidationError("Unknown activity type.")
    
    def save(self, *args, **kwargs):
        if self.weight is None:
            model = self.content_type.model  # e.g., 'lesson', 'quiztemplate'
            course = self.course_topic.course

            # Special case for quiztemplate subtype
            if model == "quiztemplate":
                try:
                    template = self.content_object  # QuizTemplate
                    quiz_type = template.question_type  # 'multiple_choice' or 'tracing'
                    activity_type = f"{model}_{quiz_type}"  # e.g. 'quiztemplate_multiple_choice'
                except Exception:
                    activity_type = model  # fallback
            else:
                activity_type = model

            try:
                weighting = CourseWeighting.objects.get(course=course, activity_type=activity_type)
                self.weight = weighting.weight
            except CourseWeighting.DoesNotExist:
                self.weight = 1  # fallback
        super().save(*args, **kwargs)


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
    

class StudentCourseEnrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    score = models.FloatField(null=True, blank=True)
    progress = models.IntegerField(default=0)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course}"
    

class CodeQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    starter_code = models.TextField(blank=True, help_text="Code pre-filled for the student")
    explanation = models.TextField(blank=True)

    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default="stdin",
    )

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CodeTestCase(models.Model):
    question = models.ForeignKey(CodeQuestion, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.TextField(help_text="Raw stdin or Python test script (e.g., print(func(...)))")
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    TEST_STYLE_CHOICES = [
        ("stdin", "Standard Input"),
        ("exec", "Python Exec Block"),
    ]
    test_style = models.CharField(
        max_length=20,
        choices=TEST_STYLE_CHOICES,
        default="stdin"
    )

    def __str__(self):
        return f"Test {self.order} for {self.question.title}"


class CodeSubmission(models.Model):
    activity_completion = models.ForeignKey(ActivityCompletion, on_delete=models.CASCADE, related_name="code_submissions")
    code = models.TextField()
    results = models.JSONField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.activity_completion.student.username} for Activity {self.activity_completion.activity.id}"


class CourseWeighting(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=30)
    weight = models.PositiveIntegerField()

    class Meta:
        unique_together = ("course", "activity_type")

    def __str__(self):
        return f"{self.course.title}: {self.activity_type} → {self.weight}"

    @property
    def display_name(self):
        # Use the display name if it exists otherwise use the activity type and title case it
        return ACTIVITY_TYPE_DISPLAY.get(self.activity_type, self.activity_type.replace("_", " ").title())