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
    context = {"form": form, "course": course}
    return render(request, "base/components/course_unit_components/course_unit_form.html", context)


@login_required
@allowed_roles(["teacher"])
def submit_course_unit_form(request):
    if request.method == "POST":
        form = CourseUnitForm(request.POST)
        course_id = request.POST.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        if form.is_valid():
            unit = form.cleaned_data["unit"]

            if not CourseUnit.objects.filter(course=course, unit=unit).exists():
                max_order = CourseUnit.objects.filter(course=course).aggregate(Max("order"))["order__max"] or 0
                new_order = max_order + 1
                CourseUnit.objects.create(course=course, unit=unit, order=new_order)

        # Only one query and return
        course_units = CourseUnit.objects.filter(course=course).select_related("unit")
        return render(
            request,
            "base/components/course_unit_components/course_unit_list.html",
            {"course_units": course_units}
        )




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

    # ✅ Re-sequence CourseUnit orders within this course
    remaining_units = CourseUnit.objects.filter(course=course).order_by("order", "id")
    for index, cu in enumerate(remaining_units, start=1):
        if cu.order != index:
            cu.order = index
            cu.save(update_fields=["order"])

    # Refresh CourseUnit list
    course_units = CourseUnit.objects.filter(course=course).select_related("unit")
    context = {"course_units": course_units}
    return render(request, "base/components/course_unit_components/course_unit_list.html", context)
