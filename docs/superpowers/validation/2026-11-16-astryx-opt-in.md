# Astryx 선택 기능 도입 원장

Plan: `docs/superpowers/plans/2026-11-16-astryx-opt-in.md`

상태: 완료. 명시 호출 스킬·프로젝트별 선택 설치 안내를 MyCodexSetting 0.5.0에 통합하고 자체 설치·배포본을 검증했다.

## 결과

- 기본 설치는 `$astryx` 연결 스킬과 안내·MIT 고지를 제공한다. Astryx npm 패키지는 사용자가 선택한 호환 프로젝트에만 설치한다.
- 사용자 안내 원본은 `kit/integrations/astryx/README.md`이며 설치 대상에는 `.mycodex/integrations/astryx/README.md`로 배포된다. README·상세 사용 안내·CHANGELOG에 연결과 버전 범위를 반영했다.
- 배포: `dist/MyCodexSetting-0.5.0/`, `dist/MyCodexSetting-0.5.0.zip`, 38 files. ZIP SHA256 `c504527d2610f1cb30b4370cf088d59420483736fe1d75766bd7931bb9c63f53`. 검토한 staging ZIP과 동일하다.
- 제품 테스트: staging 69 PASS(70.623s), 실제 원본 반영 후 69 PASS(49.570s). 평가 도구 28 PASS, 스킬 형식·strict validate·diff check PASS.
- 최종 스킬 실제 모델 시험 4건 PASS: A01 승인 대기, A04 작은 CSS 수정에서 미호출, A02 명시 호출 구현·API 조회, A08 ZIP 소비자 조회. 각 실행은 새 로그이며 이전 29개 사례와 합산해 성공률을 주장하지 않는다.
- 독립 Chrome: 4개 폭·14 checks PASS, 실제 Astryx 컴포넌트 렌더·검색/필터/폼·키보드/포커스·기존 브랜드/문의창 스타일 보존. HTTP/JS 오류 및 외부 요청 0. 최종 UI 소스 6개 해시가 검사한 사본과 동일하다.
- 최종 관리 자산 35개와 manifest·kit 원본이 일치한다. 개발 AGENTS·활성 config·Superpowers·전역 config/skills·기존 dist는 해시로 보존을 확인했다.
- 기계 판독 근거: `docs/superpowers/validation/2026-11-16-astryx-opt-in-results.json`. 원본 로그·lockfile·스크린샷은 아래 격리 root와 이번 작업의 `.superpowers/sdd/` 폴더에 보존했다.

## 제한과 검토

Windows Codex CLI·React19·고정 Astryx 0.7.16에서 확인한 범위다. 실제 OS IME·스크린리더·앱/Paseo·다른 OS·모든 버전/플러그인 조합은 미검증이다. 새 독립 UI 검사의 axe 위반은 0이나 color-contrast incomplete가 있어 완전한 접근성 적합성을 선언하지 않는다. 합성 composition은 기존 fixture 입력 동작 검사이며 OS 입력의 대체 증거가 아니다. Vite use-client 경고는 빌드 성공과 별도로 남았다.

Fresh reviewer (`gpt-6-astra`): Critical 0 / Important 0 / Minor 0, 승격 가능. 원본/스킬/ZIP/manifest·문서 링크·실제 설치/모델·독립 브라우저 증거를 대조했다. 승격 후 원본 테스트·자체 설치 검증·최종 dist 확인은 작성자가 별도로 수행했다.

Final: Ruling: reviewer가 유보한 OS IME·스크린리더·완전한 색상 대비·앱/Paseo·다른 OS/버전/플러그인 조합·디자인 우열·비용 절감은 승인된 시험 범위 밖이다. 미검증 표시를 유지하며 일반 호환 보증으로 확대하지 않는다. 승격/배포 완료 여부는 아래 실제 실행으로 따로 확인했다.

- Ruling: 이미 검토한 명시 호출 후보의 도입 요청이므로 해당 방향을 설계로 기록하고 추가 승인 질문 없이 진행한다. 기존 context-compression과 같이 연결 스킬/안내는 포함하고 npm 설치는 선택한다.
- Ruling: 기존 미커밋 작업을 포함한 현재 원본의 독립 staging 사본에서 구현·검증하고 최종 변경 경로만 반영한다. 이전 증거와 사용자 파일을 보존하기 위한 선택이며 소비자 자동 업그레이드 기능을 추가하지 않는다.
- Ruling: 이전 후보 시험의 baseline 실패·성공은 참조 증거로 남긴다. 같은 날 이미 확인한 29개 사례를 전부 다시 실행하지 않고 정식 문서/자산 변경의 실제 설치와 핵심 호출/승인/구현 경계를 새로 실행한다. 미시험 호스트에는 결과를 확장하지 않는다.
- Pre-flight: Task 1 자산 목록/문서 경로가 Task 2 설치/배포/모델 호출 입력이다. 원본과 자체 설치 manifest 동기화는 최종 원본 검증 후 수행한다.

## 실행 기록

- staging: `.superpowers/sdd/2026-11-16-astryx-opt-in/staging`. 기준 제품 64 tests PASS (52.347s).
- Task 1 RED: 신규 설치/사용자 npm 파일 보존/동명·편집 스킬 충돌/버전 경계 5 tests가 기존 0.4.0에서 의도대로 실패했다.
- Task 1 GREEN: 0.5.0 자산과 안내 반영 후 전체 제품 69 tests PASS (70.623s). PATH를 비운 기본 설치, dry-run·재설치, 기존 React18 package/config 보존, 충돌 전부 보존을 포함한다.
- `skill-creator/scripts/quick_validate.py` PASS. 후보와 달라진 부분은 제품 안내 연결, 기존 lockfile 유지, 전체 reset/Theme 일괄 적용 방지와 시험 표식 제거다.
- 실제 후속 시험 root: `C:\Users\jhyoon\AppData\Local\Temp\mycodex-astryx-optin-20261116`. 이전 시험 root와 분리해 사용자 안내 명령·최종 ZIP·최종 스킬을 실행한다.
- 사용자 안내의 core/StyleX 설치와 dev CLI 설치 모두 exit 0. core/cli 0.7.16, React/react-dom 19.3.1 유지. 버전·TextInput·Button·검색·Tailwind 문서·템플릿 추천 명령을 실제 확인했다. 브라우저 도구 설치는 소비자 명령과 별도 증거로 분리했다.
- 임시 0.5.0 ZIP CRC 정상, 설치 manifest 35개 해시 일치, dry-run/재설치 무변경. 실제 0.4.0 배포 kit로 설치한 소비자에 0.5.0 dry-run/apply는 모두 MANIFEST_CONFLICT 종료 1, 전체 파일 보존.
- 현재 완료한 모델 사례: A01 승인 대기·파일 무변경·Astryx 미호출, A04 CSS 한 줄만 변경·Astryx 미호출, A08 ZIP 후보 본문 읽기 및 실제 Button CLI 조회·파일 무변경.
- A02는 빌드 성공 후 자체 검사기의 Puppeteer `insertText` 미지원과 PowerShell stdin 한글 인코딩 오류를 디버깅했다. 실제 DOM 한글과 빌드는 정상이며 실패 로그는 보존한다. 최종 독립 검사는 UTF-8 파일 기반 검사기로 수행한다.
- 평가 도구 28 tests PASS (0.140s). staging과 백업은 작업 폴더 내부 `.gitignore`로만 제외하며 기존 추적 파일을 해제하지 않았다.
- A02 최종 종료 0, 후보 본문 읽기 1회·실제 API 조회 2회. 자체 Chrome 검사기 오류를 수정한 뒤 82개 검사를 통과했다고 보고했고, 별도 UTF-8 파일 기반 독립 검사 14개를 직접 실행해 확인했다. 제품 소스와 측정한 복사본 해시도 일치했다.
- 독립 최종 검토 후 지정한 11개 원본/문서/테스트 경로를 반영했다. 기존 자체 설치의 모든 해시를 확인한 후 새/변경 관리 자산과 manifest만 동기화했고 strict 검증은 오류·경고 0이다.
- 배포 폴더 생성 직후 일반 sandbox에서는 재빌드가 성공했지만 사용자 호스트에서는 RELEASE_CONFLICT가 발생했다. 원인은 파일 내용이 아니라 Python 임시 폴더에서 이어진 소유자 전용 ACL이었다(소유자 CodexSandboxOnline, 상속 차단). 파일을 다시 쓰는 시도는 사전 검사에서 접근 거부로 중단되어 덮어쓰기는 없었다. 새 `dist/MyCodexSetting-0.5.0` 폴더에만 `icacls /inheritance:e`로 상위 dist 권한 상속을 복원했다. 사용자 환경의 README 읽기·재빌드가 성공했고 ZIP 내용은 전후 동일하다. 기존 버전과 전역 권한은 변경하지 않았다.
- 최종 ZIP CRC·검토본 SHA256 일치·재실행 동일성·기존 dist 전부 보존 PASS. 최초 ACL 관련 실패 로그도 `evidence/release-rebuild.json`에 보존하고 성공 재검사는 `release-rebuild-final.json`, 최종 대조는 `release-final-audit.json`으로 구분했다.
