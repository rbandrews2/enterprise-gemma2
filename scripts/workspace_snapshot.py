"""Operator backup/restore into a NEW SQLite file; never replaces live data."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.workspace_preview.storage import SQLiteStorage

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    SQLiteStorage(args.source).snapshot(args.destination)
    print('Verified snapshot created. Keep it private; it may contain job and attendance data.')
