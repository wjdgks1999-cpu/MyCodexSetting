# Paseo chat용 billion-context 통합 구현 계획안

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Paseo에서 평소처럼 시작한 Codex chat에 billion-context 압축을 적용하고, 기존 MyCodexSetting 기능과 개발 절차가 압축 전후 유지되는 것을 검증한다.

**Architecture:** MyCodexSetting에 외부 패키지 준비·진단·Paseo 제공자 연결·해제 도구와 명시적 스킬을 포함한다. 실제 압축은 고정된 upstream 패키지가 담당하며, 기존 Codex 제공자와 프로젝트 문서·설정은 보존한다. Paseo app-server 연결 증명을 이후 제품 구현의 선행 관문으로 둔다.

**Tech Stack:** 기존 Python 3.11+ 표준 라이브러리·unittest, 선택 기능의 Node.js 20+·npm·Node 표준 라이브러리 bridge, billion-context `0.1.213` 검증 후보, 실제 설치된 Paseo·Codex.

**Spec:** [통합 설계 제안](../specs/2026-11-12-billion-context-design.md).

**Status:** 2026-11-12 사용자 승인 후 0.3.0 통합을 구현·검증했다. 이어진 정식 기능 승격 요청은 아래의 0.3.1 후속 작업에 기록한다. Task 5의 미검증 체크박스는 그대로 보존하며 기능 제공 상태와 구분한다. 커밋·push·외부 게시는 승인 범위에 포함하지 않는다.

## Global Constraints

- 기준은 Windows에서 사용자가 시작하는 **Paseo chat**이다. 터미널의 `bili codex` 성공만으로 지원 완료를 선언하지 않는다.
- 배포 후보는 MyCodexSetting `0.3.0`, billion-context `0.1.213`. Paseo와 실제 선택된 Codex 바이너리·버전을 Task 1에서 고정 기록한다. 다른 모델·OS·버전으로 결과를 일반화하지 않는다.
- 기본 `init`/`validate`는 Python 표준 라이브러리만 사용하며 Node 설치·네트워크 요청·프록시 기동을 추가하지 않는다.
- 패키지 준비·Paseo 연결·해제·export는 기본 dry-run, `--apply`에서만 변경한다. 부모 프로세스 환경·PATH·전역 Codex 설정·기존 제공자는 변경하지 않는다.
- `autoUpdate=false`, `autoRestartOnUpdate=false`, `advisoryCheck=false`. 세션·로그·CA·인증·npm 설치물을 배포하지 않는다.
- 새 provider ID는 `codex-bili`, label은 `Codex 문맥 압축`. 이미 같은 ID가 있으면 소유권 확인 없이 덮어쓰지 않는다.
- 압축 관찰, 실제 모델 요청 경유, MCP 인식, 설치 상태는 각각 독립적으로 판정한다. 미실행·skip·mock 성공은 실제 chat 성공으로 바꾸지 않는다.
- Superpowers·AGENTS·JIT·인계가 원래 갖는 우선순위를 유지한다. 전역 스킬 복사나 절차 완화를 호환성 해결책으로 쓰지 않는다.
- 오래된 배포본·사용자 runtime·기존 chat·사용자 데이터는 삭제하지 않는다. 커밋·push·외부 게시와 기존 설치의 자동 업그레이드는 이 계획에 포함하지 않는다.

## Review Focus

1. Paseo가 덧붙인 `app-server` 인자와 파이프 프로토콜이 wrapper·Bili 실행기에서 손상되는 경우: Task 1·3의 실제 handshake, stderr 분리, argv 시험으로 확인한다.
2. MCP만 살아 있거나 기본 compaction·기존 proxy/CA 때문에 모델 요청이 우회하는 경우: Task 1·5에서 thread에 대응한 실제 입력·압축 블록·도구 결과로 판정한다.
3. 공유 Codex home·SQLite·스킬 탐색과 동시 chat의 상태가 섞이는 경우: Task 1·5의 기존 제공자 병행, 역할·프로젝트 표식, 재개 시험으로 확인한다.
4. Paseo 설정의 비밀·알 수 없는 필드·동시 편집·동명 provider가 손상되는 경우: Task 2·4의 합성 설정 보존·충돌·해제 시험으로 확인한다.
5. 설치 성공·fixture 결과만으로 지원을 선언하거나 npm·세션 데이터가 ZIP에 들어가는 경우: Task 5·6에서 실제 지원표와 ZIP 독립 설치·내용 검사를 완료한다.

---

## Task 1: Paseo 실제 연결 가능성부터 증명

**Files:** Create `tests/integration/test_paseo_bili_protocol.py`; 실행 후 실제 결과가 있을 때만 Create `docs/superpowers/validation/2026-11-12-billion-context-paseo.md`.

**Interfaces:** 이후 작업에 제공할 것은 지원 조합 `{paseo_version, codex_path, codex_version, bili_version, node_version, launch_argv}`와 `protocol_verified`, `traffic_observed`, `compression_observed`, `tool_merge_verified`, `state_preserved`의 판정 및 근거다. 이 값은 비밀 없는 메타데이터만 기록한다.

- [x] 실제 Paseo 설치 버전, provider schema, 선택된 Codex 경로와 버전, 명령·환경 주입 지점을 확인한다. 공개 main의 동작을 설치본 사실로 사용하지 않는다. 기존 상태는 로그·비밀 복사 없이 보존한다.
- [x] 임시 fixture와 별도 시험용 제공자를 사용한다. 현재 사용자 chat을 바꾸지 않고, 고정 패키지 tarball·lock·실제 `dist/` 진입점을 확인한다. 설치 script를 끈 상태에서 실행 가능한지도 시험한다.
- [x] 프로토콜 검사를 먼저 작성한다. 실제 app-server의 initialize, 목록 조회, thread 시작, turn streaming, 중단, stdin 종료와 자식 종료를 assert한다. fake upstream 검사는 전송·구조 범위로만 표시한다.
- [x] 후보 `node <bili-entry> codex app-server ...`를 실제 Paseo 실행 경로로 시험한다. stdout에는 프로토콜만 남고 로그는 stderr인지 확인한다. 기본 30초 초기 연결 예산을 넘기거나 임의 줄 제거가 필요한 상태는 실패로 기록한다.
- [x] Paseo MCP와 Bili MCP의 병합, 실제 로그인 방식 유지, 프로젝트 CWD·기존 설정·skills·공유 SQLite 상태를 확인한다. 실패 시 전역 설정을 바꾸어 우회하지 않는다.
- [x] 비밀 없는 합성 turn으로 실제 모델 요청 경유와 압축·복원을 관찰한다. 선택 모델·컨텍스트 창·기본 compaction·기존 proxy/CA의 영향을 기록한다. 불필요한 장문으로 비용을 늘리지 않는다.
- [x] `test_paseo_bili_protocol.py`를 실제 테스트 전용 실행 조건에서 실행하고 stdout 순도·argv·종료·tool merge를 확인한다. live 조건 미충족 시 skip을 지원 성공으로 계산하지 않는다.
- [x] **관문:** 필수 전송·경유·압축·보존 시험을 통과한 경우에만 Task 2로 진행한다. 미통과면 원인과 대안 범위를 기록하고 설계를 갱신한다. 별도 CLI 지원만으로 Paseo 요구를 완료하지 않는다.

## Task 2: 패키지 준비·진단의 Python 관리 계층

**Files:** Create `kit/mycodex_lib/compression.py`, `kit/integrations/billion-context/{package.json,package-lock.json,policy.json,README.md,THIRD_PARTY_NOTICES.md}`, `tests/test_compression.py`; Modify `kit/mycodex.py`.

**Interfaces:** `inspect_compression(target: Path, runtime_root: Path, paseo_home: Path) -> dict`; `prepare_runtime(target: Path, runtime_root: Path, *, apply: bool = False) -> dict`. 반환은 JSON 직렬화 가능하고 비밀 없는 경로·버전·진단 코드·상태를 담는다. `runtime_root`는 Task 1의 확인된 호스트 경로이며 테스트는 임시 경로를 주입한다.

- [x] `test_doctor_distinguishes_install_from_observed_compression`, `test_prepare_dry_run_has_no_writes_or_network`, `test_prepare_missing_node_preserves_project`, `test_prepare_conflict_does_not_overwrite`, `test_failed_install_is_not_ready`를 먼저 작성하고 실패를 확인한다. 일반 init/validate에 Node가 필요하지 않음도 assert한다.
- [x] 위 인터페이스와 `compression doctor/prepare` CLI를 구현한다. 경로 검증·재파싱·원자적 생성은 기존 도구 패턴을 사용한다. argv 배열을 사용하고 shell 문자열로 연결하지 않는다. 설치는 고정 버전·lock을 사용하는 `npm ci`이며 global install이나 `npx latest`를 쓰지 않는다.
- [x] `policy.json`에 자동 변경 3개 스위치를 false로 고정한다. 외부 요약 서버와 본문 덤프를 기본 사용하지 않는다. runtime 소유권에는 패키지 버전·lock/bridge fingerprint·관리 경로만 기록하고 비밀은 담지 않는다.
- [x] `python -X utf8 -B -m unittest discover -s tests -p test_compression.py -v`를 실행한다. 모든 assert가 통과하고 미설치 상태의 `doctor`가 압축 성공을 주장하지 않아야 한다.

## Task 3: Paseo app-server를 위한 bridge

**Files:** Create `kit/integrations/billion-context/paseo-bridge.mjs`, `tests/integration/test_paseo_bili_bridge.py`; Modify `compression.py`의 runtime 준비 부분.

**Interfaces:** bridge는 Paseo의 `command` 뒤에 붙은 모든 argv와 stdin을 Task 1에서 검증한 Bili→Codex 경로로 전달한다. app-server stdout을 바꾸지 않으며 stderr 진단만 추가한다. `BILI_CLIENT_BIN`, 전용 정책·세션 경로를 child 환경에만 적용한다. provider command에는 프로젝트 checkout 경로가 아닌 안정적인 runtime 경로를 넣는다.

- [x] Windows 한글·공백·따옴표·빈 인자·`&`·`%`·TOML 옵션, stdout 프로토콜, stdin EOF·중단·자식 실패·부모 종료·중복 실행을 재현하는 검사를 먼저 작성하고 실패를 확인한다.
- [x] Node 표준 라이브러리로 bridge를 구현한다. `shell: false`와 직접 spawn을 사용하고 프로젝트 CWD/RPC를 바꾸지 않는다. 실제 모델 트래픽을 받지 않는 daemon으로 연결되면 정상으로 표시하지 않는다.
- [x] 다른 chat·기존 Bili 인스턴스를 소유권 확인 없이 재사용·중단하지 않는다. 기존 proxy/CA를 없애서 동작시키지 않는다. 스키마·기능 미지원은 명시적 진단으로 중단한다.
- [x] `python -X utf8 -B -m unittest discover -s tests/integration -p test_paseo_bili_bridge.py -v`와 Task 1의 실제 프로토콜 검사를 실행한다. 프로토콜·인자·lifecycle 검사가 모두 통과해야 한다.

## Task 4: Paseo 연결·해제·스킬·설치 자산에 연결

**Files:** Modify `compression.py`, `kit/mycodex.py`, `kit/mycodex_lib/model.py`, 필요 시 `install.py`·`validation.py`; Create `kit/skills/context-compression/{SKILL.md,agents/openai.yaml}`, `tests/test_compression_paseo.py`; Modify `kit/skills/project-init/SKILL.md`, `kit/skills/session-handoff/SKILL.md`의 관련 안내만.

**Interfaces:** `plan_paseo_provider(paseo_home: Path, runtime_root: Path, *, enabled: bool) -> dict`; `apply_paseo_provider(plan: dict) -> dict`; `export_compression_summary(runtime_root: Path, session_id: str, *, apply: bool = False) -> dict`. CLI는 설계 표의 `paseo-enable`, `paseo-disable`, `export`에 대응한다. plan의 이전 내용 비교는 메모리에서만 수행하고 CLI 출력에서 제외한다.

- [x] 합성 설정으로 `test_enable_preserves_unrelated_settings`, `test_existing_unowned_provider_conflicts`, `test_concurrent_edit_preserved`, `test_disable_removes_only_owned_unchanged_entry`, `test_reload_failure_is_saved_not_active`를 먼저 작성하고 실패를 확인한다. 비밀 모양의 sentinel은 stdout·오류·백업·기록에 없어야 한다.
- [x] `codex-bili`만 추가·제거하는 계획/적용과 실제 지원되는 Paseo reload를 연결한다. 설정 값 보존을 검증하며, 전체 설정 백업·기존 chat 강제 이동은 하지 않는다.
- [x] 요약 export는 별도 runtime에 고유 파일로 저장하고 경로만 반환한다. 원문 export는 첫 버전에서 제공하지 않는다. 자동 Handoff 작성·index 등록과 연결하지 않는다. `test_export_does_not_overwrite_or_update_index`와 경로 이탈 검사를 추가한다.
- [x] 새 스킬은 `allow_implicit_invocation: false`로 배포한다. project-init은 선택 기능의 비활성 상태 때문에 ready를 막지 않는다. session-handoff는 압축 요약의 사실을 현재 원본과 검증해야 함을 명시한다. AGENTS/config/Superpowers는 바꾸지 않는다.
- [x] 새 자산을 허용 목록·manifest·패키징에 연결한다. 기본 검증에서는 Node나 외부 패키지를 실행하지 않는다. 테스트는 자산 수를 고정 숫자로 추정하지 않는다.
- [x] 해당 단위 검사와 `python -X utf8 -B -m unittest discover -s tests -v`를 실행한다. 이 단계까지의 mock/프로세스 검사는 실제 모델의 절차 준수 증거와 구분한다.

## Task 5: 실제 Paseo chat에서 압축 전후 충돌 검증

**Files:** Create `tests/integration/test_compression_workflow.py`의 합성 fixture·증거 점검; Task 1의 실제 검증 문서에 결과 추가. 스킬과 실제 앱 동작 검증은 해당 결과 문서에만 기록한다.

**Interfaces:** 설계의 검증표 각 행에 `{case, versions, mode: A|B|C, executed_command_or_action, expected_invariants, observed_evidence, result: pass|fail|not_run}`를 채운다. A=기존 Codex, B=압축 제공자/압축 전, C=압축 제공자/압축 후. 실제 대화·개인 코드·인증은 산출물에 넣지 않는다.

- [x] 동일한 합성 프로젝트·요구사항·승인된 작은 spec/plan을 준비한다. 금지 파일, 원본 변경, 여러 chat 구분용 가짜 표식과 기대 결과를 코드/문서에서 먼저 정의한다. 현실의 위험 동작은 하지 않고 fake 도구로 승인 보존을 시험한다.
- [ ] 먼저 A에서 Superpowers, JIT, project-init, session-handoff, human-html, 필요한 Codex 도구가 동작하는지 확인한다. UI 스킬 목록과 실제 런타임 스킬 인식은 따로 기록한다. 기존 문제를 신규 회귀와 구분한다.
- [x] B와 C에서 같은 시나리오를 실행한다. 압축 후 spec/plan의 단계와 사용자 제약 유지, 바뀐 원본 재확인, 실제 테스트 실행을 확인한다. 말로 스킬 이름을 언급한 것만으로 준수를 인정하지 않는다.
- [x] 인계 후 프록시 없는 새 Paseo chat에서 작업을 이어간다. HTML 산출물은 일반 검색과 index/인계 원본에서 제외되는지 확인한다. 기존 규칙과 원본으로 복구되어야 한다.
- [ ] 두 chat·다른 프로젝트/worktree·승인 검토 agent를 병행한다. 모델창 추정·thread mapping·검색·압축 상태가 섞이지 않는지 확인한다. 요청한 역할에서 관찰하지 못한 검사는 not_run이다.
- [ ] 프록시 중단·포트 충돌·Paseo 재연결·기존 Codex 동시 사용·해제 후 새 chat을 시험한다. 기본 compaction과 Bili가 함께 발생하는 경우도 포함한다. 무압축 우회나 도구 목록 손실을 성공으로 처리하지 않는다.
- [x] 수집 가능한 실제 입력 토큰/크기·추가 지연·압축 횟수를 기록한다. 합성 fixture 수치와 사용자 실제 사용량은 구분한다. 광고 절감률을 합격 조건으로 사용하지 않는다.
- [ ] **관문:** 설계 검증표의 필수 항목 모두 pass여야 지원 완료다. 미검증 항목이 남으면 실험 기능 상태를 유지하고 Task 6에서 정식 지원으로 표시하지 않는다.


## Task 6: 0.3.0 자체 적용·배포와 회귀

**Files:** Modify `kit/mycodex_lib/model.py`, `README.md`, `CHANGELOG.md`, `tools/build_release.py`, `tests/test_release.py`; 관리 자산만 `.mycodex/`·`.agents/skills/context-compression/`에 동기화; Create `dist/MyCodexSetting-0.3.0/`와 ZIP은 검증 후에만. `.context/index.md`에 실제 근거를 연결한다.

**Interfaces:** 지원표는 Task 5의 검증 조합과 동일하다. ZIP은 허용 목록의 연동 코드·정책·lock·출처 고지만 포함한다. 기존 0.2.0 대상의 재설치는 충돌로 중단하고 보존한다.

- [x] CRLF checkout 후 기존 동일 배포 폴더를 보존하며 재생성하는 회귀 검사를 먼저 추가한다. LF 정규화 비교를 사용하되 실제 내용 변경·추가 파일·symlink/junction·다른 ZIP 바이트는 계속 충돌이어야 한다. 기존 0.2.0 산출물을 덮어쓰지 않는다.
- [x] 배포 README에 초회 준비→Paseo 제공자 선택→평소 chat→진단→인계 후 해제 흐름, 지원 조합·미검증 범위·라이선스 고지를 반영한다. 새 기능이 비활성이어도 기존 기능을 사용할 수 있음을 설명한다.
- [x] 버전·manifest·자체 설치본을 동기화한다. 활성 Codex 설정과 기존 스킬·사용자 문서는 보존한다. 기존 0.2.0 프로젝트용 자동 migration은 추가하지 않는다.
- [x] `python -X utf8 -B -m unittest discover -s tests -v`, opt-in 실제 통합 검사, `python -X utf8 -B .mycodex/mycodex.py validate --target . --strict --json`, `git diff --check`를 실행한다. skip과 live pass를 따로 보고한다.
- [x] `python -X utf8 -B tools/build_release.py --output <새 임시 배포 경로>`로 ZIP 단독 설치·재생성·기존 버전 보존을 확인한다. `<새 임시 배포 경로>`는 실행 시 실제 생성한 경로로 대체하고 기록한다. npm 설치물·세션·CA·인증·로그가 없는지 목록과 해시로 확인한다.
- [x] Node 없는 환경에서 신규 기본 설치·검증을 확인하고, Node가 준비된 호스트에서 배포 ZIP만으로 압축 준비와 Paseo 연결을 재검증한다. 개발 checkout 경로가 provider에 남지 않아야 한다.
- [x] 결과가 모두 충족된 경우에만 새 0.3.0 산출물을 만들고 현재 포인터를 정리한다. 미충족이면 실험 상태와 남은 항목을 정확히 남긴다. 커밋·push·외부 게시를 자동 실행하지 않는다.

## 계획 작성 시점의 검증 기록

- 실행: 현재 index/CLI/설치·검증·배포 코드 대조, Git 기준 확인, 공개 upstream 태그와 Paseo 실행 구조 확인, 로컬 프로세스·Paseo 설정의 키 구조·Codex 특정 실행 파일 버전 조회.
- 설계 builder check: 별도 읽기 전용 검토자 결과 `nothing important left`. 런타임 검증이나 사용자 승인을 뜻하지 않는다.
- 미실행: 이 계획의 모든 Task, 새 패키지 설치·provider 편집·reload·프록시·실제 모델 요청·압축·통합 테스트·새 배포. 기존 28개 테스트 결과를 새 기능의 통과로 재사용하지 않는다.

## 실행 결과

[실제 검증 기록](../validation/2026-11-12-billion-context-paseo.md)을 따른다. 0.3.0에서는 Task 5 전체 호환성 관문 미충족으로 실험 상태를 유지했다. 위의 계획 작성 시점 미실행 목록은 과거 초안의 기록이다.

## 0.3.1 후속 작업: 정식 기능 승격과 README 정리

사용자 요청: billion-context를 정식 기능으로 승격하고 과도하게 길어진 README를 목적에 맞게 정리한다. 이 요청은 0.3.0 계획의 실험 상태 유지 결정을 대체한다. 기존 연결 방식·기본 비활성·호환성 미검증 기록은 유지한다.

- [x] README를 소개·빠른 시작·주요 스킬·상세 문서 링크로 축약한다. 일반 상세는 `docs/usage.md`, 압축 상세는 기존 연동 README로 모은다.
- [x] CLI 제공 상태와 관리 스킬을 정식 선택 기능으로 맞춘다. 현재 호스트의 `unknown` 관찰 항목은 성공으로 바꾸지 않는다.
- [x] 버전을 0.3.1로 올리고 상세 사용 안내를 배포 허용 목록에 추가한다. 기존 0.3.0 산출물은 보존한다.
- [x] 자동 검사, 관리 자산 동기화·strict 검증, 새 ZIP 생성·문서 링크·기존 파일 보존을 확인하고 실제 결과를 기록한다. 전체 52 tests OK, strict findings 없음, 33개 배포 파일 일치, 상대 링크 27개 확인, 기존 보호 파일 139개 동일.

이번 작업은 문서·제공 상태·배포 구성 정리다. 새로운 live 모델/Paseo 시험이나 기존 미검증 항목의 통과를 주장하지 않는다.
