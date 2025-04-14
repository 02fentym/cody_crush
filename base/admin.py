from django.contrib import admin
from .models import Unit, Lesson, Question, Quiz, Answer

# Register your models here.
admin.site.register(Unit)
admin.site.register(Lesson)
admin.site.register(Question)
admin.site.register(Quiz)
admin.site.register(Answer)