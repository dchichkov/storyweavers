#!/usr/bin/env python3
"""
Whodunit storyworld: an inventor, a piece of apparel, a brussel misunderstanding,
and a reconciliation at the end.

The story engine builds a tiny simulated mystery:
- a child inventor makes a clever item of apparel,
- a brussel-scented misunderstanding makes it seem lost or ruined,
- clues reveal what really happened,
- the worried friends reconcile.

The world is deliberately small and constraint-checked so every generated story
has a clear setup, a turn, and a resolution.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Invention:
    id: str
    label: str
    phrase: str
    purpose: str
    is_apparel: bool = True
    vulnerable_to: set[str] = field(default_factory=set)
    clue: str = ""


@dataclass
class Misunderstanding:
    id: str
    trigger: str
    false_belief: str
    reveal: str
    requires: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    invention: str
    misunderstanding: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.clues_found: list[str] = []
        self.truth_revealed: bool = False

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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.clues_found = list(self.clues_found)
        clone.truth_revealed = self.truth_revealed
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "atelier": Place(
        id="atelier",
        label="the little atelier",
        mood="quiet",
        clues=["a spool of thread", "a sticky leaf", "a tiny shoe print"],
    ),
    "market": Place(
        id="market",
        label="the morning market",
        mood="busy",
        clues=["a cabbage leaf", "a folded note", "a crumb trail"],
    ),
    "hall": Place(
        id="hall",
        label="the bright hall",
        mood="echoing",
        clues=["a ribbon tag", "a bent button", "a smear of flour"],
    ),
}

INVENTIONS = {
    "cape": Invention(
        id="cape",
        label="cape",
        phrase="a clever red cape",
        purpose="keep its wearer warm and brave",
        vulnerable_to={"mud"},
        clue="a bit of red thread",
    ),
    "hat": Invention(
        id="hat",
        label="hat",
        phrase="a striped paper hat with a feather",
        purpose="shade a face and look fancy",
        vulnerable_to={"rain"},
        clue="a feather tip",
    ),
    "apron": Invention(
        id="apron",
        label="apron",
        phrase="a pocketed apron",
        purpose="carry tools and keep clothes neat",
        vulnerable_to={"sauce"},
        clue="a tiny pocket seam",
    ),
}

MISUNDERSTANDINGS = {
    "brussel": Misunderstanding(
        id="brussel",
        trigger="a plate of brussel sprouts",
        false_belief="someone had stolen the invention",
        reveal="the invention had been wrapped beside the brussel sprouts by mistake",
        requires={"apparel"},
    ),
    "note": Misunderstanding(
        id="note",
        trigger="a folded note",
        false_belief="the helper had ruined the invention on purpose",
        reveal="the helper was hiding a surprise repair plan",
        requires={"apparel"},
    ),
    "button": Misunderstanding(
        id="button",
        trigger="a bent button",
        false_belief="the invention had broken during a chase",
        reveal="the button came from an old coat, not the new invention",
        requires={"apparel"},
    ),
}

GENDER_NAMES = {
    "girl": ["Mina", "Lina", "Ivy", "Nora", "Tess"],
    "boy": ["Owen", "Milo", "Finn", "Noah", "Ezra"],
}
HELPERS = ["aunt", "uncle", "friend", "neighbor"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
invention(I) :- invention_fact(I).
misunderstanding(M) :- misunderstanding_fact(M).

valid_story(P, I, M) :- place(P), invention(I), misunderstanding(M),
                        supports(P, I), triggers(M, I).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
        for clue in PLACES[pid].clues:
            lines.append(asp.fact("clue", pid, clue))
    for iid, inv in INVENTIONS.items():
        lines.append(asp.fact("invention_fact", iid))
        if inv.is_apparel:
            lines.append(asp.fact("apparel", iid))
        for v in sorted(inv.vulnerable_to):
            lines.append(asp.fact("vulnerable_to", iid, v))
    for mid, mm in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding_fact", mid))
        for req in sorted(mm.requires):
            lines.append(asp.fact("requires", mid, req))
    for pid, pl in PLACES.items():
        for iid, inv in INVENTIONS.items():
            if inv.is_apparel:
                lines.append(asp.fact("supports", pid, iid))
    for mid, mm in MISUNDERSTANDINGS.items():
        for iid, inv in INVENTIONS.items():
            if "apparel" in mm.requires and inv.is_apparel:
                lines.append(asp.fact("triggers", mid, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def is_reasonable(place: Place, invention: Invention, misunderstanding: Misunderstanding) -> bool:
    return invention.is_apparel and "apparel" in misunderstanding.requires and bool(place.clues)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, pl in PLACES.items():
        for iid, inv in INVENTIONS.items():
            for mid, mm in MISUNDERSTANDINGS.items():
                if is_reasonable(pl, inv, mm):
                    out.append((pid, iid, mid))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    invention = INVENTIONS[params.invention]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "worry": 0.0},
        memes={"pride": 1.0, "confusion": 0.0, "hurt": 0.0, "reconciliation": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"care": 1.0},
        memes={"patience": 1.0},
    ))
    item = world.add(Entity(
        id=invention.id,
        kind="thing",
        type="apparel",
        label=invention.label,
        phrase=invention.phrase,
        owner=hero.id,
        location=place.label,
        meters={"clean": 1.0, "safe": 1.0},
        memes={"pride": 1.0},
    ))
    brussel = world.add(Entity(
        id="brussel",
        kind="thing",
        type="food",
        label="brussel sprouts",
        phrase="a plate of brussel sprouts",
        location=place.label,
        meters={"fresh": 1.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        brussel=brussel,
        place=place,
        invention=invention,
        misunderstanding=misunderstanding,
    )

    # Act 1: setup
    world.say(
        f"{hero.id} was a small inventor who loved to invent things that could become useful apparel."
    )
    world.say(
        f"At {place.label}, {hero.id} showed {hero.pronoun('possessive')} latest {item.label}: {item.phrase}."
    )
    world.say(
        f"It was meant to {invention.purpose}, and {hero.id} felt proud of the careful stitching."
    )

    # Act 2: misunderstanding
    world.para()
    world.say(
        f"Then something strange happened at {place.label}. Someone saw {misunderstanding.trigger} near the table."
    )
    world.say(
        f"Right away, {hero.id} thought {misunderstanding.false_belief}."
    )
    hero.memes["confusion"] += 1.0
    hero.meters["worry"] += 1.0
    world.say(
        f"{hero.id} searched under the cloth, behind the chairs, and near the warm dishes, but the {item.label} was nowhere easy to see."
    )
    world.clues_found.append("a brussel smell")

    # Clues
    clue = invention.clue
    world.say(
        f"Then {helper.label} noticed {clue} caught on a napkin beside the brussel sprouts."
    )
    world.clues_found.append(clue)
    world.say(
        f"That clue did not look like a theft at all. It looked like a mix-up."
    )

    # Reveal
    world.para()
    world.say(
        f"{helper.label} pointed to the covered tray and said the truth: {misunderstanding.reveal}."
    )
    world.truth_revealed = True
    hero.meters["worry"] = 0.0
    hero.memes["confusion"] = 0.0
    hero.memes["hurt"] = 0.0

    # Act 3: reconciliation
    world.say(
        f"{hero.id} blinked, then laughed at the silly mistake. The brussel sprouts had not stolen anything."
    )
    world.say(
        f"{hero.id} and {helper.label} straightened the table together, found the {item.label}, and smoothed the wrinkled cloth."
    )
    hero.memes["reconciliation"] += 1.0
    helper.memes["patience"] += 1.0
    world.say(
        f"By the end, {hero.id} and {helper.label} were friends again, and the little {item.label} sat safely beside the dinner plate."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly whodunit about an inventor, a piece of apparel, and a brussel-scented clue.",
        f"Tell a mystery where {f['hero'].id} invents apparel at {f['place'].label}, misunderstands a clue, and then reconciles with {f['helper'].label}.",
        f"Make a short story with the words invent, apparel, and brussel that ends with a clear reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    place: Place = f["place"]
    invention: Invention = f["invention"]
    misunderstanding: Misunderstanding = f["misunderstanding"]

    return [
        QAItem(
            question=f"What did {hero.id} invent in the story?",
            answer=f"{hero.id} invented {item.phrase}. It was a kind of apparel meant to {invention.purpose}.",
        ),
        QAItem(
            question=f"Why did {hero.id} first think something bad had happened at {place.label}?",
            answer=f"{hero.id} saw {misunderstanding.trigger} and thought {misunderstanding.false_belief}. That made {hero.id} feel worried and confused.",
        ),
        QAItem(
            question=f"What clue helped solve the misunderstanding?",
            answer=f"The clue was {invention.clue}, which {helper.label} noticed near the brussel sprouts. That clue showed the item had been mixed up, not taken away.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.label}?",
            answer=f"They talked, understood the mistake, and reconciled. By the end they were working together again, and the apparel was safe beside the plate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is apparel?",
            answer="Apparel means clothing or things people wear, like hats, capes, and aprons.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a thing means one message, but the real meaning is different.",
        ),
        QAItem(
            question="What are brussel sprouts?",
            answer="Brussel sprouts are small green vegetables that grow in little round heads on a stalk.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, understand each other better, and become friendly again.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"clues_found={world.clues_found}")
    lines.append(f"truth_revealed={world.truth_revealed}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="atelier", invention="cape", misunderstanding="brussel", name="Mina", gender="girl", helper="aunt"),
    StoryParams(place="market", invention="hat", misunderstanding="note", name="Owen", gender="boy", helper="friend"),
    StoryParams(place="hall", invention="apron", misunderstanding="button", name="Tess", gender="girl", helper="neighbor"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about inventing apparel and solving a brussel misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.invention is None or c[1] == args.invention)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, invention, misunderstanding = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        invention=invention,
        misunderstanding=misunderstanding,
        name=name,
        gender=gender,
        helper=helper,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    # valid_story/3 is about place, invention, misunderstanding
    clingo_norm = {(a, b, c) for (a, b, c) in clingo_set}
    if py == clingo_norm:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_norm - py))
    print("  only in python:", sorted(py - clingo_norm))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
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
            header = f"### {p.name}: {p.invention} at {p.place} (misunderstanding: {p.misunderstanding})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
