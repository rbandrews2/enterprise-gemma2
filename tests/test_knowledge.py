import hashlib
import io
import json
import tempfile
import unittest
import asyncio
import subprocess
from unittest.mock import patch
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from services.v2.app import create_app
from services.v2.settings import Settings
from services.v2.knowledge.download import DownloadError, download
from services.v2.knowledge.extract import extract
from services.v2.knowledge.models import Source, load_catalog
from services.v2.knowledge.store import Store, IndexUnavailable


HTML = b'<html><body><nav>discard me</nav><main><h1 id="safety">Safety</h1><p>Flagger reference alpha</p><h2 id="training">Training</h2><p>Worker reference beta</p><script>ignore me</script></main></body></html>'


def source(source_id="test-source", kind="html", agency="VDOT"):
    return Source(id=source_id, agency=agency, title="Test official source",
                  url="https://www.vdot.virginia.gov/test", publication_page="https://www.vdot.virginia.gov/test",
                  jurisdiction="VA", kind=kind, links_verified_on="2026-09-17",
                  applicability_note="Test fixture only")


def client_for(content=HTML, status=200, mime="text/html", headers=None):
    return httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, content=content, headers={"content-type": mime, **(headers or {})})))


def sample_pdf(blank=False):
    # In-memory fixture, not a user document. Physical page 2 carries the marker.
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.add_blank_page(width=612, height=792)
    if not blank:
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                 NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(b'BT /F1 12 Tf 20 700 Td (Unique flagger reference on physical page two) Tj ET')
        page[NameObject('/Contents')] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class ExtractionTests(unittest.TestCase):
    def test_html_headings_and_excluded_content(self):
        result = extract(HTML, "html")
        self.assertEqual([p["section"] for p in result["passages"]], ["Safety", "Training"])
        self.assertEqual(result["passages"][1]["anchor"], "training")
        self.assertNotIn("discard", str(result))
        self.assertNotIn("ignore", str(result))

    def test_pdf_physical_page_and_blank_page_warning(self):
        result = extract(sample_pdf(), "pdf")
        self.assertEqual(result["passages"][0]["page"], 2)
        self.assertIn("physical page two", result["passages"][0]["text"])
        self.assertIn("page_1_little_or_no_text", result["warnings"])
        self.assertFalse(extract(sample_pdf(blank=True), "pdf")["passages"])

    def test_unreadable_pdf(self):
        with self.assertRaises(Exception):
            extract(b"%PDF-invalid", "pdf")


class DownloadTests(unittest.TestCase):
    def test_approved_redirect(self):
        item = source()
        item.allowed_redirects = ["https://www.vdot.virginia.gov/approved"]
        def handler(request):
            if request.url.path == '/test':
                return httpx.Response(302, headers={'location': '/approved'})
            return httpx.Response(200, content=HTML, headers={'content-type': 'text/html'})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            self.assertEqual(download(item, client)[1], item.allowed_redirects[0])

    def test_stream_size_without_content_length(self):
        def handler(request):
            return httpx.Response(200, stream=httpx.ByteStream(HTML), headers={'content-type': 'text/html'})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(DownloadError):
                download(source(), client, max_bytes=10)

    def test_failed_type_size_signature(self):
        for kwargs in ({"status": 503}, {"mime": "text/plain"},
                       {"content": b"not html"}, {"headers": {"content-length": "99999"}}):
            with self.subTest(kwargs=kwargs), client_for(**kwargs) as client:
                with self.assertRaises(DownloadError):
                    download(source(), client, max_bytes=1000)
        with client_for() as client, self.assertRaises(DownloadError):
            download(source(), client, max_bytes=10)

    def test_redirect_rejected_before_second_request(self):
        seen = []
        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(302, headers={"location": "https://example.com/private"})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises((DownloadError, ValueError)):
                download(source(), client)
        self.assertEqual(len(seen), 1)

    def test_timeout(self):
        def handler(request):
            raise httpx.ReadTimeout("test")
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(httpx.ReadTimeout):
                download(source(), client)

    def test_invalid_catalog_host(self):
        data = source().model_dump()
        for url in ['http://www.vdot.virginia.gov/test', 'https://127.0.0.1/test',
                    'https://www.vdot.virginia.gov.attacker.example/test']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                Source.model_validate(data | {"url": url})


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name), {"test-source": source()})
        self.api = TestClient(create_app(Settings(), knowledge_store=self.store))

    def ingest(self, content=HTML):
        with client_for(content) as client:
            return self.store.ingest("test-source", client)

    def test_revisions_duplicate_rebuild_and_review(self):
        first = self.ingest()
        self.assertEqual(first["status"], "extracted")
        self.assertEqual(self.ingest()["status"], "unchanged")
        self.assertEqual(len(self.store.revisions("test-source")), 1)
        self.store.check_extraction("test-source", first["revision"], "Checked Safety and Training headings against fixture")
        self.store.rebuild()
        original = self.store.search("flagger")
        self.assertEqual(original["results"][0]["review_status"], "extraction_checked")
        self.assertTrue(original["results"][0]["url"].endswith("#safety"))
        self.assertFalse(self.store.detail("test-source")["revisions"][0]["applicability_reviewed"])
        second = self.ingest(HTML.replace(b"alpha", b"changed"))
        self.assertNotEqual(first["revision"], second["revision"])
        self.store.rebuild()
        rows = self.store.search("flagger")["results"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(row["is_latest"] for row in rows), 1)
        (self.store.data / "index.sqlite").unlink()
        self.store.rebuild()
        self.assertEqual(rows, self.store.search("flagger")["results"])

    def test_failed_download_keeps_existing_revision(self):
        self.ingest()
        with client_for(status=403) as client:
            self.assertEqual(self.store.ingest("test-source", client)["status"], "unavailable")
        self.assertEqual(len(self.store.revisions("test-source")), 1)
        self.assertEqual(self.store.detail("test-source")["ingestion"]["error"], "http_403")

    def test_reverted_remote_content_becomes_latest_download(self):
        first = self.ingest()
        self.ingest(HTML.replace(b'alpha', b'changed'))
        self.ingest()
        self.store.rebuild()
        current = [r for r in self.store.search('flagger')['results'] if r['is_latest']]
        self.assertEqual(current[0]['revision'], first['revision'])

    def test_invalid_pdf_preserved_without_search_results(self):
        item = source(kind='pdf')
        store = Store(self.store.data, {item.id: item})
        with client_for(b'%PDF-invalid', mime='application/pdf') as client:
            result = store.ingest(item.id, client)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue((store.data / 'revisions' / item.id / result['revision'] / 'original.pdf').exists())
        self.assertEqual(store.rebuild(), 0)
        with self.assertRaises(ValueError):
            store.check_extraction(item.id, result['revision'], 'This should never approve failed extraction')

    def test_extraction_timeout_can_retry_preserved_original(self):
        with patch('services.v2.knowledge.store.subprocess.run', side_effect=subprocess.TimeoutExpired('extract', 120)):
            result = self.ingest()
        self.assertEqual(result['status'], 'failed')
        self.store.retry_extraction('test-source', result['revision'])
        self.assertEqual(self.store.revisions('test-source')[0]['extraction_state'], 'extracted')
        self.assertEqual(self.store.rebuild(), 2)
        with self.assertRaises(ValueError):
            self.store.retry_extraction('test-source', result['revision'])

    def test_superseded_flag_visible(self):
        self.ingest()
        self.store.catalog['test-source'].publication_status = 'superseded'
        self.store.rebuild()
        self.assertEqual(self.store.search('flagger')['results'][0]['publication_status'], 'superseded')

    def test_nonlocal_api_request_rejected(self):
        async def check():
            transport = httpx.ASGITransport(app=create_app(Settings(), knowledge_store=self.store), client=('203.0.113.2', 4000))
            async with httpx.AsyncClient(transport=transport, base_url='http://localhost') as client:
                return await client.get('/v2/sources', headers={'x-forwarded-for': '127.0.0.1'})
        self.assertEqual(asyncio.run(check()).status_code, 403)

    def test_corruption_does_not_replace_good_index(self):
        result = self.ingest()
        self.store.rebuild()
        before = (self.store.data / "index.sqlite").read_bytes()
        folder = self.store.data / "revisions" / "test-source" / result["revision"]
        (folder / "original.html").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.store.rebuild()
        self.assertEqual(before, (self.store.data / "index.sqlite").read_bytes())

    def test_api_filters_pagination_and_errors(self):
        self.assertEqual(self.api.get('/v2/references/search?q=flagger').status_code, 503)
        self.assertEqual(self.api.get('/v2/sources').json()['results'][0]['ingestion']['status'], 'not_downloaded')
        self.ingest()
        self.store.rebuild()
        self.assertEqual(self.api.get('/v2/sources?agency=OSHA').json()['total'], 0)
        self.assertEqual(self.api.get('/v2/sources?review_status=unreviewed').json()['total'], 1)
        self.assertEqual(self.api.get('/v2/sources/missing').status_code, 404)
        self.assertEqual(self.api.get('/v2/references/search?q=flagger&source_id=missing').status_code, 404)
        for suffix in ['?q=x&limit=51','?q=x&offset=-1','?q=***','?q='+'x'*501,'?q=x&agency=bad']:
            self.assertEqual(self.api.get('/v2/references/search'+suffix).status_code, 422)
        self.assertEqual(self.api.get('/v2/references/search?q=absent').json()['status'], 'empty')
        self.assertEqual(self.api.get('/v2/references/search?q=reference&agency=OSHA').json()['total'], 0)
        response = self.api.get('/v2/references/search?q=reference&source_id=test-source&limit=1&offset=1').json()
        self.assertEqual(response['total'], 2)
        self.assertEqual(len(response['results']), 1)

    def test_catalog_is_valid(self):
        self.assertEqual({item.agency for item in load_catalog().values()}, {'VDOT','FHWA','OSHA','VOSH'})


if __name__ == '__main__':
    unittest.main()
