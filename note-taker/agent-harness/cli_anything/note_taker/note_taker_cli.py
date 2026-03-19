import json
import sys
import click
from cli_anything.note_taker.core.notes import (
    create_note, get_note, update_note, delete_note,
    pin_note, duplicate_note, search_notes,
    get_all_tags, get_tag_counts, rename_tag, parse_tags,
)
from cli_anything.note_taker.core.storage import (
    export_to_json, import_from_json, load_notes, save_notes,
)
from cli_anything.note_taker.core.logger import log


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, json_output):
    """Note Taker CLI - Create, search, and manage notes from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# ── note group ────────────────────────────────────────────────────────────────

@cli.group()
def note():
    """Note CRUD operations."""
    pass


@note.command("create")
@click.option("--title", "-t", required=True, help="Note title")
@click.option("--content", "-c", default="", help="Note content (supports markdown)")
@click.option("--tags", default="", help="Comma/space separated tags")
@click.pass_context
def note_create(ctx, title, content, tags):
    """Create a new note."""
    tag_list = parse_tags(tags)
    result = create_note(title, content, tag_list)
    log("note_create", id=result["id"], title=title[:40], tags=tag_list)
    if ctx.obj["json"]:
        click.echo(json.dumps(result, ensure_ascii=False))
    else:
        click.echo(f"Created [{result['id']}]: {result['title']}")


@note.command("list")
@click.option("--sort", "sort_by", type=click.Choice(["updated", "created", "title"]), default="updated")
@click.option("--limit", default=20, show_default=True)
@click.option("--pinned", is_flag=True, help="Show only pinned notes")
@click.pass_context
def note_list(ctx, sort_by, limit, pinned):
    """List all notes."""
    notes = search_notes(sort_by=sort_by)
    if pinned:
        notes = [n for n in notes if n.get("isPinned")]
    notes = notes[:limit]
    log("note_list", count=len(notes), sort=sort_by)
    if ctx.obj["json"]:
        click.echo(json.dumps(notes, ensure_ascii=False))
    else:
        if not notes:
            click.echo("No notes.")
            return
        for n in notes:
            pin = "[PIN] " if n.get("isPinned") else ""
            tags = f" #{' #'.join(n['tags'])}" if n["tags"] else ""
            click.echo(f"{pin}[{n['id']}] {n['title']}{tags}  ({n['updated'][:10]})")


@note.command("get")
@click.argument("note_id")
@click.pass_context
def note_get(ctx, note_id):
    """Get a single note by ID."""
    n = get_note(note_id)
    log("note_get", id=note_id, found=n is not None)
    if not n:
        msg = {"error": "not_found", "id": note_id}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Note {note_id} not found.")
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(n, ensure_ascii=False))
    else:
        click.echo(f"ID:      {n['id']}")
        click.echo(f"Title:   {n['title']}")
        click.echo(f"Tags:    {', '.join(n['tags']) or '(none)'}")
        click.echo(f"Pinned:  {n['isPinned']}")
        click.echo(f"Created: {n['created'][:19]}")
        click.echo(f"Updated: {n['updated'][:19]}")
        click.echo(f"\n{n['content']}")


@note.command("update")
@click.argument("note_id")
@click.option("--title", "-t", default=None)
@click.option("--content", "-c", default=None)
@click.option("--tags", default=None, help="Replace all tags")
@click.pass_context
def note_update(ctx, note_id, title, content, tags):
    """Update an existing note."""
    changes = {}
    if title is not None:
        changes["title"] = title
    if content is not None:
        changes["content"] = content
    if tags is not None:
        changes["tags"] = parse_tags(tags)
    if not changes:
        click.echo("Nothing to update.")
        return
    result = update_note(note_id, changes)
    log("note_update", id=note_id, fields=list(changes.keys()), found=result is not None)
    if not result:
        msg = {"error": "not_found", "id": note_id}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Note {note_id} not found.")
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(result, ensure_ascii=False))
    else:
        click.echo(f"Updated [{result['id']}]: {result['title']}")


@note.command("delete")
@click.argument("note_id")
@click.pass_context
def note_delete(ctx, note_id):
    """Delete a note by ID."""
    ok = delete_note(note_id)
    log("note_delete", id=note_id, success=ok)
    if not ok:
        msg = {"error": "not_found", "id": note_id}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Note {note_id} not found.")
        sys.exit(1)
    data = {"status": "deleted", "id": note_id}
    click.echo(json.dumps(data) if ctx.obj["json"] else f"Deleted {note_id}.")


@note.command("pin")
@click.argument("note_id")
@click.pass_context
def note_pin(ctx, note_id):
    """Toggle pin on a note."""
    result = pin_note(note_id)
    log("note_pin", id=note_id, pinned=result.get("isPinned") if result else None)
    if not result:
        msg = {"error": "not_found", "id": note_id}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Note {note_id} not found.")
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(result, ensure_ascii=False))
    else:
        state = "pinned" if result["isPinned"] else "unpinned"
        click.echo(f"{state.upper()}: {result['title']}")


@note.command("duplicate")
@click.argument("note_id")
@click.pass_context
def note_duplicate(ctx, note_id):
    """Duplicate a note."""
    result = duplicate_note(note_id)
    log("note_duplicate", original_id=note_id, new_id=result["id"] if result else None)
    if not result:
        msg = {"error": "not_found", "id": note_id}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Note {note_id} not found.")
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(result, ensure_ascii=False))
    else:
        click.echo(f"Duplicated as [{result['id']}]: {result['title']}")


# ── search ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query", default="")
@click.option("--tags", default="", help="Filter by tags (AND logic)")
@click.option("--sort", "sort_by", type=click.Choice(["updated", "created", "title"]), default="updated")
@click.pass_context
def search(ctx, query, tags, sort_by):
    """Search notes by text and/or tags."""
    tag_list = parse_tags(tags) if tags else []
    results = search_notes(query=query, tags=tag_list, sort_by=sort_by)
    log("search", query=query[:40], tags=tag_list, results=len(results))
    if ctx.obj["json"]:
        click.echo(json.dumps(results, ensure_ascii=False))
    else:
        if not results:
            click.echo("No results.")
            return
        click.echo(f"Found {len(results)} note(s):")
        for n in results:
            pin = "[PIN] " if n.get("isPinned") else ""
            tags_str = f" #{' #'.join(n['tags'])}" if n["tags"] else ""
            click.echo(f"  {pin}[{n['id']}] {n['title']}{tags_str}")


# ── tags group ────────────────────────────────────────────────────────────────

@cli.group()
def tags():
    """Tag management."""
    pass


@tags.command("list")
@click.pass_context
def tags_list(ctx):
    """List all unique tags."""
    all_tags = get_all_tags()
    log("tags_list", count=len(all_tags))
    if ctx.obj["json"]:
        click.echo(json.dumps(all_tags, ensure_ascii=False))
    else:
        if not all_tags:
            click.echo("No tags.")
        else:
            click.echo("\n".join(f"  #{t}" for t in all_tags))


@tags.command("counts")
@click.pass_context
def tags_counts(ctx):
    """Show tag usage counts."""
    counts = get_tag_counts()
    log("tags_counts", unique=len(counts))
    if ctx.obj["json"]:
        click.echo(json.dumps(counts, ensure_ascii=False))
    else:
        if not counts:
            click.echo("No tags.")
        else:
            for tag, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                click.echo(f"  #{tag}: {cnt}")


@tags.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@click.pass_context
def tags_rename(ctx, old_name, new_name):
    """Rename a tag across all notes."""
    count = rename_tag(old_name, new_name)
    log("tags_rename", old=old_name, new=new_name, updated_notes=count)
    data = {"status": "ok", "old": old_name, "new": new_name, "updated_notes": count}
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        click.echo(f"Renamed #{old_name} -> #{new_name} in {count} note(s).")


# ── export / import ────────────────────────────────────────────────────────────

@cli.command("export")
@click.option("--output", "-o", default=None, help="Output file path (default: stdout)")
@click.pass_context
def export_cmd(ctx, output):
    """Export all notes to JSON."""
    notes = load_notes()
    data = export_to_json(notes)
    log("export", count=len(notes), output=output or "stdout")
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(data)
        click.echo(f"Exported {len(notes)} notes to {output}.")
    else:
        click.echo(data)


@cli.command("import")
@click.argument("filepath")
@click.option("--merge", is_flag=True, help="Merge with existing notes (default: replace)")
@click.pass_context
def import_cmd(ctx, filepath, merge):
    """Import notes from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        click.echo(f"File not found: {filepath}", err=True)
        sys.exit(1)

    result = import_from_json(content)
    if not result["success"]:
        msg = {"error": result["error"]}
        click.echo(json.dumps(msg) if ctx.obj["json"] else f"Import failed: {result['error']}")
        sys.exit(1)

    imported = result["notes"]
    if merge:
        existing = load_notes()
        existing_ids = {n["id"] for n in existing}
        new_notes = [n for n in imported if n["id"] not in existing_ids]
        save_notes(new_notes + existing)
        count = len(new_notes)
    else:
        save_notes(imported)
        count = len(imported)

    log("import", file=filepath, count=count, merge=merge)
    data = {"status": "ok", "imported": count, "merge": merge}
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        mode = "merged" if merge else "replaced"
        click.echo(f"Imported {count} notes ({mode}).")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
