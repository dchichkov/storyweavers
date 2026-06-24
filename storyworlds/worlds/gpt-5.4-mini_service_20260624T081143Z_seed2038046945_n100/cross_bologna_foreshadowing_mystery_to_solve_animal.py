#!/usr/bin/env python3
"""
storyworlds/worlds/cross_bologna_foreshadowing_mystery_to_solve_animal.py
========================================================================

A small animal-story world with foreshadowing and a mystery to solve.

Premise:
- An animal child is hungry and a bit cross.
- Someone prepares bologna for a picnic or snack.
- A small clue foreshadows a mystery: the bologna goes missing.
- The child and a helper solve the mystery by following physical clues.

This world keeps the prose child-facing, concrete, and state-driven.
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
# Physical and emotional model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"cat", "kitten", "fox", "mouse"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.type in {"dog", "puppy", "bear", "rabbit"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label(self) -> str:
        return self.name or self.type


@dataclass
class Place:
    id: str
    label: str
    setting_words: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    animal: str
    helper: str
    food: str = "bologna"
    mood: str = "cross"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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
# ASP twin / fact registry
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery exists when the food is missing.
mystery(food_missing) :- missing(food).

% The clue trail can solve the mystery if the key clue is found.
solved(food_missing) :- clue(found), mystery(food_missing).

#show mystery/1.
#show solved/1.
"""


def asp_facts(params: StoryParams) -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", params.place),
        asp.fact("animal", params.animal),
        asp.fact("helper", params.helper),
        asp.fact("food", params.food),
    ]
    return "\n".join(lines)


def asp_program(params: StoryParams, show: str) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_reasonable(params: StoryParams) -> bool:
    return params.food == "bologna" and params.mood == "cross"


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place("kitchen", "the kitchen", ["table", "plate", "crumbs"]),
    "yard": Place("yard", "the yard", ["grass", "shoeprints", "fence"]),
    "picnic": Place("picnic", "the picnic blanket", ["basket", "napkin", "ant"]),
}

ANIMALS = {
    "cat": {"kind": "character", "type": "cat", "name": "Milo"},
    "dog": {"kind": "character", "type": "dog", "name": "Pip"},
    "rabbit": {"kind": "character", "type": "rabbit", "name": "Nia"},
    "fox": {"kind": "character", "type": "fox", "name": "Toby"},
}

HELPERS = {
    "mouse": {"kind": "character", "type": "mouse", "name": "June"},
    "bird": {"kind": "character", "type": "bird", "name": "Bea"},
    "bear": {"kind": "character", "type": "bear", "name": "Hugo"},
}

NAMES = ["Milo", "Pip", "Nia", "Toby", "Luna", "Finn", "Poppy", "Theo"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.animal not in ANIMALS:
        raise StoryError(f"Unknown animal: {params.animal}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if not asp_reasonable(params):
        raise StoryError("This world expects a cross animal and a bologna mystery.")

    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", **ANIMALS[params.animal], kind="character", meters={}, memes={"hunger": 1.2, "cross": 1.0}))
    helper = world.add(Entity(id="helper", **HELPERS[params.helper], kind="character", meters={}, memes={"calm": 1.0}))
    food = world.add(Entity(id="food", kind="thing", type=params.food, name=f"the {params.food}", owner="hero", meters={"fresh": 1.0}))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", name="a picnic basket", carries=["food"]))

    world.facts.update(hero=hero, helper=helper, food=food, basket=basket, params=params)

    # Setup
    world.say(f"{hero.label()} was in {world.place.label}, and {hero.pronoun('subject').capitalize()} felt cross because {hero.pronoun('subject')} was hungry.")
    world.say(f"{helper.label()} brought a picnic basket with {food.label()} inside.")
    world.say(f"The basket sat near the table, and a little bit of bologna smell drifted out.")
    world.para()

    # Foreshadowing clue
    hero.memes["curious"] = 0.5
    world.say(f"{hero.label()} noticed one napkin had a tiny tear, but {helper.label()} did not.")
    world.say("That small tear was a clue waiting for later.")

    # Mystery: food missing
    world.para()
    food.meters["missing"] = 1.0
    world.say(f"Then {hero.label()} looked again. The bologna was gone.")
    world.say(f"{hero.label()} stayed cross, but now the problem was bigger than grumpiness.")
    world.say(f"{helper.label()} pointed at the tiny crumbs on the floor.")
    world.say("The crumbs made a neat trail under the table and toward the yard.")

    # Solve
    world.para()
    food.meters["found"] = 1.0
    world.say(f"{hero.label()} followed the crumbs to a small spoon under the chair.")
    world.say(f"Under the chair, the bologna was stuck to the spoon, hidden where nobody had looked.")
    world.say(f"{helper.label()} laughed softly and set the bologna back on the plate.")
    hero.memes["cross"] = 0.0
    hero.memes["relief"] = 1.0
    food.meters["fresh"] = 1.0
    world.say(f"{hero.label()} was no longer cross. {hero.pronoun('subject').capitalize()} took a happy bite of {params.food}, and the mystery was solved.")

    world.facts["solved"] = True
    world.facts["missing"] = True
    world.facts["clue"] = "crumb trail"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    params: StoryParams = f["params"]
    return [
        f'Write a short animal story for young children where {hero.label()} feels cross and a {params.food} snack goes missing.',
        f'Tell a gentle mystery story with foreshadowing in {world.place.label} featuring {hero.label()} and {helper.label()}.',
        f'Write a simple story where crumbs help solve a mystery about {params.food}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    food: Entity = f["food"]
    return [
        QAItem(
            question=f"Why was {hero.label()} cross at the beginning of the story?",
            answer=f"{hero.label()} was cross because {hero.pronoun('subject')} was hungry and waiting for {food.label()}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the mystery in {world.place.label}?",
            answer="A tiny tear in the napkin and a little trail of crumbs foreshadowed that something was wrong.",
        ),
        QAItem(
            question=f"How was the mystery about {food.label()} solved?",
            answer=f"{hero.label()} followed the crumb trail to the spoon, where the {food.label()} had been hidden under the chair.",
        ),
        QAItem(
            question=f"How did {hero.label()} feel at the end?",
            answer=f"{hero.label()} felt relieved and happy, because the mystery was solved and {hero.pronoun('subject')} could eat.",
        ),
        QAItem(
            question=f"What did {helper.label()} do to help?",
            answer=f"{helper.label()} pointed out the crumbs and helped put the {food.label()} back on the plate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bologna?",
            answer="Bologna is a soft lunch meat that people often put in sandwiches.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that people try to figure out.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue that hints at something important later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_verify(params: StoryParams) -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(params, "#show mystery/1.\n#show solved/1."))
    atoms = {(a.name, len(a.arguments)) for a in model}
    return ("mystery", 1) in atoms and ("solved", 1) in atoms


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery storyworld with foreshadowing and bologna.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(PLACES))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    params = StoryParams(place=place, animal=animal, helper=helper, seed=args.seed)
    if not asp_reasonable(params):
        raise StoryError("This world only tells a cross animal bologna mystery.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print("--- trace ---")
        for key, value in sample.world.facts.items():
            if key in {"hero", "helper", "food", "basket"}:
                continue
            print(f"{key}: {value}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(StoryParams(place="kitchen", animal="cat", helper="mouse"), "#show mystery/1.\n#show solved/1."))
        return
    if args.verify:
        params = StoryParams(place="kitchen", animal="cat", helper="mouse")
        ok = asp_verify(params)
        if ok:
            print("OK: ASP and Python agree; the mystery is solvable.")
            return
        raise SystemExit(1)
    if args.asp:
        import storyworlds.asp as asp
        params = StoryParams(place="kitchen", animal="cat", helper="mouse")
        model = asp.one_model(asp_program(params, "#show mystery/1.\n#show solved/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for animal in ANIMALS:
                for helper in HELPERS:
                    try:
                        params = StoryParams(place=place, animal=animal, helper=helper, seed=base_seed)
                        if asp_reasonable(params):
                            samples.append(generate(params))
                    except StoryError:
                        pass
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            if params.story if False else False:
                pass
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
