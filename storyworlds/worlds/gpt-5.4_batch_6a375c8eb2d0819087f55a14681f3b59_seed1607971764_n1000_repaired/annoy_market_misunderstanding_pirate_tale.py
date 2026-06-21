#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py
========================================================================

A standalone storyworld about two children in a busy harbor market who are
playing pirates. A misunderstanding over which basket to fetch leads to a small
moment of annoyance, then a calmer fix: the children slow down, ask or check the
right symbol, and make things right.

The core world logic is:

    hurried grab + wrong symbol        -> mix-up + vendor annoyance
    apology + sensible fix             -> annoyance melts + relief rises
    older cautious sibling intervenes  -> misunderstanding averted before the grab

The world prefers plausible misunderstandings only: the mistaken basket must be
easy to confuse with the wanted one, sharing the same color while differing in
symbol. Low-common-sense "fixes" are known to the world but refused.

Run it
------
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py --wanted apples --mistaken tomatoes
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py --fix guess_again
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/annoy_market_misunderstanding_pirate_tale.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


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
    rig: str
    titles: tuple[str, str]
    mission: str
    send_off: str
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


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    color: str
    symbol: str
    stall: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def badge(self) -> str:
        return f"{self.color} basket with the {self.symbol}"
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
    sense: int
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "request_symbol": "",
            "request_color": "",
            "wanted_id": "",
            "grabbed_id": "",
            "used_fix": "",
        }

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


def _r_mixup(world: World) -> list[str]:
    out: list[str] = []
    grabbed = world.facts.get("grabbed_id", "")
    wanted = world.facts.get("wanted_id", "")
    request_symbol = world.facts.get("request_symbol", "")
    if not grabbed or not wanted or not request_symbol:
        return out
    cargo = world.entities.get(grabbed)
    vendor = world.entities.get("Vendor")
    instigator = next((k for k in world.kids() if k.role == "instigator"), None)
    cautioner = next((k for k in world.kids() if k.role == "cautioner"), None)
    if cargo is None or vendor is None or instigator is None or cautioner is None:
        return out
    if cargo.attrs.get("symbol") == request_symbol:
        return out
    sig = ("mixup", grabbed, wanted)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["misplaced"] += 1
    vendor.memes["annoyance"] += 1
    instigator.memes["confusion"] += 1
    cautioner.memes["worry"] += 1
    world.get("market").meters["tangle"] += 1
    out.append("__mixup__")
    return out


def _r_apology(world: World) -> list[str]:
    out: list[str] = []
    vendor = world.entities.get("Vendor")
    if vendor is None:
        return out
    if vendor.memes["annoyance"] < THRESHOLD:
        return out
    apologized = any(k.memes["apology"] >= THRESHOLD for k in world.kids())
    if not apologized:
        return out
    sig = ("apology",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vendor.memes["annoyance"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="mixup", tag="social", apply=_r_mixup),
    Rule(name="apology", tag="social", apply=_r_apology),
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


def confusion_possible(wanted: Cargo, mistaken: Cargo) -> bool:
    return wanted.id != mistaken.id and wanted.color == mistaken.color and wanted.symbol != mistaken.symbol


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_mixup(world: World, grabbed_id: str) -> dict:
    sim = world.copy()
    _grab_wrong(sim, sim.get(grabbed_id), narrate=False)
    vendor = sim.get("Vendor")
    cargo = sim.get(grabbed_id)
    return {
        "annoyed": vendor.memes["annoyance"] >= THRESHOLD,
        "misplaced": cargo.meters["misplaced"] >= THRESHOLD,
    }


def _grab_wrong(world: World, cargo_ent: Entity, narrate: bool = True) -> None:
    cargo_ent.meters["carried"] += 1
    world.facts["grabbed_id"] = cargo_ent.id
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright morning, {a.id} and {b.id} skipped into the harbor market and turned it into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" {a.id} cried. "Let\'s {theme.mission}!"'
    )


def mission(world: World, parent: Entity, a: Entity, b: Entity, wanted: Cargo) -> None:
    world.say(
        f"Between the fish stall and the fruit stall, {a.id}'s {parent.label_word} handed the children one shiny coin. "
        f'"Please bring me {wanted.the} from {wanted.stall}," {parent.pronoun()} said. '
        f'"Look for {wanted.badge}."'
    )
    world.facts["request_symbol"] = wanted.symbol
    world.facts["request_color"] = wanted.color
    world.facts["wanted_id"] = wanted.id
    a.attrs["heard_color"] = wanted.color
    a.attrs["heard_symbol"] = wanted.symbol
    b.attrs["heard_color"] = wanted.color
    b.attrs["heard_symbol"] = wanted.symbol


def tempt(world: World, a: Entity, mistaken: Cargo) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"The market was full of calls and clatter. When {a.id} spotted {mistaken.badge}, "
        f'''{a.pronoun('possessive')} eyes lit up. "It\'s red! That must be it," {a.pronoun()} whispered.'''
    )


def warn(world: World, b: Entity, a: Entity, wanted: Cargo, mistaken: Cargo, parent: Entity) -> None:
    pred = predict_mixup(world, mistaken.id)
    world.facts["predicted_annoyed"] = pred["annoyed"]
    b.memes["caution"] += 1
    extra = ""
    if pred["annoyed"]:
        extra = f" {b.pronoun().capitalize()} could almost hear the seller being annoyed already."
    world.say(
        f'{b.id} tugged at {a.id}\'s sleeve. "Wait. {parent.label_word.capitalize()} said {wanted.badge}, not the one with the {mistaken.symbol}."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, mistaken: Cargo) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Pirates are quick," {a.id} said, and before {b.id} could stop {a.pronoun("object")}, '
        f'{a.pronoun()} lifted {mistaken.the} from the stall.'
    )


def back_down(world: World, a: Entity, b: Entity, wanted: Cargo) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} froze, then looked again. The painted {wanted.symbol} was on the other basket after all. '
        f'"Oh," {a.pronoun()} said softly. "I was hurrying too fast."'
    )


def vendor_objects(world: World, vendor: Entity, mistaken: Cargo) -> None:
    vendor.memes["speaking"] += 1
    world.say(
        f'"Ahoy there," called the seller from {mistaken.stall}. "{mistaken.the.capitalize()} is for another customer." '
        f'The sharpness in {vendor.pronoun("possessive")} voice made the mistake feel suddenly heavy.'
    )
    world.say(
        f'For one small moment, the mix-up did annoy the seller, because {mistaken.the} belonged in a different pair of waiting hands.'
    )


def apply_fix(world: World, vendor: Entity, a: Entity, b: Entity, wanted: Cargo, mistaken: Cargo, fix: Fix) -> None:
    world.facts["used_fix"] = fix.id
    a.memes["apology"] += 1
    b.memes["apology"] += 1
    world.say(f"{a.id} hugged the basket close for half a second, then set it back exactly where it had been.")
    if fix.id == "ask_vendor":
        world.say(
            f'{b.id} looked up at the seller. "We got mixed up. Which one has the {wanted.symbol}?" '
            f'The seller pointed to {wanted.badge} and nodded once.'
        )
    elif fix.id == "check_symbol":
        world.say(
            f'{b.id} touched the painted marks one by one. "{mistaken.symbol}... {wanted.symbol}... there," {b.pronoun()} said, '
            f'and together they found {wanted.badge}.'
        )
    elif fix.id == "compare_list":
        world.say(
            f'{a.id} unfolded the little shopping note from {parent_word(world)}\'s pocket. Beside the word for {wanted.label} was a tiny {wanted.symbol}, '
            f'and that was enough to guide them to the right basket.'
        )
    world.say(
        f'{a.id} swallowed hard. "Sorry. I only remembered the {wanted.color} part," {a.pronoun()} said.'
    )
    propagate(world, narrate=False)
    world.say(
        f'The seller\'s face softened, and {vendor.pronoun()} handed them {wanted.the} at last.'
    )


def parent_word(world: World) -> str:
    parent = world.facts.get("parent")
    if isinstance(parent, Entity):
        return parent.label_word
    return "mom"


def ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, wanted: Cargo, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if outcome == "averted":
        world.say(
            f'Back by the striped awning, {parent.label_word.capitalize()} smiled when they brought the right basket the first time. '
            f'"A good crew checks the mark before it grabs the treasure," {parent.pronoun()} said.'
        )
    else:
        world.say(
            f'Back by the striped awning, {parent.label_word.capitalize()} listened to the whole story and squeezed both their shoulders. '
            f'"When a market sounds noisy, slow your pirate feet and check the mark," {parent.pronoun()} said. "That keeps small mistakes from growing."'
        )
    world.say(
        f'Soon the children sat on an upturned crate, sharing slices from {wanted.the} while gulls wheeled above the sails of the market. '
        f'This time they were still {theme.send_off}, but now they were careful pirates too.'
    )
@dataclass
class StoryParams:
    theme: str
    wanted: str
    mistaken: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
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
    "market": [
        (
            "What is a market?",
            "A market is a place where many people bring food or goods to sell. It can be busy and noisy because lots of people are choosing things at once.",
        )
    ],
    "symbol": [
        (
            "Why do symbols on baskets help?",
            "A symbol is a little picture or mark that helps you tell one thing from another. When two baskets are the same color, the symbol helps you pick the right one.",
        )
    ],
    "apology": [
        (
            "Why is saying sorry important after a mix-up?",
            "Saying sorry shows that you know your mistake affected someone else. It helps people calm down and trust that you want to make things right.",
        )
    ],
    "ask": [
        (
            "What should you do if you are not sure which thing is yours in a store or market?",
            "You should stop and ask a grown-up or the seller before taking it. Asking is better than guessing when other people are waiting too.",
        )
    ],
    "list": [
        (
            "What is a shopping list for?",
            "A shopping list helps you remember what to get. It can also have little notes or pictures so you can check instead of hurrying and guessing.",
        )
    ],
    "apples": [
        (
            "Where do apples grow?",
            "Apples grow on trees in orchards. They are picked when they are ripe and ready to eat.",
        )
    ],
    "tomatoes": [
        (
            "Are tomatoes fruit or vegetables?",
            "Tomatoes are fruits because they grow from the flower part of a plant and hold seeds inside. People often cook them like vegetables.",
        )
    ],
    "lemons": [
        (
            "Why do lemons taste sour?",
            "Lemons taste sour because they have a lot of acid in their juice. That sharp taste is what makes your mouth pucker.",
        )
    ],
    "corn": [
        (
            "What grows on a corn plant?",
            "Corn grows on a tall plant in ears covered with husks. Inside are rows of yellow kernels.",
        )
    ],
    "pears": [
        (
            "What does a pear feel like when it is ripe?",
            "A ripe pear feels a little soft near the top by the stem. That means it is ready to eat soon.",
        )
    ],
    "herbs": [
        (
            "What are herbs?",
            "Herbs are leafy plants used to add smell and flavor to food. Many of them smell strong and fresh when you rub them gently.",
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "symbol", "ask", "list", "apology", "apples", "tomatoes", "lemons", "corn", "pears", "herbs"]


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
    wanted = f["wanted_cfg"]
    mistaken = f["mistaken_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-flavored market story for a 3-to-5-year-old where two children mix up baskets because of a misunderstanding. '
        f'Include the word "annoy".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} almost grabs {mistaken.the}, but {b.id} helps {a.pronoun('object')} notice the {wanted.symbol} mark first, so the mistake never happens.",
            f"Write a market tale with little pirate pretend-play where an older sibling stops a misunderstanding before anyone gets annoyed.",
        ]
    return [
        base,
        f"Tell a harbor-market story where {a.id} remembers only the {wanted.color} part of the instruction, takes {mistaken.the}, and annoys a seller before the children apologize and fix the mix-up.",
        f"Write a simple story in a Pirate Tale style where the right basket is found by checking the mark instead of guessing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    vendor = f["vendor"]
    wanted = f["wanted_cfg"]
    mistaken = f["mistaken_cfg"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, at a busy harbor market with {a.id}'s {parent.label_word}. They were pretending to be little pirates on an errand.",
        ),
        (
            "What did the parent ask them to get?",
            f"{parent.label_word.capitalize()} asked them to bring {wanted.the} and to look for {wanted.badge}. The special mark mattered because another basket shared the same color.",
        ),
        (
            f"Why did {a.id} get confused?",
            f"{a.id} hurried and remembered only the {wanted.color} part of the instruction. That caused the misunderstanding, because {mistaken.the} was the same color but had a different symbol.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the mistake stopped before anyone got annoyed?",
                f"{b.id} slowed {a.id} down and pointed out the right {wanted.symbol} mark. Because they checked the symbol before grabbing anything, the seller never had a reason to feel annoyed.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They brought back the right basket on the first try and learned that careful pirates check the mark before they take treasure. The ending shows the change because they were still playful, but no longer rushing blindly.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the wrong basket was picked up?",
                f"The seller called out because {mistaken.the} was meant for someone else, and for a moment the mix-up did annoy her. The problem came from taking something before checking the full mark.",
            )
        )
        qa.append(
            (
                "How did they fix the misunderstanding?",
                f"{fix.qa_text} Then they put the wrong basket back and said sorry. That worked because the fix gave them the missing information instead of another guess.",
            )
        )
        qa.append(
            (
                f"Why did the seller calm down?",
                f"The seller saw that the children returned the basket and apologized right away. Once they made things right, there was no reason to stay annoyed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    wanted = f["wanted_cfg"]
    mistaken = f["mistaken_cfg"]
    fix = f["fix"]
    tags = {"market"} | set(wanted.tags) | set(mistaken.tags) | set(fix.tags)
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
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        wanted="apples",
        mistaken="tomatoes",
        fix="check_symbol",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="corsairs",
        wanted="lemons",
        mistaken="corn",
        fix="ask_vendor",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="thoughtful",
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="sailors",
        wanted="pears",
        mistaken="herbs",
        fix="compare_list",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
]


def explain_rejection(wanted: Cargo, mistaken: Cargo) -> str:
    return (
        f"(No story: {wanted.the} and {mistaken.the} are not a good misunderstanding pair. "
        f"A mix-up here must share a color but differ in symbol, so the child can reasonably remember the color and miss the mark.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = " / ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). This world prefers a fix that checks or asks instead of guessing. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "corrected"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
confusable(W, M) :- cargo(W), cargo(M), W != M,
                    color(W, C), color(M, C),
                    symbol(W, SW), symbol(M, SM), SW != SM.
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, W, M) :- theme(T), confusable(W, M).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(corrected) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("color", cargo_id, cargo.color))
        lines.append(asp.fact("symbol", cargo_id, cargo.symbol))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
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


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_fixes = set(asp_sensible())
    python_fixes = {f.id for f in sensible_fixes()}
    if clingo_fixes == python_fixes:
        print(f"OK: sensible fixes match ({sorted(clingo_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fixes)} python={sorted(python_fixes)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a harbor market misunderstanding in a pirate-tale style."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--wanted", choices=CARGOS)
    ap.add_argument("--mistaken", choices=CARGOS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.wanted and args.mistaken:
        wanted = CARGOS[args.wanted]
        mistaken = CARGOS[args.mistaken]
        if not confusion_possible(wanted, mistaken):
            raise StoryError(explain_rejection(wanted, mistaken))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.wanted is None or combo[1] == args.wanted)
        and (args.mistaken is None or combo[2] == args.mistaken)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, wanted_id, mistaken_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme_id,
        wanted=wanted_id,
        mistaken=mistaken_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.wanted not in CARGOS:
        raise StoryError(f"(Unknown wanted cargo: {params.wanted})")
    if params.mistaken not in CARGOS:
        raise StoryError(f"(Unknown mistaken cargo: {params.mistaken})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    wanted = CARGOS[params.wanted]
    mistaken = CARGOS[params.mistaken]
    fix = FIXES[params.fix]

    if not confusion_possible(wanted, mistaken):
        raise StoryError(explain_rejection(wanted, mistaken))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        theme=THEMES[params.theme],
        wanted=wanted,
        mistaken=mistaken,
        fix=fix,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, wanted, mistaken) combos:\n")
        for theme_id, wanted_id, mistaken_id in combos:
            print(f"  {theme_id:9} {wanted_id:10} {mistaken_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: wanted {p.wanted}, mistook {p.mistaken} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    theme: Theme,
    wanted: Cargo,
    mistaken: Cargo,
    fix: Fix,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    vendor = world.add(Entity(
        id="Vendor",
        kind="character",
        type="woman",
        role="vendor",
        label="the seller",
    ))
    market = world.add(Entity(id="market", type="market", label="the market"))

    world.facts["parent"] = parent
    world.add(Entity(
        id=wanted.id,
        type="cargo",
        label=wanted.label,
        attrs={"color": wanted.color, "symbol": wanted.symbol, "stall": wanted.stall},
    ))
    world.add(Entity(
        id=mistaken.id,
        type="cargo",
        label=mistaken.label,
        attrs={"color": mistaken.color, "symbol": mistaken.symbol, "stall": mistaken.stall},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme)
    mission(world, parent, a, b, wanted)

    world.para()
    tempt(world, a, mistaken)
    warn(world, b, a, wanted, mistaken, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, wanted)
        world.say(
            f'Together they carried {wanted.the} over to {parent.label_word}, bright and proud and unhurried.'
        )
        outcome = "averted"
    else:
        defy(world, a, b, mistaken)
        world.para()
        _grab_wrong(world, world.get(mistaken.id), narrate=False)
        vendor_objects(world, vendor, mistaken)
        world.para()
        apply_fix(world, vendor, a, b, wanted, mistaken, fix)
        outcome = "corrected"

    world.para()
    ending(world, parent, a, b, theme, wanted, outcome)

    world.facts.update(
        theme=theme,
        wanted_cfg=wanted,
        mistaken_cfg=mistaken,
        fix=fix,
        instigator=a,
        cautioner=b,
        parent=parent,
        vendor=vendor,
        outcome=outcome,
        relation=relation,
        corrected=outcome == "corrected",
        averted=outcome == "averted",
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a little pirate harbor",
        rig="The striped awnings looked like sails, the stacked crates looked like treasure chests, and the wet cobbles gleamed like a deck after spray.",
        titles=("Captain", "Scout"),
        mission="win the market treasure",
        send_off="pirates on an errand",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a busy sea fort",
        rig="The fruit stalls were bright as flags, the fish barrels felt like dockside cargo, and every bell and gull cry sounded like a harbor warning.",
        titles=("Captain", "Mate"),
        mission="fetch the morning treasure",
        send_off="small corsairs on a good course",
    ),
    "sailors": Theme(
        id="sailors",
        scene="a windy quay",
        rig="The hanging ropes looked like ship lines, the stalls made little lanes like a port, and the whole place smelled of salt and oranges.",
        titles=("Skipper", "Lookout"),
        mission="bring home the best prize from shore",
        send_off="sailors with steadier eyes",
    ),
}

CARGOS = {
    "apples": Cargo(
        id="apples",
        label="basket of apples",
        phrase="a basket of apples",
        color="red",
        symbol="star",
        stall="the fruit stall",
        tags={"apples", "market", "symbol"},
    ),
    "tomatoes": Cargo(
        id="tomatoes",
        label="basket of tomatoes",
        phrase="a basket of tomatoes",
        color="red",
        symbol="crab",
        stall="the fruit stall",
        tags={"tomatoes", "market", "symbol"},
    ),
    "lemons": Cargo(
        id="lemons",
        label="basket of lemons",
        phrase="a basket of lemons",
        color="yellow",
        symbol="moon",
        stall="the citrus stall",
        tags={"lemons", "market", "symbol"},
    ),
    "corn": Cargo(
        id="corn",
        label="bundle of corn",
        phrase="a bundle of corn",
        color="yellow",
        symbol="anchor",
        stall="the farm stall",
        tags={"corn", "market", "symbol"},
    ),
    "pears": Cargo(
        id="pears",
        label="basket of pears",
        phrase="a basket of pears",
        color="green",
        symbol="leaf",
        stall="the orchard stall",
        tags={"pears", "market", "symbol"},
    ),
    "herbs": Cargo(
        id="herbs",
        label="bundle of herbs",
        phrase="a bundle of herbs",
        color="green",
        symbol="shell",
        stall="the herb stall",
        tags={"herbs", "market", "symbol"},
    ),
}

FIXES = {
    "ask_vendor": Fix(
        id="ask_vendor",
        sense=3,
        text="ask the seller which basket matched the mark",
        qa_text="They asked the seller which basket had the right mark.",
        tags={"ask", "apology", "market"},
    ),
    "check_symbol": Fix(
        id="check_symbol",
        sense=3,
        text="compare the painted symbols instead of guessing",
        qa_text="They slowed down and compared the painted symbols.",
        tags={"symbol", "apology", "market"},
    ),
    "compare_list": Fix(
        id="compare_list",
        sense=2,
        text="look at the shopping note again",
        qa_text="They checked the little shopping note and matched the symbol.",
        tags={"list", "symbol", "market"},
    ),
    "guess_again": Fix(
        id="guess_again",
        sense=1,
        text="guess one more time and hope",
        qa_text="They guessed again.",
        tags={"guess"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "curious", "cheerful", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for theme_id in THEMES:
        for wanted_id, wanted in CARGOS.items():
            for mistaken_id, mistaken in CARGOS.items():
                if confusion_possible(wanted, mistaken):
                    combos.append((theme_id, wanted_id, mistaken_id))
    return combos

if __name__ == "__main__":
    main()
