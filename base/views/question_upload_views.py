import csv
import io

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from base.decorators import allowed_roles
from base.models import Topic, MultipleChoiceQuestion, TracingQuestion


@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    errors = []

    if request.method == "POST":

        # Step 1: Open csv file
        file = request.FILES["file"]
        data = file.read().decode("utf-8")
        csv_file = io.StringIO(data)
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=2):
            # Step 2: Validate row data
            result = question_data_validation(i, row)
            if result:
                errors.append(result)
                continue

            # Step 3: Get topic and question type
            topic = Topic.objects.get(id=row["topic_id"])
            question_type = row["question_type"].strip().lower()

            try:
                # Step 3: Create appropriate question subclass
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
                        language=row.get("language", "")
                    )
                elif question_type == "tracing":
                    print(f"Row {i} expected_output:", repr(row["expected_output"]))
                    TracingQuestion.objects.create(
                        topic=topic,
                        prompt=row["prompt"],
                        expected_output=row["expected_output"],
                        explanation=row["explanation"],
                        language=row.get("language", "")
                    )
            except Exception as e:
                errors.append(f"Row {i}: Failed to create question. Error: {str(e)}")

        # Final message
        if not errors:
            messages.success(request, "Questions uploaded successfully.")
        else:
            messages.error(request, f"{len(errors)} errors occurred during upload.")
            for err in errors:
                messages.error(request, err)

    return redirect("home")


# Helper function to validate question data
def question_data_validation(i, row):
    # Validate that the topic exists
    topic_id = row.get("topic_id")
    try:
        Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return f"Row {i}: topic ID {topic_id} does not exist."

    # Validate question type
    question_type = row.get("question_type", "").strip().lower()
    if question_type not in ["multiple_choice", "tracing"]:
        return f"Row {i}: Invalid or missing question_type."

    # Validate required fields based on question type
    if question_type == "multiple_choice":
        required_fields = ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation", "language", "topic_id"]
    elif question_type == "tracing":
        required_fields = ["prompt", "expected_output", "explanation", "language", "topic_id"]

    # Validate required fields for the given type
    for field in required_fields:
        if not row.get(field):
            return f"Row {i}: Missing value for '{field}' ({question_type} question)."

    return ""  # If all is well