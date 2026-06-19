#!/usr/bin/env python3
"""
storyworlds/worlds/twinkling_bridge_friendship.py
=================================================

A standalone storyworld for the seed:

    Words: twinkling bridge
    Features: Friendship, Flashback, Suspense
    Style: Animal Story

Source tale written from the seed
---------------------------------
Milo Mouse had to cross the twinkling bridge before moonrise to bring elderberry
syrup to Aunt Mole. Fern Squirrel came with him, because friends do not let
friends hurry over scary bridges alone.

Halfway to the creek, Milo stopped. He remembered last spring, when the same
bridge went creak-creak under his paws and one loose plank tipped like a seesaw.
The bridge looked beautiful tonight, sparkling with dew, but the memory made his
whiskers tremble. Across the water, Aunt Mole's lamp blinked once, then vanished
behind the reeds.

Fern tested the first plank and imagined what would happen if Milo ran: the
loose board would buck, the syrup basket would swing, and Milo might tumble into
the cold creek. So Fern tied a vine rail from post to post. Milo held the vine,
Fern crossed beside him, and step by careful step the bridge carried them safely.
At Aunt Mole's door, the bottle was still full, Milo's paws were dry, and the
twinkling bridge no longer looked like a monster. It looked like a path a friend
had helped him cross.
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
        if self.attrs.get("plural"):
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


@dataclass
class Animal:
    id: str
    species: str
    body: str
    home: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bridge:
    id: str
    label: str
    water: str
    sparkle: str
    far_side: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    phrase: str
    risk: str
    severity: int
    flashback: str
    test_sound: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    handles: set[str]
    strength: int
    setup: str
    crossing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Errand:
    id: str
    item: str
    recipient: str
    urgency: str
    payoff: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, bridge: Bridge, hazard: Hazard, errand: Errand) -> None:
        self.bridge = bridge
        self.hazard = hazard
        self.errand = errand
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.bridge, self.hazard, self.errand)
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


def _r_flashback(world: World) -> list[str]:
    hero = world.entities.get("hero")
    bridge = world.entities.get("bridge")
    if not hero or not bridge or hero.memes["memory"] < THRESHOLD:
        return []
    sig = ("flashback_fear", hero.id, world.hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    bridge.memes["monster_shape"] += 1
    return ["__memory__"]


def _r_unready_crossing(world: World) -> list[str]:
    hero = world.entities.get("hero")
    bridge = world.entities.get("bridge")
    parcel = world.entities.get("parcel")
    if not hero or not bridge or hero.meters["crossing"] < THRESHOLD:
        return []
    if bridge.meters["secured"] >= THRESHOLD:
        return []
    sig = ("danger", bridge.id, world.hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["danger"] += world.hazard.severity
    hero.memes["fear"] += 1
    if parcel:
        parcel.meters["at_risk"] += 1
    return ["The bridge turned risky under hurried paws."]


def _r_safe_crossing(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    bridge = world.entities.get("bridge")
    parcel = world.entities.get("parcel")
    if not hero or not bridge or hero.meters["crossing"] < THRESHOLD:
        return []
    if bridge.meters["secured"] < THRESHOLD:
        return []
    sig = ("safe_cross", bridge.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["safe"] += 1
    hero.memes["courage"] += 1
    hero.memes["fear"] = 0.0
    if friend:
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
    if parcel:
        parcel.meters["delivered_intact"] += 1
    return ["__safe__"]


CAUSAL_RULES = [
    Rule("flashback_fear", "emotional", _r_flashback),
    Rule("unready_crossing", "physical", _r_unready_crossing),
    Rule("safe_crossing", "physical_social", _r_safe_crossing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def aid_fits(aid: Aid, hazard: Hazard) -> bool:
    return hazard.risk in aid.handles and aid.strength >= hazard.severity


def select_aid(hazard: Hazard) -> Optional[Aid]:
    choices = [a for a in AIDS.values() if aid_fits(a, hazard)]
    return sorted(choices, key=lambda a: (a.strength, a.id))[0] if choices else None


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    try_cross(sim, sim.get("hero"), narrate=False)
    bridge = sim.get("bridge")
    parcel = sim.get("parcel")
    return {
        "danger": bridge.meters["danger"],
        "parcel_risk": parcel.meters["at_risk"] if parcel else 0,
        "fear": sim.get("hero").memes["fear"],
    }


def begin(world: World, hero: Entity, friend: Entity, animal: Animal,
          friend_animal: Animal, errand: Errand) -> None:
    hero.memes["care"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.id} {animal.species} had to cross the twinkling bridge before "
        f"{errand.urgency} with {errand.item} for {errand.recipient}."
    )
    world.say(
        f"{friend.id} {friend_animal.species} came too, because friends do not "
        f"let friends hurry over scary bridges alone."
    )


def approach_bridge(world: World, hero: Entity) -> None:
    world.say(
        f"The bridge hung over {world.bridge.water}, {world.bridge.sparkle}. "
        f"Across the water, {world.bridge.far_side}."
    )
    hero.memes["memory"] += 1
    propagate(world, narrate=False)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"Halfway there, {hero.id} stopped. {world.hazard.flashback} "
            f"The memory made {hero.pronoun('possessive')} whiskers tremble."
        )


def friend_predicts(world: World, hero: Entity, friend: Entity) -> None:
    pred = predict_crossing(world)
    friend.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_parcel_risk"] = pred["parcel_risk"]
    world.say(
        f"{friend.id} tested the first board: {world.hazard.test_sound}. "
        f"{friend.pronoun().capitalize()} pictured {world.hazard.consequence} "
        f"if {hero.id} ran across without help."
    )


def prepare_aid(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    bridge = world.get("bridge")
    bridge.meters["secured"] += 1
    friend.memes["care"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"So {friend.id} chose {aid.label}. {aid.setup.format(hero=hero.id, friend=friend.id)} "
        f"{hero.id} took a breath and trusted the plan."
    )


def try_cross(world: World, hero: Entity, narrate: bool = True) -> None:
    hero.meters["crossing"] += 1
    propagate(world, narrate=narrate)


def cross_safely(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    try_cross(world, hero)
    world.say(
        f"{aid.crossing.format(hero=hero.id, friend=friend.id)} Step by careful "
        f"step, the bridge carried them over."
    )
    if world.get("bridge").meters["safe"] >= THRESHOLD:
        world.say(
            f"At {world.errand.recipient}'s door, {world.errand.payoff}. "
            f"The twinkling bridge no longer looked like a monster. It looked "
            f"like a path a friend had helped {hero.pronoun('object')} cross."
        )


def tell(bridge: Bridge, hazard: Hazard, aid: Aid, errand: Errand,
         hero_name: str = "Milo", animal_id: str = "mouse",
         friend_name: str = "Fern", friend_id: str = "squirrel",
         trait: str = "timid") -> World:
    world = World(bridge, hazard, errand)
    animal = ANIMALS[animal_id]
    friend_animal = ANIMALS[friend_id]
    hero = world.add(Entity("hero", kind="character", type=animal.species,
                            label=hero_name, role="hero", traits=[trait],
                            attrs={"animal": animal_id}))
    hero.id = hero_name
    friend = world.add(Entity("friend", kind="character", type=friend_animal.species,
                              label=friend_name, role="friend",
                              attrs={"animal": friend_id}))
    friend.id = friend_name
    world.add(Entity("bridge", type="bridge", label=bridge.label))
    world.add(Entity("parcel", type="parcel", label=errand.item))

    begin(world, hero, friend, animal, friend_animal, errand)
    world.para()
    approach_bridge(world, hero)
    friend_predicts(world, hero, friend)
    world.para()
    prepare_aid(world, hero, friend, aid)
    cross_safely(world, hero, friend, aid)

    world.facts.update(hero=hero, friend=friend, animal=animal,
                       friend_animal=friend_animal, bridge=bridge,
                       hazard=hazard, aid=aid, errand=errand,
                       resolved=world.get("bridge").meters["safe"] >= THRESHOLD)
    return world


ANIMALS = {
    "mouse": Animal("mouse", "Mouse", "small paws", "a grass-woven nest", "squeak",
                    {"mouse"}),
    "squirrel": Animal("squirrel", "Squirrel", "quick paws", "a hollow oak", "chitter",
                       {"squirrel"}),
    "rabbit": Animal("rabbit", "Rabbit", "soft paws", "a ferny burrow", "thump",
                     {"rabbit"}),
    "hedgehog": Animal("hedgehog", "Hedgehog", "little feet", "a leaf pile", "snuffle",
                       {"hedgehog"}),
}

BRIDGES = {
    "creek": Bridge("creek", "willow bridge", "the silver creek",
                    "twinkling with dew like tiny stars",
                    "Aunt Mole's lamp blinked once behind the reeds",
                    {"loose_plank", "mist", "slippery_moss"}, {"bridge", "creek"}),
    "meadow": Bridge("meadow", "grass bridge", "the dark meadow ditch",
                     "twinkling with fireflies along its rails",
                     "the berry burrow glowed under a mushroom cap",
                     {"mist", "slippery_moss"}, {"bridge", "fireflies"}),
    "pine": Bridge("pine", "pine-root bridge", "the cold brook",
                   "twinkling where moonlight touched the wet roots",
                   "the owl doctor's window shone amber",
                   {"loose_plank", "slippery_moss"}, {"bridge", "brook"}),
}

HAZARDS = {
    "loose_plank": Hazard(
        "loose_plank", "a loose plank", "balance", 3,
        "He remembered last spring, when the bridge went creak-creak under his paws and one plank tipped like a seesaw.",
        "creak-creak",
        "the loose board bucking, the parcel swinging, and a small body tumbling toward the creek",
        {"plank", "suspense"}),
    "mist": Hazard(
        "mist", "a curtain of mist", "visibility", 2,
        "He remembered a foggy morning when the far rail disappeared and every step felt like stepping into milk.",
        "hush-hush",
        "the path vanishing, the parcel bumping the rail, and a frightened friend taking the wrong step",
        {"mist", "suspense"}),
    "slippery_moss": Hazard(
        "slippery_moss", "slick green moss", "traction", 3,
        "He remembered rainwater shining on the boards and his paws skidding sideways with a squeak.",
        "skritch",
        "paws sliding, the parcel tipping, and the cold water waiting underneath",
        {"moss", "suspense"}),
}

AIDS = {
    "vine_rail": Aid(
        "vine_rail", "a vine rail", {"balance", "traction"}, 3,
        "{friend} tied a vine from post to post, low enough for {hero} to hold.",
        "{hero} held the vine while {friend} walked beside him.",
        {"vine", "friendship"}),
    "firefly_lantern": Aid(
        "firefly_lantern", "a firefly lantern", {"visibility"}, 2,
        "{friend} asked three fireflies to glow inside a nutshell lantern.",
        "{friend} lifted the lantern so {hero} could see each board.",
        {"fireflies", "lantern", "friendship"}),
    "sand_path": Aid(
        "sand_path", "a pinch of dry sand", {"traction"}, 3,
        "{friend} scattered dry sand over the slick places until the boards stopped shining.",
        "{hero} stepped on the sandy patches while {friend} counted softly.",
        {"sand", "friendship"}),
    "slow_song": Aid(
        "slow_song", "a slow counting song", {"visibility", "balance"}, 1,
        "{friend} sang a slow song, one note for every board.",
        "{hero} crossed one note at a time while {friend} kept singing.",
        {"song", "friendship"}),
}

ERRANDS = {
    "syrup": Errand("syrup", "elderberry syrup", "Aunt Mole", "moonrise",
                    "the bottle was still full and Aunt Mole smiled from her blanket",
                    {"medicine"}),
    "acorns": Errand("acorns", "a pouch of winter acorns", "Grandpa Badger", "the cold wind",
                     "the acorns were dry and Grandpa Badger clapped his paws",
                     {"food"}),
    "bell": Errand("bell", "the lost nest bell", "Baby Wren", "the owls began calling",
                   "the bell chimed clear and Baby Wren stopped crying",
                   {"rescue"}),
}

HERO_NAMES = ["Milo", "Pip", "Toby", "Nico", "Bram", "Otto"]
FRIEND_NAMES = ["Fern", "Hazel", "Juniper", "Moss", "Poppy", "Rowan"]
TRAITS = ["timid", "careful", "hopeful", "nervous", "small"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for bridge_id, bridge in BRIDGES.items():
        for hazard_id in bridge.affords:
            hazard = HAZARDS[hazard_id]
            for errand_id in ERRANDS:
                for aid_id, aid in AIDS.items():
                    if aid_fits(aid, hazard):
                        combos.append((bridge_id, hazard_id, errand_id, aid_id))
    return sorted(combos)


@dataclass
class StoryParams:
    bridge: str
    hazard: str
    errand: str
    aid: str
    hero: str
    animal: str
    friend: str
    friend_animal: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [("What is a bridge for?",
                "A bridge lets someone cross over water, a ditch, or another gap without going through it.")],
    "creek": [("What is a creek?",
               "A creek is a small stream of moving water. It can be cold and slippery near the banks.")],
    "plank": [("Why is a loose plank unsafe?",
               "A loose plank can move under your feet. If it tips, you can lose your balance.")],
    "mist": [("Why can mist make crossing hard?",
              "Mist makes it harder to see where you are stepping. Going slowly and using light can help.")],
    "moss": [("Why is wet moss slippery?",
              "Wet moss holds water on its surface, so paws or shoes can slide on it easily.")],
    "vine": [("How can a vine rail help?",
              "A vine rail gives someone a steady thing to hold. Holding it can keep them balanced while they cross.")],
    "fireflies": [("Why do fireflies glow?",
                   "Fireflies make light in their bodies. In stories, their glow can help small animals see at night.")],
    "sand": [("How does sand help with slipping?",
              "Dry sand adds grip. It can make a slick place rougher so feet or paws do not slide as much.")],
    "friendship": [("What does a good friend do when you are scared?",
                    "A good friend listens, stays close, and helps you find a safe next step instead of rushing you.")],
}
KNOWLEDGE_ORDER = ["bridge", "creek", "plank", "mist", "moss", "vine", "fireflies", "sand", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    hazard, aid = f["hazard"], f["aid"]
    return [
        'Write an animal story for a 3-to-5-year-old that includes "twinkling bridge", friendship, a flashback, and suspense.',
        f"Tell a story where {hero.id} remembers a scary bridge accident, but {friend.id} helps with {aid.label}.",
        f"Write a suspenseful but gentle friendship story about crossing a twinkling bridge with {hazard.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    hazard, aid, errand = f["hazard"], f["aid"], f["errand"]
    bridge = f["bridge"]
    memory = {
        "loose_plank": "the bridge had gone creak-creak under his paws and one plank had tipped like a seesaw",
        "mist": "the far rail had disappeared in fog and every step had felt like stepping into milk",
        "slippery_moss": "rainwater had shone on the boards and his paws had skidded sideways with a squeak",
    }[hazard.id]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two animal friends. {hero.id} has to cross the twinkling bridge, and {friend.id} stays close to help."),
        (f"Why did {hero.id} need to cross the bridge?",
         f"{hero.id} needed to bring {errand.item} to {errand.recipient} before {errand.urgency}. The errand gave the scary crossing a kind reason."),
        (f"What flashback made {hero.id} afraid?",
         f"{hero.id} remembered an earlier time when {memory}. That memory put fear on {hero.pronoun('object')} before the crossing began."),
        (f"What did {friend.id} predict could happen?",
         f"{friend.id} predicted danger from {hazard.phrase}: {hazard.consequence}. That prediction came from testing the bridge before anyone rushed across."),
        ("How did the friends solve the problem?",
         f"They used {aid.label}, which matched the bridge's {hazard.risk} problem. Because the aid fit the hazard, the parcel stayed safe and {hero.id} crossed with courage."),
        ("How did the story end?",
         f"At the end, {errand.payoff}. The twinkling bridge changed from a frightening memory into a path made safer by friendship."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bridge"].tags) | set(f["hazard"].tags) | set(f["aid"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("creek", "loose_plank", "syrup", "vine_rail", "Milo", "mouse", "Fern", "squirrel", "timid"),
    StoryParams("meadow", "mist", "bell", "firefly_lantern", "Pip", "rabbit", "Hazel", "mouse", "nervous"),
    StoryParams("pine", "slippery_moss", "acorns", "sand_path", "Bram", "hedgehog", "Rowan", "squirrel", "careful"),
    StoryParams("creek", "mist", "syrup", "firefly_lantern", "Nico", "mouse", "Poppy", "rabbit", "hopeful"),
]


def explain_rejection(hazard: Hazard, aid: Optional[Aid] = None) -> str:
    if aid and not aid_fits(aid, hazard):
        return (f"(No story: {aid.label} does not solve {hazard.phrase}; the aid "
                f"must handle the bridge's {hazard.risk} problem strongly enough.)")
    return (f"(No story: no available aid can solve {hazard.phrase} safely.)")


ASP_RULES = r"""
fits(Aid, Hazard) :- aid(Aid), hazard(Hazard), handles(Aid, Risk),
                     risk(Hazard, Risk), strength(Aid, A), severity(Hazard, H), A >= H.
valid(Bridge, Hazard, Errand, Aid) :- affords(Bridge, Hazard), errand(Errand),
                                      fits(Aid, Hazard).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bridge_id, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bridge_id))
        for hazard in sorted(bridge.affords):
            lines.append(asp.fact("affords", bridge_id, hazard))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("risk", hazard_id, hazard.risk))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for errand_id in ERRANDS:
        lines.append(asp.fact("errand", errand_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("strength", aid_id, aid.strength))
        for risk in sorted(aid.handles):
            lines.append(asp.fact("handles", aid_id, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: animal friends crossing a twinkling bridge.")
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend-animal", choices=ANIMALS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print facts plus inline ASP rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bridge and args.hazard and args.hazard not in BRIDGES[args.bridge].affords:
        raise StoryError(f"(No story: {BRIDGES[args.bridge].label} does not have {HAZARDS[args.hazard].phrase} in this world.)")
    if args.hazard and args.aid and not aid_fits(AIDS[args.aid], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(HAZARDS[args.hazard], AIDS[args.aid]))
    combos = [
        c for c in valid_combos()
        if (args.bridge is None or c[0] == args.bridge)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.errand is None or c[2] == args.errand)
        and (args.aid is None or c[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    bridge, hazard, errand, aid = rng.choice(combos)
    animal = args.animal or rng.choice(sorted(ANIMALS))
    friend_choices = [a for a in sorted(ANIMALS) if a != animal]
    friend_animal = args.friend_animal or rng.choice(friend_choices)
    if friend_animal == animal and args.friend_animal:
        friend_animal = rng.choice(friend_choices)
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    trait = rng.choice(TRAITS)
    return StoryParams(bridge, hazard, errand, aid, hero, animal, friend, friend_animal, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(BRIDGES[params.bridge], HAZARDS[params.hazard],
                 AIDS[params.aid], ERRANDS[params.errand],
                 params.hero, params.animal, params.friend,
                 params.friend_animal, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (bridge, hazard, errand, aid) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{x:16}" for x in combo))
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
            header = f"### {p.hero} and {p.friend}: {p.hazard} on {p.bridge} ({p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
