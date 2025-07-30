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
    Answer, ActivityCompletion, FillInTheBlankQuestion
)

from base.constants import DEFAULT_QUIZ_QUESTION_COUNT, QUIZ_QUESTION_COUNT_OPTIONS
from base.utils import get_all_courses, update_student_progress
from django.db import transaction


# Quiz Addition
@login_required
@allowed_roles(["teacher"])
def get_quiz_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    course_id = course_topic.course.id

    context = {"ct": course_topic, "course_id": course_id, "question_count": DEFAULT_QUIZ_QUESTION_COUNT, "question_counts": QUIZ_QUESTION_COUNT_OPTIONS,}
    return render(request, "base/components/quiz_components/quiz_form.html", context)


# Allows a teacher to edit a quiz
@login_required
@allowed_roles(["teacher"])
def edit_quiz_form(request, quiz_id):
    quiz_template = get_object_or_404(QuizTemplate, id=quiz_id)
    course_topic = quiz_template.course_topic

    activity = Activity.objects.get(object_id=quiz_template.id, content_type=ContentType.objects.get_for_model(QuizTemplate))

    context = {
        "quiz_template": quiz_template,
        "ct": course_topic,
        "course_id": course_topic.course.id,
        "activity": activity,
        "question_count": quiz_template.question_count,
        "question_counts": QUIZ_QUESTION_COUNT_OPTIONS
    }
    return render(request, "base/components/quiz_components/quiz_form.html", context)


@login_required
@allowed_roles(["teacher"])
def submit_quiz_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)

    if request.method == "POST":
        course_id = request.POST.get("course_id")  # ⬅ move here

        question_count = int(request.POST.get("question_count"))
        question_type = request.POST.get("question_type")

        quiz_template = QuizTemplate.objects.create(
            course_topic=course_topic,
            question_count=question_count,
            question_type=question_type,
        )

        allow_resubmission = request.POST.get("allow_resubmission") == "on"

        Activity.objects.create(
            course_topic=course_topic,
            order=course_topic.activities.count() + 1,
            content_type=ContentType.objects.get_for_model(QuizTemplate),
            object_id=quiz_template.id,
            allow_resubmission=allow_resubmission
        )

        return render(request, "base/components/course_topic_components/course_topic_list.html", {
            "unit": course_topic.unit,
            "course_topics": CourseTopic.objects.filter(unit=course_topic.unit),
            "course_id": course_id
        })

    return HttpResponse("<div class='text-error'>Failed to create quiz</div>")


@login_required
@allowed_roles(["teacher"])
def update_quiz_form(request, quiz_id):
    quiz_template = get_object_or_404(QuizTemplate, id=quiz_id)

    if request.method == "POST":
        # Update quiz template fields
        quiz_template.question_count = int(request.POST.get("question_count"))
        quiz_template.question_type = request.POST.get("question_type")
        quiz_template.save()

        # Update the related Activity
        activity = Activity.objects.get(
            object_id=quiz_template.id,
            content_type=ContentType.objects.get_for_model(QuizTemplate)
        )
        activity.allow_resubmission = request.POST.get("allow_resubmission") == "on"
        activity.save()

        # Return partial to update the course topic list
        return render(request, "base/components/course_topic_components/course_topic_list.html", {
            "unit": quiz_template.course_topic.unit,
            "course_topics": CourseTopic.objects.filter(unit=quiz_template.course_topic.unit),
            "course_id": quiz_template.course_topic.course.id
        })

    return HttpResponse("<div class='text-error'>Failed to update quiz</div>")


# Helper function for take_quiz(): returns a list of questions that have the input fields within the prompt string
def get_rendered_questions(quiz_questions, question_type):
    rendered = []

    for qq in quiz_questions:
        q = qq.question

        if question_type == "fill_in_the_blank":
            input_html = f"<input type='text' name='q{q.id}' class='input input-bordered inline w-auto' required>"
            q.rendered_prompt = q.prompt.replace("[blank]", input_html)
        else:
            q.rendered_prompt = q.prompt  # fallback for other question types

        rendered.append(q)

    return rendered



@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, course_id, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course_topic = activity.course_topic
    template = activity.content_object

    # Always check if a completed quiz already exists
    existing_completion = ActivityCompletion.objects.filter(
        student=request.user,
        activity=activity,
        completed=True
    ).order_by("-date_completed").first()

    # ⛔️ Redirect to results if already completed — regardless of allow_resubmission
    if existing_completion and request.method == "GET":
        return redirect("quiz-results", existing_completion.id)

    # Determine the question model
    if template.question_type == "multiple_choice":
        model = MultipleChoiceQuestion
    elif template.question_type == "tracing":
        model = TracingQuestion
    elif template.question_type == "fill_in_the_blank":
        model = FillInTheBlankQuestion
    else:
        messages.error(request, "Unsupported question type.")
        return redirect("course", course_id)

    # Get content type for the selected question model
    content_type = ContentType.objects.get_for_model(model)

    # Random questions
    questions = model.objects.filter(topic=course_topic.topic).order_by("?")[:template.question_count]

    # Create Quiz
    quiz = Quiz.objects.create(
        student=request.user,
        activity=activity,
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

    return redirect("take-quiz", quiz_id=quiz.id, activity_id=activity.id)




@allowed_roles(["student"])
@login_required(login_url="login")
def take_quiz(request, quiz_id, activity_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    question_type = quiz.question_type
    course_topic = activity.course_topic
    quiz_questions = quiz.quiz_questions.all()  # this gives access to both question and bridge
    courses = get_all_courses("student", request.user)

    if request.method == "POST":
        with transaction.atomic():
            # Create the ActivityCompletion so we can link answers to it
            previous_attempts = ActivityCompletion.objects.filter(student=request.user, activity=activity).count()

            ac = ActivityCompletion.objects.create(
                student=request.user,
                activity=activity,
                completed=False,
                attempt_number=previous_attempts + 1,
                date_completed=timezone.now()
            )
            quiz.activity_completion = ac
            quiz.save()

            correct_count = 0
            total = quiz_questions.count()

            for qq in quiz_questions:
                question = qq.question
                user_input = request.POST.get(f'q{question.id}')

                if user_input:
                    is_correct = False

                    if question_type == "multiple_choice":
                        is_correct = user_input == question.correct_choice
                    elif question_type == "tracing":
                        student_output = normalize_output(user_input)
                        correct_output = normalize_output(question.expected_output)
                        is_correct = student_output == correct_output
                    elif question_type == "fill_in_the_blank":
                        correct = question.expected_answer
                        if question.case_sensitive:
                            is_correct = user_input == correct
                        else:
                            is_correct = user_input.strip().lower() == correct.strip().lower()

                    Answer.objects.create(
                        quiz=quiz,
                        quiz_question=qq,
                        activity_completion=ac,
                        selected_choice=user_input if question_type == "multiple_choice" else None,
                        text_answer=user_input if question_type in ["tracing", "fill_in_the_blank"] else None,
                        is_correct=is_correct
                    )

                    if is_correct:
                        correct_count += 1

            grade = (correct_count / total) * 100
            quiz.grade = round(grade, 2)
            quiz.save()

            weighted_score = (grade / 100) * activity.weight
            ac.completed = True
            ac.score = round(weighted_score, 2)
            ac.save()

            # ✅ NEW: Update course progress + score
            update_student_progress(
                request.user,
                activity.course_topic.course
            )

        return redirect("quiz-results", ac.id)
    
    rendered_questions = get_rendered_questions(quiz_questions, question_type)

    # GET request → show the quiz
    context = {"quiz": quiz, "questions": rendered_questions, "ct": course_topic, "courses": courses}
    return render(request, "base/main/quiz.html", context)



# Helper function to normalize output for tracing questions
def normalize_output(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip() for line in lines)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, ac_id):
    courses = get_all_courses("student", request.user)
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    quiz_template = activity.content_object
    course_id = activity.course_topic.course.id

    # All quiz attempts by this student
    all_quizzes = Quiz.objects.filter(activity=activity, student=request.user).order_by("-created")
    current_quiz = all_quizzes.filter(activity_completion=ac).first()

    answers = Answer.objects.filter(activity_completion=ac).select_related('quiz_question')
    correct = answers.filter(is_correct=True).count()
    total = answers.count()

    is_first_attempt = current_quiz is None
    can_retake = activity.allow_resubmission

    # Replaces [blank] with "______________" for fill in the blank questions
    for answer in answers:
        question = answer.quiz_question.question
        if hasattr(question, "prompt") and "[blank]" in question.prompt:
            answer.formatted_prompt = question.prompt.replace("[blank]", "______________")
        else:
            answer.formatted_prompt = getattr(question, "prompt", "")


    context = {
        "activity_completion": ac,
        "activity": activity,
        "quiz_template": quiz_template,
        "quiz": current_quiz,
        "answers": answers,
        "correct": correct,
        "total": total,
        "course_id": course_id,
        "courses": courses,
        "all_quizzes": all_quizzes,
        "can_retake": can_retake,
        "is_first_attempt": is_first_attempt,
    }

    return render(request, "base/main/quiz_results.html", context)
