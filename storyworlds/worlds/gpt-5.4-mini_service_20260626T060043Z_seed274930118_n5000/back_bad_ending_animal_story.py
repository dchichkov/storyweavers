#!/usr/bin/env python3
"""
storyworlds/worlds/back_bad_ending_animal_story.py
===================================================

A small animal story world with a clear turn and a bad ending.

Premise:
- A little animal wants to go out and play.
- The animal notices something important is missing.
- It must go back to get it, but the return trip goes wrong.

This world is intentionally tiny and classical:
- one animal protagonist
- one important object
- one place
- one bad ending, driven by the simulation state

The prose is child-facing, concrete, and state-driven. The ending is sad,
not because of arbitrary narration, but because the world model tracks that
the object stays lost or damaged after the attempt to go back.
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
# World data model
# ---------------------------------------------------------------------------

@dataclass
class Animal:
    id: str
    species: str
    name: str
    kind: str = "character"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return f"{self.name} the {self.species}"


@dataclass
class Place:
    id: str
    label: str
    risky: bool = False
    has_path_back: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    owner: str
    lost: bool = False
    damaged: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    species: str
    name: str
    place: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.steps: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.steps.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ANIMALS = {
    "rabbit": {"boyish": False},
    "fox": {"boyish": False},
    "bear": {"boyish": False},
    "cat": {"boyish": False},
    "dog": {"boyish": False},
    "squirrel": {"boyish": False},
}

PLACES = {
    "meadow": Place(id="meadow", label="the meadow", risky=True, has_path_back=True),
    "woods": Place(id="woods", label="the woods", risky=True, has_path_back=True),
    "hill": Place(id="hill", label="the hill", risky=True, has_path_back=False),
    "riverbank": Place(id="riverbank", label="the riverbank", risky=True, has_path_back=True),
}

OBJECTS = {
    "ball": {"label": "ball", "phrase": "a bright red ball"},
    "bell": {"label": "bell", "phrase": "a tiny silver bell"},
    "hat": {"label": "hat", "phrase": "a soft blue hat"},
    "lantern": {"label": "lantern", "phrase": "a small lantern"},
}

NAMES = ["Milo", "Pip", "Nina", "Toby", "Luna", "Kiki", "Bram", "Mika"]
SPECIES = ["rabbit", "fox", "bear", "cat", "dog", "squirrel"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The object is at risk if the place is risky and the animal leaves it there.
at_risk(P, O) :- risky(P), object(O), left_behind(O, P).

% A bad ending happens when the animal tries to go back but cannot recover the object.
bad_end(A, O, P) :- animal(A), object(O), place(P), at_risk(P, O), tried_to_go_back(A, P), not recovered(O).

#show at_risk/2.
#show bad_end/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
        if p.has_path_back:
            lines.append(asp.fact("path_back", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"Cannot run ASP verify: {exc}")
        return 1
    model = asp.one_model(asp_program("#show at_risk/2."))
    # Tiny parity gate: every risky place should imply some at-risk atom only
    # when combined with the Python generator. Here we just ensure program runs.
    if model is None:
        print("ASP program did not produce a model.")
        return 1
    print("OK: ASP program parsed and solved.")
    return 0

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a bad ending and a back turn.")
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--name")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", dest="object_", choices=sorted(OBJECTS))
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

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if not place.risky:
            continue
        for obj_id in OBJECTS:
            combos.append((place_id, obj_id))
    return combos

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_:
        combos = [c for c in combos if c[1] == args.object_]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, obj = rng.choice(combos)
    species = args.species or rng.choice(SPECIES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(species=species, name=name, place=place, object=obj)

def _intro(world: World, animal: Animal, obj: ObjectThing) -> None:
    world.say(f"{animal.name} was a little {animal.species} who loved to play outside.")
    world.say(f"{animal.name} had {obj.phrase}, and {animal.pronoun('possessive')} eyes shone whenever {obj.label} was near.")

def _go_out(world: World, animal: Animal, place: Place, obj: ObjectThing) -> None:
    world.say(f"One day, {animal.name} went to {place.label} with {obj.label}.")
    world.say(f"The grass was soft, and the day felt bright and easy.")

def _lose_object(world: World, animal: Animal, place: Place, obj: ObjectThing) -> None:
    obj.lost = True
    world.say(f"Then {obj.label} rolled away and disappeared in the grass.")
    world.say(f"{animal.name} looked and looked, but {obj.label} was nowhere to be seen.")

def _go_back(world: World, animal: Animal, place: Place, obj: ObjectThing) -> None:
    world.say(f"{animal.name} had to go back and look for {obj.label}.")
    if not place.has_path_back:
        animal.memes["worry"] = animal.memes.get("worry", 0) + 1
        world.say(f"But the way back was hard, and the path was too steep and tangled.")
        return
    animal.memes["worry"] = animal.memes.get("worry", 0) + 1
    world.say(f"{animal.name} hurried back, paws pattering fast.")

def _bad_turn(world: World, animal: Animal, place: Place, obj: ObjectThing) -> None:
    if place.has_path_back:
        obj.damaged = True
        world.say(f"By the time {animal.name} got back, the wind had pushed {obj.label} under a bush.")
        world.say(f"It was scratched and muddy, and it still was not the same.")
    else:
        world.say(f"When {animal.name} finally stopped, the sun was low and the day was almost gone.")
        world.say(f"{obj.label} was still lost, and {animal.name} had to go home empty-pawed.")

def _ending(world: World, animal: Animal, obj: ObjectThing, place: Place) -> None:
    if obj.damaged:
        world.say(f"{animal.name} went home holding {animal.pronoun('possessive')} empty paws, sad and quiet.")
        world.say(f"That night, {animal.name} kept the broken {obj.label} by the bed and did not want to play.")
    else:
        world.say(f"{animal.name} went home without {obj.label}, feeling small and tired.")
        world.say(f"The meadow stayed dark, and the little {animal.species} had to remember the lost {obj.label}.")

def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    obj_cfg = OBJECTS[params.object]
    world = World(place)
    animal = world.add(Animal(id="hero", species=params.species, name=params.name))
    obj = world.add(ObjectThing(id="object", label=obj_cfg["label"], phrase=obj_cfg["phrase"], owner=animal.id))

    _intro(world, animal, obj)
    world.para()
    _go_out(world, animal, place, obj)
    _lose_object(world, animal, place, obj)
    world.para()
    _go_back(world, animal, place, obj)
    _bad_turn(world, animal, place, obj)
    world.para()
    _ending(world, animal, obj, place)

    world.facts = {
        "animal": animal,
        "place": place,
        "object": obj,
        "bad_end": True,
        "went_back": True,
        "lost": obj.lost,
        "damaged": obj.damaged,
    }
    return world

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

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal: Animal = f["animal"]
    place: Place = f["place"]
    obj: ObjectThing = f["object"]
    return [
        f"Write a short animal story where {animal.name} goes to {place.label} and loses {obj.label}, then has to go back.",
        f"Tell a simple story for a young child about {animal.name} the {animal.species}, {obj.label}, and a sad ending.",
        f"Write an Animal Story style tale with the word back in it and an ending where {obj.label} is still lost or ruined.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal: Animal = f["animal"]
    place: Place = f["place"]
    obj: ObjectThing = f["object"]
    ans1 = f"{animal.name} is the little {animal.species} in the story."
    ans2 = f"{animal.name} went to {place.label} and lost {obj.label} there."
    ans3 = f"The story ends badly because {obj.label} is still { 'damaged' if obj.damaged else 'lost' } when {animal.name} goes home."
    return [
        QAItem(question=f"Who is the story about?", answer=ans1),
        QAItem(question=f"Where did {animal.name} go?", answer=ans2),
        QAItem(question="How does the story end?", answer=ans3),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does back mean in a story like this?", answer="Back means to return to where you were before."),
        QAItem(question="Why do animals look for lost things?", answer="They look for lost things because those things matter to them and they want them back."),
        QAItem(question="What is a sad ending?", answer="A sad ending is when the problem does not get fixed and the character leaves unhappy."),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    f = world.facts
    animal: Animal = f["animal"]
    obj: ObjectThing = f["object"]
    place: Place = f["place"]
    return "\n".join([
        "--- trace ---",
        f"animal={animal.name} species={animal.species} worry={animal.memes.get('worry', 0)}",
        f"place={place.label} risky={place.risky} path_back={place.has_path_back}",
        f"object={obj.label} lost={obj.lost} damaged={obj.damaged}",
    ])

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/2."))
    return sorted(set(asp.atoms(model, "at_risk")))

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show at_risk/2.\n#show bad_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show at_risk/2.\n#show bad_end/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place_id, obj_id in sorted(valid_combos()):
            params = StoryParams(
                species="rabbit",
                name="Milo",
                place=place_id,
                object=obj_id,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_:
        combos = [c for c in combos if c[1] == args.object_]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, obj = rng.choice(combos)
    species = args.species or rng.choice(SPECIES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(species=species, name=name, place=place, object=obj)

if __name__ == "__main__":
    main()
