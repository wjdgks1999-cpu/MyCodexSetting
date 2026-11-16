# MyCodexSetting 개발 지침

MyCodexSetting은 새 Codex 프로젝트의 기본 설정·문서 탐색·세션 인계 도구다. 이 파일은 개발 전용이며, 배포용 `kit/templates/AGENTS.md`에 복사하거나 배포 자산에 포함하지 않는다.

## 문서와 작업 흐름

- `.context/index.md`에서 현재 요청에 필요한 원본만 찾아 읽는다.
- 원본을 고르는 기준이 필요하면 `.mycodex/context-policy.md`를 참고한다.
- 설계·계획·진행 원장은 사용 가능한 Superpowers 절차와 기존 문서를 따른다.
- 문서를 만들거나 옮기거나 현재 작업을 전환하면 인덱스의 해당 경로를 갱신한다.
- 이전 작업을 이어갈 때는 인덱스의 최신 인계와 현재 프로젝트 상태를 대조한다.
- `.human-docs/`는 일반 개발의 읽기·검색에서 제외한다. 명시적인 HTML 생성·수정·검증 때만 해당 산출물에 접근하며, 인덱스나 인계의 원본으로 등록하지 않는다.

## 수정 원본과 자체 설치 사본

- 기능·정책·템플릿·관리 스킬의 원본은 `kit/`이다. 명령 진입점은 `kit/mycodex.py`, 구현은 `kit/mycodex_lib/`, 관리 스킬은 `kit/skills/`에 있다.
- `.mycodex/`와 `kit/skills/`에 대응하는 `.agents/skills/` 항목은 자체 설치 사본이다. 사본만 수정하지 말고 `kit/` 원본·설치 자산 목록·`.mycodex/manifest.json`의 버전·해시 일관성을 확인한다.
- `.agents/skills/superpowers/`는 별도 개발 절차이며 MyCodexSetting 설치 자산에 포함되지 않는다.
- 배포 기본 설정은 `kit/templates/config.toml`, 이 저장소의 활성 설정은 `.codex/config.toml`이다. 활성 설정을 배포 기본값으로 자동 복사하지 않는다.

## 신규 기능 도입

- 새 기능은 기존 기능·Superpowers·다른 스킬·설치/배포 정책에 미치는 영향을 먼저 확인하고, 영향 범위에 맞는 충돌·회귀 테스트 계획과 합격 기준을 작성한다.
- 격리 환경에서 기존 구성과 기능 추가 구성을 실제 비교한다. 관련 호출 경계·작업 절차·기존 동작과 파일 보존·설치와 재설치를 검증한다.
- 코드 검토나 설치 성공만으로 호환성을 통과시키지 않는다. 실행 근거와 실패·차단·미실행 항목을 원장에 구분해 남긴다.
- 필수 검증을 통과하고 확인된 충돌을 해결한 뒤 기능으로 통합한다. 충돌이 남거나 필수 검증이 미완료면 도입을 보류한다.

## 검증

프로젝트 루트에서 변경 범위에 맞는 검사를 실행한다. 기본 도구는 Python 3.11 이상과 표준 라이브러리를 사용한다.

```powershell
python -X utf8 -B -m unittest discover -s tests -v
python -X utf8 -B .mycodex/mycodex.py validate --target . --strict --json
git diff --check
```

- Paseo bridge를 변경했다면 `python -X utf8 -B -m unittest discover -s tests/integration -p test_paseo_bili_bridge.py -v`도 실행한다. Node가 필요하며 모의 엔진 검사는 실제 모델 경유·압축의 증거가 아니다.
- 기술 스택과 명령을 추정하지 않는다. 구조 검증·자동 테스트·실제 CLI·Paseo 결과와 미실행을 구분해 기록하고, 과거 결과를 현재 검증으로 대신하지 않는다.

## 설치와 배포

- 설치 로직을 수정할 때 기본 dry-run, 기존 사용자 파일 보존, 다른 버전·관리 자산 충돌 시 중단하는 계약을 유지한다.
- 배포는 `tools/build_release.py`가 `kit/`의 설치 자산 목록과 배포 문서로 구성한다.
- 기존 `dist/`의 버전별 폴더·ZIP은 보존한다. 같은 버전의 내용 충돌을 덮어쓰기로 해결하지 않는다.
- 배포를 변경하는 작업에서는 `kit/mycodex_lib/model.py`의 버전·자산 목록, 자체 설치 사본·manifest, `CHANGELOG.md`, 배포 내용의 일관성을 확인한다. 일반 개발 변경만으로 배포본을 재생성하지 않는다.
