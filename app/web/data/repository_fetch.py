import os

import requests
import zipfile
import tempfile


def get_student_submission(exercise_id: int, user_id: int, commit_hash: str) -> str:
    unique_folder = f"repositories/{exercise_id}/users/{user_id}"
    path = f"{unique_folder}/{commit_hash}"
    if os.path.isdir(path):
        return path
    os.remove(unique_folder)
    artemis_url = f"/api/v1/public/pyris/data/programming-exercises/{exercise_id}/submissions/{commit_hash}/repository"
    _download(artemis_url, path)
    return path


def get_template_repository(exercise_id: int, commit_hash: str) -> str:
    unique_folder = f"repositories/{exercise_id}/template"
    path = f"{unique_folder}/{commit_hash}"
    if os.path.isdir(path):
        return path
    os.remove(unique_folder)
    artemis_url = f"/api/v1/public/pyris/data/programming-exercises/{exercise_id}/repositories/template"
    _download(artemis_url, path)
    return path


def get_solution_repository(exercise_id: int, commit_hash: str) -> str:
    unique_folder = f"repositories/{exercise_id}/solution"
    path = f"{unique_folder}/{commit_hash}"
    if os.path.isdir(path):
        return path
    os.remove(unique_folder)
    artemis_url = f"/api/v1/public/pyris/data/programming-exercises/{exercise_id}/repositories/solution"
    _download(artemis_url, path)
    return path


def get_test_repository(exercise_id: int, commit_hash: str) -> str:
    unique_folder = f"repositories/{exercise_id}/test"
    path = f"{unique_folder}/{commit_hash}"
    if os.path.isdir(path):
        return path
    os.remove(unique_folder)
    artemis_url = f"/api/v1/public/pyris/data/programming-exercises/{exercise_id}/repositories/test"
    _download(artemis_url, path)
    return path


def _download(artemis_url: str, file_path: str):
    os.makedirs(file_path, exist_ok=False)
    with requests.get(artemis_url, stream=True) as result:
        result.raise_for_status()
        with tempfile.NamedTemporaryFile() as temp_file:
            for chunk in result.iter_content(chunk_size=8 * 1024):
                temp_file.write(chunk)
            with zipfile.ZipFile(temp_file, "r") as zip_ref:
                zip_ref.extractall(file_path)
