from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])

    def __str__(self):
        return self.role


class Unit(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"Title: {self.title}"


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return f"Unit: {self.unit.title} Title: {self.title}"
    

class Question(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    prompt = models.TextField(null=True, blank=True)
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    correct_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.prompt[0:50]



class Quiz(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now=True)
    grade = models.FloatField(null=True, blank=True)
    questions = models.ManyToManyField(Question)

    def __str__(self):
        return f"Quiz: {self.lesson} Grade: {self.grade}"
    

class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    is_correct = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"Q: {self.question.id}, Selected: {self.selected_choice}, Correct: {self.is_correct}"
