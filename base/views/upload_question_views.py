import csv
import io

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
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
        "hx_get_url": "upload-mc-questions",
        "table_id": "mc-table",
        "title": "Multiple Choice Questions",
    },
    "tracing": {
        "model": TracingQuestion,
        "form": TracingQuestionForm,
        "hx_get_url": "upload-tracing-questions",
        "table_id": "tracing-table",
        "title": "Tracing Questions",
    },
}


def get_all_courses(role, user):
    return user.enrolled_courses.all() if role == "student" else Course.objects.filter(teacher=user)


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
    ordering = sort_by if sort_by in allowed_sorts else "created"
    ordering = ordering if order == "asc" else f"-{ordering}"

    context = {
        "courses": get_all_courses(request.user.profile.role, request.user),
        "title": config["title"],
        "questions": model.objects.select_related("topic__unit").order_by(ordering),
        "upload_button": "base/components/upload_questions_components/upload_questions_button.html",
        "hx_get_url": config["hx_get_url"],
        "table_template": "base/components/upload_questions_components/question_bank_table.html",
        "row_url_name": "edit-question",
        "table_id": config["table_id"],
        "form_container_id": f"{question_type}-edit-form-container",
        "sort_by": sort_by,
        "order": order,
        "delete_url": "delete-selected-questions",
        "new_question_url": "new-question-form",
        "question_type": question_type,
    }
    return render(request, "base/main/question_bank_base.html", context)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def new_question_form(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")
    return render(request, "base/components/upload_questions_components/generic_question_form.html", {
        "form": config["form"](),
        "topics": Topic.objects.all(),
        "submit_url_name": "submit-question",
        "question_type": question_type,
        "title": config["title"],
    })


@allowed_roles(["teacher"])
@login_required(login_url="login")
def submit_question_view(request):
    question_type = request.POST.get("question_type")
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    form = config["form"](request.POST)
    topic_id = request.POST.get("topic_id")
    if form.is_valid() and topic_id:
        question = form.save(commit=False)
        question.topic = get_object_or_404(Topic, id=topic_id)
        question.save()
        return redirect("question-bank", question_type=question_type)

    return JsonResponse({"error": "Invalid form or missing topic."}, status=400)


@allowed_roles(["teacher"])
@login_required(login_url="login")
@require_POST
def delete_selected_questions(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    ids = request.POST.getlist("question_ids")
    if ids:
        try:
            config["model"].objects.filter(id__in=ids).delete()
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
    question = get_object_or_404(model, pk=question_id)
    form_class = config["form"]

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