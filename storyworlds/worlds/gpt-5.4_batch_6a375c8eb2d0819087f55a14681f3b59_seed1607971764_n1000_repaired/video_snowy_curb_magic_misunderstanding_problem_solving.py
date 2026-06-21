#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py
=====================================================================================

A standalone story world for a snowy-curb tale about a child who mistakes a
muffled video for magic, edges toward danger, and then solves the problem with
help and careful thinking.

Run it
------
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py --theme ice_pirates --source phone --spot snowbank
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py --spot storm_drain
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py --method reach_with_hand
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/video_snowy_curb_magic_misunderstanding_problem_solving.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    buried: bool = False
    plays_video: bool = False
    icy: bool = False
    long_reach: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "crossing_guard": "crossing guard",
            "shopkeeper": "shopkeeper",
            "neighbor": "neighbor",
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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    place_word: str
    role_solo: str
    role_plural: str
    send_off: str
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


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    owner: str
    glow: str
    sound: str
    reveal: str
    video: str
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
class Spot:
    id: str
    label: str
    the: str
    detail: str
    depth: int
    icy: bool
    slip_risk: int
    reveal_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Method:
    id: str
    sense: int
    reach: int
    text: str
    fail: str
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
class HelperCfg:
    id: str
    type: str
    entrance: str
    calm_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    spot = world.entities.get("spot")
    if not source or not spot:
        return out
    if source.meters["playing"] < THRESHOLD or spot.meters["covered"] < THRESHOLD:
        return out
    sig = ("mystery", source.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["wonder"] += 1
    out.append("__mystery__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    curb = world.entities.get("curb")
    instigator = world.entities.get("instigator")
    if not curb or not instigator:
        return out
    if curb.meters["slippery"] < THRESHOLD or instigator.meters["off_curb"] < THRESHOLD:
        return out
    sig = ("slip", instigator.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    instigator.meters["slipped"] += 1
    instigator.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__slip__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if not source or source.meters["found"] < THRESHOLD:
        return out
    sig = ("relief", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mystery", tag="emotional", apply=_r_mystery),
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def mystery_possible(source: Source, spot: Spot) -> bool:
    return bool(source.video and spot.depth >= 1)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def any_sensible_reaches(spot: Spot) -> bool:
    return any(m.reach >= spot.depth for m in sensible_methods())


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for source_id, source in SOURCES.items():
            for spot_id, spot in SPOTS.items():
                if mystery_possible(source, spot) and any_sensible_reaches(spot):
                    combos.append((theme_id, source_id, spot_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_wait(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def method_reaches(method: Method, spot: Spot) -> bool:
    return method.reach >= spot.depth


def outcome_of(params: "StoryParams") -> str:
    if would_wait(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "wait_safe" if method_reaches(METHODS[params.method], SPOTS[params.spot]) else "stuck"
    if SPOTS[params.spot].icy and SPOTS[params.spot].slip_risk > 0:
        return "stumble_safe" if method_reaches(METHODS[params.method], SPOTS[params.spot]) else "stuck"
    return "quick_safe" if method_reaches(METHODS[params.method], SPOTS[params.spot]) else "stuck"


def predict_trouble(world: World, spot_id: str) -> dict:
    sim = world.copy()
    sim.get("instigator").meters["off_curb"] += 1
    propagate(sim, narrate=False)
    return {
        "slip": sim.get("instigator").meters["slipped"] >= THRESHOLD,
        "fear": sim.get("instigator").memes["fear"],
        "spot": spot_id,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright winter afternoon, {a.id} and {b.id} turned the snowy curb into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s guard {theme.goal}!"'
    )


def notice_signal(world: World, b: Entity, source: Source, spot: Spot) -> None:
    spot_ent = world.get("spot")
    source_ent = world.get("source")
    spot_ent.meters["covered"] = 1.0
    source_ent.meters["playing"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But near {spot.detail}, something strange winked under the snow. "
        f"{source.glow.capitalize()} blinked through the white crust, and a tiny sound of "
        f"{source.sound} slipped out."
    )
    world.say(f'{b.id} stopped and listened. "Did you hear that? Something is hiding in {spot.the}."')


def guess_magic(world: World, a: Entity, source: Source, theme: Theme) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes went wide. "It must be magic," {a.pronoun()} whispered. '
        f'"Maybe a snow spell is trapped under there. Maybe it wants a rescue video for '
        f'{theme.role_plural}!"'
    )
    world.say("For one shivery moment, the blinking light really did look enchanted.")


def warn(world: World, b: Entity, a: Entity, spot: Spot, helper: Entity) -> None:
    pred = predict_trouble(world, spot.id)
    world.facts["predicted_slip"] = pred["slip"]
    b.memes["caution"] += 1
    extra = ""
    if pred["slip"]:
        extra = f" {b.pronoun().capitalize()} could already picture a boot skidding on the shiny slush."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "{a.id}, don\'t hop off the curb. '
        f'{spot.The} is right by the street, and the snow there is slick."{extra}'
    )
    world.say(
        f'"Let\'s ask the {helper.label_word} and figure it out the careful way," '
        f'{b.pronoun()} said.'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"What if the magic disappears?" {a.id} said. Before {b.id} could stop '
        f'{a.pronoun("object")}, {a.pronoun()} slid one boot off the curb.'
    )


def back_down(world: World, a: Entity, b: Entity, helper: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the gray street, then back at {b.id}. Because {b.id} was '
        f'{a.pronoun("possessive")} older sibling, the warning landed hard.'
    )
    world.say(
        f'"Okay," {a.pronoun()} said at last. "No leaping." They stayed on the sidewalk and waved '
        f'to the {helper.label_word}.'
    )


def slip(world: World, a: Entity, b: Entity, spot: Spot) -> None:
    a.meters["off_curb"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The slush by {spot.the} was slicker than it looked. {a.id}'s boot skidded, "
        f"and {a.pronoun()} windmilled both arms."
    )
    world.say(
        f'"Whoa!" {a.id} yelped, catching the signpost just in time. {b.id} grabbed '
        f'{a.pronoun("possessive")} coat and pulled {a.pronoun("object")} back onto the curb.'
    )


def helper_arrives(world: World, helper: Entity, cfg: HelperCfg) -> None:
    world.say(cfg.entrance)
    world.say(f'"{cfg.calm_line}" the {helper.label_word} said.')


def retrieve(world: World, helper: Entity, method: Method, spot: Spot) -> None:
    source_ent = world.get("source")
    source_ent.meters["found"] += 1
    source_ent.meters["playing"] = 0.0
    propagate(world, narrate=False)
    world.say(f"The {helper.label_word} {method.text.format(spot=spot.label)}.")
    world.say(spot.reveal_line)


def reveal(world: World, source: Source, a: Entity, b: Entity) -> None:
    world.say(
        f"It was not magic at all. It was {source.phrase}, and {source.video} was still playing."
    )
    world.say(
        f"{a.id} and {b.id} stared, then laughed the small shaky laugh that comes after a scare."
    )


def return_owner(world: World, helper: Entity, source: Source) -> None:
    world.say(
        f"A minute later, {source.owner} hurried back looking worried. When the {helper.label_word} "
        f"held up the {source.label}, {source.owner} smiled with such relief that the whole corner felt warmer."
    )
    world.say(
        f'"Thank you for solving it carefully," {source.owner} said. "I thought I had lost my video forever."'
    )


def ending(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"After that, the two {theme.role_plural} made a new rule for their games: magic could wait, "
        f"but slippery curbs could not."
    )
    world.say(
        f'{b.id} drew a rescue badge in the snow with a mittened finger, and {a.id} said, '
        f'"Next time, we solve the mystery before we chase it."'
    )
    world.say(
        f"Then they set off again along the snowy curb, {theme.send_off} -- not wilder, but wiser."
    )
def tell(
    source: Source,
    spot: Spot,
    method: Method,
    helper_cfg: Helper,
    instigator: Instigator,
    instigator_gender: str,
    cautioner: Cautioner,
    cautioner_gender: str,
    trait: Trait,
    relation: Relation,
    instigator_age: InstigatorAge,
    cautioner_age: CautionerAge,
    theme=None,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.id,
        role="helper",
        attrs={"cfg": helper_cfg.id},
    ))
    curb = world.add(Entity(
        id="curb",
        type="curb",
        label="curb",
        icy=spot.icy,
    ))
    curb.meters["slippery"] = 1.0 if spot.icy else 0.0
    world.add(Entity(
        id="source",
        type="device",
        label=source.label,
        buried=True,
        plays_video=True,
    ))
    world.add(Entity(
        id="spot",
        type="spot",
        label=spot.label,
        buried=True,
        icy=spot.icy,
        attrs={"depth": spot.depth},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme)
    notice_signal(world, b, source, spot)

    world.para()
    guess_magic(world, a, source, theme)
    warn(world, b, a, spot, helper)

    waited = would_wait(relation, instigator_age, cautioner_age, trait)
    if waited:
        back_down(world, a, b, helper)
    else:
        defy(world, a, b)
        world.para()
        slip(world, a, b, spot)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    retrieve(world, helper, method, spot)
    reveal(world, source, a, b)
    return_owner(world, helper, source)

    world.para()
    ending(world, a, b, theme)

    outcome = outcome_of(
        StoryParams(
            theme=theme.id,
            source=source.id,
            spot=spot.id,
            method=method.id,
            helper=helper_cfg.id,
            instigator=instigator,
            instigator_gender=instigator_gender,
            cautioner=cautioner,
            cautioner_gender=cautioner_gender,
            trait=trait,
            relation=relation,
            instigator_age=instigator_age,
            cautioner_age=cautioner_age,
            seed=None,
        )
    )
    world.facts.update(
        theme=theme,
        source_cfg=source,
        spot_cfg=spot,
        method_cfg=method,
        helper_cfg=helper_cfg,
        instigator=a,
        cautioner=b,
        helper=helper,
        waited=waited,
        outcome=outcome,
        slip=a.meters["slipped"] >= THRESHOLD,
        solved=world.get("source").meters["found"] >= THRESHOLD,
        relation=relation,
    )
    return world
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


THEMES = {
    "ice_pirates": Theme(
        id="ice_pirates",
        scene="a frost-white harbor",
        rig="A snowbank became their ship, a striped scarf became the captain's rope, and the curb was the dock where winter waves bumped in secret.",
        captain="Captain",
        mate="Lookout",
        goal="the silver dock",
        place_word="dock",
        role_solo="ice pirate",
        role_plural="ice pirates",
        send_off="hunting for snowy secrets",
    ),
    "snow_explorers": Theme(
        id="snow_explorers",
        scene="a map of the far north",
        rig="Their mitten prints were explorer tracks, a sled was their supply ship, and the snowy curb was the edge of an unknown land.",
        captain="Leader",
        mate="Scout",
        goal="the north edge",
        place_word="edge",
        role_solo="snow explorer",
        role_plural="snow explorers",
        send_off="to chart the rest of the white world",
    ),
    "winter_knights": Theme(
        id="winter_knights",
        scene="a bright frozen kingdom",
        rig="A heap of plowed snow became a castle wall, a twig became a banner pole, and the curb marked the kingdom's narrow bridge.",
        captain="Sir",
        mate="Guard",
        goal="the crystal bridge",
        place_word="bridge",
        role_solo="winter knight",
        role_plural="winter knights",
        send_off="to guard the gleaming bridge",
    ),
}

SOURCES = {
    "phone": Source(
        id="phone",
        label="phone",
        phrase="a lost phone in a puffy blue case",
        owner="a bundled-up woman from the bakery",
        glow="a pale rectangle of light",
        sound="muffled singing",
        reveal="The screen shone up through the wet snow.",
        video="a funny dog video",
        tags={"phone", "video", "lost_and_found"},
    ),
    "tablet": Source(
        id="tablet",
        label="tablet",
        phrase="a small tablet with snowflakes stuck to its cover",
        owner="a father carrying grocery bags",
        glow="a warm gold flicker",
        sound="tiny talking voices",
        reveal="A bigger screen slid free, bright and blinking.",
        video="a cartoon video",
        tags={"tablet", "video", "lost_and_found"},
    ),
    "camera": Source(
        id="camera",
        label="camera",
        phrase="a little action camera clipped to a strap",
        owner="a teenager in a red hat",
        glow="a blinking green dot",
        sound="faint chirps",
        reveal="The strap came out first, then the little camera under it.",
        video="a snowboarding video",
        tags={"camera", "video", "lost_and_found"},
    ),
}

SPOTS = {
    "snowbank": Spot(
        id="snowbank",
        label="snowbank",
        the="the snowbank",
        detail="the tallest part of the curbside snowbank",
        depth=1,
        icy=True,
        slip_risk=1,
        reveal_line="With one careful tug, something dark and bright came up from the snow.",
        tags={"snow", "curb"},
    ),
    "plow_ridge": Spot(
        id="plow_ridge",
        label="plow ridge",
        the="the plow ridge",
        detail="the dirty ridge of snow piled beside the curb",
        depth=2,
        icy=True,
        slip_risk=1,
        reveal_line="A hidden shape scraped loose from the packed snow and slid toward the sidewalk.",
        tags={"snow", "curb", "plow"},
    ),
    "storm_drain": Spot(
        id="storm_drain",
        label="storm drain edge",
        the="the storm drain edge",
        detail="the dark grate where the snow thinned near the curb",
        depth=3,
        icy=True,
        slip_risk=2,
        reveal_line="Something glimmered below the grate, but it sat too deep to lift safely from the sidewalk.",
        tags={"snow", "curb", "drain"},
    ),
}

METHODS = {
    "grabber": Method(
        id="grabber",
        sense=3,
        reach=2,
        text="used a long litter grabber from the corner bucket and pinched the hidden thing free from the {spot}",
        fail="tried to pinch the hidden thing free, but it was too deep to reach from the sidewalk",
        qa_text="used a long litter grabber to pull it free",
        tags={"grabber", "tool"},
    ),
    "shovel": Method(
        id="shovel",
        sense=3,
        reach=2,
        text="stood on the safe side of the curb and drew the snow back with a snow shovel until the hidden thing slid close enough to pick up",
        fail="scraped at the snow with a shovel, but the object was still too deep to reach safely",
        qa_text="used a shovel to draw the object toward the sidewalk",
        tags={"shovel", "tool"},
    ),
    "reach_with_hand": Method(
        id="reach_with_hand",
        sense=1,
        reach=1,
        text="leaned down with a bare hand toward the {spot}",
        fail="leaned down with a bare hand, but that was not safe enough near the street",
        qa_text="reached down by hand",
        tags={"hand", "unsafe"},
    ),
}

HELPERS = {
    "crossing_guard": HelperCfg(
        id="crossing_guard",
        type="crossing_guard",
        entrance="Just then the crossing guard by the corner raised one mitten and came over.",
        calm_line="First we keep our boots where the sidewalk is safe. Then we solve the mystery",
        tags={"crossing_guard", "helper"},
    ),
    "shopkeeper": HelperCfg(
        id="shopkeeper",
        type="shopkeeper",
        entrance="The shopkeeper from the little corner store stepped outside with a broom in one hand.",
        calm_line="No rushing into slush. Good problem solvers make a plan first",
        tags={"shopkeeper", "helper"},
    ),
    "neighbor": HelperCfg(
        id="neighbor",
        type="neighbor",
        entrance="A neighbor who was sweeping powder off the steps heard the fuss and came over.",
        calm_line="Let's use our eyes and tools before our feet",
        tags={"neighbor", "helper"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "clever"]


KNOWLEDGE = {
    "video": [(
        "What is a video?",
        "A video is a moving picture you can watch on a screen. Some videos also have music, talking, or funny sounds."
    )],
    "snow": [(
        "Why can snow by the curb be slippery?",
        "Snow by the curb can turn to slush or ice when cars and feet press on it. That makes boots slide more easily."
    )],
    "curb": [(
        "What is a curb for?",
        "A curb is the raised edge between the sidewalk and the street. It helps mark where people walk and where cars drive."
    )],
    "drain": [(
        "What does a storm drain do?",
        "A storm drain lets rain and melting snow flow away so water does not stay on the street. Things can slip near it, so people should be careful."
    )],
    "grabber": [(
        "What is a grabber tool?",
        "A grabber is a long tool that helps you pick something up without bending close or stepping into a risky place. It can help you stay safe while reaching."
    )],
    "shovel": [(
        "What does a snow shovel do?",
        "A snow shovel helps move snow out of the way. It can make a path or pull snow back so something hidden can be seen."
    )],
    "lost_and_found": [(
        "What should you do if you find something that belongs to someone else?",
        "You should give it to a grown-up or a trusted helper and try to return it. That is a kind and careful way to solve the problem."
    )],
    "helper": [(
        "Why is it smart to ask a helper when something seems dangerous?",
        "A helper can slow things down and make a safe plan. Good problem solving means using help when you need it."
    )],
}
KNOWLEDGE_ORDER = ["video", "snow", "curb", "drain", "grabber", "shovel", "lost_and_found", "helper"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    source = f["source_cfg"]
    spot = f["spot_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    if outcome == "wait_safe":
        return [
            f'Write a winter story for a 3-to-5-year-old where children playing {theme.role_plural} hear a strange sound under a snowy curb and think it is magic, but they stop and ask a helper instead. Include the word "video".',
            f"Tell a gentle misunderstanding story where {a.label} thinks a blinking light in {spot.the} is magic, but {b.label}, an older sibling, keeps both of them on the sidewalk until the {helper.id.replace('_', ' ')} helps.",
            "Write a child-facing story about problem solving in winter: a magical guess turns out to be wrong, and careful thinking leads to a happy lost-and-found ending.",
        ]
    return [
        f'Write a snowy-curb story for a 3-to-5-year-old where children playing {theme.role_plural} mistake a muffled video for magic and nearly rush into danger, but a helper solves the mystery safely. Include the word "video".',
        f"Tell a story where {a.label} thinks something magical is trapped in {spot.the}, slips while trying to reach it, and then learns to make a plan with the {helper.id.replace('_', ' ')}.",
        "Write a simple winter tale with magic, misunderstanding, and problem solving, ending with the children wiser than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    theme = f["theme"]
    source = f["source_cfg"]
    spot = f["spot_cfg"]
    method = f["method_cfg"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, who were pretending to be {theme.role_plural}. It also includes a {helper.label_word} who helps them solve the mystery safely.",
        ),
        (
            "What made the children think something magical was hiding by the curb?",
            f"They saw blinking light under {spot.the} and heard a tiny sound coming through the snow. Because the signal was muffled and hidden, it felt mysterious enough to seem magical.",
        ),
        (
            f"Why did {b.label} tell {a.label} not to hop off the curb?",
            f"{b.label} knew the snow by {spot.the} was slick and close to the street. {b.pronoun().capitalize()} was trying to stop a dangerous rush before someone slipped.",
        ),
    ]
    if f["waited"]:
        qa.append((
            f"What did {a.label} do after the warning?",
            f"{a.label} listened and stayed on the sidewalk instead of leaping into the slush. That gave the children time to ask for help and solve the problem carefully.",
        ))
    if f["slip"]:
        qa.append((
            f"What happened when {a.label} tried to reach the mystery?",
            f"{a.label}'s boot slipped on the slushy edge by the curb, and {a.pronoun()} had to catch a signpost. The scare showed why rushing toward a mystery is not the same as solving it.",
        ))
    qa.append((
        f"How did the {helper.label_word} solve the mystery?",
        f"The {helper.label_word} {method.qa_text}. That worked because the tool reached the hidden object without anyone stepping into the risky snow by the street.",
    ))
    qa.append((
        "What was the magical thing really?",
        f"It was {source.phrase}, and {source.video} was still playing. The misunderstanding came from mistaking a lost device's light and sound for magic.",
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the lost device going back to its owner and the children making a new rescue rule for their games. The ending proves they changed, because they chose careful problem solving over a wild rush.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"video", "snow", "curb", "lost_and_found", "helper"} | set(f["source_cfg"].tags) | set(f["spot_cfg"].tags) | set(f["method_cfg"].tags) | set(f["helper_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("buried", e.buried), ("plays_video", e.plays_video), ("icy", e.icy)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:12} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    theme: str = "ice_pirates"
    source: str = "phone"
    spot: str = "snowbank"
    method: str = "grabber"
    helper: str = "crossing_guard"
    instigator: str = "Tom"
    instigator_gender: str = "boy"
    cautioner: str = "Lily"
    cautioner_gender: str = "girl"
    trait: str = "careful"
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 7
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        theme="ice_pirates",
        source="phone",
        spot="snowbank",
        method="grabber",
        helper="crossing_guard",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        theme="snow_explorers",
        source="tablet",
        spot="plow_ridge",
        method="shovel",
        helper="shopkeeper",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        theme="winter_knights",
        source="camera",
        spot="snowbank",
        method="shovel",
        helper="neighbor",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Rose",
        cautioner_gender="girl",
        trait="steady",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
    ),
]


def explain_rejection(source: Source, spot: Spot) -> str:
    if not mystery_possible(source, spot):
        return (
            f"(No story: {source.label} in {spot.the} would not make a convincing magical misunderstanding here.)"
        )
    if not any_sensible_reaches(spot):
        return (
            f"(No story: {spot.the} is too deep to solve safely from the sidewalk with any sensible method. "
            f"Pick a shallower hiding place like the snowbank or plow ridge.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def explain_method(method_id: str, spot_id: str) -> str:
    method = METHODS[method_id]
    spot = SPOTS[spot_id]
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method_id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {method_id} cannot safely reach into {spot.the} from the sidewalk. "
        f"Use a longer tool or choose a shallower spot.)"
    )


ASP_RULES = r"""
mystery_possible(Src, Sp) :- source(Src), spot(Sp), plays_video(Src), depth(Sp, D), D >= 1.
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
reachable(Sp, M) :- spot(Sp), method(M), depth(Sp, D), reach(M, R), R >= D.
some_sensible_solution(Sp) :- sensible(M), reachable(Sp, M).
valid(T, Src, Sp) :- theme(T), source(Src), spot(Sp), mystery_possible(Src, Sp), some_sensible_solution(Sp).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
waited :- cautioner_older, authority(A), bravery_init(BR), A > BR.

retrieved :- chosen_spot(Sp), chosen_method(M), reachable(Sp, M).
stumble :- not waited, chosen_spot(Sp), icy(Sp), slip_risk(Sp, R), R > 0.

outcome(wait_safe) :- waited, retrieved.
outcome(stumble_safe) :- not waited, stumble, retrieved.
outcome(quick_safe) :- not waited, not stumble, retrieved.
outcome(stuck) :- not retrieved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("plays_video", sid))
    for spid, spot in SPOTS.items():
        lines.append(asp.fact("spot", spid))
        lines.append(asp.fact("depth", spid, spot.depth))
        lines.append(asp.fact("slip_risk", spid, spot.slip_risk))
        if spot.icy:
            lines.append(asp.fact("icy", spid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("reach", mid, method.reach))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_method", params.method),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_methods = {m.id for m in sensible_methods()}
    asp_methods = set(asp_sensible_methods())
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_methods)} python={sorted(py_methods)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a magical misunderstanding by a snowy curb, solved with care."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.spot:
        if not mystery_possible(SOURCES[args.source], SPOTS[args.spot]):
            raise StoryError(explain_rejection(SOURCES[args.source], SPOTS[args.spot]))
    if args.spot and not any_sensible_reaches(SPOTS[args.spot]):
        source = SOURCES[args.source] if args.source else next(iter(SOURCES.values()))
        raise StoryError(explain_rejection(source, SPOTS[args.spot]))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            spot_id = args.spot or "snowbank"
            raise StoryError(explain_method(args.method, spot_id))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.source is None or combo[1] == args.source)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, source_id, spot_id = rng.choice(sorted(combos))
    spot = SPOTS[spot_id]

    if args.method:
        if not method_reaches(METHODS[args.method], spot):
            raise StoryError(explain_method(args.method, spot_id))
        method_id = args.method
    else:
        options = [m.id for m in sensible_methods() if method_reaches(m, spot)]
        if not options:
            raise StoryError(explain_rejection(SOURCES[source_id], spot))
        method_id = rng.choice(sorted(options))

    helper_id = args.helper or rng.choice(sorted(HELPERS))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme_id,
        source=source_id,
        spot=spot_id,
        method=method_id,
        helper=helper_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("theme", THEMES),
        ("source", SOURCES),
        ("spot", SPOTS),
        ("method", METHODS),
        ("helper", HELPERS),
    ):
        key = getattr(params, field_name)
        if key not in registry:
            raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    source = SOURCES[params.source]
    spot = SPOTS[params.spot]
    method = METHODS[params.method]
    if not mystery_possible(source, spot) or not any_sensible_reaches(spot):
        raise StoryError(explain_rejection(source, spot))
    if method.sense < SENSE_MIN or not method_reaches(method, spot):
        raise StoryError(explain_method(params.method, params.spot))

    world = tell(
        theme=THEMES[params.theme],
        source=source,
        spot=spot,
        method=method,
        helper_cfg=HELPERS[params.helper],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, source, spot) combos:\n")
        for theme_id, source_id, spot_id in combos:
            print(f"  {theme_id:16} {source_id:8} {spot_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.source} in {p.spot} ({p.theme}, {p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
