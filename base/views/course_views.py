from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from base.models import Course, CourseUnit, CourseTopic
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

    context = {"courses": courses, "course": course, "course_units": course_units, "password_form": password_form, }
    return render(request, "base/course.html", context)

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
    return render(request, "base/components/course_enrolment_form.html", {"form": form})

@login_required
def enrol_in_course(request):
    if request.method == "POST":
        form = EnrollmentPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            course = Course.objects.filter(enrollment_password=password).first()

            if course:
                course.students.add(request.user)
                return render(request, "base/partials/course_card.html", {"course": course})
            return HttpResponse("<div class='text-error'>Invalid course password.</div>")
    return HttpResponse("<div class='text-error'>Submission failed.</div>")