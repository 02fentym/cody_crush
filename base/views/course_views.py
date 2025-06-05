from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest

from base.models import Course, CourseUnit, CourseTopic, Activity, ActivityCompletion
from base.forms import EnrollmentPasswordForm
from base.decorators import allowed_roles


@login_required(login_url="login")
def course(request, course_id):
    user = request.user
    courses = get_all_courses(user.profile.role, user)

    if user.profile.role == "teacher":
        qs = Course.objects.filter(id=course_id, teacher=user)
    else:
        qs = Course.objects.filter(id=course_id, students=user)

    course = get_object_or_404(qs)

    # Get CourseUnits and preload related Unit
    course_units = CourseUnit.objects.filter(course=course).select_related("unit")

    # Attach topics to each CourseUnit's unit
    for cu in course_units:
        cu.unit.course_topics = CourseTopic.objects.filter(unit=cu.unit).select_related("topic")

    password_form = EnrollmentPasswordForm()

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "password":
            password_form = EnrollmentPasswordForm(request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Enrollment password updated!")
                return redirect("course", course_id=course_id)
    
    completed_activities = set()
    if user.profile.role == "student":
        completed_activities = set(ActivityCompletion.objects
            .filter(student=user, completed=True)
            .values_list("activity_id", flat=True))

        # 🔁 Convert to list of ints
        completed_activities = list(map(int, completed_activities))
    
    topic_progress, unit_progress = get_progress_maps(user, course_units)
    # Attach per-topic progress directly to each CourseTopic object
    for cu in course_units:
        for ct in cu.unit.course_topics:
            ct.progress = topic_progress.get(ct.id, (0, 0))

    context = {
        "courses": courses,
        "course": course,
        "course_units": course_units,
        "password_form": password_form,
        "course_id": course_id,
        "completed_activities": completed_activities,
        "topic_progress": topic_progress,
        "unit_progress": unit_progress
    }
    return render(request, "base/main/course.html", context)

# Helper function
def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect("home")


@login_required
def get_enrolment_form(request):
    form = EnrollmentPasswordForm()
    return render(request, "base/components/course_components/course_enrolment_form.html", {"form": form})

@login_required
def enrol_in_course(request):
    if request.method == "POST":
        form = EnrollmentPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            course = Course.objects.filter(enrollment_password=password).first()

            if course:
                course.students.add(request.user)
                return render(request, "base/components/course_components/course_card.html", {"course": course})
            return HttpResponse("<div class='text-error'>Invalid course password.</div>")
    return HttpResponse("<div class='text-error'>Submission failed.</div>")

@login_required
@allowed_roles(["teacher"])
def reorder_modal(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course_units = CourseUnit.objects.filter(course=course).select_related("unit").order_by("order")
    return render(request, "base/components/course_components/reorder_modal.html", {
        "course": course,
        "course_units": course_units,
    })


@login_required
@allowed_roles(["teacher"])
@csrf_exempt
def reorder_item(request, type, id, direction):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    model_map = {
        "unit": CourseUnit,
        "topic": CourseTopic,
        "activity": Activity,
    }

    model = model_map.get(type)
    if not model:
        return HttpResponseBadRequest("Invalid type")

    obj = get_object_or_404(model, id=id)

    # Determine siblings (scope of order)
    if type == "unit":
        siblings = list(CourseUnit.objects.filter(course=obj.course).order_by("order", "id"))
    elif type == "topic":
        siblings = list(CourseTopic.objects.filter(unit=obj.unit).order_by("order", "id"))
    else:  # activity
        siblings = list(Activity.objects.filter(course_topic=obj.course_topic).order_by("order", "id"))

    index = siblings.index(obj)
    target_index = index + (-1 if direction == "up" else 1)

    if 0 <= target_index < len(siblings):
        other = siblings[target_index]

        # Use large temp value to avoid unique collision
        TEMP = 999999

        original_order = obj.order
        target_order = other.order

        obj.order = TEMP
        obj.save()

        other.order = original_order
        other.save()

        obj.order = target_order
        obj.save()

    # Return updated modal
    if type == "unit":
        course_id = obj.course.id
    elif type == "topic":
        course_unit = CourseUnit.objects.get(unit=obj.unit)
        course_id = course_unit.course.id
    else:  # activity
        unit = obj.course_topic.unit
        course_unit = CourseUnit.objects.get(unit=unit)
        course_id = course_unit.course.id


    course = get_object_or_404(Course, id=course_id)
    course_units = CourseUnit.objects.filter(course=course).select_related("unit").order_by("order")

    return render(request, "base/components/course_components/reorder_modal.html", {
        "course": course,
        "course_units": course_units,
    })


# Helper function - get progress of each CourseUnit and CourseTopic
def get_progress_maps(student, course_units):
    completed_ids = set(ActivityCompletion.objects
        .filter(student=student, completed=True)
        .values_list("activity_id", flat=True))

    topic_progress = {}
    unit_progress = {}

    for cu in course_units:
        unit_total = 0
        unit_completed = 0

        for ct in cu.unit.course_topics:
            activities = ct.activities.all()
            total = activities.count()
            completed = sum(1 for a in activities if a.id in completed_ids)

            topic_progress[ct.id] = (completed, total)

            unit_total += total
            unit_completed += completed

        unit_progress[cu.id] = (unit_completed, unit_total)

    return topic_progress, unit_progress
