"""Install pinned dependencies only inside the supplied new evaluation root."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

from common import PIN, REPO, command, protected_state, save_new, snapshot


def main(root):
    save_new(root / 'evidence/protected-before.json', protected_state())
    upstream = root / 'upstream'
    for rel in ('plugins/astryx/skills/astryx/SKILL.md', 'plugins/astryx/.codex-plugin/plugin.json', 'LICENSE'):
        url = f'https://raw.githubusercontent.com/meta/astryx/{PIN}/{rel}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MyCodexSetting-evaluation'})
        data = urllib.request.urlopen(req, timeout=60).read()
        out = upstream / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('xb') as stream:
            stream.write(data)
    save_new(root / 'evidence/upstream.json', {'commit': PIN, 'files': snapshot(upstream)})
    runtime = root / 'runtime'
    runtime.mkdir()
    dependencies = {'@astryxdesign/core': '0.7.16', '@astryxdesign/cli': '0.7.16',
                    'react': '19.3.1', 'react-dom': '19.3.1', '@stylexjs/stylex': '0.19.0',
                    'vite': '8.3.8', 'next': '16.4.6', 'tailwindcss': '4.3.5',
                    '@tailwindcss/postcss': '4.3.5', 'puppeteer-core': '25.17.0', 'axe-core': '4.10.3'}
    save_new(runtime / 'package.json', {'name': 'astryx-compatibility-fixture', 'version': '0.0.0', 'private': True, 'dependencies': dependencies})
    env = os.environ.copy()
    env['npm_config_cache'] = str(root / 'npm-cache')
    result = command([shutil.which('npm.cmd'), 'install', '--no-audit', '--no-fund'], runtime,
                     root / 'evidence/npm-install.json', timeout=600, env=env)
    print(json.dumps({'install_exit': result['exit'], 'seconds': result['seconds'], 'stdout_tail': result['stdout'][-1800:], 'stderr_tail': result['stderr'][-1500:]}))
    if result['exit'] != 0:
        return
    cli = runtime / 'node_modules/.bin/astryx.cmd'
    commands = {'version': ['--version'], 'help': ['--help'], 'init-help': ['init', '--help'],
                'search': ['search', 'button input search form'], 'button': ['component', 'Button'],
                'input': ['component', 'Input'], 'layout': ['docs', 'layout'],
                'template-help': ['template', '--help'], 'doctor': ['doctor']}
    for name, args in commands.items():
        r = command([cli, *args], runtime, root / f'evidence/cli-{name}.json', timeout=90, env=env)
        print(json.dumps({'command': name, 'exit': r['exit'], 'output_chars': len(r['stdout'])}))
    save_new(root / 'evidence/protected-after-install.json', protected_state())
    for variant in ('S', 'SR'):
        base = root / 'bases' / variant
        base.mkdir(parents=True)
        (base / 'PRD.md').write_text('# 공공데이터 길잡이\n한국어 자료 검색 서비스를 개발한다. 문구와 브랜드를 보존한다.\n외부 서비스 없이 로컬 합성 데이터만 사용한다.\n', encoding='utf-8')
        r = command([sys.executable, '-X', 'utf8', '-B', REPO / 'kit/mycodex.py', 'init', '--target', base,
                     '--requirements', 'PRD.md', '--apply'], REPO, root / f'evidence/base-{variant}.json')
        if r['exit'] != 0:
            raise RuntimeError('base install failed')
        shutil.copytree(REPO / '.agents/skills/superpowers', base / '.agents/skills/superpowers')
        if variant == 'SR':
            shutil.copytree(upstream / 'plugins/astryx/skills/astryx', base / '.agents/skills/astryx')
        command(['git', 'init', '-q', base], root, root / f'evidence/git-{variant}.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    main(p.parse_args().root.resolve())
