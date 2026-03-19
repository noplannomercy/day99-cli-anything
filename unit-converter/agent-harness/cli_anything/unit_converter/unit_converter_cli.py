import json
import sys
import click
from cli_anything.unit_converter.core.converter import CONVERTERS
from cli_anything.unit_converter.core.history import load_history, save_entry, clear_history


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx, json_output):
    """Unit Converter CLI — Length, weight, temperature conversion from the command line.

    Designed for AI agents and power users. Use --json for structured output.
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# ── convert group ──────────────────────────────────────────────────────────────

@cli.group()
def convert():
    """Conversion commands: length, weight, temperature."""
    pass


def _do_convert(ctx, category, value, from_unit, to_unit):
    fn, units = CONVERTERS[category]
    result = fn(value, from_unit, to_unit)

    if result is None:
        msg = {"error": f"Invalid units for {category}. Valid: {units}"}
        if ctx.obj["json"]:
            click.echo(json.dumps(msg))
        else:
            click.echo(f"Error: {msg['error']}", err=True)
        sys.exit(1)

    save_entry(category, value, from_unit, to_unit, result)

    data = {
        "category": category,
        "value": value,
        "from": from_unit,
        "to": to_unit,
        "result": result,
    }
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        click.echo(f"{value} {from_unit} = {result} {to_unit}")


@convert.command()
@click.argument("value", type=float)
@click.argument("from_unit")
@click.argument("to_unit")
@click.pass_context
def length(ctx, value, from_unit, to_unit):
    """Convert length units. Units: m, km, ft, mi"""
    _do_convert(ctx, "length", value, from_unit, to_unit)


@convert.command()
@click.argument("value", type=float)
@click.argument("from_unit")
@click.argument("to_unit")
@click.pass_context
def weight(ctx, value, from_unit, to_unit):
    """Convert weight units. Units: kg, lb"""
    _do_convert(ctx, "weight", value, from_unit, to_unit)


@convert.command()
@click.argument("value", type=float)
@click.argument("from_unit")
@click.argument("to_unit")
@click.pass_context
def temperature(ctx, value, from_unit, to_unit):
    """Convert temperature units. Units: C, F, K"""
    _do_convert(ctx, "temperature", value, from_unit, to_unit)


# ── history group ──────────────────────────────────────────────────────────────

@cli.group()
def history():
    """History commands: list, clear."""
    pass


@history.command("list")
@click.option("--limit", default=10, help="Number of recent entries to show")
@click.pass_context
def history_list(ctx, limit):
    """Show recent conversion history."""
    entries = load_history()[-limit:]
    if ctx.obj["json"]:
        click.echo(json.dumps(entries))
    else:
        if not entries:
            click.echo("No history yet.")
        for e in entries:
            click.echo(f"[{e['timestamp'][:19]}] {e['category']}: {e['value']} {e['from']} → {e['result']} {e['to']}")


@history.command("clear")
@click.pass_context
def history_clear(ctx):
    """Clear all conversion history."""
    clear_history()
    data = {"action": "clear_history", "status": "ok"}
    if ctx.obj["json"]:
        click.echo(json.dumps(data))
    else:
        click.echo("History cleared.")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
