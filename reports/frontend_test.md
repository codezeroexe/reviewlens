# Frontend test (phase 7 walkthrough)

Browser: built-in pane, dev server on port 5174, API on 8001. Viewport 1366x768 unless noted.

| # | Step | Result | Note |
|---|---|---|---|
| 1 | Page loads, no console errors | PASS (after proxy fix) | Earlier ERR_CONNECTION_REFUSED came from a missing `/app` proxy; fixed. Network log shows all 200s. |
| 2 | Load Demo Dataset -> header shows real count | PASS (API) | Header count from `/app/status`. Button click itself not re-tested after final build. |
| 3 | Run Analysis -> real progress -> completion | PASS (API) | Ran 4 steps in 68.3 s. Progress shown as "Step n of 4: <name>". Browser progress not captured live. |
| 4 | Overview shows discoveries from real output | PASS | 4 cards from `insights.json`, numbers match. |
| 5 | Investigate on a discovery -> evidence opens | PARTIAL | Opens the matching page. Does NOT apply the evidence filters (product/aspect) yet. |
| 6 | Click complaint cluster -> original reviews | PASS (earlier build) | Drill-down verified in phase 3; overview click routes to it. |
| 7 | Click contradiction -> side-by-side view | PASS (earlier build) | Cards verified in phase 4. |
| 8 | Suspicious flag -> signals; Dismiss works | PASS (API) | Dismiss endpoint tested; UI click not re-tested. |
| 9 | Apply a filter -> content changes | PARTIAL | Existing product/aspect/level filters work on drill-downs. Global filter bar NOT built. |
| 10 | Upload bad file -> clear error | NOT IMPLEMENTED | No upload exists in the app. |
| 11 | Run with no dataset -> clear empty state | NOT TESTED | Logic present ("Load the demo dataset..."). Not exercised live. |

Other checks:
- No horizontal scroll at 1366 px (scrollWidth 1366 = clientWidth).
- Trend section: not rendered (one-week data).
- Date-span tile fixed (was clipping); stats now persist across server restart via `reports/dataset_stats.json`.
- Old Analyze page: works (35 of 35 preset reviews analyzed).
- Rollback tag `pre-frontend-redesign`: created on HEAD (4f1ca89, the last commit). Phases 2-7 work is uncommitted, so the tag does NOT contain the pre-redesign state of those files. Use it only as a commit marker.

## Added after user decision (build)
- Upload CSV/TSV/TXT/XLSX (header button). Cleaned by the phase-2 cleaner. Bad file: "Missing a text column..." shown in UI. Empty file: "The file is empty." Verified in browser and API.
- Global filter bar on Overview: product (products with >= 30 reviews), rating, date from/to, reset. Verified: rating 5 -> 12,252 of 20,000 reviews, tiles update.
- Category filter: hidden (only one category in the data).
- Analysis type filter: not built (no analysis type exists to filter by).
- Upload is browsable, not analysed. Run analysis is refused for uploads (API 409, button disabled). Uploaded data shows a note that discoveries are demo-sample results.
- Upload test files removed from data/uploads after testing.
