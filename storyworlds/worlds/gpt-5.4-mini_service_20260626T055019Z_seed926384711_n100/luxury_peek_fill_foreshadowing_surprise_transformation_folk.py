#!/usr/bin/env python3
"""
A small folk-tale storyworld about a humble helper, a touch of luxury, a secret
peek, and a filling task that leads to a surprising transformation.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    luxury: str
    secret: str
    afford: str
    mood: str


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    fills: str
    before: str
    after: str
    risk: str
    transformed_label: str
    transformed_phrase: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cottage": Place(
        name="the old cottage",
        luxury="a velvet cushion on the window seat",
        secret="a hidden key in the hearth",
        afford="fill a basin",
        mood="warm and quiet",
    ),
    "manor": Place(
        name="the manor kitchen",
        luxury="a silver spoon with a moon carved on its handle",
        secret="a cupboard behind the bread shelf",
        afford="fill a bowl",
        mood="bright and busy",
    ),
    "garden": Place(
        name="the garden hut",
        luxury="a little golden thimble used like a cup",
        secret="a patch of roses behind the rain barrel",
        afford="fill a bucket",
        mood="green and still",
    ),
}

OBJECTS = {
    "lamp": ObjectThing(
        id="lamp",
        label="lamp",
        phrase="a lamp with a clear glass belly",
        fills="oil",
        before="dark and plain",
        after="glowing and fine",
        risk="the wick could be spilled dry",
        transformed_label="lantern",
        transformed_phrase="a lantern with a bright little flame",
    ),
    "jar": ObjectThing(
        id="jar",
        label="jar",
        phrase="a clay jar with a narrow mouth",
        fills="honey",
        before="empty and dusty",
        after="sweet and shining",
        risk="the jar could crack if it was filled too fast",
        transformed_label="gift jar",
        transformed_phrase="a gift jar tied with red string",
    ),
    "bowl": ObjectThing(
        id="bowl",
        label="bowl",
        phrase="a wooden bowl with a smooth rim",
        fills="porridge",
        before="light as a leaf",
        after="heavy and ready",
        risk="the porridge might be wasted if the bowl was watched too closely",
        transformed_label="feast bowl",
        transformed_phrase="a feast bowl that steamed like morning fog",
    ),
}

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mara", "Tessa", "Lina", "Nora", "Iris"],
    "boy": ["Oren", "Bram", "Luka", "Emil", "Hugo"],
}
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place supports a filling act when it affords that act.
can_fill(P, O) :- place(P), afford_fill(P), object(O).

% Peek creates foreshadowing when there is a hidden thing in the place.
foreshadow(P) :- place(P), secret(P), peekable(P).

% A transformation happens when the object is filled and the hidden thing is seen.
transform(O) :- object(O), filled(O), seen_secret.

#show can_fill/2.
#show foreshadow/1.
#show transform/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_name", pid, place.name))
        lines.append(asp.fact("luxury", pid, place.luxury))
        lines.append(asp.fact("secret", pid))
        lines.append(asp.fact("peekable", pid))
        lines.append(asp.fact("afford_fill", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("fills_with", oid, obj.fills))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show can_fill/2.\n#show foreshadow/1.\n#show transform/1."))
    can_fill = set(asp.atoms(model, "can_fill"))
    foreshadow = set(asp.atoms(model, "foreshadow"))
    transform = set(asp.atoms(model, "transform"))
    py_can_fill = {(pid, oid) for pid in PLACES for oid in OBJECTS}
    py_foreshadow = {(pid,) for pid in PLACES}
    py_transform = {(oid,) for oid in OBJECTS}
    if can_fill == py_can_fill and foreshadow == py_foreshadow and transform == py_transform:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def choose_richness(place: Place) -> str:
    return place.luxury


def generate_story(world: World, hero: Entity, parent: Entity, obj: ObjectThing) -> None:
    place = world.place
    world.say(
        f"Long ago, in {place.name}, there was a little {hero.type} named {hero.id} "
        f"who loved gentle work and bright treasures."
    )
    world.say(
        f"At the heart of the house lay {choose_richness(place)}, and {hero.id} often paused to admire it."
    )
    world.say(
        f"Still, {hero.id} was told not to peek toward {place.secret}, for old folk said some doors should open slowly."
    )

    world.para()
    world.say(
        f"One morning, {hero.id} found {obj.phrase}. It looked {obj.before}, and "
        f"{hero.pronoun('possessive')} {parent.type} said it would need filling before it could serve the home."
    )
    world.say(
        f"{hero.id} began to {world.facts['task']} with care, because {obj.risk}."
    )
    world.say(
        f"Then {hero.id} caught a tiny peek of {place.secret}, and the room seemed to hush."
    )
    world.facts["peeked"] = True
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1

    world.para()
    world.say(
        f"The sight was a surprise: behind the secret lay a small old charm that had gone dim and forgotten."
    )
    world.say(
        f"{hero.id} did not laugh or run. {hero.pronoun().capitalize()} kept filling the {obj.label} steadily, "
        f"and with each careful measure the charm brightened a little more."
    )
    obj_state = "filled"
    obj_name = obj.label

    world.say(
        f"When the work was done, the humble {obj_name} was no longer plain."
    )
    world.say(
        f"It had changed into {obj.transformed_phrase}, and the old charm shone beside it like a new moon."
    )
    world.say(
        f"{hero.id}'s {parent.type} smiled, for the house felt richer not because of gold, but because a careful hand had made it so."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        obj=obj,
        object_state=obj_state,
        transformed=True,
        place=place,
    )


# ---------------------------------------------------------------------------
# QA and trace
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a small child about {f["hero"].id}, {f["obj"].label}, and a secret in {f["place"].name}.',
        f"Tell a short story with foreshadowing, surprise, and transformation in {f['place'].name}.",
        f'Write a gentle tale where a child peeks, fills {f["obj"].phrase}, and discovers something changed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    obj: ObjectThing = f["obj"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who lived near {place.name} and helped with a filling task.",
        ),
        QAItem(
            question=f"What did {hero.id} peek at?",
            answer=f"{hero.id} peeked at {place.secret}, and that peek became the story's surprise.",
        ),
        QAItem(
            question=f"What changed after the work was done?",
            answer=f"{obj.phrase} changed into {obj.transformed_phrase}, so the plain thing became something more special.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.type} trust the child with the job?",
            answer=f"{parent.type.capitalize()} trusted {hero.id} to fill the {obj.label} carefully, even though peeking brought a surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is luxury?",
            answer="Luxury is something rich, fancy, and pleasant, like a soft cushion, a silver spoon, or a shining cloth.",
        ),
        QAItem(
            question="What does it mean to peek?",
            answer="To peek means to look quickly and secretly at something, as if you are only opening the door a tiny bit.",
        ),
        QAItem(
            question="What does fill mean?",
            answer="To fill something means to make it full by putting in what it needs, like water in a cup or honey in a jar.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: luxury, peek, fill.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, object=obj, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    vessel = world.add(Entity(
        id=obj.id,
        type=obj.label,
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"filled": 0.0},
        memes={"mystery": 0.0},
    ))

    world.facts["task"] = f"fill the {obj.label}"
    world.facts.update(hero=hero, parent=parent, obj=obj, place=place)

    generate_story(world, hero, parent, obj)

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
        print(asp_program("#show can_fill/2.\n#show foreshadow/1.\n#show transform/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show can_fill/2.\n#show foreshadow/1.\n#show transform/1."))
        print("can_fill:", sorted(set(asp.atoms(model, "can_fill"))))
        print("foreshadow:", sorted(set(asp.atoms(model, "foreshadow"))))
        print("transform:", sorted(set(asp.atoms(model, "transform"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="cottage", object="jar", name="Mara", gender="girl", parent="mother"),
            StoryParams(place="manor", object="lamp", name="Oren", gender="boy", parent="grandfather"),
            StoryParams(place="garden", object="bowl", name="Lina", gender="girl", parent="grandmother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
