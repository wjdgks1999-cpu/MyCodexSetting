"""Check Cloud project access, optionally round-trip one synthetic trace and score."""

import argparse
from getpass import getpass
import json
from pathlib import Path
import sys
import time
from uuid import NAMESPACE_URL, uuid5

import httpx


CLOUD_REGIONS = {
    "EU": "https://cloud.langfuse.com",
    "US": "https://us.cloud.langfuse.com",
    "JP": "https://jp.cloud.langfuse.com",
    "HIPAA": "https://hipaa.cloud.langfuse.com",
}


def smoke_check(client: httpx.Client, project_id: str, region: str) -> int:
    name = "context-eval-setup"
    seed = uuid5(NAMESPACE_URL, f"{client.base_url}{project_id}/{name}/v1")
    trace_id = seed.hex
    span_id = uuid5(seed, "span").hex[:16]
    score_id = str(uuid5(seed, "score"))

    def lookup() -> tuple[bool, bool]:
        observations = client.get("/api/public/v2/observations", params={"traceId": trace_id, "fields": "core"})
        observations.raise_for_status()
        scores = client.get("/api/public/v3/scores", params={"traceId": trace_id, "name": name})
        scores.raise_for_status()
        span_found = any(row.get("id") == span_id and row.get("traceId") == trace_id
                         and row.get("name") == name for row in observations.json()["data"])
        score_found = any(row.get("id") == score_id and row.get("traceId") == trace_id
                          and row.get("name") == name and row.get("value") == 1
                          for row in scores.json()["data"])
        return span_found, score_found

    span_found, score_found = lookup()
    if not span_found:
        start = time.time_ns()
        span = {"traceId": trace_id, "spanId": span_id, "name": name,
                "startTimeUnixNano": str(start), "endTimeUnixNano": str(start + 1_000_000)}
        response = client.post("/api/public/otel/v1/traces", headers={"x-langfuse-ingestion-version": "4"},
                               json={"resourceSpans": [{"scopeSpans": [{"spans": [span]}]}]})
        response.raise_for_status()
    if not score_found:
        response = client.post("/api/public/scores", json=[{
            "id": score_id, "traceId": trace_id, "name": name, "dataType": "NUMERIC", "value": 1,
        }])
        response.raise_for_status()
        if response.status_code == 207 and response.json().get("rejected", 0):
            print("Langfuse가 점수를 거절했습니다.")
            return 1

    deadline = time.monotonic() + 60
    while not (span_found and score_found):
        span_found, score_found = lookup()
        if span_found and score_found:
            break
        if time.monotonic() >= deadline:
            print("서버 조회 반영 대기 중입니다. 같은 명령을 다시 실행하면 같은 ID로 확인합니다.")
            return 1
        time.sleep(4)
    receipt = Path(__file__).resolve().parents[2] / ".venv-eval" / "cloud-smoke-verified.json"
    receipt.write_text(json.dumps({"region": region, "trace_id": trace_id, "score_id": score_id,
                                   "name": name, "value": 1}), encoding="utf-8")
    print("클라우드 검증 완료: 합성 Trace 1건과 점수 1건을 조회했습니다.")
    return 0


def main(smoke: bool = False) -> int:
    if not sys.stdin.isatty():
        print("PowerShell 터미널에서 직접 실행해 주세요.", file=sys.stderr)
        return 1

    region = input("프로젝트 리전 (EU / US / JP / HIPAA): ").strip().upper()
    if region not in CLOUD_REGIONS:
        print("프로젝트 화면 주소에 해당하는 리전을 선택해 주세요.")
        return 1
    project = "MyCodexSetting-Eval"
    if not smoke:
        project = input(f"평가 프로젝트 이름 [{project}]: ").strip() or project
    base_url = CLOUD_REGIONS[region]
    print(f"{base_url}에서 프로젝트를 조회합니다. 키 입력은 화면에 표시되지 않습니다.")
    public = getpass("Public Key: ").strip()
    secret = getpass("Secret Key: ").strip()
    if not public or not secret:
        print("프로젝트 키 두 개가 필요합니다.")
        return 1

    try:
        response = httpx.get(
            base_url + "/api/public/projects", auth=(public, secret),
            timeout=15.0, follow_redirects=False,
        )
        if response.status_code != 200:
            print(f"조회 실패 (HTTP {response.status_code}). 리전과 프로젝트 키를 확인해 주세요.")
            return 1
        body = response.json()
    except (httpx.HTTPError, ValueError):
        print("프로젝트 응답을 확인할 수 없습니다. 네트워크 연결과 리전을 확인해 주세요.")
        return 1
    projects = body.get("data") if isinstance(body, dict) else None
    if not (isinstance(projects, list) and len(projects) == 1
            and isinstance(projects[0], dict) and projects[0].get("name") == project):
        print("키에 연결된 프로젝트가 입력한 평가 프로젝트와 일치하는지 확인해 주세요.")
        return 1
    print(f"연결 확인: {project} ({region})")
    if smoke:
        print("전송할 합성 데이터: context-eval-setup Trace 1건과 숫자 점수 1건(값 1), ID 및 시각.")
        if input("이 프로젝트에 전송하고 결과를 조회하려면 Y를 입력하세요: ").strip().upper() != "Y":
            print("전송을 취소했습니다.")
            return 0
        try:
            with httpx.Client(base_url=base_url, auth=(public, secret), timeout=15.0,
                              follow_redirects=False) as client:
                return smoke_check(client, projects[0]["id"], region)
        except httpx.HTTPStatusError as error:
            print(f"Cloud 점검 실패 (HTTP {error.response.status_code}, {error.request.url.path}).")
        except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError):
            print("Cloud 요청, 응답 형식 또는 로컬 결과 기록을 확인해 주세요.")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Send and verify synthetic setup data after confirmation.")
    try:
        sys.exit(main(smoke=parser.parse_args().smoke))
    except (EOFError, KeyboardInterrupt):
        sys.exit("입력을 취소했습니다.")
