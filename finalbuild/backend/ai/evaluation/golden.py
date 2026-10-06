from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    expected_categories: set[str]
    forbidden_claims: set[str]

    @classmethod
    def load(cls, path: str | Path) -> "GoldenCase":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(raw["case_id"], set(raw.get("expected_categories", [])), set(raw.get("forbidden_claims", [])))

@dataclass(frozen=True)
class GoldenResult:
    category_coverage: float
    forbidden_claims_present: list[str]
    passed: bool

class GoldenCaseEvaluator:
    def evaluate(self, categories: set[str], generated_text: str, case: GoldenCase) -> GoldenResult:
        coverage = len(categories & case.expected_categories) / max(1, len(case.expected_categories))
        lower = generated_text.lower()
        forbidden = [x for x in case.forbidden_claims if x.lower() in lower]
        return GoldenResult(coverage, forbidden, coverage >= 0.5 and not forbidden)
