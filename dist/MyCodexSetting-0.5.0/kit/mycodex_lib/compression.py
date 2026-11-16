"""Optional pinned Codex launch and Paseo integration; no global config edits."""
import hashlib
import copy
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import uuid

from .install import atomic_create, atomic_write
from .model import InputError
from .paths import is_reparse, read_asset

BILI_VERSION = '0.1.213'
ASSETS = Path(__file__).resolve().parents[1] / 'integrations' / 'billion-context'
MANAGED = ('package.json', 'package-lock.json', 'policy.json', 'README.md', 'THIRD_PARTY_NOTICES.md', 'paseo-bridge.mjs')


def default_runtime() -> Path:
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local/share'))) / 'MyCodexSetting' / 'billion-context' / BILI_VERSION


def _safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if is_reparse(part):
            raise InputError('UNSAFE_PATH: symlink or reparse point.')
    return path


def _runtime(target: Path, runtime: Path) -> Path:
    target, runtime = _safe(target), _safe(runtime)
    if not target.is_dir() or runtime == target or runtime.is_relative_to(target) or target.is_relative_to(runtime):
        raise InputError('RUNTIME_LOCATION: use a separate host runtime outside the project.')
    return runtime


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> dict:
    try:
        value = json.loads(_safe(path).read_text(encoding='utf-8'))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeError):
        raise InputError('INVALID_JSON: review the indicated configuration; content withheld.') from None


def _toolchain() -> dict:
    node = os.environ.get('MYCODEX_NODE_EXE') or shutil.which('node')
    codex = os.environ.get('MYCODEX_CODEX_EXE') or shutil.which('codex')
    if not codex and os.name == 'nt':
        candidate = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/OpenAI/Codex/bin/codex.exe'
        if candidate.is_file(): codex = str(candidate)
    if not node: raise InputError('NODE_MISSING: Node 20+ is required only for compression.')
    if not codex: raise InputError('CODEX_MISSING: set MYCODEX_CODEX_EXE to the intended Codex executable.')
    # Installed Codex exposes bin through a versioned release junction. Pin its
    # resolved executable; mutable runtime/config destinations still reject links.
    node, codex = str(_safe(Path(node).resolve())), str(_safe(Path(codex).resolve()))
    npm = os.environ.get('MYCODEX_NPM_CLI') or str(Path(node).parent / 'node_modules/npm/bin/npm-cli.js')
    if not Path(npm).is_file():
        raise InputError('NPM_MISSING: set MYCODEX_NPM_CLI to npm-cli.js.')
    for exe, pattern, code in ((node, r'^v(\d+)\.', 'NODE'), (codex, r'^codex-cli (\d+)\.(\d+)\.', 'CODEX')):
        try:
            result = subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=15, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            raise InputError(code + '_UNAVAILABLE') from None
        match = re.search(pattern, result.stdout.strip())
        if result.returncode or not match or (code == 'NODE' and int(match[1]) < 20):
            raise InputError(code + '_UNSUPPORTED')
        if code == 'CODEX' and (int(match[1]), int(match[2])) < (0, 147):
            raise InputError('CODEX_UNSUPPORTED: shared SQLite overlay requires Codex 0.147+.')
    return dict(node=node, npm=str(_safe(Path(npm))), codex=codex)


def _pinned_tools_available(owner: dict) -> bool:
    tools = owner.get('tools')
    if not isinstance(tools,dict): return False
    try:
        return all(isinstance(tools.get(n),str) and Path(tools[n]).is_absolute()
                   and _safe(Path(tools[n])).is_file() for n in ('node','codex'))
    except (OSError,InputError):
        return False


def _ready(runtime: Path) -> dict | None:
    if not (runtime / 'owner.json').is_file(): return None
    owner = _json(runtime / 'owner.json')
    if owner.get('manager') != 'MyCodexSetting' or owner.get('bili_version') != BILI_VERSION:
        return None
    if not all(isinstance(owner.get(n),dict) for n in ('files','upstream','tools')):
        return None
    if not _pinned_tools_available(owner):
        return None
    try:
        if set(owner['files']) != set(MANAGED): return None
        for name, digest in owner['files'].items():
            if name not in MANAGED or _digest(read_asset(_safe(runtime / name))) != digest: return None
            if _digest(read_asset(ASSETS / name)) != digest: return None
        for name, digest in owner['upstream'].items():
            if name not in ('dist/index.js', 'dist/mcp.js', 'package.json'): return None
            if _digest(_safe(runtime / 'node_modules/billion-context' / name).read_bytes()) != digest: return None
        if set(owner['upstream']) != {'dist/index.js', 'dist/mcp.js', 'package.json'}: return None
        if _json(runtime / 'node_modules/billion-context/package.json').get('version') != BILI_VERSION: return None
    except (KeyError, TypeError, OSError):
        return None
    return owner


def inspect_compression(target: Path, runtime_root: Path, paseo_home: Path, *, client: str = 'paseo') -> dict:
    if client not in ('paseo', 'codex'): raise InputError('CLIENT_UNSUPPORTED')
    runtime = _runtime(target, runtime_root)
    owner = _ready(runtime)
    diagnostics = []
    if not owner:
        record = runtime / 'owner.json'
        if not record.is_file(): diagnostics.append('RUNTIME_NOT_PREPARED')
        elif not _pinned_tools_available(_json(record)): diagnostics.append('PINNED_TOOL_UNAVAILABLE')
        else: diagnostics.append('RUNTIME_ASSET_MISMATCH')
    registered = None
    if client == 'paseo':
        config = _safe(paseo_home / 'config.json')
        registered = False
        if config.is_file():
            d = _json(config)
            registered = isinstance(_providers(d).get('codex-bili'), dict)
    return dict(state='installed' if owner else 'not_ready', installed=bool(owner),
                bili_version=BILI_VERSION, runtime=str(runtime), provider_registered=registered,
                protocol_verified='unknown', traffic_observed='unknown', compression_observed='unknown',
                support='supported', client=client, diagnostics=diagnostics)


def run_codex(target: Path, runtime_root: Path, arguments: list[str], *, apply: bool = False) -> dict | int:
    runtime = _runtime(target, runtime_root)
    owner = _ready(runtime)
    if not owner: raise InputError('RUNTIME_NOT_READY: prepare a complete runtime first.')
    # A remote daemon does not inherit this launcher's routing environment.
    for argument in arguments:
        if argument == '--': break
        if argument == '--remote' or argument.startswith('--remote='):
            raise InputError('REMOTE_UNSUPPORTED: use a local Codex session for compression.')
    if os.environ.get('CODEX_CA_CERTIFICATE'):
        raise InputError('CUSTOM_CODEX_CA_UNVERIFIED: preserve the existing CA configuration.')
    if not apply:
        return dict(state='planned', client='codex', runtime=str(runtime), target=str(target),
                    arguments_count=len(arguments), changed=False)

    env = {k:v for k,v in os.environ.items() if not re.match(r'^(BILI_|ACP_|BILLION_CONTEXT)', k, re.I)}
    env.update({
        'BILI_CLIENT_BIN': owner['tools']['codex'],
        'BILI_CONFIG_FILE': str(runtime/'policy.json'), 'BILI_SESSIONS_DIR': str(runtime/'sessions'),
        'BILI_CODEX_STATE_MODE': 'shared', 'BILI_NATIVE_ATTACH_EXTERNAL': '0', 'BILI_NATIVE_ATTACH_POLICY': 'own-lane',
        'ACP_AUTO_UPDATE': '0', 'ACP_AUTO_RESTART_ON_UPDATE': '0',
        'BILI_ADVISORY_CHECK': '0', 'BILI_RELEASE_NOTES_CHECK': '0',
        'ACP_DEBUG': '0', 'ACP_LOG': '0', 'ACP_LOG_FILE': str(runtime/'logs/bili.log'),
    })
    home = Path(env.get('CODEX_HOME', str(Path.home()/'.codex')))
    home = (home if home.is_absolute() else target/home).resolve()
    env['CODEX_HOME'] = str(home)
    auth = home/'auth.json'
    if auth.exists():
        # Upstream creates its overlay beside CODEX_HOME. Probe that filesystem,
        # not the auth directory (which could itself be a mounted volume).
        probe = home.parent / ('.mycodex-link-check-' + str(uuid.uuid4()))
        try:
            os.link(auth, probe)
            if not os.path.samefile(auth, probe): raise OSError('link mismatch')
        except OSError:
            raise InputError('AUTH_LINK_UNAVAILABLE: authentication was not copied.') from None
        finally:
            probe.unlink(missing_ok=True)
    (runtime/'logs').mkdir(exist_ok=True)
    # Bili consumes one leading separator of its own. Preserve any native
    # separator so dash-prefixed prompts cannot turn into active Codex flags.
    # Pin the local mode ourselves: upstream's remote-mode heuristic also scans
    # after native "--" and could mistake a literal prompt for a remote flag.
    command = [owner['tools']['node'], str(runtime/'node_modules/billion-context/dist/index.js'),
               'codex', '--', '--no-daemon', *arguments]
    # Inherit the actual console/streams, including TTY resize and native JSONL.
    # Console Ctrl+C reaches the child too; let the native UI handle it without
    # Python killing its launcher on the first turn cancellation.
    with subprocess.Popen(command, cwd=target, env=env, shell=False) as process:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            return process.wait()
        finally:
            signal.signal(signal.SIGINT, previous)


def prepare_runtime(target: Path, runtime_root: Path, *, apply: bool = False) -> dict:
    runtime = _runtime(target, runtime_root)
    if not all((ASSETS / n).is_file() for n in MANAGED):
        raise InputError('INTEGRATION_INCOMPLETE: use a complete kit distribution.')
    if runtime.exists():
        if _ready(runtime): return dict(state='ready', runtime=str(runtime), changed=False)
        raise InputError('RUNTIME_CONFLICT: preserve existing runtime; choose a new empty path after review.')
    if not apply:
        return dict(state='planned', runtime=str(runtime), bili_version=BILI_VERSION,
                    action='npm ci --ignore-scripts --no-audit --no-fund', changed=False)
    tools = _toolchain()
    runtime.mkdir(parents=True, exist_ok=False)
    for name in MANAGED:
        atomic_create(runtime / name, read_asset(ASSETS / name))
    try:
        result = subprocess.run([tools['node'], tools['npm'], 'ci', '--ignore-scripts', '--no-audit', '--no-fund',
                                 '--prefix', str(runtime), '--cache', str(runtime / 'npm-cache')],
                                shell=False, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        raise InputError('INSTALL_FAILED: incomplete runtime preserved, process output withheld.') from None
    if result.returncode:
        raise InputError('INSTALL_FAILED: incomplete runtime preserved, process output withheld.')
    package = runtime / 'node_modules/billion-context'
    if _json(package / 'package.json').get('version') != BILI_VERSION or not (package / 'dist/mcp.js').is_file():
        raise InputError('INSTALL_FAILED: unexpected package layout or version.')
    owner = dict(manager='MyCodexSetting', bili_version=BILI_VERSION, tools=tools,
                 files={n:_digest(read_asset(runtime / n)) for n in MANAGED if (runtime / n).is_file()},
                 upstream={n:_digest((package / n).read_bytes()) for n in ('dist/index.js', 'dist/mcp.js', 'package.json')})
    atomic_create(runtime / 'owner.json', (json.dumps(owner, indent=2) + '\n').encode())
    return dict(state='ready', runtime=str(runtime), changed=True)


def _providers(config: dict) -> dict:
    if config.get('version') != 1: raise InputError('PASEO_SCHEMA_UNSUPPORTED')
    agents = config.setdefault('agents', {})
    if not isinstance(agents, dict): raise InputError('PASEO_SCHEMA_UNSUPPORTED')
    providers = agents.setdefault('providers', {})
    if not isinstance(providers, dict): raise InputError('PASEO_SCHEMA_UNSUPPORTED')
    return providers


def _profile_record(home: Path, runtime: Path) -> Path:
    return _safe(runtime / 'providers' / (_digest(str(home).encode()) + '.json'))


def plan_paseo_provider(paseo_home: Path, runtime_root: Path, *, enabled: bool) -> dict:
    home, runtime = _safe(paseo_home), _safe(runtime_root)
    config = _safe(home / 'config.json')
    before = config.read_bytes() if config.exists() else None
    data = _json(config) if before is not None else {'version':1}
    providers = _providers(data)
    previous = copy.deepcopy(providers.get('codex-bili'))
    record = _profile_record(home, runtime)
    ownership = _json(record) if record.exists() else None
    if 'codex-bili' in providers and (not ownership or ownership.get('manager') != 'MyCodexSetting' or ownership.get('profile') != previous):
        raise InputError('PROVIDER_CONFLICT: existing or edited codex-bili was preserved.')
    if enabled:
        owner = _ready(runtime)
        if not owner: raise InputError('RUNTIME_NOT_READY: prepare a complete runtime first.')
        profile = dict(extends='codex', label='Codex 문맥 압축', enabled=True,
                       command=[owner['tools']['node'], str(runtime / 'paseo-bridge.mjs')])
        providers['codex-bili'] = profile
    else:
        profile = None
        providers.pop('codex-bili', None)
    changed = previous != profile
    return dict(state='planned', action='enable' if enabled else 'disable', changed=changed,
                provider='codex-bili', paseo_home=str(home), runtime=str(runtime),
                _before=before, _after=(json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode(),
                _previous=previous, _profile=profile, _ownership=ownership)


def public_plan(plan: dict) -> dict:
    return {k:v for k,v in plan.items() if not k.startswith('_')}


def _reload_paseo(home: Path) -> bool:
    if os.name == 'nt':
        r = Path(os.environ.get('LOCALAPPDATA','')) / 'Programs/Paseo/resources'
        exe = r.parent / 'Paseo.exe'
        if not exe.is_file(): return False
        command = [str(exe), '--disable-warning=DEP0040', str(r / 'app.asar.unpacked/dist/daemon/node-entrypoint-runner.js'),
                   'node-script', str(r / 'app.asar/node_modules/@getpaseo/cli/dist/index.js')]
        env = dict(os.environ, ELECTRON_RUN_AS_NODE='1', PASEO_NODE_ENV='production')
    else:
        exe = shutil.which('paseo')
        if not exe: return False
        command, env = [exe], dict(os.environ)
    try:
        p = subprocess.run(command + ['daemon','reload','--home',str(home),'--json'],
                           env=env, capture_output=True, timeout=20, shell=False)
        d = json.loads(p.stdout)
        return p.returncode == 0 and isinstance(d,dict) and d.get('restartRequiredPaths') == [] and d.get('overrideControlledPaths') == []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def apply_paseo_provider(plan: dict) -> dict:
    home, runtime = _safe(Path(plan['paseo_home'])), _safe(Path(plan['runtime']))
    config = _safe(home / 'config.json')
    if plan['action'] == 'enable' and not _ready(runtime): raise InputError('RUNTIME_NOT_READY')
    current = config.read_bytes() if config.exists() else None
    if current != plan['_before']: raise InputError('PASEO_CONCURRENT_EDIT: existing configuration preserved.')
    home.mkdir(parents=True,exist_ok=True)
    lock = _safe(home / '.mycodex-provider.lock')
    try: stream = lock.open('xb')
    except FileExistsError: raise InputError('PASEO_LOCKED: review the lock before retrying.') from None
    try:
        with stream:
            config = _safe(home / 'config.json')
            current = config.read_bytes() if config.exists() else None
            if current != plan['_before']: raise InputError('PASEO_CONCURRENT_EDIT')
            if plan['changed']:
                record = _profile_record(home,runtime)
                if plan['action'] == 'enable':
                    record.parent.mkdir(parents=True,exist_ok=True)
                    content = (json.dumps(dict(manager='MyCodexSetting', profile=plan['_profile']),ensure_ascii=False)+'\n').encode()
                    if record.exists(): atomic_write(record,content,expected=record.read_bytes())
                    else: atomic_create(record,content)
                if current is None: atomic_create(config,plan['_after'])
                else: atomic_write(config,plan['_after'],expected=current)
    finally:
        lock.unlink(missing_ok=True)
    active = _reload_paseo(home)
    return dict(state='active' if active else 'saved_not_active', active=active, saved=True,
                provider='codex-bili', action=plan['action'], changed=plan['changed'],
                next_action=('Select Codex 문맥 압축 in a new chat.' if plan['action'] == 'enable' else 'Select existing Codex in a new chat.') if active
                else 'Reload Paseo configuration before starting a new chat.')


def export_compression_summary(runtime_root: Path, session_id: str, *, apply: bool = False) -> dict:
    runtime = _safe(runtime_root)
    if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',session_id):
        raise InputError('SESSION_ID_INVALID: use the Codex thread UUID, not a path.')
    found = []
    folder = _safe(runtime / 'sessions/responses')
    for file in folder.glob('*.json'):
        data = _json(file)
        if data.get('id') != session_id: continue
        if data.get('version') != 3: raise InputError('EXPORT_SCHEMA_UNSUPPORTED')
        blocks = data.get('payload',{}).get('state',{}).get('blocks',[])
        if not isinstance(blocks,list): raise InputError('EXPORT_SCHEMA_UNSUPPORTED')
        found.extend(dict(block_id=b.get('blockId'),summary=b['summary']) for b in blocks
                     if isinstance(b,dict) and b.get('active') is True and isinstance(b.get('summary'),str))
    if not found: raise InputError('SUMMARY_UNAVAILABLE: no active summary for that thread.')
    path = _safe(runtime / 'exports' / (session_id+'-'+uuid.uuid4().hex+'.json'))
    if apply:
        path.parent.mkdir(parents=True,exist_ok=True)
        payload = dict(schema_version=1,bili_version=BILI_VERSION,session_id=session_id,
                       authority='Unverified model summary. Recheck current originals before use.', summaries=found)
        atomic_create(_safe(path), (json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return dict(state='exported' if apply else 'planned',path=str(path),summaries=len(found))
