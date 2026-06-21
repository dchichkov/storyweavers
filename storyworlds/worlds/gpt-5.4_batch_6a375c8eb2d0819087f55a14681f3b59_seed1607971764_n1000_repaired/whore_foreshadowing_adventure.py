#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py
===========================================================

A standalone story world for a gentle adventure tale with **foreshadowing**:
two children follow clues toward a hilltop bell tower, early signs warn that the
shortcut rope bridge is unsafe, and a calm grown-up helps them choose the long,
safe path instead.

The seed required the exact word "whore". To keep the domain child-facing and
reasonable, this world treats it as a hurtful old graffiti word that appears on
a damaged sign by the bridge. A grown-up immediately names it as unkind and not
a word the children should use. The adventure is therefore not *about* that
word, but the world can still faithfully include it in the rendered story.

Run it
------
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py --trail bell --hazard bridge
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py --hazard river
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/whore_foreshadowing_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
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
    sturdy: bool = False
    movable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"aunt": "aunt", "uncle": "uncle", "mother": "mom", "father": "dad"}.get(
            self.type, self.type
        )
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
class Trail:
    id: str
    quest: str
    lure: str
    found_at_end: str
    end_image: str
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
class Hazard:
    id: str
    label: str
    place: str
    danger_noun: str
    warning_sign: str
    clue_lines: list[str] = field(default_factory=list)
    severity: int = 2
    passable: bool = True
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
    tool_phrase: str
    action_text: str
    qa_text: str
    sense: int = 2
    power: int = 2
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
class Reward:
    id: str
    label: str
    phrase: str
    shine: str
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
    trail: str
    hazard: str
    helper: str
    reward: str
    scout: str
    scout_gender: str
    partner: str
    partner_gender: str
    adult: str
    adult_role: str
    caution_trait: str
    delay: int = 0
    trust: int = 6
    relation: str = "siblings"
    pet: str = ""
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"scout", "partner"}]

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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("hazard")
    if sign.meters["warning_seen"] < THRESHOLD:
        return out
    sig = ("spook", sign.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("scout").memes["worry"] += 1
    world.get("partner").memes["worry"] += 1
    world.get("adult").memes["alert"] += 1
    out.append("__warning__")
    return out


def _r_shake(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.get("hazard")
    if hazard.meters["crossed"] < THRESHOLD:
        return out
    sig = ("shake", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hazard.meters["unstable"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("adult").memes["protect"] += 1
    out.append("__unstable__")
    return out


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="shake", tag="physical", apply=_r_shake),
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


TRAILS = {
    "bell": Trail(
        id="bell",
        quest="the old bell tower on the hill",
        lure="faint ding-ding sounds drifting down from the foggy hill",
        found_at_end="the bronze bell that had been ringing in the wind",
        end_image="The bell sang over the valley while the children waved from the safe stone steps.",
        tags={"bell", "tower", "adventure"},
    ),
    "flag": Trail(
        id="flag",
        quest="the lookout rock with the bright cloth flag",
        lure="a flutter of red cloth high above the pines",
        found_at_end="the bright flag snapping in the high wind",
        end_image="The flag snapped happily overhead while the children stood on the firm lookout ledge.",
        tags={"flag", "lookout", "adventure"},
    ),
    "lantern": Trail(
        id="lantern",
        quest="the old watch hut with the glass lantern",
        lure="a pale gold wink far along the ridge",
        found_at_end="the glass lantern shining in the hut window",
        end_image="The lantern glowed in the hut window, and the ridge felt wide and kind again.",
        tags={"lantern", "hut", "adventure"},
    ),
}

HAZARDS = {
    "bridge": Hazard(
        id="bridge",
        label="rope bridge",
        place="the narrow ravine",
        danger_noun="the bridge's loose ropes and missing planks",
        warning_sign='A crooked board leaned beside it. Someone had scratched the ugly word "whore" across the old paint, and Aunt Mara said at once that it was a mean word, not a word for them to use. Under it, the real warning arrow pointed to a safer trail.',
        clue_lines=[
            "At the first bend, they found a plank with a cracked end, half buried in fern leaves.",
            "A little farther on, one rope strand hung fuzzy and frayed like an old braid.",
            "Even the magpies had gone quiet above the ravine.",
        ],
        severity=3,
        passable=True,
        tags={"bridge", "ravine", "warning"},
    ),
    "stairs": Hazard(
        id="stairs",
        label="crumbly stairway",
        place="the broken cliff steps",
        danger_noun="the stairway's loose stones and crumbling edges",
        warning_sign='Near the first step, a torn notice flapped on a post. Someone had scrawled the ugly word "whore" over it, and Uncle Ren quietly said it was a hurtful word, not one children should copy. The arrow below still showed the roundabout path.',
        clue_lines=[
            "Pebbles kept ticking down the slope before anyone touched the steps.",
            "A handrail post leaned sideways like a tired tooth.",
            "The wind whistled through cracks in the stone.",
        ],
        severity=2,
        passable=True,
        tags={"stairs", "cliff", "warning"},
    ),
    "river": Hazard(
        id="river",
        label="swift stepping-stone crossing",
        place="the cold river bend",
        danger_noun="the slippery stones and fast water",
        warning_sign='A washed-out sign lay in the reeds. Across one corner was the ugly word "whore," and their grown-up said kindly that it was a bad old scribble and not a word to carry in your mouth. Beside it, a blue stripe marked the ford path upstream.',
        clue_lines=[
            "Before they saw the water, they heard it rushing harder than morning rain.",
            "The stones nearest the bank shone slick and green.",
            "A leaf spun away so quickly that both children watched it go.",
        ],
        severity=3,
        passable=False,
        tags={"river", "ford", "warning"},
    ),
}

HELPERS = {
    "guide_rope": Helper(
        id="guide_rope",
        label="guide rope",
        tool_phrase="a coil of guide rope from the grown-up's satchel",
        action_text="uncoiled a guide rope, tied it where the safe path narrowed, and led the children along the longer trail one careful step at a time",
        qa_text="used a guide rope and led them along the longer safe path",
        sense=3,
        power=3,
        tags={"rope", "safe_path"},
    ),
    "lantern_staff": Helper(
        id="lantern_staff",
        label="lantern and walking staff",
        tool_phrase="a lantern and a smooth walking staff",
        action_text="lifted the lantern, tapped each patch of ground with the walking staff, and guided everyone around the danger on the marked path",
        qa_text="used a lantern and walking staff to guide them on the marked path",
        sense=3,
        power=3,
        tags={"lantern_tool", "safe_path"},
    ),
    "chalk_marks": Helper(
        id="chalk_marks",
        label="chalk marks",
        tool_phrase="a piece of yellow chalk and a pocket map",
        action_text="marked the safe turn with yellow chalk, checked the pocket map twice, and marched the children along the long way around",
        qa_text="marked the safe turn with chalk and took the long way around",
        sense=2,
        power=2,
        tags={"chalk", "safe_path"},
    ),
    "jump_it": Helper(
        id="jump_it",
        label="big jump",
        tool_phrase="only a brave shout and quick feet",
        action_text="told everyone to jump it fast and hope for the best",
        qa_text="told them to jump fast and hope for the best",
        sense=1,
        power=1,
        tags={"risky"},
    ),
}

REWARDS = {
    "berry_cake": Reward(
        id="berry_cake",
        label="berry cake",
        phrase="a round berry cake wrapped in cloth",
        shine="purple jam shone at the cut edge",
        tags={"cake", "treat"},
    ),
    "silver_key": Reward(
        id="silver_key",
        label="silver key",
        phrase="a small silver key tied with blue string",
        shine="it flashed like fish scales in the sun",
        tags={"key", "treasure"},
    ),
    "star_map": Reward(
        id="star_map",
        label="star map",
        phrase="a folded star map drawn in blue ink",
        shine="tiny silver dots winked across the paper",
        tags={"map", "treasure"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nora", "Tess", "Mina", "Ava", "Ivy", "Rosa"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Tobin", "Eli", "Max", "Owen", "Jude"]
TRAITS = ["careful", "steady", "thoughtful", "brave", "curious", "patient"]
PETS = ["the little dog", "the goat kid", "the shaggy pony", ""]


def hazard_at_risk(hazard: Hazard) -> bool:
    return hazard.passable and hazard.severity >= 2


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def danger_level(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_resolved(helper: Helper, hazard: Hazard, delay: int) -> bool:
    return helper.power >= danger_level(hazard, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for trail_id in TRAILS:
        for hazard_id, hazard in HAZARDS.items():
            if hazard_at_risk(hazard):
                combos.append((trail_id, hazard_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("hazard").meters["crossed"] += 1
    propagate(sim, narrate=False)
    return {
        "unstable": sim.get("hazard").meters["unstable"] >= THRESHOLD,
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


def open_adventure(world: World, scout: Entity, partner: Entity, adult: Entity, trail: Trail) -> None:
    for kid in (scout, partner):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"Early one bright morning, {scout.id} and {partner.id} set out with their "
        f"{adult.label_word}, {adult.id}, to look for {trail.quest}. "
        f"They had heard {trail.lure}, and it made the whole hillside feel like a secret."
    )
    world.say(
        f'{scout.id} swung a stick like a captain\'s pointer. "{trail.quest.capitalize()} first!" '
        f"{scout.pronoun().capitalize()} called."
    )


def clue_beat(world: World, hazard: Hazard) -> None:
    for line in hazard.clue_lines:
        world.say(line)


def warning_sign(world: World, adult: Entity, hazard: Hazard) -> None:
    world.get("hazard").meters["warning_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they reached {hazard.place}, they found {hazard.warning_sign}"
    )
    world.say(
        f'{adult.id} touched the clean part of the sign. "The sign is what matters," '
        f'{adult.pronoun()} said. "It says this way is not safe today."'
    )


def temptation(world: World, scout: Entity, partner: Entity, hazard: Hazard) -> None:
    scout.memes["defiance"] += 1
    world.say(
        f"Still, {hazard.label} looked like the fastest way to the top. "
        f'"If we hurry, we can get across before anything bad happens," {scout.id} said.'
    )
    world.say(
        f"{partner.id} stared at {hazard.danger_noun} and hugged {partner.pronoun('possessive')} elbows."
    )


def grounded_warning(world: World, adult: Entity, scout: Entity, partner: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_unstable"] = pred["unstable"]
    world.facts["predicted_fear"] = pred["fear"]
    partner.memes["caution"] += 1
    extra = ""
    if pred["unstable"]:
        extra = " If someone stepped there now, it would shake and frighten everyone."
    world.say(
        f'"Listen to the clues," {adult.id} said. "The broken pieces, the quiet birds, and the warning arrow all point the same way.{extra}"'
    )


def risky_step(world: World, scout: Entity, hazard: Hazard) -> None:
    world.get("hazard").meters["crossed"] += 1
    propagate(world, narrate=False)
    scout.memes["fear"] += 1
    world.say(
        f"But {scout.id} put one foot onto the {hazard.label} to test it."
    )
    if hazard.id == "bridge":
        world.say("At once the planks gave a thin creak, and the ropes shivered.")
    elif hazard.id == "stairs":
        world.say("At once three pebbles skittered away, and one step shed a dusty edge.")
    else:
        world.say("At once cold water slapped over the nearest stone, and the current tugged hard.")


def pull_back(world: World, adult: Entity, scout: Entity) -> None:
    adult.memes["protect"] += 1
    scout.memes["trust"] += 1
    world.say(
        f"{adult.id} caught {scout.id}'s sleeve and drew {scout.pronoun('object')} back to solid ground."
    )
    world.say(
        f'"Adventure is not racing toward danger," {adult.id} said. "Adventure is seeing it in time."'
    )


def safe_solution(world: World, adult: Entity, helper: Helper, hazard: Hazard) -> None:
    world.get("hazard").meters["avoided"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["respect"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Then {adult.id} took out {helper.tool_phrase} and {helper.action_text}."
    )
    if hazard.id == "river":
        world.say("The ford upstream was slower, but the water there only lapped at their boots.")
    else:
        world.say("The longer trail took more time, but every stone underfoot felt firm and honest.")


def reach_goal(world: World, scout: Entity, partner: Entity, adult: Entity, trail: Trail, reward: Reward) -> None:
    for kid in (scout, partner):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"At last they reached {trail.quest}. There they found {trail.found_at_end}, "
        f"and beside it lay {reward.phrase}; {reward.shine}."
    )
    world.say(
        f'{partner.id} laughed first. "We still made it!" {partner.pronoun().capitalize()} said.'
    )
    pet = world.facts.get("pet", "")
    if pet:
        world.say(f"Even {pet} came puffing up the last steps behind them.")
    world.say(trail.end_image)


def tell(
    trail: Trail,
    hazard: Hazard,
    helper: Helper,
    reward: Reward,
    scout_name: str = "Finn",
    scout_gender: str = "boy",
    partner_name: str = "Lina",
    partner_gender: str = "girl",
    adult_name: str = "Mara",
    adult_role: str = "aunt",
    caution_trait: str = "careful",
    delay: int = 0,
    trust: int = 6,
    relation: str = "siblings",
    pet: str = "",
) -> World:
    world = World()
    scout = world.add(
        Entity(
            id=scout_name,
            kind="character",
            type=scout_gender,
            role="scout",
            traits=["eager"],
            attrs={"relation": relation},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=[caution_trait],
            attrs={"relation": relation},
        )
    )
    adult = world.add(
        Entity(
            id=adult_name,
            kind="character",
            type=adult_role,
            role="adult",
            label="the grown-up",
        )
    )
    world.add(Entity(id="hazard", type="hazard", label=hazard.label))
    scout.memes["trust"] = float(trust)
    partner.memes["caution"] = 5.0 if caution_trait in {"careful", "steady", "thoughtful", "patient"} else 3.0
    world.facts["pet"] = pet

    open_adventure(world, scout, partner, adult, trail)
    world.para()
    clue_beat(world, hazard)
    warning_sign(world, adult, hazard)
    temptation(world, scout, partner, hazard)
    grounded_warning(world, adult, scout, partner, hazard)
    world.para()
    risky_step(world, scout, hazard)
    pull_back(world, adult, scout)
    world.para()
    safe_solution(world, adult, helper, hazard)
    reach_goal(world, scout, partner, adult, trail, reward)

    world.facts.update(
        scout=scout,
        partner=partner,
        adult=adult,
        trail=trail,
        hazard_cfg=hazard,
        hazard=world.get("hazard"),
        helper=helper,
        reward=reward,
        relation=relation,
        danger=danger_level(hazard, delay),
        resolved=True,
        outcome="safe",
    )
    return world


KNOWLEDGE = {
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives you little hints early on about something important that may happen later. Those clues help the middle turn feel earned instead of sudden."
        )
    ],
    "bridge": [
        (
            "Why can an old rope bridge be dangerous?",
            "An old rope bridge can be dangerous because ropes fray and planks can crack or slip. If it shakes too much, someone can fall."
        )
    ],
    "stairs": [
        (
            "Why are crumbly stairs unsafe?",
            "Crumbly stairs are unsafe because loose stone can break under your feet. That can make you slip or tumble."
        )
    ],
    "river": [
        (
            "Why are slippery river stones dangerous?",
            "Slippery stones are dangerous because your feet can slide off them, and fast water can push you down. Even shallow-looking water can move strongly."
        )
    ],
    "warning": [
        (
            "Why should children listen to a warning sign?",
            "A warning sign is there to tell you about danger before you step into it. Listening early can keep a fun trip from turning into an emergency."
        )
    ],
    "safe_path": [
        (
            "Why is taking the long safe path sometimes brave?",
            "Taking the long safe path is brave because it means you are thinking instead of just rushing. Real courage often means slowing down and choosing wisely."
        )
    ],
    "hurtful_word": [
        (
            "What should you do if you see a hurtful word written somewhere?",
            "You do not need to repeat it. You can tell a trusted grown-up, and choose kind words instead."
        )
    ],
    "tower": [
        (
            "What is a bell tower?",
            "A bell tower is a tall place where a bell hangs high up. You can often hear it from far away."
        )
    ],
    "flag": [
        (
            "Why is a high flag easy to spot on an adventure?",
            "A flag catches wind and moves where people can see it from far away. Its bright color makes it a good landmark."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern gives light so you can see where to walk. Good light helps people notice safe and unsafe places."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map shows where paths and places are. It helps travelers choose where to go."
        )
    ],
    "key": [
        (
            "What is a key used for?",
            "A key opens or locks something that is meant to stay shut. In stories, a key can also feel like a clue."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "foreshadowing",
    "bridge",
    "stairs",
    "river",
    "warning",
    "safe_path",
    "hurtful_word",
    "tower",
    "flag",
    "lantern",
    "map",
    "key",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scout = f["scout"]
    partner = f["partner"]
    adult = f["adult"]
    trail = f["trail"]
    hazard = f["hazard_cfg"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that uses foreshadowing and includes the word "whore" only as a hurtful scribble on an old warning sign that a grown-up rejects.',
        f"Tell a gentle adventure where {scout.id} and {partner.id} head toward {trail.quest}, but early clues warn them not to trust {hazard.label}, and {adult.id} helps them choose the safe path.",
        f"Write a story where danger is hinted before the turning point, so the warning feels earned when the children almost test {hazard.label} and then wisely go around.",
    ]


def pair_noun(scout: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if scout.type == "boy" and partner.type == "boy":
            return "two brothers"
        if scout.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scout = f["scout"]
    partner = f["partner"]
    adult = f["adult"]
    trail = f["trail"]
    hazard = f["hazard_cfg"]
    helper = f["helper"]
    reward = f["reward"]
    pair = pair_noun(scout, partner, f.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {scout.id} and {partner.id}, and their {adult.label_word}, {adult.id}. Together they went on a hillside adventure."
        ),
        (
            "What were they looking for?",
            f"They were looking for {trail.quest}. The distant clue that called them forward was {trail.lure}."
        ),
        (
            "How did the story use foreshadowing?",
            f"The story gave warning clues before the dangerous moment, like broken pieces, quiet animals, and the sign by {hazard.place}. Those hints prepared everyone for the moment when {scout.id} nearly tested the risky shortcut."
        ),
        (
            "What did the grown-up say about the word on the sign?",
            f"The grown-up said the word 'whore' was an ugly, hurtful scribble and not a word for the children to use. That moment kept the story kind while still showing what had been written there."
        ),
        (
            f"Why was {hazard.label} unsafe?",
            f"It was unsafe because of {hazard.danger_noun}. The earlier clues all pointed to the same danger before anyone tried to cross."
        ),
        (
            f"What happened when {scout.id} tested it?",
            f"{scout.id} put one foot onto the {hazard.label}, and it reacted right away, showing the danger was real. That quick scare proved the earlier warning had been true."
        ),
        (
            f"How did {adult.id} solve the problem?",
            f"{adult.id} {helper.qa_text}. That let the adventure continue without making the children push through the danger."
        ),
        (
            "How did the story end?",
            f"They still reached {trail.quest} and found {reward.phrase}. The ending image showed that a slower safe choice still led to a real adventure."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"foreshadowing", "warning", "safe_path", "hurtful_word"}
    hazard = f["hazard_cfg"]
    trail = f["trail"]
    reward = f["reward"]
    helper = f["helper"]
    tags |= set(hazard.tags)
    tags |= set(trail.tags)
    tags |= set(reward.tags)
    tags |= set(helper.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        trail="bell",
        hazard="bridge",
        helper="guide_rope",
        reward="silver_key",
        scout="Finn",
        scout_gender="boy",
        partner="Lina",
        partner_gender="girl",
        adult="Mara",
        adult_role="aunt",
        caution_trait="careful",
        delay=0,
        trust=6,
        relation="siblings",
        pet="the little dog",
    ),
    StoryParams(
        trail="flag",
        hazard="stairs",
        helper="lantern_staff",
        reward="star_map",
        scout="Ava",
        scout_gender="girl",
        partner="Leo",
        partner_gender="boy",
        adult="Ren",
        adult_role="uncle",
        caution_trait="steady",
        delay=0,
        trust=5,
        relation="friends",
        pet="",
    ),
    StoryParams(
        trail="lantern",
        hazard="river",
        helper="guide_rope",
        reward="berry_cake",
        scout="Sam",
        scout_gender="boy",
        partner="Nora",
        partner_gender="girl",
        adult="Mara",
        adult_role="aunt",
        caution_trait="thoughtful",
        delay=0,
        trust=7,
        relation="siblings",
        pet="the goat kid",
    ),
]


def explain_rejection(hazard: Hazard) -> str:
    if not hazard.passable:
        return (
            f"(No story: {hazard.label} at {hazard.place} is not a reasonable shortcut to test. "
            f"This world needs a hazard the children can be tempted by before they choose the safe route.)"
        )
    if hazard.severity < 2:
        return (
            f"(No story: {hazard.label} is too mild to support foreshadowed danger and a meaningful safe choice.)"
        )
    return "(No story: this hazard does not fit the adventure gate.)"


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
hazard_ok(H)   :- hazard(H), passable(H), severity(H, S), S >= 2.
sensible(He)   :- helper(He), sense(He, S), sense_min(M), S >= M.
valid(T, H)    :- trail(T), hazard_ok(H).

danger(D)      :- chosen_hazard(H), severity(H, S), delay(L), D = S + L.
resolved       :- chosen_helper(He), power(He, P), danger(D), P >= D.
outcome(safe)  :- resolved.

#show valid/2.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TRAILS:
        lines.append(asp.fact("trail", tid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hazard.passable:
            lines.append(asp.fact("passable", hid))
        lines.append(asp.fact("severity", hid, hazard.severity))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("power", hid, helper.power))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "safe" if is_resolved(HELPERS[params.helper], HAZARDS[params.hazard], params.delay) else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense, p_sense = set(asp_sensible()), {h.id for h in sensible_helpers()}
    if c_sense == p_sense:
        print(f"OK: sensible helpers match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a foreshadowed adventure with a risky shortcut and a safe path."
    )
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--adult-role", choices=["aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0], default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard:
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(hazard):
            raise StoryError(explain_rejection(hazard))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))

    combos = [
        c
        for c in valid_combos()
        if (args.trail is None or c[0] == args.trail)
        and (args.hazard is None or c[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trail_id, hazard_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(h.id for h in sensible_helpers()))
    reward_id = args.reward or rng.choice(sorted(REWARDS))
    scout, scout_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=scout)
    adult_name = rng.choice(["Mara", "Ren", "Toma", "Iris"])
    adult_role = args.adult_role or rng.choice(["aunt", "uncle"])
    caution_trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    trust = rng.randint(3, 8)
    pet = rng.choice(PETS)
    delay = 0 if args.delay is None else args.delay
    return StoryParams(
        trail=trail_id,
        hazard=hazard_id,
        helper=helper_id,
        reward=reward_id,
        scout=scout,
        scout_gender=scout_gender,
        partner=partner,
        partner_gender=partner_gender,
        adult=adult_name,
        adult_role=adult_role,
        caution_trait=caution_trait,
        delay=delay,
        trust=trust,
        relation=relation,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        trail = TRAILS[params.trail]
        hazard = HAZARDS[params.hazard]
        helper = HELPERS[params.helper]
        reward = REWARDS[params.reward]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter choice: {err.args[0]})") from None

    if not hazard_at_risk(hazard):
        raise StoryError(explain_rejection(hazard))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(helper.id))
    if not is_resolved(helper, hazard, params.delay):
        raise StoryError("(No story: the chosen helper is too weak for this danger.)")

    world = tell(
        trail=trail,
        hazard=hazard,
        helper=helper,
        reward=reward,
        scout_name=params.scout,
        scout_gender=params.scout_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        adult_name=params.adult,
        adult_role=params.adult_role,
        caution_trait=params.caution_trait,
        delay=params.delay,
        trust=params.trust,
        relation=params.relation,
        pet=params.pet,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trail, hazard) combos:\n")
        for trail_id, hazard_id in combos:
            print(f"  {trail_id:8} {hazard_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.scout} & {p.partner}: {p.trail} via {p.hazard} ({p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
