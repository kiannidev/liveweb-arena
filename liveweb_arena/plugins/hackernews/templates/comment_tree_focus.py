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

from .common import (
    count_descendants_with_min_depth,
    get_category_stories,
    get_collected_hn_data,
    get_item_story,
)

RANK_CHOICES = list(range(1, 31))
DEPTH_CHOICES = [2, 3, 4, 5, 6]
METRIC_CHOICES = ["nodes", "leaf_nodes", "branch_nodes", "max_depth"]

PATTERNS = [
    "On HN /newest, open rank #{rank} story and compute '{metric}' for comments at depth >= {min_depth}.",
    "Using Hacker News newest, for story rank {rank}, return '{metric}' from descendants depth {min_depth}+.",
    "From newest rank {rank} story, traverse nested replies and report {metric} with depth threshold {min_depth}.",
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
        min_depth = rng.choice(DEPTH_CHOICES)
        metric = rng.choice(METRIC_CHOICES)
        pattern = rng.choice(PATTERNS)
        return GeneratedQuestion(
            question_text=pattern.format(rank=rank, min_depth=min_depth, metric=metric),
            start_url="https://news.ycombinator.com/newest",
            variables={"rank": rank, "min_depth": min_depth, "metric": metric},
            validation_info={"rank": rank, "min_depth": min_depth, "metric": metric, "category_slug": "newest"},
            template_name=self.name,
            expected_steps=12,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Comment Tree Focus):\n"
            f"- Target newest rank: {validation_info.get('rank')}\n"
            f"- Count descendants at depth >= {validation_info.get('min_depth')}\n"
            f"- Metric: {validation_info.get('metric')}\n"
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
        min_depth = int(validation_info.get("min_depth", 2))
        metric = str(validation_info.get("metric", "nodes"))
        total, failure = count_descendants_with_min_depth(collected, kids, min_depth=min_depth)
        if failure is not None:
            return failure
        if metric == "nodes":
            return GroundTruthResult.ok(str(total))

        # Re-traverse comment tree once to compute specialized metrics.
        seen = set()

        def _walk(comment_ids: list[int], depth: int) -> tuple[int, int, int]:
            node_count = 0
            leaf_count = 0
            branch_count = 0
            max_seen_depth = depth - 1
            for cid in comment_ids:
                if cid in seen:
                    continue
                seen.add(cid)
                payload, failure = get_item_story(collected, cid)
                if failure is not None:
                    return -1, -1, -1
                child_ids = payload.get("kids") or []
                if not isinstance(child_ids, list):
                    return -1, -1, -1
                qualifies = depth >= min_depth
                if qualifies:
                    node_count += 1
                    if len(child_ids) == 0:
                        leaf_count += 1
                    else:
                        branch_count += 1
                n, l, b = _walk([x for x in child_ids if isinstance(x, int)], depth + 1)
                if n < 0:
                    return -1, -1, -1
                node_count += n
                leaf_count += l
                branch_count += b
                max_seen_depth = max(max_seen_depth, depth)
            return node_count, leaf_count, branch_count

        _, leaf_count, branch_count = _walk([x for x in kids if isinstance(x, int)], 1)
        if leaf_count < 0:
            return GroundTruthResult.not_collected("Nested comment payload not fully collected")

        if metric == "leaf_nodes":
            return GroundTruthResult.ok(str(leaf_count))
        if metric == "branch_nodes":
            return GroundTruthResult.ok(str(branch_count))
        if metric == "max_depth":
            # Approximate max depth from story-level descendants + depth threshold floor.
            # This remains deterministic and requires nested traversal data collection.
            if total == 0:
                return GroundTruthResult.ok("0")
            # Recompute exact max depth.
            seen_depth = set()

            def _max_depth(comment_id: int, depth: int) -> int:
                if comment_id in seen_depth:
                    return depth
                seen_depth.add(comment_id)
                payload, failure = get_item_story(collected, comment_id)
                if failure is not None:
                    return depth
                child_ids = payload.get("kids") or []
                if not isinstance(child_ids, list) or len(child_ids) == 0:
                    return depth
                return max(_max_depth(c, depth + 1) for c in child_ids if isinstance(c, int))

            depth_val = 0
            for cid in kids:
                if isinstance(cid, int):
                    depth_val = max(depth_val, _max_depth(cid, 1))
            return GroundTruthResult.ok(str(depth_val))

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
