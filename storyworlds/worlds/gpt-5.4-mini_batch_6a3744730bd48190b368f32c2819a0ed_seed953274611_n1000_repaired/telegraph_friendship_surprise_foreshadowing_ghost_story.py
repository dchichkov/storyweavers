#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/telegraph_friendship_surprise_foreshadowing_ghost_story.py
==========================================================================================

A small standalone story world built from the seed words:

- telegraph
- Friendship
- Surprise
- Foreshadowing
- Ghost Story

Premise
-------
Two children discover an old telegraph in a quiet train station. A shy ghost
uses the telegraph to send friendly taps, there is a small mystery, and the
children learn that the "haunting" was really a lonely friend asking to be
noticed. The story supports a calm ghost-story mood without becoming scary.

This world models a tiny causal arc:
- a notice is seen, which raises curiosity;
- a telegraph message creates suspense and a foreshadowed surprise;
- the children answer kindly;
- the ghost reveals itself and becomes a friend;
- the ending image proves the change in the station.

The script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- generated prompts, story-grounded QA, and world-knowledge QA
- `--verify`, `--trace`, `--qa`, `--json`, `--asp`, `--show-asp`
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    visible: bool = True
    is_ghost: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.is_ghost or self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Place:
    id: str
    label: str
    quiet: bool = True
    old: bool = False
    drafty: bool = False
    echoey: bool = False
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
class Telegraph:
    id: str
    label: str
    message: str
    tap: str
    glow: str
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
class Ghost:
    id: str
    label: str
    nickname: str
    wish: str
    reveal_line: str
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
class Surprise:
    id: str
    label: str
    reveal: str
    ending_image: str
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
class StoryParams:
    place: str = "station"
    telegraph: str = "station_telegraph"
    ghost: str = "lantern_ghost"
    surprise: str = "friendly_reveal"
    child1: str = "Mina"
    child1_gender: str = "girl"
    child2: str = "Nico"
    child2_gender: str = "boy"
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    if world.get("station").meters["unease"] < THRESHOLD:
        return out
    sig = ("curiosity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for p in world.people():
        p.memes["curiosity"] += 1
    out.append("__curiosity__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ghost").meters["near"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for p in world.people():
        p.memes["kindness"] += 1
    world.get("ghost").memes["lonely"] = 0
    out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(place: Place, telegraph: Telegraph, ghost: Ghost, surprise: Surprise) -> bool:
    return place.old and place.echoey and "telegraph" in telegraph.tags and "ghost" in ghost.tags and "reveal" in surprise.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, tel in TELEGRAPHS.items():
            for gid, gh in GHOSTS.items():
                for sid, sp in SURPRISES.items():
                    if reasonableness(place, tel, gh, sp):
                        combos.append((pid, tid, gid, sid))
    return combos


def predict_story(world: World) -> dict:
    return {
        "unease": world.get("station").meters["unease"],
        "friendship": world.get("ghost").meters["near"] >= THRESHOLD,
    }


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    for p in (a, b):
        p.memes["friendship"] += 1
    world.say(
        f"On a windy evening, {a.id} and {b.id} wandered into {place.label}, "
        f"where the benches creaked and the lamps shone low and yellow."
    )
    world.say(
        "Near the waiting room stood an old telegraph, dusted with silver and "
        "silent as a held breath."
    )


def foreshadow(world: World, a: Entity, b: Entity, tel: Telegraph, place: Place) -> None:
    world.get("station").meters["unease"] += 1
    world.say(
        f"{a.id} noticed a tiny string of paper taped to the telegraph: "
        f'"When the wire taps, listen kindly."'
    )
    world.say(
        f"{b.id} shivered, not from fear but from wondering what sort of voice "
        f"could leave a message like that in {place.label}."
    )


def tap_message(world: World, tel: Telegraph) -> None:
    world.get("station").meters["unease"] += 1
    world.get("ghost").meters["near"] += 1
    world.get("ghost").memes["lonely"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came {tel.tap} {tel.tap} {tel.tap} from the telegraph key, "
        f"soft and careful, like someone knocking with a fingertip."
    )
    world.say(
        f"The little lamp beside it gave a faint {tel.glow}, and the children "
        f"looked at each other with wide eyes."
    )


def answer_kindly(world: World, a: Entity, b: Entity, ghost: Ghost) -> None:
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    world.say(
        f'"Who is there?" {a.id} asked the empty room. Then {b.id} smiled and '
        f'added, "If someone is lonely, we can be nice."'
    )
    world.say(
        f"They tapped back on the telegraph, once for hello and twice for yes."
    )


def reveal(world: World, ghost: Ghost, surprise: Surprise) -> None:
    ghost.meters["seen"] += 1
    ghost.memes["lonely"] = 0
    ghost.memes["relief"] += 1
    world.say(
        f"{surprise.reveal}"
    )
    world.say(
        f"{ghost.reveal_line} The ghost was not cruel at all. It had only been "
        f"waiting for someone brave enough to notice."
    )


def friendship_end(world: World, a: Entity, b: Entity, ghost: Ghost, surprise: Surprise) -> None:
    for p in (a, b):
        p.memes["joy"] += 1
        p.memes["friendship"] += 1
    world.say(
        f"{a.id} and {b.id} left a ribbon on the telegraph key so the ghost "
        f"would know it had friends now."
    )
    world.say(
        f"{surprise.ending_image} The station felt warm in its old bones, and "
        f"the bell over the door gave a happy little ring when the children left."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    tel = TELEGRAPHS[params.telegraph]
    ghost = GHOSTS[params.ghost]
    surprise = SURPRISES[params.surprise]

    a = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender))
    b = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender))
    station = world.add(Entity(id="station", type="place", label=place.label))
    ghost_ent = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost.label, is_ghost=True))
    world.add(Entity(id="telegraph", type="tool", label=tel.label))

    setup(world, a, b, place)
    world.para()
    foreshadow(world, a, b, tel, place)
    tap_message(world, tel)
    world.para()
    answer_kindly(world, a, b, ghost)
    reveal(world, ghost_ent, surprise)
    world.para()
    friendship_end(world, a, b, ghost_ent, surprise)

    world.facts.update(
        child1=a,
        child2=b,
        place=place,
        telegraph=tel,
        ghost=ghost,
        surprise=surprise,
        station=station,
        outcome="friendly",
        foreshadowed=True,
        surprise_reveal=True,
    )
    return world


PLACES = {
    "station": Place(
        id="station",
        label="the old train station",
        quiet=True,
        old=True,
        drafty=True,
        echoey=True,
        tags={"station", "old", "echo"},
    )
}

TELEGRAPHS = {
    "station_telegraph": Telegraph(
        id="station_telegraph",
        label="the brass telegraph",
        message="listen kindly",
        tap="tap",
        glow="little green glow",
        tags={"telegraph", "message"},
    )
}

GHOSTS = {
    "lantern_ghost": Ghost(
        id="lantern_ghost",
        label="a lantern ghost",
        nickname="the lantern ghost",
        wish="to be noticed kindly",
        reveal_line="It held up a small lantern hand and bowed.",
        tags={"ghost", "friendship"},
    )
}

SURPRISES = {
    "friendly_reveal": Surprise(
        id="friendly_reveal",
        label="a friendly reveal",
        reveal="At last, a pale shape stepped out from behind the ticket booth, and both children gasped.",
        ending_image="In the last light, the ghost stood by the telegraph like a patient friend.",
        tags={"surprise", "reveal"},
    )
}


CURATED = [
    StoryParams(
        place="station",
        telegraph="station_telegraph",
        ghost="lantern_ghost",
        surprise="friendly_reveal",
        child1="Mina",
        child1_gender="girl",
        child2="Nico",
        child2_gender="boy",
        seed=777,
    )
]


KNOWLEDGE = {
    "telegraph": [
        (
            "What is a telegraph?",
            "A telegraph is an old machine that sends messages by making taps through a wire. People used it before phones were common.",
        )
    ],
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is often a person-shaped spirit that can be spooky or friendly. In a ghost story, the surprise is often what the ghost really wants.",
        )
    ],
    "station": [
        (
            "What is a train station?",
            "A train station is a place where trains stop so people can get on or off. Old stations can be quiet and echoey at night.",
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about someone and treating them kindly. Friends listen, help, and make each other feel less alone.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you do not expect. In a story, a surprise can make the ending feel exciting and new.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a clue that hints at what might happen later. It helps the reader feel suspense before the surprise arrives.",
        )
    ],
}

KNOWLEDGE_ORDER = ["telegraph", "station", "ghost", "foreshadowing", "surprise", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story that includes the word {f['telegraph'].label} and ends in friendship.",
        f"Tell a spooky-but-kind story set in {f['place'].label} where a telegraph gives an eerie clue before a surprise reveal.",
        "Write a small ghost story with foreshadowing, a telegraph message, and a friendly ending for young children.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    place = f["place"]
    ghost = f["ghost"]
    surprise = f["surprise"]
    qa = [
        (
            "Where did the story happen?",
            f"It happened in {place.label}, which was old, echoey, and quiet enough for the telegraph taps to sound mysterious.",
        ),
        (
            "What first made the children feel curious?",
            f"They saw the note on the telegraph that said to listen kindly. That clue foreshadowed that the strange place was trying to say something gentle.",
        ),
        (
            "What did the telegraph do?",
            f"It sent careful tapping sounds and made the children notice that someone or something wanted to talk. The message built suspense before the reveal.",
        ),
        (
            "Who was behind the mystery?",
            f"It was {ghost.label}, and it was lonely rather than mean. The surprise was that the ghost wanted friendship, not fright.",
        ),
        (
            "How did {0} and {1} respond to the ghost?".format(a.id, b.id),
            f"{a.id} and {b.id} answered kindly and tapped back on the telegraph. Their friendly response helped the ghost feel seen, which changed the whole mood of the story.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"telegraph", "station", "ghost", "friendship", "surprise", "foreshadowing"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.is_ghost:
            bits.append("ghost=True")
        lines.append(f"  {e.id:14} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world requires an old echoey station, a telegraph, a ghost, and a surprise reveal.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.old:
            lines.append(asp.fact("old", pid))
        if place.echoey:
            lines.append(asp.fact("echoey", pid))
    for tid, tel in TELEGRAPHS.items():
        lines.append(asp.fact("telegraph", tid))
        lines.append(asp.fact("tagged", tid, "telegraph"))
    for gid, gh in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("tagged", gid, "ghost"))
        lines.append(asp.fact("tagged", gid, "friendship"))
    for sid, sp in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("tagged", sid, "surprise"))
        lines.append(asp.fact("tagged", sid, "reveal"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, G, S) :- place(P), telegraph(T), ghost(G), surprise(S), old(P), echoey(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combo).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(seed=1), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world with telegraph messages and a friendly surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--telegraph", choices=TELEGRAPHS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if args.telegraph and args.telegraph not in TELEGRAPHS:
        raise StoryError("(No story: unknown telegraph.)")
    if args.ghost and args.ghost not in GHOSTS:
        raise StoryError("(No story: unknown ghost.)")
    if args.surprise and args.surprise not in SURPRISES:
        raise StoryError("(No story: unknown surprise.)")
    place = args.place or "station"
    telegraph = args.telegraph or "station_telegraph"
    ghost = args.ghost or "lantern_ghost"
    surprise = args.surprise or "friendly_reveal"
    child1 = args.child1 or rng.choice(["Mina", "Iris", "June", "Owen"])
    child2 = args.child2 or rng.choice([n for n in ["Nico", "Ezra", "Pia", "Lou"] if n != child1])
    child1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    child2_gender = args.child2_gender or ("boy" if child1_gender == "girl" else "girl")
    return StoryParams(
        place=place,
        telegraph=telegraph,
        ghost=ghost,
        surprise=surprise,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.telegraph not in TELEGRAPHS or params.ghost not in GHOSTS or params.surprise not in SURPRISES:
        raise StoryError(explain_rejection())
    world = tell(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
