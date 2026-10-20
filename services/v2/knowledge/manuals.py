"""Page-aware DOT retrieval over the existing immutable source library.

The SQLite file is a disposable search index, never customer persistence. Text
matching discovers reference candidates; it does not establish applicability.
"""
from contextlib import closing
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from pydantic import Field, model_validator

from shared.contracts import StrictModel
from .store import IndexUnavailable, Store, write_json


VERSION = 5
# Whole-section assembly bound, not a claim about token capacity. The serving
# adapter measures the real chat template with the pinned model tokenizer.
MAX_CONTEXT_BYTES = 96000
STOP = set('a an the and or to for in on of is are what which how do does under required '
           'requirement requirements rule rules please tell me about at with from according'.split())
ALIASES = {'flagging': ['flagger', 'flaggers'], 'four': ['4'], 'two': ['2'],
           'striping': ['markings'], 'centerline': ['center line']}
CAPTION = re.compile(r'^\s*(Figure|Table|Typical Application)\s+([A-Z0-9][A-Z0-9.()–-]*)(?:[.\s]+)(.{2,180})$', re.I)
SECTION = re.compile(r'^\s*(Section\s+\d+[A-Z]?(?:\.\d+)?\s+[A-Za-z][^\n]{0,180}|PART\s+\d+\s*[^\n]{0,180}|CHAPTER\s+\d+[A-Z]?\.\s+[A-Za-z][^\n]{0,180})$', re.I)


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class ManualQuery(StrictModel):
    query: str = Field(min_length=2, max_length=500)
    authority: str = Field(pattern=r'^[A-Z][A-Z0-9_-]{1,19}$')
    region: str = Field(pattern=r'^[A-Z]{2}$')
    as_of: date
    source_id: str | None = Field(default=None, pattern=r'^[a-z][a-z0-9-]{1,79}$')
    edition: str | None = Field(default=None, min_length=1, max_length=150)
    diagrams_only: bool = False
    limit: int = Field(default=8, ge=1, le=20)
    offset: int = Field(default=0, ge=0, le=10000)


class FormulaRule(StrictModel):
    formula_id: str = Field(pattern=r'^[a-z][a-z0-9_-]{1,79}$')
    citation_id: str = Field(max_length=180)
    supporting_quote: str = Field(min_length=12, max_length=1200)
    expression: str = Field(min_length=1, max_length=150)
    inputs: dict[str, str] = Field(min_length=1, max_length=8)
    input_bounds: dict[str, tuple[str, str]] = Field(min_length=1, max_length=8)
    result_unit: str = Field(min_length=1, max_length=30)
    reviewer: str = Field(min_length=3, max_length=100)
    review_note: str = Field(min_length=30, max_length=1000)

    @model_validator(mode='after')
    def bounds(self):
        if set(self.inputs) != set(self.input_bounds):
            raise ValueError('Declare lower/upper bounds for every formula input')
        try:
            if any(not Decimal(lo).is_finite() or not Decimal(hi).is_finite() or Decimal(lo) >= Decimal(hi)
                   for lo, hi in self.input_bounds.values()):
                raise ValueError('Invalid reviewed input bounds')
        except InvalidOperation as error:
            raise ValueError('Invalid reviewed input bounds') from error
        return self


def literal_query(text, require_all=True):
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    terms = list(dict.fromkeys(t.lower() for t in re.findall(r'[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+|[a-zA-Z0-9]+', text)
                              if t.lower() not in STOP))[:24]
    if not terms:
        raise ValueError('Enter a work type, topic or diagram description')
    # Terms cannot inject SQL, FTS operators, field names, prefixes or quotes.
    groups = ['(' + ' OR '.join('"' + t + '"' for t in [term, *ALIASES.get(term, [])]) + ')'
              for term in terms]
    return (' AND ' if require_all else ' OR ').join(groups)


def eligible(source, manifest, as_of):
    original = manifest['source']
    return bool(source.origin == original.get('origin', 'official') == 'official'
                and source.edition == original.get('edition') and source.url == original.get('url')
                and source.document_role in {'standard', 'specification', 'correction'}
                and source.publication_status == 'current_at_verification'
                and manifest.get('extraction_checked')
                # An undated correction may support today's verified snapshot,
                # never an assertion that it existed on an earlier project date.
                and ((source.document_role == 'correction' and source.links_verified_on <= as_of)
                     or (source.effective_from and source.effective_from <= as_of))
                and (not source.effective_to or as_of <= source.effective_to))


class ManualIndex:
    def __init__(self, store: Store):
        self.store = store
        self.path = store.data / 'manual-index.sqlite'
        self.metadata = store.data / 'manual-index.json'

    def basis(self):
        rows = []
        for sid, source in sorted(self.store.catalog.items()):
            revisions = self.store.revisions(sid)
            if source.kind != 'pdf' or not revisions:
                continue
            manifest = revisions[0]
            annotations_path = self.store.data / 'revisions' / sid / manifest['revision'] / 'page-annotations.json'
            if annotations_path.exists() and annotations_path.stat().st_size > 1024 * 1024:
                raise ValueError('Oversized page annotations')
            annotations = json.loads(annotations_path.read_text(encoding='utf-8')) if annotations_path.exists() else {}
            formulas_path = annotations_path.with_name('formula-rules.json')
            if formulas_path.exists() and formulas_path.stat().st_size > 65536:
                raise ValueError('Oversized formula rules')
            rules = json.loads(formulas_path.read_text(encoding='utf-8')) if formulas_path.exists() else []
            rules = [FormulaRule.model_validate(rule).model_dump() for rule in rules]
            if len({rule['formula_id'] for rule in rules}) != len(rules):
                raise ValueError('Duplicate reviewed formula')
            sidecars = {}
            for name in ('ocr-pages', 'page-reviews'):
                path = annotations_path.with_name(name + '.json')
                if path.exists() and path.stat().st_size > 20 * 1024 * 1024:
                    raise ValueError('Oversized page sidecar')
                sidecars[name] = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
            rows.append({'source': source.model_dump(mode='json'), 'manifest': manifest, 'annotations': annotations, 'formulas': rules, **sidecars})
        return rows

    def fingerprint(self):
        return hashlib.sha256(packed(self.basis()).encode()).hexdigest()

    def rebuild(self):
        import pypdfium2 as pdfium  # Native parsing stays in the operator process.
        self.store.data.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='manual-', suffix='.sqlite', dir=self.store.data)
        os.close(descriptor)
        coverage = []
        basis = self.basis()
        try:
            with closing(sqlite3.connect(temporary)) as db, db:
                db.execute('CREATE TABLE pages (id INTEGER PRIMARY KEY,source_id TEXT,revision TEXT,page INTEGER,label TEXT,section TEXT,text TEXT,captions TEXT,metadata TEXT,UNIQUE(source_id,revision,page))')
                db.execute("CREATE VIRTUAL TABLE lookup USING fts5(text,captions,content='pages',content_rowid='id',tokenize='porter unicode61')")
                for item in basis:
                    manifest = item['manifest']
                    source = manifest['source']
                    sid, revision = source['id'], manifest['revision']
                    if not re.fullmatch(r'[a-f0-9]{64}', revision):
                        raise ValueError('Invalid source revision')
                    original = self.store.data / 'revisions' / sid / revision / 'original.pdf'
                    if original.stat().st_size > 100 * 1024 * 1024 or hashlib.sha256(original.read_bytes()).hexdigest() != revision:
                        raise ValueError('Original PDF integrity failure')
                    gaps, diagrams, section = [], 0, None
                    with pdfium.PdfDocument(original) as document:
                        if not 1 <= len(document) <= 2000:
                            raise ValueError('Manual page limit')
                        total = len(document)
                        for index in range(total):
                            page = document[index]
                            try:
                                textpage = page.get_textpage()
                                try:
                                    text = re.sub(r'\r\n?', '\n', textpage.get_text_bounded()).strip()
                                finally:
                                    textpage.close()
                            finally:
                                page.close()
                            lines = text.splitlines()
                            headings = [line.strip() for line in lines if SECTION.match(line) and not re.search(r'\.{3,}', line)]
                            # A repeated running chapter header must not terminate
                            # a subsection; prose references such as "Section 6N.01),"
                            # are not headings. Keep all section starts for outline.
                            section_heads = [h for h in headings if h.lower().startswith('section ')]
                            chapters = [h for h in headings if h.lower().startswith('chapter ')]
                            if section_heads:
                                section = section_heads[0]
                            elif chapters:
                                code = re.search(r'\d+[A-Z]?', chapters[0], re.I)[0].upper()
                                previous = re.search(r'\d+[A-Z]?', section or '', re.I)
                                if not previous or previous[0].upper() != code:
                                    section = chapters[0]
                            elif not section and headings:
                                section = headings[0]
                            captions = [line.strip() for line in lines if CAPTION.match(line)]
                            label = re.search(r'\bPage\s+([A-Z0-9][A-Z0-9.\-]*)', text)
                            # Contents lists and cross-reference leaders are not diagram pages.
                            captions = [line for line in captions if not re.search(r'\.{3,}', line)]
                            if label and label[1].upper().startswith('TC-'):
                                captions = []
                            if not re.search(r'INDEX OF SHEETS|STANDARD TITLE PAGE|TABLE OF CONTENTS', text, re.I):
                                codes = re.findall(r'^\s*((?:PM|IM|ED|MM|USP|ISD|SPD|PRS)-\d+[A-Z]?)\s*$', text, re.M)
                                captions.extend('Standard drawing ' + code for code in dict.fromkeys(codes))
                            annotation = item['annotations'].get(str(index + 1))
                            if annotation:
                                captions.append(annotation['caption'])
                                captions.append('Search tags: ' + annotation['keywords'])
                            body_lines = [line for line in lines if not re.search(
                                r'Virginia MUTCD|^\s*Part\s+\d+[A-Z]?\.|^\s*Page\s+\S+|^\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d\s*$', line, re.I)]
                            body_available = len(re.sub(r'\W', '', ' '.join(body_lines))) >= 20
                            if not body_available:
                                gaps.append(index + 1)
                            diagrams += bool(captions)
                            ocr = item['ocr-pages'].get(str(index + 1))
                            if ocr:
                                if (ocr['original_sha256'] != revision or not isinstance(ocr['text'], str)
                                        or hashlib.sha256(ocr['text'].encode()).hexdigest() != ocr['text_sha256']):
                                    raise ValueError('OCR sidecar integrity failure')
                                text = text + '\n\n[OCR transcription - visual review required]\n' + ocr['text']
                            review = item['page-reviews'].get(str(index + 1))
                            reviewed = bool(review and review.get('original_sha256') == revision
                                            and review.get('text_sha256') == hashlib.sha256(text.encode()).hexdigest()
                                            and review.get('reviewer') and len(review.get('note', '')) >= 30)
                            metadata = {'source': source, 'extraction_checked': manifest.get('extraction_checked', False),
                                        'review_status': manifest.get('review_status', 'unreviewed'),
                                        'image_review_required': not body_available and not (reviewed and ocr and len(re.sub(r'\W', '', ocr['text'])) >= 20),
                                        'page_reviewed': reviewed, 'ocr_present': bool(ocr), 'page_annotation': annotation,
                                        'section_headings': headings,
                                        'is_contents': bool(re.search(r'INDEX OF SHEETS|STANDARD TITLE PAGE|TABLE OF CONTENTS|\.{3,}', text, re.I)
                                                            or (label and label[1].upper().startswith('TC-'))),
                                        'retrieved_at': manifest['retrieved_at']}
                            db.execute('INSERT INTO pages(source_id,revision,page,label,section,text,captions,metadata) VALUES(?,?,?,?,?,?,?,?)',
                                       (sid, revision, index + 1, label[1] if label else None, section, text,
                                        '\n'.join(captions), packed(metadata)))
                    coverage.append({'source_id': sid, 'revision': revision, 'pages': total,
                                     'text_gap_pages': gaps, 'caption_candidate_pages': diagrams,
                                     'all_pages_visually_reviewed': False})
                db.execute("INSERT INTO lookup(lookup) VALUES('rebuild')")
            Path(temporary).replace(self.path)
            result = {'schema_version': VERSION, 'basis_sha256': hashlib.sha256(packed(basis).encode()).hexdigest(),
                      'index_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'coverage': coverage}
            write_json(self.metadata, result)
            return result
        finally:
            Path(temporary).unlink(missing_ok=True)

    def connect(self):
        try:
            metadata = json.loads(self.metadata.read_text(encoding='utf-8'))
            if (metadata['schema_version'] != VERSION or metadata['basis_sha256'] != self.fingerprint()
                    or metadata['index_sha256'] != hashlib.sha256(self.path.read_bytes()).hexdigest()):
                raise ValueError('Manual index is stale or changed')
            db = sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)
            db.row_factory = sqlite3.Row
            return db
        except (OSError, ValueError, KeyError, sqlite3.DatabaseError) as error:
            raise IndexUnavailable('Manual index unavailable; operator rebuild required') from error

    def record(self, row, as_of):
        row = dict(row)
        metadata = json.loads(row.pop('metadata'))
        source = self.store.catalog[row['source_id']]
        revision = row['revision']
        manifest = next(m for m in self.store.revisions(source.id) if m['revision'] == revision)
        base_url = manifest['final_url']
        # Drive's view page does not implement PDF physical-page fragments.
        url = base_url if source.origin == 'user_import' else base_url + '#page=' + str(row['page'])
        row.update(citation_id=f'{source.id}:{revision}:{row["page"]}', title=metadata['source']['title'],
                   edition=metadata['source']['edition'], authority=source.agency, regions=source.regions,
                   document_role=source.document_role, origin=metadata['source'].get('origin', 'official'), url=url,
                   usage_note=source.usage_note, publication_page=source.publication_page,
                   review_status=metadata['review_status'], publication_status=source.publication_status,
                   image_review_required=metadata.get('image_review_required', True),
                   page_annotation=metadata.get('page_annotation'),
                   applicability_note=source.applicability_note,
                   page_reviewed=metadata.get('page_reviewed', False),
                   answer_eligible=eligible(source, manifest, as_of) and metadata.get('page_reviewed', False)
                                   and not metadata.get('image_review_required', True),
                   candidate_only=True, approved_for_field_use=False)
        row['captions'] = [line for line in row['captions'].splitlines() if not line.startswith('Search tags:')]
        return row

    def search(self, request: ManualQuery):
        match = literal_query(request.query)
        latest = {item['source']['id']: item['manifest']['source'] for item in self.basis()}
        ids = [sid for sid, source in self.store.catalog.items()
               if source.agency == request.authority and request.region in source.regions
               and (not request.source_id or sid == request.source_id)
               and (not request.edition or latest.get(sid, {}).get('edition') == request.edition)
               and (not source.effective_from or source.effective_from <= request.as_of)
               and (not source.effective_to or request.as_of <= source.effective_to)
               and source.publication_status != 'superseded']
        with closing(self.connect()) as db:
            if not ids:
                return {'status': 'no_governing_source', 'total': 0, 'results': [], 'requirements_determined': False}
            where = "lookup MATCH ? AND json_extract(p.metadata,'$.is_contents')=0 AND p.source_id IN (" + ','.join('?' for _ in ids) + ')'
            params = [match, *ids]
            total = db.execute('SELECT count(*) FROM lookup JOIN pages p ON p.id=lookup.rowid WHERE ' + where, params).fetchone()[0]
            quality = 'all_keywords'
            if not total:
                params[0] = literal_query(request.query, require_all=False)
                total = db.execute('SELECT count(*) FROM lookup JOIN pages p ON p.id=lookup.rowid WHERE ' + where, params).fetchone()[0]
                quality = 'partial_keywords'
            primary = [sid for sid in ids if self.store.catalog[sid].origin == 'official'
                       and self.store.catalog[sid].document_role in {'standard', 'specification'}]
            priority_sql = ('CASE WHEN p.source_id IN (' + ','.join('?' for _ in primary) + ') THEN 0 ELSE 1 END,') if primary else ''
            heading_terms = list(dict.fromkeys(t.lower().rstrip('s') for t in re.findall(r'[A-Za-z]+', request.query)
                                              if t.lower() not in STOP and len(t) > 3))[:8]
            if heading_terms:
                priority_sql += 'CASE WHEN ' + ' AND '.join("instr(lower(json_extract(p.metadata,'$.section_headings')),?)>0" for _ in heading_terms) + ' THEN 0 ELSE 1 END,'
            rows = db.execute('SELECT p.* FROM lookup JOIN pages p ON p.id=lookup.rowid WHERE ' + where +
                              ' ORDER BY ' + priority_sql + 'bm25(lookup,1.0,4.0),p.source_id,p.page LIMIT ? OFFSET ?',
                              [*params, *primary, *heading_terms, 500 if request.diagrams_only else request.limit,
                               0 if request.diagrams_only else request.offset]).fetchall()
            if request.diagrams_only:
                candidates = {}
                for matched in rows:
                    if json.loads(matched['metadata']).get('is_contents'):
                        continue
                    neighbors = db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page BETWEEN ? AND ? ORDER BY page',
                                           (matched['source_id'], matched['revision'], max(1, matched['page']-1), matched['page']+1)).fetchall()
                    for neighbor in neighbors:
                        labels = neighbor['captions'].splitlines()
                        needs_visual_review = json.loads(neighbor['metadata']).get('image_review_required', False)
                        if not needs_visual_review and not any(re.match(r'^(Figure\s|Typical Application\s|Standard drawing\s)', caption, re.I) for caption in labels):
                            continue
                        key = neighbor['id']
                        if key not in candidates:
                            candidates[key] = {**self.record(neighbor, request.as_of), 'keyword_match_pages': []}
                        candidates[key]['keyword_match_pages'].append(matched['page'])
                total_keyword_pages = total
                total = len(candidates)
                requested_codes = set(re.findall(r'\b(?:PM|IM|ED|MM|USP|ISD|SPD|PRS)-\d+[A-Z]?\b', request.query.upper()))
                def priority(page):
                    caption_codes = set(re.findall(r'Standard drawing ([A-Z]+-\d+[A-Z]?)', '\n'.join(page['captions'])))
                    return (bool(requested_codes) and not requested_codes.intersection(caption_codes),
                            page['page'] not in page['keyword_match_pages'])
                ordered = sorted(candidates.values(), key=priority)
                results = ordered[request.offset:request.offset+request.limit]
            else:
                results = [self.record(row, request.as_of) for row in rows]
        return {'status': 'candidates_found' if results else 'no_matches', 'total': total,
                'offset': request.offset, 'limit': request.limit, 'results': results,
                'match_basis': 'keyword_discovery_only', 'match_quality': quality,
                'diagram_match_basis': 'same_or_adjacent_page_keywords' if request.diagrams_only else None,
                'candidate_window_truncated': request.diagrams_only and total_keyword_pages > 500,
                'requirements_determined': False}

    def context(self, request: ManualQuery, budget=MAX_CONTEXT_BYTES):
        if not 1000 <= budget <= MAX_CONTEXT_BYTES:
            raise ValueError('Invalid context budget')
        found = self.search(request.model_copy(update={'limit': 6, 'offset': 0}))
        packet = {'schema_version': 1, 'status': 'no_evidence', 'question': request.query,
                  'authority': request.authority, 'region': request.region, 'as_of': str(request.as_of),
                  'evidence': [], 'formulas': [], 'warnings': [], 'requirements_determined': False,
                  'approved_for_field_use': False}
        seen, incomplete = set(), False
        with closing(self.connect()) as db:
            for hit in found['results']:
                if hit['document_role'] not in {'standard', 'specification'}:
                    continue  # Informal guides remain searchable, not governing answers.
                # Expand the hit to its section, retaining whole pages, tables and
                # continuing notes. Never truncate a long section to a few snippets.
                bounds = db.execute('SELECT min(page),max(page) FROM pages WHERE source_id=? AND revision=? AND section IS ?',
                                    (hit['source_id'], hit['revision'], hit['section'])).fetchone()
                first, last = (bounds[0], bounds[1] + 1) if hit['section'] else (max(1, hit['page'] - 1), hit['page'] + 1)
                pages = db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page BETWEEN ? AND ? ORDER BY page',
                                   (hit['source_id'], hit['revision'], first, last)).fetchall()
                # Blank separator/contents pages provide no governing rule text.
                pages = [p for p in pages if (p['text'].strip() or p['captions'].strip()) and not json.loads(p['metadata']).get('is_contents')]
                group = [self.record(p, request.as_of) for p in pages]
                # One explicit reference hop brings cited sections and tables
                # into the prompt instead of asking Gemma to recall their values.
                text = '\n'.join(page['text'] for page in group)
                section_refs = set(re.findall(r'\bSection\s+(\d+[A-Z]\.\d{2}[A-Z]?)\b', text, re.I))
                figure_refs = set(re.findall(r'\b(Figure|Table)\s+(\d+[A-Z](?:[.\-][A-Z0-9]+)+)', text, re.I))
                related = {}
                for code in sorted(section_refs):
                    starts = db.execute("SELECT DISTINCT p.* FROM pages p,json_each(p.metadata,'$.section_headings') h WHERE p.source_id=? AND p.revision=? AND h.value LIKE ?",
                                        (hit['source_id'], hit['revision'], 'Section ' + code + ' %')).fetchall()
                    for start in starts:
                        bounds = db.execute('SELECT min(page),max(page) FROM pages WHERE source_id=? AND revision=? AND section IS ?',
                                            (hit['source_id'], hit['revision'], start['section'])).fetchone()
                        if bounds[0] is not None:
                            for related_page in db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page BETWEEN ? AND ?',
                                    (hit['source_id'], hit['revision'], bounds[0], bounds[1] + 1)):
                                related[related_page['id']] = related_page
                for kind, code in sorted(figure_refs):
                    for related_page in db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND captions LIKE ?',
                            (hit['source_id'], hit['revision'], '%' + kind + ' ' + code + '%')):
                        for neighbor in db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page BETWEEN ? AND ?',
                                (hit['source_id'], hit['revision'], max(1, related_page['page'] - 1), related_page['page'] + 1)):
                            related[neighbor['id']] = neighbor
                existing = {page['citation_id'] for page in group}
                for page in related.values():
                    metadata = json.loads(page['metadata'])
                    record = self.record(page, request.as_of)
                    if record['citation_id'] not in existing and not metadata.get('is_contents') and (page['text'].strip() or page['captions'].strip()):
                        group.append(record)
                        existing.add(record['citation_id'])
                # Include the complete pinned errata, even when the question's
                # keywords never occur in the correction. Preserve both sources.
                missing_companion = False
                for sid, revision in self.store.catalog[hit['source_id']].required_companions.items():
                    companion = self.store.catalog.get(sid)
                    current = self.store.revisions(sid) if companion else []
                    if (not companion or companion.agency != request.authority or request.region not in companion.regions
                            or not current or current[0]['revision'] != revision):
                        missing_companion = True
                        continue
                    corrections = db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? ORDER BY page', (sid, revision)).fetchall()
                    if not corrections:
                        missing_companion = True
                    group.extend(self.record(p, request.as_of) for p in corrections)
                if missing_companion:
                    incomplete = True
                    packet['warnings'].append('A required correction revision is missing; Atlas cannot answer from the base manual alone.')
                    continue
                group = [p for p in group if p['citation_id'] not in seen]
                trial = {**packet, 'evidence': packet['evidence'] + group}
                if len(packed(trial).encode()) > budget - 500:
                    incomplete = True
                    packet['warnings'].append('A complete section and its corrections exceed the context budget; narrow the operation or section.')
                    continue
                packet['evidence'].extend(group)
                seen.update(p['citation_id'] for p in group)
        if packet['evidence']:
            packet['status'] = 'ready_for_reviewed_answer' if all(p['answer_eligible'] for p in packet['evidence']) else 'source_review_required'
            if found.get('match_quality') == 'partial_keywords':
                packet['status'] = 'needs_clarification'
                packet['warnings'].append('Only partial keyword matches were found; refine the operation or open the source pages.')
            if any(p['image_review_required'] for p in packet['evidence']):
                packet['status'] = 'image_review_required'
                packet['warnings'].append('Some source pages contain images or little body text. Captions/tags do not replace visual review of the original diagram and notes.')
        if incomplete:
            packet['status'] = 'needs_clarification'
        elif not packet['evidence'] and found['results']:
            packet['status'] = 'source_review_required'
            packet['warnings'].append('Matches are companion or training material; governing standard evidence is required.')
        if request.authority == 'VDOT' and not any(p['source_id'] == 'vdot-vwapm-2026' for p in packet['evidence']):
            packet['warnings'].append('Temporary traffic control is in the separate VWAPM; this copy alone is not Part 6 coverage.')
        evidence = {p['citation_id']: p for p in packet['evidence'] if p['answer_eligible']}
        for item in self.basis():
            for rule in item['formulas']:
                page = evidence.get(rule['citation_id'])
                if (page and page['source_id'] == item['source']['id'] and page['revision'] == item['manifest']['revision']
                        and ' '.join(rule['supporting_quote'].split()) in ' '.join(page['text'].split())):
                    public_rule = {key: value for key, value in rule.items() if key not in {'reviewer', 'review_note'}}
                    trial = {**packet, 'formulas': packet['formulas'] + [public_rule]}
                    if len(packed(trial).encode()) <= budget:
                        packet['formulas'].append(public_rule)
        if len(packed(packet).encode()) > budget:
            raise ValueError('Context budget exceeded')
        return packet

    def outline(self, source_id):
        if source_id not in self.store.catalog:
            raise KeyError(source_id)
        with closing(self.connect()) as db:
            rows = db.execute('SELECT page,metadata FROM pages WHERE source_id=? ORDER BY page', (source_id,)).fetchall()
        sections, seen = [], set()
        for row in rows:
            metadata = json.loads(row['metadata'])
            if metadata.get('is_contents'):
                continue
            for heading in metadata.get('section_headings', []):
                if heading not in seen:
                    sections.append({'section': heading, 'page': row['page']})
                    seen.add(heading)
        return sections

    def render_page(self, source_id, revision, page_number, destination):
        """Operator-only full page render, retaining original notes and geometry."""
        import pypdfium2 as pdfium
        if source_id not in self.store.catalog or not re.fullmatch('[a-f0-9]{64}', revision):
            raise ValueError('Unknown source or revision')
        original = self.store.data / 'revisions' / source_id / revision / 'original.pdf'
        if hashlib.sha256(original.read_bytes()).hexdigest() != revision:
            raise ValueError('Original PDF integrity failure')
        destination = Path(destination)
        if destination.exists():
            raise FileExistsError(destination)
        with pdfium.PdfDocument(original) as document:
            if type(page_number) is not int or not 1 <= page_number <= len(document):
                raise ValueError('Invalid physical page')
            page = document[page_number - 1]
            try:
                bitmap = page.render(scale=1.5)
                try:
                    bitmap.to_pil().save(destination, format='PNG')
                finally:
                    bitmap.close()
            finally:
                page.close()
        return destination

    def add_formula(self, value):
        """Explicit operator review; never infer a formula from a caption or OCR."""
        from datetime import date
        from services.workspace_preview.dot_calculations import arithmetic
        rule = FormulaRule.model_validate(value)
        parts = rule.citation_id.split(':')
        if len(parts) != 3 or not re.fullmatch(r'[a-f0-9]{64}', parts[1]) or not parts[2].isdigit():
            raise ValueError('Use an exact physical-page citation')
        sid, revision, page = parts[0], parts[1], int(parts[2])
        if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', name) or not 1 <= len(unit) <= 30 for name, unit in rule.inputs.items()):
            raise ValueError('Invalid formula inputs')
        with closing(self.connect()) as db:
            row = db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page=?', (sid, revision, page)).fetchone()
        if row is None:
            raise ValueError('Unknown formula evidence')
        record = self.record(row, date.today())
        if not record['answer_eligible'] or ' '.join(rule.supporting_quote.split()) not in ' '.join(record['text'].split()):
            raise ValueError('Formula requires visually reviewed source evidence and its exact quote')
        arithmetic(rule.expression, {name: 2 for name in rule.inputs})
        path = self.store.data / 'revisions' / sid / revision / 'formula-rules.json'
        entries = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        if any(entry['formula_id'] == rule.formula_id for entry in entries):
            raise ValueError('Formula already exists; preserve its review history')
        entries.append(rule.model_dump())
        write_json(path, entries)
        return rule.model_dump()

    def annotate_page(self, source_id, revision, page_number, caption, keywords, note):
        """Record operator-supplied search tags, never engineering approval or OCR."""
        import pypdfium2 as pdfium
        if source_id not in self.store.catalog or not re.fullmatch('[a-f0-9]{64}', revision):
            raise ValueError('Unknown source or revision')
        folder = self.store.data / 'revisions' / source_id / revision
        original = folder / 'original.pdf'
        if (hashlib.sha256(original.read_bytes()).hexdigest() != revision or
                type(page_number) is not int or not 1 <= page_number <= 2000 or
                not 5 <= len(caption) <= 240 or not 1 <= len(keywords) <= 300 or not 20 <= len(note) <= 1000):
            raise ValueError('Invalid page annotation or original integrity failure')
        with pdfium.PdfDocument(original) as document:
            if page_number > len(document):
                raise ValueError('Page outside source document')
        path = folder / 'page-annotations.json'
        annotations = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if str(page_number) in annotations:
            raise ValueError('Page annotation already exists; preserve its review history')
        annotations[str(page_number)] = {'caption': caption, 'keywords': keywords, 'note': note,
                                        'method': 'operator_search_tag', 'qualified_review_required': True}
        write_json(path, annotations)
        return annotations[str(page_number)]
