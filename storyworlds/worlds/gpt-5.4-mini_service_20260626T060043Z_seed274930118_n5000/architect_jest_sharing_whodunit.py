#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/architect_jest_sharing_whodunit.py
==============================================================================================================

A small whodunit storyworld about an architect and a jesting helper who share
clues, tools, and trust until the mystery clicks into place.

The seed words push the world toward:
- architect
- jest
- sharing
- whodunit

This script keeps the mystery gentle and child-facing: something goes missing,
everyone looks a little suspicious, the architect and the jest share their
findings, and the last clue reveals the true cause.

The world model uses both physical meters and emotional memes:
- meters: distance, possession, hiddenness, and obvious physical clues
- memes: worry, confidence, mischief, trust, relief

The story is generated from state, not from a frozen paragraph template.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    rooms: list[str]
    details: list[str]


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    room: str
    reveals: str
    shared_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    shared_item: str
    suspect: str
    architect_name: str
    jest_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
SETTINGS = {
    "studio": Setting(
        place="the studio",
        rooms=["desk", "shelf", "window", "hall"],
        details=["blueprints", "small models", "pencils"],
    ),
    "workshop": Setting(
        place="the workshop",
        rooms=["table", "pegboard", "door", "corner"],
        details=["wood shavings", "measure tape", "spare nails"],
    ),
    "gallery": Setting(
        place="the gallery",
        rooms=["hall", "archway", "bench", "curtain"],
        details=["framed plans", "soft lights", "quiet footsteps"],
    ),
}

CLUES = {
    "key": Clue(
        id="key",
        label="brass key",
        phrase="a little brass key",
        room="desk",
        reveals="it opens the locked model cabinet",
    ),
    "ink": Clue(
        id="ink",
        label="ink smudge",
        phrase="a dark ink smudge",
        room="shelf",
        reveals="the missing paper was moved by someone with inky fingers",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon tied in a neat bow",
        room="window",
        reveals="it was used to bundle the plans before they vanished",
    ),
}

SHARED_ITEMS = {
    "lamp": ("lamp", "a small lamp", "desk"),
    "magnifier": ("magnifier", "a round magnifying glass", "table"),
    "sketchbook": ("sketchbook", "a shared sketchbook", "bench"),
}

SUSPECTS = {
    "cat": ("cat", "a sleepy cat", "corner"),
    "wind": ("wind", "a gusty draft", "window"),
    "apprentice": ("apprentice", "a hurried apprentice", "hall"),
}

ARCHITECT_NAMES = ["Mina", "Iris", "Leah", "Nora", "Tess", "June"]
JEST_NAMES = ["Pip", "Bobo", "Milo", "Jax", "Rin", "Drew"]
TRAITS = ["careful", "bright", "patient", "curious", "gentle", "quick-thinking"]


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    architect = world.add(Entity(
        id=params.architect_name,
        kind="character",
        type="architect",
        label="the architect",
        traits=["careful", "stubborn"],
        meters={"worry": 0.0, "confidence": 0.0},
        memes={"worry": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    jest = world.add(Entity(
        id=params.jest_name,
        kind="character",
        type="jest",
        label="the jest",
        traits=["playful", "kind"],
        meters={"worry": 0.0},
        memes={"mischief": 0.0, "trust": 0.0, "joy": 0.0},
    ))

    clue = CLUES[params.clue]
    shared_id, shared_label, shared_phrase, shared_room = params.shared_item, *SHARED_ITEMS[params.shared_item]
    shared = world.add(Entity(
        id=shared_id,
        kind="thing",
        type=shared_id,
        label=shared_label,
        phrase=shared_phrase,
        owner=architect.id,
        carried_by=architect.id,
        hidden_in=shared_room,
        meters={"distance": 0.0, "used": 0.0},
    ))

    suspect_id, suspect_label, suspect_room = params.suspect, *SUSPECTS[params.suspect]
    suspect = world.add(Entity(
        id=suspect_id,
        kind="thing",
        type=suspect_id,
        label=suspect_label,
        phrase=suspect_label,
        hidden_in=suspect_room,
        meters={"obviousness": 0.0},
        memes={"suspicion": 0.0},
    ))

    world.facts.update(
        architect=architect,
        jest=jest,
        clue=clue,
        shared=shared,
        suspect=suspect,
        room=clue.room,
    )
    return world


def show_setup(world: World) -> None:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    shared: Entity = world.facts["shared"]

    world.say(
        f"{a.id} was an architect who noticed every line, every angle, and every tiny gap."
    )
    world.say(
        f"{j.id} was a jest who liked to share jokes, snacks, and helpful little surprises."
    )
    world.say(
        f"Together, they shared {shared.phrase} while working in {world.setting.place}."
    )
    world.say(
        f"That morning, {a.id} had been counting on {clue.phrase}, because {clue.reveals}."
    )


def predict_missing_clue(world: World, clue: Clue) -> bool:
    sim = world.copy()
    c = sim.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        hidden_in=clue.room,
        meters={"obviousness": 0.0},
    ))
    return c.hidden_in is not None


def investigate(world: World) -> None:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    shared: Entity = world.facts["shared"]
    suspect: Entity = world.facts["suspect"]

    a.memes["worry"] += 1
    j.memes["trust"] += 1

    world.para()
    world.say(
        f"Then {a.id} looked at the desk and froze. {clue.phrase} was gone."
    )
    world.say(
        f"{a.id} checked the room again, while {j.id} stayed close and shared the lamp."
    )
    shared.carried_by = j.id
    shared.hidden_in = None

    if suspect.id == "wind":
        world.say(
            f"A curtain moved near the window, and a draft fluttered the papers."
        )
    elif suspect.id == "cat":
        world.say(
            f"A sleepy cat blinked from the corner with a ribbon on its tail."
        )
    else:
        world.say(
            f"An apprentice rushed past the hall, and a ribbon on their sleeve snagged the eye."
        )

    clue.meters = {"obviousness": 0.0}
    clue.room = clue.room


def share_clues(world: World) -> None:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    shared: Entity = world.facts["shared"]

    world.para()
    a.memes["confidence"] += 1
    j.memes["joy"] += 1
    world.say(
        f"{a.id} and {j.id} shared what they had found: the missing {clue.label}, the quiet room, and the clue of the {shared.label}."
    )
    world.say(
        f"{j.id} joked, but the joke carried a real idea: someone had borrowed the thing, not stolen it."
    )
    world.say(
        f"That made {a.id} look again at the hallway, where {suspect.label} had been hiding in plain sight."
    )


def solve_mystery(world: World) -> None:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    shared: Entity = world.facts["shared"]

    world.para()
    a.memes["worry"] = 0.0
    a.memes["relief"] += 1
    j.memes["trust"] += 1

    if suspect.id == "wind":
        world.say(
            f"At last, {a.id} saw it: the wind had nudged the key off the desk and into the curtain folds."
        )
    elif suspect.id == "cat":
        world.say(
            f"At last, {a.id} saw it: the cat had batted the key under the bench while chasing the ribbon."
        )
    else:
        world.say(
            f"At last, {a.id} saw it: the apprentice had borrowed the key to open the model cabinet and then set it down in the hall."
        )

    world.say(
        f"{j.id} shared a grin and handed back the lamp. {a.id} found {clue.phrase} exactly where the last clue said it would be."
    )
    world.say(
        f"In the end, the mystery was simple: nothing was ruined, and the shared tools helped everyone see the truth."
    )


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = build_world(params)
    show_setup(world)
    investigate(world)
    share_clues(world)
    solve_mystery(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    shared: Entity = world.facts["shared"]
    return [
        f"Write a gentle whodunit about {a.id}, an architect, and {j.id}, a jest, who share {shared.phrase} while looking for {clue.phrase}.",
        f"Tell a child-friendly mystery set in {world.setting.place} where two friends share clues and solve a missing-item puzzle.",
        f"Write a short story where sharing a {shared.label} helps an architect and a jest discover who moved the {clue.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a: Entity = world.facts["architect"]
    j: Entity = world.facts["jest"]
    clue: Clue = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    shared: Entity = world.facts["shared"]

    if suspect.id == "wind":
        solved = "the wind"
    elif suspect.id == "cat":
        solved = "the cat"
    else:
        solved = "the apprentice"

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {a.id}, the architect, and {j.id}, the jest, as they worked together in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {a.id} and {j.id} share while they looked for clues?",
            answer=f"They shared {shared.phrase} so they could look carefully and not miss anything important.",
        ),
        QAItem(
            question=f"What missing thing caused the mystery?",
            answer=f"The missing thing was {clue.phrase}, and it mattered because it helped {a.id} finish the plan.",
        ),
        QAItem(
            question=f"Who turned out to be the reason the clue was missing?",
            answer=f"It was {solved}, which made the mystery look big at first but simple at the end.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the friends sharing their tools, finding the clue, and seeing that the problem was solved safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an architect do?",
            answer="An architect plans buildings and thinks carefully about shapes, spaces, and how rooms fit together.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let someone else use it, enjoy it, or look at it with you.",
        ),
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where the characters try to figure out who caused a surprising problem.",
        ),
        QAItem(
            question="Why is a lamp useful in a mystery?",
            answer="A lamp is useful because it shines light into corners and helps people notice small clues.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

arch(A) :- architect(A).
jest(J) :- jest(J).
shared_item(S) :- shared(S).
clue(C) :- clue(C).
suspect(X) :- suspect(X).

compatible(A,J,S,C,X) :-
    architect(A), jest(J), shared(S), clue(C), suspect(X),
    shares_tool(S), shares_clue(C), shares_mood(J).

valid_story(A,J,S,C) :- architect(A), jest(J), shared(S), clue(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name in ARCHITECT_NAMES:
        pass
    lines.append(asp.fact("architect", "architect"))
    lines.append(asp.fact("jest", "jest"))
    for sid in SHARED_ITEMS:
        lines.append(asp.fact("shared", sid))
        lines.append(asp.fact("shares_tool", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("shares_clue", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("shares_mood", "jest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} story combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for shared in SHARED_ITEMS:
                combos.append((place, clue, shared, "suspect"))
    return combos


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
@dataclass
class DummyParams:
    place: str = "studio"
    clue: str = "key"
    shared_item: str = "lamp"
    suspect: str = "wind"
    architect_name: str = "Mina"
    jest_name: str = "Pip"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle whodunit storyworld with sharing and clues.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--shared-item", choices=SHARED_ITEMS.keys())
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
    ap.add_argument("--architect-name", choices=ARCHITECT_NAMES)
    ap.add_argument("--jest-name", choices=JEST_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    shared_item = args.shared_item or rng.choice(list(SHARED_ITEMS.keys()))
    suspect = args.suspect or rng.choice(list(SUSPECTS.keys()))
    architect_name = args.architect_name or rng.choice(ARCHITECT_NAMES)
    jest_name = args.jest_name or rng.choice(JEST_NAMES)
    if architect_name == jest_name:
        raise StoryError("The architect and the jest should be different characters.")
    return StoryParams(
        place=place,
        clue=clue,
        shared_item=shared_item,
        suspect=suspect,
        architect_name=architect_name,
        jest_name=jest_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("studio", "key", "lamp", "wind", "Mina", "Pip"),
            StoryParams("workshop", "ink", "magnifier", "cat", "Iris", "Bobo"),
            StoryParams("gallery", "ribbon", "sketchbook", "apprentice", "Leah", "Rin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
