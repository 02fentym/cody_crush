import csv
import io

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.forms import MultipleChoiceQuestionForm, TracingQuestionForm
from base.models import Topic, MultipleChoiceQuestion, TracingQuestion, Course, Language


# Question type configurations
QUESTION_TYPE_CONFIG = {
    "multiple_choice": {
        "model": MultipleChoiceQuestion,
        "form": MultipleChoiceQuestionForm,
        "template": "base/components/upload_questions_components/mc_question_form.html",
        "edit_url_name": "edit-question",
        "new_form_url_name": "new-question-form",
        "submit_url_name": "submit-mc-question",
        "delete_url_name": "delete-selected-questions",
        "hx_get_url": "upload-mc-questions",
        "table_id": "mc-table",
        "title": "Multiple Choice Questions",
        "new_question_url": "new-question-form",
    },
    "tracing": {
        "model": TracingQuestion,
        "form": TracingQuestionForm,
        "template": "base/components/upload_questions_components/tracing_question_form.html",
        "edit_url_name": "edit-question",
        "new_form_url_name": "new-question-form",
        "submit_url_name": "submit-tracing-question",
        "delete_url_name": "delete-selected-questions",
        "hx_get_url": "upload-tracing-questions",
        "table_id": "tracing-table",
        "title": "Tracing Questions",
        "new_question_url": "new-question-form",
    },
}



def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses


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

# Generic view for question bank
@allowed_roles(["teacher"])
@login_required(login_url="login")
def question_bank_view(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    model = config["model"]
    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")
    allowed_sorts = {"topic__unit__title", "topic__title", "prompt", "created"}

    if sort_by not in allowed_sorts:
        sort_by = "created"

    ordering = sort_by if order == "asc" else f"-{sort_by}"
    questions = model.objects.select_related("topic__unit").order_by(ordering)
    courses = get_all_courses(request.user.profile.role, request.user)

    context = {
        "courses": courses,
        "title": config["title"],
        "questions": questions,
        "upload_button": "base/components/upload_questions_components/upload_questions_button.html",
        "hx_get_url": config["hx_get_url"],
        "table_template": "base/components/upload_questions_components/question_bank_table.html",
        "row_url_name": config["edit_url_name"],
        "table_id": config["table_id"],
        "form_container_id": f"{question_type}-edit-form-container",
        "sort_by": sort_by,
        "order": order,
        "delete_url": config["delete_url_name"],
        "new_question_url": config["new_form_url_name"],
        "question_type": question_type,
        
    }

    return render(request, "base/main/question_bank_base.html", context)

@allowed_roles(["teacher"])
@login_required(login_url="login")
def submit_question_view(request):
    try:
        print("DEBUG: submit_question_view reached")
        question_type = request.POST.get("question_type")
        print(f"DEBUG: question_type = {question_type}")
        config = QUESTION_TYPE_CONFIG.get(question_type)
        if not config:
            return HttpResponseServerError("Invalid question type.")

        form_class = config["form"]
        form = form_class(request.POST)
        topic_id = request.POST.get("topic_id")

        if form.is_valid() and topic_id:
            question = form.save(commit=False)
            question.topic = get_object_or_404(Topic, id=topic_id)
            question.save()
            return redirect("question-bank", question_type=question_type)

        print("DEBUG: form not valid or missing topic", form.errors, topic_id)
        return JsonResponse({"error": "Invalid form or missing topic."}, status=400)
    
    except Exception as e:
        print("ERROR in submit_question_view:", str(e))
        return HttpResponseServerError("Internal server error.")


@allowed_roles(["teacher"])
@login_required(login_url="login")
def new_question_form(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    topics = Topic.objects.all()
    form_class = config["form"]
    return render(request, "base/components/upload_questions_components/generic_question_form.html", {
        "form": form_class(),
        "topics": topics,
        "submit_url_name": "submit-question",
        "question_type": question_type,
        "title": config["title"],
    })


@allowed_roles(["teacher"])
@login_required(login_url="login")
@require_POST
def delete_selected_questions(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    model = config["model"]
    question_ids = request.POST.getlist("question_ids")

    if question_ids:
        try:
            model.objects.filter(id__in=question_ids).delete()
        except Exception as e:
            return HttpResponseServerError(f"Error deleting questions: {str(e)}")

    return redirect("question-bank", question_type=question_type)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def edit_question_view(request, question_type, question_id):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    model = config["model"]
    form_class = config["form"]
    question = get_object_or_404(model, pk=question_id)

    if request.method == "POST":
        form = form_class(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("question-bank", question_type=question_type)
    else:
        form = form_class(instance=question)

    return render(request, "base/components/upload_questions_components/edit_question_form.html", {
        "form": form,
        "question": question,
        "post_url": "edit-question",
        "form_container_id": f"{question_type}-edit-form-container",
        "table_id": config["table_id"],
        "question_type": question_type,
    })


















# views.py
@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_mc_questions(request):
    errors = []
    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    if request.method == "POST":
        file = request.FILES.get("file")
        topic_id = request.POST.get("topic_id")

        if not file or not topic_id:
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
                        result = question_data_validation(i, "multiple_choice", row)
                        if result:
                            errors.append(result)
                            continue

                        try:
                            language_name = row.get("language", "").strip()
                            language = Language.objects.filter(name__iexact=language_name).first()

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
                        except Exception as e:
                            errors.append(f"Row {i}: Failed to create question. Error: {str(e)}")

                except Exception as e:
                    errors.append(f"Failed to read CSV: {str(e)}")

        if not errors:
            ordering = sort_by if order == "asc" else f"-{sort_by}"
            mc_questions = MultipleChoiceQuestion.objects.select_related("topic__unit").order_by(ordering)
            return render(request, "base/components/upload_questions_components/question_bank_table.html", {
                "questions": mc_questions,
                "row_url_name": "edit-mc-question",
                "form_container_id": "mc-edit-form-container",
                "sort_by": sort_by,
                "order": order,
                "delete_url": "delete-selected-mc-questions",
                "table_id": "mc-table",
                "hx_get_url": "upload-mc-questions",  # ✅ REQUIRED for the upload button include
                "upload_button": "base/components/upload_questions_components/upload_questions_button.html",  # ✅ ALSO REQUIRED
            })


    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/upload_mc_questions_form.html", {
        "topics": topics,
        "errors": errors,
        "table_id": "mc-table",
    })



### TRACING QUESTIONS




@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_tracing_questions(request):
    errors = []
    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    if request.method == "POST":
        file = request.FILES.get("file")
        topic_id = request.POST.get("topic_id")

        if not file or not topic_id:
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
                        result = question_data_validation(i, "tracing", row)
                        if result:
                            errors.append(result)
                            continue

                        try:
                            language_name = row.get("language", "").strip()
                            language = Language.objects.filter(name__iexact=language_name).first()

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
            ordering = sort_by if order == "asc" else f"-{sort_by}"
            tracing_questions = TracingQuestion.objects.select_related("topic__unit").order_by(ordering)
            return render(request, "base/components/upload_questions_components/question_bank_table.html", {
                "questions": tracing_questions,
                "row_url_name": "edit-tracing-question",
                "form_container_id": "tracing-edit-form-container",
                "sort_by": sort_by,
                "order": order,
                "delete_url": "delete-selected-tracing-questions",
                "table_id": "tracing-table",  # ✅ Required
                "hx_get_url": "upload-tracing-questions",  # ✅ Required
                "upload_button": "base/components/upload_questions_components/upload_questions_button.html",  # ✅ Required
            })

    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/upload_tracing_questions_form.html", {
        "topics": topics,
        "errors": errors
    })