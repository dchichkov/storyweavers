#!/usr/bin/env python3
"""
storyworlds/worlds/percussion_incriminate_foreshadowing_bravery_flashback_mystery.py
====================================================================================

A small mystery storyworld about a child who hears percussion sounds, notices
odd clues, remembers a flashback, and bravely solves a gentle mystery.

The seed premise:
- Something goes missing.
- Clues include percussion sounds that point toward the culprit.
- The story uses foreshadowing, a flashback, and a brave final step.
- The word "incriminate" is part of the world vocabulary because the clues
  can incriminate the wrong suspect before the truth is found.

This world is designed to stay child-facing, concrete, and state-driven.
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

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "uncle"}
        female = {"girl", "mother", "mom", "woman", "aunt"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    name: str
    clue_density: int = 0
    noisy: bool = False


@dataclass
class Mystery:
    missing: str
    suspect: str
    true_holder: str
    clue: str
    foreshadow: str
    flashback: str
    reveal_method: str


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    missing: str
    suspect: str
    seed: Optional[int] = None


LOCATIONS = {
    "music_room": Location(name="the music room", clue_density=3, noisy=True),
    "hall": Location(name="the hall", clue_density=2, noisy=False),
    "school_stage": Location(name="the school stage", clue_density=4, noisy=True),
    "library_corner": Location(name="the library corner", clue_density=1, noisy=False),
}

MISSING_ITEMS = {
    "drumstick": "the tiny drumstick",
    "tambourine": "the bright tambourine",
    "bell": "the hand bell",
    "triangle": "the metal triangle",
}

SUSPECTS = {
    "cat": "a sleepy cat",
    "helper": "the kind helper",
    "friend": "the nervous friend",
    "janitor": "the janitor",
}

CHILD_NAMES = ["Mina", "Toby", "Lila", "Noah", "Nora", "Jude", "Ava", "Eli"]
HELPER_NAMES = ["Ms. Finch", "Mr. Reed", "Aunt June", "Uncle Paul", "Ms. Vale", "Mr. Lane"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.place]
    mystery = make_mystery(params)

    world = World(loc)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters={"courage": 0.0, "certainty": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "bravery": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        label=params.helper_name,
        meters={"courage": 0.0},
        memes={"calm": 1.0, "helpfulness": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=params.missing,
        label=MISSING_ITEMS[params.missing],
        phrase=MISSING_ITEMS[params.missing],
        hidden=True,
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="character" if params.suspect != "cat" else "thing",
        type=params.suspect,
        label=SUSPECTS[params.suspect],
        meters={"noise": 0.0},
        memes={"suspicion": 0.0},
    ))
    true_holder = world.add(Entity(
        id="true_holder",
        kind="character",
        type="child" if params.suspect != "helper" else "adult",
        label="the shelf by the drums" if params.suspect != "janitor" else "the storage cart",
        hidden=False,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.clue,
        phrase=mystery.clue,
    ))

    world.facts.update(
        mystery=mystery,
        child=child,
        helper=helper,
        missing=missing,
        suspect=suspect,
        true_holder=true_holder,
        clue=clue,
    )

    narrate_setup(world, child, helper, missing, suspect, mystery)
    narrate_turn(world, child, helper, missing, suspect, mystery)
    narrate_resolution(world, child, helper, missing, suspect, true_holder, mystery)
    return world


def make_mystery(params: StoryParams) -> Mystery:
    missing = MISSING_ITEMS[params.missing]
    suspect = SUSPECTS[params.suspect]
    foreshadow = "a soft tap-tap from the back shelf"
    flashback = "the child remembered hearing the same tap when the helper carried boxes earlier"
    reveal_method = "follow the sound"
    clue = "a small percussion beat from behind the curtain"
    if params.missing == "tambourine":
        clue = "a jingling percussion jingle near the window"
    elif params.missing == "drumstick":
        clue = "a tiny percussion knock from under the bench"
    elif params.missing == "bell":
        clue = "a bright percussion ring by the supply box"
    elif params.missing == "triangle":
        clue = "a thin percussion ting from the metal shelf"
    return Mystery(
        missing=missing,
        suspect=suspect,
        true_holder="the shelf by the drums",
        clue=clue,
        foreshadow=foreshadow,
        flashback=flashback,
        reveal_method=reveal_method,
    )


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------
def narrate_setup(world: World, child: Entity, helper: Entity, missing: Entity,
                  suspect: Entity, mystery: Mystery) -> None:
    loc = world.location.name
    world.say(
        f"At {loc}, {child.label} looked around and noticed that {missing.label} was gone."
    )
    world.say(
        f"{child.label} had loved the little percussion practice that morning, so the empty spot felt strange."
    )
    world.say(
        f"Near the doorway, {suspect.label} seemed to be the only one close enough to notice."
    )
    world.say(
        f"That was the first foreshadowing clue: {mystery.foreshadow}."
    )
    helper.memes["calm"] += 0.5


def narrate_turn(world: World, child: Entity, helper: Entity, missing: Entity,
                 suspect: Entity, mystery: Mystery) -> None:
    world.para()
    child.memes["worry"] += 1.0
    child.meters["certainty"] += 0.5
    world.say(
        f"Then {child.label} heard it again: {mystery.clue}."
    )
    world.say(
        f"It sounded as if the sound could incriminate {suspect.label}, and {child.label} frowned."
    )
    world.say(
        f"{helper.label} noticed the look and said, \"Let's be brave and check the clues, one by one.\""
    )
    child.meters["courage"] += 0.5
    child.memes["bravery"] += 0.5
    world.say(
        f"That reminder made {child.label} stand a little straighter."
    )
    world.say(
        f"In a quick flashback, {child.label} remembered {mystery.flashback}."
    )


def narrate_resolution(world: World, child: Entity, helper: Entity, missing: Entity,
                       suspect: Entity, true_holder: Entity, mystery: Mystery) -> None:
    world.para()
    child.meters["courage"] += 1.0
    child.memes["bravery"] += 1.0
    world.say(
        f"{child.label} took a brave breath and chose to {mystery.reveal_method}."
    )
    world.say(
        f"Behind the curtain, the missing {missing.label.lower()} was not with {suspect.label} at all."
    )
    world.say(
        f"It had rolled under the shelf by the drums, where a loose little percussion toy had nudged it away."
    )
    world.say(
        f"{child.label} picked it up, and the room felt clear again."
    )
    world.say(
        f"{helper.label} smiled, and even {suspect.label} looked relieved, because the wrong clue had been harmless after all."
    )
    world.say(
        f"In the end, the mystery was solved, the false suspicion could not incriminate anyone, and the music room sounded calm again."
    )
    missing.hidden = False
    missing.found_by = child.id


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly mystery story that includes the word "percussion" and ends with the missing object being found.',
        f"Tell a short story where {child.label} hears a percussion clue, feels unsure, and then bravely solves the mystery with {helper.label}.",
        f'Write a gentle mystery with foreshadowing, a flashback, and a brave ending image involving {mystery.missing.lower()}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    missing: Entity = f["missing"]  # type: ignore[assignment]
    suspect: Entity = f["suspect"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{child.label} could not find {missing.label}, so that was the missing thing."
        ),
        QAItem(
            question=f"What clue made the mystery feel suspicious?",
            answer=f"The clue was {mystery.clue}, which sounded like percussion and made the room feel mysterious."
        ),
        QAItem(
            question=f"Why did {child.label} think {suspect.label} might be involved?",
            answer=f"{child.label} heard the clue near {suspect.label} and worried that the sound might incriminate {suspect.label}, but that first guess was wrong."
        ),
        QAItem(
            question=f"How did {child.label} act when the mystery got tricky?",
            answer=f"{child.label} was brave, listened carefully, and chose to follow the sound instead of panicking."
        ),
        QAItem(
            question=f"What was remembered in the flashback?",
            answer=f"In the flashback, {child.label} remembered hearing the same tap when the helper moved boxes earlier."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The missing {missing.label.lower()} was found near the drums, the false suspicion was cleared up, and the mystery ended calmly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is percussion?",
            answer="Percussion is music made by hitting, shaking, or tapping things like drums, bells, and triangles."
        ),
        QAItem(
            question="What does incriminate mean?",
            answer="To incriminate someone means to make it seem like they may have done something wrong, even before you know the full truth."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue early in a story that hints something important will happen later."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story remembers something that happened earlier."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while still choosing to keep going."
        ),
    ]


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
# Registry and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="music_room", child_name="Mina", child_gender="girl", helper_name="Ms. Finch", helper_gender="woman", missing="tambourine", suspect="cat"),
    StoryParams(place="hall", child_name="Toby", child_gender="boy", helper_name="Mr. Reed", helper_gender="man", missing="drumstick", suspect="friend"),
    StoryParams(place="school_stage", child_name="Lila", child_gender="girl", helper_name="Ms. Vale", helper_gender="woman", missing="bell", suspect="janitor"),
    StoryParams(place="library_corner", child_name="Noah", child_gender="boy", helper_name="Uncle Paul", helper_gender="man", missing="triangle", suspect="helper"),
]

GENDERED_NAMES = {
    "girl": CHILD_NAMES[:],
    "boy": CHILD_NAMES[:],
    "woman": HELPER_NAMES[:],
    "man": HELPER_NAMES[:],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery storyworld with percussion clues.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    place = args.place or rng.choice(list(LOCATIONS))
    missing = args.missing or rng.choice(list(MISSING_ITEMS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if missing == "triangle" and place == "library_corner":
        # allowed
        pass
    if missing == "drumstick" and suspect == "cat":
        # valid but no special restriction
        pass
    return StoryParams(
        place=place,
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        helper_gender=helper_gender,
        missing=missing,
        suspect=suspect,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        print("OK: no ASP twin defined for this world; verification is story-level only.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.missing} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
