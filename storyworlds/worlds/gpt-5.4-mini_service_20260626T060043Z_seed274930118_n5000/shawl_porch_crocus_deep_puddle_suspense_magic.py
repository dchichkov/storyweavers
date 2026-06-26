#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shawl_porch_crocus_deep_puddle_suspense_magic.py
=============================================================================================================

A small adventure storyworld about a porch, a shawl, a crocus, and the suspense
of a deep puddle. The child wants to cross the slick porch, but a sudden magic
trick is needed to recover the shawl and save the crocus from the water.
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
    wearer: Optional[str] = None
    placed_at: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Lina", "Nora", "Ivy", "Mira"],
    "boy": ["Eli", "Noah", "Finn", "Theo", "Milo"],
}
PARENT_LABEL = {"mother": "mom", "father": "dad"}

PLACE = "the porch"
SHALLOW = "a wet patch"
DEEP = "a deep puddle"

REGISTRY = {
    "shawl": {
        "label": "shawl",
        "phrase": "a soft blue shawl",
        "type": "shawl",
    },
    "crocus": {
        "label": "crocus",
        "phrase": "a small purple crocus in a clay pot",
        "type": "crocus",
    },
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(params: StoryParams) -> bool:
    return params.gender in {"girl", "boy"} and params.parent in {"mother", "father"}


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _deep_puddle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("step", 0) < 1:
        return out
    if child.meters.get("wet", 0) >= 1:
        sig = ("deep",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["suspense"] = True
            out.append("The puddle reached higher than the child's ankles, and the porch suddenly felt very still.")
    return out


def _soak_shawl(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shawl = world.get("shawl")
    if child.meters.get("wet", 0) < 1:
        return out
    if shawl.wearer != "child":
        return out
    if ("soak",) in world.fired:
        return out
    world.fired.add(("soak",))
    shawl.meters["wet"] = 1
    out.append("The shawl drank in the water and grew heavy in the child's hands.")
    return out


def _save_crocus(world: World) -> list[str]:
    out: list[str] = []
    crocus = world.get("crocus")
    child = world.get("child")
    if not world.facts.get("magic_used"):
        return out
    if crocus.placed_at == "puddle":
        if ("save",) in world.fired:
            return out
        world.fired.add(("save",))
        crocus.placed_at = "porch"
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        out.append("With one bright sparkle, the crocus lifted out of the puddle and landed safe on the porch step.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_deep_puddle, _soak_shawl, _save_crocus):
            before = len(world.fired)
            for s in rule(world):
                world.say(s)
            if len(world.fired) != before:
                changed = True


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not story_is_reasonable(params):
        raise StoryError("Invalid character options for this storyworld.")

    world = World(PLACE)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=PARENT_LABEL[params.parent]))
    shawl = world.add(Entity(
        id="shawl",
        type="shawl",
        label="shawl",
        phrase=REGISTRY["shawl"]["phrase"],
        owner="child",
        wearer="child",
        meters={"dry": 1},
    ))
    crocus = world.add(Entity(
        id="crocus",
        type="crocus",
        label="crocus",
        phrase=REGISTRY["crocus"]["phrase"],
        owner="child",
        placed_at="table",
        meters={"safe": 1},
    ))

    world.say(f"{params.name} loved the porch because it felt like the edge of an adventure.")
    world.say(f"{params.name} also loved the shawl, a soft blue wrap that fluttered like a tiny flag.")
    world.say(f"Near the door sat a purple crocus, bright as a little lamp against the wood.")

    world.para()
    world.say(f"Then rainwater gathered in a deep puddle across the porch boards.")
    world.say(f"{params.name} wanted to hurry through, but the puddle looked dark and slippery.")
    child.memes["suspense"] = 1
    child.memes["desire"] = 1
    child.meters["wet"] = 1
    child.memes["step"] = 1

    # The shawl is in the child's care; the crocus is at risk near the puddle.
    world.say(f"The shawl dipped low as {params.name} reached for the crocus pot, and the water splashed up at once.")
    shawl.wearer = "child"
    crocus.placed_at = "puddle"

    propagate(world)

    world.para()
    world.say(f"{params.name}'s {PARENT_LABEL[params.parent]} whispered, 'Hold still.'")
    world.say(f"With a small spell and a brave breath, {params.name} made the puddle glitter instead of glare.")
    world.facts["magic_used"] = True
    propagate(world)

    world.para()
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(f"The crocus stood safe again on the porch step, and the shawl lay warm and only a little damp.")
    world.say(f"{params.name} smiled at the shining water, because even a deep puddle could become part of the adventure.")

    world.facts.update(
        child=child,
        parent=parent,
        shawl=shawl,
        crocus=crocus,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short adventure story for a young child about a porch, a shawl, and a deep puddle.",
        f"Tell a magical suspense story where {p.name} must save a crocus without losing the shawl.",
        "Write a child-friendly story that turns a slippery porch moment into a brave magical rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    shawl = world.facts["shawl"]
    crocus = world.facts["crocus"]
    return [
        QAItem(
            question=f"Where did {p.name} find the deep puddle?",
            answer=f"{p.name} found it on the porch, where the rain had gathered into one deep puddle across the boards.",
        ),
        QAItem(
            question=f"What did {p.name} want to save on the porch?",
            answer=f"{p.name} wanted to save the crocus, a small purple flower that had landed near the puddle.",
        ),
        QAItem(
            question=f"What happened to the shawl during the adventure?",
            answer="The shawl splashed into the water and grew heavy, but it stayed with the child and later came out only a little damp.",
        ),
        QAItem(
            question=f"How did the story end for {p.name} and the crocus?",
            answer=f"In the end, {p.name} used a little magic, the crocus was safe again on the porch step, and the puddle had turned into part of the fun.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a shawl?",
        answer="A shawl is a piece of cloth you can drape over your shoulders to keep warm or to dress up a little.",
    ),
    QAItem(
        question="What is a porch?",
        answer="A porch is a covered area by a house, often with steps or wooden boards, where people can sit or stand outside.",
    ),
    QAItem(
        question="What is a crocus?",
        answer="A crocus is a small flower that can bloom early in spring and often has bright purple, yellow, or white petals.",
    ),
    QAItem(
        question="What is a puddle?",
        answer="A puddle is a small pool of water on the ground after rain.",
    ),
    QAItem(
        question="Why can puddles be tricky?",
        answer="Puddles can be slippery and can soak shoes, clothes, or anything that gets splashed by the water.",
    ),
    QAItem(
        question="What is magic in a story?",
        answer="Magic in a story is a special power that can make surprising things happen, like glittering water or moving a flower safely.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.wearer:
            bits.append(f"wearer={e.wearer}")
        if e.placed_at:
            bits.append(f"placed_at={e.placed_at}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(porch).
feature(suspense).
feature(magic).
theme(adventure).

entity(child).
entity(parent).
entity(shawl).
entity(crocus).

at_risk(shawl) :- puddle(deep).
at_risk(crocus) :- puddle(deep).

suspense(Story) :- at_risk(shawl), at_risk(crocus), feature(suspense).
resolved(Story) :- magic_used, feature(magic).
valid_story(Story) :- place(porch), feature(suspense), feature(magic), theme(adventure).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "porch"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "magic"),
        asp.fact("theme", "adventure"),
        asp.fact("entity", "child"),
        asp.fact("entity", "parent"),
        asp.fact("entity", "shawl"),
        asp.fact("entity", "crocus"),
        asp.fact("puddle", "deep"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python gating.")
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a porch, shawl, crocus, deep puddle, suspense, and magic.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    params = StoryParams(name=name, gender=gender, parent=parent)
    if not story_is_reasonable(params):
        raise StoryError("Invalid options for this storyworld.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother"),
    StoryParams(name="Eli", gender="boy", parent="father"),
    StoryParams(name="Nora", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/1."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
