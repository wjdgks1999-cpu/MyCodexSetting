# MyCodexSetting 상세 사용 안내

[빠른 시작](../README.md) 이후에 필요한 파일 역할, 설치·인계·설정과 문제 해결 안내입니다. 문맥 압축의 명령과 호환 범위는 [billion-context 사용 안내](../kit/integrations/billion-context/README.md)에 있습니다.

## 설치되는 파일과 원본

| 대상 프로젝트의 경로 | 역할·갱신 시점 |
|---|---|
| `AGENTS.md` | 짧은 작업 지침과 문서 탐색 안내. 확인된 명령·작업 규칙이 바뀔 때 갱신 |
| `.codex/config.toml` | 최초 설치 시 없을 때 생성하는 Codex 기본 설정. 이후 사용자가 관리 |
| `.context/index.md` | 원본 문서의 경로·용도와 설정 상태. 초기화·문서 이동·작업 전환 시 갱신 |
| 기존 PRD/GDD·설계·운영 문서 | 요구사항·설계·사실의 원본. 해당 내용이 바뀔 때 갱신 |
| `.context/decisions.md` | 기존 원본에 둘 곳이 없는 확인된 장기 결정. 필요할 때 처음 생성 |
| `.context/handoffs/*.md` | 작성 시점의 상태·근거·다음 행동. 명시적 인계 요청 시 생성 |
| `.mycodex/` | 실행 도구·정책·템플릿·설치 목록. 설치 버전 기준으로 관리 |
| `.agents/skills/` | `project-init`, `session-handoff`, `human-html`, `context-compression` 스킬 |
| `.human-docs/` | 명시적인 요청으로 만드는 사람용 HTML. 일반 개발 탐색에서 제외 |

`project.md`와 빈 지식 문서는 기본 생성하지 않습니다. 기존 원본을 우선하며 필요한 주제별 문서만 추가합니다. Superpowers의 설계·계획·진행 원장을 별도 진행 문서로 복제하지 않습니다.

배포본의 `README.md`, `CHANGELOG.md`, `docs/usage.md`는 설치 대상에 복사하지 않습니다. 대상 프로젝트의 기존 README는 보존합니다.

## 설치와 초기 조사

배포 폴더에서 실행합니다. 공백·한글이 있는 경로는 따옴표로 감쌉니다.

```powershell
python kit/mycodex.py init --target "C:/work/나의 프로젝트" --requirements PRD.md
python kit/mycodex.py init --target "C:/work/나의 프로젝트" --requirements PRD.md --apply
```

기본 실행은 파일을 쓰지 않는 dry-run이며 `--apply`가 설치합니다. 요구사항이 여러 개면 `--requirements docs/GDD.md`처럼 옵션을 반복합니다. 요구사항 경로는 대상 프로젝트 루트 기준입니다.

새 설치는 `AGENTS.md`와 `.context/index.md`를 만들고 인덱스를 `needs-review`로 둡니다. 기존 AGENTS/index는 보존합니다. Git 저장소가 없어도 설치할 수 있으며 Git을 대신 초기화하지 않습니다. `.codex/config.toml`도 없을 때만 생성합니다.

대상 프로젝트를 Codex에서 열고 `$project-init`을 명시적으로 호출합니다. 스킬은 기존 지침·요구사항·코드·문서와 Superpowers의 실제 사용 가능 여부를 확인하고 필요한 원본을 인덱스에 연결합니다. 내용이 있는 `AGENTS.override.md`가 있으면 그 파일에 탐색 규칙을 반영합니다. 코드가 없으면 기술 스택과 빌드·테스트 명령을 추정하지 않습니다.

조사와 구조 검증 후 인덱스는 `ready`가 됩니다. 이는 세팅 조사 완료이며 제품 개발 완료나 애플리케이션 테스트 통과가 아닙니다. 스킬이 목록에 없으면 새 세션에서 `.agents/skills/` 설치 경로와 검색 여부를 확인하세요.

## 구조 검증

대상 프로젝트 루트에서 실행합니다.

```powershell
python .mycodex/mycodex.py validate --target .
python .mycodex/mycodex.py validate --target . --strict --json
```

| 종료 코드 | 의미 |
|---|---|
| 0 | 검증 오류 없음. 기본 모드에서는 경고가 있을 수 있음 |
| 1 | 구조·경로·설치 충돌 등의 오류. strict에서는 경고도 포함 |
| 2 | 잘못된 CLI 인자 또는 I/O로 실행 불가 |

검증은 읽기 전용입니다. 설치 파일 해시, 명시적 스킬 정책, 인덱스와 등록된 경로, 필수 Handoff 항목을 확인합니다. 문서 본문 대신 진단 코드·경로·조치를 출력합니다. 사라진 임시 원장은 경고로 보고하며 완료를 추정하지 않습니다.

구조 검증이 통과해도 내용과 최신성은 현재 원본과 대조해야 합니다. 애플리케이션 동작은 해당 프로젝트에서 별도로 검증합니다.

## 개발·인계·재개

제품 설계·계획·구현은 준비된 Superpowers 절차로 진행합니다. Git 기반 구현·복구를 사용하기 전에 해당 개발 작업에서 Git을 준비합니다. 문서 생성·이동과 작업 전환 시 인덱스의 해당 경로를 갱신합니다.

```text
$session-handoff 현재 작업과 검증 결과를 정리하고 다음 세션에서 이어갈 문서를 만들어 주세요.
```

스킬은 지속적인 지식을 적절한 원본에 반영하고, 날짜가 있는 Handoff와 최신 포인터를 기록합니다. 일반 상태 질문이나 종료 인사만으로 실행하지 않습니다. 기록 실패 시 남은 초안·스냅샷·장기 지식 반영 상태를 구분해 보고합니다.

새 세션에서는 대상 프로젝트를 열고 이어서 할 작업을 요청합니다. Codex는 AGENTS → index → 관련 Handoff·계획·원본을 찾아 현재 파일/Git 상태와 대조합니다. 모든 과거 세션 문서를 한꺼번에 읽지 않으며, 과거 테스트 통과를 현재 변경 이후의 결과로 재사용하지 않습니다.

## 사람용 HTML

무엇을 문서로 만들지 직접 적어 호출합니다.

```text
$human-html 현재 개발하고 있는 앱 서비스의 구조를 HTML 문서로 정리해 주세요.
```

스킬은 필요한 원본만 조사해 설명·표·도식이 있는 독립 HTML을 만듭니다. 주제가 없으면 먼저 질문합니다. CSS와 도식을 내부에 넣어 브라우저에서 오프라인으로 읽을 수 있으며 파일 링크와 실제 검증 결과를 보고합니다.

문서는 처음 생성할 때 준비하는 `.human-docs/`에 고유한 이름으로 저장합니다. 내부 `.gitignore`와 `.ignore`는 Git과 ignore 규칙을 따르는 검색에서 본문을 제외합니다. Git이 없는 폴더의 ripgrep에도 `.ignore`가 적용됩니다. 루트 제외 파일은 변경하지 않으며 기존 맞춤 제외 파일이 있으면 보존하고 충돌을 보고합니다.

일반 개발에서는 이 폴더를 읽기·검색 대상과 인덱스·인계의 원본에서 제외합니다. `--no-ignore` 검색에도 `-g '!.human-docs/**'`를 지정합니다. 명시적인 HTML 생성·수정·검증 때는 해당 파일에 접근할 수 있습니다. 이 규칙은 파일 접근 차단이나 생성 시 토큰 사용량 0을 보장하지 않습니다.

저장 도구는 UTF-8 stdin을 받아 경로만 반환합니다. 기존 산출물의 기본 HTML 구조는 다음 명령으로 확인합니다. 내용의 사실성과 화면 가독성은 별도 확인 대상입니다.

```powershell
python .agents/skills/human-html/scripts/save_html.py --target . --check .human-docs/생성된-파일명.html
```

## 설정과 기존 파일 보존

Codex 기본 설정의 원본은 `kit/templates/config.toml`입니다. 모델·추론 강도·검색·권한·기억·에이전트 기본값을 담고 있으며 대상에 `.codex/config.toml`이 없을 때만 생성합니다. 설치 후 실제 설정을 바꿔도 재설치가 덮어쓰거나 구조 검증이 자산 충돌로 보고하지 않습니다. 무결성 검증 대상인 `.mycodex/templates/config.toml`과 구분합니다.

사용자 전역 설정·기억은 변경하지 않습니다. 배포 기본값을 바꾸려면 `kit/templates/config.toml`을 수정합니다. 이후 설치 때마다 이 저장소의 활성 설정을 읽어 복사하지 않습니다. 프로젝트 설정 파일 생성과 현재 세션의 설정 적용은 구분해야 합니다. 로드 조건은 [Codex 설정 공식 문서](https://learn.chatgpt.com/docs/config-file/config-basic)를 참고하세요. 비밀 파일과 원문 전문은 프로젝트 기억에 복사하지 않습니다.

같은 입력의 설치 재실행은 동일 자산을 건너뜁니다. 다른 배포 자산이 있으면 전체 사전 검사에서 멈추며 강제 교체·자동 업데이트 옵션은 없습니다. 다른 버전으로의 이전은 별도 검토가 필요합니다. 새 배포본을 받아도 기존 프로젝트의 AGENTS와 인덱스는 자동 갱신되지 않습니다.

## 설치·인계 문제 해결

- **설치 중 I/O 실패:** 부분 설치가 남을 수 있습니다. 원인을 해결한 뒤 같은 원본 kit으로 dry-run을 다시 확인합니다.
- **Handoff 포인터 교체 실패:** 연결되지 않은 스냅샷의 보고된 경로를 확인합니다. 기존 이력이나 사용자 파일을 일괄 삭제하지 않습니다.
- **인덱스 잠금 잔류:** `.context/.index.lock`은 다른 기록 작업이 끝났는지 확인한 후 처리합니다. 잠금은 도구 간 동시 기록을 조정하지만 외부 편집기의 모든 경쟁까지 보장하지는 않습니다.
- **압축 기능 미연결:** 기본 문서 탐색·인계는 그대로 사용할 수 있습니다. 기본 `init`/`validate`에는 Node나 네트워크가 필요 없습니다. 토큰 절감률은 보장하지 않습니다.

## 참고 문서

- [Codex AGENTS.md 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex Skills 공식 문서](https://learn.chatgpt.com/docs/build-skills)
