# N-gram report

Source: `reports/ngram_results.json` and `experiments/tfidf_ngram.py` (same split: train 12,068, val 2,586, test 2,587).

## Fit and tuning policy

- Vectorizer and classifier fit on TRAIN only. C tuned on VALIDATION. TEST scored once per config.
- **Verified in code:** `experiments/tfidf_ngram.py` lines 86-94. Test is not used for fitting or tuning.
- Caveat: the best config (unigram) also had the best validation macro-F1, so selection agrees on both splits.

## Test results (from reports/ngram_results.json)

| Config | Accuracy | Macro-F1 | Weighted-F1 | Vocab (fit on train) | Train seconds |
|---|---|---|---|---|---|
| Baseline (majority) | 0.7855 | 0.4399 | 0.6911 | - | - |
| unigram | 0.8179 | 0.6863 | 0.8023 | 16,688 | 0.58 |
| bigram | 0.8079 | 0.618 | 0.7718 | 146,417 | 1.37 |
| uni_bigram | 0.8148 | 0.6566 | 0.7897 | 163,105 | 1.95 |

- Production model on same test set: N/A: ReviewLens is unsupervised (5 clusters). No usefulness output to score.

## Top 20 terms (train corpus counts, min_df=2)

**unigram** (vocab 16,688): the (110,818), and (54,451), to (53,964), it (41,536), br (36,588), is (31,541), of (30,077), for (25,508), this (23,512), in (23,044), that (22,331), with (20,157), you (20,023), my (19,706), on (18,527), not (16,045), but (15,792), have (14,451), are (12,663), was (12,646)

**bigram** (vocab 146,417): br br (14,049), of the (7,884), on the (5,841), in the (5,528), to the (4,454), and the (4,204), if you (4,187), with the (4,185), for the (3,764), it is (3,457), the sound (3,372), this is (3,222), you can (2,797), to be (2,763), br the (2,636), and it (2,310), they are (2,121), it was (2,087), from the (2,066), sound quality (2,034)

**uni_bigram** (vocab 163,105): the (110,818), and (54,451), to (53,964), it (41,536), br (36,588), is (31,541), of (30,077), for (25,508), this (23,512), in (23,044), that (22,331), with (20,157), you (20,023), my (19,706), on (18,527), not (16,045), but (15,792), have (14,451), br br (14,049), are (12,663)

## Error analysis (best config, 10 sampled misclassified test rows)

- Misclassified: 471 of 2587 test rows.
- False positives (pred useful, label not): 335. False negatives: 136.
- Median words: misclassified 58.0, all test 94.0.
- Rating-label titles (e.g. 'Five Stars ...'): {'share_of_test_rows': 0.0831, 'accuracy_rows_with_title_star': 0.6977, 'accuracy_rows_without': 0.8288, 'share_of_errors_with_title_star': 0.138, 'errors_false_positive_useful': 335, 'errors_false_negative': 136}

- [R13D7EUBRHM7HG] label 0, pred 1: "help please So based on all the reviews I was drawn to purchase this device for a family function. Got it fast..my problem is that I've had this Damn thing charged since I received it today. The instructions said charge it for 6 hours or until the red light disappears. It's been well over 6 hours. S"
- [RC5ED5BMPSES5] label 0, pred 1: "this unit is said to be a hundred eighty five ... this unit is said to be a hundred eighty five watts per channel it is not it is 90 watts per channel severely lower power than what I already had which was an Onkyo 110 watt RMS per channel"
- [R10IVMJBTDE80F] label 0, pred 1: "One Star didnt need it, old one worked just fine"
- [R1Z3GWOBGSJ53D] label 1, pred 0: "piece of crap Dont waste your money, there are better speaker like the mpow armor that's 20 times better and is inthe same range of price"
- [RSTMLL7TCBSWZ] label 0, pred 1: "Five Stars Awesome AVR. Exceeds expectations with all bells and whisltes and upgrading potential for hone theater use."
- [R38039Z87AJZJP] label 0, pred 1: "One Star the sound is not clear when i plug it into my toshiba laptop :-("
- [R16GEJTZSF2HES] label 1, pred 0: "NOT durable. Coating over wires peel away. Loved these headphones when I initially bought them. They were comfortable and had decent sound quality (for my needs anyway). However, a few months after I got them, the coating over the headphone wires started to peel away/disintegrate. They still work, b"
- [R315NY20HAOIUJ] label 0, pred 1: "Five Stars very stable seems to be  just what i wanted"
- [R3UB1Q7KXPRM2R] label 0, pred 1: "Good Product; No Replacement Parts Plusses: Good sound quality (I am not an audiophile, and use it with an iPhone, so factor that in). Easy to use,. Easy to set up w/o instructions. Good battery life. Great price (under $100 at Costco).  Minuses (and this is a big one):  NO REPLACEMENT PARTS AVAILAB"
- [R1LPW330498YYF] label 1, pred 0: "Complete waste of time and money POS. It did not come with a code list. Couldn't get it to work on my DVR. Could not access the guide or list of programs I had saved on the DVR. Complete waste of time and money. Need to read more reviews before I try to buy another universal remote."

## Known limitations

- Stopwords are kept (the, and, to ...). They dominate the top-20 lists.
- Usefulness label is derived from votes (helpful/total >= 0.6, total >= 5). Not human-verified.
- Head sample of one file (Electronics). Not random across the file.
- Dedupe is before the split, on normalised text; near-duplicates across splits are not removed.
- Production model has no usefulness output, so no production comparison is possible.
