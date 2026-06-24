#!/usr/bin/env python3
"""
A small superhero story world about a child hero, a chance to transform, and a
shared rescue. The seed words are woven into the premise: insulator, chance,
and dame. The world is intentionally tiny and classical: one hero, one helper,
one problem, one transformation, one share, one happy ending.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    state: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "dame", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str = "Bright Harbor"
    danger: str = "a crackling tower"
    place: str = "the rooftop"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    problem: str
    object_name: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Pip", "Milo", "Luna", "Tess", "Rex", "Ivy"]
HELPER_NAMES = ["Dame Bella", "Dame Mina", "Aunt Jo", "Captain Blue"]
PROBLEMS = {
    "storm": "the storm lights in the tower",
    "bridge": "the broken bridge over the river",
    "cat": "a tiny cat on a high ledge",
}
OBJECTS = {
    "insulator": {
        "label": "insulator",
        "phrase": "a shiny insulator suit",
    }
}


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        other = World(self.city)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "state": v.state,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _do_transformation(world: World, hero: Entity) -> None:
    if "transformed" in world.fired:
        return
    world.fired.add("transformed")
    hero.state = "transformed"
    hero.meters["power"] = hero.meters.get("power", 0.0) + 1.0
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1.0
    world.say(
        f"Then {hero.id} took a deep breath and changed into {hero.pronoun()} "
        f"brave superhero form."
    )


def _do_sharing(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    if "shared" in world.fired:
        return
    world.fired.add("shared")
    obj.owner = helper.id
    hero.memes["kind"] = hero.memes.get("kind", 0.0) + 1.0
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1.0
    world.say(
        f"{hero.id} shared {hero.pronoun('possessive')} {obj.label} with {helper.id}, "
        f"and {helper.id} smiled because the plan worked better together."
    )


def tell(params: StoryParams) -> World:
    world = World(City())
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="young hero",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="dame",
    ))
    obj = world.add(Entity(
        id=params.object_name,
        kind="thing",
        type="insulator",
        label="insulator",
        phrase="a shiny insulator suit",
        owner=hero.id,
    ))

    hero.memes["hope"] = 1.0
    helper.memes["care"] = 1.0
    obj.meters["charge"] = 1.0

    world.say(
        f"In {world.city.name}, {hero.id} was a little hero who kept {hero.pronoun('possessive')} "
        f"{obj.label} close, because it made {hero.pronoun('object')} feel ready for any rescue."
    )
    world.say(
        f"One day, {hero.id} got a chance to help with {PROBLEMS[params.problem]}. "
        f"The dame, {helper.id}, called, \"We need a steady hand up there!\""
    )

    world.para()
    world.say(
        f"{hero.id} looked at the high {world.city.place} and wondered if {hero.pronoun('subject')} "
        f"was brave enough."
    )
    world.say(
        f"Then {hero.id} remembered the insulator suit and the chance to be useful, not just fast."
    )
    _do_transformation(world, hero)

    world.say(
        f"With {hero.pronoun('possessive')} new superhero strength, {hero.id} climbed safely and fixed the problem."
    )
    world.say(
        f"But the best part was not the fixing alone. It was how {hero.id} reached back and shared the good news, "
        f"then shared the last spark-proof tool too."
    )
    _do_sharing(world, hero, helper, obj)

    world.para()
    world.say(
        f"At sunset, {world.city.name} shone again. {helper.id} thanked {hero.id}, and {hero.id} grinned "
        f"because {hero.pronoun('subject')} had become a true superhero by helping and sharing."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        city=world.city,
        transformed=hero.state == "transformed",
        shared=True,
        problem=params.problem,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: Entity = f["obj"]
    return [
        f'Write a short superhero story for a child about {hero.id}, an insulator suit, and a chance to help.',
        f"Tell a gentle superhero tale where {hero.id} transforms, {helper.id} the dame asks for help, and they share {obj.label}.",
        f'Write a simple story that includes the words "insulator", "chance", and "dame" and ends with sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: Entity = f["obj"]
    return [
        QAItem(
            question=f"Who got the chance to be a superhero in the story?",
            answer=f"{hero.id} got the chance to help in {world.city.name} and became a superhero in the story.",
        ),
        QAItem(
            question=f"What did {hero.id} wear that helped {hero.pronoun('object')} feel ready?",
            answer=f"{hero.id} kept {hero.pronoun('possessive')} {obj.label} close. It was a shiny insulator suit.",
        ),
        QAItem(
            question=f"Who asked for help in the story?",
            answer=f"The dame, {helper.id}, asked for help when the tower needed fixing.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end that showed kindness?",
            answer=f"{hero.id} shared {hero.pronoun('possessive')} {obj.label} and the good news with {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insulator?",
            answer="An insulator is something that helps keep electricity from moving where it should not go.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, solves problems, and tries to keep others safe.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use or enjoy something too.",
        ),
        QAItem(
            question="What is a chance?",
            answer="A chance is an opportunity to try something or to do something helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.state:
            bits.append(f"state={e.state}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryRegistry:
    hero_names: list[str] = field(default_factory=lambda: HERO_NAMES[:])
    helper_names: list[str] = field(default_factory=lambda: HELPER_NAMES[:])
    problems: list[str] = field(default_factory=lambda: list(PROBLEMS.keys()))


REGISTRY = StoryRegistry()


ASP_RULES = r"""
hero(X) :- chosen_hero(X).
helper(X) :- chosen_helper(X).
object(O) :- chosen_object(O).

transforms(H) :- hero(H), chance(H), not blocked(H).
shares(H,O) :- transforms(H), object(O), helper(_).

valid_story(H,He,O) :- hero(H), helper(He), object(O), chance(H), transforms(H), shares(H,O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for h in REGISTRY.hero_names:
        lines.append(asp.fact("chosen_hero", h))
    for h in REGISTRY.helper_names:
        lines.append(asp.fact("chosen_helper", h))
    lines.append(asp.fact("chosen_object", "insulator"))
    lines.append(asp.fact("chance", "Nova"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("Nova", REGISTRY.helper_names[0], "insulator")}
    if asp_set == py_set:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
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
    hero_name = args.name or rng.choice(REGISTRY.hero_names)
    helper_name = args.helper or rng.choice(REGISTRY.helper_names)
    problem = args.problem or rng.choice(REGISTRY.problems)
    if hero_name == helper_name:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero_name,
        hero_type="hero",
        helper_name=helper_name,
        helper_type="dame",
        problem=problem,
        object_name="insulator",
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2 ** 31))
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "hero", "Dame Bella", "dame", "storm", "insulator"),
            StoryParams("Ivy", "hero", "Dame Mina", "dame", "bridge", "insulator"),
            StoryParams("Pip", "hero", "Aunt Jo", "dame", "cat", "insulator"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 20):
            if len(samples) >= max(args.n, 1):
                break
            try:
                p = resolve_params(args, random.Random(rng.randrange(2 ** 31) + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(p)
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
