import csv
import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from base.decorators import allowed_roles
from base.forms import MultipleChoiceQuestionForm, TracingQuestionForm
from base.models import Topic, MultipleChoiceQuestion, TracingQuestion, Course, Language


@allowed_roles(["teacher"])
@login_required(login_url="login")
def question_bank(request):
    courses = Course.objects.filter(teacher=request.user)
    mc_questions = MultipleChoiceQuestion.objects.select_related("topic__unit").order_by("-created")
    tracing_questions = TracingQuestion.objects.select_related("topic__unit").order_by("-created")

    template = "base/main/question_bank_table.html" if request.headers.get("Hx-Request") else "base/main/question_bank.html"

    return render(request, template, {
        "mc_questions": mc_questions,
        "tracing_questions": tracing_questions,
        "courses": courses,
    })

def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses
        

@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    errors = []

    if request.method == "POST":
        file = request.FILES.get("file")
        topic_id = request.POST.get("topic_id")
        question_type = request.POST.get("question_type", "").strip().lower()

        # Validate top-level form fields
        if not file or not topic_id or not question_type:
            errors.append("All fields are required.")
        else:
            try:
                topic = Topic.objects.get(id=topic_id)
            except Topic.DoesNotExist:
                errors.append("Invalid topic selected.")
                topic = None

            if topic:
                try:
                    data = file.read().decode("utf-8")
                    csv_file = io.StringIO(data)
                    reader = csv.DictReader(csv_file)

                    for i, row in enumerate(reader, start=2):
                        result = question_data_validation(i, question_type, row)
                        if result:
                            errors.append(result)
                            continue

                        try:
                            language_name = row.get("language", "").strip()
                            language = Language.objects.filter(name__iexact=language_name).first()

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
                                    language=language
                                )
                            elif question_type == "tracing":
                                TracingQuestion.objects.create(
                                    topic=topic,
                                    prompt=row["prompt"],
                                    expected_output=row["expected_output"],
                                    explanation=row["explanation"],
                                    language=language
                                )
                        except Exception as e:
                            errors.append(f"Row {i}: Failed to create question. Error: {str(e)}")

                except Exception as e:
                    errors.append(f"Failed to read CSV: {str(e)}")

        if not errors:
            tracing_questions = TracingQuestion.objects.select_related("topic__unit").order_by("-created")
            mc_questions = MultipleChoiceQuestion.objects.select_related("topic__unit").order_by("-created")
            return render(request, "base/components/upload_questions_components/question_bank_table.html", {
                "tracing_questions": tracing_questions,
                "mc_questions": mc_questions,
            })

    # For GET or POST with errors
    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/upload_questions_form.html", {
        "topics": topics,
        "errors": errors
    })


# Helper function to validate question data
def question_data_validation(i, question_type, row):
    # Validate required fields based on question type
    if question_type == "multiple_choice":
        required_fields = ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation", "language"]
    elif question_type == "tracing":
        required_fields = ["prompt", "expected_output", "explanation", "language"]

    # Validate required fields for the given type
    for field in required_fields:
        if not row.get(field):
            return f"Row {i}: Missing value for '{field}' ({question_type} question)."

    return ""  # If all is well



def edit_mc_question(request, question_id):
    question = get_object_or_404(MultipleChoiceQuestion, id=question_id)

    if request.method == "POST":
        form = MultipleChoiceQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("question-bank")  # or show a success screen
    else:
        form = MultipleChoiceQuestionForm(instance=question)

    if request.headers.get("Hx-Request"):
        template = "base/components/upload_questions_components/edit_mc_question_form.html"
    else:
        template = "base/components/upload_questions_components/edit_mc_question.html"
    return render(request, template, {"form": form, "question": question})


def edit_tracing_question(request, question_id):
    question = get_object_or_404(TracingQuestion, id=question_id)

    if request.method == "POST":
        form = TracingQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("question-bank")  # or show a success screen
    else:
        form = TracingQuestionForm(instance=question)

    if request.headers.get("Hx-Request"):
        template = "base/components/upload_questions_components/edit_tracing_question_form.html"
    else:
        template = "base/components/upload_questions_components/edit_tracing_question.html"
    return render(request, template, {"form": form, "question": question})