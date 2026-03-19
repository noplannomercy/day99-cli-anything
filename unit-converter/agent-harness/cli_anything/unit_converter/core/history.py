import json
import os
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_unit_converter_history.json")


def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_entry(category: str, value: float, from_unit: str, to_unit: str, result: float):
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "value": value,
        "from": from_unit,
        "to": to_unit,
        "result": result,
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
