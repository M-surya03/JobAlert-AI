import json
import os
import tempfile

STATE_FILE = os.getenv("PROCESSED_EMAILS_FILE", "processed_emails.json")


def load_processed():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{STATE_FILE} must contain a JSON array.")
    return set(str(item) for item in data)


def save_processed(processed):
    directory = os.path.dirname(os.path.abspath(STATE_FILE))
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="processed-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(sorted(processed), handle, indent=2)
        os.replace(temporary, STATE_FILE)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
