from io import BytesIO
from pypdf import PdfReader

def extract_pdf_pages(pdf_bytes: bytes, filename: str) -> list[dict]:
    """Extract selectable text page-by-page and retain source metadata."""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({
                "text": text,
                "page": page_number,
                "source": filename,
            })
    return pages

def split_into_chunks(pages: list[dict], chunk_size: int = 1100, overlap: int = 180) -> list[dict]:
    """Create bounded overlapping passages without losing their source page."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    chunks = []
    for page in pages:
        text = " ".join(page["text"].split())
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            passage = text[start:end].strip()
            if passage:
                chunks.append({
                    "text": passage,
                    "page": page["page"],
                    "source": page["source"],
                })
            if end == len(text):
                break
            start = end - overlap
    return chunks
