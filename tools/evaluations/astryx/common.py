"""Small evidence helpers; never interpret exit zero as compatibility PASS."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hallmark'))
from checks import redact

REPO = Path(__file__).resolve().parents[3]
PIN = '5051ea96a35307183e9f3fab7fadcc7b0d649e45'


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(redact(value), stream, ensure_ascii=False, indent=2)


def snapshot(root):
    result = {}
    if not root.exists():
        return result
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', '.next')]
        for name in files:
            p = Path(base) / name
            if not p.is_symlink():
                result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def process_status(code):
    return 'INCONCLUSIVE' if code is None else 'PROCESS_OK' if code == 0 else 'FAIL'


def preserves_labeled_items(text, count, sentence):
    return all(re.search(r'항목\s*' + f'{n:03}' + r'\s*:?\s*' + re.escape(sentence), text)
               for n in range(1, count + 1))


def command(args, cwd, evidence, timeout=300, env=None):
    # Reserve evidence before execution; retries need a new evidence filename.
    evidence.parent.mkdir(parents=True, exist_ok=True)
    with evidence.open('x', encoding='utf-8'):
        pass
    start = time.monotonic()
    try:
        result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        data = {'args': [str(a) for a in args], 'cwd': str(cwd), 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        data = {'args': [str(a) for a in args], 'cwd': str(cwd), 'exit': None, 'timeout': True,
                'stdout': (error.stdout or b'').decode('utf-8', errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                'stderr': (error.stderr or b'').decode('utf-8', errors='replace') if isinstance(error.stderr, bytes) else error.stderr}
    data['seconds'] = round(time.monotonic() - start, 2)
    evidence.write_text(json.dumps(redact(data), ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def protected_state(repo=REPO):
    user = Path(os.environ['USERPROFILE'])
    result = {name: snapshot(repo / name) for name in ('kit', '.mycodex', '.agents/skills/superpowers', '.codex', 'dist')}
    for name in ('.agents/skills', '.claude/skills', '.codex/skills'):
        result['global/' + name] = snapshot(user / name)
    p = user / '.codex/config.toml'
    result['global/config'] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return result
