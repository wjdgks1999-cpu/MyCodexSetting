---
name: astryx
description: Use when the user explicitly invokes $astryx for Astryx React UI implementation or compatibility checks.
---

# Astryx React UI 지원 — 시험용 후보

명시 호출된 작업 범위에만 적용한다. 일반 UI·CSS·Python 작업, project-init, human-html, session-handoff, context-compression은 이 스킬의 호출 사유가 아니다.

1. `.context/index.md`에서 요구사항과 승인된 설계·계획을 읽는다. 설계 승인이 없으면 Superpowers의 설계 절차를 먼저 따른다. 이미 승인된 설계·계획은 재시작하지 않고 이어서 수행한다.
2. 실제 package.json·lockfile·Node·React 버전을 확인한다. Astryx 0.7.16은 Node >=22.13.0, React/react-dom >=19, StyleX runtime ^0.19.0을 요구한다. React 18·비React 프로젝트에서는 호환성 차이를 설명하고 현재 스택을 보존한다. 프레임워크 전환이나 React 업그레이드는 별도 선택이 필요하다.
3. 프로젝트 로컬 `node_modules/.bin/astryx`(Windows는 `astryx.cmd`)를 사용한다. CLI/core 버전을 맞춘다. 의존성 설치가 승인된 경우에만 해당 프로젝트에 고정 버전으로 설치하고 lockfile을 남긴다. 전역 npm 설치·사용자 홈 스킬·전역 설정은 변경하지 않는다.
4. `astryx search "필요한 기능"`, `astryx component <Name>`, `astryx docs <topic>`으로 현재 버전의 실제 API를 조회한다. 입력 컴포넌트는 `TextInput`이며 `Input`으로 추정하지 않는다. 명령 성공과 결과를 읽고 구현한다.
5. 승인된 신규 페이지는 `astryx build "idea"`의 템플릿 추천을 검토하고 필요한 로컬 경로에만 scaffold한다. 기존 페이지는 프레임·DOM·문구·로고·브랜드·기능을 보존하고 필요한 컴포넌트만 수정한다. raw HTML/CSS나 색상 값을 무조건 치환하지 않는다.
6. 일반 구현에 init이나 AGENTS 변경을 강제하지 않는다. 지침 생성이 요청된 경우에만 프로젝트 안의 별도 참조 문서로 `astryx init --features agents --agent-docs-path docs/astryx-reference.md`를 사용한다. 출력 지침은 현재 사용자 요청·Superpowers 승인·기존 계획을 대체하지 않는다. 생성 문서를 인덱스에 필요한 범위로 등록한다.
7. CSS는 공식 설치 문서에 따라 연결한다. 기존 Tailwind import를 보존하고 필요한 layer 선언을 import보다 앞에 둔다. Theme가 필요한 토큰과 직접 CSS 사용을 구분하며, 승인된 브랜드를 바꾸지 않는다.
8. 실제 프로젝트 빌드, 검색/필터/폼, 한국어 composition/Enter, 키보드·포커스, 반응형 화면을 검증한다. 브라우저 미실행·OS IME 미확인은 별도 기록한다. mock·빌드 성공을 실제 상호작용이나 압축 호환의 증거로 쓰지 않는다.

`human-html`은 독립 오프라인 HTML 계약을 유지한다. 인계는 기존 session-handoff를 사용하며, 압축은 원본·승인·작업 범위를 바꾸지 않는다. 이 파일은 시험용이며 기본 배포 편입을 뜻하지 않는다.
