#!/usr/bin/env python3
"""
storyworlds/worlds/odd_comfort_bravery_mystery_to_solve_ghost.py
===============================================================

A small ghost-story world: something odd in a quiet house turns out to be a
mystery to solve, and the brave child finds a kind way to give comfort.

The seed idea:
- A child hears odd noises in a house at night.
- They feel scared, but choose bravery.
- They discover a ghost is not mean; it is lonely and needs comfort.
- Solving the mystery changes the mood from fear to warmth.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    description: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    clue: str
    noise: str
    hidden_source: str
    comfort_item: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "old_house": Setting(
        place="the old house",
        description="The old house creaked softly, and the hall light made the walls look pale.",
        affordances={"listen", "search", "comfort"},
    ),
    "attic": Setting(
        place="the attic",
        description="The attic was dusty and quiet, with a little window that let in a silver moonbeam.",
        affordances={"listen", "search", "comfort"},
    ),
    "nursery": Setting(
        place="the nursery",
        description="The nursery was calm, with a blanket basket, soft toys, and a nightlight glowing warm.",
        affordances={"listen", "search", "comfort"},
    ),
}

MYSTERIES = {
    "mystery_tapping": Mystery(
        clue="a tiny tapping sound behind the wall",
        noise="tap-tap-tap",
        hidden_source="a loose window branch tapping the glass",
        comfort_item="a blanket",
    ),
    "mystery_whisper": Mystery(
        clue="a whispering sigh from the corner",
        noise="whooo",
        hidden_source="a draft slipping through an open vent",
        comfort_item="a warm lamp",
    ),
    "mystery_rattle": Mystery(
        clue="a rattle under the floorboards",
        noise="clack-clack",
        hidden_source="a toy wind-up mouse caught beneath a box",
        comfort_item="a basket of toys",
    ),
}

GHOST_TYPES = {
    "moon_ghost": {
        "label": "moon ghost",
        "phrase": "a small pale moon ghost",
        "traits": ["odd", "lonely"],
    },
    "sheet_ghost": {
        "label": "sheet ghost",
        "phrase": "a floaty white sheet ghost",
        "traits": ["odd", "gentle"],
    },
    "lamp_ghost": {
        "label": "lamp ghost",
        "phrase": "a shy lamp-light ghost",
        "traits": ["odd", "tired"],
    },
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Ben", "Iris", "Theo", "Luna", "Owen"]
TRAITS = ["brave", "curious", "careful", "kind"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the hidden source is discoverable in the setting.
solvable(M) :- mystery(M).

% Brave children can choose to search even when afraid.
can_search(H) :- hero(H), brave(H).

% Comfort is given when the ghost is lonely and the child has solved the mystery.
comfort_given(H, G, M) :- hero(H), ghost(G), mystery(M), lonely(G), solved(M), can_search(H).

% A valid story has one hero, one ghost, one mystery, and a place that supports search.
valid_story(P, H, G, M) :- setting(P), hero(H), ghost(G), mystery(M), affords(P, search).
#show valid_story/4.
#show solvable/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for gid in GHOST_TYPES:
        lines.append(asp.fact("ghost", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.affordances:
            continue
        for mystery_id in MYSTERIES:
            for ghost_id in GHOST_TYPES:
                combos.append((place, mystery_id, ghost_id))
    return combos


def explain_rejection(place: str, mystery_id: str, ghost_id: str) -> str:
    return (
        f"(No story: the combination of {place}, {mystery_id}, and {ghost_id} does not "
        f"support a believable ghost mystery with a brave child and a solvable clue.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def make_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    ghost_name = args.ghost_name or rng.choice(["Misty", "Pale One", "Murmur", "Wisp"])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
        ghost_name=ghost_name,
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["odd", "brave"],
        memes={"fear": 0.0, "bravery": 0.0, "comfort": 0.0, "curiosity": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        memes={"worry": 0.0, "comfort": 0.0},
    ))
    ghost_kind_id = "moon_ghost"
    ghost_spec = GHOST_TYPES[ghost_kind_id]
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label=params.ghost_name,
        phrase=ghost_spec["phrase"],
        traits=list(ghost_spec["traits"]),
        memes={"lonely": 1.0, "comfort": 0.0, "peace": 0.0},
    ))

    mystery_id = "mystery_tapping"
    mystery = MYSTERIES[mystery_id]

    # Act 1
    world.say(f"{params.hero_name} lived in {setting.place}. {setting.description}")
    world.say(
        f"One night, {params.hero_name} heard {mystery.clue}, and the sound felt odd enough "
        f"to make the room go still."
    )
    hero.memes["fear"] += 1.0
    hero.memes["curiosity"] += 1.0
    parent.memes["worry"] += 1.0

    # Act 2
    world.para()
    world.say(
        f"{params.hero_name}'s {params.parent_type} held {hero.pronoun('possessive')} hand and "
        f"said, \"It is all right to be scared, but bravery means looking gently at the mystery.\""
    )
    hero.memes["bravery"] += 1.0
    world.say(
        f"So {params.hero_name} took a slow breath, walked toward the tapping, and chose "
        f"to search instead of hiding."
    )

    # Mystery turn
    world.say(
        f"At the corner, {params.hero_name} found {ghost.phrase}. {ghost.label.capitalize()} did not roar "
        f"or rattle the floor; {ghost.pronoun('subject')} only seemed lonely."
    )
    ghost.memes["lonely"] = 1.0
    hero.memes["fear"] = 0.0

    # Solve
    world.para()
    world.say(
        f"{params.hero_name} listened carefully and noticed the clue. The odd tapping came from "
        f"{mystery.hidden_source}, not from a mean ghost at all."
    )
    world.say(
        f"That made the mystery easy to solve, and the house stopped feeling spooky."
    )

    # Act 3
    world.say(
        f"{params.hero_name} brought {mystery.comfort_item} to the ghost and said, "
        f"\"You can stay with us for a little while.\""
    )
    hero.memes["comfort"] += 1.0
    ghost.memes["comfort"] += 1.0
    ghost.memes["peace"] += 1.0
    parent.memes["comfort"] += 1.0

    world.para()
    world.say(
        f"{params.hero_name}, {ghost.label}, and {params.parent_type} sat together in the quiet room. "
        f"The odd sound was gone, and the little ghost looked warm and safe at last."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        ghost=ghost,
        mystery=mystery,
        mystery_id=mystery_id,
        ghost_kind_id=ghost_kind_id,
        setting=setting,
        params=params,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short ghost story for a child named {hero.id} about an odd sound and a kind comfort.',
        f"Tell a brave mystery story where {hero.id} hears {mystery.clue} and solves it with gentleness.",
        f'Write a child-friendly ghost story that uses the word "odd" and ends with comfort.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    ghost: Entity = f["ghost"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"What made {hero.id} feel scared at first?",
            answer=f"{hero.id} felt scared because {mystery.clue} sounded odd in {setting.place}.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=(
                f"{hero.id} showed bravery by taking a slow breath, walking toward the sound, and "
                f"searching for the cause instead of hiding."
            ),
        ),
        QAItem(
            question=f"What was the mystery really caused by?",
            answer=f"The mystery was really caused by {mystery.hidden_source}.",
        ),
        QAItem(
            question=f"Why did the ghost need comfort?",
            answer=f"The ghost needed comfort because {ghost.id} was lonely, not mean.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help the ghost?",
            answer=f"{hero.id} gave {ghost.id} {mystery.comfort_item} and invited {ghost.pronoun('object')} to stay.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with the odd sound solved, the room calm, and {hero.id}, {ghost.id}, and the "
                f"{parent.type} sitting together in comfort."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel scared, like taking a careful look at a mystery.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is something confusing at first, where you look for clues until you understand it.",
        ),
        QAItem(
            question="Why can a strange sound feel spooky?",
            answer="A strange sound can feel spooky because you do not know where it comes from yet.",
        ),
        QAItem(
            question="What does comfort mean?",
            answer="Comfort means help that makes someone feel safe, calm, and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation API
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world about odd sounds, bravery, mystery, and comfort.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--ghost-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, _, _ = rng.choice(combos)
    return make_story_params(args, rng=rng).__class__(
        place=place,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        parent_type=args.parent_type or rng.choice(["mother", "father"]),
        ghost_name=args.ghost_name or rng.choice(["Misty", "Pale One", "Murmur", "Wisp"]),
    )


CURATED = [
    StoryParams(place="old_house", hero_name="Maya", hero_type="girl", parent_type="mother", ghost_name="Wisp"),
    StoryParams(place="attic", hero_name="Leo", hero_type="boy", parent_type="father", ghost_name="Murmur"),
    StoryParams(place="nursery", hero_name="Luna", hero_type="girl", parent_type="mother", ghost_name="Misty"),
]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
