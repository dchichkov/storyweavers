#!/usr/bin/env python3
"""
Standalone story world: Ghost Story with a gazelle, a dour mood, and a visit
that turns on curiosity, surprise, and dialogue.

Premise seed:
- A gazelle hears something strange and goes to attend a quiet place.
- The place feels dour and spooky at first.
- Curiosity leads the gazelle to speak with a ghost.
- Surprise changes the mood, and dialogue resolves the fear.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

MOOD_KEYS = {"dour", "curious", "surprised", "calm", "brave"}

# ---------------------------------------------------------------------------
# Shared typed entity model with meters and memes
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

    def __post_init__(self) -> None:
        for k in list(self.meters):
            self.meters[k] = float(self.meters[k])
        for k in list(self.memes):
            self.memes[k] = float(self.memes[k])

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "gazelle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_people(self) -> bool:
        return self.kind in {"character", "ghost"}


@dataclass
class Place:
    label: str
    setting: str
    eerie: bool = True
    sounds: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str = "old chapel"
    name: str = "Gala"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "old chapel": Place(
        label="an old chapel",
        setting="old chapel",
        eerie=True,
        sounds=["wind in the beams", "a slow creak", "a whisper in the dark"],
    ),
    "moonlit garden": Place(
        label="a moonlit garden",
        setting="moonlit garden",
        eerie=True,
        sounds=["leaves tapping softly", "a faraway owl", "grass rustling"],
    ),
    "attic room": Place(
        label="an attic room",
        setting="attic room",
        eerie=True,
        sounds=["a box shifting", "dust stirring", "boards sighing"],
    ),
}

GHOST_NAMES = ["Moss", "Pale", "Wisp", "Murmur"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------


def _p(world: World, text: str) -> None:
    world.say(text)


def introduce(world: World, gazelle: Entity, ghost: Entity) -> None:
    _p(
        world,
        f"{gazelle.id} was a gazelle with a dour little frown and a very bright mind."
        f" One evening, {gazelle.pronoun('subject')} went to attend {world.place.label},"
        f" because {gazelle.pronoun('subject')} had heard a strange sound."
    )
    world.facts["gazelle"] = gazelle
    world.facts["ghost"] = ghost


def haunt(world: World, ghost: Entity) -> None:
    ghost.meters["near"] = ghost.meters.get("near", 0.0) + 1.0
    ghost.memes["quiet"] = ghost.memes.get("quiet", 0.0) + 1.0
    _p(
        world,
        f"In the dark, {ghost.id} waited by the wall, soft as a candle's smoke."
    )


def feel_dour(world: World, gazelle: Entity) -> None:
    gazelle.memes["dour"] = gazelle.memes.get("dour", 0.0) + 1.0
    _p(
        world,
        f"The room felt dour and still. {gazelle.id}'s ears tipped forward, trying to"
        f" catch every small sound."
    )


def curiosity_rises(world: World, gazelle: Entity) -> None:
    gazelle.memes["curious"] = gazelle.memes.get("curious", 0.0) + 1.0
    _p(
        world,
        f"Still, curiosity tickled {gazelle.id} more than fear. {gazelle.pronoun('subject').capitalize()}"
        f" took one careful step closer."
    )


def dialogue(world: World, gazelle: Entity, ghost: Entity) -> None:
    gazelle.meters["distance"] = 0.0
    ghost.meters["distance"] = 0.0
    gazelle.memes["heard_voice"] = gazelle.memes.get("heard_voice", 0.0) + 1.0
    ghost.memes["heard_voice"] = ghost.memes.get("heard_voice", 0.0) + 1.0
    _p(
        world,
        f'"Who are you?" asked {gazelle.id}.'
        f' "A lonely ghost," said {ghost.id}, "and I attend this place so it does not feel empty."'
    )


def surprise_turn(world: World, gazelle: Entity, ghost: Entity) -> None:
    gazelle.memes["surprised"] = gazelle.memes.get("surprised", 0.0) + 1.0
    ghost.memes["surprised"] = ghost.memes.get("surprised", 0.0) + 1.0
    gazelle.memes["brave"] = gazelle.memes.get("brave", 0.0) + 1.0
    _p(
        world,
        f"{gazelle.id} blinked in surprise. The ghost was not hungry or mean at all;"
        f" {ghost.id} was only lonely."
    )


def ending(world: World, gazelle: Entity, ghost: Entity) -> None:
    gazelle.memes["calm"] = gazelle.memes.get("calm", 0.0) + 1.0
    ghost.memes["calm"] = ghost.memes.get("calm", 0.0) + 1.0
    _p(
        world,
        f"So {gazelle.id} stayed and talked with {ghost.id} until the room no longer"
        f" felt dour. At the end, the dark place felt smaller, and the night felt kind."
    )


# ---------------------------------------------------------------------------
# World assembly
# ---------------------------------------------------------------------------


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    place = PLACES[params.place]
    world = World(place)

    gazelle = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="gazelle",
            label="gazelle",
            meters={"distance": 3.0},
            memes={"dour": 1.0},
        )
    )
    ghost_name = random.choice(GHOST_NAMES)
    ghost = world.add(
        Entity(
            id=ghost_name,
            kind="ghost",
            type="ghost",
            label="ghost",
            meters={"distance": 2.0},
            memes={"quiet": 1.0},
        )
    )

    introduce(world, gazelle, ghost)
    world.para()
    haunt(world, ghost)
    feel_dour(world, gazelle)
    curiosity_rises(world, gazelle)
    dialogue(world, gazelle, ghost)
    surprise_turn(world, gazelle, ghost)
    ending(world, gazelle, ghost)

    world.facts.update(place=place, gazelle=gazelle, ghost=ghost)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    g = world.facts["gazelle"]
    ghost = world.facts["ghost"]
    return [
        f"Write a gentle ghost story about a gazelle named {g.id} who attends {p.label}.",
        f"Tell a short story where curiosity leads {g.id} to speak with a ghost named {ghost.id}.",
        f"Write a spooky-but-kind story with surprise and dialogue in {p.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    gazelle: Entity = world.facts["gazelle"]
    ghost: Entity = world.facts["ghost"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who attended {place.label} in the story?",
            answer=f"The gazelle named {gazelle.id} attended {place.label} because it heard something strange.",
        ),
        QAItem(
            question=f"Why did {gazelle.id} keep walking toward the dark place?",
            answer=f"{gazelle.id} stayed curious, even though the room felt dour, so it moved closer to learn what was there.",
        ),
        QAItem(
            question=f"What surprised {gazelle.id} about {ghost.id}?",
            answer=f"{gazelle.id} learned that {ghost.id} was lonely, not scary, and that was a surprise.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {gazelle.id} and {ghost.id} talking kindly so the place no longer felt dour.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more and look closer.",
        ),
        QAItem(
            question="What is surprise?",
            answer="Surprise is the feeling you get when something happens that you did not expect.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking back and forth between two or more characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
gazelle(G) :- gazelle_name(G).
ghost(H) :- ghost_name(H).
place(P) :- place_name(P).

curious(G) :- gazelle(G), meme(G, curious, V), V >= 1.
dour(G) :- gazelle(G), meme(G, dour, V), V >= 1.
surprised(G) :- gazelle(G), meme(G, surprised, V), V >= 1.
calm(G) :- gazelle(G), meme(G, calm, V), V >= 1.

attend(G,P) :- gazelle(G), place(P), attends(G,P).
meet(G,H) :- gazelle(G), ghost(H), dialogue(G,H).
resolved(G,H) :- meet(G,H), calm(G), calm(H), surprised(G).
#show resolved/2.
#show curious/1.
#show dour/1.
#show surprised/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_name", pid))
    for name in GHOST_NAMES:
        lines.append(asp.fact("ghost_name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program("#show resolved/2.\n#show curious/1.\n#show dour/1.\n#show surprised/1."))
    atoms = set()
    for sym in model:
        if sym.name in {"resolved", "curious", "dour", "surprised"}:
            atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    if atoms:
        print("OK: ASP program grounded and produced atoms.")
        return 0
    print("MISMATCH: ASP program produced no atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost Story world with a gazelle, dour mood, curiosity, surprise, and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(["Gala", "Nia", "Roo", "Tavi", "Luma"])
    return StoryParams(place=place, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="old chapel", name="Gala"),
    StoryParams(place="moonlit garden", name="Roo"),
    StoryParams(place="attic room", name="Luma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP unavailable: {exc}") from exc
        model = asp.one_model(asp_program("#show resolved/2.\n#show curious/1.\n#show dour/1.\n#show surprised/1."))
        print("ASP model atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
