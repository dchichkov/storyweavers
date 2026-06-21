#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py
=====================================================================================

A standalone story world for a cautionary, nursery-rhyme-like tale about a
children's make-believe league, a pile of crummy old swords, and the wiser
choice of safe play.

The world models a simple common-sense constraint:

- A play group wants something grand for its league parade.
- One child is tempted to use real, crummy swords from a shed or cellar.
- If the blades are rusted and sharp enough, waving them causes a cut scare.
- A sensible grown-up takes the swords away and offers soft, safe parade props.
- Some blunt objects are known to the world but rejected as "not really swords,"
  because then the warning and rescue become weak or dishonest.

The prose stays close to a nursery-rhyme voice: rhythmic, child-facing, and full
of dialogue, while still being driven by simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py --theme knights --cache shed --swords rusty_short
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py --swords foam_stage   # rejected
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/league_crummy_swords_dialogue_cautionary_nursery_rhyme.py --verify
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
BRAG_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "thoughtful", "gentle"}


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
    rusty: bool = False
    sharp: bool = False
    soft: bool = False
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    opening: str
    chant: str
    goal: str
    march_line: str
    ending_line: str
    role_word: str
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
class Cache:
    id: str
    label: str
    where_line: str
    find_line: str
    adult_source: str
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
class SwordSet:
    id: str
    label: str
    phrase: str
    warning_name: str
    description: str
    clang: str
    danger: int
    sense: int
    rusty: bool = False
    sharp: bool = False
    real: bool = True
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
class SafeProp:
    id: str
    label: str
    phrase: str
    move_line: str
    glow_line: str
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
class AdultFix:
    id: str
    sense: int
    text: str
    qa_text: str
    lesson: str
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
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_cut_alarm(world: World) -> list[str]:
    out: list[str] = []
    sword = world.get("swords")
    friend = world.get("friend")
    room = world.get("yard")
    if sword.meters["waved"] < THRESHOLD:
        return out
    if not sword.sharp:
        return out
    sig = ("cut_alarm", sword.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.meters["nicked"] += 1
    room.meters["danger"] += 1
    friend.memes["fear"] += 1
    world.get("leader").memes["fear"] += 1
    out.append("__nick__")
    return out


def _r_rust_worry(world: World) -> list[str]:
    out: list[str] = []
    sword = world.get("swords")
    if sword.meters["waved"] < THRESHOLD or not sword.rusty:
        return out
    sig = ("rust_worry", sword.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("parent").memes["alarm"] += 1
    out.append("__rust__")
    return out


CAUSAL_RULES = [
    Rule(name="cut_alarm", tag="physical", apply=_r_cut_alarm),
    Rule(name="rust_worry", tag="physical", apply=_r_rust_worry),
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


def hazardous(swords: SwordSet) -> bool:
    return swords.real and swords.sharp and swords.danger >= 2


def sensible_fixes() -> list[AdultFix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def would_back_down(relation: str, leader_age: int, friend_age: int, trait: str) -> bool:
    friend_older = relation == "siblings" and friend_age > leader_age
    careful = 5.0 if trait in CAREFUL_TRAITS else 3.0
    authority = careful + 1.0 + (3.0 if friend_older else 0.0)
    return friend_older and authority > BRAG_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    wave_bad_swords(sim, narrate=False)
    return {
        "nick": sim.get("friend").meters["nicked"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def introduce(world: World, theme: Theme, leader: Entity, friend: Entity) -> None:
    for kid in (leader, friend):
        kid.memes["joy"] += 1
    world.say(
        f"In a little patch of sun and shade, {leader.id} and {friend.id} made {theme.scene}. "
        f"{theme.opening}"
    )
    world.say(
        f'"{theme.chant}" sang {leader.id}. "{theme.goal}!"'
    )


def need_props(world: World, theme: Theme, friend: Entity) -> None:
    world.say(
        f"But the march looked plain and small. {friend.id} looked around and said, "
        f'"Our {theme.role_word} league needs something grander for {theme.march_line}."'
    )


def tempt(world: World, leader: Entity, cache: Cache, swords: SwordSet) -> None:
    leader.memes["brag"] += 1
    world.say(
        f'{leader.id} clapped {leader.pronoun("possessive")} hands. "I know!" {leader.pronoun().capitalize()} cried. '
        f'"{cache.find_line} {swords.phrase}!"'
    )
    world.say(
        f"They sounded brave in the mouth, but the thought itself was crummy and wrong."
    )


def warn(world: World, friend: Entity, leader: Entity, swords: SwordSet, parent: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    friend.memes["caution"] += 1
    extra = ""
    if pred["nick"]:
        extra = " They could slip and nick someone."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. '
        f'"No, {leader.id}, not those {swords.warning_name}," {friend.pronoun()} said. '
        f'"{parent.label_word.capitalize()} says real swords are for grown-up hands, not play."{extra}'
    )


def back_down(world: World, leader: Entity, friend: Entity, cache: Cache, swords: SwordSet) -> None:
    leader.memes["brag"] = 0.0
    leader.memes["relief"] += 1
    friend.memes["relief"] += 1
    sib = "brother" if friend.type == "boy" else "sister"
    world.say(
        f'"But they would make our league look bold," said {leader.id}. '
        f'Then {leader.pronoun()} saw that {friend.id}, {leader.pronoun("possessive")} big {sib}, '
        f"meant every word. So {leader.pronoun()} sighed, left the {swords.warning_name} in {cache.label}, and stepped back."
    )


def defy(world: World, leader: Entity, friend: Entity, relation: str) -> None:
    leader.memes["defiance"] += 1
    if relation == "siblings" and leader.age > friend.age:
        world.say(
            f'"Don\'t fuss," said {leader.id}. "Our league will look splendid." '
            f"Because {leader.id} was older, {friend.id} could not stop {leader.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"Don\'t fuss," said {leader.id}. "Our league will look splendid." '
            f"And before {friend.id} could answer again, {leader.pronoun()} snatched the swords."
        )


def wave_bad_swords(world: World, narrate: bool = True) -> None:
    sword = world.get("swords")
    sword.meters["waved"] += 1
    propagate(world, narrate=narrate)


def accident(world: World, swords: SwordSet, friend: Entity) -> None:
    wave_bad_swords(world)
    world.say(
        f'{swords.clang} went the {swords.warning_name} as they flashed in the air. '
        f'One scraped past {friend.id}\'s hand and left a tiny red line.'
    )
    world.say(
        f'"Ow!" cried {friend.id}. The whole pretend league stopped at once.'
    )


def rescue(world: World, parent: Entity, fix: AdultFix, swords: SwordSet, cache: Cache) -> None:
    yard = world.get("yard")
    friend = world.get("friend")
    sword = world.get("swords")
    sword.meters["taken_away"] += 1
    sword.meters["waved"] = 0.0
    yard.meters["danger"] = 0.0
    friend.memes["fear"] = 0.0
    world.get("leader").memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} came quickly from {cache.adult_source} and {fix.text}.'
    )
    if swords.rusty:
        world.say(
            f'"Those are crummy old swords," {parent.pronoun()} said. "Rust and sharp edges do not belong in games."'
        )
    else:
        world.say(
            f'"Those are real swords," {parent.pronoun()} said. "Real blades do not belong in games."'
        )


def soothe_and_lesson(world: World, parent: Entity, leader: Entity, friend: Entity, fix: AdultFix) -> None:
    for kid in (leader, friend):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'Then {parent.label_word.capitalize()} washed the little scratch, kissed the stinging hand, and spoke softly: '
        f'"{fix.lesson}"'
    )
    world.say(
        f'"We know," whispered {leader.id}. "{swords_word(world)} are not for our league."'
    )


def safe_replace(world: World, parent: Entity, leader: Entity, friend: Entity,
                 theme: Theme, prop1: SafeProp, prop2: SafeProp) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    leader.memes["safety"] += 1
    friend.memes["safety"] += 1
    world.say(
        f'From a high shelf {parent.pronoun()} brought {prop1.phrase} and {prop2.phrase}. '
        f'"Here," {parent.pronoun()} smiled, "these can march and swish and never bite."'
    )
    world.say(
        f"{leader.id} took the {prop1.label}; {friend.id} twirled the {prop2.label}. "
        f"{prop1.move_line}. {prop2.glow_line}."
    )
    world.say(
        f'Soon the little league was marching again, not with crummy swords, but with safe bright things, and {theme.ending_line}.'
    )


def resolve_without_accident(world: World, parent: Entity, leader: Entity, friend: Entity,
                             theme: Theme, prop1: SafeProp, prop2: SafeProp) -> None:
    for kid in (leader, friend):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"{leader.id} and {friend.id} went to tell {parent.label_word} about the plain little march and the bad idea they almost chose."
    )
    world.say(
        f'"A league can still be grand without danger," said {parent.label_word}.'
    )
    safe_replace(world, parent, leader, friend, theme, prop1, prop2)


def swords_word(world: World) -> str:
    return world.facts["swords_cfg"].warning_name


def tell(theme: Theme, cache: Cache, swords_cfg: SwordSet,
         props: tuple[SafeProp, SafeProp], fix: AdultFix,
         leader_name: str = "Nell", leader_gender: str = "girl",
         friend_name: str = "Tom", friend_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         leader_age: int = 5, friend_age: int = 7,
         relation: str = "siblings") -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        age=leader_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    yard = world.add(Entity(id="yard", type="place", label="the yard"))
    swords = world.add(Entity(
        id="swords",
        type="swords",
        label=swords_cfg.label,
        rusty=swords_cfg.rusty,
        sharp=swords_cfg.sharp,
        attrs={"real": swords_cfg.real},
    ))

    leader.memes["brag"] = BRAG_INIT
    friend.memes["caution"] = 5.0 if trait in CAREFUL_TRAITS else 3.0
    world.facts["predicted_danger"] = 0.0

    introduce(world, theme, leader, friend)
    need_props(world, theme, friend)

    world.para()
    tempt(world, leader, cache, swords_cfg)
    warn(world, friend, leader, swords_cfg, parent)

    averted = would_back_down(relation, leader_age, friend_age, trait)
    if averted:
        back_down(world, leader, friend, cache, swords_cfg)
        world.para()
        resolve_without_accident(world, parent, leader, friend, theme, props[0], props[1])
        outcome = "averted"
    else:
        defy(world, leader, friend, relation)
        world.para()
        accident(world, swords_cfg, friend)
        world.para()
        rescue(world, parent, fix, swords_cfg, cache)
        soothe_and_lesson(world, parent, leader, friend, fix)
        world.para()
        safe_replace(world, parent, leader, friend, theme, props[0], props[1])
        outcome = "rescued"

    world.facts.update(
        theme=theme,
        cache=cache,
        swords_cfg=swords_cfg,
        props=props,
        fix=fix,
        leader=leader,
        friend=friend,
        parent=parent,
        outcome=outcome,
        relation=relation,
        nicked=friend.meters["nicked"] >= THRESHOLD,
        averted=averted,
    )
    return world


THEMES = {
    "knights": Theme(
        id="knights",
        scene="a chalk-white knightly league beneath the plum tree",
        opening="A stick was a banner, a basket was a drum, and the stepping-stones were castles in a ring.",
        chant="League, league, brave and bright, march us round till supper-light",
        goal="Let us have a royal parade",
        march_line="their afternoon march",
        ending_line="their song skipped on sweeter than before",
        role_word="knightly",
        tags={"league", "parade"},
    ),
    "garden": Theme(
        id="garden",
        scene="a garden league of lily-guard keepers",
        opening="A twig was a trumpet, a stool was a tower, and the bean rows made lanes for marching feet.",
        chant="League, league, trim and true, make the little garden new",
        goal="Let us guard the flowers",
        march_line="their flower-guard march",
        ending_line="their guarding game bloomed safe and merry",
        role_word="garden",
        tags={"league", "garden"},
    ),
    "moon": Theme(
        id="moon",
        scene="a moon league on the washing-line deck",
        opening="A crate was a ship, a spoon was a bell, and the pale sheets were clouds for a silver sea.",
        chant="League, league, silver soon, sail us softly under moon",
        goal="Let us have a moon parade",
        march_line="their moonlit march",
        ending_line="their moon-song floated light as lace",
        role_word="moon",
        tags={"league", "parade"},
    ),
}

CACHES = {
    "shed": Cache(
        id="shed",
        label="the old shed",
        where_line="behind the rake and the pail",
        find_line="In the shed, behind the rake and the pail, I saw",
        adult_source="the kitchen door",
        tags={"shed"},
    ),
    "cellar": Cache(
        id="cellar",
        label="the cellar steps",
        where_line="under the cellar stairs",
        find_line="Under the cellar stairs there are",
        adult_source="the laundry room",
        tags={"cellar"},
    ),
    "barn": Cache(
        id="barn",
        label="the little barn",
        where_line="up by the hay wall",
        find_line="In the little barn, up by the hay wall, there are",
        adult_source="the porch",
        tags={"barn"},
    ),
}

SWORDS = {
    "rusty_short": SwordSet(
        id="rusty_short",
        label="rusty short swords",
        phrase="two rusty short swords",
        warning_name="crummy swords",
        description="brown with rust and sharp at the tips",
        clang="Clink-clack",
        danger=3,
        sense=3,
        rusty=True,
        sharp=True,
        real=True,
        tags={"swords", "rust", "danger"},
    ),
    "wall_hanger": SwordSet(
        id="wall_hanger",
        label="old wall swords",
        phrase="two old wall swords",
        warning_name="crummy swords",
        description="dusty, heavy, and still edged",
        clang="Clang-cling",
        danger=2,
        sense=2,
        rusty=False,
        sharp=True,
        real=True,
        tags={"swords", "danger"},
    ),
    "blunt_practice": SwordSet(
        id="blunt_practice",
        label="blunt practice swords",
        phrase="two blunt practice swords",
        warning_name="old swords",
        description="dented and heavy, but not keen on the edge",
        clang="Thunk-thank",
        danger=1,
        sense=2,
        rusty=False,
        sharp=False,
        real=True,
        tags={"swords"},
    ),
    # Deliberately refused: not really a cautionary sword hazard.
    "foam_stage": SwordSet(
        id="foam_stage",
        label="foam stage swords",
        phrase="two foam stage swords",
        warning_name="play swords",
        description="soft and floppy as old slippers",
        clang="Flup-flap",
        danger=0,
        sense=1,
        rusty=False,
        sharp=False,
        real=False,
        tags={"pretend"},
    ),
}

SAFE_PROPS = {
    "ribbons": SafeProp(
        id="ribbons",
        label="ribbon wands",
        phrase="two ribbon wands",
        move_line="They swished in pink and blue loops",
        glow_line="The streamer tails danced like tame little comets",
        tags={"ribbons", "safe_play"},
    ),
    "cardboard": SafeProp(
        id="cardboard",
        label="cardboard swords",
        phrase="two thick cardboard swords",
        move_line="They tapped together with a pap-pap sound",
        glow_line="Their painted stars winked in the sun",
        tags={"cardboard", "safe_play"},
    ),
    "spoons": SafeProp(
        id="spoons",
        label="wooden spoon batons",
        phrase="two wooden spoon batons",
        move_line="They bobbed like drum-majors over the grass",
        glow_line="The smooth spoons gleamed honey-brown",
        tags={"spoons", "safe_play"},
    ),
}

FIXES = {
    "take_and_clean": AdultFix(
        id="take_and_clean",
        sense=3,
        text="took the swords away at once, set them high out of reach, and fetched a damp cloth for the scratch",
        qa_text="took the swords away, put them out of reach, and cleaned the scratch",
        lesson="A brave game should not ask for a hurting thing. Sharp swords can cut in one blink.",
        tags={"first_aid", "safe_storage"},
    ),
    "lock_and_bandage": AdultFix(
        id="lock_and_bandage",
        sense=3,
        text="lifted the swords by their handles, locked them in the tool cupboard, and brought a little bandage",
        qa_text="locked the swords away and put on a little bandage",
        lesson="Real swords are not dress-up toys. If you want a march, choose a thing that cannot wound.",
        tags={"first_aid", "safe_storage"},
    ),
    "just_scold": AdultFix(
        id="just_scold",
        sense=1,
        text="only scolded from across the yard",
        qa_text="only scolded from across the yard",
        lesson="That was not enough help.",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nell", "Molly", "Tess", "May", "Kit", "Elsie", "June", "Ivy"]
BOY_NAMES = ["Tom", "Ben", "Ned", "Jack", "Finn", "Leo", "Sam", "Ollie"]
TRAITS = ["careful", "steady", "thoughtful", "gentle", "curious", "hasty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for cache_id in CACHES:
            for sword_id, sword in SWORDS.items():
                if hazardous(sword):
                    combos.append((theme, cache_id, sword_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    cache: str
    swords: str
    prop1: str
    prop2: str
    fix: str
    leader_name: str
    leader_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    leader_age: int = 5
    friend_age: int = 7
    relation: str = "siblings"
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
    "league": [
        (
            "What is a league in this kind of play?",
            "In a make-believe game, a league is a little group joined together for one purpose. Children might use the word when they want their game to feel important and shared."
        )
    ],
    "swords": [
        (
            "Why are real swords dangerous?",
            "Real swords are dangerous because they can be sharp and heavy. Even one quick swing can cut someone before anyone means to."
        )
    ],
    "rust": [
        (
            "What is rust?",
            "Rust is the rough reddish-brown stuff that grows on old metal when it gets wet and sits for a long time. Rust makes metal dirty and crumbly, and it is not safe near a scratch."
        )
    ],
    "safe_play": [
        (
            "What makes a parade prop safe for children?",
            "A safe parade prop should be light, soft, or blunt, so it can be waved without hurting anyone. Good play things look fun without making danger."
        )
    ],
    "first_aid": [
        (
            "What should a grown-up do for a small scratch?",
            "A grown-up should wash the scratch, make sure it is clean, and cover it if needed. Cleaning it quickly helps keep the skin safe."
        )
    ],
    "safe_storage": [
        (
            "Where should sharp tools be kept?",
            "Sharp tools should be kept high up or locked away where children cannot reach them. That keeps play spaces safe."
        )
    ],
    "ribbons": [
        (
            "What is a ribbon wand?",
            "A ribbon wand is a stick with long ribbons tied to it, so it swishes through the air in bright loops. It gives a parade a grand look without any blade."
        )
    ],
    "cardboard": [
        (
            "Why is cardboard safer than metal for pretend swords?",
            "Cardboard is much lighter and softer than metal. It can still look knightly, but it is far less likely to hurt someone."
        )
    ],
    "spoons": [
        (
            "How can wooden spoons become parade batons in pretend play?",
            "Children can pretend a wooden spoon is a baton or magic wand because imagination changes the job of an ordinary thing. Pretend play works best when the object stays safe."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "league",
    "swords",
    "rust",
    "safe_play",
    "first_aid",
    "safe_storage",
    "ribbons",
    "cardboard",
    "spoons",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    swords = f["swords_cfg"]
    leader = f["leader"]
    friend = f["friend"]
    if f["outcome"] == "averted":
        return [
            'Write a nursery-rhyme-style cautionary story with dialogue about a children\'s league that almost uses crummy swords, but stops in time.',
            f'Write a rhythmic story where {leader.id} wants {swords.phrase} for a little league parade, but {friend.id} warns against it and a grown-up offers safer parade things.',
            'Tell a child-facing story that includes the words "league," "crummy," and "swords," and ends with the game turning safe and bright.'
        ]
    return [
        'Write a nursery-rhyme-style cautionary story with dialogue about a little league and a bad idea involving crummy swords.',
        f'Write a rhythmic story where {leader.id} grabs {swords.warning_name} for {theme.march_line}, a small scratch happens, and a calm grown-up turns the game safe again.',
        'Tell a child-facing cautionary tale that includes the words "league," "crummy," and "swords," with a clear warning and a gentle ending image.'
    ]


def pair_noun(leader: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and friend.type == "boy":
            return "two brothers"
        if leader.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    parent = f["parent"]
    theme = f["theme"]
    cache = f["cache"]
    swords = f["swords_cfg"]
    prop1, prop2 = f["props"]
    fix = f["fix"]
    pair = pair_noun(leader, friend, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {friend.id}, who made a little {theme.role_word} league. {parent.label_word.capitalize()} came to help when the game needed a wiser turn."
        ),
        (
            "What did the children want for their league?",
            f"They wanted their league march to look grand and brave. That wish is why {leader.id} was tempted by the swords instead of a safer prop."
        ),
        (
            f"Why did {friend.id} say no to the swords?",
            f"{friend.id} knew the swords were real and unsafe for play. {friend.pronoun().capitalize()} also foresaw that someone could get nicked if the blades were waved."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {friend.id} warned {leader.id}?",
            f"{leader.id} backed down and left the swords in {cache.label}. Because the warning was taken seriously, no one was hurt and the game could change safely."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {parent.label_word} bringing {prop1.phrase} and {prop2.phrase}. The little league marched on with safe bright things instead of crummy swords."
        ))
    else:
        qa.append((
            "What happened when the swords were waved?",
            f"One sword scraped {friend.id}'s hand and left a tiny scratch. The trouble came quickly because real sharp swords can hurt someone in a single swing."
        ))
        qa.append((
            f"How did {parent.label_word} fix the problem?",
            f"{parent.label_word.capitalize()} {fix.qa_text}. That stopped the danger at once and turned the moment from a scare into a lesson."
        ))
        if swords.rusty:
            qa.append((
                "Why did the rust make the grown-up more worried?",
                "Rust meant the swords were old, dirty, and even less fit for play. A scratch from rusty metal needs quick cleaning, so the grown-up moved fast."
            ))
        qa.append((
            "How did the story end?",
            f"It ended with {prop1.phrase} and {prop2.phrase} replacing the swords. The children could still have a grand league parade, but now the ending showed a safer kind of bravery."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["swords_cfg"].tags) | set(f["fix"].tags)
    for prop in f["props"]:
        tags |= set(prop.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("rusty", ent.rusty), ("sharp", ent.sharp), ("soft", ent.soft)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="knights",
        cache="shed",
        swords="rusty_short",
        prop1="ribbons",
        prop2="cardboard",
        fix="take_and_clean",
        leader_name="Nell",
        leader_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        trait="careful",
        leader_age=5,
        friend_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="garden",
        cache="cellar",
        swords="wall_hanger",
        prop1="spoons",
        prop2="ribbons",
        fix="lock_and_bandage",
        leader_name="Ben",
        leader_gender="boy",
        friend_name="May",
        friend_gender="girl",
        parent="father",
        trait="thoughtful",
        leader_age=6,
        friend_age=5,
        relation="friends",
    ),
    StoryParams(
        theme="moon",
        cache="barn",
        swords="rusty_short",
        prop1="cardboard",
        prop2="spoons",
        fix="take_and_clean",
        leader_name="Tess",
        leader_gender="girl",
        friend_name="Ivy",
        friend_gender="girl",
        parent="mother",
        trait="steady",
        leader_age=4,
        friend_age=6,
        relation="siblings",
    ),
]


def explain_rejection(sword: SwordSet) -> str:
    if not sword.real:
        return "(No story: those are only soft play swords, so the cautionary danger is too weak. Pick real, unsafe swords for this world.)"
    if not sword.sharp or sword.danger < 2:
        return "(No story: those swords are too blunt for a convincing warning-and-rescue story here. Pick a sharper, riskier set.)"
    return "(No story: this sword choice does not fit the danger model.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return f"(Refusing fix '{fid}': it scores too low on common sense (sense={fix.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazardous(S) :- swords(S), real(S), sharp(S), danger(S,D), D >= 2.
sensible_fix(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(T,C,S) :- theme(T), cache(C), hazardous(S).

careful_trait(T) :- trait(T), is_careful(T).
init_caution(5) :- trait(T), careful_trait(T).
init_caution(3) :- trait(T), not careful_trait(T).
friend_older :- relation(siblings), leader_age(LA), friend_age(FA), FA > LA.
bonus(3) :- friend_older.
bonus(0) :- not friend_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
back_down :- friend_older, authority(A), brag_init(BR), A > BR.

outcome(averted) :- back_down.
outcome(rescued) :- not back_down.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme in THEMES:
        lines.append(asp.fact("theme", theme))
    for cache in CACHES:
        lines.append(asp.fact("cache", cache))
    for sid, sword in SWORDS.items():
        lines.append(asp.fact("swords", sid))
        if sword.real:
            lines.append(asp.fact("real", sid))
        if sword.sharp:
            lines.append(asp.fact("sharp", sid))
        if sword.rusty:
            lines.append(asp.fact("rusty", sid))
        lines.append(asp.fact("danger", sid, sword.danger))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("brag_init", int(BRAG_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("leader_age", params.leader_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_back_down(params.relation, params.leader_age, params.friend_age, params.trait) else "rescued"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_fix = set(asp_sensible_fixes())
    p_fix = {f.id for f in sensible_fixes()}
    if c_fix == p_fix:
        print(f"OK: sensible fixes match ({sorted(c_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_fix)} python={sorted(p_fix)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() for seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nursery-rhyme cautionary tale about a league, crummy swords, and safer play."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--cache", choices=CACHES)
    ap.add_argument("--swords", choices=SWORDS)
    ap.add_argument("--prop1", choices=SAFE_PROPS)
    ap.add_argument("--prop2", choices=SAFE_PROPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.swords:
        sword = SWORDS[args.swords]
        if not hazardous(sword):
            raise StoryError(explain_rejection(sword))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.cache is None or combo[1] == args.cache)
        and (args.swords is None or combo[2] == args.swords)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, cache, swords = rng.choice(sorted(combos))
    prop_keys = sorted(SAFE_PROPS.keys())
    if args.prop1 and args.prop2 and args.prop1 == args.prop2:
        raise StoryError("(Choose two different safe props.)")
    if args.prop1 and args.prop2:
        prop1, prop2 = args.prop1, args.prop2
    elif args.prop1:
        remaining = [p for p in prop_keys if p != args.prop1]
        prop1, prop2 = args.prop1, rng.choice(remaining)
    elif args.prop2:
        remaining = [p for p in prop_keys if p != args.prop2]
        prop1, prop2 = rng.choice(remaining), args.prop2
    else:
        prop1, prop2 = rng.sample(prop_keys, 2)

    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    leader_name, leader_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([3, 4, 5, 6, 7], 2)
    leader_age, friend_age = ages[0], ages[1]

    return StoryParams(
        theme=theme,
        cache=cache,
        swords=swords,
        prop1=prop1,
        prop2=prop2,
        fix=fix,
        leader_name=leader_name,
        leader_gender=leader_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        leader_age=leader_age,
        friend_age=friend_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.cache not in CACHES:
        raise StoryError(f"(Unknown cache: {params.cache})")
    if params.swords not in SWORDS:
        raise StoryError(f"(Unknown swords choice: {params.swords})")
    if params.prop1 not in SAFE_PROPS or params.prop2 not in SAFE_PROPS:
        raise StoryError("(Unknown safe prop choice.)")
    if params.prop1 == params.prop2:
        raise StoryError("(Choose two different safe props.)")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    sword = SWORDS[params.swords]
    if not hazardous(sword):
        raise StoryError(explain_rejection(sword))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        THEMES[params.theme],
        CACHES[params.cache],
        sword,
        (SAFE_PROPS[params.prop1], SAFE_PROPS[params.prop2]),
        FIXES[params.fix],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        leader_age=params.leader_age,
        friend_age=params.friend_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, cache, swords) combos:\n")
        for theme, cache, swords in combos:
            print(f"  {theme:8} {cache:8} {swords}")
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
            header = f"### {p.leader_name} & {p.friend_name}: {p.swords} for a {p.theme} league ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
