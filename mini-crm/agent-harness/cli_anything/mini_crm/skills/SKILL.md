---
name: cli-anything-mini-crm
description: CRM CLI for managing contacts, companies, deals, activities, and tasks. Connected to PostgreSQL. Use --json for agent-friendly output.
---

# cli-anything-mini-crm

미니 CRM CLI - 연락처, 회사, 딜(파이프라인), 활동, 태스크 관리. PostgreSQL 직접 연결.

## Installation

```bash
pip install cli-anything-mini-crm
```

## Command Groups

### company

| Command | Description |
|---------|-------------|
| `company list [--limit N]` | 회사 목록 |
| `company get ID` | 단일 회사 조회 |
| `company create --name X [--industry Y] [--website Z] [--memo M]` | 회사 생성 |
| `company update ID [--name X] [--industry Y] [--website Z] [--memo M]` | 수정 |
| `company delete ID` | 삭제 |

### contact

| Command | Description |
|---------|-------------|
| `contact list [--company-id ID] [--limit N]` | 연락처 목록 |
| `contact get ID` | 단일 연락처 조회 |
| `contact create --name X [--email E] [--phone P] [--position POS] [--company-id ID]` | 생성 |
| `contact update ID [옵션들]` | 수정 |
| `contact delete ID` | 삭제 |

### deal

| Command | Description |
|---------|-------------|
| `deal list [--stage STAGE] [--limit N]` | 딜 목록 |
| `deal create --title X [--amount N] [--stage STAGE] [--company-id ID] [--contact-id ID]` | 생성 |
| `deal stage DEAL_ID NEW_STAGE` | 단계 변경 |
| `deal delete ID` | 삭제 |

**deal stages:** `lead` → `qualified` → `proposal` → `negotiation` → `closed_won` / `closed_lost`

### activity

| Command | Description |
|---------|-------------|
| `activity list [--contact-id ID] [--type TYPE] [--limit N]` | 활동 목록 |
| `activity create --title X --type TYPE [--description D] [--contact-id ID] [--deal-id ID]` | 활동 기록 |

**activity types:** `call`, `email`, `meeting`, `note`

### task

| Command | Description |
|---------|-------------|
| `task list [--done] [--priority PRIORITY] [--limit N]` | 태스크 목록 |
| `task create --title X [--priority PRIORITY] [--due-date YYYY-MM-DD] [--contact-id ID]` | 생성 |
| `task complete TASK_ID` | 완료 처리 |

**priorities:** `low`, `medium`, `high`

### search / stats

```bash
cli-anything-mini-crm --json search "키워드"
cli-anything-mini-crm --json stats
```

## 사용 예시

```bash
cli-anything-mini-crm --json stats
# -> {"totals": {"contacts": 3, "companies": 2, "deals": 4, ...}, "pipeline": [...]}

cli-anything-mini-crm --json company list
cli-anything-mini-crm --json contact create --name "홍길동" --email "hong@test.com" --company-id UUID
cli-anything-mini-crm --json deal stage DEAL_ID qualified
cli-anything-mini-crm --json search "baforum"
```

## For AI Agents

1. **항상 `--json` 플래그 사용**
2. **ID 형식** - UUID (예: `6b0da7a9-4251-45db-bfb7-3e7fdbcc264f`)
3. **리턴코드** - 0: 성공, 1: not_found 또는 오류
4. **로그** - `~/.cli_anything_mini_crm.log`
5. **DB** - PostgreSQL (DATABASE_URL 환경변수로 오버라이드 가능)

## Version

1.0.0
