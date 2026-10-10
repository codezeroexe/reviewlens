# Contradiction Investigator run

**Preliminary: no evaluation of contradiction quality yet.**

- Reviews: first 20000 rows of Electronics TSV (same subset as phase 3)
- Products scanned: 10050
- Sentences naming an aspect: 21533
- Candidate pairs (pos vs neg, same product+aspect, different reviews): 2737
- Verification method: nli
- NLI label counts: {'neutral': 1582, 'contradiction': 1079, 'entailment': 76}
- NLI contradictions before strict filter: 1079
- Filter: NLI contradiction, score >= 0.9, both quotes contain the same aspect keyword
- Conflicts shown after strict filter: 567
- Runtime: 106.4 s
- Polarity: VADER compound, positive > 0.3, negative < -0.3
- Embeddings for ranking: sentence-transformers all-MiniLM-L6-v2

## Limitations

- Aspects are keyword matches. They miss paraphrases and can match the wrong sense.
- Polarity from VADER is a rough lexicon score. It can misread sarcasm and negation.
- NLI model labels a sentence pair, not the product. A 'contradiction' label is a model output, not proof.
- Context words are literal keyword matches inside the sentence only.
- Head sample of one file. Most products have few reviews, so few pairs.
