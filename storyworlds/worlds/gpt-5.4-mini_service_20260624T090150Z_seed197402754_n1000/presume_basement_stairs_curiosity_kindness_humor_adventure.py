#!/usr/bin/env python3
"""
A small story world for a child on basement stairs: curiosity, kindness, and
humor turn a spooky-feeling errand into a tiny adventure.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the basement stairs"
    affords: set[str] = field(default_factory=lambda: {"search", "descend"})


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    place: str
    is_small: bool = True
    is_funny: bool = False
    is_fragile: bool = False


@dataclass
class StoryParams:
    object: str
    helper: str
    child_name: str
    child_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

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


OBJECTS = {
    "lantern": ObjectThing(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        place="the bottom step",
    ),
    "truck": ObjectThing(
        id="truck",
        label="toy truck",
        phrase="a blue toy truck",
        place="the landing",
        is_funny=True,
    ),
    "book": ObjectThing(
        id="book",
        label="picture book",
        phrase="a picture book with a red cover",
        place="the second step",
        is_fragile=True,
    ),
    "cookie_tin": ObjectThing(
        id="cookie_tin",
        label="cookie tin",
        phrase="a tin full of paper stars",
        place="the basement shelf",
        is_funny=True,
    ),
}

HELPERS = {
    "flashlight": {
        "label": "flashlight",
        "prep": "shined a flashlight down the stairs",
        "tail": "followed the beam",
    },
    "handhold": {
        "label": "steady hand",
        "prep": "held the banister and took careful steps",
        "tail": "kept one hand on the rail",
    },
    "lantern": {
        "label": "small lantern",
        "prep": "carried a small lantern",
        "tail": "let the lantern glow on the steps",
    },
}

NAMES = {
    "girl": ["Maya", "Nina", "Lila", "Hazel", "June", "Ivy"],
    "boy": ["Eli", "Noah", "Theo", "Owen", "Milo", "Finn"],
}
TRAITS = ["curious", "kind", "brave", "playful", "helpful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(oid, hid) for oid in OBJECTS for hid in HELPERS]


def explain_rejection(obj: ObjectThing, helper: str) -> str:
    if obj.is_fragile and helper == "handhold":
        return "(No story: a fragile picture book needs light and careful steps, not just a steady hand. Try a helper with a flashlight.)"
    return "(No story: this combination does not make a clear basement-stairs adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A basement-stairs adventure story world.")
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.object and args.helper:
        obj = OBJECTS[args.object]
        if obj.is_fragile and args.helper == "handhold":
            raise StoryError(explain_rejection(obj, args.helper))
    combos = [c for c in valid_combos()
              if (args.object is None or c[0] == args.object)
              and (args.helper is None or c[1] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    obj_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES[gender])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        object=obj_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        adult=adult,
        trait=trait,
    )


def _do_action(world: World, child: Entity, obj: ObjectThing, helper: str) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["adventure"] = child.memes.get("adventure", 0) + 1
    if helper == "flashlight":
        child.meters["light"] = child.meters.get("light", 0) + 1
    elif helper == "handhold":
        child.meters["balance"] = child.meters.get("balance", 0) + 1
    else:
        child.meters["light"] = child.meters.get("light", 0) + 1


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add_entity(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        memes={"curiosity": 0, "kindness": 0, "humor": 0, "worry": 0, "adventure": 0},
        meters={"light": 0, "balance": 0},
    ))
    adult = world.add_entity(Entity(
        id="Adult",
        kind="character",
        type=params.adult,
        label=f"the {params.adult}",
        memes={"care": 0, "worry": 0, "kindness": 0},
    ))
    obj = world.add_object(OBJECTS[params.object])
    helper = HELPERS[params.helper]

    world.say(f"{child.id} was a {params.trait} little {params.child_gender} who loved curiosity and adventure.")
    world.say(f"One day, {child.id} wanted to check {world.setting.place} because {child.pronoun('subject')} had been told something important was down there.")
    world.say(f"{child.id}'s {params.adult} smiled and promised kindness would make the trip easier.")

    world.para()
    world.say(f"At the top of {world.setting.place}, {child.id} {('presumed' if True else 'thought')} the dark creak meant something spooky.")
    world.say(f"Then {child.id} noticed {obj.phrase} waiting {obj.place}.")
    world.say(f"That made {child.id}'s curiosity jump higher, and {child.pronoun('subject')} wanted to go down at once.")
    world.say(f"{params.adult.capitalize()} {helper['prep']}, so the stairs felt a little less scary.")
    _do_action(world, child, obj, params.helper)

    world.para()
    child.memes["worry"] += 1
    if obj.is_funny:
        child.memes["humor"] += 1
        world.say(f"Halfway down, {child.id} saw that the \"mystery\" was only a crooked stack of laundry baskets with a sock perched on top like a sleepy pirate hat.")
        world.say(f"{child.id} laughed so hard that the small echo sounded like a giggle from the walls.")
    else:
        world.say(f"Halfway down, {child.id} found the object and carefully reached for it.")
        if obj.is_fragile:
            world.say(f"{child.id} moved slowly so the {obj.label} would not wobble or tumble.")
    world.say(f"That little laugh made the stairs feel friendly instead of spooky.")

    world.para()
    child.memes["kindness"] += 1
    adult.memes["kindness"] = adult.memes.get("kindness", 0) + 1
    world.say(f"{child.id} carried {obj.label} back up for {params.adult} with a proud little grin.")
    world.say(f"Together they went back up {world.setting.place}, and the old stairs seemed to have less shadows than before.")
    world.say(f"{child.id} learned that curiosity can lead to adventures, kindness can make them safe, and humor can turn a creaky step into a funny story.")

    world.facts.update(
        child=child,
        adult=adult,
        obj=obj,
        helper=helper,
        params=params,
        place=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short story for a young child about {f["place"]}, curiosity, kindness, and humor, and include the word "presume".',
        f"Tell an adventure story where {f['child'].id} goes down {f['place']} with {f['adult'].label} and finds {f['obj'].phrase}.",
        f"Write a gentle basement-stairs story in which a child is curious, a grown-up is kind, and a small joke makes the ending happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    obj = f["obj"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why did {child.id} want to go down the basement stairs?",
            answer=f"{child.id} was curious and wanted to see what was waiting below the stairs.",
        ),
        QAItem(
            question=f"What did {params_child_pos(child)} {adult.label} do to help?",
            answer=f"{adult.label.capitalize()} {helper['prep']} so {child.id} could go down more safely.",
        ),
        QAItem(
            question=f"What made the trip feel funny instead of scary?",
            answer=f"{obj.phrase} turned out to be a little surprise, and {child.id} laughed when {child.pronoun('subject')} saw it clearly.",
        ),
    ]


def params_child_pos(child: Entity) -> str:
    return child.pronoun("possessive")


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn more and look for answers.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, caring, and being gentle with someone else.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is what makes people laugh because something is funny or surprising.",
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_object(lantern).
valid_object(truck).
valid_object(book).
valid_object(cookie_tin).

valid_helper(flashlight).
valid_helper(handhold).
valid_helper(lantern).

valid_story(O,H) :- valid_object(O), valid_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for oid in OBJECTS:
        lines.append(asp.fact("valid_object", oid))
    for hid in HELPERS:
        lines.append(asp.fact("valid_helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (object, helper) combos:\n")
        for obj, helper in combos:
            print(f"  {obj:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for oid in OBJECTS:
            for hid in HELPERS:
                p = StoryParams(
                    object=oid,
                    helper=hid,
                    child_name=random.choice(NAMES["girl"] + NAMES["boy"]),
                    child_gender="girl",
                    adult="mother",
                    trait="curious",
                    seed=base_seed,
                )
                samples.append(build_sample(p))
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
            sample = build_sample(params)
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
