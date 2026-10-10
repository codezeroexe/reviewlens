"""Three-part report per pair. Uses only real fields. No claimed causes."""

from contradictions.aspects import CONTEXT

REASON_UNKNOWN = "Conflicting experiences found; the reason cannot be determined from the available reviews."


def _categories_missing(pos_ctx: set[str], neg_ctx: set[str]) -> list[str]:
    found = pos_ctx | neg_ctx
    missing = []
    for cat, words in CONTEXT.items():
        if not (found & set(words)):
            missing.append(cat)
    return missing


def build(row: dict) -> dict:
    pos_ctx = set(filter(None, str(row["pos_context"]).split("; ")))
    neg_ctx = set(filter(None, str(row["neg_context"]).split("; ")))
    context_differs = bool(pos_ctx and neg_ctx and pos_ctx != neg_ctx)
    if context_differs:
        interpretation = (f"The reviews mention different conditions ({', '.join(sorted(pos_ctx))} vs "
                          f"{', '.join(sorted(neg_ctx))}). This may explain the difference, but the reviews do not prove it.")
    else:
        interpretation = REASON_UNKNOWN
    missing = _categories_missing(pos_ctx, neg_ctx)
    return {
        "product_id": row["product_id"],
        "aspect": row["aspect"],
        "method": row["method"],
        "verdict": row["verdict"],
        "nli_label": row["nli_label"] if isinstance(row["nli_label"], str) else None,
        "nli_score": row["nli_score"] if row["nli_score"] == row["nli_score"] else None,
        "context_differs": context_differs,
        "review_similarity": row["review_similarity"],
        "observed_evidence": {
            "positive": {"review_id": row["pos_review_id"], "rating": row["pos_rating"], "quote": row["pos_sentence"]},
            "negative": {"review_id": row["neg_review_id"], "rating": row["neg_rating"], "quote": row["neg_sentence"]},
        },
        "possible_interpretation": interpretation,
        "unknown_or_missing_context": [
            f"No {cat} words in either sentence." for cat in missing
        ] + ["Reviewer's device version, settings, and how long they used it are not stated in these sentences."],
    }
