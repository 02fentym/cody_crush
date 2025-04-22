from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Unit, Topic, Question, Quiz, Answer, Profile, Course, QuizTemplate, Activity
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserForm, CourseForm, UnitForm, TopicForm, EnrollmentPasswordForm
from .decorators import allowed_roles

import csv, io

###################### GENERIC VIEWS

def login_user(request):
    page = "login"

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username").lower()
        password = request.POST.get("password")
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Password is incorrect")

    context = {"page": page}
    return render(request, "base/login_register.html", context)


def register_user(request):
    page = "register"
    form = UserForm()

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            role = form.cleaned_data.get("role")
            Profile.objects.create(user=user, role=role)

            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "An error occurred during registration")

    context = {"page": page, "form": form}
    return render(request, "base/login_register.html", context)


def logout_user(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home_selector(request):
    role = request.user.profile.role

    if role == "teacher":
        return redirect("home")
    elif role == "student":
        return redirect("student-home")
    else:
        return redirect("login")  # or raise an error


@login_required
def home(request):
    if request.user.profile.role == "student":
        courses = request.user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=request.user)
    
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.language = request.POST.get("language")
            course.save()
            messages.success(request, "Course created successfully!")
            return redirect("home")
    else:
        form = CourseForm()

    context = {"courses": courses, "form": form}
    return render(request, "base/home.html", context)


###################### STUDENT VIEWS

@allowed_roles(["student"])
@login_required(login_url="login")
def student_home(request):
    context = {}
    return render(request, "base/student_home.html", context)


@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, topic_id):
    topic = Topic.objects.get(id=topic_id)
    questions = topic.question_set.all().order_by("?")[:5] #randomizes the order of the questions
    quiz = Quiz.objects.create(
        student=request.user,
        topic=topic,
        grade=None
    )
    quiz.questions.set(questions) # can only set many-to-many fields after the quiz is created in the DB
    return redirect("take-quiz", quiz_id=quiz.id)


@allowed_roles(["student"])
@login_required(login_url="login")
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    questions = quiz.questions.all()

    if request.method == "POST":
        correct_count = 0
        total = questions.count()

        for question in questions:
            selected = request.POST.get(f'q{question.id}')
            if selected:
                is_correct = (selected == question.correct_choice)
                if is_correct:
                    correct_count += 1

                Answer.objects.create(
                    quiz=quiz,
                    question=question,
                    selected_choice=selected,
                    is_correct=is_correct
                )

        grade = (correct_count / total) * 100
        quiz.grade = round(grade, 2)
        quiz.save()

        return redirect("quiz-results", quiz.id)


    context = {"quiz": quiz, "questions": questions}
    return render(request, "base/quiz.html", context)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    answers = Answer.objects.filter(quiz=quiz)

    context = {"quiz": quiz, "answers": answers}
    return render(request, "base/quiz_results.html", context)





###################### TEACHER VIEWS

@allowed_roles(["teacher"])
@login_required(login_url="login")
def teacher_home(request):
    courses = Course.objects.filter(teacher=request.user)

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.language = request.POST.get("language")
            course.save()
            messages.success(request, "Course created successfully!")
            return redirect("home")
    else:
        form = CourseForm()

    context = {"courses": courses, "form": form}
    return render(request, "base/teacher_home.html", context)


def course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    units = course.unit_set.all()

    unit_form = UnitForm()
    password_form = CourseForm(instance=course)

    if request.method == "POST":
        if request.POST.get("form_type") == "unit":
            unit_form = UnitForm(request.POST)
            if unit_form.is_valid():
                unit = unit_form.save(commit=False)
                unit.course = course
                unit.save()
                messages.success(request, "Unit created successfully!")
                return redirect("course", course_id=course_id)
        elif request.POST.get("form_type") == "password":
            password_form = EnrollmentPasswordForm(request.POST, instance=course)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Enrollment password updated!")
                return redirect("course", course_id=course_id)
    
    context = {"course": course, "units": units, "unit_form": unit_form, "password_form": password_form}
    return render(request, "base/course.html", context)


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect("home")


def unit(request, course_id, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__id=course_id)
    topics = unit.topic_set.all()

    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.unit = unit
            topic.save()
            messages.success(request, "Topic created successfully!")
            return redirect("unit", course_id=course_id, unit_id=unit_id)
        
    context = {"unit": unit, "topics": topics}
    return render(request, "base/unit.html", context)


def delete_unit(request, course_id, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__id=course_id)
    unit.delete()
    messages.success(request, "Unit deleted successfully!")
    return redirect("course", course_id=course_id)


def topic(request, course_id, unit_id, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, unit__id=unit_id, unit__course__id=course_id)
    activities = topic.activity_set.order_by("order")
    context = {"topic": topic, "activities": activities}
    return render(request, "base/topic.html", context)


def delete_topic(request, course_id, unit_id, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, unit__id=unit_id, unit__course__id=course_id)
    topic.delete()
    messages.success(request, "Topic deleted successfully!")
    return redirect("unit", course_id=course_id, unit_id=unit_id)


def create_quiz(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    unit = topic.unit
    course = unit.course
    
    question_count = int(request.POST.get("question_count", 5))
    if question_count is None:
        question_count = 5
    
    quiz_template = QuizTemplate.objects.create(
        topic=topic,
        question_count=question_count
    )
    Activity.objects.create(
        topic=topic,
        type="quiz",
        order=topic.activity_set.count() + 1,
        quiz_template=quiz_template,
        lesson=None
    )

    messages.success(request, "Quiz created successfully!")

    return redirect("topic", course_id=course.id, unit_id=unit.id, topic_id=topic_id)


def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if activity.type == "quiz":
        quiz_template = activity.quiz_template
        quiz_template.delete()
    elif activity.type == "lesson":
        lesson = activity.lesson
        lesson.delete()

    messages.success(request, "Activity deleted successfully!")
    return redirect("topic", course_id=activity.topic.unit.course.id, unit_id=activity.topic.unit.id, topic_id=activity.topic.id)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    errors = []

    if request.method == "POST":
        errors = []
        file = request.FILES["file"]
        data = file.read().decode("utf-8")
        csv_file = io.StringIO(data)
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=2):
            # validate the data first
            result = question_data_validation(i, row)
            if result != "":
                errors.append(result)
                continue

            # add the question to the database
            topic_id = row["topic_id"]
            topic = Topic.objects.get(id=topic_id)
            Question.objects.create(
                topic=topic,
                prompt=row["prompt"],
                choice_a=row["choice_a"],
                choice_b=row["choice_b"],
                choice_c=row["choice_c"],
                choice_d=row["choice_d"],
                correct_choice=row["correct_choice"].lower(),
                explanation=row["explanation"],
                language=row["language"]
            )
        if not errors:
            messages.success(request, "Questions uploaded successfully.")

    
    context = {"errors": errors}

    return render(request, "base/upload_questions.html", context)


def question_data_validation(i, row):
    topic_id = row["topic_id"]
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return f"Row {i}: topic ID {row['topic_id']} does not exist."
    
    required_fields = ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation"]
    for field in required_fields:
        if not row.get(field):
            return f"Row {i}: Missing value for {field}"
    
    return ""