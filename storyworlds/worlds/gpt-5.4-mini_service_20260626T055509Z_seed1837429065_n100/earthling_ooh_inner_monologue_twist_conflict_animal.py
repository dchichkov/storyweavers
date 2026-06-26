#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/earthling_ooh_inner_monologue_twist_conflict_animal.py
=============================================================================================================

A small animal-story world with a tiny conflict, an inner monologue, and a twist.

Premise:
- A curious animal in a quiet place spots an "earthling" and says "ooh".
- The animal wants to approach, but worries about scaring the earthling.
- A misunderstanding creates conflict.
- The twist reveals the earthling is only a garden figurine, not a frightened stranger.
- The animal's inner monologue changes from nervousness to delight.

The world is state-driven: emotions, meters, and physical placement determine the story.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"fox", "cat", "rabbit", "mouse", "bird", "squirrel", "dog"}:
            return mapping[case]
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    kind: str
    affirms: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    type: str
    name: str
    trait: str
    place: str
    curiosity: str
    worry: str
    speech: str


@dataclass
class StoryParams:
    place: str
    animal: str
    earthling_form: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _animal_pronouns(animal: str) -> tuple[str, str, str]:
    return "it", "it", "its"


ANIMALS = {
    "fox": {"name": "fox", "trait": "quick", "curiosity": "peered through the leaves", "worry": "might startle the earthling", "speech": "ooh"},
    "cat": {"name": "cat", "trait": "soft-footed", "curiosity": "watched from the wall", "worry": "might make the earthling jump", "speech": "ooh"},
    "rabbit": {"name": "rabbit", "trait": "bouncy", "curiosity": "stood in the clover", "worry": "might seem too sudden", "speech": "ooh"},
    "bird": {"name": "bird", "trait": "bright-eyed", "curiosity": "leaned from the branch", "worry": "might disturb the quiet", "speech": "ooh"},
}

PLACES = {
    "garden": Place(id="garden", name="the garden", kind="outdoor", affirms={"stillness", "statue"}),
    "yard": Place(id="yard", name="the yard", kind="outdoor", affirms={"stillness", "statue"}),
    "orchard": Place(id="orchard", name="the orchard", kind="outdoor", affirms={"stillness", "statue"}),
}

EARTHLING_FORMS = {
    "figurine": {
        "label": "earthling figurine",
        "phrase": "a tiny earthling-shaped figurine with painted shoes",
        "twist": "It was not a real earthling at all.",
    },
    "statue": {
        "label": "garden statue",
        "phrase": "a little earthling statue with a round face",
        "twist": "It was only a garden statue.",
    },
    "toy": {
        "label": "toy figure",
        "phrase": "a small earthling toy with bright buttons",
        "twist": "It was just a toy on a stone shelf.",
    },
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with inner monologue, conflict, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--earthling-form", choices=EARTHLING_FORMS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    place = args.place or rng.choice(list(PLACES))
    animal = args.animal or rng.choice(list(ANIMALS))
    earthling_form = args.earthling_form or rng.choice(list(EARTHLING_FORMS))
    trait = args.trait or ANIMALS[animal]["trait"]
    name = args.name or rng.choice(["Pip", "Milo", "Tansy", "Nori", "Wren", "Bram"])
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    if earthling_form not in EARTHLING_FORMS:
        raise StoryError("Unknown earthling form.")
    return StoryParams(place=place, animal=animal, earthling_form=earthling_form, name=name, trait=trait)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    animal_def = ANIMALS[params.animal]
    earth_def = EARTHLING_FORMS[params.earthling_form]

    world = World(place)
    animal = world.add(Entity(id="animal", kind="character", type=params.animal, label=params.name))
    earthling = world.add(Entity(id="earthling", kind="thing", type=params.earthling_form, label="earthling", phrase=earth_def["phrase"]))
    animal.memes["curiosity"] = 1
    animal.memes["worry"] = 0
    earthling.location = place.id

    world.say(f"In {place.name}, {params.name} the {params.trait} {params.animal} {animal_def['curiosity']}.")
    world.say(f"Then {params.name} spotted an earthling and said, \"{animal_def['speech']}!\"")

    world.para()
    animal.memes["curiosity"] += 1
    animal.memes["worry"] += 1
    world.say(
        f"{params.name} wanted to go closer, but a small inner monologue whispered, "
        f"\"What if I scare the earthling?\""
    )
    world.say(f"{params.name} kept still and watched from a safe distance.")

    world.para()
    animal.memes["conflict"] = 1
    world.say(
        f"An acorn rolled under {params.name}'s paws, and the earthling tipped sideways with a soft clink."
    )
    world.say(
        f"{params.name} thought, \"Oh no, I made trouble. I should have stayed quiet.\""
    )

    world.para()
    earthling.meters["fallen"] = 1
    world.say(
        f"Then the twist appeared: {earth_def['twist']} It had been sitting on a tiny stone stand all along."
    )
    world.say(
        f"{params.name}'s worry melted away. \"Ooh,\" {params.name} thought, \"I did not frighten anyone after all.\""
    )
    world.say(
        f"With a happy hop, {params.name} nudged the figurine upright and admired the little earthling under the leaves."
    )

    world.facts.update(
        animal=animal,
        earthling=earthling,
        place=place,
        params=params,
        twist=earth_def["twist"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write an animal story in {f["place"].name} where a {p.animal} says "ooh" after seeing an earthling.',
        f"Tell a short story with an inner monologue, a conflict, and a twist about {p.name} the {p.animal}.",
        f"Create a gentle animal tale where {p.name} worries about an earthling, then discovers the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    twist = world.facts["twist"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name} the {p.trait} {p.animal}, who notices an earthling in {world.facts['place'].name}.",
        ),
        QAItem(
            question=f"What did {p.name} say when the earthling appeared?",
            answer='{} said "ooh" and then watched carefully.'.format(p.name),
        ),
        QAItem(
            question="What did the animal worry about in the inner monologue?",
            answer=f"{p.name} worried about scaring the earthling and causing trouble.",
        ),
        QAItem(
            question="What was the twist?",
            answer=twist,
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{p.name} felt relieved, set the little earthling upright, and admired it in the quiet place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an earthling?",
            answer="An earthling is a being from Earth; in this storyworld, the word can also point to a tiny earthling-shaped object.",
        ),
        QAItem(
            question="What does 'ooh' often show?",
            answer="'Ooh' often shows surprise, wonder, or careful curiosity.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or tension that makes the character unsure what to do next.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, shown as words they think to themselves.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the truth look different from what it seemed at first.",
        ),
    ]


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
    lines = [f"--- world trace: {world.place.name} ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", animal="fox", earthling_form="figurine", name="Pip", trait="curious"),
    StoryParams(place="yard", animal="cat", earthling_form="statue", name="Milo", trait="soft-footed"),
    StoryParams(place="orchard", animal="bird", earthling_form="toy", name="Wren", trait="bright-eyed"),
]


ASP_RULES = r"""
animal(A) :- animal_fact(A).
place(P) :- place_fact(P).
earthling_form(E) :- earthling_fact(E).

compatible(P, A, E) :- place_fact(P), animal_fact(A), earthling_fact(E).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal_fact", a))
    for e in EARTHLING_FORMS:
        lines.append(asp.fact("earthling_fact", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show compatible/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(p, a, e) for p in PLACES for a in ANIMALS for e in EARTHLING_FORMS}
    if asp_set != py_set:
        print("MISMATCH between ASP and Python.")
        return 1
    print(f"OK: ASP matches Python ({len(asp_set)} combos).")
    sample = generate(StoryParams(place="garden", animal="fox", earthling_form="figurine", name="Pip", trait="curious"))
    if "ooh" not in sample.story.lower():
        print("MISMATCH: generated story does not include ooh.")
        return 1
    print("OK: generated story exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_combo(args, random.Random(seed))
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for c in combos:
            print(c)
        return

    samples = build_samples(args)
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
            header = f"### {p.name} the {p.animal} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
