from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect

from base.decorators import allowed_roles
from base.models import Topic, QuizTemplate, Activity, MultipleChoiceQuestion, TracingQuestion


# Quiz Addition
@login_required
@allowed_roles(["teacher"])
def get_quiz_form(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    return render(request, "base/components/quiz_form.html", {"topic": topic})

@login_required
@allowed_roles(["teacher"])
def submit_quiz_form(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    if request.method == "POST":
        question_count = int(request.POST.get("question_count"))
        question_type = request.POST.get("question_type")

        quiz_template = QuizTemplate.objects.create(
            topic=topic,
            question_count=question_count,
            question_type=question_type,
        )

        # Create the activity
        Activity.objects.create(
            topic=topic,
            order=topic.activity_set.count() + 1,
            content_type=ContentType.objects.get_for_model(QuizTemplate),
            object_id=quiz_template.id
        )

        # Rerender the full topic list (with new activity) for that unit
        return render(request, "base/partials/topic_list.html", {"unit": topic.unit})

    return HttpResponse("<div class='text-error'>Failed to create quiz</div>")


def create_quiz(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course_id = topic.unit.course.id
    
    question_count = int(request.POST.get("question_count", 5)) # Default to 5 if not provided
    question_type = request.POST.get("question_type")

    # Check if there are enough questions available for selected type
    QUESTION_TYPE_MAP = {
        "multiple_choice": MultipleChoiceQuestion,
        "tracing": TracingQuestion,
    }
    question_model = QUESTION_TYPE_MAP.get(question_type)
    available_count = question_model.objects.filter(topic=topic).count()
    if available_count < question_count:
        messages.error(request, f"Only {available_count} questions available for this topic.")
        return redirect("course", course_id=course_id)

    
    quiz_template = QuizTemplate.objects.create(
        topic=topic,
        question_count=question_count,
        question_type=question_type
    )

    Activity.objects.create(
        topic=topic,
        order=topic.activity_set.count() + 1,
        content_type=ContentType.objects.get_for_model(quiz_template),
        object_id=quiz_template.id
    )

    messages.success(request, "Quiz created successfully!")

    return redirect("course", course_id=course_id)