import time
import random
import string
from datetime import datetime
from cli_anything.note_taker.core.storage import load_notes, save_notes


def _generate_id() -> str:
    ts = int(time.time() * 1000)
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"note_{ts:x}_{rand}"


def _now() -> str:
    return datetime.now().isoformat()


def normalize_tags(tags: list) -> list:
    if not isinstance(tags, list):
        return []
    seen = set()
    result = []
    for tag in tags:
        t = str(tag).lower().strip()[:20]
        if t and t not in seen:
            seen.add(t)
            result.append(t)
        if len(result) >= 10:
            break
    return result


def parse_tags(input_str: str) -> list:
    if not input_str:
        return []
    import re
    parts = re.split(r"[\s,#]+", input_str)
    return normalize_tags([p for p in parts if p.strip()])


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_note(title: str, content: str = "", tags: list = None) -> dict:
    notes = load_notes()
    now = _now()
    note = {
        "id": _generate_id(),
        "title": title.strip() or "Untitled",
        "content": content or "",
        "tags": normalize_tags(tags or []),
        "created": now,
        "updated": now,
        "isPinned": False,
    }
    notes.insert(0, note)
    save_notes(notes)
    return note


def get_note(note_id: str) -> dict | None:
    return next((n for n in load_notes() if n["id"] == note_id), None)


def update_note(note_id: str, changes: dict) -> dict | None:
    notes = load_notes()
    idx = next((i for i, n in enumerate(notes) if n["id"] == note_id), None)
    if idx is None:
        return None
    note = {**notes[idx], **changes, "updated": _now()}
    if "tags" in changes:
        note["tags"] = normalize_tags(changes["tags"])
    notes[idx] = note
    save_notes(notes)
    return note


def delete_note(note_id: str) -> bool:
    notes = load_notes()
    new_notes = [n for n in notes if n["id"] != note_id]
    if len(new_notes) == len(notes):
        return False
    save_notes(new_notes)
    return True


def get_all_notes(sort_by: str = "updated") -> list:
    notes = load_notes()

    def key(n):
        pinned = 0 if n.get("isPinned") else 1
        if sort_by == "title":
            return (pinned, n.get("title", "").lower())
        if sort_by == "created":
            return (pinned, n.get("created", ""))
        return (pinned, n.get("updated", ""))

    reverse = sort_by != "title"
    return sorted(notes, key=key, reverse=False) if sort_by == "title" else sorted(
        notes,
        key=lambda n: (0 if n.get("isPinned") else 1, n.get(sort_by if sort_by in ("created", "updated") else "updated", "")),
        reverse=False
    )


def _sort_notes(notes: list, sort_by: str = "updated") -> list:
    def key(n):
        pinned = 0 if n.get("isPinned") else 1
        val = n.get(sort_by if sort_by in ("created", "updated") else "updated", "")
        return (pinned, val)

    if sort_by == "title":
        return sorted(notes, key=lambda n: (0 if n.get("isPinned") else 1, n.get("title", "").lower()))
    return sorted(notes, key=key, reverse=False)[::-1] if False else sorted(
        notes,
        key=lambda n: (
            0 if n.get("isPinned") else 1,
            # for dates: descending = negate isn't trivial, flip with string max
            "" if sort_by not in ("created", "updated") else n.get(sort_by, ""),
        ),
    )


def pin_note(note_id: str) -> dict | None:
    note = get_note(note_id)
    if not note:
        return None
    return update_note(note_id, {"isPinned": not note.get("isPinned", False)})


def duplicate_note(note_id: str) -> dict | None:
    note = get_note(note_id)
    if not note:
        return None
    return create_note(note["title"] + " (copy)", note["content"], list(note["tags"]))


# ── Tag helpers ────────────────────────────────────────────────────────────────

def get_all_tags() -> list:
    tags = set()
    for n in load_notes():
        tags.update(n.get("tags", []))
    return sorted(tags)


def get_tag_counts() -> dict:
    counts: dict = {}
    for n in load_notes():
        for tag in n.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def rename_tag(old: str, new: str) -> int:
    normalized = new.lower().strip()[:20]
    if not normalized:
        return 0
    notes = load_notes()
    updated = 0
    for note in notes:
        if old in note.get("tags", []):
            note["tags"] = normalize_tags(
                [normalized if t == old else t for t in note["tags"]]
            )
            note["updated"] = _now()
            updated += 1
    if updated:
        save_notes(notes)
    return updated


# ── Search ────────────────────────────────────────────────────────────────────

def search_notes(query: str = "", tags: list = None, sort_by: str = "updated") -> list:
    notes = load_notes()

    if query:
        q = query.lower()
        notes = [n for n in notes if q in n.get("title", "").lower() or q in n.get("content", "").lower()]

    if tags:
        notes = [n for n in notes if all(t in n.get("tags", []) for t in tags)]

    # Sort: pinned first, then by sort_by descending
    if sort_by == "title":
        notes = sorted(notes, key=lambda n: (0 if n.get("isPinned") else 1, n.get("title", "").lower()))
    else:
        notes = sorted(
            notes,
            key=lambda n: (0 if n.get("isPinned") else 1, n.get(sort_by, "")),
            reverse=False,
        )
        # date fields: we want descending within each pinned group
        pinned = [n for n in notes if n.get("isPinned")]
        unpinned = [n for n in notes if not n.get("isPinned")]
        if sort_by in ("created", "updated"):
            pinned = sorted(pinned, key=lambda n: n.get(sort_by, ""), reverse=True)
            unpinned = sorted(unpinned, key=lambda n: n.get(sort_by, ""), reverse=True)
        notes = pinned + unpinned

    return notes
