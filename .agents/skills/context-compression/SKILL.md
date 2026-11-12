---
name: context-compression
description: Use when the user explicitly invokes $context-compression for optional billion-context compression in Codex CLI or Paseo chat.
---

# Codex CLI·Paseo 문맥 압축

이 스킬은 정식 선택 기능의 연결을 관리한다. 먼저 `.context/index.md`에서 현재 작업의 원본을 찾고 `.mycodex/integrations/billion-context/README.md`의 지원 범위를 확인한다. 정식 기능 지정과 현재 호스트의 동작 검증은 별개이며 설치·MCP 노출·실제 모델 경유·압축 관찰은 서로 다른 상태다.

요청한 실행 환경에 맞춰 프로젝트 루트에서 `python .mycodex/mycodex.py compression doctor --target . --client codex --json` 또는 `--client paseo`로 확인한다. CLI는 Paseo가 필요 없다. `unknown`을 성공으로 바꾸지 않는다. 기본 init/validate의 ready와 압축 활성화는 별개다. 현재 chat에 압축이 소급 적용됐다고 말하지 않는다.

CLI 요청은 `compression prepare`로 runtime을 준비하고, 사용자의 프로젝트 터미널에서 실행할 `python .mycodex/mycodex.py compression codex --target . --apply` 명령을 안내한다. 현재 에이전트의 비대화형 도구 안에 대화형 CLI를 중첩 실행하지 않는다. 사용자가 제어할 터미널을 명시했고 직접 실행을 요청했거나, 승인된 자동화·검증의 `exec` 실행이면 해당 환경에서 실행한다. Codex 인자는 `--` 뒤에 전달한다. 기본 dry-run은 인자 본문을 출력하지 않으며 실제 실행은 native 입출력·종료 코드를 그대로 전달한다. 종료 후 일반 `codex`로 돌아가며 Paseo 해제는 필요 없다. 앱과 원격 서버 연결은 지원 대상으로 안내하지 않는다.

Paseo 요청은 `compression prepare`, `compression paseo-enable`, `compression paseo-disable`을 사용한다. 변경 명령은 기본 dry-run이다. 준비·연결·해제를 이미 요청받았다면 결과를 확인하고 `--apply`까지 수행한다. 호스트 runtime은 프로젝트와 별도로 두며 필요하면 `--runtime <절대 경로>`와 `--paseo-home <절대 경로>`를 지정한다. CLI와 Paseo 각각 실제 사용하는 Codex 경로를 확인해 필요한 경우 `MYCODEX_CODEX_EXE`로 전달한다. 임의의 다른 Codex를 선택하지 않는다.

충돌·불완전 설치·사용자가 편집한 제공자는 보존하고 진단을 보고한다. 전역 PATH·Codex 설정·AGENTS·Superpowers를 바꾸거나 proxy/CA를 제거해서 우회하지 않는다. 설정 저장과 reload 성공을 구분하고 새 chat에서 `Codex 문맥 압축`을 선택하도록 안내한다. 해제는 새 chat에서 기존 Codex를 선택하는 흐름이며 실행 중인 chat·프록시·세션을 삭제하지 않는다.

명시적인 요약 추출 요청에는 `compression export --target . --session <Codex thread UUID>`를 먼저 확인하고 `--apply`한다. 출력 경로만 보고한다. 요약에는 민감한 문맥이 있을 수 있으며 원문 추출은 제공하지 않는다. export를 index나 최신 인계로 자동 등록하지 않는다. 필요하면 기존 session-handoff 절차로 현재 원본·Git 상태·실행 증거를 다시 확인해 인계한다. 요약이 원본·사용자 제약·승인·개발 절차의 우선순위를 바꾸지 않는다.
