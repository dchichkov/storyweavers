#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py
===================================================================================

A standalone story world for a tiny myth-flavored tale set at a post office:
a curious child notices a gargoyle high on the old building, wonders why its
stone mouth points at the street, and learns that the gargoyle is guarding a
jammed rain spout. With a kindly postal worker and a grown-up helper, the child
solves the small problem in a sensible way, water flows again, and the ending
proves what changed.

The model is built around one concrete tension:
- curiosity about the gargoyle
- a blocked spout that threatens the letters below
- a grounded, child-safe fix using a ladder and a long brush handled by adults
- a happy ending with the mail kept dry and the gargoyle seeming to smile again

Run it
------
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py --all --qa
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py --trace
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py --json
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py --asp
    python storyworlds/worlds/gpt-5.4/gargoyle_post_office_happy_ending_dialogue_curiosity.py --verify
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
    stone: bool = False
    climbable: bool = False
    # unified state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "clerk_woman"}
        male = {"boy", "father", "man", "clerk_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "clerk_woman": "clerk",
            "clerk_man": "clerk",
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
class Setting:
    id: str
    place: str
    old_name: str
    roofline: str
    counter: str
    floor_sound: str
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
class Curiosity:
    id: str
    notice: str
    question: str
    why_clause: str
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
class Blockage:
    id: str
    material: str
    phrase: str
    risk_text: str
    clears_with: set[str] = field(default_factory=set)
    severity: int = 1
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
class Response:
    id: str
    sense: int
    safe_for_child: bool
    tool: str
    reaches_roof: bool
    clears: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_overflow_threat(world: World) -> list[str]:
    gargoyle = world.get("gargoyle")
    letters = world.get("letters")
    out: list[str] = []
    if gargoyle.meters["blocked"] < THRESHOLD:
        return out
    sig = ("overflow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    letters.meters["at_risk"] += 1
    for eid in ("child", "adult", "clerk"):
        if eid in world.entities:
            world.get(eid).memes["concern"] += 1
    out.append("__risk__")
    return out


def _r_clear_relief(world: World) -> list[str]:
    gargoyle = world.get("gargoyle")
    letters = world.get("letters")
    out: list[str] = []
    if gargoyle.meters["flowing"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    letters.meters["at_risk"] = 0.0
    letters.meters["safe"] += 1
    for eid in ("child", "adult", "clerk"):
        if eid in world.entities:
            ent = world.get(eid)
            ent.memes["relief"] += 1
            ent.memes["wonder"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="overflow_threat", tag="physical", apply=_r_overflow_threat),
    Rule(name="clear_relief", tag="physical", apply=_r_clear_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_exists(blockage: Blockage) -> bool:
    return blockage.severity > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_works(blockage: Blockage, response: Response) -> bool:
    return (
        response.sense >= SENSE_MIN
        and response.reaches_roof
        and blockage.material in response.clears
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for curiosity_id in CURIOSITIES:
            for blockage_id, blockage in BLOCKAGES.items():
                if hazard_exists(blockage):
                    combos.append((setting_id, curiosity_id, blockage_id))
    return combos


def predict_risk(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "mail_at_risk": sim.get("letters").meters["at_risk"] >= THRESHOLD,
        "blocked": sim.get("gargoyle").meters["blocked"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"In the old post office, where {setting.floor_sound} and {setting.counter}, "
        f"{child.id} came with {child.pronoun('possessive')} {adult.label_word} to mail a letter."
    )
    world.say(
        f"Above the door, along {setting.roofline}, sat a stone gargoyle from the days when the place was called {setting.old_name}."
    )
    child.memes["wonder"] += 1
    child.memes["curiosity"] += 1


def notice(world: World, child: Entity, curiosity: Curiosity) -> None:
    world.say(
        f"{child.id} stopped and stared. {curiosity.notice}"
    )
    world.say(
        f'"{curiosity.question}" {child.pronoun()} asked.'
    )


def clerk_answers(world: World, clerk: Entity, child: Entity, gargoyle: Entity, curiosity: Curiosity) -> None:
    pred = predict_risk(world)
    world.facts["predicted_mail_risk"] = pred["mail_at_risk"]
    world.say(
        f'The {clerk.label_word} looked up and smiled. "People long ago said the gargoyle watched the rain and kept the letters below it safe," {clerk.pronoun()} said.'
    )
    if pred["mail_at_risk"]:
        world.say(
            f'"Today {curiosity.why_clause}, so it may be trying to warn us," {clerk.pronoun()} added.'
        )
    gargoyle.memes["guardian"] += 1
    child.memes["curiosity"] += 1


def reveal_problem(world: World, clerk: Entity, blockage: Blockage) -> None:
    world.say(
        f'The {clerk.label_word} pointed to the gargoyle\'s mouth. "{blockage.phrase.capitalize()} is stuck in the spout, and {blockage.risk_text}," {clerk.pronoun()} said.'
    )
    world.get("gargoyle").meters["blocked"] += 1
    propagate(world, narrate=False)


def unsafe_idea(world: World, child: Entity) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f'"Can I climb up and help?" {child.id} asked.'
    )


def refuse_unsafe(world: World, adult: Entity, child: Entity) -> None:
    child.memes["disappointment"] += 1
    adult.memes["care"] += 1
    world.say(
        f'"No," said {adult.label_word.capitalize()}. "Roof work is for grown-ups with steady shoes and safe hands. You may help by watching closely and telling us what you see."'
    )


def prepare_fix(world: World, adult: Entity, clerk: Entity, response: Response) -> None:
    world.say(
        f'The {clerk.label_word} fetched {response.tool}, and {adult.label_word} set it carefully against the wall.'
    )
    world.say(
        f'"I will go up," said {adult.label_word}. "You stand by the door with the mail tray."'
    )


def do_fix(world: World, adult: Entity, clerk: Entity, response: Response, blockage: Blockage) -> None:
    gargoyle = world.get("gargoyle")
    if response_works(blockage, response):
        gargoyle.meters["blocked"] = 0.0
        gargoyle.meters["flowing"] += 1
        world.facts["fixed"] = True
        propagate(world, narrate=False)
        world.say(response.text.format(material=blockage.material))
        world.say(
            "At once a ribbon of water poured through the stone mouth and splashed safely into the drain below."
        )
    else:
        world.facts["fixed"] = False
        world.say(response.fail.format(material=blockage.material))


def child_spots_change(world: World, child: Entity, gargoyle: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["understanding"] += 1
    world.say(
        f'"Look!" cried {child.id}. "The gargoyle is not frowning now. It is drinking the rain and sending it where it belongs."'
    )
    gargoyle.memes["guardian"] += 1


def ending(world: World, child: Entity, adult: Entity, clerk: Entity) -> None:
    letters = world.get("letters")
    child.memes["joy"] += 1
    adult.memes["relief"] += 1
    clerk.memes["relief"] += 1
    if letters.meters["safe"] >= THRESHOLD:
        world.say(
            f'The {clerk.label_word} slid the dry letters back under the eaves and laughed softly. "Safe again," {clerk.pronoun()} said.'
        )
        world.say(
            f'{adult.label_word.capitalize()} pressed the stamped envelope into {child.id}\'s hand, and together they sent it on its way.'
        )
        world.say(
            f"As they left the post office, {child.id} looked back once more. High above the door, the gargoyle seemed less like a monster and more like an old stone helper keeping watch over everyone's words."
        )


def tell(
    setting: Setting,
    curiosity: Curiosity,
    blockage: Blockage,
    response: Response,
    *,
    child_name: str = "Lina",
    child_type: str = "girl",
    adult_type: str = "mother",
    clerk_type: str = "clerk_man",
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the parent", role="adult"))
    clerk = world.add(Entity(id="clerk", kind="character", type=clerk_type, label="the clerk", role="clerk"))
    gargoyle = world.add(Entity(id="gargoyle", kind="thing", type="gargoyle", label="gargoyle", role="guardian", stone=True))
    letters = world.add(Entity(id="letters", kind="thing", type="letters", label="letters"))
    ladder = world.add(Entity(id="ladder", kind="thing", type="ladder", label="ladder", climbable=True))
    brush = world.add(Entity(id="tool", kind="thing", type="tool", label=response.tool))

    child.attrs["name"] = child_name
    adult.attrs["relation"] = adult.label_word
    clerk.attrs["duty"] = "mail"
    gargoyle.attrs["spout"] = True
    letters.attrs["under_eaves"] = True
    world.facts["fixed"] = False
    world.facts["child_name"] = child_name
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["clerk"] = clerk
    world.facts["gargoyle"] = gargoyle
    world.facts["letters"] = letters
    world.facts["setting"] = setting
    world.facts["curiosity_cfg"] = curiosity
    world.facts["blockage_cfg"] = blockage
    world.facts["response_cfg"] = response

    introduce(world, child, adult, setting)
    notice(world, child, curiosity)

    world.para()
    clerk_answers(world, clerk, child, gargoyle, curiosity)
    reveal_problem(world, clerk, blockage)
    unsafe_idea(world, child)
    refuse_unsafe(world, adult, child)

    world.para()
    prepare_fix(world, adult, clerk, response)
    do_fix(world, adult, clerk, response, blockage)
    if not world.facts["fixed"]:
        raise StoryError("(No story: the chosen response cannot safely clear the blockage.)")
    child_spots_change(world, child, gargoyle)

    world.para()
    ending(world, child, adult, clerk)

    world.facts["mail_safe"] = letters.meters["safe"] >= THRESHOLD
    world.facts["mail_risk"] = letters.meters["at_risk"] >= THRESHOLD
    world.facts["curiosity_answered"] = child.memes["understanding"] >= THRESHOLD
    return world


SETTINGS = {
    "old_stone_post_office": Setting(
        id="old_stone_post_office",
        place="the post office",
        old_name="the House of Couriers",
        roofline="the rain-dark roofline",
        counter="the brass scales glimmered on the counter",
        floor_sound="boots made hollow sounds on the tiles",
        tags={"post_office", "mail"},
    ),
    "village_post_office": Setting(
        id="village_post_office",
        place="the village post office",
        old_name="the Hall of Messages",
        roofline="the old gutter and carved stone ledge",
        counter="the wooden counter smelled faintly of paper and string",
        floor_sound="the floorboards answered each step with a gentle creak",
        tags={"post_office", "mail"},
    ),
}

CURIOSITIES = {
    "mouth_question": Curiosity(
        id="mouth_question",
        notice="The stone face was fierce, but its eyes looked patient, as if it had listened to many storms.",
        question="Why does the gargoyle point its mouth at the street?",
        why_clause="the water cannot pass through its mouth",
        tags={"gargoyle", "rain"},
    ),
    "watcher_question": Curiosity(
        id="watcher_question",
        notice="Its little stone claws gripped the ledge as if it were guarding a treasure no one else could see.",
        question="Is the gargoyle guarding something?",
        why_clause="the rain is backing up behind it",
        tags={"gargoyle", "guard"},
    ),
    "sad_question": Curiosity(
        id="sad_question",
        notice="A dark line of rain marked its chin, and to a child it looked almost sad.",
        question="Why does the gargoyle look unhappy today?",
        why_clause="the spout is choked and the rain has nowhere easy to go",
        tags={"gargoyle", "rain"},
    ),
}

BLOCKAGES = {
    "leaves": Blockage(
        id="leaves",
        material="leaves",
        phrase="a nest of wet leaves",
        risk_text="the water may spill over and drip onto the sacks of letters by the wall",
        clears_with={"ladder_brush", "ladder_hand"},
        severity=1,
        tags={"leaves", "rain"},
    ),
    "twigs": Blockage(
        id="twigs",
        material="twigs",
        phrase="a little bundle of twigs",
        risk_text="the rain may splash down onto the mail waiting in the tray",
        clears_with={"ladder_brush", "ladder_hand"},
        severity=1,
        tags={"twigs", "rain"},
    ),
    "moss": Blockage(
        id="moss",
        material="moss",
        phrase="a thick plug of moss",
        risk_text="the gutter may overflow and soak the parcels beneath the eaves",
        clears_with={"ladder_brush"},
        severity=1,
        tags={"moss", "rain"},
    ),
}

RESPONSES = {
    "ladder_brush": Response(
        id="ladder_brush",
        sense=3,
        safe_for_child=False,
        tool="a tall ladder and a long-handled brush",
        reaches_roof=True,
        clears={"leaves", "twigs", "moss"},
        text='Carefully, the grown-up climbed a few rungs and brushed the {material} free while the clerk steadied the ladder below.',
        fail='The grown-up reached up with the brush, but the {material} clung too tightly to move.',
        qa_text="The grown-up used a ladder and a long brush while the clerk held the ladder steady.",
        tags={"ladder", "brush", "safety"},
    ),
    "ladder_hand": Response(
        id="ladder_hand",
        sense=2,
        safe_for_child=False,
        tool="a tall ladder",
        reaches_roof=True,
        clears={"leaves", "twigs"},
        text='Carefully, the grown-up climbed a few rungs and lifted the {material} out by hand while the clerk held the ladder steady.',
        fail='The grown-up could reach the spout, but the {material} was packed too firmly to pull free by hand.',
        qa_text="The grown-up climbed a ladder and pulled the blockage out by hand while the clerk held it steady.",
        tags={"ladder", "safety"},
    ),
    "child_climb": Response(
        id="child_climb",
        sense=1,
        safe_for_child=False,
        tool="nothing at all",
        reaches_roof=False,
        clears=set(),
        text='',
        fail='The child could not safely reach the roof.',
        qa_text="This was refused because children should not climb up to a roof.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tara", "Nora", "Iris", "Vera", "Etta", "Mina"]
BOY_NAMES = ["Oren", "Tobin", "Milo", "Sami", "Nico", "Eli", "Darin", "Pavel"]


@dataclass
class StoryParams:
    setting: str
    curiosity: str
    blockage: str
    response: str
    child_name: str
    child_type: str
    adult_type: str
    clerk_type: str
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
    "gargoyle": [
        (
            "What is a gargoyle?",
            "A gargoyle is a carved stone figure on a building. Some gargoyles are also water spouts that send rain away from the walls."
        )
    ],
    "post_office": [
        (
            "What happens in a post office?",
            "People bring letters and parcels to a post office so they can be stamped, sorted, and sent to other places."
        )
    ],
    "rain": [
        (
            "Why do buildings need spouts and gutters?",
            "Spouts and gutters carry rainwater away from roofs. That helps keep walls, doors, and things below from getting soaked."
        )
    ],
    "ladder": [
        (
            "Why should a ladder be held steady?",
            "A ladder can wobble if no one steadies it. Holding it firmly helps keep the person climbing safer."
        )
    ],
    "safety": [
        (
            "Why should children not climb onto a roof to fix things?",
            "Roofs are high and slippery, and a child could fall. A grown-up with safe tools should handle that kind of job."
        )
    ],
    "mail": [
        (
            "Why should letters be kept dry?",
            "Wet letters can smear, tear, or stick together. Keeping them dry helps the words reach the right person clearly."
        )
    ],
}
KNOWLEDGE_ORDER = ["gargoyle", "post_office", "rain", "ladder", "safety", "mail"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    blockage = f["blockage_cfg"]
    return [
        'Write a short myth-flavored story for a 3-to-5-year-old set in a post office that includes the word "gargoyle" and ends happily.',
        f"Tell a gentle story where a curious {child.type} asks why a gargoyle sits over a post office door, and the question leads to a small real problem involving {blockage.material}.",
        "Write a dialogue-rich story in which a child is not allowed to do the dangerous job, but still helps solve the mystery and learns what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    clerk = f["clerk"]
    blockage = f["blockage_cfg"]
    response = f["response_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a curious child at the post office, together with {child.pronoun('possessive')} {adult.label_word} and the clerk. They all notice the gargoyle and the trouble above the door."
        ),
        (
            f"Why did {child.label} start asking about the gargoyle?",
            f"{child.label} looked up and noticed the stone gargoyle on the old building. Curiosity made {child.pronoun('object')} ask what it was doing there and why it seemed to be watching the rain."
        ),
        (
            "What was the real problem at the post office?",
            f"{blockage.Phrase if hasattr(blockage, 'Phrase') else blockage.phrase.capitalize()} was stuck in the spout, so rainwater could not move through it properly. That meant the letters below might get wet."
        ),
        (
            f"Why was {child.label} not allowed to climb up?",
            f"{adult.label_word.capitalize()} said no because roof work is for grown-ups with safe hands and steady shoes. The danger was the height, so {child.label} helped by watching and asking careful questions instead."
        ),
    ]
    if f["fixed"]:
        qa.append(
            (
                "How did they solve the problem?",
                f"{response.qa_text} That cleared the blockage so the water could pour out the right way instead of spilling onto the mail."
            )
        )
        qa.append(
            (
                "How did the story end?",
                "The letters stayed dry, the child's own letter was mailed, and the gargoyle seemed friendly instead of grim. The ending feels happy because curiosity led to help, not trouble."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"gargoyle", "post_office", "mail"}
    tags |= set(world.facts["curiosity_cfg"].tags)
    tags |= set(world.facts["response_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, val in (("stone", ent.stone), ("climbable", ent.climbable)) if val]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="old_stone_post_office",
        curiosity="mouth_question",
        blockage="leaves",
        response="ladder_brush",
        child_name="Lina",
        child_type="girl",
        adult_type="mother",
        clerk_type="clerk_man",
    ),
    StoryParams(
        setting="village_post_office",
        curiosity="watcher_question",
        blockage="twigs",
        response="ladder_hand",
        child_name="Oren",
        child_type="boy",
        adult_type="father",
        clerk_type="clerk_woman",
    ),
    StoryParams(
        setting="old_stone_post_office",
        curiosity="sad_question",
        blockage="moss",
        response="ladder_brush",
        child_name="Mira",
        child_type="girl",
        adult_type="father",
        clerk_type="clerk_woman",
    ),
]


def explain_rejection(blockage: Blockage, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). A child should not be sent to climb up to a roof.)"
        )
    if not response.reaches_roof:
        return "(No story: this response cannot reach the gargoyle's spout.)"
    if blockage.material not in response.clears:
        return (
            f"(No story: {response.id} would not reasonably clear {blockage.material}. "
            f"Choose a response that can actually remove the blockage.)"
        )
    return "(No story: this response does not solve the problem.)"


ASP_RULES = r"""
hazard(B) :- blockage(B), severity(B,S), S > 0.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
works(B,R) :- blockage(B), response(R), sensible(R), reaches_roof(R), clears(R,B).
valid(Setting,Curiosity,Blockage) :- setting(Setting), curiosity(Curiosity), hazard(Blockage).

chosen_valid :- chosen_setting(S), chosen_curiosity(C), chosen_blockage(B), valid(S,C,B).
chosen_works :- chosen_blockage(B), chosen_response(R), works(B,R).
outcome(happy) :- chosen_valid, chosen_works.
outcome(fail) :- chosen_valid, not chosen_works.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity", cid))
    for bid, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", bid))
        lines.append(asp.fact("severity", bid, blockage.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        if response.reaches_roof:
            lines.append(asp.fact("reaches_roof", rid))
        for material in sorted(response.clears):
            lines.append(asp.fact("clears", rid, material))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_curiosity", params.curiosity),
            asp.fact("chosen_blockage", params.blockage),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "happy" if response_works(BLOCKAGES[params.blockage], RESPONSES[params.response]) else "fail"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sense, p_sense = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child, a gargoyle, and a small post-office mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--adult-type", choices=["mother", "father"])
    ap.add_argument("--clerk-type", choices=["clerk_man", "clerk_woman"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            raise StoryError(explain_rejection(BLOCKAGES[args.blockage] if args.blockage else next(iter(BLOCKAGES.values())), response))
    if args.blockage and args.response:
        blockage = BLOCKAGES[args.blockage]
        response = RESPONSES[args.response]
        if not response_works(blockage, response):
            raise StoryError(explain_rejection(blockage, response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.curiosity is None or combo[1] == args.curiosity)
        and (args.blockage is None or combo[2] == args.blockage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, curiosity_id, blockage_id = rng.choice(sorted(combos))
    blockage = BLOCKAGES[blockage_id]

    if args.response is None:
        candidates = [
            rid for rid, response in RESPONSES.items()
            if response_works(blockage, response)
        ]
        if not candidates:
            raise StoryError("(No sensible response can solve the chosen blockage.)")
        response_id = rng.choice(sorted(candidates))
    else:
        response_id = args.response

    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    clerk_type = args.clerk_type or rng.choice(["clerk_man", "clerk_woman"])

    return StoryParams(
        setting=setting_id,
        curiosity=curiosity_id,
        blockage=blockage_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
        clerk_type=clerk_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.curiosity not in CURIOSITIES:
        raise StoryError(f"(Unknown curiosity: {params.curiosity})")
    if params.blockage not in BLOCKAGES:
        raise StoryError(f"(Unknown blockage: {params.blockage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    blockage = BLOCKAGES[params.blockage]
    response = RESPONSES[params.response]
    if not response_works(blockage, response):
        raise StoryError(explain_rejection(blockage, response))

    world = tell(
        SETTINGS[params.setting],
        CURIOSITIES[params.curiosity],
        blockage,
        response,
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
        clerk_type=params.clerk_type,
    )
    world.get("child").label = params.child_name
    story = world.render().replace("child", params.child_name)
    story = story.replace("adult", world.get("adult").label_word.capitalize(), 1) if False else world.render()
    story = story.replace("child", params.child_name) if "child" in world.render() else world.render()

    named_story = world.render().replace("child", params.child_name)
    named_story = named_story.replace("adult", world.get("adult").label_word)
    named_story = named_story.replace("clerk", "clerk")
    named_story = named_story.replace("  ", " ")

    final_story = named_story.replace(" child ", f" {params.child_name} ")
    final_story = final_story.replace(" child,", f" {params.child_name},")
    final_story = final_story.replace(" child.", f" {params.child_name}.")
    final_story = final_story.replace(" child's", f" {params.child_name}'s")
    final_story = final_story.replace(" child?", f" {params.child_name}?")
    final_story = final_story.replace(" child!", f" {params.child_name}!")
    final_story = final_story.replace(" child\"", f" {params.child_name}\"")

    return StorySample(
        params=params,
        story=final_story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show works/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (setting, curiosity, blockage) combos:\n")
        for setting_id, curiosity_id, blockage_id in combos:
            print(f"  {setting_id:22} {curiosity_id:16} {blockage_id}")
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
            header = f"### {p.child_name}: {p.curiosity} at {p.setting} ({p.blockage}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
