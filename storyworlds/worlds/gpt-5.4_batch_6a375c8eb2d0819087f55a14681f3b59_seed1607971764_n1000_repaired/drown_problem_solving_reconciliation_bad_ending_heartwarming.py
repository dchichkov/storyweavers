#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drown_problem_solving_reconciliation_bad_ending_heartwarming.py
===========================================================================================

A standalone storyworld about two children by the water: they quarrel over a
floating toy, one child reaches too far and slips into deep water, a grown-up
solves the emergency as sensibly as possible, and the children reconcile.

The world keeps a tight common-sense gate:

- the place must really be risky water,
- the prize must be something a child would try to get back from the water,
- the rescue method must be sensible,
- the ending depends on whether the chosen method is strong enough for the
  place and delay.

The stories stay child-facing and heartwarming even when the ending is sad:
nobody is abandoned, the grown-ups help, and the ending image shows what the
children learned about water safety and making up after a quarrel.
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "gentle", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    floats: bool = False
    rescue_tool: bool = False
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    edge: str
    water: str
    opening: str
    ending: str
    severity: int
    drift_line: str
    warning: str
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
class Prize:
    id: str
    label: str
    phrase: str
    drift: str
    goodbye: str
    floaty: bool = True
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
class Rescue:
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


@dataclass
class StoryParams:
    place: str
    prize: str
    rescue: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    friend_age: int = 5
    relation: str = "siblings"
    trust: int = 6
    keepsake: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("instigator")
    place = world.entities.get("place")
    prize = world.entities.get("prize")
    if not child or not place or not prize:
        return out
    if child.meters["leaning"] < THRESHOLD:
        return out
    if prize.meters["drifting"] < THRESHOLD:
        return out
    sig = ("fall", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["in_water"] += 1
    child.meters["cold"] += 1
    place.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__splash__")
    return out


def _r_drown_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("instigator")
    place = world.entities.get("place")
    if not child or not place:
        return out
    if child.meters["in_water"] < THRESHOLD:
        return out
    sig = ("drown_risk", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["drown_risk"] += 1
    place.meters["danger"] += 1
    out.append("__risk__")
    return out


CAUSAL_RULES = [
    Rule(name="fall", tag="physical", apply=_r_fall),
    Rule(name="drown_risk", tag="physical", apply=_r_drown_risk),
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


PLACES = {
    "pond": Place(
        id="pond",
        label="the duck pond",
        edge="the little wooden dock",
        water="the green pond water",
        opening="On a soft afternoon, the pond looked silver under the clouds.",
        ending="After that, they stayed on the grass and watched the ducks from a safer place.",
        severity=2,
        drift_line="The water nudged things away in slow circles.",
        warning="The pond looked calm, but the drop beside the dock was deeper than it seemed.",
        tags={"pond", "water", "drown"},
    ),
    "creek": Place(
        id="creek",
        label="the creek",
        edge="the flat stepping stones",
        water="the quick brown creek",
        opening="On a cool afternoon, the creek sang over the stones.",
        ending="After that, they waved to the bright water from far back on the bank.",
        severity=3,
        drift_line="The current tugged drifting things faster and faster downstream.",
        warning="The creek was pretty, but the water moved hard enough to pull at small legs.",
        tags={"creek", "water", "drown"},
    ),
    "marina": Place(
        id="marina",
        label="the little marina",
        edge="the low floating dock",
        water="the dark harbor water",
        opening="On a breezy afternoon, ropes tapped the dock and little boats bobbed nearby.",
        ending="After that, they sat on a bench with dry towels and watched the boats from land.",
        severity=3,
        drift_line="The harbor water slid under the dock and carried small things into the shadows.",
        warning="The dock rocked underfoot, and the water beside it was cold and deep.",
        tags={"marina", "water", "drown"},
    ),
    "fountain": Place(
        id="fountain",
        label="the shallow fountain",
        edge="the low stone rim",
        water="the splashing fountain water",
        opening="On a bright afternoon, the fountain sprayed little sparkles into the air.",
        ending="After that, they stood nearby and listened to the water sing.",
        severity=0,
        drift_line="The water swirled in place instead of carrying things away.",
        warning="It was noisy and wet, but it was not the kind of deep water where someone might drown.",
        tags={"fountain", "water"},
    ),
}

PRIZES = {
    "boat": Prize(
        id="boat",
        label="toy boat",
        phrase="a red toy boat with a painted blue stripe",
        drift="bobbed away from the dock",
        goodbye="The little boat tipped once, turned, and slipped out where nobody could reach it.",
        floaty=True,
        tags={"boat", "toy", "water"},
    ),
    "duck": Prize(
        id="duck",
        label="rubber duck",
        phrase="a yellow rubber duck that squeaked when squeezed",
        drift="wobbled away on the ripples",
        goodbye="The duck twirled under the dock and was gone from sight.",
        floaty=True,
        tags={"duck", "toy", "water"},
    ),
    "paper_boat": Prize(
        id="paper_boat",
        label="paper boat",
        phrase="a folded paper boat covered in crayon stars",
        drift="sailed away with a tiny proud tilt",
        goodbye="The paper boat sagged, filled, and melted back into the water.",
        floaty=True,
        tags={"paper_boat", "toy", "water"},
    ),
    "stone": Prize(
        id="stone",
        label="smooth stone",
        phrase="a smooth gray stone from the path",
        drift="dropped straight down with a plunk",
        goodbye="The stone sank at once and stayed on the bottom.",
        floaty=False,
        tags={"stone"},
    ),
}

RESCUES = {
    "life_ring": Rescue(
        id="life_ring",
        sense=3,
        power=4,
        text="caught the bright life ring from the hook, tossed it past {child}, and pulled {obj} back to the dock",
        fail="threw the life ring, but the current swung it wide and it took too long to pull close",
        qa_text="used the life ring to pull {child} back to the edge",
        tags={"life_ring", "rescue", "water"},
    ),
    "reach_pole": Rescue(
        id="reach_pole",
        sense=3,
        power=3,
        text="lay flat on the dock, stretched out a long reach pole, and told {child} to grab it with both hands",
        fail="stretched out the reach pole, but {child} drifted just beyond it before a helper arrived",
        qa_text="reached out a long pole and pulled {child} to safety",
        tags={"reach_pole", "rescue", "water"},
    ),
    "rope": Rescue(
        id="rope",
        sense=2,
        power=2,
        text="snatched the rope from a post, looped it toward {child}, and hauled {obj} in inch by inch",
        fail="threw the rope, but it splashed short while the water kept tugging {obj} away",
        qa_text="threw a rope and hauled {child} back in",
        tags={"rope", "rescue", "water"},
    ),
    "jump_in": Rescue(
        id="jump_in",
        sense=1,
        power=1,
        text="jumped in after {child} and splashed through the cold water",
        fail="jumped in after {child}, but only made the panic bigger",
        qa_text="jumped into the water after {child}",
        tags={"jump_in", "water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "gentle", "thoughtful", "steady", "curious", "brave"]
KEEPSAKES = ["seashell bracelet", "small knitted scarf", "soft blue cap", "tiny lucky bell"]


def hazard_at_risk(place: Place, prize: Prize) -> bool:
    return place.severity > 0 and prize.floaty


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def danger_severity(place: Place, delay: int) -> int:
    return place.severity + delay


def is_contained(rescue: Rescue, place: Place, delay: int) -> bool:
    return rescue.power >= danger_severity(place, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, friend_age: int, trait: str) -> bool:
    friend_older = relation == "siblings" and friend_age > instigator_age
    authority = initial_care(trait) + 1.0 + (3.0 if friend_older else 0.0)
    return friend_older and authority > BOLDNESS_INIT


def predict_fall(world: World) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    prize = sim.get("prize")
    child.meters["leaning"] += 1
    prize.meters["drifting"] += 1
    propagate(sim, narrate=False)
    return {
        "in_water": child.meters["in_water"] >= THRESHOLD,
        "danger": sim.get("place").meters["danger"],
        "drown_risk": child.meters["drown_risk"] >= THRESHOLD,
    }


def opening_scene(world: World, a: Entity, b: Entity, place: Place, prize: Prize) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(place.opening)
    world.say(
        f"{a.id} and {b.id} took turns setting {prize.phrase} on the water beside {place.edge}. "
        f"{place.drift_line}"
    )


def quarrel(world: World, a: Entity, b: Entity, prize: Prize) -> None:
    a.memes["grumpiness"] += 1
    b.memes["hurt"] += 1
    world.say(
        f'"My turn again," {a.id} said, catching {prize.label} before {b.id} could reach it.'
    )
    world.say(
        f'{b.id} frowned. "You promised we would share." The sweet game went crooked in one small minute.'
    )


def drift_off(world: World, a: Entity, prize: Prize) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["drifting"] += 1
    world.say(
        f"In the middle of their cross voices, {prize.label} slipped free, {prize.drift}, and the children both gasped."
    )
    a.memes["alarm"] += 1


def warn(world: World, b: Entity, a: Entity, place: Place, parent: Entity) -> None:
    pred = predict_fall(world)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["care"] += 1
    extra = " You could fall in and drown." if pred["drown_risk"] else " You could fall in."
    world.say(
        f'{b.id} grabbed for {a.id}\'s sleeve. "Wait," {b.pronoun()} said. '
        f'"{place.warning}{extra} Let {parent.label_word} help."'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I can get it," {a.id} said, sounding bigger than {a.pronoun()} really felt. '
            f"Because {a.id} was the older one, {b.id} froze for a breath instead of pulling harder."
        )
    else:
        world.say(f'"I can get it," {a.id} said, and reached farther than was safe.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, prize: Prize, place: Place) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["grumpiness"] = 0.0
    b.memes["hurt"] = 0.0
    world.say(
        f'{a.id} looked at the dark water, then at {b.id}\'s worried face, and stopped. '
        f'"You were right," {a.pronoun()} whispered.'
    )
    world.say(
        f"They called for {parent.label_word}, who fetched the dock hook and drew the {prize.label} back without anyone leaning over the edge."
    )
    world.say(
        f'{a.id} gave {b.id} the next turn, and the sharp feeling between them softened.'
    )
    world.say(place.ending)


def slip(world: World, a: Entity, prize: Prize, place: Place) -> None:
    child = world.get("instigator")
    prize_ent = world.get("prize")
    child.meters["leaning"] += 1
    prize_ent.meters["drifting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} stretched after the {prize.label}. One shoe skidded on wet wood, and with a splash {a.pronoun()} went into {place.water}."
    )
    world.say(
        f"For one awful moment, {a.pronoun()} came up sputtering and could not find the dock again."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}! Help! {b.id} cried. "{world.get("instigator").id} fell in!"')


def rescue_success(world: World, parent: Entity, rescue: Rescue, child: Entity) -> None:
    child.meters["in_water"] = 0.0
    child.meters["drown_risk"] = 0.0
    world.get("place").meters["danger"] = 0.0
    child.meters["cold"] += 1
    body = rescue.text.format(child=child.id, obj=child.pronoun("object"))
    world.say(
        f"{parent.label_word.capitalize()} was moving before the echo was gone. {parent.pronoun().capitalize()} {body}."
    )
    world.say(
        f"Soon {child.id} was coughing on the boards, wrapped in shaking breaths but out of the water."
    )


def rescue_fail(world: World, parent: Entity, rescue: Rescue, child: Entity, prize: Prize) -> None:
    child.meters["in_water"] = 0.0
    child.meters["drown_risk"] = 0.0
    child.meters["cold"] += 2
    child.meters["needs_doctor"] += 1
    world.get("place").meters["danger"] = 0.0
    body = rescue.fail.format(child=child.id, obj=child.pronoun("object"))
    world.say(
        f"{parent.label_word.capitalize()} ran to the edge and {body}."
    )
    world.say(
        f"A dock worker heard the shouting, dropped to one knee with another hook, and together the grown-ups finally dragged {child.id} out."
    )
    world.say(prize.goodbye)


def comfort_and_reconcile(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    a.memes["grumpiness"] = 0.0
    b.memes["hurt"] = 0.0
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    keepsake = b.attrs.get("keepsake", "")
    world.say(
        f'{parent.label_word.capitalize()} knelt and held both children close. "{a.id}, I am so glad you are here," {parent.pronoun()} said. '
        f'"And {b.id}, thank you for calling me so fast."'
    )
    tail = ""
    if keepsake:
        tail = f" {b.id} pressed {b.pronoun('possessive')} {keepsake} into {a.id}'s cold hand for a moment, just to help {a.pronoun('object')} stop trembling."
    world.say(
        f'{a.id} turned to {b.id}. "I was mad, and I did not listen. I am sorry." '
        f'{b.id} nodded. "I was hurt, but I still wanted to help you."{tail}'
    )


def bright_ending(world: World, a: Entity, b: Entity, parent: Entity, prize: Prize, place: Place) -> None:
    for kid in (a, b):
        kid.memes["safety"] += 1
    world.say(
        f'"Nobody reaches into deep water," {parent.label_word} said softly. "If something drifts away, we solve it with a grown-up and a tool."'
    )
    world.say(
        f"Later, with dry sleeves and calmer hearts, they tied a little string to the {prize.label} before setting it near the edge again."
    )
    world.say(
        f"This time they took turns kindly, and when the toy tugged away, they pulled it back together. {place.ending}"
    )


def sad_ending(world: World, a: Entity, b: Entity, parent: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'"A child can drown in water like this," {parent.label_word} said, wrapping another towel around {a.id}. '
        f'"That is why we never lean out after a drifting toy."'
    )
    world.say(
        f"They went home early, quiet and tired. At the clinic, the doctor listened to {a.id}'s breathing and said rest would have to be the rest of the day's adventure."
    )
    world.say(
        f"From the car window, the water glimmered behind them. The toy was gone, the outing was over, and yet {a.id} and {b.id} rode home leaning gently against each other."
    )


def tell(
    place: Place,
    prize: Prize,
    rescue: Rescue,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    friend: str = "Lily",
    friend_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    friend_age: int = 5,
    relation: str = "siblings",
    trust: int = 6,
    keepsake: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation, "keepsake": keepsake},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="prize", type="toy", label=prize.label, phrase=prize.phrase, floats=prize.floaty))
    world.add(Entity(id="tool", type="tool", label=rescue.id, rescue_tool=True))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["care"] = initial_care(trait)
    b.memes["trust"] = float(trust)
    world.facts["relation"] = relation

    opening_scene(world, a, b, place, prize)
    quarrel(world, a, b, prize)

    world.para()
    drift_off(world, a, prize)
    warn(world, b, a, place, parent)

    averted = would_avert(relation, instigator_age, friend_age, trait)
    if averted:
        back_down(world, a, b, parent, prize, place)
        severity = 0
        contained = True
    else:
        defy(world, a, b)
        world.para()
        slip(world, a, prize, place)
        alarm(world, b, parent)

        severity = danger_severity(place, delay)
        world.get("instigator").meters["severity"] = float(severity)
        contained = is_contained(rescue, place, delay)

        world.para()
        if contained:
            rescue_success(world, parent, rescue, a)
            comfort_and_reconcile(world, a, b, parent)
            world.para()
            bright_ending(world, a, b, parent, prize, place)
        else:
            rescue_fail(world, parent, rescue, a, prize)
            comfort_and_reconcile(world, a, b, parent)
            world.para()
            sad_ending(world, a, b, parent, place)

    outcome = "averted" if averted else ("rescued" if contained else "bad")
    world.facts.update(
        place_cfg=place,
        prize_cfg=prize,
        rescue_cfg=rescue,
        instigator=a,
        friend=b,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        fell_in=world.get("instigator").meters["cold"] >= THRESHOLD or not averted,
        apologized=a.memes["apology"] >= THRESHOLD or averted,
    )
    return world


KNOWLEDGE = {
    "drown": [(
        "What does drown mean?",
        "Drown means a person or animal cannot get enough air because they are under water or water is filling their mouth and nose. It is why deep water is never a place for games without careful grown-up help."
    )],
    "pond": [(
        "Why can a pond be dangerous even if it looks calm?",
        "A pond can have a sudden deep edge, slippery boards, and cold water. Calm-looking water can still be a place where someone could drown."
    )],
    "creek": [(
        "Why is a creek dangerous?",
        "A creek can move faster than it looks. Running water can pull at your legs and make it hard to climb back out."
    )],
    "marina": [(
        "Why should children be careful on a dock?",
        "A dock can rock and get slippery. The water beside it is often deep, so a fall can turn scary very quickly."
    )],
    "life_ring": [(
        "What is a life ring for?",
        "A life ring is a floating rescue tool. A grown-up can throw it to someone in the water so they can hold on and be pulled back."
    )],
    "reach_pole": [(
        "Why is a long pole safer than leaning over the water?",
        "A long pole lets a helper reach someone from solid ground. It solves the problem without putting another person in danger."
    )],
    "rope": [(
        "How can a rope help in a water emergency?",
        "A rope gives the person in the water something to grab. Then a grown-up can pull from a safer place."
    )],
    "boat": [(
        "Why do toys drift away on water?",
        "Water keeps moving even when it looks gentle. A floating toy can slide farther away every second."
    )],
    "duck": [(
        "Why can a floating toy still be unsafe to chase?",
        "Because the toy may float, but the child does not float the same safe way. Reaching for it can make someone slip toward deep water."
    )],
    "paper_boat": [(
        "Why does a paper boat not last long in water?",
        "Paper soaks up water and turns soft. After a while, the folds sag and the boat falls apart."
    )],
}
KNOWLEDGE_ORDER = [
    "drown", "pond", "creek", "marina",
    "life_ring", "reach_pole", "rope",
    "boat", "duck", "paper_boat",
]


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
    b = f["friend"]
    place = f["place_cfg"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    if outcome == "bad":
        return [
            f'Write a heartwarming but sad story for a 3-to-5-year-old that includes the word "drown". Two children quarrel beside {place.label}, one falls into the water while trying to get a {prize.label}, and they reconcile before going home early.',
            f"Tell a gentle cautionary story where {a.label} and {b.label} fight over a floating toy, a grown-up solves the emergency, and the ending is bad because the day is lost and the toy is gone.",
            f'Write a story about problem solving and reconciliation near deep water. Include a warning that a child could drown, but keep the tone loving and child-facing.',
        ]
    if outcome == "averted":
        return [
            f'Write a heartwarming safety story that includes the word "drown". Two children by {place.label} start to quarrel over a drifting {prize.label}, but one child listens to a warning and nobody falls in.',
            f"Tell a gentle reconciliation story where {a.label} stops before reaching into dangerous water and the children learn to ask a grown-up for help.",
            f'Write a small story about problem solving by the water, with a safe ending and children making up after an argument.',
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "drown". Two children quarrel by {place.label}, one slips into the water while chasing a {prize.label}, and a grown-up rescues the child safely.',
        f"Tell a gentle story of problem solving and reconciliation where {a.label} falls in after not listening, then apologizes to {b.label} after the rescue.",
        f'Write a water-safety story with a clear beginning, a scary middle, and a warm ending where the children learn to solve the problem with a tool and a grown-up.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    parent = f["parent"]
    place = f["place_cfg"]
    prize = f["prize_cfg"]
    rescue = f["rescue_cfg"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, and their {parent.label_word} by {place.label}. The story follows their argument, the water danger, and the way they make up again."
        ),
        (
            "What started the trouble?",
            f"The trouble started when the children stopped sharing {prize.phrase} kindly and began to quarrel. Then the toy drifted away, which made the unsafe idea feel urgent."
        ),
        (
            f"Why did {b.label} tell {a.label} to wait?",
            f"{b.label} knew the water by {place.edge} was dangerous and said {a.label} could fall in. {place.warning}."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What solved the problem before anyone got hurt?",
            f"{a.label} listened at last, and they called for their {parent.label_word} instead of leaning over the water. A grown-up used a tool to get the toy back, which solved the problem safely."
        ))
        qa.append((
            "How did the children reconcile?",
            f"They softened toward each other after the warning was heard and the danger passed. Sharing the next turn showed that the quarrel was over."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the children staying back from the water and playing more gently. The ending proves they learned not to chase a drifting toy by themselves."
        ))
    elif f["outcome"] == "rescued":
        body = rescue.qa_text.format(child=a.label)
        qa.append((
            f"How did the grown-up save {a.label}?",
            f"Their {parent.label_word} {body}. That worked because the grown-up solved the problem from solid ground instead of reaching in blindly."
        ))
        qa.append((
            f"What did {a.label} say after the rescue?",
            f"{a.label} admitted being angry and not listening, and said sorry to {b.label}. The apology mattered because the danger began in the middle of their quarrel."
        ))
        qa.append((
            "What changed by the end?",
            f"By the end, the children were kind to each other again and used a safer plan with the toy. The warm ending shows both safety and reconciliation."
        ))
    else:
        qa.append((
            "Was the ending happy or sad?",
            f"It was sad. {a.label} was finally safe, but the toy was gone, the outing ended early, and they had to spend the rest of the day resting after the scare."
        ))
        qa.append((
            f"Did the children still reconcile even with the bad ending?",
            f"Yes. {a.label} apologized for not listening, and {b.label} answered with care instead of anger. Their making up matters because love stayed even after the frightening mistake."
        ))
        qa.append((
            f"Why did the grown-up say someone could drown there?",
            f"The water beside {place.edge} was deep and dangerous enough that a fall could become very serious. The warning explains why drifting toys are never worth chasing alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["place_cfg"].tags) | set(f["prize_cfg"].tags) | set(f["rescue_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for prize_id, prize in PRIZES.items():
            if hazard_at_risk(place, prize):
                combos.append((place_id, prize_id))
    return combos


CURATED = [
    StoryParams(
        place="pond",
        prize="boat",
        rescue="reach_pole",
        instigator="Tom",
        instigator_gender="boy",
        friend="Lily",
        friend_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        friend_age=4,
        relation="siblings",
        trust=7,
        keepsake="small knitted scarf",
    ),
    StoryParams(
        place="creek",
        prize="duck",
        rescue="life_ring",
        instigator="Mia",
        instigator_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        friend_age=7,
        relation="siblings",
        trust=4,
        keepsake="tiny lucky bell",
    ),
    StoryParams(
        place="marina",
        prize="paper_boat",
        rescue="rope",
        instigator="Sam",
        instigator_gender="boy",
        friend="Nora",
        friend_gender="girl",
        parent="mother",
        trait="gentle",
        delay=1,
        instigator_age=6,
        friend_age=5,
        relation="friends",
        trust=3,
        keepsake="seashell bracelet",
    ),
]


def explain_rejection(place: Place, prize: Prize) -> str:
    if place.severity <= 0:
        return (
            f"(No story: {place.label} is splashy but not deep or risky enough for a real drown warning. "
            f"Pick a place with deeper moving water, like the pond, creek, or marina.)"
        )
    if not prize.floaty:
        return (
            f"(No story: a {prize.label} would not drift away on top of the water, so the reaching problem does not honestly happen here. "
            f"Pick a floating toy like a boat, rubber duck, or paper boat.)"
        )
    return "(No story: this place and prize do not make a reasonable water-danger story.)"


def explain_rescue(rescue_id: str) -> str:
    rescue = RESCUES[rescue_id]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). A safer water story should prefer reaching tools and flotation. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.friend_age, params.trait):
        return "averted"
    return "rescued" if is_contained(RESCUES[params.rescue], PLACES[params.place], params.delay) else "bad"


ASP_RULES = r"""
hazard(P, Pr) :- place(P), prize(Pr), risky(P), floaty(Pr).
sensible(R)   :- rescue(R), sense(R, S), sense_min(M), S >= M.
valid(P, Pr)  :- hazard(P, Pr).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5)   :- trait(T), careful_now(T).
init_care(3)   :- trait(T), not careful_now(T).
friend_older   :- relation(siblings), instigator_age(IA), friend_age(FA), FA > IA.
bonus(3)       :- friend_older.
bonus(0)       :- not friend_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted        :- friend_older, authority(A), boldness_init(BL), A > BL.

severity(V + D) :- chosen_place(P), place_severity(P, V), delay(D).
rescue_power(Pw) :- chosen_rescue(R), power(R, Pw).
contained      :- rescue_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(rescued) :- not averted, contained.
outcome(bad)     :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_severity", place_id, place.severity))
        if place.severity > 0:
            lines.append(asp.fact("risky", place_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        if prize.floaty:
            lines.append(asp.fact("floaty", prize_id))
    for rescue_id, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("sense", rescue_id, rescue.sense))
        lines.append(asp.fact("power", rescue_id, rescue.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: quarrel by deep water, a drifting toy, a rescue, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra delay before help reaches the child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible place/prize combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.prize:
        place = PLACES[args.place]
        prize = PRIZES[args.prize]
        if not hazard_at_risk(place, prize):
            raise StoryError(explain_rejection(place, prize))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.prize is None or combo[1] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prize_id = rng.choice(sorted(combos))
    rescue_id = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    instigator, instigator_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, friend_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    keepsake = rng.choice(KEEPSAKES + ["", ""])
    return StoryParams(
        place=place_id,
        prize=prize_id,
        rescue=rescue_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        friend_age=friend_age,
        relation=relation,
        trust=trust,
        keepsake=keepsake,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    place = PLACES[params.place]
    prize = PRIZES[params.prize]
    rescue = RESCUES[params.rescue]
    if not hazard_at_risk(place, prize):
        raise StoryError(explain_rejection(place, prize))
    if rescue.sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        place=place,
        prize=prize,
        rescue=rescue,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        friend_age=params.friend_age,
        relation=params.relation,
        trust=params.trust,
        keepsake=params.keepsake,
    )

    world.facts["instigator"].label = params.instigator
    world.facts["friend"].label = params.friend

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("friend", params.friend),
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


def asp_verify() -> int:
    rc = 0

    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    python_sensible = {r.id for r in sensible_rescues()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible rescues match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible rescues: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prize) combos:\n")
        for place, prize in combos:
            print(f"  {place:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.instigator} & {p.friend}: {p.prize} at {p.place} ({p.rescue}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
