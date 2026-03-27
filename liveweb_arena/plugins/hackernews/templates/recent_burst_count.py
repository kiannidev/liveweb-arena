"""Time-sensitive burst detection template for Hacker News newest feed."""

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

WINDOW_MINUTES = [10, 15, 20, 30, 45, 60, 90, 120, 180, 240]
STORY_COUNTS = [10, 12, 15, 18, 20, 24, 30, 36, 42, 50]
ANCHOR_RANKS = [1, 2, 3, 4, 5]
INCLUDE_EQUAL_MODES = [True, False]

PATTERNS = [
    "On Hacker News newest, among the top {n} stories, how many were posted {cmp} {window} minutes of rank #{anchor_rank} story time?",
    "Using HN /newest, count top {n} stories whose posting time is {cmp} {window} minutes from rank {anchor_rank}.",
    "From the newest {n} HN stories, how many fall {cmp} a {window}-minute burst window anchored at rank {anchor_rank}?",
]


@register_template("hackernews_recent_burst_count")
class HackerNewsRecentBurstCountTemplate(QuestionTemplate):
    """Count how many newest stories fall inside a recent time burst."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_recent_burst_count")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        n = rng.choice(STORY_COUNTS)
        window = rng.choice(WINDOW_MINUTES)
        anchor_rank = rng.choice([r for r in ANCHOR_RANKS if r <= n])
        include_equal = rng.choice(INCLUDE_EQUAL_MODES)
        cmp_text = "within or equal to" if include_equal else "strictly within"
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(
                n=n,
                window=window,
                anchor_rank=anchor_rank,
                cmp=cmp_text,
            ),
            start_url="https://news.ycombinator.com/newest",
            variables={
                "story_count": n,
                "window_minutes": window,
                "anchor_rank": anchor_rank,
                "include_equal": include_equal,
            },
            validation_info={
                "story_count": n,
                "window_minutes": window,
                "anchor_rank": anchor_rank,
                "include_equal": include_equal,
                "category_slug": "newest",
            },
            template_name=self.name,
            expected_steps=8,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Recent Burst Count):\n"
            f"- Top stories considered: {validation_info.get('story_count')}\n"
            f"- Anchor rank: {validation_info.get('anchor_rank')}\n"
            f"- Time window: {validation_info.get('window_minutes')} minutes from newest post\n"
            f"- Comparison mode includes equality: {validation_info.get('include_equal')}\n"
            "- Score 1.0: exact count\n"
            "- Score 0.5: off by 1\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        collected, failure = get_collected_hn_data()
        if failure is not None:
            return failure
        n = int(validation_info.get("story_count", 20))
        window = int(validation_info.get("window_minutes", 60))
        anchor_rank = int(validation_info.get("anchor_rank", 1))
        include_equal = bool(validation_info.get("include_equal", True))

        stories, failure = get_category_stories(collected, "newest", min_count=max(n, anchor_rank))
        if failure is not None:
            return failure
        stories = stories[:n]

        anchor_story = stories[anchor_rank - 1]
        anchor_ts = anchor_story.get("time")
        if not isinstance(anchor_ts, int):
            return GroundTruthResult.fail("Anchor story missing unix timestamp")

        count = 0
        for story in stories:
            story_ts = story.get("time")
            if not isinstance(story_ts, int):
                return GroundTruthResult.fail("Story missing unix timestamp")
            delta_minutes = abs(anchor_ts - story_ts) / 60.0
            in_window = delta_minutes <= window if include_equal else delta_minutes < window
            if in_window:
                count += 1

        return GroundTruthResult.ok(str(count))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
