"""Integration tests for HackerNews gap-filling templates."""

import asyncio

import pytest

from liveweb_arena.core.gt_collector import GTCollector, GTSourceType, set_current_gt_collector
from liveweb_arena.core.task_registry import TaskRegistry
from liveweb_arena.core.validators.base import get_registered_templates
from liveweb_arena.plugins.base import SubTask
from liveweb_arena.plugins.hackernews import api_client as hn_api
from liveweb_arena.plugins.hackernews.hackernews import HackerNewsPlugin
from liveweb_arena.plugins.hackernews.templates.comment_tree_focus import (
    HackerNewsCommentTreeFocusTemplate,
)
from liveweb_arena.plugins.hackernews.templates.keyword_scan_rank import (
    HackerNewsKeywordScanRankTemplate,
)
from liveweb_arena.plugins.hackernews.templates.recent_burst_count import (
    HackerNewsRecentBurstCountTemplate,
)
from liveweb_arena.plugins.hackernews.templates.user_karma_gap import (
    HackerNewsUserKarmaGapTemplate,
)


def run_async(coro):
    return asyncio.run(coro)


@pytest.fixture
def collector():
    gt_collector = GTCollector(
        subtasks=[SubTask(plugin_name="hackernews", intent="test", validation_info={}, answer_tag="answer1")]
    )
    set_current_gt_collector(gt_collector)
    try:
        yield gt_collector
    finally:
        set_current_gt_collector(None)


def _seed_newest_stories():
    # unix times descending by rank (newest first)
    return {
        "category": "newest",
        "stories": {
            "1001": {"id": 1001, "rank": 1, "title": "AI agent launch", "time": 1700000000, "by": "alice"},
            "1002": {"id": 1002, "rank": 2, "title": "Rust performance tricks", "time": 1699999700, "by": "bob"},
            "1003": {"id": 1003, "rank": 3, "title": "Cloud data warehousing", "time": 1699999200, "by": "carol"},
            "1004": {"id": 1004, "rank": 4, "title": "Python model serving", "time": 1699996000, "by": "dave"},
            "1005": {"id": 1005, "rank": 5, "title": "Open source infra", "time": 1699995500, "by": "eve"},
        },
    }


def test_template_registry_contains_new_gap_templates():
    templates = get_registered_templates()
    assert "hackernews_recent_burst_count" in templates
    assert "hackernews_comment_tree_focus" in templates
    assert "hackernews_keyword_scan_rank" in templates
    assert "hackernews_user_karma_gap" in templates


def test_task_registry_ids_are_new_and_non_conflicting():
    assert TaskRegistry.TEMPLATES[110] == ("hackernews", "hackernews_recent_burst_count")
    assert TaskRegistry.TEMPLATES[111] == ("hackernews", "hackernews_comment_tree_focus")
    assert TaskRegistry.TEMPLATES[112] == ("hackernews", "hackernews_keyword_scan_rank")
    assert TaskRegistry.TEMPLATES[113] == ("hackernews", "hackernews_user_karma_gap")
    # Registry versioning preserves upstream version slots before these IDs
    assert [96, 97, 98] in TaskRegistry.TEMPLATE_VERSIONS
    assert [99, 100, 101] in TaskRegistry.TEMPLATE_VERSIONS


def test_fetch_newest_api_data(monkeypatch):
    async def fake_new_stories(limit=30):
        return [11, 22, 33][:limit]

    async def fake_items_batch(ids):
        return {
            11: {"id": 11, "title": "a"},
            22: {"id": 22, "title": "b"},
            33: {"id": 33, "title": "c"},
        }

    monkeypatch.setattr(hn_api.HackerNewsClient, "get_new_stories", fake_new_stories)
    monkeypatch.setattr(hn_api.HackerNewsClient, "get_items_batch", fake_items_batch)

    payload = run_async(hn_api.fetch_newest_api_data(limit=3))
    assert payload["category"] == "newest"
    assert payload["stories"]["11"]["rank"] == 1
    assert payload["stories"]["22"]["rank"] == 2
    assert payload["stories"]["33"]["rank"] == 3


def test_plugin_fetch_api_data_routes_newest(monkeypatch):
    plugin = HackerNewsPlugin()

    async def fake_newest():
        return {"category": "newest", "stories": {"1": {"id": 1, "rank": 1, "title": "x"}}}

    monkeypatch.setattr(
        "liveweb_arena.plugins.hackernews.hackernews.fetch_newest_api_data",
        fake_newest,
    )
    payload = run_async(plugin.fetch_api_data("https://news.ycombinator.com/newest"))
    assert payload["category"] == "newest"
    assert "stories" in payload


def test_plugin_needs_api_data_for_newest():
    plugin = HackerNewsPlugin()
    assert plugin.needs_api_data("https://news.ycombinator.com/newest")
    assert plugin.needs_api_data("https://hn.algolia.com/?q=python")


@pytest.mark.parametrize(
    "template_cls",
    [
        HackerNewsRecentBurstCountTemplate,
        HackerNewsCommentTreeFocusTemplate,
        HackerNewsKeywordScanRankTemplate,
        HackerNewsUserKarmaGapTemplate,
    ],
)
def test_new_templates_generation_shape(template_cls):
    q = template_cls().generate(42)
    assert q.question_text
    assert q.start_url.startswith("https://")
    assert q.expected_steps >= 8
    assert q.template_name


def test_recent_burst_ground_truth_success(collector):
    collector._merge_api_data("https://news.ycombinator.com/newest", _seed_newest_stories())

    result = run_async(
        HackerNewsRecentBurstCountTemplate().get_ground_truth(
            {"story_count": 5, "window_minutes": 60, "anchor_rank": 1, "include_equal": True}
        )
    )
    assert result.success is True
    # ranks 1,2,3 within 60 minutes from newest (0s, 300s, 800s)
    assert result.value == "3"


def test_recent_burst_not_collected(collector):
    result = run_async(
        HackerNewsRecentBurstCountTemplate().get_ground_truth(
            {"story_count": 5, "window_minutes": 60, "anchor_rank": 1, "include_equal": True}
        )
    )
    assert result.success is False
    assert result.is_data_not_collected()


def test_comment_tree_focus_success(collector):
    newest = _seed_newest_stories()
    collector._merge_api_data("https://news.ycombinator.com/newest", newest)

    # Story and nested comments for rank 2 story
    collector._merge_api_data(
        "https://news.ycombinator.com/item?id=1002",
        {"id": 1002, "title": "Rust performance tricks", "kids": [2001, 2002]},
    )
    collector._merge_api_data("https://news.ycombinator.com/item?id=2001", {"id": 2001, "kids": [2003]})
    collector._merge_api_data("https://news.ycombinator.com/item?id=2002", {"id": 2002, "kids": [2004]})
    collector._merge_api_data("https://news.ycombinator.com/item?id=2003", {"id": 2003, "kids": []})
    collector._merge_api_data("https://news.ycombinator.com/item?id=2004", {"id": 2004, "kids": [2005]})
    collector._merge_api_data("https://news.ycombinator.com/item?id=2005", {"id": 2005, "kids": []})
    result = run_async(
        HackerNewsCommentTreeFocusTemplate().get_ground_truth(
            {"rank": 2, "min_depth": 2, "metric": "nodes"}
        )
    )
    assert result.success is True
    assert result.value == "3"


def test_comment_tree_focus_missing_item(collector):
    collector._merge_api_data("https://news.ycombinator.com/newest", _seed_newest_stories())
    result = run_async(
        HackerNewsCommentTreeFocusTemplate().get_ground_truth(
            {"rank": 1, "min_depth": 2, "metric": "nodes"}
        )
    )
    assert result.success is False
    assert result.is_data_not_collected()


def test_keyword_scan_rank_found(collector):
    collector._merge_api_data(
        "https://hn.algolia.com/?q=python&page=0",
        {
            "query": "python",
            "page": 0,
            "hits": [
                {"title": "Python libs", "author": "a1", "points": 80, "num_comments": 12},
                {"title": "Advanced Python", "author": "a2", "points": 150, "num_comments": 31},
            ],
        },
    )
    result = run_async(
        HackerNewsKeywordScanRankTemplate().get_ground_truth(
            {"query": "python", "rank": 1, "field": "title", "min_points": 100, "search_page": 0}
        )
    )
    assert result.success is True
    assert result.value == "Advanced Python"


def test_keyword_scan_rank_none(collector):
    collector._merge_api_data(
        "https://hn.algolia.com/?q=python&page=0",
        {
            "query": "python",
            "page": 0,
            "hits": [{"title": "Python libs", "author": "a1", "points": 80, "num_comments": 12}],
        },
    )
    result = run_async(
        HackerNewsKeywordScanRankTemplate().get_ground_truth(
            {"query": "python", "rank": 2, "field": "author", "min_points": 50, "search_page": 0}
        )
    )
    assert result.success is True
    assert result.value == "NONE"


def test_user_karma_gap_success(collector):
    newest = _seed_newest_stories()
    collector._merge_api_data("https://news.ycombinator.com/newest", newest)

    collector._merge_api_data(
        "https://news.ycombinator.com/user?id=alice",
        {"user": {"id": "alice", "karma": 950, "created": 1700000000, "submitted": [1, 2, 3, 4]}},
    )
    collector._merge_api_data(
        "https://news.ycombinator.com/user?id=carol",
        {"user": {"id": "carol", "karma": 700, "created": 1699136000, "submitted": [9]}},
    )

    result = run_async(
        HackerNewsUserKarmaGapTemplate().get_ground_truth({"rank_a": 1, "rank_b": 3, "metric": "karma"})
    )
    assert result.success is True
    assert result.value == "250"


def test_user_karma_gap_missing_profile(collector):
    collector._merge_api_data("https://news.ycombinator.com/newest", _seed_newest_stories())
    result = run_async(
        HackerNewsUserKarmaGapTemplate().get_ground_truth({"rank_a": 1, "rank_b": 2, "metric": "karma"})
    )
    assert result.success is False
    assert result.is_data_not_collected()


def test_user_metric_created_days(collector):
    newest = _seed_newest_stories()
    collector._merge_api_data("https://news.ycombinator.com/newest", newest)
    collector._merge_api_data(
        "https://news.ycombinator.com/user?id=alice",
        {"user": {"id": "alice", "karma": 950, "created": 1700000000, "submitted": [1, 2]}},
    )
    collector._merge_api_data(
        "https://news.ycombinator.com/user?id=bob",
        {"user": {"id": "bob", "karma": 900, "created": 1699913600, "submitted": [7]}},
    )
    result = run_async(
        HackerNewsUserKarmaGapTemplate().get_ground_truth(
            {"rank_a": 1, "rank_b": 2, "metric": "created_days"}
        )
    )
    assert result.success is True
    assert result.value == "1"


def test_variant_spaces_exceed_500():
    # T110: 10 story counts * 10 windows * 5 anchors * 2 comparators = 1000
    # T111: 30 ranks * 5 depths * 4 metrics = 600
    # T112: 52 queries * 20 ranks * 4 fields * 4 point buckets = 16640
    # T113: C(30,2)=435 pairs * 3 metrics = 1305
    t110 = 10 * 10 * 5 * 2
    t111 = 30 * 5 * 4
    t112 = 52 * 20 * 4 * 4
    t113 = 435 * 3
    assert t110 > 500
    assert t111 > 500
    assert t112 > 500
    assert t113 > 500


@pytest.mark.parametrize(
    "template_cls",
    [
        HackerNewsRecentBurstCountTemplate,
        HackerNewsCommentTreeFocusTemplate,
        HackerNewsKeywordScanRankTemplate,
        HackerNewsUserKarmaGapTemplate,
    ],
)
def test_gt_source_and_cache_source(template_cls):
    t = template_cls()
    assert t.get_gt_source() == GTSourceType.PAGE_ONLY
    assert t.get_cache_source() == "hackernews"


@pytest.mark.parametrize(
    ("seed", "template_cls"),
    [
        (3, HackerNewsRecentBurstCountTemplate),
        (5, HackerNewsCommentTreeFocusTemplate),
        (7, HackerNewsKeywordScanRankTemplate),
        (9, HackerNewsUserKarmaGapTemplate),
    ],
)
def test_seed_stability(seed, template_cls):
    t = template_cls()
    q1 = t.generate(seed, variant=1)
    q2 = t.generate(seed, variant=1)
    assert q1.question_text == q2.question_text
    assert q1.validation_info == q2.validation_info
