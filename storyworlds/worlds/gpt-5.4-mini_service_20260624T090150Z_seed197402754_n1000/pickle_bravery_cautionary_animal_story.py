#!/usr/bin/env python3
"""
A small Animal-Story-style world about bravery, caution, and a pickle.

Seed tale:
---
A little rabbit named Pip found a pickle on the path. Pip wanted to show
bravery and carry it home, but the pickle was slippery and the hill was steep.
An owl warned Pip to be careful. Pip listened, asked a sturdy turtle for help,
and together they brought the pickle home without dropping it. Pip felt brave
and clever, and the pickle ended up safe in a jar on the shelf.
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
    kind: str = "thing"  # "animal" | "thing"
    species: str = ""
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    in_container: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    feature: str
    steep: bool = False
    damp: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    slippery: bool = False
    edible: bool = False


@dataclass
class Helper:
    id: str
    label: str
    trait: str
    can_carry: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_species: str
    helper: str
    helper_species: str
    object: str
    seed: Optional[int] = None


PLACES = {
    "garden_path": Place(name="the garden path", feature="a narrow little path", steep=True, damp=True),
    "forest_edge": Place(name="the forest edge", feature="a winding trail", steep=False, damp=True),
    "hill_lane": Place(name="the hill lane", feature="a small hill road", steep=True, damp=False),
}

HEROES = {
    "rabbit": ("rabbit", "a little rabbit"),
    "fox": ("fox", "a small fox"),
    "mouse": ("mouse", "a tiny mouse"),
}

HELPERS = {
    "turtle": ("turtle", "a sturdy turtle"),
    "owl": ("owl", "a wise owl"),
    "bear": ("bear", "a gentle bear"),
}

OBJECTS = {
    "pickle": ObjectThing(id="pickle", label="pickle", phrase="a shiny pickle in a jar", fragile=True, slippery=True, edible=True),
    "jar": ObjectThing(id="jar", label="jar", phrase="a glass jar with a tight lid", fragile=True),
    "basket": ObjectThing(id="basket", label="basket", phrase="a woven basket", fragile=False),
}


def reasonableness_gate(place: Place, obj: ObjectThing, helper: Helper) -> None:
    if obj.id == "pickle" and not place.steep and place.name != "the garden path":
        raise StoryError("The pickle story needs a place where careful carrying matters.")
    if obj.id == "pickle" and helper.id == "owl":
        raise StoryError("An owl can warn, but the story needs a helper who can physically carry the pickle safely.")


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.steep:
            lines.append(asp.fact("steep", pid))
        if p.damp:
            lines.append(asp.fact("damp", pid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("trait", hid, h[0]))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
        if o.slippery:
            lines.append(asp.fact("slippery", oid))
    return "\n".join(lines)


ASP_RULES = r"""
risky(O) :- fragile(O), slippery(O).
needs_caution(P,O) :- steep(P), risky(O).
safe_help(P,O,H) :- needs_caution(P,O), helper(H), trait(H,turtle).
valid_story(P,O,H) :- safe_help(P,O,H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            for helper_id, helper in HELPERS.items():
                if obj.id == "pickle" and helper.id == "turtle" and place.steep:
                    out.append((place_id, obj_id, helper_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about bravery and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=OBJECTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("No valid animal story matches the given options.")
    place, obj, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(
        place=place,
        hero=hero,
        hero_species=HEROES[hero][0],
        helper=helper,
        helper_species=HELPERS[helper][0],
        object=obj,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    helper = Helper(id=params.helper, label=HELPERS[params.helper][1], trait=params.helper_species)
    hero = Entity(id=params.hero, kind="animal", species=params.hero_species, label=HEROES[params.hero][1])

    reasonableness_gate(place, obj, helper)

    world = World(place)
    world.add(hero)
    world.add(Entity(id=helper.id, kind="animal", species=helper.trait, label=helper.label))
    world.add(Entity(id=obj.id, kind="thing", label=obj.label, phrase=obj.phrase))

    hero.memes["bravery"] = 1.0
    hero.memes["caution"] = 0.2
    world.say(f"{hero.label.capitalize()} lived near {place.name} and liked bright little adventures.")
    world.say(f"One day, {hero.label} found {obj.phrase} beside {place.feature}.")
    world.say(f"{hero.label} wanted to be brave and carry the {obj.label} home alone.")

    world.para()
    world.say(f"But {place.feature} was tricky, and the {obj.label} was slippery in {('the damp ground' if place.damp else 'the dust')}.")
    world.say(f"An owl's warning would have sounded wise, but here {HELPERS[params.helper][1]} called out, \"Slow steps are the brave steps.\"")
    world.say(f"{hero.label} listened, and that made the courage even bigger.")

    hero.memes["caution"] = 1.0
    hero.memes["confidence"] = 1.0
    world.para()
    world.say(f"{hero.label} and {helper.label} worked together, one careful step at a time.")
    world.say(f"{helper.label} held the {obj.label} steady while {hero.label} watched the path.")
    world.say(f"They brought the {obj.label} home safely, and it rested in a jar on the shelf.")

    world.facts.update(hero=hero, helper=helper, obj=obj, place=place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write an animal story about a {hero.species} and a pickle that rewards bravery and caution.",
            f"Tell a gentle tale where {hero.label} finds a pickle, wants to be brave, and gets help from a {helper.species}.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    obj: ObjectThing = world.facts["obj"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to be brave and carry the {obj.label} home alone?",
            answer=f"{hero.label.capitalize()} wanted to be brave and carry the {obj.label} home alone.",
        ),
        QAItem(
            question=f"Who helped {hero.label} bring the {obj.label} home safely?",
            answer=f"{helper.label.capitalize()} helped {hero.label} bring the {obj.label} home safely.",
        ),
        QAItem(
            question=f"Where did {hero.label} find the pickle?",
            answer=f"{hero.label} found the pickle near {place.name}.",
        ),
        QAItem(
            question=f"What did the story teach about bravery?",
            answer="It taught that brave choices can also be careful choices.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while still trying your best.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means moving carefully and thinking about danger before acting.",
        ),
        QAItem(
            question="What is a pickle?",
            answer="A pickle is a cucumber that has been kept in salty, sour liquid for eating later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_path", hero="rabbit", hero_species="rabbit", helper="turtle", helper_species="turtle", object="pickle"),
    StoryParams(place="hill_lane", hero="mouse", hero_species="mouse", helper="turtle", helper_species="turtle", object="pickle"),
]


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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
