#!/usr/bin/env python3
"""
storyworlds/worlds/soybean_fight_reconciliation_detective_story.py
===================================================================

A small detective-story world built from the seed words "soybean" and "fight",
with reconciliation as the turn and resolution.

Premise:
- A child detective notices a missing soybean item or a soybean-related clue.
- Two characters argue or fight over a misunderstanding.
- The detective follows physical clues and emotional traces to uncover the truth.
- Reconciliation restores trust, and the final image shows the repaired bond.

The world keeps the state tiny and classical:
- typed entities with meters and memes
- state-driven narration
- a simple reasonableness gate
- inline ASP twin for parity checking
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

# -----------------------------------------------------------------------------
# Core domain constants
# -----------------------------------------------------------------------------

THRESHOLD = 1.0

LOCATIONS = {
    "kitchen": "the kitchen",
    "garden": "the garden",
    "market": "the little market",
    "shed": "the shed",
}

CLUES = {
    "soybean": "soybeans",
    "pod": "soybean pods",
    "sauce": "soybean sauce",
}

ROLES = ["detective", "friend", "sister", "brother", "neighbor"]

TRAITS = ["careful", "curious", "brave", "patient", "quick-thinking", "kind"]

NAMES = ["Mina", "Leo", "Tara", "Noah", "Pia", "Owen", "Luna", "Eli"]


# -----------------------------------------------------------------------------
# Entities and world model
# -----------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("dust", "lost", "clue", "ruined"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "anger", "hurt", "curiosity", "trust", "relief", "guilt"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "mother", "woman"}
        male = {"boy", "brother", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    location: str
    clue: str
    suspect_a: str
    suspect_b: str
    reconciliation_way: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# -----------------------------------------------------------------------------
# ASP twin: facts and rules
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A case is valid when the clue exists, the setting is valid, and the conflict can
% be reconciled by one of the available repair methods.
valid_case(Location, Clue, Reconciliation) :-
    location(Location), clue(Clue), reconciliation(Reconciliation).

#show valid_case/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    lines.append(asp.fact("reconciliation", "apology"))
    lines.append(asp.fact("reconciliation", "shared_search"))
    lines.append(asp.fact("reconciliation", "returned_item"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_case/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_case")))


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------

def valid_cases() -> list[tuple[str, str, str]]:
    return [
        (loc, clue, rec)
        for loc in LOCATIONS
        for clue in CLUES
        for rec in ("apology", "shared_search", "returned_item")
    ]


def explain_rejection(location: str, clue: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not fit the detective scene at {location}. "
        f"Try one of: {', '.join(CLUES)}.)"
    )


# -----------------------------------------------------------------------------
# Story helpers
# -----------------------------------------------------------------------------

def _add_emotion(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _detective_scent_detects(world: World, detective: Entity, clue: Entity) -> None:
    _add_emotion(detective, "curiosity", 1.0)
    _add_meter(clue, "clue", 1.0)
    world.trace.append(f"{detective.id} notices the soybean clue.")


def _fight_erupts(world: World, a: Entity, b: Entity) -> None:
    _add_emotion(a, "anger", 1.0)
    _add_emotion(b, "anger", 1.0)
    _add_emotion(a, "hurt", 1.0)
    _add_emotion(b, "hurt", 1.0)
    world.trace.append("A fight starts over the missing soybean item.")


def _reconcile(world: World, detective: Entity, a: Entity, b: Entity, clue: Entity, way: str) -> None:
    _add_emotion(a, "trust", 1.0)
    _add_emotion(b, "trust", 1.0)
    _add_emotion(a, "relief", 1.0)
    _add_emotion(b, "relief", 1.0)
    a.memes["anger"] = 0.0
    b.memes["anger"] = 0.0
    world.trace.append(f"Reconciliation happens through {way}.")
    if way == "returned_item":
        clue.carried_by = None
    elif way == "shared_search":
        clue.carried_by = detective.id


def build_scene(rng: random.Random, location: Optional[str] = None, clue: Optional[str] = None) -> Scene:
    location = location or rng.choice(list(LOCATIONS))
    clue = clue or rng.choice(list(CLUES))
    return Scene(
        location=location,
        clue=clue,
        suspect_a="A",
        suspect_b="B",
        reconciliation_way=rng.choice(["apology", "shared_search", "returned_item"]),
    )


def tell(scene: Scene, hero_name: str, hero_type: str, hero_trait: str, suspect_a_name: str, suspect_b_name: str) -> World:
    world = World(scene)

    detective = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    a = world.add(Entity(id=suspect_a_name, kind="character", type="boy"))
    b = world.add(Entity(id=suspect_b_name, kind="character", type="girl"))
    clue = world.add(Entity(id="soybean_clue", kind="thing", type="soybean", label=scene.clue, phrase=f"a {scene.clue}", caretaker=hero_name))

    clue.carried_by = a.id

    # Act 1: setup
    world.say(
        f"{detective.id} was a {hero_trait} little detective who loved solving small mysteries."
    )
    world.say(
        f"One morning at {LOCATIONS[scene.location]}, {detective.id} noticed a missing {scene.clue} clue and decided to follow it."
    )

    # Act 2: tension
    world.para()
    _detective_scent_detects(world, detective, clue)
    world.say(
        f"{a.id} and {b.id} both wanted the same soybean snack, and their argument turned into a fight."
    )
    _fight_erupts(world, a, b)
    world.say(
        f"{detective.id} looked carefully at the trail, because the clue pointed to {a.id}'s hands."
    )

    # Act 3: reconciliation
    world.para()
    _reconcile(world, detective, a, b, clue, scene.reconciliation_way)
    if scene.reconciliation_way == "apology":
        world.say(
            f"{a.id} apologized first, and {b.id} said sorry too. The two friends stopped fighting and shared the soybean snack."
        )
    elif scene.reconciliation_way == "shared_search":
        world.say(
            f"{detective.id} asked them to search together, and they found the soybean clue under a box. Working side by side made the fight fade away."
        )
    else:
        world.say(
            f"{a.id} gave back the soybean snack, and {b.id} smiled. Once the snack was returned, the fight ended and the room felt calm again."
        )

    world.say(
        f"In the end, {detective.id} saw {a.id} and {b.id} sit together, quiet and safe, with the soybean clue back where it belonged."
    )

    world.facts.update(
        detective=detective,
        suspect_a=a,
        suspect_b=b,
        clue=clue,
        scene=scene,
        hero_trait=hero_trait,
        resolved=True,
    )
    return world


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

LOCATIONS_LIST = list(LOCATIONS.keys())

CURATED = [
    ("kitchen", "soybean", "apology"),
    ("garden", "pod", "shared_search"),
    ("market", "sauce", "returned_item"),
]


@dataclass
class StoryParams:
    location: str
    clue: str
    reconciliation: str
    name: str
    role: str
    trait: str
    other_a: str
    other_b: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes the word "{f["clue"].label}".',
        f"Tell a small mystery story where {f['detective'].id} sees a fight and helps everyone reconcile.",
        f"Write a gentle detective story set in {LOCATIONS[f['scene'].location']] if False else LOCATIONS[f['scene'].location]} about a soybean clue and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    a: Entity = f["suspect_a"]
    b: Entity = f["suspect_b"]
    clue: Entity = f["clue"]
    scene: Scene = f["scene"]

    return [
        QAItem(
            question=f"Who solved the mystery in the {LOCATIONS[scene.location]}?",
            answer=f"{det.id} solved it by following the soybean clue and calming the fight.",
        ),
        QAItem(
            question=f"What caused the fight between {a.id} and {b.id}?",
            answer=f"They both wanted the soybean snack, and the argument grew into a fight.",
        ),
        QAItem(
            question=f"How did the story end after the reconciliation?",
            answer=f"{a.id} and {b.id} made up, the soybean clue was back in the right place, and the room felt peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a soybean?",
            answer="A soybean is a small bean that people can cook and eat, and it can be turned into foods like soy sauce or tofu.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a fight, usually by saying sorry, sharing, or understanding each other better.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.extend(world.trace)
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Parameters and generation
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    location: str
    clue: str
    reconciliation: str
    name: str
    role: str
    trait: str
    other_a: str
    other_b: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with soybean, fight, and reconciliation.")
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--reconciliation", choices=["apology", "shared_search", "returned_item"])
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["detective"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--other-a")
    ap.add_argument("--other-b")
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
    if args.location and args.clue and (args.location, args.clue, args.reconciliation or "apology") not in [
        (loc, clue, rec) for loc in LOCATIONS for clue in CLUES for rec in ("apology", "shared_search", "returned_item")
    ]:
        raise StoryError(explain_rejection(args.location, args.clue))

    location = args.location or rng.choice(list(LOCATIONS))
    clue = args.clue or rng.choice(list(CLUES))
    reconciliation = args.reconciliation or rng.choice(["apology", "shared_search", "returned_item"])
    name = args.name or rng.choice(NAMES)
    role = args.role or "detective"
    trait = args.trait or rng.choice(TRAITS)
    other_a = args.other_a or rng.choice([n for n in NAMES if n != name])
    other_b = args.other_b or rng.choice([n for n in NAMES if n not in {name, other_a}])

    return StoryParams(
        location=location,
        clue=clue,
        reconciliation=reconciliation,
        name=name,
        role=role,
        trait=trait,
        other_a=other_a,
        other_b=other_b,
    )


def generate(params: StoryParams) -> StorySample:
    scene = Scene(
        location=params.location,
        clue=params.clue,
        suspect_a=params.reconciliation,
        suspect_b=params.reconciliation,
        reconciliation_way=params.reconciliation,
    )
    world = World(scene)
    world = tell(
        scene=scene,
        hero_name=params.name,
        hero_type=params.role,
        hero_trait=params.trait,
        suspect_a_name=params.other_a,
        suspect_b_name=params.other_b,
    )
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


# -----------------------------------------------------------------------------
# ASP verification
# -----------------------------------------------------------------------------

def asp_verify() -> int:
    import asp

    clingo_set = set(asp_valid_cases())
    python_set = set(valid_cases())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} cases).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in Python:", sorted(python_set - clingo_set))
    return 1


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        cases = asp_valid_cases()
        print(f"{len(cases)} valid cases")
        for case in cases:
            print(case)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for loc, clue, rec in CURATED:
            p = StoryParams(
                location=loc,
                clue=clue,
                reconciliation=rec,
                name="Mina",
                role="detective",
                trait="curious",
                other_a="Jin",
                other_b="Aya",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
