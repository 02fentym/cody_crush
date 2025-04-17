from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Unit, Lesson, Question, Quiz, Answer, Profile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserForm
from .decorators import allowed_roles

import csv, io

# Create your views here.

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


def home(request):
    units = Unit.objects.all()
    lessons = Lesson.objects.all()

    context = {"units": units, "lessons": lessons}

    if request.user.profile.role == "teacher":
        return render(request, "base/teacher_home.html", context)
    else:
        return render(request, "base/student_home.html", context)


@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    questions = lesson.question_set.all().order_by("?") #randomizes the order of the questions
    quiz = Quiz.objects.create(
        student=request.user,
        lesson=lesson,
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


@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    if request.method == "POST":
        file = request.FILES["file"]
        data = file.read().decode("utf-8")
        csv_file = io.StringIO(data)
        reader = csv.DictReader(csv_file)

        for row in reader:
            lesson_id = row["lesson_id"]
            lesson = Lesson.objects.get(id=lesson_id)
            Question.objects.create(
                lesson=lesson,
                prompt=row["prompt"],
                choice_a=row["choice_a"],
                choice_b=row["choice_b"],
                choice_c=row["choice_c"],
                choice_d=row["choice_d"],
                correct_choice=row["correct_choice"].lower()
            )
    
    context = {}

    return render(request, "base/upload_questions.html", context)