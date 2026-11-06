"""MyCodexSetting command line; no third-party runtime dependencies."""
import sys
sys.dont_write_bytecode = True

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from mycodex_lib.model import InputError
from mycodex_lib.paths import resolve_root
from mycodex_lib.validation import validate, exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Install and validate project context settings.')
    subs = parser.add_subparsers(dest='command', required=True)
    check = subs.add_parser('validate')
    check.add_argument('--target', required=True)
    check.add_argument('--strict', action='store_true')
    check.add_argument('--json', action='store_true')
    setup = subs.add_parser('init')
    setup.add_argument('--target', required=True)
    setup.add_argument('--requirements', required=True, action='append')
    setup.add_argument('--apply', action='store_true')
    handoff = subs.add_parser('record-handoff')
    handoff.add_argument('--target', required=True)
    handoff.add_argument('--draft', required=True)
    args = parser.parse_args(argv)
    try:
        root = resolve_root(args.target)
        if args.command == 'record-handoff':
            from mycodex_lib.handoff import record_handoff
            from mycodex_lib.paths import checked_path
            output = record_handoff(root, checked_path(root, args.draft))
            print(output.relative_to(root).as_posix())
            return 0
        if args.command == 'init':
            from mycodex_lib.install import build_install_plan, apply_install_plan
            plan = build_install_plan(Path(__file__).resolve().parent, root, tuple(args.requirements))
            for change in plan.changes:
                print(f'{change.action}: {change.path}')
            for finding in plan.findings:
                print(f'error {finding.code}: {finding.path}: {finding.message}')
            if plan.findings:
                return 1
            if args.apply:
                apply_install_plan(plan)
                print('Installation complete. Run $project-init to review settings; installation alone does not mean ready.')
            else:
                print('Dry-run complete; no files written. Use --apply to install.')
            if not (root / '.git').exists():
                print('Git repository not detected; Git was not initialized.')
            return 0
        findings = validate(root)
        result = exit_code(findings, strict=args.strict)
        payload = {'ok': result == 0, 'findings': [asdict(f) for f in findings]}
        if args.json:
            print(json.dumps(payload, ensure_ascii=True))
        else:
            for f in findings:
                print(f'{f.severity} {f.code} {f.path}: {f.message}')
            print('Validation passed.' if result == 0 else 'Validation failed.')
        return result
    except InputError as error:
        print('Input validation failed. ' + str(error), file=sys.stderr)
        return 1
    except OSError as error:
        print('I/O failed. Check target existence and access permissions; no success is claimed.', file=sys.stderr)
        if getattr(error, 'snapshot', None):
            print('Unlinked snapshot: ' + error.snapshot.relative_to(root).as_posix(), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
