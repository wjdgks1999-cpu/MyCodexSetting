# Codex CLI·Paseo 문맥 압축 사용 안내

MyCodexSetting은 [billion-context](https://github.com/ranxianglei/billion-context) 연동을 **정식 선택 기능**으로 제공합니다. 0.4.0부터 Codex CLI에서도 선택할 수 있으며, 기존 Paseo chat 연결도 유지합니다. 모델에 전달되는 문맥을 압축하고 필요할 때 검색·복원합니다. 원본 문서 탐색, Superpowers 개발 절차와 세션 인계는 계속 사용합니다.

billion-context와 내장 [acp-kernel](https://github.com/ranxianglei/acp-kernel)을 사용하며, 패키지를 배포 ZIP에 넣는 대신 **0.1.213으로 고정된 npm lock**으로 호스트 runtime에 설치합니다. [출처와 전체 라이선스 고지](THIRD_PARTY_NOTICES.md)를 함께 확인하세요. upstream LICENSE에는 MIT 본문 외 제품 출처 표시 조건도 있습니다.

## 지원 범위

기준 환경은 **Windows / Codex 0.167.0 / Bili 0.1.213 / Node 26.13.0 / gpt-6.1-sol low**이며 Paseo 방식은 **Paseo 0.15.4**에서 확인했습니다. 다음은 2026-11-12의 실제 검증 범위이며 다른 OS·버전·모델의 결과를 대신하지 않습니다.

| 구분 | 확인 범위 |
|---|---|
| Codex CLI | 실제 대화형 터미널 응답·종료, 압축·검색·원문 복원, 대화형 resume와 exec resume, 현재 PRD 재확인·RED→GREEN·인계 |
| 연결·압축 | 실제 Paseo CLI/SDK의 모델 경유, 압축·검색·원문 복원, 기존 MCP 공존 |
| 기존 개발 흐름 | Superpowers 핵심 절차의 RED→GREEN, 변경된 PRD 재확인, 인계 후 기존 Codex로 재개 |
| 관리·배포 | 준비·제공자 등록·reload·해제, ZIP 단독 설치, Node 없는 기본 설치·검증 |
| 일부만 확인 | project-init 행동, 다중 chat/프로젝트 분리, HTML 생성·구조 검사, 취소·복구 |
| 미검증 | Paseo UI 스킬 목록·모든 스킬 개별 주입, 승인 검토 역할·전체 worktree 격리, web/rules/hooks/memory 전체 조합, 기본 compaction과 동시 압축, 강제 프록시 장애·포트 충돌·재연결 전체, HTML 화면, 장기 실사용 |

정식 기능 지정은 제공 상태를 뜻합니다. `doctor`의 `support: supported`도 이 상태를 나타내며 현재 호스트의 연결·압축 성공 판정이 아닙니다. 미검증 항목의 동작이나 일정한 토큰 절감률을 보장하지 않습니다.

Codex 앱·원격 app-server 연결은 이 기능의 지원 범위에 포함하지 않습니다. CLI는 `--no-daemon`을 지원하는 Codex가 필요하며, 옵션을 지원하지 않는 버전에서는 일반 모드로 우회하지 않고 실행 오류로 종료합니다.

## 준비사항

- 기본 프로젝트에 MyCodexSetting이 설치돼 있어야 합니다. `init`/`validate`에는 Python 3.11+만 필요하며 Node나 네트워크는 사용하지 않습니다.
- 압축 기능을 준비할 호스트에는 Node **20 이상**, npm과 실제 사용하는 Codex 실행 파일이 필요합니다. Paseo 방식에만 Paseo가 필요합니다.
- CLI는 `Get-Command codex`, Paseo는 `provider diagnostic codex`로 선택 경로를 확인합니다. 자동 감지 경로가 다르거나 Windows 실행 경로가 shim이면 `MYCODEX_CODEX_EXE`에 실제 `codex.exe` 경로를 설정한 프로세스에서 준비합니다. Codex는 버전 실행 파일로 고정되므로 업데이트 뒤 자동 전환되지 않습니다.
- Windows 기본 runtime은 `%LOCALAPPDATA%/MyCodexSetting/billion-context/0.1.213/`이며 프로젝트 밖에 둡니다.

## Codex CLI에서 선택 실행

프로젝트 터미널에서 진단하고 runtime을 준비합니다. `doctor --client codex`는 Paseo 설정을 읽지 않습니다.

```powershell
python .mycodex/mycodex.py compression doctor --target . --client codex --json
python .mycodex/mycodex.py compression prepare --target .
python .mycodex/mycodex.py compression prepare --target . --apply
python .mycodex/mycodex.py compression codex --target .
python .mycodex/mycodex.py compression codex --target . --apply
```

`codex` 하위 명령도 기본은 dry-run입니다. `--apply`를 붙인 실행은 해당 프로젝트를 작업 폴더로 사용하고 실제 터미널 입출력과 종료 코드를 전달합니다. Codex 옵션은 MyCodexSetting 옵션 뒤의 `--`로 구분합니다.

```powershell
python .mycodex/mycodex.py compression codex --target . --apply -- --no-alt-screen
python .mycodex/mycodex.py compression codex --target . --apply -- resume <thread-UUID>
python .mycodex/mycodex.py compression codex --target . --apply -- exec --json "현재 프로젝트 구조를 설명해 주세요."
```

`<thread-UUID>`는 실제 세션 ID로 바꿉니다. 대화형 실행·재개에는 사용자가 접근할 수 있는 터미널이 필요합니다. 파이프나 자동화에서는 `exec`를 사용합니다. dry-run은 인자 개수만 표시하고 프롬프트 본문을 출력하지 않습니다.

이 실행은 자식 프로세스에만 압축 환경을 설정하고 `--no-daemon`을 명시합니다. 원격 서버는 자식 환경을 상속하지 않으므로 `--remote`는 거절합니다. 설정된 `CODEX_HOME`은 실행 대상 폴더 기준 절대 경로로 해석하며, 링크 경로를 해소해 인증과 overlay가 같은 위치 기준을 사용하게 합니다.

압축 CLI를 종료한 뒤 일반 실행은 평소처럼 `codex` 또는 `codex resume <thread-UUID>`를 사용합니다. 전역 alias나 Paseo 제공자를 해제할 필요가 없습니다. 기존 chat에 압축이 소급 적용되지는 않습니다.

## Paseo 연결

설치한 프로젝트에서 `$context-compression`으로 준비·연결을 요청하거나, 프로젝트 루트에서 아래 명령을 실행합니다. 각 변경 명령은 `--apply` 없이 먼저 변경안을 확인할 수 있습니다.

```powershell
python .mycodex/mycodex.py compression doctor --target . --json
python .mycodex/mycodex.py compression prepare --target .
python .mycodex/mycodex.py compression prepare --target . --apply
python .mycodex/mycodex.py compression paseo-enable --target .
python .mycodex/mycodex.py compression paseo-enable --target . --apply
```

Paseo에서 **Codex 문맥 압축**을 선택해 새 chat을 시작합니다. 기존 Codex 제공자와 기존 chat은 유지됩니다. `saved_not_active`는 설정만 저장된 상태이므로 Paseo 설정 reload 후 새 chat을 시작해야 합니다. 자동 데몬 재시작이나 기존 chat 강제 이동은 하지 않습니다.

시험용 경로가 필요하면 `--runtime <절대 경로>`와 `--paseo-home <절대 경로>`를 지정합니다. 기본값 이외의 경로를 쓸 때는 이후 진단·연결·해제·추출 명령에도 같은 옵션을 전달합니다.

## 상태 확인과 충돌 처리

`doctor`는 설치, 제공자 등록, 프로토콜 검증, 실제 모델 경유, 압축 관찰을 구분합니다. 관찰 증거가 없는 항목은 `unknown`입니다. 설치 성공이나 MCP 노출만으로 압축이 작동한다고 판정하지 않습니다. 인덱스의 `ready`와 압축 활성화도 별개입니다.

기존 runtime의 관리 파일이나 동명 제공자가 예상과 다르면 보존하고 충돌로 중단합니다. 설치 중단 runtime도 자동 삭제·덮어쓰지 않습니다. 원인을 검토한 뒤 새 빈 경로에 준비할 수 있습니다.

**이전 버전에서 이전할 때:** 프로젝트 설치 자산의 자동 업그레이드는 제공하지 않습니다. 연동 안내문을 포함한 관리 파일이 바뀌면 기존 runtime과 해시 충돌이 발생합니다. Paseo 제공자가 연결돼 있으면 이전 kit으로 먼저 해제한 뒤 프로젝트 자산 이전을 검토하고, 새 빈 runtime 경로를 지정해 준비합니다. 예를 들어 `%LOCALAPPDATA%/MyCodexSetting/billion-context/0.1.213-mycodex-0.4.0/`을 사용할 수 있습니다. 이후 명령에도 같은 `--runtime`을 전달합니다. 기존 세션과 export는 보존합니다.

## 요약 추출과 인계

```powershell
python .mycodex/mycodex.py compression export --target . --session <Codex-thread-UUID>
python .mycodex/mycodex.py compression export --target . --session <Codex-thread-UUID> --apply
```

runtime의 `exports/`에 고유 JSON을 만들고 경로만 출력합니다. 활성 요약만 제공하며 원문은 내보내지 않습니다. 요약의 사실·완료·승인을 현재 원본과 재확인한 뒤 `$session-handoff`로 인계합니다. export는 인덱스나 최신 인계로 자동 등록되지 않으며 원본·사용자 제약·승인·개발 절차의 우선순위를 바꾸지 않습니다.

## 해제

```powershell
python .mycodex/mycodex.py compression paseo-disable --target .
python .mycodex/mycodex.py compression paseo-disable --target . --apply
```

해제 후 새 chat에서 기존 Codex를 선택합니다. 도구 소유이며 수정되지 않은 제공자만 제거하고 실행 중인 chat·세션·export·다른 프록시는 삭제하지 않습니다. 배포본을 받거나 프로젝트에 설치하는 것만으로 사용자 Paseo에 연결되지는 않습니다.

## 설정과 데이터 보관

자동 업데이트·업데이트 재시작·advisory 확인·본문 덤프는 꺼져 있으며 외부 요약 서버를 기본 설정하지 않습니다. bridge는 부모 PATH·환경과 전역 Codex 설정을 바꾸지 않고 기존 proxy/CA를 우회하지 않습니다. 별도의 `CODEX_CA_CERTIFICATE`가 설정된 환경은 검증되지 않아 실행 전에 중단합니다. OS 인증서 저장소는 변경하지 않습니다.

runtime의 세션·로그·npm cache·export는 대화 내용이 들어갈 수 있으므로 비공개로 보관합니다. Bili의 CA·캐시·상태는 기본 XDG 위치에도 생기고 Codex overlay는 원래 Codex home 옆에 생깁니다. 모든 데이터가 runtime에 격리되지는 않습니다. 인증은 공유 링크를 유지하며 배포·검증 산출물에 복사하지 않습니다. 자동 정리나 해제로 사용자 데이터를 삭제하지 않습니다.
