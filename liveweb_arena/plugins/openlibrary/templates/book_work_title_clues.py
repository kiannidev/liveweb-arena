"""(clue, needle) for catalog titles; clue must not contain needle (case-insensitive)."""

from typing import List, Tuple

BOOK_TITLE_SUBSTRING_SPECS: List[Tuple[str, str]] = [
    ("Often associated with evening and absence of sunlight", "night"),
    ("Strong affection or deep attachment between characters", "love"),
    ("Armed conflict between groups or nations", "war"),
    ("Royal ruler of a realm in many fantasies", "king"),
    ("Luminous point in the night sky", "star"),
    ("Journey along a path or highway", "road"),
    ("Chronological progression or era", "time"),
    ("Missing or unable to be found", "lost"),
    ("Large domain ruled by a sovereign", "empire"),
    ("Female monarch in court intrigue tales", "queen"),
    ("Fire-breathing creature in mythic quests", "dragon"),
    ("Vessel crossing oceans in adventure yarns", "ship"),
    ("Truce after strife", "peace"),
    ("Crimson fluid in thrillers", "blood"),
    ("Precious metal sought in heists", "gold"),
    ("Hidden knowledge characters pursue", "secret"),
    ("Sleeping visions or aspirations", "dream"),
    ("Small community in pastoral settings", "village"),
    ("Stone barrier around castles", "wall"),
    ("Large body of salt water", "ocean"),
    ("Dense growth of trees", "forest"),
    ("Frozen precipitation in winter tales", "snow"),
    ("Burning brightness that destroys", "fire"),
    ("Person who investigates crimes", "detective"),
    ("Ceremony joining spouses", "wedding"),
    ("School for young wizards in popular series", "magic"),
    ("Underground burial chamber", "tomb"),
    ("Written agreement binding parties", "pact"),
    ("Young person coming of age", "child"),
    ("Season of harvest and falling leaves", "autumn"),
    ("Dwelling where families live", "house"),
    ("Sharp weapon for duels", "sword"),
    ("Pattern of heredity and kin", "bloodline"),
    ("Sphere of politics and power plays", "court"),
    ("Voyage across worlds", "journey"),
    ("Hex from folklore that binds its target", "curse"),
    ("Companion animal in quests", "wolf"),
    ("Sacred writing or prophecy", "bible"),
    ("Spectral figure haunting corridors", "ghost"),
    ("Instrument of flight for astronauts", "rocket"),
    ("Garden of temptation metaphor", "eden"),
    ("Retribution for a grave injustice", "revenge"),
    ("Clock ticking toward doom", "midnight"),
    ("Landmass ringed entirely by water", "island"),
    ("Platform where locomotives arrive", "station"),
    ("Disguise worn at Venetian celebrations", "mask"),
    ("Missive sealed with wax", "letter"),
    ("Tempest and thunder on the seas", "storm"),
    ("Circlet symbolizing monarchy", "crown"),
    ("Reflective glass revealing vanity", "mirror"),
    ("Hour hand device in parlour mysteries", "clock"),
]


def _validate_specs() -> None:
    for clue, needle in BOOK_TITLE_SUBSTRING_SPECS:
        if needle.lower() in clue.lower():
            raise ValueError(f"Clue leaks needle {needle!r}: {clue!r}")


_validate_specs()
