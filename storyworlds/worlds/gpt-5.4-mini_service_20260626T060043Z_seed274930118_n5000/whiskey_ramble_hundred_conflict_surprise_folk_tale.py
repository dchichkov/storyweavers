#!/usr/bin/env python3
"""
A standalone folk-tale storyworld about a shared flask, a long ramble, and a
small village dispute that turns on a surprising gift.

The tale premise:
- In a little hamlet, a weary traveler carries a flask of whiskey for a hundred
  old stones.
- A river crossing and a moonlit argument create conflict.
- A surprise solution reveals the flask was meant to be shared, not hoarded.

This script models physical state in meters and emotional state in memes.
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
# Core domain
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "grandfather", "traveler"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    weather: str = "clear"
    paths: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    traveler_type: str
    host_type: str
    flask: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hamlet": Place(name="the hamlet", weather="clear", paths={"lane", "bridge"}),
    "bridge": Place(name="the old bridge", weather="windy", paths={"bridge"}),
    "oak": Place(name="the oak grove", weather="misty", paths={"lane", "grove"}),
}

TRAVELER_NAMES = ["Mara", "Tobin", "Nell", "Oren", "Ivy", "Bram"]
HOST_NAMES = ["Gran", "Edda", "Pip", "Hollis", "Wren", "Mabel"]

TRAVELER_TYPES = {
    "girl": "girl",
    "boy": "boy",
    "woman": "woman",
    "man": "man",
    "traveler": "traveler",
}

HOST_TYPES = {
    "woman": "woman",
    "man": "man",
    "grandmother": "grandmother",
    "grandfather": "grandfather",
    "keeper": "keeper",
}

FLASKS = {
    "whiskey": {
        "label": "whiskey",
        "phrase": "a small flask of whiskey",
        "drink": "shared by the fire",
    }
}

# Folk-tale flavored valid combos: all supported, but story turns on conflict.
VALID_COMBOS = [(p, t, h, f) for p in PLACES for t in TRAVELER_TYPES for h in HOST_TYPES for f in FLASKS]


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def intro_line(world: World, traveler: Entity, host: Entity, flask: Entity) -> None:
    world.say(
        f"Long ago, in {world.place.name}, there lived {host.id}, who kept a warm hearth, "
        f"and {traveler.id}, who could ramble down any lane without losing the thread of a song."
    )
    world.say(
        f"{traveler.id} carried {article(flask.phrase)} {flask.label} wrapped in cloth, "
        f"for in those days a little whiskey was prized like winter fire."
    )


def ramble_line(world: World, traveler: Entity) -> None:
    traveler.memes["wanderlust"] = traveler.memes.get("wanderlust", 0) + 1
    world.say(
        f"Each morning {traveler.id} would ramble beyond the cart tracks, listening for crows, "
        f"rivers, and rumors."
    )


def hundred_line(world: World) -> None:
    world.say(
        f"At the edge of the lane stood a ring of hundred stones, old as a grandmother's tale, "
        f"and every stone had a crack for rain to sing through."
    )


def conflict_line(world: World, traveler: Entity, host: Entity, flask: Entity) -> None:
    traveler.memes["conflict"] = traveler.memes.get("conflict", 0) + 1
    host.memes["worry"] = host.memes.get("worry", 0) + 1
    world.say(
        f"One windy evening, {host.id} saw the flask and frowned. "
        f"\"That whiskey should not be kept for one pair of hands,\" {host.pronoun()} said."
    )
    world.say(
        f"{traveler.id} drew back, for {traveler.pronoun('possessive')} heart had grown tight with want, "
        f"and the two began to argue beside the hundred stones."
    )


def surprise_line(world: World, traveler: Entity, host: Entity, flask: Entity) -> None:
    traveler.memes["surprise"] = traveler.memes.get("surprise", 0) + 1
    host.memes["surprise"] = host.memes.get("surprise", 0) + 1
    world.say(
        f"Then came a surprise: the cloth around the flask had a second knot, and inside it was a tiny note "
        f"from the old miller saying, 'Pour it only when the path is shared.'"
    )
    world.say(
        f"At that, {traveler.id} looked up, and {host.id} laughed a soft laugh, because the whiskey had been meant "
        f"for company all along."
    )


def resolution_line(world: World, traveler: Entity, host: Entity, flask: Entity) -> None:
    traveler.memes["conflict"] = 0
    traveler.memes["joy"] = traveler.memes.get("joy", 0) + 1
    host.memes["joy"] = host.memes.get("joy", 0) + 1
    flask.carried_by = None
    world.say(
        f"So {traveler.id} poured a little whiskey into two cups, and the bitterness between them melted like frost."
    )
    world.say(
        f"They sat by the hearth of {world.place.name}, and by the end of the night the hundred stones seemed to wait "
        f"outside like silent witnesses to a kinder tale."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    traveler = world.add(Entity(
        id=TRAVELER_NAMES[0] if params.traveler_type == "traveler" else TRAVELER_NAMES[1],
        kind="character",
        type=params.traveler_type,
    ))
    host = world.add(Entity(
        id=HOST_NAMES[0] if params.host_type == "keeper" else HOST_NAMES[1],
        kind="character",
        type=params.host_type,
    ))
    flask = world.add(Entity(
        id=params.flask,
        type="thing",
        label="whiskey",
        phrase="a small flask of whiskey",
        owner=traveler.id,
        carried_by=traveler.id,
    ))

    world.facts.update(
        traveler=traveler,
        host=host,
        flask=flask,
        place=place,
        params=params,
    )

    intro_line(world, traveler, host, flask)
    world.para()
    ramble_line(world, traveler)
    hundred_line(world)
    conflict_line(world, traveler, host, flask)
    world.para()
    surprise_line(world, traveler, host, flask)
    resolution_line(world, traveler, host, flask)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale about whiskey, a long ramble, and a hundred old stones.',
        f"Tell a gentle story set in {world.place.name} where two people argue, then discover a surprising reason to share a flask.",
        "Write a child-friendly tale in which a small conflict becomes a kind ending after a surprise note is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler: Entity = f["traveler"]
    host: Entity = f["host"]
    qa = [
        QAItem(
            question=f"Who carried the whiskey at the start of the story?",
            answer=f"{traveler.id} carried the whiskey wrapped in cloth.",
        ),
        QAItem(
            question=f"What did {traveler.id} like to do each morning?",
            answer=f"{traveler.id} liked to ramble beyond the cart tracks and listen for stories in the wind.",
        ),
        QAItem(
            question="Why did the argument begin?",
            answer=f"{host.id} worried that the whiskey should be shared, not kept for one pair of hands.",
        ),
        QAItem(
            question="What was surprising about the flask?",
            answer="There was a second knot in the cloth and a note saying the whiskey was meant to be shared.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They poured a little whiskey into two cups and the conflict faded away.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is whiskey?",
            answer="Whiskey is a strong drink made from grain and aged for grown-up tables and fireside talks.",
        ),
        QAItem(
            question="What does it mean to ramble?",
            answer="To ramble means to walk or speak in a wandering way, taking a long path or a winding story.",
        ),
        QAItem(
            question="What does hundred mean?",
            answer="Hundred means one more than ninety-nine, and it is a large number of things.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the characters uneasy until they find a way through it.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think or do.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P). traveler(T). host(H). flask(F). whiskey(F).
% A conflict exists when the traveler keeps the flask and the host objects.
conflict(T,H,F) :- traveler(T), host(H), whiskey(F).

% Surprise arises when the hidden note is found.
surprise(F) :- whiskey(F).

% Resolution happens when the drink is shared.
resolved(T,H,F) :- conflict(T,H,F), surprise(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TRAVELER_TYPES:
        lines.append(asp.fact("traveler", t))
    for h in HOST_TYPES:
        lines.append(asp.fact("host", h))
    for f in FLASKS:
        lines.append(asp.fact("whiskey", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show conflict/3. #show surprise/1. #show resolved/3."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("conflict", 3), ("surprise", 1), ("resolved", 3)}
    if atoms != expected:
        print("MISMATCH between ASP and Python story logic")
        print("  asp:", sorted(atoms))
        print("  expected:", sorted(expected))
        return 1
    print("OK: ASP twin is present and solvable.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    return list(VALID_COMBOS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: whiskey, ramble, hundred.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--traveler-type", choices=TRAVELER_TYPES)
    ap.add_argument("--host-type", choices=HOST_TYPES)
    ap.add_argument("--flask", choices=FLASKS)
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
    place = args.place or rng.choice(list(PLACES))
    traveler_type = args.traveler_type or rng.choice(list(TRAVELER_TYPES))
    host_type = args.host_type or rng.choice(list(HOST_TYPES))
    flask = args.flask or "whiskey"
    if flask not in FLASKS:
        raise StoryError("This folk tale only knows one flask: whiskey.")
    return StoryParams(place=place, traveler_type=traveler_type, host_type=host_type, flask=flask)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"WQ: {item.question}")
            print(f"WA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/3. #show surprise/1. #show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, t, h, f in VALID_COMBOS[:5]:
            samples.append(generate(StoryParams(place=p, traveler_type=t, host_type=h, flask=f, seed=base_seed)))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### story {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
