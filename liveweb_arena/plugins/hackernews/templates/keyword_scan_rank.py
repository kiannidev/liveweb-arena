"""Search-driven interaction template using HN Algolia search."""

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

from .common import get_collected_hn_data

QUERIES = [
    "ai", "agent", "llm", "open source", "python", "javascript", "rust", "golang",
    "database", "kubernetes", "linux", "performance", "security", "compiler",
    "startup", "postgres", "cloud", "gpu", "distributed systems", "api",
    "privacy", "benchmark", "webassembly", "vector database", "observability",
    "monitoring", "network", "cache", "latency", "sqlite", "git", "docker",
    "tensorflow", "pytorch", "machine learning", "deep learning", "robotics",
    "sre", "frontend", "backend", "http", "kernel", "browser", "css", "typescript",
    "java", "cpp", "mobile", "design", "product", "analytics", "search",
]
RESULT_RANKS = list(range(1, 21))
RESULT_FIELDS = ["title", "author", "points", "comments"]
POINT_BUCKETS = [0, 1, 2, 3]

PATTERNS = [
    "Use Hacker News search for '{query}'. Considering only results with at least {min_points} points, for rank #{rank} return the {field}.",
    "On HN search page with query '{query}', after filtering to >= {min_points} points, what is the {field} of the #{rank} result?",
    "Search HN for '{query}', keep hits with points >= {min_points}, inspect result {rank}, and answer with its {field}.",
]


@register_template("hackernews_keyword_scan_rank")
class HackerNewsKeywordScanRankTemplate(QuestionTemplate):
    """Query HN search and retrieve a specific field from a ranked hit."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("hackernews_keyword_scan_rank")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        query = rng.choice(QUERIES)
        rank = rng.choice(RESULT_RANKS)
        field = rng.choice(RESULT_FIELDS)
        min_points = rng.choice(POINT_BUCKETS)
        pattern = rng.choice(PATTERNS)
        search_url = f"https://hn.algolia.com/?q={query.replace(' ', '+')}&sort=byDate&prefix=true&page=0"
        return GeneratedQuestion(
            question_text=pattern.format(query=query, rank=rank, field=field, min_points=min_points),
            start_url=search_url,
            variables={"query": query, "rank": rank, "field": field, "min_points": min_points},
            validation_info={
                "query": query,
                "rank": rank,
                "field": field,
                "min_points": min_points,
                "search_page": 0,
            },
            template_name=self.name,
            expected_steps=8,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (HN Search Field):\n"
            f"- Query: {validation_info.get('query')}\n"
            f"- Target rank: {validation_info.get('rank')}\n"
            f"- Requested field: {validation_info.get('field')}\n"
            f"- Points floor applied in GT filtering: >= {validation_info.get('min_points')}\n"
            "- Score 1.0: exact expected value\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        collected, failure = get_collected_hn_data()
        if failure is not None:
            return failure
        query = str(validation_info.get("query", "")).strip()
        field = str(validation_info.get("field", "title")).strip().lower()
        rank = int(validation_info.get("rank", 1))
        min_points = int(validation_info.get("min_points", 0))
        key = f"hn_search:{query.lower()}:{int(validation_info.get('search_page', 0))}"

        payload = collected.get(key)
        if not isinstance(payload, dict):
            return GroundTruthResult.not_collected(
                f"Search data for query '{query}' not collected. Visit hn.algolia.com search page."
            )

        hits = payload.get("hits")
        if not isinstance(hits, list):
            return GroundTruthResult.fail("Malformed Algolia search payload: missing hits list")

        filtered_hits = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            points = hit.get("points")
            if not isinstance(points, int):
                points = 0
            if points >= min_points:
                filtered_hits.append(hit)

        if rank < 1 or rank > len(filtered_hits):
            return GroundTruthResult.ok("NONE")

        target = filtered_hits[rank - 1]
        if field == "title":
            value = target.get("title")
            return GroundTruthResult.ok(str(value or ""))
        if field == "author":
            value = target.get("author")
            return GroundTruthResult.ok(str(value or ""))
        if field == "points":
            value = target.get("points")
            if isinstance(value, int):
                return GroundTruthResult.ok(str(value))
            return GroundTruthResult.fail("Missing points in target hit")
        if field == "comments":
            value = target.get("num_comments")
            if isinstance(value, int):
                return GroundTruthResult.ok(str(value))
            return GroundTruthResult.fail("Missing num_comments in target hit")
        return GroundTruthResult.fail(f"Unsupported field '{field}'")

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["news.ycombinator.com", "hn.algolia.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "hackernews"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
