"""
LLM Native 시연 — 자연어 → CLI 자동 실행
"""
import os
import subprocess
import anthropic

# ─────────────────────────────────────────
# SKILL.md 로딩
# ─────────────────────────────────────────
SKILL_PATHS = {
    "unit-converter":  r"unit-converter\agent-harness\cli_anything\unit_converter\skills\SKILL.md",
    "idea-generator":  r"idea-generator\agent-harness\cli_anything\idea_generator\skills\SKILL.md",
    "note-taker":      r"note-taker\agent-harness\cli_anything\note_taker\skills\SKILL.md",
    "mini-crm":        r"mini-crm\agent-harness\cli_anything\mini_crm\skills\SKILL.md",
    "wikiflow":        r"wikiflow\agent-harness\cli_anything\wikiflow\skills\SKILL.md",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_skills():
    skills = []
    for name, rel_path in SKILL_PATHS.items():
        path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                skills.append(f"### {name}\n{f.read()}")
    return "\n\n".join(skills)

SKILLS = load_skills()

SYSTEM_PROMPT = f"""당신은 다음 CLI 도구들을 자유롭게 사용할 수 있는 에이전트입니다.
사용자의 자연어 요청을 받으면, 적절한 CLI 도구를 선택해 작업을 완료하세요.

규칙:
- 항상 --json 플래그를 사용하세요
- 여러 단계가 필요하면 순서대로 실행하세요
- 앞 단계 결과의 id를 다음 단계에 넘기세요
- 실행 전 어떤 작업을 할지 한 줄로 설명하세요

사용 가능한 CLI:

{SKILLS}
"""

# ─────────────────────────────────────────
# CLI 실행 도구
# ─────────────────────────────────────────
def run_cli(command: str) -> str:
    """CLI 명령어를 실행하고 결과를 반환합니다."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace"
    )
    output = result.stdout.strip()
    if result.stderr.strip():
        output += f"\n[stderr] {result.stderr.strip()}"
    return output or "(출력 없음)"

tools = [
    {
        "name": "run_cli",
        "description": "CLI 명령어를 실행합니다. cli-anything-* 명령어를 실행할 때 사용하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "실행할 CLI 명령어. 예: cli-anything-note-taker --json note list"
                }
            },
            "required": ["command"]
        }
    }
]

# ─────────────────────────────────────────
# 에이전트 루프
# ─────────────────────────────────────────
def run_agent(user_input: str):
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_input}]

    print()
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # 텍스트 출력
        for block in response.content:
            if hasattr(block, "text"):
                print(f"🤖 {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    cmd = block.input["command"]
                    print(f"\n▶ {cmd}")
                    output = run_cli(cmd)
                    print(f"{output}\n")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output
                    })

            messages.append({"role": "user", "content": tool_results})

# ─────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  LLM Native 시연")
    print("  자연어로 요청하세요 (종료: q)")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n💬 ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() == "q":
            break

        run_agent(user_input)
