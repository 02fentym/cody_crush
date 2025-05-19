from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType

from base.decorators import allowed_roles
from base.models import Topic, DmojExercise, Activity, ActivityCompletion
from base.forms import DmojForm
from base.utils import fetch_dmoj_metadata_from_url, fetch_dmoj_user_data



# DMOJ Exercise Addition
def get_dmoj_form(request, topic_id):
    topic = Topic.objects.get(id=topic_id)
    form = DmojForm()
    return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "topic": topic})


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
            return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "topic": topic})

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
            response = render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "topic": topic})
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
    return render(request, "base/components/activity_components/dmoj_form.html", {"form": form, "topic": topic})


def update_dmoj_exercises(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    profile = request.user.profile
    now = timezone.now()
    cooldown_minutes = 2

    # Check if cooldown period has passed
    if now - profile.last_dmoj_update < timedelta(minutes=cooldown_minutes):
        wait_time = cooldown_minutes - (now - profile.last_dmoj_update).seconds // 60
        messages.error(request, f"Please wait {wait_time} more minutes before refreshing again.")
        return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)
    

    # Fetch DMOJ user solved problems (list of problem codes)
    solved_problems = fetch_dmoj_user_data(request.user.profile.dmoj_username)

    # Fetch ALL DMOJ exercise activities across the system
    dmojexercise_type = ContentType.objects.get_for_model(DmojExercise)
    activities = Activity.objects.filter(content_type=dmojexercise_type)

    for activity in activities:
        dmoj_exercise = activity.content_object
        if dmoj_exercise.problem_code in solved_problems:

            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity, completed=True).first()

            if not completion:
                ActivityCompletion.objects.update_or_create(
                    student=request.user,
                    activity=activity,
                    defaults={'completed': True, 'date_completed': now}
                )

    profile.last_dmoj_update = now
    profile.save()

    messages.success(request, "DMOJ exercises successfully refreshed!")
    return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)