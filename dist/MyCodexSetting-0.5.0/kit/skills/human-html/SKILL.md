---
name: human-html
description: Use when the user explicitly invokes $human-html with a topic for a human-readable HTML explanation of the current project.
---

# 사람이 읽는 HTML 설명

사용자가 적은 주제를 관련 원본으로 확인해, 브라우저에서 읽기 쉬운 독립 HTML로 설명한다. HTML은 사람이 보는 산출물이며 개발 컨텍스트의 원본이 아니다.

## 입력과 원본

- `$human-html` 뒤에 사용자가 적은 텍스트를 주제로 삼는다. 주제가 없으면 “어떤 내용을 HTML 문서로 정리할까요?”만 질문하고 파일을 만들지 않는다.
- AGENTS → `.context/index.md` → 관련 원본 순서로 필요한 범위만 조사한다. `.human-docs/`의 기존 문서를 조사 자료로 읽지 않는다.
- 실제 구현, 계획, 추론, 미확인을 구분하고 작성 시점과 확인한 원본 경로를 문서에 적는다. 비밀 값은 포함하지 않는다.

## 문서 작성과 저장

1. 주제의 핵심을 먼저 설명하고 이해에 필요한 개념 → 구조·흐름 → 세부 내용 순서로 구성한다. 용어를 풀어 쓰고 적절한 표·도식을 사용한다. 긴 문서에는 내부 목차를 둔다.
2. 언어(`lang`), UTF-8 charset, viewport, 제목, 본문을 갖춘 완전한 HTML을 작성한다. CSS·필요한 SVG 도식을 내부에 포함해 오프라인에서도 읽히게 한다. 외부 폰트·CDN·스크립트·웹사이트 배포는 필요하지 않다. 주제에 맞는 레이아웃, 충분한 대비와 여백, 모바일 줄바꿈, 인쇄 스타일을 적용한다.
3. 아래 저장 도구에 완성한 HTML을 **UTF-8 stdin**으로 전달한다. 현재 프로젝트를 target으로 지정하고 짧은 주제명을 name에 넣는다. 설치된 스킬 디렉터리의 도구 경로를 사용한다.

   ```text
   python .agents/skills/human-html/scripts/save_html.py --target . --name service-structure
   ```

   PowerShell 파이프를 쓰면 해당 실행에서 `$OutputEncoding`을 UTF-8로 설정한다. Python subprocess를 쓰면 `input=html.encode('utf-8')`로 전달한다. 도구는 `.human-docs/` 내부의 `.gitignore`·`.ignore`와 고유한 HTML을 만들고 **저장 경로만** 반환한다. 기존 파일은 덮어쓰지 않는다. `IGNORE_CONFLICT`이면 기존 규칙을 보존하고 충돌을 보고한다.
4. 같은 도구의 `--check .human-docs/<생성된-파일명>.html`로 구조를 확인한다. 브라우저를 사용할 수 있으면 **이번 요청의 파일만** 데스크톱·모바일에서 확인하고 필요한 부분만 수정한다. 검증에는 넘침·가독성 등 작은 결과나 스크린샷을 사용하고 HTML 전문·DOM 전체를 도구 출력으로 돌려받지 않는다. 브라우저가 없으면 시각 검증은 미실행으로 남긴다.

## 보관과 결과 보고

- `.human-docs/`는 일반 개발의 읽기·검색·컨텍스트 수집 대상에서 제외한다. 생성·명시적 수정·검증 요청에서만 해당 파일에 접근한다. ignore를 무시하는 검색에는 `-g '!.human-docs/**'`처럼 명시적으로 제외한다.
- 생성된 HTML은 `.context/index.md`에 연결하지 않는다. 인계의 원본·근거로 쓰거나 본문을 다른 지식 문서에 복사하지 않는다. 일반 문서 생성 시의 인덱스 갱신 규칙에서 제외한다.
- 결과는 클릭할 수 있는 **생성 경로, 짧은 설명, 실행한 검증과 미실행 검증**으로 보고한다. HTML 본문은 채팅에 출력하지 않는다.
- 폴더와 ignore는 일반 탐색을 줄이는 규칙이다. 파일 접근 차단이나 작성 시 토큰 사용량 0을 주장하지 않는다.
