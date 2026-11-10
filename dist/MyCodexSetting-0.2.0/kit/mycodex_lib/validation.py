import hashlib
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote
from .documents import parse_index, local_links, handoff_sections
from .model import Finding, InputError, REQUIRED_ASSETS, KIT_VERSION, SKILL_NAMES
from .paths import checked_path, read_asset, read_text


def exit_code(findings: tuple[Finding, ...], *, strict: bool = False) -> int:
    return int(any(f.severity == 'error' or strict for f in findings))


def is_human_document(name: str) -> bool:
    path = posixpath.normpath(unquote(name).replace('\\', '/'))
    return path.split('/', 1)[0].casefold() == '.human-docs'


def link_findings(root: Path, relative: str, text: str, *, historical: bool = False) -> list[Finding]:
    findings = []
    for link in local_links(text):
        name = posixpath.normpath(posixpath.join(posixpath.dirname(relative), link.replace('\\', '/')))
        if is_human_document(name):
            findings.append(Finding('HUMAN_DOC_REFERENCE', 'error', relative, 'Use an original source outside .human-docs; generated HTML is excluded from context.'))
            continue
        try:
            path = checked_path(root, name)
            if not path.is_file():
                findings.append(Finding('STALE_SNAPSHOT_REFERENCE' if historical else 'BROKEN_LINK', 'warning' if historical else 'error', relative, 'Recheck a historical reference.' if historical else 'Restore or update a local file link.'))
        except InputError:
            findings.append(Finding('UNSAFE_LINK', 'error', relative, 'Keep file links within the project root.'))
    return findings


def validate(root: Path) -> tuple[Finding, ...]:
    findings = []

    def error(code, path, message):
        findings.append(Finding(code, 'error', path, message))

    try:
        index = checked_path(root, '.context/index.md')
        text = read_text(index)
        data = parse_index(text)
    except FileNotFoundError:
        error('MISSING_INDEX', '.context/index.md', 'Install the context index.')
        return tuple(findings)
    except InputError:
        error('INVALID_INDEX', '.context/index.md', 'Restore the supported index format and safe path.')
        return tuple(findings)
    if data.status == 'needs-review':
        error('INIT_REVIEW_REQUIRED', '.context/index.md', 'Run $project-init and complete the settings review.')
    findings.extend(link_findings(root, '.context/index.md', text))
    for ref in data.references:
        if ref.path == 'none':
            continue
        if is_human_document(ref.path):
            error('HUMAN_DOC_REFERENCE', ref.path, 'Remove generated HTML from context references; use its original sources.')
            continue
        try:
            path = checked_path(root, ref.path)
            if not path.is_file():
                findings.append(Finding('MISSING_LEDGER' if ref.kind == 'active-ledger' else 'MISSING_REFERENCE', 'warning' if ref.kind == 'active-ledger' else 'error', ref.path, 'Check the source path; a missing ledger does not prove completion.'))
                continue
            if ref.kind == 'requirements':
                if path.suffix.lower() not in ('.md', '.txt'):
                    raise InputError('Requirements must be Markdown or text.')
                read_text(path)
            if ref.kind == 'latest-handoff':
                content = read_text(path)
                handoff_sections(content)
                findings.extend(link_findings(root, ref.path, content, historical=True))
        except InputError:
            error('INVALID_REFERENCE', ref.path, 'Check the safe path, text encoding and document format.')
    generated = False
    try:
        manifest = json.loads(read_text(checked_path(root, '.mycodex/manifest.json')))
        if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or manifest.get('kit_version') != KIT_VERSION or type(manifest.get('generated_agents')) is not bool or not isinstance(manifest.get('files'), dict):
            raise InputError('Invalid manifest.')
        if set(manifest['files']) != REQUIRED_ASSETS:
            raise InputError('Incomplete asset manifest.')
        generated = manifest['generated_agents']
        for name, digest in manifest['files'].items():
            path = checked_path(root, name)
            if not path.is_file() or hashlib.sha256(read_asset(path)).hexdigest() != digest:
                error('ASSET_MISMATCH', name, 'Restore the installed version; automatic upgrades are not supported.')
    except FileNotFoundError:
        error('MISSING_MANIFEST', '.mycodex/manifest.json', 'Complete installation from the original kit.')
    except (InputError, json.JSONDecodeError, TypeError):
        error('INVALID_MANIFEST', '.mycodex/manifest.json', 'Restore the installation inventory.')
    agents_name = 'AGENTS.override.md'
    try:
        try:
            override = checked_path(root, agents_name)
            agents = read_text(override) if override.is_file() else ''
        except FileNotFoundError:
            agents = ''
        if not agents.strip():
            agents_name = 'AGENTS.md'
            agents = read_text(checked_path(root, agents_name))
        if '.context/index.md' not in agents:
            error('AGENTS_INDEX_MISSING', agents_name, 'Add a short context-index instruction without replacing existing rules.')
        if generated and agents_name == 'AGENTS.md' and len(agents.splitlines()) > 60:
            findings.append(Finding('AGENTS_LENGTH', 'warning', agents_name, 'Keep generated instructions concise; move details to source documents.'))
        findings.extend(link_findings(root, agents_name, agents))
    except FileNotFoundError:
        error('MISSING_AGENTS', agents_name, 'Create project instructions.')
    except InputError:
        error('INVALID_AGENTS', agents_name, 'Check UTF-8 encoding and safe path.')
    for name in SKILL_NAMES:
        base = f'.agents/skills/{name}'
        try:
            policy = read_text(checked_path(root, base + '/agents/openai.yaml'))
            definition = read_text(checked_path(root, base + '/SKILL.md'))
            if not re.search(r'(?m)^policy:\s*\n  allow_implicit_invocation: false\s*$', policy) or len(re.findall('allow_implicit_invocation:', policy)) != 1 or f'name: {name}\n' not in definition:
                error('INVALID_SKILL_POLICY', base, 'Use the explicit-only invocation policy for this skill.')
        except (FileNotFoundError, InputError):
            error('MISSING_SKILL', base, 'Restore the installed skill and policy.')
    return tuple(findings)
