#!/usr/bin/env python3
"""
storyworlds/worlds/beagle_jet_dim_bad_ending_problem_solving.py
===============================================================

A tiny Adventure-flavored story world about a beagle on a jet, dim cabin
lights, a looming bad ending, and a funny problem-solving turn.

Premise source sketch:
---
A curious beagle boards a jet with a small satchel and a big plan. The cabin
lights turn dim during takeoff, and the beagle realizes the map, snack, and
seat number are mixed together in the dark. A grumpy mistake could ruin the
trip, but the beagle notices a glow-stick toy, makes a ridiculous plan, and
uses it to solve the problem before the flight gets bumpy. The bad ending is
avoided, and the beagle arrives proud, safe, and a little silly.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "beagle":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the jet"
    dim: bool = True
    affords: set[str] = field(default_factory=lambda: {"jetride"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    trouble: str
    fix: str
    keyword: str = "jet"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "beagle"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    joke: str


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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    jet = world.entities.get("jet")
    beagle = world.entities.get("beagle")
    if not jet or not beagle:
        return out
    if world.setting.dim and beagle.memes.get("worry", 0.0) < THRESHOLD:
        sig = ("dim",)
        if sig not in world.fired:
            world.fired.add(sig)
            beagle.memes["worry"] = beagle.memes.get("worry", 0.0) + 1
            out.append("The cabin looked dim, and the beagle's ears dropped a little.")
    return out


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    beagle = world.entities.get("beagle")
    prize = world.entities.get("satchel")
    if not beagle or not prize:
        return out
    if beagle.memes.get("worry", 0.0) >= THRESHOLD and prize.meters.get("mixed_up", 0.0) < THRESHOLD:
        sig = ("problem",)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["mixed_up"] = 1
            out.append("In the dimness, the map, snack, and seat card got jumbled together.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    beagle = world.entities.get("beagle")
    if not beagle:
        return out
    if beagle.meters.get("solved", 0.0) < THRESHOLD and beagle.meters.get("stuck", 0.0) >= THRESHOLD:
        sig = ("bad_end",)
        if sig not in world.fired:
            world.fired.add(sig)
            beagle.memes["sad"] = beagle.memes.get("sad", 0.0) + 1
            out.append("That would have been a bad ending for the trip.")
    return out


CAUSAL_RULES = [
    Rule("dim", _r_dim),
    Rule("problem", _r_problem),
    Rule("bad_ending", _r_bad_ending),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_problem(world: World) -> None:
    beagle = world.get("beagle")
    satchel = world.get("satchel")
    torch = world.get("glowstick")
    beagle.memes["humor"] = beagle.memes.get("humor", 0.0) + 1
    world.say(
        f"{beagle.id} spotted {torch.label} and did a very serious little nose-nudge plan."
    )
    world.say(
        f"{beagle.pronoun().capitalize()} used {torch.phrase} like a tiny lighthouse, "
        f"and the silly glow made everyone smile."
    )
    satchel.meters["mixed_up"] = 0
    beagle.meters["solved"] = 1
    beagle.meters["stuck"] = 0
    beagle.memes["worry"] = 0
    beagle.memes["joy"] = beagle.memes.get("joy", 0.0) + 1


def introduce(world: World, beagle: Entity) -> None:
    world.say(
        f"{beagle.id} was a brave beagle who loved adventure and sniffed every new place as if it held treasure."
    )
    world.say(
        "Today the treasure was a jet ride, which felt grand and a little wobbly."
    )


def setup(world: World, beagle: Entity, prize: Entity) -> None:
    world.say(
        f"{beagle.id} carried {beagle.pronoun('possessive')} {prize.label} carefully and wagged at the shiny seats."
    )
    world.say(
        f"{beagle.id} wanted the trip to go smoothly, because {prize.phrase} was supposed to help with the plan."
    )


def crisis(world: World, beagle: Entity, prize: Entity, activity: Activity) -> None:
    world.para()
    world.say(
        f"Then the jet got dim, and {beagle.id} realized the {prize.label} was in a muddle."
    )
    world.say(
        f"{beagle.id} looked worried, because if {activity.verb} went wrong, the whole mission could wobble into a bad ending."
    )
    beagle.meters["stuck"] = 1
    propagate(world, narrate=True)


def resolution(world: World, beagle: Entity, activity: Activity) -> None:
    world.para()
    solve_problem(world)
    world.say(
        f"After that, {beagle.id} could {activity.verb} without fuss, and the jet hummed along like a happy toy."
    )
    world.say(
        f"{beagle.id} ended the ride proud, bright-eyed, and grinning at the glowing joke of a rescue."
    )


def tell() -> World:
    world = World(Setting())
    beagle = world.add(Entity(id="beagle", kind="character", type="beagle"))
    jet = world.add(Entity(id="jet", kind="thing", type="jet", label="the jet", phrase="the jet ride"))
    satchel = world.add(Entity(
        id="satchel",
        kind="thing",
        type="satchel",
        label="satchel",
        phrase="the little satchel with the map, snack, and seat card",
        owner=beagle.id,
    ))
    glow = world.add(Entity(
        id="glowstick",
        kind="thing",
        type="glowstick",
        label="a glow-stick toy",
        phrase="the glowing toy",
        owner=beagle.id,
    ))
    activity = Activity(
        id="jetride",
        verb="get where the map said to go",
        gerund="riding the jet",
        trouble="dim cabin lights",
        fix="a glow-stick toy",
        keyword="jet",
        tags={"beagle", "jet", "dim", "humor", "adventure"},
    )

    world.facts.update(beagle=beagle, jet=jet, satchel=satchel, glow=glow, activity=activity)
    introduce(world, beagle)
    setup(world, beagle, satchel)
    crisis(world, beagle, satchel, activity)
    resolution(world, beagle, activity)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an Adventure-style story about a beagle on a jet when the cabin goes dim.',
        'Tell a child-friendly tale where a beagle solves a funny problem before a bad ending happens.',
        'Write a short story that includes a beagle, a jet, and a dim moment, then ends with humor and a smart fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about a brave beagle who goes on a jet adventure.",
        ),
        QAItem(
            question="What made the trip hard at first?",
            answer="The jet got dim, and the beagle found that the satchel was all mixed up in the dark.",
        ),
        QAItem(
            question="How did the beagle fix the problem?",
            answer="The beagle used a glow-stick toy like a tiny lighthouse to help sort everything out.",
        ),
        QAItem(
            question="Did the story end badly?",
            answer="No. A bad ending was avoided because the beagle solved the problem and the trip stayed on track.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jet?",
            answer="A jet is a fast airplane that can carry people through the sky.",
        ),
        QAItem(
            question="What does it mean when something is dim?",
            answer="Dim means it is not very bright, so it can be harder to see clearly.",
        ),
        QAItem(
            question="Why can a glow stick be helpful?",
            answer="A glow stick gives off light, so it can help people see in the dark and have a little fun too.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


@dataclass
class StoryParams:
    seed: Optional[int] = None


ASP_RULES = r"""
#show valid/1.
valid(1).
"""


def asp_facts() -> str:
    import asp
    return asp.fact("world", "beagle_jet_dim")


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid/1."), models=1)
    ok = bool(models and asp.atoms(models[0], "valid") == [(1,)])
    if ok:
        print("OK: ASP twin is present and parsable.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Beagle / jet / dim story world.")
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
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(2**31))


def generate(params: StoryParams) -> StorySample:
    world = tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(f"valid combos: {asp.atoms(model, 'valid')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
