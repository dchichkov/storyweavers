#!/usr/bin/env python3
"""
A standalone story world for a tiny mystery with humor:
a quail, a little suspense, and something ginger.

The premise:
- A child and a caretaker notice a missing ginger snack.
- A nervous quail keeps peeking out of a hedge.
- The search creates suspense, but the answer is gentle and funny.

The world model:
- Physical meters track hiding, crumbs, and carried items.
- Emotional memes track worry, curiosity, relief, and amusement.
- The story is generated from state changes, not from a frozen template.

This file follows the Storyweavers world contract.
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


THRESHOLD = 1.0


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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    smell: str
    color: str
    hidden_spot: str
    makes_humor: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _story_beat_search(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("suspense", 0.0) < THRESHOLD:
            continue
        if ("search", e.id) in world.fired:
            continue
        world.fired.add(("search", e.id))
        e.memes["curiosity"] = e.memes.get("curiosity", 0.0) + 1
        out.append(f"{e.label} started to look everywhere.")
    return out


def _story_beat_find(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if not clue:
        return out
    if clue.hidden_in and not world.facts.get("found"):
        for e in world.characters():
            if e.memes.get("curiosity", 0.0) < THRESHOLD:
                continue
            if ("find", e.id) in world.fired:
                continue
            world.fired.add(("find", e.id))
            world.facts["found"] = True
            e.memes["relief"] = e.memes.get("relief", 0.0) + 1
            e.memes["amusement"] = e.memes.get("amusement", 0.0) + 1
            out.append(f"Then they spotted the missing ginger treat in an odd little hiding spot.")
    return out


def _story_beat_quail_hop(world: World) -> list[str]:
    out: list[str] = []
    quail = world.entities.get("quail")
    if not quail or world.facts.get("found_by_quail"):
        return out
    if quail.hidden_in and quail.memes.get("nervous", 0.0) >= THRESHOLD:
        world.facts["found_by_quail"] = True
        quail.memes["relief"] = quail.memes.get("relief", 0.0) + 1
        out.append("A small quail hopped out, as if it had been practicing a surprise entrance.")
    return out


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_story_beat_search, _story_beat_quail_hop, _story_beat_find):
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    for line in out:
        world.say(line)
    return out


def build_world() -> World:
    place = Place(label="the garden", indoors=False, affords={"search", "hide", "peek"})
    world = World(place)

    child = world.add(Entity(
        id="Mina", kind="character", type="girl", label="Mina",
        meters={"feet": 1.0}, memes={"suspense": 1.0, "curiosity": 1.0}
    ))
    adult = world.add(Entity(
        id="Papa", kind="character", type="father", label="Papa",
        meters={}, memes={"worry": 1.0}
    ))
    quail = world.add(Entity(
        id="quail", kind="character", type="bird", label="a tiny quail",
        meters={"hops": 1.0}, memes={"nervous": 1.0, "humor": 1.0}, hidden_in="hedge"
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type="snack", label="ginger biscuit",
        phrase="a ginger biscuit in a red tin", hidden_in="flowerpot"
    ))

    world.facts.update(
        child=child,
        adult=adult,
        quail=quail,
        clue=clue,
        place=place,
    )
    return world


def tell(world: World) -> None:
    child = world.get("Mina")
    adult = world.get("Papa")
    quail = world.get("quail")
    clue = world.get("clue")

    world.say(
        f"Mina and Papa were in {world.place.label}, where a missing ginger biscuit had turned the afternoon into a puzzle."
    )
    world.say(
        f"Mina felt suspense in her chest and kept looking at the hedge, because something small there seemed to be trying very hard not to be noticed."
    )

    world.para()
    child.memes["suspense"] = 1.0
    adult.memes["worry"] = 1.0
    quail.memes["nervous"] = 1.0
    propagate(world)

    world.say(
        f"Papa lifted the red tin lid, but the tin was empty, which only made the mystery feel funnier and more serious at the same time."
    )
    world.say(
        f"Then Mina noticed a trail of tiny crumbs near a flowerpot, and the crumbs smelled warm and gingery."
    )

    world.para()
    clue.hidden_in = None
    world.facts["found"] = False
    propagate(world)

    world.say(
        f"The answer turned out to be a shy little quail, who had pecked at the ginger biscuit and then hidden in the hedge like an overdramatic detective."
    )
    world.say(
        f"Mina laughed, Papa laughed, and even the quail looked less nervous once everyone knew the secret."
    )

    world.para()
    world.say(
        f"In the end, the garden was calm again, the red tin was found, and the tiniest investigator in the hedge had become the day's funniest clue."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short mystery story for a child about a missing ginger snack and a nervous quail.",
        "Tell a funny, suspenseful garden story where crumbs lead to a gentle surprise.",
        "Write a simple story that includes a quail, suspense, and ginger, and ends with laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    quail = world.facts["quail"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"The story was about {child.label}, {adult.label}, a tiny quail, and a missing ginger biscuit."
        ),
        QAItem(
            question="What made Mina feel suspenseful?",
            answer="Mina felt suspenseful because a ginger treat had gone missing and the hedge looked like it was hiding a secret."
        ),
        QAItem(
            question="What was the surprising answer to the mystery?",
            answer=f"The surprising answer was that {quail.label} had found the ginger biscuit first and then hid in the hedge."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with everyone laughing, because the mystery was solved and the quail turned out to be a funny little clue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quail?",
            answer="A quail is a small bird that can move quickly and hide in plants."
        ),
        QAItem(
            question="What does ginger smell like?",
            answer="Ginger has a warm, spicy smell that can make snacks taste lively and a little sharp."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling that something important is about to be discovered."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        out.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    out.append(f"  facts={world.facts}")
    return "\n".join(out)


ASP_RULES = r"""
% A simple declarative twin for the tiny mystery.
% A clue is suspenseful if it is hidden and the observer is curious.
suspenseful(C) :- clue(C), hidden(C), curious(observer).

% The mystery is solved when the ginger clue is found.
solved :- clue(C), ginger(C), found(C).

% Humor appears when the quail is the unexpected source of the clue.
funny :- quail(Q), found_by(Q), ginger(C), found(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("observer", "mina"),
        asp.fact("curious", "observer"),
        asp.fact("quail", "q1"),
        asp.fact("clue", "c1"),
        asp.fact("ginger", "c1"),
        asp.fact("hidden", "c1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0. #show funny/0. #show suspenseful/1."))
    shown = {(sym.name, len(sym.arguments)) for sym in model}
    need = {("solved", 0), ("funny", 0), ("suspenseful", 1)}
    if shown == need:
        print("OK: ASP twin is internally consistent.")
        return 0
    print("MISMATCH in ASP twin.")
    print("shown:", sorted(shown))
    return 1


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    parent: str = "Papa"
    place: str = "garden"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a quail and ginger.")
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
    return StoryParams(seed=args.seed, name=rng.choice(["Mina", "Nia", "Lena", "Mabel"]), parent="Papa", place="garden")


def generate(params: StoryParams) -> StorySample:
    world = build_world()
    tell(world)
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
        print(asp_program("#show solved/0. #show funny/0. #show suspenseful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0. #show funny/0. #show suspenseful/1."))
        print(sorted((sym.name, [arg.name if hasattr(arg, "name") else getattr(arg, "string", None) for arg in sym.arguments]) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(StoryParams(seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
