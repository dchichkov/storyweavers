#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py
==================================================================================================

A standalone fairy-tale story world about a small traveler, a misunderstood sign,
and a kindred helper in an enchanted place.

The domain is intentionally tight: a child sets out on a loving errand, notices
a helper's glance, misunderstands the clue, and briefly worsens the problem by
choosing the wrong object. Then the child looks again, understands the helper's
true meaning, uses the proper aid, and reaches the destination safely. The
opening beat foreshadows the turn by telling the old woodland rule that moonlit
kindness points the true way.

Reasonableness constraint
-------------------------
Each obstacle has a concrete practical need:

* a brook needs something to cross on
* thorn vines need something to part or cut them
* darkness needs something to light the path

The world refuses combinations where the chosen "correct aid" cannot actually
solve the obstacle. The misunderstanding branch always begins with a plausible
but wrong first guess, then turns into problem solving when the hero rereads the
helper's signal.

Run it
------
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py --obstacle brook --aid stepping_stones
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py --obstacle vines --aid lantern
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py --all
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py --qa --json
    python storyworlds/worlds/gpt-5.4/glance_kindred_foreshadowing_problem_solving_misunderstanding_fairy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "fairy_girl", "mother", "queen", "aunt", "woman"}
        male = {"boy", "fairy_boy", "father", "king", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
    shimmer: str
    path_name: str
    destination: str
    home: str
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
class Errand:
    id: str
    item: str
    phrase: str
    recipient: str
    reason: str
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
class Obstacle:
    id: str
    label: str
    problem_text: str
    trouble_text: str
    solved_text: str
    need: str
    risk: str
    foreshadow: str
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
class Aid:
    id: str
    label: str
    phrase: str
    function: str
    solve_text: str
    wrong_for: set[str] = field(default_factory=set)
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
class HelperKind:
    id: str
    label: str
    phrase: str
    motion: str
    voice: str
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


def _r_stuck(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.facts["obstacle"]
    if hero.meters["wrong_attempt"] < THRESHOLD:
        return []
    sig = ("stuck", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["progress"] = 0.0
    hero.meters["stuck"] += 1
    hero.memes["worry"] += 1
    return ["__stuck__"]


def _r_solve(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.facts["obstacle"]
    aid = world.facts["aid"]
    if hero.meters["used_correct_aid"] < THRESHOLD:
        return []
    sig = ("solve", obstacle.id, aid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["progress"] += 2
    hero.meters["stuck"] = 0.0
    hero.meters["crossed"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="solve", tag="physical", apply=_r_solve),
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


def aid_solves(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.need == aid.function


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for eid in ERRANDS:
            for oid, obstacle in OBSTACLES.items():
                for aid_id, aid in AIDS.items():
                    if aid_solves(obstacle, aid):
                        combos.append((sid, eid, oid, aid_id))
    return combos


def wrong_choices_for(obstacle: Obstacle) -> list[Aid]:
    return [aid for aid in AIDS.values() if not aid_solves(obstacle, aid)]


def explain_rejection(obstacle: Obstacle, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} cannot solve {obstacle.label}. "
        f"This obstacle needs something that can {obstacle.need.replace('_', ' ')}, "
        f"so choose one of: {', '.join(sorted(a.id for a in AIDS.values() if aid_solves(obstacle, a)))}.)"
    )


def predict_wrong_attempt(world: World, wrong_aid: Aid) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["wrong_attempt"] += 1
    sim.facts["wrong_aid"] = wrong_aid
    propagate(sim, narrate=False)
    return {
        "stuck": hero.meters["stuck"] >= THRESHOLD,
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, errand: Errand) -> None:
    hero.memes["love"] += 1
    world.say(
        f"In {world.setting.place}, where {world.setting.shimmer}, there lived a little {hero.type.replace('_', ' ')} named {hero.id}. "
        f"{hero.id} was carrying {errand.phrase} to {errand.recipient}, because {errand.reason}."
    )
    world.say(
        f"The old ones in {world.setting.home} always said that in moon-bright places, a kindred heart often points the right road before a mouth can speak."
    )


def set_out(world: World, hero: Entity, helper: Entity, obstacle: Obstacle) -> None:
    hero.meters["progress"] += 1
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"So {hero.id} set out along {world.setting.path_name}. Before long, {hero.pronoun()} met {helper.label}, a kindred little traveler who moved through the leaves as softly as a song."
    )
    world.say(
        f"{helper.label.capitalize()} gave one quick glance toward the path ahead, where {obstacle.foreshadow}."
    )


def warn_without_words(world: World, helper: Entity, obstacle: Obstacle, aid: Aid) -> None:
    world.say(
        f"{helper.label.capitalize()} {helper.attrs['motion']}, then looked from the trouble to {aid.phrase}, as if trying to say, without words, what would help."
    )


def misunderstand(world: World, hero: Entity, wrong_aid: Aid, obstacle: Obstacle) -> None:
    hero.memes["confidence"] += 1
    world.say(
        f"But {hero.id} misunderstood the glance. {hero.pronoun().capitalize()} thought {helper_name(world)} meant {wrong_aid.phrase}, so {hero.pronoun()} hurried toward it instead."
    )
    world.say(
        obstacle.trouble_text.format(hero=hero.id, wrong_aid=wrong_aid.phrase)
    )


def helper_name(world: World) -> str:
    return world.get("helper").label


def wrong_attempt(world: World, hero: Entity, wrong_aid: Aid) -> None:
    hero.meters["wrong_attempt"] += 1
    world.facts["wrong_aid"] = wrong_aid
    propagate(world, narrate=False)


def realize(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, aid: Aid, wrong_aid: Aid) -> None:
    pred = predict_wrong_attempt(world, wrong_aid)
    world.facts["predicted_stuck"] = pred["stuck"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"For a moment, {hero.id} stood still. Then {hero.pronoun()} took another glance at {helper.label}'s patient face and saw the mistake."
    )
    world.say(
        f"{helper.label.capitalize()} had not meant {wrong_aid.phrase} at all. {helper.pronoun().capitalize()} had been showing {hero.pronoun('object')} {aid.phrase}, because {obstacle.problem_text.lower()}"
    )


def solve(world: World, hero: Entity, aid: Aid, obstacle: Obstacle) -> None:
    hero.meters["used_correct_aid"] += 1
    propagate(world, narrate=False)
    world.say(
        aid.solve_text.format(hero=hero.id, place=world.setting.place, obstacle=obstacle.label)
    )
    world.say(
        obstacle.solved_text.format(hero=hero.id, aid=aid.label)
    )


def arrive(world: World, hero: Entity, errand: Errand, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Soon {hero.id} reached {world.setting.destination} and gave {errand.item} to {errand.recipient}. The gift was small, but the kindness inside it felt as bright as a crown."
    )
    world.say(
        f"Before {helper.label} slipped back into the leaves, {hero.id} thanked {helper.pronoun('object')} and promised never again to guess too quickly when a kindred friend was trying to help."
    )


def ending_image(world: World, hero: Entity, helper: Entity, aid: Aid) -> None:
    world.say(
        f"After that night, whenever moonlight silvered the path, {hero.id} remembered the careful glance, the true meaning, and {aid.phrase}. And the forest seemed friendlier, as if it had made room for one wiser heart."
    )


def tell(
    setting: Setting,
    errand: Errand,
    obstacle: Obstacle,
    aid: Aid,
    wrong_aid: Aid,
    helper_kind: HelperKind,
    hero_name: str = "Lina",
    hero_type: str = "fairy_girl",
    parent_name: str = "Grandam Willow",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["gentle", "hasty"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="animal",
        label=helper_kind.label,
        role="helper",
        attrs={"motion": helper_kind.motion, "voice": helper_kind.voice},
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type="elder",
        label=parent_name,
        role="recipient",
    ))

    hero.meters["progress"] = 0.0
    hero.meters["wrong_attempt"] = 0.0
    hero.meters["used_correct_aid"] = 0.0
    hero.meters["stuck"] = 0.0
    hero.meters["crossed"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["confidence"] = 0.0
    hero.memes["wisdom"] = 0.0
    helper.memes["care"] = 0.0
    helper.memes["joy"] = 0.0

    world.facts.update(
        setting=setting,
        errand=errand,
        obstacle=obstacle,
        aid=aid,
        wrong_aid=wrong_aid,
        helper_kind=helper_kind,
        hero=hero,
        helper=helper,
        recipient=recipient,
    )

    introduce(world, hero, errand)
    set_out(world, hero, helper, obstacle)

    world.para()
    warn_without_words(world, helper, obstacle, aid)
    misunderstand(world, hero, wrong_aid, obstacle)
    wrong_attempt(world, hero, wrong_aid)

    world.para()
    realize(world, hero, helper, obstacle, aid, wrong_aid)
    solve(world, hero, aid, obstacle)

    world.para()
    arrive(world, hero, errand, helper)
    ending_image(world, hero, helper, aid)

    world.facts.update(
        misunderstanding=hero.meters["wrong_attempt"] >= THRESHOLD,
        solved=hero.meters["crossed"] >= THRESHOLD,
        delivered=hero.memes["joy"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonmeadow": Setting(
        id="moonmeadow",
        place="the Moonmeadow",
        shimmer="the dew shone like tiny lamps on every blade of grass",
        path_name="the white clover path",
        destination="the elder's willow door",
        home="the reed-ring cottages",
        tags={"moon", "meadow"},
    ),
    "fern_hollow": Setting(
        id="fern_hollow",
        place="Fern Hollow",
        shimmer="fern-fronds held silver drops and whispered whenever the wind passed",
        path_name="the fern-lantern trail",
        destination="the old hazel house",
        home="the mossy burrows",
        tags={"fern", "forest"},
    ),
    "willowmere": Setting(
        id="willowmere",
        place="Willowmere",
        shimmer="the pond edges glimmered as if the stars had bent down to drink",
        path_name="the willow-root walk",
        destination="the queen's little stone gate",
        home="the lily-bank homes",
        tags={"willow", "pond"},
    ),
}

ERRANDS = {
    "dew_cake": Errand(
        id="dew_cake",
        item="a round dew-cake",
        phrase="a round dew-cake wrapped in a dock leaf",
        recipient="Grandam Willow",
        reason="the old grandmother had a cough and loved a sweet bite before bed",
        tags={"gift", "cake"},
    ),
    "acorn_note": Errand(
        id="acorn_note",
        item="an acorn-shell note",
        phrase="an acorn-shell note tied with blue thread",
        recipient="Aunt Briar",
        reason="the note carried news that the spring fair would open at dawn",
        tags={"message", "letter"},
    ),
    "honey_drop": Errand(
        id="honey_drop",
        item="a tiny jar of honey-drop syrup",
        phrase="a tiny jar of honey-drop syrup tucked in a satchel of leaves",
        recipient="the Willow Queen",
        reason="the queen had sent kindness all winter and was to be thanked",
        tags={"gift", "honey"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="the brook",
        problem_text="the brook was too wide and cold to step through safely",
        trouble_text="Yet the shining water only soaked {hero}'s slippers and sent little cold rings around the stones. The bundle stayed dry, but the way did not open, and {hero} could not cross.",
        solved_text="With {aid}, {hero} crossed the brook neatly, one sure step after another, and not even a hem was lost to the water.",
        need="cross",
        risk="cold water tugging at careless feet",
        foreshadow="a narrow brook was talking over the stones",
        tags={"water", "crossing"},
    ),
    "vines": Obstacle(
        id="vines",
        label="the thorn vines",
        problem_text="the thorn vines had knitted themselves across the path",
        trouble_text="But the dark tangle did not move aside for {wrong_aid}. It only caught at {hero}'s sleeve and held the path shut.",
        solved_text="Soon the thorn vines parted, and a clear little doorway opened in the green wall before {hero}.",
        need="part",
        risk="thorns snagging cloth and skin",
        foreshadow="thorn vines had woven a gate across the path",
        tags={"thorns", "path"},
    ),
    "darkness": Obstacle(
        id="darkness",
        label="the dark path",
        problem_text="the dark path hid its roots and holes from unwary feet",
        trouble_text="But {wrong_aid} could not show what lay ahead. The shadows stayed thick, and {hero} dared not go farther for fear of stumbling.",
        solved_text="At once the dark path grew honest, and roots and holes stepped out of hiding before {hero}.",
        need="light",
        risk="tripping where the path cannot be seen",
        foreshadow="the path bent under a patch of deep shade",
        tags={"night", "light"},
    ),
}

AIDS = {
    "stepping_stones": Aid(
        id="stepping_stones",
        label="stepping stones",
        phrase="the round stepping stones in the water",
        function="cross",
        solve_text="{hero} placed careful feet on the round stepping stones in a bright little line. The water whispered below, but it could not catch {hero}.",
        wrong_for={"vines", "darkness"},
        tags={"stones", "crossing"},
    ),
    "silver_shears": Aid(
        id="silver_shears",
        label="silver shears",
        phrase="the silver shears hanging from a hazel branch",
        function="part",
        solve_text="{hero} reached for the silver shears and snipped gently where the thorn vines crossed. The sharp little tool worked like a promise kept.",
        wrong_for={"brook", "darkness"},
        tags={"shears", "tool"},
    ),
    "glow_lantern": Aid(
        id="glow_lantern",
        label="a glow-lantern",
        phrase="the glow-lantern blooming under a toadstool",
        function="light",
        solve_text="{hero} lifted the glow-lantern, and soft gold light spilled over the ground. Every root and pebble showed itself at once.",
        wrong_for={"brook", "vines"},
        tags={"lantern", "light"},
    ),
}

HELPERS = {
    "field_mouse": HelperKind(
        id="field_mouse",
        label="a field mouse",
        phrase="a field mouse with seed-bright eyes",
        motion="twitched one whisker",
        voice="a tiny meadow voice",
        tags={"mouse"},
    ),
    "moth": HelperKind(
        id="moth",
        label="a pale moth",
        phrase="a pale moth with dust-soft wings",
        motion="circled once in the air",
        voice="no voice at all, only wing-silence",
        tags={"moth"},
    ),
    "wren": HelperKind(
        id="wren",
        label="a brown wren",
        phrase="a brown wren with a bright bead eye",
        motion="dipped its head",
        voice="a neat bird voice",
        tags={"bird"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tansy", "Elowen", "Poppy", "Nella", "Wrenna", "Ivy"]
BOY_NAMES = ["Rowan", "Alder", "Bram", "Pip", "Nico", "Fen", "Milo", "Ash"]


@dataclass
class StoryParams:
    setting: str
    errand: str
    obstacle: str
    aid: str
    helper: str
    hero_name: str
    hero_type: str
    elder_name: str
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
    "moon": [(
        "Why can moonlight help someone walking at night?",
        "Moonlight is sunlight bouncing off the moon. Even soft moonlight can make edges and paths easier to see."
    )],
    "water": [(
        "Why is it risky to step into a cold brook at night?",
        "Cold moving water can make your feet slip and numb. When you cannot see well, it is easier to lose your balance."
    )],
    "thorns": [(
        "Why are thorn vines hard to push through?",
        "Thorn vines catch on sleeves and skin with their sharp points. They can hold a path closed unless you part them carefully."
    )],
    "night": [(
        "Why does a dark path feel harder to walk on?",
        "In darkness, roots, stones, and holes are harder to notice. That makes tripping more likely."
    )],
    "stones": [(
        "What are stepping stones for?",
        "Stepping stones give your feet small dry places to land. They help you cross water without wading through it."
    )],
    "shears": [(
        "What do shears do?",
        "Shears are a cutting tool with two blades. They can trim or part plants when used carefully."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern gives light in dark places. Light helps people notice where it is safe to step."
    )],
    "message": [(
        "Why is it good to carry a note carefully?",
        "A note can bring important news from one person to another. If you carry it carefully, the message can still be read."
    )],
    "gift": [(
        "Why do people bring small gifts to others?",
        "A small gift can show love, thanks, or care. The size is not the important part; the kindness is."
    )],
}
KNOWLEDGE_ORDER = ["moon", "water", "thorns", "night", "stones", "shears", "lantern", "message", "gift"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    helper = f["helper"]
    errand = f["errand"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "glance" and "kindred". The child should misunderstand a helper\'s clue and then solve the problem.',
        f"Tell a gentle enchanted story where {hero.id} carries {errand.item}, mistakes {helper.label}'s glance, and then uses {aid.label} to get past {obstacle.label}.",
        f"Write a fairy-tale story with foreshadowing, a misunderstanding, and problem solving, ending with the errand safely finished."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    errand = f["errand"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    wrong_aid = f["wrong_aid"]
    recipient = f["recipient"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little fairy traveler, and {helper.label}, a kindred helper in the woods. {hero.id} was trying to bring {errand.item} to {recipient.label_word}."
        ),
        (
            f"What was {hero.id} trying to do?",
            f"{hero.id} was carrying {errand.phrase} to {errand.recipient}. The errand mattered because {errand.reason}."
        ),
        (
            f"What was the problem on the path?",
            f"The problem was {obstacle.label}. {obstacle.problem_text.capitalize()}, so the errand could not continue until {hero.id} found the right way past it."
        ),
        (
            f"What did {hero.id} misunderstand?",
            f"{hero.id} misunderstood {helper.label}'s glance and chose {wrong_aid.phrase} first. That was a mistake because {wrong_aid.label} could not solve {obstacle.label}."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} looked again and understood that {helper.label} meant {aid.phrase}. Then {hero.pronoun()} used it and the path opened safely."
        ),
        (
            "How did the ending show that something had changed?",
            f"{hero.id} finished the errand and also became wiser. At the end, {hero.pronoun()} remembered not to guess too quickly when a kindred friend was trying to help."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["setting"].tags) | set(f["errand"].tags) | set(f["obstacle"].tags) | set(f["aid"].tags)
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonmeadow",
        errand="dew_cake",
        obstacle="brook",
        aid="stepping_stones",
        helper="field_mouse",
        hero_name="Lina",
        hero_type="fairy_girl",
        elder_name="Grandam Willow",
    ),
    StoryParams(
        setting="fern_hollow",
        errand="acorn_note",
        obstacle="vines",
        aid="silver_shears",
        helper="wren",
        hero_name="Rowan",
        hero_type="fairy_boy",
        elder_name="Aunt Briar",
    ),
    StoryParams(
        setting="willowmere",
        errand="honey_drop",
        obstacle="darkness",
        aid="glow_lantern",
        helper="moth",
        hero_name="Mira",
        hero_type="fairy_girl",
        elder_name="the Willow Queen",
    ),
]


ASP_RULES = r"""
valid(S,E,O,A) :- setting(S), errand(E), obstacle(O), aid(A), need(O,N), function(A,N).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid in ERRANDS:
        lines.append(asp.fact("errand", eid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("need", oid, obstacle.need))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("function", aid_id, aid.function))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a misunderstood glance, a kindred helper, and a solved path problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-type", choices=["fairy_girl", "fairy_boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid:
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not aid_solves(obstacle, aid):
            raise StoryError(explain_rejection(obstacle, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.errand is None or combo[1] == args.errand)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, errand_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["fairy_girl", "fairy_boy"])
    hero_name = rng.choice(GIRL_NAMES if hero_type == "fairy_girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    elder_name = args.elder_name or ERRANDS[errand_id].recipient
    return StoryParams(
        setting=setting_id,
        errand=errand_id,
        obstacle=obstacle_id,
        aid=aid_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.errand not in ERRANDS:
        raise StoryError(f"Unknown errand: {params.errand}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.aid not in AIDS:
        raise StoryError(f"Unknown aid: {params.aid}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    setting = SETTINGS[params.setting]
    errand = ERRANDS[params.errand]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    helper = HELPERS[params.helper]
    if not aid_solves(obstacle, aid):
        raise StoryError(explain_rejection(obstacle, aid))

    wrong_pool = wrong_choices_for(obstacle)
    if not wrong_pool:
        raise StoryError("(No plausible misunderstanding aid exists for this obstacle.)")
    wrong_aid = sorted(wrong_pool, key=lambda a: a.id)[0]

    world = tell(
        setting=setting,
        errand=errand,
        obstacle=obstacle,
        aid=aid,
        wrong_aid=wrong_aid,
        helper_kind=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        parent_name=params.elder_name,
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
        print(f"{len(combos)} valid (setting, errand, obstacle, aid) combos:\n")
        for setting, errand, obstacle, aid in combos:
            print(f"  {setting:11} {errand:10} {obstacle:10} {aid}")
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
            header = f"### {p.hero_name}: {p.obstacle} with {p.aid} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
