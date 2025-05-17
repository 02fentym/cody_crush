from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from base.decorators import allowed_roles
from base.models import (
    Activity, Quiz, QuizQuestion, Answer, ActivityCompletion,
    MultipleChoiceQuestion, TracingQuestion
)
from django.contrib.contenttypes.models import ContentType


@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    topic = activity.topic
    template = activity.content_object

    # Determine the question model
    if template.question_type == "multiple_choice":
        model = MultipleChoiceQuestion
    elif template.question_type == "tracing":
        model = TracingQuestion
    else:
        messages.error(request, "Unsupported question type.")
        return redirect("topic", topic.unit.course.id, topic.unit.id, topic.id)

    # Get content type for the selected question model
    content_type = ContentType.objects.get_for_model(model)

    # Random questions
    questions = model.objects.filter(topic=topic).order_by("?")[:template.question_count]

    # Create Quiz
    quiz = Quiz.objects.create(
        student=request.user,
        topic=topic,
        question_type=template.question_type
    )

    # Link questions using the bridge table
    for question in questions:
        QuizQuestion.objects.create(
            quiz=quiz,
            content_type=content_type,
            object_id=question.id
        )

    return redirect("take-quiz", quiz_id=quiz.id, activity_id=activity.id)


@allowed_roles(["student"])
@login_required(login_url="login")
def take_quiz(request, quiz_id, activity_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    question_type = quiz.question_type
    quiz_questions = quiz.quiz_questions.all()  # this gives access to both question and bridge

    if request.method == "POST":
        # Create the ActivityCompletion so we can link answers to it
        previous_attempts = ActivityCompletion.objects.filter(student=request.user, activity=activity).count()

        ac = ActivityCompletion.objects.create(
            student=request.user,
            activity=activity,
            completed=False,
            attempt_number=previous_attempts + 1,
            date_completed=timezone.now()
        )

        correct_count = 0
        total = quiz_questions.count()

        for qq in quiz_questions:
            question = qq.question
            user_input = request.POST.get(f'q{question.id}')

            if user_input:
                # Default to False in case we can't validate
                is_correct = False

                if question_type == "multiple_choice":
                    is_correct = user_input == question.correct_choice
                elif question_type == "tracing":
                    student_output = normalize_output(user_input)
                    correct_output = normalize_output(question.expected_output)
                    is_correct = student_output == correct_output

                # Save the answer
                Answer.objects.create(
                    quiz=quiz,
                    quiz_question=qq,
                    activity_completion=ac,
                    selected_choice=user_input if question_type == "multiple_choice" else None,
                    text_answer=user_input if question_type == "tracing" else None,
                    is_correct=is_correct
                )

                if is_correct:
                    correct_count += 1

        # Save grade
        grade = (correct_count / total) * 100
        quiz.grade = round(grade, 2)
        quiz.save()

        # Update the activity_completion to mark it complete + save the score
        ac.completed = True
        ac.score = quiz.grade
        ac.save()

        return redirect("quiz-results", ac.id)

    # GET request → show the quiz
    context = {"quiz": quiz, "questions": [qq.question for qq in quiz_questions]}
    return render(request, "base/quiz.html", context)



# Helper function to normalize output for tracing questions
def normalize_output(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip() for line in lines)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, ac_id):
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    quiz_template = activity.content_object
    answers = Answer.objects.filter(activity_completion=ac).select_related('quiz_question')

    context = {
        "activity_completion": ac,
        "activity": activity,
        "quiz_template": quiz_template,
        "answers": answers,
    }

    return render(request, "base/quiz_results.html", context)
