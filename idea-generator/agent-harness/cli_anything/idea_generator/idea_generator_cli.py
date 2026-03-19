import json
import sys
import click
from cli_anything.idea_generator.core.ideas import get_random_idea, CATEGORIES
from cli_anything.idea_generator.core.storage import (
    load_favorites,
    save_favorite,
    remove_favorite,
    clear_favorites,
)
from cli_anything.idea_generator.core.logger import log


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, json_output):
    """Idea Generator CLI - Random creative prompts from the command line.

    Categories: writing, drawing, business, coding.
    Use --json for structured output (agent-friendly).
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# ── generate ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--category", "-c",
    type=click.Choice(CATEGORIES, case_sensitive=False),
    default="writing",
    show_default=True,
    help="Idea category",
)
@click.pass_context
def generate(ctx, category):
    """Generate a random idea from the given category."""
    idea = get_random_idea(category)
    log("generate", category=category, idea=idea[:60])

    data = {"category": category, "idea": idea}
    if ctx.obj["json"]:
        click.echo(json.dumps(data, ensure_ascii=False))
    else:
        click.echo(f"[{category.upper()}] {idea}")


# ── favorites group ────────────────────────────────────────────────────────────

@cli.group()
def favorites():
    """Manage saved favorite ideas."""
    pass


@favorites.command("list")
@click.option("--limit", default=20, show_default=True, help="Max entries to show")
@click.pass_context
def favorites_list(ctx, limit):
    """List saved favorite ideas."""
    entries = load_favorites()[:limit]
    log("favorites_list", count=len(entries), limit=limit)

    if ctx.obj["json"]:
        click.echo(json.dumps(entries, ensure_ascii=False))
    else:
        if not entries:
            click.echo("No favorites yet.")
            return
        for e in entries:
            ts = e["timestamp"][:19]
            click.echo(f"[{e['id']}] [{ts}] [{e['category'].upper()}] {e['text']}")


@favorites.command("save")
@click.argument("text")
@click.option(
    "--category", "-c",
    type=click.Choice(CATEGORIES, case_sensitive=False),
    default="writing",
    show_default=True,
)
@click.pass_context
def favorites_save(ctx, text, category):
    """Save an idea to favorites. TEXT is the idea string."""
    entry = save_favorite(category, text)
    log("favorites_save", category=category, text=text[:60], saved=entry is not None)

    if entry is None:
        msg = {"status": "duplicate", "message": "Already in favorites"}
        if ctx.obj["json"]:
            click.echo(json.dumps(msg))
        else:
            click.echo("Already saved.")
        sys.exit(1)

    if ctx.obj["json"]:
        click.echo(json.dumps(entry, ensure_ascii=False))
    else:
        click.echo(f"Saved [{entry['id']}]: {entry['text']}")


@favorites.command("remove")
@click.argument("id", type=int)
@click.pass_context
def favorites_remove(ctx, id):
    """Remove a favorite by ID."""
    ok = remove_favorite(id)
    log("favorites_remove", id=id, success=ok)

    if not ok:
        msg = {"status": "not_found", "id": id}
        if ctx.obj["json"]:
            click.echo(json.dumps(msg))
        else:
            click.echo(f"ID {id} not found.")
        sys.exit(1)

    data = {"status": "removed", "id": id}
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        click.echo(f"Removed favorite {id}.")


@favorites.command("clear")
@click.pass_context
def favorites_clear(ctx):
    """Clear all favorites."""
    count = clear_favorites()
    log("favorites_clear", removed=count)

    data = {"status": "ok", "removed": count}
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        click.echo(f"Cleared {count} favorites.")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
