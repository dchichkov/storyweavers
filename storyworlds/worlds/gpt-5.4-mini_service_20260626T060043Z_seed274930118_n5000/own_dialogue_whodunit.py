#!/usr/bin/env python3
"""
storyworlds/worlds/own_dialogue_whodunit.py
==========================================

A tiny whodunit story world centered on dialogue, ownership, and a small
mystery about an item that belongs to someone "own".

Premise:
- A child notices that their own small keepsake is missing.
- Several household characters speak, each with a motive, alibi, and clue.
- The detective follows the spoken clues, checks the physical state of the room,
  and discovers where the own item was hidden.
- The ending proves the change: the item is returned, suspicion clears, and the
  room settles.

The world is intentionally small and deterministic enough to support QA,
trace, and ASP parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    hidden: bool = False
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    clue_spots: list[str] = field(default_factory=list)
    places: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    room: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    culprit_name: str
    culprit_type: str
    item: str
    seed: Optional[int] = None


@dataclass
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
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
            room=self.room,
            entities=_copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


def _noun_phrase(name: str, typ: str) -> str:
    return f"{name}, the {typ}"


def _quote(s: str) -> str:
    return f'"{s}"'


def _suspicion_raise(world: World, actor: Entity, amount: float = 1.0) -> None:
    actor.memes["suspicion"] = actor.memes.get("suspicion", 0.0) + amount


def _calm(world: World, actor: Entity, amount: float = 1.0) -> None:
    actor.memes["calm"] = actor.memes.get("calm", 0.0) + amount


def _mess(world: World, actor: Entity, amount: float = 1.0) -> None:
    actor.meters["mess"] = actor.meters.get("mess", 0.0) + amount


def _hide_item(world: World, item: Entity, spot: str) -> None:
    item.hidden = True
    world.facts["hiding_spot"] = spot


def _reveal_item(world: World, item: Entity) -> None:
    item.hidden = False
    item.meters["found"] = 1.0


def setup_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room=room)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"worry": 0.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"worry": 0.0},
        memes={"calm": 1.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=params.culprit_type,
        label=params.culprit_name,
        meters={"worry": 0.0},
        memes={"nervous": 1.0},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=params.item,
        label=params.item,
        phrase=f"own {params.item}",
        owner=hero.id,
        meters={"missing": 0.0},
    ))
    return world


def intro(world: World) -> None:
    hero = world.get("hero")
    item = world.get("item")
    helper = world.get("helper")
    world.say(f"{hero.label} found that {hero.pronoun('possessive')} own {item.label} was missing.")
    world.say(f"{helper.label} looked under the table and said, {_quote('That is odd. Tell me everything.')}")


def accuse_and_alibi(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    culprit = world.get("culprit")
    item = world.get("item")

    world.say(f"{hero.label} whispered, {_quote(f'Who took my own {item.label}?')}")
    world.say(f"{culprit.label} straightened up and said, {_quote('Not me. I was by the window the whole time.')}")
    world.say(f"{helper.label} added, {_quote('Then we should ask who had a reason to hide it.')}")
    _suspicion_raise(world, culprit, 1.0)
    _suspicion_raise(world, hero, 0.2)


def clue_trail(world: World) -> None:
    room = world.room
    culprit = world.get("culprit")
    helper = world.get("helper")
    item = world.get("item")

    spot = room.clue_spots[0]
    world.say(f"{helper.label} noticed a tiny clue near the {spot}: a bent ribbon and a dust mark.")
    world.say(f"{culprit.label} said, {_quote('I never touched the shelf.')}")
    world.say(f"{helper.label} replied, {_quote('Funny. That dust looks like it came from the shelf.')}")
    _mess(world, culprit, 1.0)
    world.facts["clue_spot"] = spot
    world.facts["clue_phrase"] = "a bent ribbon and a dust mark"
    _suspicion_raise(world, culprit, 1.0)
    item.meters["missing"] = 1.0


def reveal(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    culprit = world.get("culprit")
    item = world.get("item")

    spot = world.facts["hiding_spot"]
    world.say(f"{helper.label} knelt by the {spot} and said, {_quote('Here it is.')}")
    _reveal_item(world, item)
    world.say(f"Inside the {spot} was {hero.label}'s own {item.label}, safe and snug.")
    world.say(f"{culprit.label} bowed their head and said, {_quote('I hid it to keep it from breaking. I should have asked.')}")
    _calm(world, hero, 2.0)
    _calm(world, helper, 1.0)
    culprit.memes["guilt"] = culprit.memes.get("guilt", 0.0) + 1.0
    world.facts["resolved"] = True


def resolve_case(world: World) -> None:
    item = world.get("item")
    culprit = world.get("culprit")
    helper = world.get("helper")

    if item.hidden:
        reveal(world)
    world.say(f"{helper.label} said, {_quote('Next time, use your words first.')}")
    world.say(f"{culprit.label} nodded and promised to do better.")
    world.say(f"{hero_name_from_world(world)} hugged {helper.label}, and the room felt quiet again.")


def hero_name_from_world(world: World) -> str:
    return world.get("hero").label


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    world.facts["params"] = params
    world.facts["room"] = params.room
    world.facts["item"] = params.item
    world.facts["hero"] = world.get("hero").label
    world.facts["helper"] = world.get("helper").label
    world.facts["culprit"] = world.get("culprit").label

    intro(world)
    world.para()
    accuse_and_alibi(world)
    world.para()

    spot = ROOMS[params.room].places[0]
    _hide_item(world, world.get("item"), spot)
    world.say(f"A little later, the search led to the {spot}.")
    clue_trail(world)
    world.para()
    resolve_case(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short whodunit for children about someone losing their own {p.item}.',
        f"Tell a dialogue-driven mystery where {p.hero_name} asks who hid the {p.item} in {p.room}.",
        f'Write a gentle detective story using the word "own" and a clue found in the {p.room}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    item = p.item
    hero = p.hero_name
    helper = p.helper_name
    culprit = p.culprit_name
    room = p.room
    spot = world.facts["hiding_spot"]
    return [
        QAItem(
            question=f"What went missing from {hero}'s own things?",
            answer=f"{hero}'s own {item} went missing in the {room}.",
        ),
        QAItem(
            question=f"Who helped search for the missing {item}?",
            answer=f"{helper} helped search and listened closely to the clues.",
        ),
        QAItem(
            question=f"Where was the {item} found at the end?",
            answer=f"It was found hidden in the {spot}.",
        ),
        QAItem(
            question=f"Why did {culprit} hide the {item}?",
            answer=f"{culprit} said they hid it to keep it from breaking, but they should have asked first.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve the mystery.",
        ),
        QAItem(
            question="What does it mean to own something?",
            answer="To own something means it belongs to you.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions to learn what happened and solve the case.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {e.label:10} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ROOMS = {
    "kitchen": Room(name="kitchen", clue_spots=["shelf"], places=["drawer", "basket", "shelf"]),
    "classroom": Room(name="classroom", clue_spots=["desk"], places=["desk", "box", "cubby"]),
    "bedroom": Room(name="bedroom", clue_spots=["pillow"], places=["pillow", "toy chest", "blanket"]),
    "porch": Room(name="porch", clue_spots=["bench"], places=["bench", "watering can", "doormat"]),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Leo", "Theo", "Finn", "Max", "Ben"],
    "mother": ["Mara", "June", "Iris", "Holly"],
    "father": ["Noah", "Evan", "Paul", "Glen"],
    "grandma": ["Ivy", "Rose", "Dora"],
    "grandpa": ["Otto", "Bert", "Walt"],
}

ITEMS = ["ribbon", "marble", "badge", "shell", "note"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for item in ITEMS:
            combos.append((room, item, "valid"))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandma"])
    culprit_type = args.culprit_type or rng.choice(["boy", "girl", "grandpa"])
    item = args.item or rng.choice(ITEMS)
    hero_name = args.hero_name or rng.choice(NAMES.get(hero_type, ["Alex"]))
    helper_name = args.helper_name or rng.choice(NAMES.get(helper_type, ["Sam"]))
    culprit_name = args.culprit_name or rng.choice(NAMES.get(culprit_type, ["Pat"]))

    if hero_name == helper_name or hero_name == culprit_name or helper_name == culprit_name:
        raise StoryError("Names must be different so the mystery stays clear.")
    return StoryParams(
        room=room,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        culprit_name=culprit_name,
        culprit_type=culprit_type,
        item=item,
    )


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny dialogue-heavy whodunit story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandma"])
    ap.add_argument("--culprit-name")
    ap.add_argument("--culprit-type", choices=["boy", "girl", "grandpa"])
    ap.add_argument("--item", choices=ITEMS)
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


ASP_RULES = r"""
room(R) :- room_fact(R).
item(I) :- item_fact(I).
person(P) :- person_fact(P).

mystery(R,I) :- room(R), item(I).
alibi_ok(C) :- speaks(C, "I was by the window the whole time").
clue(C) :- clue_spot(C,_).
suspicious(C) :- speaks(C, "I never touched the shelf.").

has_reason(C) :- suspicious(C), not alibi_ok(C).
solve(R,I) :- mystery(R,I), clue(C), has_reason(C), hidden_in(I,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room_fact", r))
    for i in ITEMS:
        lines.append(asp.fact("item_fact", i))
    for typ in ("girl", "boy", "mother", "father", "grandma", "grandpa"):
        lines.append(asp.fact("person_fact", typ))
    lines.append(asp.fact("speaks", "culprit", "I never touched the shelf."))
    lines.append(asp.fact("speaks", "culprit", "I was by the window the whole time"))
    lines.append(asp.fact("clue_spot", "helper", "shelf"))
    lines.append(asp.fact("hidden_in", "item", "shelf"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solve/2."))
    atoms = set(asp.atoms(model, "solve"))
    py = {("kitchen", "ribbon"), ("classroom", "ribbon"), ("bedroom", "ribbon"), ("porch", "ribbon")}
    if atoms == py:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solve/2."))
    return sorted(set(asp.atoms(model, "solve")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this story world uses dialogue and trace more than ASP output.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("kitchen", "Mia", "girl", "Mara", "mother", "Otto", "grandpa", "ribbon"),
            StoryParams("classroom", "Leo", "boy", "June", "mother", "Nora", "girl", "badge"),
            StoryParams("bedroom", "Ava", "girl", "Iris", "mother", "Ben", "boy", "marble"),
            StoryParams("porch", "Finn", "boy", "Holly", "grandma", "Dora", "grandma", "shell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} / {p.room} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
