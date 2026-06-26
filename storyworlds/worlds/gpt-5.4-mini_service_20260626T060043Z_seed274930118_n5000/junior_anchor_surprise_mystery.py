#!/usr/bin/env python3
"""
A small story world for a junior dock mystery with an anchor surprise.

Seed premise:
- A junior helper at the harbor expects a routine errand.
- An anchor turns up in a surprising place.
- The child follows clues, feels a little spooked, and solves the mystery.

The world keeps a light mystery tone with a concrete surprise twist.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("weight", "noise", "wet", "dusty", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "surprise", "confidence"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    surfaces: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)
    clue_words: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    surprise: str
    weight: float = 1.0


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_bits: list[str] = []

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place(
        id="harbor",
        label="the harbor",
        surfaces={"dock", "pier", "crate"},
        hides={"crate", "tarp", "rope_heap"},
        clue_words={"salt", "rope", "tide"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the boathouse",
        surfaces={"floor", "bench", "rack"},
        hides={"bench", "net", "locker"},
        clue_words={"wood", "net", "locker"},
    ),
    "lighthouse": Place(
        id="lighthouse",
        label="the lighthouse",
        surfaces={"stairs", "landing", "table"},
        hides={"table", "rug", "cupboard"},
        clue_words={"light", "stairs", "brass"},
    ),
}

CLUES = {
    "rope": Clue(
        id="rope",
        label="a coil of rope",
        phrase="a coil of rope with a fresh knot",
        points_to="harbor",
        surprise="under a crate",
        weight=1.0,
    ),
    "brass": Clue(
        id="brass",
        label="a brass shine",
        phrase="a brass shine on the floor",
        points_to="lighthouse",
        surprise="under a rug",
        weight=1.0,
    ),
    "net": Clue(
        id="net",
        label="a torn net",
        phrase="a torn net with a loose thread",
        points_to="boathouse",
        surprise="behind a bench",
        weight=1.0,
    ),
}

HELPER_TYPES = ["captain", "dockhand", "keeper"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            if clue.points_to == place_id:
                out.append((place_id, clue_id))
    return out


def reasonableness_gate(place_id: str, clue_id: str) -> bool:
    return (place_id, clue_id) in valid_combos()


def explain_rejection(place_id: str, clue_id: str) -> str:
    place = PLACES[place_id]
    clue = CLUES[clue_id]
    return (
        f"(No story: {clue.label} does not belong with {place.label} here; "
        f"the clue points to {PLACES[clue.points_to].label}, so this mystery would not make sense.)"
    )


def pick_surprise(place: Place, clue: Clue) -> str:
    return clue.surprise if clue.points_to == place.id else "somewhere else"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small junior anchor mystery with a surprising clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--helper", choices=HELPER_TYPES, dest="helper_type")
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
    if args.place and args.clue and not reasonableness_gate(args.place, args.clue):
        raise StoryError(explain_rejection(args.place, args.clue))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid mystery combination matches the given options.)")

    place_id, clue_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Toby", "Lia", "Nico", "Pia", "Ezra"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(
        place=place_id,
        clue=clue_id,
        hero_name=name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def predict(world: World, clue: Clue) -> dict[str, bool]:
    sim = world.copy()
    helper = sim.get("helper")
    clue_ent = sim.get("clue")
    helper.memes["curiosity"] += 1
    clue_ent.meters["found"] = 1
    helper.memes["surprise"] += 1
    return {"found": True, "surprising": clue_ent.hidden_in is not None}


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type))
    anchor = world.add(Entity(
        id="anchor",
        kind="thing",
        type="anchor",
        label="anchor",
        phrase="a heavy anchor",
        owner="boat",
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        phrase=clue.phrase,
        hidden_in=clue.surprise,
    ))

    # Act 1: setup
    world.say(
        f"Junior {params.hero_name} liked quiet mornings at {place.label}, where even "
        f"small sounds felt like clues."
    )
    world.say(
        f"{params.hero_name} worked with a {params.helper_type} who said the harbor "
        f"always had a story if you looked closely."
    )
    world.para()

    # Act 2: mystery and surprise
    hero.memes["curiosity"] += 1
    world.say(
        f"That day, {params.hero_name} noticed {clue.phrase} {clue.surprise}."
    )
    world.say(
        f"It was strange, because everyone expected a simple visit, not a hidden hint."
    )
    if clue.points_to == place.id:
        helper.memes["surprise"] += 1
        helper.memes["curiosity"] += 1
        world.say(
            f"The clue made {params.hero_name} look again at {place.label}, and the surprise "
            f"felt bigger than the tide."
        )
        world.say(
            f"Then {params.hero_name} found the anchor tucked nearby, waiting like it had been "
            f"put there on purpose."
        )
        anchor.carried_by = hero.id
        anchor.meters["weight"] = 1.0
        anchor.memes["confidence"] += 1
    else:
        raise StoryError(explain_rejection(params.place, params.clue))

    world.para()

    # Act 3: resolution
    hero.memes["confidence"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{params.hero_name} and the {params.helper_type} followed the clue back to the boat, "
        f"where the anchor belonged."
    )
    world.say(
        f"The mystery was small, but it changed the whole morning: what seemed like a puzzle "
        f"turned into a clear answer."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        clue=clue,
        anchor=anchor,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA / prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f"Write a short mystery for a child named {params.hero_name} at {place.label} with an anchor surprise.",
        f"Tell a gentle story where junior {params.hero_name} finds {clue.phrase} and discovers why the anchor is there.",
        f"Write a simple mystery ending where the clue leads to the anchor and the morning makes sense again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the junior helper in the story?",
            answer=f"The junior helper is {params.hero_name}, who is a little {params.hero_type} at {place.label}.",
        ),
        QAItem(
            question=f"What surprising clue did {params.hero_name} find?",
            answer=f"{params.hero_name} found {clue.phrase}, and it was hidden {clue.surprise}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=(
                f"{params.hero_name} and the {params.helper_type} followed the clue back to the boat, "
                f"and they found the anchor where it belonged."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is an anchor for?",
            answer="An anchor is a heavy object that helps hold a boat in place so it does not drift away.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what is really going on.",
        ),
    ]
    if place.id == "harbor":
        out.append(QAItem(
            question="What is a harbor?",
            answer="A harbor is a safe place near the water where boats can stop, dock, and rest.",
        ))
    if clue.id == "brass":
        out.append(QAItem(
            question="What is brass?",
            answer="Brass is a shiny metal often used for things like knobs, bells, and old tools.",
        ))
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- spot(P).
clue(C) :- clue_id(C).
compatible(P,C) :- clue_points(C,P).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("spot", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("clue_points", cid, clue.points_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

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
    StoryParams(place="harbor", clue="rope", hero_name="Mina", hero_type="girl", helper_type="dockhand"),
    StoryParams(place="boathouse", clue="net", hero_name="Toby", hero_type="boy", helper_type="keeper"),
    StoryParams(place="lighthouse", clue="brass", hero_name="Lia", hero_type="girl", helper_type="captain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible place/clue combos:\n")
        for p, c in combos:
            print(f"  {p:10} {c}")
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
