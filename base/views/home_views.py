from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from base.models import (Course, CourseUnit, CourseTopic, )
from django.contrib.auth.decorators import login_required
from base.forms import CourseForm, EnrollmentPasswordForm
from django.http import HttpResponse


@login_required(login_url="login")
def home(request):
    courses = get_all_courses(request.user.profile.role, request.user)
    
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "course":
            course_form = CourseForm(request.POST)
            if course_form.is_valid():
                course = course_form.save(commit=False)
                course.teacher = request.user
                course.save()
                messages.success(request, "Course created successfully!")
                return redirect("home")
        elif form_type == "password":
            password_form = EnrollmentPasswordForm(request.POST)
            enrollment_password = request.POST.get("enrollment_password")

            try:
                course = Course.objects.get(enrollment_password=enrollment_password)
                course.students.add(request.user)
                messages.success(request, f"You have been enrolled in {course.title}!")
            except Course.DoesNotExist:
                messages.error(request, "Invalid enrollment password. Please try again.")

            return redirect("home")
    else:
        course_form = CourseForm()
        password_form = EnrollmentPasswordForm()

    context = {"courses": courses, "course_form": course_form, "password_form": password_form}
    return render(request, "base/main/home.html", context)


# Helper function to get all courses
def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses
        