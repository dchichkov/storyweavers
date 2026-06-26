#!/usr/bin/env python3
"""
A standalone storyworld for a fairy-tale reading nook:
- setting: a reading nook
- features: kindness, happy ending
- seed words: stride, convenient
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

ASP_RULES = r"""
% A reading nook story is reasonable when a little problem can be solved kindly.
kind_story(S) :- setting(S), has_kindness(S), has_happy_ending(S).
useful_help(H) :- help(H), convenient(H).
good_turn(S) :- kind_story(S), helpful_choice(S).
"""

PLACE = "reading nook"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    visitor: str
    object: str
    help_kind: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A child needs a name for the story.")
    if params.help_kind not in {"book", "lamp", "blanket", "stool"}:
        raise StoryError("The helpful item must be something gentle and fitting for a reading nook.")
    if params.object not in {"page", "book", "ribbon", "cup"}:
        raise StoryError("The scene needs a small storybook object, not a wild or dangerous one.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "reading_nook"),
        asp.fact("has_kindness", "reading_nook"),
        asp.fact("has_happy_ending", "reading_nook"),
        asp.fact("help", "book"),
        asp.fact("help", "lamp"),
        asp.fact("help", "blanket"),
        asp.fact("help", "stool"),
        asp.fact("convenient", "book"),
        asp.fact("convenient", "lamp"),
        asp.fact("convenient", "blanket"),
        asp.fact("convenient", "stool"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_help_choices() -> list[str]:
    return ["book", "lamp", "blanket", "stool"]


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(["Mina", "Nora", "Liam", "Eli", "Luna", "Ivy"]),
        visitor=rng.choice(["little fox", "tiny owl", "small mouse", "young rabbit"]),
        object=rng.choice(["book", "page", "ribbon", "cup"]),
        help_kind=rng.choice(valid_help_choices()),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale reading nook storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--visitor")
    ap.add_argument("--object")
    ap.add_argument("--help-kind", choices=valid_help_choices())
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.visitor:
        params.visitor = args.visitor
    if args.object:
        params.object = args.object
    if args.help_kind:
        params.help_kind = args.help_kind
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    visitor = world.add(Entity(id="visitor", kind="character", label=params.visitor))
    object_ent = world.add(Entity(id="object", kind="thing", label=params.object))
    helper = world.add(Entity(id="helper", kind="thing", label=params.help_kind))
    world.facts.update(
        hero=hero,
        visitor=visitor,
        object=object_ent,
        helper=helper,
        place=PLACE,
        kindness=True,
        happy_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    visitor = world.get("visitor")
    object_ent = world.get("object")
    helper = world.get("helper")

    hero.bump_meme("kindness")
    visitor.bump_meme("hope")

    world.say(
        f"Once in the cozy reading nook, {hero.label} sat by a shelf of bright tales, "
        f"and a {visitor.label} came in with a quiet, curious look."
    )
    world.say(
        f"{visitor.label.capitalize()} wanted to reach the {object_ent.label}, "
        f"but the little room was high and the path was not convenient."
    )
    world.para()
    hero.bump_meme("care")
    helper.bump_meter("use", 1)
    world.say(
        f"Then {hero.label} made a kind plan. With a gentle stride, {hero.label} moved "
        f"to the {helper.label} and brought it over."
    )
    world.say(
        f"That made the corner convenient at last, so {visitor.label} could reach the "
        f"{object_ent.label} without any fuss."
    )
    world.para()
    visitor.bump_meme("joy")
    hero.bump_meme("joy")
    world.say(
        f"The two friends smiled, and the reading nook grew warm with kindness. "
        f"In the end, they shared the {object_ent.label}, listened to the story, "
        f"and the whole little place felt like a happy ending."
    )
    world.facts["stride"] = True
    world.facts["convenient"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    visitor = f["visitor"].label
    helper = f["helper"].label
    return [
        f'Write a fairy-tale story set in a reading nook where {hero} helps {visitor} with kindness.',
        f"Tell a gentle story that uses the words stride and convenient and ends happily.",
        f"Write a child-friendly story about a reading nook, a small problem, and a kind solution with {helper}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    visitor = f["visitor"].label
    helper = f["helper"].label
    obj = f["object"].label
    return [
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place in the reading nook, a cozy little place for calm stories and kind help.",
        ),
        QAItem(
            question=f"Who helped make things convenient for {visitor}?",
            answer=f"{hero} helped by bringing the {helper}, which made the little problem easy to solve.",
        ),
        QAItem(
            question=f"What did the friends share at the end?",
            answer=f"They shared the {obj} and enjoyed the story together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone cares about others and chooses to help in a gentle way.",
        ),
        QAItem(
            question="What does convenient mean?",
            answer="Convenient means easy to use or close by, so something can be done without much trouble.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the worry gets solved and the story finishes in a good, warm way.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


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


def asp_verify() -> int:
    import asp

    program = asp_program("#show kind_story/1.\n#show useful_help/1.\n#show good_turn/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(arg.name if arg.type != 1 else arg.string for arg in sym.arguments)) for sym in model)
    expected = {
        ("kind_story", ("reading_nook",)),
        ("useful_help", ("book",)),
        ("useful_help", ("lamp",)),
        ("useful_help", ("blanket",)),
        ("useful_help", ("stool",)),
        ("good_turn", ("reading_nook",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_turn/1."))
    return sorted(set(asp.atoms(model, "good_turn")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
    StoryParams(name="Mina", visitor="little fox", object="book", help_kind="lamp"),
    StoryParams(name="Nora", visitor="tiny owl", object="page", help_kind="stool"),
    StoryParams(name="Liam", visitor="small mouse", object="ribbon", help_kind="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_turn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible reading nook stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
