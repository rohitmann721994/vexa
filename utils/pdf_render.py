"""Render a PDF page to a PNG image.

Some report/preview screens never render on-screen — clicking "View" triggers a
browser download (PDF or Word) with no HTML preview panel for Playwright to
screenshot. This renders the downloaded PDF's page(s) to PNG so the actual
content can still be captured as evidence via ``Evidence.image_step(...)``.
"""

import fitz  # PyMuPDF


def render_pages(pdf_path, zoom: float = 2.0) -> list:
    """Return a list of PNG-encoded bytes, one per page in *pdf_path*."""
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            images.append(pix.tobytes("png"))
    return images
