# 개발용 AGENTS 분리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 루트 개발 지침과 새 프로젝트에 설치할 배포 지침의 역할을 분리한다.

**Architecture:** 기존 배포 원본 경로를 유지하고 루트 AGENTS만 개발용으로 작성한다. 인덱스에서 역할과 승인·검증 기록을 찾을 수 있게 한다.

**Tech Stack:** Markdown, 기존 Python 표준 라이브러리 기반 검증·배포 도구, Git.

**Spec:** [승인된 분리 설계](../specs/2026-11-16-development-agents-design.md).

## Global Constraints

- 설치·검증 코드, 배포 템플릿, manifest, 활성 설정, 기존 배포본은 변경하지 않는다.
- 새 버전·ZIP 생성, 커밋·push·외부 게시는 이번 작업에 포함하지 않는다.
- `.human-docs/`의 실제 산출물은 읽거나 인덱스에 등록하지 않는다.
- 진행 원장은 이 계획의 체크리스트와 검증 기록으로 관리한다.

## Review Focus

- 개발용 지침이 새 프로젝트의 AGENTS 또는 배포 파일에 들어가지 않아야 한다.
- 자체 설치 템플릿을 개발용 지침으로 바꾸거나 manifest 해시를 불필요하게 변경하지 않아야 한다.
- 설정 원본과 활성 설정, 원본 코드와 자체 설치 사본의 역할이 명확해야 한다.
- 인덱스 작업 전환에서 이전 설계·계획·검증 기록을 잃지 않아야 한다.
- 문서에 적힌 명령과 검증 주장이 실제 코드·이번 실행 결과와 맞아야 한다.

## Task 1: 개발 지침과 탐색 경로 분리

**Files:** 수정 `AGENTS.md`, `.context/index.md`; 생성 이번 설계와 계획 문서.

**Interfaces:** 기존 `release_files()`가 만드는 33개 배포 파일과 `validate --strict` 계약은 유지한다.

- [x] 기존 지침·설치·검증·배포 경로를 확인하고 보호 파일 171개와 배포 내용의 기준 해시를 확보한다.
- [x] 승인 범위의 개발용 AGENTS를 작성하고 인덱스에 두 지침의 역할을 연결한다.
- [x] `python -X utf8 -B .mycodex/mycodex.py validate --target . --strict --json`을 실행한다. Expected: 오류·경고 없음.
- [x] 보호 파일·배포 내용의 전후 해시, 변경 문서의 상대 링크, Git diff를 검사한다. Expected: 보호 파일과 배포 내용 불변, 끊긴 링크 없음, 승인된 문서만 변경.
- [x] `python -X utf8 -B -m unittest discover -s tests -p test_release.py -v`를 실행한다. Expected: 배포 회귀 6개 통과.
- [x] 별도 읽기 전용 검토 후 결과를 기록하고 인덱스의 활성 작업을 완료 상태로 정리한다.

## 실행 판단과 검증 기록

- Ruling: 사용자가 승인한 현재 디렉터리의 문서 변경을 이 세션에서 직접 수행한다. 별도 worktree나 커밋을 만들지 않으며 변경은 작업 트리에서 검토할 수 있게 남긴다.
- Ruling: 실행 코드 변경이 없어 새 테스트는 추가하지 않는다. 기존 구조·배포 회귀 검사와 전후 해시 비교로 분리 경계를 검증한다.
- 시작 상태: `master`, `8dee1b1`, 작업 트리 깨끗함. 이전 활성 CLI 계획은 모두 완료 체크되어 있지만 `.superpowers/sdd/2026-11-12-billion-context-cli/progress.md`는 없다. 해당 과거 원장을 복구하거나 완료를 추정하지 않고 기존 설계·계획·검증 문서를 보존한다.
- 기준 해시: 보호 파일 171개 `f6c969d2bd32c24ac3dfbb7f6eb1e8785a1f6cdbcccab753bd9edf2cbc0aab44`; 배포 파일 33개 `5edcba25dc76f989928e52efe97df188980d973289e7eced485e08fdba9cf625`.
- 변경 후 strict 검증: `{"ok": true, "findings": []}`. `git diff --check` 통과.
- 보호 파일 171개와 배포 파일 33개의 전후 해시가 기준과 동일하다. 배포용 AGENTS와 자체 설치 템플릿도 동일하며, 루트 개발용 AGENTS는 배포 파일 목록에 없다.
- 변경 문서 4개의 상대 링크 검사: 오류 없음. 루트 AGENTS는 41줄이며 기존 공통 지침을 유지했다.
- 배포 회귀: `python -X utf8 -B -m unittest discover -s tests -p test_release.py -v` → 6 tests OK, 6.441s. 임시 폴더에서 검증했으며 기존 `dist/`는 변경하지 않았다.
- 전체 64개 테스트와 실제 CLI·Paseo 모델 실행은 이번 문서 변경 후 재실행하지 않았다.
- 최종 읽기 전용 검토: 별도 검토자가 실제 diff·신규 문서·관련 설치 및 배포 코드를 확인했다. Critical/Important/Minor 모두 없음. 테스트와 해시 비교는 이 세션의 실행 결과를 검토 근거로 사용했다.
- Final: Ruling: 검토자가 실제 CLI·Paseo 동작은 판단하지 않았다. 실행 코드와 배포 내용이 그대로인 문서 변경이므로 이번 작업에서 실제 모델 실행을 추가하지 않는다. 현재 호스트의 압축 호환성을 입증하지 않는 한계는 유지한다.
- 완료 상태: 활성 spec·plan·ledger는 `none`으로 정리하고 이번 설계·계획과 이전 CLI 원본은 추가 문서로 보존했다. 완료 후 인덱스 구조는 검토자 대신 실행 담당자가 최종 검사한다.

## 후속 축약 — 2026-11-16

사용자가 공식 지침과 비교한 검토 결과를 확인하고 중복 세 곳의 축약을 요청했다. 개발·배포 구분의 반복과 검증 기록 규칙을 합치고, 관리 스킬 이름 나열을 원본 경로 안내로 바꿨다. 핵심 제약과 검증 명령 4개는 유지했다.

- 분량: 41줄·18개 항목·3,693바이트에서 39줄·16개 항목·3,267바이트로 축약했다.
- 이번 축약 후 실행: strict 구조 검증 `{"ok": true, "findings": []}`, `git diff --check` 통과. 배포용·자체 설치 AGENTS 템플릿의 SHA-256은 변경 전과 동일하다.
- 단순 문장 정리이므로 자동 테스트와 실제 CLI·Paseo 실행은 다시 수행하지 않았다. 위의 배포 회귀 6개 통과 기록은 최초 분리 작업의 결과다.
