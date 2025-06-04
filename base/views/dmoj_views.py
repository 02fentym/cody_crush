from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from base.decorators import allowed_roles
from base.models import CourseTopic, DmojExercise, Activity, ActivityCompletion, CourseUnit, Course
from base.forms import DmojForm
from base.utils import fetch_dmoj_metadata_from_url, fetch_dmoj_user_data



# DMOJ Exercise Addition
def get_dmoj_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    form = DmojForm()
    return render(request, "base/components/activity_components/dmoj_form.html", {
        "form": form,
        "ct": course_topic,
        "course": CourseUnit.objects.get(unit=course_topic.unit).course  # for breadcrumbs or nav
    })


@login_required(login_url="login")
@allowed_roles(["teacher"])
@require_POST
def submit_dmoj_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    form = DmojForm(request.POST)

    if form.is_valid():
        url = form.cleaned_data["url"]
        metadata = fetch_dmoj_metadata_from_url(url)

        if not metadata:
            messages.error(request, "Failed to fetch DMOJ metadata. Please check the URL.")
            return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "ct": course_topic})

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
            course_topic=course_topic,
            content_type=ContentType.objects.get_for_model(DmojExercise),
            object_id=dmoj_exercise.id
        ).exists()

        if already_assigned:
            messages.error(request, "This DMOJ problem is already assigned to this topic.")
            response = render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "ct": course_topic})
            response["HX-Reswap"] = "innerHTML"
            response["HX-Retarget"] = "#modal-body"
            return response


        # Create the activity
        Activity.objects.create(
            course_topic=course_topic,
            order=course_topic.activities.count() + 1,
            content_type=ContentType.objects.get_for_model(DmojExercise),
            object_id=dmoj_exercise.id
        )

        messages.success(request, "DMOJ exercise created successfully!")
        course_unit = CourseUnit.objects.get(unit=course_topic.unit)
        return redirect("course", course_id=course_unit.course.id)


    # If form is invalid, re-render the modal with errors
    return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "ct": course_topic})


@login_required
@require_POST
def refresh_dmoj_progress(request, course_id):
    course = get_object_or_404(Course, id=course_id, students=request.user)
    username = request.user.profile.dmoj_username  # assumes you store it here

    solved_problems = fetch_dmoj_user_data(username)
    if not solved_problems:
        # optional: message user something went wrong
        return redirect("course", course_id=course_id)

    # 1. Get Unit IDs in this course
    unit_ids = CourseUnit.objects.filter(course=course).values_list("unit_id", flat=True)

    # 2. Get CourseTopics linked to those units
    topic_ids = CourseTopic.objects.filter(unit_id__in=unit_ids).values_list("id", flat=True)

    # 3. Get DMOJ Activities from those topics
    activities = Activity.objects.filter(
        course_topic_id__in=topic_ids,
        content_type__model="dmojexercise"
    ).select_related("course_topic", "content_type")


    for activity in activities:
        if activity.content_object.problem_code in solved_problems:
            ActivityCompletion.objects.update_or_create(
                student=request.user,
                activity=activity,
                defaults={
                    "completed": True,
                    "date_completed": now(),
                }
            )

    return redirect("course", course_id=course_id)