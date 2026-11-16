"""Verify the disposable release without changing the real kit or release."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

from package_probe import execute, hashes


def main(root, repo, output_name):
    if Path(output_name).name != output_name:
        raise ValueError('output-name must be a single directory name')
    base = root / output_name
    base.mkdir()  # Never overwrite earlier evidence.
    archive_path, = (root / 'packaging/explicit-metadata/release').glob('*.zip')
    extracted = base / 'extracted'
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            dest = (extracted / member.filename).resolve()
            if not dest.is_relative_to(extracted.resolve()):
                raise ValueError('unsafe archive entry')
        archive.extractall(extracted)
    release, = extracted.iterdir()
    cli = release / 'kit/mycodex.py'
    rows = []
    for mode in ('clean', 'existing-user-files'):
        target = base / mode
        target.mkdir()
        (target / 'PRD.md').write_text('# ZIP fixture\nInstallation only; no application implementation.\n', encoding='utf-8')
        preserved = {}
        if mode == 'existing-user-files':
            (target / '.codex').mkdir()
            preserved = {'AGENTS.md': b'# User instructions\nKeep this file.\n',
                         '.codex/config.toml': b'model = "fixture-user-choice"\n'}
            for name, data in preserved.items():
                (target / name).write_bytes(data)
        cmd = [sys.executable, '-X', 'utf8', '-B', str(cli), 'init', '--target', str(target), '--requirements', 'PRD.md']
        before = hashes(target)
        dry = execute(cmd)
        dry_unchanged = before == hashes(target)
        applied = execute(cmd + ['--apply'])
        installed = hashes(target)
        repeat = execute(cmd + ['--apply'])
        manifest = json.loads((target / '.mycodex/manifest.json').read_text(encoding='utf-8'))
        valid_assets = all(hashlib.sha256((target / p).read_bytes()).hexdigest() == h
                           for p, h in manifest['files'].items())
        result = execute([sys.executable, '-X', 'utf8', '-B', str(target / '.mycodex/mycodex.py'),
                          'validate', '--target', str(target), '--strict', '--json'])
        rows.append({'mode': mode, 'dry_exit': dry['exit'], 'dry_unchanged': dry_unchanged,
                     'apply_exit': applied['exit'], 'reinstall_exit': repeat['exit'],
                     'reinstall_unchanged': installed == hashes(target),
                     'user_files_preserved': all((target / p).read_bytes() == data for p, data in preserved.items()),
                     'manifest_assets_match': valid_assets, 'manifest_count': len(manifest['files']),
                     'initial_validation': json.loads(result['stdout']),
                     'initialization_review': 'NOT_RUN: needs-review deliberately retained',
                     'behavior_after_zip_install': 'NOT_RUN'})
    # Run the existing product suite against the modified temporary kit.
    candidate = root / 'packaging/explicit-metadata/source'
    if not (candidate / 'tests').exists():
        shutil.copytree(repo / 'tests', candidate / 'tests', ignore=shutil.ignore_patterns('__pycache__', 'evaluations'))
    # Save completed installation evidence before the slower regression suite.
    (base / 'consumers.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    regression = execute([sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], candidate, timeout=600)
    (base / 'candidate-suite.txt').write_text(regression['stdout'] + regression['stderr'], encoding='utf-8')
    summary = {'zip_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(), 'consumers': rows,
               'candidate_suite_exit': regression['exit'], 'candidate_suite_tail': regression['stderr'][-700:]}
    (base / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output-name', default='zip-consumer-check')
    args = parser.parse_args()
    main(args.root, args.repo, args.output_name)
