"""Collect measured evidence only. Human-reviewed verdicts are separate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from checks import changed_product_files, completed_commands, skill_read_commands, unexpected_changes
from run import save, snapshot


def events(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def evidence_fingerprint(folder):
    paths = [folder / 'baseline.json']
    for pattern in ('events-*.jsonl', 'turn-*.json', 'stderr-*.txt'):
        paths.extend(folder.glob(pattern))
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def attach_verdict(row, verdict, evidence):
    if not verdict.get('evidence_sha256') or verdict['evidence_sha256'] != evidence:
        raise ValueError('Reviewed verdict does not match the current evidence')
    for key in ('status', 'reason', 'excluded_turns'):
        if key in verdict:
            row[key] = verdict[key]


def collect(root, repo, verdict_path=None, summary_output=None):
    verdicts = json.loads(verdict_path.read_text(encoding='utf-8')) if verdict_path else {}
    source_path = root / 'evidence/source-hashes.json'
    source = json.loads(source_path.read_text(encoding='utf-8'))
    protected = {name: unexpected_changes(before, snapshot(repo / name), []) for name, before in source.items()}
    runs = []
    for folder in sorted((root / 'runs').glob('*/*/*')):
        turns = []
        for path in sorted(folder.glob('turn-*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            trace = events(folder / f"events-{data['turn']}.jsonl")
            calls = [e['item'] for e in trace if e.get('type') == 'item.completed' and 'item' in e]
            commands = completed_commands(trace)
            turns.append({'turn': data['turn'], 'thread_id': data['thread_id'], 'seconds': data['seconds'],
                          'exit_code': data['exit_code'], 'usage': data['usage'],
                          'hallmark_reads': len(skill_read_commands(trace, 'hallmark')),
                          'human_html_reads': len(skill_read_commands(trace, 'human-html')),
                          'event_types': dict(Counter(i.get('type') for i in calls)),
                          'unrelated_html_content_exposed': any('UNRELATED_HTML_CANARY_HALLMARK_7319' in i.get('aggregated_output', '') for i in commands),
                          'changed_count': len(data['changed'])})
        if not turns:
            continue
        target = folder / 'project'
        before = json.loads((folder / 'baseline.json').read_text(encoding='utf-8'))
        after = snapshot(target)
        variant, case, repeat = folder.relative_to(root / 'runs').parts
        protected_paths = ['AGENTS.md', 'PRD.md', 'docs/design.md', 'docs/plan.md',
                           'site/app.js', 'site/logo.svg', '.context/index.md']
        row = {'run_id': f'{variant}/{case}/{repeat}', 'case_id': case, 'variant': variant,
               'repeat': int(repeat), 'host': 'Windows Codex CLI 0.167.0', 'model': 'gpt-6.1-sol',
               'source_hashes': {'manifest': str(source_path),
                                  'manifest_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()},
               'status': 'NEEDS_REVIEW', 'reason': 'Evidence collection is not a compatibility verdict.',
               'evidence_paths': [str(folder)], 'metrics': {'turns': turns},
               'baseline_file_preservation': {p: before.get(p) == after.get(p) for p in protected_paths if p in before},
               'new_or_changed_product_files': changed_product_files(before, after),
               'evidence_sha256': evidence_fingerprint(folder),
               'incomplete_turns': [p.name for p in folder.glob('events-*.jsonl')
                                    if not (folder / p.name.replace('events-', 'turn-').replace('.jsonl', '.json')).exists()]}
        verdict = verdicts.get(row['run_id'])
        if verdict:
            attach_verdict(row, verdict, row['evidence_sha256'])
            row['verdict_source'] = str(verdict_path)
        if row['incomplete_turns']:
            row['status'] = 'IN_PROGRESS'
        row['metrics']['nonexcluded_turn_seconds'] = round(sum(
            turn['seconds'] for turn in turns if turn['turn'] not in row.get('excluded_turns', [])), 2)
        save(folder / 'run.json', row)
        runs.append(row)
    summary = {'protected_source_changes': protected, 'runs': runs}
    save(root / 'evidence/measured-summary.json', summary)
    if summary_output:
        save(summary_output, summary)
    print(json.dumps({'protected_source_changes': protected, 'runs': [
        {'id': r['run_id'], 'preserved': r['baseline_file_preservation'],
         'seconds': sum(t['seconds'] for t in r['metrics']['turns']),
         'canary_exposed': any(t['unrelated_html_content_exposed'] for t in r['metrics']['turns']),
         'incomplete': r['incomplete_turns']} for r in runs]}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--verdicts', type=Path)
    parser.add_argument('--summary-output', type=Path)
    args = parser.parse_args()
    collect(args.root, args.repo, args.verdicts, args.summary_output)
