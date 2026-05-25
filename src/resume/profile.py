from dataclasses import dataclass, field


@dataclass
class Profile:
    raw_text: str  # full text from all PDF pages joined with "\n\n"
    pdf_path: str  # absolute path to the source PDF
    # Keywords extracted from the resume by the LLM (populated after extraction)
    role: str = ""          # e.g. "fullstack developer"
    seniority: str = ""     # e.g. "senior"
    skills: list[str] = field(default_factory=list)  # e.g. ["nodejs", "react", "nextjs"]
