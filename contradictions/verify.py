"""Check each candidate with NLI (cross-encoder/nli-deberta-v3-small). Fallback: keep sentiment-opposed pairs, unverified."""

import pandas as pd

NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
FALLBACK_LABEL = "opposing sentiment (not verified as logical contradiction)"


def verify(pairs: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if pairs.empty:
        return pairs.assign(method=[], nli_label=[], nli_score=[]), "none"
    try:
        from transformers import pipeline
        nli = pipeline("text-classification", model=NLI_MODEL, device=-1)
    except Exception as error:
        print(f"NLI unavailable ({type(error).__name__}). Using sentiment fallback.")
        out = pairs.assign(method="sentiment-fallback", nli_label=None, nli_score=None)
        out["verdict"] = FALLBACK_LABEL
        return out, "sentiment-fallback"

    inputs = [{"text": p, "text_pair": n} for p, n in zip(pairs["pos_sentence"], pairs["neg_sentence"])]
    results = nli(inputs, batch_size=32, truncation=True)
    out = pairs.assign(method="nli",
                       nli_label=[r["label"] for r in results],
                       nli_score=[round(float(r["score"]), 4) for r in results])
    out["verdict"] = out["nli_label"].map({"contradiction": "NLI: contradiction (model score)",
                                           "entailment": "NLI: entailment (model score)",
                                           "neutral": "NLI: neutral (model score)"})
    return out, "nli"
