"""Non-root, bounded scanner boot and owned-child supervision.

Refresh only at boot, never on an assumed idle CPU timer. Requests recycle an
aging worker before signature expiry. No customer originals are written to disk.
"""
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from .clamd_scanner import ClamdScanner, daemon_config

MAX_LIFETIME = 20 * 3600
SIGNATURE_MARGIN = 3600


def lifetime(version, now=None):
    """UTC process time, same signature format validated by the adapter."""
    parts = version.split('/')
    if len(parts) != 3:
        raise ValueError('Invalid signature identity')
    age = (now or datetime.now()) - datetime.strptime(parts[2], '%a %b %d %H:%M:%S %Y')
    remaining = 24 * 3600 - age.total_seconds() - SIGNATURE_MARGIN
    if age < timedelta(0) or remaining <= 0:
        raise ValueError('Signatures need refresh')
    return min(MAX_LIFETIME, remaining)


def private_directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0, os.geteuid()) or info.st_mode & 0o077:
        raise ValueError('Private owned directory required')


def seed_database(seed, database):
    if not seed.is_dir() or seed.is_symlink():
        raise ValueError('Verified signature seed required')
    for source in seed.iterdir():
        info = source.lstat()
        if not stat.S_ISREG(info.st_mode) or source.name.startswith('.'):
            raise ValueError('Invalid signature seed entry')
        shutil.copyfile(source, database / source.name)
        (database / source.name).chmod(0o600)
    if not any(database.glob('*.c?d')):
        raise ValueError('Signature seed missing')


class Runtime:
    def __init__(self, root, stop=None):
        self.root = Path(root)
        private_directory(self.root)
        self.stop = stop or threading.Event()
        self.children = []
        self.env = dict(os.environ, TZ='UTC')
        self.socket = self.root / 'clamd.sock'
        self.config = self.root / 'clamd.conf'
        self.database = self.root / 'db'

    def launch(self, command):
        child = subprocess.Popen(command, env=self.env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(child)
        return child

    def wait(self, child, deadline):
        while child.poll() is None:
            if self.stop.wait(.1) or time.monotonic() >= deadline:
                raise RuntimeError('Scanner startup interrupted or timed out')
        if child.returncode:
            raise RuntimeError('Scanner startup failed')

    def refresh(self, database, deadline):
        config = self.root / 'freshclam.conf'
        text = (f'DatabaseDirectory {database}\nDatabaseOwner {os.getuid()}\n'
                'DatabaseMirror database.clamav.net\nConnectTimeout 10\n'
                'ReceiveTimeout 15\nMaxAttempts 1\nTestDatabases yes\n')
        # Freshclam's DatabaseOwner requires a username, not a numeric UID.
        import pwd
        text = text.replace(f'DatabaseOwner {os.getuid()}\n', f'DatabaseOwner {pwd.getpwuid(os.getuid()).pw_name}\n')
        certs = self.certs()
        if certs:
            text += f'CVDCertsDirectory {certs}\n'
            self.env['CVD_CERTS_DIR'] = str(certs)
        config.write_text(text, encoding='utf-8'); config.chmod(0o600)
        self.wait(self.launch(['freshclam', '--config-file=' + str(config), '--stdout']), deadline)

    def certs(self):
        value = self.env.get('WZOS_CLAM_CERTS_DIR', '/etc/clamav/certs')
        path = Path(value)
        if not path.exists():
            if 'WZOS_CLAM_CERTS_DIR' in self.env:
                raise ValueError('Configured vendor certificates missing')
            return None  # Older verified distro versions have no detached CVD certs.
        if (not path.is_absolute() or path.is_symlink() or not path.is_dir()
                or path.stat().st_uid not in (0, os.geteuid()) or path.stat().st_mode & 0o022):
            raise ValueError('Unsafe vendor certificate directory')
        daemon_config('/private/socket', '/private/db', path)  # Reject config injection before Freshclam.
        return path

    def boot(self, seed, *, port=8080, host='0.0.0.0'):
        deadline = time.monotonic() + 210
        self.database.mkdir(mode=0o700)
        seed_database(Path(seed), self.database)
        self.refresh(self.database, min(deadline, time.monotonic() + 75))
        self.config.write_text(daemon_config(self.socket, self.database, self.certs()), encoding='utf-8')
        self.config.chmod(0o600)
        self.env.update(WZOS_CLAMD_SOCKET=str(self.socket), WZOS_CLAMD_CONFIG=str(self.config))
        daemon = self.launch(['clamd', '--config-file=' + str(self.config)])
        engine = ClamdScanner()
        engine.path, engine.config_path, engine.configured = str(self.socket), str(self.config), True
        while not self.socket.exists():
            if daemon.poll() is not None or self.stop.wait(.1) or time.monotonic() >= deadline:
                raise RuntimeError('Engine did not become ready')
        engine.deadline_seconds = min(20, deadline - time.monotonic())
        result = engine.scan(b'%PDF-1.7\nSynthetic readiness check\n%%EOF\n')
        if result.status != 'clean':
            raise RuntimeError('Engine readiness scan failed')
        version = engine.exchange(b'VERSION', None, deadline)
        seconds = lifetime(version)
        self.env['WZOS_SCANNER_INSTANCE_DEADLINE'] = str(time.monotonic() + seconds)
        if self.stop.is_set() or time.monotonic() >= deadline:
            raise RuntimeError('Startup allowance exceeded')
        web = self.launch([sys.executable, '-m', 'uvicorn',
            'services.workspace_preview.scanner_service:create_app', '--factory',
            '--host', host, '--port', str(port), '--no-access-log', '--timeout-graceful-shutdown', '2'])
        return daemon, web, result.engine

    def monitor(self):
        while not self.stop.wait(.2):
            if (self.root / 'recycle').exists():
                return 0
            if any(child.poll() is not None for child in self.children[-2:]):
                return 1
        return 0

    def close(self):
        # Signal all owned children first; one shared grace budget, not per child.
        for child in self.children:
            if child.poll() is None:
                child.terminate()
        deadline = time.monotonic() + 6
        for child in reversed(self.children):
            if child.poll() is None:
                try: child.wait(timeout=max(.01, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=1)


class SupervisedScanner:
    """Request-driven recycle; does not rely on background execution while idle."""
    configured = True

    def __init__(self):
        self.engine = ClamdScanner()
        self.deadline = float(os.environ['WZOS_SCANNER_INSTANCE_DEADLINE'])
        if (not 0 < self.deadline < float('inf') or not self.engine.configured
                or not Path(self.engine.path).is_absolute() or not Path(self.engine.config_path).is_absolute()):
            raise ValueError('Invalid worker lifetime')

    def scan(self, data):
        from .security import ScanResult
        if time.monotonic() >= self.deadline:
            root = Path(self.engine.path).parent
            private_directory(root)
            marker = root / 'recycle'
            try:
                fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(fd)
            except FileExistsError:
                pass
            return ScanResult('error')
        return self.engine.scan(data)


def main():
    if os.name != 'posix' or os.geteuid() == 0:
        raise SystemExit('SCANNER_RUNTIME_BLOCKED: non-root Linux required')
    os.environ['TZ'] = 'UTC'; time.tzset()
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    with tempfile.TemporaryDirectory(prefix='wzos-scanner-runtime-', dir='/tmp') as folder:
        runtime = Runtime(folder, stop)
        try:
            if len(sys.argv) == 3 and sys.argv[1] == '--seed-only':
                seed = Path(sys.argv[2]); seed.mkdir(mode=0o700, exist_ok=True)
                private_directory(seed)
                runtime.refresh(seed, time.monotonic() + 75)
                return 0
            port = int(os.getenv('PORT', '8080'))
            if not 1 <= port <= 65535:
                raise ValueError('Invalid service port')
            runtime.boot(os.environ['WZOS_CLAM_SEED'], port=port)
            print('SCANNER_RUNTIME_STARTED', flush=True)
            return runtime.monitor()
        except Exception:
            print('SCANNER_RUNTIME_BLOCKED: bootstrap or process failure', flush=True)
            return 1
        finally:
            runtime.close()


if __name__ == '__main__':
    raise SystemExit(main())
