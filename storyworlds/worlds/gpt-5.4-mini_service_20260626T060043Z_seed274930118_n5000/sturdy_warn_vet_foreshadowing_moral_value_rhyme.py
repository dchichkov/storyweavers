#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a sturdy little pet, a warning, and a vet visit.

Premise:
- A child loves a sturdy little animal and wants to let it keep playing.
- A clue in the weather or behavior foreshadows trouble.
- A wise warning is ignored at first, then a vet explains the problem.
- The child learns a moral value: caring early is kinder than waiting.
- The prose keeps a gentle, rhyming cadence.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Pet:
    id: str
    species: str
    label: str
    phrase: str
    sturdy: bool = True
    sick_threshold: float = 1.0
    likes: str = "a romp in the yard"


@dataclass
class Place:
    id: str
    label: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    pet: str
    child_name: str
    child_gender: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, pet: Pet):
        self.place = place
        self.pet = pet
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self, text: str) -> None:
        self.trace_log.append(text)


PLACES = {
    "yard": Place(id="yard", label="the sunny yard", weather="sunny", affords={"play", "sniff", "dig"}),
    "barn": Place(id="barn", label="the old barn", weather="dusty", affords={"play", "sniff"}),
    "lane": Place(id="lane", label="the windy lane", weather="windy", affords={"walk", "sniff"}),
}

PETS = {
    "puppy": Pet(id="puppy", species="dog", label="puppy", phrase="a sturdy little puppy", likes="chasing a red ball"),
    "kitten": Pet(id="kitten", species="cat", label="kitten", phrase="a sturdy little kitten", likes="pouncing on yarn"),
    "duckling": Pet(id="duckling", species="duck", label="duckling", phrase="a sturdy little duckling", likes="waddling by the puddle"),
}

GIRL_NAMES = ["Mina", "Lily", "Tess", "Nora", "Ava"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Max"]
ADULTS = ["mother", "father", "grandma", "grandpa"]

ASP_RULES = r"""
#show valid/2.

warning_needed(P) :- pet(P), foreshadow(P), risk(P).
resolved(P) :- warning_needed(P), vet_visit(P).
valid(Place, Pet) :- place(Place), pet(Pet), cares_for(Place, Pet).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
        lines.append(asp.fact("weather", pid, p.weather))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        lines.append(asp.fact("species", pid, pet.species))
    lines.append(asp.fact("foreshadow", "puppy"))
    lines.append(asp.fact("risk", "puppy"))
    lines.append(asp.fact("vet_visit", "puppy"))
    lines.append(asp.fact("cares_for", "yard", "puppy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("yard", "puppy")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: sturdy pet, warning, vet, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULTS)
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
    if args.place and args.pet and (args.place, args.pet) not in combos:
        raise StoryError("No valid sturdy story fits those choices.")
    place, pet = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    if args.place:
        place = args.place
    if args.pet:
        pet = args.pet
    return StoryParams(place=place, pet=pet, child_name=name, child_gender=gender, adult=adult)


def rhyme(lines: list[str]) -> str:
    return " ".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    pet = PETS[params.pet]
    world = World(place, pet)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult, label=f"the {params.adult}"))
    pet_ent = world.add(Entity(id=pet.id, kind="character", type=pet.species, label=pet.label, phrase=pet.phrase, caretaker=adult.id))
    pet_ent.meters["energy"] = 1.0
    pet_ent.memes["happy"] = 1.0

    # Act 1
    world.say(f"On a bright little day, in {place.label}, there lived {pet.phrase}.")
    world.say(f"{child.id} loved {pet_ent.label}, and both of them played; {pet.likes} was their merry display.")
    world.say(f"It looked very sturdy, so strong and so spry, but a small cloudy clue drifted into the sky.")
    world.say(f"The wind gave a whisper, a hush and a hum, as if something was coming before it could come.")

    # Act 2
    world.say(f"{child.id} wanted to play, though {params.adult} could see, that the rosy-cheeked pet was not quite as it should be.")
    world.say(f'"Do not run too far," said {params.adult}, "please wait." But {child.id} still ran on, to a bouncy bright gate.')
    pet_ent.meters["tired"] = 1.0
    pet_ent.meters["cough"] = 1.0
    world.trace("foreshadowed tiredness and cough")
    world.say(f"Then came a small cough, like a knock on a door, and the sturdy pet sat down on the grass by the floor.")

    # Act 3
    world.say(f"{params.adult} said, " + '"We should go see the vet; early care is the kindest bet."')
    world.say(f"So off they went briskly, no fuss and no fret, to the gentle old office of a friendly vet.")
    world.say(f'The vet gave a look, with a warm knowing nod: "A rest and a checkup are part of the job."')
    world.say(f"{child.id} learned a sweet lesson, both careful and true: a warning can save a small friend from feeling too blue.")
    world.say(f"By evening, the pet was at home in the light, curled up and content, snug, safe, and all right.")

    world.facts.update(child=child, adult=adult, pet=pet_ent, place=place, params=params)
    prompts = [
        f"Write a nursery-rhyme story about {params.child_name}, a sturdy {pet.label}, a warning, and a vet.",
        f"Tell a gentle rhyme where a child learns why it is wise to listen before a pet gets sick.",
        f"Write a short moral-value story with foreshadowing and a vet visit in {place.label}.",
    ]
    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {params.child_name} and a sturdy little {pet.label} who play together in {place.label}.",
        ),
        QAItem(
            question=f"What warning did {params.adult} give?",
            answer=f"{params.adult.capitalize()} warned {params.child_name} not to run too far, because the pet already seemed tired.",
        ),
        QAItem(
            question=f"Why did they visit the vet?",
            answer="They visited the vet because a small cough and tiredness foreshadowed that the pet needed careful help.",
        ),
        QAItem(
            question=f"What moral value does the story teach?",
            answer="It teaches that listening early and caring kindly can help a friend before trouble grows big.",
        ),
    ]
    world_qa = [
        QAItem(question="What does a vet do?", answer="A vet is an animal doctor who helps pets stay healthy and checks when they seem ill."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a clue that hints something important may happen later in the story."),
        QAItem(question="What does sturdy mean?", answer="Sturdy means strong and not easy to knock over or break."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.label} weather={world.place.weather}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [StoryParams(place="yard", pet="puppy", child_name="Mina", child_gender="girl", adult="mother")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:")
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
