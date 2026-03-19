# LLM Native 시연 시나리오

> 자연어 질의 → CLI 자동 호출
> 쉬운 것부터 복잡한 것까지.

---

## 준비된 CLI 목록

| CLI | 설명 |
|-----|------|
| `cli-anything-unit-converter` | 단위 변환 (길이, 무게, 온도) |
| `cli-anything-idea-generator` | 창의 아이디어 생성 (writing/drawing/business/coding) |
| `cli-anything-note-taker` | 노트 관리 (생성/검색/태그/핀) |
| `cli-anything-mini-crm` | CRM (연락처/회사/딜/활동/태스크) |
| `cli-anything-wikiflow` | 위키 (워크스페이스/폴더/문서/버전/태그) |

---

## Level 1 — 단순 질의 (CLI 1개, 명령 1개)

### "100kg이 몇 파운드야?"
```
→ cli-anything-unit-converter convert weight 100 kg lb
```

### "코딩 아이디어 하나 줘봐"
```
→ cli-anything-idea-generator generate --category coding
```

### "내 노트 목록 보여줘"
```
→ cli-anything-note-taker note list --sort updated
```

### "CRM 현황 요약해줘"
```
→ cli-anything-mini-crm stats
```

### "위키 워크스페이스 목록 보여줘"
```
→ cli-anything-wikiflow workspace list
```

---

## Level 2 — 기본 작업 (CLI 1개, 명령 2~3개)

### "오늘 팀 미팅 내용 노트로 저장해줘. 태그는 work랑 meeting으로."
```
→ cli-anything-note-taker note create
     --title "팀 미팅 - [날짜]"
     --content "신규 기능 방향 논의"
     --tags "work,meeting"
→ cli-anything-note-taker note pin [ID]
```

### "CRM에 테크스타트라는 IT 회사 추가하고, 담당자 홍길동(hong@techstart.io) 등록해줘"
```
→ cli-anything-mini-crm company create --name "테크스타트" --industry "IT"
→ cli-anything-mini-crm contact create
     --name "홍길동"
     --email "hong@techstart.io"
     --company-id [ID]
```

### "비즈니스 아이디어 3개 생성해서 좋은 거 즐겨찾기에 저장해줘"
```
→ cli-anything-idea-generator generate --category business  (x3)
→ cli-anything-idea-generator favorites save "[선택한 아이디어]" --category business
```

### "Engineering Wiki 워크스페이스 만들고 Architecture 폴더 생성해줘"
```
→ cli-anything-wikiflow workspace create --name "Engineering Wiki"
→ cli-anything-wikiflow folder create --workspace-id [ID] --name "Architecture"
```

---

## Level 3 — 체이닝 (CLI 2개 연동)

### "코딩 아이디어 생성해서, 노트에도 저장하고 즐겨찾기에도 등록해줘"
```
→ cli-anything-idea-generator generate --category coding
→ cli-anything-idea-generator favorites save "[아이디어]"
→ cli-anything-note-taker note create --title "코딩 아이디어" --content "[아이디어]" --tags "idea,coding"
```

### "CRM에서 홍길동한테 오늘 미팅 기록하고, 위키에 회의록 만들어줘"
```
→ cli-anything-mini-crm contact list (홍길동 ID 확인)
→ cli-anything-mini-crm activity create
     --title "킥오프 미팅"
     --type meeting
     --contact-id [ID]
→ cli-anything-wikiflow doc create
     --workspace-id [ID]
     --title "홍길동 킥오프 미팅"
     --content "..."
     --status published
```

### "work 태그 달린 노트 찾아서 CRM 태스크로 등록해줘"
```
→ cli-anything-note-taker search "" --tags "work"
→ cli-anything-mini-crm task create --title "[노트 제목]" --priority high
```

---

## Level 4 — 복합 시나리오 (CLI 3개 이상, 전체 흐름)

### "신규 고객사 바포럼 온보딩해줘"
> 회사 등록 → 담당자 추가 → 딜 생성 → 위키 페이지 → 노트 요약

```
→ cli-anything-mini-crm company create --name "바포럼" --industry "교육"
→ cli-anything-mini-crm contact create --name "김대표" --company-id [ID]
→ cli-anything-mini-crm deal create
     --title "바포럼 계약"
     --stage lead
     --company-id [ID]
→ cli-anything-wikiflow workspace create --name "바포럼"
→ cli-anything-wikiflow doc create --title "고객 온보딩 현황" --status draft
→ cli-anything-note-taker note create
     --title "바포럼 온보딩 요약"
     --content "회사/담당자/딜/위키 모두 세팅 완료"
     --tags "onboarding,crm"
```

### "오늘 바이브코딩 강의 준비해줘"
> 아이디어 생성 → 노트 저장 → 위키 문서 작성 → 태스크 등록

```
→ cli-anything-idea-generator generate --category coding  (강의 소재 탐색)
→ cli-anything-note-taker note create
     --title "바이브코딩 강의 준비"
     --content "[아이디어들]"
     --tags "lecture,prep"
→ cli-anything-wikiflow doc create
     --title "바이브코딩 강의안"
     --content "..."
     --status draft
→ cli-anything-wikiflow version create [DOC_ID] --change-note "초안"
→ cli-anything-mini-crm task create
     --title "강의 자료 최종 검토"
     --priority high
     --due-date [내일]
```

### "지난 미팅 기록 전부 위키로 옮겨줘"
> CRM 활동 조회 → 각 활동을 위키 문서로 변환 → 태그 정리

```
→ cli-anything-mini-crm activity list --type meeting
→ cli-anything-wikiflow folder create --name "미팅 기록"
→ (각 활동마다)
   cli-anything-wikiflow doc create --title "[미팅명]" --content "[내용]"
→ cli-anything-wikiflow tag create --name "meeting"
→ (각 문서마다)
   cli-anything-wikiflow tag add [DOC_ID] [TAG_ID]
```

---

## 핵심 메시지

```
자연어 한 마디
  → 어떤 CLI를 호출할지 판단
  → 앞 단계 결과의 ID를 다음 단계로 전달
  → 여러 시스템을 넘나들며 실행

이게 LLM Native다.
사람용 UI(웹앱)는 바이브코딩으로,
에이전트용 인프라(CLI)는 5분 변환으로.
```

---

> 각 CLI는 `--json` 플래그로 구조화 출력.
> LLM이 앞 단계 응답의 `id`를 다음 단계 인수로 자동으로 넘긴다.
