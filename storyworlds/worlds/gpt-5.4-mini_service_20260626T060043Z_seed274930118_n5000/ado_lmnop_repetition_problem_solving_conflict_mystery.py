#!/usr/bin/env python3
"""
A small mystery storyworld with repetition, conflict, and problem solving.

Seed idea:
- A child keeps noticing the same odd clue again and again.
- The child and a helper disagree about what the clue means.
- They solve the problem by checking the clues in order and matching them up.
- The story ends with the mystery explained in a concrete, child-friendly way.

This world keeps the style close to a gentle mystery: quiet noticing,
careful repeating, a small argument, and a satisfying reveal.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class Place:
    name: str
    detail: str
    hiding_spots: list[str]


@dataclass
class Clue:
    id: str
    label: str
    repetition_line: str
    physical_sign: str
    meaning: str


@dataclass
class Culprit:
    id: str
    label: str
    why: str
    left_behind: str


PLACES = {
    "library": Place("the little library", "Rows of books made soft shadows on the floor.", ["desk", "reading rug", "quiet shelf"]),
    "attic": Place("the attic", "Old boxes waited under the slanted roof.", ["trunk", "toy box", "window ledge"]),
    "garden_shed": Place("the garden shed", "Tools hung on the wall and jars sat in a row.", ["bench", "seed box", "door crack"]),
}

CLUES = {
    "tap": Clue("tap", "tap", "The tap-tap sound came again.", "three small knocks", "someone was calling from inside"),
    "trail": Clue("trail", "trail", "The little trail showed up again.", "tiny blue crumbs", "a snack had been carried through the room"),
    "note": Clue("note", "note", "The note appeared in the same spot again.", "a folded scrap of paper", "the message had been moved and returned"),
}

CULPRITS = {
    "mouse": Culprit("mouse", "a mouse", "it wanted crumbs", "blue crumbs"),
    "wind": Culprit("wind", "the wind", "it pushed paper around", "a folded scrap of paper"),
    "cat": Culprit("cat", "a cat", "it chased a string and bumped things", "a loose ribbon"),
}

GREETINGS = ["hello", "wait", "look", "listen", "hmm"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(library). place(attic). place(garden_shed).
clue(tap). clue(trail). clue(note).
culprit(mouse). culprit(wind). culprit(cat).

matches(tap, mouse).
matches(trail, mouse).
matches(note, wind).

repetition(C) :- clue(C).
problem(C) :- repetition(C), clue(C).
conflict(H, C) :- hears(H, C), doubts(H, C).
solved(C) :- clue(C), checked(C), matched(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for kid in CULPRITS:
        lines.append(asp.fact("culprit", kid))
    for clue_id, culprit_id in [("tap", "mouse"), ("trail", "mouse"), ("note", "wind")]:
        lines.append(asp.fact("matches", clue_id, culprit_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repetition/1. #show problem/1."))
    atoms = set()
    for sym in model:
        if sym.name in {"repetition", "problem"}:
            atoms.add((sym.name, tuple(a.string if a.type.name == "String" else a.name for a in sym.arguments)))
    expected = {("repetition", (cid,)) for cid in CLUES} | {("problem", (cid,)) for cid in CLUES}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery world about repetition, conflict, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for culprit in CULPRITS:
                if clue == "tap" and culprit == "mouse":
                    combos.append((place, clue, culprit))
                elif clue == "trail" and culprit == "mouse":
                    combos.append((place, clue, culprit))
                elif clue == "note" and culprit == "wind":
                    combos.append((place, clue, culprit))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.culprit is None or c[2] == args.culprit)]
    if not combos:
        raise StoryError("No valid mystery fits those options.")
    place, clue, culprit = rng.choice(sorted(combos))
    hero = args.name or rng.choice(["Ava", "Noah", "Mina", "Leo", "Ivy"])
    helper = args.helper or rng.choice(["Grandma", "Uncle Ben", "Maya", "Sam"])
    return StoryParams(place=place, clue=clue, culprit=culprit, hero_name=hero, helper_name=helper)


def should_include_repetition(clue: Clue) -> bool:
    return True


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    culprit = CULPRITS[params.culprit]

    world = World(place=place.name)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="adult"))
    clue_obj = world.add(Entity(id="clue", type="clue", label=clue.label, phrase=clue.physical_sign, owner=hero.id))
    culprit_obj = world.add(Entity(id="culprit", type="culprit", label=culprit.label, phrase=culprit.left_behind))

    hero.memes["curious"] = 1
    helper.memes["watchful"] = 1
    world.facts.update(place=place, clue=clue, culprit=culprit, hero=hero, helper=helper)

    # Act 1
    world.say(f"{hero.id} was in {place.name}, and the room felt quiet enough to hear a whisper.")
    world.say(f"{hero.id} noticed {clue.repetition_line} {place.detail}")
    world.say(f"{hero.id} saw {clue.physical_sign} near the {place.hiding_spots[0]} and said, \"{random.choice(GREETINGS).capitalize()}, that looks odd.\"")

    # Act 2 repetition and conflict
    world.para()
    world.say(f"{hero.id} looked again. Then {hero.pronoun()} looked a third time.")
    world.say(f"The same clue was still there, so {hero.id} knew it was not an accident.")
    hero.memes["conflict"] = 1
    helper.memes["doubt"] = 1
    world.say(f"But {helper.id} frowned and said the clue could mean something else.")
    world.say(f"{hero.id} wanted to check every corner, while {helper.id} wanted to stop and guess.")
    world.say(f"They had a small conflict because one of them wanted answers now, and the other wanted to be careful.")

    # Act 3 problem solving
    world.para()
    world.say(f"{hero.id} took a slow breath and made a plan.")
    world.say(f"{hero.id} checked the {place.hiding_spots[0]}, then the {place.hiding_spots[1]}, and then the {place.hiding_spots[2]}.")
    world.say(f"Each place was quiet, but the clue made sense at last.")
    world.say(f"{hero.id} matched the {clue.label} clue to {culprit.label} because {culprit.why}.")
    world.say(f"That meant the {culprit.label} had left behind {culprit.left_behind}, and the mystery was solved.")
    world.say(f"{helper.id} smiled, and the two of them put the room back in order.")

    hero.memes["conflict"] = 0
    hero.memes["pride"] = 1
    world.facts["solved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short child-friendly mystery set in {f["place"].name} with the words "ado" and "lmnop".',
        f"Tell a story where {f['hero'].id} notices the same clue again and again, disagrees with {f['helper'].id}, and solves the problem.",
        f"Write a gentle mystery about repetition, conflict, and problem solving in {f['place'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    culprit = f["culprit"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the mystery started?",
            answer=f"{hero.id} was in {place.name}, where the room felt quiet and strange."
        ),
        QAItem(
            question=f"What clue did {hero.id} keep seeing again and again?",
            answer=f"{hero.id} kept seeing the {clue.label} clue, and the clue came back in the same way more than once."
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.id} have a conflict?",
            answer=f"They had a conflict because {hero.id} wanted to keep checking clues while {helper.id} wanted to guess too soon."
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} solved the problem by checking the hiding spots one by one and matching the clue to {culprit.label}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition in a mystery?",
            answer="Repetition means something happens or appears again and again, which can help a detective notice a pattern."
        ),
        QAItem(
            question="Why do detectives check clues carefully?",
            answer="Detectives check clues carefully so they do not guess too fast and miss the real answer."
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is when characters want different things or disagree, and they need to work through it."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is repetition in a mystery?", answer="Repetition means something shows up again and again, which can point to a pattern."),
        QAItem(question="Why do detectives check clues carefully?", answer="They check carefully so they can solve the problem instead of guessing wrong."),
        QAItem(question="What is conflict in a story?", answer="Conflict is a disagreement or problem that characters need to work through."),
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


def world_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(world_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repetition/1. #show problem/1. #show conflict/2. #show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show repetition/1. #show problem/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("library", "note", "wind", "Ava", "Grandma"),
            StoryParams("attic", "tap", "mouse", "Leo", "Uncle Ben"),
            StoryParams("garden_shed", "trail", "mouse", "Mina", "Sam"),
        ]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
