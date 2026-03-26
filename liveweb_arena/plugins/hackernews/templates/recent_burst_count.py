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

WINDOW_MINUTES = [30, 60, 120, 240]
STORY_COUNTS = [15, 20, 30]

PATTERNS = [
    "On Hacker News newest, among the top {n} stories, how many were posted within {window} minutes of the newest story timestamp?",
    "Using the HN /newest page, count top {n} stories whose posting time is within {window} minutes from the first (newest) post.",
    "From the newest {n} HN stories, how many fall inside a {window}-minute burst window anchored at the newest post time?",
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
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(n=n, window=window),
            start_url="https://news.ycombinator.com/newest",
            variables={"story_count": n, "window_minutes": window},
            validation_info={
                "story_count": n,
                "window_minutes": window,
                "category_slug": "newest",
            },
            template_name=self.name,
            expected_steps=8,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Recent Burst Count):\n"
            f"- Top stories considered: {validation_info.get('story_count')}\n"
            f"- Time window: {validation_info.get('window_minutes')} minutes from newest post\n"
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

        stories, failure = get_category_stories(collected, "newest", min_count=n)
        if failure is not None:
            return failure
        stories = stories[:n]

        newest_ts = stories[0].get("time")
        if not isinstance(newest_ts, int):
            return GroundTruthResult.fail("Newest story missing unix timestamp")

        count = 0
        for story in stories:
            story_ts = story.get("time")
            if not isinstance(story_ts, int):
                return GroundTruthResult.fail("Story missing unix timestamp")
            delta_minutes = (newest_ts - story_ts) / 60.0
            if delta_minutes <= window:
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
