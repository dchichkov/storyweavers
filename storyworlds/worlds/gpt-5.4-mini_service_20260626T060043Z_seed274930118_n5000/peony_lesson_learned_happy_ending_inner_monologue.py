#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peony_lesson_learned_happy_ending_inner_monologue.py
===============================================================================================================================

A small folk-tale storyworld about a child, a peony, a mistake, and a
gentle lesson learned. The world simulates a simple garden scene with
emotional state, physical state, and a happy ending.

Premise seed:
- A child loves a peony in a little garden.
- The child tries to pick the flower too soon.
- A parent or elder warns them.
- The child reflects in an inner monologue, learns a lesson, and makes amends.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "elder"}
        male = {"boy", "father", "dad", "man", "king", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Garden:
    place: str = "the garden"
    season: str = "spring"
    flower_name: str = "peony"
    flower_color: str = "pink"
    open_bloom: bool = True
    has_path: bool = True


@dataclass
class StoryParams:
    place: str = "garden"
    name: str = "Mila"
    child_type: str = "girl"
    parent_type: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.garden)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _inner_monologue(world: World, child: Entity, flower: Entity) -> str:
    if child.memes.get("regret", 0.0) >= THRESHOLD:
        return (
            f"In {child.pronoun('possessive')} heart, {child.id} thought, "
            f'"I must be gentle with what is beautiful, or I may hurt it."'
        )
    return (
        f"In {child.pronoun('possessive')} heart, {child.id} thought, "
        f'"This flower looks like a little pink sun."'
    )


def _warns(world: World, elder: Entity, child: Entity, flower: Entity) -> None:
    world.say(
        f'"Do not pluck the {flower.label} yet," {elder.pronoun()} said softly. '
        f'"Let it bloom for all to see."'
    )
    child.memes["hesitation"] = child.memes.get("hesitation", 0.0) + 1


def _attempt_pick(world: World, child: Entity, flower: Entity) -> None:
    child.meters["reach"] = child.meters.get("reach", 0.0) + 1
    child.memes["wanting"] = child.memes.get("wanting", 0.0) + 1
    world.say(
        f"{child.id} reached toward the {flower.label}, and for a moment "
        f"{the_flower_phrase(flower)} trembled in the breeze."
    )
    child.memes["guilt"] = child.memes.get("guilt", 0.0) + 1
    child.memes["regret"] = child.memes.get("regret", 0.0) + 1


def _lesson(world: World, child: Entity, elder: Entity, flower: Entity) -> None:
    child.memes["wisdom"] = child.memes.get("wisdom", 0.0) + 1
    child.memes["wanting"] = 0.0
    world.say(_inner_monologue(world, child, flower))
    world.say(
        f"{child.id} bowed {child.pronoun('possessive')} head and said, "
        f'"I understand now. Some lovely things are meant to be admired, not taken."'
    )
    world.say(
        f"{elder.id} smiled, because {child.id} had learned the lesson well."
    )


def _make_amends(world: World, child: Entity, elder: Entity, flower: Entity) -> None:
    child.meters["care"] = child.meters.get("care", 0.0) + 1
    world.say(
        f"{child.id} fetched a little water and a clean ribbon, then tied the ribbon "
        f"near the {flower.label} without touching the petals."
    )
    flower.meters["safe"] = flower.meters.get("safe", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["regret"] = 0.0
    world.say(
        f"After that, the {flower.label} stood bright and happy, and "
        f"{child.id} felt proud of being gentle."
    )


def the_flower_phrase(flower: Entity) -> str:
    return f"the {flower.label}"


def tell(params: StoryParams) -> World:
    garden = Garden()
    world = World(garden)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.child_type,
            traits=["little", params.trait],
            meters={"reach": 0.0, "care": 0.0},
            memes={"wanting": 0.0, "regret": 0.0, "joy": 0.0, "wisdom": 0.0},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=params.parent_type,
            label="the elder",
            meters={"watching": 0.0},
            memes={"calm": 1.0},
        )
    )
    flower = world.add(
        Entity(
            id="Peony",
            kind="thing",
            type="flower",
            label="peony",
            phrase="a round pink peony",
            owner=None,
            caretaker=elder.id,
            meters={"bloom": 1.0, "safe": 0.0},
            memes={"beauty": 1.0},
        )
    )

    world.say(
        f"Once in {garden.place}, there grew a {garden.flower_color} {flower.label} "
        f"as round as a small moon."
    )
    world.say(
        f"{child.id} loved {the_flower_phrase(flower)} and visited it each day "
        f"as if it were a treasure from a fairy king's yard."
    )
    world.say(
        f"{child.id} told {child.pronoun('possessive')} own heart, "
        f'"If I take it home, I can keep its beauty forever."'
    )

    world.para()
    _warns(world, elder, child, flower)
    _attempt_pick(world, child, flower)

    world.para()
    world.say(_inner_monologue(world, child, flower))
    _lesson(world, child, elder, flower)
    _make_amends(world, child, elder, flower)

    world.say(
        f"In the end, the {flower.label} stayed in the garden, and that was the best "
        f"kind of happy ending: the one where beauty remained for tomorrow too."
    )

    world.facts.update(
        child=child,
        elder=elder,
        flower=flower,
        garden=garden,
        lesson_learned=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    flower = f["flower"]
    return [
        f'Write a short folk tale for a child named {child.id} about a {flower.label} and a lesson learned.',
        f'Tell a gentle story where {child.id} wants to pick a {flower.label}, but learns to be patient and kind.',
        f'Write a happy-ending garden story with an inner monologue and the word "peony".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    flower = f["flower"]
    qa = [
        QAItem(
            question=f"What flower did {child.id} love in the garden?",
            answer=f"{child.id} loved a peony that grew in the garden like a little pink moon.",
        ),
        QAItem(
            question=f"What did {child.id} want to do before {elder.label} spoke up?",
            answer=f"{child.id} wanted to pick the peony and take it home, because it looked so beautiful.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=(
                f"{child.id} learned that some beautiful things should be admired where they grow, "
                f"not taken away, and that gentleness can be a kind of bravery."
            ),
        ),
        QAItem(
            question=f"How did the story end for the peony?",
            answer=(
                f"The peony stayed safe in the garden, and {child.id} helped care for it, "
                f"so the ending was happy."
            ),
        ),
    ]
    if world.facts.get("lesson_learned"):
        qa.append(
            QAItem(
                question=f"What was {child.id}'s inner monologue after the mistake?",
                answer=(
                    f"{child.id} thought that the peony was beautiful, but also that it deserved care. "
                    f"Then {child.id} decided to be gentle and make amends."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a peony?",
            answer=(
                "A peony is a flowering plant with big, soft petals. It is often prized for its beauty and scent."
            ),
        ),
        QAItem(
            question="Why should you be gentle with flowers?",
            answer=(
                "Flowers are delicate living things, so gentle hands help keep their petals and stems from being damaged."
            ),
        ),
        QAItem(
            question="What is a lesson learned?",
            answer=(
                "A lesson learned is something a person understands after thinking, trying, or making a mistake."
            ),
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def valid_params() -> list[tuple[str, str]]:
    return [("garden", "peony")]


@dataclass
class ASPEnv:
    place: str
    flower: str


ASP_RULES = r"""
#show valid/2.

valid(P,F) :- setting(P), flower(F), likes_garden(P), peony(F).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "garden"),
        asp.fact("flower", "peony"),
        asp.fact("likes_garden", "garden"),
        asp.fact("peony", "peony"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_params())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_params() ({len(py)} combo).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale of a peony, a lesson learned, and a happy ending.")
    ap.add_argument("--place", choices=["garden"], default=None)
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
    if args.place and args.place != "garden":
        raise StoryError("This world only tells stories in the garden.")
    return StoryParams(
        place="garden",
        name=args.name or rng.choice(["Mila", "Nora", "Lena", "Suri", "Ari"]),
        child_type=args.gender or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(["curious", "gentle", "brave", "dreamy"]),
    )


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combo(s):")
        for place, flower in combos:
            print(f"  {place} {flower}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="garden"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
