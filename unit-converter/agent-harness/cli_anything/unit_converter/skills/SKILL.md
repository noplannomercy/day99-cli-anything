---
name: cli-anything-unit-converter
description: Command-line interface for unit conversion — length, weight, temperature. Supports conversion history and JSON output for agent consumption.
---

# cli-anything-unit-converter

단위 변환 CLI — 길이, 무게, 온도 변환을 커맨드라인에서 수행.

## Installation

```bash
pip install cli-anything-unit-converter
```

## Usage

```bash
# JSON 출력 (에이전트용)
cli-anything-unit-converter --json convert length 100 m km

# 일반 출력
cli-anything-unit-converter convert temperature 100 C F
```

## Command Groups

### convert

단위 변환 커맨드.

| Command | Description | Units |
|---------|-------------|-------|
| `length` | 길이 변환 | m, km, ft, mi |
| `weight` | 무게 변환 | kg, lb |
| `temperature` | 온도 변환 | C, F, K |

**Arguments:** `VALUE FROM_UNIT TO_UNIT`

```bash
cli-anything-unit-converter --json convert length 100 m km
# → {"category": "length", "value": 100.0, "from": "m", "to": "km", "result": 0.1}

cli-anything-unit-converter --json convert weight 50 kg lb
# → {"category": "weight", "value": 50.0, "from": "kg", "to": "lb", "result": 110.2311}

cli-anything-unit-converter --json convert temperature 100 C F
# → {"category": "temperature", "value": 100.0, "from": "C", "to": "F", "result": 212.0}
```

### history

변환 히스토리 관리.

| Command | Description |
|---------|-------------|
| `list` | 최근 변환 기록 조회 |
| `clear` | 히스토리 전체 삭제 |

```bash
cli-anything-unit-converter --json history list --limit 5
cli-anything-unit-converter --json history clear
```

## For AI Agents

1. **항상 `--json` 플래그 사용** — 구조화된 출력으로 파싱 용이
2. **리턴코드 확인** — 0: 성공, 1: 오류 (잘못된 단위 등)
3. **절대경로 불필요** — stateless, 파일 경로 없음
4. **히스토리는 홈 디렉토리에 저장** — `~/.cli_anything_unit_converter_history.json`

## Version

1.0.0
