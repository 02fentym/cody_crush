import requests
from urllib.parse import urlparse

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