#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py
===================================================================================

A standalone storyworld for a tall-tale flavored friendship story about pudding,
a shaker, and a lesson learned.

Premise
-------
Two friends try to make a grand pudding treat in an outsized, boastful way.
One friend wants to pour in too much liquid and shake too hard. The other friend
predicts the trouble, warns with a little rhyme, and either averts the mess or
helps fix it. The ending proves that friendship and good sense matter more than
showing off.

Run it
------
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py --liquid lemonade
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py --fix keep_shaking
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pudding_shaker_liquid_lesson_learned_friendship_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
IDEAL_LIQUID = 2
SENSE_MIN = 2
PRIDE_INIT = 5.0
WISE_TRAITS = {"steady", "careful", "patient", "kind"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    brag: str
    closing: str
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
class Flavor:
    id: str
    pudding_name: str
    color: str
    boast: str
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
class Liquid:
    id: str
    label: str
    phrase: str
    splash: str
    sets_pudding: bool
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
class Shaker:
    id: str
    label: str
    phrase: str
    sealed: bool
    capacity: int
    rumble: str
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    action: str
    qa_action: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def shake_risk(pour: int, shaker: Shaker) -> int:
    excess = max(0, pour - IDEAL_LIQUID)
    brim = 1 if pour >= shaker.capacity else 0
    return excess + brim


def can_set(liquid: Liquid) -> bool:
    return liquid.sets_pudding


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_works(fix: Fix, risk: int) -> bool:
    return fix.power >= risk


def initial_wisdom(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_avert(trust: int, helper_trait: str, risk: int) -> bool:
    if risk <= 0:
        return False
    authority = initial_wisdom(helper_trait) + (trust / 3.0) + 1.0
    return authority > PRIDE_INIT + 0.5


def _r_spill(world: World) -> list[str]:
    bowl = world.get("bowl")
    room = world.get("room")
    if bowl.meters["spill"] < THRESHOLD:
        return []
    sig = ("spill", "bowl")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mess"] += 1
    for kid in [world.get("hero"), world.get("friend")]:
        kid.memes["alarm"] += 1
    return ["__spill__"]


def _r_set(world: World) -> list[str]:
    bowl = world.get("bowl")
    if bowl.meters["chilled"] < THRESHOLD or bowl.meters["mixed"] < THRESHOLD:
        return []
    if bowl.meters["too_runny"] >= THRESHOLD:
        return []
    sig = ("set", "bowl")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["set"] += 1
    for kid in [world.get("hero"), world.get("friend")]:
        kid.memes["hope"] += 1
    return ["__set__"]


def _r_help_bonds(world: World) -> list[str]:
    if world.get("hero").memes["helped"] < THRESHOLD:
        return []
    sig = ("bond", "friends")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["friendship"] += 1
    world.get("friend").memes["friendship"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="set", tag="physical", apply=_r_set),
    Rule(name="bond", tag="social", apply=_r_help_bonds),
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
        for sent in produced:
            world.say(sent)
    return produced


def predict_trouble(world: World, pour: int, shaker: Shaker, liquid: Liquid) -> dict:
    sim = world.copy()
    bowl = sim.get("bowl")
    bowl.meters["mixed"] = 1
    bowl.meters["liquid"] = float(pour)
    bowl.meters["too_runny"] = 1.0 if pour > IDEAL_LIQUID else 0.0
    if shake_risk(pour, shaker) > 0:
        bowl.meters["spill"] += 1
        propagate(sim, narrate=False)
    return {
        "spill": sim.get("bowl").meters["spill"] >= THRESHOLD,
        "too_runny": sim.get("bowl").meters["too_runny"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
        "can_set": liquid.sets_pudding and sim.get("bowl").meters["too_runny"] < THRESHOLD,
    }


def tale_opening(world: World, hero: Entity, friend: Entity,
                 setting: Setting, flavor: Flavor) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"One bright day at {setting.place}, {hero.id} and {friend.id} were such good friends "
        f"that folks said their laughter could rattle teaspoons a mile away."
    )
    world.say(
        f"They had promised to make {flavor.pudding_name}, and {setting.brag}."
    )


def giant_plan(world: World, hero: Entity, friend: Entity,
               flavor: Flavor, shaker: Shaker) -> None:
    world.say(
        f"{hero.id} held up {shaker.phrase} and declared that it was big enough "
        f"to wake sleepy crows and mix dessert clear up to the clouds."
    )
    world.say(
        f"{friend.id} laughed, because the boast was half foolish and half wonderful, "
        f"which is how the best tall plans usually begin."
    )
    world.say(
        f"Into the bowl went the {flavor.color} pudding powder, looking {flavor.boast}."
    )


def temptation(world: World, hero: Entity, liquid: Liquid, pour: int) -> None:
    hero.memes["pride"] += 1
    amount_words = {1: "just a splash", 2: "a fair measure", 3: "a heroic flood"}
    world.say(
        f"Then {hero.id} reached for {liquid.phrase}. "
        f'"Let us pour in {amount_words.get(pour, str(pour))} of liquid and shake till the spoon sings!" '
        f"{hero.pronoun().capitalize()} cried."
    )


def warning(world: World, friend: Entity, hero: Entity, liquid: Liquid,
            shaker: Shaker, pour: int) -> None:
    pred = predict_trouble(world, pour, shaker, liquid)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_too_runny"] = pred["too_runny"]
    world.facts["predicted_mess"] = pred["mess"]
    friend.memes["care"] += 1
    rhyme = "Shake it low and shake it slow; brim it high and off it'll go."
    world.facts["rhyme"] = rhyme
    line = f'{friend.id} tapped the side of the {shaker.label} and sang, "{rhyme}"'
    if pred["spill"] and pred["too_runny"]:
        line += (
            f". {friend.pronoun().capitalize()} could already picture {liquid.label} sloshing out "
            f"and the pudding turning thin as a creek."
        )
    elif pred["spill"]:
        line += (
            f". {friend.pronoun().capitalize()} could already picture {liquid.label} sloshing over the rim."
        )
    elif pred["too_runny"]:
        line += (
            f". {friend.pronoun().capitalize()} could already picture the pudding staying too loose to stand in a spoon."
        )
    world.say(line)


def heed_warning(world: World, hero: Entity, friend: Entity, liquid: Liquid) -> None:
    hero.memes["respect"] += 1
    hero.memes["lesson"] += 1
    friend.memes["relief"] += 1
    bowl = world.get("bowl")
    bowl.meters["liquid"] = float(IDEAL_LIQUID)
    world.say(
        f"{hero.id} stopped with the {liquid.label} tilted in midair, blinked once, and grinned. "
        f'"You are right," {hero.pronoun()} said. "A friend who warns you before a splash is better '
        f'than a hundred cheering fools after one."'
    )
    world.say(
        f"So {hero.id} poured only the right amount, and the bowl looked sensible again, "
        f"though still grand enough for bragging."
    )


def defy_warning(world: World, hero: Entity, liquid: Liquid, pour: int) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} was feeling taller than a windmill. "A little extra liquid never scared a legend," '
        f"{hero.pronoun()} said, and in it went."
    )
    bowl = world.get("bowl")
    bowl.meters["liquid"] = float(pour)
    bowl.meters["too_runny"] = 1.0 if pour > IDEAL_LIQUID else 0.0


def shake(world: World, hero: Entity, friend: Entity,
          shaker: Shaker, pour: int) -> None:
    bowl = world.get("bowl")
    bowl.meters["mixed"] = 1
    world.say(
        f"They snapped the lid on the {shaker.label} and shook. {shaker.rumble}."
    )
    risk = shake_risk(pour, shaker)
    bowl.meters["risk"] = float(risk)
    if risk > 0:
        bowl.meters["spill"] += 1
    propagate(world, narrate=False)
    if bowl.meters["spill"] >= THRESHOLD:
        world.say(
            f"In one jumpy instant, pudding flecks and pale {world.facts['liquid_cfg'].label} "
            f"spun out in a curly storm and dotted the table like silly little moons."
        )
        world.say(
            f"{friend.id} grabbed the bowl, and {hero.id} grabbed the spoon, and both of them stared as if "
            f"the pudding had tried to grow wings."
        )
    else:
        world.say(
            f"The mixture swirled thick and glossy instead of flying loose, and the friends cheered at once."
        )


def apply_fix(world: World, hero: Entity, friend: Entity, fix: Fix, risk: int) -> bool:
    hero.memes["helped"] += 1
    friend.memes["helped"] += 1
    propagate(world, narrate=False)
    bowl = world.get("bowl")
    room = world.get("room")
    ok = fix_works(fix, risk)
    if ok:
        bowl.meters["spill"] = 0.0
        bowl.meters["too_runny"] = 0.0
        bowl.meters["chilled"] += 1
        room.meters["mess"] = 0.0
        world.say(
            f"But friends are strongest right after a wobble. Together they {fix.action}."
        )
        world.say(
            f"The wild pudding settled down from a circus to a dessert."
        )
        propagate(world, narrate=False)
        hero.memes["lesson"] += 1
        friend.memes["relief"] += 1
        return True
    world.say(
        f"They tried to {fix.fail}, but that only made the pudding slosh and sigh."
    )
    bowl.meters["chilled"] = 0.0
    hero.memes["lesson"] += 1
    return False


def chill_success(world: World, hero: Entity, friend: Entity,
                  flavor: Flavor, setting: Setting) -> None:
    bowl = world.get("bowl")
    if bowl.meters["chilled"] < THRESHOLD:
        bowl.meters["chilled"] += 1
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After a little wait, the {flavor.pudding_name} stood up proud on each spoon "
        f"like it had learned some manners."
    )
    world.say(
        f"{hero.id} took the first bite and handed the second spoon to {friend.id}, because good pudding, "
        f"like good luck, tastes better when shared."
    )
    world.say(
        f"From then on, whenever anyone at {setting.place} bragged too hard over a bowl, the two friends would grin "
        f"and chant, \"{world.facts['rhyme']}\" {setting.closing}"
    )


def soft_failure(world: World, hero: Entity, friend: Entity,
                 setting: Setting, liquid: Liquid) -> None:
    hero.memes["sad"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"The pudding never truly set. It stayed a slippery little lake of {liquid.label}, "
        f"more fit for sipping than spooning."
    )
    world.say(
        f"Still, {friend.id} slid the better cup to {hero.id} and said that a spoiled dessert was no reason "
        f"to spoil a friendship."
    )
    world.say(
        f"{hero.id} nodded. From that day on, the lesson stayed put even when the pudding did not: "
        f"listen before you slosh, and treasure the friend who tells you the truth. "
        f"{setting.closing}"
    )


def tell(setting: Setting, flavor: Flavor, liquid: Liquid, shaker: Shaker, fix: Fix,
         hero_name: str = "Milo", hero_gender: str = "boy",
         friend_name: str = "June", friend_gender: str = "girl",
         helper_trait: str = "steady", parent_type: str = "mother",
         pour: int = 2, trust: int = 7) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["bold"],
        attrs={"name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[helper_trait],
        attrs={"name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the pie-judge",
        role="adult",
        attrs={},
    ))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="pudding",
        label="pudding bowl",
        role="dessert",
        attrs={},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label="cook tent",
        attrs={},
    ))

    hero.memes["pride"] = PRIDE_INIT
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    friend.memes["wisdom"] = initial_wisdom(helper_trait)
    friend.memes["trust"] = float(trust)
    bowl.meters["liquid"] = 0.0
    bowl.meters["spill"] = 0.0
    bowl.meters["mixed"] = 0.0
    bowl.meters["too_runny"] = 0.0
    bowl.meters["chilled"] = 0.0
    bowl.meters["set"] = 0.0
    room.meters["mess"] = 0.0

    world.facts.update(
        setting=setting,
        flavor=flavor,
        liquid_cfg=liquid,
        shaker_cfg=shaker,
        fix_cfg=fix,
        hero=hero,
        friend=friend,
        parent=parent,
        pour=pour,
        trust=trust,
        helper_trait=helper_trait,
    )

    tale_opening(world, hero, friend, setting, flavor)
    giant_plan(world, hero, friend, flavor, shaker)

    world.para()
    temptation(world, hero, liquid, pour)
    warning(world, friend, hero, liquid, shaker, pour)

    risk = shake_risk(pour, shaker)
    averted = would_avert(trust, helper_trait, risk)

    if averted:
        heed_warning(world, hero, friend, liquid)
        bowl.meters["mixed"] = 1.0
        bowl.meters["chilled"] = 1.0
        propagate(world, narrate=False)
        world.para()
        chill_success(world, hero, friend, flavor, setting)
        outcome = "averted"
    else:
        defy_warning(world, hero, liquid, pour)
        world.para()
        shake(world, hero, friend, shaker, pour)
        if risk == 0:
            bowl.meters["chilled"] = 1.0
            propagate(world, narrate=False)
            world.para()
            chill_success(world, hero, friend, flavor, setting)
            hero.memes["lesson"] += 1
            outcome = "smooth"
        else:
            world.para()
            saved = apply_fix(world, hero, friend, fix, risk)
            if saved:
                chill_success(world, hero, friend, flavor, setting)
                outcome = "saved"
            else:
                soft_failure(world, hero, friend, setting, liquid)
                outcome = "soupy"

    world.facts.update(
        risk=risk,
        averted=averted,
        outcome=outcome,
        spilled=bowl.meters["spill"] >= THRESHOLD,
        set=bowl.meters["set"] >= THRESHOLD,
        mess=room.meters["mess"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "fairground": Setting(
        id="fairground",
        place="the county fair cook tent",
        brag="old timers swore the spoons in their aprons began to tremble with excitement",
        closing="and even the pie-judge smiled into her apron.",
        tags={"fair", "friendship"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the apple orchard shed",
        brag="the hanging lanterns seemed to lean lower just to watch",
        closing="and the orchard sparrows hopped close for the chorus.",
        tags={"orchard", "friendship"},
    ),
    "windmill": Setting(
        id="windmill",
        place="the windmill hill bake shack",
        brag="the old windmill itself seemed to slow down so it would not miss the show",
        closing="and the hill carried the rhyme clear across the fields.",
        tags={"windmill", "friendship"},
    ),
}

FLAVORS = {
    "vanilla": Flavor(
        id="vanilla",
        pudding_name="vanilla pudding",
        color="pale gold",
        boast="soft as sunrise on a butter plate",
        tags={"pudding"},
    ),
    "chocolate": Flavor(
        id="chocolate",
        pudding_name="chocolate pudding",
        color="deep brown",
        boast="dark and rich enough to make a spoon stand proud",
        tags={"pudding"},
    ),
    "banana": Flavor(
        id="banana",
        pudding_name="banana pudding",
        color="sunny yellow",
        boast="bright as a pocketful of noon",
        tags={"pudding"},
    ),
}

LIQUIDS = {
    "milk": Liquid(
        id="milk",
        label="milk",
        phrase="a pitcher of milk",
        splash="white splashes",
        sets_pudding=True,
        tags={"liquid", "milk", "pudding"},
    ),
    "oat_milk": Liquid(
        id="oat_milk",
        label="oat milk",
        phrase="a jug of oat milk",
        splash="creamy splashes",
        sets_pudding=True,
        tags={"liquid", "oat_milk", "pudding"},
    ),
    "coconut_milk": Liquid(
        id="coconut_milk",
        label="coconut milk",
        phrase="a tin of coconut milk",
        splash="sweet pale splashes",
        sets_pudding=True,
        tags={"liquid", "coconut_milk", "pudding"},
    ),
    "lemonade": Liquid(
        id="lemonade",
        label="lemonade",
        phrase="a jar of lemonade",
        splash="sparkly splashes",
        sets_pudding=False,
        tags={"liquid", "lemonade"},
    ),
}

SHAKERS = {
    "silver_shaker": Shaker(
        id="silver_shaker",
        label="silver shaker",
        phrase="a silver shaker",
        sealed=True,
        capacity=3,
        rumble="It thumped like a tiny thunderstorm in a cupboard",
        tags={"shaker"},
    ),
    "mason_jar": Shaker(
        id="mason_jar",
        label="mason jar",
        phrase="a mason jar with a tin lid",
        sealed=True,
        capacity=2,
        rumble="It rattled like marbles in a drummer's pocket",
        tags={"shaker"},
    ),
    "flour_sifter": Shaker(
        id="flour_sifter",
        label="flour sifter",
        phrase="an old flour sifter",
        sealed=False,
        capacity=1,
        rumble="It buzzed and leaked and had no business holding a puddle",
        tags={"shaker"},
    ),
}

FIXES = {
    "add_more_mix": Fix(
        id="add_more_mix",
        label="add more pudding powder",
        sense=3,
        power=3,
        action="sprinkled in more pudding powder, wiped the rim, and set the bowl on ice",
        qa_action="added more pudding powder and chilled the bowl",
        fail="add more pudding powder, but there was too much slosh left in the bowl",
        tags={"fix", "pudding"},
    ),
    "ladle_and_chill": Fix(
        id="ladle_and_chill",
        label="ladle some out and chill it",
        sense=3,
        power=2,
        action="ladled some of the runny part away, cleaned the table, and chilled what remained",
        qa_action="ladled some out and chilled the pudding",
        fail="ladle some away and chill the rest, but the pudding was still too thin",
        tags={"fix", "pudding"},
    ),
    "keep_shaking": Fix(
        id="keep_shaking",
        label="keep shaking harder",
        sense=1,
        power=1,
        action="kept shaking harder",
        qa_action="kept shaking harder",
        fail="keep shaking harder",
        tags={"fix"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Ruth", "Elsie", "Nora", "Clara", "Della", "Ivy"]
BOY_NAMES = ["Milo", "Toby", "Wes", "Otis", "Finn", "Cal", "Jude", "Eli"]
TRAITS = ["steady", "careful", "patient", "kind", "bright", "quick"]


@dataclass
class StoryParams:
    setting: str
    flavor: str
    liquid: str
    shaker: str
    fix: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    helper_trait: str
    pour: int = 2
    trust: int = 7
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for lid, liquid in LIQUIDS.items():
            for kid, shaker in SHAKERS.items():
                if liquid.sets_pudding and shaker.sealed:
                    combos.append((sid, lid, kid))
    return combos


KNOWLEDGE = {
    "pudding": [
        (
            "What is pudding?",
            "Pudding is a soft, sweet dessert. It starts as a mixture and gets thicker as it sets.",
        )
    ],
    "shaker": [
        (
            "What is a shaker?",
            "A shaker is a container you can close and move back and forth to mix things inside. It works best when the lid fits tightly.",
        )
    ],
    "liquid": [
        (
            "What is a liquid?",
            "A liquid is something that can pour and flow, like milk or water. It does not keep its own shape the way a solid does.",
        )
    ],
    "milk": [
        (
            "Why can milk help make pudding?",
            "Milk gives pudding moisture so the powder can mix smoothly. The right amount helps the pudding become creamy instead of lumpy or thin.",
        )
    ],
    "lemonade": [
        (
            "Why is lemonade a poor choice for pudding mix?",
            "Lemonade is too sharp and watery for this kind of pudding mix. It can leave the dessert thin instead of thick and creamy.",
        )
    ],
    "friendship": [
        (
            "What does a good friend do when something might go wrong?",
            "A good friend tells the truth kindly and tries to help. Friendship is not just cheering; it is also warning and fixing things together.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or pattern of words with matching ending sounds. Rhymes can help people remember a lesson.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pudding", "shaker", "liquid", "milk", "lemonade", "friendship", "rhyme"]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "boy" and friend.type == "boy":
        return "two friends"
    if hero.type == "girl" and friend.type == "girl":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    flavor = f["flavor"]
    liquid = f["liquid_cfg"]
    outcome = f["outcome"]
    rhyme = f["rhyme"]
    base = (
        f'Write a short tall-tale story for a 3-to-5-year-old about friendship and a lesson learned. '
        f'Include the words "pudding", "shaker", and "liquid".'
    )
    if outcome == "soupy":
        return [
            base,
            f"Tell a tall story where {hero.label} and {friend.label} try to make {flavor.pudding_name} at {setting.place}, "
            f"ignore a warning rhyme, and end with a gentle lesson after the pudding stays runny.",
            f'Write a playful cautionary tale where a child boasts too much over a bowl, the rhyme "{rhyme}" appears, '
            f"and friendship matters more than a perfect dessert.",
        ]
    if outcome == "averted":
        return [
            base,
            f"Tell a tall tale where {friend.label} saves the pudding before the mess starts by singing a rhyme, "
            f"and the friends share the dessert happily.",
            f'Write a friendship story in a braggy, funny style where one child listens to a wise friend, uses the right amount of liquid, '
            f'and learns that careful choices still make grand pudding.',
        ]
    return [
        base,
        f"Tell a tall tale where {hero.label} and {friend.label} make {flavor.pudding_name} in a {f['shaker_cfg'].label}, "
        f"a wobble or spill happens, and the friends fix it together.",
        f'Write a rhyming friendship story where a warning about liquid and shaking becomes the lesson at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    flavor = f["flavor"]
    liquid = f["liquid_cfg"]
    shaker = f["shaker_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, {hero.label} and {friend.label}, making {flavor.pudding_name}. They are close friends, and the story follows how they work through trouble together.",
        ),
        (
            "What were they trying to make?",
            f"They were trying to make {flavor.pudding_name} in a {shaker.label}. The pudding was meant to be a big, brag-worthy treat, not an ordinary snack.",
        ),
        (
            f"Why did {friend.label} sing a rhyme before they shook the bowl?",
            f"{friend.label} could tell that too much liquid might make the pudding spill or stay runny. The rhyme was a friendly warning, so the lesson would be easy to remember before the trouble started.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What lesson did {hero.label} learn before the mess even happened?",
                f"{hero.label} learned to listen when a friend gives a careful warning. That mattered because using the right amount of liquid let the pudding set nicely instead of turning into a splashy mistake.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the friends sharing firm, creamy pudding and repeating the rhyme together. The ending image shows that friendship grew stronger because they chose sense over showing off.",
            )
        )
    elif outcome == "smooth":
        qa.append(
            (
                "Did anything go wrong when they shook it?",
                f"No big mess happened, because the amount of liquid matched the job and the shaker could handle it. The pudding behaved, and the friends still came away with a lesson about not bragging too hard.",
            )
        )
        qa.append(
            (
                "How did friendship matter in the story?",
                f"Friendship mattered because the warning was given kindly and received in good spirit, even after the shaking began. The two friends shared the finished pudding instead of arguing over who was right.",
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                "How did they fix the pudding after the wobble?",
                f"They {fix.qa_action}. That worked because the friends stopped showing off and started solving the real problem together.",
            )
        )
        qa.append(
            (
                "What lesson did the ending teach?",
                f"The ending taught that a bold mistake does not have to ruin the day if friends help each other fix it. It also showed that listening sooner would have made the work easier.",
            )
        )
    elif outcome == "soupy":
        qa.append(
            (
                "Why did the pudding stay soupy?",
                f"It stayed soupy because there was too much liquid and the fix was not strong enough to undo the mistake. The dessert failed, but the friends still learned from what happened.",
            )
        )
        qa.append(
            (
                "Was the friendship ruined?",
                f"No, the friendship stayed strong. {friend.label} still shared kindly, and {hero.label} accepted the lesson instead of blaming anyone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pudding", "shaker", "liquid", "friendship", "rhyme"}
    liquid = f["liquid_cfg"]
    if "milk" in liquid.tags:
        tags.add("milk")
    if "lemonade" in liquid.tags:
        tags.add("lemonade")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label and e.label != e.id:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


def explain_liquid(liquid: Liquid) -> str:
    return (
        f"(No story: {liquid.label} is too poor a pudding liquid for this world. "
        f"It would not set into pudding, so the whole tale loses its honest dessert problem. "
        f"Try milk, oat_milk, or coconut_milk.)"
    )


def explain_shaker(shaker: Shaker) -> str:
    return (
        f"(No story: the {shaker.label} is not sealed, so shaking liquid in it would just be a guaranteed leak. "
        f"Pick a container with a tight lid, like silver_shaker or mason_jar.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    liquid = LIQUIDS[params.liquid]
    shaker = SHAKERS[params.shaker]
    fix = FIXES[params.fix]
    risk = shake_risk(params.pour, shaker)
    if would_avert(params.trust, params.helper_trait, risk):
        return "averted"
    if risk == 0:
        return "smooth"
    return "saved" if fix_works(fix, risk) else "soupy"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
valid(S, L, Sh) :- setting(S), liquid(L), shaker(Sh), sets_pudding(L), sealed(Sh).
sensible_fix(F) :- fix(F), sense(F, N), sense_min(M), N >= M.

% --- outcome model ----------------------------------------------------------
excess(P - I) :- pour(P), ideal(I), P > I.
excess(0)     :- pour(P), ideal(I), P <= I.
brim(1)       :- pour(P), chosen_shaker(Sh), capacity(Sh, C), P >= C.
brim(0)       :- pour(P), chosen_shaker(Sh), capacity(Sh, C), P < C.
risk(E + B)   :- excess(E), brim(B).

wise_now(T)   :- helper_trait(T), wise_trait(T).
base_wisdom(5) :- helper_trait(T), wise_now(T).
base_wisdom(3) :- helper_trait(T), not wise_now(T).
authority(W + 1 + Tr) :- base_wisdom(W), trust(Tr0), Tr = Tr0 / 3.
averted       :- risk(R), R > 0, pride_init(P), authority(A), A > P + 0.5.

works         :- chosen_fix(F), risk(R), power(F, P), P >= R.

outcome(averted) :- averted.
outcome(smooth)  :- not averted, risk(0).
outcome(saved)   :- not averted, risk(R), R > 0, works.
outcome(soupy)   :- not averted, risk(R), R > 0, not works.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, liquid in LIQUIDS.items():
        lines.append(asp.fact("liquid", lid))
        if liquid.sets_pudding:
            lines.append(asp.fact("sets_pudding", lid))
    for sid, shaker in SHAKERS.items():
        lines.append(asp.fact("shaker", sid))
        if shaker.sealed:
            lines.append(asp.fact("sealed", sid))
        lines.append(asp.fact("capacity", sid, shaker.capacity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("ideal", IDEAL_LIQUID))
    lines.append(asp.fact("pride_init", 5))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_shaker", params.shaker),
            asp.fact("chosen_fix", params.fix),
            asp.fact("pour", params.pour),
            asp.fact("trust", params.trust),
            asp.fact("helper_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale storyworld: pudding, a shaker, too much liquid, and a friendship lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--flavor", choices=FLAVORS)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--shaker", choices=SHAKERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--pour", type=int, choices=[1, 2, 3])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.liquid and not LIQUIDS[args.liquid].sets_pudding:
        raise StoryError(explain_liquid(LIQUIDS[args.liquid]))
    if args.shaker and not SHAKERS[args.shaker].sealed:
        raise StoryError(explain_shaker(SHAKERS[args.shaker]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.liquid is None or combo[1] == args.liquid)
        and (args.shaker is None or combo[2] == args.shaker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, liquid, shaker = rng.choice(sorted(combos))
    flavor = args.flavor or rng.choice(sorted(FLAVORS))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    pour = args.pour if args.pour is not None else rng.choice([1, 2, 3])
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero = _pick_name(rng, hero_gender)
    friend = _pick_name(rng, friend_gender, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_trait = rng.choice(TRAITS)
    trust = rng.randint(2, 10)
    return StoryParams(
        setting=setting,
        flavor=flavor,
        liquid=liquid,
        shaker=shaker,
        fix=fix,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        helper_trait=helper_trait,
        pour=pour,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        flavor = FLAVORS[params.flavor]
        liquid = LIQUIDS[params.liquid]
        shaker = SHAKERS[params.shaker]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]}.)") from None

    if not liquid.sets_pudding:
        raise StoryError(explain_liquid(liquid))
    if not shaker.sealed:
        raise StoryError(explain_shaker(shaker))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if params.pour not in {1, 2, 3}:
        raise StoryError("(Invalid pour amount: choose 1, 2, or 3.)")

    world = tell(
        setting=setting,
        flavor=flavor,
        liquid=liquid,
        shaker=shaker,
        fix=fix,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        helper_trait=params.helper_trait,
        parent_type=params.parent,
        pour=params.pour,
        trust=params.trust,
    )

    # Replace internal ids with child-facing names in rendered text.
    story = world.render().replace("hero", params.hero).replace("friend", params.friend)

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


CURATED = [
    StoryParams(
        setting="fairground",
        flavor="vanilla",
        liquid="milk",
        shaker="silver_shaker",
        fix="ladle_and_chill",
        hero="Milo",
        hero_gender="boy",
        friend="June",
        friend_gender="girl",
        parent="mother",
        helper_trait="steady",
        pour=3,
        trust=10,
    ),
    StoryParams(
        setting="windmill",
        flavor="chocolate",
        liquid="oat_milk",
        shaker="mason_jar",
        fix="add_more_mix",
        hero="Elsie",
        hero_gender="girl",
        friend="Otis",
        friend_gender="boy",
        parent="father",
        helper_trait="bright",
        pour=3,
        trust=4,
    ),
    StoryParams(
        setting="orchard",
        flavor="banana",
        liquid="coconut_milk",
        shaker="silver_shaker",
        fix="ladle_and_chill",
        hero="Finn",
        hero_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        parent="mother",
        helper_trait="kind",
        pour=2,
        trust=5,
    ),
    StoryParams(
        setting="fairground",
        flavor="chocolate",
        liquid="milk",
        shaker="mason_jar",
        fix="ladle_and_chill",
        hero="Clara",
        hero_gender="girl",
        friend="Jude",
        friend_gender="boy",
        parent="father",
        helper_trait="quick",
        pour=3,
        trust=2,
    ),
]


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

    c_fix = set(asp_sensible_fixes())
    p_fix = {f.id for f in sensible_fixes()}
    if c_fix == p_fix:
        print(f"OK: sensible fixes match ({sorted(c_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_fix)} python={sorted(p_fix)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation and emit.
    try:
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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
        print(f"{len(combos)} compatible (setting, liquid, shaker) combos:\n")
        for setting, liquid, shaker in combos:
            print(f"  {setting:10} {liquid:12} {shaker}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.hero} & {p.friend}: {p.flavor} pudding with {p.liquid} "
                f"in {p.shaker} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
