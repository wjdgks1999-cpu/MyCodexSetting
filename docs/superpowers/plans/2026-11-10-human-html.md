# Human HTML Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 사용자가 적은 주제를 독립 HTML로 설명하고 일반 개발의 탐색·원본 참조에서 제외하는 명시적 스킬을 제공한다.

**Architecture:** `human-html` 스킬이 필요한 원본만 조사하고 HTML을 작성한다. 스킬에 포함된 작은 저장 도구가 `.human-docs/`에 새 파일과 검색 제외 규칙을 준비하며, 기존 설치 도구가 스킬·도구·정책을 배포한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, Markdown/YAML, 독립 HTML/CSS, unittest.

**Spec:** [승인 설계](../specs/2026-11-10-human-html-design.md)

## Global Constraints

- 스킬 이름 `human-html`; 명시적 호출과 사용자가 적은 주제가 필요하다.
- 산출물은 `.human-docs/`에 저장하고 일반 개발 탐색·인덱스·인계 원본에서 제외한다.
- 기존 파일·루트 `.gitignore`·전역 설정·기존 배포물은 보존한다.
- 생성·수정·검증 시에만 해당 산출물에 접근하며 본문을 도구 결과에 출력하지 않는다.
- 파일 접근 차단이나 토큰 사용량 0을 보장하지 않는다.

## Review Focus

- Git 없는 PRD-only 프로젝트에서도 검색 제외가 작동해야 한다.
- 기존 제외 파일이 맞춤형이면 삭제·덮어쓰기 대신 보존하거나 충돌을 보고해야 한다.
- 대소문자·인코딩된 경로로 HTML을 인덱스/인계에 등록해도 본문을 읽지 않아야 한다.
- 일반 검색이 ignore를 무시할 때에는 지침에 따른 명시적 제외가 필요하다.
- 새 스킬·저장 도구 누락과 암묵 호출 정책 변경을 설치 검증이 감지해야 한다.

## Task 1: 안전한 저장과 설치·검증 연결

**Files:** Create `tests/test_human_html.py`, `kit/skills/human-html/scripts/save_html.py`; modify `kit/mycodex_lib/model.py`, `kit/mycodex_lib/validation.py`.

**Interfaces:** `python save_html.py --target <root> --name <topic>` consumes UTF-8 HTML on stdin; returns only a relative `.human-docs/<time>-<topic>-<id>.html` path. `--check <relative-path>` validates an existing generated file without returning its body. Exit codes: 0 success, 1 invalid input/conflict, 2 I/O failure. `SKILL_NAMES` is the single installed-skill inventory.

- [x] Write and run failing tests for installed helper availability, save/check, file preservation, invalid input/paths, reparse targets, root ignore preservation and actual rg exclusion with/without Git.
- [x] Implement the helper using standard library and exclusive file creation; generate folder-local `.ignore` and `.gitignore` without changing existing rules.
- [x] Extend required assets and explicit-only policy validation; reject `.human-docs/` source references without reading generated content. Test encoded/case variants and handoff links.
- [x] Run `python -B -m unittest discover -s tests -v`; inspect results.

## Task 2: 스킬과 탐색 정책

**Files:** Create `kit/skills/human-html/SKILL.md`, `kit/skills/human-html/agents/openai.yaml`; modify `kit/templates/AGENTS.md`, `kit/context-policy.md`, `kit/skills/project-init/SKILL.md`, `kit/skills/session-handoff/SKILL.md`.

**Interfaces:** Uses Task 1 helper and `.human-docs/` contract; preserves existing context discovery.

- [x] Run an isolated no-skill behavior scenario before authoring; record observed gaps.
- [x] Write a concise explicit-only skill with user-topic handling, evidence-based explanation, readable offline HTML, save/check instructions and scoped visual QA.
- [x] Add normal-development exclusion and generated-document index exception to templates, policy, initialization and handoff instructions.
- [x] Run an independent skill scenario with a topic and a no-topic scenario; inspect output behavior and generated report.
- [x] Run the skill quick validator and the full unittest suite.

## Task 3: 자체 적용·설명서·최종 확인

**Files:** Update installed `.mycodex/` and `.agents/skills/{project-init,session-handoff,human-html}`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, context index and this plan's ledger.

**Interfaces:** Source version becomes `0.2.0` (development source); existing `dist/0.1.x` artifacts remain unchanged and are described as not containing the new skill.

- [x] Synchronize only the reviewed kit assets and refresh this repository's manifest; preserve project index and other existing instructions/settings.
- [x] Document invocation, output location, search exclusion and release boundary in the existing manual/changelog.
- [x] Verify strict structure, full tests, source/installed equality, actual search exclusion and desktop/mobile browser rendering of a generated example.
- [x] Perform a fresh independent review of the uncommitted changes; address material findings with tests.
- [x] Record executed checks and unverified limits, update plan/ledger/index. Leave changes reviewable without committing or publishing.

## 완료 기록 — 2026-11-10

- 구현 및 현재 저장소 자체 적용 완료. 브랜치 `feat/human-html`, 기준 커밋 `786d540`; 변경은 미커밋 상태로 보존했다.
- 최종 전체 검사: `python -X utf8 -B -m unittest discover -s tests -v` — 18 tests, 24.563s, OK. 실제 Windows junction, 한글 경로/본문, 기존 파일 보존, Git 유무별 rg 제외를 포함한다.
- 현재 설치본 검사: `python -B .mycodex/mycodex.py validate --target . --strict --json` — `{"ok": true, "findings": []}`.
- 세 스킬의 시스템 `quick_validate.py` 검사 통과. 검증 도구에 필요한 PyYAML은 시험 작업공간에만 설치했으며 제품의 실행 의존성은 표준 라이브러리로 유지했다. 검증기는 UTF-8 모드로 실행했다.
- 배포 원본과 자체 설치 자산 20개가 줄바꿈 정규화 후 모두 일치한다. 기존 `dist/`와 `.codex/config.toml`은 변경하지 않았다. `git diff --check` 통과.
- 실제 독립 에이전트 시험: 스킬 없는 경우 산출물이 index에 연결되고 검색 제외 파일이 없었다. 새 스킬을 설치 경로에서 직접 읽어 수행한 시험에서는 지정 주제의 HTML과 제외 파일·화면 검사 이미지가 모두 `.human-docs/` 안에 생성됐고 index는 보존됐다.
- 주제 없는 독립 시험은 질문만 반환했으며 HTML 보관 폴더를 만들지 않았다.
- 생성 예시는 브라우저 1365px/390px에서 시각 확인했고 가로 넘침이 없었다. 별도 rg 탐색에서도 HTML이 제외됐으며 시험 프로젝트의 strict 검증이 통과했다.
- 독립 코드 리뷰에서 발견한 잘못된 HTML 선언의 원문 출력 문제를 재현하는 테스트를 RED로 확인하고 고정 진단으로 수정했다. 저장·점검 모드 회귀 검사와 Windows drive/stream 형식 점검 경로 거부를 최종 검사에 포함했다.
- Ruling: 일반 탐색 제외가 계약이다. 별칭·동시 경쟁을 통한 강제 접근 방지나 기존 CLI에 의도적으로 직접 지정한 입력의 접근 차단은 추가하지 않는다. 브라우저 시각 품질은 생성 단계의 검사로 확인하며 구조 검사기만으로 사실성·전체 HTML 문법 적합성을 보장하지 않는다.
- 미실행: 실제 Codex UI의 스킬 목록 재탐색, 실제 서비스 실행/HTTP/배포, 실제 인쇄 출력, 새 배포 ZIP 생성. 앱 실행·배포는 이 스킬 구현의 대상이 아니다.
- 원본 구현은 완료했으며 기존 0.1.2 배포 ZIP에는 새 기능이 없다. 사용자에게 현재 `kit/` 설치 경로를 안내한다.
- 이번 계획의 임시 fixture·검사 로그·검증 의존성은 정리하며 위 결과를 이 계획에 보존한다. 명시적 session-handoff 호출은 없었으므로 인계 스냅샷을 생성하지 않는다.

## 후속 문서 축약 — 2026-11-10

- 사용자 승인에 따라 context-policy의 별도 HTML 절을 삭제하고 인덱스 갱신에 산출물 등록 제외 예외 한 문장만 남겼다. JIT Retrieval의 일반 탐색 제외와 AGENTS·스킬의 상세 규칙은 유지했다.
- 배포 원본과 현재 설치본을 함께 수정하고 해당 manifest 해시를 갱신했다. 두 사본 일치, strict 구조 검증과 `git diff --check`를 확인했다.
- 실행 동작을 바꾸지 않는 문서 축약이므로 전체 테스트는 재실행하지 않았다. 앞의 18개 테스트 결과는 구현 완료 시점의 기록이다.
- config.toml 관련 질문은 현재 설치 자산 목록과 설치 계획 코드를 확인해 답했다. 대상 프로젝트의 `.codex/config.toml`은 생성·복제하지 않으며, 이 저장소에 존재하는 개발용 설정과 구분한다.
