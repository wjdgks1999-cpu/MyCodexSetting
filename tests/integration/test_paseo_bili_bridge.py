"""Fake-engine transport tests, never evidence of real compression."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'kit/integrations/billion-context/paseo-bridge.mjs'
NODE = os.environ.get('MYCODEX_NODE_EXE') or shutil.which('node')


@unittest.skipUnless(NODE, 'Node is optional for base kit')
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mycodex-bridge-한글 ')
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name)
        self.env = dict(os.environ, CODEX_HOME=str(self.runtime / 'fake-codex-home'))
        self.env.pop('CODEX_CA_CERTIFICATE',None)
        self.bridge = self.runtime / 'paseo-bridge.mjs'
        if BRIDGE.exists(): shutil.copyfile(BRIDGE, self.bridge)
        package = self.runtime / 'node_modules/billion-context'
        (package / 'dist').mkdir(parents=True)
        (package / 'package.json').write_text('{"type":"module","version":"0.1.213"}')
        (package / 'dist/mcp.js').write_text('// fake')
        (package / 'dist/index.js').write_text('''
process.stderr.write('fake engine diagnostic\\n');
const mode=process.argv[4];
if(mode==='fail') process.exit(17);
if(mode==='hold') {
  process.stdout.write(JSON.stringify({pid:process.pid})+'\\n');
  process.stdin.resume();process.stdin.on('end',()=>process.exit(0));
} else {
 const chunks=[];for await(const c of process.stdin)chunks.push(c);
 process.stdout.write(JSON.stringify({argv:process.argv.slice(2),input:Buffer.concat(chunks).toString('utf8'),cwd:process.cwd(),
  update:process.env.ACP_AUTO_UPDATE,restart:process.env.ACP_AUTO_RESTART_ON_UPDATE,
  proxy:process.env.HTTPS_PROXY,xdg:process.env.XDG_CONFIG_HOME,
  inherited:process.env.BILI_MCP_PROXY??null,client:process.env.BILI_CLIENT_BIN}));
}
''', encoding='utf-8')
        self.owner = dict(manager='MyCodexSetting', bili_version='0.1.213', tools=dict(node=NODE, codex=NODE),
                          files={}, upstream={n:hashlib.sha256((package/n).read_bytes()).hexdigest() for n in ('dist/index.js','dist/mcp.js','package.json')})
        self.seal()

    def seal(self):
        if self.bridge.exists(): self.owner['files']['paseo-bridge.mjs'] = hashlib.sha256(self.bridge.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        (self.runtime/'owner.json').write_text(json.dumps(self.owner))

    def run_bridge(self, args, data=b''):
        env=dict(self.env,ACP_AUTO_UPDATE='1',ACP_AUTO_RESTART_ON_UPDATE='1',BILI_MCP_PROXY='http://wrong.invalid',
                 HTTPS_PROXY='http://upstream.invalid:9000',XDG_CONFIG_HOME='kept-xdg')
        return subprocess.run([NODE,str(self.bridge),*args],input=data,capture_output=True,env=env,timeout=15,cwd=ROOT)

    def test_argv_stdin_stdout_and_child_environment(self):
        args=['app-server','한글 공백','', 'a"b', '&', '%PATH%', '-c', 'mcp_servers.example.args=["x y",""]']
        data=b'{"jsonrpc":"2.0","id":1}\n'
        p=self.run_bridge(args,data)
        self.assertEqual(0,p.returncode,p.stderr.decode(errors='replace'))
        d=json.loads(p.stdout);self.assertEqual(['codex',*args],d['argv'])
        self.assertEqual(data.decode(),d['input']);self.assertEqual(str(ROOT),d['cwd'])
        self.assertEqual('0',d['update']);self.assertEqual('0',d['restart']);self.assertIsNone(d['inherited'])
        self.assertEqual('http://upstream.invalid:9000',d['proxy']);self.assertEqual('kept-xdg',d['xdg'])

    def test_child_failure_is_propagated(self):
        self.assertEqual(17,self.run_bridge(['app-server','fail']).returncode)

    def test_tampered_runtime_fails_closed(self):
        (self.runtime/'node_modules/billion-context/dist/index.js').write_text('console.log("unsafe")')
        p=self.run_bridge(['app-server']);self.assertNotEqual(0,p.returncode);self.assertEqual(b'',p.stdout)

    def test_requires_app_server(self):
        p=self.run_bridge(['exec']);self.assertNotEqual(0,p.returncode);self.assertEqual(b'',p.stdout)

    def test_abrupt_parent_exit_closes_child_stdin(self):
        p=subprocess.Popen([NODE,str(self.bridge),'app-server','hold'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.env)
        try:
            child=json.loads(p.stdout.readline())['pid']
            p.kill();p.communicate(timeout=10)
            # Child holds stdout open until it exits; communicate completion proves EOF exit.
            self.assertGreater(child,0)
        finally:
            if p.poll() is None:p.kill();p.communicate()

    def test_two_instances_keep_streams_separate(self):
        ps=[subprocess.Popen([NODE,str(self.bridge),'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.env) for _ in range(2)]
        for i,p in enumerate(ps):
            out,err=p.communicate(str(i).encode(),timeout=15)
            self.assertEqual(str(i),json.loads(out)['input']);self.assertEqual(0,p.returncode,err)


if __name__=='__main__':unittest.main()
