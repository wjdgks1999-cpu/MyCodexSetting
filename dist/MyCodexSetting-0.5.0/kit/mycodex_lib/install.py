"""Plan-first installation. Never upgrade or overwrite an existing asset."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from .documents import render_index
from .model import DocRef, IndexData, FileChange, InstallPlan, Finding, InputError, OPTIONAL_KEYS, REQUIRED_ASSETS, KIT_VERSION
from .paths import checked_path, read_asset, read_text


def _write_temp(path: Path, content: bytes) -> Path:
    fd, name = tempfile.mkstemp(prefix='.mycodex-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        return Path(name)
    except BaseException:
        if os.path.exists(name):
            os.unlink(name)
        raise


def _publish_new(source: Path, destination: Path) -> None:
    # Windows rename refuses an existing destination; POSIX link does likewise.
    if os.name == 'nt':
        os.rename(source, destination)
    else:
        os.link(source, destination)


def atomic_create(path: Path, content: bytes) -> None:
    """Publish a complete new file without ever replacing another file."""
    staged = _write_temp(path, content)
    try:
        _publish_new(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def atomic_write(path: Path, content: bytes, *, expected: bytes | None = None) -> None:
    """Replace a file, optionally detecting edits after staging and fsync."""
    staged = _write_temp(path, content)
    try:
        if expected is not None and path.read_bytes() != expected:
            raise InputError('File changed while staging; existing content was preserved.')
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def guarded_update(path: Path, content: bytes, expected: bytes) -> None:
    """Serialize this tool's index writers and check external edits at commit."""
    lock = path.parent / '.index.lock'
    try:
        stream = lock.open('xb')
    except FileExistsError:
        raise InputError('Index is locked by another operation; inspect the lock before retrying.') from None
    try:
        with stream:
            if path.read_bytes() != expected:
                raise InputError('Index changed during recording; existing content was preserved.')
            atomic_write(path, content, expected=expected)
    finally:
        lock.unlink(missing_ok=True)


def _source(bundle: Path, destination: str) -> Path:
    if destination.startswith('.mycodex/'):
        return checked_path(bundle, destination.removeprefix('.mycodex/'))
    return checked_path(bundle, destination.replace('.agents/skills/', 'skills/', 1))


def build_install_plan(bundle_root: Path, root: Path, requirements: tuple[str, ...]) -> InstallPlan:
    changes, findings = [], []
    contents = {}
    def fail(code, path, message):
        findings.append(Finding(code, 'error', path, message))
    for name in requirements:
        try:
            path = checked_path(root, name)
            if path.suffix.lower() not in ('.md', '.txt') or not path.is_file():
                raise InputError('Missing or unsupported requirements.')
            read_text(path)
            if any(c in name for c in '`|\r\n'):
                raise InputError('Unsupported navigation path.')
        except InputError:
            fail('INVALID_REQUIREMENTS', name, 'Provide an accessible UTF-8 Markdown or text requirement within the root.')
    if not requirements:
        fail('INVALID_REQUIREMENTS', '', 'Provide at least one requirements file.')
    for name in sorted(REQUIRED_ASSETS):
        source = _source(bundle_root, name)
        if not source.is_file():
            raise InputError('Source kit is incomplete; use the original distribution.')
        contents[name] = read_asset(source)
    original_manifest = None
    try:
        manifest_path = checked_path(root, '.mycodex/manifest.json', for_write=True)
        if manifest_path.exists():
            original_manifest = json.loads(read_text(manifest_path))
            if not isinstance(original_manifest, dict) or original_manifest.get('kit_version') != KIT_VERSION or original_manifest.get('schema_version') != 1 or set(original_manifest.get('files', {})) != REQUIRED_ASSETS or type(original_manifest.get('generated_agents')) is not bool:
                raise InputError('Existing installation requires manual review.')
    except (InputError, ValueError, TypeError):
        fail('MANIFEST_CONFLICT', '.mycodex/manifest.json', 'Preserve the existing installation and review its version/inventory.')
    agents_template = read_asset(bundle_root / 'templates/AGENTS.md')
    try:
        agents = checked_path(root, 'AGENTS.md', for_write=True)
        generated = original_manifest['generated_agents'] if original_manifest else (not agents.exists() or (agents.is_file() and read_asset(agents) == agents_template))
    except InputError:
        generated = False
    manifest = dict(schema_version=1, kit_version=KIT_VERSION, generated_agents=generated, files={name: hashlib.sha256(content).hexdigest() for name, content in contents.items()})
    contents['.mycodex/manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')
    refs = [DocRef('requirements', p.replace('\\', '/'), '요구사항 원본') for p in dict.fromkeys(requirements)]
    refs.extend(DocRef(k, 'none', '') for k in OPTIONAL_KEYS)
    if requirements:
        contents['.context/index.md'] = render_index(IndexData(1, 'needs-review', tuple(refs))).encode('utf-8')
    contents['AGENTS.md'] = agents_template
    contents['.codex/config.toml'] = read_asset(bundle_root / 'templates/config.toml')
    for name, content in contents.items():
        try:
            path = checked_path(root, name, for_write=True)
            # Existing nondirectory ancestors are a preflight error, not a partial write.
            cursor = path.parent
            while cursor != root:
                if cursor.exists() and not cursor.is_dir():
                    raise InputError('Parent is not a directory.')
                cursor = cursor.parent
            if path.exists():
                if not path.is_file():
                    raise InputError('Destination is not a file.')
                if name in ('AGENTS.md', '.context/index.md', '.codex/config.toml'):
                    action = 'preserve'
                else:
                    action = 'skip' if read_asset(path) == content else 'conflict'
            else:
                action = 'create'
            changes.append(FileChange(name, action, content))
            if action == 'conflict':
                fail('ASSET_CONFLICT', name, 'Existing content differs; review without overwriting.')
        except InputError:
            changes.append(FileChange(name, 'conflict', None))
            fail('UNSAFE_DESTINATION', name, 'Check directory types, symlinks and root containment.')
    return InstallPlan(root, tuple(changes), tuple(findings))


def apply_install_plan(plan: InstallPlan) -> None:
    if plan.findings:
        raise InputError('Installation preflight failed; no files were written.')
    # Recheck the entire plan before the first write.
    for change in plan.changes:
        path = checked_path(plan.root, change.path, for_write=True)
        if change.action == 'create' and path.exists():
            raise InputError('Destination changed after preflight; re-run dry-run.')
        if change.action == 'skip' and (not path.is_file() or read_asset(path) != change.content):
            raise InputError('Asset changed after preflight; re-run dry-run.')
    # Manifest last makes interrupted installations recoverable on re-run.
    ordered = sorted(plan.changes, key=lambda c: c.path == '.mycodex/manifest.json')
    for change in ordered:
        if change.action != 'create':
            continue
        path = checked_path(plan.root, change.path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        checked_path(plan.root, change.path, for_write=True)
        atomic_create(path, change.content)
