---
name: session-handoff
description: Persist verified project knowledge and a dated restart snapshot when the user explicitly invokes $session-handoff. Ordinary status questions and goodbye messages do not request this workflow.
---

# 세션 인계

명시적 호출 시 `.context/index.md`와 `.mycodex/context-policy.md`에서 현재 작업의 원본을 찾는다. 관련 설계·계획·현재 작업의 원장·실제 파일/Git 상태·이번 세션의 검증 결과를 대조한다. 다른 계획의 원장을 읽거나 변경하지 않는다.

압축 요약이나 Bili export는 검증되지 않은 참고 자료다. 요약의 사실·승인·완료 주장은 현재 원본과 실행 증거로 재확인한다. export를 원본이나 최신 인계로 자동 등록하지 않는다. 인계는 프록시 없는 새 세션에서도 원본과 이 기록만으로 재개할 수 있게 작성한다.

`.human-docs/`는 일반 탐색과 인계 근거에서 제외한다. 생성된 HTML을 읽거나 index·인계의 원본 링크로 연결하거나 본문을 지식 문서에 복사하지 않는다. HTML 생성 작업을 인계해야 하면 해당 작업의 원본·검증 결과와 산출물 경로만 짧게 기록한다.

짧은 지속적 작업 지침은 AGENTS에 반영한다. 상세 지식은 기존 원본을 우선하고 필요할 때만 주제별 문서를 만든다. 적절한 원본이 없는 확인된 장기 결정만 decisions에 기록한다. PRD/GDD·승인된 설계 원문·전역 기억·설정은 이 정리 작업으로 바꾸지 않는다. 비밀 값·사용자 원문 전문은 기록하지 않는다.

`.mycodex/templates/handoff.md`의 필수 절을 채워 `.context/handoffs/draft-<고유식별자>.md`를 만든다. 모든 원본 링크는 최종 Handoff와 같은 이 폴더에서 해석되게 한다. 근거·시점·다음 행동을 구체적으로 기록하고 다음을 구분한다.

- 완료 / 진행 / 차단 / 미검증
- 실행한 명령과 결과 / 실행하지 않은 검사
- Git 기준 커밋과 미커밋 변경 경로 / Git 미사용
- 과거 검증 결과 / 현재 변경 이후 재확인이 필요한 결과

작성 시점에는 시간대가 있는 ISO 8601을 사용한다. 원장 부재만으로 완료를 판단하지 않는다. 요구사항·결정·작업 상태의 원본을 새 요약으로 대체하지 않는다.

루트에서 `python .mycodex/mycodex.py record-handoff --target . --draft .context/handoffs/draft-<고유식별자>.md`를 실행한다. 도구가 구조·링크를 확인하고 충돌 없는 스냅샷과 최신 포인터를 기록한다. 도구는 본문의 사실성을 판단하지 않으므로 근거 대조를 생략하지 않는다.

성공하면 자신이 만든 draft만 제거하고 기록된 경로·다음 행동·미검증 항목을 보고한다. 실패하면 이전 최신 포인터를 유지하고 남은 draft/스냅샷과 이미 반영된 장기 지식 변경을 구분해 보고한다. 실패를 성공으로 표현하지 않는다. 새 세션은 index에서 관련 Handoff와 원본을 찾아 현재 상태를 다시 확인한다.
