"""Read evidence conservatively; manual judgments remain separate from exit codes."""
import argparse
import hashlib
import json
from pathlib import Path

from common import REPO, save_new, snapshot
from checks import completed_commands, skill_read_commands


def collect(root):
    rows=[]
    for folder in sorted((root/'runs').glob('*/*/*')):
        turns=[]
        for path in sorted(folder.glob('turn-*.json')):
            turns.append(json.loads(path.read_text(encoding='utf-8')))
        if not turns:
            continue
        events=[]
        evidence={}
        for pattern in ('events-*.jsonl','turn-*.json','stderr-*.txt','baseline.json','configuration.json'):
            for path in sorted(folder.glob(pattern)):
                evidence[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
                if path.suffix=='.jsonl':
                    for line in path.read_text(encoding='utf-8').splitlines():
                        try:events.append(json.loads(line))
                        except ValueError:pass
        commands=completed_commands(events)
        config_path=folder/'configuration.json'
        config=json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {'revision':'initial-host-plugins-present'}
        rows.append({'id':folder.relative_to(root/'runs').as_posix(),'configuration':config,
                     'turns':len(turns),'exit_codes':[t['exit_code'] for t in turns],
                     'seconds':sum(t['seconds'] for t in turns),'changed':sorted({p for t in turns for p in t['changed']}),
                     'astryx_skill_reads':skill_read_commands(events,'astryx'),
                     'successful_astryx_commands':[c['command'] for c in commands if c.get('exit_code')==0
                         and 'astryx' in c.get('command','').lower()
                         and 'package: @astryxdesign/' in c.get('aggregated_output','')
                         and any(x in c.get('aggregated_output','') for x in ('# Button','# TextInput','domain:','The Tailwind'))],
                     'sites_reads':[c['command'] for c in commands if '/sites/' in c.get('command','').replace('\\','/')],
                     'final_messages':[t['messages'][-1] if t['messages'] else '' for t in turns],
                     'evidence_sha256':evidence})
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    rows=collect(a.root)
    if a.output:save_new(a.output,rows)
    for r in rows:
        print(json.dumps({'id':r['id'],'config':r['configuration']['revision'],'exit':r['exit_codes'],'changed':[p for p in r['changed'] if '/.chrome-profile/' not in p],
                          'skill_reads':len(r['astryx_skill_reads']),'cli_commands':len(r['successful_astryx_commands']),
                          'sites_reads':len(r['sites_reads']),'final':r['final_messages'][-1][-380:]},ensure_ascii=False))
