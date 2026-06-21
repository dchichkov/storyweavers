#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py
=================================================================

A standalone story world for a small pirate-flavored backyard tale built from the
seed words "braid" and "feeder" plus the narrative feature of repetition.

Premise
-------
Two children turn the yard into a pirate cove. One child spots something shiny
caught near a bird feeder and wants to grab it the quick, risky way by climbing
on an unstable object. The other child warns that the perch could tip. A calm
grown-up either helps safely with the right reaching tool, or -- if the chosen
tool is too weak for the height -- the child slips, gets a scrape, and learns to
ask for help first.

The world is constrained on purpose:
- only tall hanging feeders create a real reaching problem;
- only unstable perches make the unsafe shortcut reasonable;
- only rescue tools that safely reach the feeder are accepted;
- random generation chooses only valid combinations.

Run it
------
python storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py
python storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py --seed 7 --qa
python storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py --asp
python storyworlds/worlds/gpt-5.4/braid_feeder_repetition_pirate_tale.py --verify
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
    stable: bool = True
    climbable: bool = False
    reachable: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    instigator_gender: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "she" if self.attrs.get("hair") == "braid" and self.type == "boy_braid_override" else "he",
                    "object": "him", "possessive": "his"}[case]
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
    captain: str
    mate: str
    goal: str
    launch: str
    role_plural: str
    ending: str
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
class Feeder:
    id: str
    label: str
    phrase: str
    height: int
    sway: str
    treasure: str
    hook_spot: str
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
    stable: bool
    climbable: bool
    risk: int
    wobble_text: str
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    adult_guided: bool
    text: str
    fail: str
    qa_text: str
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


def _r_tip(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    instigator = world.facts.get("instigator")
    feeder = world.get("feeder")
    if not isinstance(instigator, Entity):
        return out
    if instigator.meters["climbing"] < THRESHOLD:
        return out
    if perch.stable:
        return out
    sig = ("tip", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["tipping"] += 1
    instigator.meters["off_balance"] += 1
    instigator.memes["fear"] += 1
    if feeder:
        feeder.meters["swinging"] += 1
    out.append("__tip__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    instigator = world.facts.get("instigator")
    if not isinstance(instigator, Entity):
        return out
    if instigator.meters["off_balance"] < THRESHOLD:
        return out
    if world.facts.get("caught_in_time", False):
        return out
    sig = ("fall", instigator.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    instigator.meters["fell"] += 1
    instigator.meters["scraped"] += 1
    instigator.memes["fear"] += 1
    instigator.memes["tears"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES = [
    Rule(name="tip", tag="physical", apply=_r_tip),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


def hazard_at_risk(feeder: Feeder, perch: Perch) -> bool:
    return feeder.height >= 2 and perch.climbable and not perch.stable


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def retrieval_difficulty(feeder: Feeder) -> int:
    return feeder.height


def can_reach(tool: Tool, feeder: Feeder) -> bool:
    return tool.reach >= retrieval_difficulty(feeder)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_tip(world: World) -> dict:
    sim = world.copy()
    instigator = sim.get(world.facts["instigator"].id)
    instigator.meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "tip": sim.get("perch").meters["tipping"] >= THRESHOLD,
        "fall": instigator.meters["fell"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    hair = f" with a long {a.attrs['hair']}" if a.attrs.get("hair") == "braid" else ""
    world.say(
        f"On a bright afternoon, {a.id}{hair} and {b.id} turned the backyard into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} cried. '
        f'"{theme.launch}"'
    )


def spot_treasure(world: World, b: Entity, feeder: Feeder, theme: Theme) -> None:
    world.say(
        f"Then {b.id} pointed past the sand pit and the flower pots. "
        f"A shiny bit of treasure was caught on {feeder.phrase}, where it {feeder.sway}."
    )
    world.say(
        f'"There! There! Treasure on the feeder, treasure on the feeder!" '
        f'{b.id} said. The words bounced through the game like a pirate bell.'
    )
    world.say(
        f"It was {feeder.treasure}, and now it looked like the last prize between them and {theme.goal}."
    )


def tempt(world: World, a: Entity, feeder: Feeder, perch: Perch) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} squinted up at the feeder. "{perch.phrase}!" {a.pronoun().capitalize()} said. '
        f'"I can climb up and snatch {feeder.treasure} myself."'
    )
    world.say(f"For one exciting breath, the shortcut felt bold and clever.")


def warn(world: World, b: Entity, a: Entity, perch: Perch, parent: Entity) -> None:
    pred = predict_tip(world)
    b.memes["caution"] += 1
    world.facts["predicted_tip"] = pred["tip"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f' "{perch.label.capitalize()}s wobble, wobble, wobble," {b.id} added.'
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "{a.id}, no. {parent.label_word.capitalize()} said not to climb on {perch.label}s." '
        f'"{perch.label.capitalize()}s tip, and tippy things make people fall."{extra}'
    )


def defy(world: World, a: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just quick-quick-quick," {a.id} said, and hurried to {perch.phrase}.'
    )


def back_down(world: World, a: Entity, b: Entity, perch: Perch, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sib = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"Just quick-quick-quick," {a.id} started to say. But {b.id} was {a.pronoun("possessive")} big {sib}, '
        f"and {b.pronoun()} stood firm. {a.id} looked at the wobbling {perch.label}, swallowed, "
        f"and climbed back down before trying."
    )
    world.say(
        f"They ran to tell {parent.label_word.capitalize()} about the treasure on the feeder instead."
    )


def climb(world: World, a: Entity, perch: Entity, feeder: Feeder) -> None:
    a.meters["climbing"] += 1
    propagate(world, narrate=False)
    if perch.meters["tipping"] >= THRESHOLD:
        world.say(
            f"{a.id} put one foot up, then another. The {perch.label} gave a little shiver. "
            f"The feeder swayed. The {perch.label} wobbled -- wobble, wobble, wobble."
        )
    else:
        world.say(
            f"{a.id} climbed carefully and stretched toward the feeder."
        )


def alarm(world: World, b: Entity, a: Entity, perch: Perch, parent: Entity) -> None:
    if a.meters["fell"] >= THRESHOLD:
        world.say(f'"{a.id}! {perch.label.capitalize()} tipping!" {b.id} shouted.')
        world.say(f'"{parent.label_word.upper()}!"')
    else:
        world.say(f'"Stop, stop, stop!" {b.id} cried as the {perch.label} shook.')
        world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, tool: Tool, feeder: Feeder, a: Entity) -> None:
    world.facts["caught_in_time"] = True
    a.meters["off_balance"] = 0.0
    body = tool.text.format(treasure=feeder.treasure, feeder=feeder.label)
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say(
        f"In one calm minute, the shiny prize was free, the feeder was still, and two small pirates could breathe again."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, perch: Perch) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, the yard felt very quiet.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt beside them. "I am glad you called me," '
        f'{parent.pronoun()} said softly. "Climbing on {perch.label}s for high things is not pirate bravery. '
        f"Real bravery is stopping, stopping, stopping and asking for help."
    )
    world.say(f'"We can do that," whispered {a.id} and {b.id} together.')


def safe_end(world: World, parent: Entity, a: Entity, b: Entity, feeder: Feeder, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} tucked {feeder.treasure} into their map box and helped them hang a cloth flag by the sandbox instead."
    )
    world.say(
        f'"Now your treasure is low, low, low enough for pirates to reach," {parent.pronoun()} said with a smile.'
    )
    world.say(
        f"{a.id} grinned, {b.id} cheered, and the {theme.role_plural} {theme.ending}."
    )


def rescue_fail(world: World, parent: Entity, tool: Tool, feeder: Feeder, a: Entity) -> None:
    body = tool.fail.format(treasure=feeder.treasure, feeder=feeder.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"But the feeder still swung, and {a.id} slipped off the perch and landed with a hard little bump in the grass."
    )


def tears_and_scrape(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    a.memes["fear"] += 1
    a.memes["tears"] += 1
    b.memes["fear"] += 1
    world.say(
        f"{a.id}'s eyes filled with tears, and a bright scrape rose on {a.pronoun('possessive')} knee."
    )
    world.say(
        f"{parent.label_word.capitalize()} lifted {a.pronoun('object')} into a lap, while {b.id} stood close and held {a.pronoun('possessive')} hand."
    )


def sore_lesson(world: World, parent: Entity, a: Entity, b: Entity, perch: Perch, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    a.memes["relief"] += 1
    world.say(
        f'"You are safe, and that is what matters most," {parent.label_word.capitalize()} said, cleaning the scrape. '
        f'"But remember this: {perch.label.capitalize()}s wobble, and wobbling can turn a game into hurt."'
    )
    world.say(
        f"After that, the {theme.role_plural} still hunted treasure, but never by climbing shaky things alone."
    )
@dataclass
class StoryParams:
    theme: str = "pirates"
    feeder: str = "tube"
    perch: str = "bucket"
    tool: str = "step_ladder"
    instigator: str = "Mara"
    instigator_gender: str = "girl"
    cautioner: str = "Finn"
    cautioner_gender: str = "boy"
    parent: str = "mother"
    trait: str = "careful"
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 4
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
    "feeder": [
        (
            "What is a bird feeder?",
            "A bird feeder is a place where people put seeds for birds to eat. Birds visit it because it is an easy place to find food."
        )
    ],
    "birds": [
        (
            "Why do birds come to a feeder?",
            "Birds come to a feeder because it holds seeds or other food. A feeder helps them find a meal without searching as far."
        )
    ],
    "high": [
        (
            "Why can reaching for something high be unsafe?",
            "High things can make people stretch, climb, or wobble. If the thing holding you is shaky, you can lose your balance and fall."
        )
    ],
    "bucket": [
        (
            "Why is an upside-down bucket not a good thing to stand on?",
            "An upside-down bucket can roll or tip because it does not sit firmly under your feet. That makes it easy to wobble and fall."
        )
    ],
    "crate": [
        (
            "Why can an old crate be shaky?",
            "An old crate can rock on uneven ground or have loose boards. If it shifts under you, your balance can slip away."
        )
    ],
    "ladder": [
        (
            "What is a step ladder for?",
            "A step ladder helps a grown-up reach something high in a steadier way. Its flat steps and spread legs make it safer than climbing on random things."
        )
    ],
    "hook": [
        (
            "What is a reaching hook used for?",
            "A reaching hook helps someone pull or lift a high thing from the ground. It lets a grown-up reach farther without climbing."
        )
    ],
    "broom": [
        (
            "Can a broom help move something down from a hook?",
            "Sometimes a broom can nudge a light object down if the thing is not too high. But it only works when the broom is long enough to reach."
        )
    ],
    "help": [
        (
            "Why is asking a grown-up for help brave?",
            "Asking for help is brave because you stop before the danger gets bigger. You choose safety over showing off."
        )
    ],
}
KNOWLEDGE_ORDER = ["feeder", "birds", "high", "bucket", "crate", "ladder", "hook", "broom", "help"]


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
    feeder = f["feeder_cfg"]
    perch = f["perch_cfg"]
    tool = f["tool"]
    theme = f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old where two children see treasure caught on a bird feeder and repeat an excited line. '
        f'Include the words "braid" and "feeder".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle pirate tale where {a.id} starts to climb {perch.phrase}, but listens to older {b.id} and asks for help instead.",
            f"Write a story with repetition in which treasure on {feeder.phrase} looks tempting, yet a grown-up solves the problem safely with {tool.phrase}.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a backyard pirate adventure where {a.id} with a braid reaches for treasure on {feeder.phrase}, the perch wobbles, and a calm grown-up uses {tool.phrase} to help.",
            f"Write a simple cautionary pirate story that repeats a warning and ends with the children learning that asking for help is real bravery.",
        ]
    return [
        base,
        f"Tell a cautionary pirate tale where {a.id} tries the quick way to grab treasure from the feeder, slips, and learns why shaky climbing is unsafe.",
        f"Write a story that keeps a child-facing tone but ends with a scrape and a clear lesson about not climbing on {perch.label}s for high things.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    feeder = f["feeder_cfg"]
    perch = f["perch_cfg"]
    tool = f["tool"]
    theme = f["theme"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be {theme.role_plural}. {a.id}'s {pw} also helped when the treasure on the feeder became a real problem."
        ),
        (
            "What treasure did they see?",
            f"They saw {feeder.treasure} caught on {feeder.phrase}. It looked important because the pirate game turned it into the prize of the whole adventure."
        ),
        (
            f"Why did {b.id} warn {a.id} not to climb?",
            f"{b.id} knew the {perch.label} could tip and make someone fall. The warning mattered because the treasure was high enough to tempt a risky shortcut."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed {a.id}'s mind?",
            f"{a.id} listened when {b.id} stood firm and pointed out the danger. Because {b.id} was the older sibling, the warning carried enough weight to stop the climb before anyone got hurt."
        ))
        qa.append((
            f"How did {pw} help in the end?",
            f"{pw.capitalize()} {tool.qa_text}. That let the children get the treasure while keeping their feet on the ground."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {a.id} climbed?",
            f"The {perch.label} wobbled and the feeder swayed, so the game suddenly felt scary. That shaky moment is why {b.id} shouted for help right away."
        ))
        qa.append((
            f"How did {pw} solve the problem?",
            f"{pw.capitalize()} {tool.qa_text}. The grown-up method worked because it could reach the feeder without making anyone stand on the unstable perch."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that real bravery means stopping and asking for help. The ending proves it, because they kept playing pirates after the safe fix instead of chasing danger."
        ))
    else:
        qa.append((
            f"Why did {a.id} get hurt?",
            f"{a.id} got hurt because the {perch.label} tipped while {a.pronoun()} was climbing for something high. The weak plan could not steady the situation or reach the feeder in time."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a scrape, comfort, and a lesson. The children still imagined treasure afterward, but they no longer tried to reach high things by climbing shaky objects alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["feeder_cfg"].tags) | set(f["perch_cfg"].tags)
    if f["outcome"] in {"contained", "averted"}:
        tags |= set(f["tool"].tags) | {"help"}
    else:
        if f["tool"].id == "broom":
            tags.add("broom")
        if f["tool"].id == "long_hook":
            tags.add("hook")
        if f["tool"].id == "step_ladder":
            tags.add("ladder")
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
        if e.climbable:
            bits.append("climbable=True")
        if not e.stable:
            bits.append("stable=False")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        feeder="tube",
        perch="bucket",
        tool="long_hook",
        instigator="Mara",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=4,
    ),
    StoryParams(
        theme="corsairs",
        feeder="star",
        perch="crate",
        tool="step_ladder",
        instigator="Lily",
        instigator_gender="girl",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        theme="pirates",
        feeder="tube",
        perch="crate",
        tool="broom",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="cautious",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        theme="pirates",
        feeder="star",
        perch="bucket",
        tool="step_ladder",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
    ),
]


def explain_rejection(feeder: Feeder, perch: Perch) -> str:
    if feeder.height < 2:
        return (
            f"(No story: {feeder.phrase} hangs low enough that the treasure is not a real reaching danger. "
            f"Pick a taller feeder to create a meaningful problem.)"
        )
    if perch.stable:
        return (
            f"(No story: a {perch.label} is too steady here, so the shortcut does not create a strong tipping risk. "
            f"Pick an unstable perch like a bucket or crate.)"
        )
    return "(No story: this feeder and perch do not create the right pirate-sized reaching problem.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = " / ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense (sense={tool.sense} < {SENSE_MIN}). "
        f"A storyworld should prefer steadier grown-up help. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    tool = TOOLS[params.tool]
    feeder = FEEDERS[params.feeder]
    return "contained" if (tool.adult_guided and can_reach(tool, feeder)) else "scraped"


ASP_RULES = r"""
hazard(F,P) :- feeder(F), height(F,H), H >= 2, perch(P), climbable(P), not stable(P).
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(Th,F,P) :- theme(Th), hazard(F,P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

reachable :- chosen_tool(T), chosen_feeder(F), reach(T,R), height(F,H), R >= H.
contained :- chosen_tool(T), adult_guided(T), reachable.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(scraped) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for feeder_id, feeder in FEEDERS.items():
        lines.append(asp.fact("feeder", feeder_id))
        lines.append(asp.fact("height", feeder_id, feeder.height))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        if perch.climbable:
            lines.append(asp.fact("climbable", perch_id))
        if perch.stable:
            lines.append(asp.fact("stable", perch_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.adult_guided:
            lines.append(asp.fact("adult_guided", tool_id))
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
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_feeder", params.feeder),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {tool.id for tool in sensible_tools()}
    if c_sens == p_sens:
        print(f"OK: sensible tools match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            args = parser.parse_args([])
            cases.append(resolve_params(args, random.Random(s)))
        except StoryError:
            continue
    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, a high feeder, and the brave choice to ask for help."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--feeder", choices=FEEDERS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "", gender: Optional[str] = None) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if g == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), g


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.feeder and args.perch:
        feeder = FEEDERS[args.feeder]
        perch = PERCHES[args.perch]
        if not hazard_at_risk(feeder, perch):
            raise StoryError(explain_rejection(feeder, perch))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.feeder is None or combo[1] == args.feeder)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, feeder, perch = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(t.id for t in sensible_tools()))
    instigator, ig = _pick_kid(rng, gender="girl")
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = rng.choice(TRAITS)
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme,
        feeder=feeder,
        perch=perch,
        tool=tool,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme '{params.theme}')")
    if params.feeder not in FEEDERS:
        raise StoryError(f"(Unknown feeder '{params.feeder}')")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch '{params.perch}')")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}')")
    feeder = FEEDERS[params.feeder]
    perch = PERCHES[params.perch]
    tool = TOOLS[params.tool]
    if not hazard_at_risk(feeder, perch):
        raise StoryError(explain_rejection(feeder, perch))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))

    world = tell(
        THEMES[params.theme],
        feeder,
        perch,
        tool,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, feeder, perch) combos:\n")
        for theme, feeder, perch in combos:
            print(f"  {theme:8} {feeder:8} {perch}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.feeder} with {p.perch} ({p.theme}, {p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    theme: Theme,
    feeder: Feeder,
    perch_cfg: Perch,
    tool: Tool,
    *,
    instigator: str = "Mara",
    instigator_gender: str = "girl",
    cautioner: str = "Finn",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "siblings",
    instigator_age: int = 5,
    cautioner_age: int = 4,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation, "hair": "braid" if instigator_gender == "girl" else ""},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    perch = world.add(Entity(
        id="perch",
        type="perch",
        label=perch_cfg.label,
        stable=perch_cfg.stable,
        climbable=perch_cfg.climbable,
    ))
    feeder_ent = world.add(Entity(
        id="feeder",
        type="feeder",
        label=feeder.label,
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["caught_in_time"] = False
    world.facts["instigator"] = a
    world.facts["cautioner"] = b
    world.facts["parent"] = parent
    world.facts["theme"] = theme
    world.facts["feeder_cfg"] = feeder
    world.facts["perch_cfg"] = perch_cfg
    world.facts["tool"] = tool
    world.facts["relation"] = relation

    play_setup(world, a, b, theme)
    spot_treasure(world, b, feeder, theme)

    world.para()
    tempt(world, a, feeder, perch_cfg)
    warn(world, b, a, perch_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, perch_cfg, parent)
        world.para()
        rescue(world, parent, tool, feeder, a)
        lesson(world, parent, a, b, perch_cfg)
        world.para()
        safe_end(world, parent, a, b, feeder, theme)
        contained = True
    else:
        defy(world, a, perch_cfg)
        world.para()
        climb(world, a, perch, feeder)
        if tool.adult_guided and can_reach(tool, feeder):
            alarm(world, b, a, perch_cfg, parent)
            world.para()
            rescue(world, parent, tool, feeder, a)
            lesson(world, parent, a, b, perch_cfg)
            world.para()
            safe_end(world, parent, a, b, feeder, theme)
            contained = True
        else:
            propagate(world, narrate=False)
            alarm(world, b, a, perch_cfg, parent)
            world.para()
            rescue_fail(world, parent, tool, feeder, a)
            tears_and_scrape(world, parent, a, b)
            sore_lesson(world, parent, a, b, perch_cfg, theme)
            contained = False

    outcome = "averted" if averted else ("contained" if contained else "scraped")
    world.facts.update(
        outcome=outcome,
        averted=averted,
        rescued=contained,
        fell=a.meters["fell"] >= THRESHOLD,
        scraped=a.meters["scraped"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy pirate cove",
        rig="The old bench was their ship, a rake became a mast, and a chalk line through the dirt was the edge of the sea.",
        captain="Captain",
        mate="Lookout",
        goal="the feathery treasure island",
        launch="Set sails for the treasure!",
        role_plural="pirates",
        ending="sailed their bench-ship around the yard again, louder and wiser than before",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a secret corsair harbor",
        rig="The wheelbarrow was their boat, a broom became an oar, and a flower bed was the dangerous reef.",
        captain="Captain",
        mate="Matey",
        goal="the reef of shiny loot",
        launch="Row for the glittering prize!",
        role_plural="corsairs",
        ending="pushed their wheelbarrow ship past the reef and laughed in the sun",
    ),
}

FEEDERS = {
    "tube": Feeder(
        id="tube",
        label="tube feeder",
        phrase="the tall bird feeder",
        height=2,
        sway="clicked softly in the breeze",
        treasure="a blue ribbon from Mara's braid",
        hook_spot="the top hook",
        tags={"feeder", "birds", "high"},
    ),
    "star": Feeder(
        id="star",
        label="star feeder",
        phrase="the star-shaped feeder",
        height=3,
        sway="twinkled and swung above their heads",
        treasure="a silver foil star",
        hook_spot="the high ring",
        tags={"feeder", "birds", "high"},
    ),
    "low_tray": Feeder(
        id="low_tray",
        label="tray feeder",
        phrase="the low tray feeder",
        height=1,
        sway="hardly moved at all on its short hook",
        treasure="a red bead",
        hook_spot="the low hook",
        tags={"feeder", "birds"},
    ),
}

PERCHES = {
    "bucket": Perch(
        id="bucket",
        label="bucket",
        phrase="the upside-down bucket",
        stable=False,
        climbable=True,
        risk=2,
        wobble_text="rolled on its round bottom",
        tags={"bucket", "unstable"},
    ),
    "crate": Perch(
        id="crate",
        label="crate",
        phrase="the old apple crate",
        stable=False,
        climbable=True,
        risk=2,
        wobble_text="creaked and rocked in the grass",
        tags={"crate", "unstable"},
    ),
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="the little stool",
        stable=True,
        climbable=True,
        risk=0,
        wobble_text="stood flat on all four legs",
        tags={"stool"},
    ),
}

TOOLS = {
    "step_ladder": Tool(
        id="step_ladder",
        label="step ladder",
        phrase="a step ladder",
        sense=3,
        reach=3,
        adult_guided=True,
        text="opened a step ladder, held it steady, and lifted {treasure} down from the feeder",
        fail="opened a step ladder, but it was set too far from the feeder to free {treasure} in time",
        qa_text="used a step ladder and held it steady while lifting the treasure down",
        tags={"ladder", "help"},
    ),
    "long_hook": Tool(
        id="long_hook",
        label="long hook",
        phrase="a long reaching hook",
        sense=3,
        reach=3,
        adult_guided=True,
        text="took the long reaching hook from the shed and gently unlooped {treasure} from the feeder",
        fail="reached with the hook, but it was too short to free {treasure}",
        qa_text="used a long reaching hook to unloop the treasure safely",
        tags={"hook", "help"},
    ),
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a broom",
        sense=2,
        reach=2,
        adult_guided=True,
        text="stood on the path and nudged {treasure} loose with a broom while keeping everyone on the ground",
        fail="tried to poke {treasure} loose with a broom, but the feeder hung too high",
        qa_text="used a broom from the ground to nudge the treasure loose",
        tags={"broom", "help"},
    ),
    "jump": Tool(
        id="jump",
        label="jumping",
        phrase="just jumping",
        sense=1,
        reach=1,
        adult_guided=False,
        text="jumped up for {treasure}",
        fail="reached up by jumping, but that could not stop the slip",
        qa_text="tried to jump for the treasure",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mara", "Lily", "Nora", "Ava", "Zoe", "Mina", "Ella", "Tessa"]
BOY_NAMES = ["Finn", "Tom", "Ben", "Leo", "Sam", "Jack", "Theo", "Max"]
TRAITS = ["careful", "curious", "steady", "cautious", "sensible", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for feeder_id, feeder in FEEDERS.items():
            for perch_id, perch in PERCHES.items():
                if hazard_at_risk(feeder, perch):
                    combos.append((theme_id, feeder_id, perch_id))
    return combos

if __name__ == "__main__":
    main()
