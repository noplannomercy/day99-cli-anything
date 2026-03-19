# CLI-Anything

> 웹앱을 만드는 순간 에이전트 인프라가 따라온다.

바이브코딩으로 만든 웹앱의 백엔드 로직을 CLI로 변환하고,
LLM이 자연어로 전체 시스템을 오케스트레이션한다.

```
사람용:    웹 UI (바이브코딩으로 생성)
에이전트용: CLI + SKILL.md → MCP → IRM 오케스트레이션
```

---

## 왜 CLI인가

| | MCP | CLI |
|--|-----|-----|
| 시작 비용 | 서버 설계, transport, 스키마 | Python 파일 하나 |
| 실행 | LLM 클라이언트 필요 | 어디서든 단독 실행 |
| 체이닝 | MCP 프로토콜 | Unix pipe, 그냥 연결 |
| 변환 시간 | 수 시간 | 5분 |

CLI는 MCP의 대체가 아니라 **앞단 레이어**다.
검증이 끝나면 MCP로 승격한다.

---

## 구현된 CLI

| CLI | 원본 웹앱 | 데이터 계층 | 변환 시간 |
|-----|---------|-----------|---------|
| `cli-anything-unit-converter` | unit-converter | 파일 기반 | ~5분 |
| `cli-anything-idea-generator` | idea-generator | 파일 기반 | ~5분 |
| `cli-anything-note-taker` | note-taker | 파일 기반 | ~5분 |
| `cli-anything-mini-crm` | mini-crm | PostgreSQL | ~15분 |
| `cli-anything-wikiflow` | wikiflow (5시간 개발) | 파일 기반 | ~5분 |

---

## 설치

```bash
pip install -e unit-converter/agent-harness
pip install -e idea-generator/agent-harness
pip install -e note-taker/agent-harness
pip install -e mini-crm/agent-harness
pip install -e wikiflow/agent-harness
```

mini-crm은 PostgreSQL 필요:
```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

설치 확인:
```bash
PYTHONIOENCODING=utf-8 cli-anything-wikiflow --help
PYTHONIOENCODING=utf-8 cli-anything-mini-crm --json stats
```

---

## 빠른 시작

```bash
# 단위 변환
cli-anything-unit-converter --json convert weight 100 kg lb

# 아이디어 생성
cli-anything-idea-generator --json generate --category coding

# 노트 생성
cli-anything-note-taker --json note create --title "첫 노트" --content "내용" --tags "test"

# CRM 현황
cli-anything-mini-crm --json stats

# 위키 대시보드
cli-anything-wikiflow dashboard
```

---

## LLM Native 시연

`CLAUDE.md`가 있어 이 디렉토리에서 Claude Code를 열면
5개 CLI의 SKILL.md가 자동으로 로딩된다.
자연어만 입력하면 Claude가 CLI를 골라서 실행한다.

### 단순 질의
```
100kg이 몇 파운드야?
코딩 아이디어 하나 줘봐
내 노트 목록 보여줘
CRM 현황 요약해줘
```

### 체이닝
```
코딩 아이디어 생성해서 즐겨찾기에 저장하고 노트에도 남겨줘
```

```
홍길동한테 오늘 킥오프 미팅 CRM에 기록하고 위키에 회의록도 만들어줘
```

### 복합 시나리오
```
신규 고객사 바포럼 온보딩해줘.
회사 등록하고, 담당자 김대표 추가하고, 딜 생성하고,
위키에 고객 페이지 만들고, 노트에 온보딩 요약 저장해줘.
```

→ 전체 시나리오: [DEMO-SCENARIOS.md](DEMO-SCENARIOS.md)

---

## 새 CLI 만들기

### Path A: 신규 앱
```
요구사항 분석 → 엔티티 설계 → CLI 커맨드 설계 → 구현 → 테스트
```

### Path B: 기존 코드베이스 변환

코드베이스에서 세 가지만 찾는다. 나머지는 전부 버린다.

```
찾을 것:
  1. 데이터 모델    — 엔티티 구조와 관계
  2. 데이터 접근    — 읽기/쓰기 로직
  3. 비즈니스 로직  — 도메인 규칙, 계산, 변환

버릴 것:
  - UI 전부 (컴포넌트, 스타일, 라우트, 이벤트)
  - 인증/세션
```

데이터 계층 교체:

| 원본 | CLI 교체 |
|------|---------|
| LocalStorage / 파일 | `~/.cli_anything_<app>.json` |
| PostgreSQL / ORM | psycopg2 직접 연결 |
| MongoDB | pymongo 직접 연결 |
| 외부 API | requests 직접 호출 |

→ 상세 런북: [CLI-COMPONENT-RUNBOOK.md](CLI-COMPONENT-RUNBOOK.md)

### 디렉토리 구조

```
agent-harness/
├── setup.py
└── cli_anything/                  # NO __init__.py (네임스페이스)
    └── <app>/                     # HAS __init__.py
        ├── __init__.py
        ├── <app>_cli.py           # CLI 진입점
        ├── core/
        │   ├── __init__.py
        │   ├── storage.py         # 데이터 레이어
        │   └── logger.py          # ACTION= 형식 로깅
        └── skills/
            └── SKILL.md           # LLM용 자기 기술 문서
```

### 설치 및 검증

```bash
cd agent-harness
pip install -e .

PYTHONIOENCODING=utf-8 cli-anything-<app> --help
PYTHONIOENCODING=utf-8 cli-anything-<app> --json <entity> list
PYTHONIOENCODING=utf-8 cli-anything-<app> --json <entity> create --name "test"
```

---

## SKILL.md

**SKILL.md가 없으면 LLM이 이 CLI의 존재를 모른다.**

LLM은 SKILL.md의 `description`을 보고 CLI를 쓸지 판단하고,
`Command Groups`를 보고 어떤 커맨드를 어떻게 호출할지 결정한다.

```markdown
---
name: cli-anything-<app>
command: cli-anything-<app>
description: <한 줄 요약. LLM이 이걸 보고 이 CLI를 쓸지 판단한다.>
flags:
  - --json
---

## Command Groups
### <entity>
- `<entity> list`
- `<entity> create --name NAME`
- `<entity> delete ID`

## Usage Examples
(실제 동작하는 예시 필수)
```

---

## MCP 승격

CLI가 검증되면 MCP tool로 래핑해서 표준화한다.

```python
from mcp.server.fastmcp import FastMCP
import subprocess, json, os

mcp = FastMCP("my-tools")

@mcp.tool(description="...")
def entity_create(name: str) -> dict:
    result = subprocess.run(
        ["cli-anything-<app>", "--json", "entity", "create", "--name", name],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    return json.loads(result.stdout)
```

SKILL.md → MCP tool description으로 1:1 변환. 전환 비용 사실상 0.

---

## 참고 문서

| 문서 | 설명 |
|------|------|
| [CONVERSION-METHODOLOGY.md](CONVERSION-METHODOLOGY.md) | 웹앱 → 에이전트 인프라 변환 방법론 |
| [CLI-COMPONENT-RUNBOOK.md](CLI-COMPONENT-RUNBOOK.md) | CLI 구성요소 생성 런북 (IRM 별첨) |
| [DEMO-SCENARIOS.md](DEMO-SCENARIOS.md) | LLM Native 시연 시나리오 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 세션 컨텍스트 |
