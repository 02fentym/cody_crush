import requests
from urllib.parse import urlparse
from base.models import Course, StudentCourseEnrollment, Activity, ActivityCompletion

# DMOJ: Gets metadata from a problem URL
def fetch_dmoj_metadata_from_url(url):
    print(f"URL: {url}")
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        print(f"Path Parts: {path_parts}")
        if len(path_parts) < 2 or path_parts[0] != 'problem':
            raise ValueError("Invalid DMOJ problem URL format.")

        print(f"Path Parts 1: {path_parts[1]}")
        problem_code = path_parts[1]
        api_url = f"https://dmoj.ca/api/v2/problem/{problem_code}"

        response = requests.get(api_url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            obj = data.get("data", {}).get("object", {})
            return {
                "problem_code": problem_code,
                "title": obj.get("name", problem_code),
                "points": obj.get("points", None),
            }
        elif response.status_code == 404:
            raise ValueError(f"Problem code '{problem_code}' not found on DMOJ.")
        else:
            raise ValueError(f"Unexpected response from DMOJ API: {response.status_code}")
    except Exception as e:
        print(f"Error fetching DMOJ metadata: {e}")
        return None

# DMOJ: Fetches user data
def fetch_dmoj_user_data(username):
    try:
        api_url = f"https://dmoj.ca/api/v2/user/{username}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            obj = data.get("data", {}).get("object", {})
            return obj.get("solved_problems", [])
        elif response.status_code == 404:
            raise ValueError(f"User '{username}' not found on DMOJ.")
        else:
            raise ValueError(f"Unexpected response from DMOJ API: {response.status_code}")
    except Exception as e:
        print(f"Error fetching DMOJ user data: {e}")
        return None



# Code Question: Extracts test cases from a zip file (YAML + .in/.out files)
def extract_code_question_zip(zip_file):
    import tempfile, zipfile, os, yaml

    test_cases = []
    meta = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file) as zf:
            zf.extractall(temp_dir)

        # Locate YAML file
        yaml_file = next((f for f in os.listdir(temp_dir) if f.endswith(".yaml") or f.endswith(".yml")), None)
        if not yaml_file:
            return [], {}  # No YAML found

        with open(os.path.join(temp_dir, yaml_file), "r") as f:
            meta = yaml.safe_load(f) or {}

        for i, case in enumerate(meta.get("test_cases", [])):
            input_data = case.get("input", "")
            expected_output = case.get("output", "")

            # If input is a .in file reference
            if input_data.endswith(".in"):
                path = os.path.join(temp_dir, input_data)
                if os.path.exists(path):
                    with open(path, "r") as f:
                        input_data = f.read()

            # If output is a .out file reference
            if expected_output.endswith(".out"):
                path = os.path.join(temp_dir, expected_output)
                if os.path.exists(path):
                    with open(path, "r") as f:
                        expected_output = f.read()

            test_cases.append({
                "input_data": input_data,
                "expected_output": expected_output,
                "order": i,
                "test_style": meta.get("test_style", "stdin")
            })

    return test_cases, meta


# Code Question: Extracts test cases from a YAML file
def extract_code_question_yaml(yaml_file):
    import tempfile, os, yaml

    test_cases = []

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        for chunk in yaml_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    with open(tmp_path, "r") as f:
        meta = yaml.safe_load(f) or {}

    os.remove(tmp_path)

    for i, case in enumerate(meta.get("test_cases", [])):
        test_cases.append({
            "input_data": case.get("input", ""),
            "expected_output": case.get("output", ""),
            "order": i,
            "test_style": meta.get("test_style", "stdin")
        })

    return test_cases, meta


# Returns all courses a user is enrolled in
def get_all_courses(role, user):
    if role == "student":
        enrollments = StudentCourseEnrollment.objects.filter(student=user)
        courses = [enrollment.course for enrollment in enrollments]
    else:
        courses = Course.objects.filter(teacher=user)
    return courses


# Updates the progress and score of a student in a course
def update_student_progress(student, course):
    # Get all activities for this course
    activities = Activity.objects.filter(
        course_topic__unit__courseunit__course=course
    )

    completions = ActivityCompletion.objects.filter(
        student=student,
        activity__in=activities
    ).select_related("activity")

    total_activities = len(activities)
    completed_activities = sum(1 for ac in completions if ac.completed)
    progress = round((completed_activities / total_activities) * 100, 1) if total_activities > 0 else 0

    # Weighted average score
    total_score = 0
    total_weight = 0

    for ac in completions:
        if ac.completed and ac.score is not None:
            weight = ac.activity.weight or 1
            total_weight += weight
            total_score += ac.score
           

    score = round(total_score / total_weight * 100, 2) if total_weight > 0 else 0.0

    # Save to StudentCourseEnrollment
    enrollment = StudentCourseEnrollment.objects.get(student=student, course=course)
    enrollment.progress = progress
    enrollment.score = score
    enrollment.save()
