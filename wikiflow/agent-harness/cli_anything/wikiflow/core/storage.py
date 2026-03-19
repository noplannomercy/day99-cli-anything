"""
storage.py — WikiFlow 전체 CRUD 레이어
LocalStorage(JSON) → ~/.cli_anything_wikiflow_*.json 파일로 대체
"""
import json
import os
import uuid
from datetime import datetime

BASE = os.path.expanduser("~")

def _path(key: str) -> str:
    return os.path.join(BASE, f".cli_anything_wikiflow_{key}.json")

def _load(key: str) -> list:
    p = _path(key)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save(key: str, items: list) -> None:
    with open(_path(key), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def _now() -> str:
    return datetime.now().isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

# ── Workspace ─────────────────────────────────────────────────────────────────

def get_workspaces() -> list:
    return _load("workspaces")

def create_workspace(name: str, description: str = "", icon: str = "📁") -> dict:
    now = _now()
    w = {"id": _uuid(), "name": name, "description": description, "icon": icon, "createdAt": now, "updatedAt": now}
    items = _load("workspaces")
    items.append(w)
    _save("workspaces", items)
    return w

def update_workspace(id: str, **kwargs) -> dict | None:
    items = _load("workspaces")
    idx = next((i for i, w in enumerate(items) if w["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs, "updatedAt": _now()}
    _save("workspaces", items)
    return items[idx]

def delete_workspace(id: str) -> bool:
    items = _load("workspaces")
    new = [w for w in items if w["id"] != id]
    if len(new) == len(items):
        return False
    _save("workspaces", new)
    # Cascade folders
    folders = _load("folders")
    folder_ids = {f["id"] for f in folders if f["workspaceId"] == id}
    _save("folders", [f for f in folders if f["workspaceId"] != id])
    # Cascade documents
    docs = _load("documents")
    doc_ids = {d["id"] for d in docs if d["workspaceId"] == id}
    _save("documents", [d for d in docs if d["workspaceId"] != id])
    _cascade_delete_docs(doc_ids)
    return True

def _cascade_delete_docs(doc_ids: set) -> None:
    if not doc_ids:
        return
    for key in ("versions", "comments", "shares", "documentTags", "favorites"):
        field = "documentId" if key != "favorites" else "documentId"
        _save(key, [x for x in _load(key) if x.get("documentId") not in doc_ids])

# ── Member ────────────────────────────────────────────────────────────────────

def get_members() -> list:
    return _load("members")

def create_member(name: str, email: str, role: str = "editor", avatar: str = "") -> dict:
    m = {"id": _uuid(), "name": name, "email": email, "role": role, "avatar": avatar, "createdAt": _now()}
    items = _load("members")
    items.append(m)
    _save("members", items)
    return m

def update_member(id: str, **kwargs) -> dict | None:
    items = _load("members")
    idx = next((i for i, m in enumerate(items) if m["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs}
    _save("members", items)
    return items[idx]

def delete_member(id: str) -> bool:
    items = _load("members")
    new = [m for m in items if m["id"] != id]
    if len(new) == len(items):
        return False
    _save("members", new)
    _save("shares", [s for s in _load("shares") if s["memberId"] != id])
    _save("favorites", [f for f in _load("favorites") if f["memberId"] != id])
    _save("comments", [c for c in _load("comments") if c["authorId"] != id])
    return True

# ── Folder ────────────────────────────────────────────────────────────────────

def get_folders(workspace_id: str) -> list:
    return [f for f in _load("folders") if f["workspaceId"] == workspace_id]

def get_folder_tree(workspace_id: str) -> list:
    folders = get_folders(workspace_id)
    node_map = {f["id"]: {**f, "children": []} for f in folders}
    roots = []
    for node in node_map.values():
        pid = node.get("parentId")
        if pid and pid in node_map:
            node_map[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots

def create_folder(workspace_id: str, name: str, parent_id: str | None = None, icon: str = "📂", order: int = 0) -> dict:
    now = _now()
    f = {"id": _uuid(), "workspaceId": workspace_id, "parentId": parent_id, "name": name, "icon": icon, "order": order, "createdAt": now, "updatedAt": now}
    items = _load("folders")
    items.append(f)
    _save("folders", items)
    return f

def update_folder(id: str, **kwargs) -> dict | None:
    items = _load("folders")
    idx = next((i for i, f in enumerate(items) if f["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs, "updatedAt": _now()}
    _save("folders", items)
    return items[idx]

def delete_folder(id: str) -> bool:
    all_folders = _load("folders")
    # Collect all descendant IDs
    ids_to_delete = {id}
    changed = True
    while changed:
        changed = False
        for f in all_folders:
            if f.get("parentId") in ids_to_delete and f["id"] not in ids_to_delete:
                ids_to_delete.add(f["id"])
                changed = True
    new_folders = [f for f in all_folders if f["id"] not in ids_to_delete]
    if len(new_folders) == len(all_folders):
        return False
    _save("folders", new_folders)
    docs = _load("documents")
    doc_ids = {d["id"] for d in docs if d.get("folderId") in ids_to_delete}
    _save("documents", [d for d in docs if d.get("folderId") not in ids_to_delete])
    _cascade_delete_docs(doc_ids)
    return True

# ── Document ──────────────────────────────────────────────────────────────────

def get_documents(workspace_id: str = None, folder_id: str = None, status: str = None, tag_id: str = None) -> list:
    docs = _load("documents")
    if workspace_id:
        docs = [d for d in docs if d["workspaceId"] == workspace_id]
    if folder_id:
        docs = [d for d in docs if d.get("folderId") == folder_id]
    if status:
        docs = [d for d in docs if d["status"] == status]
    if tag_id:
        tagged = {dt["documentId"] for dt in _load("documentTags") if dt["tagId"] == tag_id}
        docs = [d for d in docs if d["id"] in tagged]
    return docs

def get_document(id: str) -> dict | None:
    return next((d for d in _load("documents") if d["id"] == id), None)

def create_document(workspace_id: str, title: str, content: str = "", excerpt: str = "",
                    status: str = "draft", folder_id: str | None = None,
                    created_by: str = "cli", is_pinned: bool = False) -> dict:
    now = _now()
    doc = {"id": _uuid(), "workspaceId": workspace_id, "folderId": folder_id,
           "title": title, "content": content, "excerpt": excerpt,
           "status": status, "isPinned": is_pinned, "viewCount": 0,
           "createdBy": created_by, "lastEditedBy": created_by,
           "createdAt": now, "updatedAt": now}
    items = _load("documents")
    items.append(doc)
    _save("documents", items)
    return doc

def update_document(id: str, **kwargs) -> dict | None:
    items = _load("documents")
    idx = next((i for i, d in enumerate(items) if d["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs, "updatedAt": _now()}
    _save("documents", items)
    return items[idx]

def delete_document(id: str) -> bool:
    items = _load("documents")
    new = [d for d in items if d["id"] != id]
    if len(new) == len(items):
        return False
    _save("documents", new)
    _cascade_delete_docs({id})
    return True

def search_documents(query: str) -> list:
    q = query.lower()
    return [d for d in _load("documents") if q in d["title"].lower() or q in d.get("content", "").lower()]

def increment_view_count(id: str) -> None:
    items = _load("documents")
    idx = next((i for i, d in enumerate(items) if d["id"] == id), None)
    if idx is not None:
        items[idx]["viewCount"] = items[idx].get("viewCount", 0) + 1
        _save("documents", items)

# ── Version ───────────────────────────────────────────────────────────────────

def get_versions(document_id: str) -> list:
    vs = [v for v in _load("versions") if v["documentId"] == document_id]
    return sorted(vs, key=lambda v: v["versionNumber"], reverse=True)

def create_version(document_id: str, title: str, content: str, change_note: str = "", created_by: str = "cli") -> dict:
    existing = get_versions(document_id)
    max_num = existing[0]["versionNumber"] if existing else 0
    v = {"id": _uuid(), "documentId": document_id, "versionNumber": max_num + 1,
         "title": title, "content": content, "changeNote": change_note,
         "createdBy": created_by, "createdAt": _now()}
    items = _load("versions")
    items.append(v)
    _save("versions", items)
    return v

def restore_version(version_id: str) -> dict | None:
    v = next((x for x in _load("versions") if x["id"] == version_id), None)
    if not v:
        return None
    doc = update_document(v["documentId"], title=v["title"], content=v["content"])
    if doc:
        create_version(v["documentId"], v["title"], v["content"],
                       change_note=f"Restored from version {v['versionNumber']}", created_by=v["createdBy"])
    return doc

# ── Tag ───────────────────────────────────────────────────────────────────────

def get_tags() -> list:
    return _load("tags")

def create_tag(name: str, color: str = "#6366f1") -> dict:
    t = {"id": _uuid(), "name": name, "color": color, "createdAt": _now()}
    items = _load("tags")
    items.append(t)
    _save("tags", items)
    return t

def update_tag(id: str, **kwargs) -> dict | None:
    items = _load("tags")
    idx = next((i for i, t in enumerate(items) if t["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs}
    _save("tags", items)
    return items[idx]

def delete_tag(id: str) -> bool:
    items = _load("tags")
    new = [t for t in items if t["id"] != id]
    if len(new) == len(items):
        return False
    _save("tags", new)
    _save("documentTags", [dt for dt in _load("documentTags") if dt["tagId"] != id])
    return True

def add_tag_to_document(document_id: str, tag_id: str) -> dict:
    items = _load("documentTags")
    existing = next((x for x in items if x["documentId"] == document_id and x["tagId"] == tag_id), None)
    if existing:
        return existing
    dt = {"id": _uuid(), "documentId": document_id, "tagId": tag_id}
    items.append(dt)
    _save("documentTags", items)
    return dt

def remove_tag_from_document(document_id: str, tag_id: str) -> None:
    _save("documentTags", [dt for dt in _load("documentTags")
                           if not (dt["documentId"] == document_id and dt["tagId"] == tag_id)])

def get_document_tags(document_id: str) -> list:
    return [dt for dt in _load("documentTags") if dt["documentId"] == document_id]

# ── Comment ───────────────────────────────────────────────────────────────────

def get_comments(document_id: str) -> list:
    cs = [c for c in _load("comments") if c["documentId"] == document_id]
    return sorted(cs, key=lambda c: c["createdAt"])

def create_comment(document_id: str, author_id: str, content: str, parent_id: str | None = None) -> dict:
    now = _now()
    c = {"id": _uuid(), "documentId": document_id, "parentId": parent_id,
         "authorId": author_id, "content": content, "isResolved": False,
         "createdAt": now, "updatedAt": now}
    items = _load("comments")
    items.append(c)
    _save("comments", items)
    return c

def update_comment(id: str, **kwargs) -> dict | None:
    items = _load("comments")
    idx = next((i for i, c in enumerate(items) if c["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs, "updatedAt": _now()}
    _save("comments", items)
    return items[idx]

def delete_comment(id: str) -> bool:
    items = _load("comments")
    new = [c for c in items if c["id"] != id and c.get("parentId") != id]
    if len(new) == len(items):
        return False
    _save("comments", new)
    return True

# ── Share ─────────────────────────────────────────────────────────────────────

def get_shares(document_id: str) -> list:
    return [s for s in _load("shares") if s["documentId"] == document_id]

def create_share(document_id: str, member_id: str, permission: str = "view") -> dict:
    items = _load("shares")
    existing = next((s for s in items if s["documentId"] == document_id and s["memberId"] == member_id), None)
    if existing:
        return existing
    s = {"id": _uuid(), "documentId": document_id, "memberId": member_id,
         "permission": permission, "createdAt": _now()}
    items.append(s)
    _save("shares", items)
    return s

def delete_share(id: str) -> bool:
    items = _load("shares")
    new = [s for s in items if s["id"] != id]
    if len(new) == len(items):
        return False
    _save("shares", new)
    return True

# ── Template ──────────────────────────────────────────────────────────────────

def get_templates() -> list:
    return _load("templates")

def create_template(title: str, content: str, description: str = "",
                    category: str = "other", created_by: str = "cli") -> dict:
    t = {"id": _uuid(), "title": title, "description": description,
         "content": content, "category": category, "createdBy": created_by,
         "createdAt": _now()}
    items = _load("templates")
    items.append(t)
    _save("templates", items)
    return t

def update_template(id: str, **kwargs) -> dict | None:
    items = _load("templates")
    idx = next((i for i, t in enumerate(items) if t["id"] == id), None)
    if idx is None:
        return None
    items[idx] = {**items[idx], **kwargs}
    _save("templates", items)
    return items[idx]

def delete_template(id: str) -> bool:
    items = _load("templates")
    new = [t for t in items if t["id"] != id]
    if len(new) == len(items):
        return False
    _save("templates", new)
    return True

# ── Favorite ──────────────────────────────────────────────────────────────────

def get_favorites(member_id: str) -> list:
    return [f for f in _load("favorites") if f["memberId"] == member_id]

def add_favorite(member_id: str, document_id: str) -> dict:
    items = _load("favorites")
    existing = next((f for f in items if f["memberId"] == member_id and f["documentId"] == document_id), None)
    if existing:
        return existing
    fav = {"id": _uuid(), "memberId": member_id, "documentId": document_id, "createdAt": _now()}
    items.append(fav)
    _save("favorites", items)
    return fav

def remove_favorite(member_id: str, document_id: str) -> bool:
    items = _load("favorites")
    new = [f for f in items if not (f["memberId"] == member_id and f["documentId"] == document_id)]
    if len(new) == len(items):
        return False
    _save("favorites", new)
    return True

# ── Dashboard ─────────────────────────────────────────────────────────────────

def get_dashboard() -> dict:
    all_docs = _load("documents")
    all_workspaces = _load("workspaces")
    all_favs = _load("favorites")

    recent_docs = sorted(all_docs, key=lambda d: d["updatedAt"], reverse=True)[:5]
    fav_ids = {f["documentId"] for f in all_favs}
    fav_docs = [d for d in all_docs if d["id"] in fav_ids]
    workspace_stats = [{"workspace": w, "documentCount": sum(1 for d in all_docs if d["workspaceId"] == w["id"])}
                       for w in all_workspaces]

    activities = []
    for doc in all_docs:
        activities.append({"id": f"created-{doc['id']}", "type": "created",
                           "documentId": doc["id"], "documentTitle": doc["title"], "timestamp": doc["createdAt"]})
        if doc["updatedAt"] != doc["createdAt"]:
            activities.append({"id": f"updated-{doc['id']}", "type": "updated",
                               "documentId": doc["id"], "documentTitle": doc["title"], "timestamp": doc["updatedAt"]})
    recent_activity = sorted(activities, key=lambda a: a["timestamp"], reverse=True)[:10]

    return {"recentDocuments": recent_docs, "favoriteDocuments": fav_docs,
            "workspaceStats": workspace_stats, "recentActivity": recent_activity}
