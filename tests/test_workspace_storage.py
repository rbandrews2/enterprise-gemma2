import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.workspace_preview.storage import SQLiteStorage


class StorageTests(unittest.TestCase):
    def test_rollback_and_snapshot_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = SQLiteStorage(root / 'source.sqlite')
            with store.connect() as db:
                db.execute('CREATE TABLE entries (id INTEGER PRIMARY KEY, note TEXT)')
                db.execute("INSERT INTO entries VALUES (1, 'committed')")
            with self.assertRaises(RuntimeError):
                with store.connect() as db:
                    db.execute("INSERT INTO entries VALUES (2, 'rolled back')")
                    raise RuntimeError()
            store.snapshot(root / 'backup.sqlite')
            SQLiteStorage(root / 'backup.sqlite').snapshot(root / 'restored.sqlite')
            with SQLiteStorage(root / 'restored.sqlite').connect() as db:
                self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM entries')], [(1, 'committed')])
            with self.assertRaises(FileExistsError):
                store.snapshot(root / 'backup.sqlite')

    def test_missing_and_corrupt_sources_do_not_create_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('missing', 'corrupt'):
                source = root / name
                if name == 'corrupt':
                    source.write_bytes(b'not a database')
                with self.assertRaises(sqlite3.DatabaseError):
                    SQLiteStorage(source).snapshot(root / 'backup.sqlite')
                self.assertFalse((root / 'backup.sqlite').exists())
            self.assertFalse((root / 'missing').exists())
