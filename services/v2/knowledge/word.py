"""Bounded, text-only OOXML reader. Never executes Word, macros or relationships."""
import hashlib
import io
from pathlib import PurePosixPath
import zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def checked_zip(data, max_total=32 * 1024 * 1024):
    archive = zipfile.ZipFile(io.BytesIO(data))
    members = archive.infolist()
    if len(members) > 2000 or sum(m.file_size for m in members) > max_total:
        archive.close()
        raise ValueError('archive_expansion_limit')
    names = set()
    for m in members:
        path = PurePosixPath(m.filename)
        if (m.filename in names or path.is_absolute() or '..' in path.parts
                or '\\' in m.filename or ':' in m.filename or m.flag_bits & 1):
            archive.close()
            raise ValueError('unsafe_archive_member')
        names.add(m.filename)
    return archive


def member_bytes(data, source):
    if hashlib.sha256(data).hexdigest() != source.archive_sha256:
        raise ValueError('archive_hash_mismatch')
    with checked_zip(data, 256 * 1024 * 1024) as archive:
        member = archive.getinfo(source.archive_member)
        if member.file_size > 8 * 1024 * 1024:
            raise ValueError('member_size_limit')
        return archive.read(member)


def word_blocks(data):
    with checked_zip(data) as archive:
        if any('vbaproject' in n.lower() for n in archive.namelist()):
            raise ValueError('macro_content_rejected')
        xml = archive.read('word/document.xml').decode('utf-8-sig')
    if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
        raise ValueError('xml_declarations_rejected')
    root = ET.fromstring(xml)
    body = root.find(W + 'body')
    if body is None:
        raise ValueError('missing_word_body')
    warnings = ['docx_layout_not_verified', 'docx_headers_footers_images_not_indexed']
    if root.find('.//' + W + 'del') is not None or root.find('.//' + W + 'ins') is not None:
        raise ValueError('tracked_changes_require_review')
    blocks = []
    for number, element in enumerate(body, 1):
        if element.tag == W + 'p':
            text = ''.join(n.text or '' for n in element.iter(W + 't'))
            if text.strip():
                blocks.append((f'Paragraph {number}', text))
        elif element.tag == W + 'tbl':
            warnings.append('table_structure_requires_visual_review')
            for row_number, row in enumerate(element.findall(W + 'tr'), 1):
                cells = [' '.join(''.join(n.text or '' for n in p.iter(W + 't'))
                                  for p in cell.findall(W + 'p')) for cell in row.findall(W + 'tc')]
                if any(cells):
                    blocks.append((f'Table {number}, row {row_number}', ' | '.join(cells)))
    return blocks, sorted(set(warnings))
