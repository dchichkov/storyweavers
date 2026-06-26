#!/usr/bin/env python3
"""
storyworlds/worlds/robe_reconciliation_quest_mystery.py
=======================================================

A small mystery-flavored story world about a missing robe, a careful quest,
and a reconciliation at the end.

Premise:
- A child treasures a special robe.
- The robe goes missing before an important evening.
- The child and a helper search through a few plausible places.
- The tension is not solved by force, but by noticing a clue and making peace.

The world is intentionally small and simulation-driven:
physical state tracks where the robe is, who is carrying it, and which places
have been searched; emotional state tracks worry, suspicion, relief, and the
softening of blame into reconciliation.
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
    carried_by: Optional[str] = None
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    id: str
    label: str
    clue: str
    hides_robe: bool = False


@dataclass
class StoryParams:
    place: str
    hide_spot: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place("attic", "the attic", "dust on a trunk lid", hides_robe=True),
    "laundry": Place("laundry", "the laundry room", "a wet footprint near the basket", hides_robe=True),
    "garden": Place("garden", "the garden shed", "a ribbon caught on a nail", hides_robe=True),
    "hall": Place("hall", "the hallway closet", "a hook left swinging", hides_robe=True),
    "chair": Place("chair", "the reading chair", "a fold in the cushion", hides_robe=True),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "sister": "girl",
    "brother": "boy",
}

HERO_NAMES = ["Mia", "Noah", "Lina", "Eli", "Ava", "Theo", "Zoe", "Finn"]
TRAITS = ["quiet", "curious", "careful", "gentle", "brave"]

# inline feature words from the seed
FEATURE_WORDS = ["reconciliation", "quest", "mystery", "robe"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_choice(place: str, hide_spot: str) -> bool:
    return place in PLACES and hide_spot in PLACES and place != hide_spot


def explain_invalid(place: str, hide_spot: str) -> str:
    return (
        f"(No story: the robe cannot be hidden in the same place where the search begins, "
        f"and both choices must be known places. Try a different pair.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A robe mystery is valid when the starting place and hiding place are different.
valid_story(Place, HideSpot) :- place(Place), place(HideSpot), Place != HideSpot.

% The clue must point toward the hiding place so the quest can resolve.
resolves(Place, HideSpot) :- valid_story(Place, HideSpot), clue(HideSpot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("label", pid, p.label))
        lines.append(asp.fact("clue", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(a, b) for a in PLACES for b in PLACES if valid_choice(a, b)}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches python valid_choice() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_choice(params.place, params.hide_spot):
        raise StoryError(explain_invalid(params.place, params.hide_spot))

    world = World()
    place = PLACES[params.place]
    hide = PLACES[params.hide_spot]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"steps": 0},
        memes={"worry": 0, "hope": 0, "relief": 0, "reconciliation": 0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label="the helper",
        meters={"steps": 0},
        memes={"worry": 0, "hope": 0, "relief": 0, "reconciliation": 0},
    ))
    robe = world.add(Entity(
        id="Robe",
        type="robe",
        label="robe",
        phrase="a soft blue robe with silver thread",
        owner=hero.id,
        carried_by=None,
        hidden_in=hide.id,
        meters={"lost": 1, "found": 0},
        memes={"value": 1},
    ))
    world.places = dict(PLACES)

    # Act 1: the mystery appears.
    world.say(f"{hero.id} loved a soft blue robe with silver thread. It made the room feel calm and special.")
    world.say(f"On the night of the lantern tea, {hero.id} reached for the robe, but it was gone.")
    world.say(f"{hero.pronoun().capitalize()} looked around {place.label} and felt a knot of worry tighten.")

    # Act 2: the quest begins.
    world.para()
    hero.memes["worry"] += 1
    helper.memes["hope"] += 1
    world.say(f"{hero.id} and {helper.label} began a small quest through {place.label}.")
    world.say(f"They searched for a clue: {hide.clue}.")
    hero.meters["steps"] += 1
    helper.meters["steps"] += 1

    if hide.id == "attic":
        clue_line = "The dusty trunk in the attic looked just wide enough to hide something folded."
    elif hide.id == "laundry":
        clue_line = "The laundry room smelled fresh, and the basket had been moved twice."
    elif hide.id == "garden":
        clue_line = "The garden shed had a ribbon on the nail, as if someone had hurried."
    elif hide.id == "hall":
        clue_line = "The hallway closet kept creaking softly whenever the house grew quiet."
    else:
        clue_line = "The reading chair had a crooked cushion, like it was hiding a secret."
    world.say(clue_line)

    # Act 3: discovery and reconciliation.
    world.para()
    robe.carried_by = "Helper"
    robe.hidden_in = ""
    robe.meters["found"] = 1
    robe.meters["lost"] = 0
    hero.memes["worry"] = 0
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1

    if hide.id == "laundry":
        world.say("At last, they found the robe tucked inside the clean laundry, folded by mistake.")
    elif hide.id == "attic":
        world.say("At last, they found the robe inside an old trunk, folded neatly under a blanket.")
    elif hide.id == "garden":
        world.say("At last, they found the robe in the garden shed, wrapped around a basket to keep it safe.")
    elif hide.id == "hall":
        world.say("At last, they found the robe on a hallway hook, hidden behind a coat.")
    else:
        world.say("At last, they found the robe tucked into the reading chair, where it had slipped from sight.")

    helper.memes["reconciliation"] += 1
    hero.memes["reconciliation"] += 1
    hero.memes["relief"] += 1
    world.say(f"{hero.id} had worried the robe was lost forever, but the helper had only hidden it to keep it safe.")
    world.say(f"{hero.id} and {helper.label} shared a careful apology and a smile, and their reconciliation felt warmer than any lamp.")

    world.facts.update(
        hero=hero,
        helper=helper,
        robe=robe,
        place=place,
        hide=hide,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    hide = f["hide"]
    return [
        f'Write a short mystery story for a child about a lost robe, a quest, and reconciliation.',
        f"Tell a gentle story where {hero.id} searches {place.label} for a robe and finds a clue in {hide.label}.",
        f'Write a child-facing mystery that uses the word "robe" and ends with reconciliation after the search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    robe = f["robe"]
    place = f["place"]
    hide = f["hide"]

    return [
        QAItem(
            question=f"What was missing when {hero.id} reached for the robe?",
            answer=f"The soft blue robe with silver thread was missing, so {hero.id} felt worried and began looking for it.",
        ),
        QAItem(
            question=f"What kind of trip did {hero.id} and {helper.label} begin?",
            answer=f"They began a small quest through {place.label}, following a clue to find the robe.",
        ),
        QAItem(
            question=f"Where was the robe finally found?",
            answer=f"It was found in {hide.label}, where it had been tucked away and forgotten for a while.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.label}?",
            answer=f"They made up, shared an apology, and their reconciliation made the room feel warm again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "robe": [(
        "What is a robe?",
        "A robe is a loose piece of clothing that you can wear over other clothes, often at home or after washing.",
    )],
    "mystery": [(
        "What is a mystery in a story?",
        "A mystery is a problem or secret that characters try to solve by noticing clues.",
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a search for something important, and the search can feel like an adventure.",
    )],
    "reconciliation": [(
        "What does reconciliation mean?",
        "Reconciliation means people who were upset make peace again and feel friendly once more.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for key in FEATURE_WORDS for q, a in WORLD_KNOWLEDGE[key]]


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


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about a robe, a quest, and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hide-spot", choices=sorted(PLACES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(PLACES))
    hide_spot = args.hide_spot or rng.choice([k for k in PLACES if k != place])
    if not valid_choice(place, hide_spot):
        raise StoryError(explain_invalid(place, hide_spot))

    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = "girl" if gender == "girl" else "boy"
    helper = args.helper or rng.choice(sorted(HELPERS))
    helper_type = HELPERS[helper]
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place,
        hide_spot=hide_spot,
        hero_name=name,
        hero_type=hero_type,
        helper_type=helper_type,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="attic", hide_spot="laundry", hero_name="Mia", hero_type="girl", helper_type="mother"),
    StoryParams(place="hall", hide_spot="chair", hero_name="Noah", hero_type="boy", helper_type="father"),
    StoryParams(place="garden", hide_spot="attic", hero_name="Ava", hero_type="girl", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (place, hide_spot) pairs:\n")
        for a, b in pairs:
            print(f"  {a:8} {b}")
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
            header = f"### {p.hero_name}: robe mystery at {p.place} (hidden in {p.hide_spot})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
