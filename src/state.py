import json
import os


def load_sent_ids(path: str) -> set:
    """Load already-sent listing IDs from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(str(x) for x in data) if isinstance(data, list) else set()
    except FileNotFoundError:
        return set()


def save_sent_ids(path: str, sent_ids: set):
    """Persist sent listing IDs back to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(sent_ids), f, ensure_ascii=False, indent=2)
