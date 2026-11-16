"""Repeat observed installation and Korean word-budget failures, not model trials."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from package_probe import execute
from run import save


def main(root):
    dest = root / 'deterministic-repeats'
    dest.mkdir()
    os.environ['HALLMARK_PUPPETEER'] = str(root / 'browser-runtime')
    installer = []
    language = []
    for repeat in range(1, 4):
        for mode in ('raw-managed', 'explicit-metadata'):
            target = dest / f'{mode}-{repeat}'
            target.mkdir()
            (target / 'PRD.md').write_text('# Installation repeat\nNo product implementation.\n', encoding='utf-8')
            cli = root / 'packaging' / mode / 'source/kit/mycodex.py'
            install = execute([sys.executable, '-X', 'utf8', '-B', str(cli), 'init', '--target', str(target),
                               '--requirements', 'PRD.md', '--apply'])
            checked = execute([sys.executable, '-X', 'utf8', '-B', str(target / '.mycodex/mycodex.py'),
                               'validate', '--target', str(target), '--strict', '--json'])
            installer.append({'mode': mode, 'repeat': repeat, 'install_exit': install['exit'],
                              'validation': json.loads(checked['stdout'])})
        for lang in ('en', 'ko'):
            target = dest / f'{lang}-{repeat}'
            target.mkdir()
            html = target / f'{lang}-page.html'
            shutil.copy2(root / 'static' / html.name, html)
            script = root / 'upstream/skills/hallmark/scripts/sloplint.mjs'
            for render in (False, True):
                command = ['node', str(script), str(html), '--scope', 'page', '--json']
                if render:
                    command.append('--render')
                result = execute(command, timeout=120)
                report = json.loads(result['stdout'])
                save(target / ('render.json' if render else 'static.json'), report)
                language.append({'lang': lang, 'repeat': repeat, 'render_requested': render,
                                 'process_exit': result['exit'], 'summary': report['summary'],
                                 'word_budget': [f for f in report['findings'] if str(f.get('gate')) == '58']})
    summary = {'installer': installer, 'language': language}
    save(dest / 'result.json', summary)
    print(json.dumps({'installer': [{'mode': r['mode'], 'repeat': r['repeat'],
                                    'errors': [f['code'] for f in r['validation']['findings']]} for r in installer],
                      'language': [{'lang': r['lang'], 'repeat': r['repeat'],
                                    'render': r['summary']['render'], 'gate_58_count': len(r['word_budget'])}
                                   for r in language]}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
