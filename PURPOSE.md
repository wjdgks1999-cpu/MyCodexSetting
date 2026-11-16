# MyCodexSetting의 목적

Codex 프로젝트의 초기 설정을 제공하고, Context Window 한계와 Context rot를 완화하는 작업 환경을 만든다.

필요한 원본만 읽기, 작업의 문서화·인계, 설명 자료 분리, 대화 압축을 함께 사용해 문맥과 토큰 사용을 관리한다.

| 기능 | 목적 | 해결하려는 문제 |
|---|---|---|
| 작업 지침·기본 설정 | 지침과 설정 재사용 | 프로젝트마다 반복되는 초기 세팅 |
| 초기 조사 (`project-init`) | 실제 구성과 원본 확인 | 추정에 의존한 작업 시작 |
| 원본 탐색 (JIT Retrieval) | 필요한 원본만 읽기 | 불필요한 문맥 누적·오래된 정보 참조 |
| Superpowers 연계 | 설계·계획·검증의 문서화 | 긴 대화에 의존한 작업·상태 누락 |
| 세션 인계 (`session-handoff`) | 핵심 상태를 기록해 새 세션에서 재개 | 긴 대화 의존·세션 간 맥락 단절 |
| 사람용 HTML (`human-html`) | 설명 자료 제공·일반 AI 탐색에서 제외 | 설명 자료의 반복 로딩에 따른 문맥 낭비 |
| 문맥 압축 (billion-context) | 대화 압축·필요한 정보 복원 | Context Window 한계·Context rot·토큰 사용 부담 |
| React UI 지원 (Astryx) | 웹 UI 디자인 개선 | 반복되는 상투적 디자인(AI slop) |
| 구조 검증 (`validate`) | 파일·참조의 일관성 확인 | 파일 누락·변경·끊어진 참조 |
| 설치·배포 | 기존 파일을 보존하며 설정 적용 | 덮어쓰기·버전 충돌 |

Superpowers는 별도로 준비하며, billion-context와 Astryx는 선택 기능이다.

근거: [기능·사용 기준](README.md), [상세 사용 안내](docs/usage.md), [원본 탐색 정책](kit/context-policy.md), [기본 설정 설계](docs/superpowers/specs/2026-11-10-project-config-design.md), [사람용 HTML 설계](docs/superpowers/specs/2026-11-10-human-html-design.md).
