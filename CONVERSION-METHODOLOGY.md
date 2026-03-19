# 웹앱 → 에이전트 인프라 구축 방법론

## 핵심 가치

**웹앱을 만드는 순간 에이전트 인프라가 따라온다.**

Next.js 웹앱의 백엔드 로직을 CLI로 변환하고, SKILL.md로 자기 기술하면
LLM이 자연어로 전체 시스템을 오케스트레이션할 수 있다.

- 사람용: 웹 UI
- 에이전트용: CLI + SKILL.md

CLI-Anything 프레임워크 없이 직접 변환. 더 빠르고 통제 가능하다.

---

## 실증 데이터

| 앱 | 개발 시간 | CLI 변환 시간 | 오류 |
|---|---|---|---|
| unit-converter | - | ~5분 | 0 |
| idea-generator | - | ~5분 | 0 |
| note-taker | - | ~10분 | 0 |
| mini-crm | - | ~15분 | DB 스키마 불일치 2건 |
| wikiflow | 5시간 | ~5분 | 세미콜론 데코레이터 구문오류 1건 |

복잡도(피쳐 수)에만 비례하고 구조 자체는 항상 동일하다.

---

## 전환 공식

| 웹앱 레이어 | CLI 레이어 |
|---|---|
| LocalStorage / IndexedDB | `~/.cli_anything_<app>.json` (파일 기반) |
| PostgreSQL / Drizzle ORM | psycopg2 직접 연결 |
| API Routes (`/api/...`) | Click 커맨드 그룹 |
| UI 이벤트 핸들러 | Click 커맨드 함수 |
| TypeScript 타입 | Python dict |
| console.log | Python logging (ACTION= 형식) |
| cascade delete (JS 로직) | Python으로 직접 포팅 |

> UI 관련 코드(React 상태, 컴포넌트, 스타일)는 전부 버린다. 백엔드 로직만 포팅한다.

---

## 디렉토리 구조

```
<app-name>/
└── agent-harness/
    ├── setup.py                          # pip 패키지 설정
    └── cli_anything/                     # PEP 420 네임스페이스 (NO __init__.py)
        └── <app>/                        # 앱 패키지 (HAS __init__.py)
            ├── __init__.py
            ├── <app>_cli.py              # Click CLI 진입점
            ├── core/
            │   ├── __init__.py
            │   ├── storage.py            # 데이터 레이어
            │   └── logger.py             # ACTION= 형식 로깅
            └── skills/
                └── SKILL.md              # LLM용 자기 기술 문서
```

---

## 단계별 전환 절차

### 1단계: 데이터 모델 분석
- `src/types/index.ts` 또는 `src/lib/storage.ts` 분석
- 엔티티 목록 및 관계 파악 (cascade delete 포함)

### 2단계: storage.py 구현
```python
# LocalStorage → 파일 기반 JSON
DATA_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_<app>.json")

def _load(): ...
def _save(data): ...

# 각 엔티티별 CRUD
def get_<entity>s(**filters): ...
def get_<entity>(id): ...
def create_<entity>(**kwargs): ...
def update_<entity>(id, **kwargs): ...
def delete_<entity>(id): ...  # cascade 포함
```

### 3단계: logger.py 구현
```python
# ACTION= 형식으로 로깅 (추적가능성 확보)
LOG_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_<app>.log")

def log(action, **kwargs):
    logger.info("ACTION={} | {}".format(action,
        " | ".join(f"{k}={v}" for k, v in kwargs.items())))
```

### 4단계: CLI 진입점 구현
```python
@click.group()
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
def cli(ctx, json_output):
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output

# 각 도메인별 커맨드 그룹
@cli.group()
def <entity>():
    """<Entity> management."""
    pass

# CRUD 커맨드
@<entity>.command("create")
@click.option("--name", required=True)
@click.pass_context
def create(ctx, name):
    r = S.create_<entity>(name)
    log("create", name=name)
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created: {r['id']}")
```

### 5단계: setup.py 작성
```python
from setuptools import setup, find_namespace_packages
setup(
    name="cli-anything-<app>",
    version="0.1.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click"],
    entry_points={
        "console_scripts": ["cli-anything-<app>=cli_anything.<app>.<app>_cli:cli"]
    },
)
```

### 6단계: 설치 및 검증
```bash
cd agent-harness
pip install -e .
PYTHONIOENCODING=utf-8 cli-anything-<app> --help
PYTHONIOENCODING=utf-8 cli-anything-<app> --json <entity> create --name "test"
```

### 7단계: SKILL.md 작성

**SKILL.md 없으면 LLM이 CLI의 존재 자체를 모른다.** 반드시 작성해야 한다.

필수 구성:
```markdown
---
name: cli-anything-<app>
command: cli-anything-<app>
description: <한 줄 요약 — LLM이 이걸 보고 이 CLI를 쓸지 판단한다>
flags:
  - --json   # LLM 호출 시 항상 사용
---

# <App> CLI Skill

## Command Groups
### <entity>
- `<entity> list` — ...
- `<entity> create --name NAME` — ...
- `<entity> delete ID` — ...

## Usage Examples
(실제 동작하는 예시 필수 — LLM이 이걸 보고 체이닝 패턴을 학습한다)
```

---

## SKILL.md와 MCP의 관계

SKILL.md는 **두 번 쓰인다.**

### CLI 직접 호출 시 (개발/검증 단계)
```
LLM → SKILL.md 직접 읽음 → cli-anything-<app> 실행
```

### MCP로 래핑 후 (운영 단계)
```
LLM → MCP tool description 읽음 → MCP tool 호출 → CLI 실행
```

SKILL.md는 LLM에게 직접 노출되지 않고, **MCP tool description 작성 소스**로 쓰인다.
SKILL.md를 잘 써뒀으면 MCP 변환이 거의 복붙 수준 → **CLI → MCP 전환 비용 사실상 0.**

| 단계 | SKILL.md 역할 |
|---|---|
| CLI 개발/검증 | LLM이 직접 읽고 CLI 호출 |
| MCP 변환 시 | tool description 작성 소스 |
| MCP 운영 중 | 개발자 참조 문서로 보존 |

---

## MCP Aggregate 패턴 (멀티 CLI)

여러 CLI를 동시에 사용할 때 도메인 충돌이 발생할 수 있다.
MCP 서버로 각 CLI를 래핑하고 Aggregate MCP로 묶으면 해소된다.

```
LLM
 └── MCP Aggregate
      ├── MCP: wikiflow  → cli-anything-wikiflow
      ├── MCP: crm       → cli-anything-mini-crm
      └── MCP: notes     → cli-anything-note-taker
```

각 MCP tool 이름에 도메인 prefix를 붙여 충돌 방지:
- `wikiflow_doc_create`, `crm_contact_list` 등

### FastMCP 래핑 예시
```python
from mcp.server.fastmcp import FastMCP
import subprocess, json

mcp = FastMCP("wiki-tools")

@mcp.tool(
    description="""WikiFlow 문서 생성.
    workspace_id: 워크스페이스 ID (workspace list로 조회)
    title: 문서 제목
    content: 문서 내용 (기본값: "")
    status: draft | published | archived (기본값: draft)
    """
)
def wikiflow_doc_create(workspace_id: str, title: str,
                        content: str = "", status: str = "draft") -> dict:
    result = subprocess.run(
        ["cli-anything-wikiflow", "--json", "doc", "create",
         "--workspace-id", workspace_id, "--title", title,
         "--content", content, "--status", status],
        capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    return json.loads(result.stdout)
```

---

## 알려진 이슈 및 해결책

### Windows cp949 인코딩 오류
em-dash 등 특수문자가 CLI help 텍스트에 있으면 발생.
```bash
# 실행 시
PYTHONIOENCODING=utf-8 cli-anything-<app> ...

# MCP subprocess 호출 시
env={**os.environ, "PYTHONIOENCODING": "utf-8"}

# 근본 해결: CLI 텍스트에서 특수문자 제거
```

### PostgreSQL 타입 직렬화
Decimal, datetime 등 JSON 직렬화 안 되는 타입이 있을 수 있음.
```python
def _serial(obj):
    if isinstance(obj, decimal.Decimal): return int(obj)
    if isinstance(obj, datetime): return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")

json.dumps(data, default=_serial)
```

### DB 스키마 불일치
TypeScript 타입 정의와 실제 DB 컬럼명이 다를 수 있음.
포팅 전 반드시 실제 스키마 확인:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name='<table>';
```

---

## 바이브코딩과의 통합

**처음부터 CLI를 같이 만들면 아키텍처 품질이 올라가는 부수효과가 있다.**

CLI를 만들려면 비즈니스 로직이 UI에서 분리되어야 하기 때문에:
- 자연스럽게 클린 아키텍처가 된다
- 상태 관리가 명확해진다
- 테스트하기 쉬워진다

바이브코딩 프롬프트에 **"CLI 버전도 같이 생성해줘"** 한 줄 추가하는 것만으로
웹 UI + 에이전트 인프라가 동시에 나온다.

---

## 결론

**웹앱 개발 비용은 그대로, 에이전트 인프라는 덤으로 얻는다.**

1. 파일/DB 직접 연결로 상태 관리
2. Click으로 LLM 친화적 인터페이스 구성
3. `--json` 플래그로 구조화 출력
4. SKILL.md로 LLM에 자기 기술 → CLI 직접 호출 가능
5. MCP Aggregate로 멀티 도메인 묶기 → 크로스 도메인 오케스트레이션

day1~66 웹앱 전체를 이 방식으로 커버하면
**"자연어로 전체 시스템 오케스트레이션"** 이 현실이 된다.
