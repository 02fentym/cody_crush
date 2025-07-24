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


# Selects a CodeQuestion and adds it to the Activity
@require_POST
def submit_code_question_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)

    allow_resubmission = request.POST.get("allow_resubmission") == "on"
    random_select = request.POST.get("random_select") == "on"
    question_id = request.POST.get("question_id")
    course_id = course_topic.course.id

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

    # For back button
    course_id = course_topic.course.id

    if request.method == "POST":
        # Only allow POST-based retake if resubmissions are allowed
        if not activity.allow_resubmission:
            existing_completion = ActivityCompletion.objects.filter(
                student=user, activity=activity, completed=True
            ).order_by("-date_completed").first()

            if existing_completion:
                return redirect("code-question-results", existing_completion.id)

        # Otherwise, fall through and render the page again to allow retake

    elif request.method == "GET":
        # If the student has already completed this activity, always redirect to results
        existing_completion = ActivityCompletion.objects.filter(
            student=user, activity=activity, completed=True
        ).order_by("-date_completed").first()

        if existing_completion:
            return redirect("code-question-results", existing_completion.id)

    # Either first attempt or resubmission is allowed
    context = {"question": question, "activity": activity, "starter_code": question.starter_code, "course_id": course_id,}
    return render(request, "base/main/take_code_question.html", context)