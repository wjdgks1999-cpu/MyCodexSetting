# Codex CLI 문맥 압축 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI에서 압축 실행을 선택하고 실제 검증한 범위를 MyCodexSetting에 제공한다.
**Architecture:** 고정 runtime을 재사용하는 Python 실행 경로, 자식 환경·터미널 상속, CLI 단독 진단. Paseo bridge는 유지한다.
**Tech Stack:** Python 3.11+ 표준 라이브러리/unittest, Node 20+, Bili 0.1.213, 실제 Codex 0.167.0.
**Spec:** [CLI 확장 설계](../specs/2026-11-12-billion-context-cli-design.md).

## Global Constraints

사용자가 CLI 추가와 검증·반영을 요청했다. 앱 제외, 고정 버전 유지, 전역 설정/인증 원문/기존 파일 보존, 기본 dry-run, 무커밋·무push·무게시. 현재 미커밋 0.3.1 소스를 격리 작업 트리에 복사한 뒤 검증된 변경만 되돌린다.

## Review Focus

- CLI-only 사용자의 malformed Paseo config가 진단·실행을 막지 않아야 한다.
- 인자에 공백·Unicode·따옴표·메타문자·빈 값이 있어도 전달이 바뀌거나 shell이 실행되지 않아야 한다.
- 원격 접속·상속된 BILI 환경 때문에 압축 경로를 우회하지 않아야 한다.
- Ctrl+C·실패 종료에서 자신의 자식 수명과 반환 코드를 다루며 다른 chat을 중단하지 않아야 한다.
- 인증 링크 실패·stale runtime·Codex 업데이트에서 성공을 잘못 보고하거나 사용자 데이터를 덮어쓰지 않아야 한다.

## Task 1: CLI 실행·진단과 자동 회귀

**Files:** `kit/mycodex.py`, `kit/mycodex_lib/compression.py`, `tests/test_compression_cli.py`, `tests/test_compression.py`.
**Interfaces:** `run_codex(target, runtime, arguments, *, apply=False)`는 dry-run dict 또는 실제 exit code를 반환한다. `inspect_compression(..., client='paseo')`는 `codex` 선택 시 Paseo를 읽지 않는다.

- [x] 새 검사를 먼저 작성해 CLI 실행 API 부재와 파서 미지원으로 실패하는 것을 확인한다.
- [x] runtime 사전 검사·자식 환경·인자 전달·stdio 상속·종료 처리를 구현한다. 기존 bridge는 변경하지 않는다.
- [x] `python -X utf8 -B -m unittest discover -s tests -v`를 실행한다. Expected: 전체 OK.
- [x] 기존 fake-engine Paseo bridge 통합 검사도 실행한다. Expected: 6 tests OK.

## Task 2: 실제 CLI 검증과 사용 안내

**Files:** `docs/superpowers/validation/2026-11-12-billion-context-cli.md`, 기존 연동 README·관리 스킬·README·CHANGELOG.
**Interfaces:** Task 1의 실행 명령을 실제 runtime과 합성 fixture에 적용한다. 실제 관찰 범위만 문서에 반영한다.

- [x] 새 전용 runtime을 고정 lock으로 준비하고 실제 터미널·모델 응답·Ctrl+C/종료를 관찰한다.
- [x] 실제 압축·검색·복원·resume·개발 흐름·인계 후 일반 Codex 재개를 확인한다. Expected: 합성 표식·최신 PRD·테스트·소유 세션 상태가 서로 맞음.
- [x] 문서·스킬에 CLI 명령과 정확한 검증 범위를 반영한다. 기존 미검증 항목은 보존한다.

## Task 3: 검토·자체 적용·0.4.0 배포

**Files:** model 버전·manifest·관리 자산·새 dist·인덱스·검증 기록.
**Interfaces:** Task 1/2의 확인된 소스와 실행 근거만 반영한다.

- [x] 새 컨텍스트의 읽기 전용 검토자에게 현재 변경과 Review Focus를 검토시킨다. Important 이상은 회귀 검사 후 수정한다.
- [x] 전체 자동 검사·strict validate·diff check를 통과시키고 기존 파일 해시를 확인한다.
- [x] 0.4.0 ZIP을 만들어 단독 설치·링크·내용 일치·기존 버전 보존을 확인한다.
- [x] main의 해당 원본이 작업 시작 시점과 같은지 확인한 후 관리 범위만 반영한다. 결과와 미검증 범위를 기록한다.
