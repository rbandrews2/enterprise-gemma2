"""Bounded local ClamAV INSTREAM adapter, adapted from Claude's security kit.

No HTTP listener, cloud credentials, storage access or user paths enter the engine.
The operator must launch clamd with the generated, validated configuration.
"""
import os
import re
import socket
import stat
import struct
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath


PROFILE = {
    'Foreground': 'yes', 'LocalSocketMode': '600', 'FixStaleSocket': 'yes',
    'MaxThreads': '1', 'MaxQueue': '2', 'StreamMaxLength': '10M',
    'MaxFileSize': '10M', 'MaxScanSize': '50M', 'MaxFiles': '1000',
    'MaxRecursion': '10', 'MaxScanTime': '15000', 'ReadTimeout': '20',
    'CommandReadTimeout': '5', 'HeuristicAlerts': 'yes',
    'AlertExceedsMax': 'yes', 'AlertEncrypted': 'yes', 'AlertOLE2Macros': 'yes',
    'ScanArchive': 'yes', 'ScanPDF': 'yes', 'ScanOLE2': 'yes',
    'ScanXMLDOCS': 'yes', 'ScanPE': 'yes', 'ScanELF': 'yes',
    'ScanHTML': 'yes', 'ScanMail': 'yes', 'OfficialDatabaseOnly': 'yes',
    'ConcurrentDatabaseReload': 'no',
}


def daemon_config(socket_path, database_directory, certs_directory=None):
    """Trusted operator paths only; never construct config from upload metadata."""
    paths = [str(socket_path), str(database_directory)]
    if certs_directory is not None:
        paths.append(str(certs_directory))
    if any(not PurePosixPath(p).is_absolute() or re.search(r'[\s#\x00]', p) for p in paths):
        raise ValueError('Absolute, whitespace-free operator paths required')
    values = {
        **PROFILE, 'LocalSocket': paths[0], 'DatabaseDirectory': paths[1],
    }
    if certs_directory is not None:
        values['CVDCertsDirectory'] = paths[2]
    return ''.join(f'{key} {value}\n' for key, value in values.items())


class ClamdScanner:
    slots = threading.BoundedSemaphore(1)
    max_bytes = 10 * 1024 * 1024
    deadline_seconds = 20

    def __init__(self):
        self.path = os.getenv('WZOS_CLAMD_SOCKET', '').strip()
        self.config_path = os.getenv('WZOS_CLAMD_CONFIG', '').strip()
        self.configured = bool(self.path or self.config_path)

    def validate_policy(self):
        if os.name != 'posix' or not all(Path(p).is_absolute() for p in [self.path, self.config_path]):
            raise ValueError('Private local Unix socket and configuration required')
        cfg = Path(self.config_path)
        parent = Path(self.path).parent
        for p in [cfg, parent]:
            info = p.lstat()
            if stat.S_ISLNK(info.st_mode) or info.st_uid not in (0, os.geteuid()) or info.st_mode & 0o022:
                raise ValueError('Unsafe operator configuration permissions')
        if not stat.S_ISREG(cfg.stat().st_mode) or cfg.stat().st_size > 8192:
            raise ValueError('Invalid daemon configuration')
        values = {}
        for line in cfg.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            key, value = line.split(maxsplit=1)
            if key in values:
                raise ValueError('Duplicate configuration option')
            values[key] = value
        expected = {**PROFILE, 'LocalSocket': self.path,
                    'DatabaseDirectory': values.get('DatabaseDirectory', '')}
        certs = values.get('CVDCertsDirectory')
        if certs is not None:
            expected['CVDCertsDirectory'] = certs
            info = Path(certs).lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0, os.geteuid()) or info.st_mode & 0o022:
                raise ValueError('Unsafe signature-verification certificate directory')
        if values != expected or not values['DatabaseDirectory']:
            raise ValueError('Daemon configuration differs from reviewed scan policy')
        daemon_config(self.path, values['DatabaseDirectory'], certs)
        endpoint = Path(self.path).lstat()
        if not stat.S_ISSOCK(endpoint.st_mode) or endpoint.st_uid not in (0, os.geteuid()) or endpoint.st_mode & 0o077:
            raise ValueError('Unsafe daemon socket')

    @staticmethod
    def remaining(deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Scanner deadline exceeded')
        return remaining

    def exchange(self, command, data, deadline):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(self.remaining(deadline))
            client.connect(self.path)
            client.settimeout(self.remaining(deadline))
            client.sendall(b'z' + command + b'\0')
            if data is not None:
                for offset in range(0, len(data), 64 * 1024):
                    chunk = data[offset:offset + 64 * 1024]
                    client.settimeout(self.remaining(deadline))
                    client.sendall(struct.pack('!I', len(chunk)) + chunk)
                client.settimeout(self.remaining(deadline))
                client.sendall(b'\0\0\0\0')
            # Require one complete record AND EOF; never accept truncated/multiple verdicts.
            response = bytearray()
            while True:
                client.settimeout(self.remaining(deadline))
                part = client.recv(1024)
                if not part:
                    break
                response.extend(part)
                if len(response) > 4096:
                    raise ValueError('Oversized scanner reply')
            if not response.endswith(b'\0') or response.count(0) != 1:
                raise ValueError('Invalid scanner reply framing')
            return response[:-1].decode('ascii', errors='strict')

    def scan(self, data):
        from .security import ScanResult
        if not self.configured:
            return ScanResult('unavailable')
        if not isinstance(data, bytes) or not 0 < len(data) <= self.max_bytes or not self.slots.acquire(blocking=False):
            return ScanResult('error')
        try:
            from .archive_policy import zip_complete
            if not zip_complete(data):
                return ScanResult('error')
            self.validate_policy()
            deadline = time.monotonic() + self.deadline_seconds
            version = self.exchange(b'VERSION', None, deadline)
            parts = version.split('/')
            if len(parts) != 3 or not re.fullmatch(r'ClamAV [0-9][0-9A-Za-z.+~-]{0,63}', parts[0]) or not parts[1].isdigit():
                raise ValueError('Invalid engine identity')
            age = datetime.now() - datetime.strptime(parts[2], '%a %b %d %H:%M:%S %Y')
            if not timedelta(0) <= age <= timedelta(hours=24):
                raise ValueError('Stale or future signature database')
            verdict = self.exchange(b'INSTREAM', data, deadline)
            engine = '/'.join(parts[:2])
            if verdict == 'stream: OK':
                return ScanResult('clean', engine)
            if re.fullmatch(r'stream: [^\r\n\x00]{1,512} FOUND', verdict):
                return ScanResult('infected', engine)
            raise ValueError('Incomplete or unknown scan verdict')
        except (OSError, ValueError, UnicodeError, OverflowError):
            return ScanResult('error')
        finally:
            self.slots.release()
