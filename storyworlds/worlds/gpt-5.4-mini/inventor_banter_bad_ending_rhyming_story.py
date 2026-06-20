#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inventor_banter_bad_ending_rhyming_story.py
============================================================================

A standalone Storyweavers world for a tiny rhyming tale about an inventor,
some banter, and a bad ending.

Premise:
- A child inventor wants to show off a homemade machine.
- A friend teases them in playful banter.
- The machine is used too soon, breaks badly, and the invention is ruined.
- The ending is sad, but the child learns to build more carefully next time.

The story is intentionally small and classical: a compact simulation with
typed entities, physical meters, emotional memes, a forward-chaining rule
engine, a reasonableness gate, and an ASP twin.

This file is self-contained aside from the shared result containers in
storyworlds/results.py and the lazy ASP helper in storyworlds/asp.py.
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
MAX_BANTER = 6.0


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
    broken: bool = False
    sparkly: bool = False

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
class Invention:
    id: str
    name: str
    phrase: str
    purpose: str
    setup: str
    rhyme: str
    safe: bool = True
    delicate: bool = False
    power: int = 1

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
class Banter:
    id: str
    line: str
    tease: str
    escalation: int
    kindness: int
    reply: str

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
class OutcomeRule:
    id: str
    apply: Callable[["World"], list[str]]

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    inv = world.get("inventor")
    machine = world.get("machine")
    if inv.meters["risk"] < THRESHOLD:
        return out
    sig = ("break", machine.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    machine.broken = True
    machine.meters["broken"] += 1
    inv.memes["dismay"] += 1
    out.append("__break__")
    return out


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    inventor = world.get("inventor")
    if not machine.broken:
        return out
    sig = ("smudge", machine.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    inventor.meters["mess"] += 1
    out.append("The workshop fell into a hush.")
    return out


CAUSAL_RULES = [
    OutcomeRule("break", _r_break),
    OutcomeRule("smudge", _r_smudge),
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


def risky_banter(banter: Banter) -> bool:
    return banter.escalation >= 3


def can_hold(machine: Invention, banter: Banter) -> bool:
    return machine.safe and banter.kindness >= 2 and machine.power >= 2


def story_breaks(machine: Invention, banter: Banter) -> bool:
    return machine.delicate and risky_banter(banter)


def reasonableness_ok(machine: Invention, banter: Banter) -> bool:
    return machine.safe and risky_banter(banter)


def predict_outcome(world: World, banter: Banter) -> dict:
    sim = world.copy()
    sim.get("inventor").meters["risk"] += float(banter.escalation)
    propagate(sim, narrate=False)
    return {
        "broken": sim.get("machine").broken,
        "mess": sim.get("inventor").meters["mess"],
    }


def setup_scene(world: World, inventor: Entity, friend: Entity, machine: Invention) -> None:
    inventor.memes["pride"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{inventor.id} was a young inventor with a little workshop light. "
        f"{inventor.id} had built {machine.phrase}, a bright idea in a tight little cart."
    )
    world.say(
        f"{friend.id} came over with a grin and a rhyme, ready for banter and time."
    )


def show_machine(world: World, inventor: Entity, machine: Invention) -> None:
    world.say(
        f'"Look here," said {inventor.id}, "my {machine.name} can {machine.purpose}!" '
        f"That was the plan, neat as a fan."
    )


def banter_line(world: World, friend: Entity, banter: Banter) -> None:
    friend.memes["tease"] += 1
    world.say(
        f'"{banter.line}" {friend.id} laughed. "{banter.tease}" '
        f"That playful banter bounced in the air like clatter."
    )


def warning(world: World, inventor: Entity, friend: Entity, machine: Invention, banter: Banter) -> None:
    pred = predict_outcome(world, banter)
    world.facts["predicted"] = pred
    if pred["broken"]:
        inventor.memes["worry"] += 1
        world.say(
            f"{inventor.id} frowned and saw the chance of wrong. "
            f'"Not yet," {inventor.id} said. "This needs more testing before it sings its song."'
        )
    else:
        world.say(
            f"{inventor.id} nodded along, but the machine still felt fragile and small. "
            f"It needed care before any big test at all."
        )


def defy(world: World, inventor: Entity, banter: Banter, machine: Invention) -> None:
    inventor.memes["risk"] += float(banter.escalation)
    world.say(
        f"{friend.id if False else inventor.id} tried to prove the machine could dance, "
        f"though the bolts were not ready for that kind of chance."
    )
    world.say(
        f"The knobs spun fast, the wires gave a spark, and the little machine shook in the dark."
    )


def accident(world: World, inventor: Entity, machine: Invention) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then crack went the cart, and the clever machine split apart. "
        f"The bright little thing was now a sad, bent part."
    )
    world.say(
        f"{inventor.id} stared at the pieces, unable to sing. "
        f"The workshop smelled like burnt dust and a broken spring."
    )


def ending_bad(world: World, inventor: Entity, friend: Entity, machine: Invention) -> None:
    inventor.memes["sadness"] += 2
    friend.memes["guilt"] += 1
    world.say(
        f"{friend.id} went quiet at last, and the teasing was through. "
        f"{friend.id} helped sweep up the screws, though the repair would be few."
    )
    world.say(
        f"{inventor.id} put the ruined gears in a tin on a shelf. "
        f"That night, the inventor felt low and blamed themself."
    )
    world.say(
        f"The ending was bad: the machine would not shine. "
        f"But {inventor.id} learned to test things before saying, 'Mine!'"
    )


def tell(machine: Invention, banter: Banter, inventor_name: str = "Nora",
         inventor_gender: str = "girl", friend_name: str = "Milo",
         friend_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    inventor = world.add(Entity(
        id=inventor_name, kind="character", type=inventor_gender,
        role="inventor", traits=["bright", "dreamy"],
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_gender,
        role="friend", traits=["playful", "teasing"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="machine", type="machine", label=machine.name, broken=False, sparkly=True))
    world.facts["machine"] = machine
    world.facts["banter"] = banter
    world.facts["parent"] = parent

    setup_scene(world, inventor, friend, machine)
    world.para()
    show_machine(world, inventor, machine)
    banter_line(world, friend, banter)
    warning(world, inventor, friend, machine, banter)

    if reasonableness_ok(machine, banter):
        defy(world, inventor, banter, machine)
        world.para()
        accident(world, inventor, machine)
        ending_bad(world, inventor, friend, machine)
        outcome = "bad"
    else:
        world.say("The rhyme stayed light, and the machine stayed right.")
        outcome = "safe"

    world.facts["outcome"] = outcome
    world.facts["inventor"] = inventor
    world.facts["friend"] = friend
    return world


INVENTIONS = {
    "music-box": Invention(
        "music-box", "music box", "a tiny music box with brass bells",
        "play a tune", "built of brass and string", "jingle in a tingle",
        safe=True, delicate=True, power=3,
    ),
    "kite-cart": Invention(
        "kite-cart", "kite cart", "a little cart with a paper kite",
        "roll down the hall", "built of wheels and tape", "roll and sway",
        safe=True, delicate=True, power=2,
    ),
    "robot-bird": Invention(
        "robot-bird", "robot bird", "a toy robot bird with silver wings",
        "flap and chirp", "built from wire and glue", "flutter and mutter",
        safe=True, delicate=True, power=4,
    ),
}

BANTERS = {
    "giggle": Banter("giggle", "That thing looks wobbly!", "Maybe your gizmo is a little silly.", 3, 1, "But I mean it kindly."),
    "joke": Banter("joke", "You call that a machine?", "I bet it can't even make a peep.", 4, 1, "It was teasing, not mean."),
    "challenge": Banter("challenge", "Bet it won't work!", "Show me, inventor, if you dare.", 5, 0, "That pushed too hard."),
}


GIRL_NAMES = ["Nora", "Maya", "Lily", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Milo", "Otis", "Finn", "Theo", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for iid, inv in INVENTIONS.items():
        for bid, banter in BANTERS.items():
            if reasonableness_ok(inv, banter):
                combos.append((iid, bid))
    return combos


@dataclass
class StoryParams:
    invention: str
    banter: str
    inventor_name: str
    inventor_gender: str
    friend_name: str
    friend_gender: str
    parent: str
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

CURATED = [
    ("music-box", "giggle"),
    ("kite-cart", "joke"),
    ("robot-bird", "challenge"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inv: Invention = f["machine"]
    banter: Banter = f["banter"]
    inventor = f["inventor"]
    friend = f["friend"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old about an inventor and some banter. Include the words "inventor" and "banter".',
        f"Tell a rhyming story where {inventor.id} shows off {inv.phrase}, then {friend.id} adds {banter.line.lower()} and the test ends badly.",
        f"Write a tiny bad-ending rhyme about a child inventor whose invention breaks after teasing banter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inventor = f["inventor"]
    friend = f["friend"]
    inv: Invention = f["machine"]
    banter: Banter = f["banter"]
    outcome = f["outcome"]
    qas = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {inventor.id}, a young inventor, and {friend.id}, who comes in with playful banter. The story follows what happens when the invention is shown too soon.",
        ),
        QAItem(
            question="What was the inventor trying to do?",
            answer=f"{inventor.id} wanted to use {inv.name} to {inv.purpose}. {inventor.id} hoped the invention would work like a charm.",
        ),
        QAItem(
            question="What did the friend say?",
            answer=f"{friend.id} said, \"{banter.line}\" That was banter: teasing words that sounded funny, but they made the moment less careful.",
        ),
    ]
    if outcome == "bad":
        qas.append(QAItem(
            question="What happened at the end?",
            answer=f"The machine broke apart, and the ending was bad. {inventor.id} felt sad, and the broken pieces had to be swept up instead of celebrated.",
        ))
        qas.append(QAItem(
            question="Why did the invention fail?",
            answer=f"It failed because the machine was delicate and the test came after risky banter pushed the inventor to try it too fast. The world model marks that kind of choice as too rough for the little machine.",
        ))
    return qas


WORLD_KNOWLEDGE = {
    "inventor": [QAItem(
        question="What is an inventor?",
        answer="An inventor is a person who makes new things or new ideas, like a machine, a tool, or a toy.",
    )],
    "banter": [QAItem(
        question="What is banter?",
        answer="Banter is light teasing or joking talk between people. It can be fun when it stays kind and gentle.",
    )],
    "machine": [QAItem(
        question="What is a machine?",
        answer="A machine is something with moving parts that helps do a job, like turning, lifting, or making a sound.",
    )],
    "broken": [QAItem(
        question="What does it mean when something is broken?",
        answer="If something is broken, it does not work the way it should anymore. It may need fixing before it can be used again.",
    )],
    "testing": [QAItem(
        question="Why should you test a new invention carefully?",
        answer="Testing carefully helps catch problems before something gets ruined or hurt. Small tests are safer than big risky ones.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items: list[QAItem] = []
    items.extend(WORLD_KNOWLEDGE["inventor"])
    items.extend(WORLD_KNOWLEDGE["banter"])
    items.extend(WORLD_KNOWLEDGE["machine"])
    if f["outcome"] == "bad":
        items.extend(WORLD_KNOWLEDGE["broken"])
        items.extend(WORLD_KNOWLEDGE["testing"])
    return items


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.broken:
            bits.append("broken=True")
        if e.sparkly:
            bits.append("sparkly=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_combo(I, B) :- invention(I), banter(B), safe(I), banter_ok(B).
bad_end(I, B) :- invention(I), banter(B), delicate(I), risky(B).
outcome(bad) :- bad_end(I, B).
outcome(safe) :- safe_combo(I, B), not bad_end(I, B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, inv in INVENTIONS.items():
        lines.append(asp.fact("invention", iid))
        if inv.safe:
            lines.append(asp.fact("safe", iid))
        if inv.delicate:
            lines.append(asp.fact("delicate", iid))
        lines.append(asp.fact("power", iid, inv.power))
    for bid, ban in BANTERS.items():
        lines.append(asp.fact("banter", bid))
        lines.append(asp.fact("banter_ok", bid))
        if ban.escalation >= 3:
            lines.append(asp.fact("risky", bid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_combo/2."))
    return sorted(set(asp.atoms(model, "safe_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_invention", params.invention),
        asp.fact("chosen_banter", params.banter),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    smoke = generate(resolve_params(argparse.Namespace(
        invention=None, banter=None, inventor_name=None, inventor_gender=None,
        friend_name=None, friend_gender=None, parent=None
    ), random.Random(7)))
    if not smoke.story.strip():
        print("MISMATCH: smoke story was empty.")
        rc = 1
    else:
        print("OK: smoke generate() produced a story.")
    if smoke.world is None or not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
        print("MISMATCH: smoke generate() missing outputs.")
        rc = 1
    else:
        print("OK: smoke generate() produced prompts and QA.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming inventor story with banter and a bad ending.")
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--banter", choices=BANTERS)
    ap.add_argument("--inventor-name")
    ap.add_argument("--inventor-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.invention is None or c[0] == args.invention)
              and (args.banter is None or c[1] == args.banter)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    inv_id, ban_id = rng.choice(sorted(combos))
    inv = INVENTIONS[inv_id]
    gender = args.inventor_gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        inventor_name = args.inventor_name or rng.choice(GIRL_NAMES)
    else:
        inventor_name = args.inventor_name or rng.choice(BOY_NAMES)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(inv_id, ban_id, inventor_name, gender, friend_name, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        INVENTIONS[params.invention],
        BANTERS[params.banter],
        params.inventor_name,
        params.inventor_gender,
        params.friend_name,
        params.friend_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show safe_combo/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible invention/banter combos:")
        for inv, ban in asp_valid_combos():
            print(f"  {inv:12} {ban}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for inv_id, ban_id in CURATED:
            params = StoryParams(
                inv_id, ban_id,
                inventor_name="Nora" if inv_id != "kite-cart" else "Lily",
                inventor_gender="girl",
                friend_name="Milo",
                friend_gender="boy",
                parent="mother",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.inventor_name} and {p.friend_name}: {p.invention} with {p.banter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
