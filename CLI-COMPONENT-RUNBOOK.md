# CLI 구성요소 생성 런북

> IRM 별첨 — 코드베이스 또는 신규 요구사항으로부터 CLI 구성요소를 생성하는 방법론.
> 이 문서 하나로 새 세션에서 작업 실행 가능.
> 최종 갱신: 2026-03

---

## 이 문서의 사용법

**입력:**
- 기존 코드베이스 경로 (변환 경로)
- 또는 도메인 요구사항 (신규 경로)

**출력:**
- `cli-anything-<app>` — PATH에 설치된 CLI 명령어
- `SKILL.md` — LLM이 이 CLI를 자율 호출하기 위한 자기 기술 문서
- IRM Phase 1-B(접근) 또는 1-C(실행확정) 진입 가능한 구성요소

**전제 조건:**
- Python 3.9+, pip
- `click`, `setuptools` 설치 가능한 환경

---

## Step 0: 경로 선택

```
기존 코드베이스가 있는가?
├── Yes → Path B: 변환
└── No  → Path A: 신규
```

---

## Path A: 신규 CLI 생성

기존 코드베이스 없이 처음부터 만드는 경우.

**일반 소프트웨어 개발 프로세스와 동일하다.**

```
요구사항 분석 → 엔티티/데이터 모델 설계 → CLI 커맨드 설계 → 구현 → 테스트
```

설계가 끝나면 **공통: 구현 패턴** 섹션으로 이동.

---

## Path B: 기존 코드베이스 변환

### 핵심 원칙

**전체 코드베이스에서 세 가지만 찾는다. 나머지는 전부 버린다.**

```
찾을 것:
  1. 데이터 모델    — 엔티티 구조와 관계
  2. 데이터 접근    — 읽기/쓰기 로직
  3. 비즈니스 로직  — 도메인 규칙, 계산, 변환

버릴 것:
  - UI 전부       (컴포넌트, 스타일, 레이아웃)
  - 프레임워크    (라우트, 미들웨어, 핸들러)
  - 이벤트        (클릭, 폼 제출, 상태 변화)
  - 인증/세션      (CLI는 로컬 실행이므로 불필요)
```

---

### B-1: 데이터 모델 찾기

엔티티 구조와 관계를 파악한다. 코드를 이해하는 게 목적이고, 변환하는 게 아니다.

**스택별 위치:**

| 스택 | 위치 |
|------|------|
| Next.js / TypeScript | `src/types/index.ts`, `src/lib/types.ts` |
| Prisma | `prisma/schema.prisma` |
| Drizzle | `src/db/schema.ts` |
| Django | `models.py` |
| FastAPI | `schemas.py`, `models.py` |
| Spring | `@Entity` 클래스 |
| Rails | `app/models/`, `db/schema.rb` |

**확인할 것:**
- 엔티티 목록과 필드
- 엔티티 간 관계 (1:N, N:M)
- cascade delete 여부 (삭제 시 연쇄 삭제되는 관계)

---

### B-2: 데이터 접근 레이어 찾기

실제 읽기/쓰기가 일어나는 곳이다. 여기가 변환의 핵심이다.

**스택별 위치:**

| 스택 | 위치 |
|------|------|
| Next.js LocalStorage | `src/lib/storage.ts`, `src/hooks/use*.ts` |
| Next.js + Drizzle/Prisma | `src/lib/db.ts`, `src/server/` |
| FastAPI | `crud.py`, `repositories/` |
| Django | `views.py` QuerySet, `managers.py` |
| Spring | `@Repository`, `JpaRepository` |
| Rails | `app/models/` ActiveRecord 메서드 |

**데이터 계층 유형 판별 — 찾은 코드를 보고 아래 중 어디 해당하는지 확인:**

```
LocalStorage / 파일 기반
  → 코드에 localStorage.getItem, fs.readFile, JSON.parse 등장
  → CLI 교체: ~/.cli_anything_<app>.json (파일 기반)

관계형 DB (PostgreSQL, MySQL, SQLite)
  → 코드에 SELECT, INSERT, ORM 쿼리 등장
  → CLI 교체: psycopg2 / pymysql / sqlite3 직접 연결

문서 DB (MongoDB, Firebase)
  → 코드에 collection.find, document.get 등장
  → CLI 교체: pymongo / firebase-admin 직접 연결

외부 API
  → 코드에 fetch, axios, HTTP 호출 등장
  → CLI 교체: requests / httpx 직접 호출
```

---

### B-3: 비즈니스 로직 찾기

도메인 규칙, 계산, 변환 로직이다. 대부분 데이터 접근 레이어와 같은 파일에 있거나 별도 서비스 파일에 있다.

**확인할 것:**
- 데이터를 가공하는 함수 (정렬, 필터, 집계)
- 도메인 규칙 (유효성 검사, 상태 전이)
- 관계 처리 (cascade delete, 참조 무결성)

**이 로직은 Python으로 그대로 포팅한다.** 언어만 바뀌고 로직은 동일.

---

### B-4: 데이터 계층 교체 패턴

B-2에서 판별한 유형에 따라 교체한다.

**LocalStorage / 파일 기반 → JSON 파일**

```python
import json, os

DATA_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_<app>.json")

def _load():
    if not os.path.exists(DATA_FILE):
        return {"entities": []}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**관계형 DB → 드라이버 직접 연결**

```python
import psycopg2, os
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")

@contextmanager
def _conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def fetchall(sql, params=None):
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

def execute(sql, params=None):
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        return cur.rowcount
```

**외부 API → HTTP 클라이언트**

```python
import requests, os

BASE_URL = os.environ.get("<APP>_API_URL", "https://api.example.com")
API_KEY  = os.environ.get("<APP>_API_KEY", "")

def _get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", params=params,
                     headers={"Authorization": f"Bearer {API_KEY}"})
    r.raise_for_status()
    return r.json()

def _post(path, data):
    r = requests.post(f"{BASE_URL}{path}", json=data,
                      headers={"Authorization": f"Bearer {API_KEY}"})
    r.raise_for_status()
    return r.json()
```

---

## 공통: 구현 패턴

Path A, Path B 모두 여기서 합류한다.

### 디렉토리 구조

```
agent-harness/
├── setup.py
└── cli_anything/                  # NO __init__.py (PEP 420 네임스페이스)
    └── <app>/                     # HAS __init__.py
        ├── __init__.py
        ├── <app>_cli.py           # CLI 진입점
        ├── core/
        │   ├── __init__.py
        │   ├── storage.py         # 데이터 레이어
        │   └── logger.py          # 로깅
        └── skills/
            └── SKILL.md
```

### logger.py 템플릿

```python
import logging, os

LOG_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_<app>.log")
_logger = None

def get_logger():
    global _logger
    if _logger: return _logger
    _logger = logging.getLogger("<app>")
    _logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(fh)
    return _logger

def log(action: str, **kwargs):
    get_logger().info("ACTION={} | {}".format(
        action, " | ".join(f"{k}={v}" for k, v in kwargs.items())))
```

### <app>_cli.py 템플릿

```python
import json, sys
import click
from cli_anything.<app>.core import storage as S
from cli_anything.<app>.core.logger import log

@click.group()
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
def cli(ctx, json_output):
    """<App> CLI"""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output

def _out(ctx, data):
    if ctx.obj["json"]:
        click.echo(json.dumps(data, ensure_ascii=False))

def _err(ctx, msg):
    d = {"error": msg}
    click.echo(json.dumps(d) if ctx.obj["json"] else f"Error: {msg}",
               err=not ctx.obj["json"])
    sys.exit(1)

# 커맨드 그룹 패턴
@cli.group()
def <entity>():
    """<Entity> management."""
    pass

@<entity>.command("list")
@click.pass_context
def entity_list(ctx):
    rows = S.get_<entity>s()
    log("<entity>_list", count=len(rows))
    if ctx.obj["json"]: click.echo(json.dumps(rows, ensure_ascii=False))
    else: click.echo("\n".join(str(r) for r in rows) or "Empty.")

@<entity>.command("create")
@click.option("--name", required=True)
@click.pass_context
def entity_create(ctx, name):
    r = S.create_<entity>(name)
    log("<entity>_create", name=name, id=r["id"])
    if ctx.obj["json"]: click.echo(json.dumps(r, ensure_ascii=False))
    else: click.echo(f"Created [{r['id']}]: {r['name']}")

def main():
    cli(obj={})

if __name__ == "__main__":
    main()
```

### setup.py 템플릿

```python
from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-<app>",
    version="0.1.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "cli-anything-<app>=cli_anything.<app>.<app>_cli:cli"
        ]
    },
)
```

---

## 공통: SKILL.md 작성

**SKILL.md가 없으면 LLM이 이 CLI의 존재를 모른다. 반드시 작성한다.**

LLM은 SKILL.md의 `description`을 보고 이 CLI를 쓸지 판단하고,
`Command Groups`를 보고 어떤 커맨드를 어떻게 호출할지 결정한다.

### 템플릿

```markdown
---
name: cli-anything-<app>
command: cli-anything-<app>
description: <한 줄 요약. LLM이 이걸 보고 이 CLI를 쓸지 판단한다.>
flags:
  - --json   # LLM 호출 시 항상 사용
---

# <App> CLI Skill

## Command Groups

### <entity>
- `<entity> list` — 전체 조회
- `<entity> create --name NAME` — 생성
- `<entity> get ID` — 단건 조회
- `<entity> update ID --name NAME` — 수정
- `<entity> delete ID` — 삭제

## Usage Examples

(실제 동작하는 예시 필수. LLM이 체이닝 패턴을 여기서 학습한다.)

    # 생성 후 ID 추출
    RESULT=$(cli-anything-<app> --json <entity> create --name "test")
    ID=$(echo $RESULT | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

    # 목록 조회
    cli-anything-<app> --json <entity> list

## Agent Usage Pattern
항상 --json 플래그를 사용한다.
앞 단계 응답의 id를 다음 단계 인수로 넘긴다.
```

---

## 공통: 설치 및 검증

```bash
# 설치
cd agent-harness
pip install -e .

# 검증
PYTHONIOENCODING=utf-8 cli-anything-<app> --help
PYTHONIOENCODING=utf-8 cli-anything-<app> --json <entity> list
PYTHONIOENCODING=utf-8 cli-anything-<app> --json <entity> create --name "test"
```

**검증 체크리스트:**
- [ ] `--help` 출력에 모든 커맨드 그룹이 보이는가
- [ ] `--json` 플래그 시 유효한 JSON이 출력되는가
- [ ] create → list 순서로 실행 시 생성한 항목이 목록에 나오는가
- [ ] 로그 파일이 생성되는가 (`~/.cli_anything_<app>.log`)

---

## 알려진 이슈

**Windows cp949 인코딩 오류**
CLI 텍스트에 em-dash 등 특수문자가 있으면 발생.
```bash
PYTHONIOENCODING=utf-8 cli-anything-<app> ...
```

**PostgreSQL 타입 직렬화**
Decimal, datetime 등 JSON 직렬화 안 되는 타입.
```python
def _serial(obj):
    import decimal
    from datetime import datetime
    if isinstance(obj, decimal.Decimal): return int(obj)
    if isinstance(obj, datetime): return obj.isoformat()
    raise TypeError(type(obj))

json.dumps(data, default=_serial)
```

**DB 스키마 불일치**
코드의 필드명과 실제 DB 컬럼명이 다를 수 있다.
변환 전 실제 스키마 확인:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name='<table>';
```

---

## IRM 연결

이 런북의 산출물은 IRM Phase 1에 직접 진입한다.

| CLI 성격 | IRM 진입점 | 판단 기준 |
|---------|-----------|---------|
| 데이터 조회 중심 | Phase 1-B (접근) | 상태 변경 없음, readOnly |
| 절차 실행 포함 | Phase 1-C (실행확정) | 외부 시스템 실행, 상태 변경 |

**MCP 승격 준비:**
- SKILL.md의 각 커맨드 → MCP tool description으로 1:1 변환
- CLI → MCP 내부 `_run()` 으로 래핑
- → IRM MCP 승격 설계 가이드 §7 참조
