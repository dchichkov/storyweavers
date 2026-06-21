#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py
===================================================================

A standalone storyworld for a small kitchen fable about impatience, pride, and
asking for help. A little animal wants a treat from a high kitchen shelf. A
wiser companion warns that proud haste makes a mess, and may even assure the
hero that patient help will come. If the hero listens, the kitchen stays tidy.
If not, a wobbling climb sends a clatter and an echo through the pans, and the
ending depends on whether a sensible grown-up response arrives in time.

The world is deliberately narrow and state-driven:
- physical meters track wobble, spill, stickiness, and reach
- emotional memes track hunger, trust, pride, caution, shame, relief, and wisdom
- prose changes with the simulated outcome: averted, contained, or spilled

Run it
------
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py --treat honey_jar --perch chair
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py --perch spoon_tower
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py --response leap_catch
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py --all
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/assure_echo_kitchen_moral_value_fable.py --verify
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
PRIDE_INIT = 6.0
TRUST_AVERT = 7


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
    reach: int = 0
    fragile: int = 0
    # two axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "cook":
            return "cook"
        return self.label or self.type
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
class Treat:
    id: str
    label: str
    phrase: str
    shelf: int
    fragility: int
    spill_word: str
    ending_image: str
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
class Perch:
    id: str
    label: str
    phrase: str
    reach: int
    stability: int
    sense: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
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
    perch = world.get("perch")
    prize = world.get("treat")
    if perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("tip", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["tilting"] += 1
    world.get("kitchen").meters["noise"] += 1
    for kid in [world.get("seeker"), world.get("advisor")]:
        kid.memes["alarm"] += 1
    out.append("__tilt__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("treat")
    if prize.meters["tilting"] < THRESHOLD:
        return out
    sig = ("spill", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["spilled"] += 1
    world.get("floor").meters["sticky"] += 1
    world.get("kitchen").meters["mess"] += 1
    world.get("seeker").memes["shame"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def can_reach(treat: Treat, perch: Perch) -> bool:
    return perch.reach >= treat.shelf


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def wobble_risk(perch: Perch) -> int:
    return max(0, 3 - perch.stability)


def severity_of(treat: Treat, perch: Perch) -> int:
    return treat.fragility + wobble_risk(perch)


def contained_by(response: Response, treat: Treat, perch: Perch) -> bool:
    return response.power >= severity_of(treat, perch)


def would_avert(relation: str, advisor_age: int, seeker_age: int, trust: int) -> bool:
    return relation == "siblings" and advisor_age > seeker_age and trust >= TRUST_AVERT


def predict_mess(world: World) -> dict:
    sim = world.copy()
    perch = sim.get("perch")
    prize = sim.get("treat")
    _climb(sim, perch, prize, narrate=False)
    return {
        "spilled": prize.meters["spilled"] >= THRESHOLD,
        "sticky": sim.get("floor").meters["sticky"] >= THRESHOLD,
        "severity": int(severity_of(TREATS[sim.facts["treat_cfg"].id], PERCHES[sim.facts["perch_cfg"].id])),
    }


def _climb(world: World, perch_ent: Entity, prize_ent: Entity, narrate: bool = True) -> None:
    perch_ent.meters["used"] += 1
    wobble = max(0, 3 - perch_ent.reach)  # quiet default, overwritten below
    wobble = max(0, 3 - PERCHES[world.facts["perch_cfg"].id].stability)
    perch_ent.meters["wobble"] += wobble
    prize_ent.meters["reached_for"] += 1
    propagate(world, narrate=narrate)


def kitchen_setup(world: World, seeker: Entity, advisor: Entity, treat: Treat) -> None:
    seeker.memes["hunger"] += 1
    seeker.memes["desire"] += 1
    advisor.memes["care"] += 1
    world.say(
        f"In a bright kitchen where copper pans hung like little suns, "
        f"{seeker.id} the {seeker.type} smelled {treat.phrase} resting on the high shelf."
    )
    world.say(
        f"{advisor.id} the {advisor.type} stood nearby, listening to the room hum softly "
        f"around the kettle and the clock."
    )


def desire(world: World, seeker: Entity, treat: Treat, perch: Perch) -> None:
    seeker.memes["pride"] += 1
    world.say(
        f'"If I climb onto {perch.phrase}, I can reach the {treat.label} myself," '
        f"{seeker.id} said, with bright eyes and a proud little tail."
    )


def warning(world: World, advisor: Entity, seeker: Entity, treat: Treat, perch: Perch) -> None:
    pred = predict_mess(world)
    world.facts["predicted_spill"] = pred["spilled"]
    world.facts["predicted_severity"] = pred["severity"]
    advisor.memes["caution"] += 1
    world.say(
        f'{advisor.id} shook {advisor.pronoun("possessive")} head. '
        f'"Friend, I assure you, a quick climb is not always a wise climb. '
        f'{perch.label.capitalize()} is a poor ladder for a high shelf, and the {treat.label} '
        f"may tumble before your paws ever taste it.\""
    )


def back_down(world: World, seeker: Entity, advisor: Entity, cook: Entity, treat: Treat, response: Response) -> None:
    seeker.memes["relief"] += 1
    seeker.memes["wisdom"] += 1
    advisor.memes["relief"] += 1
    world.say(
        f"{seeker.id} looked up at the shelf, then down at {advisor.id}, and pride grew smaller than sense."
    )
    world.say(
        f'Together they called for the cook, and soon the cook {response.text.replace("{treat}", treat.label)}.'
    )


def attempt(world: World, seeker: Entity, perch: Perch, treat: Treat) -> None:
    world.say(
        f"But {seeker.id} was sure swift paws could do what patient words could not. "
        f"{seeker.pronoun().capitalize()} scampered onto {perch.phrase} and stretched toward the {treat.label}."
    )
    _climb(world, world.get("perch"), world.get("treat"))
    if world.get("treat").meters["tilting"] >= THRESHOLD:
        world.say(
            f"The {perch.label} gave a twitch. A spoon rang against a pan, and the sharp sound sent an echo around the kitchen."
        )


def alarm(world: World, advisor: Entity, seeker: Entity, treat: Treat) -> None:
    if world.get("treat").meters["spilled"] >= THRESHOLD:
        world.say(
            f'"{seeker.id}, jump down!" cried {advisor.id}, as the {treat.label} tipped and {treat.spill_word} splashed toward the floor.'
        )


def rescue(world: World, cook: Entity, response: Response, treat: Treat) -> None:
    world.get("kitchen").meters["mess"] = 0.0
    world.get("floor").meters["sticky"] = 0.0
    world.get("treat").meters["spilled"] = 0.0
    world.say(
        f"The cook came at once and {response.text.replace('{treat}', treat.label)}."
    )
    world.say(
        f"Soon the danger was over, the shelf was set right, and the kitchen breathed quietly again."
    )


def lesson_good(world: World, cook: Entity, seeker: Entity, advisor: Entity, treat: Treat) -> None:
    seeker.memes["wisdom"] += 1
    seeker.memes["shame"] = 0.0
    seeker.memes["gratitude"] += 1
    advisor.memes["love"] += 1
    world.say(
        f'The cook knelt beside them and said, "A patient paw reaches farther than a proud one. '
        f'When help is near, wisdom is asking for it."'
    )
    world.say(
        f"{seeker.id} thanked {advisor.id}, and the two friends shared a small taste of the {treat.label} at the table."
    )


def rescue_fail(world: World, cook: Entity, response: Response, treat: Treat) -> None:
    world.get("kitchen").meters["mess"] += 1
    world.get("floor").meters["sticky"] += 1
    world.say(
        f"The cook hurried in and {response.fail.replace('{treat}', treat.label)}."
    )
    world.say(
        f"But the {treat.label} had already burst open, and sweetness spread in a broad sticky circle on the floorboards."
    )


def loss(world: World, seeker: Entity, advisor: Entity, treat: Treat) -> None:
    seeker.memes["wisdom"] += 1
    seeker.memes["shame"] += 1
    advisor.memes["pity"] += 1
    world.say(
        f"{seeker.id} stood still, licking nothing but sorrow from {seeker.pronoun('possessive')} whiskers, while {advisor.id} fetched a cloth."
    )
    world.say(
        f"The treat was gone for that day, and the bright kitchen smelled of {treat.spill_word} and a hard lesson."
    )


def ending(world: World, seeker: Entity, advisor: Entity, treat: Treat, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"Above them the pans gave back a gentle echo, as if the kitchen itself approved patient hearts."
        )
        world.say(
            "So it is in many homes: haste boasts, but patience dines."
        )
    elif outcome == "contained":
        world.say(
            f"On the clean shelf the {treat.label} glowed again, and in its shine {seeker.id} saw that calm help is sweeter than stolen hurry."
        )
        world.say(
            "Moral: Those who wait for wise help often keep both their reward and their peace."
        )
    else:
        world.say(
            f"Long after the floor was scrubbed, the memory of the clatter seemed to echo under the pans."
        )
        world.say(
            "Moral: Pride reaches quickly, but patience reaches safely."
        )


def tell(
    treat: Treat,
    perch: Perch,
    response: Response,
    seeker_name: str = "Pip",
    seeker_type: str = "mouse",
    seeker_gender: str = "boy",
    advisor_name: str = "Mina",
    advisor_type: str = "sparrow",
    advisor_gender: str = "girl",
    relation: str = "friends",
    seeker_age: int = 5,
    advisor_age: int = 6,
    trust: int = 7,
) -> World:
    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        role="seeker",
        age=seeker_age,
        attrs={"gender": seeker_gender, "relation": relation},
        label=seeker_type,
    ))
    advisor = world.add(Entity(
        id=advisor_name,
        kind="character",
        type=advisor_type,
        role="advisor",
        age=advisor_age,
        attrs={"gender": advisor_gender, "relation": relation},
        label=advisor_type,
    ))
    cook = world.add(Entity(
        id="Cook",
        kind="character",
        type="cook",
        role="cook",
        attrs={"gender": "girl" if random.Random(0).choice([True, False]) else "boy"},
        label="the cook",
    ))
    world.add(Entity(id="kitchen", type="room", label="kitchen"))
    world.add(Entity(id="floor", type="floor", label="floor"))
    world.add(Entity(id="treat", type="treat", label=treat.label, fragile=treat.fragility))
    world.add(Entity(id="perch", type="perch", label=perch.label, reach=perch.reach))

    seeker.memes["trust"] = float(trust)
    seeker.memes["pride"] = PRIDE_INIT
    advisor.memes["caution"] = 4.0
    world.facts.update(
        treat_cfg=treat,
        perch_cfg=perch,
        response=response,
        relation=relation,
        trust=trust,
        predicted_spill=False,
        predicted_severity=0,
    )

    kitchen_setup(world, seeker, advisor, treat)
    desire(world, seeker, treat, perch)

    world.para()
    warning(world, advisor, seeker, treat, perch)
    averted = would_avert(relation, advisor_age, seeker_age, trust)

    if averted:
        back_down(world, seeker, advisor, cook, treat, response)
        outcome = "averted"
    else:
        attempt(world, seeker, perch, treat)
        if world.get("treat").meters["spilled"] >= THRESHOLD:
            alarm(world, advisor, seeker, treat)
        world.para()
        if contained_by(response, treat, perch):
            rescue(world, cook, response, treat)
            lesson_good(world, cook, seeker, advisor, treat)
            outcome = "contained"
        else:
            rescue_fail(world, cook, response, treat)
            loss(world, seeker, advisor, treat)
            outcome = "spilled"

    world.para()
    ending(world, seeker, advisor, treat, outcome)

    world.facts.update(
        seeker=seeker,
        advisor=advisor,
        cook=cook,
        treat=treat,
        perch=perch,
        outcome=outcome,
        severity=severity_of(treat, perch),
        averted=averted,
        spilled=world.get("treat").meters["spilled"] >= THRESHOLD,
        sticky=world.get("floor").meters["sticky"] >= THRESHOLD,
        contained=(outcome == "contained"),
    )
    return world


TREATS = {
    "honey_jar": Treat(
        id="honey_jar",
        label="honey jar",
        phrase="a round honey jar",
        shelf=3,
        fragility=2,
        spill_word="honey",
        ending_image="golden honey catching the lamp light",
        tags={"honey", "sticky"},
    ),
    "jam_jar": Treat(
        id="jam_jar",
        label="berry jam jar",
        phrase="a berry jam jar",
        shelf=2,
        fragility=2,
        spill_word="red jam",
        ending_image="ruby jam shining like a little sunset",
        tags={"jam", "sticky"},
    ),
    "cookie_tin": Treat(
        id="cookie_tin",
        label="cookie tin",
        phrase="a blue cookie tin",
        shelf=2,
        fragility=1,
        spill_word="crumbs",
        ending_image="a blue tin beside the breadboard",
        tags={"cookies", "tin"},
    ),
}

PERCHES = {
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="the stout wooden stool",
        reach=3,
        stability=3,
        sense=3,
        tags={"stool", "balance"},
    ),
    "chair": Perch(
        id="chair",
        label="chair",
        phrase="the painted kitchen chair",
        reach=2,
        stability=2,
        sense=2,
        tags={"chair", "balance"},
    ),
    "crate": Perch(
        id="crate",
        label="crate",
        phrase="the upside-down apple crate",
        reach=2,
        stability=2,
        sense=2,
        tags={"crate", "balance"},
    ),
    "spoon_tower": Perch(
        id="spoon_tower",
        label="spoon tower",
        phrase="a tottering tower of bowls and spoons",
        reach=3,
        stability=0,
        sense=1,
        tags={"spoons", "unstable"},
    ),
}

RESPONSES = {
    "ask_cook": Response(
        id="ask_cook",
        sense=3,
        power=4,
        text="lifted the little climber down, fetched the {treat} properly, and set it safely on the table",
        fail="reached for the {treat}, but it had already fallen too hard to save",
        qa_text="fetched the treat properly and set it safely on the table",
        tags={"help", "patience"},
    ),
    "steady_paws": Response(
        id="steady_paws",
        sense=3,
        power=3,
        text="steadied the shelf, caught the wobbling {treat}, and guided it back into place",
        fail="tried to steady the shelf, but the {treat} slipped past waiting hands",
        qa_text="steadied the shelf and caught the treat before it fell",
        tags={"help", "balance"},
    ),
    "cloth_and_pan": Response(
        id="cloth_and_pan",
        sense=2,
        power=2,
        text="caught the lid, saved what could be saved, and quickly wiped the first sticky drops away",
        fail="rushed in with a cloth and pan, but the {treat} had already burst open",
        qa_text="saved part of the spill and quickly cleaned the first sticky drops",
        tags={"cleaning", "help"},
    ),
    "leap_catch": Response(
        id="leap_catch",
        sense=1,
        power=1,
        text="made a wild leap and somehow batted the {treat} back toward the shelf",
        fail="made a wild leap for the {treat}, but only helped it fall faster",
        qa_text="made a wild leap for the falling treat",
        tags={"jumping"},
    ),
}


GIRL_NAMES = ["Mina", "Tess", "Lila", "Nora", "Wren", "Poppy", "Ivy", "Elsie"]
BOY_NAMES = ["Pip", "Milo", "Finn", "Ned", "Otis", "Benji", "Toby", "Leo"]
SPECIES = ["mouse", "sparrow", "rabbit", "kitten"]
RELATIONS = ["friends", "siblings"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for treat_id, treat in TREATS.items():
        for perch_id, perch in PERCHES.items():
            if can_reach(treat, perch):
                combos.append((treat_id, perch_id))
    return combos


@dataclass
class StoryParams:
    treat: str
    perch: str
    response: str
    seeker_name: str
    seeker_type: str
    seeker_gender: str
    advisor_name: str
    advisor_type: str
    advisor_gender: str
    relation: str
    seeker_age: int = 5
    advisor_age: int = 6
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


KNOWLEDGE = {
    "honey": [(
        "Why is spilled honey messy?",
        "Honey is thick and sticky, so it clings to floors, paws, and cloth. That is why even a small spill can make a big mess."
    )],
    "jam": [(
        "Why can jam make a hard mess to clean?",
        "Jam is sweet and sticky, and its fruit juice can smear as it spreads. It often needs wiping and washing before the place is clean again."
    )],
    "cookies": [(
        "What is a cookie tin?",
        "A cookie tin is a metal box used to keep cookies dry and fresh. It makes a clattery sound if it falls."
    )],
    "stool": [(
        "What is a stool used for in a kitchen?",
        "A stool is a small seat or step that can help someone reach higher places. A sturdy stool is safer than balancing on things that wobble."
    )],
    "balance": [(
        "Why is balance important when you climb?",
        "Balance keeps your body steady so you do not tip or slip. When balance is poor, even a small reach can turn into a fall or a spill."
    )],
    "help": [(
        "Why is asking for help wise?",
        "Asking for help is wise because another person may be taller, steadier, or more experienced. It often prevents accidents before they begin."
    )],
    "patience": [(
        "What does patience mean?",
        "Patience means waiting calmly instead of rushing for what you want. Patient choices often protect both people and things."
    )],
    "sticky": [(
        "Why do sticky spills need to be cleaned quickly?",
        "Sticky spills can spread, trap dust, and make floors unpleasant or slippery. Cleaning them quickly keeps the room safe and tidy."
    )],
    "cleaning": [(
        "Why do kitchens need quick cleaning after a spill?",
        "Kitchens are places where food is made, so spills should be cleaned soon. A tidy kitchen is safer and nicer to work in."
    )],
}
KNOWLEDGE_ORDER = ["honey", "jam", "cookies", "stool", "balance", "help", "patience", "sticky", "cleaning"]


def pair_noun(world: World) -> str:
    relation = world.facts.get("relation", "friends")
    seeker = world.facts["seeker"]
    advisor = world.facts["advisor"]
    if relation == "siblings":
        return f"two {seeker.type} siblings" if seeker.type == advisor.type else "two animal siblings"
    return "two little animal friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    advisor = f["advisor"]
    treat = f["treat"]
    perch = f["perch"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable set in a kitchen about {seeker.id} the {seeker.type}, '
        f'{advisor.id} the {advisor.type}, and a {treat.label} on a high shelf. '
        f'Include the words "assure" and "echo" and end with a moral.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a kitchen fable where {advisor.id} warns {seeker.id}, assures {seeker.pronoun('object')} that help will come, and patient listening prevents a mess.",
            f"Write a moral fable about a proud little climber who gives up {perch.phrase} and chooses wise help instead."
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a kitchen fable where {seeker.id} climbs onto {perch.phrase}, a clatter sends an echo around the pans, and a calm grown-up saves the day.",
            f"Write a child-friendly moral tale where haste nearly spills a treat, but wise help turns fear into gratitude."
        ]
    return [
        base,
        f"Tell a kitchen fable where {seeker.id} ignores a warning, climbs onto {perch.phrase}, and loses the treat in a sticky mess.",
        f"Write a simple moral tale showing that pride and hurry can ruin the very reward they chase."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    advisor = f["advisor"]
    treat = f["treat"]
    perch = f["perch"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(world)}: {seeker.id} the {seeker.type} and {advisor.id} the {advisor.type}. They were in the kitchen under a shelf that held a tempting {treat.label}."
        ),
        (
            f"What did {seeker.id} want?",
            f"{seeker.id} wanted to reach the {treat.label} on the high shelf without waiting. That wish made pride feel bigger than caution for a while."
        ),
        (
            f"What warning did {advisor.id} give?",
            f"{advisor.id} warned that {perch.label} was a poor ladder for such a reach and said, 'I assure you,' to urge patience. The warning mattered because the kitchen world already held the risk of a wobble and a spill."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How was the problem solved?",
            f"{seeker.id} listened before climbing, and together they called for the cook. The cook then {response.qa_text.replace('{treat}', treat.label)}, so they kept the treat and the tidy kitchen."
        ))
        qa.append((
            "What is the moral of this story?",
            "The moral is that patient listening can save both your reward and your peace. Asking for wise help is often braver than showing off."
        ))
    elif outcome == "contained":
        qa.append((
            "What happened when the climb began?",
            f"The perch wobbled, the kitchen rang with a clatter, and an echo ran under the copper pans. That was the turning point showing that the warning had been true."
        ))
        qa.append((
            "How did the cook help?",
            f"The cook {response.qa_text.replace('{treat}', treat.label)}. Because help came quickly enough for this level of danger, the mess did not become a full loss."
        ))
        qa.append((
            "What did the hero learn?",
            f"{seeker.id} learned that calm help is sweeter than stolen hurry. The near-miss left a lesson without taking everything away."
        ))
    else:
        qa.append((
            "Why was the ending sad?",
            f"The treat burst open and spread into a sticky mess before anyone could truly save it. {seeker.id} lost the reward because pride reached faster than safety."
        ))
        qa.append((
            "What did the echo mean in the story?",
            "The echo marked the noisy moment when careless climbing turned into trouble. Later it also felt like the kitchen repeating the lesson back to the hero."
        ))
        qa.append((
            "What is the moral of this story?",
            "The moral is that pride and haste can ruin what patience would have safely gained. Waiting a little can keep a small wish from becoming a big mess."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["treat"].tags) | set(f["perch"].tags)
    if f["outcome"] == "averted":
        tags |= {"help", "patience"}
    else:
        tags |= set(f["response"].tags)
        if f["spilled"] or f["sticky"]:
            tags |= {"sticky"}
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.reach:
            bits.append(f"reach={e.reach}")
        if e.fragile:
            bits.append(f"fragile={e.fragile}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        treat="honey_jar",
        perch="stool",
        response="ask_cook",
        seeker_name="Pip",
        seeker_type="mouse",
        seeker_gender="boy",
        advisor_name="Mina",
        advisor_type="sparrow",
        advisor_gender="girl",
        relation="siblings",
        seeker_age=4,
        advisor_age=7,
        trust=9,
    ),
    StoryParams(
        treat="jam_jar",
        perch="chair",
        response="steady_paws",
        seeker_name="Lila",
        seeker_type="rabbit",
        seeker_gender="girl",
        advisor_name="Finn",
        advisor_type="mouse",
        advisor_gender="boy",
        relation="friends",
        seeker_age=5,
        advisor_age=5,
        trust=4,
    ),
    StoryParams(
        treat="cookie_tin",
        perch="crate",
        response="cloth_and_pan",
        seeker_name="Otis",
        seeker_type="kitten",
        seeker_gender="boy",
        advisor_name="Wren",
        advisor_type="sparrow",
        advisor_gender="girl",
        relation="friends",
        seeker_age=6,
        advisor_age=6,
        trust=3,
    ),
    StoryParams(
        treat="honey_jar",
        perch="spoon_tower",
        response="cloth_and_pan",
        seeker_name="Tess",
        seeker_type="mouse",
        seeker_gender="girl",
        advisor_name="Ned",
        advisor_type="rabbit",
        advisor_gender="boy",
        relation="friends",
        seeker_age=5,
        advisor_age=5,
        trust=2,
    ),
]


def explain_rejection(treat: Treat, perch: Perch) -> str:
    return (
        f"(No story: {perch.label} cannot honestly reach the shelf with the {treat.label}. "
        f"This fable needs a real chance to grab the treat so that patience versus haste has meaning.)"
    )


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of these steadier choices: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.advisor_age, params.seeker_age, params.trust):
        return "averted"
    return "contained" if contained_by(RESPONSES[params.response], TREATS[params.treat], PERCHES[params.perch]) else "spilled"


ASP_RULES = r"""
% reasonableness gate
valid(T, P) :- treat(T), perch(P), shelf(T, S), reach(P, R), R >= S.
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.

% outcome model
advisor_older :- relation(siblings), advisor_age(A), seeker_age(S), A > S.
averted :- advisor_older, trust(T), trust_avert(M), T >= M.

wobble(P, 3 - St) :- perch(P), stability(P, St), St < 3.
wobble(P, 0) :- perch(P), stability(P, St), St >= 3.
severity(F + W) :- chosen_treat(T), fragility(T, F), chosen_perch(P), wobble(P, W).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("shelf", tid, treat.shelf))
        lines.append(asp.fact("fragility", tid, treat.fragility))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("reach", pid, perch.reach))
        lines.append(asp.fact("stability", pid, perch.stability))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("trust_avert", TRUST_AVERT))
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
    extra = "\n".join([
        asp.fact("chosen_treat", params.treat),
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_response", params.response),
        asp.fact("relation", params.relation),
        asp.fact("seeker_age", params.seeker_age),
        asp.fact("advisor_age", params.advisor_age),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sense, p_sense = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() smoke test at seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Kitchen fable storyworld: a high treat, a proud climb, and a moral about patient help."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name_gender(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.perch:
        treat = TREATS[args.treat]
        perch = PERCHES[args.perch]
        if not can_reach(treat, perch):
            raise StoryError(explain_rejection(treat, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.perch is None or combo[1] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))

    seeker_name, seeker_gender = _pick_name_gender(rng)
    advisor_name, advisor_gender = _pick_name_gender(rng)
    while advisor_name == seeker_name:
        advisor_name, advisor_gender = _pick_name_gender(rng)

    return StoryParams(
        treat=treat_id,
        perch=perch_id,
        response=response_id,
        seeker_name=seeker_name,
        seeker_type=rng.choice(SPECIES),
        seeker_gender=seeker_gender,
        advisor_name=advisor_name,
        advisor_type=rng.choice(SPECIES),
        advisor_gender=advisor_gender,
        relation=rng.choice(RELATIONS),
        seeker_age=rng.choice([4, 5, 6]),
        advisor_age=rng.choice([5, 6, 7]),
        trust=rng.randint(2, 10),
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not can_reach(TREATS[params.treat], PERCHES[params.perch]):
        raise StoryError(explain_rejection(TREATS[params.treat], PERCHES[params.perch]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        treat=TREATS[params.treat],
        perch=PERCHES[params.perch],
        response=RESPONSES[params.response],
        seeker_name=params.seeker_name,
        seeker_type=params.seeker_type,
        seeker_gender=params.seeker_gender,
        advisor_name=params.advisor_name,
        advisor_type=params.advisor_type,
        advisor_gender=params.advisor_gender,
        relation=params.relation,
        seeker_age=params.seeker_age,
        advisor_age=params.advisor_age,
        trust=params.trust,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treat, perch) combos:\n")
        for treat, perch in combos:
            print(f"  {treat:10} {perch}")
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
            header = f"### {p.seeker_name}: {p.treat} from {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
