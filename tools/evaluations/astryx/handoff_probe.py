"""Finish initialization/handoff, then resume in a genuinely new CLI thread."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from common import REPO, save_new, snapshot


def main(root):
    prompts=root/'evidence/handoff-prompts'
    prompts.mkdir()
    init=prompts/'init-and-handoff.txt'
    init.write_text('$project-init 현재 원본과 설정을 검토하고 준비가 되면 ready로 전환하세요. 이어서 $session-handoff 로 정식 인계를 기록해주세요. 기존 site 파일과 동작은 보존하세요.',encoding='utf-8')
    resume=prompts/'new-thread-resume.txt'
    resume.write_text('새 세션에서 이전 작업을 이어갑니다. .context/index.md의 최신 인계와 현재 PRD.md를 다시 읽고, 최신 결정 표식과 다음 작업을 설명하세요. 파일 수정이나 구현은 하지 마세요.',encoding='utf-8')
    def trial(variant):
        run=root/'runs'/variant/'A05-handoff/1'
        target=run/'project'
        old=json.loads((run/'turn-1.json').read_text(encoding='utf-8'))
        args=[sys.executable,'-X','utf8','-B',str(REPO/'tools/evaluations/astryx/model_runs.py'),'turn','--root',str(root),'--variant',variant,'--case','A05-handoff']
        with (run/'continuation-console.txt').open('x',encoding='utf-8') as log:
            r=subprocess.run(args+['--session',old['thread_id'],'--prompt-file',str(init)],cwd=REPO,stdout=log,stderr=log)
        if r.returncode: return {'variant':variant,'init_process_exit':r.returncode}
        with (target/'PRD.md').open('a',encoding='utf-8') as stream:
            stream.write('\n최신 결정 표식: HANDOFF_CURRENT_4861. 다음 작업은 모바일 레이블 검토이며 구현은 아직 승인하지 않았다.\n')
        before=snapshot(target)
        with (run/'new-thread-console.txt').open('x',encoding='utf-8') as log:
            r=subprocess.run(args+['--prompt-file',str(resume)],cwd=REPO,stdout=log,stderr=log)
        turns=[json.loads((run/f'turn-{n}.json').read_text(encoding='utf-8')) for n in (1,2,3)]
        row={'variant':variant,'new_thread':turns[0]['thread_id']!=turns[2]['thread_id'],
             'resume_files_unchanged':before==snapshot(target),'final':turns[2]['messages'][-1],
             'handoff_final':turns[1]['messages'][-1],'process_exit':r.returncode}
        save_new(root/f'evidence/handoff-{variant}-result.json',row)
        return row
    with ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(trial,('S','SA')):print(json.dumps(row,ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
