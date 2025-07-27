from django.contrib import admin
from .models import (
    Unit, Topic, Quiz, Answer, Profile, Course, Activity,
    QuizTemplate, Lesson, MultipleChoiceQuestion, TracingQuestion,
    DmojExercise, ActivityCompletion, Language, CourseUnit, CourseTopic,
    CodeQuestion, CodeTestCase, CodeSubmission, CourseWeighting, StudentCourseEnrollment
)

# --- Customized Admin Classes ---

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id',  'object_id', 'order', 'topic_title', 'activity_type', 'weight', 'created')

    def topic_title(self, obj):
        return obj.course_topic.topic.title
    topic_title.short_description = "Topic"

    def activity_type(self, obj):
        return obj.content_type.name.title()
    activity_type.short_description = "Type"


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(admin.ModelAdmin):
    list_display = ('id','student', 'activity', 'activity_type', 'activity__weight', 'score','completed', 'date_completed')
    list_filter = ('completed', 'date_completed')
    search_fields = ('student__username', 'activity__id')

    def activity_type(self, obj):
        return obj.activity.content_type.model

    activity_type.short_description = "Type"


@admin.register(CodeQuestion)
class CodeQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'language')
    search_fields = ('title', 'language')
    list_filter = ('language',)



@admin.register(CodeSubmission) # Register the CodeSubmission model
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity_completion', 'created')




@admin.register(CodeTestCase)
class CodeTestCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'input_data', 'expected_output', 'test_style')
    search_fields = ('question__title', 'input_data', 'expected_output')
    list_filter = ('question__language',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'language', 'enrollment_password')
    search_fields = ('title', 'language')
    list_filter = ('language',)


@admin.register(CourseTopic)
class CourseTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "unit", "topic", "order",)
    list_filter = ("unit", "topic",)
    search_fields = ("unit__title", "topic__title",)


@admin.register(CourseUnit)
class CourseUnitAdmin(admin.ModelAdmin):
    list_display = ("course", "unit", "order")
    list_filter = ("course",)
    search_fields = ("course__title", "unit__title")


@admin.register(CourseWeighting)
class CourseWeightingAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'activity_type', 'weight')
    search_fields = ('course__title', 'activity_type')
    list_filter = ('activity_type',)
    

@admin.register(DmojExercise)
class DmojExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'problem_code', 'points')
    search_fields = ('title', 'problem_code')
    list_filter = ('points',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_course_topic')
    search_fields = ('title','get_course_topic')

    def get_course_topic(self, obj):
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Lesson)
        activity = Activity.objects.filter(content_type=ct, object_id=obj.id).first()
        return activity.course_topic.topic.title if activity else None

    get_course_topic.short_description = 'Course Topic'


@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic__title', 'prompt', 'language', 'created',)    
    search_fields = ('topic__title', 'prompt', 'language',)
    list_filter = ('language',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'dmoj_username')
    search_fields = ('user__username', 'dmoj_username')
    list_filter = ('role',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_topic', 'created')
    search_fields = ('course_topic__title',)

@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_topic', 'question_type', 'question_count')
    search_fields = ('course_topic__title',)
    list_filter = ('question_type',)



@admin.register(StudentCourseEnrollment)
class StudentCourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date')
    search_fields = ('student__username', 'course__title')
    list_filter = ('enrollment_date',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'description')
    search_fields = ('unit', 'title',)
    list_filter = ('unit', 'title',)


@admin.register(Unit) # Register the Unit model with a custom admin class
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


# --- Default Simple Registrations ---

admin.site.register(Answer)
admin.site.register(TracingQuestion)
