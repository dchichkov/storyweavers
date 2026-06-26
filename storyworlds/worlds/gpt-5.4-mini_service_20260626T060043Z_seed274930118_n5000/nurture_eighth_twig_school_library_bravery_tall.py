#!/usr/bin/env python3
"""
storyworlds/worlds/nurture_eighth_twig_school_library_bravery_tall.py
====================================================================

A small tall-tale storyworld set in a school library.

Premise:
- A brave eighth-grade child finds a fragile twig in the school library.
- The librarian worries the twig will snap or get lost.
- The child chooses nurture over haste and makes a safe little home for it.

The world is intentionally tiny, but state-driven:
- physical meters track things like brittleness, dryness, and safe placement
- emotional memes track bravery, worry, care, and relief

The story is meant to read like a child-facing tall tale: concrete, a little
grand, and ending with a clear image of what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTING_NAME = "school library"


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("brittle", "dry", "safe", "tidy", "heavy"):
            self.meters.setdefault(k, 0.0)
        for k in ("bravery", "worry", "care", "relief", "love", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    grade_word: str
    gender: str
    librarian_name: str
    seed: Optional[int] = None


NAMES_BY_GENDER = {
    "girl": ["Mina", "Ivy", "Lena", "Ada", "Nora", "Ruby", "Cleo"],
    "boy": ["Eli", "Noah", "Theo", "Jasper", "Owen", "Miles", "Finn"],
}

LIBRARIAN_NAMES = ["Ms. Maple", "Mr. Reed", "Ms. Bell", "Mr. Finch"]
GRADE_WORDS = ["eighth", "eighth-grade", "eighth"]
GRADE_PHRASES = {
    "eighth": "an eighth-grader",
    "eighth-grade": "an eighth-grade student",
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    return params.gender in {"girl", "boy"} and bool(params.name) and bool(params.librarian_name)


def explain_invalid(params: StoryParams) -> str:
    return "Invalid story options for this world."


# ---------------------------------------------------------------------------
# Causal narration
# ---------------------------------------------------------------------------

def _do_brave_choice(world: World, hero: Entity, twig: Entity) -> None:
    hero.memes["bravery"] += 1
    hero.memes["care"] += 1
    twig.meters["safe"] += 1
    twig.meters["brittle"] = max(0.0, twig.meters["brittle"] - 0.5)
    world.say(
        f"{hero.id} took a brave breath and chose nurture instead of hurry."
    )


def _do_settle_twig(world: World, hero: Entity, librarian: Entity, twig: Entity) -> None:
    hero.memes["bravery"] += 0.5
    librarian.memes["relief"] += 1
    twig.meters["dry"] = 0.0
    twig.meters["safe"] += 1
    world.say(
        f"Together, {hero.id} and {librarian.pronoun('subject')} found a small cup, a little water, and a sunny window."
    )
    world.say(
        f"The twig stood there like a tiny banner from a far-off forest, finally safe in the school library."
    )


def _do_read_to_twig(world: World, hero: Entity, twig: Entity) -> None:
    hero.memes["love"] += 1
    hero.memes["pride"] += 1
    twig.meters["brittle"] = max(0.0, twig.meters["brittle"] - 0.25)
    world.say(
        f"{hero.id} read a story aloud, and even the twig seemed to listen."
    )


def tell(world: World, hero: Entity, librarian: Entity, twig: Entity) -> None:
    world.say(
        f"In the {world.setting}, {hero.id} was {hero.phrase} with a pocketful of bravery and an eye for little wonders."
    )
    world.say(
        f"One day, {hero.id} found a twig no bigger than a pencil, but it looked as noble as a mast on a storm-tossed ship."
    )
    world.say(
        f"{librarian.id} worried because the twig was dry and brittle, and one clumsy bump could snap it."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to keep the twig close, but the real trick was to nurture it, not crowd it."
    )
    _do_brave_choice(world, hero, twig)
    world.say(
        f'"Let\'s make it a safe place," {hero.id} said. "{hero.pronoun("subject").capitalize()} can stay here and grow strong."'
    )
    _do_settle_twig(world, hero, librarian, twig)
    _do_read_to_twig(world, hero, twig)
    world.para()
    world.say(
        f"By the end, the twig had a wet little cup, a sunny window, and a name in {hero.id}'s heart."
    )
    world.say(
        f"{hero.id} left the library with a taller step, because bravery had turned into care."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class RegistryItem:
    id: str
    label: str


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- child(H).
librarian(L) :- staff(L).
twig(T) :- thing(T), label(T,"twig").

safe_twig(T) :- twig(T), placed_in_cup(T), near_window(T).
brave_choice(H) :- hero(H), chooses_nurture(H).
resolution(H, T) :- brave_choice(H), safe_twig(T), reads_to_twig(H, T).

#show resolution/2.
#show brave_choice/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "school_library"))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("staff", "librarian"))
    lines.append(asp.fact("thing", "twig"))
    lines.append(asp.fact("label", "twig", "twig"))
    lines.append(asp.fact("chooses_nurture", "hero"))
    lines.append(asp.fact("placed_in_cup", "twig"))
    lines.append(asp.fact("near_window", "twig"))
    lines.append(asp.fact("reads_to_twig", "hero", "twig"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show resolution/2. #show brave_choice/1.")
    model = asp.one_model(program)
    asp_res = set(asp.atoms(model, "resolution"))
    asp_brave = set(asp.atoms(model, "brave_choice"))

    py_res = {("hero", "twig")}
    py_brave = {("hero",)}

    if asp_res == py_res and asp_brave == py_brave:
        print("OK: ASP gate matches Python reasonableness and story facts.")
        return 0

    print("MISMATCH between ASP and Python:")
    print("  ASP resolution:", sorted(asp_res))
    print("  PY  resolution:", sorted(py_res))
    print("  ASP brave:", sorted(asp_brave))
    print("  PY  brave:", sorted(py_brave))
    return 1


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError(explain_invalid(params))

    world = World(setting=SETTING_NAME)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        phrase=f"{GRADE_PHRASES[params.grade_word]}",
    ))
    librarian = world.add(Entity(
        id=params.librarian_name,
        kind="character",
        type="librarian",
        phrase="the school librarian",
    ))
    twig = world.add(Entity(
        id="twig",
        kind="thing",
        type="thing",
        label="twig",
        phrase="a twig",
        owner=hero.id,
        caretaker=librarian.id,
    ))
    twig.meters["brittle"] = 1.0
    twig.meters["dry"] = 1.0
    hero.memes["bravery"] = 1.0

    world.facts = {
        "hero": hero,
        "librarian": librarian,
        "twig": twig,
        "params": params,
    }
    tell(world, hero, librarian, twig)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    librarian: Entity = f["librarian"]
    return [
        f'Write a tall tale for children set in a school library about {hero.id}, a brave eighth-grader, and a twig that needs nurture.',
        f"Tell a gentle story where {hero.id} finds a twig in the school library and {librarian.id} worries it may snap.",
        f'Write a short story that includes the words "nurture", "eighth", and "twig", and ends with bravery turning into care.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    librarian: Entity = f["librarian"]
    twig: Entity = f["twig"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"Who is the story about in the school library?",
            answer=(
                f"The story is about {hero.id}, {hero.phrase}, who is an {params.grade_word} student with a brave heart."
            ),
        ),
        QAItem(
            question=f"What fragile thing did {hero.id} find?",
            answer=(
                f"{hero.id} found a twig, and it was dry and brittle at first."
            ),
        ),
        QAItem(
            question=f"Why did {librarian.id} worry about the twig?",
            answer=(
                f"{librarian.id} worried because the twig was so brittle that a bump could snap it."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} choose to do instead of rushing?",
            answer=(
                f"{hero.id} chose nurture. {hero.id} made a safe little place for the twig, with water and a sunny window."
            ),
        ),
        QAItem(
            question=f"How did bravery help the ending?",
            answer=(
                f"Bravery helped {hero.id} speak up, ask for help, and turn worry into care, so the twig ended the story safe in the school library."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twig?",
            answer="A twig is a small, thin piece of a tree branch.",
        ),
        QAItem(
            question="What does nurture mean?",
            answer="To nurture something means to care for it gently so it can stay healthy and grow well.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
        QAItem(
            question="What is a library for?",
            answer="A library is a place where people can read, borrow books, and enjoy quiet learning time.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld set in a school library.")
    ap.add_argument("--name", choices=sum(NAMES_BY_GENDER.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--librarian", dest="librarian_name", choices=LIBRARIAN_NAMES)
    ap.add_argument("--grade-word", choices=GRADE_WORDS)
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
    name = args.name or rng.choice(NAMES_BY_GENDER[gender])
    librarian_name = args.librarian_name or rng.choice(LIBRARIAN_NAMES)
    grade_word = args.grade_word or rng.choice(GRADE_WORDS)
    params = StoryParams(
        name=name,
        grade_word=grade_word,
        gender=gender,
        librarian_name=librarian_name,
    )
    if not valid_story(params):
        raise StoryError(explain_invalid(params))
    return params


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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolution/2. #show brave_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolution/2. #show brave_choice/1."))
        print("ASP brave choices:", sorted(set(asp.atoms(model, "brave_choice"))))
        print("ASP resolutions:", sorted(set(asp.atoms(model, "resolution"))))
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mina", grade_word="eighth", gender="girl", librarian_name="Ms. Maple"),
            StoryParams(name="Eli", grade_word="eighth-grade", gender="boy", librarian_name="Mr. Reed"),
            StoryParams(name="Ada", grade_word="eighth", gender="girl", librarian_name="Ms. Bell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.librarian_name} / {p.grade_word}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
