"""Page-aware DOT retrieval over the existing immutable source library.

The SQLite file is a disposable search index, never customer persistence. Text
matching discovers reference candidates; it does not establish applicability.
"""
from contextlib import closing
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from pydantic import Field

from shared.contracts import StrictModel
from .store import IndexUnavailable, Store, write_json


VERSION = 4
MAX_CONTEXT_BYTES = 20000
STOP = set('a an the and or to for in on of is are what which how do does under required '
           'requirement requirements rule rules please tell me about at with from according'.split())
ALIASES = {'flagging': ['flagger', 'flaggers'], 'four': ['4'], 'two': ['2'],
           'striping': ['markings'], 'centerline': ['center line']}
CAPTION = re.compile(r'^\s*(Figure|Table|Typical Application)\s+([A-Z0-9][A-Z0-9.()–-]*)(?:[.\s]+)(.{2,180})$', re.I)
SECTION = re.compile(r'^\s*(Section\s+\d+[A-Z]?(?:\.\d+)?[^\n]{0,180}|PART\s+\d+[^\n]{0,180}|CHAPTER\s+\d+[A-Z]?[^\n]{0,180})$', re.I)


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
                and source.document_role in {'standard', 'specification'}
                and source.publication_status == 'current_at_verification'
                and manifest.get('extraction_checked')
                and source.effective_from and source.effective_from <= as_of
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
            rows.append({'source': source.model_dump(mode='json'), 'manifest': manifest, 'annotations': annotations})
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
                            heading = next((line.strip() for line in lines if SECTION.match(line) and not re.search(r'\.{3,}', line)), None)
                            section = heading or section
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
                            metadata = {'source': source, 'extraction_checked': manifest.get('extraction_checked', False),
                                        'review_status': manifest.get('review_status', 'unreviewed'),
                                        'image_review_required': not body_available, 'page_annotation': annotation,
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
                   applicability_note=source.applicability_note, answer_eligible=eligible(source, manifest, as_of),
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
            rows = db.execute('SELECT p.* FROM lookup JOIN pages p ON p.id=lookup.rowid WHERE ' + where +
                              ' ORDER BY bm25(lookup,1.0,4.0),p.source_id,p.page LIMIT ? OFFSET ?',
                              [*params, 500 if request.diagrams_only else request.limit,
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
                  'evidence': [], 'warnings': [], 'requirements_determined': False,
                  'approved_for_field_use': False}
        seen = set()
        with closing(self.connect()) as db:
            for hit in found['results']:
                # Preserve complete pages including surrounding notes; never clip tables.
                pages = db.execute('SELECT * FROM pages WHERE source_id=? AND revision=? AND page BETWEEN ? AND ? ORDER BY page',
                                   (hit['source_id'], hit['revision'], max(1, hit['page'] - 1), hit['page'] + 1)).fetchall()
                group = [self.record(p, request.as_of) for p in pages]
                group = [p for p in group if p['citation_id'] not in seen]
                trial = {**packet, 'evidence': packet['evidence'] + group}
                if len(packed(trial).encode()) > budget - 500:
                    packet['warnings'] = ['Some complete page groups exceed the context budget; open the source pages.']
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
        if request.authority == 'VDOT':
            packet['warnings'].append('Temporary traffic control is in the separate VWAPM; this copy alone is not Part 6 coverage.')
        if len(packed(packet).encode()) > budget:
            raise ValueError('Context budget exceeded')
        return packet

    def outline(self, source_id):
        if source_id not in self.store.catalog:
            raise KeyError(source_id)
        with closing(self.connect()) as db:
            rows = db.execute('SELECT section,min(page) AS page FROM pages WHERE source_id=? AND section IS NOT NULL GROUP BY section ORDER BY min(page)', (source_id,)).fetchall()
        return [dict(row) for row in rows]

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
