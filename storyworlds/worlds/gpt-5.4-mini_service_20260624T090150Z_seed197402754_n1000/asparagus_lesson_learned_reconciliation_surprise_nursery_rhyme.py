#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about asparagus, a surprise, and a lesson learned.

The model is deliberately small:
- a child dislikes asparagus at first,
- a caring cook prepares a gentle surprise,
- the child and helper reconcile,
- the ending proves the child learned something new.

The prose is state-driven, with physical meters and emotional memes guiding what
gets narrated.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    eaten: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    taste: str
    surprise: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def _love_lose_turn(world: World, child: Entity, dish: Dish) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    world.say(
        f"In {world.setting.place}, little {child.id} sat at the table and made a face. "
        f"“No asparagus for me,” {child.pronoun()} said, and {child.pronoun('possessive')} nose went up."
    )
    world.say(
        f"The green spears were {dish.taste}, and {child.id} was sure {dish.it()} would not be nice."
    )


def _prepare_surprise(world: World, parent: Entity, child: Entity, dish: Dish) -> None:
    parent.memes["hope"] = parent.memes.get("hope", 0.0) + 1
    world.say(
        f"{parent.pronoun().capitalize()} smiled in {world.setting.place} and stirred the pan with care."
    )
    world.say(
        f"“Hush now, little one,” {parent.id} sang. “Tonight's asparagus has a {dish.surprise} surprise.”"
    )


def _tension(world: World, child: Entity, dish: Dish) -> None:
    child.memes["stubborn"] = child.memes.get("stubborn", 0.0) + 1
    if child.memes["want"] >= THRESHOLD:
        world.say(
            f"{child.id} crossed {child.pronoun('possessive')} arms, for the smell still seemed strange."
        )


def _reveal(world: World, child: Entity, parent: Entity, dish: Dish) -> None:
    child.meters["curiosity"] = child.meters.get("curiosity", 0.0) + 1
    child.memes["surprised"] = child.memes.get("surprised", 0.0) + 1
    world.say(
        f"Then came a surprise! The asparagus wore a {dish.surprise}, bright and sweet as springtime rain."
    )
    world.say(
        f"{child.id} blinked, then took a tiny bite. It was soft, warm, and far more nice than {child.pronoun('possessive')} thought."
    )


def _reconcile(world: World, child: Entity, parent: Entity, dish: Dish) -> None:
    child.memes["stubborn"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    parent.memes["love"] = parent.memes.get("love", 0.0) + 1
    world.say(
        f"{child.id} smiled at {parent.id} and gave {parent.pronoun('object')} a quick, warm hug."
    )
    world.say(
        f"“I was wrong,” {child.id} said softly. “The surprise made the asparagus nice.”"
    )


def _lesson(world: World, child: Entity, dish: Dish) -> None:
    child.memes["learned"] = child.memes.get("learned", 0.0) + 1
    child.eaten = True
    world.say(
        f"By the end, {child.id} ate the little green spears and asked for one more bite."
    )
    world.say(
        f"The lesson learned was simple: sometimes a funny-looking thing can turn out to be delicious."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"asparagus"}),
}

DISHES = {
    "asparagus": Dish(
        id="asparagus",
        label="asparagus",
        phrase="a plate of asparagus",
        taste="a bit grassy",
        surprise="lemony breadcrumb",
        lesson="sometimes a new food is better than it looks",
        tags={"asparagus", "green", "food"},
    )
}

CHILD_NAMES = ["Milo", "Mina", "Toby", "Tia", "Nora", "Noah"]
PARENT_NAMES = ["Mama", "Papa", "Mom", "Dad", "Auntie", "Uncle"]


@dataclass
class StoryParams:
    place: str
    dish: str
    child_name: str
    child_type: str
    parent_name: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A dish is surprising when it has a surprise topping.
surprising(D) :- dish(D), has_surprise(D).

% A child is ready to reconcile when surprise and tasting both happen.
ready_to_reconcile(C, D) :- child(C), surprising(D), tastes(C, D).

% The lesson is learned when the child eats the dish after reconciling.
learned(C, D) :- ready_to_reconcile(C, D), eats(C, D).

#show surprising/1.
#show ready_to_reconcile/2.
#show learned/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for act in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, act))
    for did, dish in DISHES.items():
        lines.append(asp.fact("dish", did))
        lines.append(asp.fact("has_surprise", did))
        lines.append(asp.fact("lesson", did, dish.lesson))
        for tag in sorted(dish.tags):
            lines.append(asp.fact("tag", did, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show learned/2."))
    atoms = set(asp.atoms(model, "learned"))
    expected = {("c", "asparagus")}
    if atoms == expected:
        print("OK: ASP reasoner matches the Python story shape.")
        return 0
    print("MISMATCH between ASP and Python story shape.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about asparagus and a surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or "kitchen"
    dish = args.dish or "asparagus"
    if place not in SETTINGS or dish not in DISHES:
        raise StoryError("No valid story matches those choices.")
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    parent_name = args.parent or rng.choice(PARENT_NAMES)
    child_type = gender
    return StoryParams(place=place, dish=dish, child_name=child_name, child_type=child_type, parent_name=parent_name)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="mother" if params.parent_name in {"Mama", "Mom", "Auntie"} else "father"))
    dish = DISHES[params.dish]

    world.facts.update(child=child, parent=parent, dish=dish, params=params)

    _love_lose_turn(world, child, dish)
    world.para()
    _prepare_surprise(world, parent, child, dish)
    _tension(world, child, dish)
    world.para()
    _reveal(world, child, parent, dish)
    _reconcile(world, child, parent, dish)
    _lesson(world, child, dish)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    dish: Dish = f["dish"]
    return [
        f'Write a short nursery-rhyme-like story about a child who says no to {dish.label} but learns to try it.',
        f"Tell a gentle story in the kitchen where {params.child_name} meets an asparagus surprise and ends up smiling.",
        f'Write a simple story that includes the word "asparagus" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    dish: Dish = f["dish"]
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"What did {params.child_name} not want to eat at first?",
            answer=f"{params.child_name} did not want to eat asparagus at first.",
        ),
        QAItem(
            question=f"What surprise made the asparagus better for {params.child_name}?",
            answer=f"The asparagus had a {dish.surprise} surprise on it, which made it taste nicer.",
        ),
        QAItem(
            question=f"How did {params.child_name} and {parent.id} feel at the end?",
            answer=f"They felt happy together, and {params.child_name} learned that a new food can be nice when it has a good surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is asparagus?",
            answer="Asparagus is a green vegetable with long, skinny stalks.",
        ),
        QAItem(
            question="Why can a surprise topping help food?",
            answer="A surprise topping can make food taste sweeter, softer, or more interesting, so it feels easier to try.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and feel friendly together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


CURATED = [
    StoryParams(place="kitchen", dish="asparagus", child_name="Mina", child_type="girl", parent_name="Mama"),
    StoryParams(place="kitchen", dish="asparagus", child_name="Toby", child_type="boy", parent_name="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show learned/2."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show learned/2."))
        print(asp.atoms(model, "learned"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
