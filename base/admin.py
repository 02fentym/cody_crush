from django.contrib import admin
from .models import (
    Unit, Topic, Quiz, Answer, Profile, Course, Activity,
    QuizTemplate, Lesson, MultipleChoiceQuestion, TracingQuestion,
    DmojExercise, ActivityCompletion, Language, CourseUnit, CourseTopic
)

# --- Customized Admin Classes ---

@admin.register(Unit) # Register the Unit model with a custom admin class
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'description')
    search_fields = ('unit', 'title',)
    list_filter = ('unit', 'title',)

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

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(CourseUnit)
class CourseUnitAdmin(admin.ModelAdmin):
    list_display = ("course", "unit", "order")
    list_filter = ("course",)
    search_fields = ("course__title", "unit__title")

@admin.register(CourseTopic)
class CourseTopicAdmin(admin.ModelAdmin):
    list_display = ("unit", "topic", "order",)
    list_filter = ("unit", "topic",)
    search_fields = ("unit__title", "topic__title",)


# --- Default Simple Registrations ---

admin.site.register(Activity)
admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(TracingQuestion)
