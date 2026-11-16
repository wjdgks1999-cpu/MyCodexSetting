"""Independent assertions on completed fixture files, never on model claims."""
import argparse
import json
from pathlib import Path
import re
import sys

from common import command, preserves_labeled_items, save_new, snapshot
from model_runs import runner
from human_check import Document


def main(root, output):
    rows=[]
    for variant in ('S','SA','SR'):
        for run in sorted((root/'runs'/variant).glob('*/*')):
            if not (run/'turn-1.json').exists():continue
            case=run.parent.name
            target=run/'project'
            before=json.loads((run/'baseline.json').read_text(encoding='utf-8'))
            after=snapshot(target)
            changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
            checks={}
            if case=='A04-css':
                checks['exact_requested_css']= (target/'site/styles.css').read_text(encoding='utf-8')==runner.CSS.replace('margin-left:8px','margin-left:12px')
                checks['only_stylesheet_changed']=changed==['site/styles.css']
            elif case=='A04-python':
                r=command([sys.executable,'-X','utf8','-B','-m','unittest','-v','test_search.py'],target,
                          root/f'evidence/independent-{variant}-python-{run.name}-{output.stem}.json')
                checks['real_test_exit_zero']=r['exit']==0
                checks['ui_unchanged']=all(after.get(k)==h for k,h in before.items() if k.startswith('site/'))
            elif case in ('A04-react18','A04-nonreact'):
                checks['files_unchanged']=changed==[]
            elif case=='A05-init':
                r=command([sys.executable,'-X','utf8','-B',target/'.mycodex/mycodex.py','validate','--target',target,'--strict','--json'],target,
                          root/f'evidence/independent-{variant}-init-{run.name}-{output.stem}.json')
                checks['strict_valid']=r['exit']==0
                checks['only_index_changed']=changed==['.context/index.md']
            elif case=='A05-html':
                html=list((target/'.human-docs').glob('*.html'))
                checks['one_html']=len(html)==1
                for file in html:
                    body=file.read_text(encoding='utf-8')
                    doc=Document();doc.feed(body)
                    text=re.sub(r'\s+',' ',' '.join(doc.text))
                    checks['all_30_labels']=all(re.search(r'항목\s*'+f'{n:03}',text) for n in range(1,31))
                    checks['all_30_item_bodies']=preserves_labeled_items(text,30,'출처와 기준일을 확인하고 자료 변경 여부를 기록한다.')
                    checks['no_external_resources']=not any(not r.startswith(('data:','#')) for r in doc.resources)
                    checks['no_external_css']=not bool(re.search(r'@import\b|url\(\s*[\'"]?https?://',body,re.I))
                checks['source_index_unchanged']=after.get('.context/index.md')==before.get('.context/index.md')
                checks['no_package_install']=not (target/'package.json').exists() and not (target/'node_modules').exists()
            if checks:
                rows.append({'id':f'{variant}/{case}/{run.name}','checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL'})
    save_new(output,rows)
    print(json.dumps(rows,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.output)
