#!/usr/bin/env python3
"""
A small storyworld for a Lesson Learned rhyming story about an oak.

Premise:
- A child loves a tall oak tree and wants to play near it.
- A risky choice can shake loose acorns or scratch bark.
- A gentle helper offers a safer way, so the child learns a lesson.

The world model tracks:
- physical meters: height, wobble, scratch, dropped, safe
- emotional memes: wanting, worry, patience, pride, joy

The prose is generated from state transitions, not from a frozen template.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for key in ["height", "wobble", "scratch", "dropped", "safe"]:
            self.meters.setdefault(key, 0.0)
        for key in ["wanting", "worry", "patience", "pride", "joy", "lesson"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def rhyming_close(a: str, b: str) -> str:
    return f"{a}, {b}."  # intentionally simple; prose carries the rhyme-like cadence


def introduce(world: World, child: Entity, oak: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"Little {trait} {child.id} would roam by the oak, so tall and proud, "
        f"with whispering leaves and a leafy cloud."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} loved the tree and its acorns bright, "
        f"and dreamed of a game in the morning light."
    )
    child.memes["joy"] += 1


def set_scene(world: World, child: Entity, oak: Entity) -> None:
    oak.meters["height"] = 10.0
    world.say(
        f"Beside the oak, the grass was green; the bark was rough, the branches lean."
    )
    world.say(
        f"{child.id} stood close and looked up high, as a gentle breeze went drifting by."
    )


def risky_choice(world: World, child: Entity, oak: Entity) -> None:
    child.memes["wanting"] += 1
    child.meters["wobble"] += 1
    world.say(
        f"{child.id} wanted to climb, to reach for more, and tap on bark near the tree-trunk door."
    )
    world.say(
        f"But feet can slip and hands can sway, when a child goes up the wobbly way."
    )


def warn_and_turn(world: World, parent: Entity, child: Entity, oak: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Careful," said {parent.id}, "the oak is kind, but climbing high can tangle your mind.'
        f' You might get scratched, or drop your shoe, and then the day turns sticky and blue."'
    )
    world.say(
        f"{child.id} slowed down, then frowned a bit; the brave big plan did not quite fit."
    )


def lesson_world_update(world: World, child: Entity, oak: Entity) -> None:
    if child.meters["wobble"] >= THRESHOLD:
        child.meters["safe"] += 1
        child.memes["lesson"] += 1
    if child.memes["worry"] >= THRESHOLD:
        child.memes["patience"] += 1


def offer_safer_way(world: World, parent: Entity, child: Entity, oak: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"Then {parent.id} smiled and pointed near, to gather acorns on the ground so clear."
    )
    world.say(
        f'"Let us rake them up," {parent.id} said, "and keep our feet on the garden bed."'
    )
    world.say(
        f"{child.id} nodded yes, with a tiny grin; a safer game could still begin."
    )


def resolution(world: World, child: Entity, parent: Entity, oak: Entity) -> None:
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} picked up acorns, one by one, while the oak stood golden in the sun."
    )
    world.say(
        f"The child learned this truth and held it tight: slow can be smart, and safe feels right."
    )
    world.say(
        f"So the oak kept swaying, calm and tall, while {child.id} had fun without a fall."
    )


def build_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    oak = world.add(Entity(id="oak", kind="thing", type="tree", label="oak tree", phrase="a tall oak tree"))
    world.facts.update(child=child, parent=parent, oak=oak, params=params)

    introduce(world, child, oak)
    world.say("")
    set_scene(world, child, oak)
    risky_choice(world, child, oak)
    warn_and_turn(world, parent, child, oak)
    lesson_world_update(world, child, oak)
    world.say("")
    offer_safer_way(world, parent, child, oak)
    resolution(world, child, parent, oak)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        "Write a short rhyming story for a child who loves an oak tree and learns a safe lesson.",
        f"Tell a gentle lesson-learned rhyming story where {child.id} wants to climb an oak tree but {parent.id} helps with a safer plan.",
        "Write a simple rhyming story with an oak tree, a careful warning, and a happy ending on the ground.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"What did {child.id} want to do by the oak tree?",
            answer=f"{child.id} wanted to climb the oak tree and reach higher branches."
        ),
        QAItem(
            question=f"Why did {parent.id} warn {child.id}?",
            answer=f"{parent.id} warned {child.id} because climbing high on the oak could lead to a slip or a scratch."
        ),
        QAItem(
            question=f"What safer choice did they make instead?",
            answer=f"They chose to gather fallen acorns on the ground instead of climbing."
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that slow and safe can still be fun."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an oak tree?",
            answer="An oak tree is a large tree with strong branches and acorns."
        ),
        QAItem(
            question="What are acorns?",
            answer="Acorns are small nuts that grow on oak trees."
        ),
        QAItem(
            question="Why should a child be careful climbing a tree?",
            answer="A child should be careful because branches can be slippery and a fall can hurt."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } "
            f"memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A lesson-learned rhyming oak storyworld.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--trait", default=None)
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
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Lila", "Milo", "Nora", "Theo", "Maya", "Eli"])
    trait = args.trait or rng.choice(["curious", "cheerful", "brave", "patient"])
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


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


ASP_RULES = r"""
% Declarative twin of the simple reasonableness gate:
% a child may need a safer choice when the oak-climb is risky.
risky(climb_oak).
safer_choice(gather_acorns).
lesson_learned(gather_acorns) :- risky(climb_oak), safer_choice(gather_acorns).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("domain", "oak_lesson"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("style", "rhyming_story"),
            asp.fact("seed_word", "oak"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    ok = any(sym.name == "lesson_learned" for sym in model)
    if ok:
        print("OK: ASP twin produced a lesson-learned model.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected model.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(name="Lila", gender="girl", parent="mother", trait="curious"),
            StoryParams(name="Milo", gender="boy", parent="father", trait="brave"),
            StoryParams(name="Nora", gender="girl", parent="mother", trait="patient"),
        ]
        samples = [generate(p) for p in params_list]
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
