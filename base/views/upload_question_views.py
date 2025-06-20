import csv
import io

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.forms import MultipleChoiceQuestionForm, TracingQuestionForm, CodeQuestionForm
from base.models import Topic, MultipleChoiceQuestion, TracingQuestion, Course, Language, CodeQuestion


# Question type configurations
QUESTION_TYPE_CONFIG = {
    "multiple_choice": {
        "model": MultipleChoiceQuestion,
        "form": MultipleChoiceQuestionForm,
        "table_id": "mc-table",
        "title": "Multiple Choice Questions",
        "fields": ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation", "language"]
    },
    "tracing": {
        "model": TracingQuestion,
        "form": TracingQuestionForm,
        "table_id": "tracing-table",
        "title": "Tracing Questions",
        "fields": ["prompt", "expected_output", "explanation", "language"]
    },
    "code": {
        "model": CodeQuestion,
        "form": CodeQuestionForm,
        "table_id": "code-table",
        "title": "Programming Questions",
        "fields": [
            "title", "prompt", "starter_code", "language", "explanation", "question_type"
        ],
    }
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
        "table_id": config["table_id"],
        "sort_by": sort_by,
        "order": order,
        "question_type": question_type,
    }
    return render(request, "base/main/question_bank_base.html", context)


# Adds single question
@allowed_roles(["teacher"])
@login_required(login_url="login")
def new_question_form(request, question_type, question_id=None):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    model = config["model"]
    form_class = config["form"]
    instance = None

    if question_id:
        instance = get_object_or_404(model, pk=question_id)

    form = form_class(instance=instance)

    return render(request, "base/components/upload_questions_components/generic_question_form.html", {
        "form": form,
        "topics": Topic.objects.all(),
        "question_type": question_type,
        "title": config["title"],
        "question_id": question_id,
    })



@allowed_roles(["teacher"])
@login_required(login_url="login")
def submit_question_view(request):
    question_type = request.POST.get("question_type")
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    model = config["model"]
    form_class = config["form"]

    question_id = request.POST.get("question_id")
    topic_id = request.POST.get("topic_id")
    topic = get_object_or_404(Topic, id=topic_id) if topic_id else None

    instance = get_object_or_404(model, pk=question_id) if question_id else None
    form = form_class(request.POST, instance=instance)

    if form.is_valid() and topic:
        question = form.save(commit=False)
        question.topic = topic
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
        "table_id": config["table_id"],
        "question_type": question_type,
    })


# Bulk question upload
@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request, question_type):
    config = QUESTION_TYPE_CONFIG.get(question_type)
    if not config:
        return HttpResponseServerError("Invalid question type.")

    errors = []
    form_class = config["form"]
    model = config["model"]
    fields = config["fields"]

    if request.method == "POST":
        file = request.FILES.get("file")
        topic_id = request.POST.get("topic_id")

        if not file or not topic_id:
            errors.append("All fields are required.")
        else:
            try:
                topic = Topic.objects.get(id=topic_id)
                data = file.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(data))

                for i, row in enumerate(reader, start=2):
                    if any(not row.get(f) for f in fields):
                        errors.append(f"Row {i}: Missing fields.")
                        continue

                    instance_data = {
                        field: row[field].lower() if field == "correct_choice" else row[field]
                        for field in fields if field != "language"
                    }
                    instance_data["language"] = Language.objects.filter(name__iexact=row.get("language", "").strip()).first()
                    instance_data["topic"] = topic

                    try:
                        model.objects.create(**instance_data)
                    except Exception as e:
                        errors.append(f"Row {i}: Error: {e}")

            except Exception as e:
                errors.append(str(e))

        if not errors:
            return redirect("question-bank", question_type=question_type)

    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/upload_questions_form.html", {
        "topics": topics,
        "errors": errors,
        "table_id": config["table_id"],
        "title": f"Upload {config['title']} (CSV)",
        "question_type": question_type,  # ✅ Required for form action
    })
