from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from base.decorators import allowed_roles
from django.views.decorators.http import require_POST
import random

from base.models import CourseTopic, CourseUnit, CodeQuestion, Activity, ActivityCompletion


@login_required
@allowed_roles(["teacher"])
def get_code_question_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    code_questions = CodeQuestion.objects.filter(topic=course_topic.topic)

    context = {"course_topic": course_topic, "code_questions": code_questions}
    return render(request, "base/components/activity_components/code_question_form.html", context)


@require_POST
def submit_code_question_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)

    allow_resubmission = request.POST.get("allow_resubmission") == "on"
    random_select = request.POST.get("random_select") == "on"
    question_id = request.POST.get("question_id")
    course_id=CourseUnit.objects.get(unit=course_topic.unit).course.id

    if random_select:
        questions = CodeQuestion.objects.filter(topic=course_topic.topic)
        if not questions.exists():
            # Handle empty pool gracefully
            return redirect("course", course_id=course_id)
        code_question = random.choice(questions)
    else:
        code_question = get_object_or_404(CodeQuestion, id=question_id)

    existing_count = course_topic.activities.count()

    # Create Activity
    Activity.objects.create(
        course_topic=course_topic,
        content_object=code_question,
        allow_resubmission=allow_resubmission,
        order=existing_count + 1
    )

    return redirect("course", course_id=course_id)


@login_required
@allowed_roles(["student"])
def take_code_question(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course_topic = activity.course_topic
    question = activity.content_object  # This is the CodeQuestion
    user = request.user

    # ✅ Redirect if already completed
    existing_completion = ActivityCompletion.objects.filter(
        student=user, activity=activity, completed=True
    ).first()
    
    if existing_completion:
        print(f"existing_completion: {existing_completion.id}")
        return redirect("code-question-results", existing_completion.id)

    # Optional: preload the Course for breadcrumb/back nav
    course_id = (
        CourseUnit.objects
        .filter(unit=course_topic.unit)
        .select_related("course")
        .values_list("course__id", flat=True)
        .first()
    )

    context = {
        "question": question,
        "activity": activity,
        "starter_code": question.starter_code,
        "course_id": course_id,
    }
    return render(request, "base/main/take_code_question.html", context)
