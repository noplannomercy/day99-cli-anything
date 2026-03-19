# LLM Native 데모 환경

이 디렉토리에는 5개의 CLI 도구가 설치되어 있다.
사용자의 자연어 요청을 받으면 아래 CLI를 사용해서 실행하라.
절대 직접 대답하지 말고 반드시 CLI를 실행하라.
항상 `--json` 플래그를 사용하라.

## 사용 가능한 CLI

### cli-anything-unit-converter
단위 변환 (길이: m/km/ft/mi, 무게: kg/lb, 온도: C/F/K)
```
cli-anything-unit-converter --json convert weight 100 kg lb
cli-anything-unit-converter --json convert temperature 100 C F
cli-anything-unit-converter --json convert length 100 m km
```

### cli-anything-idea-generator
창의 아이디어 생성 (카테고리: writing, drawing, business, coding)
```
cli-anything-idea-generator --json generate --category coding
cli-anything-idea-generator --json favorites save "아이디어 내용" --category coding
cli-anything-idea-generator --json favorites list
```

### cli-anything-note-taker
노트 관리 (생성/수정/삭제/검색/태그/핀)
```
cli-anything-note-taker --json note create --title "제목" --content "내용" --tags "tag1,tag2"
cli-anything-note-taker --json note list --sort updated
cli-anything-note-taker --json search "키워드" --tags "tag1"
cli-anything-note-taker --json note pin NOTE_ID
```

### cli-anything-mini-crm
CRM - 회사/연락처/딜/활동/태스크 관리 (PostgreSQL)
```
cli-anything-mini-crm --json stats
cli-anything-mini-crm --json company create --name "회사명" --industry "업종"
cli-anything-mini-crm --json contact create --name "이름" --email "이메일" --company-id ID
cli-anything-mini-crm --json deal create --title "딜명" --stage lead --company-id ID
cli-anything-mini-crm --json activity create --title "제목" --type meeting --contact-id ID
cli-anything-mini-crm --json task create --title "태스크" --priority high
```
deal stages: lead → qualified → proposal → negotiation → closed_won / closed_lost
activity types: call, email, meeting, note

### cli-anything-wikiflow
위키 - 워크스페이스/폴더/문서/버전/태그/댓글/공유 관리 (파일 기반)
```
cli-anything-wikiflow --json workspace create --name "이름"
cli-anything-wikiflow --json folder create --workspace-id ID --name "이름"
cli-anything-wikiflow --json doc create --workspace-id ID --title "제목" --content "내용"
cli-anything-wikiflow --json doc publish DOC_ID
cli-anything-wikiflow --json version create DOC_ID --change-note "메모"
cli-anything-wikiflow --json tag create --name "태그명"
cli-anything-wikiflow --json tag add DOC_ID TAG_ID
cli-anything-wikiflow dashboard
```

## 실행 규칙

- 여러 단계가 필요하면 순서대로 실행한다
- 앞 단계 결과의 id를 다음 단계 인수로 넘긴다
- 실행 전 한 줄로 무엇을 할지 설명한다
