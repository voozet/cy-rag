from dataclasses import dataclass

@dataclass
class Evidence:
    id: str
    title: str
    source: str
    url: str
    section: str | None
    text: str
    score: float
