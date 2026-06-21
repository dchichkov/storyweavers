#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py
==============================================================

A standalone storyworld for a small animal fable domain: one animal sees another
in trouble, feels a pitiful tug of concern, chooses whether to help, and learns
that kindness returns in a later turn.

The world is deliberately narrow and state-driven:
- a small animal has a problem at a place,
- a nearby witness may ignore it or help with suitable action,
- the helped animal later returns a favor when a second problem appears,
- the ending image proves the moral value changed the day.

The reasonableness gate prefers pairings where the helper can physically perform
the rescue and where the later returned favor is plausible for the second animal.

Run it
------
    python storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py
    python storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py --trace --seed 12
    python storyworlds/worlds/gpt-5.4/pitiful_moral_value_animal_story.py --verify
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
KINDNESS_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    species: str = ""
    size: str = ""
    can_swim: bool = False
    can_fly: bool = False
    can_dig: bool = False
    carrying: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class AnimalKind:
    id: str
    noun: str
    color: str
    size: str
    move: str
    home: str
    sound: str
    ability: str
    can_swim: bool = False
    can_fly: bool = False
    can_dig: bool = False
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
class Trouble:
    id: str
    label: str
    place: str
    image: str
    need: str
    method_need: str
    meter: str
    severity: int
    fear_text: str
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
class HelpAction:
    id: str
    label: str
    sense: int
    power: int
    needs: set[str]
    text: str
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
class ReturnNeed:
    id: str
    label: str
    place: str
    problem_text: str
    need: str
    danger_text: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal_b")
    helper = world.get("animal_a")
    if animal.meters["stuck"] >= THRESHOLD and ("distress", animal.id) not in world.fired:
        world.fired.add(("distress", animal.id))
        animal.memes["fear"] += 1
        helper.memes["concern"] += 1
        out.append("__distress__")
    if animal.meters["wet"] >= THRESHOLD and ("distress", animal.id, "wet") not in world.fired:
        world.fired.add(("distress", animal.id, "wet"))
        animal.memes["fear"] += 1
        helper.memes["concern"] += 1
        out.append("__distress__")
    if animal.meters["trapped"] >= THRESHOLD and ("distress", animal.id, "trapped") not in world.fired:
        world.fired.add(("distress", animal.id, "trapped"))
        animal.memes["fear"] += 1
        helper.memes["concern"] += 1
        out.append("__distress__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("animal_a")
    animal = world.get("animal_b")
    if animal.meters["safe"] >= THRESHOLD and ("gratitude", animal.id) not in world.fired:
        world.fired.add(("gratitude", animal.id))
        animal.memes["gratitude"] += 1
        helper.memes["kindness"] += 1
        out.append("__gratitude__")
    return out


CAUSAL_RULES = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="kindness", tag="moral", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def has_ability(animal: AnimalKind, need: str) -> bool:
    return (
        (need == "swim" and animal.can_swim)
        or (need == "fly" and animal.can_fly)
        or (need == "dig" and animal.can_dig)
    )


def action_possible(animal: AnimalKind, action: HelpAction) -> bool:
    return all(has_ability(animal, need) for need in action.needs)


def help_works(animal: AnimalKind, trouble: Trouble, action: HelpAction) -> bool:
    return action_possible(animal, action) and trouble.method_need in action.needs and action.power >= trouble.severity


def return_possible(animal: AnimalKind, need: ReturnNeed) -> bool:
    return has_ability(animal, need.need)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for helper_id, helper in ANIMALS.items():
        for other_id, other in ANIMALS.items():
            if helper_id == other_id:
                continue
            for trouble_id, trouble in TROUBLES.items():
                for return_id, ret in RETURN_NEEDS.items():
                    if help_works(helper, trouble, best_action_for(helper, trouble)) and return_possible(other, ret):
                        combos.append((helper_id, other_id, trouble_id, return_id))
    return combos


def sensible_actions_for(helper: AnimalKind, trouble: Trouble) -> list[HelpAction]:
    return [
        action for action in ACTIONS.values()
        if action.sense >= KINDNESS_MIN and help_works(helper, trouble, action)
    ]


def best_action_for(helper: AnimalKind, trouble: Trouble) -> HelpAction:
    actions = sensible_actions_for(helper, trouble)
    if not actions:
        raise StoryError(explain_combo(helper, trouble))
    return max(actions, key=lambda a: (a.sense, a.power, a.id))


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, helper: Entity, other: Entity) -> None:
    meadow = world.get("meadow")
    world.say(
        f"In {meadow.label}, a {helper.attrs['color']} {helper.species} named {helper.id} liked to move {helper.attrs['move']} and listen to the morning sounds."
    )
    world.say(
        f"Not far away lived {other.id}, a {other.attrs['color']} {other.species} whose home was {other.attrs['home']}."
    )


def set_friendliness(world: World, helper: Entity, other: Entity) -> None:
    helper.memes["calm"] += 1
    other.memes["trust"] += 1
    world.say(
        f"The two animals were not best friends yet, but they nodded to each other whenever they met."
    )


def trouble_begins(world: World, other: Entity, trouble: Trouble) -> None:
    world.say(
        f"One day, {other.id} went to {trouble.place}. There {other.pronoun()} met trouble: {trouble.image}."
    )
    if trouble.meter == "stuck":
        other.meters["stuck"] += 1
    elif trouble.meter == "wet":
        other.meters["wet"] += 1
    elif trouble.meter == "trapped":
        other.meters["trapped"] += 1
    propagate(world, narrate=False)
    world.say(trouble.fear_text)


def notice(world: World, helper: Entity, other: Entity) -> None:
    helper.memes["pity"] += 1
    world.say(
        f"{helper.id} heard the sound and came closer. The sight was pitiful, and {helper.pronoun()} felt a soft pull of concern for {other.id}."
    )


def choose_help(world: World, helper: Entity, trouble: Trouble, action: HelpAction) -> None:
    helper.memes["decision_help"] += 1
    world.say(
        f'"Do not be afraid," said {helper.id}. "{action.label.capitalize()}."'
    )
    world.facts["chosen_action"] = action.id


def perform_help(world: World, helper: Entity, other: Entity, trouble: Trouble, action: HelpAction) -> None:
    if not help_works(ANIMALS[helper.species], trouble, action):
        raise StoryError("The chosen help does not fit the animal or the trouble.")
    other.meters["stuck"] = 0.0
    other.meters["wet"] = 0.0
    other.meters["trapped"] = 0.0
    other.meters["safe"] += 1
    helper.meters["effort"] += 1
    propagate(world, narrate=False)
    world.say(action.text.format(helper=helper.id, other=other.id, place=trouble.place))
    world.say(
        f"Soon {other.id} was safe again and could breathe without shaking."
    )


def thank_and_promise(world: World, other: Entity, helper: Entity) -> None:
    other.memes["gratitude_spoken"] += 1
    world.say(
        f'"Thank you," said {other.id}. "I will remember your kindness."'
    )
    helper.memes["warmth"] += 1


def second_need(world: World, helper: Entity, ret: ReturnNeed) -> None:
    helper.meters["hungry"] = 0.0
    helper.meters["tired"] = 0.0
    helper.meters["alone"] = 0.0
    if ret.id == "berry_patch":
        helper.meters["hungry"] += 1
    elif ret.id == "storm_nest":
        helper.meters["tired"] += 1
    elif ret.id == "lost_seed":
        helper.meters["alone"] += 1
    world.say(
        f"Later that afternoon, {helper.id} had a problem too. {ret.problem_text}"
    )
    world.say(ret.danger_text)


def return_kindness(world: World, other: Entity, helper: Entity, ret: ReturnNeed) -> None:
    if not return_possible(ANIMALS[other.species], ret):
        raise StoryError("The helped animal cannot reasonably return this favor.")
    other.memes["kind_return"] += 1
    helper.memes["gratitude"] += 1
    helper.meters["hungry"] = 0.0
    helper.meters["tired"] = 0.0
    helper.meters["alone"] = 0.0
    world.say(
        f"{other.id} remembered the morning and hurried over. {ret.solved_text.format(helper=helper.id, other=other.id)}"
    )


def moral_close(world: World, helper: Entity, other: Entity, ret: ReturnNeed) -> None:
    helper.memes["lesson"] += 1
    other.memes["lesson"] += 1
    world.say(
        f"By sunset, the two animals sat together near {ret.place}, no longer strangers."
    )
    world.say(
        "They learned that a kind heart notices suffering, and help given with care often comes back when it is needed most."
    )


# ---------------------------------------------------------------------------
# Tell
# ---------------------------------------------------------------------------
def tell(
    helper_cfg: AnimalKind,
    other_cfg: AnimalKind,
    trouble: Trouble,
    return_need: ReturnNeed,
    helper_name: str,
    other_name: str,
    action: HelpAction,
) -> World:
    world = World()
    world.add(Entity(id="meadow", kind="place", type="place", label="the green meadow"))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="animal",
        label=helper_cfg.noun,
        role="helper",
        species=helper_cfg.id,
        size=helper_cfg.size,
        can_swim=helper_cfg.can_swim,
        can_fly=helper_cfg.can_fly,
        can_dig=helper_cfg.can_dig,
        attrs={
            "color": helper_cfg.color,
            "move": helper_cfg.move,
            "home": helper_cfg.home,
            "sound": helper_cfg.sound,
            "ability": helper_cfg.ability,
        },
    ))
    other = world.add(Entity(
        id=other_name,
        kind="character",
        type="animal",
        label=other_cfg.noun,
        role="helped",
        species=other_cfg.id,
        size=other_cfg.size,
        can_swim=other_cfg.can_swim,
        can_fly=other_cfg.can_fly,
        can_dig=other_cfg.can_dig,
        attrs={
            "color": other_cfg.color,
            "move": other_cfg.move,
            "home": other_cfg.home,
            "sound": other_cfg.sound,
            "ability": other_cfg.ability,
        },
    ))

    world.facts.update(
        helper=helper,
        other=other,
        helper_cfg=helper_cfg,
        other_cfg=other_cfg,
        trouble=trouble,
        return_need=return_need,
        action=action,
        outcome="help_returned",
    )

    introduce(world, helper, other)
    set_friendliness(world, helper, other)

    world.para()
    trouble_begins(world, other, trouble)
    notice(world, helper, other)
    choose_help(world, helper, trouble, action)
    perform_help(world, helper, other, trouble, action)
    thank_and_promise(world, other, helper)

    world.para()
    second_need(world, helper, return_need)
    return_kindness(world, other, helper, return_need)
    moral_close(world, helper, other, return_need)

    world.facts.update(
        rescued=other.meters["safe"] >= THRESHOLD,
        returned=other.memes["kind_return"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "duck": AnimalKind(
        id="duck",
        noun="duck",
        color="yellow-brown",
        size="small",
        move="with little waddling steps",
        home="by the pond reeds",
        sound="quack",
        ability="swim",
        can_swim=True,
        tags={"pond", "kindness", "swim"},
    ),
    "swallow": AnimalKind(
        id="swallow",
        noun="swallow",
        color="blue-black",
        size="small",
        move="in quick arcs through the air",
        home="under the old barn roof",
        sound="chirp",
        ability="fly",
        can_fly=True,
        tags={"sky", "kindness", "fly"},
    ),
    "mole": AnimalKind(
        id="mole",
        noun="mole",
        color="velvet-brown",
        size="small",
        move="through the grass in soft bumps",
        home="under a warm hill of soil",
        sound="sniff",
        ability="dig",
        can_dig=True,
        tags={"earth", "kindness", "dig"},
    ),
}

TROUBLES = {
    "pond_drift": Trouble(
        id="pond_drift",
        label="drifting on the pond",
        place="the edge of the pond",
        image="a patch of water weeds wrapping around the little feet of the frightened animal",
        need="danger",
        method_need="swim",
        meter="stuck",
        severity=2,
        fear_text="The poor creature kicked and twisted, but the weeds only held tighter.",
        tags={"pond", "rescue"},
    ),
    "thorn_bush": Trouble(
        id="thorn_bush",
        label="caught in thorns",
        place="the blackberry hedge",
        image="sharp twigs hooking into fur and feathers",
        need="danger",
        method_need="fly",
        meter="trapped",
        severity=2,
        fear_text="Each tiny pull made the bush shake, and the trapped animal gave a frightened cry.",
        tags={"hedge", "rescue"},
    ),
    "buried_tunnel": Trouble(
        id="buried_tunnel",
        label="buried tunnel",
        place="the muddy hill",
        image="a small den entrance packed shut by fallen earth",
        need="danger",
        method_need="dig",
        meter="trapped",
        severity=2,
        fear_text="Dust puffed out from the blocked tunnel, and inside came a scared scratching sound.",
        tags={"hill", "rescue"},
    ),
}

ACTIONS = {
    "swim_and_pull": HelpAction(
        id="swim_and_pull",
        label="I will swim out and pull the weeds loose",
        sense=3,
        power=2,
        needs={"swim"},
        text="{helper} slipped into the water, paddled around the weeds, and tugged them free one by one for {other}.",
        qa_text="swam out and pulled the weeds loose",
        tags={"swim", "rescue"},
    ),
    "fly_and_lift": HelpAction(
        id="fly_and_lift",
        label="I will flutter above you and lift the branch away",
        sense=3,
        power=2,
        needs={"fly"},
        text="{helper} beat through the air above the tangle and lifted the springy branch just long enough for {other} to wriggle free.",
        qa_text="flew above and lifted the branch away",
        tags={"fly", "rescue"},
    ),
    "dig_open": HelpAction(
        id="dig_open",
        label="I will dig the earth away",
        sense=3,
        power=2,
        needs={"dig"},
        text="{helper} pushed dirt aside with quick strong paws until fresh air reached {other} and the blocked opening was wide again.",
        qa_text="dug the earth away",
        tags={"dig", "rescue"},
    ),
}

RETURN_NEEDS = {
    "berry_patch": ReturnNeed(
        id="berry_patch",
        label="find berries",
        place="the berry patch",
        problem_text="{helper} could not reach the sweetest berries hanging high above the brambles.",
        need="fly",
        danger_text="The fruit was there, but the branches were too high and too prickly for a safe climb.",
        solved_text="{other} flew up, pecked the ripe berries loose, and dropped them gently where {helper} could eat.",
        tags={"berries", "friendship"},
    ),
    "storm_nest": ReturnNeed(
        id="storm_nest",
        label="find shelter",
        place="the willow roots",
        problem_text="dark clouds rolled in, and {helper} had no dry place ready before the rain came.",
        need="dig",
        danger_text="The wind bent the grass low, and cold drops began to fall.",
        solved_text="{other} scratched and dug a snug hollow under the roots, and soon {helper} was tucked inside out of the rain.",
        tags={"storm", "shelter"},
    ),
    "lost_seed": ReturnNeed(
        id="lost_seed",
        label="cross water",
        place="the shallow stream",
        problem_text="{helper} found a shining seed on the far bank but could not cross the chilly stream to fetch it.",
        need="swim",
        danger_text="The water moved too fast for hopping stones, and the current looked unfriendly.",
        solved_text="{other} swam across, nudged the shining seed onto a flat leaf, and brought it back across the water.",
        tags={"stream", "help"},
    ),
}

HELPER_NAMES = ["Pip", "Moss", "Sunny", "Pebble", "Tumble", "Nip"]
OTHER_NAMES = ["Reed", "Fern", "Thistle", "Wren", "Poppy", "Dew"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    helper: str
    other: str
    trouble: str
    return_need: str
    helper_name: str
    other_name: str
    action: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "swim": [(
        "Why are ducks good at swimming?",
        "Ducks have bodies and feet that help them move through water easily. That is why they can paddle where many land animals would struggle."
    )],
    "fly": [(
        "Why can some birds help from above?",
        "A bird that can fly can reach high branches or look down on a problem from the air. Flying lets it help in places that are hard to reach from the ground."
    )],
    "dig": [(
        "Why is a mole good at digging?",
        "A mole has strong paws for pushing through earth. That makes it very good at opening soil or making a safe little tunnel."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to care when someone else is hurting or needs help. A kind action can make another creature feel safe and less alone."
    )],
    "friendship": [(
        "How can helping make friendship grow?",
        "When one animal helps another, trust can begin to grow between them. Shared kindness often turns strangers into friends."
    )],
    "pond": [(
        "Why can pond weeds be a problem?",
        "Pond weeds are soft plants in the water, but they can wrap around feet or legs. Then a small animal may have trouble moving safely."
    )],
    "storm": [(
        "Why do animals look for shelter in a storm?",
        "Rain and wind can make a small animal cold and tired. Shelter gives a dry, safer place to rest."
    )],
    "berries": [(
        "Why might berries be hard to reach?",
        "Berries can grow high on thin or prickly branches. An animal without wings may not be able to get them safely."
    )],
}
KNOWLEDGE_ORDER = ["kindness", "friendship", "pond", "storm", "berries", "swim", "fly", "dig"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    other = f["other"]
    trouble = f["trouble"]
    ret = f["return_need"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the word "pitiful" and teaches kindness.',
        f"Tell a gentle fable where {helper.id} sees {other.id} in trouble at {trouble.place}, helps, and is helped later in return.",
        f"Write an animal story with a clear moral value: one small creature notices suffering, acts with care, and friendship grows by sunset.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    other = f["other"]
    trouble = f["trouble"]
    ret = f["return_need"]
    action = f["action"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id} the {helper.species} and {other.id} the {other.species}. They begin as quiet neighbors and end as true friends."
        ),
        (
            f"Why did {helper.id} feel sorry for {other.id}?",
            f"{helper.id} saw {other.id} in trouble at {trouble.place}, and the sight looked pitiful. Because {other.id} was frightened and could not get free alone, {helper.id} felt concern and came closer."
        ),
        (
            f"How did {helper.id} help {other.id}?",
            f"{helper.id} {action.qa_text}. That worked because a {helper.species} could use {ANIMALS[helper.species].ability} in exactly the way the problem needed."
        ),
        (
            f"How did {other.id} help later?",
            f"When {helper.id} had a problem later in the day, {other.id} remembered the earlier kindness and came back to help. {ret.solved_text.format(helper=helper.id, other=other.id)}"
        ),
        (
            "What is the moral of the story?",
            "The story teaches that kindness should not stop at feeling sorry. When someone acts with care, that good turn can grow into trust, friendship, and help returned."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["helper_cfg"].tags) | set(f["other_cfg"].tags) | set(f["trouble"].tags) | set(f["return_need"].tags)
    tags.add("kindness")
    if f.get("returned"):
        tags.add("friendship")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.species:
            bits.append(f"species={ent.species}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        attrs = {k: v for k, v in ent.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------
def explain_combo(helper: AnimalKind, trouble: Trouble) -> str:
    return (
        f"(No story: a {helper.noun} cannot reasonably solve {trouble.label}. "
        f"This world only tells stories where the helper's real ability fits the trouble.)"
    )


def explain_return(other: AnimalKind, ret: ReturnNeed) -> str:
    return (
        f"(No story: a {other.noun} cannot reasonably return the favor for '{ret.label}'. "
        f"The second kindness must fit the second animal's ability too.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(H,O,T,R) :- animal(H), animal(O), H != O, trouble(T), return_need(R),
                  best_action(H,T,_), return_possible(O,R).

action_possible(H,A) :- animal(H), action(A), requires(A,Need), has(H,Need),
                        not missing_need(H,A).
missing_need(H,A) :- requires(A,Need), not has(H,Need).

works(H,T,A) :- action_possible(H,A), trouble_need(T,Need), requires(A,Need),
                trouble_severity(T,S), action_power(A,P), P >= S.

best_action(H,T,A) :- works(H,T,A), not better_action(H,T,A).
better_action(H,T,A) :- works(H,T,A), works(H,T,B), action_sense(B,SB), action_sense(A,SA), SB > SA.
better_action(H,T,A) :- works(H,T,A), works(H,T,B), action_sense(B,SA), action_sense(A,SA), action_power(B,PB), action_power(A,PA), PB > PA.

return_possible(O,R) :- animal(O), return_need(R), return_need_ability(R,Need), has(O,Need).
sensible(A) :- action(A), action_sense(A,S), kindness_min(M), S >= M.

% outcome is always the same in this narrow world once a valid combo exists
outcome(help_returned) :- chosen_helper(H), chosen_other(O), chosen_trouble(T), chosen_return(R),
                          valid(H,O,T,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        if animal.can_swim:
            lines.append(asp.fact("has", aid, "swim"))
        if animal.can_fly:
            lines.append(asp.fact("has", aid, "fly"))
        if animal.can_dig:
            lines.append(asp.fact("has", aid, "dig"))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_need", tid, trouble.method_need))
        lines.append(asp.fact("trouble_severity", tid, trouble.severity))
    for rid, ret in RETURN_NEEDS.items():
        lines.append(asp.fact("return_need", rid))
        lines.append(asp.fact("return_need_ability", rid, ret.need))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_power", aid, action.power))
        lines.append(asp.fact("action_sense", aid, action.sense))
        for need in sorted(action.needs):
            lines.append(asp.fact("requires", aid, need))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_best_actions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show best_action/3."))
    return sorted(set(asp.atoms(model, "best_action")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_other", params.other),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_return", params.return_need),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_actions = set()
    for helper_id, helper in ANIMALS.items():
        for trouble_id, trouble in TROUBLES.items():
            try:
                py_actions.add((helper_id, trouble_id, best_action_for(helper, trouble).id))
            except StoryError:
                pass
    cl_actions = set(asp_best_actions())
    if py_actions == cl_actions:
        print(f"OK: best-action model matches ({len(py_actions)} helper/trouble cases).")
    else:
        rc = 1
        print("MISMATCH in best actions:")
        if cl_actions - py_actions:
            print("  only in clingo:", sorted(cl_actions - py_actions))
        if py_actions - cl_actions:
            print("  only in python:", sorted(py_actions - cl_actions))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify for seed {s}.")
            break

    bad = 0
    for params in cases:
        py_out = "help_returned"
        cl_out = asp_outcome(params)
        if py_out != cl_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        helper="duck",
        other="swallow",
        trouble="pond_drift",
        return_need="berry_patch",
        helper_name="Pip",
        other_name="Fern",
        action="swim_and_pull",
    ),
    StoryParams(
        helper="swallow",
        other="mole",
        trouble="thorn_bush",
        return_need="storm_nest",
        helper_name="Sunny",
        other_name="Moss",
        action="fly_and_lift",
    ),
    StoryParams(
        helper="mole",
        other="duck",
        trouble="buried_tunnel",
        return_need="lost_seed",
        helper_name="Tumble",
        other_name="Reed",
        action="dig_open",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal fable storyworld: pity, kindness, and help returned."
    )
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--other", choices=ANIMALS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--return-need", dest="return_need", choices=RETURN_NEEDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--helper-name")
    ap.add_argument("--other-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.other and args.helper == args.other:
        raise StoryError("(No story: the helper and the helped animal must be different.)")

    if args.helper and args.trouble:
        helper = ANIMALS[args.helper]
        trouble = TROUBLES[args.trouble]
        if not sensible_actions_for(helper, trouble):
            raise StoryError(explain_combo(helper, trouble))

    if args.other and args.return_need:
        other = ANIMALS[args.other]
        ret = RETURN_NEEDS[args.return_need]
        if not return_possible(other, ret):
            raise StoryError(explain_return(other, ret))

    combos = [
        combo for combo in valid_combos()
        if (args.helper is None or combo[0] == args.helper)
        and (args.other is None or combo[1] == args.other)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.return_need is None or combo[3] == args.return_need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    helper_id, other_id, trouble_id, return_id = rng.choice(sorted(combos))
    helper_cfg = ANIMALS[helper_id]
    trouble_cfg = TROUBLES[trouble_id]
    sensible = sensible_actions_for(helper_cfg, trouble_cfg)
    if args.action:
        action = ACTIONS[args.action]
        if action not in sensible:
            raise StoryError("(No story: that action is not a sensible way for this helper to solve this trouble.)")
        action_id = action.id
    else:
        action_id = max(sensible, key=lambda a: (a.sense, a.power, a.id)).id

    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    other_name = args.other_name or rng.choice([n for n in OTHER_NAMES if n != helper_name])

    return StoryParams(
        helper=helper_id,
        other=other_id,
        trouble=trouble_id,
        return_need=return_id,
        helper_name=helper_name,
        other_name=other_name,
        action=action_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.helper not in ANIMALS:
        raise StoryError(f"Unknown helper animal: {params.helper}")
    if params.other not in ANIMALS:
        raise StoryError(f"Unknown other animal: {params.other}")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.return_need not in RETURN_NEEDS:
        raise StoryError(f"Unknown return_need: {params.return_need}")
    if params.action not in ACTIONS:
        raise StoryError(f"Unknown action: {params.action}")
    if params.helper == params.other:
        raise StoryError("The helper and the helped animal must be different.")

    helper_cfg = ANIMALS[params.helper]
    other_cfg = ANIMALS[params.other]
    trouble = TROUBLES[params.trouble]
    ret = RETURN_NEEDS[params.return_need]
    action = ACTIONS[params.action]

    if not help_works(helper_cfg, trouble, action):
        raise StoryError(explain_combo(helper_cfg, trouble))
    if not return_possible(other_cfg, ret):
        raise StoryError(explain_return(other_cfg, ret))

    world = tell(
        helper_cfg=helper_cfg,
        other_cfg=other_cfg,
        trouble=trouble,
        return_need=ret,
        helper_name=params.helper_name,
        other_name=params.other_name,
        action=action,
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
        print(asp_program("", "#show valid/4.\n#show best_action/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (helper, other, trouble, return_need) combos:\n")
        for helper, other, trouble, ret in combos:
            print(f"  {helper:8} {other:8} {trouble:14} {ret}")
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
            header = f"### {p.helper_name} the {p.helper}: {p.trouble} -> {p.return_need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
