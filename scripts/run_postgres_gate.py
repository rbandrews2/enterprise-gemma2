"""Run the complete suite against an operator-configured disposable PostgreSQL DB.

A passing SQLite suite with skipped PostgreSQL cases cannot satisfy this gate.
Never prints the database connection string. Each PostgreSQL fixture owns and
removes its isolated test schema; supply only a designated test database.
"""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def gate_passed(result):
    return result.testsRun > 0 and result.wasSuccessful() and not result.skipped


def discover_suite(root=ROOT):
    # tests is intentionally a non-package directory in a clean Git checkout.
    # A fresh loader avoids retaining a previous discovery top-level directory.
    return unittest.TestLoader().discover(str(root / "tests"))


def main():
    if not os.environ.get('WZOS_TEST_DATABASE_URL', '').strip():
        print('PostgreSQL gate blocked: WZOS_TEST_DATABASE_URL is not configured.', file=sys.stderr)
        return 2
    suite = discover_suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = gate_passed(result)
    print(f'PostgreSQL gate: {"PASS" if passed else "FAIL"}; '
          f'run={result.testsRun}, failures={len(result.failures)}, '
          f'errors={len(result.errors)}, skipped={len(result.skipped)}')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
