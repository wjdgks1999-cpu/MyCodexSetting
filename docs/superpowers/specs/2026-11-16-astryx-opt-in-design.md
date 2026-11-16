# Astryx 선택 기능 도입 설계

사용자 승인: 호환성 시험 결과를 바탕으로 MyCodexSetting 사용자가 선택적으로 설치·활용하도록 도입하고 설치·사용 문서를 추가한다.

## 제공 방식

- 검증한 명시 호출 연결 스킬을 `kit/skills/astryx/`에 포함한다. `allow_implicit_invocation: false`를 유지하며 사용자가 `$astryx`를 호출할 때만 적용한다.
- 기본 MyCodexSetting 설치는 Python만 사용한다. npm/Node/React/Astryx 패키지 설치, 전역 플러그인 설치, AGENTS 변경은 기본 설치가 수행하지 않는다.
- 사용자가 선택한 기존 React 19 프로젝트에서만 고정 Astryx core/cli 0.7.16과 필요한 peer dependency를 설치한다. React18/비React는 호환 차이를 설명하고 기존 스택을 보존한다.
- 설치·사용·중지·버전 충돌·호스트 범위의 원본 문서는 `kit/integrations/astryx/README.md`로 두고 설치 대상에도 포함한다. 출처·라이선스를 함께 배포한다. README와 상세 사용 안내는 이 문서를 연결한다.
- 기존 페이지는 필요한 컴포넌트만 변경한다. 전체 reset/Theme 적용은 별도 디자인 변경으로 다루고 기존 스타일 보존을 확인한다. 설계·계획·인계는 Superpowers와 기존 관리 스킬 절차를 유지한다.

## 선택과 범위

검토한 방식은 공식 원본 플러그인 일괄 설치, 연결 스킬 제공+프로젝트 의존성 선택 설치, 별도 관리 스킬 선택 설치 체계 추가다. 사용자가 승인한 명시 호출 방향과 현재 context-compression 구조에 맞춰 두 번째로 구현한다. 세 번째는 설치 명령/manifest의 새로운 선택 자산 체계를 요구하므로 이번 범위에 추가하지 않는다. 이는 구현 선택이며 사용자가 구체적인 CLI 인터페이스를 지정했다는 의미는 아니다.

MyCodexSetting은 0.5.0으로 배포한다. 0.4.0 이하의 설치/배포는 보존하고 자동 업그레이드 계약을 바꾸지 않는다. 이 저장소 자체 설치는 기존 manifest와 관리 자산을 먼저 검증한 뒤 변경된 관리 자산만 동기화한다. 사용자 AGENTS/index/config와 Superpowers는 보존한다.

지원 판단은 Windows Codex CLI에서 시험한 React19 구성에 한정한다. 앱/Paseo·OS IME·모든 호스트 플러그인 조합을 검증했다고 하지 않는다. 기존 실패는 과거 시험 원장에 보존한다.

## 검증 계약

- 신규·기존 프로젝트 설치, dry-run/재설치, 관리 스킬 충돌, manifest·명시 호출 정책, ZIP 문서 링크 및 라이선스를 실제 검사한다.
- npm 없는 기본 설치 경계와 package.json/lockfile/AGENTS/config 보존을 검사한다.
- 사용자 안내의 설치 명령을 격리 React19 프로젝트에서 실행한다. 최종 스킬로 명시 호출·미호출·승인 전 경계를 실제 Codex에서 재검증하고 구현 사례를 독립 Chrome으로 확인한다.
- 기존 제품 unittest와 평가 도구 테스트, strict validate, diff check를 통과해야 한다. 새 배포는 최종 검토 후 생성하고 과거 dist와 비교한다.
