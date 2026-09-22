"""SQLite transaction and consistent snapshot boundary; not cloud persistence."""
from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3


class SQLiteStorage:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def snapshot(self, destination: Path):
        """Copy a consistent committed database, refusing overwrite or missing input."""
        destination = Path(destination)
        # Read-only URI prevents a missing source from becoming an empty database.
        with closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)) as source:
            if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Source database failed integrity check')
            # Exclusive creation also refuses a destination symlink or existing file.
            with destination.open('xb'):
                pass
            try:
                target = sqlite3.connect(destination)
                try:
                    source.backup(target)
                    if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise ValueError('Snapshot failed integrity check')
                finally:
                    target.close()
            except BaseException:
                destination.unlink(missing_ok=True)
                raise
