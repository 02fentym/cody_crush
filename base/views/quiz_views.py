from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from base.decorators import allowed_roles
from base.models import (
    CourseTopic, Activity, Quiz, QuizTemplate, QuizQuestion,
    MultipleChoiceQuestion, TracingQuestion,
    Answer, ActivityCompletion
)


# TEACHER VIEWS

# Quiz Addition
@login_required
@allowed_roles(["teacher"])
def get_quiz_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    return render(request, "base/components/quiz_components/quiz_form.html", {"ct": course_topic})

@login_required
@allowed_roles(["teacher"])
def submit_quiz_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)

    if request.method == "POST":
        question_count = int(request.POST.get("question_count"))
        question_type = request.POST.get("question_type")

        quiz_template = QuizTemplate.objects.create(
            course_topic=course_topic,
            question_count=question_count,
            question_type=question_type,
        )

        # Create the activity
        Activity.objects.create(
            course_topic=course_topic,
            order=course_topic.activities.count() + 1,
            content_type=ContentType.objects.get_for_model(QuizTemplate),
            object_id=quiz_template.id
        )

        # Rerender the full topic list (with new activity) for that unit
        return render(request, "base/components/course_topic_components/course_topic_list.html", {
            "unit": course_topic.unit,
            "course_topics": CourseTopic.objects.filter(unit=course_topic.unit)
        })

    return HttpResponse("<div class='text-error'>Failed to create quiz</div>")


def create_quiz(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    course_id = course_topic.unit.course.id
    
    question_count = int(request.POST.get("question_count", 5)) # Default to 5 if not provided
    question_type = request.POST.get("question_type")

    # Check if there are enough questions available for selected type
    QUESTION_TYPE_MAP = {
        "multiple_choice": MultipleChoiceQuestion,
        "tracing": TracingQuestion,
    }
    question_model = QUESTION_TYPE_MAP.get(question_type)
    available_count = question_model.objects.filter(topic=course_topic.topic).count()
    if available_count < question_count:
        messages.error(request, f"Only {available_count} questions available for this topic.")
        return redirect("course", course_id=course_id)

    
    quiz_template = QuizTemplate.objects.create(
        course_topic=course_topic,
        question_count=question_count,
        question_type=question_type
    )

    Activity.objects.create(
        course_topic=course_topic,
        order=course_topic.activities.count() + 1,
        content_type=ContentType.objects.get_for_model(quiz_template),
        object_id=quiz_template.id
    )

    messages.success(request, "Quiz created successfully!")

    return redirect("course", course_id=course_id)


# STUDENT VIEWS
@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, course_id, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course_topic = activity.course_topic
    template = activity.content_object

    # Determine the question model
    if template.question_type == "multiple_choice":
        model = MultipleChoiceQuestion
    elif template.question_type == "tracing":
        model = TracingQuestion
    else:
        messages.error(request, "Unsupported question type.")
        return redirect("topic", course_id, course_topic.topic.unit.id, course_topic.id)

    # Get content type for the selected question model
    content_type = ContentType.objects.get_for_model(model)

    # Random questions
    questions = model.objects.filter(topic=course_topic.topic).order_by("?")[:template.question_count]

    # Create Quiz
    quiz = Quiz.objects.create(
        student=request.user,
        course_topic=course_topic,
        question_type=template.question_type
    )

    # Link questions using the bridge table
    for question in questions:
        QuizQuestion.objects.create(
            quiz=quiz,
            content_type=content_type,
            object_id=question.id
        )

    return redirect("take-quiz", course_id=course_id, quiz_id=quiz.id, activity_id=activity.id)


@allowed_roles(["student"])
@login_required(login_url="login")
def take_quiz(request, course_id, quiz_id, activity_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    question_type = quiz.question_type
    course_topic = activity.course_topic
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

        return redirect("quiz-results", ac.id, course_id)

    # GET request → show the quiz
    context = {"quiz": quiz, "questions": [qq.question for qq in quiz_questions], "ct": course_topic, "course_id": course_id}
    return render(request, "base/main/quiz.html", context)



# Helper function to normalize output for tracing questions
def normalize_output(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip() for line in lines)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, ac_id, course_id):
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    quiz_template = activity.content_object
    answers = Answer.objects.filter(activity_completion=ac).select_related('quiz_question')

    quiz = answers.first().quiz if answers.exists() else None
    correct = answers.filter(is_correct=True).count()
    total = answers.count()

    context = {
        "activity_completion": ac,
        "activity": activity,
        "quiz_template": quiz_template,
        "answers": answers,
        "quiz": quiz,
        "course_id": course_id,
        "correct": correct,
        "total": total
    }

    return render(request, "base/main/quiz_results.html", context)
