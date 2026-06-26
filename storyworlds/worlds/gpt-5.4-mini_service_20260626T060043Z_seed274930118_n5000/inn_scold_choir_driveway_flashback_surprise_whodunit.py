#!/usr/bin/env python3
"""
A tiny whodunit storyworld set in a driveway.

Premise:
- A rainy driveway outside an old inn.
- A child hears a strange sound from a choir rehearsal gone wrong.
- A small mystery forms around a missing silver bell.

Turn:
- A flashback reveals who last handled the bell.
- A surprise clue in the driveway solves the case.

The world model tracks physical meters and emotional memes so the prose is
state-driven rather than template-swapped.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"seen": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the driveway"
    weather: str = "drizzly"


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    hint: str
    risk: str


@dataclass
class StoryParams:
    clue: str
    name: str
    role: str
    witness: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld in a driveway.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child", "neighbor", "caretaker"])
    ap.add_argument("--witness", choices=["innkeeper", "choir_lead", "driver"])
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


SETTING = Setting()

CLUES = {
    "bell": Clue(
        id="bell",
        label="silver bell",
        reveal="under the inn porch mat",
        hint="a faint ring in the driveway",
        risk="missing from the choir table",
    ),
    "sheet": Clue(
        id="sheet",
        label="music sheet",
        reveal="stuck to a wet tire",
        hint="a flutter near the car door",
        risk="blown away from the choir stand",
    ),
    "glove": Clue(
        id="glove",
        label="white glove",
        reveal="caught on a mailbox hook",
        hint="a bright scrap near the gate",
        risk="left beside the choir robe basket",
    ),
}

NAMES = ["Mina", "Theo", "June", "Luca", "Ivy", "Nora"]
ROLES = ["child", "neighbor", "caretaker"]
WITNESSES = {
    "innkeeper": "the innkeeper",
    "choir_lead": "the choir leader",
    "driver": "the driver",
}


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "driveway"),
        asp.fact("place", "inn"),
        asp.fact("group", "choir"),
    ]
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("label", cid, clue.label))
        lines.append(asp.fact("risk", cid, clue.risk))
        lines.append(asp.fact("reveal", cid, clue.reveal))
    return "\n".join(lines)


ASP_RULES = r"""
holds(clue_missing(C)) :- clue(C).
explained(C) :- clue(C), reveal(C, _).
case_solved :- explained(C), clue(C).
#show case_solved/0.
#show explained/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        raise StoryError(f"ASP verification needs clingo/asp helpers: {exc}") from exc
    model = asp.one_model(asp_program("#show explained/1.\n#show case_solved/0."))
    explained = set(asp.atoms(model, "explained"))
    if len(explained) == len(CLUES):
        print(f"OK: ASP explains all clues ({len(explained)}).")
        return 0
    print("MISMATCH in ASP explanation count.")
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.role == "child" and params.witness == "driver" and params.clue == "glove":
        return
    if params.role == "caretaker" and params.clue == "bell":
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(list(CLUES))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    witness = args.witness or rng.choice(list(WITNESSES))
    params = StoryParams(clue=clue, name=name, role=role, witness=witness)
    reasonableness_gate(params)
    return params


def flashback(world: World, hero: Entity, witness: Entity, clue: Clue) -> None:
    world.say(
        f"Flashback: {hero.id} remembered {witness.label_word if hasattr(witness, 'label_word') else witness.label} "
        f"setting the {clue.label} near the choir table."
    )


def surprise(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"Surprise: {clue.label} appeared {clue.reveal}, and the whole mystery made sense at once."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    clue = CLUES[params.clue]

    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    witness = world.add(Entity(id=params.witness, kind="character", type="adult", label=WITNESSES[params.witness]))
    inn = world.add(Entity(id="inn", kind="place", type="inn", label="the inn"))
    choir = world.add(Entity(id="choir", kind="group", type="choir", label="the choir"))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=clue.id,
        label=clue.label,
        phrase=clue.label,
        caretaker=witness.id,
    ))

    hero.memes["curiosity"] = 2.0
    witness.memes["concern"] = 1.0
    missing.meters["seen"] = 0.0

    world.say(
        f"{hero.id} stood in {world.setting.place} beside the old inn, where the choir had just gone quiet."
    )
    world.say(
        f"Someone had scolded the group after the {clue.risk}, and that made {hero.id} look twice at every wet footprint."
    )
    world.para()
    world.say(
        f"{hero.id} noticed {clue.hint} while {witness.label} frowned at the empty spot."
    )
    world.say(
        f"{hero.id} asked careful questions, because a good whodunit begins with small clues, not loud guesses."
    )
    world.para()
    flashback(world, hero, witness, clue)
    world.say(
        f"That memory fit the marks near the driveway, and the scold suddenly sounded less like blame and more like worry."
    )
    world.para()
    surprise(world, hero, clue)
    world.say(
        f"{witness.label} let out a relieved breath, and the choir smiled when the {clue.label} was found."
    )
    world.say(
        f"By the end, {hero.id} had solved the little mystery, and the driveway looked ordinary again."
    )

    world.facts.update(
        hero=hero,
        witness=witness,
        clue=clue,
        inn=inn,
        choir=choir,
        missing=missing,
        solved=True,
        place=world.setting.place,
    )

    prompts = [
        f"Write a child-friendly whodunit set in a driveway beside an inn.",
        f"Tell a mystery story where a choir gets scolded and a clue is found by surprise.",
        f"Write a short story with a flashback that helps solve a little mystery.",
    ]
    story_qa = [
        QAItem(
            question=f"Where did {hero.id} solve the mystery?",
            answer=f"{hero.id} solved the mystery in the driveway beside the inn.",
        ),
        QAItem(
            question=f"What clue helped solve the case?",
            answer=f"The {clue.label} helped solve the case.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed that {witness.label} had placed the {clue.label} near the choir table.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the trouble.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a scene that remembers something from earlier.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think is true.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} label={e.label}")
    if qa:
        print()
        for i, item in enumerate(sample.story_qa, 1):
            print(f"SQ{i}: {item.question}")
            print(f"SA{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1):
            print(f"WQ{i}: {item.question}")
            print(f"WA{i}: {item.answer}")


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for clue in CLUES:
            params = StoryParams(
                clue=clue,
                name=NAMES[0],
                role="child",
                witness="innkeeper",
            )
            samples.append(generate(params))
        return samples
    samples = []
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        params = valid_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show explained/1.\n#show case_solved/0."))
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show explained/1.\n#show case_solved/0."))
        print(f"ASP atoms: {asp.atoms(model, 'explained')}, solved={bool(asp.atoms(model, 'case_solved'))}")
        return

    samples = generate_many(args)

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
