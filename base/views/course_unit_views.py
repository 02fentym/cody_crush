from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.template.loader import render_to_string

from base.decorators import allowed_roles
from base.models import Course, CourseUnit
from base.forms import CourseUnitForm
from django.db.models import Max


@login_required
@allowed_roles(["teacher"])
def get_course_unit_form(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = CourseUnitForm()
    return render(request, "base/components/course_unit_components/course_unit_form.html", {"form": form, "course": course})


@login_required
@allowed_roles(["teacher"])
def submit_course_unit_form(request):
    if request.method == "POST":
        form = CourseUnitForm(request.POST)
        course_id = request.POST.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        if form.is_valid():
            unit = form.cleaned_data["unit"]

            # Check if it already exists
            course_unit, created = CourseUnit.objects.get_or_create(course=course, unit=unit)

            if created:
                # Assign next available order
                max_order = CourseUnit.objects.filter(course=course).aggregate(Max("order"))["order__max"] or 0
                course_unit.order = max_order + 1
                course_unit.save()

        course_units = CourseUnit.objects.filter(course=course).select_related("unit")
        return render(request, "base/components/course_unit_components/course_unit_list.html", {"course_units": course_units})



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
    return render(request, "base/components/course_unit_components/course_unit_list.html", {"course_units": course_units})


def move_unit(course_id, unit_id, direction):
    units = CourseUnit.objects.filter(course_id=course_id).order_by("order")
    unit = get_object_or_404(units, id=unit_id)

    index = list(units).index(unit)
    target_index = index + (-1 if direction == "up" else 1)

    if 0 <= target_index < len(units):
        other = units[target_index]
        unit.order, other.order = other.order, unit.order
        unit.save()
        other.save()

    updated_units = CourseUnit.objects.filter(course_id=course_id).order_by("order")
    html = render_to_string("base/components/course_unit_components/course_unit_list.html", {
        "course_units": updated_units,
    })
    return HttpResponse(html)

def move_unit_up(request, course_id, unit_id):
    return move_unit(course_id, unit_id, "up")

def move_unit_down(request, course_id, unit_id):
    return move_unit(course_id, unit_id, "down")