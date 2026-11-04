---
schema_version: 1
status: ready
---
# 프로젝트 컨텍스트 안내

## 원본과 현재 작업

| key | path | purpose |
|---|---|---|
| requirements | `docs/requirements.md` | 요구사항 원본 |
| decisions | `none` |  |
| active-spec | `docs/superpowers/specs/2026-11-04-mycodexsetting-design.md` | 승인된 설계 |
| active-plan | `docs/superpowers/plans/2026-11-04-mycodexsetting.md` | Native 구현 계획 |
| active-ledger | `.superpowers/sdd/2026-11-04-mycodexsetting/progress.md` | Git 미사용 환경의 실행 근거 |
| latest-handoff | `none` |  |

## 추가 문서

| path | purpose |
|---|---|
| `docs/validation/2026-11-04-acceptance.md` | 실제 검증 결과와 미검증 범위 |

## 초기화 확인 사항

- 2026-11-04 조사 완료. 요구사항은 docs/requirements.md이며 상세 내용은 복제하지 않는다.
- Superpowers는 현재 환경에 등록된 using-superpowers, executing-plans, test-driven-development, verification-before-completion 등을 실제 읽고 사용했다. 로컬 원본은 `.agents/skills/superpowers/`에 있다.
- 프로젝트의 Python 표준 라이브러리 구조와 테스트 실행 명령을 코드 및 실제 실행 결과로 확인하고 AGENTS에 반영했다.
- 설치 직후 구조 검증의 유일한 오류가 INIT_REVIEW_REQUIRED임을 확인한 후 ready로 전환했다. 이후 검증 결과는 연결된 검증 기록을 따른다.
- Git은 사용하지 않으며 실제 Codex 별도 프로세스의 정책 제한과 플랫폼별 미검증 범위는 검증 기록에서 확인한다.
