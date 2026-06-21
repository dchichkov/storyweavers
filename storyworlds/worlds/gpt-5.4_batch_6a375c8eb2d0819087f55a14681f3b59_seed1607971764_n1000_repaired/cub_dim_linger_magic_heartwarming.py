#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py
===============================================================

A standalone story world about a little cub, a magical flower, and the warm,
patient help that teaches careful noticing. The story always begins with a cub
trying to prepare a glowing welcome for someone they love. When the flower goes
dim, the cub's first quick fix is not enough. A grown-up helps the cub notice
what the flower truly needs, and together they use the right gentle magic.

The exact story varies across:
- where the flower is kept
- which flower it is
- what kind of trouble it is in
- which caring spell is used
- which helper creature joins in
- whether the flower is ready before the homecoming or opens a moment later

Run it
------
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --place doorstep --plant moonbell --need thirsty --care moonwater
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --plant embercup --need shy
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/cub_dim_linger_magic_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    afford_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    bloom_word: str
    glow_word: str
    allowed_needs: set[str] = field(default_factory=set)
    resilience: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Need:
    id: str
    symptom: str
    inner_state: str
    fix_care: str
    required_helper: str
    severity: int
    mistake_line: str
    recovery_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Care:
    id: str
    label: str
    gerund: str
    helper: str
    power: int
    action_text: str
    lesson_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    arrive_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str = "window_nook"
    plant: str = "moonbell"
    need: str = "thirsty"
    care: str = "moonwater"
    cub_name: str = "Nori"
    cub_type: str = "girl"
    elder_type: str = "grandmother"
    returning_type: str = "mother"
    delay: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def remember(self, fact: str) -> None:
        self.history.append(fact)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "window_nook": Place(
        id="window_nook",
        label="window nook",
        phrase="in the round window nook of the den",
        afford_helpers={"dew_motes", "fireflies"},
        tags={"window", "night"},
    ),
    "hearthside": Place(
        id="hearthside",
        label="hearthside stool",
        phrase="on a small stool by the hearth",
        afford_helpers={"ember_moths", "fireflies"},
        tags={"hearth", "warmth"},
    ),
    "doorstep": Place(
        id="doorstep",
        label="doorstep shelf",
        phrase="on the little shelf beside the burrow door",
        afford_helpers={"dew_motes", "ember_moths", "fireflies"},
        tags={"door", "home"},
    ),
}

PLANTS = {
    "moonbell": Plant(
        id="moonbell",
        label="moonbell",
        phrase="a moonbell in a blue clay pot",
        bloom_word="silver bell",
        glow_word="pearly",
        allowed_needs={"thirsty", "shy"},
        resilience=1,
        tags={"flower", "moonbell"},
    ),
    "embercup": Plant(
        id="embercup",
        label="embercup",
        phrase="an embercup in a striped pot",
        bloom_word="tiny warm cup",
        glow_word="amber",
        allowed_needs={"chilly", "thirsty"},
        resilience=2,
        tags={"flower", "embercup"},
    ),
    "lanternbloom": Plant(
        id="lanternbloom",
        label="lanternbloom",
        phrase="a lanternbloom in a mossy pot",
        bloom_word="round lantern blossom",
        glow_word="golden",
        allowed_needs={"chilly", "shy"},
        resilience=1,
        tags={"flower", "lanternbloom"},
    ),
}

NEEDS = {
    "thirsty": Need(
        id="thirsty",
        symptom="Its petals had tipped inward, and the light inside looked small and sippy, as if the flower had been trying to drink the evening.",
        inner_state="thirsty",
        fix_care="moonwater",
        required_helper="dew_motes",
        severity=1,
        mistake_line="A bright snap of quick magic only made the poor flower blink and droop lower.",
        recovery_line="When the first cool drops touched the soil, the stem gave a tiny relieved shiver.",
        tags={"water", "care"},
    ),
    "chilly": Need(
        id="chilly",
        symptom="Its leaves had curled around the stem, and its glow had gone thin, like a blanket pulled too tight on a cold night.",
        inner_state="chilly",
        fix_care="warming_hum",
        required_helper="ember_moths",
        severity=2,
        mistake_line="A sharp sparkle spell danced on the petals for a second, but it did not reach the cold gathered deep inside the stem.",
        recovery_line="As the warm humming settled around the pot, the leaves loosened the way small paws loosen near a fire.",
        tags={"warmth", "care"},
    ),
    "shy": Need(
        id="shy",
        symptom="The bud was closed tight even though evening had come, as if the flower had heard too much hurrying and wanted one quiet friend before opening.",
        inner_state="shy",
        fix_care="welcome_whisper",
        required_helper="fireflies",
        severity=2,
        mistake_line="A fast little shine spell made the pot glitter, but the bud tucked itself in even more.",
        recovery_line="When the soft whispers circled the pot, the bud stopped hiding and listened.",
        tags={"feelings", "care"},
    ),
}

CARES = {
    "moonwater": Care(
        id="moonwater",
        label="moonwater",
        gerund="pouring moonwater",
        helper="dew_motes",
        power=2,
        action_text="cupped the floating dew motes and tipped their silver drops into the soil",
        lesson_text="Some magic likes to be given as a drink, not as a flash.",
        qa_text="They used moonwater, letting cool silver drops sink into the soil.",
        tags={"water", "magic"},
    ),
    "warming_hum": Care(
        id="warming_hum",
        label="warming hum",
        gerund="humming a warming charm",
        helper="ember_moths",
        power=2,
        action_text="hummed low and steady while ember moths drifted around the pot like tiny coals with wings",
        lesson_text="Some magic opens only when it is warmed slowly.",
        qa_text="They used a warming hum, and ember moths carried the gentle heat around the plant.",
        tags={"warmth", "magic"},
    ),
    "welcome_whisper": Care(
        id="welcome_whisper",
        label="welcome whisper",
        gerund="whispering a welcome charm",
        helper="fireflies",
        power=2,
        action_text="leaned close and whispered a welcome while a ring of fireflies bobbed around the bud",
        lesson_text="Some magic is shy and answers kindness better than glitter.",
        qa_text="They used a welcome whisper, and the fireflies made a soft friendly ring around the bud.",
        tags={"friendship", "magic"},
    ),
}

HELPERS = {
    "dew_motes": Helper(
        id="dew_motes",
        label="dew motes",
        phrase="a swirl of dew motes",
        arrive_text="From the cool window, dew motes drifted in like tiny floating beads of silver water.",
        tags={"water", "magic"},
    ),
    "ember_moths": Helper(
        id="ember_moths",
        label="ember moths",
        phrase="three ember moths",
        arrive_text="From the hearth-shadow, ember moths lifted into the air, glowing as softly as sleepy coals.",
        tags={"warmth", "magic"},
    ),
    "fireflies": Helper(
        id="fireflies",
        label="fireflies",
        phrase="a ring of fireflies",
        arrive_text="Outside the door, a few patient fireflies blinked on and gathered as if they had been waiting to help.",
        tags={"friendship", "magic"},
    ),
}

GIRL_NAMES = ["Nori", "Mina", "Tala", "Pip", "Luma", "Bree", "Ivy", "Suri"]
BOY_NAMES = ["Milo", "Tobin", "Ash", "Rook", "Finn", "Oren", "Bram", "Pico"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]
RETURNS = ["mother", "father", "grandmother", "grandfather"]


def care_matches(need_id: str, care_id: str) -> bool:
    return need_id in NEEDS and care_id in CARES and NEEDS[need_id].fix_care == care_id


def helper_available(place_id: str, care_id: str) -> bool:
    if place_id not in PLACES or care_id not in CARES:
        return False
    return CARES[care_id].helper in PLACES[place_id].afford_helpers


def plant_allows(plant_id: str, need_id: str) -> bool:
    if plant_id not in PLANTS or need_id not in NEEDS:
        return False
    return need_id in PLANTS[plant_id].allowed_needs


def valid_combo(place_id: str, plant_id: str, need_id: str, care_id: str) -> bool:
    return (
        place_id in PLACES
        and plant_id in PLANTS
        and need_id in NEEDS
        and care_id in CARES
        and care_matches(need_id, care_id)
        and helper_available(place_id, care_id)
        and plant_allows(plant_id, need_id)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for plant_id in PLANTS:
            for need_id in NEEDS:
                for care_id in CARES:
                    if valid_combo(place_id, plant_id, need_id, care_id):
                        combos.append((place_id, plant_id, need_id, care_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    plant = PLANTS[params.plant]
    need = NEEDS[params.need]
    care = CARES[params.care]
    if care.power + plant.resilience > need.severity + params.delay:
        return "ready_before_return"
    return "opens_in_returning_hands"


def explain_invalid(place_id: str, plant_id: str, need_id: str, care_id: str) -> str:
    if plant_id in PLANTS and need_id in NEEDS and need_id not in PLANTS[plant_id].allowed_needs:
        return (
            f"(No story: {PLANTS[plant_id].label} is not the sort of flower that turns "
            f"{NEEDS[need_id].inner_state} in this world. Pick a need that fits the flower.)"
        )
    if need_id in NEEDS and care_id in CARES and NEEDS[need_id].fix_care != care_id:
        return (
            f"(No story: a {NEEDS[need_id].inner_state} flower would not be helped by "
            f"{CARES[care_id].label}. This storyworld only allows caring magic that truly matches the need.)"
        )
    if place_id in PLACES and care_id in CARES and CARES[care_id].helper not in PLACES[place_id].afford_helpers:
        return (
            f"(No story: {PLACES[place_id].label} does not have the helper needed for "
            f"{CARES[care_id].label}. Choose a place where that gentle magic can happen.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def introduce(world: World, cub: Entity, elder: Entity, returning: Entity, place: Place, plant: Plant) -> None:
    cub.memes["love"] += 1
    world.say(
        f"In the evening, {cub.id} set {plant.phrase} {place.phrase}. "
        f"The den was cub-dim, the soft kind of dim that made the lamplight look sleepy and kind."
    )
    world.say(
        f"{cub.id} wanted the {plant.label} to glow for {returning.title_word} when {returning.pronoun()} came home, "
        f"so {cub.pronoun()} patted the pot and whispered, \"Be beautiful when {returning.pronoun()} comes in.\""
    )
    world.say(
        f"{elder.title_word.capitalize()} was nearby, folding a blanket and watching with a warm little smile."
    )
    world.remember("setup_welcome")


def observe_problem(world: World, cub: Entity, plant_ent: Entity, need: Need, returning: Entity) -> None:
    cub.memes["worry"] += 1
    plant_ent.meters["glow"] = 0.4
    plant_ent.meters["droop"] = 1.0
    world.say(
        f"But when {cub.id} leaned close, {need.symptom}"
    )
    world.say(
        f"{cub.id}'s ears drooped. \"Oh no,\" {cub.pronoun()} said. "
        f"\"It won't be ready before {returning.title_word} gets back.\""
    )
    world.remember("noticed_problem")


def quick_fix(world: World, cub: Entity, plant_ent: Entity, need: Need) -> None:
    cub.memes["impatience"] += 1
    plant_ent.meters["droop"] += 0.5
    world.say(
        f"{cub.id} tapped one paw in the air and tried a quick sparkle spell. {need.mistake_line}"
    )
    world.remember("quick_fix_failed")


def elder_notices(world: World, elder: Entity, cub: Entity, need: Need) -> None:
    elder.memes["care"] += 1
    cub.memes["trust"] += 1
    world.say(
        f"{elder.title_word.capitalize()} came and knelt beside {cub.id}. "
        f"\"Little one,\" {elder.pronoun()} said softly, \"that flower is not being difficult. It is telling us it feels {need.inner_state}.\""
    )
    world.remember("elder_explains")


def gather_helper(world: World, helper_ent: Entity, helper: Helper) -> None:
    helper_ent.meters["present"] = 1.0
    world.say(helper.arrive_text)
    world.remember(f"helper_{helper.id}")


def apply_care(world: World, cub: Entity, elder: Entity, plant_ent: Entity, need: Need, care: Care) -> None:
    plant_ent.meters["droop"] = max(0.0, plant_ent.meters["droop"] - 1.0)
    plant_ent.meters["glow"] += 1.0
    cub.memes["hope"] += 1
    world.say(
        f"Together, {elder.title_word} and {cub.id} {care.action_text}. {need.recovery_line}"
    )
    world.say(
        f"\"{care.lesson_text}\" said {elder.title_word}."
    )
    world.remember(f"care_{care.id}")


def linger_or_wait(world: World, cub: Entity, delay: int) -> None:
    if delay <= 0:
        cub.memes["patience"] += 1
        world.say(
            f"{cub.id} sat very still after that. Even the quiet seemed to help."
        )
        world.remember("waited_calmly")
        return
    cub.memes["patience"] += 1
    world.say(
        f"For a little while, {cub.id} could not help but linger beside the pot, watching for every tiny change and holding {cub.pronoun('possessive')} breath between blinks."
    )
    world.remember("lingered_beside_pot")


def homecoming_ready(world: World, cub: Entity, returning: Entity, plant: Plant, plant_ent: Entity) -> None:
    plant_ent.meters["bloom"] = 1.0
    cub.memes["joy"] += 1
    cub.memes["worry"] = 0.0
    world.say(
        f"Before the latch lifted, the {plant.label} opened into a {plant.bloom_word}, and a {plant.glow_word} light filled the doorway shelf."
    )
    world.say(
        f"When {returning.title_word} came in, {cub.id} pointed with both paws. "
        f"\"It waited for you,\" {cub.pronoun()} said."
    )
    world.say(
        f"{returning.title_word.capitalize()} gathered {cub.id} close and looked at the shining flower. "
        f"\"You didn't just make it bright,\" {returning.pronoun()} said. \"You helped it feel better.\""
    )
    world.remember("bloomed_before_return")


def homecoming_late(world: World, cub: Entity, elder: Entity, returning: Entity, plant: Plant, plant_ent: Entity) -> None:
    plant_ent.meters["bloom"] = 1.0
    cub.memes["joy"] += 1
    cub.memes["worry"] = 0.0
    world.say(
        f"The door opened before the flower had quite finished. {returning.title_word.capitalize()} stepped in quietly, saw the circle of care around the pot, and set down {returning.pronoun('possessive')} satchel without a word."
    )
    world.say(
        f"Then the {plant.label} gave one last soft gleam and opened into a {plant.bloom_word} right in {returning.title_word}'s hands."
    )
    world.say(
        f"{cub.id} looked up in surprise, and {returning.title_word} kissed the top of {cub.pronoun('possessive')} head. "
        f"\"Good things can take a minute,\" {returning.pronoun()} said. \"I love coming home to patient magic.\""
    )
    world.say(
        f"{elder.title_word.capitalize()} laughed quietly, and the sweet glow seemed to linger in everyone's fur even after coats and baskets were put away."
    )
    world.remember("bloomed_in_returning_hands")


def closing_image(world: World, cub: Entity, elder: Entity, returning: Entity, plant: Plant) -> None:
    cub.memes["love"] += 1
    world.say(
        f"That night, the little home felt warmer than before. The {plant.label}'s light rested on {cub.id}, {elder.title_word}, and {returning.title_word} together, and the whole den looked as if kindness itself had learned a bit of magic."
    )
    world.remember("closing_image")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    plant = PLANTS[params.plant]
    need = NEEDS[params.need]
    care = CARES[params.care]
    helper = HELPERS[care.helper]

    world = World()
    cub = world.add(Entity(id=params.cub_name, kind="character", type=params.cub_type, label=params.cub_name))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder_type, label="the elder"))
    returning = world.add(Entity(id="Returning", kind="character", type=params.returning_type, label="the returning loved one"))
    plant_ent = world.add(Entity(id="Plant", kind="thing", type="plant", label=plant.label, attrs={"place": place.id}))
    helper_ent = world.add(Entity(id="Helper", kind="thing", type="helper", label=helper.label))

    cub.memes["hope"] = 0.0
    cub.memes["worry"] = 0.0
    cub.memes["trust"] = 0.0
    cub.memes["patience"] = 0.0
    cub.memes["joy"] = 0.0
    plant_ent.meters["glow"] = 1.0
    plant_ent.meters["droop"] = 0.0
    plant_ent.meters["bloom"] = 0.0
    helper_ent.meters["present"] = 0.0

    world.facts.update(
        place=place,
        plant_cfg=plant,
        need_cfg=need,
        care_cfg=care,
        helper_cfg=helper,
        cub=cub,
        elder=elder,
        returning=returning,
        plant=plant_ent,
        helper=helper_ent,
        delay=params.delay,
        outcome=outcome_of(params),
    )

    introduce(world, cub, elder, returning, place, plant)
    world.para()
    observe_problem(world, cub, plant_ent, need, returning)
    quick_fix(world, cub, plant_ent, need)
    elder_notices(world, elder, cub, need)
    world.para()
    gather_helper(world, helper_ent, helper)
    apply_care(world, cub, elder, plant_ent, need, care)
    linger_or_wait(world, cub, params.delay)
    world.para()

    if world.facts["outcome"] == "ready_before_return":
        homecoming_ready(world, cub, returning, plant, plant_ent)
    else:
        homecoming_late(world, cub, elder, returning, plant, plant_ent)

    world.para()
    closing_image(world, cub, elder, returning, plant)
    return world


def generation_prompts(world: World) -> list[str]:
    cub = world.facts["cub"]
    plant = world.facts["plant_cfg"]
    need = world.facts["need_cfg"]
    returning = world.facts["returning"]
    return [
        'Write a heartwarming magic story for a 3-to-5-year-old that includes the words "cub-dim" and "linger".',
        f"Tell a cozy story where a little cub named {cub.id} tries to make a {plant.label} glow for {returning.title_word}, but first has to learn what a {need.inner_state} flower truly needs.",
        f"Write a gentle bedtime-style story in which magic works best when someone slows down, notices carefully, and cares for a dim flower instead of forcing it to shine.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    cub = world.facts["cub"]
    elder = world.facts["elder"]
    returning = world.facts["returning"]
    plant = world.facts["plant_cfg"]
    need = world.facts["need_cfg"]
    care = world.facts["care_cfg"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {cub.id}, a little cub who wanted to welcome {returning.title_word} home with a glowing {plant.label}. {elder.title_word.capitalize()} helped when the flower went dim."
        ),
        (
            f"Why did {cub.id} feel worried?",
            f"{cub.id} saw that the {plant.label} was looking {need.inner_state} and feared it would not be ready in time. The flower's dim glow made {cub.pronoun('object')} worry that the welcome surprise might fail."
        ),
        (
            f"What mistake did {cub.id} make first?",
            f"{cub.id} tried a quick sparkle spell because {cub.pronoun()} wanted the flower bright right away. That did not help, because the problem was not a lack of glitter but the flower's real need."
        ),
        (
            f"How did {elder.title_word} help the flower?",
            f"{elder.title_word.capitalize()} helped by noticing what the flower was truly feeling and then using the right gentle magic. {care.qa_text} That worked because the care matched the flower's real trouble."
        ),
    ]
    if outcome == "ready_before_return":
        qa.append(
            (
                "What happened when the loved one came home?",
                f"The flower had already opened before {returning.title_word} stepped in, so the welcome was waiting at the door. {returning.title_word.capitalize()} saw that {cub.id} had cared for the flower instead of just trying to make it flashy."
            )
        )
    else:
        qa.append(
            (
                "Was the flower ready before the loved one came home?",
                f"No. The door opened while they were still waiting, but the ending was still happy because the flower opened in {returning.title_word}'s hands a moment later. That showed {cub.id} that patient magic can still become a lovely welcome."
            )
        )
    qa.append(
        (
            "What did the story teach?",
            f"It taught that kind attention matters more than rushing. In this story, magic worked when {cub.id} slowed down, accepted help, and cared for what the flower truly needed."
        )
    )
    return qa


KNOWLEDGE = {
    "water": [
        (
            "Why do thirsty plants need water?",
            "Plants need water to keep their stems, leaves, and petals full and strong. When they get enough to drink, they can lift themselves up and grow."
        )
    ],
    "warmth": [
        (
            "Why can warmth help a chilled plant or creature?",
            "Gentle warmth helps cold things relax and move more easily again. It is the slow kind of help that wakes them up without scaring them."
        )
    ],
    "friendship": [
        (
            "Why might a shy creature like quiet company?",
            "Quiet company feels safe because it does not push or startle. When something shy feels welcome, it is easier for it to open up."
        )
    ],
    "magic": [
        (
            "What is gentle magic?",
            "Gentle magic is magic used to help, comfort, or care for someone or something. In stories like this one, it works best when it matches the real need."
        )
    ],
    "flower": [
        (
            "Why do flowers sometimes open slowly?",
            "Flowers can open slowly because they respond to light, warmth, water, and time. Some blossoms simply need the right conditions and a little patience."
        )
    ],
    "home": [
        (
            "Why does a welcome at home feel special?",
            "A welcome at home feels special because it tells someone they were missed and loved. Even a small light or gift can make coming home feel warm."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "flower", "water", "warmth", "friendship", "home"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"magic", "flower", "home"}
    tags |= set(world.facts["need_cfg"].tags)
    tags |= set(world.facts["care_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="doorstep",
        plant="moonbell",
        need="thirsty",
        care="moonwater",
        cub_name="Nori",
        cub_type="girl",
        elder_type="grandmother",
        returning_type="mother",
        delay=0,
    ),
    StoryParams(
        place="hearthside",
        plant="embercup",
        need="chilly",
        care="warming_hum",
        cub_name="Milo",
        cub_type="boy",
        elder_type="grandfather",
        returning_type="father",
        delay=1,
    ),
    StoryParams(
        place="window_nook",
        plant="lanternbloom",
        need="shy",
        care="welcome_whisper",
        cub_name="Tala",
        cub_type="girl",
        elder_type="aunt",
        returning_type="mother",
        delay=0,
    ),
    StoryParams(
        place="doorstep",
        plant="embercup",
        need="thirsty",
        care="moonwater",
        cub_name="Finn",
        cub_type="boy",
        elder_type="uncle",
        returning_type="grandfather",
        delay=1,
    ),
    StoryParams(
        place="doorstep",
        plant="lanternbloom",
        need="chilly",
        care="warming_hum",
        cub_name="Bree",
        cub_type="girl",
        elder_type="grandmother",
        returning_type="father",
        delay=1,
    ),
]


ASP_RULES = r"""
care_matches(N,C) :- need_fix(N,C).
helper_available(P,C) :- care_helper(C,H), affords(P,H).
plant_allows(Pl,N) :- allows_need(Pl,N).

valid(P,Pl,N,C) :- place(P), plant(Pl), need(N), care(C),
                   care_matches(N,C), helper_available(P,C), plant_allows(Pl,N).

difficulty(P,Pl,N,V) :- chosen_place(P), chosen_plant(Pl), chosen_need(N),
                        resilience(Pl,R), severity(N,S), delay(D), V = S + D - R.
ready_before_return :- chosen_care(C), power(C,PC), difficulty(_,_,_,V), PC > V.
opens_in_returning_hands :- chosen_care(C), power(C,PC), difficulty(_,_,_,V), PC <= V.

outcome(ready_before_return) :- ready_before_return.
outcome(opens_in_returning_hands) :- opens_in_returning_hands.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for helper_id in sorted(place.afford_helpers):
            lines.append(asp.fact("affords", place_id, helper_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("resilience", plant_id, plant.resilience))
        for need_id in sorted(plant.allowed_needs):
            lines.append(asp.fact("allows_need", plant_id, need_id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("severity", need_id, need.severity))
        lines.append(asp.fact("need_fix", need_id, need.fix_care))
    for care_id, care in CARES.items():
        lines.append(asp.fact("care", care_id))
        lines.append(asp.fact("care_helper", care_id, care.helper))
        lines.append(asp.fact("power", care_id, care.power))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_need", params.need),
            asp.fact("chosen_care", params.care),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming magic storyworld: a cub, a dim flower, and the right kind of caring spell."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--plant", choices=sorted(PLANTS))
    ap.add_argument("--need", choices=sorted(NEEDS))
    ap.add_argument("--care", choices=sorted(CARES))
    ap.add_argument("--cub-name")
    ap.add_argument("--cub-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=sorted(ELDERS))
    ap.add_argument("--returning-type", choices=sorted(RETURNS))
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = ready before the homecoming, 1 = may open a moment later")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.plant and args.need and args.care and not valid_combo(args.place, args.plant, args.need, args.care):
        raise StoryError(explain_invalid(args.place, args.plant, args.need, args.care))
    if args.plant and args.need and not plant_allows(args.plant, args.need):
        place_probe = args.place or next(iter(PLACES))
        care_probe = args.care or NEEDS[args.need].fix_care
        raise StoryError(explain_invalid(place_probe, args.plant, args.need, care_probe))
    if args.need and args.care and not care_matches(args.need, args.care):
        place_probe = args.place or next(iter(PLACES))
        plant_probe = args.plant or next(iter(PLANTS))
        raise StoryError(explain_invalid(place_probe, plant_probe, args.need, args.care))
    if args.place and args.care and not helper_available(args.place, args.care):
        plant_probe = args.plant or next(iter(PLANTS))
        need_probe = args.need or next(iter(NEEDS))
        raise StoryError(explain_invalid(args.place, plant_probe, need_probe, args.care))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.plant is None or c[1] == args.plant)
        and (args.need is None or c[2] == args.need)
        and (args.care is None or c[3] == args.care)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, plant, need, care = rng.choice(sorted(combos))
    cub_type = args.cub_type or rng.choice(["girl", "boy"])
    cub_name = args.cub_name or rng.choice(GIRL_NAMES if cub_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(ELDERS)
    returning_type = args.returning_type or rng.choice(RETURNS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        place=place,
        plant=plant,
        need=need,
        care=care,
        cub_name=cub_name,
        cub_type=cub_type,
        elder_type=elder_type,
        returning_type=returning_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.place, params.plant, params.need, params.care):
        raise StoryError(explain_invalid(params.place, params.plant, params.need, params.care))

    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: ASP gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_combos - py_combos:
            print("  only in ASP:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in Python:", sorted(py_combos - asp_combos))

    cases = list(CURATED)
    for s in range(20):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify for seed {s}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome calculations differ.")

    try:
        smoke = generate(cases[0])
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, plant, need, care) combos:\n")
        for place, plant, need, care in combos:
            print(f"  {place:12} {plant:12} {need:8} {care}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.cub_name}: {p.plant} at {p.place} ({p.need}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
