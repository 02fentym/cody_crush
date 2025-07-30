from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.models import Course, CourseWeighting
from base.constants import ACTIVITY_TYPE_DISPLAY
from django.contrib import messages
from base.utils import get_all_courses

@login_required
def course_settings(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    courses = get_all_courses("teacher", request.user)

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("weight_"):
                _, weighting_id = key.split("_")
                try:
                    cw = CourseWeighting.objects.get(id=weighting_id, course=course)
                    cw.weight = int(value)
                    cw.save()
                except (CourseWeighting.DoesNotExist, ValueError):
                    pass
        update_activity_weights(course)
        messages.success(request, "Weights updated and all activities refreshed.")

    weightings = CourseWeighting.objects.filter(course=course).order_by("activity_type")

    context = {"course": course, "weightings": weightings, "courses": courses}
    return render(request, "base/main/course_settings.html", context)


def update_activity_weights(course):
    print(f"Updating weights for course: {course.title}")
    weightings = CourseWeighting.objects.filter(course=course)
    weighting_map = {w.activity_type: w.weight for w in weightings}
    print(f"Weighting map: {weighting_map}")

    for ct in course.coursetopic_set.all():
        print(f"  CourseTopic: {ct}")
        for activity in ct.activities.all():
            print(f"    Activity {activity.id} ({activity.content_type.model}) current weight: {activity.weight}")
            model = activity.content_type.model
            if model == "quiztemplate":
                qt = activity.content_object
                key = f"{model}_{qt.question_type}"
            else:
                key = model

            new_weight = weighting_map.get(key)
            if new_weight is not None and activity.weight != new_weight:
                activity.weight = new_weight
                print(f"    → Updating weight to {new_weight}")
                activity.save()