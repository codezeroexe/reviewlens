"""Score and select. score = relevance (share) + evidence (sample size, 2+ excerpts bonus) - warning penalty."""

MAX_OVERVIEW = 5
MAX_PER_TYPE = 2
OVERVIEW_EXCLUDE = {"quality_warning"}


def score(ins: dict) -> float:
    main = ins["numbers"][0]
    relevance = main["pct"] / 100
    evidence = min(main["denominator"], 100) / 100 + (0.2 if len(ins["excerpts"]) >= 2 else 0.0)
    penalty = 0.3 if ins["warning"] else 0.0
    return round(relevance + evidence - penalty, 4)


def rank(insights: list[dict]) -> list[dict]:
    for ins in insights:
        ins["score"] = score(ins)
    return sorted(insights, key=lambda i: -i["score"])


def overview(ranked: list[dict]) -> list[dict]:
    picked, per_type = [], {}
    for ins in ranked:
        if ins["type"] in OVERVIEW_EXCLUDE:
            continue  # quality warnings: drill-down only (heuristic, small samples)
        if per_type.get(ins["type"], 0) >= MAX_PER_TYPE:
            continue
        picked.append(ins)
        per_type[ins["type"]] = per_type.get(ins["type"], 0) + 1
        if len(picked) == MAX_OVERVIEW:
            break
    return picked
