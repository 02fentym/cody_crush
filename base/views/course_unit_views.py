from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.models import Course, CourseUnit
from base.forms import CourseUnitForm


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


@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_course_unit(request, course_unit_id):
    course_unit = get_object_or_404(CourseUnit, id=course_unit_id)

    # ✅ Confirm this course belongs to the logged-in teacher
    if course_unit.course.teacher != request.user:
        return HttpResponseForbidden("Unauthorized")

    course = course_unit.course
    course_unit.delete()

    # Refresh CourseUnit list
    course_units = CourseUnit.objects.filter(course=course).select_related("unit")
    return render(request, "base/partials/unit_list.html", {"course_units": course_units})

