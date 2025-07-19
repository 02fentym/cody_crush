from django.utils import timezone
import os
import uuid
import json
import subprocess
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from base.decorators import allowed_roles

from base.models import CodeQuestion, ActivityCompletion, Activity, Course, CourseUnit, CodeSubmission


# Create test files and test cases
def write_test_files(code, question, student_path, tests_path):
    os.makedirs(student_path, exist_ok=True)
    os.makedirs(tests_path, exist_ok=True)

    with open(os.path.join(student_path, "solution.py"), "w") as f:
        f.write(code)

    for i, case in enumerate(
        question.test_cases.filter(is_hidden=True).order_by("order"), start=1
    ):
        with open(os.path.join(tests_path, f"{i}.in"), "w") as f_in:
            f_in.write(case.input_data)
        with open(os.path.join(tests_path, f"{i}.out"), "w") as f_out:
            f_out.write(case.expected_output)


# Run tests in Docker container and capture output
def run_docker(student_path, tests_path):
    docker_cmd = [
        "docker", "run", "--rm",
        "--memory=256m",
        "--cpus=0.5",
        "--pids-limit=64",
        "-v", os.path.abspath(student_path) + ":/app/student",
        "-v", os.path.abspath(tests_path) + ":/app/tests",
        "code-runner-python"
    ]

    result = subprocess.run(
        docker_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10
    )
    return result.stdout.decode().strip()


# Submit code and create/save results
@login_required
@allowed_roles(["student"])
def submit_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    course_id = request.POST.get("course_id")
    code = request.POST.get("code")
    question_id = request.POST.get("question_id")

    if not code or not question_id:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    question = get_object_or_404(CodeQuestion, id=question_id)

    # Set up file system paths
    submission_id = str(uuid.uuid4())
    base_path = os.path.join(settings.MEDIA_ROOT, "submissions", submission_id)
    student_path = os.path.join(base_path, "student")
    tests_path = os.path.join(base_path, "tests")

    write_test_files(code, question, student_path, tests_path)

    try:
        output = run_docker(student_path, tests_path)
        data = json.loads(output)

        results = data.get("results", [])
        summary = data.get("summary", {})
        passed = summary.get("all_passed", False)

        activity = Activity.objects.filter(content_type__model="codequestion", object_id=question.id).first()
        ac = None

        if activity and request.user.is_authenticated:
            # 🔒 Check for existing completion if resubmissions not allowed
            if not activity.allow_resubmission:
                ac = ActivityCompletion.objects.filter(
                    student=request.user,
                    activity=activity,
                    completed=True
                ).first()

                if ac:
                    return redirect("code-question-results", ac.id)

            # Count attempts for this user + activity
            previous_attempts = ActivityCompletion.objects.filter(
                student=request.user,
                activity=activity
            ).count()

            # ✅ Create a new ActivityCompletion
            ac = ActivityCompletion.objects.create(
                student=request.user,
                activity=activity,
                completed=passed,
                date_completed=timezone.now(),
                attempt_number=previous_attempts + 1
            )

            # ✅ Save the submission
            CodeSubmission.objects.create(
                activity_completion=ac,
                code=code,
                results=results,
                summary=summary,
            )

        return render(request, "base/main/code_results.html", {
            "question": question,
            "activity": activity,
            "results": results,
            "summary": summary,
            "course_id": course_id
        })

    except subprocess.TimeoutExpired:
        return JsonResponse({"error": "Code execution timed out"}, status=408)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Failed to parse grading output"}, status=500)


def test_code_component(request):
    return render(request, "components/code_editor.html")


# Code question results page
@login_required(login_url="login")
@allowed_roles(["student"])
def code_question_results(request, ac_id):
    from base.models import CodeSubmission

    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    question = activity.content_object

    latest_submission = (
        CodeSubmission.objects
        .filter(activity_completion=ac)
        .order_by("-created")
        .first()
    )

    unit = activity.course_topic.unit
    course_unit = CourseUnit.objects.select_related("course").filter(unit=unit).first()
    course_id = course_unit.course.id if course_unit else None

    context = {
        "question": question,
        "activity": activity,
        "results": latest_submission.results if latest_submission else [],
        "summary": latest_submission.summary if latest_submission else {"passed": 0, "total": 0, "all_passed": False},
        "course_id": course_id,
        "courses": Course.objects.filter(students=request.user),
    }

    return render(request, "base/main/code_results.html", context)
