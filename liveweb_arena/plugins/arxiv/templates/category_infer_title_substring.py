"""ArXiv category discovery + title substring count (registry T112).

The question describes which new-submissions stream to open using prose only
(no official category label, no URL). The substring to search for is given
via a semantic clue that does not spell the literal needle (see
`title_substring_clues.TITLE_SUBSTRING_SPECS`).

Effective variants: len(CATEGORIES) * len(TITLE_SUBSTRING_SPECS) * len(TOP_N) * len(PATTERNS) > 500.
"""

import random
from typing import Any, Dict, Optional

from liveweb_arena.core.ground_truth_trigger import GroundTruthResult, TriggerConfig, UrlPatternTrigger
from liveweb_arena.core.gt_collector import GTSourceType
from liveweb_arena.core.validators.base import (
    GeneratedQuestion,
    QuestionTemplate,
    ValidationResult,
    register_template,
)

from .category_discovery_hints import CATEGORY_NAVIGATION_HINTS
from .common import get_collected_listing_data, get_papers_from_listing
from .title_substring_clues import TITLE_SUBSTRING_SPECS
from .variables import CATEGORIES

TOP_N = [4, 5, 6, 7, 8]

PATTERNS = [
    (
        "On arXiv, open today's new-submissions feed for the stream best matching this description: "
        "\"{nav_hint}\". Among the first {n} titles, how many contain a case-insensitive substring "
        "matching this clue (count each paper at most once): {clue}"
    ),
    (
        "Find the arXiv new-submissions page whose topical focus fits: \"{nav_hint}\". "
        "Scanning only the first {n} titles, count how many satisfy the substring clue (ignore letter case): {clue}"
    ),
    (
        "Locate the daily new papers on arXiv for the area described as: \"{nav_hint}\". "
        "In the first {n} titles, how many include a substring described by: {clue} (case-insensitive)?"
    ),
]


@register_template("arxiv_category_infer_title_substring")
class ArxivCategoryInferTitleSubstringTemplate(QuestionTemplate):
    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("arxiv_category_infer_title_substring")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        cat = rng.choice(CATEGORIES)
        nav_hint = CATEGORY_NAVIGATION_HINTS[cat.code]
        n = rng.choice(TOP_N)
        clue, needle = rng.choice(TITLE_SUBSTRING_SPECS)
        pattern = rng.choice(PATTERNS)
        question_text = pattern.format(nav_hint=nav_hint, n=n, clue=clue)
        return GeneratedQuestion(
            question_text=question_text,
            start_url="https://arxiv.org",
            variables={"category": cat.code, "top_n": n, "needle": needle, "substring_clue": clue},
            validation_info={
                "category": cat.code,
                "top_n": n,
                "needle": needle,
                "substring_clue": clue,
            },
            template_name=self.name,
            expected_steps=14,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (ArXiv category discovery + substring clue):\n"
            f"- Expected listing category code: {validation_info.get('category')}\n"
            f"- Papers scanned: first {validation_info.get('top_n')}\n"
            f"- Substring clue shown to agent: {validation_info.get('substring_clue')}\n"
            f"- Canonical substring for scoring (case-insensitive): {validation_info.get('needle')}\n"
            "- Score 1.0: exact count\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        category = str(validation_info.get("category", ""))
        n = int(validation_info.get("top_n", 5))
        needle = str(validation_info.get("needle", "")).lower()

        data, failure = get_collected_listing_data(category)
        if failure is not None:
            return failure
        papers, failure = get_papers_from_listing(data)
        if failure is not None:
            return failure
        if len(papers) < n:
            return GroundTruthResult.not_collected(
                f"Need at least {n} papers in listing, have {len(papers)}."
            )

        count = 0
        for p in papers[:n]:
            title = p.get("title")
            if not isinstance(title, str):
                return GroundTruthResult.fail("Paper missing title string")
            if needle and needle in title.lower():
                count += 1
        return GroundTruthResult.ok(str(count))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["arxiv.org"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "arxiv"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
