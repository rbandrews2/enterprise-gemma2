import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from services.v2.knowledge.extract import extract
from services.v2.knowledge.models import Source
from services.v2.knowledge.store import Store
from services.v2.knowledge.word import checked_zip
from scripts.package_source_library import package, verify


def zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, value in files.items():
            z.writestr(name, value)
    return buffer.getvalue()


XML = b'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>Pavement marking materials</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Material</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Inspection</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>'''


class WordSourceTests(unittest.TestCase):
    def test_table_and_paragraph_citations_have_no_invented_page(self):
        result = extract(zip_bytes({'word/document.xml': XML}), 'docx')
        self.assertEqual(result['passages'][1]['section'], 'Table 2, row 1')
        self.assertEqual(result['passages'][1]['text'], 'Material | Inspection')
        self.assertIsNone(result['passages'][0]['page'])
        self.assertIn('table_structure_requires_visual_review', result['warnings'])

    def test_unsafe_archives_and_active_content_rejected(self):
        for files in ({'../outside': b'x'}, {'C:/outside': b'x'}):
            with self.assertRaises(ValueError):
                checked_zip(zip_bytes(files))
        with self.assertRaises(ValueError):
            checked_zip(zip_bytes({'large': b'12345'}), max_total=4)
        for files in ({'word/document.xml': XML, 'word/vbaProject.bin': b'x'},
                      {'word/document.xml': XML.replace(b'<w:p>', b'<w:ins><w:p>', 1).replace(b'</w:p>', b'</w:p></w:ins>', 1)},
                      {'word/document.xml': b'<!DOCTYPE x><x/>'}):
            with self.assertRaises(ValueError):
                extract(zip_bytes(files), 'docx')

    def test_pinned_member_ingestion_search_duplicate_and_snapshot(self):
        original = zip_bytes({'word/document.xml': XML})
        archive = zip_bytes({'marking.docx': original})
        source = Source(id='marking-doc', agency='VDOT', title='Test marking document',
            url='https://www.vdot.virginia.gov/test.zip', publication_page='https://www.vdot.virginia.gov/test',
            kind='docx', jurisdiction='VA', links_verified_on='2026-10-01', applicability_note='Fixture only',
            archive_member='marking.docx', archive_sha256=hashlib.sha256(archive).hexdigest())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive.zip'
            path.write_bytes(archive)
            store = Store(Path(tmp) / 'data', {source.id: source})
            result = store.ingest(source.id, archive_path=path)
            self.assertEqual(result['status'], 'extracted')
            self.assertEqual(store.ingest(source.id, archive_path=path)['status'], 'unchanged')
            store.rebuild()
            row = store.search('pavement')['results'][0]
            self.assertEqual(row['section'], 'marking.docx / Paragraph 1')
            self.assertEqual(row['revision'], hashlib.sha256(original).hexdigest())
            self.assertFalse(row['applicability_reviewed'])
            destination = Path(tmp) / 'snapshot'
            package(store, destination)
            self.assertFalse(verify(destination)['applicability_verified'])
            path.write_bytes(b'changed')
            self.assertEqual(store.ingest(source.id, archive_path=path)['status'], 'unavailable')
            self.assertEqual(store.revisions(source.id)[0]['revision'], result['revision'])
