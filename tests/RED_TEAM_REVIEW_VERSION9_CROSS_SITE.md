# Red Team Review — Version 9 cross-site templates (IDs 110–113)

Templates: `openmeteo_daily_precip_peak_day` (110), `openlibrary_subject_nested_work_title` (111),
`arxiv_category_infer_title_substring` (112), `arxiv_category_infer_author_filter` (113).

**CLAUDE.md evaluation gaps (portfolio table) addressed by this version:**

| Gap | Template | Mechanism |
|-----|----------|-----------|
| Time-sensitive events | T110 | Calendar-relative **which day** has highest **daily max precipitation probability** (forecast shifts daily). |
| Nested structure navigation | T111 | **Two-level drill-down**: subject hub listing → **ranked work** → **work detail page** (hierarchical navigation, not a flat single list read). |
| Search-driven interaction | T112 | **Infer** arXiv new-submissions stream from prose (`category_discovery_hints.py`); no official category label in the question. |
| User-generated content | T111 (primary) | **Catalog titles** are curator/community-facing text; substring audit is over real title strings on the work page. T113 uses **author lines** on live listings (collaborative paper metadata). |

## Check 1 — API semantic verification

| Template | API / binding |
|----------|----------------|
| T110 | Open-Meteo forecast JSON: `daily.precipitation_probability_max[0:3]` vs same fields injected into docs cache (`openmeteo:{lat,lon}`). |
| T111 | Subject payload (`ol:{subject_url}`) for `works[]` + **work detail** (`ol:{/works/...}`) with `title`; GT requires both merges. |
| T112–T113 | ArXiv listing payload: `papers` ordered by `rank`; titles / authors from the same snapshot as the listing page. |

## Check 2 — Memorization / variant space (effective > 500)

| Template | Lower bound |
|----------|-------------|
| T110 | `len(CITIES) * 3` patterns ≥ 510 (`variables.CITIES` = 170). |
| T111 | `len(SUBJECT_SCENARIOS) * len(RANKS) * len(BOOK_TITLE_SUBSTRING_SPECS) * len(PATTERNS)` = 30×8×51×3 = 36,720. |
| T112 | `len(CATEGORIES) * len(TITLE_SUBSTRING_SPECS) * len(TOP_N) * len(PATTERNS)` = 41×49×5×3 = 30,135. |
| T113 | `41 * 5 * 5 * 3` = 3,075. |

## Check 3 — Cross-parameter collapse

- T110: Answer depends on live `precipitation_probability_max`; not constant across cities/dates.
- T111: Rank, subject, clue/needle, and live titles change counts; work page must be visited or GT is `not_collected`.
- T112–T113: Listing content changes daily; thresholds and clues vary.

## Check 4 — Visibility / page binding

All four use `GTSourceType.PAGE_ONLY` and collected data from visited plugin URLs (Open-Meteo docs with coords, arXiv `/list/.../new`, Open Library **subject + work** pages for T111).

## Check 5 — CLAUDE.md §3 (no navigation hints)

- **T110**: City name only; start URL is generic docs home (coordinates chosen when opening a city).
- **T111**: Prose hub description only — no `/subjects/...` slug or openlibrary.org URL in the question; substring is given as a **clue**, not the literal needle (`book_work_title_clues._validate_specs()`).
- **T112–T113**: Prose **navigation hints** per category (`category_discovery_hints.py`) are vetted so the **official arXiv category display name** does not appear as a substring of the hint. Official labels are validator-only.
- **T112 substring**: The **literal needle** is not spelled in the clue text (`title_substring_clues._validate_specs()`).

## Check 6 — SFT / shortcut attacks

- T110: Requires reading three daily maxima and comparing; city-specific weather breaks memorization.
- T111: Requires mapping prose → subject hub, **opening a ranked work**, and resolving a **clue → substring** on a live catalog title.
- T112: Requires correct category inference plus clue → substring resolution on changing titles.
- T113: Same routing as T112 with author-count arithmetic on listings.

## Evidence

- Synthetic GT: `tests/test_version9_cross_site_templates.py`, `tests/test_openmeteo_integration.py` (`test_gt_with_real_api_data` includes T110 on a real API snapshot).
