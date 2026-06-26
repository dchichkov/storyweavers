#!/usr/bin/env python3
"""
storyworlds/worlds/crater_tidal_pool_conflict_surprise_mystery.py
==================================================================

A standalone story world for a small Mystery-style tale set at a tidal pool.

Premise:
- A curious child discovers a strange crater in a tidal pool.
- A careful helper warns about the tide, creating conflict.
- A surprising clue reveals the crater was made by a hidden sea creature or
  drifting object, and the mystery is solved safely.

The world is simulated with typed entities, physical meters, and emotional
memes. The story text is narrated from the changing state, not from a frozen
template.
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
    kind: str = "thing"  # character | thing
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tidal pool"
    tideline: str = "the tide is pulling back"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    surprise: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    clue: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    clue = world.facts["clue_obj"]
    if child.memes.get("discover", 0.0) >= THRESHOLD and clue.meters.get("revealed", 0.0) >= THRESHOLD:
        sig = ("surprise", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
            out.append("__surprise__")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("stubborn", 0.0) < THRESHOLD:
        return []
    if helper.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("conflict", child.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0.0) + 1
    return ["__conflict__"]


CAUSAL_RULES = [_r_conflict, _r_surprise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if s not in {"__conflict__", "__surprise__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the tidal pool", tideline="the tide was slipping low", affords={"search", "observe", "peek"})

CLUES = {
    "shell": Clue(
        id="shell",
        label="a spiral shell",
        reveal="half-buried in the sand",
        surprise="it had been hiding under the crater's shadow",
        cause="a crab had dragged it there",
        tags={"shell", "crab"},
    ),
    "glass": Clue(
        id="glass",
        label="a smooth piece of sea glass",
        reveal="glinting blue at the bottom",
        surprise="it matched a bottle neck near the rocks",
        cause="a wave had rolled it into the crater",
        tags={"glass", "wave"},
    ),
    "crabtrap": Clue(
        id="crabtrap",
        label="an old crab trap bell",
        reveal="tinkling under a net of seaweed",
        surprise="it was tied to a line snared in the pool",
        cause="a fisher had lost it in a storm",
        tags={"crab", "net", "storm"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Ava", "Zoe", "June", "Ivy", "Elsa"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Max", "Owen", "Ben"]
TRAITS = ["curious", "careful", "bold", "quiet", "bright", "thoughtful"]


def valid_clues() -> list[str]:
    return sorted(CLUES)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "tidal_pool"), asp.fact("affords", "tidal_pool", "search"),
             asp.fact("affords", "tidal_pool", "observe"), asp.fact("affords", "tidal_pool", "peek")]
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_clue(C) :- clue(C).
mystery(C) :- valid_clue(C), tagged(C, shell).
mystery(C) :- valid_clue(C), tagged(C, glass).
mystery(C) :- valid_clue(C), tagged(C, crab).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_clues() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_clue/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid_clue")))


def asp_verify() -> int:
    py = set(valid_clues())
    cl = set(asp_valid_clues())
    if py == cl:
        print(f"OK: clingo gate matches valid_clues() ({len(py)} clues).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world set in a tidal pool with a crater and a surprise.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    clue = args.clue or rng.choice(valid_clues())
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def _child_title(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type=params.gender, traits=["little", params.trait, "curious"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=CLUES[params.clue].label, phrase=CLUES[params.clue].label))
    world.facts.update(child=child, helper=helper, clue_obj=clue, clue=CLUES[params.clue], params=params)

    child.memes["curiosity"] = 1
    world.say(f"{params.name} was a little {_child_title(params.gender)} who noticed every odd thing by the tidal pool.")
    world.say(f"{params.name} loved to look closely when {SETTING.tideline}.")
    world.say(f"One day, {params.name} spotted a crater in the wet sand, and it looked too round to be an accident.")
    world.say(f"At the edge of the pool, {params.helper} frowned and said to be careful.")
    world.say(f"{params.name} wanted to search the crater right away, but {params.helper} worried the next wave might rush in.")

    world.say(f"{params.name} stepped closer anyway, because the crater had a secret feel to it.")
    child.memes["stubborn"] = 1
    helper.memes["worry"] = 1
    child.memes["discover"] = 1

    # reveal clue
    clue.meters["revealed"] = 1
    world.say(f"Inside the crater, {CLUES[params.clue].reveal} was {CLUES[params.clue].surprise}.")
    propagate(world, narrate=False)

    world.say(f"That clue showed what made the mark: {CLUES[params.clue].cause}.")
    if child.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f"{params.name} and {params.helper} had argued for a moment, but the new clue made them both quiet.")
    world.say(f"Together they watched the water fill the crater again, and the mystery became a small, safe answer.")
    world.say(f"When they walked home, {params.name} kept the little clue in a pocket and looked back at the shining tidal pool.")

    return world


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    clue = world.facts["clue"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    qa = [
        QAItem(
            question=f"What did {p.name} notice at the tidal pool?",
            answer=f"{p.name} noticed a crater in the wet sand near the tidal pool.",
        ),
        QAItem(
            question=f"Why did {helper.label or 'the helper'} worry when {p.name} wanted to search the crater?",
            answer=f"{helper.label or 'The helper'} worried because the tide could come back and rush over the crater.",
        ),
        QAItem(
            question=f"What clue did {p.name} find in the crater?",
            answer=f"{p.name} found {clue.label}, {clue.reveal}.",
        ),
    ]
    if child.memes.get("conflict", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What caused the conflict in the story?",
                answer=f"The conflict happened because {p.name} wanted to search the crater right away, but {helper.label or 'the helper'} wanted {p.name} to wait for safety.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery ended when the clue showed what made the crater, and {p.name} and {helper.label or 'the helper'} watched the pool fill back in safely.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue = world.facts["clue"]
    out = [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a little pool of seawater left behind when the tide goes out.",
        ),
        QAItem(
            question="What does a crater look like?",
            answer="A crater is a round dip or hole in the ground, often made by something pressing down or hitting it.",
        ),
    ]
    if "shell" in clue.tags:
        out.append(QAItem(question="What is a shell?", answer="A shell is the hard covering that many sea animals, like snails and crabs, live in or carry."))  # noqa: E501
    if "glass" in clue.tags:
        out.append(QAItem(question="What is sea glass?", answer="Sea glass is a smooth piece of broken glass that waves and sand have worn down over time."))
    if "crab" in clue.tags:
        out.append(QAItem(question="What is a crab?", answer="A crab is a sea animal with a hard shell and sideways legs."))  # noqa: E501
    return out


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    clue = world.facts["clue"]
    return [
        'Write a short mystery story for a child set in a tidal pool, and include a crater.',
        f'Write a gentle story where {p.name} sees a strange crater at the tidal pool and finds {clue.label}.',
        f'Write a child-friendly mystery about a tidal pool crater, a worry about the tide, and a surprising clue.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(clue="shell", name="Maya", gender="girl", helper="mother", trait="curious"),
    StoryParams(clue="glass", name="Finn", gender="boy", helper="father", trait="careful"),
    StoryParams(clue="crabtrap", name="Lily", gender="girl", helper="father", trait="bold"),
]


def asp_verify_and_list() -> int:
    py = set(valid_clues())
    cl = set(asp_valid_clues())
    if py != cl:
        return asp_verify()
    print(f"{len(py)} clues are compatible.")
    for c in sorted(py):
        print(f"  {c}")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sys.exit(asp_verify_and_list())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} at the tidal pool"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
