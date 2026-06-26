#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trauma_bad_ending_conflict_space_adventure.py
================================================================================

A small, standalone storyworld about a space adventure that turns into a
conflict-heavy bad ending shaped by trauma.

Premise:
- A young crew member boards a tiny ship for a simple delivery mission.
- A stray event in space reminds them of a painful past loss.
- Fear and conflict grow until the mission goes wrong.
- The ending proves the world changed: the cargo is lost, the ship is damaged,
  and the crew member must live with the scare instead of a neat victory.

This world stays child-facing and concrete while still allowing trauma as an
emotional state in the model.
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
# Entities and world state
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    crewmate: str
    cargo: str
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orbit": "the moon orbit",
    "asteroid_belt": "the asteroid belt",
    "deep_space": "deep space",
    "station_dock": "the station dock",
}

CARGO = {
    "star_map": ("a shiny star map", "star map", "torso"),
    "medicine": ("a little box of medicine", "medicine box", "hands"),
    "repair_kit": ("a small repair kit", "repair kit", "hands"),
}

NAMES_GIRL = ["Mira", "Luna", "Tia", "Nia", "Ari", "Zoe"]
NAMES_BOY = ["Finn", "Oren", "Kai", "Jett", "Leo", "Milo"]
CREWMATES = ["captain", "pilot", "engineer", "navigator"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"fuel": 0.0, "damage": 0.0},
        memes={"joy": 0.0, "fear": 0.0, "trauma": 0.0, "conflict": 0.0},
    ))
    crew = world.add(Entity(
        id="Crewmate",
        kind="character",
        type="person",
        label=params.crewmate,
        meters={"stress": 0.0},
        memes={"patience": 1.0, "conflict": 0.0},
    ))
    cargo_label, cargo_phrase, cargo_region = CARGO[params.cargo]
    cargo = world.add(Entity(
        id="Cargo",
        type=params.cargo,
        label=cargo_label,
        phrase=cargo_phrase,
        owner=hero.id,
        caretaker=crew.id,
        worn_by=hero.id,
        meters={"safe": 1.0, "lost": 0.0},
    ))

    world.facts.update(hero=hero, crew=crew, cargo=cargo, cargo_region=cargo_region)
    return world


def predict_panic(world: World) -> bool:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    hero.memes["fear"] += 1.0
    hero.memes["trauma"] += 1.0
    return hero.memes["trauma"] >= 1.0


def tell(world: World) -> World:
    hero = world.facts["hero"]
    crew = world.facts["crew"]
    cargo = world.facts["cargo"]
    cargo_label = cargo.label

    world.say(f"{hero.id} was a little {hero.type} on a tiny ship with a bright window.")
    world.say(f"{hero.id} loved the quiet hum of the engines and the promise of {cargo_label} delivery.")
    world.say(f"{hero.id}'s {crew.label} had packed {cargo.phrase} carefully for the trip.")

    world.para()
    world.say(f"Then the ship drifted into {world.place}, where the stars looked close enough to touch.")
    world.say(f"A sharp crack rang through the hull, and the sound brought back a bad memory for {hero.id}.")
    world.say(f"{hero.id} remembered the old day when something in space had gone wrong, and fear rushed in fast.")
    hero.memes["fear"] += 1.0
    hero.memes["trauma"] += 1.0
    crew.memes["conflict"] += 1.0
    crew.meters["stress"] += 1.0

    world.say(f"{hero.id} wanted to hide and hold still, but the {crew.label} needed help right away.")
    world.say(f'"Keep moving," the {crew.label} said, but {hero.id} heard the words like a push instead of a hug.')
    hero.memes["conflict"] += 1.0

    world.para()
    world.say(f"{hero.id} tried to reach for the cargo latch, but {hero.id} was shaking too much.")
    world.say(f"The box slipped, bumped the panel, and slid away in the low gravity.")
    cargo.meters["safe"] -= 1.0
    cargo.meters["lost"] += 1.0
    hero.meters["damage"] += 1.0
    crew.meters["stress"] += 1.0

    world.say(f"The little ship spun once, then steadied, but the cargo was gone and the mission was ruined.")
    world.say(f"{hero.id} sat very still, staring at the dark window, while the {crew.label} fixed the broken latch alone.")
    world.say(f"In the end, there was no happy landing, only a quiet ride back and a heavy feeling in {hero.pronoun('possessive')} chest.")

    world.facts.update(
        trauma=True,
        bad_ending=True,
        conflict=True,
        lost_cargo=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    cargo = world.facts["cargo"]
    crew = world.facts["crew"]
    return [
        f"Write a short space adventure for a young child where {hero.id} travels with {cargo.label} and feels scared after a loud event.",
        f"Tell a story about a small ship, a worried {crew.label}, and a child who remembers a painful space scare.",
        f"Write a simple tale with stars, conflict, and a bad ending where a cargo delivery goes wrong because fear takes over.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    crew = world.facts["crew"]
    cargo = world.facts["cargo"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was about {hero.id}, a little {hero.type} on a tiny ship.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to deliver?",
            answer=f"{hero.id} was trying to deliver {cargo.phrase} safely.",
        ),
        QAItem(
            question=f"Why did the trip turn tense?",
            answer=f"The trip turned tense because a sharp sound in space brought back trauma for {hero.id}, and that fear led to conflict with the {crew.label}.",
        ),
        QAItem(
            question=f"What happened to the cargo at the end?",
            answer=f"The cargo slipped away and was lost, so the mission ended badly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is space like?",
            answer="Space is huge, dark, and full of stars, planets, and quiet floating things.",
        ),
        QAItem(
            question="What does a spaceship do?",
            answer="A spaceship carries people or cargo through space from one place to another.",
        ),
        QAItem(
            question="What does trauma mean?",
            answer="Trauma is a very upsetting experience that can leave someone feeling scared again when they remember it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe the chosen story pieces.
hero(H) :- hero_fact(H).
crew(C) :- crew_fact(C).
cargo(K) :- cargo_fact(K).

% A trauma story is valid when a loud space event causes fear and conflict.
trauma_story(H) :- trauma_fact(H), fear_fact(H), conflict_fact(H).

% The ending is a bad ending when cargo is lost.
bad_ending :- lost_cargo_fact.

#show trauma_story/1.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hero_fact", "hero"),
        asp.fact("crew_fact", "crew"),
        asp.fact("cargo_fact", "cargo"),
        asp.fact("trauma_fact", "hero"),
        asp.fact("fear_fact", "hero"),
        asp.fact("conflict_fact", "hero"),
        asp.fact("lost_cargo_fact"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show trauma_story/1. #show bad_ending/0."))
    trauma = bool(asp.atoms(model, "trauma_story"))
    bad = bool(asp.atoms(model, "bad_ending"))
    if trauma and bad:
        print("OK: ASP twin recognizes the trauma conflict bad-ending story.")
        return 0
    print("MISMATCH: ASP twin failed to recognize the story pattern.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class ParamChoices:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure trauma storyworld with a bad ending.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crewmate", choices=CREWMATES)
    ap.add_argument("--cargo", choices=list(CARGO))
    ap.add_argument("--place", choices=list(PLACES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    return StoryParams(
        name=args.name or rng.choice(name_pool),
        gender=gender,
        crewmate=args.crewmate or rng.choice(CREWMATES),
        cargo=args.cargo or rng.choice(list(CARGO)),
        place=args.place or rng.choice(list(PLACES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    StoryParams(name="Mira", gender="girl", crewmate="captain", cargo="star_map", place="deep_space"),
    StoryParams(name="Finn", gender="boy", crewmate="engineer", cargo="repair_kit", place="asteroid_belt"),
    StoryParams(name="Luna", gender="girl", crewmate="navigator", cargo="medicine", place="orbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show trauma_story/1. #show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show trauma_story/1. #show bad_ending/0."))
        print("ASP model:", asp.atoms(model, "trauma_story"), asp.atoms(model, "bad_ending"))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
