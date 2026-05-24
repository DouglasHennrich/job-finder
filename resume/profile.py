from dataclasses import dataclass


@dataclass
class Profile:
    raw_text: str  # full text from all PDF pages joined with "\n\n"
    pdf_path: str  # absolute path to the source PDF
