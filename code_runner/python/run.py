import subprocess
import os
import glob
import json
import importlib.util
import sys
import io

student_file = "student/solution.py"
test_dir = "tests"
timeout_seconds = 2

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_stdin_test(input_data, expected_output):
    try:
        result = subprocess.run(
            ["python", student_file],
            input=input_data.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds
        )
        actual_output = result.stdout.decode().strip()
        return actual_output == expected_output.strip(), actual_output, result.stderr.decode()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def run_exec_test(input_code, expected_output):
    try:
        # Redirect stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Load student code as module
        spec = importlib.util.spec_from_file_location("solution", student_file)
        solution = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(solution)

        # Execute the test case input in isolated scope
        local_scope = {"solution": solution}
        exec(input_code, {}, local_scope)

        # Capture output
        actual_output = sys.stdout.getvalue().strip()
        sys.stdout = old_stdout
        return actual_output == expected_output.strip(), actual_output, ""
    except Exception as e:
        sys.stdout = old_stdout
        return False, "", str(e)

def main():
    in_files = sorted(glob.glob(os.path.join(test_dir, "*.in")))
    results = []

    for in_file in in_files:
        test_name = os.path.basename(in_file).replace(".in", "")
        out_file = os.path.join(test_dir, f"{test_name}.out")

        input_data = load_file(in_file)
        expected_output = load_file(out_file) if os.path.exists(out_file) else ""
        style = "exec" if input_data.lstrip().startswith("#exec") else "stdin"

        if style == "exec":
            input_data = input_data.replace("#exec", "", 1).lstrip()
            passed, actual, errors = run_exec_test(input_data, expected_output)
        else:
            passed, actual, errors = run_stdin_test(input_data, expected_output)

        results.append({
            "test": test_name,
            "passed": passed,
            "expected": expected_output.strip(),
            "actual": actual.strip(),
            "error": errors.strip()
        })

    summary = {
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
        "all_passed": all(r["passed"] for r in results)
    }

    print(json.dumps({
        "results": results,
        "summary": summary
    }))

if __name__ == "__main__":
    main()
