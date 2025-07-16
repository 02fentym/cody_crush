from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from base.decorators import allowed_roles
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages


from base.models import CourseTopic, CourseUnit, Language, CodeQuestion, Activity, ActivityCompletion


@login_required
@allowed_roles(["teacher"])
def get_code_question_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    course_unit = CourseUnit.objects.select_related("course").filter(unit=course_topic.unit).first()
    course_id = course_unit.course.id if course_unit else None

    context = {"ct": course_topic, "course_id": course_id, "languages": Language.objects.all()}
    return render(request, "base/components/activity_components/code_question_form.html", context)


@login_required
@allowed_roles(["teacher"])
def submit_code_question_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    questions = CodeQuestion.objects.filter(topic=course_topic.topic)

    if not questions.exists():
        messages.error(request, "No code questions available for this topic.")
        return redirect("course", course_id=CourseUnit.objects.get(unit=course_topic.unit).course.id)

    random_question = questions.order_by("?").first()

    Activity.objects.create(
        course_topic=course_topic,
        order=course_topic.activities.count() + 1,
        content_type=ContentType.objects.get_for_model(CodeQuestion),
        object_id=random_question.id
    )

    messages.success(request, "Random code question assigned.")
    return redirect("course", course_id=CourseUnit.objects.get(unit=course_topic.unit).course.id)


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
