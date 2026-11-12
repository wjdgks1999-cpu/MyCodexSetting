# billion-context를 Paseo chat에 연결하는 설계안

현재 상태: 2026-11-12 사용자의 정식 기능 승격 요청에 따라 0.3.1부터 Windows/Paseo용 정식 선택 기능으로 제공한다. 아래는 0.3.0 통합 설계이며, 당시의 실험 상태 유지 기준은 이번 제공 상태 결정으로 대체한다. 전체 호환성 검증을 완료했다는 뜻은 아니며, 실제 확인·미검증 범위는 [사용 안내](../../../kit/integrations/billion-context/README.md)와 [검증 기록](../validation/2026-11-12-billion-context-paseo.md)을 따른다.

## 목적과 사용자 흐름

MyCodexSetting의 문서 탐색, 템플릿, 설정, Superpowers 개발 절차에 실행 중 대화 압축 기능을 더한다. 사용자는 Paseo에서 chat으로 작업을 시작한다. 최종 지원 기준은 터미널 데모가 아니라 **Paseo chat → Codex app-server → billion-context → 모델** 전체 경로다.

MyCodexSetting 배포본에는 연동 도구와 명시적 스킬을 포함한다. 사용 설정 후 Paseo에서 `Codex 문맥 압축` 제공자를 선택하고 평소처럼 chat을 시작한다. 기존 `Codex` 제공자는 유지한다. 이미 실행 중인 chat의 통신을 소급 변경하지 않는다.

## 설계 작성 시점의 상태 — 2026-11-12

- 로컬 저장소는 `master`, `cb96a56`, 제품 버전 `0.2.0`이다. 문서 작성 전 미커밋 변경은 없었다.
- 배포 원본은 `kit/`, 자체 설치본은 `.mycodex/`와 `.agents/skills/`다. 설치 자산은 `model.py`의 허용 목록과 manifest로 검증한다.
- 현재 설치 계약은 기존 파일 보존, 기본 dry-run, Python 표준 라이브러리, 사용자 전역 Codex 설정 미변경, 자동 업그레이드 미제공이다.
- 실제 사용 방식은 사용자가 밝힌 **Paseo chat**이다. 로컬 Paseo 프로세스와 기본 `~/.paseo/config.json`의 존재만 확인했다. 본문이나 비밀 값은 출력하지 않았다. 해당 설정에는 `codex` 재정의와 제안 ID `codex-bili`가 없다.
- PATH에는 `codex`가 없었지만 설치 경로의 실행 파일은 `codex-cli 0.167.0`을 반환했다. **Paseo가 실제 선택한 바이너리와 동일하다는 확인은 아직 없다.** Paseo 설치 버전의 파일 조회는 접근 제한으로 확인하지 못했다.
- 공개 Paseo 코드 `68818067f2a55c5655dc43f380a143fe4cb7ebb6`는 사용자 지정 명령 배열과 환경을 지원하고, Codex 실행 명령 뒤에 `app-server`를 추가해 파이프로 통신한다. 사용자 설치본이 같은 버전이라는 뜻은 아니다.
- billion-context 비교 기준은 배포 태그 `v0.1.213`이다. 최신 master `c26c31ace45a88f42a2ed0ba23df2217d9c1ce99`와 구분한다. 태그 문서는 루트 `CLIENTS.md`, `CONFIGURATION.md`에 있고 최신 master에서는 `docs/`로 이동했다.
- 앞선 조사에서 기존 `dist/0.2.0` 폴더의 CRLF 때문에 재생성이 `RELEASE_CONFLICT`로 중단되는 현상을 재현했다. 이 설계는 기존 배포본을 덮어쓰지 않는다.

## 검토한 방식과 권장안

| 방식 | 결과와 비용 | 판단 |
|---|---|---|
| README에 외부 설치법만 추가 | 구현은 작지만 Paseo 연결·진단·해제가 사용자 작업으로 남음 | 요구한 기능 제공 범위에 부족 |
| 연동 도구가 고정 버전 패키지와 Paseo 제공자를 관리 | 압축 엔진은 upstream을 사용하고 연결·보존·검증을 이 프로젝트가 담당 | **권장 제안** |
| 압축 엔진을 복사하거나 fork해 내장 | 세부 제어가 가능하지만 모델 프로토콜·저장 형식·업데이트를 직접 유지해야 함 | 첫 도입 범위를 넘어섬 |

이 권장안과 계획은 2026-11-12 사용자가 승인했다. 아래의 미실행 표현은 설계 당시의 선행 조건이며 현재 실행 결과와 구분한다.

## 가장 먼저 해결할 연결 검증

Paseo의 명령 교체 지점에서 Node 실행 파일과 전용 bridge를 호출한다. bridge는 고정된 billion-context의 `bili codex` 실행기에 Paseo가 붙인 인자를 그대로 전달한다. 예상 호출은 `node <bili-entry> codex app-server ...`이며 **아직 실행 검증하지 않은 후보**다.

첫 단계에서 다음을 모두 증명해야 한다.

1. Paseo가 실제 사용하는 바이너리·버전·실행 인자를 확인한다. 임의로 설치된 다른 Codex로 대체하지 않는다.
2. 실제 `initialize`/`initialized`, `thread/start`, `turn/start`, 스트리밍, 중단·종료가 통과한다. stdout은 app-server 프로토콜 전용이며 bridge 진단은 stderr로만 보낸다. 임의의 stdout 줄 제거로 프로토콜 문제를 숨기지 않는다.
3. 실행기의 배너, `--no-daemon`, Windows 인자 처리, 모델 목록 조회가 app-server 모드에서도 호환된다. 부모 종료 시 자식·프록시 정리가 정상이다.
4. Paseo가 제공한 도구와 `mcp_servers`가 Bili MCP 주입과 병합되어 양쪽 도구가 남는다. 도구가 보이는 것과 모델 요청이 실제 프록시를 통과하는 것은 별개로 확인한다.
5. 알려진 thread와 프록시 대화를 대응시킨 뒤 실제 압축과 복원을 관찰한다. 상태 HTTP 200이나 설치 성공만으로 지원 판정을 내리지 않는다.

Paseo가 선택한 실제 모델·컨텍스트 창도 함께 확인한다. `100K`나 알 수 없는 모델의 fallback 값을 제품 기본값으로 추정하지 않는다. 기존 proxy/CA 환경과 기본 compaction의 상호 작용을 조사하고, 기본 압축을 일괄 끄는 방식으로 충돌을 숨기지 않는다.

이 관문이 실패하면 Paseo 지원은 차단 상태다. 터미널에서만 성공한 결과로 대신 통과시키지 않는다. 다른 전송 방식이나 upstream 수정이 필요하면 근거를 남기고 설계를 다시 검토한다.

## 연동 구성과 소유권

### 프로젝트에 배포할 파일

- `kit/mycodex_lib/compression.py`: dry-run 계획, 실행 환경 진단, 외부 패키지 준비, Paseo 연결·해제, 명시적 export의 진입점.
- `kit/integrations/billion-context/`: `paseo-bridge.mjs`, `package.json`, `package-lock.json`, `policy.json`, `README.md`, `THIRD_PARTY_NOTICES.md`.
- `kit/skills/context-compression/SKILL.md`, `agents/openai.yaml`: 설치 상태 확인과 사용 설정을 돕는 명시적 스킬. 현재 자기 세션에 압축을 소급 적용했다고 주장하지 않는다.
- `kit/mycodex.py`, `model.py`, 설치·검증 코드: 새 명령과 관리 자산을 연결한다. 일반 `init`/`validate`는 Node나 프록시를 실행하지 않는다.

사용자별 실행 파일은 프로젝트와 별도인 전용 runtime에 둔다. Windows 기본 제안은 `%LOCALAPPDATA%/MyCodexSetting/billion-context/0.1.213/`다. 호스트마다 생성하므로 배포 ZIP이나 프로젝트 원본 경로를 Paseo에 고정하지 않는다. Linux/macOS 지원은 별도 실검증 전까지 미검증으로 표시한다.

고정 버전 패키지는 runtime의 `package.json`·lock으로 `npm ci` 설치한다. 최초 검증에서 `--ignore-scripts`로 배포 파일이 정상 사용되는지도 확인한다. 관리자가 복사한 bridge·정책과 외부 npm 파일을 구분하고 버전·lock fingerprint를 기록한다. 설치 중단·오프라인·기존 runtime 내용 차이를 성공으로 처리하지 않는다. 같은 버전이 다르면 덮어쓰지 않고 충돌로 보고한다.

### Paseo 제공자

`agents.providers.codex-bili`에 `extends: "codex"`, label `Codex 문맥 압축`, `command: [<절대 Node 경로>, <runtime bridge 경로>]`를 추가하는 안이다. 기존 Codex와 다른 제공자의 필드·기본 선택·기존 chat은 보존한다. 제공자별 `OPENAI_BASE_URL`/`OPENAI_API_KEY`로 인증 방식을 바꾸지 않는다.

`~/.paseo/config.json`의 **이 항목 추가·제거만** 새 기능의 명시적 변경 범위다. 기본은 dry-run이다. `--apply` 때에만 적용하고 Paseo의 지원되는 reload 방법으로 새 chat에 반영한다. reload 실패는 파일 저장과 구분한다. 기존 `codex-bili`가 도구 소유가 아니거나 사용자가 수정했으면 보존하고 충돌로 중단한다. 전체 설정 백업은 비밀을 복제할 수 있으므로 보관하지 않는다. 동시 편집 확인은 메모리의 이전 바이트와 atomic 교체로 처리하고 민감한 내용은 출력하지 않는다.

Paseo가 chat 시작 시 app-server를 준비하는 CWD와 실제 thread의 프로젝트 CWD가 다를 수 있다. bridge는 runtime으로 chdir하지 않고 RPC의 프로젝트 CWD를 변경하지 않는다. 프로세스 CWD만으로 프로젝트를 추정하지 않는다. 여러 chat·프로젝트의 분리는 thread 대응과 실검증으로 보장해야 한다.

### 환경·데이터

- `BILI_CLIENT_BIN`으로 실제 검증한 Codex 절대 경로를 사용한다. PATH나 사용자 전역 환경 변수는 바꾸지 않는다.
- 전용 `BILI_CONFIG_FILE`, `BILI_SESSIONS_DIR`, 명시적인 로그·덤프 경로를 사용한다. 본문 덤프는 기본 비활성화한다. `XDG_*` 전체를 덮어써 Codex와 그 도구의 기존 설정 경로까지 바꾸지 않는다.
- Bili가 생성하는 CA·캐시·인스턴스 기록과 Codex overlay는 별도로 조사·표시한다. 모든 상태가 전용 runtime에 격리된다고 주장하지 않는다. OS 인증서 저장소를 자동 변경하지 않는다.
- Codex overlay와 `CODEX_SQLITE_HOME`이 기존 로그인·skills·rules·hooks·메모리·SQLite 상태에 미치는 영향을 확인한다. Bili나 MyCodexSetting이 인증 파일을 복사해 보관하지 않도록 확인한다. 실제 토큰·인증 원문을 읽거나 결과에 남기지 않는다.
- `autoUpdate=false`, `autoRestartOnUpdate=false`, `advisoryCheck=false`를 전용 정책에 명시한다. 세션 삭제는 자동화하지 않는다. 긴급 수정은 검토 후 새 고정 버전으로 제공한다. 승인 없이 보안 완화·백신 제외·외부 요약 서버를 설정하지 않는다.
- 기본 `AGENTS.md`, `.codex/config.toml`, Superpowers 파일에는 프록시 주소나 압축 실행 규칙을 추가하지 않는다. 압축 요약은 원본·사용자 허용 범위·개발 절차의 우선순위를 바꾸지 않는다.

## 승인된 CLI 계약

| 명령 | 기본 동작 | 변경 조건 |
|---|---|---|
| `compression doctor --target . --json` | 설치·버전·실행 경로·Paseo 연결 상태 진단 | 읽기 전용. 비활성 기능 때문에 일반 구조 검증을 실패시키지 않음 |
| `compression prepare --target . [--apply]` | 호스트 runtime 생성과 고정 패키지 설치 변경안 | `--apply` 때만 파일 생성·다운로드 |
| `compression paseo-enable --target . [--apply]` | 전용 제공자 추가 변경안 | `--apply` 때만 해당 항목 추가·reload |
| `compression paseo-disable --target . [--apply]` | 도구 소유 제공자 제거 변경안 | 해당 항목이 마지막 적용 내용과 같을 때만 제거 |
| `compression export --target . --session <id> [--apply]` | export 대상·출력 위치 확인 | `--apply` 때 runtime의 `exports/`에 고유 파일 저장. 원문 포함은 첫 버전에서 미지원 |

`doctor`는 `installed`, `provider_registered`, `protocol_verified`, `traffic_observed`, `compression_observed`를 분리한다. 관찰하지 않은 항목은 `unknown`이다. 경로·버전·진단 코드·개수만 반환하고 환경 값·대화·토큰을 출력하지 않는다. 준비·연결의 종료 코드는 0=해당 작업 성공, 1=검증/충돌/준비 미완료, 2=CLI/I/O 실행 불가로 기존 계약과 맞춘다.

사용 해제는 새 chat에서 기존 Codex를 선택하는 흐름이다. 실행 중인 프록시를 강제 종료하거나 긴 대화를 즉시 직접 연결로 전환하지 않는다. 필요하면 export를 참고해 `$session-handoff`로 원본·검증을 대조한 인계를 만든 후 새 chat을 시작한다. export 자체를 신뢰된 인계로 자동 등록하지 않는다. 제공자 제거 후에도 사용자 세션·export·다른 프록시는 삭제하지 않는다.

## 충돌 검증과 합격 조건

같은 Codex·모델·Superpowers·fixture를 사용해 A=기존 Paseo Codex, B=압축 제공자/압축 전, C=압축 제공자/실제 압축 후를 비교한다. 단위 테스트와 프록시 mock은 모델이 절차를 지키는지의 증거로 대체하지 않는다.

| 대상 | 재현할 상황 | 합격 증거 |
|---|---|---|
| Paseo 프로토콜 | 새 chat, 모델 조회, 스트리밍, 질문·승인 응답, 중단·재개, daemon 재연결 | 초기 연결·turn 완료·취소 동작, JSON-RPC 오염 없음, 도구 목록 보존 |
| 실제 압축 | 합성 대화에서 버전이 지원하는 방법으로 압축·복원 유도 | thread 대응, 압축 블록 발생, 이후 모델 입력 감소, 오래된 구체적 사실 복원; 본문 없는 개수·크기 지표 |
| Superpowers 절차 | 승인된 소형 spec/plan fixture로 계획→구현→검증; 계획 단계에서 압축 후 계속 | 관련 SKILL.md 읽기 흔적, spec/plan의 제약·다음 단계 유지, 실행한 테스트 결과; 결과 없는 완료 주장 없음 |
| 사용자 지침·승인 | 압축 전 기록한 금지 파일·변경 범위를 압축 후 다시 시험 | 보호 파일 무변경. 위험 동작은 fake 도구로 시험하고 실제 push/삭제를 실행하지 않음 |
| JIT와 원본 | 요약 이후 원본 요구사항 변경·이동 | index와 현재 원본 재확인, 오래된 요약보다 새 원본 적용 |
| project-init | PRD만 있는 fixture와 기존 설정 fixture | ready의 의미 유지, 스택·명령을 추정하지 않음, 기존 설정 보존 |
| session-handoff | 압축 이후 인계·새 chat에서 재개 | 필수 절·실행/미실행 구분·포인터 갱신; 프록시 없이도 인계와 원본으로 재개 |
| human-html | 압축 이후 명시적으로 합성 HTML 생성 | 저장 도구·한글 경로 정상, 일반 검색 제외, index·인계의 원본으로 미등록 |
| skills 표시 | Paseo 선택 목록과 실제 Codex 사용 가능 스킬 비교 | `.agents/skills`의 실제 인식 확인. UI 표시와 런타임 인식을 각각 기록; 사용자 전역에 몰래 복사하지 않음 |
| 다중 chat·agent | 동시 chat 두 개, 다른 프로젝트·worktree, 승인 검토 agent | 표식·압축·검색 결과가 다른 thread/역할로 섞이지 않음; 실제 선택한 바이너리·모드 기록 |
| Codex 기본 기능 | web search, 파일·shell 도구, 기존 MCP, rules/hooks·메모리 | A/B/C에서 필요한 기능 이용 가능, 정책·승인 범위 유지. 기능 미제공 환경은 미검증으로 구분 |
| 기본 compaction | 같은 thread에서 Codex 기본 압축과 Bili 압축이 만나는 경우 | 압축 담당·순서·실제 입력이 확인되고 중복 압축으로 원본 참조·tool-call 쌍이 손상되지 않음 |
| 장애·해제 | 프록시 중단, 포트 충돌, 재시작, 설치 실패, provider 동시 편집 | 무압축으로 조용히 우회하지 않음, 다른 chat 프로세스 미종료, 파일·사용자 상태 보존, 인계 후 새 chat 복구 |

압축 유도는 비밀 없는 합성 자료로 수행한다. 실제 사용자 대화는 벤치마크 입력으로 복사하지 않는다. 출력 문장의 동일성보다 필수 동작·산출물·제약 준수를 비교한다. 비용·지연·입력 토큰의 전후 수치는 실제 수집 가능한 항목만 기록하고 절감률을 사전 보장하지 않는다.

먼저 A에서 필수 기능 자체가 동작하는지 확인한다. A도 실패하면 기존 환경 문제와 신규 회귀를 구분하고, 해당 기능의 호환 완료 판정은 보류한다. A와 C가 똑같이 실패했다는 이유로 통과시키지 않는다.

## 구현과 배포의 범위

- 제안 제품 버전은 `0.3.0`. 우선 Windows + 실제 사용자 Paseo chat 조합만 실검증 대상으로 삼는다. 세 구성요소 버전을 묶은 지원표를 남긴다.
- 기존 0.2.0 설치에 자동 덮어쓰기·업그레이드를 추가하지 않는다. 신규 설치와 별도 임시 0.2.0 fixture의 충돌 보존을 확인한다. 자체 설치본 동기화도 관리 자산만 대상으로 별도 기록한다.
- ZIP에는 연동 소스·lock·정책·안내·출처 고지만 넣고 npm 설치물·세션·인증·CA·로그는 넣지 않는다. 설치자가 Node 없이 기존 기능을 사용할 수 있어야 한다.
- 원본 LICENSE의 MIT 본문 외 출처 표시 조건을 확인해 배포 README와 THIRD_PARTY_NOTICES에 반영한다. 포함하는 kernel의 고지도 확인한다.
- 기존 CRLF 재생성 문제는 별도 회귀 수정으로 처리한 뒤 배포 검증한다. 실제 내용이 바뀐 기존 배포본을 허용하거나 덮어쓰는 변경은 금지한다.
- 필수 Paseo/압축/절차/격리/복구 검증 중 하나라도 미검증이면 **실험 연동** 상태이며 지원 완료로 배포하지 않는다.

## 설계 작성 당시의 조사와 출처

현재까지는 저장소·공개 소스·설정 구조·실행 파일 버전을 읽기 전용으로 조사했다. Bili 설치, Paseo 설정 편집/reload, 프록시 연결, 새 압축 chat, 이 기능의 테스트와 배포는 **모두 미실행**이다. 앞선 28개 테스트 통과는 0.2.0 조사 시점의 결과이며 이 제안 기능의 검증이 아니다.

설계 초안은 brainstorming의 builder check에 따라 별도 검토자에게 읽기 전용으로 검토를 맡겼고 `nothing important left`를 받았다. 이는 설계에 추가 질문이 없다는 결과이며 사용자 승인이나 런타임 호환 증명이 아니다.

- [Bili 배포 태그](https://github.com/ranxianglei/billion-context/tree/v0.1.213), [Codex 연동](https://github.com/ranxianglei/billion-context/blob/v0.1.213/CLIENTS.md), [설정·업데이트·저장](https://github.com/ranxianglei/billion-context/blob/v0.1.213/CONFIGURATION.md), [LICENSE](https://github.com/ranxianglei/billion-context/blob/v0.1.213/LICENSE)
- [Paseo Codex 설명](https://paseo.sh/docs/codex), [사용자 지정 제공자](https://paseo.sh/docs/custom-providers)
- [검토한 Paseo 실행 코드](https://github.com/getpaseo/paseo/blob/68818067f2a55c5655dc43f380a143fe4cb7ebb6/packages/server/src/server/agent/providers/codex-app-server-agent.ts), [제공자 스키마](https://github.com/getpaseo/paseo/blob/68818067f2a55c5655dc43f380a143fe4cb7ebb6/packages/protocol/src/provider-config.ts)
- [OpenAI 프로젝트 설정 적용 범위](https://learn.chatgpt.com/docs/config-file/config-advanced#project-config-files-codexconfigtoml), [환경·인증서·상태 경로](https://learn.chatgpt.com/docs/config-file/environment-variables)
