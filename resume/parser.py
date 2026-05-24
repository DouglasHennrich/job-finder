import os

import pdfplumber

from resume.profile import Profile


def parse_pdf(pdf_path: str) -> Profile:
    # TODO (T011):
    # 1. Check os.path.exists(pdf_path); if not, raise FileNotFoundError with
    #    "[ERROR] PDF not found: {pdf_path} — check the file exists and the path is correct"
    # 2. Open PDF with pdfplumber.open(pdf_path) as context manager
    # 3. For each page: append page.extract_text() or "" to a list
    # 4. Join all page texts with "\n\n" and strip()
    # 5. If raw_text is empty, raise ValueError with
    #    "[ERROR] PDF produced no extractable text. The file may be image-only (scanned). Use a text-layer PDF."
    # 6. Return Profile(raw_text=raw_text, pdf_path=os.path.abspath(pdf_path))
    raise NotImplementedError
