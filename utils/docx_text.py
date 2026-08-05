"""Minimal .docx text extraction (stdlib only — no python-docx dependency).

Handy for verifying Word report exports without parsing rendered PDF output.
"""

import re
import zipfile
from typing import List

_TEXT_RUN = re.compile(r"<w:t[^>]*>([^<]*)</w:t>")
_PAGE_BREAK = re.compile(r'w:type="page"')


def extract_text(docx_path) -> str:
    """Concatenate all visible text runs in word/document.xml, in document order."""
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    return "".join(_TEXT_RUN.findall(xml))


def count_page_breaks(docx_path) -> int:
    """Number of explicit page-break runs (<w:br w:type="page"/>) in the document."""
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    return len(_PAGE_BREAK.findall(xml))


def split_blocks(text: str, marker: str) -> List[str]:
    """Split extracted report text into one chunk per *marker* occurrence,
    dropping any leading preamble before the first marker."""
    blocks = re.split(rf"(?={re.escape(marker)})", text)
    return [b for b in blocks if marker in b]
