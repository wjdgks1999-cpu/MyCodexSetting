"""Opt-in real Codex evaluation runner. No model calls occur on import.

Run from the authenticated host user, using a host-created temporary root.
The CLI keeps its normal authentication; no credentials are read or copied.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile

from checks import changed_paths, skill_read_commands, render_status, redact

PIN = '04977e15f3dfd6ee4b74c887dac3eb52665d6c92'
CASES = json.loads(Path(__file__).with_name('cases.json').read_text(encoding='utf-8'))
MODEL = 'gpt-6.1-sol'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(data), ensure_ascii=False, indent=2), encoding='utf-8')


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()
            and not any(x in ('.git', '__pycache__', 'node_modules') for x in p.relative_to(root).parts)}


def prepare(root, repo):
    upstream = root / 'upstream'
    if not upstream.exists():
        req = urllib.request.Request(f'https://codeload.github.com/nutlope/hallmark/zip/{PIN}',
                                     headers={'User-Agent': 'MyCodexSetting-compatibility-test'})
        archive = urllib.request.urlopen(req, timeout=60).read()
        z = zipfile.ZipFile(io.BytesIO(archive))
        for member in z.infolist():
            rel = Path(*Path(member.filename).parts[1:])
            if member.is_dir() or not (rel.as_posix().startswith('skills/hallmark/') or
                                       rel.as_posix() in ('LICENSE', 'package.json', 'install.mjs', 'install-hook.mjs')):
                continue
            dest = (upstream / rel).resolve()
            if not dest.is_relative_to(upstream.resolve()):
                raise ValueError('unsafe archive entry')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(member))
        save(root / 'evidence/upstream.json', {'commit': PIN, 'archive_sha256': hashlib.sha256(archive).hexdigest(),
                                              'files': snapshot(upstream)})
    if not (root / 'evidence/source-hashes.json').exists():
        hashes = {base: snapshot(repo / base) for base in ('kit', '.mycodex', '.agents/skills/superpowers', 'dist', '.codex')}
        save(root / 'evidence/source-hashes.json', hashes)
    for variant in ('B', 'S', 'H', 'SH', 'SH-E'):
        base = root / 'bases' / variant
        if base.exists():
            continue
        base.mkdir(parents=True)
        (base / 'PRD.md').write_text('# 공공데이터 길잡이\n\n한국어 공공데이터 이용자를 위한 자료 검색 서비스. 차분하고 명료한 화면. '
                                    '기존 문구와 로고를 보존한다. 이미지 자료는 로컬 SVG만 사용하고 외부 이미지/API는 사용하지 않는다. '
                                    '임의의 이용자 수·후기·실적을 만들지 않는다. 소개 페이지와 검색 도구가 대상이다.\n', encoding='utf-8')
        r = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(repo / 'kit/mycodex.py'), 'init',
                            '--target', str(base), '--requirements', 'PRD.md', '--apply'], capture_output=True, text=True, encoding='utf-8')
        if r.returncode:
            raise RuntimeError(r.stdout + r.stderr)
        if 'S' in variant:
            shutil.copytree(repo / '.agents/skills/superpowers', base / '.agents/skills/superpowers')
        if 'H' in variant:
            shutil.copytree(upstream / 'skills/hallmark', base / '.agents/skills/hallmark')
        if variant == 'SH-E':
            policy = base / '.agents/skills/hallmark/agents/openai.yaml'
            policy.write_text(policy.read_text(encoding='utf-8').replace('allow_implicit_invocation: true',
                                                                       'allow_implicit_invocation: false'), encoding='utf-8')
        # Defaults remain identical; comparison changes only the extra skill folders.
        subprocess.run(['git', 'init', '-q', str(base)], check=True, capture_output=True)
    print(json.dumps({'root': str(root), 'prepared': ['B', 'S', 'H', 'SH', 'SH-E']}))


def config_args(root):
    result = ['-c', 'features.memories=false', '-c', 'memories.generate_memories=false',
              '-c', 'memories.use_memories=false', '-c', 'features.hooks=false',
              '-c', 'model_reasoning_effort="xhigh"', '-c', 'skills.bundled.enabled=false']
    disabled = [{'name': name, 'enabled': False} for name in ('find-skills', 'orca-cli')]
    # TOML inline tables rather than JSON objects.
    result += ['-c', 'skills.config=[' + ','.join('{name=' + json.dumps(x['name']) + ',enabled=false}' for x in disabled) + ']']
    result += ['-c', 'developer_instructions=' + json.dumps(
        'This is an authorized isolated compatibility evaluation. Work only in the current fixture repository. '
        'Do not create external sites or projects, publish, deploy, push, commit, call image generation APIs, '
        'or change global settings or skills. Do not read authentication files or environment secrets. '
        'Local reports and screenshots are allowed. Follow the applicable project and skill workflows. '
        'Read Korean files with explicit UTF-8. These constraints apply to every turn.', ensure_ascii=True)]
    return result


def list_skills(root, exe, cwd):
    args = [str(exe), 'app-server', '--stdio', *config_args(root)]
    proc = subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding='utf-8')
    output = queue.Queue()
    def read_lines():
        for line in proc.stdout:
            try: output.put(json.loads(line))
            except ValueError: pass
        output.put(None)
    threading.Thread(target=read_lines, daemon=True).start()
    # Drain stderr without persisting provider/config messages.
    threading.Thread(target=lambda: proc.stderr.read(), daemon=True).start()
    def rpc(request):
        proc.stdin.write(json.dumps(request) + '\n'); proc.stdin.flush()
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            event = output.get(timeout=max(0.1, deadline - time.monotonic()))
            if event is None: raise RuntimeError('app-server exited')
            if event.get('id') == request.get('id'): return event
        raise TimeoutError('app-server response')
    try:
        rpc({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'hallmark_eval', 'version': '1.0'},
                                                        'capabilities': {'experimentalApi': True}}})
        proc.stdin.write('{"method":"initialized"}\n'); proc.stdin.flush()
        result = rpc({'id': 2, 'method': 'skills/list', 'params': {'cwds': [str(cwd)], 'forceReload': True}})
        save(root / 'evidence' / ('skills-' + cwd.name + '.json'), result)
        data = result.get('result', {}).get('data', [])
        print(json.dumps({'cwd': str(cwd), 'groups': [{'enabled': [s['name'] for s in d['skills'] if s['enabled']],
                                                     'errors': d.get('errors', [])} for d in data],
                          'error': result.get('error')}, ensure_ascii=False))
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()


HTML = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>공공데이터 길잡이</title><link rel="stylesheet" href="styles.css"></head><body><header><img src="logo.svg" width="40" height="40" alt="공공데이터 길잡이"><h1>공공데이터 길잡이</h1><p>자료 · 검색</p></header><main><form id="search-form"><label for="q">자료 검색</label><input id="q"><button id="search" type="submit">검색</button><label for="category">분야</label><select id="category"><option value="all">전체</option><option value="water">물</option><option value="transport">교통</option></select></form><ul id="results"><li data-category="water">하천 수질 자료</li><li data-category="transport">대중교통 자료</li></ul><form id="contact"><label for="email">문의 이메일</label><input id="email" type="email" required><button type="submit">문의 보내기</button><output id="status"></output></form></main><footer>공개 자료의 출처와 기준일을 확인하세요.</footer><script src="app.js"></script></body></html>'''
CSS = ':root{--brand:#6d28d9;--text:#17212b;--paper:#fff}body{margin:0 auto;max-width:960px;padding:24px;color:var(--text);background:var(--paper);font-family:Arial,sans-serif}header{display:flex;align-items:center;gap:12px;flex-wrap:wrap}form{margin:24px 0}#search{margin-left:8px}button{padding:12px;background:var(--brand);color:white}input,select{padding:10px}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #085} @media(max-width:480px){body{padding:12px}form{display:flex;gap:8px;flex-wrap:wrap}}'
JS = "document.querySelector('#search-form').addEventListener('submit',e=>{e.preventDefault();const q=document.querySelector('#q').value;const c=document.querySelector('#category').value;document.querySelectorAll('#results li').forEach(li=>li.hidden=!li.textContent.includes(q)||(c!=='all'&&li.dataset.category!==c));});document.querySelector('#contact').addEventListener('submit',e=>{e.preventDefault();document.querySelector('#status').textContent='문의가 접수되었습니다.';});"


def fixture(root, variant, case, repeat):
    run = root / 'runs' / variant / case / str(repeat)
    target = run / 'project'
    if target.exists(): return run, target
    shutil.copytree(root / 'bases' / variant, target)
    (target / 'docs').mkdir()
    design = '# 승인된 설계\n\n상태: 승인됨. 이 문서의 수정은 요청되지 않았다.\n\n로고 logo.svg, 브랜드 색상 #6d28d9, 제목 공공데이터 길잡이, 문구 자료 · 검색을 보존한다. 검색·분야 필터·이메일 문의 폼을 유지한다. 정적 HTML/CSS/JS로 만들며 외부 의존성·이미지 API는 사용하지 않는다. 사이트 파일은 site/ 아래에 둔다. 구현·검증은 현재 세션에서 직접 수행한다. 커밋·push·배포는 하지 않는다.\n'
    (target / 'docs/design.md').write_text(design, encoding='utf-8')
    (target / 'docs/plan.md').write_text('# 승인된 구현 계획\n\n1. site/index.html, styles.css, app.js와 logo.svg를 만든다.\n2. 검색·필터·문의 동작을 구현한다.\n3. 가능한 실제 검증을 실행하고 미실행을 보고한다.\n\n실행 방식: 이 세션에서 직접 구현.\n', encoding='utf-8')
    index = target / '.context/index.md'
    body = index.read_text(encoding='utf-8')
    if case in ('S02', 'S05', 'S09'):
        body = body.replace('| active-spec | `none` |  |', '| active-spec | `docs/design.md` | 승인 설계 |')
        body = body.replace('| active-plan | `none` |  |', '| active-plan | `docs/plan.md` | 승인 구현 계획 |')
    index.write_text(body, encoding='utf-8')
    if case == 'S09' and variant.startswith('S'):
        body = body.replace('status: needs-review', 'status: ready')
        body += '\n## Evaluation setup review\n\nThe evaluator checked the PRD, source paths, installed asset inventory, and actual skills/list availability of Superpowers. This marks configuration review only; no product or browser test is claimed.\n'
        index.write_text(body, encoding='utf-8')
    # S01 must have no approved design artifact.
    if case in ('S01', 'S08'):
        (target / 'docs/design.md').unlink(); (target / 'docs/plan.md').unlink()
    if CASES[case]['site']:
        site = target / 'site'; site.mkdir()
        for name, content in {'index.html': HTML, 'styles.css': CSS, 'app.js': JS,
                               'logo.svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" fill="#6d28d9"/><path d="M10 28V12h20v16" stroke="white" fill="none"/></svg>'}.items():
            (site / name).write_text(content, encoding='utf-8')
    if case == 'S04':
        (target / 'search.py').write_text('def sort_records(records):\n    return sorted(records, key=lambda row: row["id"], reverse=True)\n', encoding='utf-8')
        (target / 'test_search.py').write_text('import unittest\nfrom search import sort_records\nclass SearchTest(unittest.TestCase):\n    def test_ascending(self):\n        self.assertEqual([x["id"] for x in sort_records([{ "id": 2 }, { "id": 1 }])], [1,2])\n', encoding='utf-8')
    if case == 'S07':
        with (target / 'PRD.md').open('a', encoding='utf-8') as file:
            file.write('\n## 상세 설명 시험 자료\n\n아래 항목들은 설명 보존 시험을 위한 합성 자료다.\n')
            for n in range(1, 61):
                file.write(f'\n- 항목 {n:03}: 자료의 출처와 기준일은 원본 제공기관의 설명에서 확인하며 변경 여부는 별도 기록한다.\n')
    if case in ('S07', 'S08', 'S09'):
        other = target / '.human-docs/unrelated.html'
        other.parent.mkdir(exist_ok=True)
        other.write_text('<!doctype html><html lang="en"><body>UNRELATED_HTML_CANARY_HALLMARK_7319</body></html>', encoding='utf-8')
    save(run / 'baseline.json', snapshot(target))
    return run, target


def validate_session(run, session):
    if session is None:
        return
    owned = {json.loads(p.read_text(encoding='utf-8')).get('thread_id') for p in run.glob('turn-*.json')}
    if session not in owned:
        raise ValueError('Resume session does not belong to this fixture')


def reserve_turn(run):
    completed = {int(p.stem.split('-')[-1]) for p in run.glob('turn-*.json')}
    attempts = {int(p.stem.split('-')[-1]) for pattern in ('events-*.jsonl', 'stderr-*.txt') for p in run.glob(pattern)}
    if attempts - completed:
        raise RuntimeError('An incomplete attempt exists; preserve its evidence and use a new fixture repeat')
    n = max(completed | attempts, default=0) + 1
    # Reserve before spawning a model. Exclusive creation prevents concurrent overwrite.
    for name in (f'events-{n}.jsonl', f'stderr-{n}.txt'):
        with (run / name).open('x', encoding='utf-8'):
            pass
    return n


def turn(root, exe, variant, case, repeat, prompt_file=None, session=None):
    run, target = fixture(root, variant, case, repeat)
    validate_session(run, session)
    prompt = Path(prompt_file).read_text(encoding='utf-8') if prompt_file else CASES[case]['prompt']
    if not prompt_file and variant in ('B', 'S'):
        prompt = prompt.replace('$hallmark redesign site/index.html', '기존 site/index.html을 재설계해주세요.')
        prompt = prompt.replace('$hallmark audit site/index.html', 'site/index.html의 디자인을 감사하고 보고서를 작성해주세요.')
    before = snapshot(target)
    args = [str(exe), '--no-daemon', '--approve-for-me', 'exec']
    if session: args += ['resume', session]
    args += ['--ignore-user-config', '--json', '-m', MODEL, *config_args(root)]
    if not session: args += ['-C', str(target)]
    args += ['-']
    start = time.monotonic()
    env = os.environ.copy()
    env.pop('TOGETHER_API_KEY', None)
    if (root / 'browser-runtime/node_modules/puppeteer-core').exists():
        env['HALLMARK_PUPPETEER'] = str(root / 'browser-runtime')
    n = reserve_turn(run)
    proc = subprocess.Popen(args, cwd=target, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding='utf-8', env=env)
    collected = {'out': [], 'err': []}
    def drain(stream, key, path):
        with path.open('a', encoding='utf-8') as file:
            for line in stream:
                try: line = json.dumps(redact(json.loads(line)), ensure_ascii=False) + '\n'
                except ValueError: line = redact(line)
                collected[key].append(line)
                file.write(line); file.flush()
    readers = [threading.Thread(target=drain, args=(proc.stdout, 'out', run / f'events-{n}.jsonl')),
               threading.Thread(target=drain, args=(proc.stderr, 'err', run / f'stderr-{n}.txt'))]
    for reader in readers: reader.start()
    proc.stdin.write(prompt); proc.stdin.close()
    try: proc.wait(timeout=1800)
    except subprocess.TimeoutExpired:
        proc.terminate(); proc.wait(timeout=15)
    for reader in readers: reader.join(timeout=15)
    out, err = ''.join(collected['out']), ''.join(collected['err'])
    events = []
    for line in out.splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    after = snapshot(target)
    result = {'variant': variant, 'case': case, 'repeat': repeat, 'turn': n, 'exit_code': proc.returncode,
              'seconds': round(time.monotonic()-start, 2), 'model': MODEL, 'effort': 'xhigh',
              'harness_revision': 'evidence-preserving-v2',
              'prompt': prompt, 'changed': changed_paths(before, after),
              'hallmark_read': skill_read_commands(events, 'hallmark'),
              'render_status': render_status(events), 'thread_id': session,
              'messages': [e['item']['text'] for e in events if e.get('type') == 'item.completed'
                           and e.get('item', {}).get('type') == 'agent_message'],
              'usage': [e.get('usage') for e in events if e.get('type') == 'turn.completed']}
    for e in events:
        if e.get('type') == 'thread.started': result['thread_id'] = e['thread_id']
    save(run / f'turn-{n}.json', result)
    display = dict(result)
    display['messages'] = [m[:1800] for m in result['messages']]
    print(json.dumps(redact(display), ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'skills', 'turn', 'summary'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--exe', type=Path, default=Path(os.environ['LOCALAPPDATA']) / 'Programs/OpenAI/Codex/bin/codex.exe')
    parser.add_argument('--variant', choices=['B', 'S', 'H', 'SH', 'SH-E'], default='SH')
    parser.add_argument('--case', choices=list(CASES), default='S01')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--prompt-file')
    parser.add_argument('--session')
    args = parser.parse_args()
    if args.action == 'prepare': prepare(args.root, args.repo)
    elif args.action == 'skills': list_skills(args.root, args.exe, args.root / 'bases' / args.variant)
    elif args.action == 'summary':
        for folder in sorted((args.root / 'runs').glob('*/*/*')):
            logs = sorted(folder.glob('events-*.jsonl'), key=lambda p: int(p.stem.split('-')[1]))
            if not logs: continue
            latest = logs[-1]
            done = folder / latest.name.replace('events-', 'turn-').replace('.jsonl', '.json')
            if done.exists():
                d = json.loads(done.read_text(encoding='utf-8'))
                print(json.dumps({'run': folder.relative_to(args.root).as_posix(), 'done': True,
                                  'seconds': d['seconds'], 'changed': d['changed'],
                                  'hallmark_reads': len(d['hallmark_read']),
                                  'last_message': d['messages'][-1][-850:] if d['messages'] else ''}, ensure_ascii=False))
            else:
                completed = []
                for line in latest.read_text(encoding='utf-8').splitlines():
                    try:
                        e = json.loads(line)
                        if e.get('type') == 'item.completed': completed.append(e['item'])
                    except ValueError: pass
                messages = [i.get('text', '') for i in completed if i.get('type') == 'agent_message']
                print(json.dumps({'run': folder.relative_to(args.root).as_posix(), 'done': False,
                                  'items': len(completed), 'last_message': messages[-1][-450:] if messages else ''}, ensure_ascii=False))
    else: turn(args.root, args.exe, args.variant, args.case, args.repeat, args.prompt_file, args.session)


if __name__ == '__main__':
    main()
