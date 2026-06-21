#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py
==============================================================================

A standalone story world for a tiny mythic tale about a worm, a worried child,
a wiser companion, and a thirsty sacred garden. The story is state-driven:
a blocked watercourse makes a holy plant droop, a child wrongly blames the worm,
dialogue carries the warning and the quarrel, and reconciliation comes when the
children discover the true cause together.

Run it
------
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py --place hill_shrine --crop moonflower --blockage stone --omen bowed_leaves --remedy lift_stone
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py --remedy splash_bucket
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py --all
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/worm_foreshadowing_dialogue_reconciliation_myth.py --verify
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
SENSE_MIN = 2
TRUST_TO_HEED = 6


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "priestess": "priestess",
            "priest": "priest",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    waterway: str
    sky: str
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
class Crop:
    id: str
    label: str
    phrase: str
    plural_name: str
    blessing: str
    need: int
    ending_image: str
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
class Blockage:
    id: str
    label: str
    cause: str
    severity: int
    omen_tags: set[str] = field(default_factory=set)
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
class Omen:
    id: str
    sign_text: str
    elder_line: str
    trail_text: str
    tag: str
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
class Remedy:
    id: str
    label: str
    action_text: str
    fail_text: str
    qa_text: str
    power: int
    sense: int
    fixes: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"accuser", "peacekeeper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_thirst(world: World) -> list[str]:
    crop = world.get("crop")
    canal = world.get("canal")
    if canal.meters["blocked"] < THRESHOLD:
        return []
    sig = ("thirst", world.facts["blockage"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["thirst"] += float(world.facts["crop_cfg"].need)
    return ["__thirst__"]


def _r_droop(world: World) -> list[str]:
    crop = world.get("crop")
    if crop.meters["thirst"] < THRESHOLD:
        return []
    sig = ("droop", world.facts["crop_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["droop"] += 1.0
    for kid in world.kids():
        kid.memes["worry"] += 1.0
    return ["__droop__"]


def _r_revive(world: World) -> list[str]:
    crop = world.get("crop")
    canal = world.get("canal")
    if canal.meters["flow"] < THRESHOLD or crop.meters["droop"] < THRESHOLD:
        return []
    sig = ("revive", world.facts["crop_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["recovery"] += 1.0
    crop.meters["thirst"] = 0.0
    crop.meters["droop"] = 0.0
    return ["__revive__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="thirst", tag="physical", apply=_r_thirst),
    Rule(name="droop", tag="physical", apply=_r_droop),
    Rule(name="revive", tag="physical", apply=_r_revive),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "hill_shrine": Place(
        id="hill_shrine",
        label="the Hill Shrine",
        opening="Above the terraces stood the Hill Shrine, where bells of baked clay rang whenever the dawn wind touched them.",
        waterway="a narrow silver runnel that came from the lion-headed spring",
        sky="The morning sky was pale as a shell, and every stone looked newly washed by the gods.",
        tags={"shrine", "spring"},
    ),
    "laurel_court": Place(
        id="laurel_court",
        label="the Laurel Court",
        opening="In the Laurel Court, old roots knotted the earth like sleeping serpents and the carved basin shone with cool light.",
        waterway="a singing channel that curled beneath the laurel roots",
        sky="The leaves made green shadows that quivered like little prophecies.",
        tags={"court", "basin"},
    ),
    "sun_steps": Place(
        id="sun_steps",
        label="the Sun Steps",
        opening="On the Sun Steps, each terrace held a square of holy soil, and each square was watched by a painted stone face.",
        waterway="a bright thread of water that slipped from step to step",
        sky="High above, swallows stitched black marks across the gold-blue air.",
        tags={"terrace", "water"},
    ),
}

CROPS = {
    "moonflower": Crop(
        id="moonflower",
        label="moonflower vine",
        phrase="a moonflower vine with white cups folded like sleeping stars",
        plural_name="moonflowers",
        blessing="it was said to open only for truthful hands",
        need=2,
        ending_image="that night the moonflowers opened and shone like a necklace laid upon the dark",
        tags={"flower", "night"},
    ),
    "sun_gourd": Crop(
        id="sun_gourd",
        label="sun-gourd patch",
        phrase="a patch of sun-gourds round and gold beneath broad leaves",
        plural_name="sun-gourds",
        blessing="the elders said each ripe gourd held a little warmth from summer",
        need=1,
        ending_image="by evening the sun-gourds glowed under their leaves like little lanterns",
        tags={"gourd", "harvest"},
    ),
    "star_berries": Crop(
        id="star_berries",
        label="star-berry bed",
        phrase="a bed of star-berries whose tiny fruits wore five-pointed crowns",
        plural_name="star-berries",
        blessing="children were told the dawn birds blessed them before sunrise",
        need=2,
        ending_image="at dusk the star-berries flashed red among the leaves like dropped sparks",
        tags={"berries", "dawn"},
    ),
}

BLOCKAGES = {
    "stone": Blockage(
        id="stone",
        label="fallen stone",
        cause="a fallen stone had slid into the mouth of the channel",
        severity=2,
        omen_tags={"droop", "dust", "silence"},
        tags={"stone", "channel"},
    ),
    "reeds": Blockage(
        id="reeds",
        label="snarled reeds",
        cause="a snarl of reeds had woven itself across the waterway",
        severity=1,
        omen_tags={"droop", "silence"},
        tags={"reeds", "channel"},
    ),
    "silt": Blockage(
        id="silt",
        label="heavy silt",
        cause="heavy silt had settled thick as porridge in the channel bed",
        severity=2,
        omen_tags={"dust", "silence"},
        tags={"silt", "channel"},
    ),
}

OMENS = {
    "bowed_leaves": Omen(
        id="bowed_leaves",
        sign_text="One leaf had bowed low, as if listening for water that was not there.",
        elder_line='The old keepers said, "When leaves bow in silence, the roots are asking a question."',
        trail_text="The worm slid beneath the bowed leaf and then along the dry edge of the furrow.",
        tag="droop",
        tags={"leaf", "warning"},
    ),
    "dusty_furrow": Omen(
        id="dusty_furrow",
        sign_text="A pale seam of dust lay across the furrow where the soil should have been dark and cool.",
        elder_line='The old keepers said, "Where sacred earth goes dusty by morning, water has lost its road."',
        trail_text="The worm lifted its small red head from the dusty seam and traveled toward the silent channel.",
        tag="dust",
        tags={"dust", "warning"},
    ),
    "silent_runnel": Omen(
        id="silent_runnel",
        sign_text="The runnel beside the roots was too quiet; even the little frogs had not bothered to sing there.",
        elder_line='The old keepers said, "A quiet channel hides a shut mouth."',
        trail_text="The worm crossed the quiet mud and paused beside the still place where the water should have whispered.",
        tag="silence",
        tags={"water", "warning"},
    ),
}

REMEDIES = {
    "lift_stone": Remedy(
        id="lift_stone",
        label="lift the stone",
        action_text="set their shoulders under the stone together and rolled it from the mouth of the channel",
        fail_text="strained at the stone, but it sat too deep and the water only trembled behind it",
        qa_text="lifted the stone away from the channel so the water could run again",
        power=3,
        sense=3,
        fixes="stone",
        tags={"stone", "repair"},
    ),
    "cut_reeds": Remedy(
        id="cut_reeds",
        label="cut the reeds",
        action_text="used a bronze garden knife to cut the snarled reeds and pull them clear",
        fail_text="cut at the reeds, but too many roots still held the water back",
        qa_text="cut away the reeds that were tangling the waterway",
        power=2,
        sense=3,
        fixes="reeds",
        tags={"reeds", "repair"},
    ),
    "scoop_silt": Remedy(
        id="scoop_silt",
        label="scoop the silt",
        action_text="knelt with clay bowls and scooped the heavy silt from the channel until the bed shone wet again",
        fail_text="scooped and scooped, but too much silt remained for the thin trickle to break through",
        qa_text="scooped the heavy silt out of the channel",
        power=2,
        sense=3,
        fixes="silt",
        tags={"silt", "repair"},
    ),
    "splash_bucket": Remedy(
        id="splash_bucket",
        label="splash a bucket over the roots",
        action_text="splashed a single bucket over the roots",
        fail_text="splashed a single bucket over the roots, but it vanished into the thirsty ground at once",
        qa_text="splashed one bucket of water over the roots",
        power=1,
        sense=1,
        fixes="none",
        tags={"water", "repair"},
    ),
}

GIRL_NAMES = ["Iris", "Mara", "Thaleia", "Dora", "Nysa", "Eleni", "Rhea", "Calla"]
BOY_NAMES = ["Theo", "Lykos", "Damon", "Nikos", "Aren", "Soren", "Leos", "Iason"]
TRAITS = ["quick", "careful", "proud", "gentle", "thoughtful", "eager"]


@dataclass
class StoryParams:
    place: str
    crop: str
    blockage: str
    omen: str
    remedy: str
    accuser: str
    accuser_gender: str
    peacekeeper: str
    peacekeeper_gender: str
    elder_type: str
    accuser_trait: str
    peacekeeper_trait: str
    trust: int = 5
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


CURATED = [
    StoryParams(
        place="hill_shrine",
        crop="moonflower",
        blockage="stone",
        omen="bowed_leaves",
        remedy="lift_stone",
        accuser="Theo",
        accuser_gender="boy",
        peacekeeper="Iris",
        peacekeeper_gender="girl",
        elder_type="priestess",
        accuser_trait="proud",
        peacekeeper_trait="gentle",
        trust=7,
        delay=0,
    ),
    StoryParams(
        place="laurel_court",
        crop="sun_gourd",
        blockage="reeds",
        omen="silent_runnel",
        remedy="cut_reeds",
        accuser="Mara",
        accuser_gender="girl",
        peacekeeper="Damon",
        peacekeeper_gender="boy",
        elder_type="priest",
        accuser_trait="quick",
        peacekeeper_trait="thoughtful",
        trust=5,
        delay=0,
    ),
    StoryParams(
        place="sun_steps",
        crop="star_berries",
        blockage="silt",
        omen="dusty_furrow",
        remedy="scoop_silt",
        accuser="Lykos",
        accuser_gender="boy",
        peacekeeper="Rhea",
        peacekeeper_gender="girl",
        elder_type="priestess",
        accuser_trait="eager",
        peacekeeper_trait="careful",
        trust=8,
        delay=1,
    ),
    StoryParams(
        place="hill_shrine",
        crop="moonflower",
        blockage="stone",
        omen="silent_runnel",
        remedy="lift_stone",
        accuser="Nysa",
        accuser_gender="girl",
        peacekeeper="Theo",
        peacekeeper_gender="boy",
        elder_type="priest",
        accuser_trait="quick",
        peacekeeper_trait="gentle",
        trust=3,
        delay=2,
    ),
]


def remedy_is_sensible(remedy: Remedy) -> bool:
    return remedy.sense >= SENSE_MIN


def omen_matches(blockage: Blockage, omen: Omen) -> bool:
    return omen.tag in blockage.omen_tags


def remedy_matches(blockage: Blockage, remedy: Remedy) -> bool:
    return remedy.fixes == blockage.id


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for crop_id in CROPS:
            for blockage_id, blockage in BLOCKAGES.items():
                for omen_id, omen in OMENS.items():
                    if not omen_matches(blockage, omen):
                        continue
                    for remedy_id, remedy in REMEDIES.items():
                        if remedy_is_sensible(remedy) and remedy_matches(blockage, remedy):
                            combos.append((place_id, crop_id, blockage_id, omen_id, remedy_id))
    return combos


def distress(blockage: Blockage, crop: Crop, delay: int) -> int:
    return blockage.severity + crop.need + delay


def is_saved(blockage: Blockage, crop: Crop, remedy: Remedy, delay: int) -> bool:
    return remedy.power >= distress(blockage, crop, delay)


def would_heed(trust: int) -> bool:
    return trust >= TRUST_TO_HEED


def outcome_of(params: StoryParams) -> str:
    if not all(k in PLACES for k in [params.place]) or params.crop not in CROPS or params.blockage not in BLOCKAGES or params.omen not in OMENS or params.remedy not in REMEDIES:
        raise StoryError("(Invalid params: unknown registry key.)")
    if would_heed(params.trust):
        return "heeded"
    return "saved" if is_saved(BLOCKAGES[params.blockage], CROPS[params.crop], REMEDIES[params.remedy], params.delay) else "withered"


def explain_omen(blockage: Blockage, omen: Omen) -> str:
    return (
        f"(No story: the omen '{omen.id}' does not fit the blockage '{blockage.id}'. "
        f"This myth needs a true warning sign, not a random decoration.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). This world prefers a real fix for the blocked channel.)"
    )


def explain_pair(blockage: Blockage, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} does not actually fix {blockage.label}. "
        f"The remedy must clear the true blockage.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_garden(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    crop = sim.get("crop")
    return {
        "thirst": crop.meters["thirst"],
        "droop": crop.meters["droop"],
    }


def introduce(world: World, a: Entity, b: Entity, elder: Entity, crop: Crop) -> None:
    world.say(world.place.opening)
    world.say(world.place.sky)
    world.say(
        f"That morning, {a.id} and {b.id} had been sent with {elder.label_word} to tend {crop.phrase}. "
        f"The people of {world.place.label} believed {crop.blessing}."
    )


def omen_scene(world: World, a: Entity, b: Entity, worm: Entity, omen: Omen, crop: Crop) -> None:
    world.say(
        f"Beneath the leaves, a small bronze-red worm turned the soil in a patient ring around the roots of the {crop.label}."
    )
    world.say(omen.sign_text)
    world.say(omen.elder_line)
    pred = predict_garden(world)
    world.facts["predicted_thirst"] = pred["thirst"]
    world.facts["predicted_droop"] = pred["droop"]


def quarrel(world: World, a: Entity, b: Entity, worm: Entity, elder: Entity, crop: Crop) -> None:
    a.memes["blame"] += 1.0
    b.memes["protective"] += 1.0
    world.say(
        f'"That worm is nibbling the blessing away," {a.id} said. "Look how the {crop.plural_name} are bending."'
    )
    world.say(
        f'"No," said {b.id}, kneeling close. "It is only turning the earth. {elder.label_word.capitalize()} says a root can thirst even when a leaf still looks green."'
    )


def heed_and_follow(world: World, a: Entity, b: Entity, worm: Entity, omen: Omen) -> None:
    a.memes["trust"] += 1.0
    b.memes["trust"] += 1.0
    world.say(
        f'{a.id} stopped with {a.pronoun("possessive")} hand in the air. "{b.id}, perhaps you are right," {a.pronoun()} said.'
    )
    world.say(
        f"{omen.trail_text} The two children followed it instead of striking at it."
    )


def refuse_and_follow(world: World, a: Entity, b: Entity, worm: Entity, omen: Omen) -> None:
    a.memes["anger"] += 1.0
    world.say(
        f'"It is easy for you to defend a worm," {a.id} snapped. "{elder_word(world).capitalize()} entrusted us with the garden."'
    )
    world.say(
        f'{b.id} answered softly, "Then let us search before we punish." {omen.trail_text} After one hard breath, {a.id} followed.'
    )


def elder_word(world: World) -> str:
    return world.get("elder").label_word


def discover(world: World, blockage: Blockage) -> None:
    canal = world.get("canal")
    canal.meters["blocked"] = 1.0
    canal.meters["flow"] = 0.0
    propagate(world, narrate=False)
    crop = world.get("crop")
    world.say(
        f"At the end of the furrow they found the truth: {blockage.cause}. Behind it, the water waited like a held breath."
    )
    if crop.meters["droop"] >= THRESHOLD:
        world.say(
            f"Then {world.facts['accuser'].id} saw that the worm had not harmed the roots at all. The roots were thirsty."
        )


def repair_success(world: World, remedy: Remedy) -> None:
    canal = world.get("canal")
    canal.meters["blocked"] = 0.0
    canal.meters["flow"] = 1.0
    world.say(
        f"The children {remedy.action_text}. A clear voice of water slipped forward, then another, until the channel was singing again."
    )
    propagate(world, narrate=False)


def repair_fail(world: World, remedy: Remedy) -> None:
    canal = world.get("canal")
    canal.meters["blocked"] = 1.0
    canal.meters["flow"] = 0.0
    world.say(
        f"The children {remedy.fail_text}. The holy bed darkened for a moment, but the thirst beneath it remained."
    )


def reconciliation(world: World, a: Entity, b: Entity, worm: Entity, crop: Crop, saved: bool, heeded: bool) -> None:
    a.memes["shame"] += 1.0
    a.memes["peace"] += 1.0
    b.memes["peace"] += 1.0
    worm.memes["safe"] += 1.0
    if heeded:
        world.say(
            f'"I was ready to blame what I did not understand," {a.id} said. "Forgive me, {b.id}."'
        )
        world.say(
            f'"You listened before doing harm," {b.id} answered. "That is how gardens and friendships stay alive."'
        )
        return
    if saved:
        world.say(
            f'"I spoke against you and against the worm," {a.id} said to {b.id}. "Forgive me. It was guiding us to the thirsty place."'
        )
        world.say(
            f'"I forgive you," said {b.id}. "Now we know that anger is louder than truth, but not stronger."'
        )
    else:
        world.say(
            f'"I was cruel to the worm and unfair to you," {a.id} whispered. "Forgive me, {b.id}."'
        )
        world.say(
            f'"I forgive you," said {b.id}, taking {a.pronoun("possessive")} hand. "We were late, but we can still learn to look for the true wound first."'
        )


def ending(world: World, crop: Crop, saved: bool, heeded: bool) -> None:
    if heeded:
        world.say(
            f"Together they traced the furrow to the blockage and called for tools before any root had truly suffered. The worm vanished into the loosened earth like a tiny priest of the ground."
        )
        world.say(
            f"When evening came, {crop.ending_image}, and the children told the tale as a warning against quick blame."
        )
        return
    if saved:
        world.say(
            f"Before sunset the roots drank deep again. The worm curled beneath the cool soil, and no one in {world.place.label} called it a thief after that."
        )
        world.say(crop.ending_image.capitalize() + ".")
    else:
        world.say(
            f"Some leaves could not be called back that day, and the children felt the loss like a pebble in each sandal."
        )
        world.say(
            f"Yet they left a little crescent of damp earth for the worm and promised that next time they would listen sooner than they accused."
        )


def tell(
    place: Place,
    crop_cfg: Crop,
    blockage: Blockage,
    omen: Omen,
    remedy: Remedy,
    accuser_name: str = "Theo",
    accuser_gender: str = "boy",
    peacekeeper_name: str = "Iris",
    peacekeeper_gender: str = "girl",
    elder_type: str = "priestess",
    accuser_trait: str = "proud",
    peacekeeper_trait: str = "gentle",
    trust: int = 5,
    delay: int = 0,
) -> World:
    world = World(place)
    accuser = world.add(
        Entity(
            id=accuser_name,
            kind="character",
            type=accuser_gender,
            role="accuser",
            traits=[accuser_trait],
            attrs={"trust": trust},
        )
    )
    peacekeeper = world.add(
        Entity(
            id=peacekeeper_name,
            kind="character",
            type=peacekeeper_gender,
            role="peacekeeper",
            traits=[peacekeeper_trait],
            attrs={"trust": trust},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    worm = world.add(
        Entity(
            id="worm",
            kind="thing",
            type="worm",
            role="helper",
            label="the worm",
        )
    )
    crop = world.add(
        Entity(
            id="crop",
            kind="thing",
            type="crop",
            label=crop_cfg.label,
            attrs={"need": crop_cfg.need},
        )
    )
    canal = world.add(
        Entity(
            id="canal",
            kind="thing",
            type="canal",
            label=place.waterway,
        )
    )
    canal.meters["blocked"] = 0.0
    canal.meters["flow"] = 1.0
    crop.meters["thirst"] = 0.0
    crop.meters["droop"] = 0.0
    crop.meters["recovery"] = 0.0

    world.facts.update(
        place=place,
        crop_cfg=crop_cfg,
        blockage=blockage,
        omen=omen,
        remedy=remedy,
        accuser=accuser,
        peacekeeper=peacekeeper,
        elder=elder,
        worm=worm,
        trust=trust,
        delay=delay,
    )

    introduce(world, accuser, peacekeeper, elder, crop_cfg)
    world.para()
    omen_scene(world, accuser, peacekeeper, worm, omen, crop_cfg)
    quarrel(world, accuser, peacekeeper, worm, elder, crop_cfg)

    heeded = would_heed(trust)
    world.facts["heeded"] = heeded

    world.para()
    if heeded:
        heed_and_follow(world, accuser, peacekeeper, worm, omen)
        discover(world, blockage)
        saved = True
    else:
        refuse_and_follow(world, accuser, peacekeeper, worm, omen)
        discover(world, blockage)
        saved = is_saved(blockage, crop_cfg, remedy, delay)
        if saved:
            repair_success(world, remedy)
        else:
            repair_fail(world, remedy)
    world.facts["saved"] = saved

    world.para()
    reconciliation(world, accuser, peacekeeper, worm, crop_cfg, saved=saved, heeded=heeded)
    ending(world, crop_cfg, saved=saved, heeded=heeded)

    world.facts["outcome"] = "heeded" if heeded else ("saved" if saved else "withered")
    world.facts["crop_recovered"] = crop.meters["recovery"] >= THRESHOLD or heeded
    world.facts["crop_drooped"] = crop.meters["droop"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "worm": [
        (
            "What does a worm do in soil?",
            "A worm tunnels through soil and helps loosen it. Loose soil lets air and water move more easily around roots."
        )
    ],
    "channel": [
        (
            "Why does a plant need water to reach its roots?",
            "Roots drink water from the soil so the plant can stay firm and alive. If the water cannot reach them, leaves and fruit begin to droop."
        )
    ],
    "stone": [
        (
            "How can a fallen stone block water?",
            "A stone can sit in a narrow channel like a stopper in a bottle. Then the water piles up behind it instead of flowing forward."
        )
    ],
    "reeds": [
        (
            "Why can reeds stop a little waterway?",
            "Reeds can tangle together and catch bits of grass and mud. Soon the water has trouble slipping through."
        )
    ],
    "silt": [
        (
            "What is silt?",
            "Silt is very fine earth carried by water. When it settles, it can fill a channel and make the water slow or stop."
        )
    ],
    "repair": [
        (
            "Why is it important to find the real problem before fixing something?",
            "A true fix has to touch the real cause. If you guess wrong, you may hurt something innocent and still leave the trouble in place."
        )
    ],
    "reconcile": [
        (
            "What does it mean to reconcile after an argument?",
            "To reconcile means to make peace again after hurt or anger. People listen, tell the truth, and forgive each other."
        )
    ],
}
KNOWLEDGE_ORDER = ["worm", "channel", "stone", "reeds", "silt", "repair", "reconcile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["accuser"]
    b = f["peacekeeper"]
    crop = f["crop_cfg"]
    omen = f["omen"]
    outcome = f["outcome"]
    base = (
        f'Write a short mythic story for a 3-to-5-year-old that includes the word "worm", '
        f'uses dialogue, and begins with a warning sign about a sacred {crop.label}.'
    )
    if outcome == "heeded":
        return [
            base,
            f"Tell a myth where {a.id} is ready to blame a worm, but {b.id} asks {a.pronoun('object')} to look closer, and their friendship is strengthened because they listen before acting.",
            f'Write a gentle myth with foreshadowing from "{omen.sign_text}" and end with reconciliation after the children discover the true cause together.',
        ]
    if outcome == "saved":
        return [
            base,
            f"Tell a myth where {a.id} wrongly accuses a worm of harming a sacred plant, but the worm leads the children to the blocked watercourse and they make peace after saving the garden.",
            f'Write a simple mythic story with foreshadowing, spoken quarrel, and reconciliation, ending with the sacred garden alive again.',
        ]
    return [
        base,
        f"Tell a myth where two children learn too late that the worm was innocent and the true danger was a blocked channel, but they still reconcile and promise to judge more wisely.",
        f'Write a sad but gentle myth with dialogue and reconciliation, where a foreshadowing sign warns of thirst before the children understand it.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["accuser"]
    b = f["peacekeeper"]
    crop = f["crop_cfg"]
    blockage = f["blockage"]
    omen = f["omen"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children tending a sacred {crop.label}, and a worm they first misunderstand. Their argument matters because the garden's roots are already in danger."
        ),
        (
            "What was the warning sign at the beginning?",
            f"The warning sign was this: {omen.sign_text} It foreshadowed that the roots were not getting the water they needed."
        ),
        (
            f"Why did {a.id} blame the worm?",
            f"{a.id} saw the drooping sign near the roots and guessed the worm was hurting the plant. The fear of losing the sacred garden made {a.pronoun('object')} judge too quickly."
        ),
        (
            f"How did {b.id} answer?",
            f"{b.id} told {a.id} that the worm was only turning the earth and that the roots might be thirsty instead. That calm answer pushed the story away from anger and toward the truth."
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                "What happened because they listened before acting?",
                f"They followed the worm's trail, found that {blockage.cause}, and called for the right tools before the roots suffered badly. Listening early kept blame from becoming harm."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                "How did they save the garden?",
                f"They discovered that {blockage.cause}, and then they {remedy.qa_text}. Once the water sang through the channel again, the sacred roots could drink."
            )
        )
    else:
        qa.append(
            (
                "Why could they not fully save the garden that day?",
                f"They found the true blockage, but they were late and their first fix was not strong enough for the deep thirst below. Some leaves had already gone too far without water."
            )
        )
    qa.append(
        (
            "How did the children reconcile?",
            f"{a.id} admitted the worm was innocent and asked {b.id} for forgiveness. {b.id} forgave {a.pronoun('object')}, so the ending proves they learned truth should come before blame."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"worm", "channel", "repair", "reconcile"}
    blockage = f["blockage"]
    if blockage.id in {"stone", "reeds", "silt"}:
        tags.add(blockage.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- registry gate ---------------------------------------------------------
valid(P,C,B,O,R) :- place(P), crop(C), blockage(B), omen(O), remedy(R),
                    omen_tag(O,T), blockage_allows(B,T),
                    fixes(R,B), sense(R,S), sense_min(M), S >= M.

sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
heeded :- trust(T), heed_min(M), T >= M.
distress(D) :- chosen_blockage(B), severity(B,S), chosen_crop(C), need(C,N), delay(L), D = S + N + L.
saved_by_fix :- chosen_remedy(R), power(R,P), distress(D), P >= D.

outcome(heeded)   :- heeded.
outcome(saved)    :- not heeded, saved_by_fix.
outcome(withered) :- not heeded, not saved_by_fix.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        lines.append(asp.fact("need", crop_id, crop.need))
    for blockage_id, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", blockage_id))
        lines.append(asp.fact("severity", blockage_id, blockage.severity))
        for tag in sorted(blockage.omen_tags):
            lines.append(asp.fact("blockage_allows", blockage_id, tag))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("omen_tag", omen_id, omen.tag))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
        if remedy.fixes != "none":
            lines.append(asp.fact("fixes", remedy_id, remedy.fixes))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("heed_min", TRUST_TO_HEED))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_blockage", params.blockage),
            asp.fact("chosen_crop", params.crop),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("trust", params.trust),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True, header="### smoke")
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: story text was empty.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {rid for rid, remedy in REMEDIES.items() if remedy_is_sensible(remedy)}
    if c_sens == p_sens:
        print(f"OK: sensible remedies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test_generation()
        print("OK: smoke test generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic garden, a worm, a warning sign, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the children are before they try the fix")
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)), help="how ready the accuser is to heed the calmer child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and not remedy_is_sensible(REMEDIES[args.remedy]):
        raise StoryError(explain_remedy(args.remedy))
    if args.blockage and args.omen:
        blockage = BLOCKAGES[args.blockage]
        omen = OMENS[args.omen]
        if not omen_matches(blockage, omen):
            raise StoryError(explain_omen(blockage, omen))
    if args.blockage and args.remedy:
        blockage = BLOCKAGES[args.blockage]
        remedy = REMEDIES[args.remedy]
        if not remedy_matches(blockage, remedy):
            raise StoryError(explain_pair(blockage, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.crop is None or combo[1] == args.crop)
        and (args.blockage is None or combo[2] == args.blockage)
        and (args.omen is None or combo[3] == args.omen)
        and (args.remedy is None or combo[4] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, crop, blockage, omen, remedy = rng.choice(sorted(combos))
    accuser_gender = rng.choice(["girl", "boy"])
    peacekeeper_gender = rng.choice(["girl", "boy"])
    accuser = _pick_name(rng, accuser_gender)
    peacekeeper = _pick_name(rng, peacekeeper_gender, avoid=accuser)
    elder_type = args.elder or rng.choice(["priestess", "priest"])
    accuser_trait = rng.choice(TRAITS)
    peacekeeper_trait = rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(2, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        crop=crop,
        blockage=blockage,
        omen=omen,
        remedy=remedy,
        accuser=accuser,
        accuser_gender=accuser_gender,
        peacekeeper=peacekeeper,
        peacekeeper_gender=peacekeeper_gender,
        elder_type=elder_type,
        accuser_trait=accuser_trait,
        peacekeeper_trait=peacekeeper_trait,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        crop = CROPS[params.crop]
        blockage = BLOCKAGES[params.blockage]
        omen = OMENS[params.omen]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err!s}.)") from None

    if not omen_matches(blockage, omen):
        raise StoryError(explain_omen(blockage, omen))
    if not remedy_is_sensible(remedy):
        raise StoryError(explain_remedy(params.remedy))
    if not remedy_matches(blockage, remedy):
        raise StoryError(explain_pair(blockage, remedy))

    world = tell(
        place=place,
        crop_cfg=crop,
        blockage=blockage,
        omen=omen,
        remedy=remedy,
        accuser_name=params.accuser,
        accuser_gender=params.accuser_gender,
        peacekeeper_name=params.peacekeeper,
        peacekeeper_gender=params.peacekeeper_gender,
        elder_type=params.elder_type,
        accuser_trait=params.accuser_trait,
        peacekeeper_trait=params.peacekeeper_trait,
        trust=params.trust,
        delay=params.delay,
    )
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, crop, blockage, omen, remedy) combos:\n")
        for place, crop, blockage, omen, remedy in combos:
            print(f"  {place:12} {crop:12} {blockage:8} {omen:14} {remedy}")
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
                f"### {p.accuser} & {p.peacekeeper}: {p.crop} at {p.place} "
                f"({p.blockage}, {p.omen}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
