#!/usr/bin/env python3
"""
storyworlds/worlds/bureau_socket_attitudinal_twist_bravery_cautionary_animal.py
==============================================================================

A small animal-story world about a curious animal, a bureau, and a socket.

Premise:
- An animal wants to investigate something tucked near a bureau.
- A socket nearby makes the situation risky.
- A cautionary warning creates tension.
- A brave, careful twist in attitude leads to a safe resolution.

The story is designed to feel like a compact Animal Story:
small creature, clear warning, a brave choice, and a gentle ending image.

World model:
- Animals and objects are typed entities with physical meters and emotional memes.
- The physical risk comes from proximity to the socket.
- The emotional turn is an attitudinal shift from curiosity/impulse toward bravery/caution.
- The narrated resolution proves what changed in the world state.

ASP twin:
- A Python reasonableness gate and inline ASP_RULES mirror each other.
- Facts are emitted from registries via asp_facts().
- --verify checks Python/ASP parity and runs a small story exercise.

"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
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
    near_socket: bool = False
    movable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("reach", "risk", "distance", "care", "safety"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "bravery", "caution", "worry", "relief", "attitude"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "kitten", "girl", "mother", "mom"}
        male = {"dog", "puppy", "boy", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Objective:
    id: str
    label: str
    phrase: str
    risk_source: str
    safer_tool: str
    involves_twist: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", affords={"inspect"}),
    "living_room": Setting(place="the living room", affords={"inspect"}),
    "hallway": Setting(place="the hallway", affords={"inspect"}),
}

OBJECTIVES = {
    "toy": Objective(
        id="toy",
        label="toy mouse",
        phrase="a little toy mouse",
        risk_source="socket",
        safer_tool="stick",
        involves_twist=True,
    ),
    "string": Objective(
        id="string",
        label="string ribbon",
        phrase="a bright string ribbon",
        risk_source="socket",
        safer_tool="tongs",
        involves_twist=True,
    ),
    "ball": Objective(
        id="ball",
        label="ball",
        phrase="a bouncy ball",
        risk_source="socket",
        safer_tool="net",
        involves_twist=False,
    ),
}

ANIMAL_NAMES = {
    "cat": ["Milo", "Pip", "Toby", "Nina", "Luna", "Coco"],
    "dog": ["Rex", "Benny", "Mabel", "Tilly", "Otis", "Sunny"],
    "rabbit": ["Poppy", "Junie", "Basil", "Pearl", "Faye", "Nori"],
}

TRAITS = ["curious", "small", "spry", "gentle", "bold"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    animal: str
    name: str
    objective: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(O) :- objective(O), near_socket(O).
safe_fix(O) :- objective(O), tool(T), uses(T, O), cautious(T).
valid_story(P, A, O) :- setting(P), animal(A), objective(O), affords(P, inspect), risk(O), safe_fix(O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", sid, act))
    for oid, obj in OBJECTIVES.items():
        lines.append(asp.fact("objective", oid))
        lines.append(asp.fact("near_socket", oid))
        lines.append(asp.fact("uses", obj.safer_tool, oid))
        lines.append(asp.fact("cautious", obj.safer_tool))
    for animal in ANIMAL_NAMES:
        lines.append(asp.fact("animal", animal))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def objective_needs_caution(obj: Objective) -> bool:
    return obj.risk_source == "socket" and obj.safer_tool in {"stick", "tongs", "net"}

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "inspect" not in setting.affords:
            continue
        for animal in ANIMAL_NAMES:
            for oid, obj in OBJECTIVES.items():
                if objective_needs_caution(obj):
                    combos.append((place, animal, oid))
    return combos


# ---------------------------------------------------------------------------
# Narration and mechanics
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    animal = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        owner=None,
    ))
    socket = world.add(Entity(
        id="socket",
        kind="thing",
        type="socket",
        label="wall socket",
        phrase="the wall socket",
        near_socket=True,
    ))
    objective = world.add(Entity(
        id=params.objective,
        kind="thing",
        type=params.objective,
        label=OBJECTIVES[params.objective].label,
        phrase=OBJECTIVES[params.objective].phrase,
        owner=params.name,
        caretaker=params.name,
        movable=True,
    ))
    tool = world.add(Entity(
        id=OBJECTIVES[params.objective].safer_tool,
        kind="thing",
        type="tool",
        label=OBJECTIVES[params.objective].safer_tool,
        phrase=f"a careful {OBJECTIVES[params.objective].safer_tool}",
        owner=params.name,
        movable=True,
    ))
    world.facts.update(animal=animal, socket=socket, objective=objective, tool=tool)
    return world

def danger_score(world: World, animal: Entity, objective: Entity) -> float:
    return 1.0 if objective.near_socket or objective.id in OBJECTIVES else 0.0

def simulate_risk(world: World, animal: Entity, objective: Entity) -> None:
    if danger_score(world, animal, objective) >= THRESHOLD:
        animal.memes["worry"] += 1
        objective.meters["distance"] = 0.0

def safe_twist(world: World, animal: Entity, objective: Entity, tool: Entity) -> None:
    animal.memes["bravery"] += 1
    animal.memes["caution"] += 1
    animal.memes["attitude"] += 1
    animal.meters["reach"] += 1
    objective.meters["distance"] += 1
    tool.meters["safety"] += 1

def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    animal = world.get(params.name)
    objective = world.get(params.objective)
    tool = world.get(OBJECTIVES[params.objective].safer_tool)
    place = world.setting.place

    # Act 1: setup
    world.say(
        f"In {place}, {animal.id} was a little {animal.type} with a very curious heart."
    )
    world.say(
        f"{animal.pronoun().capitalize()} kept looking at {objective.phrase} near the {world.facts['socket'].label}."
    )
    world.para()

    # Act 2: cautionary warning
    simulate_risk(world, animal, objective)
    animal.memes["curiosity"] += 1
    animal.memes["attitude"] -= 1
    world.say(
        f"Then {animal.id} saw the {world.facts['socket'].label} beside it and paused."
    )
    world.say(
        f'"Careful," said a grown-up. "A socket is not a toy, and that spot is too close."'
    )
    world.say(
        f"{animal.id} wanted to go closer, but {animal.pronoun('possessive')} ears flattened as {animal.id} listened."
    )
    world.para()

    # Act 3: brave caution and twist
    safe_twist(world, animal, objective, tool)
    world.say(
        f"{animal.id} took a brave breath, found a {tool.label}, and used it with a careful twist."
    )
    world.say(
        f"With that safe trick, {animal.id} nudged the {objective.label} away from the socket."
    )
    animal.memes["worry"] = 0.0
    animal.memes["relief"] += 1
    objective.meters["distance"] += 1.0
    world.say(
        f"In the end, {animal.id} sat back with a calm, new attitude, and the little {objective.label} stayed safely far from the wall."
    )

    world.facts.update(
        danger=animal.memes["worry"] > 0,
        resolved=True,
        tool=tool,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    objective = f["objective"]
    return [
        f'Write a short Animal Story about a curious {animal.type} named {animal.id} who notices a {objective.label} near a bureau and a socket.',
        f'Tell a gentle story where {animal.id} must use bravery and caution to move a {objective.label} away from danger.',
        f'Write a simple story with a cautionary warning, a brave twist, and a happy ending image involving a bureau socket scene.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal = f["animal"]
    objective = f["objective"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {animal.id} want to do in {world.setting.place}?",
            answer=f"{animal.id} wanted to inspect {objective.phrase} and see what was behind it.",
        ),
        QAItem(
            question=f"Why did the grown-up warn {animal.id}?",
            answer=f"The grown-up warned {animal.id} because the wall socket was too close, and sockets are not safe toys.",
        ),
        QAItem(
            question=f"How did {animal.id} solve the problem in the end?",
            answer=f"{animal.id} used {tool.phrase} with a careful twist and bravely moved the {objective.label} away from the socket.",
        ),
        QAItem(
            question=f"How did {animal.id} feel at the end?",
            answer=f"{animal.id} felt brave, careful, and relieved after choosing a safer way to play.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bureau?",
            answer="A bureau is a piece of furniture with drawers that people use to keep clothes or small things.",
        ),
        QAItem(
            question="What is a socket?",
            answer="A socket is a place in the wall where electricity comes out for lamps and other things.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and paying attention so something unsafe does not happen.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while still trying to do the right thing.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning movement, like turning a tool or turning your body carefully.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing" and e.near_socket:
            bits.append("near_socket=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verify
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a bureau, a socket, and a cautious brave twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMAL_NAMES)
    ap.add_argument("--name")
    ap.add_argument("--objective", choices=OBJECTIVES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.animal is None or c[1] == args.animal)
              and (args.objective is None or c[2] == args.objective)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, animal, objective = rng.choice(sorted(combos))
    name = args.name or rng.choice(ANIMAL_NAMES[animal])
    return StoryParams(place=place, animal=animal, name=name, objective=objective)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="nursery", animal="cat", name="Milo", objective="toy"),
    StoryParams(place="living_room", animal="rabbit", name="Poppy", objective="string"),
    StoryParams(place="hallway", animal="dog", name="Rex", objective="ball"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.animal} in {p.place} (objective: {p.objective})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
