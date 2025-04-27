from django.contrib import admin
from .models import (
    Unit, Topic, Quiz, Answer, Profile, Course, Activity,
    QuizTemplate, Lesson, MultipleChoiceQuestion, TracingQuestion,
    DmojExercise, ActivityCompletion
)

# --- Customized Admin Classes ---

@admin.register(Unit) # Register the Unit model with a custom admin class
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'course')
    search_fields = ('title',)
    list_filter = ('course',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit')
    search_fields = ('title',)
    list_filter = ('unit',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'enrollment_password')
    search_fields = ('title', 'language')
    list_filter = ('language',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'dmoj_username')
    search_fields = ('user__username', 'dmoj_username')
    list_filter = ('role',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = ('topic', 'question_type', 'question_count')
    search_fields = ('topic__title',)
    list_filter = ('question_type',)

@admin.register(DmojExercise)
class DmojExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'problem_code', 'points')
    search_fields = ('title', 'problem_code')
    list_filter = ('points',)

@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity', 'completed', 'date_completed')
    list_filter = ('completed', 'date_completed')
    search_fields = ('student__username', 'activity__id')

# --- Default Simple Registrations ---

admin.site.register(Activity)
admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(TracingQuestion)
