#!/usr/bin/env python3
"""
A small storyworld about a child, a relative, a mystery, a misunderstanding,
and a kind reveal.

The core premise is simple: something goes missing, the child suspects a
relative, and the truth turns out to be a kind surprise rather than a theft.
The world model tracks physical objects, locations, and emotional state so the
story can unfold causally instead of as a frozen paragraph.
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
    location: str = ""
    held_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother", "sister", "cousin"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather", "brother", "cousin"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    text: str
    location: str
    points_to: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: dict[str, Clue] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy
        return World(
            place=_copy.deepcopy(self.place),
            entities=_copy.deepcopy(self.entities),
            clues=_copy.deepcopy(self.clues),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    relative: str
    object: str
    seed: Optional[int] = None


PLACES = {
    "house": Place("house", "the house", indoors=True, clues=["hallway", "kitchen", "porch"]),
    "cottage": Place("cottage", "the cottage", indoors=True, clues=["front room", "stair", "windowsill"]),
    "apartment": Place("apartment", "the apartment", indoors=True, clues=["table", "closet", "balcony"]),
}

RELATIVES = {
    "aunt": {"type": "aunt", "label": "Aunt", "kindness": "kind"},
    "uncle": {"type": "uncle", "label": "Uncle", "kindness": "kind"},
    "grandmother": {"type": "grandmother", "label": "Grandma", "kindness": "gentle"},
    "grandfather": {"type": "grandfather", "label": "Grandpa", "kindness": "gentle"},
    "cousin": {"type": "cousin", "label": "Cousin", "kindness": "helpful"},
}

OBJECTS = {
    "key": {"label": "key", "phrase": "a small brass key", "hidden_in": "flowerpot"},
    "cookie": {"label": "cookie", "phrase": "a plate of star cookies", "hidden_in": "oven"},
    "book": {"label": "book", "phrase": "a picture book with a blue ribbon", "hidden_in": "chair"},
    "toy": {"label": "toy", "phrase": "a tiny red toy car", "hidden_in": "basket"},
    "note": {"label": "note", "phrase": "a folded note with a smiley face", "hidden_in": "pocket"},
}

CHILD_NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ivy", "Ava", "Zoe"],
    "boy": ["Leo", "Ben", "Noah", "Finn", "Eli", "Max"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about a relative and a kind misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relative", choices=RELATIVES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    relative = args.relative or rng.choice(list(RELATIVES))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    if args.object == "cookie" and relative == "cousin":
        raise StoryError("This mystery needs a relative who plausibly prepares a surprise, not an equal child for the cookie case.")
    return StoryParams(place=place, child_name=name, child_gender=gender, relative=relative, object=obj)


def select_relative_label(relative: str) -> str:
    return RELATIVES[relative]["label"]


def intro_lines(world: World, child: Entity, relative: Entity, obj: Entity) -> None:
    world.say(
        f"{child.id} lived in {world.place.label} and loved neat, ordinary days."
        f" But one morning, {child.pronoun('possessive')} {obj.label} was missing."
    )
    world.say(
        f"{child.id} noticed a tiny trail of clues, and {child.pronoun()} began to wonder about "
        f"{relative.label}."
    )


def add_clues(world: World, obj: Entity, relative: Entity) -> None:
    hidden_spot = OBJECTS[obj.type]["hidden_in"]
    world.clues["trail"] = Clue("trail", "a few dusty footprints near the hallway", "hallway", relative.id)
    world.clues["smile"] = Clue("smile", "a scrap of paper with a smiling doodle", "table", relative.id)
    world.clues["rustle"] = Clue("rustle", "a soft rustle from the kitchen", "kitchen", relative.id)
    obj.location = hidden_spot
    obj.hidden = True
    relative.meters["suspicion"] = 0.0


def observe_clue(world: World, child: Entity, clue: Clue) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} found {clue.text}. That made {child.pronoun('object')} more curious, because the clue seemed to point toward {world.get(clue.points_to).label}."
    )


def suspect(world: World, child: Entity, relative: Entity, obj: Entity) -> None:
    child.memes["suspicion"] = child.memes.get("suspicion", 0.0) + 1
    relative.memes["hurt"] = relative.memes.get("hurt", 0.0) + 1
    world.say(
        f"{child.id} thought {relative.label} had taken {child.pronoun('possessive')} {obj.label}. "
        f"{relative.label} looked surprised and a little hurt."
    )


def reveal_kindness(world: World, child: Entity, relative: Entity, obj: Entity) -> None:
    relative.memes["kindness"] = relative.memes.get("kindness", 0.0) + 1
    child.memes["shame"] = child.memes.get("shame", 0.0) + 1
    obj.hidden = False
    obj.held_by = child.id
    world.say(
        f"Then {relative.label} pointed to {obj.location} and said, "
        f"'"I hid it to make you a surprise."'
    )
    world.say(
        f"{relative.label} had not taken {obj.label} away at all. {relative.label} had wrapped it with a ribbon and hidden it so {child.id} could find it after lunch."
    )
    world.say(
        f"{child.id}'s cheeks got warm. {child.id} realized the mystery was really a kind surprise."
    )


def closing_image(world: World, child: Entity, relative: Entity, obj: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(
        f"{child.id} smiled, hugged {relative.pronoun('object')}, and held {child.pronoun('possessive')} {obj.label} close. "
        f"In the quiet house, the clues no longer looked scary; they looked kind."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, label=params.child_name))
    rel_cfg = RELATIVES[params.relative]
    relative = world.add(Entity(id=params.relative, kind="character", type=rel_cfg["type"], label=rel_cfg["label"]))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(id=params.object, type=params.object, label=obj_cfg["label"], phrase=obj_cfg["phrase"], owner=child.id))

    add_clues(world, obj, relative)

    world.say(
        f"It was a quiet day in {place.label}, and {child.id} felt sure something odd was going on."
    )
    world.para()
    intro_lines(world, child, relative, obj)

    world.para()
    observe_clue(world, child, world.clues["trail"])
    suspect(world, child, relative, obj)
    observe_clue(world, child, world.clues["smile"])

    world.para()
    reveal_kindness(world, child, relative, obj)
    closing_image(world, child, relative, obj)

    world.facts.update(child=child, relative=relative, obj=obj, place=place)
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
    child = f["child"]
    relative = f["relative"]
    obj = f["obj"]
    return [
        f'Write a short mystery story for a young child about {child.id}, {relative.label}, and {obj.label}.',
        f"Tell a gentle story where a child misunderstands a relative, but the relative was only being kind.",
        f'Write a story with clues, a mistaken guess, and a kind surprise ending in {world.place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    relative = f["relative"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"What did {child.id} think had happened to {child.pronoun('possessive')} {obj.label}?",
            answer=f"{child.id} thought {relative.label} had taken {child.pronoun('possessive')} {obj.label}, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"Why did {relative.label} hide the {obj.label}?",
            answer=f"{relative.label} hid it because {relative.pronoun()} wanted to make a kind surprise for {child.id}.",
        ),
        QAItem(
            question=f"What did {child.id} learn at the end?",
            answer=f"{child.id} learned that the mystery was not stealing at all; it was a kind gesture from {relative.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone guesses the wrong reason for something and later learns the truth.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something caring or helpful for someone else, like making a surprise or helping them feel better.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues and careful thinking before the answer is found.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    for c in world.clues.values():
        lines.append(f"  clue {c.id:8} at {c.location}: {c.text} -> {c.points_to}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child may suspect the relative if clues point toward the relative.
suspect(C,R) :- clue_points_to(C,R), child(X), relative(R).

% It is a misunderstanding if the item is hidden for a surprise rather than stolen.
misunderstanding(O) :- hidden_for_kindness(O).
kindness(R) :- hid_for_surprise(R).

% A valid mystery story has a clue trail, a mistaken suspicion, and a kind reveal.
valid_story(P, R, O) :- place(P), relative(R), object(O),
                        clue_points_to(trail(R), R),
                        misunderstanding(O),
                        kindness(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for rid, r in RELATIVES.items():
        lines.append(asp.fact("relative", rid))
        lines.append(asp.fact("kind_label", rid, r["kindness"]))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("clue_points_to", "trail", "aunt"))
    lines.append(asp.fact("clue_points_to", "smile", "aunt"))
    lines.append(asp.fact("clue_points_to", "rustle", "aunt"))
    lines.append(asp.fact("hidden_for_kindness", "key"))
    lines.append(asp.fact("hidden_for_kindness", "cookie"))
    lines.append(asp.fact("hidden_for_kindness", "book"))
    lines.append(asp.fact("hid_for_surprise", "aunt"))
    lines.append(asp.fact("hid_for_surprise", "uncle"))
    lines.append(asp.fact("hid_for_surprise", "grandmother"))
    lines.append(asp.fact("hid_for_surprise", "grandfather"))
    lines.append(asp.fact("hid_for_surprise", "cousin"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = set(valid_combos())
    if atoms == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for rel in RELATIVES:
            for obj in OBJECTS:
                if rel == "cousin" and obj == "cookie":
                    continue
                combos.append((place, rel, obj))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="house", child_name="Mia", child_gender="girl", relative="aunt", object="key"),
    StoryParams(place="cottage", child_name="Leo", child_gender="boy", relative="grandmother", object="book"),
    StoryParams(place="apartment", child_name="Nora", child_gender="girl", relative="uncle", object="cookie"),
    StoryParams(place="house", child_name="Finn", child_gender="boy", relative="cousin", object="toy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relative is None or c[1] == args.relative)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rel, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    return StoryParams(place=place, child_name=name, child_gender=gender, relative=rel, object=obj)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for rel in RELATIVES:
            for obj in OBJECTS:
                if rel == "cousin" and obj == "cookie":
                    continue
                combos.append((place, rel, obj))
    return combos


if __name__ == "__main__":
    main()
