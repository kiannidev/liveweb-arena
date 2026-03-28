"""ArXiv category discovery + author-count threshold (registry T113).

Same navigation pattern as `arxiv_category_infer_title_substring`: prose describes
which new-submissions stream to open—no official label in the question text.

Effective variants: len(CATEGORIES) * len(TOP_N) * len(AUTHOR_THRESHOLDS) * len(PATTERNS) > 500.
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
from .variables import CATEGORIES

TOP_N = [4, 5, 6, 7, 8]
AUTHOR_THRESHOLDS = [2, 3, 4, 5, 6]

PATTERNS = [
    (
        "On arXiv, open today's new-submissions listing for the stream best described by: \"{nav_hint}\". "
        "Among the first {n} papers, how many list strictly more than {k} authors?"
    ),
    (
        "Locate the arXiv new-submissions page matching this topical description: \"{nav_hint}\". "
        "Considering only the first {n} entries, count papers whose author count is greater than {k}."
    ),
    (
        "Find the daily new papers on arXiv under the area summarized as: \"{nav_hint}\". "
        "In the top {n} items, how many have more than {k} authors named on the listing?"
    ),
]


@register_template("arxiv_category_infer_author_filter")
class ArxivCategoryInferAuthorFilterTemplate(QuestionTemplate):
    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("arxiv_category_infer_author_filter")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        cat = rng.choice(CATEGORIES)
        nav_hint = CATEGORY_NAVIGATION_HINTS[cat.code]
        n = rng.choice(TOP_N)
        k = rng.choice(AUTHOR_THRESHOLDS)
        pattern = rng.choice(PATTERNS)
        question_text = pattern.format(nav_hint=nav_hint, n=n, k=k)
        return GeneratedQuestion(
            question_text=question_text,
            start_url="https://arxiv.org",
            variables={"category": cat.code, "top_n": n, "author_threshold": k},
            validation_info={"category": cat.code, "top_n": n, "author_threshold": k},
            template_name=self.name,
            expected_steps=14,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (ArXiv category discovery + author threshold):\n"
            f"- Expected listing category code: {validation_info.get('category')}\n"
            f"- Papers scanned: first {validation_info.get('top_n')}\n"
            f"- Strict author floor: {validation_info.get('author_threshold')}\n"
            "- Score 1.0: exact count\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        category = str(validation_info.get("category", ""))
        n = int(validation_info.get("top_n", 5))
        k = int(validation_info.get("author_threshold", 3))

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
            authors = p.get("authors")
            if not isinstance(authors, list):
                return GroundTruthResult.fail("Paper missing authors list")
            if len(authors) > k:
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
