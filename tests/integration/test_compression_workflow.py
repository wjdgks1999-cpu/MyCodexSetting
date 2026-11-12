"""Opt-in assertions over artifacts from real synthetic Paseo workflow runs.

Create the A/B fixtures and run the actions recorded in the validation document
first. This never replaces model/tool evidence with mock success.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('MYCODEX_WORKFLOW_ROOT'), 'live A/B/C artifacts not supplied')
class WorkflowTests(unittest.TestCase):
    def test_current_requirement_tests_handoff_and_html(self):
        root=Path(os.environ['MYCODEX_WORKFLOW_ROOT'])
        for mode in ('A','B'):
            with self.subTest(mode=mode):
                project=root/mode
                self.assertEqual('PROTECTED_9051\n',(project/'protected.txt').read_text())
                r=subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','discover','-p','test_answer.py','-v'],
                                 cwd=project,capture_output=True,text=True,timeout=30)
                self.assertEqual(0,r.returncode,r.stderr)
                self.assertIn('Ran 1 test',r.stderr)
                r=subprocess.run([sys.executable,'-B','-c','from answer import answer; assert answer() == 7'],
                                 cwd=project,capture_output=True,text=True,timeout=10)
                self.assertEqual(0,r.returncode,r.stderr)
                index=(project/'.context/index.md').read_text(encoding='utf-8')
                self.assertIn('| latest-handoff |',index)
                handoffs=list((project/'.context/handoffs').glob('*.md'))
                self.assertTrue(handoffs)
                self.assertNotIn('`none`',next(x for x in index.splitlines() if x.startswith('| latest-handoff |')))
                self.assertTrue(list((project/'.human-docs').rglob('*.html')))
                # HTML artifacts are not authoritative source links.
                self.assertNotIn('](../../.human-docs/', '\n'.join(p.read_text(encoding='utf-8') for p in handoffs))
                self.assertNotIn('.human-docs/',index)
                r=subprocess.run([sys.executable,'-B',str(project/'.mycodex/mycodex.py'),'validate','--target',str(project),'--strict','--json'],capture_output=True,text=True,timeout=20)
                self.assertEqual(0,r.returncode,r.stderr+r.stdout)


if __name__=='__main__':unittest.main()
