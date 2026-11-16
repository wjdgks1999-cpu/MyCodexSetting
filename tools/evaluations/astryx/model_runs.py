"""Real CLI turns using the existing evidence-preserving evaluation runner."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from common import REPO, save_new, snapshot

LEGACY = REPO / 'tools/evaluations/hallmark'
sys.path.insert(0, str(LEGACY))
spec = importlib.util.spec_from_file_location('existing_runner', LEGACY / 'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

CASES = {
    'A01': '공공데이터 서비스를 소개하는 새 웹페이지를 만들어줘.',
    'A04-css': '기존 site/index.html 검색 버튼의 margin-left만 8px에서 12px로 수정해주세요. 다른 디자인, 문구, 동작은 바꾸지 마세요.',
    'A04-python': 'search.py의 sort_records는 id 오름차순이어야 합니다. 정렬 오류를 고치고 test_search.py로 확인해주세요. 웹 UI는 변경하지 마세요.',
    'A04-react18': 'React 18 프로젝트입니다. $astryx로 UI를 개선할 수 있는지 호환성을 확인해주세요. 기존 React 버전을 보존하세요. 구현은 호환성 확인 이후입니다.',
    'A04-nonreact': '현재는 정적 HTML 프로젝트입니다. $astryx로 버튼 디자인을 개선할 수 있는지 확인해주세요. 프레임워크 전환은 승인하지 않았습니다.',
    'A05-init': '$project-init',
    'A05-html': '$human-html PRD.md의 서비스 구조를 설명하는 독립적인 오프라인 HTML을 만들어주세요. 모든 합성 설명 항목을 보존해주세요.',
    'A05-handoff': '$session-handoff',
    'A05-doctor': '$context-compression Codex CLI 연결 상태를 진단해주세요. 현재 대화에 압축이 적용됐다고 가정하지 마세요.',
    'A02': '$astryx docs/design.md와 docs/plan.md는 승인되었습니다. 이 세션에서 직접 구현하세요. 기존 src/App.jsx의 검색 입력과 버튼만 Astryx TextInput과 Button으로 교체하세요. 기존 한국어 문구, 검색/분야 필터/문의 폼 동작, 로고, 브랜드 색상과 바깥 레이아웃을 보존하세요. 의존성은 이미 준비되어 있습니다. 새로운 scaffold나 AGENTS 변경은 필요하지 않습니다. npm.cmd run build로 검증하고 커밋하지 마세요.',
    'A08-zip': '$astryx 로컬 CLI로 Button 컴포넌트 문서를 실제 조회하고 현재 프로젝트 React 버전과 호환되는지 알려주세요. 파일은 변경하지 마세요.',
}


def fixture(root, variant, case, repeat):
    run = root / 'runs' / variant / case / str(repeat)
    target = run / 'project'
    if target.exists():
        return run, target
    if case == 'A08-zip':
        source = root / 'packaging/zip-consumer'
    else:
        source = root / 'bases' / variant
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
    if case.startswith('A04') or case in ('A05-handoff', 'A05-doctor'):
        site = target / 'site'
        site.mkdir()
        (site / 'index.html').write_text(runner.HTML, encoding='utf-8')
        (site / 'styles.css').write_text(runner.CSS, encoding='utf-8')
        (site / 'app.js').write_text(runner.JS, encoding='utf-8')
        (site / 'logo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="#6d28d9"/></svg>', encoding='utf-8')
    if case == 'A04-python':
        (target / 'search.py').write_text('def sort_records(records):\n    return sorted(records, key=lambda row: row["id"], reverse=True)\n', encoding='utf-8')
        (target / 'test_search.py').write_text('import unittest\nfrom search import sort_records\nclass SearchTest(unittest.TestCase):\n    def test_ascending(self):\n        self.assertEqual([r["id"] for r in sort_records([{"id":2},{"id":1}])],[1,2])\n', encoding='utf-8')
    if case == 'A04-react18':
        save_new(target / 'package.json', {'name': 'legacy-react-fixture', 'private': True, 'dependencies': {'react': '18.3.1', 'react-dom': '18.3.1'}})
    if case == 'A05-html':
        with (target / 'PRD.md').open('a', encoding='utf-8') as stream:
            stream.write('\n## 합성 설명 자료\n')
            for n in range(1, 31):
                stream.write(f'\n- 항목 {n:03}: 출처와 기준일을 확인하고 자료 변경 여부를 기록한다.\n')
    if case in ('A02', 'A08-zip'):
        app = root / 'apps/vite-baseline'
        for p in app.rglob('*'):
            if not p.is_file() or any(x in ('node_modules', 'dist', '.git') for x in p.relative_to(app).parts):
                continue
            dest = target / p.relative_to(app)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
        # The dependency directory is shared read-only by contract; no installs in this case.
        subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(target / 'node_modules'), str(root / 'runtime/node_modules')], check=True, capture_output=True)
        docs = target / 'docs'
        docs.mkdir(exist_ok=True)
        (docs / 'design.md').write_text('# 승인된 설계\nReact 19 + Vite, 기존 UI 기능·브랜드·문구를 보존하며 입력과 검색 버튼만 Astryx로 교체한다. 별도 scaffold/init은 하지 않는다.\n', encoding='utf-8')
        (docs / 'plan.md').write_text('# 승인된 구현 계획\n1. 로컬 Astryx CLI로 TextInput과 Button API를 조회한다.\n2. src/App.jsx의 입력/검색 버튼을 교체한다.\n3. npm.cmd run build로 확인한다.\n실행: 현재 세션 직접 구현. 외부 서비스와 커밋 금지.\n', encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(target)], check=True, capture_output=True)
    save_new(run / 'baseline.json', snapshot(target))
    return run, target


def main(args):
    runner.fixture = fixture
    runner.snapshot = snapshot
    runner.CASES = {k: {'prompt': v} for k, v in CASES.items()}
    old_config = runner.config_args
    def config(root):
        opts = old_config(root)
        # Keep existing guard; add fixture-specific dependency restrictions.
        opts += ['-c', 'features.apps=false', '-c', 'features.plugins=false',
                 '-c', 'features.remote_plugin=false', '-c', 'features.plugin_discovery_prefetch=false']
        return opts
    runner.config_args = config
    os.environ['PATH'] = str(args.root / 'runtime/node_modules/.bin') + os.pathsep + os.environ['PATH']
    os.environ['npm_config_cache'] = str(args.root / 'npm-cache')
    os.environ['ASTRYX_EVAL_ROOT'] = str(args.root)
    if args.action == 'skills':
        runner.list_skills(args.root, args.exe, args.root / 'bases' / args.variant)
    elif args.action == 'prepare':
        run, target = fixture(args.root, args.variant, args.case, args.repeat)
        print(target)
    else:
        run, target = fixture(args.root, args.variant, args.case, args.repeat)
        config_path = run / 'configuration.json'
        if not config_path.exists():
            save_new(config_path, {'revision': 'plugin-isolation-v2', 'plugins': False, 'apps': False,
                                   'model': runner.MODEL, 'effort': 'xhigh'})
        runner.turn(args.root, args.exe, args.variant, args.case, args.repeat, args.prompt_file, args.session)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'skills', 'turn'])
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--variant', choices=['S', 'SA', 'SR'], default='SA')
    p.add_argument('--case', choices=CASES, default='A01')
    p.add_argument('--repeat', type=int, default=1)
    p.add_argument('--prompt-file')
    p.add_argument('--session')
    p.add_argument('--exe', type=Path, default=Path(os.environ['LOCALAPPDATA']) / 'Programs/OpenAI/Codex/bin/codex.exe')
    main(p.parse_args())
