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

RANK_CHOICES = list(range(1, 31))
METRIC_CHOICES = ["karma", "created_days", "submitted_count"]

PATTERNS = [
    "On HN newest, compare authors at ranks #{rank_a} and #{rank_b}. Return signed difference for metric '{metric}' (rank {rank_a} minus rank {rank_b}).",
    "Using Hacker News newest, visit user profiles for ranks {rank_a} and {rank_b}. What is {metric}(rank {rank_a}) - {metric}(rank {rank_b})?",
    "From newest HN stories, compute {metric} gap between authors at ranks {rank_a} and {rank_b} (first minus second).",
]


@register_template("hackernews_user_karma_gap")
class HackerNewsUserKarmaGapTemplate(QuestionTemplate):
    """Compare karma of two story authors from newest feed."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_user_karma_gap")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        rank_a, rank_b = sorted(rng.sample(RANK_CHOICES, 2))
        metric = rng.choice(METRIC_CHOICES)
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(rank_a=rank_a, rank_b=rank_b, metric=metric),
            start_url="https://news.ycombinator.com/newest",
            variables={"rank_a": rank_a, "rank_b": rank_b, "metric": metric},
            validation_info={"rank_a": rank_a, "rank_b": rank_b, "metric": metric, "category_slug": "newest"},
            template_name=self.name,
            expected_steps=10,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN User Karma Gap):\n"
            f"- Compare newest ranks {validation_info.get('rank_a')} and {validation_info.get('rank_b')}\n"
            f"- Metric: {validation_info.get('metric')} from /user profile pages\n"
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

        metric = str(validation_info.get("metric", "karma"))
        if metric == "karma":
            value_a = data_a.get("karma")
            value_b = data_b.get("karma")
            if not isinstance(value_a, int) or not isinstance(value_b, int):
                return GroundTruthResult.fail("User karma missing in collected profile data")
            return GroundTruthResult.ok(str(value_a - value_b))

        if metric == "created_days":
            value_a = data_a.get("created")
            value_b = data_b.get("created")
            if not isinstance(value_a, int) or not isinstance(value_b, int):
                return GroundTruthResult.fail("User created timestamp missing in collected profile data")
            return GroundTruthResult.ok(str((value_a - value_b) // 86400))

        if metric == "submitted_count":
            submitted_a = data_a.get("submitted")
            submitted_b = data_b.get("submitted")
            if not isinstance(submitted_a, list) or not isinstance(submitted_b, list):
                return GroundTruthResult.fail("User submitted list missing in collected profile data")
            return GroundTruthResult.ok(str(len(submitted_a) - len(submitted_b)))

        return GroundTruthResult.fail(f"Unsupported metric '{metric}'")

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
