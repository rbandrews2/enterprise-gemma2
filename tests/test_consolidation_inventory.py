from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.inventory_consolidation import inventory


class InventoryTests(unittest.TestCase):
    def test_counts_without_exporting_values_or_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.sqlite'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE accounts(id TEXT, token TEXT)')
                db.execute("INSERT INTO accounts VALUES ('sample', 'do-not-export')")
                db.commit()
            before = path.read_bytes()
            result = inventory(path)
            self.assertEqual(result['tables'], [{'table': 'accounts', 'rows': 1, 'columns': ['id', 'token']}])
            self.assertNotIn('do-not-export', str(result))
            self.assertEqual(before, path.read_bytes())

    def test_missing_source_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.sqlite'
            with self.assertRaises(FileNotFoundError):
                inventory(path)
            self.assertFalse(path.exists())
