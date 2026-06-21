#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py
=====================================================================

A small fairy-tale storyworld about a child at a lantern-lit bingo feast who is
tempted to be unfair in order to win a beautiful sash.

This world is built around:
- the required words: "egg-dim", "bingo", "sash"
- a clear inner monologue
- a lesson learned
- state-driven prose with a small causal model
- a Python reasonableness gate plus an inline ASP twin

Run it
------
python storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py
python storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py --all
python storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py --trace
python storyworlds/worlds/gpt-5.4/egg_dim_bingo_sash_lesson_learned_inner.py --verify
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
BRAVERY_TO_DEFY = 5


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "grandmother", "aunt"}
        male = {"boy", "man", "king", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "queen": "queen",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Venue:
    id: str
    place: str
    opening: str
    egg_dim: str
    caller_spot: str
    sash_spot: str
    affords: set[str] = field(default_factory=set)
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
class Temptation:
    id: str
    object_kind: str
    severity: int
    need: str
    thought: str
    act_text: str
    warning: str
    confession: str
    apology: str
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
class Repair:
    id: str
    sense: int
    power: int
    text: str
    noticed_text: str
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
class SashPrize:
    id: str
    label: str
    phrase: str
    glow: str
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_unfairness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    hall = world.get("hall")
    wrong = (
        world.get("card").meters["wrong_mark"]
        + world.get("shell").meters["peeked"]
        + world.get("sash").meters["borrowed"]
    )
    if wrong >= THRESHOLD and ("unfair", hero.id) not in world.fired:
        world.fired.add(("unfair", hero.id))
        hall.meters["unfairness"] += 1
        hero.memes["guilt"] += 1
        helper = world.get("helper")
        helper.memes["concern"] += 1
        out.append("__unfair__")
    return out


def _r_confession_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["confessed"] >= THRESHOLD and ("relief", hero.id) not in world.fired:
        world.fired.add(("relief", hero.id))
        hero.memes["relief"] += 1
        hero.memes["guilt"] = 0.0
        hero.memes["lesson"] += 1
        world.get("caller").memes["trust"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="unfairness", tag="social", apply=_r_unfairness),
    Rule(name="confession_relief", tag="emotional", apply=_r_confession_relief),
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


def temptation_possible(venue: Venue, temptation: Temptation) -> bool:
    return temptation.id in venue.affords


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_fits(temptation: Temptation, repair: Repair) -> bool:
    return repair.id in REPAIR_MAP[temptation.id]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for temptation_id, temptation in TEMPTATIONS.items():
            if not temptation_possible(venue, temptation):
                continue
            for repair_id, repair in REPAIRS.items():
                if repair.sense >= SENSE_MIN and repair_fits(temptation, repair):
                    combos.append((venue_id, temptation_id, repair_id))
    return combos


def would_avert(helper_kind: str, helper_trait: str, relation: str, helper_age: int, hero_age: int) -> bool:
    older = relation == "siblings" and helper_age > hero_age
    wise = helper_trait in {"wise", "steady", "honest"}
    strong_helper = helper_kind in {"grandmother", "grandfather", "queen"}
    return (older and wise) or strong_helper


def trouble_severity(temptation: Temptation, delay: int) -> int:
    return temptation.severity + delay


def repair_contains(temptation: Temptation, repair: Repair, delay: int) -> bool:
    return repair.power >= trouble_severity(temptation, delay)


def predict_trouble(world: World, temptation: Temptation) -> dict:
    sim = world.copy()
    enact_temptation(sim, temptation, narrate=False)
    return {
        "unfairness": sim.get("hall").meters["unfairness"],
        "guilt": sim.get("hero").memes["guilt"],
    }


def introduce(world: World, hero: Entity, helper: Entity, venue: Venue, sash: SashPrize) -> None:
    world.say(
        f"Once, in {venue.place}, {hero.id} went with {helper.id} to a feast where the lanterns burned {venue.egg_dim}. "
        f"{venue.opening}"
    )
    world.say(
        f"At the far end of the room, above {venue.sash_spot}, hung {sash.phrase}. {sash.glow}"
    )
    hero.memes["wonder"] += 1
    hero.memes["desire"] += 1


def begin_bingo(world: World, hero: Entity, helper: Entity, venue: Venue) -> None:
    world.say(
        f"In the middle stood the long bingo table, and the caller waited by {venue.caller_spot} with a velvet bowl of number-shells."
    )
    world.say(
        f'{helper.id} smoothed {hero.id}\'s sleeve and whispered, "Play true, and let the game be merry."'
    )
    world.get("card").meters["ready"] += 1
    world.get("shell").meters["in_bowl"] += 1


def longing(world: World, hero: Entity, sash: SashPrize) -> None:
    world.say(
        f"{hero.id} looked again at the {sash.label}. Inside, a small voice said, "
        f'"If I win that sash, everyone will see me first."'
    )


def inner_monologue(world: World, hero: Entity, temptation: Temptation) -> None:
    pred = predict_trouble(world, temptation)
    world.facts["predicted_unfairness"] = pred["unfairness"]
    world.facts["predicted_guilt"] = pred["guilt"]
    hero.memes["tempted"] += 1
    world.say(
        f"But another thought fluttered under {hero.pronoun('possessive')} ribs: "
        f'"{temptation.thought}"'
    )
    world.say(
        f'{hero.pronoun().capitalize()} knew the hall was {world.venue.egg_dim}, and {temptation.need}.'
    )


def warning(world: World, helper: Entity, temptation: Temptation) -> None:
    helper.memes["care"] += 1
    extra = ""
    if helper.type in {"grandmother", "grandfather", "queen"}:
        extra = f" {helper.id}'s voice was soft, but it carried the weight of old good sense."
    world.say(
        f'{helper.id} watched {world.get("hero").id}\'s face and murmured, "{temptation.warning}"{extra}'
    )


def back_down(world: World, hero: Entity, helper: Entity, sash: SashPrize) -> None:
    hero.memes["tempted"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    hero.memes["honest_pride"] += 1
    world.say(
        f"{hero.id} let out the breath {hero.pronoun()} had been holding and folded both hands in {hero.pronoun('possessive')} lap."
    )
    world.say(
        f'"No," {hero.pronoun()} told the busy little wish inside. "I would rather lose honestly than touch that {sash.label} unfairly."'
    )


def enact_temptation(world: World, temptation: Temptation, narrate: bool = True) -> None:
    hero = world.get("hero")
    if temptation.id == "slide_marker":
        world.get("card").meters["wrong_mark"] += 1
    elif temptation.id == "peek_shell":
        world.get("shell").meters["peeked"] += 1
    elif temptation.id == "borrow_sash":
        world.get("sash").meters["borrowed"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(temptation.act_text)


def caught_beat(world: World, caller: Entity, temptation: Temptation) -> None:
    caller.memes["notice"] += 1
    world.say(
        f"Then the game paused. The caller's eyes settled on {world.get('hero').id}, and the music in the room seemed to hold still."
    )
    if temptation.id == "slide_marker":
        world.say(
            f'"Little one," said the caller, "that moon-bean rests on a square I did not call."'
        )
    elif temptation.id == "peek_shell":
        world.say(
            f'"Little one," said the caller, "the next shell is for every player, not for secret eyes alone."'
        )
    else:
        world.say(
            f'"Little one," said the caller, "a winner\'s sash must wait for winning shoulders."'
        )


def confess(world: World, hero: Entity, caller: Entity, temptation: Temptation, repair: Repair, noticed: bool) -> None:
    hero.memes["confessed"] += 1
    if temptation.id == "slide_marker":
        world.get("card").meters["wrong_mark"] = 0.0
    elif temptation.id == "peek_shell":
        world.get("shell").meters["peeked"] = 0.0
    elif temptation.id == "borrow_sash":
        world.get("sash").meters["borrowed"] = 0.0
    world.get("hall").meters["unfairness"] = 0.0
    propagate(world, narrate=False)
    line = repair.noticed_text if noticed else repair.text
    world.say(
        f'{hero.id} stood up so quickly that {hero.pronoun("possessive")} stool gave a tiny scrape. "{temptation.confession}"'
    )
    world.say(
        f"{line} {caller.pronoun().capitalize()} listened, and no one laughed."
    )
    world.say(
        f'{hero.id} added, "{temptation.apology}"'
    )
    hero.memes["honest_pride"] += 1


def reward_truth(world: World, hero: Entity, helper: Entity, caller: Entity, sash: SashPrize, noticed: bool) -> None:
    world.get("sash").attrs["owner"] = hero.id
    hero.meters["wearing_sash"] += 1
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    if noticed:
        start = "The caller's stern look melted into a kind one."
    else:
        start = "The caller smiled before the round could twist any further."
    world.say(
        f"{start} \"A true heart can still set things right,\" {caller.pronoun()} said."
    )
    world.say(
        f"{caller.pronoun().capitalize()} lifted {sash.phrase} and laid it across {hero.id}'s shoulders. It was not a winner's prize now, but an honesty sash, and it felt warmer than moonlight."
    )
    world.say(
        f"{helper.id} squeezed {hero.id}'s hand. From then on, whenever the feast folk called bingo, {hero.id} listened with clear eyes and waited for {hero.pronoun('possessive')} turn."
    )


def honest_end(world: World, hero: Entity, helper: Entity, caller: Entity, sash: SashPrize) -> None:
    world.get("sash").attrs["owner"] = hero.id
    hero.meters["wearing_sash"] += 1
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    world.say(
        f"When the round ended, the caller had seen everything in the gentle way grown folk sometimes do. \"You did not take the crooked path,\" {caller.pronoun()} said."
    )
    world.say(
        f"{caller.pronoun().capitalize()} placed {sash.phrase} over {hero.id}'s shoulders anyway. \"Keep this honesty sash, and remember how much lighter a true heart feels.\""
    )
    world.say(
        f"So {hero.id} went home under the stars with {helper.id}, the sash at {hero.pronoun('possessive')} shoulder and a steadier little voice inside."
    )


def tell(
    venue: Venue,
    temptation: Temptation,
    repair: Repair,
    sash_cfg: SashPrize,
    hero_name: str = "Elin",
    hero_gender: str = "girl",
    helper_name: str = "Nona",
    helper_type: str = "grandmother",
    helper_trait: str = "wise",
    relation: str = "kin",
    hero_age: int = 6,
    helper_age: int = 60,
    caller_type: str = "queen",
    delay: int = 0,
) -> World:
    world = World(venue)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            age=hero_age,
            traits=["eager"],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            age=helper_age,
            traits=[helper_trait],
            attrs={"relation": relation},
        )
    )
    caller = world.add(
        Entity(
            id="Caller",
            kind="character",
            type=caller_type,
            role="caller",
            age=40,
            attrs={},
        )
    )
    world.add(Entity(id="hall", type="hall", label=venue.place, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="card", type="card", label="bingo card", attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="shell", type="shell", label="number-shell", attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="sash", type="sash", label=sash_cfg.label, attrs={"owner": ""}, meters=defaultdict(float), memes=defaultdict(float)))

    world.facts.update(
        venue=venue,
        temptation=temptation,
        repair=repair,
        sash_cfg=sash_cfg,
        hero=hero,
        helper=helper,
        caller=caller,
        relation=relation,
        delay=delay,
        predicted_unfairness=0,
        predicted_guilt=0,
    )

    introduce(world, hero, helper, venue, sash_cfg)
    begin_bingo(world, hero, helper, venue)
    world.para()
    longing(world, hero, sash_cfg)
    inner_monologue(world, hero, temptation)
    warning(world, helper, temptation)

    averted = would_avert(helper_type, helper_trait, relation, helper_age, hero_age)
    world.facts["averted"] = averted

    if averted:
        back_down(world, hero, helper, sash_cfg)
        world.para()
        honest_end(world, hero, helper, caller, sash_cfg)
        outcome = "averted"
    else:
        enact_temptation(world, temptation, narrate=True)
        noticed = not repair_contains(temptation, repair, delay)
        world.facts["noticed"] = noticed
        world.para()
        if noticed:
            caught_beat(world, caller, temptation)
        confess(world, hero, caller, temptation, repair, noticed)
        world.para()
        reward_truth(world, hero, helper, caller, sash_cfg, noticed)
        outcome = "noticed" if noticed else "mended"

    world.facts.update(
        outcome=outcome,
        lesson=world.get("hero").memes["lesson"] >= THRESHOLD or world.get("hero").memes["honest_pride"] >= THRESHOLD,
        wearing_sash=world.get("hero").meters["wearing_sash"] >= THRESHOLD,
        unfairness=world.get("hall").meters["unfairness"],
    )
    return world


VENUES = {
    "moon_hall": Venue(
        id="moon_hall",
        place="the Moonseed Hall",
        opening="Silver paper stars hung from the rafters, and everyone spoke in feast-day whispers.",
        egg_dim="egg-dim as if a candle glowed behind a shell",
        caller_spot="a carved stool of ash wood",
        sash_spot="a hook beside the caller's chair",
        affords={"slide_marker", "peek_shell", "borrow_sash"},
        tags={"bingo", "hall"},
    ),
    "orchard_pavilion": Venue(
        id="orchard_pavilion",
        place="the Orchard Pavilion",
        opening="Pear blossoms nodded outside the curtains, and honey cakes warmed the air.",
        egg_dim="egg-dim under paper lantern pears",
        caller_spot="a table of polished cherry wood",
        sash_spot="a willow peg by the lantern post",
        affords={"slide_marker", "borrow_sash"},
        tags={"bingo", "orchard"},
    ),
    "tower_gallery": Venue(
        id="tower_gallery",
        place="the old Tower Gallery",
        opening="Tiny bells tinkled in the drafts, and long windows wore blue evening like cloaks.",
        egg_dim="egg-dim in the folds of tower light",
        caller_spot="a narrow stand beneath the bell rope",
        sash_spot="a brass arm fixed to the stone",
        affords={"peek_shell", "borrow_sash"},
        tags={"bingo", "tower"},
    ),
}

TEMPTATIONS = {
    "slide_marker": Temptation(
        id="slide_marker",
        object_kind="card",
        severity=1,
        need="one little moon-bean could slide without much noise",
        thought="If I nudge my bean one square, perhaps fortune will think I belong there",
        act_text="When the caller looked down at the bowl, one of Hero's fingers gave a moon-bean the smallest secret push across the bingo card.",
        warning="A win that is bent never sits straight in the heart.",
        confession="I moved my marker where it did not belong. I wanted the sash too much.",
        apology="I am sorry. I will put it right and play fairly now.",
        tags={"bingo", "honesty"},
    ),
    "peek_shell": Temptation(
        id="peek_shell",
        object_kind="shell",
        severity=2,
        need="the next shell lay close enough for curious fingers",
        thought="If I knew the next number first, I could be ready before anyone else",
        act_text="As the bells chimed, Hero lifted the lip of the velvet bowl and peeked at the next number-shell before the call.",
        warning="Secret seeing is only another kind of stealing.",
        confession="I peeked into the bowl to know the next shell first. That was not fair.",
        apology="I am sorry. I will not hide little tricks inside a game again.",
        tags={"bingo", "honesty"},
    ),
    "borrow_sash": Temptation(
        id="borrow_sash",
        object_kind="sash",
        severity=2,
        need="the hook with the prize sash was just within reach",
        thought="If I felt the sash on my shoulder now, maybe the room would already believe I had earned it",
        act_text="While the song between rounds fluttered through the room, Hero reached up and draped the prize sash over one shoulder before the game was won.",
        warning="What is worn before it is earned will feel heavy instead of fine.",
        confession="I took the sash before winning it. I wanted to look like the winner.",
        apology="I am sorry. I would rather deserve a thing than merely touch it.",
        tags={"sash", "honesty"},
    ),
}

REPAIRS = {
    "quiet_confess": Repair(
        id="quiet_confess",
        sense=3,
        power=2,
        text="At once Hero set the matter in plain words before the next call could begin.",
        noticed_text="Hero's cheeks flamed, but the truth came out in steady words.",
        qa_text="confessed right away and corrected the mistake before the game went on",
        tags={"confess", "truth"},
    ),
    "public_apology": Repair(
        id="public_apology",
        sense=3,
        power=3,
        text="Hero turned to the whole table, returned what was not rightly won, and apologized clearly.",
        noticed_text="Hero returned what was not rightly won and apologized to everyone at the table.",
        qa_text="returned what was not rightly won and gave a clear apology",
        tags={"confess", "apology"},
    ),
    "hide_it": Repair(
        id="hide_it",
        sense=1,
        power=0,
        text="Hero tried to keep a straight face and hope the crooked moment would vanish on its own.",
        noticed_text="Hero tried to hide the mistake, but hiding only made the silence colder.",
        qa_text="tried to hide it",
        tags={"hide"},
    ),
}

REPAIR_MAP = {
    "slide_marker": {"quiet_confess", "public_apology"},
    "peek_shell": {"public_apology"},
    "borrow_sash": {"quiet_confess", "public_apology"},
}

SASHES = {
    "blue": SashPrize(
        id="blue",
        label="blue sash",
        phrase="a blue sash stitched with silver acorns",
        glow="It shone like a small ribbon of evening sky.",
        tags={"sash"},
    ),
    "gold": SashPrize(
        id="gold",
        label="gold sash",
        phrase="a gold sash sewn with tiny suns",
        glow="It glimmered warmly whenever the lanterns breathed.",
        tags={"sash"},
    ),
    "green": SashPrize(
        id="green",
        label="green sash",
        phrase="a green sash edged with little leaves",
        glow="Its hem flashed softly like dew in grass.",
        tags={"sash"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Tansy", "Lark", "Oona", "Pia", "Nell"]
BOY_NAMES = ["Rowan", "Bram", "Ivo", "Theo", "Perrin", "Milo", "Ash"]
HELPER_NAMES = ["Nona", "Bran", "Aunt Willow", "Uncle Fen", "Queen Moss", "Gran Reed"]
HELPER_TYPES = ["grandmother", "grandfather", "aunt", "uncle", "queen"]
HELPER_TRAITS = ["wise", "steady", "honest", "gentle"]
RELATIONS = ["kin", "siblings", "neighbors"]

KNOWLEDGE = {
    "bingo": [
        (
            "What is bingo?",
            "Bingo is a game where a caller announces numbers and players mark matching spaces on their cards. You win by completing the right pattern honestly."
        )
    ],
    "sash": [
        (
            "What is a sash?",
            "A sash is a long band of cloth worn across the body or tied at the waist. In stories, it can show honor, celebration, or belonging."
        )
    ],
    "honesty": [
        (
            "Why is honesty important in a game?",
            "Honesty keeps the game fair for everyone. When people play by the same rules, a win feels joyful instead of crooked."
        )
    ],
    "confess": [
        (
            "Why can telling the truth fix a problem?",
            "Telling the truth lets people put a wrong thing right. It may feel scary at first, but it often makes the heart lighter."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology says what was wrong and tries to mend the harm. It is stronger when the person also changes what they do next."
        )
    ],
    "truth": [
        (
            "Can doing the right thing feel hard?",
            "Yes. Sometimes the right thing feels harder at first because you must be brave enough to be truthful."
        )
    ],
}
KNOWLEDGE_ORDER = ["bingo", "sash", "honesty", "confess", "apology", "truth"]


@dataclass
class StoryParams:
    venue: str
    temptation: str
    repair: str
    sash: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    helper_trait: str
    relation: str
    hero_age: int = 6
    helper_age: int = 60
    caller_type: str = "queen"
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


def explain_rejection(venue: Venue, temptation: Temptation, repair: Optional[Repair] = None) -> str:
    if not temptation_possible(venue, temptation):
        return (
            f"(No story: in {venue.place}, this temptation has no honest chance to arise. "
            f"That place does not put the {temptation.object_kind} within tempting reach.)"
        )
    if repair is not None and not repair_fits(temptation, repair):
        return (
            f"(No story: repair '{repair.id}' does not properly mend the temptation '{temptation.id}'. "
            f"The fix must match the harm and restore fairness.)"
        )
    return "(No story: this combination does not fit the world.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it is below the common-sense threshold "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(
        helper_kind=params.helper_type,
        helper_trait=params.helper_trait,
        relation=params.relation,
        helper_age=params.helper_age,
        hero_age=params.hero_age,
    ):
        return "averted"
    temptation = TEMPTATIONS[params.temptation]
    repair = REPAIRS[params.repair]
    return "mended" if repair_contains(temptation, repair, params.delay) else "noticed"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    temptation = f["temptation"]
    sash = f["sash_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "egg-dim", '
        f'"bingo", and "sash". Give the child an inner monologue and end with a lesson learned.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle fairy tale where {hero.id} wants {sash.phrase} at a bingo feast, thinks about {temptation.id}, but listens to {helper.id} and chooses honesty before doing anything wrong.",
            f"Write a small magical story where the biggest turn happens inside {hero.id}'s thoughts, and the ending shows that a true heart feels lighter than a crooked win.",
        ]
    if outcome == "noticed":
        return [
            base,
            f"Tell a fairy tale where {hero.id} gives in to temptation at bingo, is noticed, tells the truth, and learns that honesty can mend a shaky moment.",
            f"Write a story with a clear lesson learned: a child reaches for a sash or a game advantage too soon, then makes things right with a brave apology.",
        ]
    return [
        base,
        f"Tell a fairy tale where {hero.id} is tempted to be unfair during bingo, confesses quickly, and is rewarded for honesty rather than winning.",
        f"Write a story where an inner monologue leads to a wrong choice, but the child repairs the harm before the room turns against them.",
    ]


def pair_noun(relation: str) -> str:
    if relation == "siblings":
        return "two family children"
    if relation == "kin":
        return "two relatives"
    return "a child and a trusted elder friend"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    caller = f["caller"]
    venue = f["venue"]
    temptation = f["temptation"]
    repair = f["repair"]
    sash = f["sash_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who went to a fairy-tale bingo feast with {helper.id}. The story also includes the caller, who helps fairness matter more than showing off."
        ),
        (
            "What did the room look like at the beginning?",
            f"The feast was held in {venue.place}, where the lanterns burned {venue.egg_dim}. That egg-dim light made the place feel magical, but it also made a small unfair act feel possible."
        ),
        (
            f"Why did {hero.id} care so much about the sash?",
            f"{hero.id} longed for {sash.phrase} because it looked special and honorable. Inside, {hero.pronoun()} wanted everyone to see {hero.pronoun('object')} as important."
        ),
        (
            f"What was {hero.id}'s inner monologue about?",
            f"{hero.pronoun().capitalize()} argued inside {hero.pronoun('possessive')} own thoughts about whether to take a crooked shortcut. The little private thought came before the big turning point in the room."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Did {hero.id} actually cheat at bingo?",
                f"No. {helper.id}'s warning and {hero.id}'s own better thought stopped the unfair act before it happened. That is why the lesson was learned inside the choice itself."
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"It ended with {hero.id} wearing the sash as an honesty sash, not as a prize stolen or rushed. The final image shows that truth made {hero.pronoun('possessive')} heart steadier."
            )
        )
    else:
        qa.append(
            (
                f"What unfair thing did {hero.id} do?",
                f"{temptation.confession} That act mattered because bingo only feels joyful when everyone follows the same rules."
            )
        )
        if outcome == "noticed":
            qa.append(
                (
                    f"How was the problem repaired after the caller noticed?",
                    f"{hero.id} told the truth, and {repair.qa_text}. The repair worked because honesty replaced secrecy, even after the room had already gone still."
                )
            )
        else:
            qa.append(
                (
                    f"How did {hero.id} fix the problem before it grew bigger?",
                    f"{hero.id} confessed quickly, and {repair.qa_text}. That stopped the unfairness before the next part of the game could carry it forward."
                )
            )
        qa.append(
            (
                "What lesson was learned?",
                f"The lesson was that wearing honor is not the same as earning it. {hero.id} learned that a truthful heart feels lighter than any crooked victory."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bingo", "sash", "honesty"} | set(f["temptation"].tags) | set(f["repair"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="moon_hall",
        temptation="slide_marker",
        repair="quiet_confess",
        sash="blue",
        hero_name="Elin",
        hero_gender="girl",
        helper_name="Nona",
        helper_type="grandmother",
        helper_trait="wise",
        relation="kin",
        hero_age=6,
        helper_age=68,
        caller_type="queen",
        delay=0,
    ),
    StoryParams(
        venue="orchard_pavilion",
        temptation="borrow_sash",
        repair="public_apology",
        sash="gold",
        hero_name="Rowan",
        hero_gender="boy",
        helper_name="Aunt Willow",
        helper_type="aunt",
        helper_trait="gentle",
        relation="kin",
        hero_age=7,
        helper_age=33,
        caller_type="queen",
        delay=1,
    ),
    StoryParams(
        venue="tower_gallery",
        temptation="peek_shell",
        repair="public_apology",
        sash="green",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Bran",
        helper_type="grandfather",
        helper_trait="steady",
        relation="kin",
        hero_age=6,
        helper_age=71,
        caller_type="queen",
        delay=0,
    ),
    StoryParams(
        venue="moon_hall",
        temptation="borrow_sash",
        repair="quiet_confess",
        sash="gold",
        hero_name="Theo",
        hero_gender="boy",
        helper_name="Perrin",
        helper_type="uncle",
        helper_trait="honest",
        relation="siblings",
        hero_age=6,
        helper_age=9,
        caller_type="queen",
        delay=0,
    ),
    StoryParams(
        venue="orchard_pavilion",
        temptation="slide_marker",
        repair="quiet_confess",
        sash="green",
        hero_name="Nell",
        hero_gender="girl",
        helper_name="Queen Moss",
        helper_type="queen",
        helper_trait="wise",
        relation="neighbors",
        hero_age=5,
        helper_age=40,
        caller_type="queen",
        delay=0,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
possible(V,T) :- venue(V), temptation(T), affords(V,T).
sensible(R)   :- repair(R), sense(R,S), sense_min(M), S >= M.
fit(T,R)      :- temptation(T), repair(R), fixes(T,R).
valid(V,T,R)  :- possible(V,T), sensible(R), fit(T,R).

% --- outcome model ---------------------------------------------------------
older_helper :- relation(siblings), helper_age(HA), hero_age(A), HA > A.
wise_trait   :- helper_trait(T), wise_like(T).
strong_helper :- helper_kind(K), strong_helper_kind(K).
averted :- older_helper, wise_trait.
averted :- strong_helper.

severity(S + D) :- chosen_temptation(T), temptation_severity(T,S), delay(D).
contained :- chosen_repair(R), repair_power(R,P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(mended)  :- not averted, contained.
outcome(noticed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for temptation_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, temptation_id))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("temptation_severity", temptation_id, temptation.severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
    for temptation_id, repairs in REPAIR_MAP.items():
        for repair_id in sorted(repairs):
            lines.append(asp.fact("fixes", temptation_id, repair_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted({"wise", "steady", "honest"}):
        lines.append(asp.fact("wise_like", trait))
    for kind in sorted({"grandmother", "grandfather", "queen"}):
        lines.append(asp.fact("strong_helper_kind", kind))
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
            asp.fact("chosen_temptation", params.temptation),
            asp.fact("chosen_repair", params.repair),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("helper_kind", params.helper_type),
            asp.fact("helper_trait", params.helper_trait),
            asp.fact("helper_age", params.helper_age),
            asp.fact("hero_age", params.hero_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    p_sensible = {r.id for r in sensible_repairs()}
    c_sensible = set(asp_sensible())
    if p_sensible == c_sensible:
        print(f"OK: sensible repairs match ({sorted(p_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params seed={seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale bingo storyworld: a child longs for a sash, faces a crooked temptation, and learns an honesty lesson."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--sash", choices=SASHES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the child waits before repairing the wrong")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the inline ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_names(rng: random.Random, gender: str, helper_type: str) -> tuple[str, str]:
    hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_map = {
        "grandmother": ["Nona", "Gran Reed"],
        "grandfather": ["Bran"],
        "aunt": ["Aunt Willow"],
        "uncle": ["Uncle Fen"],
        "queen": ["Queen Moss"],
    }
    helper_name = rng.choice(helper_map[helper_type])
    return hero_name, helper_name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    if args.venue and args.temptation:
        venue = VENUES[args.venue]
        temptation = TEMPTATIONS[args.temptation]
        if not temptation_possible(venue, temptation):
            raise StoryError(explain_rejection(venue, temptation))

    if args.temptation and args.repair:
        temptation = TEMPTATIONS[args.temptation]
        repair = REPAIRS[args.repair]
        if not repair_fits(temptation, repair):
            raise StoryError(explain_rejection(VENUES[args.venue] if args.venue else next(iter(VENUES.values())), temptation, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.temptation is None or combo[1] == args.temptation)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, temptation_id, repair_id = rng.choice(sorted(combos))
    sash_id = args.sash or rng.choice(sorted(SASHES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    relation = args.relation or rng.choice(RELATIONS)
    hero_name, helper_name = pick_names(rng, hero_gender, helper_type)
    helper_trait = rng.choice(HELPER_TRAITS)
    hero_age = rng.choice([5, 6, 7])
    if relation == "siblings":
        helper_age = rng.choice([8, 9, 10])
        if helper_type not in {"aunt", "uncle"}:
            helper_type = rng.choice(["aunt", "uncle"])
            hero_name, helper_name = pick_names(rng, hero_gender, helper_type)
    elif helper_type in {"grandmother", "grandfather"}:
        helper_age = rng.choice([58, 64, 71])
    elif helper_type == "queen":
        helper_age = rng.choice([35, 40, 48])
    else:
        helper_age = rng.choice([28, 33, 39])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        venue=venue_id,
        temptation=temptation_id,
        repair=repair_id,
        sash=sash_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_trait=helper_trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
        caller_type="queen",
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        temptation = TEMPTATIONS[params.temptation]
        repair = REPAIRS[params.repair]
        sash = SASHES[params.sash]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if (params.venue, params.temptation, params.repair) not in set(valid_combos()):
        raise StoryError("(The chosen venue, temptation, and repair do not make a reasonable story.)")

    world = tell(
        venue=venue,
        temptation=temptation,
        repair=repair,
        sash_cfg=sash,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_trait=params.helper_trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        caller_type=params.caller_type,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("Hero", params.hero_name),
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
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (venue, temptation, repair) combos:\n")
        for venue, temptation, repair in combos:
            print(f"  {venue:16} {temptation:14} {repair}")
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
            header = f"### {p.hero_name}: {p.temptation} at {p.venue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
