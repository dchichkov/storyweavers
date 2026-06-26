#!/usr/bin/env python3
"""
A small detective-story world about an orphaned child whose curiosity leads to a
mystery solved outside.

Premise:
- A curious orphan child notices a strange clue outdoors.
- The child wants to keep looking, but the clue is risky or puzzling.
- A helper guides the child to inspect the evidence carefully.
- The mystery is solved, and the child ends the story feeling steadier and seen.

This script follows the Storyweavers storyworld contract.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old street"
    outside: bool = True
    affordance: str = "search"


@dataclass
class Mystery:
    id: str
    clue: str
    question: str
    solution: str
    danger: str
    method: str
    outside_detail: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "alley": Setting(place="the narrow alley", outside=True, affordance="search"),
    "garden": Setting(place="the quiet garden", outside=True, affordance="search"),
    "porch": Setting(place="the front porch", outside=True, affordance="search"),
    "yard": Setting(place="the weedy yard", outside=True, affordance="search"),
}

MYSTERIES = {
    "lost_key": Mystery(
        id="lost_key",
        clue="a small brass key",
        question="Who dropped the key?",
        solution="the grocer's pouch had a hole in it",
        danger="the key might be kicked into the drain",
        method="follow the scuff marks and listen for the metal click",
        outside_detail="It lay near a muddy crack in the pavement.",
    ),
    "missing_note": Mystery(
        id="missing_note",
        clue="a folded note with a red ribbon",
        question="Who was the note for?",
        solution="the note had blown out of a mailbox and snagged on a bush",
        danger="the wind could carry it farther away",
        method="watch where the ribbon bends and where the leaves point",
        outside_detail="It fluttered in a thorny hedge like a tiny flag.",
    ),
    "strange_bootprint": Mystery(
        id="strange_bootprint",
        clue="one deep bootprint",
        question="Why was there only one print?",
        solution="a delivery worker had stepped down from a cart",
        danger="rain could blur the print before it was studied",
        method="measure the tread and trace the cart wheels",
        outside_detail="The print sat in damp dirt beside a bicycle track.",
    ),
}

HELPERS = {
    "cat": "a patient cat",
    "neighbor": "an old neighbor",
    "guard": "a kind gate guard",
    "sister": "an older sister",
}

TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed", "patient"]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Noa", "Rosa", "Tia"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Milo", "Finn", "Jules"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def is_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return setting.outside and bool(mystery.clue) and bool(mystery.solution)


def reasonableness_error(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: this mystery needs an outside place where clues can be found. "
        f"'{setting.place}' does not fit the detective setup.)"
    )


def build_character_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def capitalize_name(name: str) -> str:
    return name


def tell(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    place = world.setting.place
    world.say(
        f"{hero.id} was an orphan child with a very curious mind, the kind that "
        f"noticed every loose stone and every skipped shadow."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked to look for answers outside, because "
        f"the air felt full of tiny questions."
    )
    world.say(
        f"One day at {place}, {hero.id} spotted {article(mystery.clue)} {mystery.clue}. "
        f"{mystery.outside_detail}"
    )
    world.say(
        f"{hero.id} wanted to keep following the clue, but {mystery.danger}."
    )

    world.para()
    world.say(
        f"{helper.label} noticed {hero.id} standing still and said, "
        f"\"Slow down. A good detective watches first and runs later.\""
    )
    world.say(
        f"Together they used {mystery.method}. That helped them answer the question: "
        f"{mystery.question}"
    )

    world.para()
    world.say(
        f"In the end, they found out that {mystery.solution}. "
        f"{hero.id} tucked the clue safely away and felt less alone."
    )
    world.say(
        f"The little detective stood outside in the evening light, smiling at "
        f"the solved mystery and the calm, clear path home."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for a young child about an orphan named {hero.id} who is very curious and finds {article(mystery.clue)} {mystery.clue} outside.',
        f"Tell a gentle mystery story where {hero.id} and {f['helper'].label} look outside at {world.setting.place} and solve what happened.",
        f'Write a story with the words "outside", "curious", and "mystery" where a child solves a small clue in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a curious orphan child who likes solving mysteries outside.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find at {place}?",
            answer=f"{hero.id} found {article(mystery.clue)} {mystery.clue} at {place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.label} helped {hero.id} solve the mystery by telling {hero.pronoun('object')} to look carefully.",
        ),
        QAItem(
            question=f"What did the clue lead them to learn?",
            answer=f"It led them to learn that {mystery.solution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand yet, so you look for clues to figure it out.",
        ),
        QAItem(
            question="Why do detectives look carefully?",
            answer="Detectives look carefully because small details can help them understand what happened.",
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they can point toward the answer and help solve the problem.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when it has an outside setting, a clue, and a solution.
valid_story(S, M) :- outside(S), mystery(M), clue(M), solution(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.outside:
            lines.append(asp.fact("outside", sid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid))
        lines.append(asp.fact("solution", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = {(sid, mid) for sid, s in SETTINGS.items() for mid, m in MYSTERIES.items() if is_reasonable(s, m)}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python reasonableness ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python reasonableness:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small outside detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or build_character_name(gender, rng)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)

    s = SETTINGS[setting]
    m = MYSTERIES[mystery]
    if not is_reasonable(s, m):
        raise StoryError(reasonableness_error(s, m))

    return StoryParams(
        setting=setting,
        mystery=mystery,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"curiosity": 2.0, "loneliness": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=HELPERS[params.helper],
        meters={"distance": 0.0},
        memes={"kindness": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.clue,
        phrase=mystery.clue,
        location=setting.place,
    ))

    world.facts.update(hero=hero, helper=helper, clue=clue, mystery=mystery, setting=setting)
    tell(world, hero, helper, mystery)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.location:
            bits.append(f"location={e.location!r}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="alley", mystery="lost_key", name="Mina", gender="girl", helper="neighbor", trait="curious"),
    StoryParams(setting="garden", mystery="missing_note", name="Owen", gender="boy", helper="sister", trait="sharp-eyed"),
    StoryParams(setting="yard", mystery="strange_bootprint", name="Ivy", gender="girl", helper="guard", trait="patient"),
]


def asp_list() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    vals = sorted(set(asp.atoms(model, "valid_story")))
    print(f"{len(vals)} valid stories:\n")
    for sid, mid in vals:
        print(f"  {sid:10} {mid}")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sys.exit(asp_list())

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
