#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py
=======================================================

A standalone story world for a tiny myth-like domain: a sacred village relic
goes missing, everyone worries about its whereabouts, and a child discovers a
surprising truth. The relic was not stolen at all. A spirit moved it to a safe
sanctuary because a real danger was coming.

The model uses:
- typed entities with physical meters and emotional memes,
- a small causal rule engine,
- a reasonableness gate over compatible relic/hazard/spirit/sanctuary sets,
- an inline ASP twin for parity checks,
- three Q&A sets grounded in world state rather than parsed prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --relic moon_seed
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --hazard ash_wind
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --all
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --json
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --asp
    python storyworlds/worlds/gpt-5.4/whereabouts_surprise_myth.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "goddess"}
        male = {"boy", "father", "grandfather", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    keeps: str
    ritual_line: str
    vulnerability: str
    transform_places: set[str] = field(default_factory=set)
    transformed_image: str = ""
    restored_image: str = ""
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
class Hazard:
    id: str
    label: str
    omen: str
    danger_line: str
    harms: set[str] = field(default_factory=set)
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
class Spirit:
    id: str
    label: str
    type: str
    clue: str
    speaks: str
    guards_against: set[str] = field(default_factory=set)
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
class Sanctuary:
    id: str
    label: str
    phrase: str
    protects_from: set[str] = field(default_factory=set)
    image: str = ""
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_absence_dims_village(world: World) -> list[str]:
    relic = world.get("relic")
    village = world.get("village")
    if relic.attrs.get("place") == "altar":
        return []
    sig = ("absence_dims_village", relic.attrs.get("place"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["dim"] += 1
    for eid in ("hero", "elder"):
        world.get(eid).memes["worry"] += 1
    return []


def _r_clue_brings_hope(world: World) -> list[str]:
    if not world.facts.get("clue_found"):
        return []
    sig = ("clue_brings_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["hope"] += 1
    return []


def _r_shelter_clears_dread(world: World) -> list[str]:
    relic = world.get("relic")
    if relic.attrs.get("place") != "sanctuary" or not world.facts.get("truth_known"):
        return []
    sig = ("shelter_clears_dread", world.facts.get("outcome"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("village").meters["dim"] = 0.0
    world.get("hero").memes["worry"] = 0.0
    world.get("elder").memes["worry"] = 0.0
    world.get("hero").memes["awe"] += 1
    world.get("elder").memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="absence_dims_village", tag="physical", apply=_r_absence_dims_village),
    Rule(name="clue_brings_hope", tag="emotional", apply=_r_clue_brings_hope),
    Rule(name="shelter_clears_dread", tag="resolution", apply=_r_shelter_clears_dread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def threatened(relic: Relic, hazard: Hazard) -> bool:
    return relic.id in hazard.harms


def spirit_can_help(spirit: Spirit, hazard: Hazard) -> bool:
    return hazard.id in spirit.guards_against


def sanctuary_is_safe(sanctuary: Sanctuary, hazard: Hazard) -> bool:
    return hazard.id in sanctuary.protects_from


def valid_combo(relic: Relic, hazard: Hazard, spirit: Spirit, sanctuary: Sanctuary) -> bool:
    return threatened(relic, hazard) and spirit_can_help(spirit, hazard) and sanctuary_is_safe(sanctuary, hazard)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for relic_id, relic in RELICS.items():
        for hazard_id, hazard in HAZARDS.items():
            for spirit_id, spirit in SPIRITS.items():
                for sanctuary_id, sanctuary in SANCTUARIES.items():
                    if valid_combo(relic, hazard, spirit, sanctuary):
                        combos.append((relic_id, hazard_id, spirit_id, sanctuary_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.relic not in RELICS or params.sanctuary not in SANCTUARIES:
        raise StoryError("(Invalid params: unknown relic or sanctuary.)")
    relic = RELICS[params.relic]
    return "transformed" if params.sanctuary in relic.transform_places else "restored"


def predict_ruin(world: World) -> dict:
    sim = world.copy()
    relic = sim.get("relic")
    hazard = sim.facts["hazard"]
    if threatened(sim.facts["relic_cfg"], hazard) and relic.attrs.get("place") == "altar":
        relic.meters["cracked"] += 1
        sim.get("village").meters["dim"] += 1
    return {
        "cracked": relic.meters["cracked"] >= THRESHOLD,
        "village_dim": sim.get("village").meters["dim"],
    }


def introduce(world: World, hero: Entity, elder: Entity, relic: Entity, relic_cfg: Relic) -> None:
    world.say(
        f"In the old days, when hills still listened and the moon sometimes answered, "
        f"the village kept {relic_cfg.phrase} on a stone altar. The people believed "
        f"it {relic_cfg.keeps}."
    )
    world.say(
        f"{hero.id} helped {elder.label_word} sweep the altar each dawn, and "
        f"{elder.pronoun()} always said, \"{relic_cfg.ritual_line}\""
    )
    hero.memes["reverence"] += 1
    elder.memes["reverence"] += 1
    relic.attrs["place"] = "altar"


def omen(world: World, hero: Entity, hazard: Hazard) -> None:
    world.say(
        f"That morning, {hazard.omen}. Even the sparrows went quiet, as if they had heard "
        f"{hazard.danger_line.lower()}."
    )
    world.get("village").meters["risk"] += 1
    hero.memes["unease"] += 1


def discover_absence(world: World, hero: Entity, elder: Entity, relic_cfg: Relic) -> None:
    relic = world.get("relic")
    relic.attrs["place"] = "missing"
    world.facts["asked_whereabouts"] = True
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} turned back to the altar, {relic_cfg.label} was gone. "
        f"Only a pale ring of dust lay where it had rested."
    )
    world.say(
        f"\"What are its whereabouts?\" {hero.id} cried. Villagers lifted their hands to their mouths, "
        f"for no one had ever seen the altar empty."
    )
    world.say(
        f"{elder.label_word.capitalize()} did not shout. {elder.pronoun().capitalize()} touched the cold stone "
        f"and looked at the sky with worried eyes."
    )


def read_sign(world: World, hero: Entity, spirit: Spirit, sanctuary: Sanctuary, hazard: Hazard) -> None:
    pred = predict_ruin(world)
    world.facts["predicted_cracked"] = pred["cracked"]
    world.facts["predicted_dim"] = pred["village_dim"]
    world.facts["clue_found"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} saw {spirit.clue} leading away from the altar and toward {sanctuary.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered the omen and whispered, "
        f"\"Maybe no thief took it. Maybe someone hid it before {hazard.label} could hurt it.\""
    )


def journey(world: World, hero: Entity, elder: Entity, sanctuary: Sanctuary) -> None:
    hero.meters["distance"] += 1
    elder.meters["distance"] += 1
    world.say(
        f"So {hero.id} and {elder.label_word} climbed the path to {sanctuary.phrase}. "
        f"The stones were cool under their feet, and the day felt as if it were holding its breath."
    )


def reveal(world: World, hero: Entity, spirit_cfg: Spirit, sanctuary: Sanctuary) -> None:
    spirit = world.get("spirit")
    relic = world.get("relic")
    relic.attrs["place"] = "sanctuary"
    world.facts["truth_known"] = True
    world.facts["surprise"] = "protected_not_stolen"
    propagate(world, narrate=False)
    world.say(
        f"There, in {sanctuary.image}, sat {spirit_cfg.label}. Beside {spirit.pronoun('object')} rested "
        f"the missing relic, safe and bright."
    )
    world.say(
        f"\"Do not fear,\" said {spirit_cfg.label}. \"{spirit_cfg.speaks}\""
    )


def return_or_transform(world: World, hero: Entity, elder: Entity, relic_cfg: Relic, outcome: str) -> None:
    relic = world.get("relic")
    if outcome == "transformed":
        relic.meters["blessed"] += 1
        world.say(
            f"As {hero.id} stepped closer, the relic changed. {relic_cfg.transformed_image}"
        )
    else:
        relic.meters["blessed"] += 1
        world.say(
            f"When {elder.label_word} lifted it, {relic_cfg.restored_image}"
        )
    world.say(
        f"{hero.id} bowed low, no longer asking for the relic's whereabouts, because now "
        f"{hero.pronoun()} understood why it had been hidden."
    )


def closing(world: World, hero: Entity, elder: Entity, relic_cfg: Relic, outcome: str) -> None:
    if outcome == "transformed":
        end = "The people looked up in wonder and saw that the blessing had grown larger than the old ritual."
    else:
        end = "The people breathed again, for the old rhythm of the village had been set right."
    world.say(
        f"That evening the villagers gathered once more, and {relic_cfg.label} stood upon the altar. "
        f"{end}"
    )
    world.say(
        f"{hero.id} kept the spirit's secret in a grateful heart. After that day, whenever a strange sign "
        f"appeared in the sky, {hero.pronoun()} looked for kindness before blame."
    )


def tell(
    relic_cfg: Relic,
    hazard: Hazard,
    spirit_cfg: Spirit,
    sanctuary: Sanctuary,
    *,
    hero_name: str = "Aro",
    hero_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    village = world.add(Entity(id="village", type="village", label="the village"))
    relic = world.add(Entity(id="relic", type="relic", label=relic_cfg.label, role="relic"))
    spirit = world.add(Entity(id="spirit", kind="character", type=spirit_cfg.type, label=spirit_cfg.label, role="spirit"))

    hero.attrs["name"] = hero_name
    elder.attrs["kin"] = elder_type
    relic.attrs["place"] = "altar"
    world.facts["hero_name"] = hero_name
    world.facts["hero_type"] = hero_gender
    world.facts["elder_type"] = elder_type
    world.facts["relic_cfg"] = relic_cfg
    world.facts["hazard"] = hazard
    world.facts["spirit_cfg"] = spirit_cfg
    world.facts["sanctuary_cfg"] = sanctuary
    world.facts["asked_whereabouts"] = False
    world.facts["clue_found"] = False
    world.facts["truth_known"] = False
    world.facts["predicted_cracked"] = False
    world.facts["predicted_dim"] = 0.0
    world.facts["surprise"] = ""
    world.facts["outcome"] = "restored"

    introduce(world, hero, elder, relic, relic_cfg)
    omen(world, hero, hazard)

    world.para()
    discover_absence(world, hero, elder, relic_cfg)
    read_sign(world, hero, spirit_cfg, sanctuary, hazard)
    journey(world, hero, elder, sanctuary)

    world.para()
    reveal(world, hero, spirit_cfg, sanctuary)
    outcome = "transformed" if sanctuary.id in relic_cfg.transform_places else "restored"
    world.facts["outcome"] = outcome
    return_or_transform(world, hero, elder, relic_cfg, outcome)

    world.para()
    closing(world, hero, elder, relic_cfg, outcome)
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["village"] = village
    world.facts["relic"] = relic
    world.facts["spirit"] = spirit
    return world


RELICS = {
    "moon_seed": Relic(
        id="moon_seed",
        label="the Moon Seed",
        phrase="the Moon Seed, pale as milk in a dark bowl",
        keeps="the night's silver calm from spilling away",
        ritual_line="Guard the small light, and the great light will remember us.",
        vulnerability="ash_wind",
        transform_places={"dew_grotto"},
        transformed_image="Its white shell opened like a flower, and a silver vine uncurled, carrying tiny moons on its leaves.",
        restored_image="its smooth shell shone clean and whole, with a cool light under the skin.",
        tags={"moon", "seed", "altar"},
    ),
    "sun_comb": Relic(
        id="sun_comb",
        label="the Sun Comb",
        phrase="the Sun Comb of amber teeth",
        keeps="dawn neatly braided so morning does not come in tangles",
        ritual_line="Comb the day gently, and the day will shine gently back.",
        vulnerability="mist_flood",
        transform_places={"eagle_ledge"},
        transformed_image="The amber teeth flashed, and a warm mane of light streamed from them like the first sunrise after winter.",
        restored_image="every amber tooth gleamed, and not one was bent or dulled.",
        tags={"sun", "comb", "dawn"},
    ),
    "river_flute": Relic(
        id="river_flute",
        label="the River Flute",
        phrase="the River Flute carved from blue reed",
        keeps="the river singing in one clear channel instead of wandering into the fields",
        ritual_line="Listen first, and the water will know where to go.",
        vulnerability="ash_wind",
        transform_places={"reed_hollow"},
        transformed_image="The flute answered with a new, deep note, and the sound braided water and wind into one shining song.",
        restored_image="the blue reed looked supple again, without even a hairline split.",
        tags={"river", "flute", "reed"},
    ),
}

HAZARDS = {
    "ash_wind": Hazard(
        id="ash_wind",
        label="the Ash Wind",
        omen="a gray wind crept over the hill, carrying warm dust that stung the eyes",
        danger_line="the Ash Wind dries, scours, and cracks sacred things",
        harms={"moon_seed", "river_flute"},
        tags={"wind", "ash", "danger"},
    ),
    "mist_flood": Hazard(
        id="mist_flood",
        label="the Mist Flood",
        omen="a white mist began to pool in the valley, though no rain had fallen",
        danger_line="the Mist Flood swells softly, then soaks what was thought safe",
        harms={"sun_comb"},
        tags={"mist", "flood", "danger"},
    ),
}

SPIRITS = {
    "owl_spirit": Spirit(
        id="owl_spirit",
        label="the Owl Spirit",
        type="goddess",
        clue="a drifting line of white feathers",
        speaks="I carried it where dust cannot gnaw it, because watchfulness is kinder than waiting for grief.",
        guards_against={"ash_wind"},
        tags={"owl", "feather", "watchfulness"},
    ),
    "otter_spirit": Spirit(
        id="otter_spirit",
        label="the Otter Spirit",
        type="god",
        clue="little wet pawprints that glittered and vanished",
        speaks="I set it above the creeping mist, because laughter is no excuse for carelessness, and water rises without asking.",
        guards_against={"mist_flood"},
        tags={"otter", "water", "pawprints"},
    ),
    "cricket_spirit": Spirit(
        id="cricket_spirit",
        label="the Cricket Spirit",
        type="god",
        clue="a chain of bright chirps from stone to stone",
        speaks="I tucked it where the wind must sing before it can bite, because music should be guarded by music.",
        guards_against={"ash_wind"},
        tags={"cricket", "song", "chirp"},
    ),
}

SANCTUARIES = {
    "dew_grotto": Sanctuary(
        id="dew_grotto",
        label="the Dew Grotto",
        phrase="the Dew Grotto under the hill",
        protects_from={"ash_wind"},
        image="a cave whose roof wept silver drops into a pool clear as glass",
        tags={"grotto", "dew", "cave"},
    ),
    "eagle_ledge": Sanctuary(
        id="eagle_ledge",
        label="Eagle Ledge",
        phrase="Eagle Ledge above the clouds",
        protects_from={"mist_flood"},
        image="a high shelf of stone where the air was gold and dry",
        tags={"ledge", "height", "eagle"},
    ),
    "reed_hollow": Sanctuary(
        id="reed_hollow",
        label="the Reed Hollow",
        phrase="the Reed Hollow beside the old river bend",
        protects_from={"ash_wind"},
        image="a cradle of green reeds whispering around a spring-fed pool",
        tags={"reeds", "river", "spring"},
    ),
}

GIRL_NAMES = ["Nara", "Seli", "Ira", "Mira", "Tala", "Una", "Luma", "Neri"]
BOY_NAMES = ["Aro", "Tarin", "Milo", "Soren", "Ilan", "Kori", "Daren", "Lio"]
ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    relic: str
    hazard: str
    spirit: str
    sanctuary: str
    hero_name: str
    hero_gender: str
    elder_type: str
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


KNOWLEDGE = {
    "altar": [
        (
            "What is an altar?",
            "An altar is a special place where people set important things with care. In stories, it can be a place for prayer, memory, or ritual.",
        )
    ],
    "myth": [
        (
            "What makes a story feel like a myth?",
            "A myth often tells about old sacred things, spirits, and signs in nature. It usually explains why people learned a custom or a lesson.",
        )
    ],
    "ash": [
        (
            "What is ash?",
            "Ash is the soft gray powder left after something burns. Wind can carry it through the air and make things dry and dusty.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud very near the ground, made of tiny drops of water. It can make the world look soft and hidden.",
        )
    ],
    "owl": [
        (
            "Why do stories use owls as watchers?",
            "Owls are quiet birds with sharp eyes, so many stories imagine them as careful watchers of the night. That makes them good helpers in myths.",
        )
    ],
    "otter": [
        (
            "What is an otter?",
            "An otter is a playful animal that swims well in rivers and ponds. It has sleek fur, small paws, and likes water.",
        )
    ],
    "cricket": [
        (
            "Why do crickets matter in stories?",
            "Crickets make music with their chirping, so stories often use them as signs of night, patience, or hidden messages. A small sound can still guide someone.",
        )
    ],
    "grotto": [
        (
            "What is a grotto?",
            "A grotto is a small cave or rocky hollow. In stories, grottos often feel secret, cool, and magical.",
        )
    ],
    "ledge": [
        (
            "What is a ledge?",
            "A ledge is a narrow shelf of rock high on a cliff or wall. It can be hard to reach, which makes it feel safe or sacred in a story.",
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants with long stems. They grow near rivers and ponds and bend when the wind moves through them.",
        )
    ],
}

KNOWLEDGE_ORDER = ["myth", "altar", "ash", "mist", "owl", "otter", "cricket", "grotto", "ledge", "reeds"]


CURATED = [
    StoryParams(
        relic="moon_seed",
        hazard="ash_wind",
        spirit="owl_spirit",
        sanctuary="dew_grotto",
        hero_name="Nara",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        relic="sun_comb",
        hazard="mist_flood",
        spirit="otter_spirit",
        sanctuary="eagle_ledge",
        hero_name="Aro",
        hero_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        relic="river_flute",
        hazard="ash_wind",
        spirit="cricket_spirit",
        sanctuary="reed_hollow",
        hero_name="Seli",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        relic="river_flute",
        hazard="ash_wind",
        spirit="owl_spirit",
        sanctuary="dew_grotto",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="grandfather",
    ),
]


def generation_prompts(world: World) -> list[str]:
    relic = world.facts["relic_cfg"]
    hazard = world.facts["hazard"]
    spirit = world.facts["spirit_cfg"]
    sanctuary = world.facts["sanctuary_cfg"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    return [
        f'Write a short myth for a young child in which a sacred object disappears and someone asks about its whereabouts. Include the word "whereabouts".',
        f"Tell a myth-like story about {hero.attrs['name']} and {hero.pronoun('possessive')} {elder.label_word}, who think {relic.label} is lost, but discover a surprising spirit guardian instead.",
        f"Write a gentle myth where {hazard.label.lower()} threatens {relic.label.lower()}, and the twist is that {spirit.label.lower()} hid it safely in {sanctuary.label.lower()}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    relic = world.facts["relic_cfg"]
    hazard = world.facts["hazard"]
    spirit = world.facts["spirit_cfg"]
    sanctuary = world.facts["sanctuary_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']} and {hero.pronoun('possessive')} {elder.label_word}, who care for {relic.label}. They belong to a village that depends on the relic's blessing.",
        ),
        (
            f"Why were people worried when {relic.label} was missing?",
            f"They believed {relic.label} {relic.keeps}, so the empty altar felt frightening. The village also saw {hazard.label.lower()} coming, which made the loss feel even more dangerous.",
        ),
        (
            "What did the hero ask when the altar was empty?",
            f"{hero.attrs['name']} asked about the relic's whereabouts. That question shows how suddenly the disappearance happened and how deeply the hero cared.",
        ),
        (
            "Why did the hero follow the clue instead of blaming a thief?",
            f"{hero.attrs['name']} noticed {spirit.clue} and remembered the warning sign in the sky. {hero.pronoun().capitalize()} guessed the relic might have been hidden for protection, because {hazard.label.lower()} could have harmed it.",
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that nobody had stolen the relic at all. {spirit.label} had moved it to {sanctuary.label} to keep it safe from {hazard.label.lower()}.",
        ),
    ]
    if outcome == "transformed":
        qa.append(
            (
                "How did the relic change at the end?",
                f"It did not merely come back unchanged. In the sanctuary it took on a new blessing, and {relic.transformed_image.lower()}",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The relic returned safely to the altar, and the village's fear lifted. Everyone learned that hidden kindness can look like loss at first.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"myth"}
    tags |= world.facts["relic_cfg"].tags
    tags |= world.facts["hazard"].tags
    tags |= world.facts["spirit_cfg"].tags
    tags |= world.facts["sanctuary_cfg"].tags
    mapped = set()
    if "altar" in tags:
        mapped.add("altar")
    if "ash" in tags:
        mapped.add("ash")
    if "mist" in tags:
        mapped.add("mist")
    if "owl" in tags:
        mapped.add("owl")
    if "otter" in tags:
        mapped.add("otter")
    if "cricket" in tags:
        mapped.add("cricket")
    if "grotto" in tags:
        mapped.add("grotto")
    if "ledge" in tags or "height" in tags:
        mapped.add("ledge")
    if "reeds" in tags or "river" in tags:
        mapped.add("reeds")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in mapped and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(relic: Relic, hazard: Hazard, spirit: Spirit, sanctuary: Sanctuary) -> str:
    if not threatened(relic, hazard):
        return (
            f"(No story: {hazard.label} does not seriously threaten {relic.label}, so there is no good reason to hide it.)"
        )
    if not spirit_can_help(spirit, hazard):
        return (
            f"(No story: {spirit.label} is not a fitting guardian against {hazard.label}, so the surprise rescue would feel unearned.)"
        )
    if not sanctuary_is_safe(sanctuary, hazard):
        return (
            f"(No story: {sanctuary.label} does not protect the relic from {hazard.label}, so moving it there would not be sensible.)"
        )
    return "(No story: the requested combination is not mythically reasonable.)"


ASP_RULES = r"""
threatened(R,H) :- harms(H,R).
spirit_can_help(S,H) :- guards_against(S,H).
sanctuary_is_safe(P,H) :- protects_from(P,H).

valid(R,H,S,P) :- relic(R), hazard(H), spirit(S), sanctuary(P),
                  threatened(R,H), spirit_can_help(S,H), sanctuary_is_safe(P,H).

outcome(transformed) :- chosen_relic(R), chosen_place(P), valid(R,_,_,P), transform_place(R,P).
outcome(restored) :- chosen_relic(R), chosen_place(P), valid(R,_,_,P), not transform_place(R,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for relic_id in sorted(hazard.harms):
            lines.append(asp.fact("harms", hid, relic_id))
    for sid, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", sid))
        for hazard_id in sorted(spirit.guards_against):
            lines.append(asp.fact("guards_against", sid, hazard_id))
    for pid, place in SANCTUARIES.items():
        lines.append(asp.fact("sanctuary", pid))
        for hazard_id in sorted(place.protects_from):
            lines.append(asp.fact("protects_from", pid, hazard_id))
    for rid, relic in RELICS.items():
        for pid in sorted(relic.transform_places):
            lines.append(asp.fact("transform_place", rid, pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    program = asp_program(
        "\n".join(
            [
                asp.fact("chosen_relic", params.relic),
                asp.fact("chosen_place", params.sanctuary),
            ]
        ),
        "#show outcome/1.",
    )
    model = asp.one_model(program)
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome calculations differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if "whereabouts" not in sample.story.lower():
            raise StoryError("Smoke test story did not include required word 'whereabouts'.")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like story world: a sacred relic goes missing, its whereabouts are questioned, and a spirit's surprising kindness is revealed."
    )
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--sanctuary", choices=SANCTUARIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.hazard and args.spirit and args.sanctuary:
        relic = RELICS[args.relic]
        hazard = HAZARDS[args.hazard]
        spirit = SPIRITS[args.spirit]
        sanctuary = SANCTUARIES[args.sanctuary]
        if not valid_combo(relic, hazard, spirit, sanctuary):
            raise StoryError(explain_rejection(relic, hazard, spirit, sanctuary))

    combos = [
        combo
        for combo in valid_combos()
        if (args.relic is None or combo[0] == args.relic)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.spirit is None or combo[2] == args.spirit)
        and (args.sanctuary is None or combo[3] == args.sanctuary)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    relic_id, hazard_id, spirit_id, sanctuary_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(ELDERS)

    return StoryParams(
        relic=relic_id,
        hazard=hazard_id,
        spirit=spirit_id,
        sanctuary=sanctuary_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.relic not in RELICS:
        raise StoryError(f"(Invalid relic: {params.relic})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Invalid hazard: {params.hazard})")
    if params.spirit not in SPIRITS:
        raise StoryError(f"(Invalid spirit: {params.spirit})")
    if params.sanctuary not in SANCTUARIES:
        raise StoryError(f"(Invalid sanctuary: {params.sanctuary})")

    relic = RELICS[params.relic]
    hazard = HAZARDS[params.hazard]
    spirit = SPIRITS[params.spirit]
    sanctuary = SANCTUARIES[params.sanctuary]
    if not valid_combo(relic, hazard, spirit, sanctuary):
        raise StoryError(explain_rejection(relic, hazard, spirit, sanctuary))

    world = tell(
        relic,
        hazard,
        spirit,
        sanctuary,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
    )
    world.get("hero").attrs["name"] = params.hero_name
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (relic, hazard, spirit, sanctuary) combos:\n")
        for relic, hazard, spirit, sanctuary in combos:
            out = "transformed" if sanctuary in RELICS[relic].transform_places else "restored"
            print(f"  {relic:12} {hazard:10} {spirit:14} {sanctuary:11} [{out}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = (
                f"### {p.hero_name}: {p.relic} / {p.hazard} / {p.spirit} / {p.sanctuary} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
