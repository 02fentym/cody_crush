from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from base.models import (Topic, Course, Activity, Lesson, MultipleChoiceQuestion, TracingQuestion,
     DmojExercise, ActivityCompletion, CourseUnit,
)
from django.contrib.auth.decorators import login_required
from base.forms import CourseForm, EnrollmentPasswordForm, LessonForm
from django.contrib.contenttypes.models import ContentType
from base.decorators import allowed_roles
from base.utils import fetch_dmoj_user_data
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse


import csv, io, markdown, re

from markdown.extensions.fenced_code import FencedCodeExtension


###################### GENERIC VIEWS


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
    return render(request, "base/home.html", context)


# Helper function to get all courses
def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses
        

###################### STUDENT VIEWS






###################### TEACHER VIEWS

@login_required(login_url="login")
def course(request, course_id):
    user = request.user
    courses = get_all_courses(user.profile.role, user)

    if user.profile.role == "teacher":
        qs = Course.objects.filter(id=course_id, teacher=user)
    else:
        qs = Course.objects.filter(id=course_id, students=user)

    course = get_object_or_404(qs)

    # Show CourseUnit list instead of old Unit list
    course_units = CourseUnit.objects.filter(course=course).select_related("unit")

    password_form = EnrollmentPasswordForm()

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # Course password update
        if form_type == "password":
            password_form = EnrollmentPasswordForm(request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Enrollment password updated!")
                return redirect("course", course_id=course_id)

    context = {"courses": courses, "course": course, "course_units": course_units, "password_form": password_form,}
    return render(request, "base/course.html", context)


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect("home")


@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    errors = []

    if request.method == "POST":

        # Step 1: Open csv file
        file = request.FILES["file"]
        data = file.read().decode("utf-8")
        csv_file = io.StringIO(data)
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=2):
            # Step 2: Validate row data
            result = question_data_validation(i, row)
            if result:
                errors.append(result)
                continue

            # Step 3: Get topic and question type
            topic = Topic.objects.get(id=row["topic_id"])
            question_type = row["question_type"].strip().lower()

            try:
                # Step 3: Create appropriate question subclass
                if question_type == "multiple_choice":
                    MultipleChoiceQuestion.objects.create(
                        topic=topic,
                        prompt=row["prompt"],
                        choice_a=row["choice_a"],
                        choice_b=row["choice_b"],
                        choice_c=row["choice_c"],
                        choice_d=row["choice_d"],
                        correct_choice=row["correct_choice"].lower(),
                        explanation=row["explanation"],
                        language=row.get("language", "")
                    )
                elif question_type == "tracing":
                    print(f"Row {i} expected_output:", repr(row["expected_output"]))
                    TracingQuestion.objects.create(
                        topic=topic,
                        prompt=row["prompt"],
                        expected_output=row["expected_output"],
                        explanation=row["explanation"],
                        language=row.get("language", "")
                    )
            except Exception as e:
                errors.append(f"Row {i}: Failed to create question. Error: {str(e)}")

        # Final message
        if not errors:
            messages.success(request, "Questions uploaded successfully.")
        else:
            messages.error(request, f"{len(errors)} errors occurred during upload.")
            for err in errors:
                messages.error(request, err)

    return redirect("home")


# Helper function to validate question data
def question_data_validation(i, row):
    # Validate that the topic exists
    topic_id = row.get("topic_id")
    try:
        Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return f"Row {i}: topic ID {topic_id} does not exist."

    # Validate question type
    question_type = row.get("question_type", "").strip().lower()
    if question_type not in ["multiple_choice", "tracing"]:
        return f"Row {i}: Invalid or missing question_type."

    # Validate required fields based on question type
    if question_type == "multiple_choice":
        required_fields = ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation", "language", "topic_id"]
    elif question_type == "tracing":
        required_fields = ["prompt", "expected_output", "explanation", "language", "topic_id"]

    # Validate required fields for the given type
    for field in required_fields:
        if not row.get(field):
            return f"Row {i}: Missing value for '{field}' ({question_type} question)."

    return ""  # If all is well



def create_lesson(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    form = LessonForm()

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()

            Activity.objects.create(
                topic=topic,
                order=topic.activity_set.count() + 1,
                content_type=ContentType.objects.get_for_model(lesson),
                object_id=lesson.id
            )

            return redirect("course", topic.unit.course.id)
        else:
            messages.error(request, "Please fix the errors below.")

        
    context = {"topic": topic, "form": form, "is_edit": False}
    return render(request, "base/create_edit_lesson.html", context)


def edit_lesson(request, topic_id, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    topic = Topic.objects.get(id=topic_id)
    form = LessonForm(instance=lesson)

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            return redirect("course", topic.unit.course.id)

    context = {"form": form, "is_edit": True}
    return render(request, "base/create_edit_lesson.html", context)


@allowed_roles(["student"])
@login_required(login_url="login")
def view_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    activity = Activity.objects.get(content_type__model="lesson", object_id=lesson.id)
    course_language = activity.topic.unit.course.language.lower()  # like "python", "java"

    if request.method == "POST":
        if 'mark_as_complete' in request.POST:
            ActivityCompletion.objects.update_or_create(
                student=request.user,
                activity=activity,
                defaults={'completed': True, 'date_completed': timezone.now()}
            )
        else:
            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
            if completion:
                completion.completed = False
                date_completed = None
                completion.save()

        return redirect('view-lesson', lesson_id=lesson.id)

    # Step 1: Parse the Markdown (handle fenced code blocks)
    lesson_html = markdown.markdown(
        lesson.content,
        extensions=[FencedCodeExtension()]
    )

    # Step 2: Post-process to add language class
    lesson_html = re.sub(r'<pre><code>', f'<pre><code class="language-{course_language}">', lesson_html)
    lesson_html = re.sub(r'(?<!<pre>)<code>', f'<code class="language-{course_language}">', lesson_html)

    # Step 3: Get completion status
    completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
    completed = completion.completed if completion else False

    context = {
        "lesson": lesson,
        "lesson_html": lesson_html,
        "activity": activity,
        "completed": completed,
    }
    return render(request, "base/view_lesson.html", context)


def update_dmoj_exercises(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    profile = request.user.profile
    now = timezone.now()
    cooldown_minutes = 2

    # Check if cooldown period has passed
    if now - profile.last_dmoj_update < timedelta(minutes=cooldown_minutes):
        wait_time = cooldown_minutes - (now - profile.last_dmoj_update).seconds // 60
        messages.error(request, f"Please wait {wait_time} more minutes before refreshing again.")
        return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)
    

    # Fetch DMOJ user solved problems (list of problem codes)
    solved_problems = fetch_dmoj_user_data(request.user.profile.dmoj_username)

    # Fetch ALL DMOJ exercise activities across the system
    dmojexercise_type = ContentType.objects.get_for_model(DmojExercise)
    activities = Activity.objects.filter(content_type=dmojexercise_type)

    for activity in activities:
        dmoj_exercise = activity.content_object
        if dmoj_exercise.problem_code in solved_problems:

            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity, completed=True).first()

            if not completion:
                ActivityCompletion.objects.update_or_create(
                    student=request.user,
                    activity=activity,
                    defaults={'completed': True, 'date_completed': now}
                )

    profile.last_dmoj_update = now
    profile.save()

    messages.success(request, "DMOJ exercises successfully refreshed!")
    return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)



################## SECTION: Forms for adding things (units, topics, lessons, quizzes, etc)


# Join Course
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


################## SECTION: Course Management

