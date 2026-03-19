---
name: cli-anything-note-taker
description: Command-line interface for note management. Full CRUD, tag system, text/tag search, pin, duplicate, export/import JSON. Supports --json output for agent consumption.
---

# cli-anything-note-taker

노트 관리 CLI - 생성/수정/삭제/검색/태그/핀/내보내기.

## Installation

```bash
pip install cli-anything-note-taker
```

## Command Groups

### note

| Command | Description |
|---------|-------------|
| `note create --title X [--content Y] [--tags Z]` | 노트 생성 |
| `note list [--sort updated\|created\|title] [--limit N] [--pinned]` | 목록 조회 |
| `note get ID` | 단일 노트 조회 |
| `note update ID [--title X] [--content Y] [--tags Z]` | 수정 |
| `note delete ID` | 삭제 |
| `note pin ID` | 핀 토글 |
| `note duplicate ID` | 복제 |

```bash
cli-anything-note-taker --json note create --title "회의록" --content "10시 미팅" --tags "work,urgent"
# -> {"id": "note_...", "title": "회의록", "tags": ["work", "urgent"], ...}

cli-anything-note-taker --json note list --sort updated --limit 10
cli-anything-note-taker --json note get note_19d03fdab83_zgkfpch93
cli-anything-note-taker --json note update NOTE_ID --title "새 제목"
cli-anything-note-taker --json note delete NOTE_ID
cli-anything-note-taker --json note pin NOTE_ID
cli-anything-note-taker --json note duplicate NOTE_ID
```

### search

텍스트 + 태그 복합 검색 (AND 로직).

```bash
cli-anything-note-taker --json search "미팅"
cli-anything-note-taker --json search "" --tags "work,urgent"
cli-anything-note-taker --json search "프로젝트" --tags "work" --sort title
```

### tags

| Command | Description |
|---------|-------------|
| `tags list` | 전체 태그 목록 |
| `tags counts` | 태그별 사용 횟수 |
| `tags rename OLD NEW` | 전체 노트에서 태그 일괄 변경 |

```bash
cli-anything-note-taker --json tags list
cli-anything-note-taker --json tags counts
cli-anything-note-taker --json tags rename work job
```

### export / import

```bash
cli-anything-note-taker export --output backup.json
cli-anything-note-taker --json import backup.json
cli-anything-note-taker --json import backup.json --merge   # 기존 노트에 병합
```

## For AI Agents

1. **항상 `--json` 플래그 사용** - 구조화된 출력
2. **노트 ID 형식** - `note_<hex_timestamp>_<random9>`
3. **태그 규칙** - 소문자, 최대 20자, 최대 10개, 중복 자동 제거
4. **정렬** - 핀 노트 항상 최상단, 그 다음 sort_by 기준
5. **로그** - `~/.cli_anything_note_taker.log`
6. **저장소** - `~/.cli_anything_note_taker_notes.json`

## Version

1.0.0
