from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Max

from base.decorators import allowed_roles
from base.models import Unit, CourseTopic, CourseUnit
from base.forms import CourseTopicForm


@login_required
@allowed_roles(["teacher"])
def get_course_topic_form(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    form = CourseTopicForm()
    return render(request, "base/partials/course_topic_form.html", {"form": form, "unit": unit})

@login_required
@allowed_roles(["teacher"])
@require_POST
def submit_course_topic_form(request):
    form = CourseTopicForm(request.POST)
    unit_id = request.POST.get("unit_id")
    unit = get_object_or_404(Unit, id=unit_id)

    print("POST data:", request.POST)
    print("Form valid:", form.is_valid())
    print("Errors:", form.errors)


    if form.is_valid():
        topic = form.cleaned_data["topic"]
        CourseTopic.objects.get_or_create(unit=unit, topic=topic)

    course_topics = CourseTopic.objects.filter(unit=unit).select_related("topic")
    return render(request, "base/partials/course_topic_list.html", {"course_topics": course_topics, "unit": unit})


@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_course_topic(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    unit = course_topic.unit

    # ✅ Check that the unit belongs to a course taught by this teacher
    if not CourseUnit.objects.filter(unit=unit, course__teacher=request.user).exists():
        return HttpResponse("Unauthorized", status=403)

    course_topic.delete()

    course_topics = CourseTopic.objects.filter(unit=unit).select_related("topic")
    return render(request, "base/partials/course_topic_list.html", {"course_topics": course_topics, "unit": unit, })
