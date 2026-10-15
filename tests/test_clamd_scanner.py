import os
import socket
import struct
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from pathlib import Path

from services.workspace_preview.clamd_scanner import ClamdScanner, daemon_config
from services.workspace_preview.security import configured_scanner, ClamAVScanner


class FakeSocket:
    def __init__(self, replies):
        self.replies, self.sent = iter(replies), []
        self.closed = False

    def __enter__(self): return self
    def __exit__(self, *_): self.closed = True
    def settimeout(self, timeout):
        if timeout <= 0: raise AssertionError('No deadline')
    def connect(self, path): self.path = path
    def sendall(self, data): self.sent.append(data)
    def recv(self, _): return next(self.replies, b'')


class ClamdScannerTests(unittest.TestCase):
    def setUp(self):
        # Transport is mocked here; real Unix permissions/socket tests run on Linux.
        family = patch('services.workspace_preview.clamd_scanner.socket.AF_UNIX',getattr(socket,'AF_UNIX',1),create=True)
        family.start()
        self.addCleanup(family.stop)

    def scanner(self):
        with patch.dict(os.environ, {'WZOS_CLAMD_SOCKET':'/private/clamd.sock',
                                     'WZOS_CLAMD_CONFIG':'/private/clamd.conf'}):
            return ClamdScanner()

    def version(self, age=timedelta()):
        return ('ClamAV 1.4.3/12345/' + (datetime.now()-age).strftime('%a %b %d %H:%M:%S %Y')).encode()+b'\0'

    def scan(self, verdict, version=None):
        connections = [FakeSocket([version or self.version()]), FakeSocket(verdict)]
        with patch.object(ClamdScanner, 'validate_policy'), patch('services.workspace_preview.clamd_scanner.socket.socket',side_effect=connections):
            result = self.scanner().scan(b'harmless synthetic bytes')
        return result, connections

    def test_streamed_bytes_have_network_order_lengths_and_no_paths(self):
        result, sockets = self.scan([b'stream: ',b'OK\0'])
        self.assertEqual(result.status,'clean')
        self.assertEqual(result.engine,'ClamAV 1.4.3/12345')
        self.assertEqual(sockets[0].sent,[b'zVERSION\0'])
        self.assertEqual(sockets[1].sent,[b'zINSTREAM\0',struct.pack('!I',24)+b'harmless synthetic bytes',b'\0\0\0\0'])
        self.assertTrue(all(s.closed for s in sockets))

    def test_positive_signature_and_limit_alerts_hold_without_leaking_signature(self):
        for verdict in [b'stream: Synthetic.Private FOUND\0',b'stream: Heuristics.Limits.Exceeded FOUND\0',b'stream: Heuristics.Encrypted.PDF FOUND\0']:
            result,_=self.scan([verdict])
            self.assertEqual(result.status,'infected')
            self.assertNotIn('Private',result.engine)

    def test_errors_truncation_oversized_multiple_and_unknown_replies_never_clean(self):
        for response in [[b'stream: OK'],[b'stream: OK\0evil\0'],[b'file: OK\0'],
                         [b'stream: access denied ERROR\0'],[b'\xff\0'],[b'x'*4097]]:
            with self.subTest(response=str(response)[:70]):
                self.assertEqual(self.scan(response)[0].status,'error')

    def test_stale_future_missing_and_malformed_engine_identity_block_scan(self):
        for version in [self.version(timedelta(days=2)),self.version(timedelta(days=-1)),b'PONG\0',b'ClamAV x/none/date\0']:
            result,connections=self.scan([b'stream: OK\0'],version)
            self.assertEqual(result.status,'error')
            self.assertEqual(connections[1].sent,[])

    def test_missing_socket_timeout_and_rejected_policy_fail_closed(self):
        for error in [FileNotFoundError(),socket.timeout(),ValueError('bad policy')]:
            with patch.object(ClamdScanner,'validate_policy',side_effect=error):
                self.assertEqual(self.scanner().scan(b'fixture').status,'error')
        with patch.object(ClamdScanner,'validate_policy'),patch('services.workspace_preview.clamd_scanner.socket.socket',side_effect=socket.timeout()):
            self.assertEqual(self.scanner().scan(b'fixture').status,'error')

    def test_single_worker_and_size_admission_happen_before_connection(self):
        scanner=self.scanner()
        self.assertTrue(scanner.slots.acquire(blocking=False))
        try:
            with patch('services.workspace_preview.clamd_scanner.socket.socket') as connect:
                self.assertEqual(scanner.scan(b'fixture').status,'error')
                connect.assert_not_called()
        finally: scanner.slots.release()
        for value in [b'',b'x'*(scanner.max_bytes+1),'not bytes']:
            with patch('services.workspace_preview.clamd_scanner.socket.socket') as connect:
                self.assertEqual(scanner.scan(value).status,'error')
                connect.assert_not_called()

    def test_bad_daemon_config_never_falls_back_to_cli(self):
        with patch.dict(os.environ, {'WZOS_CLAMD_SOCKET':'','WZOS_CLAMD_CONFIG':'relative.conf','WZOS_CLAMSCAN_PATH':'/bin/clamscan'}):
            self.assertIsInstance(configured_scanner(),ClamdScanner)
            self.assertEqual(configured_scanner().scan(b'fixture').status,'error')
        with patch.dict(os.environ, {'WZOS_CLAMD_SOCKET':'','WZOS_CLAMD_CONFIG':''}):
            self.assertIsInstance(configured_scanner(),ClamAVScanner)

    def test_generated_policy_is_private_bounded_and_rejects_config_injection(self):
        text=daemon_config('/private/clamd.sock','/private/db')
        for option in ['LocalSocketMode 600','MaxThreads 1','AlertExceedsMax yes','AlertEncrypted yes','AlertOLE2Macros yes','OfficialDatabaseOnly yes']:
            self.assertIn(option,text)
        self.assertNotIn('TCPSocket',text)
        self.assertIn('CVDCertsDirectory /private/certs',daemon_config('/private/clamd.sock','/private/db','/private/certs'))
        for path in ['relative','/tmp/has space','/tmp/x\nTCPSocket 3310','/tmp/x#comment']:
            with self.assertRaises(ValueError): daemon_config(path,'/private/db')

    def test_monotonic_deadline_is_total_not_per_chunk(self):
        with patch('services.workspace_preview.clamd_scanner.time.monotonic',return_value=11):
            with self.assertRaises(TimeoutError): self.scanner().remaining(10)


@unittest.skipUnless(os.name == 'posix', 'Unix socket permissions require the Linux cloud gate')
class LinuxPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wzos-policy-')
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.config=root/'clamd.conf'; self.endpoint=root/'clamd.sock'
        self.original=daemon_config(self.endpoint,root/'db')
        self.config.write_text(self.original,encoding='utf-8'); self.config.chmod(0o600)
        server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        server.bind(str(self.endpoint)); self.endpoint.chmod(0o600)
        self.addCleanup(server.close)
        with patch.dict(os.environ, {'WZOS_CLAMD_SOCKET':str(self.endpoint),'WZOS_CLAMD_CONFIG':str(self.config)}):
            self.scanner=ClamdScanner()

    def test_private_policy_and_socket_are_accepted(self):
        self.scanner.validate_policy()

    def test_world_readable_socket_or_mutable_config_is_rejected(self):
        self.endpoint.chmod(0o666)
        with self.assertRaises(ValueError): self.scanner.validate_policy()
        self.endpoint.chmod(0o600); self.config.chmod(0o666)
        with self.assertRaises(ValueError): self.scanner.validate_policy()

    def test_tcp_duplicate_weakened_and_symlink_policies_are_rejected(self):
        for change in [self.original+'TCPSocket 3310\n',self.original+'MaxThreads 1\n',
                       self.original.replace('AlertExceedsMax yes','AlertExceedsMax no')]:
            self.config.write_text(change,encoding='utf-8')
            with self.assertRaises(ValueError): self.scanner.validate_policy()
        self.config.write_text(self.original,encoding='utf-8')
        target=self.config.with_suffix('.real'); self.config.rename(target); self.config.symlink_to(target)
        with self.assertRaises(ValueError): self.scanner.validate_policy()

    def test_optional_certificate_bundle_requires_private_trusted_directory(self):
        certs=Path(self.temp.name)/'certs'; certs.mkdir(mode=0o700)
        self.config.write_text(daemon_config(self.endpoint,Path(self.temp.name)/'db',certs),encoding='utf-8')
        self.scanner.validate_policy()
        certs.chmod(0o777)
        with self.assertRaises(ValueError): self.scanner.validate_policy()


if __name__ == '__main__': unittest.main()
