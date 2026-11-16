"""Tests for evidence checks; these never call a model."""
import importlib.util
from pathlib import Path
import unittest
import sys
import tempfile
import json
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[2] / 'tools/evaluations/hallmark/checks.py'
spec = importlib.util.spec_from_file_location('hallmark_checks', FILE)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
sys.path.insert(0, str(FILE.parent))
import run as runner
import collect as collector


class EvidenceChecks(unittest.TestCase):
    def test_incomplete_trace_blocks_before_model_spawn(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'events-1.jsonl').write_text('original failure', encoding='utf-8')
            with patch.object(runner, 'fixture', return_value=(root, root)), \
                 patch.object(runner, 'snapshot', return_value={}), \
                 patch.object(runner.subprocess, 'Popen', side_effect=AssertionError('model spawned')):
                with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                    runner.turn(root, Path('unused'), 'SH', 'S03', 1)
            self.assertEqual((root / 'events-1.jsonl').read_text(), 'original failure')

    def test_foreign_thread_blocks_before_model_spawn(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'turn-1.json').write_text(json.dumps({'thread_id': 'owned'}), encoding='utf-8')
            with patch.object(runner, 'fixture', return_value=(root, root)), \
                 patch.object(runner, 'snapshot', return_value={}), \
                 patch.object(runner.subprocess, 'Popen', side_effect=AssertionError('model spawned')):
                with self.assertRaisesRegex(ValueError, 'fixture'):
                    runner.turn(root, Path('unused'), 'SH', 'S03', 1, session='foreign')

    def test_incomplete_turn_cannot_overwrite_failure_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            event = root / 'events-1.jsonl'
            event.write_text('interrupted evidence', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                runner.reserve_turn(root)
            self.assertEqual(event.read_text(), 'interrupted evidence')
            self.assertFalse((root / 'stderr-1.txt').exists())

    def test_attempt_number_uses_existing_number_not_file_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'turn-3.json').write_text('{}', encoding='utf-8')
            self.assertEqual(runner.reserve_turn(root), 4)
            self.assertTrue((root / 'events-4.jsonl').exists())
            self.assertTrue((root / 'stderr-4.txt').exists())

    def test_foreign_resume_session_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'turn-1.json').write_text(json.dumps({'thread_id': 'owned'}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fixture'):
                runner.validate_session(root, 'foreign')
            runner.validate_session(root, 'owned')
            runner.validate_session(root, None)  # S09 deliberately opens a new thread.

    def test_verdict_rejects_new_evidence_with_same_run_id(self):
        row = {'run_id': 'SH-E/S05/1', 'status': 'NEEDS_REVIEW'}
        verdict = {'status': 'PASS', 'reason': 'reviewed old evidence', 'evidence_sha256': {'events-1.jsonl': 'old'}}
        with self.assertRaisesRegex(ValueError, 'evidence'):
            collector.attach_verdict(row, verdict, {'events-1.jsonl': 'new'})
        self.assertEqual(row['status'], 'NEEDS_REVIEW')

    def test_verdict_accepts_exact_evidence_only(self):
        row = {'status': 'NEEDS_REVIEW'}
        hashes = {'events-1.jsonl': 'same'}
        collector.attach_verdict(row, {'status': 'PASS', 'reason': 'reviewed', 'evidence_sha256': hashes}, hashes)
        self.assertEqual(row['status'], 'PASS')
        with self.assertRaises(ValueError):
            collector.attach_verdict({}, {'status': 'PASS'}, hashes)

    def test_product_evidence_includes_root_and_api_files(self):
        files = {'index.html': 'h', 'styles.css': 'c', 'scripts/app.js': 'j',
                 'assets/logo.svg': 's', 'search.py': 'p', 'site/.hallmark/compare.html': 'r',
                 '.human-docs/report.html': 'r', 'docs/report.md': 'd'}
        self.assertEqual(checks.changed_product_files({}, files),
                         ['assets/logo.svg', 'index.html', 'scripts/app.js', 'search.py', 'styles.css'])

    def test_project_init_fixture_is_prd_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / 'bases/SH-E'
            (base / '.context').mkdir(parents=True)
            (base / '.context/index.md').write_text('status: needs-review\n', encoding='utf-8')
            (base / 'PRD.md').write_text('# Fixture\n', encoding='utf-8')
            _, target = runner.fixture(root, 'SH-E', 'S08', 1)
            self.assertFalse((target / 'docs/design.md').exists())
            self.assertFalse((target / 'docs/plan.md').exists())
            self.assertFalse((target / 'site').exists())
            self.assertIn('needs-review', (target / '.context/index.md').read_text())

    def test_protected_change_is_failure(self):
        self.assertEqual(checks.unexpected_changes({'site/a.css': 'a', 'AGENTS.md': 'a'},
                                                 {'site/a.css': 'b', 'AGENTS.md': 'b'}, ['site/']), ['AGENTS.md'])

    def test_deleted_protected_file_is_failure(self):
        self.assertEqual(checks.unexpected_changes({'AGENTS.md': 'a'}, {}, ['site/']), ['AGENTS.md'])

    def test_prefix_must_match_directory_boundary(self):
        self.assertEqual(checks.unexpected_changes({}, {'site-secret/a': 'x'}, ['site/']), ['site-secret/a'])

    def test_skill_claim_is_not_load_evidence(self):
        events = [{'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'I used Hallmark'}}]
        self.assertFalse(checks.skill_read_commands(events, 'hallmark'))

    def test_listing_is_not_load_evidence(self):
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                   'command': 'rg --files .agents/skills/hallmark/SKILL.md', 'exit_code': 0}}]
        self.assertFalse(checks.skill_read_commands(events, 'hallmark'))

    def test_successful_skill_read_is_evidence(self):
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                   'command': 'Get-Content .agents/skills/hallmark/SKILL.md', 'exit_code': 0,
                   'aggregated_output': '---\nname: hallmark\n---\n# Hallmark'}}]
        self.assertEqual(len(checks.skill_read_commands(events, 'hallmark')), 1)

    def test_partial_shell_success_does_not_prove_skill_read(self):
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                   'command': 'Get-Content .agents/skills/hallmark/SKILL.md; Write-Output done',
                   'exit_code': 0, 'aggregated_output': 'Cannot find path\ndone'}}]
        self.assertFalse(checks.skill_read_commands(events, 'hallmark'))

    def test_failed_read_is_not_evidence(self):
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                   'command': 'Get-Content .agents/skills/hallmark/SKILL.md', 'exit_code': 1}}]
        self.assertFalse(checks.skill_read_commands(events, 'hallmark'))

    def test_missing_render_cannot_pass(self):
        self.assertEqual(checks.render_status([]), 'NOT_RUN')

    def test_render_failure_not_replaced_by_success_claim(self):
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                   'command': 'node sloplint.mjs site --render', 'exit_code': 1}},
                  {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'All tests passed'}}]
        self.assertEqual(checks.render_status(events), 'FAIL')

    def test_code_before_approval_detected(self):
        turns = [{'approved': False, 'changed': ['site/index.html']},
                 {'approved': True, 'changed': ['site/styles.css']}]
        self.assertEqual(checks.unapproved_product_turns(turns), [1])

    def test_root_and_web_product_files_before_approval_detected(self):
        turns = [{'approved': False, 'changed': ['index.html']},
                 {'approved': False, 'changed': ['web/styles.css']}]
        self.assertEqual(checks.unapproved_product_turns(turns), [1, 2])

    def test_design_document_is_not_product_code(self):
        self.assertEqual(checks.unapproved_product_turns([{'approved': False, 'changed': ['docs/design.md']}]), [])

    def test_provider_credentials_are_redacted_before_storage(self):
        value = {'source_repository_credential': {'token': 'fake-credential'},
                 'nested': '{"siwc_bypass_bearer_token":"fake-bypass"}',
                 'command': 'git https://user:fake-password@example.test/repo',
                 'usage': {'input_tokens': 123}}
        clean = checks.redact(value)
        self.assertNotIn('fake-', str(clean))
        self.assertEqual(clean['usage']['input_tokens'], 123)


if __name__ == '__main__':
    unittest.main()
