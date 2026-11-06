import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


KIT = Path(__file__).resolve().parents[1] / "kit"
TICK = chr(96)


class KitRegressionTests(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.target = self.workspace / "target"
        self.target.mkdir()
        (self.target / "PRD.md").write_text("Export JSON.\n", encoding="utf-8")
        self.cli = self.target / ".mycodex" / "mycodex.py"
        self.index = self.target / ".context" / "index.md"

    def command(self, cli, *args):
        return subprocess.run(
            [sys.executable, "-B", str(cli), *args, "--target", str(self.target)],
            capture_output=True, text=True, encoding="utf-8",
        )

    def install(self, kit=KIT):
        return self.command(kit / "mycodex.py", "init", "--requirements", "PRD.md", "--apply")

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def mark_ready(self):
        self.index.write_bytes(self.index.read_bytes().replace(b"status: needs-review", b"status: ready"))

    def validate(self):
        return self.command(self.cli, "validate", "--strict", "--json")

    def test_reinstall_and_validate_across_line_endings(self):
        lf_kit = self.workspace / "lf-kit"
        crlf_kit = self.workspace / "crlf-kit"
        for bundle in (lf_kit, crlf_kit):
            shutil.copytree(KIT, bundle, ignore=shutil.ignore_patterns("__pycache__"))
        for path in lf_kit.rglob("*"):
            if path.is_file():
                lf = path.read_bytes().replace(b"\r\n", b"\n")
                path.write_bytes(lf)
                (crlf_kit / path.relative_to(lf_kit)).write_bytes(lf.replace(b"\n", b"\r\n"))

        self.assert_success(self.install(lf_kit))
        self.mark_ready()
        self.assert_success(self.install(crlf_kit))

        manifest_path = self.target / ".mycodex" / "manifest.json"
        assets = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        for name in (*assets, ".mycodex/manifest.json"):
            path = self.target / name
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assert_success(self.validate())
        self.assert_success(self.install(lf_kit))

        policy = self.target / ".mycodex" / "context-policy.md"
        with policy.open("ab") as stream:
            stream.write(b"Actual content change.\n")
        validation = self.validate()
        self.assertEqual(validation.returncode, 1, validation.stderr)
        self.assertEqual(
            [(item["code"], item["path"]) for item in json.loads(validation.stdout)["findings"]],
            [("ASSET_MISMATCH", ".mycodex/context-policy.md")],
        )
        conflict = self.install(lf_kit)
        self.assertEqual(conflict.returncode, 1, conflict.stdout + conflict.stderr)
        self.assertIn("ASSET_CONFLICT: .mycodex/context-policy.md", conflict.stdout)

    def test_validate_uses_existing_override_when_it_has_content(self):
        override = self.target / "AGENTS.override.md"
        original = "Preserve this existing project rule.\n"
        override.write_text(original, encoding="utf-8")
        self.assert_success(self.install())
        self.assertEqual(override.read_text(encoding="utf-8"), original)
        self.mark_ready()
        invalid = self.validate()
        self.assertEqual(invalid.returncode, 1, invalid.stderr)
        self.assertEqual(
            [(item["code"], item["path"]) for item in json.loads(invalid.stdout)["findings"]],
            [("AGENTS_INDEX_MISSING", "AGENTS.override.md")],
        )
        override.write_text(" \n\t\n", encoding="utf-8")
        self.assert_success(self.validate())
        override.unlink()
        override.mkdir()
        self.assert_success(self.validate())
        override.rmdir()
        override.write_text(original + "Read .context/index.md for this task.\n", encoding="utf-8")
        (self.target / "AGENTS.md").write_text("Inactive base instructions.\n", encoding="utf-8")
        self.assert_success(self.validate())

    def record_handoff_with_index(self, change_index):
        self.assert_success(self.install())
        self.mark_ready()
        original = self.index.read_text(encoding="utf-8")
        modified = change_index(original)
        self.assertNotEqual(modified, original)
        self.index.write_text(modified, encoding="utf-8")
        self.assert_success(self.validate())

        draft_name = ".context/handoffs/draft.md"
        draft = self.target / draft_name
        draft.parent.mkdir()
        template = (self.target / ".mycodex/templates/handoff.md").read_text(encoding="utf-8")
        fields = {
            "goal": "Resume export work.",
            "timestamp_with_timezone": "2026-11-06T00:00:00+00:00",
            "evidence_links": "[PRD](../../PRD.md)",
            "completed_in_progress_blocked_unverified": "In progress.",
            "commands_results_or_not_run": "Not run.",
            "next_action": "Implement export.",
            "current_state_checks_and_git_baseline": "Recheck PRD.",
        }
        draft.write_text(re.sub(r"\{\{(\w+)}}", lambda match: fields[match[1]], template), encoding="utf-8")

        result = self.command(self.cli, "record-handoff", "--draft", draft_name)
        self.assert_success(result)
        snapshot = result.stdout.strip()
        self.assertTrue((self.target / snapshot).is_file())
        self.assertEqual(self.index.read_text(encoding="utf-8"), self.expected_index(modified, snapshot))
        self.assert_success(self.validate())

    def expected_index(self, text, snapshot):
        lines = text.splitlines(keepends=True)
        for number, line in enumerate(lines):
            if line.startswith((f"| latest-handoff |", f"| {TICK}latest-handoff{TICK} |")):
                lines[number] = line.replace(f"{TICK}none{TICK}", f"{TICK}{snapshot}{TICK}", 1)
                return "".join(lines)
        self.fail("Missing index row in fixture")

    def test_handoff_updates_index_key_written_as_inline_code(self):
        self.record_handoff_with_index(lambda text: text.replace(
            "| latest-handoff |", f"| {TICK}latest-handoff{TICK} |",
        ))

    def test_handoff_ignores_latest_row_example_outside_navigation_table(self):
        example = f"\n~~~markdown\n| latest-handoff | {TICK}none{TICK} | Example |\n~~~\n"
        self.record_handoff_with_index(lambda text: text + example)


if __name__ == "__main__":
    unittest.main()
