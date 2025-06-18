import csv
import io

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError

from base.decorators import allowed_roles
from base.forms import MultipleChoiceQuestionForm, TracingQuestionForm
from base.models import Topic, MultipleChoiceQuestion, TracingQuestion, Course, Language


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


@login_required
@allowed_roles(["teacher"])
def mc_questions(request):
    courses = get_all_courses(request.user.profile.role, request.user)

    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    allowed_sorts = {
        "topic__unit__title",
        "topic__title",
        "prompt",
        "created",
    }

    if sort_by not in allowed_sorts:
        sort_by = "created"

    ordering = sort_by if order == "asc" else f"-{sort_by}"

    questions = MultipleChoiceQuestion.objects.select_related("topic__unit").order_by(ordering)

    context = {
        "courses": courses,
        "title": "Multiple Choice Questions",
        "upload_button": "base/components/upload_questions_components/upload_questions_button.html",
        "hx_get_url": "upload-mc-questions",
        "table_template": "base/components/upload_questions_components/question_bank_table.html",
        "table_id": "mc-table",
        "row_url_name": "edit-mc-question",
        "form_container_id": "mc-edit-form-container",
        "questions": questions,
        "sort_by": sort_by,
        "order": order,
        "delete_url": "delete-selected-mc-questions",  # Added
        "new_question_url": "new-mc-question-form",
    }

    return render(request, "base/main/question_bank_base.html", context)


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

def edit_mc_question(request, question_id):
    question = get_object_or_404(MultipleChoiceQuestion, pk=question_id)
    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    if request.method == "POST":
        form = MultipleChoiceQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            ordering = sort_by if order == "asc" else f"-{sort_by}"
            mc_questions = MultipleChoiceQuestion.objects.select_related("topic__unit").order_by(ordering)
            response = render(request, "base/components/upload_questions_components/question_bank_table.html", {
                "questions": mc_questions,
                "row_url_name": "edit-mc-question",
                "form_container_id": "mc-edit-form-container",
                "sort_by": sort_by,
                "order": order,
                "delete_url": "delete-selected-mc-questions",
                "table_id": "mc-table",  
                "hx_get_url": "upload-mc-questions", 
                "upload_button": "base/components/upload_questions_components/upload_questions_button.html", 
            })
            response["HX-Trigger"] = "question-updated"
            return response
    else:
        form = MultipleChoiceQuestionForm(instance=question)
    
    context = {
        "form": form,
        "question": question,
        "post_url": "edit-mc-question",
        "form_container_id": "mc-edit-form-container",
        "table_id": "mc-table",
    }
    return render(request, "base/components/upload_questions_components/edit_question_form.html", context)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def delete_selected_mc_questions(request):
    if request.method == "POST":
        question_ids = request.POST.getlist("question_ids")
        if question_ids:
            try:
                question_ids = [int(qid) for qid in question_ids]
                MultipleChoiceQuestion.objects.filter(id__in=question_ids).delete()
            except Exception as e:
                return HttpResponseServerError(f"Error deleting questions: {str(e)}")

    return redirect("mc-questions")  # ✅ This ensures full reload




def new_mc_question_form(request):
    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/mc_question_form.html", {
        "form": MultipleChoiceQuestionForm(),
        "topics": topics,
    })


@allowed_roles(["teacher"])
@login_required(login_url="login")
def submit_mc_question(request):
    if request.method == "POST":
        form = MultipleChoiceQuestionForm(request.POST)
        topic_id = request.POST.get("topic_id")

        if form.is_valid() and topic_id:
            question = form.save(commit=False)
            question.topic = get_object_or_404(Topic, id=topic_id)
            question.save()
            return redirect("mc-questions")  # 👈 Full page reload here

    return JsonResponse({"error": "Invalid form or missing topic."}, status=400)


### TRACING QUESTIONS

@login_required
@allowed_roles(["teacher"])
def tracing_questions(request):
    courses = get_all_courses(request.user.profile.role, request.user)

    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    allowed_sorts = {
        "topic__unit__title",
        "topic__title",
        "prompt",
        "created",
    }

    if sort_by not in allowed_sorts:
        sort_by = "created"

    ordering = sort_by if order == "asc" else f"-{sort_by}"

    questions = TracingQuestion.objects.select_related("topic__unit").order_by(ordering)

    context = {
        "courses": courses,
        "title": "Tracing Questions",
        "questions": questions,
        "upload_button": "base/components/upload_questions_components/upload_questions_button.html",
        "hx_get_url": "upload-tracing-questions",
        "table_template": "base/components/upload_questions_components/question_bank_table.html",
        "row_url_name": "edit-tracing-question",
        "table_id": "tracing-table",
        "form_container_id": "tracing-edit-form-container",
        "sort_by": sort_by,
        "order": order,
        "delete_url": "delete-selected-tracing-questions",
        "new_question_url": "new-tracing-question-form",
    }

    return render(request, "base/main/question_bank_base.html", context)



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



def edit_tracing_question(request, question_id):
    question = get_object_or_404(TracingQuestion, pk=question_id)
    sort_by = request.GET.get("sort_by", "created")
    order = request.GET.get("order", "desc")

    if request.method == "POST":
        form = TracingQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            ordering = sort_by if order == "asc" else f"-{sort_by}"
            tracing_questions = TracingQuestion.objects.select_related("topic__unit").order_by(ordering)
            response = render(request, "base/components/upload_questions_components/question_bank_table.html", {
                "questions": tracing_questions,
                "row_url_name": "edit-tracing-question",
                "form_container_id": "tracing-edit-form-container",
                "sort_by": sort_by,
                "order": order,
                "delete_url": "delete-selected-tracing-questions",  # Added
            })
            response["HX-Trigger"] = "question-updated"
            return response
    else:
        form = TracingQuestionForm(instance=question)
    
    context = {
        "form": form,
        "question": question,
        "post_url": "edit-tracing-question",
        "form_container_id": "tracing-edit-form-container",
        "table_id": "tracing-table",
    }
    return render(request, "base/components/upload_questions_components/edit_question_form.html", context)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def delete_selected_tracing_questions(request):
    if request.method == "POST":
        question_ids = request.POST.getlist("question_ids")
        if question_ids:
            try:
                question_ids = [int(qid) for qid in question_ids]
                TracingQuestion.objects.filter(id__in=question_ids).delete()
            except Exception:
                return HttpResponseServerError("Error deleting questions.")

        return redirect("tracing-questions")  # 🔁 Full page reload

    return redirect("tracing-questions")



def new_tracing_question_form(request):
    topics = Topic.objects.all()
    return render(request, "base/components/upload_questions_components/tracing_question_form.html", {
        "form": TracingQuestionForm(),
        "topics": topics,
    })


@allowed_roles(["teacher"])
@login_required(login_url="login")
def submit_tracing_question(request):
    if request.method == "POST":
        form = TracingQuestionForm(request.POST)
        topic_id = request.POST.get("topic_id")

        if form.is_valid() and topic_id:
            question = form.save(commit=False)
            question.topic = get_object_or_404(Topic, id=topic_id)
            question.save()
            return redirect("tracing-questions")  # 🔁 Full page reload

    return JsonResponse({"error": "Invalid form or missing topic."}, status=400)

