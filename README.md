# MyCodexSetting

Codex 프로젝트를 시작할 때 필요한 작업 지침, 설정, 문서 탐색과 세션 인계 흐름을 준비하는 도구입니다. 개발은 Superpowers 절차로 진행하고, 필요할 때 HTML 설명 문서와 Codex CLI·Paseo 문맥 압축을 함께 사용합니다.

<!-- source-only:start -->
**최신 버전 0.4.0** · [배포 ZIP](dist/MyCodexSetting-0.4.0.zip) · [배포 폴더](dist/MyCodexSetting-0.4.0/README.md)

배포 원본은 `kit/`입니다. `python tools/build_release.py`로 배포본을 만들며, 같은 버전의 내용이 다르면 기존 산출물을 보존하고 충돌을 보고합니다. 실제 검증 기록은 [CLI](docs/superpowers/validation/2026-11-12-billion-context-cli.md)와 [Paseo](docs/superpowers/validation/2026-11-12-billion-context-paseo.md)에 있습니다.
<!-- source-only:end -->

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

**2. 사용하는 환경에서 Codex 대화를 시작하고 초기 조사를 요청합니다.**

- **Paseo:** 대상 프로젝트 폴더를 작업 경로로 지정해 Codex chat을 시작합니다.
- **터미널의 Codex CLI:** 대상 프로젝트 루트의 터미널에서 `codex`를 실행합니다.

열린 Codex 대화에 아래 요청을 입력합니다.

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

### Paseo에서 사용할 때

대상 프로젝트의 Codex chat에서 준비·연결을 요청합니다.

```text
$context-compression Paseo에서 문맥 압축을 사용할 수 있도록 준비하고 연결해 주세요.
```

연결 후 Paseo에서 **Codex 문맥 압축**을 선택해 새 chat을 시작합니다. 압축 없이 사용하려면 기존 Codex 제공자를 선택합니다.

### 터미널에서 Codex CLI로 사용할 때

대상 프로젝트 루트의 터미널에서 최초 한 번 runtime을 준비하고, 압축을 사용할 세션을 시작합니다.

```powershell
python .mycodex/mycodex.py compression prepare --target . --apply
python .mycodex/mycodex.py compression codex --target . --apply
```

이후에는 두 번째 명령으로 압축 세션을 시작합니다. 압축 없이 사용하려면 평소처럼 `codex`를 실행합니다.

두 방식의 상세 준비·인자 전달·재개·이전 버전 충돌 처리는 [문맥 압축 사용 안내](kit/integrations/billion-context/README.md)를 따릅니다. 원본 문서·인덱스·인계는 계속 관리합니다.

## 상세 안내

- [설치·파일 역할·인계·설정·문제 해결](docs/usage.md)
- [CLI·Paseo 문맥 압축 사용 안내와 호환 범위](kit/integrations/billion-context/README.md)
- [버전별 변경 이력](CHANGELOG.md)
- [billion-context·acp-kernel 출처와 라이선스](kit/integrations/billion-context/THIRD_PARTY_NOTICES.md)
