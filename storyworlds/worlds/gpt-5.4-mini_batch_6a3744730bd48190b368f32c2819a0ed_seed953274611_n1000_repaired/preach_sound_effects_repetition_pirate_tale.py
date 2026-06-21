#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/preach_sound_effects_repetition_pirate_tale.py
===============================================================================

A tiny pirate tale storyworld about a crew that keeps hearing a preachy message,
with sound effects and repetition as the main narrative instruments.

Premise:
A small pirate crew wants to keep sailing, but one crew member keeps banging a
drum and preaching a warning about a reef. The others ignore the repeated
warning until the sea and ship state make the danger impossible to miss. Then a
calm captain uses a safer maneuver, and the ending image proves the change: the
ship sails on, and the preachy lesson becomes a remembered chant.

This script is self-contained and follows the Storyweavers contract:
- typed entities with meters and memes
- a reasonableness gate plus an inline ASP twin
- story-driven QA sets
- standalone CLI with text, JSON, trace, QA, ASP, and verify modes
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
SEA_RISK_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
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
class CrewMember:
    id: str
    type: str
    title: str
    role: str
    voice: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.title
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
class Ship:
    id: str
    name: str
    storm_sense: int
    reef_clearance: int
    safe_move: str
    sound: str
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
class Hazard:
    id: str
    name: str
    label: str
    risky: bool = True
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
class Signal:
    id: str
    name: str
    sound: str
    safe: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    action: str
    success: str
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
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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


def _r_reach(world: World) -> list[str]:
    out = []
    ship = world.get("ship")
    reef = world.get("reef")
    if ship.meters["near_reef"] >= THRESHOLD and reef.meters["danger"] < THRESHOLD:
        reef.meters["danger"] += 1
        out.append("__reef__")
    return out


def _r_panic(world: World) -> list[str]:
    out = []
    if world.get("ship").meters["near_reef"] >= THRESHOLD:
        for ent in list(world.entities.values()):
            if isinstance(ent, CrewMember):
                ent.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("reach", "sea", _r_reach), Rule("panic", "sea", _r_panic)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def hazard_at_risk(hazard: Hazard, ship: Ship) -> bool:
    return hazard.risky and ship.reef_clearance <= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for s in SHIPS:
        for h in HAZARDS:
            for _sig in SIGNALS:
                if hazard_at_risk(HAZARDS[h], SHIPS[s]):
                    combos.append((s, h, _sig))
    return combos


SENSE_MIN = 2


def choose_name(rng: random.Random, names: list[str], avoid: str = "") -> str:
    pool = [n for n in names if n != avoid]
    return rng.choice(pool)


def prediction(world: World) -> dict:
    sim = world.copy()
    sim.get("ship").meters["near_reef"] += 1
    propagate(sim, narrate=False)
    return {"reef_danger": sim.get("reef").meters["danger"]}


def sound_effect(step: str) -> str:
    return {"drum": "Boom-boom!", "bell": "Ding-ding!", "wave": "Splash!"}.get(step, "Thump!")


def tell(ship: Ship, hazard: Hazard, signal: Signal, response: Response,
         captain: CrewMember, mate: CrewMember, singer: CrewMember) -> World:
    world = World()
    world.add(Entity(id="ship", kind="thing", type="ship", label=ship.name))
    reef = world.add(Entity(id="reef", kind="thing", type="reef", label=hazard.label))
    world.add(Entity(id="sea", kind="thing", type="sea", label="the sea"))
    world.add(captain)
    world.add(mate)
    world.add(singer)

    captain.memes["calm"] = 1
    mate.memes["curious"] = 1
    singer.memes["urgent"] = 1

    world.say(
        f"On a bright blue day, {captain.id} and {mate.id} sailed {ship.name} past "
        f"the singing sea. {sound_effect('wave')} went the waves. {signal.sound} went "
        f"{singer.id}'s drum."
    )
    world.say(
        f"{singer.id} kept preaching, '{signal.name}! {signal.name}! Keep away from "
        f"{hazard.label}!' But {mate.id} just laughed and tapped {mate.pronoun('possessive')} boot."
    )

    world.para()
    captain.say = None if False else None
    world.say(
        f"{mate.id} leaned over the rail. {sound_effect('wave')} {sound_effect('drum')} "
        f"The ship crept closer and closer."
    )
    world.get("ship").meters["near_reef"] += 1
    world.get("ship").meters["speed"] += 1
    propagate(world, narrate=False)

    pred = prediction(world)
    world.facts["predicted_reef_danger"] = pred["reef_danger"]
    if pred["reef_danger"] >= SEA_RISK_LIMIT:
        mate.memes["worry"] += 1
        world.say(
            f"Then the water turned sharp and white. {singer.id} preached again, "
            f"'{signal.name}! {signal.name}!' {sound_effect('bell')} rang from the mast."
        )
        world.say(
            f"{captain.id} saw the danger at once. 'Hard to starboard!' {captain.id} cried."
        )
        if response.power >= ship.storm_sense:
            world.para()
            world.say(
                f"In a snap, {captain.id} {response.action}, and {response.success}."
            )
            ship_state = world.get("ship")
            ship_state.meters["near_reef"] = 0
            ship_state.memes["relief"] += 1
            mate.memes["relief"] += 1
            singer.memes["pride"] += 1
            world.say(
                f"The reef slid by with a hush. {sound_effect('wave')} went the water, "
                f"and {singer.id} smiled because the warning had finally been heard."
            )
            world.say(
                f"By sunset, the crew was laughing again, and the drum beat changed to "
                f"Boom-boom, safe and sound, Boom-boom, safe and sound."
            )
            outcome = "safe"
        else:
            world.para()
            world.say(
                f"{captain.id} tried to {response.action}, but {response.fail}."
            )
            reef.meters["danger"] += 1
            ship_state = world.get("ship")
            ship_state.meters["damaged"] += 1
            world.say(
                f"Crash! The hull bumped the reef. The mast shook, and everyone grabbed "
                f"the rail as the ship limped away."
            )
            world.say(
                f"Even then, {singer.id} kept the chant: '{signal.name}, {signal.name}!' "
                f"because some lessons have to be heard twice."
            )
            outcome = "damaged"
    else:
        world.say(
            f"The sea stayed calm, but {singer.id} still preached, '{signal.name}! {signal.name}!' "
            f"because a wise pirate warns before trouble starts."
        )
        world.get("ship").meters["near_reef"] = 0
        outcome = "avoided"

    world.facts.update(
        ship=ship,
        hazard=hazard,
        signal=signal,
        response=response,
        captain=captain,
        mate=mate,
        singer=singer,
        outcome=outcome,
    )
    return world


SHIP_NAMES = {
    "briny": Ship(id="briny", name="the Briny Gull", storm_sense=2, reef_clearance=1, safe_move="turn fast", sound="creak-creak", tags={"ship"}),
    "tide": Ship(id="tide", name="the Tide Wren", storm_sense=3, reef_clearance=1, safe_move="spin the wheel", sound="squeak-squeak", tags={"ship"}),
    "dawn": Ship(id="dawn", name="the Dawn Cutlass", storm_sense=4, reef_clearance=2, safe_move="trim the sail", sound="whish-whish", tags={"ship"}),
}

HAZARDS = {
    "reef": Hazard(id="reef", name="reef", label="the jagged reef", risky=True, tags={"reef", "sea"}),
    "rocks": Hazard(id="rocks", name="rocks", label="the black rocks", risky=True, tags={"rocks", "sea"}),
}

SIGNALS = {
    "reef": Signal(id="reef", name="preach reef", sound="Boom-boom!", safe=True, tags={"preach", "sound"}),
    "rocks": Signal(id="rocks", name="preach rocks", sound="Ding-ding!", safe=True, tags={"preach", "sound"}),
}

RESPONSES = {
    "starboard": Response(id="starboard", sense=3, power=4, action="turned hard to starboard", success="the ship spun away from the reef", fail="the wheel jammed for a breath", tags={"turn"}),
    "trim": Response(id="trim", sense=3, power=3, action="trimmed the sail and turned with the wind", success="the sail caught and the ship glided free", fail="the sail flapped and stalled", tags={"sail"}),
    "slow": Response(id="slow", sense=2, power=2, action="slowed the ship and backed the line", success="the ship drifted clear", fail="the ship still slid too close", tags={"line"}),
    "bucket": Response(id="bucket", sense=1, power=1, action="splashed a bucket at the bow", success="a splash made no real difference", fail="the splash did nothing at all", tags={"weak"}),
}

CYCLE_NAMES = ["Boom-boom", "Boom-boom", "Ding-ding", "Preach-preach"]
CREW_NAMES = ["Mara", "Ned", "Pip", "Jory", "Lana", "Finn"]
BOY_NAMES = ["Sam", "Tom", "Ben", "Jack"]
GIRL_NAMES = ["Lily", "Mia", "Rose", "Nora"]
TRAITS = ["bold", "steady", "curious", "grumpy"]


@dataclass
class StoryParams:
    ship: str
    hazard: str
    signal: str
    response: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    singer_name: str
    singer_gender: str
    trait: str
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


CURATED = [
    StoryParams(ship="briny", hazard="reef", signal="reef", response="starboard",
                captain_name="Mara", captain_gender="girl", mate_name="Pip", mate_gender="boy",
                singer_name="Lana", singer_gender="girl", trait="steady"),
    StoryParams(ship="tide", hazard="rocks", signal="rocks", response="trim",
                captain_name="Tom", captain_gender="boy", mate_name="Lily", mate_gender="girl",
                singer_name="Ned", singer_gender="boy", trait="curious"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "preach" and keeps repeating a warning sound.',
        f"Tell a short sea adventure where {f['singer'].id} keeps preaching about {f['hazard'].label} until the captain listens.",
        f"Write a pirate story with sound effects like Boom-boom and Splash, ending with the ship safely past danger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    singer = f["singer"]
    hazard = f["hazard"]
    response = f["response"]
    qa = [
        ("Who kept preaching in the story?",
         f"{singer.id} kept preaching about {hazard.label} over and over. The repeated warning helped the crew notice the danger."),
        ("Why did the captain change course?",
         f"The captain saw that the ship was getting close to {hazard.label}. The warning and the sound effects showed the danger was real, so the captain used {response.action}."),
        ("How did the story end?",
         f"It ended safely, with the ship past the danger and the crew cheerful again. The last image is of a safer sail and a warning chant that now sounds wise."),
    ]
    if f["outcome"] == "damaged":
        qa.append((
            "What happened when the response was too weak?",
            f"The ship bumped the hazard and got damaged. The crew still got away, but the lesson came with a louder crash."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does preach mean in this story?",
         "Here, preach means to keep warning someone in a strong, repeated way. The speaker says the same message again and again so nobody misses it."),
        ("Why use repeated sound effects in a pirate tale?",
         "Repeated sound effects make the sea adventure feel lively and easy to follow. They also help show that a warning is happening more than once."),
        ("What is a reef?",
         "A reef is a hard, rocky place under the water. Ships must steer away from it because it can scrape and damage a hull."),
    ]


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
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(ship: Ship, hazard: Hazard) -> str:
    return f"(No story: {ship.name} is not the sort of ship that can make this reef warning matter.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {good}.)"


def valid_story_choice(ship: Ship, hazard: Hazard) -> bool:
    return hazard_at_risk(hazard, ship)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with preachy repetition and sound effects.")
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    ship_id = args.ship or rng.choice(list(SHIP_NAMES))
    hazard_id = args.hazard or rng.choice(list(HAZARDS))
    if not valid_story_choice(SHIP_NAMES[ship_id], HAZARDS[hazard_id]):
        raise StoryError(explain_rejection(SHIP_NAMES[ship_id], HAZARDS[hazard_id]))
    response_id = args.response or rng.choice([r.id for r in sensible_responses()])
    signal_id = args.signal or hazard_id
    name1 = args.name or rng.choice(CREW_NAMES)
    name2 = choose_name(rng, CREW_NAMES, avoid=name1)
    name3 = choose_name(rng, CREW_NAMES, avoid=name1)
    g1 = "girl" if name1 in GIRL_NAMES else "boy"
    g2 = "girl" if name2 in GIRL_NAMES else "boy"
    g3 = "girl" if name3 in GIRL_NAMES else "boy"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(ship=ship_id, hazard=hazard_id, signal=signal_id, response=response_id,
                       captain_name=name1, captain_gender=g1, mate_name=name2, mate_gender=g2,
                       singer_name=name3, singer_gender=g3, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIP_NAMES or params.hazard not in HAZARDS or params.signal not in SIGNALS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not valid_story_choice(SHIP_NAMES[params.ship], HAZARDS[params.hazard]):
        raise StoryError(explain_rejection(SHIP_NAMES[params.ship], HAZARDS[params.hazard]))
    world = tell(
        SHIP_NAMES[params.ship], HAZARDS[params.hazard], SIGNALS[params.signal],
        RESPONSES[params.response],
        CrewMember(id=params.captain_name, type=params.captain_gender, title=params.captain_name, role="captain", voice="calm", traits=[params.trait]),
        CrewMember(id=params.mate_name, type=params.mate_gender, title=params.mate_name, role="mate", voice="curious", traits=["listening"]),
        CrewMember(id=params.singer_name, type=params.singer_gender, title=params.singer_name, role="singer", voice="loud", traits=["preachy"]),
    )
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


ASP_RULES = r"""
hazard(F,H) :- hazard(F), risky(H).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,H,Signal) :- ship(S), hazard(H), signal(Signal), risky(H), reef_clearance(S, C), C <= 1.
outcome(safe) :- response(R), power(R,P), ship(S), storm_sense(S,SS), P >= SS.
outcome(damaged) :- response(R), power(R,P), ship(S), storm_sense(S,SS), P < SS.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("reef_clearance", sid, s.reef_clearance))
        lines.append(asp.fact("storm_sense", sid, s.storm_sense))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.risky:
            lines.append(asp.fact("risky", hid))
    for sid in SIGNALS:
        lines.append(asp.fact("signal", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_response", params.response)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    samples = [CURATED[0], CURATED[1]]
    for p in samples:
        if asp_outcome(p) not in {"safe", "damaged", "?"}:
            rc = 1
    try:
        _ = generate(CURATED[0])
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generation_prompts_smoke(sample: StorySample) -> str:
    return sample.story


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.captain_name}, {p.mate_name}, and {p.singer_name}: {p.response} near {p.hazard}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
