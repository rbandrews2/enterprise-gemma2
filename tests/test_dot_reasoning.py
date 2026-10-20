"""Synthetic evidence and request controls; never call real providers."""
import asyncio
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
import httpx

from services.v2.knowledge.manuals import ManualIndex
from services.v2.knowledge.manual_review import review
from services.v2.knowledge.store import Store
from services.workspace_preview.atlas_requests import AtlasRequests
from services.workspace_preview.dot_calculations import Calculation, arithmetic, verify_calculations
from services.workspace_preview.dot_knowledge import GuidelinesGemma
from services.workspace_preview.intelligence import ModelUnavailable
import test_dot_manuals as fixture


class ReasoningTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = fixture.official()
        self.store = Store(self.root/'sources', {self.source.id: self.source})
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
                200, content=fixture.pdf_bytes(), headers={'content-type': 'application/pdf'}))) as client:
            self.revision = self.store.ingest(self.source.id, client=client)['revision']
        self.store.check_extraction(self.source.id, self.revision, 'Synthetic extraction only, not actual road requirements.')
        self.index = ManualIndex(self.store)
        self.index.rebuild()

    def tearDown(self):
        self.directory.cleanup()

    def reviewed(self):
        for page in (1, 2, 3):
            review(self.store, self.source.id, self.revision, page,
                   'Synthetic original compared with extracted fixture text and all notes; no actual engineering approval.')
        self.index.rebuild()

    def test_complete_section_and_page_specific_review(self):
        packet = self.index.context(fixture.query(query='yellow centerline'))
        self.assertEqual(packet['status'], 'source_review_required')
        self.assertIn(3, [p['page'] for p in packet['evidence']])
        self.reviewed()
        packet = self.index.context(fixture.query(query='yellow centerline'))
        self.assertEqual(packet['status'], 'ready_for_reviewed_answer')
        self.assertIn('Additional source notes continue', packet['evidence'][2]['text'])

    def test_partial_lexical_match_does_not_replace_model_reasoning_with_a_keyword_gate(self):
        self.reviewed()
        packet = self.index.context(fixture.query(query='Explain synthetic markings uncertainty'))
        self.assertEqual(packet['status'], 'ready_for_reviewed_answer')
        self.assertIn('matched partially', str(packet['warnings']))
        self.assertIn(3, [p['page'] for p in packet['evidence']])

    def test_missing_mandatory_correction_blocks_base_only_answer(self):
        self.reviewed()
        self.store.catalog[self.source.id] = self.source.model_copy(update={
            'required_companions': {'missing-errors': 'a'*64}})
        self.index.rebuild()
        packet = self.index.context(fixture.query())
        self.assertEqual(packet['status'], 'needs_clarification')
        self.assertFalse(packet['evidence'])
        self.assertIn('correction', str(packet['warnings']))

    def test_changed_ocr_invalidates_page_review(self):
        self.reviewed()
        folder = self.store.data/'revisions'/self.source.id/self.revision
        text = 'Synthetic added OCR - not reviewed.'
        from services.v2.knowledge.manual_review import digest
        (folder/'ocr-pages.json').write_text(json.dumps({'1': {
            'text': text, 'text_sha256': digest(text), 'original_sha256': self.revision,
            'reviewed': False, 'engine': 'synthetic'}}), encoding='utf-8')
        self.index.rebuild()
        packet = self.index.context(fixture.query())
        page = next(p for p in packet['evidence'] if p['page'] == 1)
        self.assertFalse(page['answer_eligible'])
        self.assertFalse(page['page_reviewed'])

    def test_formula_rules_require_exact_reviewed_page_and_survive_context_assembly(self):
        rule = {'formula_id': 'synthetic-formula', 'citation_id': f'{self.source.id}:{self.revision}:1',
                'supporting_quote': 'Synthetic markings shall use reviewed evidence.', 'expression': 'W*2',
                'inputs': {'W': 'ft'}, 'input_bounds': {'W': ['1', '100']}, 'result_unit': 'ft', 'reviewer': 'synthetic operator',
                'review_note': 'Synthetic arithmetic fixture only; not a real formula or engineering recommendation.'}
        with self.assertRaises(ValueError): self.index.add_formula(rule)
        self.reviewed()
        self.index.add_formula(rule)
        self.index.rebuild()
        packet = self.index.context(fixture.query())
        self.assertEqual(packet['formulas'][0]['formula_id'], 'synthetic-formula')
        with self.assertRaises(ValueError): self.index.add_formula(rule)

    def test_pinned_correction_is_included_without_matching_question_keywords(self):
        import io
        from reportlab.pdfgen.canvas import Canvas
        output = io.BytesIO(); canvas = Canvas(output)
        canvas.drawString(40, 750, 'Synthetic erratum: a provisional exception needs verification.')
        canvas.showPage(); canvas.save()
        correction = self.source.model_copy(update={'id': 'synthetic-errors', 'document_role': 'correction',
                                                    'url': 'https://www.vdot.virginia.gov/errors.pdf'})
        self.store.catalog[correction.id] = correction
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
                200, content=output.getvalue(), headers={'content-type': 'application/pdf'}))) as client:
            revision = self.store.ingest(correction.id, client=client)['revision']
        self.store.check_extraction(correction.id, revision, 'Synthetic erratum fixture text checked; not actual agency policy.')
        review(self.store, correction.id, revision, 1, 'Synthetic erratum and provisional wording checked against fixture only; no actual approval.')
        self.store.catalog[self.source.id] = self.source.model_copy(update={'required_companions': {correction.id: revision}})
        self.reviewed()
        packet = self.index.context(fixture.query(query='yellow centerline'))
        self.assertEqual(packet['status'], 'ready_for_reviewed_answer')
        self.assertIn(correction.id, [page['source_id'] for page in packet['evidence']])

    def test_errata_running_title_is_not_extracted_table_content(self):
        import io
        from reportlab.pdfgen.canvas import Canvas
        output = io.BytesIO(); canvas = Canvas(output)
        canvas.drawString(20, 750, 'LIST OF KNOWN ERRORS IN VWAPM VERSION 11.0 (JANUARY 2026 EDITION)')
        canvas.rect(40, 100, 500, 400); canvas.showPage(); canvas.save()
        source = self.source.model_copy(update={'id': 'synthetic-image-errors', 'document_role': 'correction',
                                                'url': 'https://www.vdot.virginia.gov/image-errors.pdf'})
        self.store.catalog[source.id] = source
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
                200, content=output.getvalue(), headers={'content-type': 'application/pdf'}))) as client:
            self.store.ingest(source.id, client=client)
        coverage = self.index.rebuild()['coverage']
        self.assertEqual(next(row for row in coverage if row['source_id'] == source.id)['text_gap_pages'], [1])

    def test_token_overflow_stops_before_generation(self):
        self.reviewed()
        calls = []
        def handler(request):
            calls.append(request.url.path)
            return httpx.Response(200, json={'count': 30000, 'max_model_len': 32767})
        async def token(origin): return 'test.test.test'
        model = GuidelinesGemma(httpx.MockTransport(handler), token)
        with patch.dict('os.environ', {'WZOS_ATLAS_DOT_INFERENCE_ENABLED': '1',
                                     'WZOS_ATLAS_DOT_MODEL_URL': 'https://synthetic.test.run.app'}):
            with self.assertRaisesRegex(ModelUnavailable, 'window'):
                asyncio.run(model.ask(self.index.context(fixture.query())))
        self.assertEqual(calls, ['/tokenize'])


class CalculationTests(unittest.TestCase):
    def test_arithmetic_is_bounded_and_never_executes_code(self):
        self.assertEqual(str(arithmetic('W*S**2/60', {'W': 12, 'S': 30})), '180')
        for expression in ('__import__("os")', 'x.y', '1/0', '10**999999', '[x for x in y]', '('):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                arithmetic(expression, {})

    def test_only_reviewed_formula_and_explicit_units(self):
        packet = {'question': 'Synthetic width 12 ft and speed 30 mph.', 'evidence': [
            {'citation_id': 'synthetic:1', 'answer_eligible': True, 'text': 'Synthetic formula L = W*S**2/60. Not a real requirement.'}],
            'formulas': [{'formula_id': 'synthetic', 'citation_id': 'synthetic:1',
                          'supporting_quote': 'Synthetic formula L = W*S**2/60.',
                          'expression': 'W*S**2/60', 'inputs': {'W': 'ft', 'S': 'mph'}, 'input_bounds': {'W': ['1', '100'], 'S': ['1', '100']}, 'result_unit': 'ft'}]}
        calculation = Calculation(formula_id='synthetic', inputs=[
            {'name': 'W', 'value': '12', 'unit': 'ft', 'question_quote': '12 ft'},
            {'name': 'S', 'value': '30', 'unit': 'mph', 'question_quote': '30 mph'}])
        result = verify_calculations([calculation], packet)[0]
        self.assertEqual(result['result'], '180')
        self.assertFalse(result['applicability_verified'])
        with self.assertRaises(ValueError):
            verify_calculations([calculation], {**packet, 'formulas': []})
        calculation.inputs[0].unit = 'm'
        with self.assertRaises(ValueError): verify_calculations([calculation], packet)


class AdmissionTests(unittest.TestCase):
    def test_shared_limits_duplicate_and_tenant_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'requests.sqlite'
            @contextmanager
            def connect():
                db = sqlite3.connect(path)
                db.row_factory = sqlite3.Row
                try:
                    with db: yield db
                finally: db.close()
            first, second = AtlasRequests(connect), AtlasRequests(connect)
            a = {'id': 'a', 'organization_id': 'alpha'}
            b = {'id': 'b', 'organization_id': 'beta'}
            c = {'id': 'c', 'organization_id': 'gamma'}
            first.change('dot:1', a, 'start')
            with self.assertRaises(HTTPException) as error: second.change('dot:2', a, 'start')
            self.assertEqual(error.exception.status_code, 429)
            second.change('dot:2', b, 'start')
            with self.assertRaises(HTTPException) as error: first.change('dot:3', c, 'start')
            self.assertEqual(error.exception.status_code, 429)
            with self.assertRaises(HTTPException) as error: first.change('dot:1', b, 'read')
            self.assertEqual(error.exception.status_code, 404)
            first.change('dot:1', a, 'completed')
            with self.assertRaises(HTTPException) as error: second.change('dot:1', a, 'start')
            self.assertEqual(error.exception.status_code, 409)
            second.change('dot:2', b, 'completed')
            for number in range(3, 8):
                first.change('dot:'+str(number), a, 'start')
                first.change('dot:'+str(number), a, 'completed')
            with self.assertRaises(HTTPException) as error: first.change('dot:8', a, 'start')
            self.assertEqual(error.exception.status_code, 429)


if __name__ == '__main__': unittest.main()
