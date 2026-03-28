"""Which calendar day has the highest max precipitation probability — MEDIUM.

Reads Open-Meteo **daily** `precipitation_probability_max` for the first three
forecast days and picks today vs tomorrow vs day-after-tomorrow. Answers track
real forecast updates (time-sensitive in the sense of **calendar-relative**
risk peaks, distinct from hourly threshold counting on T99 and daylight math
on sunrise/sunset).

Effective variants: len(CITIES) * 3 patterns >= 510.
"""

import random
from typing import Any, Dict, List, Optional

from liveweb_arena.core.ground_truth_trigger import GroundTruthResult, TriggerConfig, UrlPatternTrigger
from liveweb_arena.core.gt_collector import GTSourceType
from liveweb_arena.core.validators.base import (
    GeneratedQuestion,
    QuestionTemplate,
    ValidationResult,
    register_template,
)

from .common import DOCS_HOME_URL, get_collected_location_data
from .variables import CITIES

DAY_LABELS: List[str] = ["today", "tomorrow", "the day after tomorrow"]

PATTERNS = [
    (
        "According to Open-Meteo's multi-day forecast for {city}, which day shows the highest "
        "**maximum daily precipitation probability** in the table—today, tomorrow, or the day after tomorrow? "
        "Reply with exactly one of those three phrases (lowercase)."
    ),
    (
        "On Open-Meteo for {city}, compare the **daily maximum precipitation probability** values for "
        "today, tomorrow, and the day after tomorrow. Which day is highest? Answer with exactly: "
        "today, tomorrow, or the day after tomorrow."
    ),
    (
        "Using Open-Meteo forecast data for {city}, identify which of the next three calendar days "
        "has the largest **precipitation probability maximum** in the daily section. Respond with only "
        "today, tomorrow, or the day after tomorrow."
    ),
]


@register_template("openmeteo_daily_precip_peak_day")
class OpenMeteoDailyPrecipPeakDayTemplate(QuestionTemplate):
    """Pick the calendar day (0–2) with highest daily max precip probability."""

    GT_SOURCE = GTSourceType.PAGE_ONLY

    def __init__(self):
        super().__init__("openmeteo_daily_precip_peak_day")

    def generate(self, seed: int, variant: Optional[int] = None) -> GeneratedQuestion:
        rng = random.Random(seed)
        city = rng.choice(CITIES)
        pattern = rng.choice(PATTERNS)
        question_text = pattern.format(city=city.display_name)
        return GeneratedQuestion(
            question_text=question_text,
            start_url=DOCS_HOME_URL,
            variables={"city": city.name, "coord_key": city.coord_key},
            validation_info={"city_name": city.name, "coord_key": city.coord_key},
            template_name=self.name,
            expected_steps=8,
        )

    def get_validation_rules(self, validation_info: Dict[str, Any]) -> str:
        city = validation_info.get("city_name", "")
        return f"""Task-Specific Rules (Open Meteo daily precip peak day):
- City: {city}
- Use daily maximum precipitation probability for the first three forecast days
- Answer must be exactly one of: today, tomorrow, the day after tomorrow (lowercase)
- Tie-break: if two days share the same maximum, choose the earlier day (today before tomorrow, etc.)
- Score 1.0: exact phrase match
- Score 0.0: otherwise"""

    async def get_ground_truth(self, validation_info: Dict[str, Any]) -> GroundTruthResult:
        coord_key = validation_info.get("coord_key", "")
        city_name = validation_info.get("city_name", "")
        data, failure = get_collected_location_data(coord_key, city_name)
        if failure is not None:
            return failure

        daily = data.get("daily")
        if not isinstance(daily, dict):
            return GroundTruthResult.fail("No daily data in API response")

        probs = daily.get("precipitation_probability_max")
        if not isinstance(probs, list) or len(probs) < 3:
            return GroundTruthResult.fail("Need three daily precipitation_probability_max values")

        parsed: List[float] = []
        for i, raw in enumerate(probs[:3]):
            if raw is None:
                return GroundTruthResult.fail(f"Null precipitation_probability_max at index {i}")
            try:
                parsed.append(float(raw))
            except (TypeError, ValueError):
                return GroundTruthResult.fail(f"Non-numeric precipitation_probability_max: {raw!r}")

        best_i = 0
        best_v = parsed[0]
        for i in range(1, 3):
            if parsed[i] > best_v:
                best_v = parsed[i]
                best_i = i

        return GroundTruthResult.ok(DAY_LABELS[best_i])

    async def validate_answer(self, answer: str, validation_info: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(
            score=0.0, is_correct=False, expected=None, actual=answer, details="Use LLM validation"
        )

    def get_ground_truth_trigger(self, validation_info: dict) -> TriggerConfig:
        return TriggerConfig(trigger=UrlPatternTrigger(domains=["open-meteo.com"]))

    @classmethod
    def get_cache_source(cls) -> str:
        return "openmeteo"

    def get_gt_source(self) -> GTSourceType:
        return self.GT_SOURCE
