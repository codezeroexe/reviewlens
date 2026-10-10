# N-gram results (TEST split)

| config | ngram | C | accuracy | macro-F1 | weighted-F1 | val macro-F1 | vocab |
|---|---|---|---|---|---|---|---|
| baseline | - | - | 0.7855 | 0.4399 | 0.6911 | - | - |
| unigram | (1, 1) | 10.0 | 0.8179 | 0.6863 | 0.8023 | 0.659 | 16688 |
| bigram | (2, 2) | 10.0 | 0.8079 | 0.618 | 0.7718 | 0.6275 | 146417 |
| uni_bigram | (1, 2) | 10.0 | 0.8148 | 0.6566 | 0.7897 | 0.6493 | 163105 |
