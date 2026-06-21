#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py
==============================================================================

A standalone story world for a gentle animal tale about a hungry little animal
who sneaks food, tries to deny it, and learns that a small lie can let havoc
grow.

The domain is deliberately small and classical:

- a young animal is helping store food at home
- a tempting snack sits in a precarious place
- the child sneaks a taste, the storage tips, and food spills
- when asked, the child tries to deny doing it
- the delay before the truth comes out lets visiting animals or the rolling mess
  create more havoc
- a sensible cleanup restores order, and the elder teaches the lesson:
  tell the truth quickly and ask before taking

Run it
------
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py --theme squirrel_hollow
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py --snack berries --response broom_pan
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/deny_havoc_dialogue_lesson_learned_animal_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "doe"}
        male = {"boy", "father", "uncle", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.type
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
    home: str
    opening: str
    pantry_place: str
    elder_word: str
    child_kind: str
    plural_homefolk: str
    ending_place: str
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
class Snack:
    id: str
    label: str
    phrase: str
    plural: bool
    mess_kind: str
    spread: int
    scent: int
    visitors: str
    spill_line: str
    clue: str
    lesson_name: str
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
class Storage:
    id: str
    label: str
    place: str
    reach_line: str
    tip_line: str
    stable: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    handles: set[str]
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    home = world.get("home")
    child = world.get("child")
    if snack.meters["spilled"] >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            home.meters["mess"] += 1
            child.memes["worry"] += 1
            out.append("__spill__")
    return out


def _r_visitors(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    home = world.get("home")
    if snack.meters["spilled"] < THRESHOLD:
        return out
    if world.facts.get("confessed", False):
        return out
    if world.facts.get("delay_left", 0) <= 0:
        return out
    sig = ("visitors", world.facts["delay_left"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    home.meters["havoc"] += 1
    home.meters["visitors"] += snack.attrs["scent"]
    world.get("child").memes["guilt"] += 1
    out.append("__havoc__")
    return out


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="visitors", tag="physical", apply=_r_visitors),
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


def compatible_response(snack: Snack, response: Response) -> bool:
    return snack.mess_kind in response.handles and response.sense >= SENSE_MIN


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for snack_id, snack in SNACKS.items():
            for response_id, response in RESPONSES.items():
                if compatible_response(snack, response):
                    combos.append((theme_id, snack_id, response_id))
    return combos


def spill_severity(snack: Snack, delay: int) -> int:
    return snack.spread + delay


def is_restored(snack: Snack, response: Response, delay: int) -> bool:
    return response.power >= spill_severity(snack, delay)


def predict_havoc(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.facts["delay_left"] = delay
    sim.facts["confessed"] = False
    snack = sim.get("snack")
    snack.meters["spilled"] += 1
    propagate(sim, narrate=False)
    for _ in range(delay):
        propagate(sim, narrate=False)
        sim.facts["delay_left"] -= 1
    return {
        "havoc": sim.get("home").meters["havoc"],
        "visitors": sim.get("home").meters["visitors"],
    }


def introduce(world: World, theme: Theme, child: Entity, elder: Entity, snack: Snack, storage: Storage) -> None:
    child.memes["hunger"] += 1
    child.memes["joy"] += 1
    world.say(
        f"In {theme.home}, {theme.opening} {child.id} helped {elder.id} put away "
        f"{snack.phrase}. The tastiest bundle sat {storage.place}, and the whole "
        f"{theme.pantry_place} smelled rich and cozy."
    )
    world.say(
        f'"Please wait until nibble-time," {elder.id} said. "{snack.lesson_name.capitalize()} '
        f'is for sharing, not for sneaking."'
    )


def tempt(world: World, child: Entity, snack: Snack, storage: Storage) -> None:
    child.memes["desire"] += 1
    world.say(
        f"But {child.id}'s nose twitched. {storage.reach_line} because one tiny taste "
        f"felt too good to wait for."
    )


def spill(world: World, child: Entity, snack_cfg: Snack, storage: Storage) -> None:
    snack = world.get("snack")
    snack.meters["spilled"] += 1
    snack.meters["open"] += 1
    propagate(world, narrate=False)
    world.say(storage.tip_line)
    world.say(snack_cfg.spill_line)


def question(world: World, elder: Entity, child: Entity) -> None:
    world.say(
        f'{elder.id} turned at once. "What happened in the pantry nook?" {elder.pronoun()} asked.'
    )


def deny(world: World, child: Entity, snack: Snack) -> None:
    child.memes["denial"] += 1
    world.facts["denied"] = True
    world.say(
        f'"I did not touch the {snack.label}," said {child.id}. {child.pronoun().capitalize()} tried '
        f"to deny it, even while {snack.clue}."
    )


def havoc_beats(world: World, theme: Theme, snack: Snack, delay: int) -> None:
    world.facts["delay_left"] = delay
    for beat in range(delay):
        propagate(world, narrate=False)
        world.facts["delay_left"] = max(0, world.facts["delay_left"] - 1)
        if beat == 0:
            world.say(
                f"While the little lie sat in the air, {snack.visitors} slipped toward the smell. "
                f"Soon the floor was full of tiny feet and bigger trouble."
            )
        elif beat == 1:
            world.say(
                f"The mess rolled and spread through {theme.ending_place}, and the small confusion "
                f"turned into real havoc."
            )
        else:
            world.say(
                "By then, everyone was darting, hopping, or flapping at once, and the mess grew wider."
            )


def evidence(world: World, elder: Entity, child: Entity, snack: Snack) -> None:
    child.memes["shame"] += 1
    world.say(
        f'{elder.id} looked at {child.id}\'s paws, then at the floor. "{snack.clue.capitalize()}," '
        f'{elder.pronoun()} said softly. "The truth is right here."'
    )


def confess(world: World, child: Entity, elder: Entity, snack: Snack) -> None:
    child.memes["honesty"] += 1
    child.memes["relief"] += 1
    world.facts["confessed"] = True
    world.say(
        f'{child.id} drooped {child.pronoun("possessive")} whiskers. "I am sorry," {child.pronoun()} whispered. '
        f'"I wanted {snack.lesson_name}, and I tipped it. Then I tried to deny it."'
    )


def cleanup_success(world: World, elder: Entity, child: Entity, response: Response, snack: Snack, theme: Theme) -> None:
    home = world.get("home")
    snack_ent = world.get("snack")
    home.meters["mess"] = 0.0
    home.meters["havoc"] = 0.0
    snack_ent.meters["spilled"] = 0.0
    body = response.text.format(snack=snack.label)
    world.say(
        f"{elder.id} nodded and {body}. In a few calm moments, the visitors were guided out, the floor was tidy again, and the pantry nook felt peaceful."
    )
    world.say(
        f'"Next time, tell me fast," {elder.id} said. "When we deny the truth, we give little problems time to grow."'
    )
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    child.memes["guilt"] = 0.0
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"That evening, {child.id} asked before taking a snack, and {elder.id} set one in a small leaf bowl. They nibbled together by {theme.ending_place}, and the new quiet proved what {child.id} had learned."
    )


def cleanup_fail(world: World, elder: Entity, child: Entity, response: Response, snack: Snack, theme: Theme) -> None:
    body = response.fail.format(snack=snack.label)
    world.say(
        f"{elder.id} tried to help and {body}. The muddle stayed for a long while, and supper had to wait until every last crumb and track was found."
    )
    world.say(
        f'"Do you see why this felt so big?" {elder.id} asked. "The spill was small at first, but the deny made the havoc bigger."'
    )
    child.memes["lesson"] += 1
    child.memes["sadness"] += 1
    child.memes["honesty"] += 1
    world.say(
        f"The next day, {child.id} still asked before taking {snack.lesson_name}, and {elder.id} answered with a kind nod. The pantry was mended slowly, but the truth came quicker after that."
    )


def tell(
    theme: Theme,
    snack_cfg: Snack,
    storage: Storage,
    response: Response,
    *,
    child_name: str = "Pip",
    child_type: str = "girl",
    elder_name: str = "Moss",
    elder_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", label=elder_name))
    home = world.add(Entity(id="home", type="home", label=theme.home))
    snack = world.add(Entity(id="snack", type="food", label=snack_cfg.label))
    snack.attrs["scent"] = snack_cfg.scent

    world.facts["theme"] = theme
    world.facts["snack_cfg"] = snack_cfg
    world.facts["storage"] = storage
    world.facts["response"] = response
    world.facts["delay_left"] = 0
    world.facts["confessed"] = False
    world.facts["denied"] = False

    introduce(world, theme, child, elder, snack_cfg, storage)
    world.para()
    tempt(world, child, snack_cfg, storage)
    spill(world, child, snack_cfg, storage)
    question(world, elder, child)
    deny(world, child, snack_cfg)

    world.para()
    havoc_beats(world, theme, snack_cfg, delay)
    evidence(world, elder, child, snack_cfg)
    confess(world, child, elder, snack_cfg)

    world.para()
    restored = is_restored(snack_cfg, response, delay)
    if restored:
        cleanup_success(world, elder, child, response, snack_cfg, theme)
    else:
        cleanup_fail(world, elder, child, response, snack_cfg, theme)

    world.facts.update(
        child=child,
        elder=elder,
        home=home,
        snack=snack,
        confessed=True,
        delay=delay,
        severity=spill_severity(snack_cfg, delay),
        restored=restored,
        visitors=home.meters["visitors"],
        outcome="restored" if restored else "messy",
    )
    return world


KNOWLEDGE = {
    "honesty": [
        (
            "Why is it better to tell the truth quickly after a mistake?",
            "Telling the truth quickly helps grown-ups fix the problem sooner. A small mess can stay small if nobody wastes time hiding it."
        )
    ],
    "deny": [
        (
            "What does deny mean?",
            "To deny something is to say it did not happen or that you did not do it. Sometimes people deny a mistake because they feel scared or ashamed."
        )
    ],
    "havoc": [
        (
            "What is havoc?",
            "Havoc means wild confusion and messy trouble. A little problem can turn into havoc when it spreads and nobody stops it in time."
        )
    ],
    "acorns": [
        (
            "Why do acorns make a slippery mess on the floor?",
            "Acorns are round and hard, so they can roll in many directions. That makes them easy to scatter and easy to trip over."
        )
    ],
    "berries": [
        (
            "Why are spilled berries hard to clean up?",
            "Berries can burst and smear juice where they land. Their sweet smell can also draw other hungry animals toward the mess."
        )
    ],
    "seeds": [
        (
            "Why do scattered seeds spread so far?",
            "Seeds are tiny and light, so they bounce and slip into little cracks. A few seeds can quickly become a wide, fussy mess."
        )
    ],
    "broom": [
        (
            "What does a broom help you do?",
            "A broom lets you sweep dry things together into one pile. That makes rolling crumbs or nuts easier to gather."
        )
    ],
    "cloth": [
        (
            "Why is a cloth useful for sticky spills?",
            "A cloth can wipe soft or juicy messes off a surface. It works better than sweeping when the spill smears."
        )
    ],
    "ask_first": [
        (
            "Why should a child ask before taking stored food?",
            "Stored food may be counted for a meal or kept in a careful place. Asking first shows respect and helps keep everyone safe and prepared."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "deny",
    "havoc",
    "honesty",
    "acorns",
    "berries",
    "seeds",
    "broom",
    "cloth",
    "ask_first",
]


THEMES = {
    "squirrel_hollow": Theme(
        id="squirrel_hollow",
        home="a warm oak-tree hollow",
        opening="a little squirrel named Pip",
        pantry_place="pantry nook",
        elder_word="mother",
        child_kind="squirrel",
        plural_homefolk="squirrels",
        ending_place="the round hollow window",
        tags={"honesty"},
    ),
    "rabbit_burrow": Theme(
        id="rabbit_burrow",
        home="a tidy burrow under the hill",
        opening="a little rabbit named Pip",
        pantry_place="cool root-shelf",
        elder_word="mother",
        child_kind="rabbit",
        plural_homefolk="rabbits",
        ending_place="the burrow doorway",
        tags={"honesty"},
    ),
    "beaver_lodge": Theme(
        id="beaver_lodge",
        home="a snug lodge beside the pond",
        opening="a little beaver named Pip",
        pantry_place="reed pantry",
        elder_word="father",
        child_kind="beaver",
        plural_homefolk="beavers",
        ending_place="the smooth lodge step",
        tags={"honesty"},
    ),
}

SNACKS = {
    "acorns": Snack(
        id="acorns",
        label="acorns",
        phrase="a heap of bright brown acorns",
        plural=True,
        mess_kind="dry",
        spread=1,
        scent=1,
        visitors="two chipmunks and a curious jay",
        spill_line="Down they came: tap-tap-tap, bouncing acorns in every corner.",
        clue="dusty acorn bits clung to the child's paws",
        lesson_name="acorns",
        tags={"acorns", "ask_first"},
    ),
    "berries": Snack(
        id="berries",
        label="berries",
        phrase="a basket of shiny red berries",
        plural=True,
        mess_kind="sticky",
        spread=2,
        scent=2,
        visitors="ants and finches",
        spill_line="The berries plopped, rolled, and burst into little ruby smears.",
        clue="berry juice shone on the child's paws",
        lesson_name="berries",
        tags={"berries", "ask_first"},
    ),
    "seeds": Snack(
        id="seeds",
        label="seeds",
        phrase="a pouch of sunflower seeds",
        plural=True,
        mess_kind="dry",
        spread=1,
        scent=1,
        visitors="sparrows and field mice",
        spill_line="The seeds hissed across the floor like tiny rain and skittered into cracks.",
        clue="seed shells dotted the child's whiskers",
        lesson_name="seeds",
        tags={"seeds", "ask_first"},
    ),
}

STORAGES = {
    "hanging_basket": Storage(
        id="hanging_basket",
        label="hanging basket",
        place="from a peg above the child's head",
        reach_line="Pip stood on tiptoe and tugged the hanging basket",
        tip_line="The basket swung once, twice, and then tipped sideways.",
        stable=True,
        tags={"basket"},
    ),
    "tall_jar": Storage(
        id="tall_jar",
        label="tall jar",
        place="on the highest shelf",
        reach_line="Pip stretched for the tall jar",
        tip_line="The jar wobbled on the edge, popped open, and tipped forward.",
        stable=True,
        tags={"jar"},
    ),
    "reed_tray": Storage(
        id="reed_tray",
        label="reed tray",
        place="near the back of the pantry shelf",
        reach_line="Pip pulled the reed tray a little closer",
        tip_line="The tray skidded, bumped the shelf edge, and flipped down.",
        stable=True,
        tags={"tray"},
    ),
}

RESPONSES = {
    "broom_pan": Response(
        id="broom_pan",
        sense=3,
        power=3,
        handles={"dry"},
        text="took up a tiny broom and leaf-pan, swept the {snack} into a neat pile, and poured them back into a safe bowl",
        fail="swept what {elder_pronoun} could, but dry crumbs had already rolled too far to catch at once",
        qa_text="swept the spilled food together with a little broom and pan",
        tags={"broom"},
    ),
    "damp_cloth": Response(
        id="damp_cloth",
        sense=3,
        power=3,
        handles={"sticky"},
        text="pressed a damp leaf-cloth over the sticky spots, wiped the {snack} up gently, and scrubbed away the sweet smell",
        fail="wiped and wiped, but the sticky tracks had already spread into too many corners",
        qa_text="used a damp cloth to wipe up the sticky spill",
        tags={"cloth"},
    ),
    "scoop_bowl": Response(
        id="scoop_bowl",
        sense=2,
        power=2,
        handles={"dry"},
        text="used a shallow bark bowl to scoop the {snack} together before the visitors could carry more away",
        fail="scooped several mouthfuls back, but too many pieces had scattered under shelves and mats",
        qa_text="scooped the dry spill back into a bowl",
        tags={"broom"},
    ),
    "splash_water": Response(
        id="splash_water",
        sense=1,
        power=1,
        handles={"dry", "sticky"},
        text="splashed water everywhere and made the whole pantry sloshy",
        fail="splashed water, which only spread the mess farther",
        qa_text="splashed water at the mess",
        tags={"cloth"},
    ),
}

GIRL_NAMES = ["Pip", "Tansy", "Mina", "Nell", "Hazel", "Poppy"]
BOY_NAMES = ["Pip", "Bram", "Ollie", "Rowan", "Moss", "Finn"]
TRAITS = ["hungry", "bouncy", "curious", "impulsive", "eager"]


@dataclass
class StoryParams:
    theme: str
    snack: str
    storage: str
    response: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
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


def pair_prompt_child(theme: Theme) -> str:
    return theme.child_kind


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    snack = f["snack_cfg"]
    child = f["child"]
    elder = f["elder"]
    restored = f["restored"]
    if restored:
        return [
            f'Write a short animal story for a 3-to-5-year-old that uses the words "deny" and "havoc". Include dialogue and a clear lesson learned.',
            f"Tell a gentle story where a little {pair_prompt_child(theme)} named {child.id} spills {snack.label}, tries to deny it, and then learns that honesty helps fix trouble quickly.",
            f'Write an animal-home story with dialogue, a mistake, a confession, and a warm ending that teaches children not to deny what they did.',
        ]
    return [
        f'Write a short animal story for a 3-to-5-year-old that uses the words "deny" and "havoc". Include dialogue and a lesson learned, even if the cleanup takes a long time.',
        f"Tell a cautionary animal story where {child.id} denies spilling {snack.label}, the mess grows into havoc, and {elder.id} explains why the lie made things worse.",
        f'Write an animal story with dialogue where a child tells an untrue thing after a mistake, and the ending shows that truth helps sooner than hiding.',
    ]


def pair_word(child: Entity, theme: Theme) -> str:
    article = "an" if theme.child_kind[0].lower() in "aeiou" else "a"
    return f"{article} little {theme.child_kind}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    snack = f["snack_cfg"]
    storage = f["storage"]
    theme = f["theme"]
    response = f["response"]
    outcome = f["outcome"]
    delay = f["delay"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(child, theme)} named {child.id} and {elder.id}, who were putting away food at home."
        ),
        (
            f"Why did {child.id} reach for the {snack.label}?",
            f"{child.id} wanted a taste before nibble-time and did not want to wait. That hungry feeling is what led {child.pronoun('object')} to reach for the food in its high place."
        ),
        (
            f"What happened when {child.id} touched the {storage.label}?",
            f"The storage tipped and the {snack.label} spilled across the floor. The accident turned one sneaky reach into a real mess at once."
        ),
        (
            f"What did {child.id} say when {elder.id} asked what happened?",
            f"{child.id} tried to deny doing it and said {child.pronoun('subject')} had not touched the {snack.label}. The clue on {child.pronoun('possessive')} paws showed the truth anyway."
        ),
    ]
    if delay > 0:
        qa.append(
            (
                "Why did the mess turn into havoc?",
                f"The spill was left alone while {child.id} kept denying it, so other hungry animals and more confusion came in. The delay gave the trouble time to spread instead of being cleaned up right away."
            )
        )
    if outcome == "restored":
        qa.append(
            (
                f"How did {elder.id} fix the problem?",
                f"{elder.id} {response.qa_text}. Because the cleanup matched the kind of spill, the pantry became calm again."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned to tell the truth quickly and ask before taking stored food. That is why the story ends with the snack being shared peacefully instead of hidden."
            )
        )
    else:
        qa.append(
            (
                "Did the cleanup become easy right away?",
                "No. The lie let the mess spread too long, so the cleanup took much more time. The child still learned that honesty would have kept the problem smaller."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that a mistake can be mended, but denying it can make the work and worry bigger. The next day {child.pronoun('subject')} asked first instead of sneaking."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    snack = f["snack_cfg"]
    response = f["response"]
    tags = {"deny", "havoc", "honesty"} | set(snack.tags) | set(response.tags)
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {{'delay': {world.facts.get('delay')}, 'outcome': {world.facts.get('outcome')!r}, 'severity': {world.facts.get('severity')}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="squirrel_hollow",
        snack="acorns",
        storage="hanging_basket",
        response="broom_pan",
        child_name="Pip",
        child_type="girl",
        elder_name="Moss",
        elder_type="mother",
        delay=0,
    ),
    StoryParams(
        theme="rabbit_burrow",
        snack="berries",
        storage="tall_jar",
        response="damp_cloth",
        child_name="Hazel",
        child_type="girl",
        elder_name="Thorn",
        elder_type="mother",
        delay=1,
    ),
    StoryParams(
        theme="beaver_lodge",
        snack="seeds",
        storage="reed_tray",
        response="scoop_bowl",
        child_name="Finn",
        child_type="boy",
        elder_name="Rowan",
        elder_type="father",
        delay=1,
    ),
    StoryParams(
        theme="rabbit_burrow",
        snack="berries",
        storage="hanging_basket",
        response="damp_cloth",
        child_name="Nell",
        child_type="girl",
        elder_name="Fern",
        elder_type="mother",
        delay=2,
    ),
    StoryParams(
        theme="squirrel_hollow",
        snack="seeds",
        storage="tall_jar",
        response="scoop_bowl",
        child_name="Ollie",
        child_type="boy",
        elder_name="Bram",
        elder_type="father",
        delay=2,
    ),
]


def explain_response(snack: Snack, response: Response) -> str:
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses() if snack.mess_kind in r.handles))
        return (
            f"(No story: response '{response.id}' is too weak or not sensible here. "
            f"Try one of: {better}.)"
        )
    if snack.mess_kind not in response.handles:
        return (
            f"(No story: {response.id} does not suit a {snack.label} spill. "
            f"Choose a cleanup that actually handles a {snack.mess_kind} mess.)"
        )
    return "(No story: invalid cleanup choice.)"


def outcome_of(params: StoryParams) -> str:
    snack = SNACKS[params.snack]
    response = RESPONSES[params.response]
    return "restored" if is_restored(snack, response, params.delay) else "messy"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
compatible(Sn, R) :- snack(Sn), response(R), mess_kind(Sn, M), handles(R, M), sense(R, S), sense_min(Min), S >= Min.
valid(T, Sn, R) :- theme(T), snack(Sn), response(R), compatible(Sn, R).

% --- outcome ---------------------------------------------------------------
severity(V) :- chosen_snack(Sn), spread(Sn, Sp), delay(D), V = Sp + D.
restored :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(restored) :- restored.
outcome(messy) :- not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("mess_kind", snack_id, snack.mess_kind))
        lines.append(asp.fact("spread", snack_id, snack.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for handle in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, handle))
    for storage_id in STORAGES:
        lines.append(asp.fact("storage", storage_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a child sneaks food, tries to deny it, and learns that honesty stops havoc from growing."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child keeps denying before confessing")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (theme, snack, response) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random) -> tuple[str, str]:
    child_type = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    return rng.choice(pool), child_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.response:
        snack = SNACKS[args.snack]
        response = RESPONSES[args.response]
        if not compatible_response(snack, response):
            raise StoryError(explain_response(snack, response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.snack is None or combo[1] == args.snack)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, snack_id, response_id = rng.choice(sorted(combos))
    storage_id = args.storage or rng.choice(sorted(STORAGES))
    child_name, child_type = _pick_name(rng)
    elder_type = THEMES[theme_id].elder_word
    elder_pool = GIRL_NAMES if elder_type == "mother" else BOY_NAMES
    elder_name_choices = [n for n in elder_pool if n != child_name] or elder_pool
    elder_name = rng.choice(elder_name_choices)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        theme=theme_id,
        snack=snack_id,
        storage=storage_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        elder_name=elder_name,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.storage not in STORAGES:
        raise StoryError(f"(Unknown storage: {params.storage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Delay must be 0, 1, or 2.)")

    snack = SNACKS[params.snack]
    response = RESPONSES[params.response]
    if not compatible_response(snack, response):
        raise StoryError(explain_response(snack, response))

    world = tell(
        THEMES[params.theme],
        snack,
        STORAGES[params.storage],
        response,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, snack, response) combos:\n")
        for theme_id, snack_id, response_id in combos:
            print(f"  {theme_id:16} {snack_id:8} {response_id}")
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
            header = f"### {p.child_name}: {p.snack} in {p.theme} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
