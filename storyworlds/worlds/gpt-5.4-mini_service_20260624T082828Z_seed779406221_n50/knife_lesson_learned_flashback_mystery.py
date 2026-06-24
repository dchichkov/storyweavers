#!/usr/bin/env python3
"""
Knife Lesson Learned Mystery World
=================================

A small, self-contained storyworld about a child, a mystery, a careful tool,
and a lesson learned through a flashback.

Premise:
- A child finds a missing picnic cheese knife.
- The knife is useful, but it must be handled safely.
- A small mystery turns into a lesson learned when the child remembers a
  flashback and realizes where the knife belongs.

This world is designed to generate short, complete, child-facing stories with:
- a beginning mystery,
- a middle turn driven by world state,
- and an ending that proves what changed.
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
    hidden: bool = False
    carried_by: Optional[str] = None
    location: str = ""
    # meters: physical state; memes: emotional state
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    clues: list[str] = field(default_factory=list)
    safe_spots: set[str] = field(default_factory=set)


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    location: str
    safe_use: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    item: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(
        name="the kitchen",
        clues=["under the bread box", "beside the cutting board", "in the dish rack"],
        safe_spots={"drawer", "counter"},
    ),
    "picnic": Place(
        name="the picnic table",
        clues=["under the napkin", "near the apple basket", "beside the juice box"],
        safe_spots={"basket", "blanket"},
    ),
    "shed": Place(
        name="the garden shed",
        clues=["on the tool hook", "inside the red box", "behind the watering can"],
        safe_spots={"hook", "shelf"},
    ),
}

ITEMS = {
    "knife": MysteryItem(
        id="knife",
        label="knife",
        phrase="a small butter knife",
        location="kitchen",
        safe_use="cutting soft food",
        lesson="a knife belongs with the grown-up tools, not in a child's hands",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Eli", "Zoe", "Sam"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "quiet", "bright"]


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def first_letter(name: str) -> str:
    return name[0].lower()


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def intro_line(child: Entity, place: Place) -> str:
    return (
        f"{child.name_word()} was a little {child.type} who loved noticing tiny clues. "
        f"One afternoon, {child.pronoun()} wandered through {place.name} and saw that something was missing."
    )


def mystery_line(child: Entity, item: MysteryItem, place: Place) -> str:
    return (
        f"{child.name_word()} found the old note on the table: \"The {item.label} is gone.\" "
        f"{child.pronoun().capitalize()} looked around {place.name} and wondered where it had gone."
    )


def flashback_line(child: Entity, item: MysteryItem) -> str:
    return (
        f"Then {child.name_word()} had a flashback. {child.pronoun().capitalize()} remembered the {item.label} "
        f"used for {item.safe_use} at the family picnic, after a grown-up said to put it back right away."
    )


def lesson_line(child: Entity, item: MysteryItem) -> str:
    return (
        f"That was the lesson learned: {item.lesson}. "
        f"{child.name_word()} carried the {item.label} to the right place and felt proud to have solved the mystery safely."
    )


def ending_line(child: Entity, item: MysteryItem, place: Place) -> str:
    return (
        f"In the end, the {item.label} was back where it belonged, near the safe spot in {place.name}, "
        f"and the room felt calm again."
    )


# ---------------------------------------------------------------------------
# Reasoning and narration
# ---------------------------------------------------------------------------

def is_reasonable(place_key: str, item_key: str) -> bool:
    return place_key in PLACES and item_key in ITEMS


def predict_story(world: World, child: Entity, item: MysteryItem) -> dict[str, object]:
    sim = world.copy()
    found = item.location == sim.place.name.split("the ", 1)[-1] or item.location == sim.place.name
    return {
        "found": found,
        "mystery": True,
        "lesson": True,
    }


def tell(place: Place, item: MysteryItem, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the grown-up",
        memes={"worry": 1.0, "relief": 0.0, "trust": 0.0},
    ))
    knife = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        location=place.name,
        hidden=True,
        owner="Parent",
        caretaker="Parent",
        meters={"sharpness": 1.0, "safety": 0.0},
    ))

    world.say(intro_line(child, place))
    world.say(mystery_line(child, item, place))

    world.para()
    if place.name == "the picnic table":
        world.say(
            f"Near the basket, {child.name_word()} noticed a shiny edge under a napkin. "
            f"It was {article(item.label)} {item.label}, and that made the mystery feel bigger."
        )
    else:
        world.say(
            f"Behind a box and beside a hook, {child.name_word()} spotted a little clue. "
            f"It pointed toward the missing {item.label}."
        )

    world.say(f"{child.name_word()} did not grab it, because {child.pronoun()} knew sharp things needed careful hands.")
    child.memes["care"] = 1.0

    world.para()
    world.say(f"Then {child.name_word()} had a flashback.")
    world.say(flashback_line(child, item))
    child.memes["memory"] = 1.0
    parent.memes["trust"] += 1.0

    world.say(
        f"{child.name_word()} told {parent.label} what {child.pronoun()} remembered, and together they checked the safe places first."
    )

    knife.hidden = False
    knife.carried_by = "Parent"
    knife.location = "drawer" if place.name == "the kitchen" else "basket"
    knife.meters["safety"] = 1.0
    world.facts["knife_found"] = True
    world.facts["lesson"] = item.lesson

    world.para()
    world.say(
        f"The clue fit the memory. The {item.label} had been left in the wrong spot, but it was easy to return it."
    )
    world.say(lesson_line(child, item))
    world.say(ending_line(child, item, place))

    world.facts.update(
        child=child,
        parent=parent,
        knife=knife,
        item=item,
        place=place,
        resolved=True,
        child_type=child_type,
        parent_type=parent_type,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    place = f["place"]
    return [
        f'Write a short mystery story for a little child named {child.name_word()} about a missing {item.label}.',
        f"Tell a child-friendly story set at {place.name} that includes a flashback and ends with a lesson learned about a {item.label}.",
        f"Write a gentle story where {child.name_word()} solves a mystery by remembering where the {item.label} belongs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    place = f["place"]
    return [
        QAItem(
            question=f"What mystery did {child.name_word()} notice at {place.name}?",
            answer=f"{child.name_word()} noticed that a {item.label} was missing and tried to solve the mystery.",
        ),
        QAItem(
            question=f"What helped {child.name_word()} remember where the {item.label} belonged?",
            answer=f"A flashback helped {child.name_word()} remember the {item.label} at the family picnic.",
        ),
        QAItem(
            question=f"What lesson was learned about the {item.label}?",
            answer=f"The lesson learned was that {item.lesson}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {item.label} was returned to a safe place, and the mystery was solved calmly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly shows something that happened earlier, so the character remembers an important detail.",
        ),
        QAItem(
            question="Why should a knife be handled carefully?",
            answer="A knife has a sharp edge, so it should be handled carefully to avoid cuts and to keep everyone safe.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the important idea a character understands by the end of the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} " + " ".join(bits))
    out.append(f"facts: {world.facts}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(kitchen;picnic;shed).
item(knife).

missing_knife(P) :- place(P), chosen_place(P), item(knife).

flashback_needed(P) :- chosen_place(P), item(knife), place(P).
lesson_learned(knife) :- flashback_needed(_).

safe_return(knife, P) :- chosen_place(P), place(P).
mystery_story(P) :- chosen_place(P), missing_knife(P), lesson_learned(knife), safe_return(knife, P).

#show mystery_story/1.
#show lesson_learned/1.
#show safe_return/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("chosen_place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models(show: str) -> list[list[object]]:
    import storyworlds.asp as asp
    return asp.solve(asp_program(show), models=0)


def asp_verify() -> int:
    py = {p for p in PLACES}
    if not py:
        print("MISMATCH: no places available.")
        return 1
    models = asp_models("#show mystery_story/1.")
    if not models:
        print("MISMATCH: ASP produced no models.")
        return 1
    print(f"OK: ASP generated {len(models)} model(s) over {len(PLACES)} places.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Knife mystery storyworld with a flashback and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    item = args.item or "knife"
    if not is_reasonable(place, item):
        raise StoryError("Invalid story options: the mystery needs a known place and the knife item.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], params.child_name, params.child_type, params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, "knife") for p in PLACES]
        for i, (place, item) in enumerate(combos):
            params = StoryParams(
                place=place,
                item=item,
                child_name=CHILD_NAMES[i % len(CHILD_NAMES)],
                child_type=["girl", "boy"][i % 2],
                parent_type=["mother", "father"][i % 2],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
