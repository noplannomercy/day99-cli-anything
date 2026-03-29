"""
cli-anything MCP Server

IRM Phase 1-B/C 승격: idea-generator / note-taker / mini-crm / wikiflow
구조: FastMCP → _run() → CLI subprocess (list args, no shell injection)
로깅: ~/.cli_anything_mcp.log
"""
import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# ─── 서버 초기화 ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "cli-anything",
    instructions=(
        "idea-generator / note-taker / mini-crm / wikiflow CLI를 MCP tool로 노출. "
        "unit-converter 제외. 모든 tool은 CLI subprocess를 경유한다."
    ),
)

# ─── 로깅 ───────────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_mcp.log")
_log = logging.getLogger("cli-anything-mcp")
_log.setLevel(logging.DEBUG)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_log.addHandler(_fh)


# ─── 공통 유틸 ──────────────────────────────────────────────────────────────────
async def _run(args: list[str]) -> tuple[bool, str]:
    """모든 CLI 호출의 단일 경유 지점. asyncio.to_thread로 Windows 호환성 확보."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd_str = " ".join(args)
    _log.info(f"RUN | {cmd_str}")
    t0 = datetime.now()

    def _sync() -> tuple[bool, str]:
        result = subprocess.run(
            args,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        ok = result.returncode == 0
        return ok, result.stdout.strip() if ok else result.stderr.strip()

    ok, out = await asyncio.to_thread(_sync)
    elapsed = (datetime.now() - t0).total_seconds()
    _log.info(f"RESULT | ok={ok} | elapsed={elapsed:.3f}s | cmd={cmd_str}")
    if not ok:
        _log.error(f"STDERR | {out}")
    return ok, out


def _parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "JSON 파싱 실패", "raw": raw}


def _ok(data) -> str:
    return json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2)


def _fail(msg: str, detail: str = "") -> str:
    return json.dumps(
        {"success": False, "error": msg, "detail": detail},
        ensure_ascii=False,
        indent=2,
    )


# ════════════════════════════════════════════════════════════════════════════════
# IDEA GENERATOR
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="idea_generate")
async def idea_generate(category: str = "coding") -> str:
    """
    창의 아이디어를 1개 생성한다.

    트리거 조건:
    - "아이디어 줘", "아이디어 생성", "영감", "inspiration" 등의 요청
    - category: writing | drawing | business | coding (기본값: coding)

    반환: 생성된 아이디어 텍스트 + 카테고리
    다음 단계: 마음에 들면 idea_favorites_save로 저장
    """
    ok, raw = await _run(
        ["cli-anything-idea-generator", "--json", "generate", "--category", category]
    )
    if not ok:
        return _fail("아이디어 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="idea_favorites_save")
async def idea_favorites_save(content: str, category: str = "coding") -> str:
    """
    아이디어를 즐겨찾기에 저장한다.

    트리거 조건:
    - "아이디어 저장해줘", "즐겨찾기 추가" 요청 시
    - idea_generate 결과를 보존할 때

    선행 조건: idea_generate 호출로 content 확보
    반환: 저장된 즐겨찾기 항목 (content, category, saved_at)
    """
    ok, raw = await _run(
        [
            "cli-anything-idea-generator", "--json",
            "favorites", "save", content,
            "--category", category,
        ]
    )
    if not ok:
        return _fail("즐겨찾기 저장 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="idea_favorites_list")
async def idea_favorites_list() -> str:
    """
    즐겨찾기에 저장된 아이디어 목록을 반환한다.

    트리거 조건:
    - "즐겨찾기 목록", "저장된 아이디어 보여줘" 요청 시

    반환: 즐겨찾기 목록 (content, category, saved_at)
    """
    ok, raw = await _run(
        ["cli-anything-idea-generator", "--json", "favorites", "list"]
    )
    if not ok:
        return _fail("즐겨찾기 목록 조회 실패", raw)
    return _ok(_parse(raw))


# ════════════════════════════════════════════════════════════════════════════════
# NOTE TAKER
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="note_create")
async def note_create(title: str, content: str, tags: str = "") -> str:
    """
    노트를 생성하고 저장한다.

    트리거 조건:
    - "노트 저장", "메모해줘", "기록해줘" 등의 요청
    - 다른 tool 실행 결과를 노트로 남길 때
    - tags: 쉼표 구분 문자열 (예: "work,meeting")

    반환: 생성된 노트 (id, title, content, tags, created_at)
    다음 단계: note_pin으로 핀 고정 가능
    """
    args = [
        "cli-anything-note-taker", "--json",
        "note", "create",
        "--title", title,
        "--content", content,
    ]
    if tags:
        args += ["--tags", tags]
    ok, raw = await _run(args)
    if not ok:
        return _fail("노트 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="note_list")
async def note_list(sort: str = "updated") -> str:
    """
    저장된 노트 목록을 반환한다.

    트리거 조건:
    - "내 노트 보여줘", "노트 목록" 요청 시
    - sort: updated | created | title (기본값: updated)

    반환: 노트 목록 (id, title, tags, pinned, updated_at)
    """
    ok, raw = await _run(
        ["cli-anything-note-taker", "--json", "note", "list", "--sort", sort]
    )
    if not ok:
        return _fail("노트 목록 조회 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="note_search")
async def note_search(keyword: str, tags: str = "") -> str:
    """
    키워드와 태그로 노트를 검색한다.

    트리거 조건:
    - "노트 검색", "~관련 노트 찾아줘" 요청 시
    - 특정 태그가 달린 노트를 찾을 때
    - tags: 쉼표 구분 문자열 (예: "work,sprint")

    반환: 조건에 맞는 노트 목록
    """
    args = ["cli-anything-note-taker", "--json", "search", keyword]
    if tags:
        args += ["--tags", tags]
    ok, raw = await _run(args)
    if not ok:
        return _fail("노트 검색 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="note_pin")
async def note_pin(note_id: str) -> str:
    """
    노트를 핀 고정(토글)한다. 이미 핀된 노트는 핀 해제된다.

    트리거 조건:
    - "노트 고정", "상단에 고정" 요청 시

    선행 조건: note_id 확보 (note_create 또는 note_list 결과에서)
    반환: 핀 상태가 변경된 노트
    """
    ok, raw = await _run(
        ["cli-anything-note-taker", "--json", "note", "pin", note_id]
    )
    if not ok:
        return _fail("노트 핀 실패", raw)
    return _ok(_parse(raw))


# ════════════════════════════════════════════════════════════════════════════════
# MINI CRM
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="crm_stats")
async def crm_stats() -> str:
    """
    CRM 전체 현황과 파이프라인 통계를 반환한다.

    트리거 조건:
    - "CRM 현황", "파이프라인 요약", "CRM 통계" 요청 시
    - 온보딩/플래닝 시작 전 현재 상태 파악 시

    반환: 회사/연락처/딜/활동/태스크 수 + 파이프라인 단계별 집계
    """
    ok, raw = await _run(["cli-anything-mini-crm", "--json", "stats"])
    if not ok:
        return _fail("CRM 통계 조회 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="crm_company_create")
async def crm_company_create(name: str, industry: str = "") -> str:
    """
    CRM에 새 회사를 등록한다.

    트리거 조건:
    - "회사 등록", "고객사 추가", "파트너사 등록" 요청 시
    - 온보딩 플로우의 첫 번째 단계

    반환: 생성된 회사 (id, name, industry, created_at)
    다음 단계: 반환된 id를 crm_contact_create / crm_deal_create의 company_id로 사용
    """
    args = ["cli-anything-mini-crm", "--json", "company", "create", "--name", name]
    if industry:
        args += ["--industry", industry]
    ok, raw = await _run(args)
    if not ok:
        return _fail("회사 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="crm_contact_create")
async def crm_contact_create(name: str, email: str, company_id: str = "") -> str:
    """
    CRM에 새 연락처(담당자)를 등록한다.

    트리거 조건:
    - "담당자 추가", "연락처 등록", "담당자 등록" 요청 시

    선행 조건: company_id가 필요하면 crm_company_create 먼저 호출
    반환: 생성된 연락처 (id, name, email, company_id)
    다음 단계: 반환된 id를 crm_activity_create의 contact_id로 사용
    """
    args = [
        "cli-anything-mini-crm", "--json",
        "contact", "create",
        "--name", name,
        "--email", email,
    ]
    if company_id:
        args += ["--company-id", company_id]
    ok, raw = await _run(args)
    if not ok:
        return _fail("연락처 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="crm_deal_create")
async def crm_deal_create(title: str, stage: str = "lead", company_id: str = "") -> str:
    """
    CRM에 새 딜(영업 기회)을 생성한다.

    트리거 조건:
    - "딜 생성", "영업 기회 등록", "계약 딜 만들어" 요청 시
    - stage: lead | qualified | proposal | negotiation | closed_won | closed_lost

    선행 조건: company_id가 필요하면 crm_company_create 먼저 호출
    반환: 생성된 딜 (id, title, stage, company_id)
    """
    args = [
        "cli-anything-mini-crm", "--json",
        "deal", "create",
        "--title", title,
        "--stage", stage,
    ]
    if company_id:
        args += ["--company-id", company_id]
    ok, raw = await _run(args)
    if not ok:
        return _fail("딜 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="crm_activity_create")
async def crm_activity_create(
    title: str, activity_type: str = "meeting", contact_id: str = ""
) -> str:
    """
    CRM에 활동(미팅/콜/이메일 등)을 기록한다.

    트리거 조건:
    - "미팅 기록", "콜 기록", "활동 로그 남겨줘" 요청 시
    - activity_type: call | email | meeting | note

    선행 조건: contact_id가 필요하면 crm_contact_create 먼저 호출
    반환: 생성된 활동 기록 (id, title, type, contact_id, created_at)
    """
    args = [
        "cli-anything-mini-crm", "--json",
        "activity", "create",
        "--title", title,
        "--type", activity_type,
    ]
    if contact_id:
        args += ["--contact-id", contact_id]
    ok, raw = await _run(args)
    if not ok:
        return _fail("활동 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="crm_task_create")
async def crm_task_create(title: str, priority: str = "medium") -> str:
    """
    CRM에 태스크를 등록한다.

    트리거 조건:
    - "태스크 등록", "할 일 추가", "검토 태스크 만들어" 요청 시
    - priority: low | medium | high

    반환: 생성된 태스크 (id, title, priority, status=pending)
    """
    ok, raw = await _run(
        [
            "cli-anything-mini-crm", "--json",
            "task", "create",
            "--title", title,
            "--priority", priority,
        ]
    )
    if not ok:
        return _fail("태스크 생성 실패", raw)
    return _ok(_parse(raw))


# ════════════════════════════════════════════════════════════════════════════════
# WIKIFLOW
# ════════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="wiki_workspace_list")
async def wiki_workspace_list() -> str:
    """
    위키 워크스페이스 목록을 반환한다.

    트리거 조건:
    - "워크스페이스 목록", "위키 현황 보여줘" 요청 시
    - 기존 워크스페이스 id를 확인할 때

    반환: 워크스페이스 목록 (id, name, created_at)
    다음 단계: id를 wiki_folder_create / wiki_doc_create의 workspace_id로 사용
    """
    ok, raw = await _run(
        ["cli-anything-wikiflow", "--json", "workspace", "list"]
    )
    if not ok:
        return _fail("워크스페이스 목록 조회 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_workspace_create")
async def wiki_workspace_create(name: str) -> str:
    """
    새 위키 워크스페이스를 생성한다.

    트리거 조건:
    - "워크스페이스 만들어", "새 위키 공간 생성" 요청 시
    - 새 프로젝트/도메인 위키 공간이 필요할 때

    반환: 생성된 워크스페이스 (id, name, created_at)
    다음 단계: 반환된 id를 wiki_folder_create / wiki_doc_create의 workspace_id로 사용
    """
    ok, raw = await _run(
        ["cli-anything-wikiflow", "--json", "workspace", "create", "--name", name]
    )
    if not ok:
        return _fail("워크스페이스 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_folder_create")
async def wiki_folder_create(workspace_id: str, name: str) -> str:
    """
    워크스페이스 안에 폴더를 생성한다.

    트리거 조건:
    - "폴더 만들어", "카테고리 추가" 요청 시

    선행 조건: wiki_workspace_create 또는 wiki_workspace_list로 workspace_id 확보
    반환: 생성된 폴더 (id, name, workspace_id)
    다음 단계: 반환된 id를 wiki_doc_create의 folder_id로 사용 가능
    """
    ok, raw = await _run(
        [
            "cli-anything-wikiflow", "--json",
            "folder", "create",
            "--workspace-id", workspace_id,
            "--name", name,
        ]
    )
    if not ok:
        return _fail("폴더 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_doc_create")
async def wiki_doc_create(
    workspace_id: str, title: str, content: str, folder_id: str = ""
) -> str:
    """
    위키 문서를 생성한다. 생성 직후 상태는 draft이다.

    트리거 조건:
    - "문서 작성", "위키 페이지 만들어", "초안 작성" 요청 시

    선행 조건: wiki_workspace_create 또는 wiki_workspace_list로 workspace_id 확보
    반환: 생성된 문서 (id, title, status=draft, workspace_id)
    다음 단계:
    - wiki_doc_publish 로 퍼블리시
    - wiki_version_create 로 버전 스냅샷 생성
    - wiki_tag_add 로 태그 연결
    """
    args = [
        "cli-anything-wikiflow", "--json",
        "doc", "create",
        "--workspace-id", workspace_id,
        "--title", title,
        "--content", content,
    ]
    if folder_id:
        args += ["--folder-id", folder_id]
    ok, raw = await _run(args)
    if not ok:
        return _fail("문서 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_doc_publish")
async def wiki_doc_publish(doc_id: str) -> str:
    """
    draft 상태의 위키 문서를 published로 변경한다.

    트리거 조건:
    - "문서 퍼블리시", "공개", "발행해줘" 요청 시
    - wiki_doc_create 이후 공개 상태로 만들 때

    선행 조건: wiki_doc_create로 doc_id 확보
    반환: 업데이트된 문서 (id, title, status=published)
    """
    ok, raw = await _run(
        ["cli-anything-wikiflow", "--json", "doc", "publish", doc_id]
    )
    if not ok:
        return _fail("문서 퍼블리시 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_version_create")
async def wiki_version_create(doc_id: str, change_note: str = "") -> str:
    """
    위키 문서의 버전 스냅샷을 생성한다.

    트리거 조건:
    - "버전 생성", "스냅샷 저장", "버전 남겨줘" 요청 시

    선행 조건: wiki_doc_create로 doc_id 확보
    반환: 생성된 버전 (id, doc_id, version_number, change_note)
    """
    args = ["cli-anything-wikiflow", "--json", "version", "create", doc_id]
    if change_note:
        args += ["--change-note", change_note]
    ok, raw = await _run(args)
    if not ok:
        return _fail("버전 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_tag_create")
async def wiki_tag_create(name: str) -> str:
    """
    새 위키 태그를 생성한다.

    트리거 조건:
    - "태그 만들어", "새 태그 추가" 요청 시
    - 문서에 달 태그가 아직 없을 때

    반환: 생성된 태그 (id, name)
    다음 단계: 반환된 id를 wiki_tag_add의 tag_id로 사용
    """
    ok, raw = await _run(
        ["cli-anything-wikiflow", "--json", "tag", "create", "--name", name]
    )
    if not ok:
        return _fail("태그 생성 실패", raw)
    return _ok(_parse(raw))


@mcp.tool(name="wiki_tag_add")
async def wiki_tag_add(doc_id: str, tag_id: str) -> str:
    """
    위키 문서에 태그를 연결한다.

    트리거 조건:
    - "문서에 태그 달아줘" 요청 시

    선행 조건:
    - wiki_doc_create로 doc_id 확보
    - wiki_tag_create로 tag_id 확보
    반환: 태그가 추가된 문서 정보
    """
    ok, raw = await _run(
        ["cli-anything-wikiflow", "--json", "tag", "add", doc_id, tag_id]
    )
    if not ok:
        return _fail("태그 추가 실패", raw)
    return _ok(_parse(raw))


# ─── 진입점 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
