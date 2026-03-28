"""Open Library subject-hub discovery (registry T111).

Prose describes the hub; no subject slug, path, or openlibrary.org URL appears in the
question text (CLAUDE.md §3). The agent navigates from the generic start URL."""

import random
from typing import Any, Dict, List, Optional, Tuple

from liveweb_arena.core.ground_truth_trigger import GroundTruthResult, TriggerConfig, UrlPatternTrigger
from liveweb_arena.core.gt_collector import GTSourceType, get_current_gt_collector
from .common import find_subject_payload
from liveweb_arena.core.validators.base import (
    GeneratedQuestion,
    QuestionTemplate,
    ValidationResult,
    register_template,
)

SUBJECT_SCENARIOS: List[Tuple[str, str]] = [
    ("science_fiction", "Hub for imagined futures, space travel, and tech not yet commonplace."),
    ("fantasy", "Hub where magic, mythical beings, and alternate worlds dominate."),
    ("mystery", "Hub for detectives, crimes, clues, and puzzle plots."),
    ("romance", "Hub where love stories and relationships drive the narrative."),
    ("horror", "Hub for fear, dread, and the uncanny."),
    ("thriller", "Hub for suspense, danger, and high stakes."),
    ("biography", "Hub for real life stories of notable people in book form."),
    ("history", "Hub for documented past events and civilizations."),
    ("philosophy", "Hub for ethics, knowledge, and abstract reasoning."),
    ("poetry", "Hub for verse and rhythmic literary language."),
    ("adventure", "Hub for exploration, quests, and perilous journeys."),
    ("children", "Hub aimed at young readers."),
    ("classic_literature", "Hub for widely studied older literary works."),
    ("drama", "Hub for plays and theatrical works as books."),
    ("psychology", "Hub for mind, behavior, and mental life in non-fiction."),
    ("crime", "Hub for lawbreaking, police, and criminal milieux in fiction."),
    ("humor", "Hub for comedy and light entertainment."),
    ("war", "Hub for armed conflict and military experience."),
    ("travel", "Hub for journeys and accounts of places."),
    ("art", "Hub for visual art and artists in books."),
    ("music", "Hub for composers, performance, and sound culture."),
    ("religion", "Hub for faith, spirituality, and sacred themes."),
    ("science_fiction", "Second hint: speculative societies unlike the present day."),
    ("fantasy", "Second hint: enchanted realms and heroic quests."),
    ("mystery", "Second hint: hidden culprits and investigative plots."),
    ("romance", "Second hint: courtship and emotional arcs as core."),
    ("history", "Second hint: chronicles of empires and recorded eras."),
    ("thriller", "Second hint: conspiracies and races against time."),
    ("horror", "Second hint: supernatural threat and survival."),
    ("philosophy", "Second hint: arguments about what we should believe or do."),
]

TOP_N = [6, 8, 10, 12, 14]
EDITION_FLOORS = [800, 1200, 1600, 2000, 2500]

PATTERNS = [
    (
        "Open Library groups works into topical hubs. Find the hub best matching: \"{hint}\". "
        "Among the first {n} works on that hub page, how many list strictly more than {floor} editions?"
    ),
    (
        "On Open Library, locate the subject hub aligned with: \"{hint}\". "
        "In the first {n} works shown, count how many edition counts exceed {floor}."
    ),
    (
        "Using Open Library subject pages, open the hub described by: \"{hint}\". "
        "Of the initial {n} works, how many show more than {floor} editions?"
    ),
]


@register_template("openlibrary_subject_hub_infer")
class OpenLibrarySubjectHubInferTemplate(QuestionTemplate):
    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("openlibrary_subject_hub_infer")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        slug, hint = rng.choice(SUBJECT_SCENARIOS)
        n = rng.choice(TOP_N)
        floor = rng.choice(EDITION_FLOORS)
        pattern = rng.choice(PATTERNS)
        question_text = pattern.format(hint=hint, n=n, floor=floor)
        return GeneratedQuestion(
            question_text=question_text,
            start_url="https://openlibrary.org",
            variables={"subject_slug": slug, "top_n": n, "edition_floor": floor},
            validation_info={"subject_slug": slug, "top_n": n, "edition_floor": floor},
            template_name=self.name,
            expected_steps=14,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        return (
            "Task-Specific Rules (Open Library Subject Hub Infer):\n"
            "- Questions must not paste subject URLs; navigation starts from the Open Library home page.\n"
            f"- Subject slug (validator): {validation_info.get('subject_slug')}\n"
            f"- Top works: {validation_info.get('top_n')}\n"
            f"- Edition floor: {validation_info.get('edition_floor')}\n"
            "- Score 1.0: exact count\n"
            "- Score 0.0: otherwise"
        )

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        gt_collector = get_current_gt_collector()
        if gt_collector is None:
            return GroundTruthResult.system_error("No GT collector available")
        slug = str(validation_info.get("subject_slug", ""))
        n = int(validation_info.get("top_n", 10))
        floor = int(validation_info.get("edition_floor", 1000))

        payload = find_subject_payload(gt_collector.get_collected_api_data(), slug)
        if payload is None:
            return GroundTruthResult.not_collected(
                f"Subject hub data for '{slug}' not collected. Visit the matching subjects page."
            )

        works = payload.get("works")
        if not isinstance(works, dict):
            return GroundTruthResult.fail("Malformed works on subject payload")

        ordered = sorted(works.values(), key=lambda w: w.get("rank", 0))
        ordered = [w for w in ordered if isinstance(w, dict)]
        if len(ordered) < n:
            return GroundTruthResult.not_collected(
                f"Need at least {n} works on subject page, have {len(ordered)}."
            )

        count = 0
        for w in ordered[:n]:
            ec = w.get("edition_count")
            if not isinstance(ec, (int, float)):
                return GroundTruthResult.fail("Work missing numeric edition_count")
            if ec > floor:
                count += 1
        return GroundTruthResult.ok(str(count))

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation")

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["openlibrary.org"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "openlibrary"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
