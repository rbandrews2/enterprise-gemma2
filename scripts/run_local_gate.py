"""Verbose local regression with per-test timing and a hung-test stack dump.

Does not replace the PostgreSQL gate. A timed-out test terminates this process
with failure; use only local/disposable fixtures, never production configuration.
"""
import argparse
import faulthandler
import sys
import time
import unittest
from run_postgres_gate import discover_suite


class TimedResult(unittest.TextTestResult):
    timeout_seconds = 120

    def startTest(self, test):
        super().startTest(test)
        self.started_at = time.monotonic()
        self.stream.write(f'\nSTART {test.id()}\n')
        self.stream.flush()
        faulthandler.dump_traceback_later(self.timeout_seconds, exit=True)

    def stopTest(self, test):
        faulthandler.cancel_dump_traceback_later()
        self.stream.write(f'END {test.id()} {time.monotonic()-self.started_at:.3f}s\n')
        self.stream.flush()
        super().stopTest(test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-timeout', type=int, default=120)
    args = parser.parse_args()
    if not 10 <= args.test_timeout <= 600:
        parser.error('Test timeout must be 10–600 seconds')
    TimedResult.timeout_seconds = args.test_timeout
    try:
        result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(discover_suite())
    finally:
        faulthandler.cancel_dump_traceback_later()
    passed = result.testsRun > 0 and result.wasSuccessful()
    print(f'Local gate: {"PASS" if passed else "FAIL"}; run={result.testsRun}, '
          f'failures={len(result.failures)}, errors={len(result.errors)}, skipped={len(result.skipped)}', flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
