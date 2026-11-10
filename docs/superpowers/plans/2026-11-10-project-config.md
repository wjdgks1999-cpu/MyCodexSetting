# Project Config Installation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** config.toml을 설치 템플릿에 포함하고 대상 설정이 없을 때 생성한다.

**Architecture:** 기존 설치 계획에 사용자 소유 `.codex/config.toml` 생성/보존을 추가한다. `.mycodex/templates/config.toml`만 관리 자산으로 검증한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, TOML, unittest.

**Spec:** [프로젝트 설정 설치 설계](../specs/2026-11-10-project-config-design.md)

## Global Constraints

- 현재 설정값을 초기 템플릿으로 사용한다. 대상의 기존 설정과 전역 설정은 보존한다.
- 기본 dry-run과 `--apply` 흐름, 전체 사전 검사, 사용자 설정 변경 허용을 유지한다.
- 0.2.0 개발 원본을 갱신하며 기존 dist와 현재 활성 설정은 변경하지 않는다.

## Review Focus

- 기존 설정이 템플릿과 달라도 재설치와 구조 검증이 정상이어야 한다.
- `.codex/config.toml`이 디렉터리인 경우 다른 설치 파일도 쓰지 않아야 한다.
- 템플릿 누락·변조는 감지하되 사용자 설정 변경은 충돌로 보고하지 않아야 한다.
- 새 세션의 실제 적용과 설치 파일 생성은 구분해서 보고해야 한다.

## Task 1: 설치 계약과 회귀 검사

**Files:** `tests/test_project_config.py`, `kit/templates/config.toml`, `kit/mycodex_lib/model.py`, `kit/mycodex_lib/install.py`.

**Interfaces:** 새 옵션 없이 기존 `init --target ... --requirements ... [--apply]`를 사용한다.

- [x] 실제 CLI의 dry-run·생성·보존·재설치·사전 검사·자산 검증 테스트를 먼저 작성하고 실패를 확인한다.
- [x] 현재 설정을 템플릿으로 추가하고, 관리 자산과 사용자 소유 설정 파일의 설치 경로를 연결한다.
- [x] 전체 `python -X utf8 -B -m unittest discover -s tests -v` 결과를 확인한다.

## Task 2: 자체 적용과 안내

**Files:** 현재 설치본의 `.mycodex/` 관련 자산·manifest, `README.md`, `CHANGELOG.md`, 컨텍스트 인덱스.

**Interfaces:** Task 1의 템플릿과 설치 로직을 자체 적용한다. 활성 `.codex/config.toml`은 보존한다.

- [x] 설치본의 관련 자산·manifest만 동기화하고 현재 설정 보존을 확인한다.
- [x] 기존 설정 범위 안내를 새 설치 계약에 맞춰 고치고 공식 프로젝트 설정 적용 조건을 연결한다.
- [x] strict 구조 검증·원본/설치본 일치·TOML 문법·diff를 확인하고 독립 리뷰를 수행한다.
- [x] 실제 실행과 미실행 범위를 기록하고 현재 작업 포인터를 정리한다. 커밋·배포는 수행하지 않는다.

## 실행 기록

- 요청에 있는 config.toml은 현재 저장소의 값을 초기 템플릿으로 사용하는 것으로 해석했고 구현 전에 알렸다. 기존 파일 보존과 기본 dry-run은 기존 설치 계약을 그대로 적용한다.
- 새 CLI 회귀 검사 6개가 구현 전 모두 실패했음을 확인했다. 구현 후 전체 `python -X utf8 -B -m unittest discover -s tests -v`는 24 tests, 27.465s, OK였다.
- 관리 템플릿과 사용자 소유 설정을 구분했다. 기존 config와 설치 후 바꾼 config가 재설치 및 strict 검증에서 보존되고, 관리 템플릿 변조는 검증 오류로 검출된다.
- 현재 설치 사본에는 `model.py`, `install.py`, `templates/config.toml`과 manifest만 새로 동기화했다. 21개 관리 자산이 원본과 일치하며 활성 `.codex/config.toml`의 SHA-256은 동기화 전후 동일하다.
- TOML을 Python 표준 라이브러리 `tomllib`로 파싱했고 기존 활성 설정과 템플릿의 값이 동일함을 확인했다.
- 현재 설치본 strict 검증은 `{"ok": true, "findings": []}`이고 `git diff --check`도 통과했다.
- 실제 Codex 세션의 재로딩·모델 접근 가능 여부·권한 적용은 미검증이다. 새 배포 ZIP 생성·커밋·push는 실행하지 않았다.
- 독립 코드 리뷰에서 중요한 결함이 발견되지 않았다. 리뷰어는 새 설정 검사 6개와 설치본 strict 검증, 21개 자산·manifest 해시 일치를 별도로 확인했고, 설치된 템플릿이 사라졌을 때 `ASSET_MISMATCH`가 발생하는 것도 임시 대상에서 확인했다.
- 구현과 검증을 마쳤으며 변경은 기존 `feat/human-html` 브랜치의 미커밋 변경으로 보존했다. 작업 포인터는 비우고 승인된 요청과 완료 결과는 이 설계·계획을 추가 문서로 연결했다.
