"""Synthetic case preparation and artifact scoring for the 0.5.1 CLI pilot."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import tiktoken


TASK = """Use this synthetic archive project's current approved policy and surviving exception.
Update policy.json (integer keys ordinary and frozen). In status.json report the state BEFORE
this final task of the two checks shape and replay, using passed, failed or not_run.
Perform the outstanding replay check by running python -B replay.py. Only change
policy.json, status.json and the generated replay receipt. Work inside this project."""
RULES = """Work within this synthetic project only. No network, other projects, global configuration,
credentials, subagents or third-party services. Use only local project files and local shell or edit tools.
Do not alter source records or verification scripts. Use UTF-8. Complete the task concisely."""
BEFORE = "Earlier baseline: shape check passed; replay check not_run. Frozen series remains capped at 4."
DECISION = "Approved for estuary archive: ordinary batch cap 13. Keep prior frozen-series exception."
OLD = "Superseded estuary proposal: ordinary batch cap 19, including frozen series. Never approved."


def write(root, name, body):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def prepare(root, kit, feature, long, enabled):
    root.mkdir(parents=True)
    write(root, "records/current.md", DECISION if feature != "handoff" else
          "Approved for estuary archive: ordinary batch cap 11. Retain the frozen-series exception.")
    write(root, "records/retired.md", OLD)
    write(root, "records/evidence.md", BEFORE)
    write(root, "policy.json", '{"ordinary": 9, "frozen": 9}\n')
    write(root, "replay.py",
          "import json\nfrom pathlib import Path\np = json.loads(Path('policy.json').read_text(encoding='utf-8-sig'))\n"
          "assert isinstance(p['ordinary'], int) and isinstance(p['frozen'], int)\n"
          "Path('replay-receipt.json').write_text(json.dumps(p), encoding='utf-8')\nprint('REPLAY_EXECUTED')\n")
    encoder = tiktoken.get_encoding("o200k_base")
    target = (64_000 if long else 8_000) // 8
    history = []
    for i in range(8):
        line = f"Unrelated inland archive shift {i}: records were sorted and queued for review.\n"
        content = line * (target // len(encoder.encode(line)))
        if i == 0:
            content = BEFORE + "\n" + content
        if i == 4:
            content = OLD + "\n" + content
        write(root, f"records/shift-{i+1:02d}.txt", content)
        history.append(content)
    if feature == "handoff":
        subprocess.run([sys.executable, "-X", "utf8", "-B", str(kit / "mycodex.py"), "init",
                        "--target", str(root), "--requirements", "records/current.md", "--apply"],
                       check=True, capture_output=True)
        index = root / ".context/index.md"
        index.write_bytes(index.read_bytes().replace(b"needs-review", b"ready"))
    elif feature == "jit" and enabled:
        write(root, "AGENTS.md", "\n".join((kit / "templates/AGENTS.md").read_text(encoding="utf-8").splitlines()[0:4])+"\n")
        (root / ".mycodex").mkdir()
        shutil.copyfile(kit / "context-policy.md", root / ".mycodex/context-policy.md")
        write(root, ".context/index.md", "# Current sources\n| Topic | Source |\n|---|---|\n"
              "| Current approved policy | records/current.md |\n| Exception and checks | records/evidence.md |\n")
    protected = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [*sorted((root/"records").glob("*")), root/"replay.py"]}
    return history, sum(len(encoder.encode(v)) for v in history), protected


def score(root, replay_seen, protected):
    def read(name):
        try:
            obj = json.loads((root/name).read_text(encoding="utf-8-sig"))
            return obj if isinstance(obj, dict) else {}
        except (OSError, ValueError):
            return {}
    policy, status, receipt = map(read, ["policy.json", "status.json", "replay-receipt.json"])
    scores = {"current": policy.get("ordinary") == 13, "exception": policy.get("frozen") == 4,
              "prior_status": status == {"shape":"passed","replay":"not_run"},
              "next_action": bool(policy) and receipt == policy and replay_seen}
    changed = [name for name, digest in protected.items() if not (root/name).is_file()
               or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest]
    return scores, changed
