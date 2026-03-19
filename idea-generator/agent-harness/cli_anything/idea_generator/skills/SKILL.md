---
name: cli-anything-idea-generator
description: Command-line interface for random creative idea generation. Categories: writing, drawing, business, coding. Supports favorites management and JSON output for agent consumption.
---

# cli-anything-idea-generator

랜덤 창의 아이디어 생성 CLI - writing, drawing, business, coding 카테고리.

## Installation

```bash
pip install cli-anything-idea-generator
```

## Usage

```bash
# JSON 출력 (에이전트용)
cli-anything-idea-generator --json generate --category writing

# 일반 출력
cli-anything-idea-generator generate --category coding
```

## Command Groups

### generate

랜덤 아이디어 생성.

| Option | Description | Values |
|--------|-------------|--------|
| `--category` / `-c` | 카테고리 | writing, drawing, business, coding |

```bash
cli-anything-idea-generator --json generate --category writing
# -> {"category": "writing", "idea": "A ghost tries to solve their own murder"}

cli-anything-idea-generator --json generate --category coding
# -> {"category": "coding", "idea": "Build a markdown editor with live preview"}

cli-anything-idea-generator --json generate
# -> {"category": "writing", "idea": "..."}  (default: writing)
```

### favorites

즐겨찾기 관리.

| Command | Description |
|---------|-------------|
| `list [--limit N]` | 즐겨찾기 목록 조회 |
| `save TEXT [--category X]` | 아이디어 저장 |
| `remove ID` | ID로 즐겨찾기 삭제 |
| `clear` | 전체 삭제 |

```bash
cli-anything-idea-generator --json favorites list
# -> [{"id": 1773887827544, "category": "writing", "text": "...", "timestamp": "..."}]

cli-anything-idea-generator --json favorites save "My idea" --category coding
# -> {"id": 1773887827544, "category": "coding", "text": "My idea", "timestamp": "..."}

cli-anything-idea-generator --json favorites remove 1773887827544
# -> {"status": "removed", "id": 1773887827544}

cli-anything-idea-generator --json favorites clear
# -> {"status": "ok", "removed": 3}
```

## For AI Agents

1. **항상 `--json` 플래그 사용** - 구조화된 출력으로 파싱 용이
2. **리턴코드 확인** - 0: 성공, 1: 오류 (중복, ID 없음 등)
3. **로그 위치** - `~/.cli_anything_idea_generator.log` (ACTION= 형식)
4. **즐겨찾기 저장소** - `~/.cli_anything_idea_generator_favorites.json`
5. **중복 방지** - 동일 세션 내 연속 동일 아이디어 생성 안함, 즐겨찾기 중복 저장 불가

## Version

1.0.0
