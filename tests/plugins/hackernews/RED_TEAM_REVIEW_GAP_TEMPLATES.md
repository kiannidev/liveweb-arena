# Red Team Review: HackerNews Gap Templates (T110-T113)

Date: 2026-03-27  
Scope: `hackernews_recent_burst_count`, `hackernews_comment_tree_focus`, `hackernews_keyword_scan_rank`, `hackernews_user_karma_gap`

This document records the mandatory 6-check red-team review with concrete data.

## Template Summary

- **T110** (`hackernews_recent_burst_count`): count stories within time window around an anchor rank timestamp.
- **T111** (`hackernews_comment_tree_focus`): compute nested comment-tree metrics at configurable depth threshold.
- **T112** (`hackernews_keyword_scan_rank`): use HN search (`hn.algolia.com`) and extract rank/field from filtered search hits.
- **T113** (`hackernews_user_karma_gap`): compare user-profile metrics across two story-author ranks.

## Check 1: API Semantic Verification

Pass.

- **T110/T111/T113** semantics map directly to Firebase item/user payload fields:
  - Story timestamps (`time`), comment tree (`kids`), user profile (`karma`, `created`, `submitted`).
- **T112** semantics map to Algolia search payload fields:
  - Query-specific `hits`, `title`, `author`, `points`, `num_comments`.
- Real payload structures were captured and exercised in:
  - `tests/plugins/hackernews/test_gap_templates_real_api_data.py`

## Check 2: World Knowledge Attack

Pass.

- Questions are tied to dynamic, rapidly changing page/API state:
  - newest ordering/timestamps, per-story comment trees, query-time search hits, and live user metrics.
- Static world knowledge cannot recover:
  - rank-conditioned values (`rank`, `anchor_rank`),
  - depth-filtered nested counts,
  - per-query ranked search result fields.
- Estimated no-browse success remains low (near random for numeric/string exact tasks).

## Check 3: Memorization Space Analysis

Pass.

Effective variant space lower-bound (parameter-level):

- **T110**: `10 story_counts * 10 windows * 5 anchors * 2 comparators = 1000`
- **T111**: `30 ranks * 5 min_depths * 4 metrics = 600`
- **T112**: `52 queries * 20 ranks * 4 fields * 4 point thresholds = 16640`
- **T113**: `C(30,2)=435 rank pairs * 3 metrics = 1305`

All exceed 500.

## Check 4: Answer Stability

Pass.

- **T110/T111/T112** rely on high-volatility feeds (`newstories`, search_by_date, active comment trees).
- **T113** mixes slower (`karma`, `created`) and more dynamic (`submitted_count`) profile dimensions.
- Because answers are rank-conditioned and interaction-dependent, even stable user/account facts do not collapse the overall QA pool.

## Check 5: Random Baseline Analysis

Pass.

- Answer format is open numeric/string exact match, not multiple-choice.
- Random guess probability is low:
  - numeric exact-difference/count tasks (T110/T111/T113),
  - exact string/integer extraction from ranked filtered search hits (T112).
- No binary-choice style templates in this set.

## Check 6: Cross-Parameter Collapse Detection

Pass.

- Added independent dimensions to avoid collapse:
  - **T110**: anchor rank + comparator mode
  - **T111**: depth + structural metric
  - **T112**: query + rank + field + point-threshold filter
  - **T113**: rank-pair combinations + metric family
- `NONE` paths remain valid but are no longer dominant across the whole parameter space due to expanded query/field/rank/threshold combinations and non-binary answers.

## Verification Artifacts

- Real API structure GT verification:
  - `tests/plugins/hackernews/test_gap_templates_real_api_data.py`
- Core template behavior and variant-space assertions:
  - `tests/test_hackernews_gap_templates.py`
- Nested collection path coverage for T111:
  - story detail fetch now includes bounded `_comment_items` subtree payload
  - GT collector merges `_comment_items` so nested metrics can be computed
    after story-detail navigation without requiring each comment URL visit
- Local command run:
  - `PYTHONPATH=. pytest -q tests/test_hackernews_gap_templates.py tests/plugins/hackernews/test_gap_templates_real_api_data.py`
