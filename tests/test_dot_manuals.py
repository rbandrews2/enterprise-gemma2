"""Synthetic evidence only: no real inference, downloads or authority claims."""
import asyncio
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import httpx
from reportlab.pdfgen.canvas import Canvas

from services.v2.knowledge.manuals import ManualIndex, ManualQuery, packed
from services.v2.knowledge.models import Source, load_catalog
from services.v2.knowledge.store import IndexUnavailable, Store
from services.workspace_preview.dot_knowledge import GuidelinesGemma, register, validate_draft
from services.workspace_preview.intelligence import ModelUnavailable
from scripts.package_source_library import package, verify


def pdf_bytes():
    output = io.BytesIO()
    canvas = Canvas(output)
    for lines in (
        ['Section 3B.01 Yellow Centerline', 'Standard:', 'Synthetic markings shall use reviewed evidence.', 'Page 3B-1'],
        ['Figure 3B-1. Two-Lane Centerline Markings', 'Guidance:',
         'The synthetic example requires review of the adjoining notes.', 'Page 3B-2'],
        ['Additional source notes continue on this page for manual review.'],
        [],
        ['Page TC-1', 'Figure 3B-1. Two-Lane Centerline Markings ............. 2'],
    ):
        y = 750
        for text in lines:
            canvas.drawString(50, y, text)
            y -= 20
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def official():
    return Source(id='test-manual', agency='VDOT', title='Synthetic manual',
                  url='https://www.vdot.virginia.gov/test.pdf',
                  publication_page='https://www.vdot.virginia.gov/test',
                  edition='Synthetic 1', jurisdiction='VA synthetic only', kind='pdf',
                  document_role='standard', regions=['VA'], effective_from='2020-01-01',
                  publication_status='current_at_verification', links_verified_on='2026-10-20',
                  applicability_note='Synthetic test; no actual engineering requirements')


def query(**changes):
    return ManualQuery(**{'query': 'two lane centerline markings', 'authority': 'VDOT',
                          'region': 'VA', 'as_of': '2026-10-20', **changes})


class ManualTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = official()
        self.store = Store(self.root/'library', {self.source.id: self.source})
        self.pdf = pdf_bytes()
        transport = httpx.MockTransport(lambda request: httpx.Response(
            200, content=self.pdf, headers={'content-type': 'application/pdf'}))
        with httpx.Client(transport=transport) as client:
            self.result = self.store.ingest(self.source.id, client=client)
        self.assertEqual(self.result['status'], 'extracted')
        self.store.check_extraction(self.source.id, self.result['revision'], 'Synthetic pages 1 through 3 checked for this fixture only.')
        self.index = ManualIndex(self.store)
        self.coverage = self.index.rebuild()

    def tearDown(self):
        self.directory.cleanup()

    def test_all_pages_labels_gaps_and_caption_candidates(self):
        coverage = self.coverage['coverage'][0]
        self.assertEqual(coverage['pages'], 5)
        self.assertEqual(coverage['text_gap_pages'], [4])
        self.assertFalse(coverage['all_pages_visually_reviewed'])
        found = self.index.search(query(diagrams_only=True))
        self.assertEqual([p['page'] for p in found['results']], [2])
        page = found['results'][0]
        self.assertEqual(page['label'], '3B-2')
        self.assertIn('#page=2', page['url'])
        self.assertTrue(page['captions'])
        self.assertTrue(page['candidate_only'])
        self.assertFalse(page['approved_for_field_use'])
        self.assertTrue(self.index.outline(self.source.id))
        self.assertNotIn(4, [p['page'] for p in found['results']])
        self.assertNotIn(5, [p['page'] for p in found['results']])

    def test_whole_page_context_and_budget_without_clipping(self):
        packet = self.index.context(query())
        self.assertEqual(packet['status'], 'ready_for_reviewed_answer')
        self.assertLessEqual(len(packed(packet).encode()), 20000)
        self.assertIn('The synthetic example requires review of the adjoining notes.', str(packet))
        small = self.index.context(query(), budget=1000)
        self.assertFalse(small['evidence'])
        self.assertTrue(small['warnings'])

    def test_no_cross_state_authority_edition_or_date_substitution(self):
        for update in ({'authority': 'NCDOT', 'region': 'NC'}, {'region': 'NC'},
                       {'edition': 'Other edition'}, {'as_of': date(2019, 1, 1)}):
            result = self.index.search(query().model_copy(update=update))
            self.assertEqual(result['status'], 'no_governing_source')
            self.assertFalse(result['results'])

    def test_diagram_discovery_uses_adjacent_notes_but_not_tables(self):
        # All these words occur on physical page1, while the figure is on page2.
        result = self.index.search(query(query='synthetic reviewed evidence', diagrams_only=True))
        self.assertEqual([p['page'] for p in result['results']], [2])
        self.assertIn(1, result['results'][0]['keyword_match_pages'])
        self.assertEqual(result['diagram_match_basis'], 'same_or_adjacent_page_keywords')

    def test_literal_query_rejects_operators_and_empty_terms(self):
        self.index.search(query().model_copy(update={'query': 'centerline" OR x:foo* NOT (bar)'}))
        self.assertTrue(self.index.search(query())['results'])
        with self.assertRaises(ValueError):
            self.index.search(query().model_copy(update={'query': 'what are the requirements'}))

    def test_training_and_unknown_currency_cannot_enable_answers(self):
        for change in ({'document_role': 'training'}, {'publication_status': 'unknown'}):
            self.store.catalog[self.source.id] = self.source.model_copy(update=change)
            self.index.rebuild()
            packet = self.index.context(query())
            self.assertEqual(packet['status'], 'source_review_required')
            self.assertFalse(any(p['answer_eligible'] for p in packet['evidence']))

    def test_stale_and_changed_index_fail_closed(self):
        self.store.catalog[self.source.id] = self.source.model_copy(update={'edition': 'Changed'})
        with self.assertRaises(IndexUnavailable):
            self.index.search(query())

    def test_catalog_changes_cannot_relabel_an_old_document(self):
        self.store.catalog[self.source.id] = self.source.model_copy(update={'edition': 'Changed'})
        self.index.rebuild()
        result = self.index.search(query())['results']
        self.assertEqual(result[0]['edition'], 'Synthetic 1')
        self.assertFalse(result[0]['answer_eligible'])
        self.assertFalse(self.index.search(query(edition='Changed'))['results'])
        self.store.catalog[self.source.id] = self.source
        self.index.path.write_bytes(b'altered')
        with self.assertRaises(IndexUnavailable):
            self.index.search(query())

    def test_original_tampering_blocks_rebuild_and_render(self):
        original = self.store.data/'revisions'/self.source.id/self.result['revision']/'original.pdf'
        original.write_bytes(b'%PDF-altered')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.index.rebuild()
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.index.render_page(self.source.id, self.result['revision'], 2, self.root/'page.png')

    def test_full_page_render_and_snapshot_rebuild(self):
        self.index.annotate_page(self.source.id, self.result['revision'], 2,
                                 'Figure 3B-1. Synthetic example', 'synthetic reference',
                                 'Synthetic page label only; no engineering approval.')
        self.index.rebuild()
        output = self.index.render_page(self.source.id, self.result['revision'], 2, self.root/'page.png')
        self.assertTrue(output.read_bytes().startswith(b'\x89PNG'))
        report = package(self.store, self.root/'snapshot')
        self.assertEqual(verify(self.root/'snapshot'), report)
        snapshot = ManualIndex(Store(self.root/'snapshot', self.store.catalog))
        self.assertTrue(snapshot.search(query())['results'])
        self.assertTrue((self.root/'snapshot/revisions'/self.source.id/self.result['revision']/'page-annotations.json').exists())
        with self.assertRaises(FileExistsError):
            self.index.render_page(self.source.id, self.result['revision'], 2, output)

    def test_header_only_diagram_is_not_treated_as_extracted_body(self):
        self.assertEqual(self.index.search(query(diagrams_only=True))['results'][0]['page'], 2)
        self.index.annotate_page(self.source.id, self.result['revision'], 4,
                                'Figure 3B-9. Image-only synthetic diagram', 'diagram image',
                                'Synthetic visual tag; the image is not transcribed.')
        self.index.rebuild()
        result = self.index.search(query(query='diagram image', diagrams_only=True))
        self.assertTrue(result['results'][0]['image_review_required'])
        packet = self.index.context(query(query='diagram image'))
        self.assertEqual(packet['status'], 'image_review_required')

    def test_pinned_import_never_downloads_or_claims_official_identity(self):
        item = self.source.model_copy(update={
            'id': 'imported-manual', 'origin': 'user_import',
            'url': 'https://drive.google.com/file/d/synthetic-file/view',
            'pinned_sha256': hashlib.sha256(self.pdf).hexdigest()})
        item = Source.model_validate(item.model_dump())
        store = Store(self.root/'imports', {item.id: item})
        path = self.root/'input.pdf'
        path.write_bytes(self.pdf)
        with patch('services.v2.knowledge.store.download', side_effect=AssertionError('No download')):
            result = store.ingest(item.id, local_pdf=path)
            self.assertEqual(result['status'], 'extracted')
            self.assertEqual(store.ingest(item.id)['status'], 'unavailable')
        manifest = store.revisions(item.id)[0]
        self.assertFalse(manifest['provenance']['official_identity_verified'])
        self.assertFalse(manifest['extraction_checked'])
        path.write_bytes(b'%PDF-wrong')
        self.assertEqual(store.ingest(item.id, local_pdf=path)['status'], 'unavailable')
        self.assertEqual(len(store.revisions(item.id)), 1)

    def test_cited_quotes_and_unknown_citations_are_validated(self):
        packet = self.index.context(query())
        page = next(p for p in packet['evidence'] if 'Synthetic markings shall' in p['text'])
        value = {'status': 'draft', 'claims': [{'text': 'Review synthetic evidence.',
                 'citation_id': page['citation_id'], 'supporting_quote': 'Synthetic markings shall use reviewed evidence.'}],
                 'unresolved': []}
        self.assertEqual(validate_draft(value, packet).status, 'draft')
        for change in ({'citation_id': 'made-up'}, {'supporting_quote': 'An invented rule that is not on this page.'}):
            bad = json.loads(json.dumps(value))
            bad['claims'][0].update(change)
            with self.assertRaises(ValueError):
                validate_draft(bad, packet)

    def test_enterprise_auth_flags_and_review_gate_precede_provider(self):
        class Model:
            calls = 0
            async def ask(self, packet):
                self.calls += 1
                return {'draft': 'synthetic'}
        model = Model()
        app = FastAPI()
        def actor(request):
            identity = request.headers.get('x-test-user')
            if not identity:
                raise HTTPException(401)
            return {'id': identity, 'organization_id': 'synthetic-org',
                    'edition': 'core' if identity == 'core' else 'enterprise'}
        register(app, actor, self.store, model)
        payload = query().model_dump(mode='json')
        with TestClient(app) as client, patch.dict(os.environ, {'WZOS_ATLAS_DOT_ENABLED': '0'}):
            self.assertEqual(client.post('/api/atlas/dot/ask', json=payload).status_code, 401)
            self.assertEqual(client.post('/api/atlas/dot/ask', json=payload, headers={'x-test-user': 'core'}).status_code, 403)
            self.assertEqual(client.post('/api/atlas/dot/ask', json=payload, headers={'x-test-user': 'enterprise'}).status_code, 503)
        self.store.catalog[self.source.id] = self.source.model_copy(update={'publication_status': 'unknown'})
        self.index.rebuild()
        with TestClient(app) as client, patch.dict(os.environ, {'WZOS_ATLAS_DOT_ENABLED': '1'}):
            result = client.post('/api/atlas/dot/ask', json=payload, headers={'x-test-user': 'enterprise'})
            self.assertEqual(result.status_code, 200)
            self.assertFalse(result.json()['provider_called'])
            self.assertEqual(model.calls, 0)

    def test_supplied_catalog_copy_is_pinned_and_not_training(self):
        source = load_catalog()['vdot-mutcd-user-20261020']
        self.assertEqual(source.origin, 'user_import')
        self.assertEqual(source.document_role, 'standard')
        self.assertEqual(source.regions, ['VA'])
        self.assertEqual(len(source.pinned_sha256), 64)

    def test_model_uses_one_request_and_validates_citations_without_tools(self):
        packet = self.index.context(query())
        page = next(p for p in packet['evidence'] if 'Synthetic markings shall' in p['text'])
        answer = {'status': 'draft', 'claims': [{'text': 'Review synthetic evidence.',
                  'citation_id': page['citation_id'], 'supporting_quote': 'Synthetic markings shall use reviewed evidence.'}],
                  'unresolved': ['Confirm project applicability.']}
        calls = []
        response_tools = []
        def handler(request):
            body = json.loads(request.content)
            calls.append(body)
            self.assertEqual(request.headers['authorization'], 'Bearer test.test.test')
            self.assertFalse(body['stream'])
            self.assertNotIn('tools', body)
            self.assertEqual(body['response_format']['type'], 'json_schema')
            return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
                'message': {'content': json.dumps(answer), 'tool_calls': response_tools}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50}})
        async def token(origin):
            self.assertEqual(origin, 'https://synthetic-model.test.run.app')
            return 'test.test.test'
        model = GuidelinesGemma(httpx.MockTransport(handler), token)
        env = {'WZOS_ATLAS_DOT_INFERENCE_ENABLED': '1', 'WZOS_ATLAS_DOT_MODEL_URL': 'https://synthetic-model.test.run.app'}
        with patch.dict(os.environ, env):
            result = asyncio.run(model.ask(packet))
            self.assertEqual(len(calls), 1)
            self.assertTrue(result['qualified_review_required'])
            self.assertFalse(result['approved_for_field_use'])
            response_tools.append({'function': {'name': 'do_not_execute'}})
            with self.assertRaises(ModelUnavailable):
                asyncio.run(model.ask(packet))
            self.assertEqual(len(calls), 2)  # Two explicit calls, no automatic retries.
        with patch.dict(os.environ, {'WZOS_ATLAS_DOT_INFERENCE_ENABLED': '0'}):
            with self.assertRaises(ModelUnavailable):
                asyncio.run(model.ask(packet))
            self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
