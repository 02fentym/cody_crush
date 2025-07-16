from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.models import (
    Activity, CourseUnit, Lesson, QuizTemplate, DmojExercise
)


# Activity Deletion
@login_required
@allowed_roles(["teacher"])
@require_POST
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    content_object = activity.content_object

    # Only delete the underlying object if it's not a CodeQuestion
    if isinstance(content_object, (Lesson, QuizTemplate, DmojExercise)):
        content_object.delete()

    course_topic = activity.course_topic
    activity.delete()
    reorder_activities(course_topic)

    course = CourseUnit.objects.get(unit=course_topic.unit).course
    return redirect("course", course_id=course.id)




# Activity Reordering after deletion event
def reorder_activities(course_topic):
    activities = Activity.objects.filter(course_topic=course_topic).order_by("order", "id")
    for i, activity in enumerate(activities, start=1):
        if activity.order != i:
            activity.order = i
            activity.save()
