"""Insight object shape (from plans/phase6.md) and a validator. Every excerpt must be a real substring of its review."""

TYPES = {"common_problem", "experience_gap", "informative_evidence", "emerging", "comparison", "quality_warning"}


def make(id, type, headline, interpretation, numbers, excerpts, warning, evidence_ref, score=0.0):
    assert type in TYPES, type
    return {
        "id": id, "type": type, "headline": headline, "interpretation": interpretation,
        "numbers": [{"label": n["label"], "numerator": int(n["numerator"]), "denominator": int(n["denominator"]),
                     "pct": round(100 * n["numerator"] / n["denominator"], 1) if n["denominator"] else 0.0}
                    for n in numbers],
        "excerpts": excerpts, "warning": warning, "evidence_ref": evidence_ref, "score": round(float(score), 4),
    }


def check_excerpts(insight: dict, texts: dict) -> None:
    """Raise if any excerpt is not a substring of its review. Guards against invented quotes."""
    for ex in insight["excerpts"]:
        if ex["text"] not in texts[ex["review_id"]]:
            raise ValueError(f"excerpt not in review {ex['review_id']}")
