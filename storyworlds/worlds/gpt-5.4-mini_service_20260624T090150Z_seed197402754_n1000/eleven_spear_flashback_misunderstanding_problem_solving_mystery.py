#!/usr/bin/env python3
"""
A small mystery story world: eleven clues, a spear-shaped shadow, a flashback,
a misunderstanding, and a careful round of problem solving.

A child or small hero notices a puzzling sign, remembers an earlier moment,
misreads the clue at first, then solves the mystery by checking the world.
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
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    places_to_check: tuple[str, ...]


@dataclass
class Clue:
    label: str
    where: str
    shadow_word: str
    innocent_explanation: str
    true_explanation: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting("the garden", False, ("bench", "hedge", "gate", "path")),
    "library": Setting("the library", True, ("desk", "shelf", "window", "rug")),
    "museum": Setting("the museum", True, ("hall", "display", "corner", "archway")),
}

CLUES = {
    "garden": Clue(
        label="eleven little marks",
        where="the path by the old gate",
        shadow_word="spear",
        innocent_explanation="a spear-shaped shadow from a garden rake",
        true_explanation="the handle of a rake leaning near the wall",
    ),
    "library": Clue(
        label="eleven tiny scratches",
        where="the floor beside the desk",
        shadow_word="spear",
        innocent_explanation="a spear-shaped streak made by a loose bookmark",
        true_explanation="a bookmark caught under the chair leg",
    ),
    "museum": Clue(
        label="eleven pale dots",
        where="the glass case",
        shadow_word="spear",
        innocent_explanation="a spear-shaped reflection from a pointer stick",
        true_explanation="a guide's pointer reflecting in the light",
    ),
}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a curious little {hero.type} who loved mysteries and counted things twice."
    )
    world.say(
        f"One day, {hero.id} found {clue.label} near {clue.where}, and one line looked like a spear."
    )


def flashback(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"{hero.id} stopped and remembered an earlier day when {hero.pronoun('possessive')} own toy looked the same."
    )
    world.say(
        f"In that flashback, the shape had fooled {hero.pronoun('object')} before, so {hero.id} felt unsure."
    )


def misunderstanding(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    world.say(
        f"{hero.id} first thought the spear shape meant someone had left a weapon behind."
    )
    world.say(
        f"But that was a misunderstanding, because the clue was only a shadow, not a real spear."
    )


def problem_solving(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    world.say(
        f"{hero.id} looked for {hero.pronoun('possessive')} first clue, then checked the floor, the wall, and the light."
    )
    world.say(
        f"At last, {hero.id} solved the mystery: {clue.innocent_explanation} made the spear shape."
    )
    world.say(
        f"The answer was simple, and the scary guess was wrong; the real thing was {clue.true_explanation}."
    )


def ending(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} smiled, counted all eleven clues again, and walked away knowing how a shadow can trick the eye."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    return [
        'Write a short mystery story for a young child that uses the words "eleven" and "spear".',
        f"Tell a gentle mystery where {hero.id} finds {clue.label} and has to solve a misunderstanding.",
        "Write a child-facing story with a flashback, a wrong guess, and a careful solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} find near {clue.where}?",
            answer=f"{hero.id} found {clue.label} near {clue.where}.",
        ),
        QAItem(
            question=f"Why did {hero.id} think of a spear at first?",
            answer=(
                f"{hero.id} saw a spear-shaped shadow and first guessed it might be something dangerous, "
                f"but that was only a misunderstanding."
            ),
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=(
                f"{hero.id} checked the place carefully, remembered the earlier moment in a flashback, "
                f"and learned the shape came from {clue.innocent_explanation}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem that people solve by looking for clues.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened earlier.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea at first.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means carefully thinking, checking clues, and finding an answer.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(h1).
setting(garden).
setting(library).
setting(museum).

clue(garden, eleven_marks).
clue(library, eleven_scratches).
clue(museum, eleven_dots).

shape(spear).
feature(flashback).
feature(misunderstanding).
feature(problem_solving).

compatible(H, S, C) :- hero(H), setting(S), clue(S, C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid, f"eleven_{cid}"))
    lines.append(asp.fact("shape", "spear"))
    lines.append(asp.fact("feature", "flashback"))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "problem_solving"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(hero, place, f"eleven_{place}") for hero in ["h1"] for place in SETTINGS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python compatibility ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_places() -> list[str]:
    return sorted(SETTINGS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(["Mia", "Leo", "Nora", "Zane", "Ava", "Toby"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    clue = CLUES[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    world.facts["hero"] = hero
    world.facts["clue"] = clue

    intro(world, hero, clue)
    world.para()
    flashback(world, hero, clue)
    misunderstanding(world, hero, clue)
    world.para()
    problem_solving(world, hero, clue)
    ending(world, hero, clue)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with eleven clues and a spear-shaped shadow.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind}) type={e.type}")
    lines.append("  facts:")
    for k, v in world.facts.items():
        if isinstance(v, Entity):
            lines.append(f"    {k}: {v.id}")
        elif isinstance(v, Clue):
            lines.append(f"    {k}: {v.label} at {v.where}")
        else:
            lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible story combinations:")
        for combo in combos:
            print("  ", combo)
        return

    samples: list[StorySample] = []
    if args.all:
        for place in valid_places():
            params = StoryParams(place=place, hero_name="Mia", hero_type="girl", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
