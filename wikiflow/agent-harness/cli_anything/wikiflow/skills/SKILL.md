---
name: cli-anything-wikiflow
version: 0.1.0
description: WikiFlow knowledge base CLI — workspace, folder, document, version, tag, comment, share, template, favorite, dashboard management. File-based storage at ~/.cli_anything_wikiflow_*.json.
command: cli-anything-wikiflow
install: pip install -e <path>/wikiflow/agent-harness
flags:
  - --json   # structured JSON output for LLM consumption
---

# WikiFlow CLI Skill

Manages a wiki/knowledge base system with full CRUD for all entities. File-based storage (no external DB needed).

## Command Groups

### workspace
- `workspace list` — list all workspaces
- `workspace create --name NAME [--description DESC] [--icon ICON]`
- `workspace update WORKSPACE_ID [--name NAME] [--description DESC] [--icon ICON]`
- `workspace delete WORKSPACE_ID` — cascade deletes folders and documents

### member
- `member list`
- `member create --name NAME --email EMAIL [--role admin|editor|viewer] [--avatar URL]`
- `member update MEMBER_ID [--name NAME] [--email EMAIL] [--role ROLE]`
- `member delete MEMBER_ID`

### folder
- `folder list WORKSPACE_ID`
- `folder tree WORKSPACE_ID` — recursive tree view
- `folder create --workspace-id ID --name NAME [--parent-id ID] [--icon ICON]`
- `folder delete FOLDER_ID` — cascade deletes documents inside

### doc
- `doc list [--workspace-id ID] [--folder-id ID] [--status draft|published|archived] [--tag-id ID] [--limit N]`
- `doc get DOC_ID [--increment-view]`
- `doc create --workspace-id ID --title TITLE [--content TEXT] [--excerpt TEXT] [--status STATUS] [--folder-id ID] [--created-by NAME] [--pin]`
- `doc update DOC_ID [--title TITLE] [--content TEXT] [--excerpt TEXT] [--status STATUS] [--last-edited-by NAME]`
- `doc delete DOC_ID` — cascade deletes versions, tags, comments, shares, favorites
- `doc search QUERY` — full-text search on title and content
- `doc pin DOC_ID` — toggle pin
- `doc publish DOC_ID` — set status to published

### version
- `version list DOC_ID`
- `version create DOC_ID [--change-note NOTE] [--created-by NAME]` — snapshots current doc content
- `version restore VERSION_ID` — restores doc content from version

### tag
- `tag list`
- `tag create --name NAME [--color HEX]`
- `tag delete TAG_ID`
- `tag add DOC_ID TAG_ID` — attach tag to document
- `tag remove DOC_ID TAG_ID`

### comment
- `comment list DOC_ID`
- `comment create DOC_ID --author-id MEMBER_ID --content TEXT [--parent-id COMMENT_ID]` — supports threaded replies
- `comment resolve COMMENT_ID`
- `comment delete COMMENT_ID`

### share
- `share list DOC_ID`
- `share add DOC_ID --member-id MEMBER_ID [--permission view|edit|admin]`
- `share remove SHARE_ID`

### template
- `template list`
- `template create --title TITLE --content CONTENT [--description DESC] [--category meeting-notes|proposal|technical-doc|other] [--created-by NAME]`
- `template delete TEMPLATE_ID`

### favorite
- `favorite list MEMBER_ID`
- `favorite add MEMBER_ID DOC_ID`
- `favorite remove MEMBER_ID DOC_ID`

### dashboard
- `dashboard` — summary: recent docs, favorites, workspace stats, recent activity

## Usage Examples

```bash
# Create a workspace
cli-anything-wikiflow --json workspace create --name "Engineering Wiki"

# Add a member
cli-anything-wikiflow --json member create --name "Alice" --email "alice@co.com" --role "admin"

# Create a folder
cli-anything-wikiflow --json folder create --workspace-id WS_ID --name "Architecture"

# Create and publish a document
DOC=$(cli-anything-wikiflow --json doc create --workspace-id WS_ID --title "Design Doc" --content "...")
DOC_ID=$(echo $DOC | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
cli-anything-wikiflow --json doc publish $DOC_ID

# Snapshot a version before editing
cli-anything-wikiflow --json version create $DOC_ID --change-note "Before refactor"

# Full-text search
cli-anything-wikiflow --json doc search "database"

# Dashboard
cli-anything-wikiflow dashboard
```

## Agent Usage Pattern

Always use `--json` flag when calling from code. Parse `id` from responses to chain operations.

Typical workflow: create workspace → add members → create folders → create docs → snapshot versions → add tags → share with members → dashboard.
