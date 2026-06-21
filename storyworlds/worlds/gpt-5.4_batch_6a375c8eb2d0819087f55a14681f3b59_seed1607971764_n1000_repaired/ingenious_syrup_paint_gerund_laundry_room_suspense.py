#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py
=================================================================================

A standalone story world about a child in a laundry room who has an ingenious
but sticky idea: using syrup to make a painted banner shine. In this little
Tall-Tale-flavored world, the washing machine rumbles like a mountain, a ribbon
of syrup can creep toward a basket of clean laundry, and a calm grown-up helps
the children choose a better way to make art.

The domain is deliberately small and constraint-checked:
- A story only works when the chosen at-risk target is actually clean laundry
  close enough to be spoiled by a sticky spill.
- A low-common-sense response is known to the world but refused.
- Some stories are near-misses: an older sibling talks the instigator out of the
  idea before any spill happens.
- Otherwise, the spill happens; the ending depends on whether the response is
  quick and strong enough to stop the sticky river in time.

Run it
------
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py --qa
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py --all
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py --asp
    python storyworlds/worlds/gpt-5.4/ingenious_syrup_paint_gerund_laundry_room_suspense.py --verify
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
BRIGHTNESS_GOAL = 1
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    cloth: bool = False
    clean_laundry: bool = False
    sticky_source: bool = False
    proper_paint: bool = False
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
    boast: str
    props: str
    mission: str
    poster: str
    roar: str
    ending: str
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
class Syrup:
    id: str
    label: str
    phrase: str
    color: str
    pour: str
    gleam: str
    sticky: int
    sticky_source: bool = True
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
class Target:
    id: str
    label: str
    the: str
    place: str
    clean_name: str
    absorbent: bool
    near_laundry: bool
    severity: int
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
class Fix:
    id: str
    sense: int
    power: int
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


def _r_sticky_spread(world: World) -> list[str]:
    out: list[str] = []
    syrup = world.get("syrup")
    if syrup.meters["spilled"] < THRESHOLD:
        return out
    target = world.get("target")
    sig = ("sticky_spread", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["sticky_risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__suspense__")
    return out


def _r_ruin_laundry(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    if target.meters["sticky_risk"] < THRESHOLD:
        return out
    if target.meters["saved"] >= THRESHOLD:
        return out
    sig = ("ruined", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if target.clean_laundry:
        target.meters["sticky"] += 1
        target.meters["dirty"] += 1
        out.append("__ruined__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sticky_spread", tag="physical", apply=_r_sticky_spread),
    Rule(name="ruin_laundry", tag="physical", apply=_r_ruin_laundry),
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


def hazard_at_risk(syrup: Syrup, target: Target) -> bool:
    return syrup.sticky_source and target.absorbent and target.near_laundry


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def spill_severity(syrup: Syrup, target: Target, delay: int) -> int:
    return syrup.sticky + target.severity + delay


def is_saved(fix: Fix, syrup: Syrup, target: Target, delay: int) -> bool:
    return fix.power >= spill_severity(syrup, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_sticky(world: World) -> dict:
    sim = world.copy()
    sim.get("syrup").meters["spilled"] += 1
    propagate(sim, narrate=False)
    target = sim.get("target")
    return {
        "reaches_laundry": target.meters["sticky_risk"] >= THRESHOLD,
        "ruins_laundry": target.meters["sticky"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In the laundry room, where the washer {theme.roar}, {a.id} and {b.id} "
        f"{theme.boast} {theme.props}"
    )
    world.say(
        f"They had one grand mission: {theme.mission} on {theme.poster} before the washer finished its next mighty gulp."
    )


def need_shine(world: World, a: Entity, b: Entity) -> None:
    a.memes["desire"] += 1
    world.say(
        f'The colors were bright already, but {a.id} wanted the banner to shine even more. '
        f'"It needs one last splendid sparkle," {a.pronoun()} said.'
    )
    world.say(
        f'{b.id} looked at the paints, the cloth, and the neat stacks of clean laundry waiting nearby.'
    )


def tempt(world: World, a: Entity, syrup: Syrup) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'Then {a.id} had an ingenious idea. "{syrup.label.capitalize()}!" {a.pronoun()} cried. '
        f'"If I pour {syrup.phrase} over the paint-gerund part, it will gleam {syrup.gleam}."'
    )
    world.say(
        f"For one small, suspenseful moment, the idea sounded almost as big as a parade drum."
    )


def warn(world: World, b: Entity, a: Entity, syrup: Syrup, target: Target, parent: Entity) -> None:
    pred = predict_sticky(world)
    b.memes["caution"] += 1
    world.facts["predicted_reaches"] = pred["reaches_laundry"]
    world.facts["predicted_ruins"] = pred["ruins_laundry"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} could almost see a sticky river crawling toward {target.the}."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, syrup is for pancakes, not paint. '
        f'If it slips off the banner, it will run to {target.the} by {target.place}, and then {parent.label_word} will have a gooey mess to wash."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, syrup: Syrup) -> None:
    a.memes["defiance"] += 1
    older_instigator = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_instigator:
        world.say(
            f'"Just a drop," {a.id} said. Because {a.id} was {b.id}\'s older sibling, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Just a drop," {a.id} said, and tipped the bottle anyway.')


def back_down(world: World, a: Entity, b: Entity, syrup: Syrup, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    sib = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at {b.id}, who was {a.pronoun("possessive")} big {sib}, and the brave idea suddenly seemed smaller. '
        f'{a.pronoun().capitalize()} set {syrup.phrase} back on the shelf without opening it.'
    )
    world.say(
        f'Together they called for {parent.label_word} and asked for a better way to make the banner shine.'
    )


def spill(world: World, syrup_ent: Entity, syrup: Syrup, target: Target) -> None:
    syrup_ent.meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The cap slipped. Out came {syrup.pour}, glossy and slow, and then all at once fast as a little amber snake. '
        f'It slid across the folding table and reached for {target.the}.'
    )


def suspense(world: World, b: Entity, target: Target) -> None:
    b.memes["alarm"] += 1
    world.say(
        f'{b.id} gasped. "{target.The}! It\'s going to reach {target.clean_name}!"'
    )
    world.say("The washer thumped once, twice, and the whole laundry room seemed to hold its breath.")


def rescue(world: World, parent: Entity, fix: Fix, target_ent: Entity, target: Target) -> None:
    target_ent.meters["saved"] += 1
    target_ent.meters["sticky_risk"] = 0.0
    world.get("syrup").meters["spilled"] = 0.0
    body = fix.text.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came in at a trot and {body}.")
    world.say(
        f"The sticky river stopped short of {target.the}, and the clean laundry stayed bright and sweet-smelling."
    )


def rescue_fail(world: World, parent: Entity, fix: Fix, target_ent: Entity, target: Target) -> None:
    body = fix.fail.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} hurried in and {body}.")
    target_ent.meters["sticky"] += 1
    target_ent.meters["dirty"] += 1
    world.say(
        f"But the syrup was too far along. It kissed {target.the} and left it tacky, spotty, and no longer clean."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, syrup: Syrup) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'Then {parent.label_word} knelt between them. "Ingenious ideas are wonderful," {parent.pronoun()} said, '
        f'"but good ideas must fit the job. {syrup.label.capitalize()} is sticky food, not paint."'
    )
    world.say(
        f'{a.id} and {b.id} nodded. The lesson felt plain as a clothespin and true as thunder.'
    )


def sad_lesson(world: World, parent: Entity, a: Entity, b: Entity, target: Target, syrup: Syrup) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["sadness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} gave them a long hug beside {target.the}. "Nobody is hurt, and that matters most," {parent.pronoun()} said.'
    )
    world.say(
        f'But they all had to wash {target.clean_name} again, and {a.id} never forgot that {syrup.label} can turn a clever plan into a sticky trouble.'
    )


def proper_fix(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f'After the excitement, {parent.label_word} opened a cabinet and brought out washable poster paint and a little tray. '
        f'"Here is the right shine for cloth," {parent.pronoun()} said.'
    )
    world.say(
        f'Together they finished the banner properly, and when they lifted it up, it blazed so bright it looked fit to wake the moon.'
    )
    world.say(
        f'At the end, in the rumbling laundry room, {theme.ending}'
    )


THEMES = {
    "parade": Theme(
        id="parade",
        boast="were making a banner so grand it might have needed its own trumpet",
        props="A string of clothespins became a row of silver flags, and the folding table felt as wide as a town square.",
        mission="to finish the laundry-room parade banner",
        poster="an old practice sheet",
        roar="growled like a stone giant under the floor",
        ending="the children marched in a circle between the baskets as if they were leading the biggest parade in three counties",
        tags={"craft", "banner"},
    ),
    "circus": Theme(
        id="circus",
        boast="were painting a sign so splendid it seemed ready to call in a dozen flying elephants",
        props="The soap boxes stacked up like grandstands, and the laundry baskets looked like tiny circus wagons.",
        mission="to finish the circus sign",
        poster="an old drop cloth",
        roar="snorted and clanked like a brass band trapped in a cave",
        ending="the children bowed beside the washer as if the whole room were a circus ring full of cheers",
        tags={"craft", "sign"},
    ),
    "river": Theme(
        id="river",
        boast="were painting a map so mighty it looked able to boss a river into changing course",
        props="The dryer door was their round moon, and the ironing board stood tall like a bridge over a canyon.",
        mission="to finish the river map",
        poster="a wide scrap of cloth",
        roar="rolled and boomed like a faraway waterfall in boots",
        ending="the children spread the map on the table and grinned as if they had charted the whole county by lantern light",
        tags={"craft", "map"},
    ),
}

SYRUPS = {
    "maple": Syrup(
        id="maple",
        label="maple syrup",
        phrase="the maple syrup",
        color="amber",
        pour="a ribbon of amber syrup",
        gleam="like polished brass",
        sticky=2,
        tags={"syrup", "sticky_food"},
    ),
    "berry": Syrup(
        id="berry",
        label="berry syrup",
        phrase="the berry syrup",
        color="purple-red",
        pour="a purple-red ribbon of syrup",
        gleam="like sunset on a spoon",
        sticky=2,
        tags={"syrup", "sticky_food"},
    ),
    "peach": Syrup(
        id="peach",
        label="peach syrup",
        phrase="the peach syrup",
        color="gold",
        pour="a gold ribbon of syrup",
        gleam="like warm summer glass",
        sticky=1,
        tags={"syrup", "sticky_food"},
    ),
}

TARGETS = {
    "towels": Target(
        id="towels",
        label="clean towels",
        the="the clean towels",
        place="the wicker basket",
        clean_name="the towels",
        absorbent=True,
        near_laundry=True,
        severity=2,
        tags={"towels", "laundry"},
    ),
    "shirts": Target(
        id="shirts",
        label="fresh shirts",
        the="the fresh shirts",
        place="the rolling hamper",
        clean_name="the shirts",
        absorbent=True,
        near_laundry=True,
        severity=2,
        tags={"shirts", "laundry"},
    ),
    "socks": Target(
        id="socks",
        label="matching socks",
        the="the matching socks",
        place="the blue basket",
        clean_name="the socks",
        absorbent=True,
        near_laundry=True,
        severity=1,
        tags={"socks", "laundry"},
    ),
    "washer_lid": Target(
        id="washer_lid",
        label="washer lid",
        the="the washer lid",
        place="the machine itself",
        clean_name="the washer lid",
        absorbent=False,
        near_laundry=False,
        severity=0,
        tags={"metal"},
    ),
}

FIXES = {
    "towel_dam": Fix(
        id="towel_dam",
        sense=3,
        power=4,
        text="snatched two old rags, made a quick dam along the table edge, and lifted the {target} away from danger",
        fail="threw old rags down, but the syrup had already slipped around them",
        qa_text="made a rag dam and moved the laundry out of danger",
        tags={"rags", "cleanup"},
    ),
    "tray_swap": Fix(
        id="tray_swap",
        sense=3,
        power=3,
        text="slid a plastic tray under the dripping cloth and whisked the {target} to the top shelf",
        fail="slid a tray underneath, but the syrup had already dripped onto the laundry",
        qa_text="caught the spill with a tray and moved the laundry away",
        tags={"tray", "cleanup"},
    ),
    "rinse_sink": Fix(
        id="rinse_sink",
        sense=2,
        power=2,
        text="grabbed the cloth banner and carried it to the sink before the syrup could reach the {target}",
        fail="rushed the banner to the sink, but the syrup had already touched the laundry first",
        qa_text="carried the sticky banner to the sink before the spill spread farther",
        tags={"sink", "cleanup"},
    ),
    "spoon_scoop": Fix(
        id="spoon_scoop",
        sense=1,
        power=1,
        text="tried to chase the syrup with a spoon",
        fail="chased the syrup with a spoon, but it ran faster than that",
        qa_text="tried to scoop the syrup with a spoon",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "June", "Hazel", "Ruby", "Elsie"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Theo", "Finn", "Jack", "Eli"]
TRAITS = ["careful", "curious", "cautious", "steady", "clever", "sensible", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for theme_id in THEMES:
        for syrup_id, syrup in SYRUPS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(syrup, target):
                    combos.append((theme_id, syrup_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    syrup: str
    target: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
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
    "syrup": [
        (
            "What is syrup?",
            "Syrup is a thick, sweet liquid people pour on food like pancakes. It is tasty, but it is very sticky and can make a big mess.",
        )
    ],
    "sticky_food": [
        (
            "Why is syrup bad for clean clothes?",
            "Syrup soaks into cloth and leaves sticky spots that grab dust and dirt. That means the clothes are not clean anymore and have to be washed again.",
        )
    ],
    "laundry": [
        (
            "What happens in a laundry room?",
            "A laundry room is where people wash and dry clothes, towels, and other cloth things. It often has baskets, soap, and machines that clean laundry.",
        )
    ],
    "cleanup": [
        (
            "What should you do when something sticky spills near clean laundry?",
            "Move the clean laundry away first and stop the spill with rags, a tray, or another safe barrier. Then ask a grown-up to help clean the sticky mess properly.",
        )
    ],
    "craft": [
        (
            "What is washable paint for?",
            "Washable paint is made for art, so it gives color without turning everything into food-sticky goo. It is much better for crafts than syrup.",
        )
    ],
}
KNOWLEDGE_ORDER = ["syrup", "sticky_food", "laundry", "cleanup", "craft"]


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
    syrup = f["syrup_cfg"]
    theme = f["theme"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a Tall Tale style story for a 3-to-5-year-old set in a laundry room. '
        f'Use the words "ingenious", "syrup", and "paint-gerund", and build suspense around a craft mistake.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a near-miss story where {a.id} has an ingenious idea to use {syrup.label} on a banner, but {b.id} warns that it could spoil {target.label}, and the children ask a grown-up for help instead.",
            f"Write a gentle suspense story in a laundry room where a big sibling talks a younger child out of using syrup for art, and the ending proves they found the right paint.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a suspenseful Tall Tale where {a.id} pours {syrup.label} during a laundry-room craft, the spill creeps toward {target.label}, and a calm grown-up saves the day.",
            f"Write a child-facing story where clean laundry is almost ruined by an ingenious but bad art idea, and the ending shows a better way to finish the banner.",
        ]
    return [
        base,
        f"Tell a cautionary Tall Tale where {a.id} uses {syrup.label} on a cloth project, the sticky spill reaches {target.label}, and everyone learns why syrup is not paint.",
        f"Write a suspense story in a laundry room with a sad-but-safe ending: the clean laundry is spoiled, nobody is hurt, and the children remember the lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    syrup = f["syrup_cfg"]
    target = f["target_cfg"]
    fix = f["fix_cfg"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, working on a grand art project in the laundry room with {a.id}'s {parent.label_word} nearby in the house.",
        ),
        (
            "What were they trying to make?",
            f"They were trying to make {theme.mission.replace('to finish ', '')}. The laundry room felt huge and dramatic, which made the project seem even grander.",
        ),
        (
            f"Why did {a.id} want to use {syrup.label}?",
            f"{a.id} thought the syrup would make the banner shine more brightly. It sounded ingenious at first, but {syrup.label} was sticky food, not craft paint.",
        ),
        (
            f"Why was {b.id} worried?",
            f"{b.id} was worried the syrup would slide off the cloth and reach {target.the}. If that happened, the clean laundry would turn sticky and would need washing again.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and put the syrup back, so no spill happened at all. Then the children asked {parent.label_word} for the right art supplies instead.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with proper washable paint and a finished banner. The ending image shows the children happily admiring their work instead of cleaning a sticky mess.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did {a.id}'s {parent.label_word} save the laundry?",
                f"{parent.label_word.capitalize()} {fix.qa_text}. That worked because the grown-up stopped the syrup before it could soak into the cloth.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that an ingenious idea still has to fit the job. Syrup can look shiny, but art needs proper paint if you want a good ending.",
            )
        )
    else:
        qa.append(
            (
                "Did the sticky spill reach the laundry?",
                f"Yes. The syrup touched {target.clean_name}, so it was no longer clean and had to be washed again. That is why the ending felt sad, even though everyone was safe.",
            )
        )
        qa.append(
            (
                "What did the children learn at the end?",
                f"They learned that clever-sounding ideas can still make trouble when the material is wrong. Syrup belongs on food, not on a cloth project near clean laundry.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["syrup_cfg"].tags) | set(f["target_cfg"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def tell(
    theme: Theme,
    syrup: Syrup,
    target: Target,
    fix: Fix,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(
        Entity(
            id="room",
            type="room",
            label="laundry room",
            attrs={"setting": "laundry room"},
        )
    )
    syrup_ent = world.add(
        Entity(
            id="syrup",
            type="syrup",
            label=syrup.label,
            sticky_source=True,
        )
    )
    target_ent = world.add(
        Entity(
            id="target",
            type="laundry",
            label=target.label,
            cloth=target.absorbent,
            clean_laundry=target.near_laundry,
        )
    )
    paint_ent = world.add(
        Entity(
            id="paint",
            type="paint",
            label="washable poster paint",
            proper_paint=True,
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme)
    need_shine(world, a, b)

    world.para()
    tempt(world, a, syrup)
    warn(world, b, a, syrup, target, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    severity = 0
    saved = True

    if averted:
        back_down(world, a, b, syrup, parent)
        world.para()
        proper_fix(world, parent, a, b, theme)
    else:
        defy(world, a, b, syrup)
        world.para()
        spill(world, syrup_ent, syrup, target)
        suspense(world, b, target)
        severity = spill_severity(syrup, target, delay)
        target_ent.meters["severity"] = float(severity)
        saved = is_saved(fix, syrup, target, delay)
        world.para()
        if saved:
            rescue(world, parent, fix, target_ent, target)
            lesson(world, parent, a, b, syrup)
            world.para()
            proper_fix(world, parent, a, b, theme)
        else:
            rescue_fail(world, parent, fix, target_ent, target)
            sad_lesson(world, parent, a, b, target, syrup)

    outcome = "averted" if averted else ("contained" if saved else "spoiled")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        syrup_cfg=syrup,
        target_cfg=target,
        target=target_ent,
        fix_cfg=fix,
        relation=relation,
        ignited=False,
        outcome=outcome,
        severity=severity,
        delay=delay,
        laundry_spoiled=target_ent.meters["sticky"] >= THRESHOLD,
    )
    return world


CURATED = [
    StoryParams(
        theme="parade",
        syrup="maple",
        target="towels",
        fix="towel_dam",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="circus",
        syrup="berry",
        target="shirts",
        fix="tray_swap",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="river",
        syrup="maple",
        target="shirts",
        fix="rinse_sink",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="mother",
        trait="curious",
        delay=2,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
]


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
        flags = [n for n, on in (("cloth", e.cloth), ("clean_laundry", e.clean_laundry),
                                 ("sticky_source", e.sticky_source), ("proper_paint", e.proper_paint)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(syrup: Syrup, target: Target) -> str:
    if not target.absorbent:
        return (
            f"(No story: {target.the} is not cloth, so syrup would not spoil clean laundry there. "
            f"Pick towels, shirts, or socks instead.)"
        )
    if not target.near_laundry:
        return (
            f"(No story: {target.the} is not a nearby clean-laundry target, so the suspense about saving clean washing falls away.)"
        )
    return "(No story: this syrup and target do not make a reasonable sticky-laundry problem.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_saved(FIXES[params.fix], SYRUPS[params.syrup], TARGETS[params.target], params.delay) else "spoiled"


ASP_RULES = r"""
hazard(S, T) :- syrup(S), target(T), sticky_source(S), absorbent(T), near_laundry(T).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(Th, S, T) :- theme(Th), syrup(S), target(T), hazard(S, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(St + Tv + D) :- chosen_syrup(S), sticky(S, St), chosen_target(T), target_severity(T, Tv), delay(D).
fix_power(P) :- chosen_fix(F), power(F, P).
contained :- fix_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spoiled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for syrup_id, syrup in SYRUPS.items():
        lines.append(asp.fact("syrup", syrup_id))
        if syrup.sticky_source:
            lines.append(asp.fact("sticky_source", syrup_id))
        lines.append(asp.fact("sticky", syrup_id, syrup.sticky))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.absorbent:
            lines.append(asp.fact("absorbent", target_id))
        if target.near_laundry:
            lines.append(asp.fact("near_laundry", target_id))
        lines.append(asp.fact("target_severity", target_id, target.severity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
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


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_syrup", params.syrup),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
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
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sense = set(asp_sensible_fixes())
    p_sense = {f.id for f in sensible_fixes()}
    if c_sense == p_sense:
        print(f"OK: sensible fixes match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an ingenious syrup art idea in a suspenseful laundry room Tall Tale."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--syrup", choices=SYRUPS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None and not TARGETS[args.target].absorbent:
        syrup = SYRUPS[args.syrup] if args.syrup else next(iter(SYRUPS.values()))
        raise StoryError(explain_rejection(syrup, TARGETS[args.target]))
    if args.syrup and args.target:
        syrup = SYRUPS[args.syrup]
        target = TARGETS[args.target]
        if not hazard_at_risk(syrup, target):
            raise StoryError(explain_rejection(syrup, target))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.syrup is None or combo[1] == args.syrup)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, syrup_id, target_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme_id,
        syrup=syrup_id,
        target=target_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.syrup not in SYRUPS:
        raise StoryError(f"(Unknown syrup: {params.syrup})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    syrup = SYRUPS[params.syrup]
    target = TARGETS[params.target]
    fix = FIXES[params.fix]

    if not hazard_at_risk(syrup, target):
        raise StoryError(explain_rejection(syrup, target))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        THEMES[params.theme],
        syrup,
        target,
        fix,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, syrup, target) combos:\n")
        for theme_id, syrup_id, target_id in combos:
            print(f"  {theme_id:8} {syrup_id:8} {target_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.syrup} near {p.target} ({p.theme}, {p.fix}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
