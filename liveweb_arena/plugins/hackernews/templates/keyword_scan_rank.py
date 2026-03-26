"""Search-driven keyword scanning template for Hacker News newest feed."""

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

from .common import get_category_stories, get_collected_hn_data

KEYWORDS = ["ai", "open", "data", "rust", "python", "cloud", "model", "agent"]
SEARCH_SPANS = [15, 20, 30]

PATTERNS = [
    "On HN newest, scan top {n} stories and find the first rank whose title contains '{keyword}' (case-insensitive). Return the rank or NONE.",
    "Using Hacker News /newest, among top {n} titles, what is the earliest rank containing keyword '{keyword}'? If absent, answer NONE.",
    "Search through the newest {n} HN headlines for '{keyword}'. Report first matching rank, otherwise NONE.",
]


@register_template("hackernews_keyword_scan_rank")
class HackerNewsKeywordScanRankTemplate(QuestionTemplate):
    """Find first newest rank whose title matches a keyword."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_keyword_scan_rank")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        keyword = rng.choice(KEYWORDS)
        n = rng.choice(SEARCH_SPANS)
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(n=n, keyword=keyword),
            start_url="https://news.ycombinator.com/newest",
            variables={"keyword": keyword, "span": n},
            validation_info={"keyword": keyword, "story_count": n, "category_slug": "newest"},
            template_name=self.name,
            expected_steps=8,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Keyword Scan Rank):\n"
            f"- Keyword: {validation_info.get('keyword')}\n"
            f"- Search span: top {validation_info.get('story_count')} newest stories\n"
            "- Score 1.0: exact rank match, or exact NONE when no match exists\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        collected, failure = get_collected_hn_data()
        if failure is not None:
            return failure
        keyword = str(validation_info.get("keyword", "")).lower().strip()
        n = int(validation_info.get("story_count", 20))

        stories, failure = get_category_stories(collected, "newest", min_count=n)
        if failure is not None:
            return failure
        stories = stories[:n]

        for story in stories:
            title = str(story.get("title", "")).lower()
            rank = story.get("rank")
            if keyword and keyword in title and isinstance(rank, int):
                return GroundTruthResult.ok(str(rank))
        return GroundTruthResult.ok("NONE")

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
