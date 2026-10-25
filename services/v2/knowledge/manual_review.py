"""Operator-only OCR/review sidecars. Originals stay immutable; OCR is unreviewed."""
import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .store import Store, write_json
from .page_text import representation


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def original(store, source_id, revision):
    if source_id not in store.catalog or not re.fullmatch('[a-f0-9]{64}', revision):
        raise ValueError('Unknown source or revision')
    path = store.data / 'revisions' / source_id / revision / 'original.pdf'
    if hashlib.sha256(path.read_bytes()).hexdigest() != revision:
        raise ValueError('Original integrity failure')
    return path


def ocr(store, source_id, revision, pages):
    import pypdfium2 as pdfium
    path = original(store, source_id, revision)
    engine = shutil.which('tesseract')
    if not engine:
        raise ValueError('Install the distribution tesseract-ocr package in Cloud Shell first')
    pages = sorted(set(pages))
    if not pages or len(pages) > 25 or any(type(p) is not int or p < 1 for p in pages):
        raise ValueError('Use a bounded batch of 1 to 25 physical pages')
    sidecar = path.with_name('ocr-pages.json')
    entries = json.loads(sidecar.read_text(encoding='utf-8')) if sidecar.exists() else {}
    version = subprocess.run([engine, '--version'], check=True, capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    with pdfium.PdfDocument(path) as document, tempfile.TemporaryDirectory(prefix='atlas-ocr-') as temporary:
        if pages[-1] > len(document):
            raise ValueError('Page outside document')
        for number in pages:
            if str(number) in entries:
                raise ValueError('OCR already exists; preserve its history instead of overwriting')
            page = document[number - 1]
            try:
                width, height = page.get_size()
                # 300 dpi for small table symbols; cap oversized drawing sheets.
                scale = min(300 / 72, (12000000 / (width * height)) ** 0.5)
                bitmap = page.render(scale=scale)
                try:
                    image = Path(temporary) / 'page.png'
                    bitmap.to_pil().save(image)
                finally:
                    bitmap.close()
            finally:
                page.close()
            text = subprocess.run([engine, str(image), 'stdout', '-l', 'eng'], check=True,
                                  capture_output=True, text=True, timeout=180).stdout.strip()
            if len(text.encode()) > 100000:
                raise ValueError('Oversized OCR page')
            entries[str(number)] = {'text': text, 'text_sha256': digest(text), 'engine': version,
                                    'original_sha256': revision, 'reviewed': False}
            write_json(sidecar, entries)
    return {'source_id': source_id, 'revision': revision, 'pages': pages, 'reviewed': False}


def page_raw(store, source_id, revision, page):
    import pypdfium2 as pdfium
    path = original(store, source_id, revision)
    with pdfium.PdfDocument(path) as document:
        if type(page) is not int or not 1 <= page <= len(document):
            raise ValueError('Select a physical page in this original')
        pdf_page = document[page - 1]
        try:
            text_page = pdf_page.get_textpage()
            try:
                text = re.sub(r'\r\n?', '\n', text_page.get_text_bounded()).strip()
            finally:
                text_page.close()
        finally:
            pdf_page.close()
    return path, text


def transcribe(store, source_id, revision, page, text, note):
    """Stage a full-page replacement; a separate visual review is still required."""
    path, raw = page_raw(store, source_id, revision, page)
    target = path.with_name('page-transcriptions.json')
    entries = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    if str(page) in entries:
        raise ValueError('Transcription already exists; preserve its history')
    entry = {'page': page, 'original_sha256': revision, 'source_text_sha256': digest(raw),
             'text': text, 'text_sha256': digest(text), 'note': note,
             'author': getpass.getuser(), 'created_at': datetime.now(timezone.utc).isoformat()}
    representation(raw, revision, page, transcription=entry)
    entries[str(page)] = entry
    write_json(target, entries)
    return entry


def review(store, source_id, revision, page, note):
    """Called only after visually comparing this exact page's text and original."""
    if len(note.strip()) < 30:
        raise ValueError('Describe the visual comparison, tables and limitations')
    path, text = page_raw(store, source_id, revision, page)
    ocr_path = path.with_name('ocr-pages.json')
    ocr_pages = json.loads(ocr_path.read_text(encoding='utf-8')) if ocr_path.exists() else {}
    replacements_path = path.with_name('page-transcriptions.json')
    replacements = json.loads(replacements_path.read_text(encoding='utf-8')) if replacements_path.exists() else {}
    text, binding = representation(text, revision, page, ocr_pages.get(str(page)), replacements.get(str(page)))
    target = path.with_name('page-reviews.json')
    entries = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    if str(page) in entries:
        raise ValueError('Review already exists; preserve its history')
    entries[str(page)] = {'text_sha256': digest(text), 'reviewer': getpass.getuser(),
                         'reviewed_at': datetime.now(timezone.utc).isoformat(), 'note': note,
                         'original_sha256': revision, 'field_approval': False}
    if binding:
        entries[str(page)]['representation_sha256'] = binding
    write_json(target, entries)
    return entries[str(page)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('ocr', 'review', 'transcribe'):
        command = commands.add_parser(name)
        command.add_argument('source')
        command.add_argument('revision')
        if name == 'ocr': command.add_argument('pages', type=int, nargs='+')
        else:
            command.add_argument('page', type=int)
            command.add_argument('--note', required=True)
            if name == 'transcribe': command.add_argument('--text-file', type=Path, required=True)
    args = parser.parse_args()
    store = Store(args.data) if args.data else Store()
    if args.command == 'transcribe':
        if args.text_file.stat().st_size > 100000:
            raise ValueError('Oversized replacement text')
        result = transcribe(store, args.source, args.revision, args.page,
                            args.text_file.read_text(encoding='utf-8'), args.note)
    else:
        result = ocr(store, args.source, args.revision, args.pages) if args.command == 'ocr' else review(store, args.source, args.revision, args.page, args.note)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
