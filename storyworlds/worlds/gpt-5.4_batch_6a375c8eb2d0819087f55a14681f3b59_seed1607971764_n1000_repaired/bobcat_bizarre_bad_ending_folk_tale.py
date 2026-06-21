#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py
=================================================================

A standalone story world for a cautionary folk tale about a young bobcat who
follows a bizarre lure toward a forbidden crossing and pays for it with a bad
ending. The world models desire, warning, danger, and loss as simulated state,
then renders a complete tale from that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --setting reed_marsh --crossing rotten_log
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --setting frost_pond --crossing rotten_log
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --json
    python storyworlds/worlds/gpt-5.4/bobcat_bizarre_bad_ending_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bobcat", "cat", "fox", "raven", "owl", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"lynx", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    crossing_options: set[str] = field(default_factory=set)
    shore_text: str = ""
    far_side: str = ""
    dusk_image: str = ""
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
class Lure:
    id: str
    label: str
    appearance: str
    call: str
    desire: int
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
class Crossing:
    id: str
    label: str
    over: str
    risk: int
    break_text: str
    harm: str
    ending_kind: str
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
class Elder:
    id: str
    type: str
    label: str
    voice: str
    wisdom: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_danger(world: World) -> list[str]:
    hero = world.get("hero")
    crossing = world.get("crossing")
    if hero.meters["on_crossing"] < THRESHOLD:
        return []
    sig = ("danger", crossing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["danger"] += crossing.attrs["risk"]
    hero.memes["fear"] += 1
    world.get("place").meters["hazard"] += 1
    return []


def _r_break(world: World) -> list[str]:
    hero = world.get("hero")
    crossing = world.get("crossing")
    if hero.meters["danger"] < crossing.attrs["risk"]:
        return []
    sig = ("break", crossing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crossing.meters["broken"] += 1
    hero.meters["fallen"] += 1
    hero.meters["empty_paws"] += 1
    hero.memes["fear"] += 1
    hero.memes["shame"] += 1
    if crossing.attrs["ending_kind"] == "soaked":
        hero.meters["wet"] += 1
        hero.meters["cold"] += 1
    else:
        hero.meters["stranded"] += 1
        hero.meters["cold"] += 1
        hero.meters["hungry"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="break", tag="physical", apply=_r_break),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def crossing_fits(setting: Setting, crossing: Crossing) -> bool:
    return crossing.id in setting.crossing_options


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for lure_id in LURES:
            for crossing_id, crossing in CROSSINGS.items():
                if crossing_fits(setting, crossing):
                    combos.append((setting_id, lure_id, crossing_id))
    return combos


def explain_rejection(setting: Setting, crossing: Crossing) -> str:
    return (
        f"(No story: {crossing.label} does not belong in {setting.place}. "
        f"In this little world, that place reasonably uses only "
        f"{', '.join(sorted(setting.crossing_options))}.)"
    )


def predict_fall(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["on_crossing"] += 1
    propagate(sim, narrate=False)
    return {
        "broken": sim.get("crossing").meters["broken"] >= THRESHOLD,
        "wet": hero.meters["wet"] >= THRESHOLD,
        "stranded": hero.meters["stranded"] >= THRESHOLD,
    }


def folk_opening(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"In the days when pines were said to whisper advice to anyone humble enough "
        f"to listen, there lived a young bobcat named {hero.id} beside {setting.place}."
    )
    world.say(
        f"He had quick paws, bright eyes, and a proud little heart that loved whatever "
        f"looked rare or strange."
    )


def introduce_elder(world: World, elder: Entity) -> None:
    world.say(
        f"Not far from his den lived {elder.label}, an old {elder.type} whose "
        f"{elder.attrs['voice']} had guided many creatures home before dark."
    )


def reveal_lure(world: World, hero: Entity, setting: Setting, lure: Lure) -> None:
    hero.memes["wonder"] += 1
    hero.memes["greed"] += float(lure.desire)
    world.say(
        f"One dusk, while {setting.shore_text}, {hero.id} saw {lure.appearance} on the far side, "
        f"near {setting.far_side}."
    )
    world.say(
        f"It gave off {lure.call}, so odd and sparkling that even the crickets fell still. "
        f'"What a bizarre marvel," {hero.id} whispered. "If I carry it home, every eye in the '
        f'valley will turn toward me."'
    )


def warn(world: World, elder: Entity, hero: Entity, crossing: Crossing) -> None:
    pred = predict_fall(world)
    hero.memes["warning_heard"] += 1
    world.facts["predicted_broken"] = pred["broken"]
    world.facts["predicted_wet"] = pred["wet"]
    world.facts["predicted_stranded"] = pred["stranded"]
    consequence = "leave you soaked in the bitter water" if pred["wet"] else "leave you stranded above the dark stones"
    world.say(
        f'But {elder.label} called after him in {elder.attrs["voice"]}: '
        f'"Do not trust {crossing.label} at dusk. It will {consequence}, and no shining thing is worth that price."'
    )
    world.say(
        f"{elder.label} had seen foolish feet choose hurry over wisdom before."
    )


def defy(world: World, hero: Entity, crossing: Crossing) -> None:
    hero.memes["defiance"] += 1
    hero.meters["on_crossing"] += 1
    world.say(
        f"{hero.id} flattened his ears, not from fear but from pride. "
        f'"Old voices always tremble at shadows," he said, and sprang onto {crossing.label}.'
    )
    propagate(world, narrate=False)


def collapse(world: World, hero: Entity, crossing: Crossing) -> None:
    world.say(crossing.break_text)
    if hero.meters["wet"] >= THRESHOLD:
        world.say(
            f"He splashed into the black water below, and the cold bit through his fur at once."
        )
    if hero.meters["stranded"] >= THRESHOLD:
        world.say(
            f"He caught himself on a narrow shelf of stone, but there he hung with nowhere safe to leap."
        )
    world.say(
        f"The strange prize vanished from reach, and {hero.id} found he held nothing at all."
    )


def bad_ending(world: World, hero: Entity, setting: Setting, elder: Entity, crossing: Crossing, lure: Lure) -> None:
    if crossing.ending_kind == "soaked":
        world.say(
            f"When at last he dragged himself home, the moon had climbed high and the reeds had frozen silver. "
            f"{elder.label} wrapped him in dry moss, but no warmth could hide his shame."
        )
        world.say(
            f"All winter long, creatures told how {hero.id} chased {lure.label} over {crossing.label} and came back with only a cough and an empty belly."
        )
        world.say(
            f"So it is said in {setting.place}: whoever follows a bizarre glitter for pride's sake may keep his fur, yet lose his good name."
        )
    else:
        world.say(
            f"The moon rose higher, and the whole valley glimmered while {hero.id} shivered alone above {crossing.over}. "
            f"No feast waited for him, and no proud story either."
        )
        world.say(
            f"At dawn {elder.label} showed him the long safe path back, yet the valley remembered that he had trusted a strange gleam more than wise counsel."
        )
        world.say(
            f"So it is said in {setting.place}: a proud paw that runs after a bizarre wonder may not be broken forever, but it may come home smaller than it left."
        )


def tell(
    setting: Setting,
    lure: Lure,
    crossing: Crossing,
    *,
    hero_name: str = "Brindle",
    hero_trait: str = "proud",
    elder_id: str = "raven_grandam",
    seed: Optional[int] = None,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="bobcat",
            label=hero_name,
            role="hero",
            traits=[hero_trait],
            attrs={},
        )
    )
    elder_cfg = ELDERS[elder_id]
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_cfg.type,
            label=elder_cfg.label,
            role="elder",
            traits=["wise"],
            attrs={"voice": elder_cfg.voice, "wisdom": elder_cfg.wisdom},
        )
    )
    place = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=setting.place,
            attrs={},
        )
    )
    crossing_ent = world.add(
        Entity(
            id="crossing",
            kind="thing",
            type="crossing",
            label=crossing.label,
            attrs={"risk": crossing.risk, "ending_kind": crossing.ending_kind},
        )
    )
    lure_ent = world.add(
        Entity(
            id="lure",
            kind="thing",
            type="lure",
            label=lure.label,
            attrs={"desire": lure.desire},
        )
    )

    for key in [
        "on_crossing",
        "danger",
        "fallen",
        "empty_paws",
        "wet",
        "cold",
        "stranded",
        "hungry",
    ]:
        hero.meters[key] = 0.0
    for key in ["wonder", "greed", "warning_heard", "defiance", "fear", "shame"]:
        hero.memes[key] = 0.0
    place.meters["hazard"] = 0.0
    crossing_ent.meters["broken"] = 0.0

    world.facts.update(
        hero=hero,
        elder=elder,
        setting=setting,
        lure=lure,
        crossing_cfg=crossing,
        crossing=crossing_ent,
        lure_ent=lure_ent,
        predicted_broken=False,
        predicted_wet=False,
        predicted_stranded=False,
        outcome="bad",
        seed=seed,
    )

    folk_opening(world, hero, setting)
    introduce_elder(world, elder)
    world.para()
    reveal_lure(world, hero, setting, lure)
    warn(world, elder, hero, crossing)
    world.para()
    defy(world, hero, crossing)
    collapse(world, hero, crossing)
    world.para()
    bad_ending(world, hero, setting, elder, crossing, lure)

    world.facts.update(
        fell=hero.meters["fallen"] >= THRESHOLD,
        soaked=hero.meters["wet"] >= THRESHOLD,
        stranded=hero.meters["stranded"] >= THRESHOLD,
        hungry=hero.meters["hungry"] >= THRESHOLD,
        shamed=hero.memes["shame"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "reed_marsh": Setting(
        id="reed_marsh",
        place="the Reed Marsh",
        crossing_options={"rotten_log"},
        shore_text="the cattails bowed in the wind",
        far_side="a clump of moon-white reeds",
        dusk_image="the reeds had frozen silver",
        tags={"marsh", "water"},
    ),
    "frost_pond": Setting(
        id="frost_pond",
        place="the Frost Pond",
        crossing_options={"thin_ice"},
        shore_text="the cattails stood stiff around the pond",
        far_side="a hummock of snow by the black ice",
        dusk_image="the ice sang under the moon",
        tags={"ice", "winter"},
    ),
    "stone_ravine": Setting(
        id="stone_ravine",
        place="the Stone Ravine",
        crossing_options={"crumbly_ledge"},
        shore_text="the wind moved through the pines above the ravine",
        far_side="a jut of rock where shadows pooled",
        dusk_image="the ravine held the night like a bowl",
        tags={"ravine", "stone"},
    ),
}

LURES = {
    "glass_fish": Lure(
        id="glass_fish",
        label="the glass fish charm",
        appearance="a little fish of green glass, turning by itself in the fading light",
        call="a faint chiming, as if tiny bells were hidden inside it",
        desire=2,
        tags={"shiny", "strange"},
    ),
    "laughing_lantern_seed": Lure(
        id="laughing_lantern_seed",
        label="the laughing lantern seed",
        appearance="a golden seed that blinked on and off like a lantern with a heartbeat",
        call="a merry sound that did not belong to any bird, brook, or beast",
        desire=3,
        tags={"light", "strange"},
    ),
    "whistling_shell": Lure(
        id="whistling_shell",
        label="the whistling shell",
        appearance="a pale shell that shone where no sea had ever been",
        call="a thin song, sweeter than a flute and stranger than wind in a hollow bone",
        desire=2,
        tags={"music", "strange"},
    ),
}

CROSSINGS = {
    "rotten_log": Crossing(
        id="rotten_log",
        label="the rotten log",
        over="the marsh water",
        risk=2,
        break_text="The bark rolled under his weight, the wet wood split, and the whole log turned like a bad thought beneath his paws.",
        harm="soaked",
        ending_kind="soaked",
        tags={"water", "fall"},
    ),
    "thin_ice": Crossing(
        id="thin_ice",
        label="the thin ice",
        over="the pond",
        risk=2,
        break_text="The skin of ice gave one sharp cry and shattered into dark plates around him.",
        harm="soaked",
        ending_kind="soaked",
        tags={"ice", "fall"},
    ),
    "crumbly_ledge": Crossing(
        id="crumbly_ledge",
        label="the crumbly ledge",
        over="the ravine",
        risk=3,
        break_text="The ledge sighed, then broke away in a shower of pebbles, and the cliff spat him downward.",
        harm="stranded",
        ending_kind="stranded",
        tags={"cliff", "fall"},
    ),
}

ELDERS = {
    "raven_grandam": Elder(
        id="raven_grandam",
        type="raven",
        label="Raven-Grandam",
        voice="hoarse old voice",
        wisdom="slow feet on a safe path beat quick feet on a foolish one",
        tags={"elder", "warning"},
    ),
    "owl_uncle": Elder(
        id="owl_uncle",
        type="owl",
        label="Owl-Uncle",
        voice="round, patient voice",
        wisdom="the night keeps what it tempts the proud to grab",
        tags={"elder", "warning"},
    ),
    "fox_aunt": Elder(
        id="fox_aunt",
        type="fox",
        label="Fox-Aunt",
        voice="low amber voice",
        wisdom="not every shining thing is meant to be carried home",
        tags={"elder", "warning"},
    ),
}

NAMES = ["Brindle", "Ash", "Stripe", "Moss", "Tawny", "Quickpaw", "Briar"]
TRAITS = ["proud", "restless", "vain", "greedy"]


@dataclass
class StoryParams:
    setting: str
    lure: str
    crossing: str
    hero_name: str
    hero_trait: str
    elder: str
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
    "bobcat": [
        (
            "What is a bobcat?",
            "A bobcat is a wild cat with tufted ears, sharp claws, and a short tail. It lives outdoors and hunts quietly."
        )
    ],
    "strange": [
        (
            "What does bizarre mean?",
            "Bizarre means very strange or unusual. Something bizarre may feel surprising because it does not look or sound the way you expect."
        )
    ],
    "warning": [
        (
            "Why should you listen to a wise warning?",
            "A wise warning can keep you from walking into danger you have not noticed yet. Listening first is often safer than rushing first."
        )
    ],
    "ice": [
        (
            "Why is thin ice dangerous?",
            "Thin ice can break under weight without much warning. If it breaks, the water underneath is very cold and hard to climb out of."
        )
    ],
    "water": [
        (
            "Why is cold water dangerous at night?",
            "Cold water can make your body lose heat very fast. At night it is harder to find help and get warm again."
        )
    ],
    "cliff": [
        (
            "Why is a cliff ledge dangerous?",
            "A narrow cliff ledge can crumble or leave you with no safe place to stand. One bad step can trap you far from help."
        )
    ],
    "pride": [
        (
            "Why can pride cause trouble?",
            "Pride can make someone ignore good advice because they want to prove too much. Then they may choose a risky path just to look bold."
        )
    ],
}
KNOWLEDGE_ORDER = ["bobcat", "strange", "warning", "ice", "water", "cliff", "pride"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    lure = f["lure"]
    crossing = f["crossing_cfg"]
    elder = f["elder"]
    return [
        (
            f'Write a short folk tale for a 3-to-5-year-old that includes the words '
            f'"bobcat" and "bizarre" and ends badly.'
        ),
        (
            f"Tell a cautionary tale about a young bobcat named {hero.id} who ignores "
            f"{elder.label}'s warning and chases {lure.label} across {crossing.label} at {setting.place}."
        ),
        (
            f"Write a simple folk-style story where pride pulls a bobcat toward a bizarre wonder, "
            f"and the ending shows clearly why the safe path mattered."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    setting = f["setting"]
    lure = f["lure"]
    crossing = f["crossing_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young bobcat named {hero.id} and {elder.label}, the elder who warned him. "
            f"The tale happens beside {setting.place} at dusk."
        ),
        (
            f"What strange thing did {hero.id} see?",
            f"He saw {lure.label}, which looked and sounded wonderfully odd. "
            f"Its bizarre shine made him want to carry it home and be admired."
        ),
        (
            f"Why did {elder.label} warn {hero.id} not to cross?",
            (
                f"{elder.label} knew that {crossing.label} was unsafe at dusk. "
                + (
                    "In the world model, even a quick test of that crossing ends with a fall into cold water."
                    if f["predicted_wet"]
                    else "In the world model, even a quick test of that crossing ends with the bobcat stranded above the dark stones."
                )
            ),
        ),
        (
            f"Why did {hero.id} ignore the warning?",
            f"He wanted the strange prize so badly that pride pushed harder than caution. "
            f"He thought wise elders feared shadows, so he leapt before he listened."
        ),
    ]
    if f["soaked"]:
        qa.append(
            (
                f"What happened when {hero.id} stepped onto {crossing.label}?",
                f"{crossing.label.capitalize()} gave way and threw him into the cold below. "
                f"He lost the prize at once, and the water left him shivering and ashamed."
            )
        )
    if f["stranded"]:
        qa.append(
            (
                f"What happened when {hero.id} stepped onto {crossing.label}?",
                f"The ledge broke apart and dropped him onto a narrow shelf of stone. "
                f"He could not reach the prize or climb home by himself, so he spent the night cold and hungry."
            )
        )
    qa.append(
        (
            "How did the story end?",
            (
                f"It ended badly: {hero.id} did not come back proud and triumphant. "
                + (
                    "He came back wet, empty-pawed, and talked about for all the wrong reasons."
                    if f["soaked"]
                    else "He came back after a hard, hungry night, and the valley remembered his foolish choice."
                )
            ),
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bobcat", "strange", "warning", "pride"}
    crossing = world.facts["crossing_cfg"]
    if crossing.id == "thin_ice":
        tags.add("ice")
        tags.add("water")
    elif crossing.id == "rotten_log":
        tags.add("water")
    else:
        tags.add("cliff")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="reed_marsh",
        lure="laughing_lantern_seed",
        crossing="rotten_log",
        hero_name="Brindle",
        hero_trait="proud",
        elder="raven_grandam",
        seed=1,
    ),
    StoryParams(
        setting="frost_pond",
        lure="glass_fish",
        crossing="thin_ice",
        hero_name="Ash",
        hero_trait="vain",
        elder="owl_uncle",
        seed=2,
    ),
    StoryParams(
        setting="stone_ravine",
        lure="whistling_shell",
        crossing="crumbly_ledge",
        hero_name="Briar",
        hero_trait="greedy",
        elder="fox_aunt",
        seed=3,
    ),
]


ASP_RULES = r"""
valid(S,L,C) :- setting(S), lure(L), crossing(C), allows(S,C).

ending_kind(C,soaked)   :- crossing(C), risk(C,2).
ending_kind(C,stranded) :- crossing(C), risk(C,3).

#show valid/3.
#show ending_kind/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for crossing_id in sorted(setting.crossing_options):
            lines.append(asp.fact("allows", setting_id, crossing_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for crossing_id, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", crossing_id))
        lines.append(asp.fact("risk", crossing_id, crossing.risk))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending_kinds() -> dict[str, str]:
    import asp

    model = asp.one_model(asp_program())
    return {crossing: kind for crossing, kind in asp.atoms(model, "ending_kind")}


def outcome_of(params: StoryParams) -> str:
    crossing = CROSSINGS[params.crossing]
    return crossing.ending_kind


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

    py_endings = {cid: c.ending_kind for cid, c in CROSSINGS.items()}
    cl_endings = asp_ending_kinds()
    if py_endings == cl_endings:
        print(f"OK: crossing ending kinds match ({sorted(py_endings)}).")
    else:
        rc = 1
        print("MISMATCH in crossing endings:")
        print("  clingo:", cl_endings)
        print("  python:", py_endings)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        if not buf.getvalue().strip():
            raise StoryError("emit() produced no text")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about a bobcat, a bizarre lure, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.crossing:
        setting = SETTINGS[args.setting]
        crossing = CROSSINGS[args.crossing]
        if not crossing_fits(setting, crossing):
            raise StoryError(explain_rejection(setting, crossing))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.lure is None or combo[1] == args.lure)
        and (args.crossing is None or combo[2] == args.crossing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, lure_id, crossing_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting_id,
        lure=lure_id,
        crossing=crossing_id,
        hero_name=args.name or rng.choice(NAMES),
        hero_trait=rng.choice(TRAITS),
        elder=args.elder or rng.choice(sorted(ELDERS)),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Unknown crossing: {params.crossing})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")

    setting = SETTINGS[params.setting]
    lure = LURES[params.lure]
    crossing = CROSSINGS[params.crossing]
    if not crossing_fits(setting, crossing):
        raise StoryError(explain_rejection(setting, crossing))

    world = tell(
        setting=setting,
        lure=lure,
        crossing=crossing,
        hero_name=params.hero_name,
        hero_trait=params.hero_trait,
        elder_id=params.elder,
        seed=params.seed,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        endings = asp_ending_kinds()
        print(f"{len(combos)} compatible (setting, lure, crossing) combos:\n")
        for setting, lure, crossing in combos:
            print(f"  {setting:12} {lure:22} {crossing:14} -> {endings.get(crossing, '?')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.hero_name}: {p.setting}, {p.lure}, {p.crossing} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
