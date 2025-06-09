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
    Answer, ActivityCompletion, CourseUnit, Course
)

def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses

# Quiz Addition
@login_required
@allowed_roles(["teacher"])
def get_quiz_form(request, course_topic_id):
    course_topic = get_object_or_404(CourseTopic, id=course_topic_id)
    course_unit = CourseUnit.objects.select_related("course").filter(unit=course_topic.unit).first()
    course_id = course_unit.course.id if course_unit else None

    return render(request, "base/components/quiz_components/quiz_form.html", {
        "ct": course_topic,
        "course_id": course_id
    })


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

        Activity.objects.create(
            course_topic=course_topic,
            order=course_topic.activities.count() + 1,
            content_type=ContentType.objects.get_for_model(QuizTemplate),
            object_id=quiz_template.id
        )

        return render(request, "base/components/course_topic_components/course_topic_list.html", {
            "unit": course_topic.unit,
            "course_topics": CourseTopic.objects.filter(unit=course_topic.unit),
            "course_id": course_id
        })

    return HttpResponse("<div class='text-error'>Failed to create quiz</div>")



@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, course_id, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course_topic = activity.course_topic
    template = activity.content_object

    # Check if the student has already completed this quiz
    existing_completion = ActivityCompletion.objects.filter(
        student=request.user,
        activity=activity,
        completed=True
    ).first()

    if existing_completion:
        return redirect("quiz-results", existing_completion.id)


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

        weighted_score = (grade / 100) * activity.weight  # ← scale to weight
        ac.completed = True
        ac.score = round(weighted_score, 2)
        ac.save()

        return redirect("quiz-results", ac.id)

    # GET request → show the quiz
    context = {"quiz": quiz, "questions": [qq.question for qq in quiz_questions], "ct": course_topic, "courses": courses}
    return render(request, "base/main/quiz.html", context)



# Helper function to normalize output for tracing questions
def normalize_output(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip() for line in lines)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, ac_id):
    courses = Course.objects.filter(students=request.user)
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    quiz_template = activity.content_object
    answers = Answer.objects.filter(activity_completion=ac).select_related('quiz_question')
    
    unit = ac.activity.course_topic.unit
    course_unit = CourseUnit.objects.select_related("course").filter(unit=unit).first()
    course_id = course_unit.course.id if course_unit else None


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
        "total": total,
        "courses": courses
    }

    return render(request, "base/main/quiz_results.html", context)
