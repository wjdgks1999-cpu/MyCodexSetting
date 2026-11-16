# Astryx 도입 가능성 사전 검토

상태: 공식 소스·문서 검토 완료. 설치·모델 행동·브라우저 호환성 시험은 미실행. 제품 통합 미수행.

후속 상태: 위 문장은 사전 검토 시점의 기록이다. 사용자 승인으로 설치·실행 시험을 진행했으며 현재 결과는 `docs/superpowers/validation/2026-11-16-astryx-compatibility.md`를 따른다.

이후 승인한 선택 기능의 정식 통합·0.5.0 배포 결과는 `docs/superpowers/validation/2026-11-16-astryx-opt-in.md`를 따른다. 이 사전 검토의 미실행 표시는 당시 기록으로 보존한다.

## 판단

Astryx는 MyCodexSetting의 **React UI 제작 지원 기능 후보**가 될 수 있다. 범용 웹디자인 스킬과 React 컴포넌트·테마 시스템은 제공 범위가 다르므로 Hallmark의 완전한 대체재로 취급하지 않는다.

권장 후보는 명시 호출용 연결 스킬을 MyCodexSetting에 기본 제공하고, Astryx를 사용하기로 한 호환 프로젝트에서만 프로젝트 의존성을 준비하는 형태다. 기존 Superpowers가 설계·계획·구현·검증 절차를 담당하고 Astryx는 컴포넌트·테마·템플릿 구현을 지원한다. 원본 플러그인의 광범위한 호출 설명과 전역 설치 지시를 그대로 기본값으로 가져오는 방식은 권장하지 않는다.

이것은 도입 구조에 대한 사전 판단이다. 기존 기능과 충돌이 없다는 실행 결과나 기본 도입 승인이 아니다. 개발용 AGENTS의 신규 기능 원칙에 따라 아래 시험을 구체화하고 통과해야 통합할 수 있다.

## 확인한 버전과 원본

2026-11-16 공식 GitHub 연결로 확인했다.

- 저장소: `meta/astryx`, 공개 저장소, 기본 브랜치 `main`.
- GitHub 최신 release: `v0.7.16`, 게시 시각 `2026-11-14T00:48:07Z`.
- 검토 기준 release commit: `5051ea96a35307183e9f3fab7fadcc7b0d649e45`.
- 별도 확인한 main: `95025f18cff937d9cbeda3890e366f47aa5c723e`, package version `0.7.17`. 이를 v0.7.16과 같은 실행 대상으로 취급하지 않았다. npm latest 배포 여부는 별도 검증하지 않았다.
- v0.7.16의 공식 Codex plugin manifest version: `0.1.0`. CLI/core 패키지 버전과 다른 번호다.
- 프로젝트는 Beta로 안내하며 MIT 라이선스를 제공한다. 실제 재배포 시 포함하는 원본의 저작권·라이선스 고지를 보존한다.

## 제품과 배포의 차이

| 구분 | 확인한 내용 | MyCodexSetting에 주는 의미 |
|---|---|---|
| UI 구현 | React 19 이상, react-dom 19 이상, StyleX runtime peer dependency | 비React 프로젝트에 일괄 설치할 기본 스택으로 삼지 않는다 |
| CLI | Node >=22.13.0, 컴포넌트 문서·검색·테마·템플릿·진단·codemod | 현재 kit의 Python 중심 초기 설치에 Node 의존성을 무조건 추가하지 않는다 |
| 기본 스타일 | 미리 빌드된 CSS/JS, 일반 소비는 별도 StyleX 컴파일러 없이 가능 | StyleX를 모든 소비자 빌드에 강제해야 한다는 해석은 잘못이다. 일부 템플릿·소스 확장은 별도 확인 필요 |
| Tailwind | 함께 사용 가능하나 CSS layer/import 순서 요구 | 기존 CSS reset·테마·Tailwind와 실제 화면 회귀를 검사해야 한다 |
| 공식 agent plugin | Codex/Claude 공용 스킬 1개, CLI에 연결하는 안내 | 플러그인만으로 React 컴포넌트나 CLI가 모두 설치된 것은 아니다 |
| 기존 관리 스킬 정책 | kit은 `agents/openai.yaml`의 명시 호출 false 정책을 요구 | 원본 스킬 폴더에는 SKILL.md만 있으므로 관리 스킬로 편입하려면 별도 metadata·자산 목록 처리가 필요 |

CDN으로 빌드 단계 없는 React 예제도 있지만, 오프라인 단일 HTML과 같은 조건이 아니다. MyCodexSetting의 `human-html` 요구사항을 대체하지 않는다.

## 실제 코드에서 찾은 충돌 후보

다음은 소스에서 확인한 지시·쓰기 경로와 그에 따른 가설이다. 모델이 실제로 위반했다는 판정은 아니다.

1. **넓은 호출 범위:** 공식 SKILL description은 일반 UI 생성·수정·스타일·테마 작업을 포함한다. 본문은 Astryx가 없는 프로젝트에 core/cli를 추가하고 init을 실행하도록 지시한다. 작은 CSS 수정이나 비React 프로젝트에서 불필요한 도입으로 이어지는지 시험해야 한다.
2. **전역 설치:** 스킬 본문은 `astryx`를 찾지 못하면 `npm i -g @astryxdesign/cli`를 실행하도록 지시한다. 컴퓨터 단위 설치 지원 코드는 `~/.agents/skills/astryx/SKILL.md`와 다른 도구의 스킬 링크/사본을 관리한다. MyCodexSetting의 격리 시험과 프로젝트별 설치 원칙에 맞는 제한이 필요하다. 이번 검토에서는 실행하지 않았다.
3. **AGENTS 지침 추가:** init의 Codex preset은 AGENTS.md를 대상으로 한다. 기본 모드에서는 다른 도구의 지침 파일도 관여한다. 관리 블록을 넣고 기존 블록을 갱신하는 코드이며, 기존 사용자 지침 전체를 지운다고 단정하지 않는다. 컨텍스트 인덱스·Superpowers 순서·명시 호출 경계·파일 길이와 공존하는지 검증해야 한다.
4. **템플릿과 디자인 제약:** 공식 스킬은 페이지를 템플릿에서 시작하도록 하고 raw div/span·외부 CSS import·직접 hex/px 등을 컴포넌트/토큰으로 바꾸도록 지시한다. 승인된 디자인·기존 DOM·좁은 수정 범위·독립 HTML과 충돌할 여지가 있다. 프로젝트 지침 생성기에는 기존 페이지는 보존하고 전체 scaffold를 건너뛰라는 보완도 있으므로 실제 순서를 시험해야 한다.
5. **Superpowers:** 템플릿 추천과 컴포넌트 구현은 기존 절차 안에서 사용할 수 있다. 그러나 원본 스킬에는 Superpowers의 설계 승인·기존 계획을 우선한다는 연결 계약이 없다. 승인 전에 init/설치/페이지 생성이 시작되는지, 승인된 계획을 처음부터 반복하는지 확인해야 한다.
6. **한국어:** CLI 문서 언어 옵션은 en/zh/dense로 안내한다. 한국어 UI가 불가능하다는 뜻은 아니다. 한글 IME 조합 중 Enter, 검색/필터, 긴 레이블, 줄바꿈, 폼 오류와 접근성을 실제 브라우저에서 검증해야 한다.

공식 문서의 일반 CSS/Tailwind 확장 지원과 agent 지침의 강한 스타일 제약도 구분한다. 라이브러리 자체가 raw CSS를 사용할 수 없게 막는다고 해석하지 않는다.

## 권장 시험 경계

정식 실행 전 고정 버전·fixture·합격 기준·반복 정책을 계획으로 작성한다. 아래는 사전 검토에서 도출한 필수 시험 영역이며 모두 **NOT_RUN**이다.

| ID | 비교 입력 | 핵심 합격 기준 |
|---|---|---|
| A01 | PRD-only 신규 프로젝트, 승인 전/후 | Superpowers 승인 전에 스택·패키지·AGENTS·제품 파일 생성 금지; 승인 후 원래 계획에서 진행 |
| A02 | React 19 + Vite 신규 UI | 명시 호출로 실제 Astryx 로드·구현·빌드·브라우저 동작 확인; 설치 성공만으로 통과 금지 |
| A03 | 기존 React 19 + Next/Tailwind 앱 | 브랜드·문구·검색·필터·폼·기존 CSS 보존, 스타일 layer와 hydration 회귀 없음 |
| A04 | 4px 간격 수정, Python 버그, React 18/비React 프로젝트 | 불필요한 호출·패키지 설치·React 업그레이드·템플릿 교체·전역 변경 없음 |
| A05 | project-init, human-html, session-handoff, context-compression | 원본 탐색/오프라인 HTML/인계/압축 경계 유지; 압축은 실제 모델 경유와 발생 증거가 필요 |
| A06 | init·재실행·사용자 수정 AGENTS/config·중복 사용자 스킬 | 기존 파일/정책/인덱스 보존, 관리 블록 중복 없음, 충돌 시 보존·중단, 전역 파일 무변경 |
| A07 | 한국어 표·폼·검색 및 360/768/1280/1920px | IME·키보드·포커스·모션 감소·긴 문구·반응형 표시·기능 보존 |
| A08 | 임시 kit/ZIP 배포와 새 소비자 설치, CLI·앱/Paseo | metadata·라이선스·버전·자산 누락 없음; ZIP 설치 후 실제 호출까지 확인; 호스트별 미실행 구분 |

기준군은 현재 MyCodexSetting + Superpowers, 비교군은 그 구성 + 후보 연결 스킬이다. 원본 공식 플러그인은 별도 진단군으로 보존한다. 전역 설치·외부 서비스 생성·게시·유료 이미지 호출은 시험 중 허용하지 않는다. 호스트의 Sites/imagegen 등은 실제 제공 목록과 통제 조건을 기록하고, 다른 제공자의 동작을 Astryx 고유의 실패로 잘못 귀속하지 않는다.

## 이번 작업의 실행 범위

- 실행: 공식 저장소 metadata/release/tag, 고정 commit의 플러그인·SKILL·패키지 요건·지침 생성 코드 조회. 현재 kit의 정책 검사, Superpowers 승인 절차, human-html 계약과 대조.
- 미실행: npm/npx 설치, 전역 설치, Astryx init, 실제 Codex 조합 세션, 앱 빌드, 브라우저 시험, 배포 ZIP 생성.
- 변경: 이 검토 문서와 컨텍스트 인덱스 등록만. 제품 코드·설치 사본·배포 자산은 변경하지 않는다.

## 원본 링크

- [공식 저장소](https://github.com/meta/astryx)
- [v0.7.16 release](https://github.com/meta/astryx/releases/tag/v0.7.16)
- [공식 agent plugin 안내](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/plugins/astryx/README.md)
- [Codex plugin manifest](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/plugins/astryx/.codex-plugin/plugin.json)
- [공식 SKILL.md](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/plugins/astryx/skills/astryx/SKILL.md)
- [CLI package.json](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/packages/cli/package.json)
- [Core package.json](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/packages/core/package.json)
- [Core 설치·Tailwind·CDN 안내](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/packages/core/README.md)
- [프로젝트 agent 지침 생성기](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/packages/cli/foundation/agent-docs/agent-docs.mjs)
- [컴퓨터 단위 스킬 관리](https://github.com/meta/astryx/blob/5051ea96a35307183e9f3fab7fadcc7b0d649e45/packages/cli/foundation/agent-docs/computer-agent-text.mjs)
