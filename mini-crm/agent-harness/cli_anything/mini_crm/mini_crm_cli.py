import json
import sys
import click
from cli_anything.mini_crm.core.db import fetchall, fetchone, execute, execute_returning
from cli_anything.mini_crm.core.logger import log

DEAL_STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
ACTIVITY_TYPES = ['call', 'email', 'meeting', 'note']
PRIORITIES = ['low', 'medium', 'high']


def _serial(obj):
    """JSON serialize datetime/UUID/Decimal objects."""
    import datetime, uuid, decimal
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, decimal.Decimal):
        return int(obj)
    raise TypeError(f"Not serializable: {type(obj)}")


def jdump(data):
    return json.dumps(data, default=_serial, ensure_ascii=False)


@click.group()
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
def cli(ctx, json_output):
    """Mini CRM CLI - Manage contacts, companies, deals, activities and tasks."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# ── companies ─────────────────────────────────────────────────────────────────

@cli.group()
def company():
    """Company management."""
    pass


@company.command("list")
@click.option("--limit", default=20)
@click.pass_context
def company_list(ctx, limit):
    """List companies."""
    rows = fetchall(
        "SELECT id, name, industry, website, employee_count, created_at FROM companies ORDER BY name LIMIT %s",
        (limit,)
    )
    log("company_list", count=len(rows))
    click.echo(jdump(rows) if ctx.obj["json"] else
               "\n".join(f"[{r['id']}] {r['name']} / {r['industry'] or '-'}" for r in rows) or "No companies.")


@company.command("get")
@click.argument("company_id")
@click.pass_context
def company_get(ctx, company_id):
    """Get a company by ID."""
    row = fetchone("SELECT * FROM companies WHERE id = %s", (company_id,))
    log("company_get", id=company_id, found=row is not None)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else
               f"Name: {row['name']}\nIndustry: {row['industry']}\nWebsite: {row['website']}\nMemo: {row['memo']}")


@company.command("create")
@click.option("--name", required=True)
@click.option("--industry", default=None)
@click.option("--website", default=None)
@click.option("--memo", default=None)
@click.pass_context
def company_create(ctx, name, industry, website, memo):
    """Create a company."""
    row = execute_returning(
        "INSERT INTO companies (name, industry, website, memo) VALUES (%s,%s,%s,%s) RETURNING *",
        (name, industry, website, memo)
    )
    log("company_create", name=name)
    click.echo(jdump(row) if ctx.obj["json"] else f"Created [{row['id']}]: {row['name']}")


@company.command("update")
@click.argument("company_id")
@click.option("--name", default=None)
@click.option("--industry", default=None)
@click.option("--website", default=None)
@click.option("--memo", default=None)
@click.pass_context
def company_update(ctx, company_id, name, industry, website, memo):
    """Update a company."""
    fields, vals = [], []
    for col, val in [("name", name), ("industry", industry), ("website", website), ("memo", memo)]:
        if val is not None:
            fields.append(f"{col} = %s")
            vals.append(val)
    if not fields:
        click.echo("Nothing to update.")
        return
    vals.append(company_id)
    row = execute_returning(
        f"UPDATE companies SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s RETURNING *",
        vals
    )
    log("company_update", id=company_id, fields=fields)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else f"Updated: {row['name']}")


@company.command("delete")
@click.argument("company_id")
@click.pass_context
def company_delete(ctx, company_id):
    """Delete a company."""
    n = execute("DELETE FROM companies WHERE id = %s", (company_id,))
    log("company_delete", id=company_id, deleted=n)
    if not n:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump({"status": "deleted", "id": company_id}) if ctx.obj["json"] else f"Deleted {company_id}.")


# ── contacts ──────────────────────────────────────────────────────────────────

@cli.group()
def contact():
    """Contact management."""
    pass


@contact.command("list")
@click.option("--company-id", default=None)
@click.option("--limit", default=20)
@click.pass_context
def contact_list(ctx, company_id, limit):
    """List contacts."""
    if company_id:
        rows = fetchall(
            "SELECT c.*, co.name as company_name FROM contacts c LEFT JOIN companies co ON c.company_id=co.id WHERE c.company_id=%s ORDER BY c.name LIMIT %s",
            (company_id, limit)
        )
    else:
        rows = fetchall(
            "SELECT c.*, co.name as company_name FROM contacts c LEFT JOIN companies co ON c.company_id=co.id ORDER BY c.name LIMIT %s",
            (limit,)
        )
    log("contact_list", count=len(rows))
    click.echo(jdump(rows) if ctx.obj["json"] else
               "\n".join(f"[{r['id']}] {r['name']} / {r['email'] or '-'} / {r['company_name'] or '-'}" for r in rows) or "No contacts.")


@contact.command("get")
@click.argument("contact_id")
@click.pass_context
def contact_get(ctx, contact_id):
    """Get a contact by ID."""
    row = fetchone(
        "SELECT c.*, co.name as company_name FROM contacts c LEFT JOIN companies co ON c.company_id=co.id WHERE c.id=%s",
        (contact_id,)
    )
    log("contact_get", id=contact_id, found=row is not None)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else
               f"Name: {row['name']}\nEmail: {row['email']}\nPhone: {row['phone']}\nCompany: {row['company_name']}\nPosition: {row['position']}")


@contact.command("create")
@click.option("--name", required=True)
@click.option("--email", default=None)
@click.option("--phone", default=None)
@click.option("--position", default=None)
@click.option("--company-id", default=None)
@click.option("--memo", default=None)
@click.pass_context
def contact_create(ctx, name, email, phone, position, company_id, memo):
    """Create a contact."""
    row = execute_returning(
        "INSERT INTO contacts (name, email, phone, position, company_id, memo) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
        (name, email, phone, position, company_id, memo)
    )
    log("contact_create", name=name, email=email)
    click.echo(jdump(row) if ctx.obj["json"] else f"Created [{row['id']}]: {row['name']}")


@contact.command("update")
@click.argument("contact_id")
@click.option("--name", default=None)
@click.option("--email", default=None)
@click.option("--phone", default=None)
@click.option("--position", default=None)
@click.option("--company-id", default=None)
@click.option("--memo", default=None)
@click.pass_context
def contact_update(ctx, contact_id, name, email, phone, position, company_id, memo):
    """Update a contact."""
    fields, vals = [], []
    for col, val in [("name", name), ("email", email), ("phone", phone), ("position", position), ("company_id", company_id), ("memo", memo)]:
        if val is not None:
            fields.append(f"{col} = %s")
            vals.append(val)
    if not fields:
        click.echo("Nothing to update.")
        return
    vals.append(contact_id)
    row = execute_returning(
        f"UPDATE contacts SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s RETURNING *",
        vals
    )
    log("contact_update", id=contact_id)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else f"Updated: {row['name']}")


@contact.command("delete")
@click.argument("contact_id")
@click.pass_context
def contact_delete(ctx, contact_id):
    """Delete a contact."""
    n = execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
    log("contact_delete", id=contact_id, deleted=n)
    if not n:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump({"status": "deleted"}) if ctx.obj["json"] else f"Deleted {contact_id}.")


# ── deals ─────────────────────────────────────────────────────────────────────

@cli.group()
def deal():
    """Deal / pipeline management."""
    pass


@deal.command("list")
@click.option("--stage", type=click.Choice(DEAL_STAGES), default=None)
@click.option("--limit", default=20)
@click.pass_context
def deal_list(ctx, stage, limit):
    """List deals."""
    if stage:
        rows = fetchall(
            "SELECT d.*, c.name as contact_name, co.name as company_name FROM deals d LEFT JOIN contacts c ON d.contact_id=c.id LEFT JOIN companies co ON d.company_id=co.id WHERE d.stage=%s ORDER BY d.created_at DESC LIMIT %s",
            (stage, limit)
        )
    else:
        rows = fetchall(
            "SELECT d.*, c.name as contact_name, co.name as company_name FROM deals d LEFT JOIN contacts c ON d.contact_id=c.id LEFT JOIN companies co ON d.company_id=co.id ORDER BY d.created_at DESC LIMIT %s",
            (limit,)
        )
    log("deal_list", count=len(rows), stage=stage)
    click.echo(jdump(rows) if ctx.obj["json"] else
               "\n".join(f"[{r['id']}] {r['title']} / {r['stage']} / {r['amount']:,}원 / {r['company_name'] or '-'}" for r in rows) or "No deals.")


@deal.command("create")
@click.option("--title", required=True)
@click.option("--amount", type=int, default=0)
@click.option("--stage", type=click.Choice(DEAL_STAGES), default="lead")
@click.option("--contact-id", default=None)
@click.option("--company-id", default=None)
@click.option("--memo", default=None)
@click.pass_context
def deal_create(ctx, title, amount, stage, contact_id, company_id, memo):
    """Create a deal."""
    row = execute_returning(
        "INSERT INTO deals (title, amount, stage, contact_id, company_id, memo) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
        (title, amount, stage, contact_id, company_id, memo)
    )
    log("deal_create", title=title, stage=stage, amount=amount)
    click.echo(jdump(row) if ctx.obj["json"] else f"Created [{row['id']}]: {row['title']} / {row['stage']}")


@deal.command("stage")
@click.argument("deal_id")
@click.argument("new_stage", type=click.Choice(DEAL_STAGES))
@click.pass_context
def deal_stage(ctx, deal_id, new_stage):
    """Move a deal to a new stage."""
    row = execute_returning(
        "UPDATE deals SET stage=%s, updated_at=NOW() WHERE id=%s RETURNING *",
        (new_stage, deal_id)
    )
    log("deal_stage", id=deal_id, new_stage=new_stage)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else f"Moved '{row['title']}' -> {new_stage}")


@deal.command("delete")
@click.argument("deal_id")
@click.pass_context
def deal_delete(ctx, deal_id):
    """Delete a deal."""
    n = execute("DELETE FROM deals WHERE id = %s", (deal_id,))
    log("deal_delete", id=deal_id, deleted=n)
    if not n:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump({"status": "deleted"}) if ctx.obj["json"] else f"Deleted {deal_id}.")


# ── activities ────────────────────────────────────────────────────────────────

@cli.group()
def activity():
    """Activity log management."""
    pass


@activity.command("list")
@click.option("--contact-id", default=None)
@click.option("--type", "act_type", type=click.Choice(ACTIVITY_TYPES), default=None)
@click.option("--limit", default=20)
@click.pass_context
def activity_list(ctx, contact_id, act_type, limit):
    """List activities."""
    wheres, params = [], []
    if contact_id:
        wheres.append("a.contact_id = %s")
        params.append(contact_id)
    if act_type:
        wheres.append("a.type = %s")
        params.append(act_type)
    where_sql = f"WHERE {' AND '.join(wheres)}" if wheres else ""
    params.append(limit)
    rows = fetchall(
        f"SELECT a.*, c.name as contact_name FROM activities a LEFT JOIN contacts c ON a.contact_id=c.id {where_sql} ORDER BY a.created_at DESC LIMIT %s",
        params
    )
    log("activity_list", count=len(rows))
    click.echo(jdump(rows) if ctx.obj["json"] else
               "\n".join(f"[{r['id']}] [{r['type']}] {r['title']} / {r['contact_name'] or '-'}" for r in rows) or "No activities.")


@activity.command("create")
@click.option("--title", required=True)
@click.option("--type", "act_type", type=click.Choice(ACTIVITY_TYPES), required=True)
@click.option("--description", default=None)
@click.option("--contact-id", default=None)
@click.option("--deal-id", default=None)
@click.pass_context
def activity_create(ctx, title, act_type, description, contact_id, deal_id):
    """Log an activity."""
    row = execute_returning(
        "INSERT INTO activities (title, type, description, contact_id, deal_id) VALUES (%s,%s,%s,%s,%s) RETURNING *",
        (title, act_type, description, contact_id, deal_id)
    )
    log("activity_create", title=title, type=act_type)
    click.echo(jdump(row) if ctx.obj["json"] else f"Logged [{row['id']}]: [{row['type']}] {row['title']}")


# ── tasks ─────────────────────────────────────────────────────────────────────

@cli.group()
def task():
    """Task management."""
    pass


@task.command("list")
@click.option("--done", is_flag=True, help="Show completed tasks only")
@click.option("--priority", type=click.Choice(PRIORITIES), default=None)
@click.option("--limit", default=20)
@click.pass_context
def task_list(ctx, done, priority, limit):
    """List tasks."""
    wheres, params = [f"is_completed = %s"], [done]
    if priority:
        wheres.append("priority = %s")
        params.append(priority)
    params.append(limit)
    rows = fetchall(
        f"SELECT * FROM tasks WHERE {' AND '.join(wheres)} ORDER BY due_date ASC NULLS LAST LIMIT %s",
        params
    )
    log("task_list", count=len(rows), done=done)
    click.echo(jdump(rows) if ctx.obj["json"] else
               "\n".join(f"[{r['id']}] {'[DONE]' if r['is_completed'] else '[TODO]'} {r['title']} / {r['priority']}" for r in rows) or "No tasks.")


@task.command("create")
@click.option("--title", required=True)
@click.option("--priority", type=click.Choice(PRIORITIES), default="medium")
@click.option("--due-date", default=None, help="YYYY-MM-DD")
@click.option("--contact-id", default=None)
@click.option("--deal-id", default=None)
@click.pass_context
def task_create(ctx, title, priority, due_date, contact_id, deal_id):
    """Create a task."""
    row = execute_returning(
        "INSERT INTO tasks (title, priority, due_date, contact_id, deal_id) VALUES (%s,%s,%s,%s,%s) RETURNING *",
        (title, priority, due_date, contact_id, deal_id)
    )
    log("task_create", title=title, priority=priority)
    click.echo(jdump(row) if ctx.obj["json"] else f"Created [{row['id']}]: {row['title']} / {row['priority']}")


@task.command("complete")
@click.argument("task_id")
@click.pass_context
def task_complete(ctx, task_id):
    """Mark a task as complete."""
    row = execute_returning(
        "UPDATE tasks SET is_completed=TRUE, updated_at=NOW() WHERE id=%s RETURNING *",
        (task_id,)
    )
    log("task_complete", id=task_id)
    if not row:
        click.echo(jdump({"error": "not_found"}) if ctx.obj["json"] else "Not found.")
        sys.exit(1)
    click.echo(jdump(row) if ctx.obj["json"] else f"Completed: {row['title']}")


# ── search ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx, query):
    """Search across contacts, companies, and deals."""
    q = f"%{query}%"
    contacts = fetchall(
        "SELECT id, name, email, 'contact' as type FROM contacts WHERE name ILIKE %s OR email ILIKE %s LIMIT 5",
        (q, q)
    )
    companies = fetchall(
        "SELECT id, name, industry, 'company' as type FROM companies WHERE name ILIKE %s OR industry ILIKE %s LIMIT 5",
        (q, q)
    )
    deals = fetchall(
        "SELECT id, title, stage, 'deal' as type FROM deals WHERE title ILIKE %s LIMIT 5",
        (q,)
    )
    result = {"contacts": contacts, "companies": companies, "deals": deals}
    log("search", query=query, total=len(contacts)+len(companies)+len(deals))
    if ctx.obj["json"]:
        click.echo(jdump(result))
    else:
        for section, rows in result.items():
            if rows:
                click.echo(f"\n[{section.upper()}]")
                for r in rows:
                    click.echo(f"  [{r['id']}] {r.get('name') or r.get('title')}")


# ── stats ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def stats(ctx):
    """Show CRM statistics."""
    totals = fetchone("""
        SELECT
            (SELECT COUNT(*) FROM contacts) as contacts,
            (SELECT COUNT(*) FROM companies) as companies,
            (SELECT COUNT(*) FROM deals) as deals,
            (SELECT COUNT(*) FROM deals WHERE stage='closed_won') as won,
            (SELECT COALESCE(SUM(amount),0) FROM deals WHERE stage='closed_won') as won_amount,
            (SELECT COUNT(*) FROM tasks WHERE is_completed=FALSE) as open_tasks
    """)
    pipeline = fetchall(
        "SELECT stage, COUNT(*) as count, COALESCE(SUM(amount),0) as total FROM deals GROUP BY stage ORDER BY stage"
    )
    result = {"totals": totals, "pipeline": pipeline}
    log("stats")
    if ctx.obj["json"]:
        click.echo(jdump(result))
    else:
        t = totals
        click.echo(f"Contacts: {t['contacts']}  Companies: {t['companies']}  Deals: {t['deals']}")
        click.echo(f"Won: {t['won']} deals / {int(t['won_amount']):,}원  |  Open tasks: {t['open_tasks']}")
        click.echo("\nPipeline:")
        for r in pipeline:
            click.echo(f"  {r['stage']:15} {r['count']:3}건  {int(r['total']):>15,}원")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
