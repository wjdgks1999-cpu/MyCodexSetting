# Codex CLI 문맥 압축 확장

사용자는 CLI만 추가하고 필요한 검증 후 MyCodexSetting에 반영하도록 요청했다. 앱은 범위 밖이다. 아래 구현 선택은 이 범위에 따라 정하며 기존 Paseo 검증을 CLI 검증으로 대신하지 않는다.

## 방식과 선택

기존 고정 runtime과 Python 관리 CLI를 재사용해 `compression codex --target . --apply -- <Codex 인자>`로 실행한다. `--apply`가 없으면 비밀일 수 있는 인자 본문을 출력하지 않는 dry-run이다. 일반 `codex` 실행은 그대로 둔다. 전역 설치·alias·프로필 자동 변경은 하지 않는다.

Paseo bridge는 JSON stdio용이며 app-server만 허용하므로 대화형 터미널에 재사용하지 않는다. 별도 Node bridge를 복제하기보다 Python이 검증된 upstream 실행 파일을 shell 없이 직접 띄우고 터미널 입출력을 상속한다. 실행 준비·환경 정책은 기존 bridge와 일치시킨다.

## 계약

- Python 3.11+ 표준 라이브러리, Node 20+, billion-context 0.1.213 고정. 현재 측정 환경의 Codex 0.167.0을 우선 검증한다.
- `doctor --client codex`는 Paseo 설치·config 없이 진단한다. 제공 상태와 실제 관찰 unknown을 구분한다.
- CLI 실행은 현재 kit·runtime·upstream 해시와 고정 실행 파일을 확인하고, 자식에만 BILI/ACP 정책을 적용한다. 기존 proxy/CA를 제거하지 않는다. 별도 CODEX_CA_CERTIFICATE는 기존과 같이 미지원으로 중단한다.
- 인증은 기존 링크 공유 방식을 유지한다. 링크 사전 검사 실패 시 upstream의 인증 복사 fallback으로 진행하지 않는다. 인증 내용을 읽거나 산출물에 복사하지 않는다.
- 원격 서버 연결은 자식 환경으로 요청 경유를 보장할 수 없어 거절한다. upstream의 no-daemon 경로를 사용한다. 대화형·resume·exec를 우선 검증하고, 앱·서버·기타 관리 명령의 지원으로 일반화하지 않는다.
- stdout/stderr/stdin과 종료 코드를 보존하고 사용자 인자를 shell 문자열로 조합하지 않는다. Ctrl+C와 정상 종료를 실제 터미널에서 확인한다.
- 기존 AGENTS·활성 config·Superpowers·이전 배포본을 보존한다. 커밋·push·외부 게시·사용자 Paseo 활성화는 하지 않는다.

## 검증과 완료 조건

자동 검사: dry-run 무실행/무기록, 파서 인자 경계, Unicode·공백·따옴표·특수문자 전달, cwd·환경·stdio·종료 코드, 기존 runtime 충돌, 원격 연결 거절, CLI 단독 doctor, 기본 Node 불필요, 기존 Paseo bridge 회귀.

실측: 실제 터미널의 시작·응답·종료, 직접/압축 CLI 비교, 모델 요청 경유, 충분히 오래된 합성 이력의 압축·검색·복원, 세션 재개, 작은 개발·현재 원본 재확인·인계·일반 Codex 복귀. 전용 합성 fixture와 소유 프로세스만 사용한다. 실제 압축이 0블록이면 성공으로 세지 않는다. 실패·미검증은 그대로 기록한다.

0.4.0 배포에 CLI 사용 안내를 추가한다. README는 짧은 환경 선택 안내만 유지하고 상세는 기존 연동 README에 둔다. 자체 관리 자산·manifest·ZIP을 동기화하고 독립 ZIP 설치와 링크를 확인한다.
