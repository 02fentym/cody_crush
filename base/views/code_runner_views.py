from django.utils import timezone
import os
import uuid
import json
import subprocess
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from base.decorators import allowed_roles
from base.utils import get_all_courses, update_student_progress
from base.models import CodeQuestion, ActivityCompletion, Activity, CourseUnit, CodeSubmission
from django.db import transaction

# Create test files and test cases
def write_test_files(code, question, student_path, tests_path, language):
    os.makedirs(student_path, exist_ok=True)
    os.makedirs(tests_path, exist_ok=True)

    # Choose file name based on language
    filename = "Solution.java" if language == "java" else "solution.py"

    with open(os.path.join(student_path, filename), "w") as f:
        f.write(code)

    for i, case in enumerate(
        question.test_cases.filter(is_hidden=True).order_by("order"), start=1
    ):
        with open(os.path.join(tests_path, f"{i}.in"), "w") as f_in:
            f_in.write(case.input_data)
        with open(os.path.join(tests_path, f"{i}.out"), "w") as f_out:
            f_out.write(case.expected_output)



# Run tests in Docker container and capture output
def run_docker(student_path, tests_path, language):
    image = f"code-runner-{language}"

    docker_cmd = [
        "docker", "run", "--rm",
        "--memory=256m",
        "--cpus=0.5",
        "--pids-limit=64",
        "-v", os.path.abspath(student_path) + ":/app/student",
        "-v", os.path.abspath(tests_path) + ":/app/tests",
        image
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

    # Run tests in Docker container
    activity_id = request.POST.get("activity_id")
    activity = get_object_or_404(Activity, id=activity_id)
    language = activity.course_topic.course.language.name.lower()

    write_test_files(code, question, student_path, tests_path, language)

    try:
        output = run_docker(student_path, tests_path, language)
        print("[DEBUG Docker Output]", output)

        data = json.loads(output)

        results = data.get("results", [])
        summary = data.get("summary", {})
        passed = summary.get("all_passed", False)


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

            # Calculate score
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.get("passed"))
            score = activity.weight * (passed_tests / total_tests) if total_tests > 0 else 0

            with transaction.atomic():
                # ✅ Create a new ActivityCompletion
                ac = ActivityCompletion.objects.create(
                    student=request.user,
                    activity=activity,
                    completed=passed,
                    score=score,
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

                # ✅ Update course-level progress and score
                update_student_progress(
                    request.user,
                    activity.course_topic.course
                )

        return redirect("code-question-results", ac.id)

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
    courses = get_all_courses("student", request.user)
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    question = activity.content_object

    # 🆕 All previous attempts (newest first)
    all_attempts = (
        ActivityCompletion.objects
        .filter(student=request.user, activity=activity)
        .order_by("-date_completed")
    )

    latest_submission = (
        CodeSubmission.objects
        .filter(activity_completion=ac)
        .order_by("-created")
        .first()
    )

    unit = activity.course_topic.unit
    course_unit = CourseUnit.objects.select_related("course").filter(unit=unit).first()
    course_id = course_unit.course.id if course_unit else None
    
    if latest_submission and latest_submission.summary:
        passed = latest_submission.summary.get("passed", 0)
        total = latest_submission.summary.get("total", 1)
        all_passed = latest_submission.summary.get("all_passed", False)
        pct = round((passed / total) * 100) if total else 0
        summary = {
            "passed": passed,
            "total": total,
            "all_passed": all_passed,
            "pct": pct,
        }
    else:
        summary = {
            "passed": 0,
            "total": 0,
            "all_passed": False,
            "pct": 0,
        }


    context = {
        "question": question,
        "activity": activity,
        "results": latest_submission.results if latest_submission else [],
        "summary": summary,
        "course_id": course_id,
        "all_attempts": all_attempts,
        "courses": courses,
    }

    return render(request, "base/main/code_results.html", context)

