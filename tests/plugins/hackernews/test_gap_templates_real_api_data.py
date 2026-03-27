"""GT computation tests using real Hacker News API data snapshots.

Snapshots were fetched live on 2026-03-27 from:
- https://hacker-news.firebaseio.com/v0/newstories.json
- https://hacker-news.firebaseio.com/v0/item/<id>.json
- https://hacker-news.firebaseio.com/v0/user/<id>.json
- https://hn.algolia.com/api/v1/search_by_date

These tests validate that template GT logic computes concrete values using
real API response structure and field naming.
"""

import asyncio
from typing import Any, Dict

from liveweb_arena.core.gt_collector import set_current_gt_collector
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


class _DummyCollector:
    def __init__(self, data: Dict[str, Dict[str, Any]]):
        self._data = data

    def get_collected_api_data(self) -> Dict[str, Dict[str, Any]]:
        return self._data


def _run_gt(data: Dict[str, Dict[str, Any]], coro):
    set_current_gt_collector(_DummyCollector(data))
    try:
        return asyncio.run(coro)
    finally:
        set_current_gt_collector(None)


NEWEST_5_STORIES = {
    "47541556": {
        "id": 47541556,
        "rank": 1,
        "title": "OpenID AuthZen Authorization API 1.0 released",
        "by": "Tepix",
        "time": 1774612147,
        "score": 1,
        "descendants": 1,
    },
    "47541541": {
        "id": 47541541,
        "rank": 2,
        "title": "How to move from Prompt to Context Engineering (With demo code)",
        "by": "visopsys",
        "time": 1774612071,
        "score": 1,
        "descendants": 0,
    },
    "47541528": {
        "id": 47541528,
        "rank": 3,
        "title": "Crisp open source BA/PM framework for Claude Code(stop building the wrong thing)",
        "by": "mirkoradeka",
        "time": 1774611991,
        "score": 1,
        "descendants": 0,
    },
    "47541523": {
        "id": 47541523,
        "rank": 4,
        "title": "GLM-5.1 Released",
        "by": "sumitsrivastava",
        "time": 1774611963,
        "score": 1,
        "descendants": 0,
    },
    "47541521": {
        "id": 47541521,
        "rank": 5,
        "title": "Show HN: Agent-CI (Run GitHub Actions on your local machine.)",
        "by": "pistoriusp",
        "time": 1774611955,
        "score": 1,
        "descendants": 2,
    },
}

HN_SEARCH_PYTHON_PAGE0 = {
    "query": "python",
    "page": 0,
    "hits": [
        {
            "title": "Show HN: 10 Lines of Python to fix mangled copy-paste from Claude Code",
            "author": "collectedparts",
            "points": 1,
            "num_comments": 0,
        },
        {
            "title": "Telnyx v4.87.1 and v4.87.2 are compromised by TeamPCP",
            "author": "ramimac",
            "points": 2,
            "num_comments": 1,
        },
        {
            "title": "Show HN: Pyconject - Ditch messy YAML loading in Python with config injection",
            "author": "neolaw",
            "points": 1,
            "num_comments": 1,
        },
        {
            "title": "Mojo's Not (Yet) Python",
            "author": "birdculture",
            "points": 2,
            "num_comments": 0,
        },
        {
            "title": "Show HN: LLMBillingKit - measure net margin per LLM call with one line of Python",
            "author": "davidphan11",
            "points": 1,
            "num_comments": 1,
        },
    ],
}


def _collected_for_recent_burst() -> Dict[str, Dict[str, Any]]:
    return {"hn_category:newest": {"category": "newest", "stories": NEWEST_5_STORIES}}


def _collected_for_search() -> Dict[str, Dict[str, Any]]:
    return {"hn_search:python:0": HN_SEARCH_PYTHON_PAGE0}


def _collected_for_nested_comments() -> Dict[str, Dict[str, Any]]:
    return {
        "hn_category:newest": {
            "category": "newest",
            "stories": {
                "47540833": {
                    "id": 47540833,
                    "rank": 1,
                    "title": "Hold on to Your Hardware",
                    "by": "LucidLynx",
                }
            },
        },
        # Story with root comment
        "47540833": {"id": 47540833, "kids": [47541161]},
        # Root depth=1
        "47541161": {"id": 47541161, "kids": [47541519, 47541377, 47541263]},
        # Depth=2
        "47541519": {"id": 47541519, "kids": []},
        "47541377": {"id": 47541377, "kids": [47541427]},
        "47541263": {"id": 47541263, "kids": [47541473, 47541336, 47541494]},
        # Depth=3
        "47541427": {"id": 47541427, "kids": [47541578, 47541483]},
        "47541473": {"id": 47541473, "kids": []},
        "47541336": {"id": 47541336, "kids": []},
        "47541494": {"id": 47541494, "kids": [47541522]},
        # Depth=4
        "47541578": {"id": 47541578, "kids": []},
        "47541483": {"id": 47541483, "kids": []},
        "47541522": {"id": 47541522, "kids": [47541558, 47541548]},
        # Depth=5
        "47541558": {"id": 47541558, "kids": []},
        "47541548": {"id": 47541548, "kids": []},
    }


def _collected_for_user_metrics() -> Dict[str, Dict[str, Any]]:
    return {
        "hn_category:newest": {"category": "newest", "stories": NEWEST_5_STORIES},
        "user:Tepix": {
            "user": {
                "id": "Tepix",
                "karma": 13466,
                "created": 1376904746,
                "submitted": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        },
        "user:visopsys": {
            "user": {
                "id": "visopsys",
                "karma": 351,
                "created": 1321339868,
                "submitted": [1, 2, 3, 4, 5],
            }
        },
    }


def test_t110_recent_burst_with_real_snapshot():
    tmpl = HackerNewsRecentBurstCountTemplate()
    result = _run_gt(
        _collected_for_recent_burst(),
        tmpl.get_ground_truth(
            {
                "story_count": 5,
                "window_minutes": 3,
                "anchor_rank": 1,
                "include_equal": True,
            }
        ),
    )
    assert result.success is True
    assert result.value == "3"


def test_t111_nested_comment_nodes_with_real_snapshot():
    tmpl = HackerNewsCommentTreeFocusTemplate()
    result = _run_gt(
        _collected_for_nested_comments(),
        tmpl.get_ground_truth({"rank": 1, "min_depth": 3, "metric": "nodes"}),
    )
    # depth>=3 nodes: 47541427,47541473,47541336,47541494,47541578,47541483,47541522,47541558,47541548
    assert result.success is True
    assert result.value == "9"


def test_t112_hn_search_with_real_snapshot():
    tmpl = HackerNewsKeywordScanRankTemplate()
    result = _run_gt(
        _collected_for_search(),
        tmpl.get_ground_truth(
            {"query": "python", "rank": 2, "field": "author", "min_points": 2, "search_page": 0}
        ),
    )
    # Filtered by points>=2 gives authors: ramimac, birdculture
    assert result.success is True
    assert result.value == "birdculture"


def test_t113_user_metric_with_real_snapshot():
    tmpl = HackerNewsUserKarmaGapTemplate()
    result = _run_gt(
        _collected_for_user_metrics(),
        tmpl.get_ground_truth({"rank_a": 1, "rank_b": 2, "metric": "created_days"}),
    )
    assert result.success is True
    assert result.value == "643"
