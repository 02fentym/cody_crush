from django.shortcuts import render, redirect, get_object_or_404
from .models import Unit, Lesson, Question, Quiz, Answer

# Create your views here.
def home(request):
    units = Unit.objects.all()
    lessons = Lesson.objects.all()

    context = {"units": units, "lessons": lessons}
    return render(request, "base/student_home.html", context)

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


def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    answers = Answer.objects.filter(quiz=quiz)

    context = {"quiz": quiz, "answers": answers, "choices": choices}
    return render(request, "base/quiz_results.html", context)
