#!/usr/bin/env python3
"""
A standalone storyworld for a small adventure about a stylus, a pensive totem,
and a moral choice that lands with a little humor.

The world is intentionally small and constraint-checked:
- a hero travels to a place
- a curious totem is found there
- a stylus is used to write or draw
- the hero faces a gentle moral test
- humor helps resolve the tension
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    carrier: Optional[str] = None
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


@dataclass
class Place:
    name: str
    mood: str
    has_to tem: bool = False
    has_stylus: bool = False
    adventure_tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
    "ruins": Place(
        name="the old river ruins",
        mood="windy",
        has_totem=True,
        has_stylus=True,
        adventure_tags={"stone", "echo", "map"},
    ),
    "grove": Place(
        name="the mossy grove",
        mood="quiet",
        has_totem=True,
        has_stylus=True,
        adventure_tags={"tree", "trail", "bird"},
    ),
    "cave": Place(
        name="the bright cave",
        mood="echoing",
        has_totem=True,
        has_stylus=True,
        adventure_tags={"torch", "spark", "stone"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lina", "Ada", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Noah", "Theo"]
COMPANIONS = ["fox", "sparrow", "dog", "rabbit"]


@dataclass
class Totem:
    label: str = "totem"
    phrase: str = "a pensive totem with a sleepy carved face"
    mood: str = "pensive"
    age: str = "ancient"
    hidden_value: str = "kindness"


@dataclass
class Stylus:
    label: str = "stylus"
    phrase: str = "a little stylus with a smooth tip"
    material: str = "bone"
    uses: str = "writing and tracing"


TOTEM = Totem()
STYLUS = Stylus()


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def hero_pronouns(gender: str) -> dict[str, str]:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}
    return {"subject": "he", "object": "him", "possessive": "his"}


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a curious young {params.gender}",
        meters={"travel": 0.0, "care": 0.0, "pride": 0.0},
        memes={"wonder": 1.0, "pensive": 0.0, "joy": 0.0, "moral_value": 0.0, "humor": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion,
        label=f"the {params.companion}",
        phrase=f"a small {params.companion} who liked to follow along",
        meters={"travel": 0.0},
        memes={"trust": 1.0},
    ))
    totem = world.add(Entity(
        id="totem",
        kind="thing",
        type="totem",
        label="totem",
        phrase=TOTEM.phrase,
        owner=None,
        carrier=None,
        meters={"stillness": 1.0},
        memes={"pensive": 1.0, "secret": 1.0},
    ))
    stylus = world.add(Entity(
        id="stylus",
        kind="thing",
        type="stylus",
        label="stylus",
        phrase=STYLUS.phrase,
        owner=params.name,
        carrier=params.name,
        meters={"sharpness": 1.0},
    ))

    p = hero_pronouns(params.gender)

    # Act I: setup
    world.say(
        f"{hero.label} set out for {place.name} with {companion.label}. "
        f"The day felt like a small adventure, the kind with stones underfoot and a big sky overhead."
    )
    world.say(
        f"At the center of the path stood {totem.phrase}. "
        f"It looked pensive, as if it had been thinking for a hundred quiet years."
    )
    world.say(
        f"{hero.label} also carried {stylus.phrase}, because {p['subject']} liked to mark maps, names, and little clues."
    )
    hero.meters["travel"] += 1.0
    companion.meters["travel"] += 1.0

    # Act II: tension
    world.para()
    world.say(
        f"Beside the totem lay a fallen sign that had been scratched into pieces. "
        f"{hero.label} saw that the path ahead was hard to read."
    )
    hero.memes["pensive"] += 1.0
    world.say(
        f"{p['subject'].capitalize()} could use the stylus to copy the old symbols, "
        f"but {p['subject']} also noticed a basket of fresh trail marks nearby that belonged to no one."
    )
    world.say(
        f"The choice was plain: copy the clues honestly, or take the easy marks and pretend they were found first."
    )

    # Act III: moral turn with humor
    world.para()
    hero.memes["moral_value"] += 1.0
    if params.place == "ruins":
        world.say(
            f"{hero.label} chose the honest way. {p['subject'].capitalize()} knelt by the totem and copied the true symbols with the stylus, "
            f"even though the wind kept trying to steal the page."
        )
    elif params.place == "grove":
        world.say(
            f"{hero.label} chose the honest way. {p['subject'].capitalize()} copied the real trail clues from the pensive totem, "
            f"while the fox watched with a very serious face."
        )
    else:
        world.say(
            f"{hero.label} chose the honest way. {p['subject'].capitalize()} copied the real path marks from the totem, "
            f"and the cave answered with one dramatic echo after another."
        )
    hero.memes["humor"] += 1.0
    companion.memes["trust"] += 1.0
    hero.meters["care"] += 1.0
    world.say(
        f"When {hero.label} finished, the {params.companion} sneezed at the ink and startled itself. "
        f"The silly little sneeze broke the tension, and {hero.label} laughed."
    )
    world.say(
        f"The totem seemed less lonely after that, as if it approved of the choice. "
        f"The path was clear, the stylus was still safe, and the adventure could go on without a stolen shortcut."
    )

    world.facts = {
        "hero": hero,
        "companion": companion,
        "totem": totem,
        "stylus": stylus,
        "place": place,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    return [
        f'Write a short adventure story for a small child about a {hero.type} who finds a pensive totem at {place.name}.',
        f'Tell a gentle moral story using the words "stylus", "pensive", and "totem", with a little humor and a brave ending.',
        f'Write a simple tale where a child uses a stylus to make an honest choice on an adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    place = world.facts["place"]
    p = hero.pronoun()
    return [
        QAItem(
            question="What did the child carry on the adventure?",
            answer="The child carried a stylus, which was used for writing and tracing clues.",
        ),
        QAItem(
            question=f"What kind of thing was waiting at {place.name}?",
            answer="A pensive totem was waiting there, with a sleepy carved face and a quiet, thoughtful mood.",
        ),
        QAItem(
            question="What honest choice did the child make?",
            answer="The child chose to copy the real clues instead of taking an easy shortcut, so the adventure stayed fair.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with laughter after {companion.label} sneezed at the ink, and the child felt proud for doing the right thing.",
        ),
        QAItem(
            question="Why did the child feel proud?",
            answer="The child felt proud because the stylus was used for an honest job, not for cheating.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stylus?",
            answer="A stylus is a small pointed tool for writing, drawing, or tracing marks.",
        ),
        QAItem(
            question="What does pensive mean?",
            answer="Pensive means quiet and thoughtful, like someone or something that seems to be thinking deeply.",
        ),
        QAItem(
            question="What is a totem?",
            answer="A totem is a carved object that can stand for a place, a family, or an important idea.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- chosen(H,_).
place(P) :- chosen(_,P).
totem_at(P) :- place(P), has_totem(P).
stylus_at(P) :- place(P), has_stylus(P).

adventure(H,P) :- chosen(H,P), totem_at(P), stylus_at(P).
moral_value(H) :- honest_choice(H).
humor(H) :- funny_moment(H).

#show adventure/2.
#show moral_value/1.
#show humor/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("chosen_place", pid))
        if place.has_totem:
            lines.append(asp.fact("has_totem", pid))
        if place.has_stylus:
            lines.append(asp.fact("has_stylus", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show adventure/2. #show moral_value/1. #show humor/1."))
    atoms = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    ok = True
    expected_any = any(p.has_totem and p.has_stylus for p in PLACES.values())
    if expected_any and not any(name == "adventure" for name, _ in atoms):
        ok = False
    if ok:
        print("OK: ASP reasoning gate is reachable and consistent.")
        return 0
    print("MISMATCH: ASP gate did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Selection / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a stylus, a pensive totem, and moral humor.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    place = args.place or rng.choice(list(PLACES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, name=name, gender=gender, companion=companion)


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show adventure/2. #show moral_value/1. #show humor/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure/2. #show moral_value/1. #show humor/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for gender in ["girl", "boy"]:
                params = StoryParams(
                    place=place,
                    name=(GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0]),
                    gender=gender,
                    companion=COMPANIONS[0],
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
