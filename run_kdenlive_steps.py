"""
cli-anything-kdenlive 작업 순서 실행 스크립트
각 단계를 순서대로 실행하고 JSON 결과를 출력합니다.
"""
import sys
import os
import json
from datetime import datetime

# cli-anything-kdenlive 모듈 경로 추가
sys.path.insert(0, r"C:\Users\vavag\.claude\plugins\marketplaces\cli-anything\kdenlive\agent-harness")

from cli_anything.kdenlive.core import project as proj_mod
from cli_anything.kdenlive.core import timeline as tl_mod
from cli_anything.kdenlive.core import export as export_mod
from cli_anything.kdenlive.core.session import Session

PROJECT_FILE = r"C:\workspace\prj20060203\day99-cli-anything\kdenlive-test.json"
MLT_OUTPUT = r"C:\workspace\prj20060203\day99-cli-anything\test.mlt"

def banner(step, title):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print('='*60)

def jprint(data):
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


# ── 세션 초기화 ──────────────────────────────────────────
sess = Session()


# ── Step 1: 프로젝트 생성 (1920x1080 30fps) ──────────────
banner(1, "프로젝트 생성 (1920x1080 30fps)")
proj = proj_mod.create_project(
    name="test-project",
    width=1920,
    height=1080,
    fps_num=30,
    fps_den=1,
)
sess.set_project(proj, PROJECT_FILE)
proj_mod.save_project(proj, PROJECT_FILE)
info = proj_mod.get_project_info(proj)
jprint(info)


# ── Step 2: 비디오 프로파일 목록 확인 ────────────────────
banner(2, "사용 가능한 비디오 프로파일 목록")
profiles = proj_mod.list_profiles()
jprint(profiles)


# ── Step 3: 비디오 트랙 추가 ─────────────────────────────
banner(3, "비디오 트랙 추가")
sess.snapshot("Add video track")
track = tl_mod.add_track(
    sess.get_project(),
    name="Video 1",
    track_type="video",
)
jprint(track)


# ── Step 4: 타임라인 목록 확인 ───────────────────────────
banner(4, "타임라인 트랙 목록")
tracks = tl_mod.list_tracks(sess.get_project())
jprint(tracks)


# ── Step 5: MLT XML 생성 ─────────────────────────────────
banner(5, f"MLT XML 생성 → {MLT_OUTPUT}")
xml_content = export_mod.generate_kdenlive_xml(sess.get_project())
# 파일 저장
os.makedirs(os.path.dirname(MLT_OUTPUT), exist_ok=True)
with open(MLT_OUTPUT, "w", encoding="utf-8") as f:
    f.write(xml_content)
result = {"status": "ok", "path": MLT_OUTPUT, "size_bytes": len(xml_content.encode("utf-8"))}
jprint(result)

# 프로젝트도 저장
sess.save_session(PROJECT_FILE)
print(f"\n프로젝트 저장: {PROJECT_FILE}")
