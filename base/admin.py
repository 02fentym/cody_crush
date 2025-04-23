from django.contrib import admin
from .models import Unit, Topic, Question, Quiz, Answer, Profile, Course, Activity, QuizTemplate, Lesson

# Register your models here.
admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(Profile)
admin.site.register(Course)
admin.site.register(Activity)
admin.site.register(QuizTemplate)
admin.site.register(Lesson)