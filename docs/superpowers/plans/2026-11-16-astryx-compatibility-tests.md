# Astryx 설치·호환성 시험 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Steps use checkboxes for tracking.

상태: 설치·실행 시험 및 독립 최종 검토 완료. PASS/FAIL/미실행 구분과 도입 판단은 원장을 따른다. 체크 표시는 검사를 수행하고 결과를 기록했다는 뜻이며 전 항목 PASS라는 뜻이 아니다.

**Goal:** Astryx를 격리 설치하고 현재 MyCodexSetting·Superpowers와의 실제 동작을 비교하여 도입 가능 범위를 판정한다.

**Architecture:** 기준군 S는 현재 kit + Superpowers, 후보군 SA는 여기에 명시 호출 어댑터를 추가한다. 원본 공식 스킬 SR은 별도 진단군이다. 설치·화면·모델 행동·패키징 증거를 구분한다.

**Tech Stack:** Python 3.11+, 호스트 Codex CLI, Node >=22.13.0, npm, Astryx core/cli 0.7.16, React 19, Vite, Next/Tailwind, Chrome.

**Spec:** `docs/reviews/2026-11-16-astryx-feasibility.md`

## Global Constraints

- 사용자 승인: 2026-11-16 설치부터 테스트까지 진행 요청. 제품 기본 편입은 이번 작업에 포함하지 않는다.
- 공식 소스 commit `5051ea96a35307183e9f3fab7fadcc7b0d649e45`; 패키지는 npm integrity와 lockfile로 고정한다.
- 실제 kit·설치 사본·활성 설정·기존 dist·전역 스킬은 변경하지 않는다. 별도 임시 폴더에 설치한다.
- 외부 서비스 생성·게시·배포·전역 npm 설치·이미지 API 호출·인증 파일 열람/복사는 금지한다.
- 정상 설치의 lifecycle도 관찰한다. 전후 전역 설정·스킬 경로 해시와 생성 여부를 비교한다.
- 판정은 PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT_RUN을 구분한다. 실행 로그·파일 해시·버전·브라우저 결과를 보존한다.
- 한 번 통과한 모델 행동은 관찰 범위의 증거다. 호출/승인 핵심 경계는 2회 반복하고, 실패는 새 fixture로 재현한다. 무관한 UI 완성도 점수로 충돌을 판정하지 않는다.
- 앱/Paseo가 실제로 실행되지 않으면 CLI 결과로 대체하지 않는다. 미검증 호스트는 통합 지원 범위에서 제외한다.

## Review Focus

- 원본 스킬을 설치한 경우와 어댑터를 설치한 경우의 결과가 섞이지 않아야 한다.
- 모델의 성공 주장과 실제 파일 변경·명령·브라우저 동작이 일치해야 한다.
- 기존 AGENTS의 사용자 지시, config, 브랜드/문구, 작동하던 검색·폼을 보존해야 한다.
- React 18·비React·작은 CSS 작업에서 불필요한 프레임워크 도입이 없어야 한다.
- 압축 진단/모의 입력/합성 composition 이벤트를 실제 압축/OS IME 입력으로 표현하지 않아야 한다.

## Files and evidence

- `tools/evaluations/astryx/`: 격리 준비·후보 스킬·모델 실행·설치/패키징·브라우저 검증 도구.
- `tests/evaluations/test_astryx_harness.py`: 새 검증 도구에 필요한 증거 보존·판정 회귀 검사.
- `docs/superpowers/validation/2026-11-16-astryx-compatibility.md`: 진행 원장과 최종 판정.
- `docs/superpowers/validation/2026-11-16-astryx-results.json`: 실행 요약과 증거 해시.
- 임시 root의 `evidence/`, `runs/`, `apps/`, `packaging/`: 원본 로그·lockfile·스크린샷. 기존 증거를 덮어쓰지 않는다.

## Task 1: 설치 및 init 동작

- [x] 현재 제품 자동 테스트를 실행하여 기준 상태를 확인한다.
- [x] 격리 root 생성, 보호 대상 해시 저장, 공식 스킬·라이선스 다운로드와 SHA 기록.
- [x] 버전을 고정하여 core/cli 및 시험 도구를 로컬 설치한다. 버전·CLI 검색·component·template·doctor를 실제 실행한다.
- [x] 사용자 AGENTS/config가 있는 fixture에서 init·재실행을 검사한다. 사용자 영역 보존, 관리 블록 개수, 설정 변화, 다른 agent 파일 생성을 기록한다.
- [x] 잘못된 관리 블록·중복 스킬·사용자가 편집한 자산의 보존/중단을 검사한다. 전역 파일 무변경을 확인한다.

## Task 2: 실제 React UI 및 기존 페이지 회귀

- [x] 동일한 한국어 검색/필터/폼 fixture를 기준/후보로 작성한다. 실패하면 라이브러리 결함과 fixture 구현 오류를 분리한다.
- [x] Vite + React 19에서 Astryx component를 실제 렌더하고 production build를 실행한다.
- [x] Next + React 19 + Tailwind 기존 페이지에 component를 추가하고 기존 로고·색상·문구·검색·필터·폼·CSS layer를 비교한다.
- [x] Chrome 360/768/1280/1920에서 가로 넘침·레이블·키보드·포커스·검색·폼·한국어 긴 문구를 검사한다. JS/hydration 오류와 외부 요청도 기록한다.
- [x] composition/Enter 자동 검사를 수행하고 OS IME 수동 입력과 구분한다. 지원 범위를 넘는 검사는 NOT_RUN으로 둔다.

## Task 3: 실제 Codex + Superpowers 행동 비교

- [x] 동일 CLI/model/effort의 S/SA/SR 실제 스킬 목록과 도구 통제를 확인한다.
- [x] A01: PRD만 있는 새 프로젝트에서 설계 승인 전 제품 생성/설치/init이 없는지 S/SA 비교, 핵심 경계 2회. SR도 진단한다.
- [x] A02: 승인된 React19 계획을 명시 호출로 구현하여 실제 Astryx 스킬/CLI 사용·계획 재시작 여부·빌드·화면을 확인한다.
- [x] A04: 4px CSS 수정·Python 오류·React18·비React 요청에서 스택/전역/불필요한 파일 변경이 없는지 S/SA 비교. CSS 호출 경계 2회.
- [x] A05: project-init, 독립 오프라인 human-html, session-handoff 후 새 세션 재개, context-compression 진단 경계를 S/SA 비교한다.
- [x] 압축 실제 경유를 격리 runtime으로 실행할 수 있으면 수행한다. 실제 압축 발생이 없으면 조합 호환 PASS로 올리지 않는다.

## Task 4: 임시 배포 및 판정

- [x] kit 사본에 어댑터/metadata/라이선스/자산 목록을 추가하고 임시 ZIP을 생성한다. 실제 dist는 보존한다.
- [x] ZIP 신규 설치·dry-run·재설치·사용자 AGENTS/config·편집 자산 충돌을 검사하고 manifest 전체 해시를 확인한다.
- [x] ZIP 소비자에서 실제 명시 호출을 수행한다. 후보 kit에 기존 제품 테스트를 실행한다.
- [x] 새로운 테스트 도구의 증거 보존 검사를 실행하고 전체 결과를 원장·기계 판독 요약에 기록한다.
- [x] fresh reviewer가 판정과 증거의 일치를 검토한다. 중요 지적은 재현 후 수정/재검증한다. Critical/Important 0, Minor 1은 원장에 보류 기록.
- [x] 실제 제품/전역 상태 무변경, strict validate, git diff --check를 확인한다.

## Gate

핵심 호출/승인 경계·기존 파일/행동 보존·React19 빌드/브라우저·설치/재설치/ZIP에 미해결 FAIL이 없을 때 해당 범위의 후보로 판단한다. 필수 항목 BLOCKED/INCONCLUSIVE/NOT_RUN은 PASS에 합산하지 않는다. 모든 호스트와 압축 조합을 검증하지 못했다면 전체 기본 기능 도입을 승인한 것으로 보고하지 않는다.
