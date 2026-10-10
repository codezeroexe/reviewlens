# Label notes

## Usefulness (used in phase 2)
- Rule (user-chosen): `useful = 1 if helpful_votes / total_votes >= 0.6 else 0`.
- Only rows with `total_votes >= 5` are labelled. Rows with fewer votes are excluded, not labelled 0. Same threshold as notebook cell 16.
- Source for threshold 0.6: the example rule in `plans/phase1.md`, chosen by the user. Not tuned on data.
- Not a training label for the production model. Production model stays unsupervised.
- Limits: helpful votes are noisy. Newer reviews have few votes, so the 5-vote filter drops them. Rating-independent: a helpful review can have any star rating. Votes can reflect product popularity, not review quality.

## Suspicious / fake (dropped from phase 2)
- No label and no model exist in the app. A label would have to be invented, which the plan forbids.
- Phase 2 experiment and batch output omit the suspicious column.
- Revisit only if the user supplies a labelled source or a rule.
