from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])

    def __str__(self):
        return f"{self.user.username} ({self.role.title()})"


class Unit(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Topic(models.Model):
    title = models.CharField(max_length=200)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.unit.title} - {self.title}"

    
class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    prompt = models.TextField(null=True, blank=True)
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    correct_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    #explanation = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.topic.title}: {self.prompt[:40]}"



class Quiz(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now=True)
    grade = models.FloatField(null=True, blank=True)
    questions = models.ManyToManyField(Question)

    def __str__(self):
        return f"{self.topic.title} Quiz for {self.student.username}"
    

class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    is_correct = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"Answer to '{self.question.prompt[:30]}...' by {self.quiz.student.username}"
