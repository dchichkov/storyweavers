#!/usr/bin/env python3
"""
storyworlds/worlds/station_inner_ghost.py
=========================================

A standalone story world sketch for a child alone at a station who hears a
ghostly warning and has to decide whether a private worry is a clue or only a
fear. The world is intentionally small: a station, a warning, a train, a visible
test, and a child whose inner monologue becomes useful only after it is checked
against the physical world.

Run it
------
    python storyworlds/worlds/station_inner_ghost.py
    python storyworlds/worlds/station_inner_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/station_inner_ghost.py --all --trace
    python storyworlds/worlds/station_inner_ghost.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: physical and emotional state live on the same carriers.
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type in {"girl", "mother", "aunt", "grandmother", "woman"}:
            return "herself"
        if self.type in {"boy", "father", "uncle", "grandfather", "man"}:
            return "himself"
        return "themself"


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Station:
    id: str
    name: str
    platform: str
    shelter: str
    sound: str
    helper: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    ghost_name: str
    ghost_role: str
    apparition: str
    line: str
    requires: str
    check_phrase: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Train:
    id: str
    color: str
    arrival: str
    clue_text: str
    clue_phrase: str
    right_home: bool
    destination: str
    clue_kind: str
    danger_reason: str
    safe_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Worry:
    id: str
    thought: str
    small_body: str
    brave_body: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    station: str
    warning: str
    train: str
    worry: str
    name: str
    gender: str
    trait: str
    guardian: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def role(self, role: str) -> Optional[Entity]:
        return next((e for e in self.entities.values() if e.role == role), None)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.station)
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


def _r_warning_focus(world: World) -> list[str]:
    child = world.role("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost:
        return []
    if ghost.memes["warned"] < THRESHOLD or child.memes["private_worry"] < THRESHOLD:
        return []
    sig = ("warning_focus", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["attention"] += 1
    child.memes["fear"] += 0.5
    return []


def _r_train_risk(world: World) -> list[str]:
    train = world.entities.get("train")
    if not train or not train.attrs.get("arrived"):
        return []
    sig = ("train_risk", train.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if not train.attrs.get("right_home"):
        train.meters["wrong_train"] += 1
        train.meters["danger"] += 1
    else:
        train.meters["safe_home"] += 1
    return []


def _r_clue_becomes_clear(world: World) -> list[str]:
    child = world.role("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return []
    if child.memes["attention"] < THRESHOLD or clue.meters["visible"] < THRESHOLD:
        return []
    sig = ("clue_clear", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["clarity"] += 1
    clue.meters["understood"] += 1
    return []


def _r_decision_state(world: World) -> list[str]:
    child = world.role("child")
    train = world.entities.get("train")
    if not child or not train or child.memes["clarity"] < THRESHOLD:
        return []
    sig = ("decision", train.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if train.meters["danger"] >= THRESHOLD:
        child.memes["trusted_clue"] += 1
        child.memes["courage"] += 1
    else:
        child.memes["named_fear"] += 1
        child.memes["courage"] += 1
        child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    return []


CAUSAL_RULES = [
    Rule("warning_focus", "inner", _r_warning_focus),
    Rule("train_risk", "physical", _r_train_risk),
    Rule("clue_clear", "physical_inner", _r_clue_becomes_clear),
    Rule("decision", "inner", _r_decision_state),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            for sentence in rule.apply(world):
                world.say(sentence)
        changed = len(world.fired) != before


# ---------------------------------------------------------------------------
# Domain logic.
# ---------------------------------------------------------------------------
def clue_available(station: Station, warning: Warning, train: Train) -> bool:
    return warning.requires in station.supports and train.clue_kind == warning.requires


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, station in STATIONS.items():
        for wid, warning in WARNINGS.items():
            for tid, train in TRAINS.items():
                if clue_available(station, warning, train):
                    combos.append((sid, wid, tid))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "clue" if not TRAINS[params.train].right_home else "fear"


def valid_story(station_id: str, warning_id: str, train_id: str) -> bool:
    return (station_id, warning_id, train_id) in set(valid_combos())


def explain_rejection(station: Station, warning: Warning, train: Train) -> str:
    if warning.requires not in station.supports:
        return (f"(No story: {station.name} does not have {warning.check_phrase} "
                f"needed to test the ghost's warning.)")
    if train.clue_kind != warning.requires:
        return (f"(No story: the ghost says to check {warning.check_phrase}, but "
                f"this train gives a different kind of clue. The child needs a "
                f"concrete test, not a guess.)")
    return "(No story: this station warning cannot be tested.)"


# ---------------------------------------------------------------------------
# Verbs / screenplay beats.
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, station: Station, guardian: str) -> None:
    world.say(
        f"Once upon a time, a {child.traits[0]} little {child.type} named "
        f"{child.id} waited alone at {station.name}."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {guardian} had gone to the "
        f"ticket window, and the {station.platform} felt big around "
        f"{child.pronoun('object')}."
    )
    world.say(
        f"The {station.shelter} stood close by, and {station.sound}."
    )


def private_worry(world: World, child: Entity, worry: Worry) -> None:
    child.memes["private_worry"] += 1
    child.memes["lonely"] += 0.5
    world.say(
        f"{child.id} held {child.pronoun('possessive')} ticket in both hands."
    )
    world.say(
        f'"{worry.thought}?" {child.pronoun()} thought, and the thought felt '
        f"small and loud inside {child.pronoun('possessive')} coat."
    )


def ghost_warning(world: World, warning: Warning) -> None:
    ghost = world.add(Entity(
        id="ghost", kind="character", type="ghost", label=warning.ghost_name,
        role="warning", traits=[warning.ghost_role],
    ))
    ghost.memes["warned"] += 1
    world.say(
        f"Then a pale {warning.apparition} glimmered beside the bench, as thin "
        f"as breath on glass."
    )
    world.say(f'"{warning.line}," whispered {warning.ghost_name}.')


def train_arrives(world: World, train_cfg: Train, warning: Warning) -> None:
    child = world.role("child")
    if child is None:
        raise StoryError("(No story: the child was not introduced.)")
    train = world.add(Entity(
        id="train", type="train", label=f"the {train_cfg.color} train",
        attrs={"right_home": train_cfg.right_home, "arrived": True},
    ))
    clue = world.add(Entity(
        id="clue", type="sign", label=train_cfg.clue_text,
        attrs={"kind": train_cfg.clue_kind},
    ))
    clue.meters["visible"] += 1
    world.say(
        f"Soon {train_cfg.arrival}, and the doors sighed open in a silver line."
    )
    if train_cfg.clue_kind == "bell_count":
        clue_place = "Over the platform"
    elif train_cfg.clue_kind == "lantern_signal":
        clue_place = "On the front rail"
    else:
        clue_place = "Near one window"
    world.say(
        f"{clue_place}, {train_cfg.clue_phrase}. It was exactly the sort of "
        f"thing {warning.ghost_name} had told {child.pronoun('object')} to check."
    )
    propagate(world)
    if train.meters["danger"] >= THRESHOLD:
        train.meters["destination_seen"] += 1


def inner_turn(world: World, child: Entity, worry: Worry, train_cfg: Train) -> None:
    if child.memes["trusted_clue"] >= THRESHOLD:
        world.say(
            f"{child.id}'s knees wanted to hurry, but {child.pronoun('possessive')} "
            f"mind made a quiet picture: {train_cfg.danger_reason}."
        )
        world.say(
            f'"This is not just being scared," {child.pronoun()} told '
            f"{child.reflexive()}. \"This is a clue.\""
        )
    else:
        world.say(
            f"{child.id}'s stomach still felt like a button pulled too tight, "
            f"but the clue did not match the scary picture in "
            f"{child.pronoun('possessive')} head."
        )
        world.say(
            f'"{worry.brave_body}," {child.pronoun()} told '
            f"{child.reflexive()}. \"That was a fear, not a clue.\""
        )


def ending(world: World, child: Entity, station: Station, warning: Warning,
           train_cfg: Train, guardian: str) -> None:
    if child.memes["trusted_clue"] >= THRESHOLD:
        helper = station.helper[0].upper() + station.helper[1:]
        world.say(
            f"{child.id} stepped back from the yellow line and called to "
            f"{station.helper}."
        )
        world.say(
            f"{helper} noticed {train_cfg.clue_text} and nodded. "
            f'"Good eyes. That train is not yours."'
        )
        world.say(
            f"A little later, {child.pronoun('possessive')} {guardian} came back, "
            f"and the right train hummed in with its warm windows."
        )
        world.say(
            f"As {child.id} climbed aboard, the pale {warning.apparition} "
            f"glimmered once, and {station.final_image}."
        )
    else:
        helper = station.helper[0].upper() + station.helper[1:]
        world.say(
            f"{child.id} showed the ticket to {station.helper} before stepping on."
        )
        world.say(
            f"{helper} smiled and said, \"Yes, this one goes home.\" "
            f"{train_cfg.safe_reason}"
        )
        world.say(
            f"When {child.pronoun('possessive')} {guardian} came hurrying back, "
            f"{child.id} was waiting in the bright doorway, not alone anymore."
        )
        world.say(
            f"The pale {warning.apparition} faded into the station clock, and "
            f"{station.final_image}."
        )


def tell(station: Station, warning: Warning, train: Train, worry: Worry,
         name: str = "Mia", gender: str = "girl", trait: str = "careful",
         guardian: str = "aunt") -> World:
    world = World(station)
    child = world.add(Entity(
        id=name, kind="character", type=gender, role="child",
        traits=[trait, "small"], attrs={"guardian": guardian},
    ))

    introduce(world, child, station, guardian)
    private_worry(world, child, worry)

    world.para()
    ghost_warning(world, warning)
    propagate(world)
    train_arrives(world, train, warning)

    world.para()
    inner_turn(world, child, worry, train)
    ending(world, child, station, warning, train, guardian)

    world.facts.update(
        child=child, station=station, warning=warning, train=train,
        worry=worry, guardian=guardian, outcome="clue" if not train.right_home else "fear",
        clue_checked=child.memes["clarity"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
STATIONS = {
    "small": Station(
        "small", "the small station", "empty platform", "green clock",
        "the rails hummed softly", "the station guard",
        "the clock ticked on, gentle as a heart",
        supports={"destination_card", "bell_count"}, tags={"station", "train"}),
    "rainy": Station(
        "rainy", "Rainpool Station", "wet platform", "glass shelter",
        "rain tapped tiny fingers on the roof", "the conductor",
        "rain silvered the rails behind them",
        supports={"destination_card", "lantern_signal"}, tags={"station", "rain"}),
    "old": Station(
        "old", "Old Elm Station", "wooden platform", "lamp room",
        "a far whistle curled through the dark", "the porter",
        "the lamp room glowed like a jar of stars",
        supports={"destination_card", "bell_count", "lantern_signal"},
        tags={"station", "ghost"}),
}

WARNINGS = {
    "card": Warning(
        "card", "the old stationmaster", "stationmaster", "blue coat",
        "Read the card before you ride. A train can wear a friendly face and "
        "still go the wrong way",
        "destination_card", "the destination card",
        "A real worry gets checked against the world",
        tags={"ghost", "sign", "train"}),
    "bell": Warning(
        "bell", "the bell lady", "bell keeper", "white scarf",
        "Wait for the two clear bells. One bell calls workers, but two bells "
        "call passengers home",
        "bell_count", "the station bell",
        "Listening can turn a worry into a useful clue",
        tags={"ghost", "bell", "train"}),
    "lantern": Warning(
        "lantern", "the lantern man", "night watchman", "smoky lantern",
        "Look for the green lantern. Red light means stop, even when the doors "
        "are open",
        "lantern_signal", "the lantern signal",
        "A brave choice can be waiting",
        tags={"ghost", "signal", "train"}),
}

TRAINS = {
    "depot": Train(
        "depot", "blue", "a blue train slid in without a cheerful whistle",
        "a card that said DEPOT ONLY", "a little card said DEPOT ONLY",
        False, "the depot", "destination_card",
        "it would carry the train away to the shed, not home",
        "The card named the home line clearly.",
        tags={"train", "sign", "clue"}),
    "home_card": Train(
        "home_card", "red", "a red train rolled in with warm square windows",
        "a card that said HOME LINE", "a little card said HOME LINE",
        True, "home", "destination_card",
        "the worry would have been wrong because the card named home",
        "The card named home, so the private worry loosened.",
        tags={"train", "sign"}),
    "one_bell": Train(
        "one_bell", "green", "a green train clanked in after one lonely bell",
        "one clear bell", "the station bell rang only once",
        False, "the yard", "bell_count",
        "one bell meant the train was going to the yard",
        "Two bells would have meant a passenger train.",
        tags={"train", "bell", "clue"}),
    "two_bells": Train(
        "two_bells", "yellow", "a yellow train came in after two bright bells",
        "two clear bells", "the station bell rang twice, clear and round",
        True, "home", "bell_count",
        "the worry would have been wrong because two bells meant home",
        "The two bells matched the ghost's rule, so the train was the right one.",
        tags={"train", "bell"}),
    "red_lantern": Train(
        "red_lantern", "black", "a black train breathed steam beside the platform",
        "a red lantern", "a red lantern swung beneath the driver's window",
        False, "the freight siding", "lantern_signal",
        "the red lantern meant stop, not climb aboard",
        "A green lantern would have meant it was safe to board.",
        tags={"train", "signal", "clue"}),
    "green_lantern": Train(
        "green_lantern", "cream", "a cream train purred into the station",
        "a green lantern", "a green lantern shone beneath the driver's window",
        True, "home", "lantern_signal",
        "the worry would have been wrong because the green lantern meant go",
        "The green lantern matched the ghost's rule, so the train was safe.",
        tags={"train", "signal"}),
}

WORRIES = {
    "wrong_train": Worry(
        "wrong_train", "What if I get on the wrong train and it takes me far away",
        "the train felt too big", "I checked what I could check",
        tags={"worry", "train"}),
    "left_behind": Worry(
        "left_behind", "What if everyone forgets me here",
        "the platform felt too empty", "Being alone made the thought louder",
        tags={"worry", "alone"}),
    "ghost": Worry(
        "ghost", "What if the whisper is only trying to scare me",
        "the ghost felt cold and strange", "A scary voice can still point to a real sign",
        tags={"worry", "ghost"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Rose", "Lucy"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Theo", "Max", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "quiet", "curious", "thoughtful", "brave", "watchful"]
GUARDIANS = ["aunt", "father", "mother", "grandmother", "uncle"]

CURATED = [
    StoryParams("small", "card", "depot", "wrong_train", "Mia", "girl",
                "careful", "aunt"),
    StoryParams("old", "bell", "two_bells", "left_behind", "Leo", "boy",
                "quiet", "father"),
    StoryParams("rainy", "lantern", "red_lantern", "ghost", "Nora", "girl",
                "watchful", "mother"),
    StoryParams("old", "card", "home_card", "wrong_train", "Theo", "boy",
                "thoughtful", "grandmother"),
    StoryParams("rainy", "lantern", "green_lantern", "left_behind", "Ava",
                "girl", "brave", "uncle"),
]


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "station": [("What is a train station?",
                 "A train station is a place where trains stop so people can get "
                 "on and off. It often has platforms, signs, clocks, and helpers.")],
    "train": [("Why should you check before boarding a train?",
               "Different trains can go to different places, even if they stop at "
               "the same platform. Checking the sign or asking a helper keeps you "
               "from riding the wrong way.")],
    "ghost": [("What is a ghost story?",
               "A ghost story is a story with a spirit or strange visitor in it. "
               "It can be spooky, but it can also be gentle and helpful.")],
    "sign": [("What does a destination sign tell you?",
              "A destination sign tells where a train is going. Reading it helps "
              "a passenger know whether the train is the right one.")],
    "bell": [("Why might a station use bells?",
              "A station bell can send a simple signal that people can hear. In "
              "this story, the number of bells tells the child what kind of train "
              "has arrived.")],
    "signal": [("What does a train signal do?",
                "A signal tells people when to stop, wait, or go. It is a simple "
                "way to keep trains and passengers safe.")],
    "worry": [("Can a worry ever be useful?",
               "Yes. A worry can be useful when it reminds you to check a real "
               "clue, like a sign or a signal. If the world does not support it, "
               "then it may just be a fear.")],
    "alone": [("What can a child do if they feel alone at a station?",
               "They can stay in one safe place and ask a station helper for help. "
               "They should not run onto a train just because they feel scared.")],
}
KNOWLEDGE_ORDER = ["station", "train", "sign", "bell", "signal", "ghost",
                   "worry", "alone"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, station, warning, train = f["child"], f["station"], f["warning"], f["train"]
    return [
        f'Write a TinyStories-style ghost story using the word "station", where '
        f'a {child.type} named {child.id} waits alone and checks a real clue '
        f'before boarding a train.',
        f"Tell a child-facing story about {child.id} at {station.name}. A gentle "
        f"ghost says, \"{warning.line},\" and {child.id} must decide whether a "
        f"private worry is a clue or a fear.",
        f"Write a concrete story where a {train.color} train arrives at a station "
        f"and the ending turns on {train.clue_text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, station, warning, train, worry = (
        f["child"], f["station"], f["warning"], f["train"], f["worry"]
    )
    guardian = f["guardian"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {child.id}, a little {child.type} waiting alone at "
         f"{station.name}. {child.pronoun('possessive').capitalize()} {guardian} "
         f"has gone to the ticket window."),
        (f"What private worry did {child.id} have?",
         f"{child.id} worried, \"{worry.thought}?\" The worry felt loud because "
         f"{child.pronoun()} was small and alone on the platform."),
        ("What did the ghost warn?",
         f"{warning.ghost_name.capitalize()} warned {child.id} to check "
         f"{warning.check_phrase} before riding. The warning gave the child a "
         f"concrete thing to check instead of only a spooky feeling."),
        (f"What clue did {child.id} notice?",
         f"{child.id} noticed {train.clue_text}. That clue matched the ghost's "
         f"test, so the child could compare the worry with the real station."),
    ]
    if f["outcome"] == "clue":
        qa.append((
            f"Was {child.id}'s worry a clue or a fear?",
            f"It became a clue because {train.clue_text} showed the train was "
            f"not the right one. {child.id} stepped back and asked "
            f"{station.helper} instead of boarding."))
        qa.append((
            "How did the story end?",
            f"{child.id} waited for the right train, and {child.pronoun('possessive')} "
            f"{guardian} came back before they rode home. The ghost faded after "
            f"the warning had helped."))
    else:
        qa.append((
            f"Was {child.id}'s worry a clue or a fear?",
            f"It was a fear because {train.clue_text} showed the train matched "
            f"the ghost's rule. {child.id} still checked with {station.helper}, "
            f"but the clue said it was safe to go home."))
        qa.append((
            "How did the story end?",
            f"{child.id} boarded from the bright doorway after checking the clue. "
            f"The ghost faded into the station, and {child.id} was not alone "
            f"anymore."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["station"].tags) | set(f["warning"].tags) | set(f["train"].tags)
    tags |= set(f["worry"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        attrs = {k: v for k, v in e.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid only when the station has the exact clue channel the ghost
% tells the child to check, and the train exposes that same clue channel.
valid(S, W, T) :- station(S), warning(W), train(T),
                  supports(S, R), requires(W, R), train_clue(T, R).

outcome(clue) :- chosen_train(T), wrong_train(T).
outcome(fear) :- chosen_train(T), not wrong_train(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, station in STATIONS.items():
        lines.append(asp.fact("station", sid))
        for req in sorted(station.supports):
            lines.append(asp.fact("supports", sid, req))
    for wid, warning in WARNINGS.items():
        lines.append(asp.fact("warning", wid))
        lines.append(asp.fact("requires", wid, warning.requires))
    for tid, train in TRAINS.items():
        lines.append(asp.fact("train", tid))
        lines.append(asp.fact("train_clue", tid, train.clue_kind))
        if not train.right_home:
            lines.append(asp.fact("wrong_train", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_train", params.train)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    empty = build_parser().parse_args([])
    for seed in range(200):
        try:
            cases.append(resolve_params(empty, random.Random(seed)))
        except StoryError:
            continue
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child alone at a station, a ghostly "
                    "warning, and a private worry tested against a concrete clue.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.station and args.warning and args.train:
        st, wr, tr = STATIONS[args.station], WARNINGS[args.warning], TRAINS[args.train]
        if not clue_available(st, wr, tr):
            raise StoryError(explain_rejection(st, wr, tr))

    combos = [c for c in valid_combos()
              if (args.station is None or c[0] == args.station)
              and (args.warning is None or c[1] == args.warning)
              and (args.train is None or c[2] == args.train)]
    if not combos:
        raise StoryError("(No valid station, warning, and train combination matches.)")

    station_id, warning_id, train_id = rng.choice(sorted(combos))
    worry_id = args.worry or rng.choice(sorted(WORRIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(station_id, warning_id, train_id, worry_id, name, gender,
                       trait, guardian)


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params.station, params.warning, params.train):
        raise StoryError(explain_rejection(
            STATIONS[params.station], WARNINGS[params.warning], TRAINS[params.train]))
    world = tell(
        STATIONS[params.station], WARNINGS[params.warning], TRAINS[params.train],
        WORRIES[params.worry], params.name, params.gender, params.trait,
        params.guardian,
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (station, warning, train) combos:\n")
        for station, warning, train in combos:
            print(f"  {station:7} {warning:8} {train}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.name}: {p.station} / {p.warning} / {p.train} "
                      f"({outcome_of(p)})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
