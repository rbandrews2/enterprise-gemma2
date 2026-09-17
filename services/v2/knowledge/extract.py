"""Extraction preserves physical PDF pages; it does not validate layout or rules."""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import pypdfium2 as pdfium


def chunks(text: str, page=None, section=None, anchor=None):
    words = text.split()
    for start in range(0, len(words), 350):
        yield {"text": " ".join(words[start:start + 350]), "page": page,
               "section": section, "anchor": anchor}


def extract(data: bytes, kind: str):
    passages, warnings = [], []
    if kind == "pdf":
        engine = "pdfium"
        with pdfium.PdfDocument(data) as document:
            if len(document) > 2000:
                raise ValueError("too_many_pages")
            for number in range(len(document)):
                page = document[number]
                try:
                    textpage = page.get_textpage()
                    try:
                        text = textpage.get_text_bounded()
                    finally:
                        textpage.close()
                finally:
                    page.close()
                if len(re.sub(r"\W", "", text)) < 20:
                    warnings.append(f"page_{number + 1}_little_or_no_text")
                    continue
                passages.extend(chunks(text, page=number + 1))
    else:
        engine = "beautifulsoup"
        soup = BeautifulSoup(data, "html.parser")
        root = soup.find("main") or soup.find("article") or soup.body
        if root is None:
            raise ValueError("missing_html_body")
        for tag in root.select("script, style, nav, footer, header, noscript, svg, form"):
            tag.decompose()
        heading, anchor, buffer = "Document", None, []
        for element in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr"]):
            text = element.get_text(" ", strip=True)
            if element.name.startswith("h"):
                passages.extend(chunks(" ".join(buffer), section=heading, anchor=anchor))
                heading, anchor, buffer = text, element.get("id"), []
            elif not element.find_parent(["p", "li", "tr"]):
                buffer.append(text)
        passages.extend(chunks(" ".join(buffer), section=heading, anchor=anchor))
    if not passages:
        warnings.append("no_searchable_text_manual_review_required")
    return {"extractor_version": 1, "engine": engine, "passages": passages, "warnings": warnings}


if __name__ == "__main__":
    # Invoked in a separate, time-bounded process by ingestion.
    result = extract(Path(sys.argv[1]).read_bytes(), sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
