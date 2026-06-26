#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tricycle_exist_embarrass_magic_folk_tale.py
================================================================================

A small folk-tale storyworld about a child, a tricycle, a little embarrassment,
and a bit of magic that helps the day turn kind again.

Seed premise:
- A child loves a tricycle.
- Something goes wrong in public and makes the child feel embarrassed.
- A magical helper offers a folk-tale style fix.
- The ending proves the child is braver and the tricycle still matters.

This script is self-contained and uses only the standard library for the
narration engine; clingo is imported lazily only when ASP helpers are used.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    name: str
    does: str
    charm: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    magic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_green": Place(
        name="the village green",
        indoors=False,
        vibe="warm and open",
        affords={"ride", "show", "sing"},
    ),
    "lantern_yard": Place(
        name="the lantern yard",
        indoors=False,
        vibe="quiet and bright",
        affords={"ride", "show", "sing"},
    ),
    "old_stable": Place(
        name="the old stable",
        indoors=True,
        vibe="still and dusty",
        affords={"ride", "show"},
    ),
}

MAGICS = {
    "moon_glow": Magic(
        id="moon_glow",
        name="moon glow",
        does="softens shame into courage",
        charm="a small silver song",
        ending="the moon glow stayed in the child's pocket like a brave little pebble",
        tags={"magic", "glow", "moon"},
    ),
    "bell_berry": Magic(
        id="bell_berry",
        name="bell berry charm",
        does="rings away embarrassment",
        charm="a berry the size of a bead, bright as a bell",
        ending="the bell berry charm jingled once and made the child's cheeks feel cool again",
        tags={"magic", "berry", "bell"},
    ),
    "fox_thread": Magic(
        id="fox_thread",
        name="fox thread",
        does="ties a wobbly heart steady",
        charm="a red thread that shone like a fox's tail",
        ending="the fox thread tied one brave thought to the next until the child could smile",
        tags={"magic", "fox", "thread"},
    ),
}

TRICYCLES = {
    "red_tricycle": {
        "label": "red tricycle",
        "phrase": "a shiny red tricycle with a silver bell",
        "kind": "tricycle",
    },
    "blue_tricycle": {
        "label": "blue tricycle",
        "phrase": "a little blue tricycle with a crooked basket",
        "kind": "tricycle",
    },
    "green_tricycle": {
        "label": "green tricycle",
        "phrase": "a green tricycle with painted stars on the wheels",
        "kind": "tricycle",
    },
}

TRAITS = ["cheerful", "curious", "gentle", "brave", "playful", "hopeful"]
GIRL_NAMES = ["Mina", "Lena", "Pia", "Nora", "Iris", "Tessa"]
BOY_NAMES = ["Owen", "Nico", "Jasper", "Milo", "Theo", "Arlo"]


# ---------------------------------------------------------------------------
# Shared result helpers
# ---------------------------------------------------------------------------

def family_label(kind: str) -> str:
    return {"mother": "mother", "father": "father"}.get(kind, kind)


def pronoun_for(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def story_world_reasonable(place: Place, magic: Magic) -> bool:
    return "ride" in place.affords and "magic" in magic.tags


def select_magic(place: Place, rng: random.Random) -> Magic:
    choices = [m for m in MAGICS.values() if story_world_reasonable(place, m)]
    if not choices:
        raise StoryError("No reasonable magic found for this place.")
    return rng.choice(sorted(choices, key=lambda m: m.id))


def select_place(rng: random.Random) -> Place:
    return rng.choice(list(PLACES.values()))


def build_child(world: World, params: StoryParams, tricycle_id: str) -> tuple[Entity, Entity, Entity]:
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"joy": 0.0},
        memes={"embarrass": 0.0, "courage": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=family_label(params.parent),
        meters={"care": 0.0},
    ))
    trike = world.add(Entity(
        id=tricycle_id,
        kind="thing",
        type="tricycle",
        label=TRICYCLES[tricycle_id]["label"],
        phrase=TRICYCLES[tricycle_id]["phrase"],
        owner=child.id,
        ridden_by=child.id,
        meters={"dust": 0.0},
    ))
    return child, parent, trike


def predict_embarrassment(world: World, child: Entity, magic: Magic, trike: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["embarrass"] += 1.0
    sim.get(trike.id).meters["dust"] += 1.0
    return sim.get(child.id).memes["embarrass"] >= 1.0


def setup_intro(world: World, child: Entity, parent: Entity, trike: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved a {trike.label}."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {trike.label} had a happy little bell, "
        f"and {child.id} rode it everywhere the path would go."
    )
    world.say(
        f"At home, {child.id}'s {parent.label} said the tricycle had to stay clean and kind."
    )


def inciting_event(world: World, child: Entity, parent: Entity, trike: Entity, magic: Magic) -> None:
    place = world.place.name
    world.para()
    world.say(
        f"One day at {place}, {child.id} showed off a fast turn, but {trike.label} "
        f"wobbled in the dust and bumped a little flower pot."
    )
    child.memes["embarrass"] += 1.0
    child.meters["joy"] += 0.0
    world.say(
        f"People looked over, and {child.id}'s cheeks grew hot with embarrassment."
    )
    world.say(
        f"{child.id} wished the ground could swallow {child.pronoun('object')} up."
    )
    world.say(
        f"Then the {magic.name} came into the story like an old folk song."
    )


def magical_turn(world: World, child: Entity, parent: Entity, trike: Entity, magic: Magic) -> None:
    world.para()
    child.memes["courage"] += 1.0
    child.meters["dust"] = 0.0
    trike.meters["dust"] = 0.0
    world.say(
        f"A kind old helper offered {child.id} {magic.charm}."
    )
    world.say(
        f"The charm did what it was meant to do: it {magic.does}."
    )
    world.say(
        f"With a careful breath, {child.id} held the charm over the {trike.label}, "
        f"and the dust slid off like dry leaves in a breeze."
    )
    world.say(
        f"{magic.ending}."
    )
    world.say(
        f"{child.id} stopped hiding and looked up at {child.pronoun('possessive')} {parent.label}."
    )


def resolution(world: World, child: Entity, parent: Entity, trike: Entity, magic: Magic) -> None:
    world.para()
    child.memes["embarrass"] = 0.0
    child.meters["joy"] += 1.0
    world.say(
        f"{child.id}'s {parent.label} smiled and said that mistakes do not have to last forever."
    )
    world.say(
        f"So {child.id} rode the {trike.label} again, slower this time, while the little bell gave a bright ring."
    )
    world.say(
        f"By the end, the village folk were not laughing at all; they were cheering for a child who learned to go on."
    )
    world.say(
        f"That is how the story ended: the {tricycle_word(trike)} still existed, the shame had passed, "
        f"and the magic stayed like a small warm lantern in {child.pronoun('possessive')} heart."
    )


def tricycle_word(trike: Entity) -> str:
    return trike.label


def tell(place: Place, magic: Magic, child_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    trike_id = random.choice(list(TRICYCLES.keys()))
    child, parent, trike = build_child(world, StoryParams(
        place=place_key(place),
        magic=magic.id,
        name=child_name,
        gender=gender,
        parent=parent_type,
        trait=trait,
    ), trike_id)

    world.facts.update(child=child, parent=parent, trike=trike, magic=magic, place=place)

    setup_intro(world, child, parent, trike)
    inciting_event(world, child, parent, trike, magic)
    magical_turn(world, child, parent, trike, magic)
    resolution(world, child, parent, trike, magic)
    return world


def place_key(place: Place) -> str:
    for k, v in PLACES.items():
        if v.name == place.name:
            return k
    raise ValueError("unknown place")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    trike: Entity = f["trike"]
    magic: Magic = f["magic"]
    place: Place = f["place"]
    return [
        f'Write a short folk tale for young children about {child.id}, a {trike.label}, and a bit of {magic.name}.',
        f"Tell a gentle story where {child.id} feels embarrassed at {place.name} and a magical helper makes things better.",
        f'Write a simple story that includes the words "{tricycle_word(trike)}", "exist", and "embarrass".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    trike: Entity = f["trike"]
    magic: Magic = f["magic"]
    place: Place = f["place"]

    qas = [
        QAItem(
            question=f"What did {child.id} love riding in the story?",
            answer=f"{child.id} loved riding the {trike.label}, because it felt cheerful and free.",
        ),
        QAItem(
            question=f"Why did {child.id} feel embarrassed at {place.name}?",
            answer=f"{child.id} felt embarrassed because the {trike.label} wobbled in the dust and bumped a flower pot, so everyone looked over.",
        ),
        QAItem(
            question=f"What magical help did {child.id} get?",
            answer=f"{child.id} got {magic.charm}, which helped {magic.does}.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the {trike.label}?",
            answer=f"In the end, {child.id} rode the {trike.label} again with more courage, and the shame was gone.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: Magic = f["magic"]
    trike: Entity = f["trike"]
    return [
        QAItem(
            question="What is a tricycle?",
            answer="A tricycle is a small vehicle with three wheels that a child can ride.",
        ),
        QAItem(
            question="What does it mean to exist?",
            answer="To exist means to be real or to be present in the world.",
        ),
        QAItem(
            question="What is embarrassment?",
            answer="Embarrassment is a bashful feeling that can happen when something awkward occurs in front of other people.",
        ),
        QAItem(
            question=f"What does {magic.name} suggest in this story?",
            answer=f"It suggests a little bit of folk magic that can calm feelings and help a child be brave again.",
        ),
        QAItem(
            question=f"Why might a child care for a {trike.label}?",
            answer="A child may care for a tricycle because it is fun, special, and part of play.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
magic(M) :- magic_fact(M).
tricycle(T) :- tricycle_fact(T).

embarrass(C) :- feeling(C, embarrass).
exist(X) :- exists(X).

reasonable_story(P, M) :- place(P), magic(M), affording(P, ride), magic_tag(M, magic).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, p in PLACES.items():
        lines.append(asp.fact("place_fact", k))
        if p.indoors:
            lines.append(asp.fact("indoors", k))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", k, a))
    for k, m in MAGICS.items():
        lines.append(asp.fact("magic_fact", k))
        for t in sorted(m.tags):
            lines.append(asp.fact("magic_tag", k, t))
    for k, t in TRICYCLES.items():
        lines.append(asp.fact("tricycle_fact", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    asp_set = set(asp.atoms(model, "reasonable_story"))
    py_set = set((p, m) for p in PLACES for m in MAGICS if story_world_reasonable(PLACES[p], MAGICS[m]))
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about a tricycle, embarrassment, and a little magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place_key_choice = args.place or rng.choice(list(PLACES))
    place = PLACES[place_key_choice]
    if args.magic:
        magic = MAGICS[args.magic]
        if not story_world_reasonable(place, magic):
            raise StoryError("That magic does not fit this place in a reasonable folk tale.")
    else:
        magic = select_magic(place, rng)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place_key_choice,
        magic=magic.id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    magic = MAGICS[params.magic]
    world = tell(place, magic, params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show reasonable_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/2."))
        combos = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(combos)} reasonable place/magic pairs:")
        for p, m in combos:
            print(f"  {p} / {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in PLACES:
            for m in MAGICS:
                if story_world_reasonable(PLACES[p], MAGICS[m]):
                    params = StoryParams(
                        place=p,
                        magic=m,
                        name=random.choice(GIRL_NAMES + BOY_NAMES),
                        gender=random.choice(["girl", "boy"]),
                        parent=random.choice(["mother", "father"]),
                        trait=random.choice(TRAITS),
                    )
                    samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
