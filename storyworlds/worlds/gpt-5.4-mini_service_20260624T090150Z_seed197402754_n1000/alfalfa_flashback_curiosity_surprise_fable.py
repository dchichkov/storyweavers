#!/usr/bin/env python3
"""
A tiny fable world about curiosity in an alfalfa patch, with a flashback turn
and a surprise ending.

The seed prompt suggests a classical, child-friendly fable tone: a small animal,
a tempting patch of alfalfa, a remembered lesson, and a surprise that changes
the path forward. The simulation keeps the world small and stateful: hunger,
curiosity, caution, and trust all move as the story unfolds.
"""

from __future__ import annotations

import argparse
import copy
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "bunny"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox", "wolf", "crow"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Field:
    place: str = "the meadow"
    affords: set[str] = field(default_factory=lambda: {"browse", "sniff", "hide"})


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    sweetness: str
    scent: str
    favored_by: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    animal: str
    food: str
    seed: Optional[int] = None


class World:
    def __init__(self, field_: Field) -> None:
        self.field = field_
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.timeline: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.timeline.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.field)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_hunger(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters.get("hunger", 0.0) >= THRESHOLD and ("hunger", e.id) not in world.fired:
            world.fired.add(("hunger", e.id))
            e.memes["restless"] = e.memes.get("restless", 0.0) + 1
            out.append(f"{e.id}'s belly rumbled a little louder.")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    rabbit = next((e for e in world.entities.values() if e.type == "rabbit"), None)
    food = next((e for e in world.entities.values() if e.kind == "thing" and e.type == "food"), None)
    if not rabbit or not food:
        return out
    if rabbit.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.facts.get("surprise_seen"):
        return out
    world.facts["surprise_seen"] = True
    rabbit.memes["surprise"] = rabbit.memes.get("surprise", 0.0) + 1
    out.append(f"{rabbit.id} found not one patch, but two: the alfalfa was growing beside a hidden clover bed.")
    return out


CAUSAL_RULES = [_r_hunger, _r_surprise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reaction(world: World, hero: Entity, food: Food) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["curiosity"] = h.memes.get("curiosity", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "surprised": bool(sim.facts.get("surprise_seen")),
        "hunger": h.meters.get("hunger", 0.0),
    }


def introduce(world: World, hero: Entity, food: Food) -> None:
    world.say(f"Long ago, in {world.field.place}, there lived a small {hero.type} named {hero.id}.")
    world.say(f"{hero.id} loved the sweet smell of {food.label}, and {food.phrase} always made {hero.pronoun()} hopeful.")


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1
    world.say(
        f"One morning, {hero.id} remembered how an older friend had once followed a scent too quickly "
        f"and startled a sleeping nest. That memory made {hero.id} pause."
    )


def curious_move(world: World, hero: Entity, food: Food) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["hunger"] = hero.meters.get("hunger", 0.0) + 1
    world.say(
        f"Still, {hero.id} tiptoed closer, because curiosity is a little lantern that can light even a quiet field."
    )
    world.say(f"{hero.pronoun().capitalize()} sniffed the air and crept toward the alfalfa.")
    propagate(world, narrate=True)


def surprise_turn(world: World, hero: Entity, food: Food) -> None:
    if world.facts.get("surprise_seen"):
        world.say(
            f"Then the grass parted, and a second green patch appeared beside the alfalfa, "
            f"full of clover and tiny bees humming kindly."
        )


def resolve(world: World, hero: Entity, food: Food) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0.0) - 1)
    world.say(
        f"{hero.id} smiled, chose the safer path, and shared a little of the clover with the bees' shadowed flowers."
    )
    world.say(
        f"By the end, {hero.id} had learned that a wise pause can turn curiosity into a happy surprise."
    )


def tell(place: str, animal: str, food_id: str) -> World:
    field_ = FIELD_REGISTRY[place]
    food_def = FOOD_REGISTRY[food_id]
    world = World(field_)
    hero = world.add(Entity(id="Mina", kind="character", type=animal))
    food = world.add(Entity(id="food", type="food", label=food_def.label, phrase=food_def.phrase))
    world.facts.update(hero=hero, food=food, food_def=food_def, place=place)

    introduce(world, hero, food)
    world.para()
    flashback(world, hero)
    curious_move(world, hero, food)
    world.para()
    surprise_turn(world, hero, food)
    resolve(world, hero, food)
    world.facts["hero"] = hero
    return world


FIELD_REGISTRY = {
    "meadow": Field(place="the meadow"),
    "garden": Field(place="the garden"),
    "hill": Field(place="the sunny hill"),
}

FOOD_REGISTRY = {
    "alfalfa": Food(
        id="alfalfa",
        label="alfalfa",
        phrase="a patch of tender alfalfa leaves",
        sweetness="soft",
        scent="fresh",
        favored_by={"rabbit", "hare", "bunny"},
    ),
    "clover": Food(
        id="clover",
        label="clover",
        phrase="a patch of clover leaves",
        sweetness="mild",
        scent="green",
        favored_by={"rabbit", "hare", "bunny"},
    ),
}

ANIMALS = ["rabbit", "hare", "bunny"]


@dataclass
class Registry:
    fields: dict[str, Field]
    foods: dict[str, Food]


REGISTRY = Registry(fields=FIELD_REGISTRY, foods=FOOD_REGISTRY)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in FIELD_REGISTRY:
        for animal in ANIMALS:
            for food_id, food in FOOD_REGISTRY.items():
                if animal in food.favored_by:
                    out.append((place, animal, food_id))
    return out


KNOWLEDGE = {
    "alfalfa": [
        (
            "What is alfalfa?",
            "Alfalfa is a leafy plant that grows in patches and is often eaten by rabbits and other small animals.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something that happened earlier, so the reader understands the choice better.",
        )
    ],
    "curiosity": [
        (
            "What does curiosity mean?",
            "Curiosity means wanting to learn or discover something new by looking, asking, or exploring carefully.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something unexpected that suddenly appears or happens.",
        )
    ],
}

ASP_RULES = r"""
favored(A, F) :- animal(A), food(F), likes(A, F).
valid(P, A, F) :- place(P), animal(A), food(F), favored(A, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in FIELD_REGISTRY:
        lines.append(asp.fact("place", place))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for food_id, food in FOOD_REGISTRY.items():
        lines.append(asp.fact("food", food_id))
        for a in sorted(food.favored_by):
            lines.append(asp.fact("likes", a, food_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    food_def = f["food_def"]
    return [
        f'Write a short fable for a young child about curiosity, a flashback, and {food_def.label}.',
        f"Tell a gentle story where a {hero.type} remembers an old lesson, grows curious, and discovers a surprise near {food_def.label}.",
        f'Write a simple fable that includes "{food_def.label}" and ends with a wise choice after a surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    food_def = world.facts["food_def"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about Mina, a little {hero.type}, who lives in {world.field.place} and loves {food_def.label}.",
        ),
        QAItem(
            question=f"What did Mina remember in the flashback?",
            answer="Mina remembered that following a scent too fast can startle a sleeping nest, so she chose to pause first.",
        ),
        QAItem(
            question=f"What surprise did Mina find near the alfalfa?",
            answer="Mina found that the alfalfa grew beside a hidden clover bed, so the field had more good things than she first expected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag, pairs in KNOWLEDGE.items():
        if tag == "alfalfa":
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
        if tag == "flashback":
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
        if tag == "curiosity":
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
        if tag == "surprise":
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", animal="rabbit", food="alfalfa"),
    StoryParams(place="garden", animal="hare", food="alfalfa"),
    StoryParams(place="hill", animal="bunny", food="alfalfa"),
]


def explain_rejection(place: str, animal: str, food: str) -> str:
    return f"(No story: a {animal} in {place} does not naturally match {food} in this little fable world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about alfalfa, curiosity, flashback, and surprise.")
    ap.add_argument("--place", choices=FIELD_REGISTRY)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--food", choices=FOOD_REGISTRY)
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
    if args.place and args.animal and args.food:
        if (args.place, args.animal, args.food) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.animal, args.food))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.animal is None or c[1] == args.animal)
              and (args.food is None or c[2] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, animal, food = rng.choice(sorted(combos))
    return StoryParams(place=place, animal=animal, food=food)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.animal, params.food)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, animal, food) combos:\n")
        for place, animal, food in combos:
            print(f"  {place:8} {animal:6} {food:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
