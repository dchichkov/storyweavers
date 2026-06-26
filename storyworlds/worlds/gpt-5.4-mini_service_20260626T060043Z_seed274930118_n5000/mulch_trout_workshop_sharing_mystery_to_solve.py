#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mulch_trout_workshop_sharing_mystery_to_solve.py
===============================================================================================================

A small fairy-tale story world set in a workshop, built from the seed words
"mulch" and "trout". The story pattern centers on Sharing, a Mystery to Solve,
and Foreshadowing.

Premise:
- In a cozy workshop, a young maker prepares a little garden craft for a trout-
  themed pond lantern.
- A missing basket of mulch threatens the plan.
- Clues in the room foreshadow who or what moved it.

Turn:
- The maker notices a trail, asks for help, and shares tools and guesses.
- A friend remembers where the mulch was last seen.

Resolution:
- They find the mulch, share it fairly, and finish the trout craft together.

The world model tracks:
- physical meters: carried, hidden, prepared, shared
- emotional memes: curiosity, worry, trust, delight

The story is not a frozen paragraph; state changes drive the prose.
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("carried", "hidden", "prepared", "shared", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "trust", "delight", "helpfulness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "maid", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "knight", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        import copy
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


def _r_find(world: World) -> list[str]:
    out = []
    mulch = world.get("mulch")
    if mulch.meters["hidden"] >= THRESHOLD and world.facts.get("clue_seen"):
        if "find_mulch" in world.fired:
            return []
        world.fired.add("find_mulch")
        mulch.meters["found"] += 1
        mulch.meters["hidden"] = 0.0
        out.append("The hidden mulch was found at last.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    mulch = world.get("mulch")
    if mulch.meters["found"] < THRESHOLD:
        return []
    if mulch.meters["shared"] >= THRESHOLD:
        return []
    if "share_mulch" in world.fired:
        return []
    world.fired.add("share_mulch")
    mulch.meters["shared"] += 1
    mulch.shared_with.update({"maker", "friend"})
    out.append("They shared the mulch in two neat little heaps.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_find, _r_share):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str = "Poppy"
    friend: str = "Bram"
    place: str = "the workshop"
    seed: Optional[int] = None


NAMES = ["Poppy", "Mina", "Elsie", "Anya", "Iris", "Ruby"]
FRIENDS = ["Bram", "Tobin", "Clover", "Nell", "Moss", "Wren"]


def foreshadow(world: World, maker: Entity) -> None:
    maker.memes["curiosity"] += 1
    world.say(
        f"Long before the lantern was finished, {maker.id} noticed a little trail of crumbs "
        f"and twigs near the bench."
    )
    world.say("The trail did not say where it led, but it made the room feel full of a secret.")
    world.facts["clue_seen"] = True


def setup(world: World, params: StoryParams) -> None:
    maker = world.add(Entity(id="maker", kind="character", type="girl", label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="boy", label=params.friend))
    mulch = world.add(Entity(
        id="mulch",
        type="mulch",
        label="mulch",
        phrase="a small basket of soft brown mulch",
        owner=maker.id,
    ))
    trout = world.add(Entity(
        id="trout",
        type="trout",
        label="trout",
        phrase="a painted trout ornament",
        owner=maker.id,
    ))
    world.facts.update(maker=maker, friend=friend, mulch=mulch, trout=trout, place=world.place)


def opening(world: World) -> None:
    maker: Entity = world.facts["maker"]
    trout: Entity = world.facts["trout"]
    world.say(
        f"Once in {world.place}, there lived a little maker named {maker.label}. "
        f"{maker.pronoun().capitalize()} loved bright, gentle things and fairy-tale tasks."
    )
    world.say(
        f"On the shelf beside {maker.pronoun('possessive')} bench sat a painted {trout.label}, "
        f"waiting to become part of a tiny garden wonder."
    )
    trout.meters["prepared"] += 1
    maker.memes["delight"] += 1


def mystery(world: World) -> None:
    maker: Entity = world.facts["maker"]
    friend: Entity = world.facts["friend"]
    mulch: Entity = world.facts["mulch"]
    maker.memes["worry"] += 1
    world.say(
        f"But when {maker.label} reached for the basket of mulch, it was gone."
    )
    world.say(
        f"{maker.pronoun().capitalize()} looked under cloth, behind tools, and beside the kettle, "
        f"and even {friend.label} came to help search."
    )
    world.say(
        f"Still, the mulch did not appear, and the missing basket made a careful mystery."
    )
    mulch.meters["hidden"] = 1.0
    propagate(world, narrate=True)


def sharing_turn(world: World) -> None:
    maker: Entity = world.facts["maker"]
    friend: Entity = world.facts["friend"]
    mulch: Entity = world.facts["mulch"]
    maker.memes["curiosity"] += 1
    friend.memes["helpfulness"] += 1
    world.say(
        f"{friend.label} remembered seeing the basket near the window, where the warm light made the dust dance."
    )
    world.say(
        f"{maker.label} did not keep the search secret; {maker.pronoun()} shared the clue, "
        f"and {friend.label} shared {friend.pronoun('possessive')} guess."
    )
    world.say(
        f"Together they lifted the wicker tray, and there, tucked safely beneath it, was the mulch."
    )
    world.facts["clue_seen"] = True
    propagate(world, narrate=True)
    if mulch.meters["shared"] >= THRESHOLD:
        maker.memes["trust"] += 1
        friend.memes["trust"] += 1


def ending(world: World) -> None:
    maker: Entity = world.facts["maker"]
    friend: Entity = world.facts["friend"]
    mulch: Entity = world.facts["mulch"]
    trout: Entity = world.facts["trout"]
    maker.memes["delight"] += 1
    friend.memes["delight"] += 1
    world.say(
        f"At last, they sprinkled the mulch around the little trout ornament and set it into the finished tray."
    )
    world.say(
        f"{maker.label} smiled because the mystery was solved, the mulch was shared, and the workshop felt warm as a storybook hearth."
    )
    world.say(
        f"{friend.label} smiled too, for the trout shone brightly, and the basket of mulch now belonged to their shared little creation."
    )
    world.facts["ended"] = True


def tell(params: StoryParams) -> World:
    world = World(place="the workshop")
    setup(world, params)
    opening(world)
    world.para()
    foreshadow(world, world.facts["maker"])
    mystery(world)
    world.para()
    sharing_turn(world)
    ending(world)
    return world


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mulch?",
            answer="Mulch is a layer of plant bits or bark spread on soil to help keep it covered and neat.",
        ),
        QAItem(
            question="What is a trout?",
            answer="A trout is a kind of fish that lives in fresh water like rivers and streams.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something together with you.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early on about something important that will matter later.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem where the answer is hidden at first, so the characters must look for clues.",
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    maker: Entity = world.facts["maker"]
    friend: Entity = world.facts["friend"]
    mulch: Entity = world.facts["mulch"]
    trout: Entity = world.facts["trout"]
    return [
        QAItem(
            question=f"Who was the little maker in the workshop story?",
            answer=f"The little maker was {maker.label}, who worked in the workshop with a friend named {friend.label}.",
        ),
        QAItem(
            question="What was missing from the workshop?",
            answer=f"The basket of mulch was missing, which made the search into a mystery to solve.",
        ),
        QAItem(
            question="How did the characters solve the problem?",
            answer="They followed a clue, searched together, found the mulch, and shared it for the finished craft.",
        ),
        QAItem(
            question="What did the trout have to do with the ending?",
            answer=f"The painted trout became part of the finished little garden piece after the mulch was found and shared.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    maker: Entity = world.facts["maker"]
    return [
        'Write a short fairy-tale story set in a workshop about a missing basket of mulch and a painted trout.',
        f"Tell a gentle story where {maker.label} and a friend solve a mystery by sharing clues and working together.",
        "Write a child-friendly story with foreshadowing, a missing object, and a warm ending image.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.shared_with:
            parts.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A missing mulch basket is a mystery when it is hidden and the clue has been seen.
mystery(M) :- item(M), hidden(M), clue_seen.

% If the missing item is found, it can be shared.
shareable(M) :- item(M), found(M).

% Sharing happens only after the item is found.
shared(M) :- shareable(M), found(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "workshop"))
    lines.append(asp.fact("item", "mulch"))
    lines.append(asp.fact("item", "trout"))
    lines.append(asp.fact("hidden", "mulch"))
    lines.append(asp.fact("clue_seen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show mystery/1.\n#show shared/1."))
    mystery_atoms = set(asp.atoms(model, "mystery"))
    shared_atoms = set(asp.atoms(model, "shared"))
    ok = ("mulch",) in mystery_atoms and ("mulch",) not in shared_atoms
    if ok:
        print("OK: ASP gate behaves as expected.")
        return 0
    print("MISMATCH in ASP verification.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale workshop story world with mulch, trout, sharing, mystery, and foreshadowing.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if friend == name:
        friend = rng.choice([f for f in FRIENDS if f != name])
    return StoryParams(name=name, friend=friend, place="the workshop", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show mystery/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Poppy", friend="Bram", place="the workshop", seed=base_seed),
            StoryParams(name="Mina", friend="Wren", place="the workshop", seed=base_seed + 1),
            StoryParams(name="Elsie", friend="Clover", place="the workshop", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            i += 1
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
