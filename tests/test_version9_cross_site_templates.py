"""Registry, registration, and GT smoke tests for Version 9 cross-site templates (110–113)."""

import asyncio

import pytest

from liveweb_arena.core.gt_collector import GTCollector, set_current_gt_collector
from liveweb_arena.core.task_registry import TaskRegistry
from liveweb_arena.core.validators.base import get_template
from liveweb_arena.plugins import get_all_plugins
from liveweb_arena.plugins.arxiv.templates.category_infer_author_filter import ArxivCategoryInferAuthorFilterTemplate
from liveweb_arena.plugins.arxiv.templates.category_infer_title_substring import ArxivCategoryInferTitleSubstringTemplate
from liveweb_arena.plugins.arxiv.templates.variables import CATEGORIES
from liveweb_arena.plugins.base import SubTask
from liveweb_arena.plugins.openlibrary.templates.nested_work_title_substring import (
    OpenLibrarySubjectNestedWorkTitleTemplate,
)


@pytest.fixture
def mixed_collector():
    gt = GTCollector(
        subtasks=[
            SubTask(plugin_name="arxiv", intent="t", validation_info={}, answer_tag="a1"),
            SubTask(plugin_name="openlibrary", intent="t", validation_info={}, answer_tag="a2"),
        ]
    )
    set_current_gt_collector(gt)
    try:
        yield gt
    finally:
        set_current_gt_collector(None)


def run_async(coro):
    return asyncio.run(coro)


def test_version9_task_registry_mapping():
    assert TaskRegistry.TEMPLATES[110] == ("openmeteo", "openmeteo_daily_precip_peak_day")
    assert TaskRegistry.TEMPLATES[111] == ("openlibrary", "openlibrary_subject_nested_work_title")
    assert TaskRegistry.TEMPLATES[112] == ("arxiv", "arxiv_category_infer_title_substring")
    assert TaskRegistry.TEMPLATES[113] == ("arxiv", "arxiv_category_infer_author_filter")


def test_version9_templates_are_registered():
    get_all_plugins()
    for name in (
        "openmeteo_daily_precip_peak_day",
        "openlibrary_subject_nested_work_title",
        "arxiv_category_infer_title_substring",
        "arxiv_category_infer_author_filter",
    ):
        assert get_template(name) is not None, f"missing template {name!r}"


def test_arxiv_category_infer_questions_avoid_official_labels():
    """The active category's official display name must not appear verbatim in the question."""
    get_all_plugins()
    tmpl = ArxivCategoryInferTitleSubstringTemplate()
    for seed in range(120):
        gq = tmpl.generate(seed)
        vi = gq.validation_info or {}
        code = vi.get("category")
        cat = next(c for c in CATEGORIES if c.code == code)
        assert cat.name.lower() not in gq.question_text.lower(), (
            f"seed {seed}: question leaks official name for {code}"
        )


def test_arxiv_author_filter_questions_avoid_official_labels():
    get_all_plugins()
    tmpl = ArxivCategoryInferAuthorFilterTemplate()
    for seed in range(120):
        gq = tmpl.generate(seed)
        code = (gq.validation_info or {}).get("category")
        cat = next(c for c in CATEGORIES if c.code == code)
        assert cat.name.lower() not in gq.question_text.lower(), (
            f"seed {seed}: question leaks official name for {code}"
        )


def test_arxiv_title_substring_gt(mixed_collector):
    mixed_collector._merge_api_data(
        "https://arxiv.org/list/cs.LG/new",
        {
            "category": "cs.LG",
            "papers": {
                "1": {"rank": 1, "title": "Graph neural models", "authors": ["A"]},
                "2": {"rank": 2, "title": "Pure algebra", "authors": ["B"]},
                "3": {"rank": 3, "title": "Data-centric learning", "authors": ["C"]},
                "4": {"rank": 4, "title": "No match here", "authors": ["D"]},
                "5": {"rank": 5, "title": "Another graph paper", "authors": ["E"]},
            },
        },
    )
    result = run_async(
        ArxivCategoryInferTitleSubstringTemplate().get_ground_truth(
            {"category": "cs.LG", "top_n": 5, "needle": "graph"}
        )
    )
    assert result.success is True
    assert result.value == "2"


def test_arxiv_author_filter_gt(mixed_collector):
    mixed_collector._merge_api_data(
        "https://arxiv.org/list/cs.AI/new",
        {
            "category": "cs.AI",
            "papers": {
                "1": {"rank": 1, "title": "Solo", "authors": ["a"]},
                "2": {"rank": 2, "title": "Duo", "authors": ["a", "b"]},
                "3": {"rank": 3, "title": "Many", "authors": ["a", "b", "c", "d"]},
            },
        },
    )
    result = run_async(
        ArxivCategoryInferAuthorFilterTemplate().get_ground_truth(
            {"category": "cs.AI", "top_n": 3, "author_threshold": 2}
        )
    )
    assert result.success is True
    assert result.value == "1"


def test_openlibrary_nested_work_title_gt(mixed_collector):
    works = {
        "/works/OLA": {"key": "/works/OLA", "rank": 1, "title": "Alpha"},
        "/works/OLB": {"key": "/works/OLB", "rank": 2, "title": "Beta"},
    }
    mixed_collector._merge_api_data(
        "https://openlibrary.org/subjects/fantasy",
        {"works": works, "subject": "fantasy"},
    )
    mixed_collector._merge_api_data(
        "https://openlibrary.org/works/OLB",
        {"key": "/works/OLB", "title": "Night Watch and Goodnight Moon"},
    )
    result = run_async(
        OpenLibrarySubjectNestedWorkTitleTemplate().get_ground_truth(
            {"subject_slug": "fantasy", "rank": 2, "needle": "night"}
        )
    )
    assert result.success is True
    assert result.value == "2"
