"""Select a provenance-bound page representation; selection is not review."""
import hashlib
import json


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def representation(raw, revision, page, ocr=None, transcription=None):
    if transcription is not None:
        entry = transcription
        text = entry.get('text')
        if (entry.get('original_sha256') != revision or type(entry.get('page')) is not int
                or entry['page'] != page or entry.get('source_text_sha256') != digest(raw)
                or not isinstance(text, str) or not text.strip() or len(text.encode()) > 100000
                or entry.get('text_sha256') != digest(text)
                or not isinstance(entry.get('note'), str) or len(entry['note'].strip()) < 30):
            raise ValueError('Replacement transcription integrity failure')
        binding = digest(json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
        return text, binding
    if ocr:
        if (ocr.get('original_sha256') != revision or not isinstance(ocr.get('text'), str)
                or digest(ocr['text']) != ocr.get('text_sha256')):
            raise ValueError('OCR sidecar integrity failure')
        raw += '\n\n[OCR transcription - visual review required]\n' + ocr['text']
    return raw, None
