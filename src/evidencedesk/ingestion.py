import io
import re
from dataclasses import dataclass
from pathlib import PurePath

from pypdf import PdfReader


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    title: str
    page: int
    text: str


def parse_file(filename: str, payload: bytes, max_chars: int) -> tuple[str, list[str]]:
    title = PurePath(filename.replace("\\", "/")).name[:160] or "document.txt"
    suffix = PurePath(title).suffix.lower()
    if suffix == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(payload))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported")
            if len(reader.pages) > 100:
                raise ValueError("PDFs are limited to 100 pages")
            pages = []
            size = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                size += len(text)
                if size > max_chars:
                    raise ValueError("Document exceeds the extracted text limit")
                pages.append(text)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not read this PDF") from exc
    elif suffix in {".txt", ".md"}:
        try:
            pages = [payload.decode("utf-8-sig")]
        except UnicodeDecodeError as exc:
            raise ValueError("Text files must use UTF-8") from exc
    else:
        raise ValueError("Use a PDF, Markdown, or UTF-8 text file")
    pages = [re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", p) for p in pages]
    if not any(p.strip() for p in pages):
        raise ValueError("No text found; scanned PDFs need OCR before upload")
    if sum(len(p) for p in pages) > max_chars:
        raise ValueError("Document exceeds the extracted text limit")
    return title, pages


def chunk_documents(documents, size=650, overlap=100):
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed non-negative overlap")
    chunks = []
    for doc in documents:
        for page, text in enumerate(doc["pages"], 1):
            if doc["title"].lower().endswith(".md"):
                text = re.sub(r"(?m)^#{1,6}\s+.*$", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            start = 0
            index = 0
            while start < len(text):
                end = min(start + size, len(text))
                if end < len(text):
                    boundary = text.rfind(" ", start + size // 2, end)
                    if boundary > start:
                        end = boundary
                part = text[start:end].strip()
                if part:
                    chunks.append(Chunk(f"{doc['id']}:p{page}:c{index}", doc["id"], doc["title"], page, part))
                if end == len(text):
                    break
                start = max(start + 1, end - overlap)
                index += 1
    return chunks
