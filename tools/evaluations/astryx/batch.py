"""Independent fixture trials, at most three concurrent CLI processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

from common import REPO


def main(root):
    jobs = [(v, c, 1) for c in ('A04-css','A04-python','A04-react18','A04-nonreact','A05-init','A05-html','A05-handoff','A05-doctor','A02') for v in ('S','SA')]
    jobs += [(v,c,2) for c in ('A01','A04-css') for v in ('S','SA')]
    jobs += [('SR','A04-css',1)]
    def execute(job):
        variant,case,repeat=job
        dest=root/'batch-output'/f'{variant}-{case}-{repeat}.txt'
        dest.parent.mkdir(exist_ok=True)
        with dest.open('x',encoding='utf-8') as log:
            args=[sys.executable,'-X','utf8','-B',str(REPO/'tools/evaluations/astryx/model_runs.py'),'turn',
                  '--root',str(root),'--variant',variant,'--case',case,'--repeat',str(repeat)]
            r=subprocess.run(args,cwd=REPO,stdout=log,stderr=log,text=True,encoding='utf-8')
        return {'variant':variant,'case':case,'repeat':repeat,'process_exit':r.returncode}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(execute,j) for j in jobs]
        for future in as_completed(futures):
            print(json.dumps(future.result()),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
