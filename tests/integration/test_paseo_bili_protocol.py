"""Opt-in transport probe; fake Codex home, no credentials or model inference.

Run with MYCODEX_BILI_PROBE_RUNTIME, MYCODEX_CODEX_EXE, MYCODEX_NODE_EXE.
A pass establishes stdio transport only, never Paseo chat/compression support.
"""
import json
import ctypes
import os
from pathlib import Path
import queue
import subprocess
from tempfile import TemporaryDirectory
import threading
import time
import unittest


class RpcProcess:
    def __init__(self, command, *, env, cwd):
        self.proxy_records = [Path(env[k]) / "billion-context" for k in ("XDG_STATE_HOME", "XDG_CACHE_HOME")]
        self.expects_proxy = Path(command[0]).stem.lower() == "node"
        self.process = subprocess.Popen(
            command, cwd=cwd, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        self.lines = queue.Queue()
        self.stderr_bytes = 0
        self.non_json_lines = 0
        self._next_id = 0
        self._readers = [
            threading.Thread(target=self._stdout, daemon=True),
            threading.Thread(target=self._stderr, daemon=True),
        ]
        for reader in self._readers:
            reader.start()

    def _stdout(self):
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _stderr(self):
        for line in self.process.stderr:
            # Do not retain or echo diagnostics that might contain payloads.
            self.stderr_bytes += len(line.encode("utf-8"))

    def notify(self, method, params):
        self.process.stdin.write(json.dumps({"method": method, "params": params}) + "\n")
        self.process.stdin.flush()

    def request(self, method, params, timeout=30):
        self._next_id += 1
        request_id = self._next_id
        self.process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                raise AssertionError(f"RPC_EOF: method={method}, exit={self.process.poll()}, stderr_bytes={self.stderr_bytes}")
            try:
                message = json.loads(line)
            except (ValueError, TypeError):
                self.non_json_lines += 1
                raise AssertionError(f"RPC_STDOUT_CONTAMINATED: method={method}, line_bytes={len(line.encode('utf-8'))}") from None
            if not isinstance(message, dict):
                raise AssertionError("RPC_STDOUT_NOT_OBJECT")
            if message.get("id") == request_id:
                return message
        raise AssertionError(f"RPC_TIMEOUT: method={method}, stderr_bytes={self.stderr_bytes}")

    def close(self):
        proxy_pids = set()
        # These directories are new and unshared. Discover instance metadata,
        # which can precede the lazily flushed session-writer metadata.
        deadline = time.monotonic() + (10 if self.expects_proxy else 0)
        while self.expects_proxy and not proxy_pids and time.monotonic() < deadline:
            for folder in self.proxy_records:
                for record in folder.rglob("*.json"):
                    try:
                        data = json.loads(record.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        continue
                    if isinstance(data, dict) and type(data.get("pid")) is int and "origin" in data:
                        proxy_pids.add(data["pid"])
            if not proxy_pids:
                time.sleep(0.1)
        observed_proxy = bool(proxy_pids)
        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    # Only this probe's owned process tree, never name-based kills.
                    subprocess.run(["taskkill.exe", "/PID", str(self.process.pid), "/T", "/F"], capture_output=True, timeout=10)
                else:
                    self.process.terminate()
                self.process.wait(timeout=10)
            # The launcher uses a detached proxy with a watchdog/drain period.
            # Wait for that owned proxy before removing its SQLite files.
            deadline = time.monotonic() + 45
            while proxy_pids and time.monotonic() < deadline:
                proxy_pids = {pid for pid in proxy_pids if self._alive(pid)}
                if proxy_pids:
                    time.sleep(0.2)
            if proxy_pids:
                raise AssertionError("PROBE_PROXY_DID_NOT_DRAIN")
            if self.expects_proxy and not observed_proxy:
                raise AssertionError("PROBE_PROXY_OWNERSHIP_UNOBSERVED")
        finally:
            for reader in self._readers:
                reader.join(timeout=2)
            for stream in (self.process.stdout, self.process.stderr):
                if stream:
                    stream.close()

    @staticmethod
    def _alive(pid):
        if os.name == "nt":
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            kernel.WaitForSingleObject.restype = ctypes.c_ulong
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(0x00100000, False, pid)
            if not handle:
                if ctypes.get_last_error() == 5:
                    raise AssertionError("PROBE_PROCESS_STATUS_ACCESS_DENIED")
                return False
            try:
                return kernel.WaitForSingleObject(handle, 0) == 258
            finally:
                kernel.CloseHandle(handle)
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False


@unittest.skipUnless(os.environ.get("MYCODEX_BILI_PROBE_RUNTIME"), "opt-in transport probe; not evidence of live support")
class PaseoBiliProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="mycodex-bili-protocol-")
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.codex = Path(os.environ["MYCODEX_CODEX_EXE"])
        self.node = Path(os.environ["MYCODEX_NODE_EXE"])
        self.runtime = Path(os.environ["MYCODEX_BILI_PROBE_RUNTIME"])
        self.env = dict(os.environ)
        # Synthetic transport tests must not accidentally use ambient API keys.
        for key in list(self.env):
            if any(token in key.upper() for token in ("API_KEY", "ACCESS_TOKEN", "AUTH_TOKEN", "SECRET")):
                self.env.pop(key, None)
        home = self.root / "codex-home"
        home.mkdir()
        (home / "link-probe.txt").write_text("synthetic shared-state sentinel", encoding="utf-8")
        policy = self.root / "bili.json"
        policy.write_text(json.dumps({
            "autoUpdate": False, "autoRestartOnUpdate": False,
            "advisoryCheck": False, "releaseNotesCheck": False,
            "debug": False, "log": "error",
        }), encoding="utf-8")
        self.env.update({
            "CODEX_HOME": str(home),
            "BILI_CLIENT_BIN": str(self.codex),
            "BILI_CONFIG_FILE": str(policy),
            "BILI_SESSIONS_DIR": str(self.root / "bili-sessions"),
            "ACP_AUTO_UPDATE": "0", "BILI_ADVISORY_CHECK": "0",
            "BILI_RELEASE_NOTES_CHECK": "0",
            "XDG_CONFIG_HOME": str(self.root / "xdg-config"),
            "XDG_DATA_HOME": str(self.root / "xdg-data"),
            "XDG_CACHE_HOME": str(self.root / "xdg-cache"),
            "XDG_STATE_HOME": str(self.root / "xdg-state"),
        })

    def assert_handshake(self, command):
        process = RpcProcess(command, env=self.env, cwd=self.root)
        self.addCleanup(process.close)
        reply = process.request("initialize", {
            "clientInfo": {"name": "codex_app_server_daemon", "title": "Codex App Server Daemon", "version": "0.0.0"},
            "capabilities": {"experimentalApi": True},
        })
        self.assertNotIn("error", reply, "initialize must succeed")
        self.assertIn("result", reply)
        process.notify("initialized", {})
        reply = process.request("config/read", {"includeLayers": False})
        self.assertNotIn("error", reply, "config/read must succeed")
        self.assertIn("result", reply)
        self.assertEqual(process.non_json_lines, 0)
        if process.expects_proxy:
            links = list(self.root.glob("codex-home-bili*/link-probe.txt"))
            self.assertTrue(links, "overlay must expose existing state")
            self.assertTrue(all(os.path.samefile(self.root / "codex-home/link-probe.txt", p) for p in links), "overlay must link state instead of copying it")

    def test_direct_codex_initialize_and_config_read(self):
        self.assert_handshake([str(self.codex), "app-server"])

    def test_bili_preserves_initialize_and_config_read(self):
        entry = self.runtime / "node_modules/billion-context/dist/index.js"
        self.assertTrue(entry.is_file())
        self.assert_handshake([str(self.node), str(entry), "codex", "app-server"])

    @unittest.skipUnless(os.environ.get('MYCODEX_BILI_BRIDGE_RUNTIME'), 'opt-in prepared bridge runtime')
    def test_managed_bridge_preserves_initialize_and_config_read(self):
        bridge = Path(os.environ['MYCODEX_BILI_BRIDGE_RUNTIME']) / 'paseo-bridge.mjs'
        self.assertTrue(bridge.is_file())
        self.assert_handshake([str(self.node), str(bridge), 'app-server'])


if __name__ == "__main__":
    unittest.main()
