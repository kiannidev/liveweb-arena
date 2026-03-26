"""User-generated content template comparing author karma."""

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

from .common import get_category_stories, get_collected_hn_data, get_user_data

RANK_PAIR_CHOICES = [(1, 2), (1, 3), (2, 4), (3, 5)]

PATTERNS = [
    "On HN newest, compare author karma for story ranks #{rank_a} and #{rank_b}. Return signed difference (rank {rank_a} author karma minus rank {rank_b} author karma).",
    "Using Hacker News newest, visit user profiles for authors at ranks {rank_a} and {rank_b}. What is karma(rank {rank_a}) - karma(rank {rank_b})?",
    "From newest HN stories, compute the karma gap between authors at ranks {rank_a} and {rank_b} (first minus second).",
]


@register_template("hackernews_user_karma_gap")
class HackerNewsUserKarmaGapTemplate(QuestionTemplate):
    """Compare karma of two story authors from newest feed."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_user_karma_gap")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        rank_a, rank_b = rng.choice(RANK_PAIR_CHOICES)
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(rank_a=rank_a, rank_b=rank_b),
            start_url="https://news.ycombinator.com/newest",
            variables={"rank_a": rank_a, "rank_b": rank_b},
            validation_info={"rank_a": rank_a, "rank_b": rank_b, "category_slug": "newest"},
            template_name=self.name,
            expected_steps=10,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN User Karma Gap):\n"
            f"- Compare newest ranks {validation_info.get('rank_a')} and {validation_info.get('rank_b')}\n"
            "- Metric: author karma from /user profile pages\n"
            "- Score 1.0: exact signed difference\n"
            "- Score 0.5: absolute error <= 50 karma\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        collected, failure = get_collected_hn_data()
        if failure is not None:
            return failure

        rank_a = int(validation_info.get("rank_a", 1))
        rank_b = int(validation_info.get("rank_b", 2))
        min_count = max(rank_a, rank_b)

        stories, failure = get_category_stories(collected, "newest", min_count=min_count)
        if failure is not None:
            return failure

        story_a = stories[rank_a - 1]
        story_b = stories[rank_b - 1]
        user_a = story_a.get("by")
        user_b = story_b.get("by")
        if not isinstance(user_a, str) or not isinstance(user_b, str):
            return GroundTruthResult.fail("Story author missing")

        data_a, failure = get_user_data(collected, user_a)
        if failure is not None:
            return failure
        data_b, failure = get_user_data(collected, user_b)
        if failure is not None:
            return failure

        karma_a = data_a.get("karma")
        karma_b = data_b.get("karma")
        if not isinstance(karma_a, int) or not isinstance(karma_b, int):
            return GroundTruthResult.fail("User karma missing in collected profile data")

        return GroundTruthResult.ok(str(karma_a - karma_b))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
