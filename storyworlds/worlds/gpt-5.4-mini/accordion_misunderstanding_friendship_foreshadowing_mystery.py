#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/accordion_misunderstanding_friendship_foreshadowing_mystery.py
==============================================================================================

A standalone storyworld for a small mystery about an accordion, a misunderstanding,
and a friendship that clears up the clues.

The domain is intentionally tiny:
- a child hears mysterious accordion music
- a misunderstanding makes the music seem suspicious
- foreshadowing points to the real source of the sound
- friendship helps the characters solve the mystery kindly

The world is classical and state-driven:
- typed entities with physical meters and emotional memes
- forward rules over a fixpoint
- a reasonableness gate with an inline ASP twin
- generated prose, prompts, grounded QA, and world-knowledge QA
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
    role: str = ""
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Location:
    id: str
    label: str
    mood: str
    echo: str
    secret: str
    noisy: bool = False
    public: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    portable: bool = True
    musical: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Misunderstanding:
    id: str
    suspicion: str
    mistaken: str
    warning: str
    fear: str
    clears_when_seen: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Friendship:
    id: str
    helper_line: str
    softening_line: str
    apology_line: str
    made_braver: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Foreshadowing:
    id: str
    hint: str
    hint_line: str
    payoff: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["heard_sound"] < THRESHOLD:
            continue
        sig = ("suspicion", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["suspicion"] += 1
        out.append("__suspect__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if "child" in world.entities and "friend" in world.entities:
        child = world.get("child")
        friend = world.get("friend")
        if child.memes["suspicion"] >= THRESHOLD and friend.memes["kindness"] < THRESHOLD:
            sig = ("misunderstanding",)
            if sig not in world.fired:
                world.fired.add(sig)
                child.memes["worry"] += 1
                friend.memes["hurt"] += 1
                out.append("__misunderstanding__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    if "child" in world.entities and "friend" in world.entities:
        child = world.get("child")
        friend = world.get("friend")
        if child.memes["worry"] >= THRESHOLD and friend.memes["kindness"] >= THRESHOLD:
            sig = ("friendship",)
            if sig not in world.fired:
                world.fired.add(sig)
                child.memes["trust"] += 1
                friend.memes["trust"] += 1
                out.append("__friendship__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if "accordion" in world.entities and "hall" in world.entities:
        accordion = world.get("accordion")
        hall = world.get("hall")
        if accordion.meters["played"] >= THRESHOLD and hall.meters["echo"] >= THRESHOLD:
            sig = ("reveal",)
            if sig not in world.fired:
                world.fired.add(sig)
                hall.meters["clue"] += 1
                out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "mind", _r_suspicion),
    Rule("misunderstanding", "social", _r_misunderstanding),
    Rule("friendship", "social", _r_friendship),
    Rule("reveal", "mystery", _r_reveal),
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
        for s in produced:
            world.say(s)
    return produced


def choose_clue(world: World, instrument: Instrument, location: Location) -> str:
    if location.noisy:
        return f"The sound bounced through {location.label} like a secret"
    return f"The sound floated through {location.label} like a clue"


def preview(world: World, instrument: Instrument, location: Location) -> dict:
    sim = world.copy()
    sim.get("accordion").meters["played"] += 1
    propagate(sim, narrate=False)
    return {
        "echo": sim.get("hall").meters["echo"],
        "clue": sim.get("hall").meters["clue"],
    }


def intro(world: World, child: Entity, friend: Entity, location: Location) -> None:
    child.memes["curiosity"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"On a quiet evening, {child.id} and {friend.id} were in {location.label}. "
        f"The air felt {location.mood}, and every small sound seemed important."
    )


def hear(world: World, child: Entity, instrument: Instrument, location: Location) -> None:
    child.meters["heard_sound"] += 1
    world.say(
        f"Then they heard an accordion from somewhere nearby: {instrument.sound}. "
        f"{choose_clue(world, instrument, location)}."
    )
    world.say(
        f"{child.id} stopped at once. {child.pronoun().capitalize()} looked toward the hallway, "
        f"wondering who could be making that music."
    )


def misread(world: World, child: Entity, friend: Entity, misunderstanding: Misunderstanding) -> None:
    child.memes["suspicion"] += 1
    world.say(
        f"{child.id} frowned. \"It sounds strange,\" {child.pronoun()} whispered. "
        f"\"Maybe someone is hiding something.\""
    )
    world.say(
        f"{friend.id} wasn't so sure, but {child.id} had already remembered "
        f"{misunderstanding.suspicion}."
    )


def foreshadow(world: World, location: Location, foreshadowing: Foreshadowing) -> None:
    hall = world.get("hall")
    hall.meters["echo"] += 1
    world.say(
        f"Earlier, a tiny hint had gone by: {foreshadowing.hint}. "
        f"{foreshadowing.hint_line}."
    )


def investigate(world: World, child: Entity, friend: Entity, instrument: Instrument) -> None:
    world.say(
        f"So the two friends followed the sound together, slow and careful, "
        f"through the {world.get('hall').label}."
    )
    world.say(
        f"When they peeked around the corner, they found {instrument.phrase}. "
        f"It was only {instrument.clue}, not a secret at all."
    )


def reconcile(world: World, child: Entity, friend: Entity, misunderstanding: Misunderstanding,
              friendship: Friendship, instrument: Instrument) -> None:
    child.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{child.id} blushed. \"I thought the music meant trouble,\" {child.pronoun()} admitted."
    )
    world.say(
        f"{friend.id} smiled and said, \"Sometimes mysteries are just things we do not know yet.\" "
        f"{friendship.helper_line}"
    )
    world.say(
        f"{child.id} said sorry, and {friend.id} forgave {child.pronoun('object')} right away. "
        f"{misunderstanding.clears_when_seen}. {friendship.softening_line}"
    )


def ending(world: World, child: Entity, friend: Entity, instrument: Instrument,
           foreshadowing: Foreshadowing) -> None:
    world.say(
        f"At the end, the accordion music was no longer scary. "
        f"{child.id} and {friend.id} sat together and listened until the last note faded."
    )
    world.say(
        f"{foreshadowing.payoff} {instrument.label} rested nearby, and the hallway felt warm "
        f"instead of strange."
    )


def tell(location: Location, instrument: Instrument, misunderstanding: Misunderstanding,
         friendship: Friendship, foreshadowing: Foreshadowing,
         child_name: str = "Maya", child_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         parent_name: str = "Mom", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label=location.label))
    accordion = world.add(Entity(id="accordion", kind="thing", type="instrument", label=instrument.label))
    world.facts["parent"] = parent
    world.facts["location"] = location
    world.facts["instrument"] = instrument
    world.facts["misunderstanding"] = misunderstanding
    world.facts["friendship"] = friendship
    world.facts["foreshadowing"] = foreshadowing

    intro(world, child, friend, location)
    world.para()
    foreshadow(world, location, foreshadowing)
    hear(world, child, instrument, location)
    misread(world, child, friend, misunderstanding)
    world.para()
    child.memes["worry"] += 1
    friend.memes["kindness"] += 1
    accordion.meters["played"] += 1
    propagate(world, narrate=False)
    investigate(world, child, friend, instrument)
    world.para()
    reconcile(world, child, friend, misunderstanding, friendship, instrument)
    ending(world, child, friend, instrument, foreshadowing)

    world.facts.update(
        child=child,
        friend=friend,
        hall=hall,
        accordion=accordion,
        heard=True,
        solved=True,
    )
    return world


LOCATIONS = {
    "hallway": Location("hallway", "the hallway", "still", "soft", "hidden", noisy=False, public=False),
    "stairwell": Location("stairwell", "the stairwell", "echoing", "hollow", "hidden", noisy=True, public=False),
    "porch": Location("porch", "the porch", "moonlit", "thin", "nearby", noisy=True, public=True),
}

INSTRUMENTS = {
    "accordion": Instrument(
        "accordion",
        "accordion",
        "an accordion",
        "a lively tune",
        "a neighbor practicing for the evening",
        portable=True,
        musical=True,
        tags={"accordion", "music"},
    )
}

MISUNDERSTANDINGS = {
    "suspicion": Misunderstanding(
        "suspicion",
        "a worried guess",
        "a secret or a trick",
        "It only sounded mysterious because the hall echoed",
        "They almost thought the music meant trouble",
        "the mystery was only a friendly song",
        tags={"mystery", "misunderstanding"},
    )
}

FRIENDSHIPS = {
    "comfort": Friendship(
        "comfort",
        "They stayed together",
        "Their friendship made the hallway feel kinder",
        "They promised to listen first next time",
        "Both of them became braver once they understood",
        tags={"friendship"},
    )
}

FORESHADOWS = {
    "echo": Foreshadowing(
        "echo",
        "a tiny echo from the hallway",
        "Before the song began, the wall had already made a whispery echo",
        "That echo was the clue that pointed to the real answer",
        tags={"foreshadowing", "mystery"},
    )
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Theo", "Ben", "Owen"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ray"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for inst in INSTRUMENTS:
            for mis in MISUNDERSTANDINGS:
                combos.append((loc, inst, mis))
    return combos


@dataclass
@dataclass
class StoryParams:
    location: str
    instrument: str
    misunderstanding: str
    friendship: str
    foreshadowing: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about an accordion and a misunderstanding.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--friendship", choices=FRIENDSHIPS)
    ap.add_argument("--foreshadowing", choices=FORESHADOWS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.location is None or c[0] == args.location)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, inst, mis = rng.choice(sorted(combos))
    friendship = args.friendship or "comfort"
    foreshadowing = args.foreshadowing or "echo"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    parent_gender = args.parent_gender or ("woman" if parent_name in {"Mom", "Aunt June"} else "man")
    return StoryParams(loc, inst, mis, friendship, foreshadowing,
                       child_name, child_gender, friend_name, friend_gender,
                       parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        LOCATIONS[params.location],
        INSTRUMENTS[params.instrument],
        MISUNDERSTANDINGS[params.misunderstanding],
        FRIENDSHIPS[params.friendship],
        FORESHADOWS[params.foreshadowing],
        params.child_name, params.child_gender,
        params.friend_name, params.friend_gender,
        params.parent_name, params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    loc = f["location"]
    return [
        f'Write a child-friendly mystery story that includes the word "accordion" and is set in {loc.label}.',
        f"Tell a story where a strange accordion sound causes a misunderstanding, but friendship clears it up.",
        f"Write a gentle mystery with foreshadowing: a tiny clue hints at the accordion before the friends find it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    instrument = f["instrument"]
    mis = f["misunderstanding"]
    fs = f["foreshadowing"]
    loc = f["location"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two friends who heard a mysterious sound in {loc.label}."),
        ("What sound did they hear?",
         f"They heard an accordion playing a lively tune. At first, that made the hall seem strange."),
        ("Why did {child}'s friend think it was okay?".replace("{child}", child.id),
         f"{friend.id} stayed calm and helped {child.id} look for the source. That friendship mattered because it turned fear into a kind search."),
        ("What was the misunderstanding?",
         f"{child.id} thought the music might mean a secret or a trick, but it was really only {mis.clears_when_seen}."),
        ("How did the foreshadowing help?",
         f"The tiny echo was a clue before the song was even found. It pointed toward the hallway and made the answer feel fair."),
        ("How did the story end?",
         f"The friends found the accordion, understood the mystery, and felt closer afterward. The scary guess changed into trust."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an accordion?",
         "An accordion is a musical instrument with buttons or keys and sides that open and close. It makes music when someone squeezes and plays it."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks something is one way, but it is really something else."),
        ("What is foreshadowing?",
         "Foreshadowing is a small clue that hints at what will happen later in a story."),
        ("What is friendship?",
         "Friendship is when people care about each other, help each other, and stay kind."),
        ("Why can an echo be a clue in a mystery?",
         "An echo can show that a sound is bouncing around a room, which helps someone guess where it came from."),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.noisy:
            lines.append(asp.fact("noisy", lid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friendship", fid))
    for tid in FORESHADOWS:
        lines.append(asp.fact("foreshadowing", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(L, I, M) :- location(L), instrument(I), misunderstanding(M).
has_mystery(M) :- misunderstanding(M).
has_friendship(F) :- friendship(F).
has_hint(T) :- foreshadowing(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(resolve_params(argparse.Namespace(
            location=None, instrument=None, misunderstanding=None,
            friendship=None, foreshadowing=None,
            child_name=None, child_gender=None, friend_name=None,
            friend_gender=None, parent_name=None, parent_gender=None,
        ), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this domain expects an accordion, a mystery, and a misunderstanding that can be resolved by friendship.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (location, instrument, misunderstanding) combos:\n")
        for loc, inst, mis in combos:
            print(f"  {loc:10} {inst:12} {mis}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("hallway", "accordion", "suspicion", "comfort", "echo",
                        "Maya", "girl", "Noah", "boy", "Mom", "woman"),
            StoryParams("stairwell", "accordion", "suspicion", "comfort", "echo",
                        "Lily", "girl", "Leo", "boy", "Dad", "man"),
            StoryParams("porch", "accordion", "suspicion", "comfort", "echo",
                        "Nora", "girl", "Finn", "boy", "Aunt June", "woman"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child_name} and {p.friend_name}: accordion mystery at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
