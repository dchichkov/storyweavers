#!/usr/bin/env python3
"""
A small slice-of-life storyworld about an island child, a hobby, teamwork,
curiosity, and repetition.

The seed image is a gentle, everyday tale:
a child on an island loves a hobby, keeps practicing, gets curious about a
problem, and learns to work with someone else to finish something lovely.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Person:
    name: str
    role: str  # child, grandparent, friend
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"progress": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "curiosity": 0.0, "teamwork": 0.0})

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Place:
    island: str = "the island"
    spot: str = "the breezy porch"
    features: list[str] = field(default_factory=lambda: ["tide pools", "shell paths", "little boats"])


@dataclass
class Hobby:
    id: str
    name: str
    repeated_verb: str
    finished_object: str
    tool: str
    small_problem: str
    fix_method: str
    tag: str
    question_seed: str


@dataclass
class World:
    place: Place
    hero: Person
    helper: Person
    hobby: Hobby
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "lagoon": Place(island="the island", spot="the lagoon porch", features=["tide pools", "blue water", "quiet boats"]),
    "harbor": Place(island="the island", spot="the harbor bench", features=["nets", "shells", "rope rails"]),
    "village": Place(island="the island", spot="the village steps", features=["chalk paths", "flower pots", "fish crates"]),
}

HOBBIES = {
    "shell_stringing": Hobby(
        id="shell_stringing",
        name="stringing shell necklaces",
        repeated_verb="thread the shells one by one",
        finished_object="a bright shell necklace",
        tool="a length of soft string",
        small_problem="one shell kept slipping away",
        fix_method="hold the string steady together",
        tag="shells",
        question_seed="shell",
    ),
    "kite_patching": Hobby(
        id="kite_patching",
        name="patching a kite",
        repeated_verb="smooth the paper again and again",
        finished_object="a patched kite",
        tool="sticky tape and careful fingers",
        small_problem="a corner of the kite kept lifting",
        fix_method="press the paper down together",
        tag="kite",
        question_seed="kite",
    ),
    "driftwood_sorting": Hobby(
        id="driftwood_sorting",
        name="sorting driftwood into little shapes",
        repeated_verb="try different pieces until they fit",
        finished_object="a tiny driftwood boat",
        tool="a basket and a string marker",
        small_problem="the boat pieces would not line up",
        fix_method="compare the pieces side by side",
        tag="wood",
        question_seed="wood",
    ),
}

NAMES = ["Mina", "Tari", "Lena", "Owen", "Nico", "Sana", "Ari", "Koa"]
TRAITS = ["patient", "curious", "gentle", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hobby(shell_stringing).
hobby(kite_patching).
hobby(driftwood_sorting).

problem(shell_stringing, slipping_shell).
problem(kite_patching, lifting_corner).
problem(driftwood_sorting, misfit_piece).

team_fix(shell_stringing, hold_string_steady).
team_fix(kite_patching, press_together).
team_fix(driftwood_sorting, compare_side_by_side).

good_story(H) :- hobby(H), problem(H, _), team_fix(H, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for h in HOBBIES.values():
        lines.append(asp.fact("hobby", h.id))
        lines.append(asp.fact("problem", h.id, h.small_problem.replace(" ", "_")))
        lines.append(asp.fact("team_fix", h.id, h.fix_method.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_hobbies() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    clingo_set = {x[0] for x in asp_valid_hobbies()}
    python_set = set(HOBBIES.keys())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches hobby registry ({len(clingo_set)} hobbies).")
        return 0
    print("MISMATCH between clingo and hobby registry:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hobby: str
    name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life island hobby storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    hobby = args.hobby or rng.choice(sorted(HOBBIES))
    place = args.place or rng.choice(sorted(PLACES))
    name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hobby=hobby, name=name, helper_name=helper_name, trait=trait)


def story_valid(params: StoryParams) -> None:
    if params.name == params.helper_name:
        raise StoryError("The hero and helper must be different people.")


def generate(params: StoryParams) -> StorySample:
    story_valid(params)
    place = PLACES[params.place]
    hobby = HOBBIES[params.hobby]
    hero = Person(name=params.name, role="child", traits=["little", params.trait])
    helper = Person(name=params.helper_name, role="friend", traits=["helpful", "steady"])
    world = World(place=place, hero=hero, helper=helper, hobby=hobby)

    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1

    world.say(
        f"On {place.island}, {hero.name} was a {params.trait} little child who loved {hobby.name}."
    )
    world.say(
        f"Every afternoon, {hero.name} would sit on {place.spot} with {hobby.tool} and "
        f"{hobby.repeated_verb}."
    )
    world.say(
        f"{hero.name} liked the way the work slowly turned into {hobby.finished_object}."
    )

    world.para()
    world.say(
        f"One day, while {hero.name} was practicing, {hobby.small_problem}."
    )
    hero.memes["curiosity"] += 1
    hero.meters["mess"] += 1
    world.say(
        f"{hero.name} leaned closer and looked again, because being curious on the island "
        f"often helped with little problems."
    )

    world.para()
    helper.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1
    world.say(
        f"Then {helper.name} came over and said, 'Let's {hobby.fix_method}.'"
    )
    world.say(
        f"So the two of them worked side by side. {hero.name} held the {hobby.tool.split()[0]} "
        f"steady, and {helper.name} helped with the tricky part."
    )
    for _ in range(2):
        hero.meters["progress"] += 1
        world.say(
            f"They tried again and again, and each try made the {hobby.finished_object} look a little better."
        )

    world.para()
    world.say(
        f"At last, {hero.name} smiled at {hobby.finished_object}. The small problem was gone, "
        f"and the whole porch felt calm again."
    )
    world.say(
        f"That evening, {hero.name} and {helper.name} sat together and admired how repetition "
        f"and teamwork had turned a simple hobby into something beautiful."
    )

    world.facts.update(hero=hero, helper=helper, hobby=hobby, place=place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    h = world.facts["hobby"]
    p = world.facts["place"]
    hero = world.facts["hero"]
    return [
        f"Write a gentle slice-of-life story about {hero.name} on {p.island} and the hobby of {h.name}.",
        f"Tell a child-friendly island story where repetition helps {hero.name} improve at {h.question_seed}-based craft.",
        f"Write a short story about teamwork and curiosity on {p.spot}, ending with a finished hobby project.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    hobby = world.facts["hobby"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What hobby did {hero.name} love on the island?",
            answer=f"{hero.name} loved {hobby.name} on {place.island}.",
        ),
        QAItem(
            question=f"Who helped {hero.name} with the hobby?",
            answer=f"{helper.name} helped {hero.name}, and they worked together side by side.",
        ),
        QAItem(
            question=f"What made the project better after the small problem appeared?",
            answer=f"Repetition and teamwork made the project better, because they kept trying again until it worked.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "shells": (
        "What are shells?",
        "Shells are hard outer homes made by some sea creatures, and people often find them on beaches.",
    ),
    "kite": (
        "What is a kite?",
        "A kite is a toy that can fly in the sky when someone holds its string and the wind catches it.",
    ),
    "wood": (
        "What is driftwood?",
        "Driftwood is wood that has floated in water and washed up on shore.",
    ),
    "curiosity": (
        "What does curiosity mean?",
        "Curiosity means wanting to look, learn, and find out how things work.",
    ),
    "teamwork": (
        "What is teamwork?",
        "Teamwork means people help each other and work together to do something.",
    ),
    "repetition": (
        "Why do people repeat practice?",
        "People repeat practice because doing something again and again can help them get better at it.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    hobby = world.facts["hobby"]
    keys = [hobby.tag, "curiosity", "teamwork", "repetition"]
    out: list[QAItem] = []
    for key in keys:
        q, a = WORLD_KNOWLEDGE[key]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"hero={world.hero.name} meters={world.hero.meters} memes={world.hero.memes}\n"
        f"helper={world.helper.name} meters={world.helper.meters} memes={world.helper.memes}\n"
        f"hobby={world.hobby.id}\n"
        f"place={world.place.island} / {world.place.spot}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="lagoon", hobby="shell_stringing", name="Mina", helper_name="Tari", trait="curious"),
    StoryParams(place="harbor", hobby="kite_patching", name="Owen", helper_name="Sana", trait="patient"),
    StoryParams(place="village", hobby="driftwood_sorting", name="Lena", helper_name="Ari", trait="careful"),
]


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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
