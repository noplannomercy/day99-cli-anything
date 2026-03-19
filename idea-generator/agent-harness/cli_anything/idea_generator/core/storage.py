import json
import os
from datetime import datetime

STORAGE_FILE = os.path.join(
    os.path.expanduser("~"), ".cli_anything_idea_generator_favorites.json"
)
MAX_FAVORITES = 20


def load_favorites() -> list:
    if not os.path.exists(STORAGE_FILE):
        return []
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_all(favorites: list) -> None:
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)


def save_favorite(category: str, text: str) -> dict | None:
    favorites = load_favorites()
    # Deduplicate by text+category
    if any(f["text"] == text and f["category"] == category for f in favorites):
        return None
    entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "category": category,
        "text": text,
        "timestamp": datetime.now().isoformat(),
    }
    favorites.insert(0, entry)
    # Enforce max
    while len(favorites) > MAX_FAVORITES:
        favorites.pop()
    _save_all(favorites)
    return entry


def remove_favorite(fav_id: int) -> bool:
    favorites = load_favorites()
    original_len = len(favorites)
    favorites = [f for f in favorites if f["id"] != fav_id]
    if len(favorites) == original_len:
        return False
    _save_all(favorites)
    return True


def clear_favorites() -> int:
    count = len(load_favorites())
    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)
    return count
