"""Build then inspect a real local production server; own processes only."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.request

from common import REPO, command, save_new


def main(root, app_name, target=None, evidence_name=None):
    target = target or root / 'apps' / app_name
    evidence_name = evidence_name or app_name
    evidence = root / 'evidence/ui' / evidence_name
    evidence.mkdir(parents=True)
    env = os.environ.copy()
    env['NEXT_TELEMETRY_DISABLED'] = '1'
    result = command([shutil.which('npm.cmd'), 'run', 'build'], target, evidence / 'build.json', timeout=600, env=env)
    if result['exit'] != 0:
        print(json.dumps({'app':app_name,'build_exit':result['exit'],'tail':result['stdout'][-2000:]+result['stderr'][-2000:]}))
        return
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    if app_name.startswith('next'):
        args = ['node', root / 'runtime/node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '-p', str(port)]
    else:
        args = ['node', root / 'runtime/node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', str(port), '--strictPort']
    with (evidence / 'server.txt').open('x',encoding='utf-8') as log:
        server = subprocess.Popen([str(a) for a in args],cwd=target,stdout=log,stderr=log,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                try:
                    urllib.request.urlopen(url,timeout=2).close()
                    break
                except Exception:
                    if server.poll() is not None:
                        raise RuntimeError('server exited')
                    time.sleep(0.3)
            script = 'template_browser.cjs' if app_name == 'template-library' else 'browser_check.cjs'
            r=command(['node', REPO / 'tools/evaluations/astryx' / script, root / 'runtime', url, evidence / 'browser'], target,
                      evidence / 'browser-process.json',timeout=180,env=env)
            print(json.dumps({'app':app_name,'build_exit':0,'browser_exit':r['exit'],'tail':r['stdout'][-6500:],'stderr':r['stderr'][-1000:]},ensure_ascii=False))
        finally:
            subprocess.run(['taskkill','/PID',str(server.pid),'/T','/F'],capture_output=True)
            server.wait(timeout=15)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--app',required=True)
    p.add_argument('--target',type=Path)
    p.add_argument('--evidence-name')
    a=p.parse_args()
    main(a.root,a.app,a.target,a.evidence_name)
