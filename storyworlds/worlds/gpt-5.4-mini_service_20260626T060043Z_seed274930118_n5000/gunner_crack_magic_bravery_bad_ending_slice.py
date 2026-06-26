#!/usr/bin/env python3
"""
A small slice-of-life storyworld about Gunner, a crack, a little magic, and
the bravery it takes to face a bad ending without making the day feel broken.

The world is intentionally modest: one child, one beloved object, one small
crack, one gentle magic attempt, and one ending that stays a little sad but
still meaningful.
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
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"crack": 0.0, "clean": 0.0, "fixed": 0.0}
        if not self.memes:
            self.memes = {"love": 0.0, "fear": 0.0, "bravery": 0.0, "sadness": 0.0}


@dataclass
class Place:
    id: str
    label: str
    afford_magic: bool = True
    afford_crack: bool = True
    afford_fix: bool = True


@dataclass
class StoryParams:
    place: str
    object: str
    name: str = "Gunner"
    parent: str = "mom"
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", afford_magic=True, afford_crack=True, afford_fix=True),
    "hallway": Place(id="hallway", label="the hallway", afford_magic=True, afford_crack=True, afford_fix=True),
    "windowseat": Place(id="windowseat", label="the window seat", afford_magic=True, afford_crack=True, afford_fix=False),
}

OBJECTS = {
    "cup": {"label": "cup", "phrase": "a blue cup with tiny stars", "fragile": True, "kind": "cup"},
    "bowl": {"label": "bowl", "phrase": "a small yellow bowl", "fragile": True, "kind": "bowl"},
    "frame": {"label": "frame", "phrase": "a wooden frame with a family picture", "fragile": True, "kind": "frame"},
}

MAGIC_KINDS = {
    "glow": "a warm glow",
    "mend": "a careful mend",
    "whisper": "a soft whisper of magic",
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"crack": 0.0}
        if not self.memes:
            self.memes = {"love": 0.0, "bravery": 0.0, "sadness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.trace: list[str] = []

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


def crack_object(world: World, obj: Entity) -> None:
    if "cracked" not in world.fired:
        obj.meters["crack"] = 1.0
        world.fired.add("cracked")
        world.say(f"One afternoon, {obj.label} got a thin crack along one side.")


def attempt_magic(world: World, obj: Entity, magic: str) -> bool:
    if not world.place.afford_magic:
        return False
    if "magic" in world.fired:
        return False
    world.fired.add("magic")
    if world.place.id == "windowseat":
        world.say(
            f"Gunner held {obj.label} up to the light and tried {MAGIC_KINDS[magic]}. "
            f"The little spell shimmered, but the crack stayed there."
        )
        return False
    obj.meters["fixed"] = 0.4
    world.say(
        f"Gunner whispered {MAGIC_KINDS[magic]} over {obj.label}, and the crack looked a little softer."
    )
    return True


def brave_talk(world: World, hero: Entity, parent: Entity, obj: Entity) -> None:
    if "brave" not in world.fired:
        world.fired.add("brave")
        hero.memes["bravery"] += 1.0
        hero.memes["sadness"] += 1.0
        world.say(
            f"Even so, Gunner took a breath and told {parent.label} about the crack instead of hiding it."
        )
        world.say(
            f"{parent.label.capitalize()} listened, and that made Gunner stand a little straighter."
        )


def bad_ending(world: World, hero: Entity, parent: Entity, obj: Entity) -> None:
    world.say(
        f"In the end, the magic did not fix everything. {obj.label} still had its crack, "
        f"and Gunner still felt the disappointment of that."
    )
    world.say(
        f"But Gunner washed the {obj.label}, set it on the shelf, and kept using it carefully, "
        f"while {parent.label} stayed nearby."
    )


def tell(place: Place, object_id: str, name: str = "Gunner", parent: str = "mom") -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", label=name))
    adult = world.add(Entity(id=parent, kind="character", label=parent))
    cfg = OBJECTS[object_id]
    obj = world.add(Entity(id=object_id, kind="object", label=cfg["label"], phrase=cfg["phrase"]))

    world.say(f"{name} was having a quiet day in {place.label}.")
    world.say(f"{name} liked {obj.phrase} because it made the room feel friendly.")
    world.para()

    crack_object(world, obj)
    world.say(f"Gunner stared at the crack and felt a small twist in his chest.")
    world.say(f"He wanted the day to stay simple, but the crack made the cup feel different.")

    world.para()
    attempt_magic(world, obj, "mend")
    brave_talk(world, hero, adult, obj)
    bad_ending(world, hero, adult, obj)

    world.facts.update(hero=hero, parent=adult, obj=obj, place=place, magic="mend")
    return world


def knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in this story?",
            answer="Magic is a small make-believe force that Gunner tries to use to help the cracked object.",
        ),
        QAItem(
            question="What does bravery mean here?",
            answer="Bravery means telling the truth about the crack even when Gunner feels sad and wishes it were gone.",
        ),
        QAItem(
            question="Why is the ending called bad?",
            answer="It is a bad ending because the crack does not disappear, even after Gunner tries the spell.",
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    obj: Entity = f["obj"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who is called Gunner in {place.label}.",
        ),
        QAItem(
            question=f"What cracked in {place.label}?",
            answer=f"{obj.label.capitalize()} cracked while Gunner was having an ordinary day there.",
        ),
        QAItem(
            question=f"What did Gunner do after the magic did not fully work?",
            answer=f"Gunner bravely told {parent.label} the truth and kept the cracked {obj.label} safely on the shelf.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj: Entity = f["obj"]
    place: Place = f["place"]
    return [
        f'Write a short slice-of-life story about Gunner, a crack, and {obj.label} in {place.label}.',
        f"Tell a gentle story where Gunner tries magic on a cracked {obj.label} but the ending stays a little sad.",
        f"Write a child-friendly story with bravery, magic, and a bad ending in {place.label}.",
    ]


def world_qa(world: World) -> list[QAItem]:
    return knowledge_qa()


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for mk in MAGIC_KINDS:
        lines.append(asp.fact("magic", mk))
    for pid, p in PLACES.items():
        if p.afford_magic:
            lines.append(asp.fact("affords_magic", pid))
        if p.afford_crack:
            lines.append(asp.fact("affords_crack", pid))
        if p.afford_fix:
            lines.append(asp.fact("affords_fix", pid))
    for oid, cfg in OBJECTS.items():
        lines.append(asp.fact("fragile", oid))
        lines.append(asp.fact("label", oid, cfg["label"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,O) :- place(P), object(O), affords_crack(P), affords_magic(P).
bad_ending(P,O) :- valid_story(P,O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    python_set = {(p, o) for p in PLACES for o in OBJECTS if PLACES[p].afford_magic and PLACES[p].afford_crack}
    if atoms == python_set:
        print(f"OK: clingo gate matches Python gate ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate")
    if atoms - python_set:
        print(" only in clingo:", sorted(atoms - python_set))
    if python_set - atoms:
        print(" only in python:", sorted(python_set - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about Gunner, a crack, magic, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--name", default="Gunner")
    ap.add_argument("--parent", choices=["mom", "dad"], default="mom")
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
    obj = args.object_ or rng.choice(list(OBJECTS))
    return StoryParams(place=place, object=obj, name=args.name, parent=args.parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.object, params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="kitchen", object="cup", name="Gunner", parent="mom"),
    StoryParams(place="hallway", object="bowl", name="Gunner", parent="dad"),
    StoryParams(place="windowseat", object="frame", name="Gunner", parent="mom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} / {p.place} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
