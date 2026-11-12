# MyCodexSetting

Codex 프로젝트를 시작할 때 필요한 작업 지침, 설정, 문서 탐색과 세션 인계 흐름을 준비하는 도구입니다. 개발은 Superpowers 절차로 진행하고, 필요할 때 HTML 설명 문서와 Codex CLI·Paseo 문맥 압축을 함께 사용합니다.

## 제공하는 기능

| 기능 | 역할 |
|---|---|
| 작업 지침·설정 | `AGENTS.md` 초안과 `.codex/config.toml` 기본값 준비 |
| 문서 탐색 | `.context/index.md`로 현재 요청에 필요한 원본만 찾는 JIT Retrieval |
| 프로젝트 초기 조사 | 요구사항·코드·기존 문서를 확인하고 인덱스 구성 |
| 세션 인계 | 현재 상태·검증 근거·다음 행동을 기록하고 새 세션에서 재확인 |
| 사람용 HTML | 사용자가 지정한 주제를 독립 HTML로 설명 |
| 문맥 압축 | **정식 선택 기능**인 billion-context로 Codex CLI·Paseo의 모델 전달 문맥 압축·복원 |

설계·계획·구현은 준비된 Superpowers를 사용합니다. MyCodexSetting은 원본 문서와 개발 절차를 연결하며, Superpowers 자체를 설치하지는 않습니다.

## 빠른 시작

Python **3.11 이상**, Codex에서 열 수 있는 대상 폴더, 그 안의 UTF-8 PRD/GDD, 사용 가능한 Superpowers를 준비합니다. PRD만 있는 폴더와 기존 프로젝트 모두에 적용할 수 있습니다.

**1. 설치할 변경안을 확인한 뒤 적용합니다.** 아래 명령은 배포 폴더 또는 이 저장소에서 실행합니다. `--requirements`는 대상 폴더 기준 경로입니다.

```powershell
python kit/mycodex.py init --target "C:/work/나의 프로젝트" --requirements PRD.md
python kit/mycodex.py init --target "C:/work/나의 프로젝트" --requirements PRD.md --apply
```

첫 명령은 파일을 쓰지 않습니다. 기존 문서·설정은 보존하며, 다른 버전의 설치 자산이 있으면 충돌로 중단합니다. 자동 업그레이드는 제공하지 않습니다.

**2. 대상 프로젝트를 Codex에서 열고 초기 조사를 요청합니다.**

```text
$project-init PRD.md를 기준으로 프로젝트 세팅을 초기화해 주세요.
```

조사가 끝나면 인덱스가 `ready`가 됩니다. 이는 세팅 조사 완료를 뜻하며 제품 개발이나 애플리케이션 테스트 완료를 뜻하지 않습니다.

**3. 대상 프로젝트 루트에서 구조를 검증합니다.**

```powershell
python .mycodex/mycodex.py validate --target . --strict --json
```

## 작업 중 사용하는 스킬

| 명시적 호출 | 사용 시점 |
|---|---|
| `$project-init` | 처음 세팅하거나 프로젝트 구조를 조사할 때 |
| `$session-handoff` | 다음 세션을 위한 상태·근거·다음 행동을 남길 때 |
| `$human-html` | 지정한 주제를 사람이 읽기 쉬운 HTML로 만들 때 |
| `$context-compression` | CLI·Paseo 문맥 압축을 준비·진단하거나 사용 방법과 요약 추출을 요청할 때 |

새 세션에서는 대상 프로젝트를 열고 이어서 할 일을 요청하면 됩니다. Codex는 인덱스에서 관련 원본과 최신 인계를 찾아 현재 상태와 대조합니다. `.human-docs/`의 HTML은 일반 개발 탐색과 인계 원본에서 제외합니다.

## 문맥 압축 선택

[billion-context](https://github.com/ranxianglei/billion-context)는 필요한 호스트에서 선택해 사용하는 정식 기능입니다. Node **20 이상**·npm·Codex가 필요하며, Paseo 방식은 Paseo도 준비합니다.

```text
$context-compression Paseo에서 문맥 압축을 사용할 수 있도록 준비하고 연결해 주세요.
```

Paseo는 연결 후 **Codex 문맥 압축**을 선택해 새 chat을 시작합니다. CLI는 runtime 준비 후 프로젝트 터미널에서 실행합니다.

```powershell
python .mycodex/mycodex.py compression codex --target . --apply
```

일반 CLI는 평소처럼 `codex`로 실행합니다. 준비·인자 전달·재개·호환 범위는 [문맥 압축 사용 안내](kit/integrations/billion-context/README.md)를 따릅니다. 원본 문서·인덱스·인계는 계속 관리합니다.

## 상세 안내

- [설치·파일 역할·인계·설정·문제 해결](docs/usage.md)
- [CLI·Paseo 문맥 압축 사용 안내와 호환 범위](kit/integrations/billion-context/README.md)
- [버전별 변경 이력](CHANGELOG.md)
- [billion-context·acp-kernel 출처와 라이선스](kit/integrations/billion-context/THIRD_PARTY_NOTICES.md)
