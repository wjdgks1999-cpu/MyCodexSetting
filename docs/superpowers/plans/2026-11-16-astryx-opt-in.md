# Astryx 선택 기능 도입 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 검증한 Astryx 연결 기능과 사용 안내를 MyCodexSetting 0.5.0에 선택 기능으로 제공한다.

**Architecture:** 기본 설치는 스킬·안내·라이선스만 배포한다. React 프로젝트의 npm 의존성은 사용자가 선택하여 설치한다. 기존 설치/충돌 검사기를 그대로 사용한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, pinned Astryx 0.7.16, 실제 Codex CLI/Chrome 시험.

**Spec:** `docs/superpowers/specs/2026-11-16-astryx-opt-in-design.md`

상태: 0.5.0 통합·실제 실행·독립 검토·자체 설치·배포 검증 완료. 실행 결과와 미검증 범위는 원장을 따른다.

## Global Constraints

- 기존 미커밋 문서와 Hallmark/Astryx 시험 증거를 보존한다. 제품 변경은 현재 파일의 격리 staging 사본에서 검증 후 지정 경로만 반영한다.
- 정식 연결 스킬은 명시 호출, 로컬 고정 의존성, 기존 설계/스택 보존을 유지한다. 전역 설치나 기존 AGENTS 자동 init은 하지 않는다.
- 과거 29개 사례의 성공을 최종 변경본의 새 실행 결과로 대체하지 않는다. 변경된 배포/문서 경계와 핵심 모델 사례를 새로 실행한다.
- 새 버전만 생성하며 기존 dist를 덮어쓰지 않는다. 커밋·push·외부 게시는 이번 범위가 아니다.

## Task 1: 관리 자산·사용 안내

**Files:** `kit/skills/astryx/SKILL.md`, `agents/openai.yaml`, `kit/integrations/astryx/{README.md,LICENSE,THIRD_PARTY_NOTICES.md}`, `kit/mycodex_lib/model.py`, `README.md`, `docs/usage.md`, `CHANGELOG.md`, `tests/test_astryx.py`, `tests/test_release.py`.

**Interfaces:** 현재 installer의 REQUIRED_ASSETS와 SKILL_NAMES를 사용한다. v0.5.0 소비자와 manifest를 Task 2가 검증한다.

- [x] 현재 staging 제품 테스트로 기준 상태 확인.
- [x] 설치 시 Astryx 안내/명시 호출 metadata 포함, npm 파일 무생성, 기존 npm/AGENTS/config 보존, 편집/동명 충돌 전부 보존, ZIP 링크/라이선스 포함을 검사하는 테스트를 먼저 작성해 실패를 확인.
- [x] 기존 후보에서 시험 표식을 제거하고 설치 안내 연결·reset 주의를 추가. 자산 목록과 0.5.0 버전을 반영.
- [x] 사용자 문서에 선택 여부, 조건 확인→프로젝트 로컬 설치→명시 호출→빌드/브라우저 검증, 중지/제거, 기존 버전 충돌 경로를 작성.
- [x] `python -X utf8 -B -m unittest discover -s tests -v`: 전체 PASS.

## Task 2: 최종 자산 실제 실행·배포

**Files:** `tools/evaluations/astryx/`의 기존 runner 재사용, 이번 작업의 격리 증거, `docs/superpowers/validation/2026-11-16-astryx-opt-in.md`, `.context/index.md`.

**Interfaces:** Task 1의 실제 kit를 설치하고 문서 명령/최종 SKILL을 사용한다. 과거 fixture를 원문 변경 없이 복제하되 새 실행 경로로 분리한다.

- [x] 사용자 문서의 npm 명령을 격리 React19 앱에서 실제 실행하고 고정 버전/API 조회/빌드 확인.
- [x] 최종 스킬의 명시 호출 A02와 승인 전 A01·작은 CSS A04를 실제 Codex에서 실행, 스킬 읽기·명령·변경 파일을 검증. A02를 독립 Chrome에서 검증.
- [x] 최종 kit의 임시 ZIP 신규·재설치·사용자 파일 보존과 모든 문서 링크 확인. 이전 버전 충돌 시 전부 보존 확인.
- [x] fresh reviewer로 원본/사본/문서/실행 증거와 판정 대조. 중요 문제만 수정·재검증.
- [x] 검증된 원본을 현재 저장소에 반영. 기존 자체 설치 자산 일치 확인 후 관리 사본·manifest 동기화, strict validate.
- [x] `python -X utf8 -B tools/build_release.py`로 새 0.5.0만 생성. 재실행 동일성·과거 dist 보존·ZIP CRC·링크 확인.
- [x] 제품/평가 테스트, strict validate, diff check 결과와 미검증 범위를 원장에 기록.

## Review Focus

- 스킬 제공과 npm 의존성 설치/활성화가 문서에서 구분되는가.
- 설치 없이도 기본 Python 기능이 유지되고 기존 package/AGENTS/config가 보존되는가.
- 배포 폴더와 설치된 `.mycodex` 양쪽에서 안내와 라이선스가 접근 가능한가.
- 기존 버전 사용자가 자동 업그레이드나 전역 설치를 지시받지 않는가.
- 실제 새 실행과 과거 시험, 앱/Paseo/OS IME 미검증이 구분되는가.
