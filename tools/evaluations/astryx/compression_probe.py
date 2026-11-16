"""Approved synthetic real-model compression exercise, no credential reads."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from common import REPO, redact, save_new
from model_runs import runner


def main(root, phase):
    project=root/'compression/project'
    evidence=root/'evidence/compression'
    evidence.mkdir(parents=True,exist_ok=True)
    if phase=='exercise':
        data=project/'synthetic'
        data.mkdir()
        for chunk in range(1,9):
            lines=[]
            for row in range(1,101):
                marker=' ASTRYX_RESTORE_CANARY_72831 group=11 sample=0319' if chunk==1 and row==19 else ''
                lines.append(f'chunk={chunk:02} row={row:03} synthetic public-data observation: catalog category water or transport; approved branding stays purple; React19 UI uses local files; no request is sent; original source is authoritative.{marker}')
            (data/f'chunk-{chunk:02}.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        prompt='$astryx 승인된 호환성 시험입니다. 제품 구현은 하지 마세요. 먼저 로컬 Astryx CLI로 TextInput 문서를 실제 조회하고, synthetic/chunk-01.txt부터 chunk-08.txt까지 차례로 각 파일 전체를 도구로 읽으세요. 이들은 압축 검증을 위한 합성 기록입니다. 여러 읽기 호출 이후 압축 도구가 제공되면 acp_status로 가능한 범위를 확인하고 오래된 읽기 결과를 실제 compress 하세요. 최근 메시지 보호 설정은 바꾸지 마세요. 압축이 가능하지 않으면 이유를 기록하세요. 이어 search_context와 decompress로 첫 파일의 CANARY 표식이 있는 원문을 파일로 복원하고, 복원 파일을 실제 읽어 표식·group·sample 값을 보고하세요. 원래 파일 재열람만으로 복원을 입증했다고 하지 마세요. 브라우저나 외부 서비스는 필요 없습니다. 인증 파일과 환경 비밀값은 읽지 마세요.'
        session=None
    elif phase=='api':
        first=json.loads((evidence/'exercise-result.json').read_text(encoding='utf-8'))
        session=first['thread_id']
        shutil.copy2(root/'runtime/package.json',project/'package.json')
        shutil.copy2(root/'runtime/package-lock.json',project/'package-lock.json')
        subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(project/'node_modules'),str(root/'runtime/node_modules')],check=True,capture_output=True)
        prompt='$astryx 시험 준비 누락을 바로잡아 현재 프로젝트에 React19와 로컬 CLI 의존성을 준비했습니다. 현재 package.json과 실제 설치 버전을 확인한 뒤 .\\node_modules\\.bin\\astryx.cmd component TextInput을 실제 실행하세요. 기존 .context/astryx-restore-original.txt의 복원 표식도 다시 확인하고 API 조회 결과를 답해주세요. 파일을 수정하거나 설치하거나 UI를 구현하지 마세요.'
    else:
        first=json.loads((evidence/'exercise-result.json').read_text(encoding='utf-8'))
        session=first['thread_id']
        with (project/'PRD.md').open('a',encoding='utf-8') as stream:
            stream.write('\n## 최신 변경\n승인 대상 프로젝트의 React 버전은 18이다. 설치된 시험 의존성과 다르면 그 차이를 보고한다. 버전 전환과 패키지 설치는 승인하지 않았다. 현재 결정 표식: CURRENT_REACT18_9162.\n')
        prompt='$astryx PRD.md가 변경됐습니다. 현재 원본을 다시 읽고 설치나 UI 구현 없이 Astryx 호환성을 판단해주세요. 이전 요약이 현재 원본을 대신하지 않게 하며 최신 결정 표식과 React 버전을 답해주세요.'
    args=[sys.executable,'-X','utf8','-B',str(project/'.mycodex/mycodex.py'),'compression','codex','--target',str(project),
          '--runtime',str(root/'compression/runtime'),'--apply','--','--approve-for-me','exec']
    if session:args+=['resume',session]
    args+=['--ignore-user-config','--json','-m',runner.MODEL,*runner.config_args(root),'-c','features.plugins=false','-c','features.remote_plugin=false','-c','features.apps=false']
    if not session:args+=['-C',str(project)]
    args+=['-']
    env=os.environ.copy()
    env['MYCODEX_CODEX_EXE']=str(Path(os.environ['LOCALAPPDATA'])/'Programs/OpenAI/Codex/bin/codex.exe')
    env['PATH']=str(root/'runtime/node_modules/.bin')+os.pathsep+env['PATH']
    env.pop('TOGETHER_API_KEY',None)
    out=evidence/f'{phase}-events.jsonl'
    err=evidence/f'{phase}-stderr.txt'
    for p in (out,err):
        with p.open('x',encoding='utf-8'):pass
    save_new(evidence/f'{phase}-input.json',{'prompt':prompt,'session':session,'model':runner.MODEL,'effort':'xhigh'})
    start=time.monotonic()
    proc=subprocess.Popen(args,cwd=project,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
    def drain(stream,path):
        with path.open('a',encoding='utf-8') as f:
            for line in stream:
                try:line=json.dumps(redact(json.loads(line)),ensure_ascii=False)+'\n'
                except ValueError:line=redact(line)
                f.write(line);f.flush()
    threads=[threading.Thread(target=drain,args=(proc.stdout,out)),threading.Thread(target=drain,args=(proc.stderr,err))]
    for t in threads:t.start()
    proc.stdin.write(prompt);proc.stdin.close()
    try:
        proc.wait(timeout=1200)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
        proc.wait(timeout=15)
    for t in threads:t.join(timeout=15)
    events=[]
    for line in out.read_text(encoding='utf-8').splitlines():
        try:events.append(json.loads(line))
        except ValueError:pass
    ids=[e['thread_id'] for e in events if e.get('type')=='thread.started']
    messages=[e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
    result={'phase':phase,'exit':proc.returncode,'seconds':round(time.monotonic()-start,2),'thread_id':ids[-1] if ids else session,'messages':messages}
    save_new(evidence/f'{phase}-result.json',result)
    print(json.dumps({**result,'messages':messages[-2:]},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--phase',choices=['exercise','api','resume'],default='exercise')
    a=p.parse_args()
    main(a.root,a.phase)
