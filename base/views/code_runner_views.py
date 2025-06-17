import os
import uuid
import shutil
import json
import subprocess
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt  # Remove if you’re using a CSRF token
def submit_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

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

    # Write the student's code
    with open(os.path.join(student_path, "solution.py"), "w") as f:
        f.write(code)

    # TODO: Load test files from DB and write to tests_path
    # For now, just copy sample ones from your dev folder
    dev_test_folder = "/Users/mikefenty/Library/CloudStorage/Dropbox/Programming/Django Projects/cody_crush/code_runner/python/tests"
    for filename in os.listdir(dev_test_folder):
        src = os.path.join(dev_test_folder, filename)
        dst = os.path.join(tests_path, filename)
        shutil.copyfile(src, dst)

    # Run Docker
    docker_cmd = [
        "docker", "run", "--rm",
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

        print("Docker exited with return code:", result.returncode)
        print("stdout:")
        print(result.stdout.decode())
        print("stderr:")
        print(result.stderr.decode())


        data = json.loads(output)
        return JsonResponse(data)
    except subprocess.TimeoutExpired:
        return JsonResponse({"error": "Code execution timed out"}, status=408)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Failed to parse grading output"}, status=500)


def test_code_component(request):
    return render(request, "components/code_editor.html")
