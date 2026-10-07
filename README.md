# Codex 설정과 스킬

## 파일 구성

```text
.
├── README.md
├── .codex/
│   └── config.toml
└── .agents/
    └── skills/
        ├── agents-md/
        │   ├── SKILL.md
        │   ├── SPEC.md
        │   ├── SOURCES.md
        │   └── agents/openai.yaml
        └── close-coding-session/
            ├── SKILL.md
            └── agents/openai.yaml
```

## config.toml 설정

설정 파일: [`.codex/config.toml`](.codex/config.toml)

아래 표는 현재 파일에 작성된 19개 설정을 설명합니다. 설명과 공식 문서의 확인 기준일은 **2026년 10월 7일**입니다.

프로젝트의 `.codex/config.toml`은 해당 프로젝트에 적용되는 설정입니다. 여러 프로젝트에서 사용할 개인 기본값은 일반적으로 사용자 폴더의 `~/.codex/config.toml`에 둡니다. Windows의 기본 경로는 `%USERPROFILE%\.codex\config.toml`입니다.

프로젝트 설정은 신뢰된 프로젝트에서 로드됩니다. 실행 옵션과 관리 정책 등에 따라 실제 적용값은 달라질 수 있습니다. [설정 적용 범위와 우선순위](https://learn.chatgpt.com/docs/config-file/config-basic)

### 모델과 추론

| 설정 항목 | 현재 값 | 의미 | 적용 시 참고사항 |
|---|---|---|---|
| `model` | `"gpt-6.1-sol"` | 기본으로 사용할 모델을 지정합니다. | 계정과 클라이언트에서 해당 모델을 사용할 수 있어야 합니다. |
| `model_reasoning_effort` | `"xhigh"` | 일반 작업의 추론 강도를 높게 설정합니다. | 추론 강도가 높으면 처리 시간과 사용량이 늘어날 수 있습니다. |
| `plan_mode_reasoning_effort` | `"xhigh"` | 계획 모드의 추론 강도를 지정합니다. | 생략하면 계획 모드의 기본 프리셋을 사용합니다. |

컨텍스트 크기와 자동 압축 기준은 직접 지정하지 않고 모델의 기본값을 사용합니다. [모델 안내](https://learn.chatgpt.com/docs/models), [추론·압축 설정](https://learn.chatgpt.com/docs/config-file/config-reference)

### 검색과 작업 권한

| 설정 항목 | 현재 값 | 의미 | 적용 시 참고사항 |
|---|---|---|---|
| `web_search` | `"live"` | 웹 검색을 실시간 모드로 설정합니다. | 검색이 필요한 작업에서 사용하며, 모든 질문에 검색을 강제하지는 않습니다. |
| `sandbox_mode` | `"workspace-write"` | 작업 폴더와 허용된 경로에서 파일 수정과 명령 실행을 허용합니다. | 추가 경로와 보호 경로에는 별도의 접근 제한이 적용됩니다. |
| `approval_policy` | `"on-request"` | 필요할 때 권한 확대 등의 승인을 요청할 수 있도록 합니다. | 허용 범위 안의 일반 작업은 계속 진행할 수 있습니다. |
| `approvals_reviewer` | `"auto_review"` | 해당 승인 요청을 별도의 검토 에이전트가 심사합니다. | 요청을 승인하거나 거절할 수 있으며, 샌드박스 제한은 유지됩니다. |
| `windows.sandbox` | `"elevated"` | 전용 낮은 권한 사용자와 Windows 권한 경계를 사용하는 샌드박스 방식입니다. | 초기 설정에 관리자 승인이 필요할 수 있습니다. |
| `sandbox_workspace_write.network_access` | `true` | 샌드박스 안에서 실행하는 명령의 외부 네트워크 접근을 허용합니다. | 패키지 다운로드 등의 명령에 적용됩니다. 웹 검색 모드와는 별도 설정입니다. |

표의 `windows.sandbox`는 `[windows]` 섹션의 `sandbox`를 뜻합니다. 다른 점 표기 항목도 섹션과 키를 합쳐 표시했습니다. [설정 레퍼런스](https://learn.chatgpt.com/docs/config-file/config-reference), [샌드박스](https://learn.chatgpt.com/docs/sandboxing), [자동 승인 검토](https://learn.chatgpt.com/docs/sandboxing/auto-review), [Windows 샌드박스](https://learn.chatgpt.com/docs/windows/windows-sandbox)

### 기능과 메모리

| 설정 항목 | 현재 값 | 의미 | 적용 시 참고사항 |
|---|---|---|---|
| `features.hooks` | `true` | 세션 시작이나 도구 실행 전후에 동작하는 훅 기능을 활성화합니다. | 실행할 훅은 별도로 정의해야 하며, 사용자·프로젝트 훅에는 신뢰 확인이 필요합니다. |
| `features.memories` | `true` | 이전 작업 정보를 기억하고 재사용하는 메모리 기능을 활성화합니다. | 생성과 사용 조건은 아래 `memories` 설정에서 지정합니다. |
| `features.multi_agent` | `true` | 서브에이전트 협업 도구를 활성화합니다. | 실제 협업 방식은 작업 요청과 지침에 따릅니다. |
| `memories.generate_memories` | `true` | 새 대화를 메모리 생성 입력으로 저장할 수 있도록 허용합니다. | 모든 대화가 즉시 메모리로 생성된다는 뜻은 아닙니다. |
| `memories.use_memories` | `true` | 기존 메모리를 이후 세션에 제공해 참고하도록 합니다. | 기존 메모리의 최신성과 적용 범위는 작업 중 확인해야 합니다. |
| `memories.disable_on_external_context` | `false` | 웹 검색·MCP 등 외부 문맥을 사용한 대화도 메모리 생성 대상에서 제외하지 않습니다. | `true`로 바꾸면 해당 대화를 메모리 생성 대상에서 제외합니다. |

`features.multi_agent`의 현재 기본값은 `true`입니다. `memories.generate_memories`, `memories.use_memories`, `memories.disable_on_external_context`도 현재 기본값과 같은 값을 명시하고 있습니다. [훅 안내](https://learn.chatgpt.com/docs/hooks), [메모리 안내](https://learn.chatgpt.com/docs/customization/memories), [기능 설정](https://learn.chatgpt.com/docs/config-file/config-reference)

### 서브에이전트

| 설정 항목 | 현재 값 | 의미 | 적용 시 참고사항 |
|---|---|---|---|
| `agents.enabled` | `true` | 멀티에이전트 도구 사용을 허용합니다. | 현재 기본값도 `true`입니다. |
| `agents.max_concurrent_threads_per_session` | `3` | 동시에 열어 둘 수 있는 서브에이전트 스레드의 상한을 지정합니다. | 주 에이전트는 제외됩니다. 실행 환경의 상한이 더 낮으면 그 제한을 따릅니다. |
| `agents.default_subagent_model` | `"gpt-6.1-sol"` | 생성하는 서브에이전트의 기본 모델을 지정합니다. | 생성 시 명시한 모델과 개별 에이전트 설정이 우선할 수 있습니다. |
| `agents.default_subagent_reasoning_effort` | `"high"` | 생성하는 서브에이전트의 기본 추론 강도를 지정합니다. | 주 에이전트의 `xhigh`와 별도로 적용합니다. 생성 시 명시한 값과 개별 설정이 우선할 수 있습니다. |

스레드 상한은 협업이 실행될 때 적용됩니다. 이 값 자체가 서브에이전트를 생성하는 지침은 아닙니다. [서브에이전트 설정과 동작](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## 스킬 설명과 사용 방법

현재 두 스킬 모두 `agents/openai.yaml`에 `allow_implicit_invocation: false`가 지정되어 있습니다. 사용할 때 스킬 이름을 명시적으로 호출합니다.

| 스킬 | 목적 | 사용하는 시점 | 주요 결과 |
|---|---|---|---|
| [`agents-md`](.agents/skills/agents-md/SKILL.md) | 프로젝트의 `AGENTS.md`를 간결하고 정확하게 작성·관리합니다. | 프로젝트 초기 설정, 작업 규칙 변경, 기존 지침 정리 시 | 실제 명령과 문서 경로를 확인한 작업 지침 |
| [`close-coding-session`](.agents/skills/close-coding-session/SKILL.md) | 큰 작업을 검증하고 필요한 지식과 재개 상태를 보존합니다. | 큰 작업을 마무리하거나 새 대화로 넘기기로 결정한 시점 | 검증 결과, 필요한 문서 갱신, 최소 인계 내용, 새 세션 시작 프롬프트 |

### agents-md

원본: [`getsentry/skills`의 `agents-md`](https://github.com/getsentry/skills/tree/main/skills/agents-md)

실제 저장소를 조사한 뒤 에이전트가 따라야 할 명령과 중요한 규칙을 정리하는 스킬입니다.

- 패키지 관리 도구, 테스트·린트 명령, 코드 관례, 기존 문서를 확인합니다.
- 저장소 전체 지침은 루트 `AGENTS.md`에 두고, 다른 규칙이 필요한 하위 폴더에만 추가 지침을 둡니다.
- 기존 문서 내용을 복사하기보다 정확한 파일 경로로 연결합니다.
- 생성하는 지침은 60줄 미만을 목표로 하고 100줄을 넘기지 않습니다.
- Claude 호환이 필요하면 `CLAUDE.md`를 `AGENTS.md`의 심볼릭 링크로 구성합니다.

일반 문서 작성이나 코드 리뷰보다, 프로젝트의 에이전트 작업 지침을 만들거나 정리할 때 사용합니다.

**사용 전 준비**

이 스킬은 특정 문서를 필수 입력으로 지정하지 않습니다. 대상 프로젝트의 실제 파일과 명령을 조사해 지침을 작성합니다.

| 구분 | 준비할 내용 | 필요한 이유 |
|---|---|---|
| 기본 조건 | 대상 프로젝트 경로와 파일 읽기·쓰기 권한 | 실제 구성을 조사하고 해당 프로젝트에 지침 파일을 작성합니다. |
| 기본 조건 | 지침을 새로 작성할지, 기존 지침을 정리할지에 대한 요청 | 작성 범위와 작업 목적을 정합니다. |
| 있으면 활용 | 기존 `AGENTS.md`와 적용되는 작업 규칙 | 기존 규칙을 보존하고 중복되거나 오래된 내용을 정리합니다. |
| 있으면 활용 | 패키지 설정·잠금 파일, 빌드·테스트 설정, CI 워크플로 | 실제 사용할 수 있는 명령과 개발 도구를 확인합니다. |
| 있으면 활용 | README, 기여 안내, 설계·요구사항·보안·배포 문서 | 지침에 연결할 정확한 참고 경로와 프로젝트 제약을 확인합니다. |
| 작업에 따라 준비 | 문서에 아직 없는 사용자 규칙, 하위 폴더별 차이, Claude 호환 필요 여부 | 파일만으로 확인할 수 없는 운영 기준을 반영합니다. |

준비된 파일이 적으면 확인 가능한 내용으로 시작합니다. 존재하지 않는 명령이나 문서 경로는 추정해 추가하지 않습니다.

**호출 예시**

```text
$agents-md 이 프로젝트를 조사하고, 실제 실행 명령과 참고 문서 경로를 포함한 AGENTS.md를 작성해주세요.
```

```text
$agents-md 현재 AGENTS.md에서 오래된 명령과 중복 내용을 확인하고, 기존 문서를 참조하도록 정리해주세요.
```

스킬의 작성 계약은 [`SPEC.md`](.agents/skills/agents-md/SPEC.md), 출처와 유지관리 기록은 [`SOURCES.md`](.agents/skills/agents-md/SOURCES.md), 호출 설정은 [`agents/openai.yaml`](.agents/skills/agents-md/agents/openai.yaml)에 있습니다.

### close-coding-session

큰 코딩 작업이나 세션을 마무리하기로 결정한 뒤 명시적으로 호출하는 스킬입니다. 저장소와 검증 결과를 기준으로 실제 작업 상태를 확인합니다.

1. 적용되는 지침, 계획·진행 문서, Git 변경사항을 읽습니다.
2. 관련 테스트·타입 검사·린트·빌드 등을 확인하고, 실패하거나 실행하지 못한 항목을 기록합니다.
3. 작업 상태를 완료·미완료·차단·검증되지 않음으로 분류합니다.
4. 반복되는 규칙은 `AGENTS.md`, 설계 지식은 해당 문서, 미완료 작업 상태는 기존 계획·진행 문서에 반영합니다.
5. 인계 내용과 다음 대화에 붙여 넣을 시작 프롬프트를 제공합니다.

필요한 지식이 없으면 저장소를 수정하지 않습니다. 임시 로그나 대화 전체를 보존하는 대신, 이후에도 필요한 정보만 정리합니다.

마무리 절차에서 구현을 임의로 수정하거나 커밋·푸시·배포를 진행하지 않습니다. 인계 파일은 기존 관례가 있거나 사용자가 별도로 요청한 경우에만 작성합니다. 미완료 작업은 기존 진행 문서에 재개 상태를 남깁니다.

**사용 전 준비**

작업이나 세션을 마무리하기로 결정한 뒤 호출합니다. 현재 스킬은 Git 상태와 변경사항을 확인하는 절차를 전제로 합니다.

| 구분 | 준비할 내용 | 필요한 이유 |
|---|---|---|
| 기본 조건 | 대상 Git 저장소와 Git을 실행할 수 있는 환경 | 작업 경로, 변경 파일, 스테이징 여부와 미추적 파일을 확인합니다. |
| 기본 조건 | 검증할 작업 결과와 목표·범위를 확인할 수 있는 자료 | 요청한 결과와 실제 구현을 비교합니다. 기존 문서와 대화에서 확인 가능한 정보를 활용합니다. |
| 이 구성의 운영 전제 | 프로젝트에서 사용 중인 계획·진행 문서와 해당 경로 | 미완료 작업, 결정 사항, 검증 상태와 다음 행동을 기존 문서에 남깁니다. |
| 있으면 활용 | 적용되는 `AGENTS.md`, 설계 문서, 결정 기록 | 지침을 확인하고 지식을 반영할 기존 문서를 찾습니다. |
| 검증 항목이 있으면 준비 | 테스트·타입 검사·린트·빌드 명령과 실행 환경 | 관련 검증을 수행합니다. 환경이 준비되지 않은 항목은 미실행 사유와 함께 기록합니다. |
| 작업에 따라 준비 | 이번 작업과 관계없는 기존 변경사항, 실행 제한, 인계 파일 작성 여부 | 사용자 변경을 보존하고 검증·문서 갱신 범위를 정확히 정합니다. |

테스트가 모두 통과하거나 작업이 완료된 상태에서만 호출할 필요는 없습니다. 미완료·실패·검증하지 못한 상태도 확인하고 인계하는 것이 이 스킬의 역할입니다.

**호출 예시**

```text
$close-coding-session 현재 작업을 검증하고, 필요한 지식을 기존 프로젝트 문서에 반영한 뒤 세션을 마무리해주세요.
```

```text
$close-coding-session 새 대화에서 이어가려고 합니다. 미완료 작업과 검증 상태를 기존 진행 문서에 정리하고, 재개 프롬프트를 작성해주세요.
```

실제 절차는 [`SKILL.md`](.agents/skills/close-coding-session/SKILL.md), 호출 설정은 [`agents/openai.yaml`](.agents/skills/close-coding-session/agents/openai.yaml)에 있습니다.

## 참고 문서

| 확인할 내용 | 문서 |
|---|---|
| 설정 위치와 우선순위 | [Codex 설정 기본 안내](https://learn.chatgpt.com/docs/config-file/config-basic) |
| 설정 항목과 허용값 | [설정 레퍼런스](https://learn.chatgpt.com/docs/config-file/config-reference) |
| 모델과 추론 강도 | [모델 안내](https://learn.chatgpt.com/docs/models) |
| 자동 승인 검토 | [Auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review) |
| Windows 샌드박스 | [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) |
| 훅과 메모리 | [Hooks](https://learn.chatgpt.com/docs/hooks), [Memories](https://learn.chatgpt.com/docs/customization/memories) |
| 서브에이전트 | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) |
| agents-md 원본 | [getsentry/skills](https://github.com/getsentry/skills/tree/main/skills/agents-md) |
