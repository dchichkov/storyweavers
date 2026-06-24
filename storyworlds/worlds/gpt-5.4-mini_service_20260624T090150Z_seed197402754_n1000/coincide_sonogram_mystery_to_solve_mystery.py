#!/usr/bin/env python3
"""
Story world: a small mystery to solve, where a child notices that two clues
coincide and a sonogram helps reveal the answer.

Seed-tale inspiration:
- A child hears a strange clue.
- A grown-up worries and looks for patterns.
- Two separate observations coincide.
- A sonogram becomes the helpful tool.
- The mystery is solved, and the child feels reassured.
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
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.type in {"parents", "siblings", "children"}


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    details: str


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    phrase: str
    reveal: str
    reason: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, clue: Clue):
        self.place = place
        self.clue = clue
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

PLACES = {
    "clinic": Place(
        id="clinic",
        label="the clinic",
        indoors=True,
        details="The waiting room smelled clean, and the hallway was quiet.",
    ),
    "home": Place(
        id="home",
        label="the living room",
        indoors=True,
        details="A lamp glowed softly beside a little table with paper cups.",
    ),
    "hospital": Place(
        id="hospital",
        label="the hospital",
        indoors=True,
        details="The lights were bright, but the room felt calm and still.",
    ),
}

CLUES = {
    "beep": Clue(
        id="beep",
        label="a tiny beep",
        kind="sound",
        phrase="a tiny beep from a machine",
        reveal="the machine was checking a heartbeat",
        reason="the beep and the sonogram both pointed to the same healthy answer",
    ),
    "bump": Clue(
        id="bump",
        label="a little bump",
        kind="shape",
        phrase="a little bump under the cloth",
        reveal="the bump was only a tucked blanket corner",
        reason="the shape and the sonogram both matched the blanket, not a problem",
    ),
    "glow": Clue(
        id="glow",
        label="a soft glow",
        kind="light",
        phrase="a soft glow on the screen",
        reveal="the glow was a clear picture of a baby waving",
        reason="the glow and the sonogram matched the same tiny baby picture",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Luna", "Theo"]
TRAITS = ["curious", "quiet", "brave", "gentle", "careful", "bright"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

class Need:
    def __init__(self) -> None:
        self.mystery = 0.0
        self.worry = 0.0
        self.relief = 0.0
        self.curiosity = 0.0
        self.coincide = 0.0


def setup_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    world = World(PLACES[params.place], CLUES[params.clue])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"stillness": 1.0},
        memes={"curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="Mom" if params.parent_type == "mother" else "Dad",
        meters={"care": 1.0},
        memes={"worry": 1.0},
    ))
    sonogram = world.add(Entity(
        id="Sonogram",
        kind="thing",
        type="sonogram",
        label="sonogram",
        phrase="a sonogram picture",
        owner=parent.id,
        used_by=parent.id,
        meters={"power": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, sonogram=sonogram)
    return world


def _intro(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue
    place = world.place

    world.say(
        f"{hero.label} was a {random.choice(TRAITS)} little {hero.type} who liked noticing small things."
    )
    world.say(
        f"One day, {hero.label} and {parent.label} went to {place.label}. {place.details}"
    )
    world.say(
        f"Then they heard {clue.phrase}, and that made the room feel like a mystery."
    )


def _investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue
    sonogram: Entity = world.facts["sonogram"]  # type: ignore[assignment]

    hero.memes["curiosity"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{hero.label} leaned in and asked what was going on. {parent.label} looked worried, but kind."
    )
    world.say(
        f"{parent.label} said, 'Let's solve this together.' Then {parent.pronoun('subject')} used the sonogram."
    )
    world.say(
        f"The sonogram showed a clear picture, and that clue helped them think."
    )
    world.facts["coincide"] = True
    world.facts["sonogram_used"] = sonogram.id
    world.facts["clue"] = clue.id


def _turn(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue

    world.say(
        f"Then two things coincided: the strange clue and the sonogram picture matched each other."
    )
    world.say(
        f"That coincidence made the mystery smaller, not bigger."
    )
    world.say(
        f"{parent.label} smiled and explained that {clue.reveal}."
    )
    hero.memes["curiosity"] += 1
    parent.memes["worry"] = max(0.0, parent.memes["worry"] - 1.0)
    world.facts["solved"] = True


def _resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue

    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1.0
    world.say(
        f"In the end, the mystery was solved, and {hero.label} felt brave again."
    )
    world.say(
        f"{hero.label} looked at the sonogram and the old clue and saw how they belonged to the same answer."
    )
    world.say(
        f"The little room felt calm, because the strange thing had turned out to be safe."
    )


def tell_story(world: World) -> None:
    _intro(world)
    world.para()
    _investigate(world)
    world.para()
    _turn(world)
    world.para()
    _resolution(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue
    return [
        f"Write a short mystery story for a small child about {hero.label}, {parent.label}, and a sonogram.",
        f"Tell a gentle story where a clue and a sonogram coincide and help solve a mystery.",
        f"Write a child-friendly story set at {world.place.label} that ends with the mystery solved.",
        f"Make a simple story using the words coincide and sonogram in a reassuring way.",
        f"Create a mystery-to-solve story where the grown-up explains the answer kindly after checking the sonogram.",
        f"Write a calm story about {clue.label} becoming understandable once the sonogram is used.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Clue = world.clue
    place = world.place

    return [
        QAItem(
            question=f"Who went to {place.label} in the story?",
            answer=f"{hero.label} and {parent.label} went to {place.label} together.",
        ),
        QAItem(
            question=f"What made the day feel like a mystery?",
            answer=f"{clue.phrase} made the day feel like a mystery.",
        ),
        QAItem(
            question="What tool helped solve the mystery?",
            answer="The sonogram helped solve the mystery by showing a clear picture.",
        ),
        QAItem(
            question="What did it mean when the clue and the sonogram coincided?",
            answer="It meant they matched and pointed to the same answer.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the mystery solved and {hero.label} feeling calm and brave again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sonogram?",
            answer="A sonogram is a picture made with sound waves that helps doctors look inside the body in a safe way.",
        ),
        QAItem(
            question="What does it mean when two things coincide?",
            answer="When two things coincide, they happen together or match each other closely.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs careful thinking to solve.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
parent(P) :- parent_name(P).
place(X) :- place_name(X).
clue(C) :- clue_name(C).
tool(sonogram).

mystery_to_solve(H, C, T) :- hero(H), clue(C), tool(T).
coincide(H, C, T) :- mystery_to_solve(H, C, T), clue_matches_tool(C, T).
solved(H) :- coincide(H, _, _).

#show mystery_to_solve/3.
#show coincide/3.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    hero: Entity = world_placeholder()["hero"]  # type: ignore[index]
    parent: Entity = world_placeholder()["parent"]  # type: ignore[index]
    place: Place = world_placeholder()["place"]  # type: ignore[index]
    clue: Clue = world_placeholder()["clue"]  # type: ignore[index]
    lines = [
        asp.fact("hero_name", hero.id),
        asp.fact("parent_name", parent.id),
        asp.fact("place_name", place.id),
        asp.fact("clue_name", clue.id),
        asp.fact("clue_matches_tool", clue.id, "sonogram"),
    ]
    return "\n".join(lines)


def world_placeholder() -> dict[str, object]:
    # Used only by asp_facts() to keep the structure simple and local.
    return {
        "hero": Entity(id="Child", kind="character", type="girl", label="Child"),
        "parent": Entity(id="Parent", kind="character", type="mother", label="Mom"),
        "place": PLACES["clinic"],
        "clue": CLUES["beep"],
    }


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    atoms = set((sym.name, tuple(getattr(a, "number", getattr(a, "string", a.name)) for a in sym.arguments)) for sym in model)
    expected = {("mystery_to_solve", ("Child", "beep", "sonogram")), ("coincide", ("Child", "beep", "sonogram")), ("solved", ("Child",))}
    if atoms == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH:")
    print("  asp atoms:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("Hero type must be girl or boy.")
    if params.parent_type not in {"mother", "father"}:
        raise StoryError("Parent type must be mother or father.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    parent_type = args.parent or ("mother" if hero_type == "girl" else "father")
    hero_name = args.name or rng.choice(CHILD_NAMES)
    params = StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
    )
    validate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    return "\n".join([
        "--- trace ---",
        f"place={world.place.id}",
        f"clue={world.clue.id}",
        f"hero.memes={hero.memes}",
        f"parent.memes={parent.memes}",
        f"facts={world.facts}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="clinic", clue="beep", hero_name="Mia", hero_type="girl", parent_type="mother"),
    StoryParams(place="home", clue="bump", hero_name="Leo", hero_type="boy", parent_type="father"),
    StoryParams(place="hospital", clue="glow", hero_name="Nora", hero_type="girl", parent_type="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery-to-solve storyworld with a sonogram and a coincidence.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_to_solve/3.\n#show coincide/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print(asp_program("#show mystery_to_solve/3.\n#show coincide/3.\n#show solved/1."))
        return

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
            header = f"### {p.hero_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
