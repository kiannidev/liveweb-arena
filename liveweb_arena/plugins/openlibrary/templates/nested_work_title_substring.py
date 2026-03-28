"""Open Library nested navigation + catalog title audit (registry T111).

Requires **two browsing levels**: subject hub listing, then the ranked work's
detail page. Ground truth counts **non-overlapping** case-insensitive
occurrences of a substring in the **work page** catalog title; the substring
is specified only via a semantic clue (no literal needle in the question).

Covers CLAUDE.md gaps: **nested structure navigation** (hierarchical drill-down)
and **user-generated / catalog text** (real book titles).

Effective variants: len(SUBJECT_SCENARIOS) * len(RANKS) * len(BOOK_TITLE_SUBSTRING_SPECS) * len(PATTERNS) > 500.
"""

import random
from typing import Any, Dict, List, Optional

from liveweb_arena.core.ground_truth_trigger import GroundTruthResult, TriggerConfig, UrlPatternTrigger
from liveweb_arena.core.gt_collector import GTSourceType, get_current_gt_collector
from liveweb_arena.core.validators.base import (
    GeneratedQuestion,
    QuestionTemplate,
    ValidationResult,
    register_template,
)

from .book_work_title_clues import BOOK_TITLE_SUBSTRING_SPECS
from .common import find_subject_payload
from .subject_hub_infer import SUBJECT_SCENARIOS

RANKS = [1, 2, 3, 4, 5, 6, 7, 8]

PATTERNS = [
    (
        'Starting from the Open Library home page, locate the subject hub best described by: "{hint}". '
        "Open the work that appears at **position {rank}** in that hub's listing (1 = topmost). "
        "On the work's detail page, how many **non-overlapping** case-insensitive occurrences of the "
        "substring described below appear in the **catalog title**? Substring clue: {clue}"
    ),
    (
        'On Open Library, navigate from the home page to the topical hub matching: "{hint}". '
        "Select the book ranked **{rank}** on that hub page, then view its work page. "
        "Count non-overlapping matches (ignore letter case) in the official title for: {clue}"
    ),
    (
        'Find the Open Library subject area fitting: "{hint}". Go to the **{rank}-th** listed work '
        "(counting from 1). From that work's page, report how many times (non-overlapping, "
        "case-insensitive) the title contains a substring matching: {clue}"
    ),
]


def _count_nonoverlapping(haystack: str, needle: str) -> int:
    if not needle:
        return 0
    h = haystack.lower()
    n = needle.lower()
    count = 0
    i = 0
    while True:
        j = h.find(n, i)
        if j < 0:
            break
        count += 1
        i = j + len(n)
    return count


@register_template("openlibrary_subject_nested_work_title")
class OpenLibrarySubjectNestedWorkTitleTemplate(QuestionTemplate):
    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("openlibrary_subject_nested_work_title")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        slug, hint = rng.choice(SUBJECT_SCENARIOS)
        rank = rng.choice(RANKS)
        clue, needle = rng.choice(BOOK_TITLE_SUBSTRING_SPECS)
        pattern = rng.choice(PATTERNS)
        question_text = pattern.format(hint=hint, rank=rank, clue=clue)
        return GeneratedQuestion(
            question_text=question_text,
            start_url="https://openlibrary.org",
            variables={"subject_slug": slug, "rank": rank, "needle": needle, "substring_clue": clue},
            validation_info={
                "subject_slug": slug,
                "rank": rank,
                "needle": needle,
                "substring_clue": clue,
            },
            template_name=self.name,
            expected_steps=16,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (Open Library nested work title substring):\n"
            "- Navigate subject hub then open the ranked work; do not paste hub URLs in answers.\n"
            f"- Subject slug (validator): {validation_info.get('subject_slug')}\n"
            f"- Listing rank: {validation_info.get('rank')}\n"
            f"- Substring clue: {validation_info.get('substring_clue')}\n"
            f"- Canonical needle: {validation_info.get('needle')}\n"
            "- Count non-overlapping case-insensitive occurrences in the catalog title on the work page.\n"
            "- Score 1.0: exact count\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        gt_collector = get_current_gt_collector()
        if gt_collector is None:
            return GroundTruthResult.system_error("No GT collector available")
        slug = str(validation_info.get("subject_slug", ""))
        rank = int(validation_info.get("rank", 1))
        needle = str(validation_info.get("needle", ""))

        collected = gt_collector.get_collected_api_data()
        payload = find_subject_payload(collected, slug)
        if payload is None:
            return GroundTruthResult.not_collected(
                f"Subject hub data for '{slug}' not collected. Visit the matching subjects page."
            )
        works = payload.get("works")
        if not isinstance(works, dict):
            return GroundTruthResult.fail("Malformed works on subject payload")

        ordered: List[Dict[str, Any]] = sorted(works.values(), key=lambda w: w.get("rank", 0))
        ordered = [w for w in ordered if isinstance(w, dict)]
        if len(ordered) < rank:
            return GroundTruthResult.not_collected(
                f"Need at least {rank} works on subject page, have {len(ordered)}."
            )
        target = ordered[rank - 1]
        wkey = target.get("key")
        if not isinstance(wkey, str) or not wkey.startswith("/works/"):
            return GroundTruthResult.fail("Work entry missing canonical key")

        detail = collected.get(f"ol:{wkey}")
        if not isinstance(detail, dict):
            return GroundTruthResult.not_collected(
                f"Work page for {wkey} not collected. Open the work from the hub listing."
            )
        title = detail.get("title")
        if not isinstance(title, str):
            return GroundTruthResult.fail("Work detail missing title string")

        return GroundTruthResult.ok(str(_count_nonoverlapping(title, needle)))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["openlibrary.org"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "openlibrary"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
