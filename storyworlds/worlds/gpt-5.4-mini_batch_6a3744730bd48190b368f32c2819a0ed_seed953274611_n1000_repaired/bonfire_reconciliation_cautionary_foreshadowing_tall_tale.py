#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bonfire_reconciliation_cautionary_foreshadowing_tall_tale.py
============================================================================================

A tiny, standalone storyworld for a tall-tale-style bonfire story.

Premise:
- Two kids build a bonfire for a night gathering.
- One child sees a warning sign in the wind and hesitates.
- The other child ignores the caution, and the fire grows too lively.
- A grown-up intervenes with a sensible fix.
- The children reconcile, learn the lesson, and end with a safer bright fire.

The prose is intentionally state-driven: meters and memes evolve through the
simulation, and the ending image proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
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
BRAVERY_INIT = 5.0
CAUTION_TRAITS = {"careful", "watchful", "cautious", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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


@dataclass
class Place:
    id: str
    label: str
    moonlit: bool = False
    breeze: str = "soft"
    sparks: str = "quick sparks"
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
class Firewood:
    id: str
    label: str
    phrase: str
    dry: bool = True
    flare: int = 2
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
class WarningSign:
    id: str
    label: str
    omen: str
    hint: str
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

    def people(self) -> list[Entity]:
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
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_wind_whispers(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    bonfire = world.get("bonfire")
    if bonfire.meters["burning"] < THRESHOLD:
        return out
    sig = ("whisper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.memes["wonder"] += 1
    for p in world.people():
        p.memes["attention"] += 1
    out.append("__whisper__")
    return out


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    bonfire = world.get("bonfire")
    if bonfire.meters["burning"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("field").meters["glow"] += 1
    for p in world.people():
        p.memes["fear"] += 1
    out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("wind_whispers", _r_wind_whispers), Rule("spread", _r_spread)]


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


def story_smoke(world: World) -> None:
    world.get("bonfire").meters["burning"] += 1
    propagate(world, narrate=False)


def sense_of(fix: Fix) -> bool:
    return fix.sense >= 2


def blaze_power(firewood: Firewood, delay: int) -> int:
    return firewood.flare + delay


def contained(fix: Fix, firewood: Firewood, delay: int) -> bool:
    return fix.power >= blaze_power(firewood, delay)


def foreshadow(world: World, sign: WarningSign, child: Entity) -> None:
    child.memes["unease"] += 1
    world.say(
        f"As the sun slid low, {sign.omen} moved over the field like a message "
        f"written in a giant hand. {child.id} noticed {sign.hint} and slowed down."
    )


def build_scene(world: World, a: Entity, b: Entity, place: Place, firewood: Firewood) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright evening, {a.id} and {b.id} built a bonfire in {place.label}, "
        f"where old legends said the grass could hear a whisper."
    )
    world.say(
        f"They stacked {firewood.phrase} into a tower fit for a giant, and the sky "
        f"looked on as if it had opened one sleepy blue eye."
    )


def warn(world: World, cautioner: Entity, instigator: Entity, sign: WarningSign, firewood: Firewood) -> None:
    world.say(
        f"{cautioner.id} pointed at the sky. \"That wind has a crooked story in it,\" "
        f"{cautioner.pronoun()} said. \"A dry pile like {firewood.label} can leap high "
        f"when it is tempted.\""
    )
    cautioner.memes["caution"] += 1
    world.facts["warned"] = sign.id


def defy(world: World, instigator: Entity, firewood: Firewood) -> None:
    instigator.memes["defiance"] += 1
    world.say(
        f"\"A bonfire is meant to be bold,\" {instigator.id} said, and set the torch "
        f"to the dry sticks."
    )
    world.say("For one blink, nothing moved. Then the embers woke up hungry.")


def ignite(world: World, firewood: Firewood) -> None:
    world.get("bonfire").meters["burning"] += 1
    world.get("bonfire").meters["fierce"] += 1
    story_smoke(world)
    world.say(
        f"The bonfire cracked and climbed. Sparks hopped into the dark like red-gold "
        f"grasshoppers, and the whole field glowed as if a little sun had fallen down."
    )


def alarm(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"\"{a.id}!\" {b.id} cried. \"The flames are leaping higher than a fence in a storm!\""
    )
    world.say(f"The old sky itself seemed to lean closer and listen.")


def rescue(world: World, adult: Entity, fix: Fix, firewood: Firewood) -> None:
    world.get("bonfire").meters["burning"] = 0.0
    world.get("bonfire").meters["fierce"] = 0.0
    world.get("field").meters["glow"] = 0.0
    body = fix.text.replace("{target}", firewood.label)
    world.say(
        f"{adult.label_word.capitalize()} came striding out with the calm of a river "
        f"that knows its own way. {adult.pronoun().capitalize()} {body}."
    )
    world.say(
        f"The bonfire hissed, bowed its head, and settled down to a safe red glow."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity, sign: WarningSign) -> None:
    for child in (a, b):
        child.memes["fear"] = 0.0
        child.memes["relief"] += 1
        child.memes["reconciliation"] += 1
    world.say("For a heartbeat, nobody spoke.")
    world.say(
        f"Then {adult.label_word.capitalize()} set a hand on both their shoulders and "
        f"said, \"I'm glad you called. Remember the warning the wind gave you: "
        f"{sign.hint}. Fire is a wonderful guest, but a terrible runaway.\""
    )
    world.say(
        f"{a.id} looked at {b.id}, then back at the cooling coals, and nodded. "
        f"\"I should have listened,\" {a.id} whispered."
    )
    world.say(
        f"{b.id} gave {a.id} a grin as crooked as a fence nail. \"We still made a good "
        f"story,\" {b.id} said, \"we just don't need the dangerous chapter again.\""
    )


def reconciliation(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f"The two children bumped shoulders and laughed, the kind of laugh that fixes "
        f"what words alone cannot mend."
    )
    world.say(
        f"By the time the first star blinked awake over {place.label}, they were sitting "
        f"side by side again, warm from the same old blaze."
    )


def safe_end(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"Later, the bonfire sat low and polite, and the night around it looked bigger "
        f"than before. {a.id} and {b.id} watched the sparks rise and fall like tiny "
        f"lanterns being taught manners by the moon."
    )


def bad_end(world: World, adult: Entity, a: Entity, b: Entity, firewood: Firewood) -> None:
    for child in (a, b):
        child.memes["fear"] += 1
    world.say(
        f"The flames ran too far, too fast. {adult.label_word.capitalize()} got everyone "
        f"back from the heat, but the bonfire had turned wild and mean."
    )
    world.say(
        f"Even so, {a.id} and {b.id} held hands tight, learned the hard lesson, and "
        f"promised never again to poke a sleeping giant with a dry twig."
    )


def tell(place: Place, firewood: Firewood, sign: WarningSign, fix: Fix,
         instigator: str = "Milo", cautioner: str = "June", adult: str = "Aunt Wren",
         delay: int = 0, instigator_age: int = 7, cautioner_age: int = 8,
         relation: str = "friends", trust: int = 4) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type="boy", role="instigator",
                         age=instigator_age, traits=["bold"], attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type="girl", role="cautioner",
                         age=cautioner_age, traits=["watchful"], attrs={"relation": relation}))
    grown = world.add(Entity(id=adult, kind="character", type="mother", role="adult", label="the grown-up"))
    world.add(Entity(id="place", type="place", label=place.label, tags=set(place.tags)))
    bonfire = world.add(Entity(id="bonfire", type="fire", label="the bonfire", tags={"bonfire"}))
    field = world.add(Entity(id="field", type="place", label=place.label, tags=set(place.tags)))
    bonfire.memes["trust"] = float(trust)
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = 5.0 if "careful" in b.traits else 3.0

    build_scene(world, a, b, place, firewood)
    world.para()
    foreshadow(world, sign, b)
    warn(world, b, a, sign, firewood)
    if relation == "friends" and cautioner_age > instigator_age and b.memes["caution"] + 1 > BRAVERY_INIT:
        world.say(f"{a.id} blinked, thought better of it, and decided not to strike the match at once.")
        world.say(f"That was the smart part of the night.")
        world.para()
        rescue(world, grown, fix, firewood)
        lesson(world, grown, a, b, sign)
        reconciliation(world, a, b, place)
        world.para()
        safe_end(world, a, b, place)
        outcome = "averted"
    else:
        defy(world, a, firewood)
        ignite(world, firewood)
        alarm(world, a, b, place)
        world.para()
        if contained(fix, firewood, delay):
            rescue(world, grown, fix, firewood)
            lesson(world, grown, a, b, sign)
            reconciliation(world, a, b, place)
            world.para()
            safe_end(world, a, b, place)
            outcome = "contained"
        else:
            bad_end(world, grown, a, b, firewood)
            outcome = "burned"

    world.facts.update(
        instigator=a, cautioner=b, adult=grown, place_cfg=place, firewood_cfg=firewood,
        sign=sign, fix=fix, delay=delay, relation=relation, trust=trust,
        outcome=outcome, resolved=(outcome != "burned"),
    )
    return world


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", moonlit=True, breeze="bright", sparks="glittering sparks", tags={"meadow"}),
    "riverbank": Place(id="riverbank", label="the riverbank", moonlit=True, breeze="whistling", sparks="spark showers", tags={"riverbank"}),
    "hilltop": Place(id="hilltop", label="the hilltop", moonlit=True, breeze="windy", sparks="red sparks", tags={"hilltop"}),
}

FIREWOODS = {
    "pine": Firewood(id="pine", label="pine logs", phrase="a stack of dry pine logs", dry=True, flare=3, tags={"pine"}),
    "kindling": Firewood(id="kindling", label="kindling", phrase="a teetering castle of kindling", dry=True, flare=2, tags={"kindling"}),
    "branches": Firewood(id="branches", label="branches", phrase="a heap of brittle branches", dry=True, flare=4, tags={"branches"}),
}

WARNINGS = {
    "wind": WarningSign(id="wind", label="wind", omen="a long wind", hint="a long wind can turn a little flame into a racing one", tags={"wind"}),
    "smoke": WarningSign(id="smoke", label="smoke", omen="a ribbon of smoke", hint="smoke is the bonfire's way of telling on itself", tags={"smoke"}),
    "sparks": WarningSign(id="sparks", label="sparks", omen="sparks jumping sideways", hint="sparks that jump sideways are looking for trouble", tags={"sparks"}),
}

FIXES = {
    "water": Fix(id="water", sense=3, power=4, text="filled a water pail from the pump and splashed the water over {target} until the heat sighed out", fail="poured water, but the fire was already too big for that little pail", qa_text="filled a water pail from the pump and splashed the fire out"),
    "blanket": Fix(id="blanket", sense=3, power=3, text="threw a heavy wool blanket over {target} and smothered the sparks", fail="threw a blanket, but the blaze licked it aside", qa_text="threw a heavy wool blanket over the flames and smothered them"),
    "shovel": Fix(id="shovel", sense=2, power=2, text="used a shovel to pull the burning sticks apart and let them cool fast", fail="used a shovel, but the blaze had already galloped too far", qa_text="used a shovel to break the fire apart"),
}

TRAITS = ["careful", "watchful", "cautious", "thoughtful", "steady", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FIREWOODS:
            for s in WARNINGS:
                combos.append((p, f, s))
    return combos


@dataclass
class StoryParams:
    place: str
    firewood: str
    sign: str
    fix: str
    instigator: str
    cautioner: str
    adult: str
    delay: int = 0
    relation: str = "friends"
    trust: int = 4
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale bonfire story for a child using the word "bonfire" and a warning about {f["sign"].label}.',
        f"Tell a cautionary story where {f['instigator'].id} and {f['cautioner'].id} build a bonfire, one child sees the warning first, and the grown-up's fix saves the night.",
        f"Write a story with foreshadowing, a near-miss, and reconciliation around a bonfire in {f['place_cfg'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, adult = f["instigator"], f["cautioner"], f["adult"]
    place, firewood, sign, fix = f["place_cfg"], f["firewood_cfg"], f["sign"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {adult.label_word}. They meet in {place.label} where the bonfire begins as a brave-looking pile of {firewood.label}."),
        ("What warning did the cautioner notice?",
         f"{b.id} noticed {sign.omen} and said it sounded like trouble. That was the foreshadowing, because the wind was hinting that the fire could run wild."),
        ("What did the instigator do after the warning?",
         f"{a.id} ignored the warning and lit the bonfire anyway. That choice made the middle of the story turn from playful to dangerous."),
    ]
    if f["outcome"] == "averted":
        qa.append((
            "How did the story end?",
            f"{a.id} thought better of it before the flames got away, so the grown-up could settle the bonfire safely and the children stayed friends. The ending image is quiet and bright instead of wild."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            "How did the grown-up fix the problem?",
            f"{adult.label_word.capitalize()} {fix.qa_text}. That worked because the fix had enough power for the fire's size, and the night cooled down instead of burning out of control."
        ))
        qa.append((
            "How did the children make up?",
            f"They apologized to each other, then laughed together again after the danger was gone. Their reconciliation came when they chose the safer way and stood side by side near the low red glow."
        ))
        qa.append((
            "What did the ending look like?",
            f"The bonfire sat low and polite while the children watched the sparks. It looked like a tiny sun that had finally learned manners."
        ))
    else:
        qa.append((
            "Why was the ending scary?",
            f"The fire grew too fierce for {adult.label_word} to calm with that fix. Everyone got away safely, but the bonfire had turned into a wild thing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["sign"].tags) | set(f["firewood_cfg"].tags) | {"bonfire"}
    out = []
    if "bonfire" in tags:
        out.append(("What is a bonfire?", "A bonfire is a big outdoor fire made by piling up wood and lighting it on purpose. People gather near it to tell stories, warm their hands, or sing songs."))
    if "wind" in tags:
        out.append(("Why can wind be dangerous near a fire?", "Wind can push flames and sparks farther than you expect. That can turn a small fire into a bigger one very quickly."))
    if "smoke" in tags:
        out.append(("What does smoke tell you?", "Smoke can be a warning that something is burning. If smoke starts acting strange, it is wise to pay attention right away."))
    if f["fix"].id == "water":
        out.append(("What does water do to fire?", "Water cools fire and helps put out many flames. It is one of the usual ways grown-ups fight a small fire."))
    if f["fix"].id == "blanket":
        out.append(("Why can a heavy blanket help?", "A heavy blanket can cover a small fire and take away the air it needs. Without air, the flames can smother and go out."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", firewood="pine", sign="wind", fix="water", instigator="Milo", cautioner="June", adult="Aunt Wren", delay=0, relation="friends", trust=4),
    StoryParams(place="riverbank", firewood="branches", sign="sparks", fix="blanket", instigator="Ada", cautioner="Bess", adult="Uncle Pike", delay=1, relation="siblings", trust=3),
    StoryParams(place="hilltop", firewood="kindling", sign="smoke", fix="shovel", instigator="Finn", cautioner="Ivy", adult="Grandma Vale", delay=2, relation="friends", trust=6),
]


def explain_rejection() -> str:
    return "(No story: that choice set does not make a sensible bonfire tale.)"


def outcome_of(params: StoryParams) -> str:
    if params.relation == "siblings" and params.trust > 6 and params.delay == 0:
        return "averted"
    return "contained" if contained(FIXES[params.fix], FIREWOODS[params.firewood], params.delay) else "burned"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, f in FIREWOODS.items():
        lines.append(asp.fact("firewood", fid))
        lines.append(asp.fact("flare", fid, f.flare))
    for sid in WARNINGS:
        lines.append(asp.fact("sign", sid))
    for fxid, fx in FIXES.items():
        lines.append(asp.fact("fix", fxid))
        lines.append(asp.fact("sense", fxid, fx.sense))
        lines.append(asp.fact("power", fxid, fx.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F,S) :- place(P), firewood(F), sign(S).
sensible(X) :- fix(X), sense(X,N), N >= 2.
contained(X,F,D) :- fix(X), power(X,P), flare(F,Fl), D >= 0, P >= Fl + D.
outcome(averted) :- trust_high, early_hesitation.
outcome(contained) :- not outcome(averted), chosen_fix(X), chosen_firewood(F), chosen_delay(D), contained(X,F,D).
outcome(burned) :- not outcome(averted), not outcome(contained).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    if set(asp_sensible()) != set(FIXES):
        rc = 1
        print("MISMATCH in sensible fixes")
    else:
        print("OK: sensible fixes match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale bonfire storyworld with reconciliation and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--firewood", choices=FIREWOODS)
    ap.add_argument("--sign", choices=WARNINGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--instigator")
    ap.add_argument("--cautioner")
    ap.add_argument("--adult")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.firewood is None or c[1] == args.firewood)
              and (args.sign is None or c[2] == args.sign)]
    if not combos:
        raise StoryError(explain_rejection())
    place, firewood, sign = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        firewood=firewood,
        sign=sign,
        fix=fix,
        instigator=args.instigator or rng.choice(["Milo", "Ada", "Finn", "Ivy", "June", "Bess"]),
        cautioner=args.cautioner or rng.choice(["June", "Bess", "Nell", "Otis", "Wren"]),
        adult=args.adult or rng.choice(["Aunt Wren", "Grandma Vale", "Uncle Pike"]),
        delay=delay,
        relation=rng.choice(["friends", "siblings"]),
        trust=rng.randint(0, 10),
    )


def generate(params: StoryParams) -> StorySample:
    for key in ["place", "firewood", "sign", "fix"]:
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(explain_rejection())
    if params.fix not in FIXES:
        raise StoryError(explain_rejection())
    world = tell(PLACES[params.place], FIREWOODS[params.firewood], WARNINGS[params.sign], FIXES[params.fix],
                 instigator=params.instigator, cautioner=params.cautioner, adult=params.adult,
                 delay=params.delay, relation=params.relation, trust=params.trust)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
