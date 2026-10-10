"""Render an immutable saved draft. No network requests, model calls or approval."""
from io import BytesIO
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate

FONT_LOCK = Lock()


def render_pdf(saved):
    """Only saved content determines PDF bytes; current-job status stays in the UI."""
    with FONT_LOCK:
        if 'WzosBody' not in pdfmetrics.getRegisteredFontNames():
            fonts = Path(reportlab.__file__).parent / 'fonts'
            pdfmetrics.registerFont(TTFont('WzosBody', str(fonts / 'Vera.ttf')))
            pdfmetrics.registerFont(TTFont('WzosBold', str(fonts / 'VeraBd.ttf')))
    ink, gold = colors.HexColor('#17191c'), colors.HexColor('#967020')
    body = ParagraphStyle('Body', fontName='WzosBody', fontSize=9, leading=14,
                          textColor=ink, spaceAfter=7, splitLongWords=True)
    title = ParagraphStyle('Title', parent=body, fontName='WzosBold', fontSize=23,
                           leading=29, spaceAfter=14)
    heading = ParagraphStyle('Heading', parent=body, fontName='WzosBold',
                             fontSize=13, leading=18, textColor=gold, spaceBefore=14,
                             spaceAfter=8, keepWithNext=True)
    small = ParagraphStyle('Small', parent=body, fontSize=8, leading=12)
    story = []

    def text(value, style=body):
        value = str(value) if value is not None else 'Not recorded'
        # Treat all customer/source content as text, never ReportLab markup.
        story.append(Paragraph(escape(value).replace('\n', '<br/>'), style))

    def section(name):
        text(name, heading)

    def fields(value, prefix=''):
        if isinstance(value, dict):
            for key, item in value.items():
                fields(item, (prefix + ' / ' if prefix else '') + key.replace('_', ' '))
        elif isinstance(value, list):
            if not value:
                text(prefix + ': None recorded')
            for i, item in enumerate(value, 1):
                fields(item, f'{prefix} {i}')
        else:
            text(f'{prefix}: {value if value is not None else "Not recorded"}')

    report, order = saved['report'], saved['report']['order']
    text('WZOS powered by Atlas AI Assistant', small)
    text('Work Zone Report', title)
    text('DRAFT — NOT APPROVED FOR FIELD USE', heading)
    text(order['title'])
    text('Molecular Project Development LLC', small)
    text(f"Snapshot: {saved['id']} | Job revision: {saved['order_version']}", small)
    text(f"Saved: {saved['saved_at']}", small)
    text('Snapshot SHA-256: ' + saved['sha256'], small)
    text('This PDF preserves the saved draft and reference candidates. Later job, '
         'source or form changes require a new snapshot. It is not an approved '
         'traffic-control plan or proof of compliance.')
    section('Work order')
    for key in ('work_type', 'address', 'locality', 'work_date', 'road_authority', 'notes'):
        text(f"{key.replace('_', ' ').title()}: {order.get(key) or 'Not recorded'}")
    section('Reported site and measured geometry')
    text('Customer-reported information — verification required.')
    fields(order.get('site') or {}, 'Site')
    if order.get('job_geometry'):
        fields(order['job_geometry'], 'Geometry')
    else:
        text('Work limits and measured approaches are not recorded.')
    section('Readiness checklist')
    checklist = report.get('checklist')
    if checklist:
        text(f"Checklist revision {checklist['version']}; job basis revision "
             f"{checklist['order_version']}; stale at save: {checklist['stale']}.")
        fields(checklist['items'])
    else:
        text('No saved checklist.')
    section('Linked form drafts')
    forms = report.get('forms', [])
    text(f"{len(forms)} of {report.get('forms_total', len(forms))} linked records "
         'included. Drafts do not establish required-form completion.')
    for form in forms:
        text(f"{form['title']} | revision {form['version']} | {form.get('status', 'draft')}", heading)
        for key in ('details', 'safety', 'inspection'):
            if form.get(key):
                fields(form[key], key)
    packet = report.get('preparation') or {}
    section('Reference preparation and missing information')
    text(packet.get('note', 'No saved reference preparation.'))
    for question in packet.get('questions', []):
        text(question['question'])
    for item in packet.get('form_recommendations', []):
        text(f"{item['title']} | {item['priority']}: {item['reason']}")
    refs = packet.get('references') or {}
    for topic in refs.get('topics', []):
        section(topic['id'].replace('_', ' ').title())
        if not topic.get('candidates'):
            text('No reference candidates saved for this topic.')
        for ref in topic.get('candidates', []):
            text(ref['title'], heading)
            text(f"{ref['agency']} | edition: {ref.get('edition') or 'unverified'} | "
                 f"page: {ref.get('page') if ref.get('page') is not None else 'not recorded'} | "
                 f"section: {ref.get('section') or 'not recorded'}", small)
            text(f"Review: {ref.get('review_status', 'unreviewed')} | "
                 f"Publication: {ref.get('publication_status', 'unknown')} | "
                 f"Latest revision: {ref.get('is_latest', 'unknown')}", small)
            text('Document revision: ' + ref['revision'], small)
            text(ref['text'])
            url = ref.get('url', '')
            parts = urlsplit(url)
            if parts.scheme == 'https' and parts.netloc:
                text('Official source: ' + url, small)
                story.append(Paragraph('<link href="' + escape(url, {'"': '&quot;'}) +
                                       '">Open official source</link>', small))
            elif url:
                text('Source link unavailable: unsupported URL scheme.', small)
    for gap in refs.get('coverage_gaps', []):
        text('Coverage gap: ' + gap)
    section('Scope and remaining review')
    for value in report.get('limitations', []):
        text(value)
    text('Site imagery is not embedded in this PDF. No sign or flagger placement, '
         'diagram, external delivery or qualified approval is supplied by this export.')
    if len(story) > 5000:
        raise ValueError('Report exceeds the PDF layout limit')
    output = BytesIO()

    def page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(gold)
        canvas.line(42, 40, letter[0] - 42, 40)
        canvas.setFont('WzosBody', 7)
        canvas.drawString(42, 28, 'WZOS | Draft — review required')
        canvas.drawRightString(letter[0] - 42, 28, f'Page {doc.page}')
        canvas.restoreState()

    SimpleDocTemplate(output, pagesize=letter, leftMargin=42, rightMargin=42,
                      topMargin=38, bottomMargin=54, invariant=True,
                      title='WZOS Work Zone Report — Draft',
                      author='Molecular Project Development LLC').build(
                          story, onFirstPage=page, onLaterPages=page)
    return output.getvalue()
