"""Exercise the shipped opt-in guide against an isolated React app and ZIP."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

from common import REPO, command, save_new, snapshot


def main(root, source, prior):
    root.mkdir(parents=True, exist_ok=False)
    runtime = root / 'runtime'
    runtime.mkdir()
    save_new(root / 'evidence/source.json', {'kit': snapshot(source / 'kit'), 'source': str(source)})
    package = {'name': 'astryx-opt-in-fixture', 'private': True, 'version': '0.0.0', 'type': 'module',
               'scripts': {'build': 'vite build'}, 'dependencies': {'react': '19.3.1', 'react-dom': '19.3.1'},
               'devDependencies': {'vite': '8.3.8'}}
    save_new(runtime / 'package.json', package)
    env = os.environ.copy()
    env['npm_config_cache'] = str(root / 'npm-cache')
    npm = shutil.which('npm.cmd')
    commands = {
        'existing-react-fixture': [npm, 'install', '--no-audit', '--no-fund'],
        'guide-core-install': [npm, 'install', '--save-exact', '@astryxdesign/core@0.7.16', '@stylexjs/stylex@0.19.0'],
        'guide-cli-install': [npm, 'install', '--save-dev', '--save-exact', '@astryxdesign/cli@0.7.16'],
    }
    for name, args in commands.items():
        result = command(args, runtime, root / f'evidence/{name}.json', timeout=600, env=env)
        print(json.dumps({'step': name, 'exit': result['exit']}), flush=True)
        if result['exit'] != 0:
            raise RuntimeError(name)
    cli = runtime / 'node_modules/.bin/astryx.cmd'
    for name, args in {'version': ['--version'], 'input': ['component', 'TextInput'], 'button': ['component', 'Button'],
                       'search': ['search', 'search input'], 'tailwind': ['docs', 'tailwind'],
                       'build': ['build', 'searchable resource library']}.items():
        result = command([cli, *args], runtime, root / f'evidence/guide-{name}.json', timeout=120, env=env)
        if result['exit'] != 0:
            raise RuntimeError(name)
    installed = json.loads((runtime / 'package.json').read_text(encoding='utf-8'))
    assert installed['dependencies']['react'] == installed['dependencies']['react-dom'] == '19.3.1'
    assert installed['dependencies']['@astryxdesign/core'] == '0.7.16'
    assert installed['devDependencies']['@astryxdesign/cli'] == '0.7.16'
    save_new(root / 'evidence/guide-package.json', installed)
    save_new(root / 'evidence/guide-lock.json', {'sha256': hashlib.sha256((runtime / 'package-lock.json').read_bytes()).hexdigest()})
    # Evaluation-only browser tools, separate from documented consumer install.
    result = command([npm, 'install', '--save-dev', '--save-exact', 'puppeteer-core@25.17.0', 'axe-core@4.10.3'],
                     runtime, root / 'evidence/browser-tool-install.json', timeout=600, env=env)
    if result['exit'] != 0:
        raise RuntimeError('browser tools')
    app = root / 'apps/vite-baseline'
    app.mkdir(parents=True)
    for name in ('index.html', 'src'):
        previous = prior / 'apps/vite-baseline' / name
        if previous.is_dir():
            shutil.copytree(previous, app / name)
        else:
            shutil.copy2(previous, app / name)
    for name in ('package.json', 'package-lock.json'):
        shutil.copy2(runtime / name, app / name)
    result = command([sys.executable, '-X', 'utf8', '-B', source / 'tools/build_release.py', '--output', root / 'release'],
                     source, root / 'evidence/release-build.json')
    if result['exit'] != 0:
        raise RuntimeError('release')
    release = json.loads(result['stdout'])
    archive = Path(release['archive'])
    with ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        zipped.extractall(root / 'unpacked')
    bundle = root / 'unpacked' / archive.stem
    for label, base in [('SA', root / 'bases/SA'), ('zip', root / 'packaging/zip-consumer')]:
        base.mkdir(parents=True)
        shutil.copy2(prior / 'bases/S/PRD.md', base / 'PRD.md')
        kit = source / 'kit' if label == 'SA' else bundle / 'kit'
        args = [sys.executable, '-X', 'utf8', '-B', kit / 'mycodex.py', 'init', '--target', base,
                '--requirements', 'PRD.md']
        before = snapshot(base)
        dry = command(args, source, root / f'evidence/{label}-dry.json')
        assert dry['exit'] == 0 and before == snapshot(base)
        result = command([*args, '--apply'], source, root / f'evidence/{label}-install.json')
        if result['exit'] != 0:
            raise RuntimeError('base install')
        installed_files = snapshot(base)
        repeat = command([*args, '--apply'], source, root / f'evidence/{label}-repeat.json')
        assert repeat['exit'] == 0 and installed_files == snapshot(base)
        manifest = json.loads((base / '.mycodex/manifest.json').read_text(encoding='utf-8'))
        assert manifest['kit_version'] == '0.5.0'
        assert all(hashlib.sha256((base / p).read_bytes()).hexdigest() == h for p, h in manifest['files'].items())
        shutil.copytree(REPO / '.agents/skills/superpowers', base / '.agents/skills/superpowers')
    save_new(root / 'evidence/prepared.json', {'root': str(root), 'version': release['version'],
                                             'zip_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                                             'manifest_assets': len(manifest['files']), 'status': 'PREPARED'})
    print(json.dumps({'root': str(root), 'status': 'PREPARED'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    args = parser.parse_args()
    main(args.root.resolve(), args.source.resolve(), args.prior.resolve())
