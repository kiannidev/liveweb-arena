"""Shared utilities for advanced Hacker News templates."""

from typing import Any, Dict, List, Optional, Tuple

from liveweb_arena.core.ground_truth_trigger import GroundTruthResult
from liveweb_arena.core.gt_collector import get_current_gt_collector


def get_collected_hn_data() -> Tuple[Optional[Dict[str, Dict[str, Any]]], Optional[GroundTruthResult]]:
    """Return collected API payload map for current evaluation."""
    gt_collector = get_current_gt_collector()
    if gt_collector is None:
        return None, GroundTruthResult.system_error("No GT collector")
    return gt_collector.get_collected_api_data(), None


def get_category_stories(
    collected: Dict[str, Dict[str, Any]],
    category_slug: str,
    min_count: int = 1,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[GroundTruthResult]]:
    """Extract ordered category stories from collected data."""
    key = f"hn_category:{category_slug}"
    category_data = collected.get(key)
    if not isinstance(category_data, dict):
        return None, GroundTruthResult.not_collected(
            f"Category data '{category_slug}' not collected. Visit /{category_slug}."
        )

    stories = category_data.get("stories")
    if not isinstance(stories, dict):
        return None, GroundTruthResult.fail(f"Malformed stories in category '{category_slug}'")

    result: List[Dict[str, Any]] = []
    for _, story in stories.items():
        if not isinstance(story, dict):
            continue
        rank = story.get("rank")
        if rank is None:
            continue
        result.append(story)

    result.sort(key=lambda s: s["rank"])
    if len(result) < min_count:
        return None, GroundTruthResult.not_collected(
            f"Need at least {min_count} stories in '{category_slug}', got {len(result)}."
        )
    return result, None


def get_item_story(
    collected: Dict[str, Dict[str, Any]],
    item_id: int,
) -> Tuple[Optional[Dict[str, Any]], Optional[GroundTruthResult]]:
    """Get item story data by item id from collected payload."""
    key = str(item_id)
    story = collected.get(key)
    if not isinstance(story, dict):
        return None, GroundTruthResult.not_collected(
            f"Item {item_id} not collected. Visit /item?id={item_id}."
        )
    return story, None


def get_user_data(
    collected: Dict[str, Dict[str, Any]],
    username: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[GroundTruthResult]]:
    """Get user payload by username."""
    key = f"user:{username}"
    payload = collected.get(key)
    if not isinstance(payload, dict):
        return None, GroundTruthResult.not_collected(
            f"User data for '{username}' not collected. Visit /user?id={username}."
        )
    user = payload.get("user")
    if not isinstance(user, dict):
        return None, GroundTruthResult.fail(f"Malformed user payload for '{username}'.")
    return user, None


def parse_iso_minutes(timestamp: Any) -> Optional[int]:
    """Parse basic ISO timestamp and return minutes from day start."""
    if not isinstance(timestamp, str) or "T" not in timestamp:
        return None
    time_part = timestamp.split("T", 1)[1]
    if ":" not in time_part:
        return None
    hour_s, minute_s = time_part.split(":", 1)
    try:
        hour = int(hour_s)
        minute = int(minute_s[:2])
    except ValueError:
        return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour * 60 + minute
