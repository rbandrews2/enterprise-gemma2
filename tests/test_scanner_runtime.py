import os
import subprocess
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from services.workspace_preview.scanner_runtime import Runtime, SupervisedScanner, lifetime


class RuntimeTests(unittest.TestCase):
    def test_lifetime_reserves_refresh_margin_and_rejects_stale_future(self):
        now = datetime(2026,10,15,12)
        def version(age):
            return 'ClamAV 1.5.4/12345/'+(now-age).strftime('%a %b %d %H:%M:%S %Y')
        self.assertEqual(lifetime(version(timedelta()),now),20*3600)
        self.assertEqual(lifetime(version(timedelta(hours=22)),now),3600)
        for age in (timedelta(hours=23),timedelta(days=2),timedelta(seconds=-1)):
            with self.assertRaises(ValueError): lifetime(version(age),now)

    def runtime(self):
        with patch('services.workspace_preview.scanner_runtime.private_directory'):
            return Runtime('/private')

    def test_wait_aborts_on_signal_timeout_and_failed_updater(self):
        runtime=self.runtime(); child=Mock()
        child.poll.return_value=None
        runtime.stop.set()
        with self.assertRaises(RuntimeError): runtime.wait(child, float('inf'))
        runtime.stop.clear()
        with self.assertRaises(RuntimeError): runtime.wait(child,0)
        child.poll.return_value=1; child.returncode=1
        with self.assertRaises(RuntimeError): runtime.wait(child,float('inf'))

    def test_child_failure_or_recycle_stops_supervision(self):
        runtime=self.runtime(); dead=Mock(); dead.poll.return_value=1
        runtime.children=[dead]
        with patch.object(Path,'exists',return_value=False): self.assertEqual(runtime.monitor(),1)
        runtime.children=[]
        with patch.object(Path,'exists',return_value=True): self.assertEqual(runtime.monitor(),0)

    def test_cleanup_signals_all_children_then_kills_stuck_child(self):
        runtime=self.runtime(); children=[Mock(),Mock()]
        for child in children: child.poll.return_value=None
        children[0].wait.side_effect=[subprocess.TimeoutExpired('synthetic',1),0]
        runtime.children=children
        runtime.close()
        for child in children: child.terminate.assert_called_once()
        children[0].kill.assert_called_once()

    def test_expired_worker_holds_without_engine_and_sets_recycle_marker(self):
        with patch.dict(os.environ,{'WZOS_CLAMD_SOCKET':str(Path.cwd()/'private'/'clamd.sock'),
                                    'WZOS_CLAMD_CONFIG':str(Path.cwd()/'private'/'clamd.conf'),
                                    'WZOS_SCANNER_INSTANCE_DEADLINE':'1'}):
            scanner=SupervisedScanner()
        with patch('services.workspace_preview.scanner_runtime.time.monotonic',return_value=2), \
             patch('services.workspace_preview.scanner_runtime.private_directory'), \
             patch('services.workspace_preview.scanner_runtime.os.open',return_value=99) as create, \
             patch('services.workspace_preview.scanner_runtime.os.close'), \
             patch.object(scanner.engine,'scan') as engine:
            self.assertEqual(scanner.scan(b'synthetic').status,'error')
            create.assert_called_once()
            engine.assert_not_called()

    def test_invalid_worker_deadline_is_not_a_fallback(self):
        for value in ('nan','inf','0','invalid'):
            with patch.dict(os.environ,{'WZOS_SCANNER_INSTANCE_DEADLINE':value}):
                with self.assertRaises(ValueError): SupervisedScanner()
