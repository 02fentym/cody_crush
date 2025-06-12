import re
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from base.decorators import allowed_roles
from base.models import Topic, Lesson, Activity, ActivityCompletion, CourseTopic, CourseUnit
from base.forms import LessonForm


@login_required
@allowed_roles(["teacher"])
def create_lesson(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    form = LessonForm()

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()

            Activity.objects.create(
                course_topic=course_topic,
                order=course_topic.activities.count() + 1,
                content_type=ContentType.objects.get_for_model(lesson),
                object_id=lesson.id
            )

            course_unit = CourseUnit.objects.filter(unit=course_topic.unit).first()
            return redirect("course", course_unit.course.id)
        else:
            messages.error(request, "Please fix the errors below.")

        
    context = {"topic": course_topic, "form": form, "is_edit": False}
    return render(request, "base/main/create_edit_lesson.html", context)

@login_required
@allowed_roles(["teacher"])
def edit_lesson(request, course_topic_id, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    course_topic = CourseTopic.objects.get(id=course_topic_id)
    form = LessonForm(instance=lesson)

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            course_unit = CourseUnit.objects.filter(unit=course_topic.unit).first()
            return redirect("course", course_unit.course.id)

    context = {"form": form, "is_edit": True}
    return render(request, "base/main/create_edit_lesson.html", context)

@login_required
@allowed_roles(["student"])
def view_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    activity = Activity.objects.get(content_type__model="lesson", object_id=lesson.id)
    course_language = activity.topic.unit.course.language.lower()  # like "python", "java"

    if request.method == "POST":
        if 'mark_as_complete' in request.POST:
            ActivityCompletion.objects.update_or_create(
                student=request.user,
                activity=activity,
                defaults={'completed': True, 'date_completed': timezone.now()}
            )
        else:
            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
            if completion:
                completion.completed = False
                date_completed = None
                completion.save()

        return redirect('view-lesson', lesson_id=lesson.id)

    # Step 1: Parse the Markdown (handle fenced code blocks)
    lesson_html = markdown.markdown(
        lesson.content,
        extensions=[FencedCodeExtension()]
    )

    # Step 2: Post-process to add language class
    lesson_html = re.sub(r'<pre><code>', f'<pre><code class="language-{course_language}">', lesson_html)
    lesson_html = re.sub(r'(?<!<pre>)<code>', f'<code class="language-{course_language}">', lesson_html)

    # Step 3: Get completion status
    completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
    completed = completion.completed if completion else False

    context = {
        "lesson": lesson,
        "lesson_html": lesson_html,
        "activity": activity,
        "completed": completed,
    }
    return render(request, "base/main/view_lesson.html", context)