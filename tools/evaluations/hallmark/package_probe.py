"""Exercise packaging in disposable copies. Does not select a product design."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def execute(args, cwd=None, timeout=60):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    return {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def main(root, repo):
    output = []
    for mode in ('raw-managed', 'explicit-metadata'):
        base = root / 'packaging' / mode
        if base.exists():
            raise RuntimeError('Preserve existing packaging evidence; choose a new root')
        source = base / 'source'
        shutil.copytree(repo / 'kit', source / 'kit')
        for name in ('README.md', 'CHANGELOG.md', 'docs/usage.md', 'tools/build_release.py'):
            dest = source / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / name, dest)
        skill = source / 'kit/skills/hallmark'
        shutil.copytree(root / 'upstream/skills/hallmark', skill)
        shutil.copy2(root / 'upstream/LICENSE', skill / 'LICENSE')
        model = source / 'kit/mycodex_lib/model.py'
        text = model.read_text(encoding='utf-8')
        text = text.replace("SKILL_NAMES = ('project-init', 'session-handoff', 'human-html', 'context-compression')",
                            "SKILL_NAMES = ('project-init', 'session-handoff', 'human-html', 'context-compression', 'hallmark')")
        assets = ['.agents/skills/hallmark/' + p.relative_to(skill).as_posix() for p in skill.rglob('*') if p.is_file()]
        text += '\nREQUIRED_ASSETS.update(' + repr(sorted(assets)) + ')\n'
        model.write_text(text, encoding='utf-8')
        if mode == 'explicit-metadata':
            policy = skill / 'agents/openai.yaml'
            policy.write_text(policy.read_text(encoding='utf-8').replace('allow_implicit_invocation: true',
                                                                       'allow_implicit_invocation: false'), encoding='utf-8')
        target = base / 'consumer'; target.mkdir(parents=True)
        (target / 'PRD.md').write_text('# Packaging fixture\nOnly installation is under test.\n', encoding='utf-8')
        cmd = [sys.executable, '-X', 'utf8', '-B', str(source / 'kit/mycodex.py'), 'init',
               '--target', str(target), '--requirements', 'PRD.md']
        before = hashes(target)
        dry = execute(cmd)
        dry_unchanged = before == hashes(target)
        applied = execute(cmd + ['--apply'])
        validation = execute([sys.executable, '-X', 'utf8', '-B', str(target / '.mycodex/mycodex.py'),
                              'validate', '--target', str(target), '--strict', '--json'])
        # needs-review is intentionally retained; no fake initialization approval.
        installed = hashes(target)
        reinstall = execute(cmd + ['--apply'])
        reinstall_unchanged = installed == hashes(target)
        release = execute([sys.executable, '-X', 'utf8', '-B', str(source / 'tools/build_release.py'),
                           '--output', str(base / 'release')])
        zip_files = list((base / 'release').glob('*.zip'))
        zip_ok = False
        if zip_files:
            with zipfile.ZipFile(zip_files[0]) as archive:
                names = archive.namelist()
                expected = {'kit/skills/hallmark/' + p.relative_to(skill).as_posix() for p in skill.rglob('*') if p.is_file()}
                actual = {'/'.join(n.split('/')[1:]) for n in names}
                zip_ok = expected <= actual and archive.testzip() is None
        # A changed installed asset must be preserved and rejected on reinstall.
        policy = target / '.agents/skills/hallmark/agents/openai.yaml'
        policy.write_text(policy.read_text(encoding='utf-8') + '\n# user edit\n', encoding='utf-8')
        edited = hashes(target)
        conflict = execute(cmd + ['--apply'])
        row = {'mode': mode, 'dry_run_unchanged': dry_unchanged, 'install_exit': applied['exit'],
               'validation': json.loads(validation['stdout']), 'reinstall_exit': reinstall['exit'],
               'reinstall_unchanged': reinstall_unchanged, 'release': release, 'all_skill_assets_in_zip': zip_ok,
               'skill_asset_count': len(assets), 'edited_reinstall_exit': conflict['exit'],
               'edited_assets_preserved': edited == hashes(target)}
        (base / 'result.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        output.append(row)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    args = p.parse_args(); main(args.root, args.repo)
