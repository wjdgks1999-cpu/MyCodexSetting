---
schema_version: 1
status: ready
---
# 프로젝트 컨텍스트 안내

## 원본과 현재 작업

| key | path | purpose |
|---|---|---|
| requirements | `README.md` | 프로젝트의 기능과 사용 기준 |
| decisions | `none` |  |
| active-spec | `docs/superpowers/specs/2026-11-20-codex-cli-context-evaluation.md` | JIT·인계·압축의 Codex CLI 실효성 평가 설계 |
| active-plan | `none` |  |
| active-ledger | `none` |  |
| latest-handoff | `.context/handoffs/2026-11-20-170756.md` | 다른 컴퓨터의 실험 환경 준비와 재개 지점 |

## 추가 문서

| path | purpose |
|---|---|
| `PURPOSE.md` | 기능별 도입 목적과 해결하려는 문제 |
| `CHANGELOG.md` | 0.5.1 모델·컨텍스트 설정 변경과 버전별 배포 이력 |
| `AGENTS.md` | MyCodexSetting 자체 개발 지침 |
| `kit/templates/AGENTS.md` | 새 프로젝트에 설치하는 배포용 지침 원본 |
| `kit/templates/config.toml` | 새 프로젝트에 설치하는 Codex 설정 기본값 |
| `docs/superpowers/specs/2026-11-16-astryx-opt-in-design.md` | 승인된 Astryx 선택 기능 도입 구조 |
| `docs/superpowers/plans/2026-11-16-astryx-opt-in.md` | 완료된 선택 기능 도입·검증 계획 |
| `docs/superpowers/validation/2026-11-16-astryx-opt-in.md` | 0.5.0 통합·실행·배포 결과와 제한 |
| `docs/superpowers/specs/2026-11-16-development-agents-design.md` | 개발용 지침과 배포용 템플릿 분리 승인 설계 |
| `docs/superpowers/plans/2026-11-16-development-agents.md` | 개발용 AGENTS 분리·축약 완료 기록과 실제 검증 결과 |
| `docs/superpowers/plans/2026-11-16-hallmark-compatibility-tests.md` | 사용자 결정으로 도입 보류한 Hallmark 시험 계획·1차 원장·미실행 범위 |
| `docs/superpowers/validation/2026-11-16-hallmark-compatibility.md` | Hallmark 실제 호환성 시험·차단 원인·기본 도입 보류 판정 |
| `docs/superpowers/validation/2026-11-16-hallmark-runs.json` | 실제 시험 22개·27턴의 측정·판정·증거 해시 요약 |
| `docs/reviews/2026-11-16-astryx-feasibility.md` | Astryx 공식 소스 사전 검토·도입 후보·후속 실제 시험 원장 연결 |
| `docs/superpowers/validation/2026-11-16-astryx-results.json` | Astryx 실제 모델 29개 사례·33턴과 별도 압축·설치·브라우저 증거 해시 |
| `docs/superpowers/validation/2026-11-16-astryx-opt-in-results.json` | 정식 0.5.0 스킬 새 모델 4건·독립 UI·설치·배포 증거 해시 |
| `kit/integrations/astryx/README.md` | 선택 기능의 설치·명시 호출·사용 중지·호환 범위 |
| `docs/superpowers/plans/2026-11-16-astryx-compatibility-tests.md` | 도입 전 격리 호환성 시험 계획 |
| `docs/superpowers/validation/2026-11-16-astryx-compatibility.md` | 도입 전 실제 시험·조건부 후보 판정·미검증 범위 |
| `docs/usage.md` | 설치·파일 역할·인계·설정·문제 해결 상세 안내 |
| `kit/integrations/billion-context/README.md` | 정식 문맥 압축 기능의 사용법·호환 범위·이전 안내 |
| `docs/superpowers/validation/2026-11-12-billion-context-paseo.md` | 실제 Paseo 연결·압축·복원·workflow·배포 검증과 미검증 항목 |
| `docs/superpowers/validation/2026-11-12-billion-context-cli.md` | 실제 CLI 실행·압축·복원·재개·인계와 배포 검증 |
| `docs/superpowers/specs/2026-11-12-billion-context-cli-design.md` | 기존 CLI 확장의 승인 범위와 실행·검증 계약 |
| `docs/superpowers/plans/2026-11-12-billion-context-cli.md` | CLI 확장 완료 계획과 검증 기록 |
| `docs/superpowers/specs/2026-11-12-billion-context-design.md` | 기존 Paseo 통합 설계와 0.3.1 제공 상태 |
| `docs/superpowers/plans/2026-11-12-billion-context.md` | 기존 Paseo 통합·승격 완료 기록 |
| `docs/superpowers/specs/2026-11-10-human-html-design.md` | human-html 승인 설계 |
| `docs/superpowers/plans/2026-11-10-human-html.md` | human-html 완료 계획과 실제 검증 결과 |
| `docs/superpowers/specs/2026-11-10-project-config-design.md` | config.toml 설치 계약 |
| `docs/superpowers/plans/2026-11-10-project-config.md` | config.toml 설치 완료 계획과 실제 검증 결과 |
| `docs/superpowers/plans/2026-11-10-release-0.2.0.md` | 0.2.0 배포 완료 계획과 실제 검증 결과 |
