# Astryx 선택 설치·사용 안내

[Astryx](https://github.com/meta/astryx)는 React 컴포넌트·테마·페이지 템플릿과 CLI 문서를 제공하는 도구입니다. MyCodexSetting은 0.5.0부터 이를 사용하는 **명시 호출 `$astryx` 스킬**을 제공합니다. 범용 웹디자인 스킬이나 Superpowers의 대체 기능은 아닙니다.

## 무엇이 설치되나요?

MyCodexSetting의 기본 `init`은 연결 스킬과 이 안내·라이선스만 복사합니다. Node, npm 패키지, React 앱, 공식 전역 플러그인은 설치하지 않습니다. 기본 문서 탐색·인계에는 Node와 네트워크가 필요하지 않습니다.

| 선택 | 결과 |
|---|---|
| Astryx를 사용하지 않음 | 기존 MyCodexSetting 기능과 개발 절차를 그대로 사용 |
| `$astryx`로 호환성만 확인 | 현재 스택·설치 상태를 조사하고 필요한 조건을 안내 |
| 호환 프로젝트에 패키지 설치 | 해당 프로젝트에서 Astryx UI 구현 가능. 다른 프로젝트와 전역 설정은 유지 |

이 안내는 배포본의 `kit/integrations/astryx/README.md`와 설치 대상의 `.mycodex/integrations/astryx/README.md`에서 읽을 수 있습니다. 설치 대상 스킬은 `.agents/skills/astryx/`입니다.

## 1. 프로젝트 조건 확인

- Node **22.13.0 이상**, npm 사용 프로젝트.
- 기존 **React와 react-dom 19 이상**의 앱 및 package.json. React18·비React 프로젝트는 현재 스택을 유지하고 호환성 검토부터 진행합니다.
- 검증 기준: Astryx core/cli **0.7.16**, StyleX runtime **0.19.0**. core/cli 버전을 맞추고 lockfile을 보존합니다.
- 다른 패키지 관리자를 사용하는 프로젝트는 기존 lockfile을 유지해 동등한 로컬 설치를 진행합니다. 아래 npm 명령으로 두 번째 lockfile을 만들지 않습니다.

대상 프로젝트 루트의 **PowerShell**에서 확인합니다.

```powershell
node --version
npm.cmd ls react react-dom @stylexjs/stylex @astryxdesign/core @astryxdesign/cli --depth=0
```

패키지가 아직 없으면 목록 확인이 비정상 종료할 수 있습니다. package.json·lockfile도 함께 확인합니다. 이미 다른 Astryx/StyleX 버전을 쓰고 있다면 아래 명령으로 바로 교체하지 말고 호환성과 변경 범위를 먼저 검토합니다. PRD만 있는 프로젝트는 Superpowers로 설계와 기술 스택을 먼저 정합니다.

Codex CLI 대화에서 조사만 요청할 수도 있습니다.

```text
$astryx 현재 프로젝트에서 사용할 수 있는지 확인해 주세요. 파일 수정이나 패키지 설치는 하지 마세요.
```

## 2. 원하는 프로젝트에만 설치

조건을 확인하고 설치하기로 선택한 **대상 앱 루트**에서 실행합니다. 첫 명령은 UI 런타임 의존성, 두 번째는 개발용 CLI를 추가합니다. React 버전은 이 명령으로 바꾸지 않습니다.

```powershell
npm.cmd install --save-exact @astryxdesign/core@0.7.16 @stylexjs/stylex@0.19.0
npm.cmd install --save-dev --save-exact @astryxdesign/cli@0.7.16
.\node_modules\.bin\astryx.cmd --version
.\node_modules\.bin\astryx.cmd component TextInput
.\node_modules\.bin\astryx.cmd component Button
```

package.json·package-lock.json이 변경되고 프로젝트 안에 node_modules가 생깁니다. lockfile은 코드와 함께 관리합니다. peer dependency 충돌을 `--force`나 `--legacy-peer-deps`로 우회하지 말고 원인을 확인합니다. npm이 lifecycle 스크립트를 제한하더라도 전역 허용 설정을 바꾸지 말고 CLI/API 조회로 필요한 동작을 확인합니다.

테마 패키지가 필요한 디자인을 선택한 경우에만 추가합니다.

```powershell
npm.cmd install --save-exact @astryxdesign/theme-neutral@0.7.16
```

전역 `npm install -g`, 공식 플러그인의 중복 설치, `astryx init`은 위 흐름에 필요하지 않습니다. macOS/Linux에서는 해당 패키지 관리자의 명령과 로컬 `./node_modules/.bin/astryx`를 사용하되, 아래 실측 지원 범위와 구분합니다.

## 3. MyCodexSetting에서 사용

대상 프로젝트 루트에서 `codex`를 실행합니다. 새로 설치한 스킬이 보이지 않으면 새 세션을 열어 `.agents/skills/astryx/` 검색 여부를 확인합니다. MyCodexSetting 초기 조사가 끝나지 않았다면 먼저 `$project-init`을 실행합니다.

승인된 React UI 작업에 명시 호출합니다.

```text
$astryx 승인된 설계와 계획에 따라 기존 검색 입력과 버튼을 TextInput·Button으로 바꿔 주세요. 기존 문구·브랜드 색상·검색·폼 동작을 보존하고 빌드와 브라우저로 검증해 주세요.
```

새 페이지는 요청할 디자인과 기능을 적습니다. 설계 승인이 없으면 먼저 Superpowers 절차로 설계를 정하고, 승인 후 템플릿 추천·필요한 컴포넌트를 사용합니다. 기존 페이지는 작은 부분부터 적용합니다. 스킬 이름을 말하지 않은 일반 UI·CSS·Python 수정에는 이 기능을 자동 적용하지 않습니다.

CSS 연결 시 `astryx.css`와 기존 앱 스타일의 순서·layer를 확인합니다. 기존 앱에 전체 `reset.css`나 페이지 전체 Theme를 바로 씌우면 입력창 테두리·본문·여백이 바뀔 수 있습니다. 기존 Tailwind import와 브랜드를 보존하고 필요한 부분만 적용한 뒤 화면을 비교합니다. 설치 직후 자동으로 CSS나 테마가 적용되는 것은 아닙니다.

CLI에서 현재 버전 문서와 추천을 조회할 수 있습니다.

```powershell
.\node_modules\.bin\astryx.cmd search "search input"
.\node_modules\.bin\astryx.cmd docs tailwind
.\node_modules\.bin\astryx.cmd build "searchable resource library"
```

`build`는 템플릿 추천 명령이며 앱의 production build가 아닙니다. 실제 앱 검증은 해당 프로젝트의 빌드·테스트 명령을 사용합니다. 입력·검색·필터·폼·키보드·포커스·모바일 폭을 확인하고, 한글 조합 입력과 접근성의 미검증 항목도 기록합니다. 작업 인계는 기존 `$session-handoff`를 사용합니다. `$human-html`의 독립 오프라인 HTML은 계속 별도 기능입니다.

## 사용 중지·기존 설치와 충돌

사용하지 않을 때는 `$astryx`를 호출하지 않으면 됩니다. 관리 스킬 파일만 삭제하면 MyCodexSetting 무결성 검증에서 누락으로 보고하므로 활성화 스위치처럼 삭제하지 않습니다.

패키지를 제거하려면 먼저 프로젝트 코드의 Astryx import·컴포넌트·CSS를 기존 구현으로 바꾸고, 다른 코드가 필요로 하지 않는 패키지만 기존 패키지 관리자로 제거합니다. StyleX가 원래 프로젝트의 의존성이었다면 함께 제거하지 않습니다. 변경 후 앱을 다시 빌드·검증합니다.

새 프로젝트에는 현재 배포본을 설치합니다. 기존 프로젝트에서 다른 버전의 kit으로 `init`을 실행하면 manifest·관리 자산 충돌 시 변경 없이 멈춥니다. 기존 `.mycodex`와 관리 스킬을 백업하고 변경점을 검토하는 별도 이전 작업이 필요합니다. 사용자 AGENTS·index·config·Superpowers를 일괄 삭제하거나 manifest의 버전 숫자만 바꾸지 않습니다.

이미 동명 `astryx` 스킬이 있거나 설치 자산을 사용자가 편집한 경우에도 덮어쓰지 않고 충돌을 보고합니다. 공식 전역 플러그인을 함께 쓰고 있다면 중복 지시와 실제 로드 경로를 확인하고 사용할 연결 방식을 정합니다.

## 지원·검증 범위

실측 기준은 Windows Codex CLI 0.167.0, Node 26.13.0, React 19.3.1, Astryx 0.7.16입니다. Vite 8.3.8·Next 16.4.6/Tailwind 4.3.5 fixture의 빌드·Chrome 동작과 기존 관리 스킬 경계를 시험했습니다. 이는 모든 버전과 컴포넌트의 보증이 아닙니다.

Codex 앱·Paseo에서의 Astryx 조합과 실제 Windows 한글 IME·스크린리더는 미검증입니다. 문맥 압축의 Paseo 지원과 Astryx의 Paseo 검증 여부는 별개입니다. 호스트 플러그인이 함께 적용된 초기 시험에는 승인 전 구현 사례가 있어 모든 플러그인 조합의 무충돌을 주장하지 않습니다.

Astryx는 Beta이며 MyCodexSetting은 검증한 버전을 고정해 안내합니다. 버전 변경 시 API·기존 스타일·Superpowers/다른 스킬·설치/재설치 경계를 다시 확인합니다. 출처와 라이선스는 [고지](THIRD_PARTY_NOTICES.md) 및 [MIT 원문](LICENSE)을 참고하세요.
