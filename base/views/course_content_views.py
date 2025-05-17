from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Max
from django.contrib.contenttypes.models import ContentType

from base.decorators import allowed_roles
from base.models import (
    Course, CourseUnit, Unit, Topic, Activity,
    DmojExercise
)
from base.forms import (
    CourseUnitForm, TopicForm, DmojForm
)
from base.utils import fetch_dmoj_metadata_from_url


# Course Unit Creation
@login_required
@allowed_roles(["teacher"])
def get_course_unit_form(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = CourseUnitForm()
    return render(request, "base/partials/course_unit_form.html", {"form": form, "course": course})


@login_required
@allowed_roles(["teacher"])
def submit_course_unit_form(request):
    if request.method == "POST":
        form = CourseUnitForm(request.POST)
        course_id = request.POST.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        if form.is_valid():
            unit = form.cleaned_data["unit"]
            CourseUnit.objects.get_or_create(course=course, unit=unit)

        course_units = CourseUnit.objects.filter(course=course).select_related("unit")
        return render(request, "base/partials/unit_list.html", {"course_units": course_units})



# Course Unit Deletion
@require_POST
@login_required(login_url="login")
@allowed_roles(["teacher"])
def delete_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__teacher=request.user)
    course = unit.course
    unit.delete()

    units = course.unit_set.prefetch_related("topic_set__activity_set").all()
    return render(request, "base/partials/unit_list.html", {"units": units, "course": course})


# Course Topic Addition
@login_required(login_url="login")
@allowed_roles(["teacher"])
def get_topic_form(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    form = TopicForm()
    context = {"form": form, "unit": unit}
    return render(request, "base/partials/topic_form.html", context)

@require_POST
@login_required(login_url="login")
@allowed_roles(["teacher"])
def submit_topic_form(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    form = TopicForm(request.POST)

    if form.is_valid():
        topic = form.save(commit=False)
        topic.unit = unit
        topic.order = (unit.topic_set.aggregate(Max("order"))["order__max"] or 0) + 1
        topic.save()
        topics = unit.topic_set.all()
        return render(request, "base/partials/topic_list.html", {"topics": topics, "unit": unit})

    return render(request, "base/partials/topic_form.html", {"form": form, "unit": unit})

# Course Topic Deletion
@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, unit__course__teacher=request.user)
    unit = topic.unit
    topic.delete()

    topics = unit.topic_set.all()
    return render(request, "base/partials/topic_list.html", {"topics": topics, "unit": unit})


# Activity Deletion
@require_POST
@login_required(login_url="login")
@allowed_roles(["teacher"])
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    unit = activity.topic.unit

     # Delete the associated object, whether it's a lesson or quiz_template
    activity.content_object.delete()

    # Delete the Activity itself too
    activity.delete()

    messages.success(request, "Activity deleted successfully!")
    return render(request, "base/partials/topic_list.html", {"unit": unit})


# DMOJ Exercise Addition
def get_dmoj_form(request, topic_id):
    topic = Topic.objects.get(id=topic_id)
    form = DmojForm()
    return render(request, "base/partials/dmoj_form.html", {"form": form, "topic": topic})


@login_required(login_url="login")
@allowed_roles(["teacher"])
@require_POST
def submit_dmoj_form(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    form = DmojForm(request.POST)

    if form.is_valid():
        url = form.cleaned_data["url"]
        metadata = fetch_dmoj_metadata_from_url(url)

        if not metadata:
            messages.error(request, "Failed to fetch DMOJ metadata. Please check the URL.")
            return render(request, "base/partials/dmoj_form.html", {"form": form, "topic": topic})

        # Try to get or create the DmojExercise
        dmoj_exercise, created = DmojExercise.objects.get_or_create(
            problem_code=metadata["problem_code"],
            defaults={
                "title": metadata["title"],
                "url": url,
                "points": metadata["points"],
            }
        )

        # Prevent duplicate assignment to the same topic
        already_assigned = Activity.objects.filter(
            topic=topic,
            content_type=ContentType.objects.get_for_model(DmojExercise),
            object_id=dmoj_exercise.id
        ).exists()

        if already_assigned:
            messages.error(request, "This DMOJ problem is already assigned to this topic.")
            response = render(request, "base/partials/dmoj_form.html", {"form": form, "topic": topic})
            response["HX-Reswap"] = "innerHTML"
            response["HX-Retarget"] = "#modal-body"
            return response


        # Create the activity
        Activity.objects.create(
            topic=topic,
            order=topic.activity_set.count() + 1,
            content_type=ContentType.objects.get_for_model(DmojExercise),
            object_id=dmoj_exercise.id
        )

        messages.success(request, "DMOJ exercise created successfully!")
        return render(request, "base/partials/topic_list.html", {"unit": topic.unit})

    # If form is invalid, re-render the modal with errors
    return render(request, "base/partials/dmoj_form.html", {"form": form, "topic": topic})



