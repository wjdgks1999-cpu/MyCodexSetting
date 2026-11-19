# MyCodexSetting 1.0 · Context Rot 평가 인계

## 목표

새 컴퓨터의 첫 작업은 **기존 Langfuse Cloud 프로젝트 `MyCodexSetting-Eval`에 연결하고 합성 Trace와 점수를 재조회하는 것**이다. 연결을 확인한 뒤 중단된 파일럿을 이어간다. 사용자는 Windows 승인 창이 나타날 수 있는 기존 병렬 실행 방식을 허용했다. 파일럿의 합계 한도는 **30분·요금표 환산 US$15**이며, 본 실험은 파일럿을 검토한 후 별도로 승인받는다.

평가할 기능은 **JIT 원본 탐색, 세션 인계, 문맥 압축** 세 가지다. Sol·Terra·Luna 각각에서 같은 과제의 짧은/긴 문맥과 기능 OFF/ON 네 조건을 비교한다. 주 지표는 `OFF의 정확도 하락폭 − ON의 정확도 하락폭`(%p)이다. 토큰·비용·시간·부작용은 보조 지표다.

## 작성 시점

기존 PC 상태 확인은 `2026-11-19T12:08:57+09:00`, 새 PC 인계 반영은 `2026-11-19T12:16:13+09:00`이다. 기존 저장소는 `C:\Users\jhyoon\Desktop\MyApp\MyP\MyCodexSetting`, 브랜치는 `master`, HEAD는 `d390fce86cbb9fbda3bf47faa2d6891c27fe981f`다. 새 PC에서는 이전해 온 저장소 루트를 기준으로 아래 명령을 실행한다. 연결 도구, 평가 계획·원장, 파일럿 코드와 0.5.1 ZIP은 기존 작업 트리의 미커밋 파일이므로 해당 커밋만 복제하면 누락된다.

## 관련 원본

- [평가 계획과 합격 기준](docs/superpowers/plans/2026-11-19-v1-feature-evaluation.md)
- [중단 시점 결과표](docs/superpowers/validation/2026-11-19-context-rot-pilot.md) · [조건별 원장 JSON과 로그 해시](docs/superpowers/validation/2026-11-19-context-rot-pilot.json)
- [파일럿 실행기](tools/evaluations/context_rot/pilot.py) · [합성 과제 및 채점기](tools/evaluations/context_rot/fixture.py) · [Langfuse 연결 확인 도구](tools/evaluations/langfuse_check.py)

## 작업 상태

| 모델 | 종료 결과가 기록된 조건 | 종료 행을 쓰기 전에 중단된 조건 |
|---|---|---|
| `gpt-6.2-sol` | JIT 짧음 OFF, 짧음 ON, 김 ON 모두 **4/4** | JIT 김 OFF |
| `gpt-6.1-terra` | 인계 김 ON · 시간 초과 | 인계 짧음 ON |
| `gpt-6-luna` | 압축 짧음 ON · 시간 초과 | 압축 김 OFF |

완료 3건, 시간 초과 2건, 종료 행 없는 시도 3건이다. **네 조건이 모두 완료된 묶음은 0개**다. 현재 세 기능의 Context Rot 완화 효과는 미검증이고 1.0 승격은 판단 보류다. CLI 파일럿 범위에서 실행했으며 Paseo 비교는 미실행이다.

## 검증

- 실측 환경은 Windows Codex CLI `0.167.0`, 세 모델 모두 `xhigh`다. 평가 설정은 컨텍스트 창 272,000·자동 압축 기준 231,200이고, 기록된 세션의 모델 사용량 이벤트에서 유효 창 258,400이 관측됐다.
- 평가 대상은 [0.5.1 ZIP](dist/MyCodexSetting-0.5.1.zip)이며 SHA-256은 `e264485389e761abea00cc005b15b2f7b2f54351fc04859d68b69883b5cb7ea3`이다. 압축용 `billion-context 0.1.213`은 이번 실행의 전용 런타임에서 준비·진단했다. Luna의 미완료 사례만으로 압축 효과를 판정할 수 없다.
- 종료 행 5개에서 확인한 사용량의 환산액은 **US$0.357542**다. 시간 초과 행의 미정산 사용량과 종료 행 없는 시도의 비용이 남아 있어 전체 사용액과 잔액은 미확정이다.
- **기존 PC**에서는 사용자가 `MyCodexSetting-Eval`의 읽기 전용 조회 성공을 확인했다. 당시 합성 Trace·점수의 서버 재조회 확인 파일은 없었고, 측정 결과 업로드도 미확인이다. **새 PC**의 인증·전송·재조회는 미실행이다.

## 다음 행동

### 1. 새 PC에서 Langfuse 연결

기존 환경은 Windows·Python 3.13.2였다. 새 PC의 PowerShell에서 이전해 온 저장소 루트를 열고 다음을 실행한다. Langfuse CLI는 필요하지 않다.

```powershell
python -m venv .venv-eval
.\.venv-eval\Scripts\python.exe -m pip install langfuse==5.2.0 tiktoken==0.14.0
.\.venv-eval\Scripts\python.exe -X utf8 -B .\tools\evaluations\langfuse_check.py --smoke
```

프로젝트를 만든 **기존 리전**을 선택하고, 해당 프로젝트의 Public Key와 Secret Key를 사용자 터미널의 숨김 입력란에 넣는다. 키는 채팅·파일에 기록하지 않는다. `연결 확인: MyCodexSetting-Eval`을 확인한 뒤 합성 데이터 전송에 동의하면 `Y`를 입력한다. **같은 실행에서** `클라우드 검증 완료`가 출력되고 `.venv-eval/cloud-smoke-verified.json`에 재조회 결과가 기록되면 새 PC의 연결 확인이 끝난다. 이 명령은 모델을 호출하지 않는다. 인증이나 재조회가 실패하면 해당 단계부터 해결한다.

### 2. 연결 확인 후 파일럿 재개

1. **기존 증거를 대조한다.** 원본 실행 폴더는 **기존 PC의** `%TEMP%\mycodex-rot-pilot-20261119a`다. 이전해 온 `pilot01-*.jsonl` 세 파일이 있으면 원장 JSON의 `journal_sha256`과 대조하고, `cells/pilot01/`이 있으면 중단 셀의 산출물도 확인한다. 임시 폴더를 가져오지 못했으면 저장소의 결과표·원장 JSON을 기준으로 삼고, 복구할 수 없는 사용량과 결과는 미상으로 둔다.
2. **새 실행 환경을 확인한다.** 새 PC의 Codex CLI 경로·버전·로그인, 세 모델과 유효 컨텍스트 창을 확인한다. 0.5.1 ZIP 해시를 대조하고 새 PC 경로에 전용 압축 런타임을 준비·진단한다. 실행 기록에 PC와 시도 ID를 표시한다.
3. **남은 예산으로 조건을 선택한다.** Sol의 JIT 긴 문맥 OFF가 첫 누락 조건이다. 새 PC에서 이 한 조건을 재개할 수 있지만 기존 PC의 세 조건과 합쳐 동일 환경의 네 조건 비교로 판정할 수는 없다. 비교가 필요하면 남은 한도 안에서 새 PC의 네 조건을 한 묶음으로 실행한다. 실행기의 `--models`는 모델만 선택하고 새 `--tag`는 순서와 예산을 초기화하므로 이전 소요시간·미정산 비용을 반영하고 중복 시도를 구분한다.
4. **Terra 인계와 Luna 압축을 이어간다.** 이전 절대 마감은 `2026-11-19T12:23:25+09:00`이었고 실행기에는 세션당 155초 제한이 있다. 시간 초과 원인과 조건 변경을 기록한다. 실제 평가 행은 승인된 필드로만 전송하고 서버의 Trace ID와 점수를 대조한다.

## 재확인 사항

이전 중단 시점에 파일럿 컨트롤러와 보이는 샌드박스 설정 도우미는 각각 0개였다. UAC 창의 개별 출처와 반복 원인은 확정되지 않았다. 병렬 재개에 대한 사용자 동의는 확보됐다. 새 세션에서는 실제 모델 ID·호스트·런타임을 확인하고, 파일럿 결과는 본 실험의 성능 판정과 분리한다.
