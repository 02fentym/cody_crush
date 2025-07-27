from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from base.decorators import allowed_roles
from base.models import CourseTopic, DmojExercise, Activity, ActivityCompletion, CourseUnit, StudentCourseEnrollment
from base.forms import DmojForm
from base.utils import fetch_dmoj_metadata_from_url, fetch_dmoj_user_data, update_student_progress
from django.db import transaction



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
        course_id = course_topic.course.id
        return redirect("course", course_id=course_id)


    # If form is invalid, re-render the modal with errors
    return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "ct": course_topic})


@login_required
@allowed_roles(["teacher"])
def edit_dmoj_form(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    exercise = activity.content_object
    course_topic = activity.course_topic

    form = DmojForm(initial={"url": exercise.url})

    return render(request, "base/components/activity_components/dmoj_form.html", {
        "form": form,
        "ct": course_topic,
        "exercise_id": exercise.id,
        "edit_mode": True
    })

@login_required
@allowed_roles(["teacher"])
@require_POST
def update_dmoj(request, exercise_id):
    exercise = get_object_or_404(DmojExercise, id=exercise_id)
    form = DmojForm(request.POST)

    if form.is_valid():
        new_url = form.cleaned_data["url"]
        metadata = fetch_dmoj_metadata_from_url(new_url)
        if not metadata:
            messages.error(request, "Invalid URL or failed to fetch metadata.")
        else:
            exercise.url = new_url
            exercise.title = metadata["title"]
            exercise.problem_code = metadata["problem_code"]
            exercise.points = metadata["points"]
            exercise.save()
            messages.success(request, "DMOJ exercise updated.")

    activity = Activity.objects.get(
        content_type=ContentType.objects.get_for_model(DmojExercise),
        object_id=exercise.id
    )
    course_id = activity.course_topic.course.id

    return redirect("course", course_id=course_id)



@login_required
@require_POST
def refresh_dmoj_progress(request, course_id):
    enrollment = get_object_or_404(StudentCourseEnrollment, student=request.user, course_id=course_id)
    course = enrollment.course
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

    with transaction.atomic():
        for activity in activities:
            exercise = activity.content_object
            if exercise is None:
                print(f"[WARN] Activity {activity.id} has no content_object")
                continue

            if exercise.problem_code in solved_problems:
                ActivityCompletion.objects.update_or_create(
                    student=request.user,
                    activity=activity,
                    defaults={
                        "completed": True,
                        "score": activity.weight,  # ✅ consistent scoring
                        "date_completed": now(),
                    }
                )

        # ✅ Recalculate after all completions
        update_student_progress(request.user, course)


    return redirect("course", course_id=course_id)