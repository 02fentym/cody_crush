import os
import uuid
import json
import subprocess
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from base.decorators import allowed_roles

from base.models import CodeQuestion, ActivityCompletion, Activity, Course, CourseUnit


def submit_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    course_id = request.POST.get("course_id")
    code = request.POST.get("code")
    language = request.POST.get("language", "python")
    question_id = request.POST.get("question_id")

    if not code or not question_id:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    # Create temp dir for this submission
    submission_id = str(uuid.uuid4())
    base_path = os.path.join(settings.MEDIA_ROOT, "submissions", submission_id)
    student_path = os.path.join(base_path, "student")
    tests_path = os.path.join(base_path, "tests")

    os.makedirs(student_path, exist_ok=True)
    os.makedirs(tests_path, exist_ok=True)

    # Write student's code
    with open(os.path.join(student_path, "solution.py"), "w") as f:
        f.write(code)

    question = get_object_or_404(CodeQuestion, id=question_id)
    test_cases = question.test_cases.filter(is_hidden=True).order_by("order")

    for i, case in enumerate(test_cases, start=1):
        with open(os.path.join(tests_path, f"{i}.in"), "w") as f_in:
            f_in.write(case.input_data)
        with open(os.path.join(tests_path, f"{i}.out"), "w") as f_out:
            f_out.write(case.expected_output)

    # Run Docker
    docker_cmd = [
        "docker", "run", "--rm",
        "--memory=256m",
        "--cpus=0.5",
        "--pids-limit=64",
        "-v", os.path.abspath(student_path) + ":/app/student",
        "-v", os.path.abspath(tests_path) + ":/app/tests",
        "code-runner-python"
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        output = result.stdout.decode().strip()
        data = json.loads(output)

        results = data.get("results", [])
        summary = data.get("summary", {})

        # Save completion only if all tests passed
        activity = Activity.objects.filter(content_type__model="codequestion", object_id=question.id).first()
        if activity and request.user.is_authenticated and summary.get("all_passed"):
            ActivityCompletion.objects.update_or_create(
                student=request.user,
                activity=activity,
                defaults={"completed": True}
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


@login_required(login_url="login")
@allowed_roles(["student"])
def code_question_results(request, ac_id):
    courses = Course.objects.filter(students=request.user)
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    question = activity.content_object

    unit = activity.course_topic.unit
    course_unit = CourseUnit.objects.select_related("course").filter(unit=unit).first()
    course_id = course_unit.course.id if course_unit else None

    context = {
        "question": question,
        "activity": activity,
        "results": [],  # optionally ac.submission_data if storing
        "summary": {"passed": 0, "total": 0, "all_passed": False},
        "course_id": course_id,
        "courses": courses,
    }

    return render(request, "base/main/code_results.html", context)

