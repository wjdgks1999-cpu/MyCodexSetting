# Hallmark 기본 포함 검토: 1차 실제 실행 결과

**판정: 원본 그대로 기본 포함은 불가. 명시 호출 후보도 기본 도입 승인은 보류한다.**

MyCodexSetting의 현행 관리 스킬 정책과 원본 Hallmark의 자동 호출 설정이 충돌했다. 한국어 소개 페이지의 분량 검사 누락도 정적 검사와 실제 Chrome 렌더링에서 재현했다. 반면 실행한 Superpowers 조합에서는 설계 승인 무시나 반복 설계 순환을 관측하지 않았고, 명시 재설계·감사·작은 수정·비디자인 작업의 경계는 지켜졌다. 이 제한된 결과를 모든 스킬·호스트에서의 무충돌 보장으로 확대하지 않는다.

이 문서는 [승인된 테스트 계획](../plans/2026-11-16-hallmark-compatibility-tests.md)의 **1차 실행 결과**다. 차단 원인 확인 후 확장 인증 시험을 보류했다. 전 사례 3회 반복을 완료한 보고서가 아니며, 제품 통합·배포 승인도 아니다.

## 고정한 환경과 후보

| 항목 | 실제 값 |
|---|---|
| MyCodexSetting | 0.4.0, HEAD `8dee1b11ddefacafcbe523cb568b44721ee7908c` + 기존 미커밋 AGENTS 분리 작업 |
| Hallmark | 2.0.0, `04977e15f3dfd6ee4b74c887dac3eb52665d6c92` |
| 다운로드 ZIP SHA256 | `1d41fe4c866c2ce18a86ae6f07c45c9ecd8274949a35307cf6527832226a1435` |
| 실행 호스트 | Windows, 실제 사용자 인증의 Codex CLI 0.167.0 |
| 비교 모델 | `gpt-6.1-sol`, reasoning `xhigh`; 연결 확인만 `low` |
| 도구 | Python 3.13.2, Node 26.13.0, Chrome 157.0.8103.52 |
| 브라우저 보조 | 임시 경로의 puppeteer-core 25.17.0, 설치 시 `--ignore-scripts` |
| Superpowers | 현재 설치본을 파일별 SHA256으로 고정; MyCodexSetting ZIP에는 포함하지 않음 |
| 시험 입력 | 합성 한국어 PRD와 정적 HTML/CSS/JS; 실제 서비스 데이터 사용 안 함 |

- B: 기존 네 관리 스킬만 제공. S: B + Superpowers. H: B + 원본 Hallmark. SH: B + Superpowers + 원본 Hallmark.
- SH-E: SH에서 **`allow_implicit_invocation: true`를 `false`로만 변경**. Hallmark 본문·스크립트·테마는 원본과 같다. 자동 호출을 끈 것과 선택 설치는 다른 개념이다.
- 기억 읽기/쓰기·hooks·일부 개인 스킬을 세션 옵션으로 제외했다. 실제 `skills/list`에서 B/S/H/SH 로컬 구성이 구별되고 로딩 오류가 없었다. 호스트가 별도로 주입하는 Sites 등 cloud/plugin 스킬은 남아 있었다. 로컬 목록만으로 완전 격리를 주장하지 않는다.
- 비교용 프로젝트는 배포용 `kit/templates/AGENTS.md`로 초기화했다. 개발용 루트 AGENTS를 소비자 지침으로 사용하지 않았다.

증거 루트: `C:\Users\jhyoon\AppData\Local\Temp\mycodex-hallmark-host-cmlbmk8v`.
`evidence/source-hashes.json`, `upstream.json`, `skills-*.json`, `runs/<variant>/<case>/<repeat>/events-*.jsonl`, `turn-*.json`, `run.json`에 원본·호출·변경·시간 근거가 있다. 임시 파일은 운영체제 정리 대상이므로 영구 보관을 보장하지 않는다. 저장소에는 평가 도구와 [22개 fixture·27턴의 측정 요약](2026-11-16-hallmark-runs.json)을 남긴다. 이 수에는 무효·중단·smoke도 포함되며 통과 횟수가 아니다.

## 실제로 재현한 문제

### 1. 원본의 자동 호출 설정과 현행 배포 정책 충돌

임시 kit에 Hallmark를 다섯 번째 관리 스킬로 넣고 모든 자산을 manifest에 포함했다. 원본 설치는 파일 생성 자체는 성공하지만 strict validate에서 `INVALID_SKILL_POLICY`가 나온다. 원인은 MyCodexSetting이 관리 스킬의 명시 호출 정책을 요구하는데 Hallmark 원본은 자동 호출을 허용하기 때문이다.

이는 Codex가 원본 metadata를 읽지 못한다는 뜻이 아니다. 실제 CLI 스킬 로딩은 성공했다. metadata만 false로 바꾼 후보는 이 오류가 사라졌으며, 아직 조사하지 않은 새 프로젝트의 정상 오류인 `INIT_REVIEW_REQUIRED`는 그대로 남겼다.

근거: `packaging/{raw-managed,explicit-metadata}/result.json`, `deterministic-repeats/result.json`. 새 설치 세 번 모두 원본에서 정책 오류가 나고 명시 호출 후보에서는 사라졌다. 이 반복은 결정적 설치 검사이며 모델 세션 3회 반복과 구분한다.

### 2. 한국어 분량 검사 누락

footer를 둔 소개 페이지에 대응하는 영어/한국어 600어절 입력을 넣었다. 영어는 정적 검사에서 603 visible words 경고가 나왔고, 실제 렌더링에서는 한 화면 592 words 위반도 검출했다. 한국어는 같은 gate 58이 검출되지 않았다. 전체 linter에는 다른 스타일 지적이 있으므로 한국어 페이지 전체가 통과했다는 의미는 아니다.

원본 `sloplint-render.mjs:801`은 단어에 `[A-Za-z]{2,}`가 있는지 검사한다. 원본 정적 검사도 영문 중심으로 단어를 계산한다. 앱 범위에서는 원래 gate 58을 적용하지 않으므로, 이번 재현은 **소개 페이지의 page 범위**로 한정했다. 한국어 콘텐츠가 실제 삭제된 것은 아니며, 분량 검사 기능의 누락이다.

근거: `static/{en,ko}-page.html`, `*-page-report.json`, `*-render-report.json`, `deterministic-repeats/`. 새 경로에서 정적/실제 렌더 검사를 각각 세 번 반복해 모두 같은 차이를 확인했다. footer가 없던 초기 입력은 양쪽 모두 미검출이라 언어 차이 증거에서 제외했다.

### 3. 호스트 기본 Sites 선택에 따른 외부 항목 생성

초기 B/H 시험에서 Sites가 자동 선택되어 외부 빈 프로젝트가 만들어졌다. 두 실행을 중단하고 최종 반복 수에서 제외했다. B에서도 발생했으므로 Hallmark가 추가되어서만 생긴 충돌로 귀속할 수 없다. 이후 모든 구성에 작업 범위를 fixture 내부로 제한하고 외부 생성·게시·배포·이미지 API·전역 변경을 금지하는 동일 developer 지침을 추가했다. 따라서 이후 결과는 이 통제 조건에서만 유효하다.

API 확인 당시 두 항목은 version 0, preview/live URL 없음, 외부 방문자 0이었다. 배포된 웹사이트는 없다. 그러나 삭제 API가 없고 브라우저 접근 호스트가 unavailable이어서 **빈 항목 두 개는 미삭제**다.

- B: `appgprj_6afa96b0dc888191afc9aca736ab4f9a`
- H: `appgprj_6afa9774172c81918d8b3df97c44f8f9`

Sites 응답의 인증 필드가 한 차례 도구 출력에 포함되어, 이후에는 허용 필드만 출력하고 평가용 파일에서 해당 필드를 제거했다. 플랫폼의 도구 기록까지 삭제했다고 주장하지 않는다. 서비스의 인증 내용이나 값은 이 문서에 보관하지 않는다.

## 사례별 실행 범위

`PASS`는 해당 run의 명시한 관측 기준에 한정한다. 한 사례에 부분 증거만 있으면 사례 전체는 `INCONCLUSIVE`다. `NOT_RUN`은 차단 원인 확인 후 실행하지 않은 항목이다.

| 사례 | 판정·실제 근거 | 미검증 범위 |
|---|---|---|
| S01 새 페이지·승인 | S/SH 각 1회 승인 대기 후 구현. SH에서 Hallmark 실제 로드. 승인 전 제품 파일 변경 없음. 독립 재실행: S 검색 8 + Chrome 12개, SH 21개 검사 통과 | 초기 호스트 통제 변경 때문에 전체 네 구성 비교는 INCONCLUSIVE. B/H 유효 완료 없음. SH-E와 3회 반복 없음 |
| S02 승인 계획부터 구현 | NOT_RUN | 원본/후보의 단계 회귀·명시 호출·ZIP 설치 후 실행 |
| S03 작은 CSS 수정 | S/SH 각 1회 PASS. CSS 왼쪽 여백 8→12px만 변경, Hallmark 미호출. SH 결과 독립 Chrome 4개 폭과 검색·필터·문의 확인 | SH-E와 반복 2·3 |
| S04 검색 정렬 버그 | S/SH-E 각 1회 PASS. 실패 재현 후 unittest 1개 통과, 사이트 파일 불변, Hallmark 미호출 | B/H/SH·추가 반복 |
| S05 보존 조건 재설계 | SH-E 1회 PASS. Hallmark 실제 로드. PRD·승인 설계·계획·로고·app.js 해시 불변. 독립 Chrome 360/768/1280/1920px 넘침 없음, 검색·필터·문의 보존 | 같은 재설계의 S 대조 실행·추가 반복·프레임워크 |
| S06 감사만 | S/SH-E 각 1회 PASS. 후보는 Hallmark 실제 로드, 양쪽 변경은 `.hallmark/` 보고·캡처뿐. 원본 파일 모두 보존 | 추가 반복 없음 |
| S07 human-html | 장문 S/SH-E 각 1회 PASS. 원문 60항목·각 해설을 담은 독립 HTML, 인덱스·제품 불변, Hallmark 미호출. 독립 검사에서 번호 누락·외부 의존성 없음 | 최초 짧은 PRD는 별도 smoke. 추가 반복 없음 |
| S08 PRD-only 초기화 | 수정된 fixture의 S/SH-E 각 1회 PASS. Superpowers 조사 후 인덱스만 ready 전환, 실제 validate 성공. 앱·스택 생성 없음 | 최초 SH-E 실행은 승인 문서가 남아 있어 smoke로만 취급. B/H·추가 반복 없음 |
| S09 인계·새 세션 | INCONCLUSIVE. SH-E 인계 작성과 다른 thread의 미완료 브라우저 검사 재개 확인. 이어가기에서 기존 문의 오표시를 발견·수정하고 실제 22개 검사 수행 | S 대조·추가 반복 없음. Hallmark 미호출 상태라 활성 Hallmark 로그와 원장 우선순위는 미검증 |
| S10 문맥 압축 | NOT_RUN. 임시 runtime 준비만 성공 | 실제 모델 경유·압축·복원과 Hallmark 조합 전체 미검증 |
| S11 한국어·화면 | 언어 분량 검사 FAIL 재현. 기존 app 재설계·신규 소개 페이지는 실제 Chrome 검사 수행 | 모든 화면 유형·블라인드 품질 평가·프레임워크·반복 없음 |
| S12 다른 제공자 | INCONCLUSIVE. 초기 Sites 부작용 관측 및 중단 | 통제된 Sites/imagegen 명시 요청, 가짜 키+통신 차단 조합 미실행 |
| S13 의존성·도구 | INCONCLUSIVE. Puppeteer 부재 시 render `not run`, 임시 준비 후 실제 render `ran` 확인 | Node/Chrome 없음, 네트워크 차단, subagent 유무의 모델 비교 미실행 |
| S14 중복·기본 설정 | NOT_RUN | 동명 사용자 스킬, 기본 기억 설정, 실제 앱의 새 세션 미검증 |

S05에서 보라색과 `자료 · 검색`은 Hallmark 미관 규칙과 부딪힐 수 있었으나 사용자 보존 지시를 우선했다. S06은 이 충돌을 보고하고 원본을 바꾸지 않았다. 따라서 **규칙 문구가 겹친다는 이유만으로 Superpowers와 실제 행동 충돌이 발생했다고 결론 내리지 않는다.**

문의 fixture는 실제 서버 전송 없이 로컬 접수 문구만 표시하도록 의도적으로 단순화했다. S05 동작 보존 검사는 기존 동작과 같은지 본 것이며 실제 문의 전송 성공을 검증한 것이 아니다. S09 이어가기에서는 이 오표시를 고치며 `site/app.js`와 `index.html`이 변경됐다. 인계 복원은 관측됐지만 전체 파일 불변이나 Hallmark 활성 조합 통과의 증거로 집계하지 않는다. reduced-motion 설정 인식만으로 모든 애니메이션의 접근성을 인증하지 않는다. S01의 생성 테스트는 실제 CSS 동작도 검사했다.

## 배포 경로와 비용

임시 패키지는 Hallmark 187개 자산과 라이선스를 포함하며 ZIP CRC 검사를 통과했다. dry-run 무변경, 동일 버전 재설치 불변, 설치 파일 변조 시 중단과 사용자 수정 보존을 확인했다. ZIP을 별도 경로에 풀어 깨끗한 소비자와 기존 AGENTS/config가 있는 소비자에 설치했고, 양쪽 모두 manifest 217개 자산이 일치했다. 기존 사용자 AGENTS/config도 보존됐다. 실제 `kit/`, 설치 사본, 설정, 기존 `dist/`는 변경하지 않았다.

ZIP 소비자의 초기화 조사는 실행하지 않아 `INIT_REVIEW_REQUIRED`를 유지했다. 인덱스 안내가 없는 사용자 AGENTS를 보존한 소비자는 `AGENTS_INDEX_MISSING`도 보고했다. 이것을 설치 실패나 최종 strict 통과로 바꾸어 기록하지 않았다. 근거: `zip-consumer-recheck/result.json`. 임시 후보 kit에서 기존 제품 테스트 64개도 통과했다(187.633초).

행동 시험의 Hallmark는 프로젝트에 직접 준비한 추가 스킬이다. 임시 managed ZIP을 거쳐 설치한 뒤 동일 행동을 다시 실행한 것은 아니다. 따라서 행동 성공과 패키징 성공을 합쳐 종단간 기본 배포 통과로 처리하지 않는다.

| 실제 비교 | S | Hallmark 포함 |
|---|---:|---:|
| S01 설계+구현, 손상된 승인 입력 턴 제외 | 1,499.09초 | SH 1,343.53초 |
| S03 CSS 수정 | 111.33초 | SH 98.83초 |
| S04 정렬 수정 | 198.52초 | SH-E 119.17초 |
| S06 감사만 | 586.33초 | SH-E 634.95초 |
| S07 장문 HTML | 608.19초 | SH-E 629.38초 |
| S08 수정된 PRD-only 초기화 | 222.65초 | SH-E 240.29초 |

각 1회이므로 속도 우열이나 중앙값을 결론 내리지 않는다. 명시 재설계는 1,088.23초, 명시 감사는 634.95초였다. CLI가 제공한 input/cached/output token 수는 turn 기록에 남겼다. cached input을 포함하는 누적 input은 컨텍스트 길이나 비용 자체가 아니므로 가격으로 환산하지 않는다. SH S01 구현 턴에서 input 5,071,379, cached input 4,955,520, output 46,451로 반복 호출 부담은 작지 않았다.

## 시험 자체의 오류와 검증 상태

- 최초 네 모델 실행은 실제 권한이 read-only/never로 적용되어 무효였다. 공식 `--approve-for-me`를 사용한 읽기 확인 후 새 fixture에서 재시작했다. 권한 우회 플래그를 쓰지 않았다.
- 합성 승인 파일이 PowerShell을 거치며 `?`로 손상된 두 턴은 모델이 재전송을 요청했고 수정하지 않았다. 절차 충돌·추가 질문 비용으로 계산하지 않았다.
- 최초 S07은 장문 fixture가 아니었고 최초 S08은 PRD-only가 아니었다. 각각 smoke로 분리하고 새 fixture를 만들었다.
- ZIP 후보 전체 회귀의 최초 실행은 평가 도구의 60초 제한에 걸렸다. 이를 제품 실패로 세지 않고 별도 증거 경로에서 제한을 600초로 늘려 재실행해 64개 통과를 확인했다.
- 기존 제품 테스트: 64개 통과(초기 44.938초, 수정 후 최종 49.067초). 평가 실행기 검사: 최종 23개 통과(0.097초). 실행하지 않은 render를 통과로 처리하지 않고, 성공 주장·실패한 스킬 읽기·승인 전 코드 변경·비밀 필드 저장 등을 구분하는 검사다.
- 보호 자산 해시 대조: `kit/`, `.mycodex/`, `.agents/skills/superpowers/`, `.codex/`, `dist/` 변화 없음. 저장소 strict validate는 오류·경고 없이 성공했고 `git diff --check`도 통과했다.
- 별도 fresh review에서 재실행 시 로그 덮어쓰기, 다른 fixture 세션 재개, 같은 run ID에 이전 PASS 적용 문제를 발견했다. 합성 회귀의 실패를 확인한 뒤 미완료 시도 거부·배타적 로그 생성·세션 소유권 검사·증거 해시 결합으로 수정했고 23개 검사가 통과했다. 제품 변경 목록에 루트 페이지/API가 빠지는 문제도 함께 고쳤다. 추가 유료 모델 실행이나 재검토를 성공 근거로 꾸미지 않았다.
- 마감 시 22개 fixture의 미완료 turn 없음. 프로세스 명령행에서 시험 루트를 사용하는 잔여 프로세스도 없었다. 측정 요약의 run 상태는 PASS 11, INCONCLUSIVE 7, BLOCKED 4이며, 별도 설치·한국어 실패와 전체 14개 사례의 완성률을 나타내는 숫자는 아니다.

## 기본 도입에 대한 결정

1. **원본 그대로 기본 포함:** 현행 관리 스킬 정책 검사 실패로 불가. 자동 호출 정책을 예외 처리하려면 그것은 별도 제품 정책 변경이며 이번 시험에서 수행하지 않았다.
2. **명시 호출 후보를 기본 포함:** 기술적으로 포장·명시 실행은 가능하지만 현재 승인하지 않는다. 한국어 검사 수정, 호스트 도구 경계, ZIP 설치 후 행동 시험, 전 사례 반복과 실제 사용 호스트 증거가 필요하다.
3. **Superpowers와의 관계:** 실행한 범위에서는 직접적인 승인·계획 충돌을 관측하지 않았다. 이것이 모든 조합에서의 무충돌을 뜻하지 않는다. 본문 중 독자 절차와 도구 가정은 계속 검토할 유지보수 대상이다.

후속 작업이 승인되면, 한국어 검사와 호출 경계를 수정한 후보를 먼저 고정한 뒤 미실행 조건을 이어서 시험한다. 이번 변경은 평가 도구·테스트·문서이며 기본 기능을 추가하지 않았다.

고정 원본: [SKILL.md](https://github.com/nutlope/hallmark/blob/04977e15f3dfd6ee4b74c887dac3eb52665d6c92/skills/hallmark/SKILL.md), [Codex metadata](https://github.com/nutlope/hallmark/blob/04977e15f3dfd6ee4b74c887dac3eb52665d6c92/skills/hallmark/agents/openai.yaml), [렌더 검사](https://github.com/nutlope/hallmark/blob/04977e15f3dfd6ee4b74c887dac3eb52665d6c92/skills/hallmark/scripts/sloplint-render.mjs).
