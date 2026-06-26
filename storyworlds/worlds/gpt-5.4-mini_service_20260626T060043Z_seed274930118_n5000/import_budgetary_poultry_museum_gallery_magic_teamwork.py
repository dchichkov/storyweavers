#!/usr/bin/env python3
"""
A tall-tale story world set in a museum gallery where an import, a budget,
and a poultry surprise are braided together by magic, teamwork, and curiosity.

The seed premise:
- In a museum gallery, a careful curator tries to manage an imported
  budgetary display.
- A curious child notices a crate of poultry-themed props, and a little
  magic makes the exhibit lively enough to become a problem.
- Teamwork turns the trouble into a memorable showpiece.

This script models physical state in meters and emotional state in memes,
then narrates a complete story driven by those state changes.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.m(key) + amount

    def add_e(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.e(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "curator"}
        male = {"boy", "man", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Gallery:
    place: str = "the museum gallery"
    budget: int = 5
    import_bonus: int = 2
    magic_allowed: bool = True
    affords: set[str] = field(default_factory=lambda: {"import", "budget", "poultry"})


@dataclass
class StoryParams:
    place: str = "museum_gallery"
    focus: str = "import"
    seed: Optional[int] = None
    name: str = "Mina"
    child_type: str = "girl"
    curator_type: str = "curator"
    magic: bool = True
    teamwork: bool = True
    curiosity: bool = True


class World:
    def __init__(self, gallery: Gallery) -> None:
        self.gallery = gallery
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
        import copy
        c = World(self.gallery)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# ASP twin and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when curiosity meets a museum import, the budget is tight,
% and teamwork plus magic can turn trouble into a display-safe success.

valid_story(P, F) :- place(P), focus(F), museum(P), import_theme(F),
                     tight_budget(P), magic_on(P), teamwork_on(P), curiosity_on(P).

needs_help(P) :- valid_story(P, _), budget_low(P), poultry_present(P).
rescued(P) :- needs_help(P), teamwork_on(P), magic_on(P).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "museum_gallery"),
        asp.fact("museum", "museum_gallery"),
        asp.fact("focus", "import"),
        asp.fact("import_theme", "import"),
        asp.fact("tight_budget", "museum_gallery"),
        asp.fact("budget_low", "museum_gallery"),
        asp.fact("poultry_present", "museum_gallery"),
        asp.fact("magic_on", "museum_gallery"),
        asp.fact("teamwork_on", "museum_gallery"),
        asp.fact("curiosity_on", "museum_gallery"),
    ]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("museum_gallery", "import")}
    if clingo_set == python_set:
        print("OK: clingo gate matches Python gate (1 combo).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reason_gate(params: StoryParams) -> None:
    if params.place != "museum_gallery":
        raise StoryError("This world only tells museum gallery stories.")
    if params.focus not in {"import", "budget", "poultry"}:
        raise StoryError("Focus must be import, budget, or poultry.")
    if not params.magic or not params.teamwork or not params.curiosity:
        raise StoryError("This tale needs magic, teamwork, and curiosity all at once.")


def build_world(params: StoryParams) -> World:
    reason_gate(params)
    world = World(Gallery())
    curator = world.add(Entity(
        id="Curator", kind="character", type=params.curator_type, label="curator",
        meters={"budget": 5}, memes={"pride": 1, "worry": 0}
    ))
    child = world.add(Entity(
        id=params.name, kind="character", type=params.child_type, label=params.name,
        memes={"curiosity": 2, "delight": 1}
    ))
    crate = world.add(Entity(
        id="Crate", type="thing", label="import crate",
        phrase="a heavy imported crate with brass corners",
        caretaker=curator.id, meters={"weight": 3, "sealed": 1}
    ))
    poultry = world.add(Entity(
        id="Poultry", type="thing", label="poultry figure",
        phrase="a feathered poultry display piece",
        meters={"shiny": 1}, memes={"oddity": 2}
    ))
    magic_lantern = world.add(Entity(
        id="Lantern", type="thing", label="magic lantern",
        phrase="a little lantern that glowed like a trapped sunrise",
        meters={"spark": 2}, memes={"magic": 2}
    ))
    world.facts.update(curator=curator, child=child, crate=crate, poultry=poultry, lantern=magic_lantern)
    return world


def narrate_setup(world: World) -> None:
    c = world.get("Curator")
    child = next(e for e in world.entities.values() if e.id != "Curator" and e.kind == "character")
    world.say(
        f"In the museum gallery, the curator kept a careful eye on a small budget, "
        f"for the walls were full of grand old pictures and the floor was full of echoes."
    )
    world.say(
        f"Then {child.id}, a child with a nose for wonder, tiptoed in and noticed a strange import crate "
        f"that had arrived with a tag tied on it like a dangling star."
    )
    world.para()
    world.say(
        f"{child.id} loved curiosity as other children loved candy, and {child.pronoun('subject')} "
        f"wanted to know what could be worth so much care in a place that was always watching its pennies."
    )
    c.add_e("worry", 1)
    c.add_e("duty", 1)


def trigger_magic(world: World) -> None:
    curator = world.get("Curator")
    child = next(e for e in world.entities.values() if e.id != "Curator" and e.kind == "character")
    crate = world.get("Crate")
    poultry = world.get("Poultry")
    lantern = world.get("Lantern")

    world.say(
        f"The child leaned closer, and the magic lantern flickered once, then twice, as if it had heard the gallery breathing."
    )
    child.add_e("curiosity", 1)
    child.add_e("boldness", 1)
    lantern.add_m("spark", 1)
    crate.add_m("sealed", -1)
    poultry.add_e("oddity", 1)
    curator.add_e("worry", 2)
    curator.add_m("budget", -2)

    world.say(
        f"With a pop like a corn kernel in a kettle, the import crate sprang open and out waddled a poultry figure, "
        f"bright as a painted barn door."
    )
    world.say(
        f"The curator gasped, because the budget was already thin and a runaway poultry display could knock over more than paper bills."
    )


def teamwork_turn(world: World) -> None:
    curator = world.get("Curator")
    child = next(e for e in world.entities.values() if e.id != "Curator" and e.kind == "character")
    poultry = world.get("Poultry")
    lantern = world.get("Lantern")

    world.para()
    world.say(
        f"{child.id} did not bolt. {child.pronoun('subject').capitalize()} stayed put, then pointed at the birdlike marvel and said, "
        f'"Let me help. We can steady it before it tippy-taps into the statues."'
    )
    child.add_e("teamwork", 2)
    curator.add_e("hope", 1)
    curator.add_e("worry", -1)

    world.say(
        f"So the two of them worked like a violin duet. One held the crate door, the other guided the feathered showpiece, "
        f"and the magic lantern kept shining just enough to calm the room."
    )
    poultry.add_m("steady", 1)
    lantern.add_m("spark", -1)
    curator.add_m("budget", 1)
    curator.add_e("pride", 2)


def resolution(world: World) -> None:
    curator = world.get("Curator")
    child = next(e for e in world.entities.values() if e.id != "Curator" and e.kind == "character")
    poultry = world.get("Poultry")

    world.para()
    world.say(
        f"At last the poultry figure stood straight on its little display base, and the curator found that the budget had not gone hungry after all."
    )
    world.say(
        f"{child.id} grinned from ear to ear, because curiosity had led to trouble, but teamwork had led to the fix."
    )
    world.say(
        f"The gallery looked taller somehow, as if the pictures on the walls had leaned closer to listen to the tale."
    )
    curator.add_e("relief", 2)
    child.add_e("joy", 2)
    poultry.add_m("displayed", 1)
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    trigger_magic(world)
    teamwork_turn(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Registries and QA
# ---------------------------------------------------------------------------

NAMES = ["Mina", "Toby", "Ivy", "Junie", "Hank", "Pippa"]
TRAITS = ["curious", "brave", "cheerful", "spry"]

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story about a museum gallery, an import crate, and a little poultry surprise.',
        'Tell a child-friendly story where curiosity meets a tight budget, then magic and teamwork set things right.',
        f'Write a museum-gallery adventure that includes the words "import", "budgetary", and "poultry".',
    ]

def story_qa(world: World) -> list[QAItem]:
    child = next(e for e in world.entities.values() if e.kind == "character" and e.id != "Curator")
    curator = world.get("Curator")
    return [
        QAItem(
            question=f"Who was curious in the museum gallery?",
            answer=f"{child.id} was curious, and {child.pronoun('subject')} helped turn the trouble into a safe success."
        ),
        QAItem(
            question="Why was the curator worried?",
            answer="The curator was worried because the gallery had a tight budget and an imported crate opened to reveal a lively poultry figure."
        ),
        QAItem(
            question="How was the problem solved?",
            answer="The problem was solved by teamwork, with the child steadying the display while the curator managed the crate and the magic lantern calmed the room."
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a museum gallery?",
            answer="A museum gallery is a room where art, objects, and displays are shown for people to look at and learn from."
        ),
        QAItem(
            question="What does it mean to import something?",
            answer="To import something means to bring it from another place, often across a border or from far away."
        ),
        QAItem(
            question="Why can a budget matter?",
            answer="A budget matters because it is the amount of money you have to spend, so you must choose carefully."
        ),
        QAItem(
            question="Why can teamwork help?",
            answer="Teamwork helps because people can use their different skills together to fix a problem faster and better."
        ),
        QAItem(
            question="What does curiosity do in a story?",
            answer="Curiosity makes someone ask questions and explore, which can lead to discovery and adventure."
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can make surprising things happen, like a lantern glimmering or a crate opening in an unexpected way."
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: museum gallery, import, budgetary poultry, magic, teamwork, curiosity.")
    ap.add_argument("--place", default="museum_gallery")
    ap.add_argument("--focus", choices=["import", "budget", "poultry"])
    ap.add_argument("--name", choices=NAMES)
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
    return StoryParams(
        place=args.place or "museum_gallery",
        focus=args.focus or rng.choice(["import", "budget", "poultry"]),
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        child_type="girl" if rng.random() < 0.5 else "boy",
        curator_type="curator",
        magic=True,
        teamwork=True,
        curiosity=True,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combos:")
        for p, f in stories:
            print(f"  {p} / {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        params_list = [
            StoryParams(name="Mina"),
            StoryParams(name="Toby", focus="budget"),
            StoryParams(name="Ivy", focus="poultry"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
