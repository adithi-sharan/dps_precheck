import json
from pathlib import Path


DATA_DIR = Path("data")


def load_records() -> list[dict]:
    with open(DATA_DIR / "existing_records.json", "r") as f:
        return json.load(f)


def load_submissions() -> list[dict]:
    file_path = DATA_DIR / "sample_submissions.json"

    if not file_path.exists():
        with open(file_path, "w") as f:
            json.dump([], f)

    with open(file_path, "r") as f:
        return json.load(f)


def save_submission(submission: dict) -> None:
    submissions = load_submissions()
    submissions.append(submission)

    with open(DATA_DIR / "sample_submissions.json", "w") as f:
        json.dump(submissions, f, indent=2)