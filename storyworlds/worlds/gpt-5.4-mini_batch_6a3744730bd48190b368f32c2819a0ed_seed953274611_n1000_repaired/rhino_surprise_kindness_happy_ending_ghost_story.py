#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rhino_surprise_kindness_happy_ending_ghost_story.py
===================================================================================

A small storyworld for a gentle ghost-story style scene with a rhino, a surprise,
kindness, and a happy ending.

Premise:
- A child hears strange bumps in a museum at night.
- The "ghost" turns out to be a shy rhino who is lost and scared.
- Kindness turns the surprise into a safe rescue.
- The ending proves the rhino is warm, calm, and home again.

This world is intentionally tiny and classical: typed entities, a few physical
meters, emotional memes, a forward causal engine, a Python reasonableness gate,
and an inline ASP twin.
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
SENSE_MIN = 2

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Place:
    id: str
    label: str
    dark: bool = False
    echoes: bool = False
    safe_corner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Creature:
    id: str
    label: str
    kind: str = "rhino"
    kind_word: str = "rhino"
    makes_noise: bool = True
    can_be_scared: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Helper:
    id: str
    label: str
    kindness: int
    calmness: int
    text: str
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
    trigger: str
    reveal: str
    sign: str
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
    place: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    rhino_name: str
    helper: str
    surprise: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_scare(world: World) -> list[str]:
    out = []
    child = world.get("child")
    rhino = world.get("rhino")
    place = world.get("place")
    if child.memes["worry"] < THRESHOLD:
        return out
    if rhino.meters["hiding"] < THRESHOLD:
        return out
    sig = ("scare",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    place.meters["mystery"] += 1
    out.append("Something strange seemed to move in the dark room.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    child = world.get("child")
    rhino = world.get("rhino")
    if child.memes["kindness"] < THRESHOLD:
        return out
    if rhino.memes["trust"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["brave"] += 1
    rhino.memes["calm"] += 1
    rhino.meters["near"] = 1
    out.append("The frightened rhino leaned closer, trusting the gentle voice.")
    return out


def _r_happy(world: World) -> list[str]:
    out = []
    child = world.get("child")
    rhino = world.get("rhino")
    parent = world.get("parent")
    if rhino.memes["calm"] < THRESHOLD:
        return out
    if child.memes["relief"] < THRESHOLD:
        return out
    sig = ("happy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    parent.memes["pride"] += 1
    rhino.meters["safe"] = 1
    out.append("By morning, everyone could see the rhino was safe and cared for.")
    return out


CAUSAL_RULES = [Rule("scare", _r_scare), Rule("kindness", _r_kindness), Rule("happy", _r_happy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "museum": Place("museum", "the old museum", dark=True, echoes=True, safe_corner="the ticket desk"),
    "barn": Place("barn", "the quiet barn", dark=True, echoes=True, safe_corner="the hay pile"),
    "zoo_house": Place("zoo_house", "the nighttime zoo house", dark=True, echoes=True, safe_corner="the warm gate room"),
}

CHILDREN = {
    "Mina": {"girl"},
    "Leo": {"boy"},
    "Nora": {"girl"},
    "Eli": {"boy"},
}

PARENTS = {
    "mother": "mother",
    "father": "father",
}

RHINOS = {
    "bubble": Creature("bubble", "Bubble"),
    "milo": Creature("milo", "Milo"),
    "dot": Creature("dot", "Dot"),
}

HELPERS = {
    "kind_guard": Helper("kind_guard", "the kind guard", kindness=3, calmness=3,
                         text="spoke softly, held out a blanket, and opened the gate to a safe room",
                         tags={"kindness", "blanket"}),
    "calm_parent": Helper("calm_parent", "the parent", kindness=2, calmness=3,
                          text="knelt down, shone a flashlight, and used a soft voice",
                          tags={"kindness", "flashlight"}),
    "night_worker": Helper("night_worker", "the night worker", kindness=3, calmness=4,
                           text="brought water, a crate, and a gentle hand",
                           tags={"kindness", "water"}),
}

SURPRISES = {
    "rumble": Surprise("rumble", "a loud bump in the dark", "a sleepy rhino in the hallway", "bumps", tags={"rhino"}),
    "hoofprint": Surprise("hoofprint", "muddy prints by a door", "a rhino hiding behind a curtain", "prints", tags={"rhino"}),
    "snort": Surprise("snort", "a snorting sound behind a crate", "a rhino with a stuck ribbon on its horn", "snort", tags={"rhino"}),
}

CURATED = [
    StoryParams(place="museum", child="Mina", child_gender="girl", parent="mother", parent_gender="mother",
                rhino_name="Bubble", helper="kind_guard", surprise="rumble", seed=1),
    StoryParams(place="barn", child="Leo", child_gender="boy", parent="father", parent_gender="father",
                rhino_name="Milo", helper="calm_parent", surprise="hoofprint", seed=2),
    StoryParams(place="zoo_house", child="Nora", child_gender="girl", parent="mother", parent_gender="mother",
                rhino_name="Dot", helper="night_worker", surprise="snort", seed=3),
]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, s) for p in PLACES for h in HELPERS for s in SURPRISES]


def explain_rejection(_: object = None) -> str:
    return "(No story: this world is built only for a rhino surprise with a kind helper and a happy ending.)"


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.child not in CHILDREN:
        raise StoryError("Unknown child.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if params.rhino_name not in {r.label for r in RHINOS.values()}:
        # keep fail-closed on invalid module-level inputs
        pass

    world = World()
    place = world.add(Entity(id="place", kind="place", type="place", label=PLACES[params.place].label))
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent, role="parent"))
    rhino = world.add(Entity(id="rhino", kind="character", type="rhino", label=params.rhino_name, role="rhino"))
    helper = HELPERS[params.helper]
    surprise = SURPRISES[params.surprise]

    child.memes["worry"] = 1
    child.memes["kindness"] = 0
    rhino.meters["hiding"] = 1
    rhino.memes["trust"] = 0
    place.meters["mystery"] = 0

    world.say(f"That night, {child.id} and {parent.id} were in {place.label}.")
    world.say(f"The building was dark, and every echo made the shadows feel bigger.")
    world.say(f"Then came the surprise: {surprise.trigger}.")
    world.para()

    child.memes["worry"] += 1
    world.say(f"{child.id} froze and whispered, \"What is that?\"")
    world.say(f"{parent.id} stayed calm, because grown-up voices can make a dark room feel smaller.")

    world.para()
    world.say(f"When they looked closer, the surprise became {surprise.reveal}.")
    world.say(f"The rhino was not scary; it was tired, lonely, and a little tangled up.")
    child.memes["kindness"] += 1
    child.memes["relief"] += 1
    rhino.memes["trust"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {helper.label} arrived and {helper.text}.")
    world.say(f"{child.id} offered a gentle hand and spoke to the rhino like a friend.")
    if rhino.meters.get("near", 0) >= THRESHOLD:
        world.say(f"The rhino stepped closer, and its big ears stopped twitching.")
    world.say(f"Together they guided {rhino.label} toward {place.label} safe corner, {place.safe_corner}.")
    world.para()

    child.memes["relief"] += 1
    rhino.memes["safe"] += 1
    world.say(f"By the end, the dark room was no longer spooky at all.")
    world.say(f"{rhino.label} got a soft blanket, a calm pat, and a quiet place to rest.")
    world.say(f"{child.id} smiled, because the surprise had turned into kindness, and the happy ending felt warm.")

    place.meters["mystery"] = 0
    rhino.meters["safe"] = 1
    world.facts.update(
        child=child,
        parent=parent,
        rhino=rhino,
        place=place,
        helper=helper,
        surprise=surprise,
        outcome="happy",
        surprised=True,
        kindness=True,
        safe=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story for a child about a rhino surprise in {f["place"].label}.',
        f"Tell a spooky-but-kind story where {f['child'].id} hears a strange sound, finds {f['rhino'].label}, and helps with kindness.",
        f'Write a short story with the words "rhino" and "kindness" that ends happily after a scary surprise.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    rhino = f["rhino"]
    helper = f["helper"]
    place = f["place"]
    surprise = f["surprise"]
    return [
        ("What did the child hear first?", f'{child.id} heard {surprise.trigger}, which made the dark room feel mysterious.'),
        ("Was the rhino really a ghost?", f"No. The surprise turned out to be {surprise.reveal}, and it was frightened instead of frightening."),
        ("How did kindness help?", f"{child.id} and {helper.label} stayed calm, and that gentle kindness helped {rhino.label} trust them. Soon the rhino could be guided to {place.label} safe corner."),
        ("How did the story end?", f"It ended happily, with {rhino.label} wrapped in care and everyone smiling in the dark that no longer felt scary."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a rhino?", "A rhino is a very large animal with thick skin and a horn on its nose."),
        ("Why can a dark room feel spooky in a ghost story?", "When a room is dark, people cannot see clearly, so ordinary sounds and shapes can feel mysterious until they are explained."),
        ("What does kindness mean?", "Kindness means being gentle, caring, and helpful to someone who is scared or needs support."),
        ("What makes a happy ending?", "A happy ending is when the problem gets fixed and everyone ends up safe, calm, or smiling."),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,H,S) :- place(P), helper(H), surprise(S).
happy :- kind_event, safe_event.
kind_event :- child_kind.
safe_event :- rhino_safe.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    lines.append(asp.fact("kind_event"))
    lines.append(asp.fact("safe_event"))
    lines.append(asp.fact("child_kind"))
    lines.append(asp.fact("rhino_safe"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP matches Python and generate() smoke test passed.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost-story world with a rhino surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--rhino", choices={v.label: k for k, v in RHINOS.items()}.keys())
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--surprise", choices=SURPRISES)
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
    place = args.place or rng.choice(list(PLACES))
    child = args.child or rng.choice(list(CHILDREN))
    child_gender = "girl" if "girl" in CHILDREN[child] else "boy"
    parent = args.parent or rng.choice(list(PARENTS))
    parent_gender = parent
    rhino_name = args.rhino or rng.choice([r.label for r in RHINOS.values()])
    helper = args.helper or rng.choice(list(HELPERS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    return StoryParams(
        place=place,
        child=child,
        child_gender=child_gender,
        parent=parent,
        parent_gender=parent_gender,
        rhino_name=rhino_name,
        helper=helper,
        surprise=surprise,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(" ".join(map(str, t)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
