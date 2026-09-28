import tempfile
import unittest
from pathlib import Path
from scripts.package_source_library import package, verify
from services.v2.knowledge.store import Store
from test_knowledge import source, client_for


class SourcePackageTests(unittest.TestCase):
    def test_snapshot_rebuilds_and_excludes_unrelated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = source()
            store = Store(root/'sources', {item.id:item})
            with client_for() as client:
                store.ingest(item.id, client)
            (store.data/'customer-secret.txt').write_text('not for deployment')
            report = package(store, root/'snapshot')
            self.assertFalse((root/'snapshot/customer-secret.txt').exists())
            self.assertFalse(report['applicability_verified'])
            self.assertEqual(verify(root/'snapshot'), report)
            self.assertEqual(report['coverage'][0]['review_status'], 'unreviewed')
            copied = Store(root/'snapshot', store.catalog)
            self.assertTrue(copied.search('Flagger')['results'])
            with self.assertRaises(FileExistsError):
                package(store, root/'snapshot')
            with self.assertRaises(ValueError):
                package(store, store.data/'nested')
            (root/'snapshot/index.sqlite').write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify(root/'snapshot')

    def test_corrupted_original_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = source()
            store = Store(root/'sources', {item.id:item})
            with client_for() as client:
                result = store.ingest(item.id, client)
            (store.data/'revisions'/item.id/result['revision']/'original.html').write_text('altered')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                package(store, root/'snapshot')
            self.assertFalse((root/'snapshot/snapshot.json').exists())
