#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py
=====================================================================

A standalone story world for funny, cautionary animal stories about reaching for
raspberries the unsafe way. A young animal wants the highest berries for a
treat, spots a wobbly thing to stand on, and is warned by a friend or sibling.
Sometimes the warning works and the risky idea is dropped. Sometimes the child
tries anyway, tumbles into raspberry mush, and learns a safer way to pick.

The world model tracks physical meters (wobble, fall, stains, scratches,
berries_lost) and emotional memes (pride, caution, fear, embarrassment, relief,
joy). Story text comes from those state changes rather than frozen templates.

Run it
------
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py --bush tall_canes --perch rolling_log
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py --perch flat_stone
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/raspberry_humor_cautionary_animal_story.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
    unstable: bool = False
    rolling: bool = False
    thorny: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
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
class AnimalRole:
    id: str
    species: str
    child_word: str
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
class Bush:
    id: str
    label: str
    phrase: str
    height: int
    thorniness: int
    flavor: str
    tags: set[str] = field(default_factory=set)

    @property
    def thorny(self) -> bool:
        return self.thorniness > 0
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
class Perch:
    id: str
    label: str
    phrase: str
    instability: int
    rolling: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def unstable(self) -> bool:
        return self.instability > 0
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
class SafeTool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    ending: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"picker", "warner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    picker = world.get("picker")
    perch = world.get("perch")
    if picker.meters["reaching"] < THRESHOLD or perch.meters["stood_on"] < THRESHOLD:
        return out
    if not perch.unstable:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobble"] += float(max(1, perch.attrs.get("instability", 1)))
    picker.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    picker = world.get("picker")
    perch = world.get("perch")
    bush = world.get("bush")
    if perch.meters["wobble"] < THRESHOLD:
        return out
    force = perch.attrs.get("instability", 0) + bush.attrs.get("thorniness", 0)
    if not perch.rolling and force < 3:
        return out
    sig = ("fall", picker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    picker.meters["fall"] += 1
    picker.meters["stained"] += 1
    picker.meters["berries_lost"] += 1
    picker.memes["embarrassment"] += 1
    if bush.attrs.get("thorniness", 0) >= 2:
        picker.meters["scratches"] += 1
    out.append("__fall__")
    return out


def _r_puddle(world: World) -> list[str]:
    out: list[str] = []
    picker = world.get("picker")
    basket = world.get("basket")
    if picker.meters["fall"] < THRESHOLD:
        return out
    sig = ("basket_squish", basket.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basket.meters["squished"] += 1
    out.append("__squish__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="fall", tag="physical", apply=_r_fall),
    Rule(name="squish", tag="physical", apply=_r_puddle),
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


def hazard_at_risk(bush: Bush, perch: Perch) -> bool:
    return bush.height >= 2 and perch.unstable


def sensible_tools() -> list[SafeTool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def severity_of(bush: Bush, perch: Perch, delay: int) -> int:
    return bush.thorniness + perch.instability + delay


def is_saved(tool: SafeTool, bush: Bush, perch: Perch, delay: int) -> bool:
    return tool.power >= severity_of(bush, perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, picker_age: int, warner_age: int, trait: str) -> bool:
    older = relation == "siblings" and warner_age > picker_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def predict_mess(world: World) -> dict:
    sim = world.copy()
    attempt_pick(sim, narrate=False)
    picker = sim.get("picker")
    return {
        "fall": picker.meters["fall"] >= THRESHOLD,
        "stained": picker.meters["stained"] >= THRESHOLD,
        "scratches": picker.meters["scratches"] >= THRESHOLD,
    }


def introduce(world: World, picker: Entity, warner: Entity, adult: Entity, role: AnimalRole) -> None:
    picker.memes["joy"] += 1
    warner.memes["joy"] += 1
    world.say(
        f"On a bright morning in the bramble meadow, {picker.id} the little {role.child_word} "
        f"and {warner.id} went out with {adult.label} to gather raspberry fruit for supper."
    )
    world.say(
        f"The bushes smelled sweet and sunny, and every ripe raspberry looked like a tiny red cap."
    )


def goal(world: World, picker: Entity, bush: Bush) -> None:
    picker.memes["pride"] += 1
    world.say(
        f"Soon the low berries were tucked into the basket, but the plumpest raspberry fruit still hung "
        f"high on {bush.phrase}. {picker.id} wanted those best ones most of all."
    )


def temptation(world: World, picker: Entity, perch: Perch) -> None:
    picker.memes["bravado"] += 1
    world.say(
        f"{picker.id}'s eyes landed on {perch.phrase}. "
        f'"I can stand on {perch.label} and reach the top!" {picker.pronoun()} said.'
    )


def warn(world: World, warner: Entity, picker: Entity, perch: Perch, bush: Bush) -> None:
    pred = predict_mess(world)
    warner.memes["caution"] += 1
    world.facts["predicted_fall"] = pred["fall"]
    if pred["fall"]:
        extra = " and tumble straight into the berry basket" if pred["stained"] else ""
        world.say(
            f'{warner.id} twitched {warner.pronoun("possessive")} whiskers. '
            f'"Please do not do that. {perch.label.capitalize()} looks wobbly, '
            f'and {picker.id} could slip{extra}. Even a good raspberry is not worth a bump."'
        )
    else:
        world.say(
            f'{warner.id} frowned. "That looks silly. Let us ask for help first."'
        )
    if bush.thorniness >= 2:
        world.say(
            f'{warner.id} added, "And those canes have sharp little thorns."'
        )


def back_down(world: World, picker: Entity, warner: Entity, adult: Entity) -> None:
    picker.memes["relief"] += 1
    warner.memes["relief"] += 1
    picker.memes["bravery"] = 0.0
    world.say(
        f'{picker.id} set one paw on {world.get("perch").label}, then looked at {warner.id} and stopped. '
        f'"All right," {picker.pronoun()} said. "I would rather keep my tail unbumped."'
    )
    world.say(
        f"They carried the basket to {adult.label}, who smiled at the wise choice."
    )


def defy(world: World, picker: Entity, warner: Entity, perch: Perch) -> None:
    picker.memes["defiance"] += 1
    older_picker = picker.attrs.get("relation") == "siblings" and picker.age > warner.age
    if older_picker:
        world.say(
            f'"I will only be one blink," {picker.id} said, sounding very sure because '
            f'{picker.pronoun()} was the older sibling. Before {warner.id} could stop {picker.pronoun("object")}, '
            f'{picker.pronoun()} padded over to {perch.phrase}.'
        )
    else:
        world.say(
            f'"I will only be one blink," {picker.id} said, and padded over to {perch.phrase}.'
        )


def attempt_pick(world: World, narrate: bool = True) -> None:
    picker = world.get("picker")
    perch = world.get("perch")
    bush = world.get("bush")
    perch.meters["stood_on"] += 1
    picker.meters["reaching"] += 1
    propagate(world, narrate=False)
    if not narrate:
        return
    if perch.meters["wobble"] >= THRESHOLD and picker.meters["fall"] < THRESHOLD:
        world.say(
            f"{picker.id} stretched up for the brightest raspberry, and {perch.label} gave a naughty little wobble."
        )
    elif picker.meters["fall"] >= THRESHOLD:
        splat = "plop-squish"
        world.say(
            f"{picker.id} stretched up for the brightest raspberry. Then {perch.label} wiggled, rolled, and {splat}! "
            f"{picker.id} tumbled nose-first into the basket."
        )
        if bush.attrs.get("thorniness", 0) >= 2:
            world.say(
                f"A few thorny twigs scratched {picker.pronoun('possessive')} sleeve on the way down."
            )
        world.say(
            f"When {picker.pronoun()} popped back up, {picker.pronoun('possessive')} nose wore a ridiculous raspberry mustache."
        )
    else:
        world.say(
            f"{picker.id} reached up carefully and nearly got the berry."
        )


def call_adult(world: World, warner: Entity, adult: Entity) -> None:
    world.say(f'"{adult.label.capitalize()}!" {warner.id} called. "We need the safe way, please!"')


def rescue(world: World, adult: Entity, picker: Entity, tool: SafeTool, bush: Bush) -> None:
    picker.meters["stained"] = 0.0
    picker.memes["relief"] += 1
    picker.memes["love"] += 1
    world.say(
        f"{adult.label.capitalize()} hurried over, checked {picker.id} from ears to toes, "
        f"and wiped the berry mash from {picker.pronoun('possessive')} face with a leaf-soft cloth."
    )
    if tool.id == "ladder":
        world.say(
            f"Then {adult.pronoun()} brought {tool.phrase}, planted it on steady ground, and held it firm beside {bush.phrase}."
        )
    elif tool.id == "hook":
        world.say(
            f"Then {adult.pronoun()} brought {tool.phrase}, so the top raspberries could be tugged down without any climbing at all."
        )
    else:
        world.say(
            f"Then {adult.pronoun()} bent low and offered {picker.id} a gentle lift, just long enough to reach one raspberry at a time."
        )
    world.say(
        f'"Raspberry fruit tastes best when paws stay on something steady," {adult.label} said. '
        f'{picker.id} gave a small, sticky nod.'
    )


def rescue_fail(world: World, adult: Entity, picker: Entity, tool: SafeTool) -> None:
    picker.memes["relief"] += 1
    picker.memes["sadness"] += 1
    world.say(
        f"{adult.label.capitalize()} hurried over and brushed the worst berry mash away, but by then the basket had tipped, "
        f"and most of the raspberry fruit was already squashed in the grass."
    )
    if tool.id == "parent_lift":
        world.say(
            f"{adult.pronoun().capitalize()} could comfort {picker.id}, but there were not many berries left to save."
        )
    else:
        world.say(
            f"{adult.pronoun().capitalize()} brought {tool.phrase}, but it was too late to save the picnic basket."
        )


def lesson(world: World, adult: Entity, picker: Entity, warner: Entity) -> None:
    picker.memes["lesson"] += 1
    warner.memes["love"] += 1
    world.say(
        f"{adult.label.capitalize()} was not cross. {adult.pronoun().capitalize()} put an arm around both little gatherers and said, "
        f'"High treats are never worth a wobbly trick. Ask for steady help first."'
    )
    world.say(
        f'{picker.id} looked at the pink smear on {picker.pronoun("possessive")} paws and gave a sheepish laugh. '
        f'"I suppose a raspberry mustache is funny only once," {picker.pronoun()} said.'
    )


def safe_ending(world: World, picker: Entity, warner: Entity, adult: Entity, tool: SafeTool) -> None:
    picker.memes["joy"] += 1
    warner.memes["joy"] += 1
    world.say(
        f"Soon the basket filled the proper way. {tool.ending}"
    )
    world.say(
        f"At the end, {picker.id} offered the very best raspberry to {warner.id} before taking one for {picker.pronoun('object')}self, "
        f"and all three went home laughing."
    )


def sadder_ending(world: World, picker: Entity, warner: Entity, adult: Entity) -> None:
    picker.memes["lesson"] += 1
    warner.memes["sadness"] += 1
    world.say(
        f"They still carried a few unbroken berries home, but there was no full tart that evening, only a small bowl of mashed raspberry sauce."
    )
    world.say(
        f"{picker.id} ate quietly and remembered the sticky tumble every time {picker.pronoun()} saw a high branch after that."
    )


def tell(
    role: AnimalRole,
    bush: Bush,
    perch: Perch,
    tool: SafeTool,
    picker_name: str = "Pip",
    warner_name: str = "Moss",
    adult_name: str = "Aunt Bramble",
    trait: str = "careful",
    delay: int = 0,
    picker_age: int = 5,
    warner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    picker = world.add(
        Entity(
            id="picker",
            kind="character",
            type=role.species,
            label=picker_name,
            role="picker",
            age=picker_age,
            attrs={"relation": relation, "display_name": picker_name},
        )
    )
    warner = world.add(
        Entity(
            id="warner",
            kind="character",
            type=role.species,
            label=warner_name,
            role="warner",
            age=warner_age,
            traits=[trait],
            attrs={"relation": relation, "display_name": warner_name},
        )
    )
    adult = world.add(
        Entity(
            id="adult",
            kind="character",
            type=role.species,
            label=adult_name,
            role="adult",
            attrs={"display_name": adult_name},
        )
    )
    bush_ent = world.add(
        Entity(
            id="bush",
            type="bush",
            label=bush.label,
            thorny=bush.thorny,
            edible=True,
            attrs={"height": bush.height, "thorniness": bush.thorniness},
        )
    )
    perch_ent = world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch.label,
            unstable=perch.unstable,
            rolling=perch.rolling,
            attrs={"instability": perch.instability},
        )
    )
    world.add(Entity(id="basket", type="basket", label="basket"))
    picker.memes["bravery"] = BRAVERY_INIT
    warner.memes["caution"] = initial_caution(trait)
    world.facts.update(
        role=role,
        bush_cfg=bush,
        perch_cfg=perch,
        tool_cfg=tool,
        delay=delay,
        relation=relation,
    )

    introduce(world, picker, warner, adult, role)
    goal(world, picker, bush)
    world.para()
    temptation(world, picker, perch)
    warn(world, warner, picker, perch, bush)

    averted = would_avert(relation, picker_age, warner_age, trait)
    if averted:
        back_down(world, picker, warner, adult)
        world.para()
        rescue(world, adult, picker, tool, bush)
        safe_ending(world, picker, warner, adult, tool)
        outcome = "averted"
        saved = True
    else:
        defy(world, picker, warner, perch)
        world.para()
        attempt_pick(world, narrate=True)
        call_adult(world, warner, adult)
        world.para()
        saved = is_saved(tool, bush, perch, delay)
        if saved:
            rescue(world, adult, picker, tool, bush)
            lesson(world, adult, picker, warner)
            world.para()
            safe_ending(world, picker, warner, adult, tool)
            outcome = "saved"
        else:
            rescue_fail(world, adult, picker, tool)
            lesson(world, adult, picker, warner)
            world.para()
            sadder_ending(world, picker, warner, adult)
            outcome = "squashed"

    world.facts.update(
        picker=picker,
        warner=warner,
        adult=adult,
        bush=bush_ent,
        perch=perch_ent,
        basket=world.get("basket"),
        tool=tool,
        outcome=outcome,
        saved=saved,
        averted=averted,
        picker_name=picker_name,
        warner_name=warner_name,
        adult_name=adult_name,
        scratched=picker.meters["scratches"] >= THRESHOLD,
        fell=picker.meters["fall"] >= THRESHOLD,
        squished=world.get("basket").meters["squished"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "squirrel": AnimalRole(
        id="squirrel",
        species="squirrel",
        child_word="squirrel",
        tags={"squirrel", "animal"},
    ),
    "rabbit": AnimalRole(
        id="rabbit",
        species="rabbit",
        child_word="rabbit",
        tags={"rabbit", "animal"},
    ),
    "raccoon": AnimalRole(
        id="raccoon",
        species="raccoon",
        child_word="raccoon",
        tags={"raccoon", "animal"},
    ),
}

BUSHES = {
    "arching_patch": Bush(
        id="arching_patch",
        label="arching raspberry patch",
        phrase="the arching raspberry patch",
        height=2,
        thorniness=1,
        flavor="sun-warm",
        tags={"raspberry", "bramble"},
    ),
    "tall_canes": Bush(
        id="tall_canes",
        label="tall raspberry canes",
        phrase="the tall raspberry canes",
        height=3,
        thorniness=2,
        flavor="dark-sweet",
        tags={"raspberry", "bramble", "thorns"},
    ),
    "low_patch": Bush(
        id="low_patch",
        label="low raspberry patch",
        phrase="the low raspberry patch",
        height=1,
        thorniness=1,
        flavor="soft-sweet",
        tags={"raspberry"},
    ),
}

PERCHES = {
    "rolling_log": Perch(
        id="rolling_log",
        label="the rolling log",
        phrase="a round fallen log",
        instability=3,
        rolling=True,
        tags={"log", "balance"},
    ),
    "upturned_pail": Perch(
        id="upturned_pail",
        label="the upturned pail",
        phrase="an upturned berry pail",
        instability=2,
        rolling=False,
        tags={"pail", "wobble"},
    ),
    "crooked_stool": Perch(
        id="crooked_stool",
        label="the crooked stool",
        phrase="a little crooked stool",
        instability=2,
        rolling=False,
        tags={"stool", "wobble"},
    ),
    "flat_stone": Perch(
        id="flat_stone",
        label="the flat stone",
        phrase="a broad flat stone",
        instability=0,
        rolling=False,
        tags={"stone"},
    ),
}

TOOLS = {
    "ladder": SafeTool(
        id="ladder",
        label="little ladder",
        phrase="a little ladder",
        power=4,
        sense=3,
        ending="With the little ladder held steady, the highest berries came down without any drama at all.",
        tags={"ladder", "steady_help"},
    ),
    "hook": SafeTool(
        id="hook",
        label="berry hook",
        phrase="a long berry hook",
        power=3,
        sense=3,
        ending="With the berry hook, even the top fruit bowed politely into the basket.",
        tags={"hook", "steady_help"},
    ),
    "parent_lift": SafeTool(
        id="parent_lift",
        label="grown-up lift",
        phrase="a grown-up's careful lift",
        power=2,
        sense=2,
        ending="One careful lift at a time was slower, but every berry reached the basket whole.",
        tags={"grownup_help", "steady_help"},
    ),
    "twig_poke": SafeTool(
        id="twig_poke",
        label="twig poke",
        phrase="a thin little twig",
        power=1,
        sense=1,
        ending="The twig was not much help at all.",
        tags={"twig"},
    ),
}

NAMES = {
    "squirrel": ["Pip", "Nettle", "Acorn", "Tansy", "Midge"],
    "rabbit": ["Poppy", "Thimble", "Moss", "Clover", "Nib"],
    "raccoon": ["Bandit", "Pebble", "Fern", "Skipper", "Dot"],
}
TRAITS = ["careful", "steady", "thoughtful", "patient", "playful", "bouncy", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id in ANIMALS:
        for bush_id, bush in BUSHES.items():
            for perch_id, perch in PERCHES.items():
                if hazard_at_risk(bush, perch):
                    combos.append((animal_id, bush_id, perch_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    bush: str
    perch: str
    tool: str
    picker_name: str
    warner_name: str
    adult_name: str
    trait: str
    delay: int = 0
    picker_age: int = 5
    warner_age: int = 7
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
    "raspberry": [
        (
            "What is a raspberry?",
            "A raspberry is a small soft fruit made of many tiny juicy bumps together. It is sweet, but it squishes very easily.",
        )
    ],
    "bramble": [
        (
            "What is a bramble patch?",
            "A bramble patch is a place where berry canes grow in a tangle. It can have sweet fruit and scratchy stems at the same time.",
        )
    ],
    "thorns": [
        (
            "Why do thorny canes need care?",
            "Thorns are sharp little points on a plant. They can scratch skin or fur if you push in too fast.",
        )
    ],
    "ladder": [
        (
            "Why is a ladder safer than standing on a wobbly thing?",
            "A ladder is made for climbing and can stand still on the ground when a grown-up steadies it. A wobbly thing can tip or roll before you are ready.",
        )
    ],
    "hook": [
        (
            "What does a berry hook do?",
            "A berry hook lets a picker pull high branches down gently. That means you can reach the fruit without climbing on something risky.",
        )
    ],
    "steady_help": [
        (
            "Why should children ask for steady help with high fruit?",
            "Steady help keeps feet safe and leaves more fruit un-squashed. Asking first is wiser than trying a tricky stunt.",
        )
    ],
    "squirrel": [
        (
            "What kind of animal is a squirrel?",
            "A squirrel is a small animal with quick paws and a busy tail. Many squirrels are very good at climbing trees.",
        )
    ],
    "rabbit": [
        (
            "What kind of animal is a rabbit?",
            "A rabbit is a soft-furred animal with long ears and strong back legs. Rabbits can hop fast and nibble plants with neat little teeth.",
        )
    ],
    "raccoon": [
        (
            "What kind of animal is a raccoon?",
            "A raccoon is a clever animal with nimble paws and a mask-like face. It often uses those paws to feel and hold things carefully.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "raspberry",
    "bramble",
    "thorns",
    "ladder",
    "hook",
    "steady_help",
    "squirrel",
    "rabbit",
    "raccoon",
]


def pair_noun(relation: str) -> str:
    if relation == "siblings":
        return "two young siblings"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    role = f["role"]
    bush = f["bush_cfg"]
    perch = f["perch_cfg"]
    tool = f["tool_cfg"]
    picker_name = f["picker_name"]
    warner_name = f["warner_name"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny cautionary animal story for a 3-to-5-year-old that includes the word "raspberry" and a child who almost climbs on {perch.label} to reach high fruit.',
            f"Tell a gentle animal story where {picker_name} wants the highest berries from {bush.label}, but listens to {warner_name} and chooses the safe way instead.",
            f"Write a story about a little {role.species} who nearly makes a silly mistake for a raspberry, then asks for steady help and ends happily.",
        ]
    if outcome == "saved":
        return [
            f'Write a humorous cautionary animal story that includes the word "raspberry" and a tumble caused by standing on {perch.label}.',
            f"Tell a story where {picker_name} ignores a warning, gets berry mash on {f['picker'].pronoun('possessive')} face, and then learns to use {tool.label}.",
            f"Write a child-friendly story about reaching too high for fruit, with a funny middle and a wiser ending.",
        ]
    return [
        f'Write a cautionary animal story with humor that includes the word "raspberry" and shows how a risky trick can spoil a picnic.',
        f"Tell a story where {picker_name} tries to reach high fruit from {bush.label}, tumbles, and loses most of the berries before the safe tool can help.",
        f"Write a gentle but sadder lesson story about how one silly choice with high fruit leads to a sticky mess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    picker = f["picker"]
    warner = f["warner"]
    adult = f["adult"]
    bush_cfg = f["bush_cfg"]
    perch_cfg = f["perch_cfg"]
    tool = f["tool"]
    picker_name = f["picker_name"]
    warner_name = f["warner_name"]
    adult_name = f["adult_name"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(relation)} named {picker_name} and {warner_name}, and {adult_name} who helps them gather fruit. They go out to pick raspberry fruit together.",
        ),
        (
            f"Why did {picker_name} want to stand on {perch_cfg.label}?",
            f"{picker_name} wanted the highest, plumpest raspberry fruit from {bush_cfg.label}. The low berries were already picked, so the tempting ones were still up high.",
        ),
        (
            f"What warning did {warner_name} give?",
            f"{warner_name} said {perch_cfg.label} looked wobbly and that high fruit was not worth a bump. The warning came from seeing that the risky perch and the thorny bush could lead to a fall.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {picker_name}'s mind?",
                f"{picker_name} stopped after looking at {warner_name} and thinking about the risk. Instead of showing off, {picker.pronoun()} chose steady help and stayed safe.",
            )
        )
        qa.append(
            (
                f"How did {adult_name} help at the end?",
                f"{adult_name} brought {tool.phrase} so the high berries could be reached the safe way. That let the basket fill without any tumble or sticky mess.",
            )
        )
    elif f["outcome"] == "saved":
        qa.append(
            (
                f"What happened when {picker_name} tried the risky idea?",
                f"{picker_name} fell into the basket and got covered in berry mash. The funny raspberry mustache showed the consequence right on {picker.pronoun('possessive')} face.",
            )
        )
        qa.append(
            (
                f"Was anyone angry with {picker_name}?",
                f"No. {adult_name} checked that {picker_name} was all right, cleaned {picker.pronoun('object')} up, and explained the safer way. The lesson came with comfort and help, not shouting.",
            )
        )
        qa.append(
            (
                f"How did they solve the problem after the fall?",
                f"They used {tool.label} to reach the high fruit safely. Once the ground was steady and the tool was right, the raspberry picking could continue without another spill.",
            )
        )
    else:
        qa.append(
            (
                f"What was lost because of the tumble?",
                f"Most of the berry basket was squashed in the grass, so the picnic treat could not be made properly. The mistake did not just make a mess; it wasted the fruit too.",
            )
        )
        qa.append(
            (
                f"What did {picker_name} learn?",
                f"{picker_name} learned that a high treat is not worth a wobbly trick. After seeing the sticky result, {picker.pronoun()} remembered to ask for steady help first.",
            )
        )
    if f["scratched"]:
        qa.append(
            (
                f"Why did the bush make the fall worse?",
                f"The bush had sharp little thorns, so the tumble included scratches as well as berry stains. That made the risky idea more than just silly; it also made it uncomfortable.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["role"].tags) | set(f["bush_cfg"].tags) | set(f["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("unstable", ent.unstable), ("rolling", ent.rolling), ("thorny", ent.thorny), ("edible", ent.edible)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="squirrel",
        bush="arching_patch",
        perch="upturned_pail",
        tool="hook",
        picker_name="Pip",
        warner_name="Moss",
        adult_name="Aunt Bramble",
        trait="careful",
        delay=0,
        picker_age=4,
        warner_age=7,
        relation="siblings",
    ),
    StoryParams(
        animal="rabbit",
        bush="tall_canes",
        perch="rolling_log",
        tool="ladder",
        picker_name="Poppy",
        warner_name="Nib",
        adult_name="Gran Thistle",
        trait="playful",
        delay=0,
        picker_age=6,
        warner_age=5,
        relation="siblings",
    ),
    StoryParams(
        animal="raccoon",
        bush="tall_canes",
        perch="crooked_stool",
        tool="parent_lift",
        picker_name="Pebble",
        warner_name="Fern",
        adult_name="Uncle Mosscoat",
        trait="thoughtful",
        delay=1,
        picker_age=6,
        warner_age=4,
        relation="friends",
    ),
    StoryParams(
        animal="rabbit",
        bush="arching_patch",
        perch="rolling_log",
        tool="hook",
        picker_name="Thimble",
        warner_name="Clover",
        adult_name="Aunt Burrow",
        trait="steady",
        delay=0,
        picker_age=5,
        warner_age=8,
        relation="siblings",
    ),
]


def explain_rejection(bush: Bush, perch: Perch) -> str:
    if bush.height < 2:
        return (
            f"(No story: {bush.label} is low enough to reach from the ground, so there is no honest reason to climb on {perch.label}. Pick a taller raspberry patch.)"
        )
    if not perch.unstable:
        return (
            f"(No story: {perch.label} is not wobbly enough to make a cautionary story here. Pick an unstable perch such as a rolling log or an upturned pail.)"
        )
    return "(No story: this combination does not create the intended hazard.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense (sense={tool.sense} < {SENSE_MIN}). "
        f"Try one of these steadier fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.picker_age, params.warner_age, params.trait):
        return "averted"
    tool = TOOLS[params.tool]
    bush = BUSHES[params.bush]
    perch = PERCHES[params.perch]
    return "saved" if is_saved(tool, bush, perch, params.delay) else "squashed"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(B,P) :- bush(B), perch(P), high(B), unstable(P).
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(A,B,P) :- animal(A), bush(B), perch(P), hazard(B,P).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
warner_older :- relation(siblings), picker_age(PA), warner_age(WA), WA > PA.
bonus(3) :- warner_older.
bonus(0) :- not warner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- warner_older, authority(A), bravery_init(BR), A > BR.

severity(Th + In + D) :- chosen_bush(B), thorniness(B,Th), chosen_perch(P), instability(P,In), delay(D).
tool_power(Pw) :- chosen_tool(T), power(T,Pw).
saved :- tool_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(saved) :- not averted, saved.
outcome(squashed) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for bush_id, bush in BUSHES.items():
        lines.append(asp.fact("bush", bush_id))
        lines.append(asp.fact("height", bush_id, bush.height))
        lines.append(asp.fact("thorniness", bush_id, bush.thorniness))
        if bush.height >= 2:
            lines.append(asp.fact("high", bush_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("instability", perch_id, perch.instability))
        if perch.unstable:
            lines.append(asp.fact("unstable", perch_id))
        if perch.rolling:
            lines.append(asp.fact("rolling", perch_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        lines.append(asp.fact("sense", tool_id, tool.sense))
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


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_bush", params.bush),
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("picker_age", params.picker_age),
            asp.fact("warner_age", params.warner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_tools = set(asp_sensible_tools())
    p_tools = {tool.id for tool in sensible_tools()}
    if c_tools == p_tools:
        print(f"OK: sensible tools match ({sorted(c_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_tools)} python={sorted(p_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny cautionary animal stories about risky raspberry picking. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--bush", choices=BUSHES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.bush and args.perch:
        bush = BUSHES[args.bush]
        perch = PERCHES[args.perch]
        if not hazard_at_risk(bush, perch):
            raise StoryError(explain_rejection(bush, perch))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.bush is None or combo[1] == args.bush)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, bush_id, perch_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(tool.id for tool in sensible_tools()))
    animal_names = list(NAMES[animal_id])
    picker_name = rng.choice(animal_names)
    warner_pool = [name for name in animal_names if name != picker_name]
    warner_name = rng.choice(warner_pool)
    adult_name = rng.choice(["Aunt Bramble", "Uncle Mosscoat", "Gran Thistle", "Old Hazel"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    picker_age, warner_age = ages[0], ages[1]
    return StoryParams(
        animal=animal_id,
        bush=bush_id,
        perch=perch_id,
        tool=tool_id,
        picker_name=picker_name,
        warner_name=warner_name,
        adult_name=adult_name,
        trait=trait,
        delay=delay,
        picker_age=picker_age,
        warner_age=warner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.bush not in BUSHES:
        raise StoryError(f"(Unknown bush: {params.bush})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.tool in TOOLS and TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    bush = BUSHES[params.bush]
    perch = PERCHES[params.perch]
    if not hazard_at_risk(bush, perch):
        raise StoryError(explain_rejection(bush, perch))

    world = tell(
        role=ANIMALS[params.animal],
        bush=bush,
        perch=perch,
        tool=TOOLS[params.tool],
        picker_name=params.picker_name,
        warner_name=params.warner_name,
        adult_name=params.adult_name,
        trait=params.trait,
        delay=params.delay,
        picker_age=params.picker_age,
        warner_age=params.warner_age,
        relation=params.relation,
    )
    story = world.render().replace("picker", params.picker_name).replace("warner", params.warner_name)
    story = story.replace("adult", params.adult_name)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, bush, perch) combos:\n")
        for animal_id, bush_id, perch_id in combos:
            print(f"  {animal_id:8} {bush_id:14} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.picker_name} and {p.warner_name}: {p.bush} / {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
