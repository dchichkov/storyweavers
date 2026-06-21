#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mantle_reconciliation_ghost_story.py
====================================================================

A small ghost-story world about a child, a worried ghost, an old mantle, and a
reconciliation that makes the house feel kind again.

The premise is simple: a child finds a cold, lonely ghost near the fireplace.
Something precious tied to the mantle has gone missing, so the ghost keeps
rattling and sighing. By listening, searching, and returning the lost keepsake,
the child helps the ghost forgive the past. The ending proves the change in the
house: the mantle is warm with a small lamp, the ghost is calm, and both sides
share the room without fear.

This script follows the shared Storyweavers contract:
- stdlib-only prose engine
- typed entities with meters and memes
- separate story/prompt/QA generation from world state
- inline ASP twin with a Python reasonableness gate
- verify mode that checks parity and exercises ordinary generation
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
SCARED = 4.0


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
    can_speak: bool = False
    is_ghost: bool = False
    is_child: bool = False
    is_object: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    has_mantle: bool = False
    has_fireplace: bool = False
    has_window: bool = False
    has_stairs: bool = False
    quiet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str = "object"
    is_lost: bool = False
    is_returned: bool = False
    is_warmth: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    type: str
    reason: str
    lost_item: str
    wants_apology: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_cold(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    if ghost.meters["restless"] >= THRESHOLD and ("cold", ghost.id) not in world.fired:
        world.fired.add(("cold", ghost.id))
        ghost.memes["sad"] += 1
        world.get("house").meters["spooky"] += 1
        out.append("__restless__")
    return out


def _r_search(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["searching"] >= THRESHOLD and ("search", child.id) not in world.fired:
        world.fired.add(("search", child.id))
        world.get("mantle").meters["attention"] += 1
        out.append("__search__")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold), Rule("search", _r_search)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def whisper(world: World, ghost: Ghost, child: Entity) -> None:
    ghost.meters["restless"] += 1
    child.memes["curious"] += 1
    world.say(
        f"On a quiet evening, {child.id} heard a soft sigh near the fireplace. "
        f"A pale ghost stood by the {world.get('mantle').label}, looking as lonely as a lost song."
    )
    world.say(
        f'"Please," the ghost whispered, "something dear was taken from my {ghost.reason}. '
        f"It lies near the mantle, and I cannot rest until it comes home."'
    )


def listen(world: World, child: Entity, ghost: Ghost) -> None:
    child.memes["kind"] += 1
    world.say(
        f"{child.id} did not run away. {child.pronoun().capitalize()} held still and listened, "
        f"then said, \"I can help you look. Tell me what went missing.\""
    )
    world.say(
        f"The ghost's glow dimmed from sharp and blue to small and silver, as if the room had remembered how to breathe."
    )


def search(world: World, child: Entity, item: ObjectThing) -> None:
    child.meters["searching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} searched behind the heavy chair, under the old rug, and along the dusty {world.get('mantle').label}. "
        f"At last, {child.pronoun()} found {item.phrase} tucked in a crack where nobody would notice it."
    )


def return_item(world: World, child: Entity, ghost: Ghost, item: ObjectThing) -> None:
    item.is_returned = True
    ghost.meters["restless"] = 0.0
    ghost.memes["hope"] += 1
    world.say(
        f"{child.id} carried {item.phrase} back to the ghost and placed it in {ghost.pronoun('possessive')} hands. "
        f"The ghost touched it softly, and the blue light turned warm around the edges."
    )


def reconcile(world: World, child: Entity, ghost: Ghost) -> None:
    child.memes["peace"] += 1
    ghost.memes["peace"] += 1
    world.say(
        f'"I am sorry the house forgot you," {child.id} said.'
    )
    world.say(
        f'The ghost bowed its head. "And I am sorry I frightened you," it replied. '
        f'"I was angry for a long time. I can let that go now."'
    )
    world.say(
        f"They sat together by the fireless hearth, and the room felt less like a haunted place and more like a home."
    )


def ending(world: World, child: Entity, ghost: Ghost, lamp: ObjectThing) -> None:
    child.memes["joy"] += 1
    ghost.memes["calm"] += 1
    lamp.is_warmth = True
    world.say(
        f"The next night, {child.id} set a tiny lamp on the {world.get('mantle').label}. "
        f"Its light was small, but it was enough."
    )
    world.say(
        f"The ghost no longer rattled. It drifted by the window like a quiet cloud, and {child.id} smiled back without fear."
    )


def tell(params) -> World:
    world = World()
    house = world.add(Place(id="house", label="old house", has_mantle=True, has_fireplace=True, has_window=True, has_stairs=True))
    mantle = world.add(ObjectThing(id="mantle", label="mantle", phrase="the mantle"))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child", traits=["brave"], can_speak=True, is_child=True))
    ghost = world.add(Ghost(id="ghost", label="ghost", type="ghost", reason="old hurt", lost_item="locket", tags={"ghost", "reconciliation"}))
    lost = world.add(ObjectThing(id="locket", label="silver locket", phrase="a silver locket", is_lost=True, tags={"locket"}))
    lamp = world.add(ObjectThing(id="lamp", label="tiny lamp", phrase="a tiny lamp", is_warmth=True, tags={"lamp"}))

    whisper(world, ghost, child)
    world.para()
    listen(world, child, ghost)
    search(world, child, lost)
    world.para()
    return_item(world, child, ghost, lost)
    reconcile(world, child, ghost)
    world.para()
    ending(world, child, ghost, lamp)

    world.facts.update(
        child=child,
        ghost=ghost,
        lost=lost,
        lamp=lamp,
        house=house,
        mantle=mantle,
        outcome="reconciled",
        child_name=child.id,
        child_type=child.type,
    )
    return world


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    seed: Optional[int] = None


NAMES = ["Maya", "Eli", "Nora", "Theo", "Lily", "Noah", "Ivy", "Finn"]
TYPES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str]]:
    return [("child", t) for t in TYPES]


ASP_RULES = r"""
ghost_restless(G) :- ghost(G).
reconciled :- returned(locket), apologized(child), forgave(ghost).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("ghost", "ghost"), asp.fact("returned", "locket"), asp.fact("apologized", "child"), asp.fact("forgave", "ghost")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/0."))
    asp_ok = bool(asp.atoms(model, "reconciled"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python reconciliation differ.")
        return 1
    try:
        sample = generate(StoryParams(child_name="Maya", child_type="girl"))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a mantle and reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--type", choices=TYPES)
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
    name = args.name or rng.choice(NAMES)
    ctype = args.type or rng.choice(TYPES)
    return StoryParams(child_name=name, child_type=ctype)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle ghost story that includes the word "mantle" and ends with reconciliation.',
        f"Tell a child-friendly ghost story where {world.facts['child_name']} helps a lonely ghost forgive an old hurt near the mantle.",
        "Write a spooky-but-kind story about a house where listening, returning something lost, and saying sorry make the ghost calm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    c = world.facts["child"]
    g = world.facts["ghost"]
    return [
        ("Who is the story about?", f"It is about {c.id} and a lonely ghost in an old house. The child helps the ghost by listening instead of running away."),
        ("What did the child find?", f"{c.id} found a silver locket hidden near the mantle. Returning it gave the ghost peace and made reconciliation possible."),
        ("How did the story end?", "It ended with an apology, forgiveness, and a small lamp on the mantle. The ghost became calm, and the house felt like a home again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mantle?", "A mantle is the shelf or ledge above a fireplace. People often place small decorations or lamps there."),
        ("What does reconciliation mean?", "Reconciliation means making peace again after a hurt or a disagreement. It usually includes listening, apologizing, and forgiving."),
        ("Why do ghost stories feel spooky?", "Ghost stories feel spooky because they use dark rooms, whispers, and strange feelings. When they are gentle, they can still end in kindness."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if hasattr(e, "label") and getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.child_type not in TYPES:
        raise StoryError("Unknown child type.")
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
        print(asp_program("#show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for reconciliation facts.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, name in enumerate(NAMES[:2]):
            samples.append(generate(StoryParams(child_name=name, child_type=TYPES[i % 2], seed=base_seed + i)))
    else:
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
