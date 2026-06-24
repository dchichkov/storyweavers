#!/usr/bin/env python3
"""
A small fable-like story world set in a science corner, built around paints,
christening, witnessing, and a surprising turn.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SCIENCE_CORNER = "the science corner"


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = SCIENCE_CORNER


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    canvas = world.get("canvas")
    paints = world.get("paints")
    if paints.meters.get("shaken", 0) >= 1 and "spill" not in world.fired:
        world.fired.add("spill")
        canvas.meters["stained"] = canvas.meters.get("stained", 0) + 1
        paints.meters["lost"] = paints.meters.get("lost", 0) + 1
        out.append("A bright splash jumped onto the paper and left a new mark.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    canvas = world.get("canvas")
    if canvas.meters.get("stained", 0) >= 1 and "surprise" not in world.fired:
        world.fired.add("surprise")
        world.get("child").memes["wonder"] = world.get("child").memes.get("wonder", 0) + 1
        out.append("The blotch was not a mistake at all; it made a smiling star appear.")
    return out


RULES = [Rule("spill", _r_spill), Rule("surprise", _r_surprise)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    paints = world.add(Entity(id="paints", type="paints", label="paints", plural=True))
    canvas = world.add(Entity(id="canvas", type="paper", label="paper", caretaker=parent.id))

    world.say(f"In {SCIENCE_CORNER}, {params.name} was a little {params.gender} who loved making careful pictures.")
    world.say(f"{params.name}'s {params.parent} kept a small tray of paints beside the jars and stones.")
    world.say(f"{params.name} wanted to christen the new paper with a first brave color.")
    world.para()
    world.say(f"At first, the colors trembled in the cups, and {params.name} watched them like a tiny witness.")
    paints.meters["shaken"] = 1
    propagate(world)
    world.para()
    world.say(f"{params.name} paused, then smiled at the surprise.")
    world.say("“Sometimes a small accident can tell a kinder story,” said the parent.")
    world.say(f"So {params.name} painted around the shining star, and the paper became a picture worth keeping.")
    world.facts.update(child=child, parent=parent, paints=paints, canvas=canvas)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a short fable set in {SCIENCE_CORNER} about {child.label} and some paints.",
        f"Tell a gentle story where a child wants to christen a page with paints and then witnesses a surprise.",
        "Write a child-friendly fable with a science corner, paints, witness, christen, and surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"].label
    return [
        QAItem(
            question=f"Where did {child} make the picture?",
            answer=f"{child} made the picture in {SCIENCE_CORNER}, beside the science tools and jars.",
        ),
        QAItem(
            question=f"What did {child} want to do with the new paper?",
            answer=f"{child} wanted to christen the new paper with the first color from the paints.",
        ),
        QAItem(
            question="What surprising thing did the blotch turn into?",
            answer="The blotch turned into a smiling star, so the mistake became part of the picture.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are paints for?",
            answer="Paints are for making colors and pictures on paper, cloth, wood, or other surfaces.",
        ),
        QAItem(
            question="What does it mean to christen something?",
            answer="To christen something is to give it a first special use or a first new beginning.",
        ),
        QAItem(
            question="What does it mean to witness something?",
            answer="To witness something means to see it happen with your own eyes.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "science_corner"),
        asp.fact("object", "paints"),
        asp.fact("object", "canvas"),
        asp.fact("verb", "christen"),
        asp.fact("verb", "witness"),
        asp.fact("feature", "surprise"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
uses_science_corner :- setting(science_corner).
story_ready :- object(paints), verb(christen), verb(witness), feature(surprise), uses_science_corner.
#show story_ready/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ready/0."))
    ok = any(sym.name == "story_ready" for sym in model)
    if ok:
        print("OK: ASP rules accept the science-corner paints/christen/witness/surprise world.")
        return 0
    print("MISMATCH: ASP rules did not derive story_ready.")
    return 1


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like science-corner story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn"]
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(name_pool)
    return StoryParams(name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show story_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ready/0."))
        print("story_ready" if any(sym.name == "story_ready" for sym in model) else "no story_ready")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i in range(3):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        for i in range(max(args.n, 1)):
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
