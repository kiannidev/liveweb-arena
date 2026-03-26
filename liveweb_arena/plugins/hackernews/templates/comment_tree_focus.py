"""Nested-structure navigation template for Hacker News comments."""

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

from .common import get_category_stories, get_collected_hn_data, get_item_story

RANK_CHOICES = [1, 2, 3, 4, 5]

PATTERNS = [
    "On HN newest, open the #{rank} story and report how many top-level comments it has (the immediate children count).",
    "Using Hacker News /newest, inspect rank {rank} story detail: how many direct root comments are attached to the story?",
    "From HN newest, visit story #{rank}. What is the count of first-level comments under the story node?",
]


@register_template("hackernews_comment_tree_focus")
class HackerNewsCommentTreeFocusTemplate(QuestionTemplate):
    """Measure top-level comment node count for a selected newest story rank."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_comment_tree_focus")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        rank = rng.choice(RANK_CHOICES)
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(rank=rank),
            start_url="https://news.ycombinator.com/newest",
            variables={"rank": rank},
            validation_info={"rank": rank, "category_slug": "newest"},
            template_name=self.name,
            expected_steps=9,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Comment Tree Focus):\n"
            f"- Target newest rank: {validation_info.get('rank')}\n"
            "- Expected answer is top-level comment count (immediate children only)\n"
            "- Score 1.0: exact\n"
            "- Score 0.5: off by <=2\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        collected, failure = get_collected_hn_data()
        if failure is not None:
            return failure

        rank = int(validation_info.get("rank", 1))
        stories, failure = get_category_stories(collected, "newest", min_count=rank)
        if failure is not None:
            return failure

        target_story = stories[rank - 1]
        item_id = target_story.get("id")
        if not isinstance(item_id, int):
            return GroundTruthResult.fail("Target story missing id")

        item_data, failure = get_item_story(collected, item_id)
        if failure is not None:
            return failure

        kids = item_data.get("kids")
        if kids is None:
            return GroundTruthResult.ok("0")
        if not isinstance(kids, list):
            return GroundTruthResult.fail("Malformed kids field in item payload")
        return GroundTruthResult.ok(str(len(kids)))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
