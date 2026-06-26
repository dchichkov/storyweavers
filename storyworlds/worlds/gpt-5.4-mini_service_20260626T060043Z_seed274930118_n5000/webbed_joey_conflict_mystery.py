#!/usr/bin/env python3
"""
storyworlds/worlds/webbed_joey_conflict_mystery.py
===================================================

A small mystery storyworld about a curious child, a webbed clue, and a conflict
that gets untangled by looking closely.

Premise:
- Joey notices a strange webbed mark near a quiet place.
- Another character is blamed too quickly.
- Joey investigates the clue, learns what really happened, and the tension eases.

The world is deliberately tiny: a single clue, a few suspects, one conflict, and
one resolution that changes what the characters believe.
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

MYSTERY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the garden"
    clue: str = "webbed"
    mood: str = "quiet"
    rain: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    friend: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about Joey and a webbed clue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
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


PLACES = {
    "garden": Scene(place="the garden", clue="webbed", mood="quiet", rain=False),
    "pond": Scene(place="the pond", clue="webbed", mood="still", rain=True),
    "shed": Scene(place="the shed", clue="webbed", mood="hushed", rain=False),
}

CLUES = {
    "webbed": "webbed",
    "muddy": "muddy",
    "shiny": "shiny",
}

FRIENDS = {
    "Mina": "girl",
    "Theo": "boy",
    "Iris": "girl",
    "Ned": "boy",
}

SUSPECTS = {
    "duck": "duck",
    "cat": "cat",
    "raccoon": "raccoon",
    "frog": "frog",
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, scene in PLACES.items():
        for clue in CLUES:
            if clue == "webbed" and scene.place in {"the garden", "the pond"}:
                combos.append((place, clue))
    return combos


ASP_RULES = r"""
valid(Place, Clue) :- place(Place), clue(Clue), clue_fit(Place, Clue).
clue_fit(garden, webbed).
clue_fit(pond, webbed).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue:
        if (args.place, args.clue) not in valid_combos():
            raise StoryError("That clue does not fit the chosen place.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not combos:
        raise StoryError("No valid mystery fits those options.")
    place, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(sorted(FRIENDS))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    return StoryParams(place=place, clue=clue, name=name, friend=friend, suspect=suspect)


def _narrate_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a careful child who noticed tiny details. "
        f"{friend.id} liked staying close when things felt strange."
    )


def _narrate_clue(world: World, hero: Entity) -> None:
    world.say(
        f"One quiet day, {hero.id} found a {world.scene.clue} mark near {world.scene.place}."
    )
    world.say(
        f"It looked like a little print with thin lines, as if something had slipped away in a hurry."
    )


def _narrate_conflict(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    suspect.memes["blamed"] = suspect.memes.get("blamed", 0) + 1
    world.say(
        f"Before anyone looked closely, the grown-ups blamed the {suspect.label}."
    )
    world.say(
        f"{hero.id} did not think that was fair, and the room grew tense."
    )


def _narrate_investigation(world: World, hero: Entity, suspect: Entity) -> None:
    hero.meters["looking"] = hero.meters.get("looking", 0) + 1
    world.say(
        f"{hero.id} knelt down and studied the mark again."
    )
    world.say(
        f"The lines were webbed, so the clue had come from a {suspect.label}, not from a naughty mess."
    )


def _narrate_resolution(world: World, hero: Entity, friend: Entity, suspect: Entity) -> None:
    suspect.memes["blamed"] = 0
    world.say(
        f"{hero.id} showed the careful clue to everyone, and the blame lifted off the {suspect.label}."
    )
    world.say(
        f"{friend.id} smiled, the tension went soft, and the quiet place felt peaceful again."
    )


def tell(scene: Scene, hero_name: str, friend_name: str, suspect_name: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Joey", "Theo", "Ned"} else "girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type=FRIENDS[friend_name]))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=SUSPECTS[suspect_name], label=suspect_name))

    _narrate_intro(world, hero, friend)
    world.para()
    _narrate_clue(world, hero)
    _narrate_conflict(world, hero, suspect)
    world.para()
    _narrate_investigation(world, hero, suspect)
    _narrate_resolution(world, hero, friend, suspect)

    world.facts.update(hero=hero, friend=friend, suspect=suspect, scene=scene)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    scene = f["scene"]
    return [
        f'Write a short mystery story for a young child about {hero.id}, a {world.scene.clue} clue, and a mistaken accusation.',
        f'Tell a gentle mystery where {hero.id} finds something {world.scene.clue} near {scene.place} and proves the {suspect.label} was not at fault.',
        "Write a child-friendly detective story with a tense middle and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    suspect = f["suspect"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"Who found the {scene.clue} clue?",
            answer=f"{hero.id} found the {scene.clue} clue near {scene.place}.",
        ),
        QAItem(
            question=f"Why did the story feel tense?",
            answer=f"It felt tense because people blamed the {suspect.label} too quickly, and {hero.id} thought that was not fair.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer=f"{hero.id} looked closely at the clue, noticed it was webbed, and showed everyone that the {suspect.label} was not the cause.",
        ),
        QAItem(
            question=f"How did {friend.id} feel at the end?",
            answer=f"{friend.id} felt calm and happy when the blame went away and the place became peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for a clue to be webbed?",
            answer="A webbed clue has thin lines that cross over each other, like the threads in a web.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out what really happened.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.name, params.friend, params.suspect)
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
    StoryParams(place="garden", clue="webbed", name="Joey", friend="Mina", suspect="duck"),
    StoryParams(place="pond", clue="webbed", name="Joey", friend="Theo", suspect="frog"),
    StoryParams(place="shed", clue="webbed", name="Joey", friend="Iris", suspect="raccoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, clue in combos:
            print(f"  {place:8} {clue}")
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
        header = "### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
