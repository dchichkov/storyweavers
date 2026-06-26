#!/usr/bin/env python3
"""
A small comedy storyworld set in a bus depot.

Premise:
- A cheerful autobot works at a busy bus depot.
- It wears a garter-like spring strap that keeps a route card clipped in place.
- A harmless mix-up makes the autobot fear it will lose the right bus sign.
- A helper uses humor and dialogue to solve the problem.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bus depot"


@dataclass
class Gizmo:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str
    helper: str
    gadget: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the bus depot")

GADGETS = {
    "garter": Gizmo(
        id="garter",
        label="a bright garter",
        phrase="a bright garter with a springy clip",
        guards={"paper", "tag"},
    ),
    "clip": Gizmo(
        id="clip",
        label="a metal clip",
        phrase="a tiny metal clip",
        guards={"paper"},
    ),
}

NAMES = ["Milo", "Nina", "Ravi", "Tia", "Zuri", "Owen"]
HELPERS = ["mechanic", "dispatcher", "driver", "porter"]
TRAITS = ["playful", "curious", "cheerful", "silly", "bright"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _do_mistake(world: World, autobot: Entity, gadget: Gizmo) -> None:
    if autobot.memes.get("pride", 0) >= 1:
        autobot.memes["fluster"] = autobot.memes.get("fluster", 0) + 1
    autobot.meters["rattle"] = autobot.meters.get("rattle", 0) + 1
    autobot.meters["lost"] = autobot.meters.get("lost", 0) + 1
    if gadget.id == "garter":
        autobot.meters["paper"] = autobot.meters.get("paper", 0) + 1


def tell(name: str, helper: str, gadget_id: str) -> World:
    world = World(SETTING)
    autobot = world.add(Entity(
        id=name,
        kind="character",
        type="autobot",
        traits=["tiny", random.choice(TRAITS)],
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper,
        label=f"the {helper}",
    ))
    gadget = world.add(Entity(
        id=gadget_id,
        type="thing",
        label=GADGETS[gadget_id].label,
        phrase=GADGETS[gadget_id].phrase,
        owner=autobot.id,
        caretaker=helper_ent.id,
        worn_by=autobot.id,
    ))

    autobot.memes["joy"] = 1
    autobot.memes["pride"] = 1
    world.say(
        f"{autobot.id} was a tiny autobot at {world.setting.place} who loved keeping the platform tidy."
    )
    world.say(
        f"It wore {gadget.phrase} so its route card would stay clipped on during the rush."
    )

    world.para()
    world.say(
        f"One noisy morning, {autobot.id} looked at the arrivals board and said, "
        f"“I am perfectly ready. Absolutely ready. Extra ready.”"
    )
    world.say(
        f"The {helper} laughed and said, “That is a lot of ready for one little autobot.”"
    )
    world.say(
        f"Then the wind from a passing coach whooshed through {world.setting.place} and sent the route card spinning."
    )
    _do_mistake(world, autobot, gadget)
    world.say(
        f"{autobot.id} gasped. “Oh no! My sign has gone wobbly-whoo!” it said."
    )

    world.para()
    autobot.memes["worry"] = 1
    world.say(
        f"The {helper} smiled and pointed at the bright {gadget.id}. “Good thing you wore that garter-clip. It kept the paper close, even when the depot got silly.”"
    )
    world.say(
        f"{autobot.id} blinked twice. “So the garter was not fancy nonsense?” it asked."
    )
    world.say(
        f"“Not at all,” said the {helper}. “It was small, but it saved the day.”"
    )
    world.say(
        f"{autobot.id} giggled so hard its wheels made a tiny squeak. “Then I shall call it my hero garter!”"
    )
    world.say(
        f"Together they pinned the card straight, and the buses rolled in one by one while everyone at the depot smiled."
    )
    autobot.memes["joy"] = 3
    autobot.memes["worry"] = 0
    autobot.meters["found"] = 1

    world.facts.update(
        autobot=autobot,
        helper=helper_ent,
        gadget=gadget,
        setting=world.setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short comedy story for children about an autobot at a bus depot, with a funny mix-up and a cheerful fix.",
        f"Tell a dialogue-heavy story where {f['autobot'].id} worries about a garter at the bus depot and a helper makes the problem funny.",
        "Make the ending show that the small gadget helped the autobot keep its place and stay calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["autobot"]
    h: Entity = f["helper"]
    g: Entity = f["gadget"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {a.id}, a tiny autobot at the bus depot.",
        ),
        QAItem(
            question=f"What did {a.id} wear to keep the route card in place?",
            answer=f"{a.id} wore {g.phrase} so the route card would stay clipped on.",
        ),
        QAItem(
            question=f"Who helped {a.id} when the card went wobbly?",
            answer=f"The {h.type} helped {a.id} by laughing, explaining the garter-clip, and fixing the card.",
        ),
        QAItem(
            question=f"Why did {a.id} worry after the coach passed?",
            answer=f"{a.id} worried because the wind made the route card spin, so the autobot thought it had lost control of the sign.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the card pinned straight and everyone at the depot smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, park, and get ready for the next trips.",
        ),
        QAItem(
            question="What does a clip do?",
            answer="A clip holds something in place so it does not fall or slide away.",
        ),
        QAItem(
            question="Why can wind be annoying outside?",
            answer="Wind can be annoying because it can blow papers, hats, and other light things around.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.

valid(Name, Gadget) :- autobot(Name), gadget(Gadget), usable(Gadget).
resolved(Name) :- valid(Name, Gadget), helper(H), pair(Name, H, Gadget).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("autobot", "Milo"),
        asp.fact("gadget", "garter"),
        asp.fact("gadget", "clip"),
        asp.fact("usable", "garter"),
        asp.fact("usable", "clip"),
        asp.fact("helper", "mechanic"),
        asp.fact("helper", "dispatcher"),
        asp.fact("pair", "Milo", "mechanic", "garter"),
        asp.fact("pair", "Milo", "dispatcher", "clip"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("Milo", "garter"), ("Milo", "clip")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} options).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Python gate / params / generation
# ---------------------------------------------------------------------------
def valid_gadgets() -> list[str]:
    return ["garter", "clip"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set in a bus depot.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gadget", choices=GADGETS)
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
    gadget = args.gadget or rng.choice(valid_gadgets())
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, helper=helper, gadget=gadget)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.helper, params.gadget)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(name="Milo", helper="mechanic", gadget="garter"),
    StoryParams(name="Nina", helper="dispatcher", gadget="clip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name} / {p.helper} / {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
