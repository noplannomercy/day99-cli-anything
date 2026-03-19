import json, sys
import click
from cli_anything.wikiflow.core import storage as S
from cli_anything.wikiflow.core.logger import log

DOC_STATUSES = ["draft", "published", "archived"]
MEMBER_ROLES = ["admin", "editor", "viewer"]
SHARE_PERMS = ["view", "edit", "admin"]
TEMPLATE_CATS = ["meeting-notes", "proposal", "technical-doc", "other"]


def j(data, ctx):
    if ctx.obj["json"]:
        click.echo(json.dumps(data, ensure_ascii=False))
    return data

def err(msg, ctx):
    d = {"error": msg}
    click.echo(json.dumps(d) if ctx.obj["json"] else f"Error: {msg}", err=not ctx.obj["json"])
    sys.exit(1)


@click.group()
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
def cli(ctx, json_output):
    """WikiFlow CLI - Workspace, document, version, tag, comment management."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# workspace

@cli.group()
def workspace():
    """Workspace management."""
    pass

@workspace.command("list")
@click.pass_context
def ws_list(ctx):
    rows = S.get_workspaces()
    log("workspace_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{w['id']}] {w['icon']} {w['name']}" for w in rows) or "No workspaces.")

@workspace.command("create")
@click.option("--name", required=True)
@click.option("--description", default="")
@click.option("--icon", default="folder")
@click.pass_context
def ws_create(ctx, name, description, icon):
    r = S.create_workspace(name, description, icon)
    log("workspace_create", name=name, id=r["id"])
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['name']}")

@workspace.command("update")
@click.argument("workspace_id")
@click.option("--name", default=None)
@click.option("--description", default=None)
@click.option("--icon", default=None)
@click.pass_context
def ws_update(ctx, workspace_id, name, description, icon):
    kwargs = {k: v for k, v in [("name", name), ("description", description), ("icon", icon)] if v is not None}
    r = S.update_workspace(workspace_id, **kwargs)
    log("workspace_update", id=workspace_id)
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Updated: {r['name']}")

@workspace.command("delete")
@click.argument("workspace_id")
@click.pass_context
def ws_delete(ctx, workspace_id):
    ok = S.delete_workspace(workspace_id)
    log("workspace_delete", id=workspace_id, ok=ok)
    if not ok: err("not_found", ctx)
    d = {"status": "deleted", "id": workspace_id}
    if ctx.obj["json"]: click.echo(json.dumps(d))
    else: click.echo(f"Deleted workspace {workspace_id} (cascade complete).")


# member

@cli.group()
def member():
    """Member management."""
    pass

@member.command("list")
@click.pass_context
def mb_list(ctx):
    rows = S.get_members()
    log("member_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{m['id']}] {m['name']} <{m['email']}> [{m['role']}]" for m in rows) or "No members.")

@member.command("create")
@click.option("--name", required=True)
@click.option("--email", required=True)
@click.option("--role", type=click.Choice(MEMBER_ROLES), default="editor")
@click.option("--avatar", default="")
@click.pass_context
def mb_create(ctx, name, email, role, avatar):
    r = S.create_member(name, email, role, avatar)
    log("member_create", name=name, email=email)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['name']}")

@member.command("update")
@click.argument("member_id")
@click.option("--name", default=None)
@click.option("--email", default=None)
@click.option("--role", type=click.Choice(MEMBER_ROLES), default=None)
@click.pass_context
def mb_update(ctx, member_id, name, email, role):
    kwargs = {k: v for k, v in [("name", name), ("email", email), ("role", role)] if v is not None}
    r = S.update_member(member_id, **kwargs)
    log("member_update", id=member_id)
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Updated: {r['name']}")

@member.command("delete")
@click.argument("member_id")
@click.pass_context
def mb_delete(ctx, member_id):
    ok = S.delete_member(member_id)
    log("member_delete", id=member_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted member {member_id}.")


# folder

@cli.group()
def folder():
    """Folder management."""
    pass

@folder.command("list")
@click.argument("workspace_id")
@click.pass_context
def fl_list(ctx, workspace_id):
    rows = S.get_folders(workspace_id)
    log("folder_list", workspace=workspace_id, count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{f['id']}] {f['icon']} {f['name']} (parent={f.get('parentId','root')})" for f in rows) or "No folders.")

@folder.command("tree")
@click.argument("workspace_id")
@click.pass_context
def fl_tree(ctx, workspace_id):
    tree = S.get_folder_tree(workspace_id)
    log("folder_tree", workspace=workspace_id)
    if ctx.obj["json"]: click.echo(json.dumps(tree, ensure_ascii=False))
    else:
        def _print(nodes, indent=0):
            for n in nodes:
                click.echo("  " * indent + f"[{n['id']}] {n['icon']} {n['name']}")
                _print(n.get("children", []), indent + 1)
        _print(tree)

@folder.command("create")
@click.option("--workspace-id", required=True)
@click.option("--name", required=True)
@click.option("--parent-id", default=None)
@click.option("--icon", default="folder")
@click.pass_context
def fl_create(ctx, workspace_id, name, parent_id, icon):
    r = S.create_folder(workspace_id, name, parent_id, icon)
    log("folder_create", name=name, workspace=workspace_id)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['name']}")

@folder.command("delete")
@click.argument("folder_id")
@click.pass_context
def fl_delete(ctx, folder_id):
    ok = S.delete_folder(folder_id)
    log("folder_delete", id=folder_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted folder {folder_id} (cascade complete).")


# doc

@cli.group()
def doc():
    """Document management."""
    pass

@doc.command("list")
@click.option("--workspace-id", default=None)
@click.option("--folder-id", default=None)
@click.option("--status", type=click.Choice(DOC_STATUSES), default=None)
@click.option("--tag-id", default=None)
@click.option("--limit", default=20)
@click.pass_context
def doc_list(ctx, workspace_id, folder_id, status, tag_id, limit):
    rows = S.get_documents(workspace_id, folder_id, status, tag_id)[:limit]
    log("doc_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{d['id']}] {'[PIN]' if d['isPinned'] else ''} {d['title']} [{d['status']}] views={d['viewCount']}" for d in rows) or "No documents.")

@doc.command("get")
@click.argument("doc_id")
@click.option("--increment-view", is_flag=True)
@click.pass_context
def doc_get(ctx, doc_id, increment_view):
    if increment_view: S.increment_view_count(doc_id)
    d = S.get_document(doc_id)
    log("doc_get", id=doc_id, found=d is not None)
    if not d: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(d, ensure_ascii=False))
    else:
        click.echo(f"Title:   {d['title']}\nStatus:  {d['status']}\nPinned:  {d['isPinned']}\nViews:   {d['viewCount']}\nCreated: {d['createdAt'][:19]}\n\n{d['content']}")

@doc.command("create")
@click.option("--workspace-id", required=True)
@click.option("--title", required=True)
@click.option("--content", default="")
@click.option("--excerpt", default="")
@click.option("--status", type=click.Choice(DOC_STATUSES), default="draft")
@click.option("--folder-id", default=None)
@click.option("--created-by", default="cli")
@click.option("--pin", is_flag=True)
@click.pass_context
def doc_create(ctx, workspace_id, title, content, excerpt, status, folder_id, created_by, pin):
    r = S.create_document(workspace_id, title, content, excerpt, status, folder_id, created_by, pin)
    log("doc_create", title=title, workspace=workspace_id, status=status)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['title']} [{r['status']}]")

@doc.command("update")
@click.argument("doc_id")
@click.option("--title", default=None)
@click.option("--content", default=None)
@click.option("--excerpt", default=None)
@click.option("--status", type=click.Choice(DOC_STATUSES), default=None)
@click.option("--last-edited-by", default=None)
@click.pass_context
def doc_update(ctx, doc_id, title, content, excerpt, status, last_edited_by):
    kwargs = {k: v for k, v in [("title", title), ("content", content), ("excerpt", excerpt), ("status", status), ("lastEditedBy", last_edited_by)] if v is not None}
    if not kwargs: click.echo("Nothing to update."); return
    r = S.update_document(doc_id, **kwargs)
    log("doc_update", id=doc_id, fields=list(kwargs.keys()))
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Updated: {r['title']}")

@doc.command("delete")
@click.argument("doc_id")
@click.pass_context
def doc_delete(ctx, doc_id):
    ok = S.delete_document(doc_id)
    log("doc_delete", id=doc_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted {doc_id} (cascade complete).")

@doc.command("search")
@click.argument("query")
@click.pass_context
def doc_search(ctx, query):
    rows = S.search_documents(query)
    log("doc_search", query=query, results=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{d['id']}] {d['title']}" for d in rows) or "No results.")

@doc.command("pin")
@click.argument("doc_id")
@click.pass_context
def doc_pin(ctx, doc_id):
    d = S.get_document(doc_id)
    if not d: err("not_found", ctx)
    r = S.update_document(doc_id, isPinned=not d["isPinned"])
    log("doc_pin", id=doc_id, pinned=r["isPinned"])
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"{'Pinned' if r['isPinned'] else 'Unpinned'}: {r['title']}")

@doc.command("publish")
@click.argument("doc_id")
@click.pass_context
def doc_publish(ctx, doc_id):
    r = S.update_document(doc_id, status="published")
    log("doc_publish", id=doc_id)
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Published: {r['title']}")


# version

@cli.group()
def version():
    """Document version management."""
    pass

@version.command("list")
@click.argument("doc_id")
@click.pass_context
def ver_list(ctx, doc_id):
    rows = S.get_versions(doc_id)
    log("version_list", doc=doc_id, count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{v['id']}] v{v['versionNumber']} {v['title']} - {v['changeNote']}" for v in rows) or "No versions.")

@version.command("create")
@click.argument("doc_id")
@click.option("--change-note", default="")
@click.option("--created-by", default="cli")
@click.pass_context
def ver_create(ctx, doc_id, change_note, created_by):
    d = S.get_document(doc_id)
    if not d: err("not_found", ctx)
    r = S.create_version(doc_id, d["title"], d["content"], change_note, created_by)
    log("version_create", doc=doc_id, version=r["versionNumber"])
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Saved v{r['versionNumber']}: {r['title']}")

@version.command("restore")
@click.argument("version_id")
@click.pass_context
def ver_restore(ctx, version_id):
    r = S.restore_version(version_id)
    log("version_restore", version_id=version_id, ok=r is not None)
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Restored: {r['title']}")


# tag

@cli.group()
def tag():
    """Tag management."""
    pass

@tag.command("list")
@click.pass_context
def tag_list(ctx):
    rows = S.get_tags()
    log("tag_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{t['id']}] {t['name']} ({t['color']})" for t in rows) or "No tags.")

@tag.command("create")
@click.option("--name", required=True)
@click.option("--color", default="#6366f1")
@click.pass_context
def tag_create(ctx, name, color):
    r = S.create_tag(name, color)
    log("tag_create", name=name)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['name']}")

@tag.command("delete")
@click.argument("tag_id")
@click.pass_context
def tag_delete(ctx, tag_id):
    ok = S.delete_tag(tag_id)
    log("tag_delete", id=tag_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted tag {tag_id}.")

@tag.command("add")
@click.argument("doc_id")
@click.argument("tag_id")
@click.pass_context
def tag_add(ctx, doc_id, tag_id):
    r = S.add_tag_to_document(doc_id, tag_id)
    log("tag_add", doc=doc_id, tag=tag_id)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Tagged document {doc_id} with {tag_id}.")

@tag.command("remove")
@click.argument("doc_id")
@click.argument("tag_id")
@click.pass_context
def tag_remove(ctx, doc_id, tag_id):
    S.remove_tag_from_document(doc_id, tag_id)
    log("tag_remove", doc=doc_id, tag=tag_id)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "removed"}))
    else: click.echo(f"Removed tag {tag_id} from {doc_id}.")


# comment

@cli.group()
def comment():
    """Comment management."""
    pass

@comment.command("list")
@click.argument("doc_id")
@click.pass_context
def cm_list(ctx, doc_id):
    rows = S.get_comments(doc_id)
    log("comment_list", doc=doc_id, count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{c['id']}] {'[RESOLVED]' if c['isResolved'] else ''} {c['content'][:60]}" for c in rows) or "No comments.")

@comment.command("create")
@click.argument("doc_id")
@click.option("--author-id", required=True)
@click.option("--content", required=True)
@click.option("--parent-id", default=None)
@click.pass_context
def cm_create(ctx, doc_id, author_id, content, parent_id):
    r = S.create_comment(doc_id, author_id, content, parent_id)
    log("comment_create", doc=doc_id, author=author_id)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Comment [{r['id']}] added.")

@comment.command("resolve")
@click.argument("comment_id")
@click.pass_context
def cm_resolve(ctx, comment_id):
    r = S.update_comment(comment_id, isResolved=True)
    log("comment_resolve", id=comment_id)
    if not r: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Resolved comment {comment_id}.")

@comment.command("delete")
@click.argument("comment_id")
@click.pass_context
def cm_delete(ctx, comment_id):
    ok = S.delete_comment(comment_id)
    log("comment_delete", id=comment_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted comment {comment_id}.")


# share

@cli.group()
def share():
    """Document sharing."""
    pass

@share.command("list")
@click.argument("doc_id")
@click.pass_context
def sh_list(ctx, doc_id):
    rows = S.get_shares(doc_id)
    log("share_list", doc=doc_id, count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{s['id']}] member={s['memberId']} perm={s['permission']}" for s in rows) or "No shares.")

@share.command("add")
@click.argument("doc_id")
@click.option("--member-id", required=True)
@click.option("--permission", type=click.Choice(SHARE_PERMS), default="view")
@click.pass_context
def sh_add(ctx, doc_id, member_id, permission):
    r = S.create_share(doc_id, member_id, permission)
    log("share_add", doc=doc_id, member=member_id, perm=permission)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Shared [{r['id']}] with {member_id} ({permission}).")

@share.command("remove")
@click.argument("share_id")
@click.pass_context
def sh_remove(ctx, share_id):
    ok = S.delete_share(share_id)
    log("share_remove", id=share_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Removed share {share_id}.")


# template

@cli.group()
def template():
    """Template management."""
    pass

@template.command("list")
@click.pass_context
def tpl_list(ctx):
    rows = S.get_templates()
    log("template_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{t['id']}] [{t['category']}] {t['title']}" for t in rows) or "No templates.")

@template.command("create")
@click.option("--title", required=True)
@click.option("--content", required=True)
@click.option("--description", default="")
@click.option("--category", type=click.Choice(TEMPLATE_CATS), default="other")
@click.option("--created-by", default="cli")
@click.pass_context
def tpl_create(ctx, title, content, description, category, created_by):
    r = S.create_template(title, content, description, category, created_by)
    log("template_create", title=title, category=category)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['title']}")

@template.command("delete")
@click.argument("template_id")
@click.pass_context
def tpl_delete(ctx, template_id):
    ok = S.delete_template(template_id)
    log("template_delete", id=template_id, ok=ok)
    if not ok: err("not_found", ctx)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "deleted"}))
    else: click.echo(f"Deleted template {template_id}.")


# favorite

@cli.group()
def favorite():
    """Favorite documents."""
    pass

@favorite.command("list")
@click.argument("member_id")
@click.pass_context
def fav_list(ctx, member_id):
    rows = S.get_favorites(member_id)
    log("favorite_list", member=member_id, count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(f"[{f['id']}] doc={f['documentId']}" for f in rows) or "No favorites.")

@favorite.command("add")
@click.argument("member_id")
@click.argument("doc_id")
@click.pass_context
def fav_add(ctx, member_id, doc_id):
    r = S.add_favorite(member_id, doc_id)
    log("favorite_add", member=member_id, doc=doc_id)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Added to favorites.")

@favorite.command("remove")
@click.argument("member_id")
@click.argument("doc_id")
@click.pass_context
def fav_remove(ctx, member_id, doc_id):
    ok = S.remove_favorite(member_id, doc_id)
    log("favorite_remove", member=member_id, doc=doc_id, ok=ok)
    if ctx.obj["json"]: click.echo(json.dumps({"status": "removed" if ok else "not_found"}))
    else: click.echo("Removed." if ok else "Not found.")


# dashboard

@cli.command()
@click.pass_context
def dashboard(ctx):
    """Show dashboard summary."""
    r = S.get_dashboard()
    log("dashboard")
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else:
        click.echo(f"Recent docs: {len(r['recentDocuments'])} | Favorites: {len(r['favoriteDocuments'])}")
        click.echo(f"Workspaces:")
        for ws in r["workspaceStats"]:
            click.echo(f"  {ws['workspace']['icon']} {ws['workspace']['name']}: {ws['documentCount']} docs")
        click.echo(f"Recent activity: {len(r['recentActivity'])} events")


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
