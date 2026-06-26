#!/usr/bin/env python3
"""
Standalone storyworld: cobble blockade color reconciliation detective story.

A small detective-style domain about a child sleuth, a blocked cobble lane,
a missing color clue, and a reconciliation that clears the way.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_color: str
    blocked: bool
    clue: str
    block_reason: str
    resolution: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "laneway": Place(id="laneway", label="the cobble laneway", features={"cobble", "narrow"}),
    "market": Place(id="market", label="the market square", features={"cobble", "busy"}),
    "courtyard": Place(id="courtyard", label="the old courtyard", features={"cobble", "quiet"}),
}

COLORS = {
    "red": "red",
    "blue": "blue",
    "gold": "gold",
    "green": "green",
    "violet": "violet",
}

MYSTERIES = {
    "paint": Mystery(
        id="paint",
        missing_color="blue",
        blocked=True,
        clue="a blue fingerprint on a stone",
        block_reason="a crate blockade stacked across the cobble path",
        resolution="the neighbors moved the crates and shared the paint back",
    ),
    "poster": Mystery(
        id="poster",
        missing_color="gold",
        blocked=True,
        clue="a gold ribbon caught on a nail",
        block_reason="a pallet blockade outside the shop door",
        resolution="the shopkeeper and the neighbor reconciled and opened the way",
    ),
}

HERO_NAMES = ["Mina", "Theo", "Iris", "Noah", "Elsa", "Jun"]
ADJ = ["careful", "curious", "brave", "quiet", "bright", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the place has cobble, the case has a clue,
% and the blockade is not permanent.
solvable(P, M) :- place(P), mystery(M), cobble_place(P), clue(M), not permanent_blockade(M).

% Reconciliation is possible when both sides are willing and the blockade is social,
% not a locked gate.
reconciliation(M) :- mystery(M), willing_left(M), willing_right(M), not locked_blockade(M).

% A valid story needs both a solvable mystery and reconciliation.
valid(P, M) :- solvable(P, M), reconciliation(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "cobble" in place.features:
            lines.append(asp.fact("cobble_place", pid))
    for mid, mys in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid))
        if mys.blocked:
            lines.append(asp.fact("blocked", mid))
            lines.append(asp.fact("blockade", mid))
        lines.append(asp.fact("willing_left", mid))
        lines.append(asp.fact("willing_right", mid))
        if "locked" in mys.block_reason:
            lines.append(asp.fact("locked_blockade", mid))
        else:
            lines.append(asp.fact("permanent_blockade", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, m) for p, m in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        if "cobble" not in place.features:
            continue
        for mid, mys in MYSTERIES.items():
            if mys.blocked:
                out.append((place_id, mid))
    return out


def explain_rejection(place_id: str, mystery_id: str) -> str:
    return (
        f"(No story: {PLACES[place_id].label} and the {mystery_id} case do not make a coherent "
        f"cobble-blockade-color mystery with reconciliation.)"
    )


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    adjective: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mys = MYSTERIES[params.mystery]
    world = World(place=place)

    detective = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl" if params.hero in {"Mina", "Iris", "Elsa"} else "boy",
        label=params.hero,
        meters={"curiosity": 0.0, "distance": 0.0},
        memes={"wonder": 0.0, "resolve": 0.0},
    ))
    neighbor = world.add(Entity(
        id="neighbor",
        kind="character",
        type="adult",
        label="the neighbor",
        meters={"distance": 0.0},
        memes={"stubbornness": 0.0, "regret": 0.0, "goodwill": 0.0},
    ))
    painter = world.add(Entity(
        id="painter",
        kind="character",
        type="adult",
        label="the painter",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "goodwill": 0.0},
    ))
    crate = world.add(Entity(
        id="crate",
        type="thing",
        label="crate blockade",
        phrase="a tall crate blockade",
        location=place.id,
        meters={"height": 1.0, "blocking": 1.0},
    ))
    paint = world.add(Entity(
        id="paint",
        type="thing",
        label=f"{mys.missing_color} paint",
        phrase=f"a tin of {mys.missing_color} paint",
        owner="painter",
        carried_by=None,
        location="shop",
        meters={"amount": 1.0},
    ))

    world.facts.update(
        place=place,
        mystery=mys,
        detective=detective,
        neighbor=neighbor,
        painter=painter,
        crate=crate,
        paint=paint,
    )

    # Act 1
    world.say(
        f"{detective.label} was a {params.adjective} little detective who loved solving small town puzzles."
    )
    world.say(
        f"One morning, {detective.label} noticed that {place.label} had a {mys.block_reason}."
    )
    world.para()
    world.say(
        f"At the end of the path, there should have been {mys.clue}, but the way was blocked."
    )
    world.say(
        f"{detective.label} tucked a notebook under {detective.pronoun('possessive')} arm and followed the cobbles."
    )

    # Act 2
    detective.meters["curiosity"] += 1
    detective.memes["resolve"] += 1
    world.para()
    world.say(
        f"{detective.label} asked careful questions and found the missing {mys.missing_color} paint."
    )
    world.say(
        f"It turned out the neighbor had stacked the crates to keep the lane clear during a quarrel."
    )
    neighbor.memes["stubbornness"] += 1
    painter.memes["worry"] += 1
    world.say(
        f"The painter wanted the paint back, but the neighbor wanted the lane quiet."
    )
    world.say(
        f"{detective.label} saw that the blockade was not a locked one; it was a hurt-feelings blockade."
    )

    # Reconciliation turn
    world.para()
    detective.memes["wonder"] += 1
    neighbor.memes["regret"] += 1
    neighbor.memes["goodwill"] += 1
    painter.memes["goodwill"] += 1
    crate.meters["blocking"] = 0.0
    world.say(
        f"{detective.label} brought them together and named the problem plainly: the color was missing, and the path was blocked."
    )
    world.say(
        f"After a quiet apology, the neighbor and the painter chose reconciliation instead of more arguing."
    )
    world.say(
        f"They moved the crate blockade aside, shared the {mys.missing_color} paint, and found the clue at last."
    )

    # End
    world.para()
    world.say(
        f"By evening, {place.label} shone over the cobbles, the blockade was gone, and the {mys.missing_color} clue made sense."
    )
    world.say(
        f"{detective.label} closed the notebook with a smile, because the mystery had turned into peace."
    )
    world.facts["resolved"] = True
    return world


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        if (args.place, args.mystery) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.mystery))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    adjective = args.adjective or rng.choice(ADJ)
    return StoryParams(place=place, mystery=mystery, hero=hero, adjective=adjective)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short detective story about {params.hero} solving a cobble blockade mystery with a color clue.",
            f"Tell a child-friendly story where reconciliation clears a blocked cobble lane.",
            f"Write a gentle mystery story featuring {params.hero}, color, and a blockade on the cobbles.",
        ],
        story_qa=[
            QAItem(
                question=f"What kind of place was blocked in the story?",
                answer=f"It was {world.place.label}, a cobble place with a blockade across the lane.",
            ),
            QAItem(
                question=f"What color clue did {params.hero} find?",
                answer=f"{params.hero} found the {MYSTERIES[params.mystery].missing_color} paint clue.",
            ),
            QAItem(
                question=f"How did the argument end?",
                answer="It ended with reconciliation, because the neighbor and the painter apologized and worked together.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is cobble?",
                answer="Cobble is a rounded stone used to make old streets and paths.",
            ),
            QAItem(
                question="What is a blockade?",
                answer="A blockade is something that blocks a path or keeps people from going through.",
            ),
            QAItem(
                question="What does reconciliation mean?",
                answer="Reconciliation means people who were upset make peace and get along again.",
            ),
            QAItem(
                question="What is a color clue in a mystery?",
                answer="A color clue is a colored sign, stain, or object that helps solve the case.",
            ),
        ],
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child detective storyworld about cobbles, blockade, color, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--adjective", choices=ADJ)
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
    return choose_params(args, rng)


CURATED = [
    StoryParams(place="laneway", mystery="paint", hero="Mina", adjective="curious"),
    StoryParams(place="market", mystery="poster", hero="Theo", adjective="careful"),
]


def asp_program_text() -> str:
    return asp_program("#show valid/2.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_text())
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos:")
        for p, m in vals:
            print(f"  {p} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
