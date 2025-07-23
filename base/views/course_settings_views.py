from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.models import Course, CourseWeighting
from base.forms import CourseWeightingForm
from base.constants import WEIGHTING_DISPLAY_NAMES


@login_required
def course_settings_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

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

    weightings = CourseWeighting.objects.filter(course=course).order_by("activity_type")

    context = {"course": course, "weightings": weightings}
    return render(request, "base/main/course_settings.html", context)


@login_required
def course_weight_settings(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

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

    weightings = CourseWeighting.objects.filter(course=course).order_by("activity_type")

    context = {"course": course, "weightings": weightings}
    return render(request, "base/main/course_weight_settings.html", context)
