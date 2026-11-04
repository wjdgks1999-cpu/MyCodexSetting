---
name: project-init
description: Initialize project context from an existing PRD or GDD when the user explicitly invokes $project-init after installing MyCodexSetting.
---

# 프로젝트 설정 조사

명시적 호출로 설치된 세팅을 프로젝트에 맞게 완성한다. 기술 스택 선택·제품 설계·구현은 이후 Superpowers 작업이다.

대상 프로젝트 루트를 확인하고 적용되는 AGENTS/override, `.context/index.md`, `.mycodex/context-policy.md`를 읽는다. 정책과 아래 도구는 설치된 MyCodexSetting에 포함된다. 필수 자산이 없으면 초기화 도구로 설치할 필요를 보고하고 임의로 빈 파일을 만들지 않는다.

1. index의 PRD/GDD를 읽고 기존 문서·관련 코드·구성을 조사한다. 비밀 파일·의존성 폴더·다른 작업의 원장 전체는 읽지 않는다. 기존 사용자 지침을 유지하고 충돌을 보고한다.
2. 실제 사용 가능한 Superpowers 스킬을 확인하고 확인한 이름·경로 또는 환경의 근거를 index의 초기화 확인 사항에 남긴다. 전역 제공도 인정한다. 디렉터리 존재만 확인되거나 실제 사용 가능 여부를 확인하지 못하면 needs-review를 유지한다. 자동 설치하지 않는다.
3. index는 원본의 위치와 용도만 연결한다. AGENTS에는 짧은 지속적 지침만 추가하며 기존 규칙을 보존한다. 긴 설명은 기존 원본을 우선하고 실제 필요가 있을 때만 주제별 문서를 만든다. project.md나 빈 결정·지식 문서를 생성하지 않는다.
4. 코드가 없는 PRD-only 프로젝트는 정상이다. 코드·스택·명령이 아직 미정임을 구분하고 명령을 만들어 넣지 않는다. 명령을 기록할 때는 코드/구성 근거와 실행 여부를 구분한다.
5. 루트에서 `python .mycodex/mycodex.py validate --target . --json`을 실행한다. 유일한 오류가 INIT_REVIEW_REQUIRED이고 설정 조사가 끝났다면 index의 status만 ready로 바꾸고 다시 검증한다. 실패하면 needs-review로 되돌린다. 기존 메모와 참조는 보존한다.

결과에는 확인한 원본, 변경 파일, 검증 결과, 미확인 사항을 짧게 남긴다. ready는 세팅 조사 완료이며 애플리케이션 동작·테스트 통과가 아니다. 커밋·배포·전역 설정 변경·제품 구현을 이 스킬의 일부로 수행하지 않는다.
