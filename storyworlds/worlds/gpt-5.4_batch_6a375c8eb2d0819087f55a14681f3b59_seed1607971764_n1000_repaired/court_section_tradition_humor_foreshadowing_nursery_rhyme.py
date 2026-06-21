#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py
=======================================================================================

A small nursery-rhyme-style story world about a tiny court, a parade section,
and a wobbly tradition. The world models a cheerful court custom: each section
of the court carries a ceremonial treat across the tiles to the judge's stool.

The tension is physical and concrete. Some sections march more bumpily than
others, some treats wobble more than others, and some supports are sensible
enough to steady the treat while others are too silly to count. The helper can
foresee the risk before the march begins, giving us a foreshadowing beat rooted
in simulation rather than decoration.

Run it
------
    python storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py --court berry --section drum --treat jelly_stack
    python storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py --support tall_hat
    python storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/court_section_tradition_humor_foreshadowing_nursery_rhyme.py --verify
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
HAZARD_MIN = 3


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
        female = {"girl", "mother", "queen", "duck", "goose_hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        species = self.attrs.get("species", "")
        if species:
            return f"{self.id} {species}"
        return self.id
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
class CourtCfg:
    id: str
    label: str
    judge: str
    floor: str
    bounce: int
    image: str
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
class SectionCfg:
    id: str
    label: str
    move: str
    beat: str
    bumpiness: int
    refrain: str
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
class TreatCfg:
    id: str
    label: str
    phrase: str
    fragility: int
    wobble_sign: str
    splat: str
    topping: str
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
class SupportCfg:
    id: str
    label: str
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


def _r_wobble_risk(world: World) -> list[str]:
    out: list[str] = []
    if "treat" not in world.entities:
        return out
    treat = world.get("treat")
    if treat.meters["wobble"] < THRESHOLD:
        return out
    sig = ("risk", "treat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("court").meters["hush"] += 1
    for rid in ("hero", "helper"):
        world.get(rid).memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_splat_mess(world: World) -> list[str]:
    out: list[str] = []
    if "treat" not in world.entities:
        return out
    treat = world.get("treat")
    if treat.meters["spilled"] < THRESHOLD:
        return out
    sig = ("mess", "treat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("court").meters["sticky"] += 1
    for rid in ("hero", "helper", "judge"):
        world.get(rid).memes["surprise"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble_risk", tag="physical", apply=_r_wobble_risk),
    Rule(name="splat_mess", tag="physical", apply=_r_splat_mess),
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


def hazard_value(court: CourtCfg, section: SectionCfg, treat: TreatCfg) -> int:
    return court.bounce + section.bumpiness + treat.fragility


def sensible_supports() -> list[SupportCfg]:
    return [s for s in SUPPORTS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for court_id, court in COURTS.items():
        for section_id, section in SECTIONS.items():
            for treat_id, treat in TREATS.items():
                if hazard_value(court, section, treat) >= HAZARD_MIN:
                    combos.append((court_id, section_id, treat_id))
    return combos


def outcome_contains(support: SupportCfg, court: CourtCfg, section: SectionCfg,
                     treat: TreatCfg, delay: int) -> bool:
    return support.power >= hazard_value(court, section, treat) + delay


def predict_wobble(world: World, severity: int) -> dict:
    sim = world.copy()
    sim.get("treat").meters["wobble"] += float(severity)
    propagate(sim, narrate=False)
    return {
        "risky": sim.get("court").meters["hush"] >= THRESHOLD,
        "wobble": sim.get("treat").meters["wobble"],
        "worry": sim.get("hero").memes["worry"] + sim.get("helper").memes["worry"],
    }


def open_court(world: World, court: CourtCfg, section: SectionCfg,
               hero: Entity, helper: Entity, judge: Entity) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In {court.label}, on {court.floor}, the morning rang light and sweet. "
        f"{court.image}"
    )
    world.say(
        f"Every Thursday the court kept a tradition: each section crossed the square "
        f"to the judge's stool with a festival treat. This was the {section.label}, "
        f"so {hero.title} and {helper.title} were to go step by step and neat-neat-neat."
    )
    world.say(
        f'{judge.title} called, "{section.refrain}!" and the little court answered, '
        f'"{section.refrain}!"'
    )


def choose_treat(world: World, hero: Entity, treat: TreatCfg) -> None:
    world.say(
        f"{hero.title} picked {treat.phrase} for the walk. It looked so fine and shiny "
        f"that {hero.pronoun()} stood a bit taller just for carrying it."
    )
    world.say(
        f"But {treat.wobble_sign}, as if the treat itself already knew a funny thing "
        f"might happen before the rhyme was through."
    )


def warn(world: World, helper: Entity, hero: Entity, support: SupportCfg,
         treat: TreatCfg, severity: int) -> None:
    pred = predict_wobble(world, severity)
    world.facts["predicted_wobble"] = pred["wobble"]
    helper.memes["care"] += 1
    extra = " even before the marching drum went dum-dum-dum" if pred["risky"] else ""
    world.say(
        f'{helper.title} peeped at the {treat.label} and whispered, "{treat.label.capitalize()}s '
        f"do not like a bouncy walk. We should use {support.label}."
        f"{extra}."
    )


def boast(world: World, hero: Entity, section: SectionCfg) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I can manage," said {hero.title}, giving one brave little nod. '
        f'"I know the {section.label} beat: {section.beat}."'
    )


def start_march(world: World, court: CourtCfg, section: SectionCfg, treat: TreatCfg) -> int:
    severity = hazard_value(court, section, treat)
    world.get("treat").meters["wobble"] += float(severity)
    propagate(world, narrate=False)
    world.say(
        f"So off went the {section.label}: {section.move}. The {treat.label} gave one wobble, "
        f"then another, then a wobble that looked quite too proud of itself."
    )
    if severity >= 6:
        world.say(
            f"Even the spoons in the watching crowd leaned sideways to stare. "
            f"The whole court went hush-hush-hush."
        )
    else:
        world.say(
            f"A tiny gasp ran through the court, small as a mouse sneeze."
        )
    return severity


def steady_success(world: World, helper: Entity, hero: Entity, judge: Entity,
                   support: SupportCfg, treat: TreatCfg, section: SectionCfg) -> None:
    world.get("treat").meters["wobble"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Then {helper.title} {support.text}. At once the silly wobble settled down, "
        f"and the {treat.label} rode as calm as moonlight on milk."
    )
    world.say(
        f"{judge.title} laughed so softly that even the lilies seemed to bob. "
        f'"Well done," {judge.pronoun()} said. "A good tradition may keep its tune, '
        f'and a wise tradition may learn a new step too."'
    )
    world.say(
        f"From that day on, the {section.label} was allowed to use {support.label} "
        f"whenever a treat looked tall or trembly."
    )


def steady_fail(world: World, helper: Entity, hero: Entity, judge: Entity,
                support: SupportCfg, treat: TreatCfg) -> None:
    world.get("treat").meters["spilled"] += 1
    propagate(world, narrate=False)
    hero.memes["sad"] += 1
    helper.memes["sad"] += 1
    world.say(
        f"{helper.title} {support.fail}, but the wobble had already learned too much mischief."
    )
    world.say(
        f"Down went the {treat.label} with {treat.splat}. Jam skittered one way, crumbs skipped "
        f"the other, and a stripe of topping landed on the empty cushion beside the judge."
    )
    world.say(
        f"{judge.title} blinked, then chuckled instead of scolding. "
        f'"Well," {judge.pronoun()} said, "the court has been fed, if not in the proper section."'
    )
    world.say(
        f"After the floor was wiped clean, the court changed the tradition: no one would carry "
        f"a tall treat alone again."
    )


def ending_image_success(world: World, court: CourtCfg, hero: Entity, helper: Entity,
                         support: SupportCfg, treat: TreatCfg) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Next Thursday in {court.label}, {hero.title} and {helper.title} crossed the court together. "
        f"The {treat.label} sat on {support.label}, steady as a button, and everyone sang the old "
        f"refrain with one new smile tucked inside it."
    )


def ending_image_fail(world: World, court: CourtCfg, hero: Entity, helper: Entity,
                      treat: TreatCfg) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Next Thursday in {court.label}, {hero.title} carried a smaller {treat.label} with {helper.title} beside "
        f"{hero.pronoun('object')}. Nothing wobbled, nothing toppled, and the rhyme came out tidy at last."
    )
@dataclass
class StoryParams:
    court: str
    section: str
    treat: str
    support: str
    hero_name: str
    hero_gender: str
    hero_species: str
    helper_name: str
    helper_gender: str
    helper_species: str
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


KNOWLEDGE = {
    "court": [
        (
            "What is a court in this story?",
            "A court here is a special meeting place where everyone gathers in order, watches a custom, and listens to a judge. It is not a game field; it is more like a little public square with rules."
        )
    ],
    "tradition": [
        (
            "What is a tradition?",
            "A tradition is something people do again and again in the same special way. It helps everyone remember what matters to their group."
        )
    ],
    "section": [
        (
            "What is a section?",
            "A section is one part of a bigger group. In a parade, each section has its own job and way of moving."
        )
    ],
    "tray": [
        (
            "Why does a tray help carry food?",
            "A tray gives food a flat, steady place to rest on. That makes it less likely to tip when someone walks."
        )
    ],
    "balance": [
        (
            "Why do two hands or paws help with balance?",
            "Using two hands or paws gives better control than using just one. It lets the carrier steady a wobble before it grows bigger."
        )
    ],
    "sharing": [
        (
            "Why can sharing a heavy or wobbly job be smart?",
            "Sharing means two people can steady the same thing together. If one side wiggles, the other side can help keep it safe."
        )
    ],
    "jelly": [
        (
            "Why does jelly wobble?",
            "Jelly is soft and jiggly, so it moves when the plate moves. A bouncy walk can make it shake even more."
        )
    ],
    "custard": [
        (
            "Why can a custard cup spill easily?",
            "Custard is soft and smooth, so a sharp bump can send it sloshing over the rim. That is why careful carrying matters."
        )
    ],
    "jam": [
        (
            "Why can jam make a funny mess?",
            "Jam is sticky and bright, so when it splashes it spreads and shows up everywhere. That is why a jam tart can turn a tiny wobble into a big laugh."
        )
    ],
}
KNOWLEDGE_ORDER = ["court", "section", "tradition", "tray", "balance", "sharing", "jelly", "custard", "jam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    court = f["court_cfg"]
    section = f["section_cfg"]
    treat = f["treat_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    if outcome == "contained":
        return [
            f'Write a short nursery-rhyme-style story set in {court.label.lower()} about a child in the {section.label.lower()} carrying a {treat.label}. Include the words "court", "section", and "tradition".',
            f"Tell a humorous story with foreshadowing where a wobble almost ruins a court tradition, but {support.label} saves the day.",
            f"Write a gentle story for young children where a proud little marcher learns that a tradition can stay kind and still change a little."
        ]
    return [
        f'Write a nursery-rhyme-style story in a tiny court where the {section.label.lower()} tries to carry a {treat.label}. Include the words "court", "section", and "tradition".',
        "Tell a humorous cautionary story with foreshadowing where a silly wobble becomes a splat, and the court changes the tradition for next time.",
        f"Write a child-facing story where a helper warns early, the warning proves true, and everyone learns to share the carrying."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    judge = f["judge"]
    court = f["court_cfg"]
    section = f["section_cfg"]
    treat = f["treat_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.title} and {helper.title} in {court.label}. They are part of the {section.label} and must carry a special treat across the court."
        ),
        (
            "What was the court tradition?",
            f"The tradition was that each section of the court carried a festival treat to {judge.label}'s stool. That custom is what made the little walk feel important."
        ),
        (
            f"Why did {helper.title} worry before the march?",
            f"{helper.title} saw signs that the {treat.label} would wobble. The warning came before the trouble, so it foreshadowed what the march would be like."
        ),
        (
            f"What made the treat hard to carry?",
            f"The {section.label} had a bouncy way of moving, and the {treat.label} was easy to wobble. Those two things together made the danger grow while they were still in the middle of the court."
        ),
    ]
    if outcome == "contained":
        qa.append(
            (
                "How was the problem solved?",
                f"{helper.title} {support.qa_text}. That stopped the wobble before it became a spill, so the tradition could continue in a wiser way."
            )
        )
        qa.append(
            (
                "How did the court change at the end?",
                f"The court kept the tradition, but it allowed extra help for tall or trembly treats. The ending shows that a good custom can change a little when everyone learns something useful."
            )
        )
    else:
        qa.append(
            (
                "What happened when the helper tried to help?",
                f"The help came too late for that much wobble, and the {treat.label} spilled across the tiles. The funny splat made everyone stare, but no one was hurt."
            )
        )
        qa.append(
            (
                "What changed after the spill?",
                f"The court changed the tradition so no one would carry a tall treat alone again. The mess became a lesson, and next time the rhyme ended neatly instead of with a flop."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"court", "section", "tradition"}
    f = world.facts
    tags |= set(f["support_cfg"].tags)
    tags |= set(f["treat_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        court="berry",
        section="ribbon",
        treat="jam_tart",
        support="helper_hold",
        hero_name="Mabel",
        hero_gender="girl",
        hero_species="Mouse",
        helper_name="Pip",
        helper_gender="boy",
        helper_species="Rabbit",
        delay=0,
    ),
    StoryParams(
        court="pebble",
        section="drum",
        treat="custard_cup",
        support="two_paws",
        hero_name="Tilly",
        hero_gender="girl",
        hero_species="Mole",
        helper_name="Otis",
        helper_gender="boy",
        helper_species="Hedgehog",
        delay=1,
    ),
    StoryParams(
        court="clover",
        section="spoon",
        treat="jelly_stack",
        support="silver_tray",
        hero_name="Daisy",
        hero_gender="girl",
        hero_species="Duckling",
        helper_name="Milo",
        helper_gender="boy",
        helper_species="Squirrel",
        delay=0,
    ),
    StoryParams(
        court="pebble",
        section="drum",
        treat="jelly_stack",
        support="helper_hold",
        hero_name="Nell",
        hero_gender="girl",
        hero_species="Mouse",
        helper_name="Bram",
        helper_gender="boy",
        helper_species="Rabbit",
        delay=2,
    ),
    StoryParams(
        court="berry",
        section="spoon",
        treat="seed_bun",
        support="two_paws",
        hero_name="Lulu",
        hero_gender="girl",
        hero_species="Squirrel",
        helper_name="Ned",
        helper_gender="boy",
        helper_species="Mole",
        delay=0,
    ),
]


def explain_rejection(court: CourtCfg, section: SectionCfg, treat: TreatCfg) -> str:
    return (
        f"(No story: {treat.label} in {section.label} at {court.label} does not create enough wobble "
        f"to make a real problem here. Pick a bumpier section or a more fragile treat.)"
    )


def explain_support(support_id: str) -> str:
    support = SUPPORTS[support_id]
    better = ", ".join(sorted(s.id for s in sensible_supports()))
    return (
        f"(Refusing support '{support_id}': it is too silly to count as a sensible fix "
        f"(sense={support.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return (
        "contained"
        if outcome_contains(
            SUPPORTS[params.support],
            COURTS[params.court],
            SECTIONS[params.section],
            TREATS[params.treat],
            params.delay,
        )
        else "spilled"
    )


ASP_RULES = r"""
hazard(C,S,T,V) :- court(C), section(S), treat(T),
                   bounce(C,BC), bump(S,BS), fragility(T,FT), V = BC + BS + FT.
valid(C,S,T)    :- hazard(C,S,T,V), hazard_min(M), V >= M.

sensible(P)     :- support(P), sense(P,N), sense_min(M), N >= M.
severity(V + D) :- chosen_court(C), chosen_section(S), chosen_treat(T),
                   hazard(C,S,T,V), delay(D).
contained       :- chosen_support(P), power(P,W), severity(SV), W >= SV.
outcome(contained) :- contained.
outcome(spilled)   :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, court in COURTS.items():
        lines.append(asp.fact("court", cid))
        lines.append(asp.fact("bounce", cid, court.bounce))
    for sid, section in SECTIONS.items():
        lines.append(asp.fact("section", sid))
        lines.append(asp.fact("bump", sid, section.bumpiness))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("fragility", tid, treat.fragility))
    for pid, support in SUPPORTS.items():
        lines.append(asp.fact("support", pid))
        lines.append(asp.fact("sense", pid, support.sense))
        lines.append(asp.fact("power", pid, support.power))
    lines.append(asp.fact("hazard_min", HAZARD_MIN))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_court", params.court),
            asp.fact("chosen_section", params.section),
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_support", params.support),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {s.id for s in sensible_supports()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible supports match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible supports: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a court tradition, a parade section, and a wobble."
    )
    ap.add_argument("--court", choices=COURTS)
    ap.add_argument("--section", choices=SECTIONS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name_gender(args_gender: Optional[str], given_name: Optional[str], rng: random.Random,
                      avoid: str = "") -> tuple[str, str]:
    gender = args_gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    if given_name:
        return given_name, gender
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.support and SUPPORTS[args.support].sense < SENSE_MIN:
        raise StoryError(explain_support(args.support))

    if args.court and args.section and args.treat:
        court = COURTS[args.court]
        section = SECTIONS[args.section]
        treat = TREATS[args.treat]
        if hazard_value(court, section, treat) < HAZARD_MIN:
            raise StoryError(explain_rejection(court, section, treat))

    combos = [
        c for c in valid_combos()
        if (args.court is None or c[0] == args.court)
        and (args.section is None or c[1] == args.section)
        and (args.treat is None or c[2] == args.treat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    court_id, section_id, treat_id = rng.choice(sorted(combos))
    support_id = args.support or rng.choice(sorted(s.id for s in sensible_supports()))
    hero_name, hero_gender = _pick_name_gender(args.hero_gender, args.hero_name, rng)
    helper_name, helper_gender = _pick_name_gender(args.helper_gender, args.helper_name, rng, avoid=hero_name)
    hero_species = rng.choice(SPECIES)
    helper_species = rng.choice([s for s in SPECIES if s != hero_species] or SPECIES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        court=court_id,
        section=section_id,
        treat=treat_id,
        support=support_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_species=helper_species,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        court = COURTS[params.court]
        section = SECTIONS[params.section]
        treat = TREATS[params.treat]
        support = SUPPORTS[params.support]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if hazard_value(court, section, treat) < HAZARD_MIN:
        raise StoryError(explain_rejection(court, section, treat))
    if support.sense < SENSE_MIN:
        raise StoryError(explain_support(params.support))

    world = tell(
        court=court,
        section=section,
        treat=treat,
        support=support,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_species=params.hero_species,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_species=params.helper_species,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible supports: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (court, section, treat) combos:\n")
        for court, section, treat in combos:
            print(f"  {court:7} {section:7} {treat}")
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
            header = (
                f"### {p.hero_name} in {p.court} court: {p.section} section with {p.treat} "
                f"({p.support}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(court: CourtCfg, section: SectionCfg, treat: TreatCfg, support: SupportCfg,
         hero_name: str = "Mabel", hero_gender: str = "girl", hero_species: str = "Mouse",
         helper_name: str = "Pip", helper_gender: str = "boy", helper_species: str = "Rabbit",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"species": hero_species, "name": hero_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        attrs={"species": helper_species, "name": helper_name},
    ))
    judge_type = "duck" if "Duck" in court.judge else "goose_hen"
    judge = world.add(Entity(
        id="judge",
        kind="character",
        type=judge_type,
        label=court.judge,
        role="judge",
        attrs={"species": court.judge.split()[-1], "name": court.judge},
    ))
    court_ent = world.add(Entity(
        id="court",
        kind="thing",
        type="place",
        label=court.label,
        role="place",
    ))
    treat_ent = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        role="treat",
    ))

    world.facts.update(
        court_cfg=court,
        section_cfg=section,
        treat_cfg=treat,
        support_cfg=support,
        delay=delay,
        hero=hero,
        helper=helper,
        judge=judge,
        court=court_ent,
        treat=treat_ent,
    )

    open_court(world, court, section, hero, helper, judge)
    choose_treat(world, hero, treat)

    world.para()
    severity = hazard_value(court, section, treat)
    warn(world, helper, hero, support, treat, severity)
    boast(world, hero, section)
    march_severity = start_march(world, court, section, treat)
    world.facts["severity"] = march_severity

    world.para()
    contained = outcome_contains(support, court, section, treat, delay)
    if contained:
        steady_success(world, helper, hero, judge, support, treat, section)
        world.para()
        ending_image_success(world, court, hero, helper, support, treat)
        outcome = "contained"
    else:
        steady_fail(world, helper, hero, judge, support, treat)
        world.para()
        ending_image_fail(world, court, hero, helper, treat)
        outcome = "spilled"

    world.facts["outcome"] = outcome
    world.facts["contained"] = contained
    world.facts["spilled"] = not contained
    return world


COURTS = {
    "berry": CourtCfg(
        id="berry",
        label="Berry Court",
        judge="Judge Goose",
        floor="red-and-cream berry tiles",
        bounce=1,
        image="The berry flags twitched, the benches blinked in the sun, and the sparrows looked ready for a rhyme.",
        tags={"court", "tradition"},
    ),
    "clover": CourtCfg(
        id="clover",
        label="Clover Court",
        judge="Judge Duck",
        floor="soft clover stones",
        bounce=0,
        image="The clover leaves made cool green shadows, and even the breeze seemed to hop in time.",
        tags={"court", "tradition"},
    ),
    "pebble": CourtCfg(
        id="pebble",
        label="Pebble Court",
        judge="Judge Goose",
        floor="round pebble squares",
        bounce=2,
        image="The pebbles clicked under small shoes, and every click sounded like a secret little drum.",
        tags={"court", "tradition"},
    ),
}

SECTIONS = {
    "ribbon": SectionCfg(
        id="ribbon",
        label="Ribbon Section",
        move="twirl, step, twirl",
        beat="swish-swish, dip and glide",
        bumpiness=2,
        refrain="Ribbon section, bright and light",
        tags={"section", "parade"},
    ),
    "spoon": SectionCfg(
        id="spoon",
        label="Spoon Section",
        move="tiptoe, tiptoe, tick",
        beat="tiny taps and careful toes",
        bumpiness=1,
        refrain="Spoon section, steady and soon",
        tags={"section", "parade"},
    ),
    "drum": SectionCfg(
        id="drum",
        label="Drum Section",
        move="thump, bounce, thump",
        beat="dum-dum, proud and loud",
        bumpiness=3,
        refrain="Drum section, beat the day",
        tags={"section", "parade"},
    ),
}

TREATS = {
    "seed_bun": TreatCfg(
        id="seed_bun",
        label="seed bun",
        phrase="a round seed bun with a shiny top",
        fragility=1,
        wobble_sign="the poppy seeds gave a tiny shiver",
        splat="a polite little pluff",
        topping="poppy seeds",
        tags={"bun", "food"},
    ),
    "jam_tart": TreatCfg(
        id="jam_tart",
        label="jam tart",
        phrase="a jam tart with a red wink in the middle",
        fragility=2,
        wobble_sign="the jam winked and trembled at the edges",
        splat="a merry red splish",
        topping="jam",
        tags={"tart", "food", "jam"},
    ),
    "custard_cup": TreatCfg(
        id="custard_cup",
        label="custard cup",
        phrase="a custard cup with a lemon-yellow top",
        fragility=3,
        wobble_sign="the custard made a tiny quiver, as if it were trying not to sneeze",
        splat="a yellow flup and a buttery slide",
        topping="custard",
        tags={"custard", "food"},
    ),
    "jelly_stack": TreatCfg(
        id="jelly_stack",
        label="jelly stack",
        phrase="a tall jelly stack with a cherry on top",
        fragility=4,
        wobble_sign="the cherry nodded once, and the jelly gave a see-through shimmy",
        splat="a bright pink boing and a slippery flop",
        topping="cherry",
        tags={"jelly", "food"},
    ),
}

SUPPORTS = {
    "silver_tray": SupportCfg(
        id="silver_tray",
        label="the silver tray",
        sense=3,
        power=5,
        text="slid the silver tray under it and matched the marching beat with both paws",
        fail="slid the silver tray under it",
        qa_text="used the silver tray to steady the treat",
        tags={"tray", "help"},
    ),
    "two_paws": SupportCfg(
        id="two_paws",
        label="both paws",
        sense=2,
        power=3,
        text="reached in and tucked both paws around the plate until the wobble gave up",
        fail="reached in with both paws",
        qa_text="held the plate with both paws",
        tags={"balance", "help"},
    ),
    "helper_hold": SupportCfg(
        id="helper_hold",
        label="a shared carry",
        sense=3,
        power=4,
        text="caught the plate from below so the two of them carried it together",
        fail="caught the plate from below",
        qa_text="helped carry the treat together",
        tags={"help", "sharing"},
    ),
    "tall_hat": SupportCfg(
        id="tall_hat",
        label="a tall hat",
        sense=1,
        power=0,
        text="tried to balance it on a tall hat like a circus trick",
        fail="tried to balance it on a tall hat like a circus trick",
        qa_text="balanced it on a tall hat",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Nell", "Daisy", "Poppy", "Lulu"]
BOY_NAMES = ["Pip", "Toby", "Milo", "Otis", "Ned", "Bram"]
SPECIES = ["Mouse", "Rabbit", "Mole", "Squirrel", "Duckling", "Hedgehog"]

if __name__ == "__main__":
    main()
