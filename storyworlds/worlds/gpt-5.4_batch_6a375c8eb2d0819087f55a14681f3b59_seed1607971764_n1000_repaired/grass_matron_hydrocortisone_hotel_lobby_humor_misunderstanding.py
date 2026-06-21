#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py
================================================================================================

A small storyworld about a child who comes into a hotel lobby with an itchy rash
after brushing against decorative grass. A kindly but grand hotel matron mishears
the word "hydrocortisone," fetches the wrong thing in a comic folk-tale manner,
and the misunderstanding is cleared before the itch grows worse.

The world model tracks physical meters like itch and redness, and emotional memes
like worry, care, and amusement. The prose is rendered from simulated state, not
from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py --grass fountain_grass
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py --grass burr_grass
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py --all
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py --qa --json
    python storyworlds/worlds/gpt-5.4/grass_matron_hydrocortisone_hotel_lobby_humor_misunderstanding.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman", "matron"}
        male = {"boy", "father", "man", "bellboy", "porter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"matron": "matron"}.get(self.type, self.type)
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
class Grass:
    id: str
    label: str
    place: str
    touch: str
    rash_risk: int
    burrs: bool = False
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
class Misunderstanding:
    id: str
    heard_as: str
    fetched_item: str
    display: str
    confusion: int
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
    sense: int
    suited_for_rash: bool
    suited_for_burrs: bool
    action: str
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


def _r_scratch(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["itch"] >= THRESHOLD and hero.meters["relief"] < THRESHOLD:
        sig = ("scratch", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["scratching"] += 1
            hero.meters["redness"] += 1
            hero.memes["worry"] += 1
            out.append("__scratch__")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    matron = world.get("matron")
    if hero.memes["confusion"] >= THRESHOLD and world.facts.get("clarified"):
        sig = ("laugh", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["amusement"] += 1
            matron.memes["amusement"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule(name="scratch", tag="physical", apply=_r_scratch),
    Rule(name="laughter", tag="social", apply=_r_laughter),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def grass_needs_rash_care(grass: Grass) -> bool:
    return grass.rash_risk >= 2 and not grass.burrs


def remedy_fits(grass: Grass, remedy: Remedy) -> bool:
    if grass.burrs:
        return remedy.suited_for_burrs
    return grass_needs_rash_care(grass) and remedy.suited_for_rash


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for grass_id, grass in GRASSES.items():
        for remedy_id, remedy in REMEDIES.items():
            if remedy.sense >= SENSE_MIN and remedy_fits(grass, remedy):
                combos.append((grass_id, remedy_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    if helper.clarifies >= misunderstanding.confusion:
        return "quick"
    return "comic"


def predict_need(world: World, grass: Grass, remedy: Remedy) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["itch"] = float(grass.rash_risk)
    propagate(sim, narrate=False)
    return {
        "itch": hero.meters["itch"],
        "redness": hero.meters["redness"],
        "needs_rash_care": remedy.suited_for_rash and grass_needs_rash_care(grass),
        "needs_burr_care": remedy.suited_for_burrs and grass.burrs,
    }


def lobby_opening(world: World, hero: Entity, matron: Entity, grass: Grass) -> None:
    world.say(
        f"In the old days, when brass lamps shone like moons and every hotel lobby "
        f"had a carpet thick as bread, {hero.id} came hurrying in from {grass.place}."
    )
    world.say(
        f"The child had brushed against {grass.label}, and {grass.touch}. At the great desk "
        f"stood the hotel matron, straight as a candle and twice as watchful."
    )


def itch_begins(world: World, hero: Entity, grass: Grass) -> None:
    hero.meters["itch"] = float(grass.rash_risk)
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} tried to stand still with good manners, but one ankle kept twitching, "
        f"for the {grass.label} had left a lively itch."
    )
    propagate(world, narrate=False)
    if hero.meters["redness"] >= THRESHOLD:
        world.say(
            f"Soon there was a pink place on the skin, made redder by nervous scratching."
        )


def ask_for_help(world: World, hero: Entity) -> None:
    world.say(
        f'"Please," said {hero.id}, "have you any hydrocortisone? I brushed the grass, and now I itch."'
    )


def misunderstanding_beat(world: World, hero: Entity, matron: Entity,
                          misunderstanding: Misunderstanding) -> None:
    hero.memes["confusion"] += 1
    matron.memes["duty"] += 1
    world.say(
        f'The matron blinked. She heard "{misunderstanding.heard_as}" where {hero.id} had said '
        f'"hydrocortisone," and because she was a matron who liked to solve troubles fast, '
        f"she swept away and returned with {misunderstanding.display}."
    )
    world.say(
        f'"Here it is," she declared, holding up {misunderstanding.fetched_item}. '
        f'"A fine thing indeed."'
    )


def helper_clarifies(world: World, hero: Entity, matron: Entity, helper: Entity,
                     grass: Grass, remedy: Remedy) -> None:
    world.facts["clarified"] = True
    helper.memes["care"] += 1
    matron.memes["care"] += 1
    world.say(
        f"But the {helper.label} looked from the item to {hero.id}'s ankle and bowed a little. "
        f'"Matron," {helper.pronoun()} said, "the child does not need a treasure. '
        f'{hero.pronoun().capitalize()} needs {remedy.label} for an itchy patch from the grass."'
    )
    if grass.burrs:
        world.say(
            f'The matron peered closer and saw the tiny burr still clinging there. '
            f'"Ah," she said, "first the burr, then the balm."'
        )
    else:
        world.say(
            f'The matron peered closer and saw that the trouble was only skin-deep. '
            f'"Ah," she said, "not a jewel at all, but a cream from the first-aid drawer."'
        )


def hero_points(world: World, hero: Entity, matron: Entity, grass: Grass, remedy: Remedy) -> None:
    world.facts["clarified"] = True
    hero.memes["bravery"] += 1
    matron.memes["care"] += 1
    world.say(
        f"No helper understood at once, so {hero.id} took a brave breath and pointed to the itchy place."
    )
    if grass.burrs:
        world.say(
            f'"Not {misquote(remedy.label)} for a crown," said {hero.id}, trying not to laugh. '
            f'"First please pull out the little burr, and then the hydrocortisone."'
        )
    else:
        world.say(
            f'"Not for a royal stone," said {hero.id}, trying not to giggle. '
            f'"Only hydrocortisone for the rash from the grass."'
        )
    world.say(
        f'Then the matron understood and pressed one hand to her heart. '
        f'"Child," she said, "I have been listening with my ears and not with my eyes."'
    )


def misquote(label: str) -> str:
    if "hydrocortisone" in label:
        return "hydrocortisone"
    return label


def apply_remedy(world: World, hero: Entity, matron: Entity, grass: Grass, remedy: Remedy) -> None:
    if grass.burrs:
        hero.meters["burr"] = 1.0
        world.say(
            f"The matron fetched tweezers first, lifted the little burr away, and only then {remedy.action}."
        )
        hero.meters["burr"] = 0.0
    else:
        world.say(
            f"Then the matron {remedy.action}."
        )
    hero.meters["relief"] += 1
    hero.meters["itch"] = max(0.0, hero.meters["itch"] - 2.0)
    hero.meters["redness"] = max(0.0, hero.meters["redness"] - 1.0)
    hero.memes["worry"] = 0.0
    hero.memes["comfort"] += 1
    propagate(world, narrate=False)


def closing(world: World, hero: Entity, matron: Entity, helper: Optional[Entity],
            misunderstanding: Misunderstanding) -> None:
    if world.facts.get("clarified"):
        propagate(world, narrate=False)
    world.say(
        f"In a little while the itch quieted, as if a noisy cricket had gone to sleep."
    )
    if helper is not None and helper.id in world.entities and helper.role == "helper":
        world.say(
            f"{hero.id}, the matron, and the {helper.label} all smiled at the mix-up about "
            f'"{misunderstanding.heard_as}."'
        )
    else:
        world.say(
            f"{hero.id} and the matron smiled at the mix-up and let the grand old lobby keep the secret."
        )
    world.say(
        f"And there, under the tall palms by the carpeted stair, the child sat peacefully at last, "
        f"with unscratchy ankles and a new story to tell."
    )


@dataclass
class StoryParams:
    grass: str
    misunderstanding: str
    remedy: str
    helper: str
    hero_name: str
    hero_gender: str
    matron_style: str
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


def tell(grass: Grass, misunderstanding: Misunderstanding, remedy: Remedy,
         helper_cfg: "Helper", hero_name: str = "Nell", hero_type: str = "girl",
         matron_style: str = "stately", seed: Optional[int] = None) -> World:
    world = World()
    world.facts["clarified"] = False

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["traveling", "polite"],
        attrs={"seed": seed or 0},
    ))
    matron = world.add(Entity(
        id="Matron",
        kind="character",
        type="matron",
        role="matron",
        label="matron",
        traits=[matron_style],
        attrs={"drawer": "first-aid drawer"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.person_type,
        role="helper",
        label=helper_cfg.label,
        traits=[helper_cfg.style],
        attrs={},
    ))

    hero.meters["itch"] = 0.0
    hero.meters["redness"] = 0.0
    hero.meters["relief"] = 0.0
    hero.meters["scratching"] = 0.0
    hero.meters["burr"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["confusion"] = 0.0
    hero.memes["amusement"] = 0.0
    hero.memes["comfort"] = 0.0
    hero.memes["bravery"] = 0.0
    matron.memes["care"] = 0.0
    matron.memes["duty"] = 0.0
    matron.memes["amusement"] = 0.0
    helper.memes["care"] = 0.0

    lobby_opening(world, hero, matron, grass)
    itch_begins(world, hero, grass)

    world.para()
    ask_for_help(world, hero)
    misunderstanding_beat(world, hero, matron, misunderstanding)

    world.para()
    if helper_cfg.clarifies >= misunderstanding.confusion:
        helper_clarifies(world, hero, matron, helper, grass, remedy)
    else:
        hero_points(world, hero, matron, grass, remedy)
    apply_remedy(world, hero, matron, grass, remedy)

    world.para()
    closing(world, hero, matron, helper, misunderstanding)

    world.facts.update(
        hero=hero,
        matron=matron,
        helper=helper,
        grass=grass,
        misunderstanding=misunderstanding,
        remedy=remedy,
        outcome=outcome_of(StoryParams(
            grass=grass.id,
            misunderstanding=misunderstanding.id,
            remedy=remedy.id,
            helper=helper_cfg.id,
            hero_name=hero_name,
            hero_gender=hero_type,
            matron_style=matron_style,
            seed=seed,
        )),
        needed_burr_help=grass.burrs,
        needed_rash_help=grass_needs_rash_care(grass),
        scratched=hero.meters["scratching"] >= THRESHOLD,
        relieved=hero.meters["relief"] >= THRESHOLD,
    )
    return world


GRASSES = {
    "fountain_grass": Grass(
        id="fountain_grass",
        label="the fountain grass",
        place="the little courtyard beside the hotel lobby",
        touch="its feathery leaves brushed the child's bare ankle",
        rash_risk=2,
        burrs=False,
        tags={"grass", "itch", "rash"},
    ),
    "reed_grass": Grass(
        id="reed_grass",
        label="the tall reed grass",
        place="the tiled path just outside the revolving door",
        touch="its narrow blades whisked over the child's skin like tiny brooms",
        rash_risk=3,
        burrs=False,
        tags={"grass", "itch", "rash"},
    ),
    "burr_grass": Grass(
        id="burr_grass",
        label="the burr grass",
        place="the stone edge of the hotel garden",
        touch="one clingy burr rode in on the sock and pricked the ankle",
        rash_risk=1,
        burrs=True,
        tags={"grass", "burr", "itch"},
    ),
    "soft_lawn": Grass(
        id="soft_lawn",
        label="the soft lawn grass",
        place="the strip of lawn in front of the hotel steps",
        touch="it bent underfoot and did no more than tickle",
        rash_risk=1,
        burrs=False,
        tags={"grass"},
    ),
}

MISUNDERSTANDINGS = {
    "hide_court_stone": Misunderstanding(
        id="hide_court_stone",
        heard_as="hide-court-a-stone",
        fetched_item="a polished pebble in a velvet ring",
        display="a polished pebble wrapped in hotel ribbon",
        confusion=3,
        tags={"misunderstanding", "humor"},
    ),
    "high_curtain_scone": Misunderstanding(
        id="high_curtain_scone",
        heard_as="high-curtain scone",
        fetched_item="a little tea scone from the breakfast tray",
        display="a small warm scone on a silver saucer",
        confusion=2,
        tags={"misunderstanding", "humor"},
    ),
    "hydra_court_song": Misunderstanding(
        id="hydra-court-song",
        heard_as="hydra court song",
        fetched_item="a brass music box shaped like a dragon",
        display="a brass music box that chimed one proud note",
        confusion=3,
        tags={"misunderstanding", "humor"},
    ),
}

REMEDIES = {
    "hydrocortisone": Remedy(
        id="hydrocortisone",
        label="hydrocortisone",
        sense=3,
        suited_for_rash=True,
        suited_for_burrs=True,
        action="opened the first-aid drawer, dabbed on a little hydrocortisone, and fanned the spot with a folded card",
        qa_text="She dabbed on hydrocortisone from the first-aid drawer to calm the itchy skin.",
        tags={"hydrocortisone", "cream", "first_aid"},
    ),
    "cool_cloth": Remedy(
        id="cool_cloth",
        label="a cool cloth",
        sense=2,
        suited_for_rash=False,
        suited_for_burrs=False,
        action="pressed on a cool cloth",
        qa_text="She pressed on a cool cloth.",
        tags={"first_aid"},
    ),
    "tweezers_only": Remedy(
        id="tweezers_only",
        label="tweezers",
        sense=2,
        suited_for_rash=False,
        suited_for_burrs=True,
        action="used the tweezers and left the skin clean",
        qa_text="She used tweezers to remove the burr.",
        tags={"burr", "first_aid"},
    ),
}

@dataclass
class Helper:
    id: str
    label: str
    person_type: str
    clarifies: int
    style: str
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


HELPERS = {
    "bellboy": Helper(
        id="bellboy",
        label="bellboy",
        person_type="bellboy",
        clarifies=3,
        style="quick-eyed",
        tags={"helper", "hotel"},
    ),
    "porter": Helper(
        id="porter",
        label="porter",
        person_type="porter",
        clarifies=2,
        style="steady",
        tags={"helper", "hotel"},
    ),
    "page": Helper(
        id="page",
        label="page",
        person_type="boy",
        clarifies=1,
        style="earnest",
        tags={"helper", "hotel"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Tess", "Wren", "Lila", "Mina", "Rose", "Ada"]
BOY_NAMES = ["Finn", "Tobin", "Leo", "Milo", "Ned", "Jory", "Bram", "Owen"]
MATRON_STYLES = ["stately", "brisk", "kindly", "grand"]


KNOWLEDGE = {
    "grass": [
        (
            "Can grass make your skin itch?",
            "Yes, some kinds of grass can brush the skin and leave it itchy or red. Tiny hairs, rough edges, or bits stuck to the skin can bother you."
        )
    ],
    "rash": [
        (
            "What is a rash?",
            "A rash is a patch of skin that looks red or feels itchy or sore. It means the skin is irritated and needs gentle care."
        )
    ],
    "hydrocortisone": [
        (
            "What is hydrocortisone?",
            "Hydrocortisone is a cream grown-ups sometimes use on itchy skin. It can help calm redness and itching when a doctor or trusted grown-up says it is the right thing to use."
        )
    ],
    "first_aid": [
        (
            "What should you do if your skin gets itchy after touching a plant?",
            "Tell a grown-up and show them the itchy place. A grown-up can wash the skin, look for anything stuck there, and choose the safest help."
        )
    ],
    "burr": [
        (
            "What is a burr from grass?",
            "A burr is a tiny rough seed or bit from a plant that can cling to socks or fur. If it pokes the skin, it should be removed gently."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when one person means one thing and another person hears or thinks something else. Asking a calm question can clear it up."
        )
    ],
    "hotel": [
        (
            "What is a hotel lobby?",
            "A hotel lobby is the big room near the front desk where guests come in, wait, and ask for help. It is often the first room people see in a hotel."
        )
    ],
}
KNOWLEDGE_ORDER = ["hotel", "grass", "rash", "hydrocortisone", "burr", "misunderstanding", "first_aid"]


CURATED = [
    StoryParams(
        grass="fountain_grass",
        misunderstanding="high_curtain_scone",
        remedy="hydrocortisone",
        helper="porter",
        hero_name="Nell",
        hero_gender="girl",
        matron_style="stately",
        seed=1,
    ),
    StoryParams(
        grass="reed_grass",
        misunderstanding="hide_court_stone",
        remedy="hydrocortisone",
        helper="bellboy",
        hero_name="Finn",
        hero_gender="boy",
        matron_style="grand",
        seed=2,
    ),
    StoryParams(
        grass="burr_grass",
        misunderstanding="hydra-court-song",
        remedy="hydrocortisone",
        helper="page",
        hero_name="Mira",
        hero_gender="girl",
        matron_style="kindly",
        seed=3,
    ),
]


def explain_rejection(grass: Grass, remedy: Remedy) -> str:
    if grass.burrs and not remedy.suited_for_burrs:
        return (
            f"(No story: {grass.label} leaves a prickly burr, so {remedy.label} is not enough on its own. "
            f"Pick a remedy that can follow burr removal.)"
        )
    if not grass_needs_rash_care(grass):
        return (
            f"(No story: {grass.label} only tickles lightly here, so there is no honest need for hydrocortisone or a first-aid scene. "
            f"Choose a grass that truly causes an itch.)"
        )
    if not remedy.suited_for_rash:
        return (
            f"(No story: {remedy.label} does not actually treat the itchy rash caused by {grass.label}. "
            f"Choose a remedy that fits the problem.)"
        )
    return "(No story: that combination is not a reasonable little tale.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    grass = f["grass"]
    misunderstanding = f["misunderstanding"]
    return [
        'Write a folk-tale-style story for a 3-to-5-year-old set in a hotel lobby that includes the words "grass" and "hydrocortisone".',
        f"Tell a humorous misunderstanding story in a hotel lobby where {hero.id} asks for hydrocortisone after brushing against {grass.label}, and the matron hears {misunderstanding.heard_as} instead.",
        "Write a gentle folk tale where a careful grown-up first gets the wrong idea, then looks closely, helps the child, and everyone ends with a laugh.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    matron = f["matron"]
    helper = f["helper"]
    grass = f["grass"]
    misunderstanding = f["misunderstanding"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in a hotel lobby, and the hotel matron who tries to help. The {helper.label} also helps the misunderstanding get sorted out."
        ),
        (
            f"Why did {hero.id} ask for help?",
            f"{hero.id} had brushed against {grass.label}, and the skin began to itch and turn pink. That is why the child asked for hydrocortisone in the lobby."
        ),
        (
            "What was the misunderstanding?",
            f'The matron did not hear "hydrocortisone" correctly. She heard "{misunderstanding.heard_as}" instead, so she brought the wrong thing before looking closely.'
        ),
    ]
    if f.get("outcome") == "quick":
        qa.append(
            (
                f"How was the problem solved?",
                f"The {helper.label} noticed the itchy ankle and explained what {hero.id} really meant. Then the matron used {remedy.label}, so the itch quieted down."
            )
        )
    else:
        qa.append(
            (
                f"How was the problem solved after the mix-up lasted longer?",
                f"{hero.id} bravely pointed to the itchy place and explained the trouble clearly. Then the matron understood, used {remedy.label}, and the funny mistake turned into a laugh."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended peacefully in the hotel lobby, with the itch calmed and the misunderstanding cleared. The ending image shows {hero.id} resting without scratching while the grown-ups smile."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hotel", "misunderstanding", "first_aid"} | set(world.facts["grass"].tags) | set(world.facts["remedy"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts={{outcome: {world.facts.get('outcome')}, clarified: {world.facts.get('clarified')}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- gate --------------------------------------------------------------
needs_rash_care(G) :- grass(G), rash_risk(G, R), R >= 2, not burrs(G).
fits(G, Rm) :- remedy(Rm), grass(G), burrs(G), suited_for_burrs(Rm).
fits(G, Rm) :- remedy(Rm), grass(G), needs_rash_care(G), suited_for_rash(Rm).
sensible(Rm) :- remedy(Rm), sense(Rm, S), sense_min(M), S >= M.
valid(G, Rm) :- grass(G), remedy(Rm), sensible(Rm), fits(G, Rm).

% --- misunderstanding outcome -----------------------------------------
quick :- chosen_helper(H), clarifies(H, C), chosen_misunderstanding(Ms), confusion(Ms, X), C >= X.
comic :- not quick.

outcome(quick) :- quick.
outcome(comic) :- comic.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, grass in GRASSES.items():
        lines.append(asp.fact("grass", gid))
        lines.append(asp.fact("rash_risk", gid, grass.rash_risk))
        if grass.burrs:
            lines.append(asp.fact("burrs", gid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        if remedy.suited_for_rash:
            lines.append(asp.fact("suited_for_rash", rid))
        if remedy.suited_for_burrs:
            lines.append(asp.fact("suited_for_burrs", rid))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("confusion", mid, mis.confusion))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("clarifies", hid, helper.clarifies))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_misunderstanding", params.misunderstanding),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: an itchy child, a hotel lobby matron, hydrocortisone, and a comic misunderstanding."
    )
    ap.add_argument("--grass", choices=GRASSES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--matron-style", choices=MATRON_STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible grass/remedy set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.grass and args.remedy:
        grass = GRASSES[args.grass]
        remedy = REMEDIES[args.remedy]
        if remedy.sense < SENSE_MIN or not remedy_fits(grass, remedy):
            raise StoryError(explain_rejection(grass, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.grass is None or combo[0] == args.grass)
        and (args.remedy is None or combo[1] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    grass_id, remedy_id = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    matron_style = args.matron_style or rng.choice(MATRON_STYLES)
    return StoryParams(
        grass=grass_id,
        misunderstanding=misunderstanding,
        remedy=remedy_id,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        matron_style=matron_style,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.grass not in GRASSES:
        raise StoryError(f"(Unknown grass: {params.grass})")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Unknown misunderstanding: {params.misunderstanding})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    grass = GRASSES[params.grass]
    remedy = REMEDIES[params.remedy]
    if remedy.sense < SENSE_MIN or not remedy_fits(grass, remedy):
        raise StoryError(explain_rejection(grass, remedy))

    world = tell(
        grass=grass,
        misunderstanding=MISUNDERSTANDINGS[params.misunderstanding],
        remedy=remedy,
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        matron_style=params.matron_style,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_remedies()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible remedies match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            ns = build_parser().parse_args([])
            params = resolve_params(ns, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (grass, remedy) combos:\n")
        for grass, remedy in combos:
            print(f"  {grass:15} {remedy}")
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
            header = f"### {p.hero_name}: {p.grass} / {p.misunderstanding} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
