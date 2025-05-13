from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Document:
    text: str

@dataclass
class ClassificationResult:
    category: str
    scores: Dict[str, int]
