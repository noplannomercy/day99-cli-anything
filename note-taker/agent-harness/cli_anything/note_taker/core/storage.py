import json
import os

NOTES_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_note_taker_notes.json")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_note_taker_settings.json")

DEFAULT_SETTINGS = {
    "theme": "dark",
    "autoSave": True,
    "defaultView": "preview",
}


def load_notes() -> list:
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_notes(notes: list) -> bool:
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            return {**DEFAULT_SETTINGS, **saved}
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> bool:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def export_to_json(notes: list) -> str:
    from datetime import datetime
    return json.dumps(
        {"notes": notes, "exported": datetime.now().isoformat(), "version": "1.0"},
        indent=2,
        ensure_ascii=False,
    )


def import_from_json(json_string: str) -> dict:
    try:
        data = json.loads(json_string)
        if "notes" in data and isinstance(data["notes"], list):
            return {"success": True, "notes": data["notes"]}
        return {"success": False, "error": "Invalid format"}
    except Exception as e:
        return {"success": False, "error": str(e)}
