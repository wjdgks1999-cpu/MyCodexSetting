"""Observe upstream init and preservation in disposable projects/homes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from common import REPO, command, protected_state, save_new, snapshot


def main(root):
    cli = root / 'runtime/node_modules/.bin/astryx.cmd'
    base = root / 'install-probes'
    base.mkdir()
    rows = []
    for mode in ('codex', 'default', 'malformed'):
        target = base / mode
        shutil.copytree(root / 'bases/S', target, ignore=shutil.ignore_patterns('.git'))
        shutil.copy2(root / 'runtime/package.json', target / 'package.json')
        agents = target / 'AGENTS.md'
        original = agents.read_text(encoding='utf-8') + '\n사용자 보존 문구: 출처를 확인하고 승인된 계획을 따른다.\n'
        if mode == 'malformed':
            original += '\n<!-- ASTRYX:START -->\nUSER_EDIT_WITHOUT_END\n'
        agents.write_text(original, encoding='utf-8')
        (target / '.codex/config.toml').write_text('model = "fixture-preserved-choice"\n', encoding='utf-8')
        before = snapshot(target)
        args = [cli, 'init', '--json'] + (['--agent', 'codex'] if mode != 'default' else [])
        first = command(args, target, root / f'evidence/init-{mode}-1.json')
        after = snapshot(target)
        text = agents.read_text(encoding='utf-8')
        again = command(args, target, root / f'evidence/init-{mode}-2.json')
        rows.append({'mode': mode, 'first_exit': first['exit'], 'repeat_exit': again['exit'],
                     'user_text_preserved': original in text, 'config_preserved': before['.codex/config.toml'] == after.get('.codex/config.toml'),
                     'start_markers': text.count('<!-- ASTRYX:START -->'), 'end_markers': text.count('<!-- ASTRYX:END -->'),
                     'line_count': len(text.splitlines()), 'repeat_unchanged': after == snapshot(target),
                     'changed': sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k)),
                     'whole_tree_preserved': before == after})
    # npm 11 did not auto-run unapproved scripts. Run exactly the inspected local scripts.
    runtime = root / 'runtime'
    env = os.environ.copy()
    env.update(INIT_CWD=str(runtime), npm_command='install')
    local_before = snapshot(runtime)
    for package in ('core', 'cli'):
        r = command(['node', runtime / f'node_modules/@astryxdesign/{package}/scripts/postinstall.mjs'], runtime,
                    root / f'evidence/postinstall-{package}.json', env=env)
        rows.append({'mode': f'postinstall-{package}', 'exit': r['exit'], 'runtime_user_files_preserved': local_before == snapshot(runtime)})
    # Test computer-scope collision logic without touching the real user's home.
    home = base / 'synthetic-home'
    home.mkdir()
    env = os.environ.copy()
    for key in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'XDG_CONFIG_HOME'):
        env[key] = str(home / key.lower()) if key not in ('HOME', 'USERPROFILE') else str(home)
    env['PATH'] = str(cli.parent) + os.pathsep + env['PATH']
    r = command([cli, 'init', '--user', '--json'], home, root / 'evidence/fake-home-init.json', env=env)
    skill = home / '.agents/skills/astryx/SKILL.md'
    created = skill.exists()
    if created:
        with skill.open('a', encoding='utf-8') as stream:
            stream.write('\nUSER_EDIT_KEEP\n')
    before = snapshot(home)
    repeat = command([cli, 'init', '--user', '--json'], home, root / 'evidence/fake-home-edited-repeat.json', env=env)
    rows.append({'mode': 'synthetic-home-edited-skill', 'first_exit': r['exit'], 'repeat_exit': repeat['exit'],
                 'skill_created': created, 'edited_files_preserved': before == snapshot(home)})
    foreign = base / 'foreign-home'
    skill = foreign / '.agents/skills/astryx/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('---\nname: astryx\ndescription: Foreign user skill\n---\nKEEP_FOREIGN\n', encoding='utf-8')
    for key in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'XDG_CONFIG_HOME'):
        env[key] = str(foreign / key.lower()) if key not in ('HOME', 'USERPROFILE') else str(foreign)
    original = skill.read_bytes()
    r = command([cli, 'init', '--user', '--json'], foreign, root / 'evidence/fake-home-foreign.json', env=env)
    rows.append({'mode': 'foreign-skill', 'exit': r['exit'], 'foreign_skill_preserved': skill.read_bytes() == original})
    # Characterize direct inclusion of the upstream skill under the real managed policy.
    source = base / 'raw-kit'
    shutil.copytree(REPO / 'kit', source)
    shutil.copytree(root / 'upstream/plugins/astryx/skills/astryx', source / 'skills/astryx')
    model = source / 'mycodex_lib/model.py'
    model.write_text(model.read_text(encoding='utf-8').replace("'context-compression')", "'context-compression', 'astryx')", 1), encoding='utf-8')
    target = base / 'raw-consumer'
    target.mkdir()
    (target / 'PRD.md').write_text('# Fixture\n', encoding='utf-8')
    r = command([sys.executable, '-X', 'utf8', '-B', source / 'mycodex.py', 'init', '--target', target,
                 '--requirements', 'PRD.md', '--apply'], base, root / 'evidence/raw-managed-install.json')
    rows.append({'mode': 'raw-managed', 'install_exit': r['exit'], 'stdout': r['stdout']})
    save_new(root / 'evidence/install-probe-results.json', rows)
    current = protected_state()
    save_new(root / 'evidence/protected-after-probes.json', current)
    original = json.loads((root / 'evidence/protected-before.json').read_text(encoding='utf-8'))
    print(json.dumps({'results': rows, 'protected_unchanged': original == current}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    main(p.parse_args().root)
