from django.contrib import admin
from .models import Unit, Topic, Quiz, Answer, Profile, Course, Activity, QuizTemplate, Lesson, MultipleChoiceQuestion, TracingQuestion, DmojExercise

# Register your models here.
admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(Profile)
admin.site.register(Course)
admin.site.register(Activity)
admin.site.register(QuizTemplate)
admin.site.register(Lesson)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(TracingQuestion)
admin.site.register(DmojExercise)