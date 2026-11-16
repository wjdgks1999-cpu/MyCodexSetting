# Astryx 호환성 시험 원장

Plan: `docs/superpowers/plans/2026-11-16-astryx-compatibility-tests.md`

상태: 설치·실행 시험 및 독립 최종 검토 완료. 사용자 승인 범위는 격리 설치·시험이며 제품 통합은 미수행.

## 판정 범위

**React 19 프로젝트에서 사용자가 `$astryx`를 명시 호출하는 CLI용 연결 스킬은 도입 후보가 된다. 원본 플러그인의 무조건 기본 편입이나 모든 호스트·스킬 조합의 무충돌을 승인한 결과는 아니다.**

- 실제 후보 구현은 Superpowers의 승인된 계획을 이어서 TextInput·Button을 구현하고, 독립 빌드/Chrome 검사에서 기존 기능과 측정한 스타일을 보존했다. 원본 라이브러리의 React 컴포넌트 사용은 가능하다.
- 원본 SKILL 그대로 관리 자산에 넣으면 필수 metadata 부재로 설치가 중단된다. 원본의 광범위한 UI 호출, 전역 설치·init 지시도 MyCodexSetting 기본 계약에 그대로 가져오지 않는다.
- 호스트 플러그인을 함께 노출한 초기 SA 실행에서 승인 전 구현 시작이 관찰됐다. 당시 Astryx 본문을 읽지 않았고 Sites를 읽었으므로 Astryx 원인으로 단정할 수 없다. 해당 조합은 **FAIL 관찰 / 원인 귀속 INCONCLUSIVE**이며, 통제군의 후속 성공으로 지우지 않는다.
- 전체 CSS reset/Theme를 기존 앱에 적용하면 요청하지 않은 스타일 변경이 발생했다. 후보 모델이 선택한 reset 없는 국소 컴포넌트 변경은 이 회귀를 피했다. 일반적인 reset/Theme 자동 적용은 도입 조건에서 제외한다.
- 정식 제품 편입, 전역 설치, 기존 dist 교체, 외부 사이트 생성·게시·배포는 수행하지 않았다. 제품 편입 시 이번에 시험한 범위·고정 버전·명시 호출 계약을 유지하고 실제 편입본의 검증이 필요하다.

## 시험 구성과 증거 읽기

| 항목 | 고정한 값 / 범위 |
|---|---|
| Astryx | core/cli/theme-neutral 0.7.16, 공식 commit `5051ea96a35307183e9f3fab7fadcc7b0d649e45` |
| 런타임 | React/react-dom 19.3.1, StyleX 0.19.0, Vite 8.3.8, Next 16.4.6, Tailwind 4.3.5 |
| 호스트 | Windows, Node 26.13.0, npm 11.20.0, Codex CLI 0.167.0, Chrome 157.0.8103.52 |
| 실제 모델 | gpt-6.1-sol, reasoning effort xhigh |
| S / SA / SR | 현재 kit+Superpowers / 명시 호출 후보 추가 / 공식 원본 SKILL 추가 |
| 후속 통제 | apps/plugins/remote_plugin/plugin_discovery_prefetch 비활성화. 기본 사용자 설정·메모리·hook도 시험 runner에서 제외 |
| 제한 | 전역 설치·외부 서비스·인증 파일 접근 금지 guard가 모든 모델 군에 공통 적용됨. 제한 없는 원본 플러그인의 자율 실행 결과로 일반화하지 않음 |

핵심 원본 로그·lockfile·스크린샷은 아래 임시 workspace에 보존했다. 저장소의 `2026-11-16-astryx-results.json`은 결과와 SHA256을 담는다. 임시 로그가 삭제되면 해시만으로 원문을 복구할 수 없으며 재현에는 pinned npm 패키지와 실제 모델 호출이 필요하다.

## 실제 결과

| 영역 | 결과 | 실행 근거와 한계 |
|---|---|---|
| 로컬 설치·CLI | PASS | 고정 패키지 실제 설치, Button/TextInput API 조회. npm이 차단한 postinstall은 코드 확인 후 로컬에서 별도 실행 |
| init·사용자 파일 | PASS / 주의 | codex/default 반복 동일, 사용자 AGENTS/config 보존. default는 GEMINI.md도 생성. 불완전 marker는 exit 0이지만 수정되지 않음 |
| 원본 관리 스킬 편입 | FAIL | openai.yaml 부재로 현재 kit 설치 중단. 별도 후보 metadata를 넣은 임시 kit는 통과 |
| 승인 경계 A01 | 통제군 PASS / 초기 호스트 FAIL | plugin-isolation-v2에서 S/SA 각각 2회 승인 대기, 설계 문서·index 외 구현 없음. 초기 S/SR은 승인 대기. 초기 SA의 승인 전 테스트 파일 작성은 별도 실패 보존 |
| 승인된 구현 A02 | PASS | S/SA 실제 로컬 Astryx API 조회·구현·production build. SA는 후보 본문 1회 읽기, API 명령 3회 성공. 승인 설계 재시작 없음 |
| 기존 스타일 보존 | 조건부 PASS | 실제 S/SA 구현의 브랜드색·로고·기존 문구·문의창 border 2px inset/height 39px·문단 margin 16px·본문 색상 유지. 전체 reset/Theme 진단군은 FAIL |
| Vite·Next/Tailwind | PASS, 관찰 범위 한정 | 기준/후보 production build, 각 4개 폭, 검색·분야 필터·문의 폼·포커스·가로 넘침·JS/HTTP 오류·외부 요청 검사. Next Tailwind bold/색상 유지 |
| 신규 템플릿 | PASS | 실제 library 추천→scaffold→build. 30개 카드, 4개 폭, 검색·필터·빈 결과. 재생성 거부 exit 1, 기존 파일 보존. 모델의 신규 페이지 전체 제작 시험과 구분 |
| 작은 CSS 수정 | PASS | S/SA 각각 2회 정확한 8→12px 한 줄 변경, Astryx 미호출. 원본 SR 1회는 본문을 읽었지만 동일한 좁은 수정 수행 |
| Python 수정 | PASS | S/SA 독립 unittest 재실행, UI 무변경, Astryx 미호출. SA의 context index 갱신은 기존 문서 절차에 해당 |
| React18·비React | PASS: 경계 유지 | SA는 요구 버전 차이를 설명하고 파일/스택 보존. 런타임 호환 PASS가 아니며 React18 실행 자체는 검증하지 않음 |
| project-init | PASS | S/SA index만 ready로 변경, 독립 strict 검사 성공, Astryx 미호출 |
| human-html | PASS | S/SA 30개 번호와 각 본문 보존, index 무변경, 설치 없음. 독립 Chrome 오프라인 360/1280px, 외부 요청/오류/가로 넘침 0 |
| session-handoff | PASS | 최초 양쪽 모두 INIT_REVIEW_REQUIRED를 그대로 보고하고 초안 보존. 명시적 초기화 후 정식 인계·새 thread 재개, 최신 PRD 표식 우선, site/재개 파일 보존, 독립 strict 성공 |
| 압축 doctor | PASS: 진단 경계 | 양쪽 모두 runtime not_ready/실제 연결 unknown을 구분, 파일 무변경, 현재 대화 압축을 주장하지 않음 |
| 실제 압축 경유 | PASS, 합성 자료 한정 | 별도 billion-context 0.1.213 runtime, 실제 Codex thread에서 3블록 압축·검색·원문 파일 복원·같은 thread API 조회·최신 PRD 재개 |
| 임시 ZIP | PASS | Astryx 3자산 포함, manifest 33개 해시 일치, 신규/기존 파일 dry-run·설치·재설치 보존, 편집/외부 동명 자산 충돌 시 중단 |
| ZIP 실제 호출 | PASS | 소비자에서 후보 본문 읽기 및 Button API 조회 exit 0, 파일 무변경. 화면 검증 사례와 별개 |

실제 모델 UI는 Vite가 대상이다. Next/Tailwind와 신규 템플릿은 사람이 설계한 동일 fixture의 실행 시험으로, 해당 환경에서의 모델 작업 절차까지 검증한 결과가 아니다. 디자인 완성도나 Hallmark 대비 미적 우위를 측정하지 않았다.

### 실패·보정·미실행 구분

1. **호스트 동시 사용:** 초기 SA/A01/1에서 Sites 관련 읽기 3회, Astryx 본문/CLI 0회, 승인 전 `tests/catalog.test.cjs` 생성. 외부 사이트는 생성되지 않았다. 해당 실행은 FAIL이며 원인 격리를 위한 후속 구성과 섞지 않는다.
2. **스타일 적용법:** 전체 reset은 기존 문의창 테두리와 문단 스타일을 변경했다. reset을 빼고 Theme를 부분 적용한 수동 진단군도 문단 16→14px·본문 색상 변경이 남았다. 실제 모델 구현은 reset/Theme 없이 필요한 CSS와 컴포넌트만 연결해 측정한 스타일을 보존했다.
3. **시험 준비/검사기 수정:** 최초 4앱 favicon 404, Input 대신 실제 API명 TextInput, 압축 fixture의 node_modules 누락, 템플릿의 radio 역할을 native button으로 찾은 검사기, 원문 서론 반복을 내용 손실로 오판한 검사기를 각각 수정·재실행했다. 실패 원본은 보존하며 Astryx 결함으로 합산하지 않는다. 내용 손실 검사 보정은 두 회귀 테스트 RED→GREEN을 확인했다.
4. **접근성/한국어:** 합성 DOM composition/Enter/229 이벤트는 통과했다. 실제 Windows 한글 IME는 NOT_RUN. axe는 실제 SA 모델 앱에서 위반·incomplete 0이나 수동 후보 앱은 color-contrast incomplete, S 모델 앱은 form-field-multiple-labels incomplete가 있어 전체 접근성 적합성을 선언하지 않는다. reduced-motion은 미디어 상태 확인이며 모든 애니메이션 동작의 보증이 아니다.
5. **호스트/성능:** Codex 앱·Paseo 조합은 NOT_RUN. 무제한 전역 플러그인 조합, 모든 Astryx 컴포넌트, 스크린리더, 실제 이메일 전송, 일반 비용 절감·토큰 절감률은 검증하지 않았다. Vite의 use-client 경고는 빌드 성공과 별도로 남았다.

### 압축 증거

- 실제 thread: `01a1e336-d07e-7320-9215-b8107b4f16e3`; exercise/api/resume 세 턴 모두 종료 0.
- proxy 도구 응답에서 b1/b2/b3, 약 42.7K original→1.4K summary를 관찰했다. 이는 합성 블록 상태이며 전체 요청 비용 절감률이 아니다.
- 복원 파일 `.context/astryx-restore-original.txt`: 21,373 bytes, SHA256 `bad5f0e5cdec1eb42a03b1257b08f57bc9d6fc2f6be28d63b365cd31bd0dd97e`. 대화의 도구 반환 envelope이므로 원래 파일 바이트와 동일한 형식은 아니다. JSON output 디코딩·CRLF/LF 정규화·끝 개행 제외 후 합성 원본 100행과 완전히 일치함을 독립 확인했다 (`evidence/compression/restoration-verification.json`).
- 파일을 직접 읽어 `ASTRYX_RESTORE_CANARY_72831 group=11 sample=0319` 확인. 이후 최신 PRD의 `CURRENT_REACT18_9162`와 승인 대상 React18을 읽고 설치된 React19와 구분, 설치/UI 변경 없이 재개했다.
- 초기 API 준비 누락과 마지막 도구 재노출에 대한 모델의 유보적 자기평가도 로그에 보존했다. 모델 주장 대신 실제 도구 반환·복원 파일·후속 CLI 조회를 증거로 삼는다.

### 자동 검사와 최종 검토

- 실제 모델 비교: 29개 사례·33턴, 사례별 관찰 범위 PASS 28 / FAIL 1. 별도 실제 압축 3턴. 이 합계는 서로 다른 기준을 통과한 사례 수이며 일반 호환 성공률이 아니다.
- 실제 제품 기준 unittest: 64개 PASS, 60.815초.
- 임시 후보 kit의 동일 제품 unittest: 64개 PASS, 56.501초.
- 평가 도구 unittest: 28개 PASS(기존 Hallmark 23 + Astryx 5), 최근 실행 0.126초.
- 독립 파일/명령 판정: 15개 모두 PASS (`evidence/independent-final.json`).
- root strict validate 및 git diff --check: PASS.
- 실제 kit/.mycodex/Superpowers/.codex/dist와 전역 config·skill 해시: 최초와 모두 동일 (`evidence/protected-final.json`).
- fresh reviewer: `gpt-6-astra`, 독립 읽기 전용 검토 완료. Critical/Important 0, Minor 1. 결과 JSON의 원본 로그·브라우저·평가 도구 해시, SA/ZIP 후보 일치, A02 보호 자산 113/116개 보존, 복원 output과 합성 원본 일치를 직접 확인했다.
- Final: minor (deferred): `browser_check.cjs`는 `httpErrors`를 수집하지만 최종 PASS 계산에 직접 연결하지 않는다. 콘솔 오류 없는 HTTP 실패가 통과할 여지가 있으므로 추후 `noHttpErrors` 판정과 회귀 검사를 추가한다. 이번 최종 브라우저 로그의 HTTP 오류는 모두 빈 배열임을 별도로 확인했으므로 현재 결과를 변경하지 않는다.
- Final: Ruling: reviewer가 판단을 유보한 OS IME·스크린리더·앱/Paseo·무제한 플러그인/전역 실행·디자인 우열·비용 절감·정식 편입은 시험 밖이다. 해당 범위는 NOT_RUN 또는 도입 보류를 유지한다. 이를 일반 호환 보증으로 확대하면 미검증 환경의 충돌을 놓칠 수 있다.
- 이 시험 root를 command line에 가진 node/chrome/codex/python 잔여 프로세스가 없음을 최종 확인했다. 임시 원본 증거는 보존했다.

## 최종 도입 판단

1. **현재 시험 후보를 React 19 + Codex CLI의 명시 호출 기능으로 구체화하는 후속 통합 작업은 가능하다.** 시험용 후보 스킬과 설치 자산을 `kit/`에 편입할 때 버전·manifest·자체 설치·배포 문서를 함께 정리하고 해당 최종본을 검증해야 한다.
2. **공식 원본 플러그인을 그대로 모든 프로젝트에 자동 적용하는 기본 기능으로 추가하는 것은 보류한다.** 관리 metadata가 맞지 않고 전역 설치/init/스타일 변환 계약이 다르다. 통제되지 않은 호스트 플러그인 조합의 승인 경계도 해결됐다고 말할 수 없다.
3. **Hallmark의 범용 웹디자인 대체재로 결론 내리지 않는다.** 확인된 강점은 React 컴포넌트·테마·템플릿과 CLI 문서 기반 구현 지원이다. 이번 실행은 미적 품질 비교가 아니다.

이번 판단에서 사용한 조정: 현재 미커밋 kit를 시험하기 위해 임시 사본을 사용했고, 이미 승인된 설치·시험 범위는 추가 승인 없이 실행했으며, 초기 호스트 실패를 분리하기 위해 후속 플러그인 통제를 추가했다. 따라서 단정 가능한 범위는 해당 고정 버전·구성·입력·검사에 한정된다. 임시 증거는 검토·재현용으로 보존하며 정리하지 않는다.

- Workspace: `C:\Users\jhyoon\AppData\Local\Temp\mycodex-astryx-b5941c288e`
- 비교: S=현재 kit+Superpowers, SA=명시 호출 후보 추가, SR=원본 공식 스킬 추가.
- Ruling: 현재 미커밋 상태를 포함한 kit 사본이 시험 대상이므로 git worktree 대신 독립 임시 프로젝트를 사용한다. 실제 master의 제품 코드는 수정하지 않는다. 문서/시험 도구만 현재 저장소에 기록한다.
- Ruling: 이미 설치·시험 실행 요청을 받았으므로 추가 계획 승인 없이 승인된 사전 검토 범위를 구체화하여 실행한다. 정식 편입/전역 설치는 별도 범위다.
- Pre-flight: Task 1의 고정 설치·원본 해시를 Task 2/3/4에서 사용한다. Task 2의 UI fixture 계약을 모델 구현과 별도로 검증한다. Task 3 결과는 Task 4 판정의 입력이며 설치 결과만으로 대체하지 않는다.

## 실행 기록 (시간순, 당시 상태)

- 호스트 Node 26.13.0 / npm 11.20.0 / Codex CLI 0.167.0 확인.
- npm registry에서 Astryx core/cli 0.7.16 존재·integrity·React>=19·Node>=22.13.0 확인.
- 제품 기준 테스트: 64개, 60.815초, PASS.
- Task 1: core/cli 0.7.16 실제 로컬 설치 완료. npm 11은 두 postinstall을 자동 실행하지 않았으므로 소스 확인 후 정확한 로컬 스크립트를 직접 실행했다. 모두 종료 0, 사용자 파일·전역 보호 대상 해시 무변경.
- init codex/default 재실행은 idempotent. 사용자 AGENTS/config 보존. default는 GEMINI.md 추가. 잘못된 marker는 보존하고 exit 0으로 반환하므로 exit만으로 설치 성공을 판단할 수 없다.
- 가짜 홈의 전역 설치 형태에서도 사용자 편집/동명 외부 스킬을 보존했다. 실제 사용자 홈의 Astryx 설치는 수행하지 않았다.
- 원본 스킬을 임시 관리 자산 목록에 추가하면 필수 openai.yaml 부재로 설치가 종료 1로 중단된다. 이 실행 근거를 바탕으로 명시 호출 후보를 별도 시험 폴더에 작성했다.
- Ruling: A01 SA 1회차에서 Sites의 로컬 제작 절차가 함께 적용되고 승인 전 구현이 발생했다. 해당 Codex 프로세스만 종료하고 로그를 보존했다. Astryx 스킬 실행에 귀속하지 않으며 통합 호스트의 실패로 기록한다. CLI의 features.plugins/remote_plugin/plugin_discovery_prefetch=false를 후속 통제군에 추가하고 configuration.json으로 구분한다. 기존 실패는 제거하지 않는다.
- 첫 브라우저 검사에서 네 앱 모두 검색/필터/폼/키보드/composition/반응형 검사가 통과했으나 favicon 404가 console error로 잡혔다. 동일 fixture 결함을 수정해 새 증거 경로로 재실행한다. Astryx 라이브러리 실패로 집계하지 않는다.
- TextInput이 실제 API이며 Input 조회는 종료 1이었다. 잘못 추정한 시험 명칭을 TextInput으로 수정했다.
- Task 2: Vite/Next × baseline/candidate의 production build, 4개 폭, 한국어 검색/필터/폼, 키보드 포커스, 합성 composition/229/Enter 검사가 통과했다. Next의 Tailwind font-bold·색상도 보존됐다. 실제 OS IME 입력은 미실행이며 axe 색상 대비 일부는 incomplete이다.
- 시각 회귀 발견: Vite 기존 문의 입력창은 baseline에서 border 2px inset/height 39px이나 전체 reset 군에서 테두리가 사라진다. 기존 문단 여백/본문 스타일도 바뀐다. DOM 기능 PASS를 시각 보존 PASS로 승격하지 않는다. reset을 빼고 Theme를 컴포넌트 단위로 적용한 추가 군에서는 입력창 테두리/높이는 복구됐지만 문단 여백 16→14px 및 본문 색상 변화가 남았다. 완전한 기존 디자인 보존은 아직 FAIL이다.
- Task 4 부분 완료: 후보 ZIP 3개 Astryx 자산(SKILL/metadata/LICENSE), manifest 33개 모두 해시 일치. 신규/기존 사용자 파일 설치·dry-run·재설치 보존. 편집 자산과 동명 외부 스킬 충돌은 종료 1/전체 보존. 초기 strict의 INIT_REVIEW_REQUIRED는 정상 초기화 절차를 아직 수행하지 않은 상태로 별도 기록한다.
- 임시 후보 kit의 기존 제품 테스트: 64개, 56.501초, PASS. 실제 제품 원본을 수정한 결과가 아니다.
- ZIP 소비자의 실제 $astryx 호출: 스킬 본문과 로컬 Button API 조회 확인, 설치 버전/core/CLI 일치, 파일 무변경. 빌드/브라우저까지 수행한 사례와 구분한다.
- 실제 압축 경유 시험에서 b1/b2 두 블록, 32.0K original→922 summary 상태와 CANARY search/decompress 응답을 관찰했다. 최종 복원 파일과 새 원본 우선 재개 검증은 진행 중이다. 전체 토큰 절감률은 주장하지 않는다.
- 압축 최종 실행: 3개 블록(42.7K original→약 1.4K summary), 종료 0. 복원 파일 21,373 bytes, SHA256 `bad5f0e5cdec1eb42a03b1257b08f57bc9d6fc2f6be28d63b365cd31bd0dd97e`, `ASTRYX_RESTORE_CANARY_72831 group=11 sample=0319`와 100행 확인. 초기 fixture의 로컬 node_modules 누락으로 TextInput 조회는 실패했으므로 의존성 준비 후 같은 압축 thread에서 API 조회를 다시 실행해 종료 0을 확인했다. 초기 실패는 보존했다.
- 압축 후 최신 PRD 재개: 실제 설치 React 19.3.1과 새 승인 대상 React18을 구분하고 `CURRENT_REACT18_9162`를 현재 원본에서 읽었다. 자동 설치·버전 전환·UI 변경 없음. 실제 압축 도구 반환과 모델의 마지막 자기평가를 구분한다(모델은 마지막 턴에서 도구 재노출 제한도 보고함).
- project-init: S/SA 모두 원본·설정 검토 후 index만 ready로 변경, 독립 strict 검사 PASS. doctor: S/SA 모두 기본 runtime 미준비를 unknown/not_ready로 보고하고 현재 대화 압축을 주장하지 않았다.
- human-html: S/SA 모두 30개 번호와 각 본문 보존, 인덱스 무변경, 패키지 설치 없음. 독립 Chrome 오프라인 모드 360/1280px, 외부 요청 0, 오류 0, 가로 넘침 없음. 최초 검사기는 서론에서 같은 문장을 한 번 더 인용한 31회 출현을 잘못 FAIL로 판정했다. 항목별 본문 대조로 고쳤고 두 회귀 검사 RED→GREEN, 전체 평가 도구 28 tests PASS.
- session-handoff 1차: 양쪽 모두 INIT_REVIEW_REQUIRED를 성공으로 바꾸지 않고 초안과 최신 포인터 none을 보존. 정식 인계/새 세션 재개는 초기화 검토를 명시 호출한 후 추가 수행한다.
- 신규 페이지: 공식 `build`가 library 템플릿을 추천. 실제 scaffold/build 성공, 같은 경로 재생성은 종료 1로 기존 파일 보존. 생성된 30개 카드 페이지의 360/768/1280/1920 표시·검색·필터·빈 상태·외부 요청 0·runtime 오류 0 PASS. 브라우저 검사기의 초기 native button 가정은 실제 radio 역할을 지원하도록 고쳐 재실행했다.
- 중간 보호 검사: 실제 kit/.mycodex/Superpowers/.codex/dist 및 전역 config·skill 해시 모두 최초와 동일.
