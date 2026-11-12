# Paseo와 billion-context 실제 검증

현재 제공 상태: 2026-11-12 사용자의 승격 요청에 따라 **0.3.1 정식 선택 기능**으로 제공한다. [사용 안내](../../../kit/integrations/billion-context/README.md)에 사용법과 호환 범위를 정리했다. 이번 지정은 아래 실측 범위를 늘리거나 `not_run`을 통과로 바꾸지 않는다.

아래 Task 1–6은 **0.3.0 당시의 검증 기록**이다. 승인된 [설계](../specs/2026-11-12-billion-context-design.md)와 [계획](../plans/2026-11-12-billion-context.md)의 연결·압축 선행 관문을 통과했고, 관리 CLI·bridge·스킬을 구현해 당시 실험 연동으로 제공했다.

## 조합과 시험 범위

- Windows, 설치된 Paseo **0.15.4**, Paseo가 감지한 Codex **0.167.0**, Node **26.13.0**, billion-context **0.1.213 (133f3525c)**, **gpt-6.1-sol / low**.
- Paseo의 EXE·ASAR package·실제 provider 실행 코드와 진단을 확인했다. 공개 main을 설치본의 사실로 사용하지 않았다. Paseo는 사용자 지정 명령 뒤에 `app-server`를 붙이고 stdio로 연결한다.
- 고정 npm lock으로 `npm ci --ignore-scripts --no-audit --no-fund`를 실행했다. 초기 runtime에 93개 패키지가 설치됐고 배포된 `dist/index.js`와 `dist/mcp.js`를 사용했다. global npm 설치는 하지 않았다.
- TEMP의 `feat/billion-context` 작업 트리에서 구현했다. 실제 모델 시험은 기존 Paseo와 별도인 localhost 전용·relay 비활성 home과 합성 프로젝트만 사용했다. 사용자 기존 Paseo 설정·chat은 바꾸지 않았다. 커밋·push·외부 게시를 하지 않았다.
- 실제 사용자 대화·코드를 시험 입력으로 복사하지 않았다. 인증 원문을 조회·출력·복사하지 않고 overlay auth의 samefile 링크 여부만 확인했다. Codex 전역 설정은 해시로 전후 동일함을 확인했다.

## Task 1: 실제 경유·압축·복원

| 검사 | 실제 관찰 | 판정 |
|---|---|---|
| 기존 baseline | 28 tests, 29.491s, OK | 기존 0.2.0 기준이며 신규 검증과 구분 |
| 직접/Bili stdio | 초기 opt-in 2 tests OK; initialize/config-read·순수 JSON stdout·EOF 종료·프록시 drain | pass: 추론 없는 전송 검사 |
| Paseo 직접/Bili chat | 각 합성 응답 표식, idle; SDK thread와 CWD 대응 | pass: 실제 모델 응답 |
| 실제 프록시 경유 | 해당 responses session의 모델·API input count와 Paseo usage 일치 | pass: MCP 노출만 확인한 결과와 구분 |
| 로그인·상태 | ChatGPT 로그인, 기본 OpenAI provider, auth 공유 링크, 전역 config 해시 유지 | pass: 관찰한 조합 |
| 파일 읽기 | 최초 TEMP fixture는 양쪽 모두 Access denied. 승인된 프로젝트 내부 fixture에서는 양쪽 성공; Bili shell exit 0, 10,334 bytes | 권한 완화 없이 fixture만 변경 |
| 작은 범위 압축 | 0 blocks | no-op: 성공으로 세지 않음 |
| 오래된 범위 압축·검색 | `m00003–m00007`에서 1 block, tokensSaved=2820, 원래 합성 표식 회수 | pass |
| 원문 복원 | decompress가 반환한 전용 복원 파일만 읽어 표식·group=9·sample=799 회수 | pass: 원본 파일 재조회 없이 SDK shell exit 0·10KB 초과 결과 확인 |
| host MCP 공존 | `mycodex_probe.fixture_echo`와 `bili.acp_status`가 같은 chat에서 모두 completed, error=null; 합성 nonce 일치 | pass |
| 취소·종료 | 지연 요청 stop 후 running→idle, inFlight=0; 시험 chat 5개 archive·전용 데몬 종료·health로 확인한 소유 프록시 3개 종료 | pass: 사용자 기존 chat 미변경 |

기본 최근 메시지 3개·약 5000 tokens 보존 설정을 낮추지 않았다. 두 번째 합성 도구 출력을 추가해 이전 읽기를 보존 구간 밖으로 옮겼고 압축 가능량 3077 tokens를 관찰한 뒤 요청했다. 해당 thread의 API input은 직전 읽기 완료 때 **35,521**, 압축·검색 완료 때 **34,374**였다. 각 호출의 관리 메시지가 다르므로 단순 차이를 일반 절감률로 확대하지 않는다. Bili의 **2820 tokensSaved**, 로그의 fold 비율, Paseo의 CostUsd=0은 전체 세션·시스템 문맥·실제 비용 절감률이나 무료 사용의 증거가 아니다.

한 upstream stream은 completion 없이 끝나 응답이 지연됐다. 시험 요청을 취소한 뒤 같은 chat에서 읽기·압축을 계속했다. 원인을 서비스나 Bili의 결함으로 확정하지 않았다. 최초 decompress는 모델이 `toFile`을 선택했지만 당시 시험 요청이 파일 접근을 금지해 결과를 읽지 못했다. 이후 도구가 반환한 복원 파일만 허용해 검증했으며 compression 설정·권한을 바꾸지 않았다.

## Task 5: 관리 bridge의 A/B/C 비교

A는 기존 Codex, B는 관리 bridge의 압축 전, C는 같은 B chat의 실제 압축 후다. 두 합성 fixture에 PRD·승인된 작은 spec/plan·보호 파일·설치 자산·프로젝트 로컬 Superpowers를 제공했다. 전역 스킬은 설치하지 않았다. C 직전에 PRD의 정수를 **3 → 7**로 바꿨다. 관리 bridge의 해당 thread에서 active tier-1 블록 1개를 확인했다. 이 두 번째 workflow의 tokensSaved는 **0**으로 관찰돼 절감 성과로 계산하지 않는다. model window는 `registry-peek` 근거 **475000**으로 관찰했으며 100K로 바꾸지 않았다.

| case | mode | 실행한 행동·기대 조건 | 관찰 근거 | result |
|---|---|---|---|---|
| 프로토콜/연결 | A/B/C | handshake·실제 run/send·reload, 정상 turn | 실제 Codex transport 3 tests OK, 각 chat idle | pass |
| 압축/복원 | B/C | 실제 블록·구체적 사실 보존 | Task 1 복원 및 관리 bridge active block 1 | pass |
| Superpowers 핵심 절차 | A/C | 승인 fixture plan, 실제 RED→GREEN | SDK shell 출력에서 각각 1-test FAILED와 OK, using-superpowers/executing-plans/TDD/verification SKILL 읽기 | pass |
| 사용자 제약 | A/C | 보호 파일 무변경·외부 위험 작업 금지 | protected.txt 동일, fixture commit 없음, 실제 push/deploy/delete 미실행 | pass: 한정 범위 |
| JIT 최신 원본 | A/C | 요약보다 바뀐 PRD 우선 | 두 fixture의 answer()=7 및 실제 unittest 각 1개 통과 | pass |
| project-init | A/C | 설정 조사 요청·ready 의미 유지 | needs-review→ready 및 strict 통과; PRD-only/기존 맞춤 설정 전체 행동 비교는 미실행 | partial / not_run |
| session-handoff | A/C 및 새 A | 인계·최신 포인터·native 재개 | 두 인계와 index 구조 통과, 새 native chat에서 WORKFLOW_RESUME_OK 7 및 실제 1-test OK | pass |
| human-html | A/C | 명시적 한글 HTML 생성, 일반 원본 제외 | 저장 helper 구조 검사·HTML 존재, index/인계에 HTML 원본 링크 없음 | pass: 화면 검증 제외 |
| skills 표시 | A/B/C | UI와 실제 런타임 인식을 구분 | 핵심 절차 읽기·산출물은 확인; UI 목록과 모든 명시적 스킬 개별 주입은 미관찰 | not_run |
| 다중 chat/프로젝트/역할 | A/B | thread·표식 분리 | 서로 다른 thread/CWD/응답 표식. 승인 검토 역할과 별도 worktree 전체 격리는 미실행 | partial / not_run |
| Codex 기본 기능 | A/B/C | shell·파일·기존 MCP 유지 | 실제 shell/파일 및 host MCP+Bili 공존. web/rules/hooks/memory 전체는 미실행 | partial / not_run |
| 기본 compaction | C | 이중 압축 시 원본·tool-call 쌍 보존 | 기본 compaction을 끄지 않았으나 동시 발생 시험은 없음 | not_run |
| 장애·해제 | B/C/새 A | 취소·제공자 해제/reload·native 복구 | owned profile 제거와 native 재개 성공. 강제 프록시 장애·포트 충돌·데몬 재연결 전체는 미실행 | partial / not_run |

`MYCODEX_WORKFLOW_ROOT`에 실제 A/B fixture를 지정한 `python -X utf8 -B -m unittest discover -s tests/integration -p test_compression_workflow.py -v`: **1 test / 두 subcase, 1.252s, OK**. 함수·실행 가능한 unittest·보호 파일·인계·HTML 제외·strict validate를 실제 산출물로 재확인했다. 모델의 완료 표식만으로 판정하지 않았다.

두 경로 모두 일시적인 `orchestrator_helper_incomplete` shell 준비 오류가 발생했다. 권한·CA·sandbox 변경 없이 재시도해 진행했다. A의 최초 인계는 필수 절 오류로 도구가 거절했으며 최종 인계와 포인터의 존재를 따로 검사했다. 의도된 TDD 실패와 최종 검증 실패를 구분했다. 전체 절차·역할·기본 compaction 호환 완료를 선언하지 않으며, 큰 window를 채우기 위한 불필요한 추론이나 실제 위험 작업을 실행하지 않았다.

workflow 전용 chat 3개를 archive하고 데몬을 종료했다. health로 확인한 소유 프록시 1개가 종료됐고 전역 config 해시와 auth 공유 링크가 유지됐다.

## Task 6: 배포 후보 검증

- 최초 구현 전체 단위/회귀 **49 tests, 38.580s, OK**; task-done 재실행 **49 tests, 37.811s, OK**. CRLF 동일 폴더는 보존하고 실제 내용 변경·추가 파일·다른 ZIP은 충돌을 유지했다.
- 명시적 opt-in 통합 **10 tests, 32.435s, OK**: 실제 Codex transport 3개, fake-engine bridge 6개, 실제 A/C 산출물 검사 1개. 자동 검사만으로 live 압축 증명을 대체하지 않는다. live 조건 없는 skip은 pass가 아니다.
- 관리 자산 30개 동기화 후 `.mycodex/mycodex.py validate --target . --strict --json`: `ok=true, findings=[]`. AGENTS·활성 config·Superpowers는 보존했다.
- 새 임시 배포 경로 `MyCodexSetting-bili-releasecheck-20261112`에서 ZIP 생성·CRC·목록을 확인했다. 허용 목록 32 files이며 npm 설치물·세션·로그·CA·인증·개발 자료는 없다.
- ZIP을 따로 풀어 PATH를 빈 값으로 둔 Python 절대 경로로 신규 init/validate를 실행했고 Node 없이 통과했다. fixture의 ready 변경은 구조 검사를 위한 명시적 준비이며 제품 조사 완료 주장에 사용하지 않았다.
- 기존 0.2.0 배포본으로 설치한 fixture에 새 init --apply는 충돌 종료 1, 전후 모든 파일 바이트 동일이었다.
- ZIP으로 설치된 `.mycodex/mycodex.py`만 사용해 새 runtime을 실제 npm ci로 준비했다. 전용 Paseo home의 제공자 등록·reload·새 chat 응답 `MYCODEX_ZIP_RUNTIME_OK`를 확인했다. provider command에는 Node와 host runtime bridge만 있으며 checkout/압축 해제 폴더 경로가 남지 않았다.
- ZIP 시험의 chat 1개·도구 소유 profile·전용 데몬을 해제했고 health로 확인한 소유 프록시 1개도 종료됐다. 사용자 기존 Paseo home과 chat은 유지했다.
- 스킬 quick_validate는 처음 PyYAML 부재로 실행 불가였다. 개발 scratch에만 의존성을 넣어 재실행해 `Skill is valid!`를 확인했다. 제품 Python 의존성은 늘리지 않았다.

## 재현과 한계

별도 읽기 전용 최종 검토에서 오래된 bridge/policy를 같은 upstream 버전이라는 이유로 재사용할 수 있는 문제를 찾았다. runtime의 자체 owner 해시뿐 아니라 현재 kit의 모든 관리 자산 해시와도 일치해야 ready로 판정하도록 수정했다. 사라진 pinned 실행 파일은 `PINNED_TOOL_UNAVAILABLE`, 불완전 배포 원본은 `INTEGRATION_INCOMPLETE`로 진단하며 기존 runtime을 보존한다. 관련 3개 회귀 검사의 실패를 먼저 확인한 후 수정했고 최종 전체 검사는 **52 tests, 37.123s, OK**였다. bridge 자체는 검토 전후 동일하므로 위 실제 전송·Paseo 증거의 적용 범위도 같다.

검증 기록 일부의 한글이 PowerShell stdin 전달 중 `?`로 손상된 것을 발견해 Unicode를 보존하는 apply_patch로 원래 실행 근거를 재작성했다. index·계획·설계의 과거 상태도 현재 결과와 구분했다. 제품 코드와 배포 README는 이 문자 손상의 영향을 받지 않았다. 최종 `git diff --check`와 strict validate가 통과했다.

`tests/integration/test_paseo_bili_protocol.py`는 고정 runtime·실제 Codex·Node 경로를 명시하는 opt-in 전송 검사다. fake Codex home으로 추론 없이 실행한다. `test_paseo_bili_bridge.py`의 fake engine 검사는 argv·stdio·환경·종료만 증명한다. 실제 chat은 설치된 Paseo CLI/SDK의 별도 home에서 검증했으며 본문 대신 버전·상태·개수·크기·합성 표식 결과만 기록했다.

Task 5 표의 not_run 항목이 남아 전체 호환성 관문은 미충족이다. 산출물은 **실험 기능을 포함한 0.3.0**이며 정식 호환 지원 완료를 뜻하지 않는다.

## 원래 프로젝트 반영 후 최종 확인

- 원래 작업 폴더에서 전체 **52 tests, 46.259s, OK**, strict validate `ok=true, findings=[]`, `git diff --check` 통과.
- 기존 AGENTS·활성 `.codex/config.toml`·Superpowers·0.2.0 배포본 **106개 파일의 해시가 동일**하다. 자체 설치 관리 자산과 source가 일치한다.
- 최종 ZIP 32개 파일의 전체 내용이 source 허용 목록과 일치하고 CRC가 정상이다. SHA-256: `5961db9ccb7aed2556b278f54afebe17fefd26768eaf89c7b7f3736e36ef7061`.
- 최종 ZIP을 새 임시 경로에 풀어 Node 없는 init/validate를 재확인했다. 최종 ZIP의 관리 코드로 기존 시험 runtime의 readiness와 Paseo 연결 dry-run을 확인했다. 실제 모델 응답은 위 별도 ZIP 시험의 결과이며 검토 후 bridge 코드는 동일하다.
- 권한이 다른 실행 계정에서 만든 새 배포 폴더는 정상 내용임을 확인해 정확한 TEMP 경로에 보존한 뒤, 일반 실행 계정으로 같은 폴더를 재생성했다. 일반 Git에서 배포 폴더 전체를 읽을 수 있으며 ZIP 바이트는 그대로다.
- 사용자 기존 Paseo 연결은 비활성 상태로 유지했다. 시험용 home만 연결·해제했고 모든 시험 chat과 소유 프록시의 종료를 확인했다. 커밋·push·외부 게시는 하지 않았다. 무커밋 작업의 근거를 보존하기 위해 실행 원장과 작업 트리는 남겼다.

## 0.3.1 정식 기능 승격·문서 정리 확인

2026-11-12 사용자 요청으로 billion-context를 정식 선택 기능으로 지정했다. README·관리 스킬·CLI의 제공 상태를 맞추고, 기존 호환성 표의 미검증 항목은 유지했다. 이번 작업은 실제 Paseo 모델 요청이나 압축·복원을 재실행하지 않았다.

- README는 **175 → 77줄**, 문자 수는 **9368 → 2843자**로 줄였다. 일반 상세를 `docs/usage.md`, 압축 상세를 `kit/integrations/billion-context/README.md`로 옮겼다. 원본의 설치·인계·설정·충돌·데이터 보관·라이선스 정보를 해당 문서에 보존했다.
- 기존 ZIP 단독 설치 검사에 상세 문서 포함·상대 링크 검사를 추가하고, doctor 검사에서 제공 상태와 미설치·미관찰 상태의 분리를 확인했다. 변경 전 두 검사의 기대 실패 후 `python -X utf8 -B -m unittest discover -s tests -v`: **52 tests, 34.386s, OK**.
- 자체 설치 파일이 기존 manifest와 일치하는지 먼저 확인한 후 관리 파일 4개와 manifest만 0.3.1로 동기화했다. `python -X utf8 -B .mycodex/mycodex.py validate --target . --strict --json`: `ok=true, findings=[]`. `git diff --check` 통과.
- `python -X utf8 -B tools/build_release.py`로 0.3.1 폴더·ZIP을 만들고 재실행도 통과했다. 허용 목록 **33 files**의 전체 내용 일치·CRC 정상·저장소와 배포본 상대 링크 **27개**를 확인했다. SHA-256: `56f6cac82325da8bf6aa9bd12bb0883fb16e60315128178c48dce7742755656d`.
- AGENTS·활성 config·Superpowers·기존 0.2.0/0.3.0 배포본 등 보호 파일 **139개**의 해시가 동일하다. runtime·Paseo 제공자·현재 chat은 변경하지 않았다. 0.3.0 runtime의 안내문 해시 충돌 가능성과 별도 이전 방법은 연동 사용 안내에 명시했다.
