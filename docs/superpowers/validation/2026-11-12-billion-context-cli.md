# Codex CLI 문맥 압축 검증

2026-11-12, 사용자가 승인한 CLI 확장을 검증했다. [설계](../specs/2026-11-12-billion-context-cli-design.md)와 [계획](../plans/2026-11-12-billion-context-cli.md)을 따른다. 앱은 범위 밖이다.

## 조합과 방법

- Windows, Codex 0.167.0, Node 26.13.0, billion-context 0.1.213, gpt-6.1-sol low.
- 실제 ConPTY에서 stdin/stdout/stderr 모두 TTY임을 확인했다. 최초 TERM=dumb 경고 후 테스트 프로세스에만 xterm-256color를 지정했다.
- 샌드박스의 읽기 전용 login status는 미로그인, 사용자 실행 환경에서는 ChatGPT 로그인으로 확인됐다. 인증 파일을 읽거나 복사하지 않고 기존 사용자 실행 환경에서 테스트했다. 모델의 명령 sandbox·승인·proxy/CA는 완화하지 않았다.
- 프로젝트 안의 별도 합성 fixture와 전용 TEMP runtime을 사용했다. 기존 개인 코드·대화는 시험 입력으로 사용하지 않았다. 원래 설정은 해시, 인증은 링크 동일성으로 확인한다.

## 실제 관찰

| 검사 | 관찰 | 판정 |
|---|---|---|
| 일반 CLI | 실제 터미널 CLI_NATIVE_OK, 종료 코드 0 | pass |
| 압축 CLI | 실제 터미널 CLI_BILI_TTY_OK, 별도 proxy와 embedded 모드 | pass |
| 실제 모델 경유 | 해당 thread의 responses 상태·API usage·gpt-6.1-sol 대응 | pass |
| 파일 읽기 | 첫 350줄·마지막 200줄 합성 로그, 실제 shell 결과와 표식 | pass |
| 압축·검색·복원 | 활성 b1 블록, search_context·decompress, 반환 파일 41,720자에서 sample=0219·group=11·CLI_MANGO_7319 확인 | pass |
| 최신 원본과 개발 | PRD 3→7 변경을 다시 읽고 answer()=7 구현, 실제 unittest RED→GREEN, 보호 파일 동일 | pass |
| 핵심 절차·인계 | using-superpowers/executing-plans/TDD/verification 읽기, 인계·최신 포인터·strict 확인 | pass: 작은 합성 작업 |
| 수정 후 exec resume | 같은 thread, 현재 PRD·인계 확인 및 실제 unittest exit 0, CLI_EXEC_RESUME_OK answer=7 | pass |
| 수정 후 대화형 resume | 실제 터미널 CLI_TTY_RESUME_OK answer=7 | pass |
| Ctrl+C | 실행 중 sleep turn 취소 후 TUI 유지, /stop으로 해당 chat의 background terminal 정리, CLI_CANCEL_RECOVERED 응답, 정상 종료 코드 0 | pass |
| 일반 CLI로 복귀 | 압축 launcher 종료 후 같은 thread를 native exec resume로 재개, 실제 unittest exit 0, CLI_NATIVE_RESUME_OK answer=7 | pass |
| 최종 ZIP 실행 | ZIP에서 설치한 .mycodex 경로와 새 runtime으로 CLI_ZIP_OK, JSON stdout·종료 코드 0 | pass |

최근 메시지·토큰 보존 기본값을 낮추지 않았다. 추가 합성 출력을 읽어 오래된 범위를 압축했다. block의 `compressedTokens=10427`을 관찰했지만 집계 `tokensSaved=0`이므로 전체 세션 절감량이나 절감률을 주장하지 않는다.

최초 인계 등록은 fixture의 needs-review 상태로 거절됐다. 모델이 설정 검토를 수행한 뒤 ready와 유효한 인계를 확인했다. 이 최초 실패를 성공으로 계산하지 않았다. 실제 tool 결과에서 RED와 GREEN을 별도로 확인했고 완성 파일의 unittest와 strict도 재실행했다.

## 자동 검사와 독립 검토

- 새 API·파서 검사 8개의 실패를 먼저 확인하고 구현했다. 초기 전체 60 tests OK 및 기존 Paseo fake-engine bridge 6 tests OK.
- 읽기 전용 검토에서 Bili가 자체 `--`를 소비해 native 구분자를 잃는 경우, native `--` 뒤 문자열에 대한 upstream 원격 모드 추정 문제를 확인했다. Bili 구분자와 명시적 `--no-daemon`을 추가했고 관련 검사 RED→GREEN을 확인했다.
- 상대 CODEX_HOME이 부모와 자식에서 다르게 해석되고 링크된 home의 overlay 파일시스템을 잘못 검사할 수 있는 문제도 재현했다. 자식 작업 폴더 기준으로 home을 한 번 절대·실경로로 해석하고, overlay가 생성되는 부모에서 인증 hardlink 가능 여부를 검사한다. 두 검사 RED→GREEN.
- 검토자가 수정된 CLI 검사 12개를 독립 재실행해 통과했고 검토 범위 내 남은 조치 항목이 없다고 보고했다. 인증·세션·private review 본문이나 live 모델 실행을 검토자에게 맡기지 않았다.
- 최종 코드의 `python -X utf8 -B -m unittest discover -s tests -v`: **64 tests, 39.084s, OK**. argv·stdio·cwd·환경·종료 코드·원격 연결 거절·인증 링크 실패·stale runtime·Paseo 없는 진단·기본 설치·배포 회귀를 포함한다.

## 검증 범위

CLI의 기본 대화형 실행·resume·exec resume와 작은 개발·인계 흐름을 확인했다. 전체 CLI 관리 명령, remote/app, 다른 OS·Codex/Node/model 버전, 모든 MCP 개별 호출, 강제 종료·포트 충돌 전체, 장기 실사용, 기본 compaction과의 동시 발생은 미검증이다. 기존 Paseo 실제 검증을 이번 CLI 결과로 대체하지 않는다.

## 배포 확인

- 0.4.0 ZIP의 33개 파일이 배포 원본과 바이트 단위로 일치하고 CRC와 상대 문서 링크 8개가 유효하다. 최종 문서 반영 후 배포 회귀 6 tests OK.
- ZIP만 추출해 PATH가 빈 환경에서 Python 절대 경로로 기본 설치와 strict 검증을 통과했다. 0.3.1 설치에 0.4.0 init을 적용하면 MANIFEST_CONFLICT로 거절하고 모든 파일을 보존했다.
- ZIP 설치본만으로 새 runtime을 준비하고 실제 exec --json 응답을 확인했다. 개발용 kit 경로를 실행하지 않았다. 재확인 실행에서 전역 config.toml의 전후 해시도 동일했다.
- 원래 Codex home과 overlay의 auth.json은 같은 파일의 공유 링크이며 인증 원문은 읽거나 복사하지 않았다. hardlink 사전 검사 파일은 남지 않았다.
- 전역 config.toml은 작업 최초 해시와 달랐다. 최종 수정 시각 07:07:12.304 UTC는 일반 CLI 기준 thread 생성 시각 07:07:12.321 UTC와 일치하며, 압축 CLI 최초 thread는 07:08:01.084 UTC다. 일반 CLI 기준 실행 시점의 변경으로 보이나 변경 내용·원인은 확정하지 못했다. 임의 복원하지 않았으며 작업 전체에 걸친 전역 파일 불변을 주장하지 않는다. 이후 압축 실행 전후의 동일성은 별도로 확인했다.
- 작업 트리 자체 설치 자산 5개와 manifest를 0.4.0으로 동기화하고 strict 검증을 통과했다. 시작 당시 main의 166개 파일 해시를 다시 확인한 뒤 CLI 변경 17개 파일과 새 배포본만 반영했다.
- 최종 main에서 전체 **64 tests OK (55.859s)**, 기존 Paseo fake-engine bridge **6 tests OK (2.047s)**, strict validate, git diff --check, 배포 재생성을 통과했다. 관리 자산 30개가 kit 원본과 일치하고 AGENTS·프로젝트 config·Superpowers·기존 배포본 173개 보호 파일 해시도 그대로다.
- 테스트 proxy의 18787 health endpoint는 실행 종료 후 연결되지 않음을 확인했다. 전용 runtime·합성 세션은 보존했다. main은 master/cb96a56이며 커밋·push·게시하지 않았다.
