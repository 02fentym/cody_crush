import subprocess
import os
import glob
import json

student_file = "student/solution.py"
test_dir = "tests"
timeout_seconds = 2

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_test(input_data, expected_output):
    try:
        result = subprocess.run(
            ["python", student_file],
            input=input_data.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds
        )
        actual_output = result.stdout.decode().strip()
        expected_output = expected_output.strip()
        return actual_output == expected_output, actual_output, expected_output, result.stderr.decode()
    except subprocess.TimeoutExpired:
        return False, "", expected_output, "Timeout"

def main():
    in_files = sorted(glob.glob(os.path.join(test_dir, "*.in")))
    results = []

    for in_file in in_files:
        test_name = os.path.basename(in_file).replace(".in", "")
        out_file = os.path.join(test_dir, f"{test_name}.out")

        input_data = load_file(in_file)
        expected_output = load_file(out_file) if os.path.exists(out_file) else ""

        passed, actual, expected, errors = run_test(input_data, expected_output)
        results.append({
            "test": test_name,
            "passed": passed,
            "expected": expected,
            "actual": actual,
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
