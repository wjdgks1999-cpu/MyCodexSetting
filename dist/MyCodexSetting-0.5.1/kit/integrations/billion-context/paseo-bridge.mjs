// Stdio stays byte-for-byte transparent. This file never calls a model itself.
import {spawn} from 'node:child_process';
import {createHash, randomUUID} from 'node:crypto';
import {readFileSync, lstatSync, existsSync, linkSync, unlinkSync, statSync, mkdirSync} from 'node:fs';
import {dirname, resolve, join, parse, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {homedir} from 'node:os';

const root = dirname(fileURLToPath(import.meta.url));
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
function safe(path) {
  if (!isAbsolute(path)) throw Error('PATH');
  for (let p = resolve(path);; p = dirname(p)) {
    if (existsSync(p) && lstatSync(p).isSymbolicLink()) throw Error('REPARSE');
    if (dirname(p) === p) break;
  }
  return path;
}
function fail(code) { process.stderr.write(`mycodex-bili: ${code}; inspect compression doctor.\n`); process.exitCode = 1; }

try {
  if (process.argv[2] !== 'app-server') throw Error('APP_SERVER_REQUIRED');
  safe(root);
  const owner = JSON.parse(readFileSync(safe(join(root, 'owner.json')), 'utf8'));
  if (owner.manager !== 'MyCodexSetting' || owner.bili_version !== '0.1.213') throw Error('OWNER');
  for (const [name, expected] of Object.entries(owner.files)) {
    if (!['package.json','package-lock.json','policy.json','README.md','THIRD_PARTY_NOTICES.md','paseo-bridge.mjs'].includes(name)) throw Error('OWNER');
    const bytes = readFileSync(safe(join(root,name)), 'utf8').replace(/\r\n/g,'\n');
    if (hash(bytes) !== expected) throw Error('MANAGED_CHANGED');
  }
  if (!owner.files['paseo-bridge.mjs'] || !owner.upstream) throw Error('OWNER');
  for (const name of ['package.json','dist/index.js','dist/mcp.js']) {
    if (hash(readFileSync(safe(join(root,'node_modules/billion-context',name)))) !== owner.upstream[name]) throw Error('UPSTREAM_CHANGED');
  }
  safe(owner.tools.codex);
  if (process.env.CODEX_CA_CERTIFICATE) throw Error('CUSTOM_CODEX_CA_UNVERIFIED');
  // Bili's fallback copies auth if links fail. Prove hardlinks work without reading auth.
  const auth = join(process.env.CODEX_HOME || join(homedir(),'.codex'),'auth.json');
  if (existsSync(auth)) {
    const check = join(dirname(auth), `.mycodex-link-check-${randomUUID()}`);
    try { linkSync(auth,check); if (statSync(auth).ino !== statSync(check).ino) throw Error('AUTH_LINK'); }
    finally { if (existsSync(check)) unlinkSync(check); }
  }
  const env = {...process.env};
  for (const key of Object.keys(env)) if (/^(BILI_|ACP_|BILLION_CONTEXT)/i.test(key)) delete env[key];
  Object.assign(env, {
    BILI_CLIENT_BIN: owner.tools.codex,
    BILI_CONFIG_FILE: join(root,'policy.json'), BILI_SESSIONS_DIR: join(root,'sessions'),
    BILI_CODEX_STATE_MODE:'shared', BILI_NATIVE_ATTACH_EXTERNAL:'0', BILI_NATIVE_ATTACH_POLICY:'own-lane',
    ACP_AUTO_UPDATE:'0', ACP_AUTO_RESTART_ON_UPDATE:'0', BILI_ADVISORY_CHECK:'0', BILI_RELEASE_NOTES_CHECK:'0',
    ACP_DEBUG:'0', ACP_LOG:'0', ACP_LOG_FILE:join(root,'logs','bili.log'),
  });
  mkdirSync(join(root,'logs'), {recursive:true});
  const child = spawn(process.execPath, [join(root,'node_modules/billion-context/dist/index.js'),'codex',...process.argv.slice(2)],
                      {cwd:process.cwd(), env, shell:false, windowsHide:true, stdio:['pipe','pipe','pipe']});
  child.stdout.pipe(process.stdout); child.stderr.pipe(process.stderr);
  child.stdin.on('error', () => {});
  process.stdin.pipe(child.stdin);
  let finishing = false;
  const stop = () => { if (finishing) return; finishing = true; child.stdin.end();
    const timer = setTimeout(() => child.kill(), 5000); timer.unref(); };
  process.once('SIGINT',stop); process.once('SIGTERM',stop); process.once('SIGHUP',stop);
  process.stdout.on('error',stop);
  child.on('error', () => { fail('SPAWN_FAILED'); process.stdin.destroy(); });
  child.on('close', (code,signal) => { process.stdin.destroy(); process.exitCode = code ?? (signal ? 1 : 0); });
} catch {
  fail('PREFLIGHT_FAILED');
}
