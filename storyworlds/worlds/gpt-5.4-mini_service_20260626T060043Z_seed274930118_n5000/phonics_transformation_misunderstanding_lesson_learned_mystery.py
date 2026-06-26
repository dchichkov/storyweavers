#!/usr/bin/env python3
"""
storyworlds/worlds/phonics_transformation_misunderstanding_lesson_learned_mystery.py
=====================================================================================

A small mystery-style storyworld about phonics, misunderstanding, transformation,
and a lesson learned.

Seed tale:
---
A child hears a puzzling note in a quiet classroom. The letters look like a clue,
but the first guess is wrong. By sounding out the word slowly, the child turns
confusion into understanding, finds the missing thing, and learns that phonics
can unlock a mystery.

World ideas:
- Phonics turns a squiggle-note into a readable clue.
- Misunderstanding creates the mystery turn.
- Transformation happens when the clue is sounded out correctly.
- Lesson learned ends the story with a clear, child-facing takeaway.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    hush: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    letters: str
    decoded: str
    sounds: list[str]
    meaning: str
    target: str
    clue_kind: str = "note"


@dataclass
class StoryParams:
    setting: str
    clue: str
    target: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "classroom": Setting(place="the classroom", hush="quiet and careful", afford={"read"}),
    "library": Setting(place="the library", hush="soft and still", afford={"read"}),
    "hallway": Setting(place="the hallway bulletin board", hush="echoey and bright", afford={"read"}),
}

CLUES = {
    "note": Clue(
        id="note",
        letters="b-a-t",
        decoded="bat",
        sounds=["b", "a", "t"],
        meaning="a small flying animal, not a baseball bat",
        target="hat",
    ),
    "tag": Clue(
        id="tag",
        letters="r-u-g",
        decoded="rug",
        sounds=["r", "u", "g"],
        meaning="a soft floor covering",
        target="mug",
    ),
    "card": Clue(
        id="card",
        letters="sh-i-p",
        decoded="ship",
        sounds=["sh", "i", "p"],
        meaning="a boat that sails on water",
        target="lid",
    ),
    "chalk": Clue(
        id="chalk",
        letters="c-u-p",
        decoded="cup",
        sounds=["c", "u", "p"],
        meaning="a small container for drinks",
        target="cap",
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nia", "Toby", "Ari", "Zoe", "Ben", "Luna"]
HELPER_NAMES = ["Ms. Finch", "Mr. Reed", "Ms. Vale"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "patient"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def clean_word(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def intro_line(hero: Entity, setting: Setting, clue: Clue) -> str:
    return (
        f"{hero.id} was a little {hero.type} who loved quiet mysteries, "
        f"and {setting.place} was the perfect place to look for clues."
    )


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=HELPER_NAMES[0]))
    note = world.add(Entity(
        id="clue",
        kind="thing",
        type="note",
        label="note",
        phrase=f"a small note with the letters {clue.letters}",
        owner=helper.id,
        meters={"hidden": 1.0},
    ))
    lost_item = world.add(Entity(
        id="lost",
        kind="thing",
        type=params.target,
        label=params.target,
        phrase=f"a missing {params.target}",
        owner=helper.id,
        meters={"missing": 1.0},
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["confusion"] = 0.0
    hero.memes["confidence"] = 0.0
    hero.memes["relief"] = 0.0

    world.facts.update(hero=hero, helper=helper, clue=clue, note=note, lost=lost_item)
    return world


def run_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    note: Entity = world.facts["note"]  # type: ignore[assignment]
    lost: Entity = world.facts["lost"]  # type: ignore[assignment]

    world.say(intro_line(hero, world.setting, clue))
    world.say(
        f"One day, {helper.label} found a tiny note and asked {hero.id} to help solve the mystery."
    )
    world.say(
        f"The note showed the letters {clue.letters}, but at first {hero.id} guessed wrong."
    )

    world.para()
    hero.memes["confusion"] += 1.0
    world.say(
        f"{hero.id} thought the clue meant a {clue.meaning.split(',')[0]}, "
        f"which did not fit the missing {lost.label} at all."
    )
    world.say(
        f"{helper.label} smiled and said, 'Let's sound it out slowly: "
        + ", ".join(clue.sounds)
        + ".'"
    )

    world.para()
    hero.memes["confidence"] += 1.0
    hero.memes["confusion"] = 0.0
    note.meters["hidden"] = 0.0
    note.meters["read"] = 1.0
    note.phrase = f"a note that now clearly reads {clue.decoded}"

    world.say(
        f"{hero.id} tapped each sound, and the jumble of letters changed into the word {clue.decoded}."
    )
    world.say(
        f"That was the right clue, because the lost {lost.label} had been tucked near the {clue.target} all along."
    )

    world.para()
    lost.meters["found"] = 1.0
    hero.memes["relief"] += 1.0
    hero.memes["lesson"] = 1.0

    world.say(
        f"{hero.id} looked in the right spot and found the missing {lost.label}."
    )
    world.say(
        f"With a proud grin, {hero.id} learned the lesson: when a word is puzzling, phonics can turn a misunderstanding into a clear answer."
    )

    world.facts["solved"] = True
    world.facts["lesson"] = "sound out the letters slowly"
    world.facts["transformation"] = f"{clue.letters} -> {clue.decoded}"
    world.facts["misunderstanding"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    return [
        f"Write a tiny mystery story for children where {hero.id} solves a clue by using phonics.",
        f"Tell a story in which the letters {clue.letters} are first misunderstood, then decoded correctly.",
        "Write a gentle classroom mystery with a misunderstanding, a transformation, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    lost: Entity = f["lost"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery was {hero.id} helping to solve?",
            answer=f"{hero.id} was helping to solve the mystery of the missing {lost.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} first misunderstand about the clue?",
            answer=f"At first, {hero.id} guessed the letters {clue.letters} meant the wrong thing.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.id}?",
            answer=f"{helper.label} helped by telling {hero.id} to sound the word out slowly, one sound at a time.",
        ),
        QAItem(
            question="What changed when the child used phonics?",
            answer=f"The confusing letters changed into the word {clue.decoded}, and the clue became easy to understand.",
        ),
        QAItem(
            question="What lesson did the child learn at the end?",
            answer="The child learned that sounding out letters slowly can turn a misunderstanding into a clear answer.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "phonics": (
        "What are phonics?",
        "Phonics is a way of learning to read by connecting letters with their sounds.",
    ),
    "mystery": (
        "What is a mystery?",
        "A mystery is a story with a puzzle that the characters try to solve.",
    ),
    "sound": (
        "Why do people sound out words?",
        "People sound out words to help them read tricky letters one small sound at a time.",
    ),
    "lesson": (
        "What is a lesson learned?",
        "A lesson learned is a useful idea that someone remembers after something happens.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(A, C, T) :- setting(A), clue(C), target(T), afford(A, read), clue_target(C, T).
valid_story(A, C, T, H) :- valid(A, C, T), hero_type(H).

% Reasonableness gate:
% A clue is valid when the setting supports reading and the clue points to the
% target object in a way that can be solved by sounding out the letters.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_letters", cid, c.letters))
        lines.append(asp.fact("clue_target", cid, c.target))
    for h in ["girl", "boy"]:
        lines.append(asp.fact("hero_type", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Validity helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for clue_id, clue in CLUES.items():
            if setting in {"classroom", "library", "hallway"} and clue.letters and clue.target:
                combos.append((setting, clue_id, clue.target))
    return combos


def explain_rejection(setting: str, clue: str, target: str) -> str:
    return (
        f"(No story: the clue {clue!r} does not cleanly lead to {target!r} "
        f"in {setting!r}, so the mystery would not have a fair phonics solution.)"
    )


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny phonics mystery storyworld with misunderstanding, transformation, and lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--target")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["teacher"])
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
    combos = valid_combos()
    if args.setting and args.clue and args.target:
        if (args.setting, args.clue, args.target) not in combos:
            raise StoryError(explain_rejection(args.setting, args.clue, args.target))
    combos = [c for c in combos
              if (not args.setting or c[0] == args.setting)
              and (not args.clue or c[1] == args.clue)
              and (not args.target or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, target = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_type = "teacher"
    return StoryParams(setting=setting, clue=clue, target=target,
                       hero_name=hero_name, hero_type=hero_type,
                       helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    run_story(world)
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
        print()
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Curated outputs
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="classroom", clue="note", target="hat", hero_name="Mia", hero_type="girl", helper_type="teacher"),
    StoryParams(setting="library", clue="tag", target="mug", hero_name="Leo", hero_type="boy", helper_type="teacher"),
    StoryParams(setting="hallway", clue="card", target="lid", hero_name="Nia", hero_type="girl", helper_type="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combinations ({len(stories)} with hero type):\n")
        for s, c, t in combos:
            hero_types = sorted(h for (ss, cc, tt, h) in stories if (ss, cc, tt) == (s, c, t))
            print(f"  {s:10} {c:6} {t:6} [{', '.join(hero_types)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
