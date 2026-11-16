"""Freeze observed evidence and separately labelled manual scope judgments."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from collect import collect
from common import PIN, REPO, save_new


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(root, output):
    rows = collect(root)
    if len(rows) != 29 or sum(r['turns'] for r in rows) != 33:
        raise RuntimeError('Expected 29 completed case instances and 33 CLI turns; do not finalize incomplete evidence.')
    independent = json.loads((root / 'evidence/independent-final.json').read_text(encoding='utf-8'))
    for row in rows:
        initial_failure = row['id'] == 'SA/A01/1'
        row['manual_scope_judgment'] = {
            'status': 'FAIL' if initial_failure else 'PASS',
            'scope': 'case-specific behavior only, not universal compatibility',
            'attribution': 'INCONCLUSIVE: Sites read, no Astryx body or CLI read' if initial_failure else 'observed test configuration',
        }
        row['changed'] = [p for p in row['changed'] if '/.chrome-profile/' not in p]
        row.pop('final_messages')
    evidence = {}
    for path in sorted((root / 'evidence').rglob('*')):
        if path.is_file() and path.suffix in ('.json', '.jsonl', '.txt', '.png'):
            evidence[path.relative_to(root).as_posix()] = sha(path)
    package = json.loads((root / 'runtime/package.json').read_text(encoding='utf-8'))
    handoffs = {v: json.loads((root / f'evidence/handoff-{v}-result.json').read_text(encoding='utf-8')) for v in ('S', 'SA')}
    for value in handoffs.values():
        value.pop('final')
        value.pop('handoff_final')
    browsers = {}
    for name in ('vite-baseline-r2', 'vite-candidate-r2', 'next-baseline-r2', 'next-candidate-r2',
                 'vite-model-S', 'vite-model-SA', 'template-library-r2'):
        data = json.loads((root / f'evidence/ui/{name}/browser/browser.json').read_text(encoding='utf-8'))
        browsers[name] = {k: data[k] for k in ('status', 'checks', 'accessibility', 'viewports') if k in data}
    source_hashes = {}
    for base in (REPO / 'tools/evaluations/astryx', REPO / 'tools/evaluations/hallmark'):
        for path in sorted(base.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                source_hashes[path.relative_to(REPO).as_posix()] = sha(path)
    summary = {
        'schema_version': 1,
        'date': '2026-11-16',
        'evidence_root': str(root),
        'upstream_commit': PIN,
        'dependencies': package.get('dependencies', {}),
        'dev_dependencies': package.get('devDependencies', {}),
        'lockfile_sha256': sha(root / 'runtime/package-lock.json'),
        'model': 'gpt-6.1-sol', 'effort': 'xhigh', 'codex_cli': '0.167.0',
        'case_instances': len(rows),
        'cli_turns': sum(r['turns'] for r in rows),
        'additional_real_compression_turns': 3,
        'manual_case_counts': dict(Counter(r['manual_scope_judgment']['status'] for r in rows)),
        'judgment_method': 'Manual log/file review, backed by independent checks; process exit zero alone is not PASS.',
        'adoption': {
            'explicit_react19_cli_candidate': 'SUPPORTED_IN_TESTED_SCOPE',
            'all_hosts_default_feature': 'DEFERRED',
            'raw_plugin_drop_in': 'FAIL_CURRENT_MANAGED_METADATA_CONTRACT',
            'production_integrated': False,
            'unrestricted_host_plugins': 'INCONCLUSIVE_ATTRIBUTION_WITH_ONE_OBSERVED_APPROVAL_GATE_FAILURE',
        },
        'limitations': ['OS Korean IME NOT_RUN', 'Codex app and Paseo NOT_RUN',
                        'No unrestricted global plugin matrix', 'Not all Astryx components or screen readers tested',
                        'Full CSS reset/Theme integration recipe changes existing styles',
                        'Next/template tests are authored fixtures, not model workflow trials',
                        'Guard forbids global installs and external services in every model group',
                        'Synthetic compression blocks are not a general token/cost savings benchmark',
                        'Raw logs live in a local temporary directory, not in the repository'],
        'runs': rows, 'independent_file_checks': independent, 'handoffs': handoffs,
        'browser_observations': browsers,
        'compression_restoration': json.loads((root / 'evidence/compression/restoration-verification.json').read_text(encoding='utf-8')),
        'protected_state_unchanged': (root / 'evidence/protected-before.json').read_bytes() == (root / 'evidence/protected-final.json').read_bytes(),
        'evidence_sha256': evidence, 'harness_sha256': source_hashes,
    }
    save_new(output, summary)
    print(json.dumps({k: summary[k] for k in ('case_instances', 'cli_turns', 'manual_case_counts', 'protected_state_unchanged')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.root, args.output)
