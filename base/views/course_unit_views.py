from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.models import Course, Unit, CourseUnit
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
