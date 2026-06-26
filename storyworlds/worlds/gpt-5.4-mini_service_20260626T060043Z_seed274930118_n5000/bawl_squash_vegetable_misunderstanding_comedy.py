#!/usr/bin/env python3
"""
storyworlds/worlds/bawl_squash_vegetable_misunderstanding_comedy.py
=====================================================================

A small comedy storyworld about a child, a vegetable, and a misunderstanding.

Seed tale:
---
A child in the kitchen spots a big squash on the table and starts to bawl.
The grown-up thinks the child is upset about dinner, but the child is actually
upset that the squash has a face drawn on it and looks funny enough to giggle.
After a silly misunderstanding, they both laugh, chop the squash into soup,
and eat dinner together.

This world turns that premise into a small simulation:
- a child has emotions and a physical appetite for a veggie-related task
- a vegetable may be mistaken for a toy, a face, or a costume piece
- a bawl can mean loud crying, but also can be misread as dramatic noise
- the misunderstanding is resolved by showing the real intention

The story stays child-facing and authored, with a clear turn and resolution.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    veggie: str
    misunderstanding: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


PLACES = {
    "kitchen": "the kitchen",
    "garden": "the garden",
    "cafeteria": "the cafeteria",
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Max"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
MISUNDERSTANDINGS = [
    "thought the child was crying because the squash was for dinner",
    "thought the child had dropped the bowl",
    "thought the child was scared of the vegetable's funny face",
    "thought the child did not want to help",
]


VEGETABLES = {
    "squash": {
        "label": "squash",
        "phrase": "a round orange squash",
        "kind": "vegetable",
        "color": "orange",
        "can_be_face": True,
        "can_be_food": True,
        "can_be_joke": True,
    },
    "carrot": {
        "label": "carrot",
        "phrase": "a long bright carrot",
        "kind": "vegetable",
        "color": "orange",
        "can_be_face": False,
        "can_be_food": True,
        "can_be_joke": False,
    },
    "broccoli": {
        "label": "broccoli",
        "phrase": "a fluffy green broccoli crown",
        "kind": "vegetable",
        "color": "green",
        "can_be_face": False,
        "can_be_food": True,
        "can_be_joke": True,
    },
}


def _capitalize_first(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about a bawl, a squash, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--veggie", choices=VEGETABLES.keys())
    ap.add_argument("--misunderstanding", choices=range(len(MISUNDERSTANDINGS)), type=int)
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
    place = args.place or rng.choice(list(PLACES.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    veggie = args.veggie or rng.choice(list(VEGETABLES.keys()))
    misunderstanding = args.misunderstanding
    if misunderstanding is None:
        misunderstanding = rng.randrange(len(MISUNDERSTANDINGS))
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent,
        veggie=veggie,
        misunderstanding=MISUNDERSTANDINGS[misunderstanding],
    )


def _child_title(hero: Entity) -> str:
    return hero.id


def _hero_desc(hero: Entity) -> str:
    return f"little {hero.memes.get('trait', 'silly')} {hero.type}"


def setup_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label=f"the {params.parent_type}"))
    veg_cfg = VEGETABLES[params.veggie]
    veg = world.add(Entity(
        id=params.veggie,
        kind="thing",
        type=veg_cfg["kind"],
        label=veg_cfg["label"],
        phrase=veg_cfg["phrase"],
        caretaker=parent.id,
    ))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label="bowl"))
    hero.memes["trait"] = random.choice(["curious", "silly", "playful", "cheery"])
    world.facts.update(hero=hero, parent=parent, veggie=veg, bowl=bowl, params=params)
    return world


def introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]
    veg: Entity = world.facts["veggie"]
    world.say(f"{hero.id} was a {_hero_desc(hero)} who loved finding funny things in {world.place}.")
    world.say(f"On the table sat {veg.phrase}, looking as important as a king's hat.")


def want_and_bawl(world: World) -> None:
    hero: Entity = world.facts["hero"]
    veg: Entity = world.facts["veggie"]
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    hero.memes["noise"] = hero.memes.get("noise", 0) + 1
    world.say(f"{hero.id} wanted to make soup with the {veg.label}, but {veg.label} had a face drawn on it.")
    world.say(f"So {hero.id} started to bawl, loud and round, like a tiny trumpet with a wobble.")
    hero.memes["bawl"] = hero.memes.get("bawl", 0) + 1


def misunderstanding_scene(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    veg: Entity = world.facts["veggie"]
    clue = world.facts["params"].misunderstanding
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    world.say(f"{parent.label.capitalize()} heard the noise and {clue}.")
    world.say(f'"Oh no," {parent.id} said. "Do you dislike the {veg.label}?"')


def reveal_and_laugh(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    veg: Entity = world.facts["veggie"]
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0) + 1
    world.say(f"{hero.id} wiped their eyes and pointed at the silly face on the {veg.label}.")
    world.say(f'"No!" {hero.id} said. "I was bawling because it looks so funny!"')
    world.say(f"{parent.label.capitalize()} blinked, then burst out laughing so hard the spoon shook in the bowl.")
    world.say(f"Together they peeled the {veg.label}, chopped it up, and made soup that smelled warm and sweet.")


def ending_image(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    veg: Entity = world.facts["veggie"]
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(f"By dinner time, {hero.id} was smiling, {parent.label} was smiling, and the {veg.label} was in the pot.")
    world.say(f"The funny face was gone, the misunderstanding was gone, and the kitchen felt full of giggles.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    want_and_bawl(world)
    misunderstanding_scene(world)
    world.para()
    reveal_and_laugh(world)
    ending_image(world)
    veg: Entity = world.facts["veggie"]
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    world.facts["resolved"] = True
    world.facts["theme"] = "misunderstanding"
    world.facts["comedy"] = True
    world.facts["final_image"] = f"{hero.id} and {parent.label} laughing over {veg.label} soup"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    veg: Entity = f["veggie"]
    place = world.place
    return [
        f'Write a short comedy story for a young child about a misunderstanding in {place} involving a {veg.label}.',
        f"Tell a funny story where {hero.id} starts to bawl, but {parent.label} misreads it and later realizes the truth.",
        f"Write a gentle, silly story with a vegetable, a loud bawl, and a happy ending in the {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    veg: Entity = f["veggie"]
    return [
        QAItem(
            question=f"Why did {hero.id} bawl when they saw the {veg.label}?",
            answer=f"{hero.id} bawled because the {veg.label} had a funny face drawn on it, and it looked silly enough to make them cry-laugh.",
        ),
        QAItem(
            question=f"What did {parent.label} misunderstand about {hero.id}'s bawling?",
            answer=f"{parent.label.capitalize()} thought {hero.id} was upset about the {veg.label} being for dinner, but {hero.id} was really reacting to the funny face.",
        ),
        QAItem(
            question=f"What happened after the misunderstanding was cleared up?",
            answer=f"{hero.id} and {parent.label} laughed together, chopped the {veg.label}, and made soup.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable?",
            answer="A vegetable is a plant part people often eat, like squash, carrots, or broccoli.",
        ),
        QAItem(
            question="What does bawl mean?",
            answer="To bawl means to cry loudly or make a big noisy sob.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not yet know the real meaning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="kitchen", hero_name="Mia", hero_type="girl", parent_type="mother", veggie="squash", misunderstanding=MISUNDERSTANDINGS[0]),
    StoryParams(place="garden", hero_name="Leo", hero_type="boy", parent_type="father", veggie="broccoli", misunderstanding=MISUNDERSTANDINGS[2]),
    StoryParams(place="cafeteria", hero_name="Nora", hero_type="girl", parent_type="father", veggie="carrot", misunderstanding=MISUNDERSTANDINGS[1]),
]


ASP_RULES = r"""
place(kitchen). place(garden). place(cafeteria).
hero_name(mia). hero_name(leo). hero_name(nora). hero_name(ben). hero_name(ava). hero_name(theo). hero_name(lily). hero_name(max).
hero_type(girl). hero_type(boy).
parent_type(mother). parent_type(father).
veggie(squash). veggie(carrot). veggie(broccoli).

misunderstanding(0). misunderstanding(1). misunderstanding(2). misunderstanding(3).

story(P, H, T, Par, V, M) :- place(P), hero_name(H), hero_type(T), parent_type(Par), veggie(V), misunderstanding(M).
#show story/6.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero_name", h))
    for t in HERO_TYPES:
        lines.append(asp.fact("hero_type", t))
    for p in PARENT_TYPES:
        lines.append(asp.fact("parent_type", p))
    for v in VEGETABLES:
        lines.append(asp.fact("veggie", v))
    for i in range(len(MISUNDERSTANDINGS)):
        lines.append(asp.fact("misunderstanding", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show story/6."))
    atoms = asp.atoms(model, "story")
    py = set()
    for p in PLACES:
        for h in HERO_NAMES:
            for t in HERO_TYPES:
                for par in PARENT_TYPES:
                    for v in VEGETABLES:
                        for m in range(len(MISUNDERSTANDINGS)):
                            py.add((p, h, t, par, v, m))
    asp_set = set(atoms)
    if asp_set == py:
        print(f"OK: ASP parity matches ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python registry space.")
    return 1


def build_story_from_args(args: argparse.Namespace, seed: int) -> StoryParams:
    rng = random.Random(seed)
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            params = build_story_from_args(args, seed)
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
            header = f"### {p.hero_name}: {p.veggie} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
