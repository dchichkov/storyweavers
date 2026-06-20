#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/peddle_mayor_hassle_mystery_to_solve_whodunit.py
=================================================================================

A standalone story world for a small whodunit about a child, a mayor, and a
hassle that turns into a mystery to solve.

Seed flavor:
- Words: peddle, mayor, hassle
- Style: whodunit
- Feature: mystery to solve

The domain is a tiny town square where a child rides a tricycle or bike, the
mayor is trying to get ready for a town event, and something important goes
missing or gets mixed up. The child notices clues while pedaling around, asks
questions, and helps solve the puzzle. The ending proves what changed: the town
gets its missing thing back, the hassle is gone, and the mayor can smile again.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/peddle_mayor_hassle_mystery_to_solve_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/peddle_mayor_hassle_mystery_to_solve_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/peddle_mayor_hassle_mystery_to_solve_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/peddle_mayor_hassle_mystery_to_solve_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "mayor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mayor": "mayor"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    clue: str
    messy: bool = False
    noisy: bool = False
    outdoors: bool = True


@dataclass
class ObjectThing:
    id: str
    label: str
    important: bool = False
    hidden_in: str = ""
    owner: str = ""
    found_by_clue: str = ""
    missing: bool = False


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    mayor_name: str
    place: str
    object: str
    clue_place: str
    seed: Optional[int] = None


TOWNS = {
    "square": Place("square", "the town square", "a ribbon snapped on the banner pole", messy=False, noisy=True),
    "market": Place("market", "the market street", "muddy footprints near the fruit stand", messy=True, noisy=True),
    "library_steps": Place("library_steps", "the library steps", "a windy flutter by the steps", messy=False, noisy=False),
    "bakery": Place("bakery", "the bakery corner", "crumbs beside the poster board", messy=True, noisy=False),
}

MYSTERY_OBJECTS = {
    "key": ObjectThing("key", "the mayor's key", important=True, hidden_in="flowerpot", owner="mayor", found_by_clue="green petals", missing=True),
    "banner": ObjectThing("banner", "the festival banner", important=True, hidden_in="cart", owner="mayor", found_by_clue="red string", missing=True),
    "hat": ObjectThing("hat", "the mayor's hat", important=True, hidden_in="bench", owner="mayor", found_by_clue="button trail", missing=True),
}

CHILD_NAMES = ["Mia", "Luca", "Nora", "Finn", "Ava", "Owen", "Zoe", "Leo"]
GENDERS = ["girl", "boy"]
MAYOR_NAMES = ["Mayor Bell", "Mayor June", "Mayor Pine", "Mayor Reed"]
REASONS = ["to get to the clue fast", "to check every corner", "to help deliver notices", "to circle the square again"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in TOWNS:
        for obj in MYSTERY_OBJECTS:
            combos.append((place, obj, "mayor"))
    return combos


def reasonableness_check(place: str, obj: str) -> None:
    if place not in TOWNS:
        raise StoryError("Unknown place.")
    if obj not in MYSTERY_OBJECTS:
        raise StoryError("Unknown mystery object.")
    if not MYSTERY_OBJECTS[obj].important:
        raise StoryError("This world needs an important missing thing.")
    if not MYSTERY_OBJECTS[obj].missing:
        raise StoryError("The object must be missing to make a mystery.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with a child, a mayor, and a solved hassle.")
    ap.add_argument("--place", choices=TOWNS)
    ap.add_argument("--object", choices=MYSTERY_OBJECTS)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--mayor")
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
    place = args.place or rng.choice(list(TOWNS))
    obj = args.object or rng.choice(list(MYSTERY_OBJECTS))
    reasonableness_check(place, obj)
    child_gender = args.gender or rng.choice(GENDERS)
    child_name = args.child or rng.choice(CHILD_NAMES)
    mayor_name = args.mayor or rng.choice(MAYOR_NAMES)
    clue_place = TOWNS[place].clue
    return StoryParams(child_name, child_gender, mayor_name, place, obj, clue_place)


def _r_discover(world: World) -> list[str]:
    out = []
    kid = world.get("child")
    if kid.memes.get("curiosity", 0.0) >= THRESHOLD and kid.attrs.get("has_clue"):
        sig = ("discover",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.facts["found"] = True
        out.append("__found__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _r_discover(world):
            changed = True
            if not s.startswith("__"):
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="solver", traits=["curious"]))
    mayor = world.add(Entity("mayor", kind="character", type="mayor", label=params.mayor_name, role="mayor"))
    obj = world.add(Entity("object", type="thing", label=MYSTERY_OBJECTS[params.object].label, attrs={"hidden_in": MYSTERY_OBJECTS[params.object].hidden_in}))
    place = TOWNS[params.place]

    child.memes["curiosity"] = 1.0
    child.memes["helpfulness"] = 1.0

    world.say(
        f"{child.id} loved riding a little bike through {place.label}. One morning, "
        f"{mayor.label} looked worried, because {obj.label} was missing and the whole town had become a hassle."
    )
    world.say(
        f'"If we do not find it soon, the festival will be in a fix," said {mayor.label}. '
        f'{child.id} peddled around {place.label} and promised to look.'
    )
    world.para()
    world.say(
        f"{child.id} noticed {place.clue}. That clue did not look like much, but it fit the mystery."
    )
    child.attrs["has_clue"] = True
    propagate(world, narrate=False)
    if place.messy:
        world.say(
            f"By the {place.label}, a little hassle had made the ground messy, so the clue stood out even more."
        )
    world.say(
        f"{child.id} followed the clue to a {MYSTERY_OBJECTS[params.object].hidden_in} and found {obj.label} tucked away."
    )
    world.para()
    world.say(
        f"{mayor.label} hurried over, thanked {child.id}, and fixed the notice right away."
    )
    world.say(
        f"At last, the festival could begin. The mayor smiled, the hassle was gone, and {child.id} rode home proud of the solved mystery."
    )

    world.facts.update(
        child=child,
        mayor=mayor,
        obj=obj,
        place=place,
        found=True,
        object_key=params.object,
        place_key=params.place,
    )
    return world


KNOWLEDGE = {
    "mayor": [("What is a mayor?", "A mayor is the person who helps lead a town or city and makes decisions for it.")],
    "peddle": [("What does it mean to peddle?", "To peddle means to push the pedals on a bike or tricycle so it moves forward.")],
    "hassle": [("What is a hassle?", "A hassle is a problem that makes things harder or more annoying than they should be.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery.")],
    "festival": [("What is a festival?", "A festival is a fun event where people gather to celebrate something special.")],
    "missing": [("What does it mean when something is missing?", "If something is missing, it is not where people expect it to be, so they have to look for it.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a whodunit story for a young child that includes the words peddle, mayor, and hassle.",
        f"Tell a mystery to solve where {f['child'].id} notices a clue while riding around {f['place'].label} and helps {f['mayor'].label} find a missing item.",
        f"Write a short town mystery in a child-friendly style, where a small hassle turns into a solved mystery and the mayor can smile again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mayor = f["mayor"]
    obj = f["obj"]
    place = f["place"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {mayor.label}. {child.id} is the one who notices the clue and helps solve the mystery."),
        ("What was the hassle?", f"The hassle was that {obj.label} was missing, and that made the town worry about the festival. Once it was found, the worry was over."),
        ("How did {0} help?".format(child.id), f"{child.id} peddled around {place.label}, noticed a clue, and followed it to the hiding place. That is how the missing thing was found."),
        ("How did the story end?", f"{mayor.label} thanked {child.id}, the missing item was returned, and the festival could finally begin. The ending shows the mystery was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mayor", "peddle", "hassle", "clue", "festival", "missing"}
    out: list[tuple[str, str]] = []
    for key in ["mayor", "peddle", "hassle", "clue", "festival", "missing"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Mayor Bell", "square", "key", "square"),
    StoryParams("Leo", "boy", "Mayor June", "market", "banner", "market"),
    StoryParams("Ava", "girl", "Mayor Pine", "library_steps", "hat", "library_steps"),
]


def valid_combo_story(params: StoryParams) -> bool:
    return params.place in TOWNS and params.object in MYSTERY_OBJECTS


ASP_RULES = r"""
valid(Place, Obj) :- place(Place), object(Obj).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in TOWNS:
        lines.append(asp.fact("place", p))
    for o in MYSTERY_OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, object=None, child=None, gender=None, mayor=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        return 1 if not print(f"SMOKE TEST FAILED: {e}") else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, object) combos:\n")
        for place, obj in asp_valid_combos():
            print(f"  {place:14} {obj}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
