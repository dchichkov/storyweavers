#!/usr/bin/env python3
"""
A small slice-of-life story world about a curious child, a wig, and a careful
choice on the fourteenth day of the month.

The core premise:
- A child is curious about trying on a wig.
- Someone worries that the wig could get trampled or tangled.
- A gentle compromise lets them enjoy the moment without ruining it.

This file is self-contained and follows the Storyweavers storyworld contract.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dirty": 0.0, "scuffed": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "tenderness": 0.0}

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
    place: str
    indoors: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    item: str
    gear: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True),
    "playroom": Setting(place="the playroom", indoors=True),
    "hall": Setting(place="the hallway", indoors=True),
    "living_room": Setting(place="the living room", indoors=True),
}

ITEMS = {
    "wig": Item(
        id="wig",
        label="wig",
        phrase="a soft curly wig",
        region="head",
        fragile=True,
        genders={"girl", "boy"},
    ),
    "crown": Item(
        id="crown",
        label="paper crown",
        phrase="a bright paper crown",
        region="head",
        fragile=True,
        genders={"girl", "boy"},
    ),
    "hat": Item(
        id="hat",
        label="sun hat",
        phrase="a floppy sun hat",
        region="head",
        fragile=False,
        genders={"girl", "boy"},
    ),
}

GEAR = {
    "stand": Gear(
        id="stand",
        label="wig stand",
        phrase="a little wig stand",
        covers={"head"},
        protects={"dirty", "scuffed"},
        prep="set the wig on a little wig stand",
        tail="placed the wig on its stand",
    ),
    "bag": Gear(
        id="bag",
        label="cloth bag",
        phrase="a cloth bag with a tie",
        covers={"head"},
        protects={"dirty", "scuffed"},
        prep="put the wig in a cloth bag",
        tail="tied the bag shut",
    ),
    "ribbon": Gear(
        id="ribbon",
        label="ribbon box",
        phrase="a box lined with ribbon",
        covers={"head"},
        protects={"dirty", "scuffed"},
        prep="carry the wig to a ribbon-lined box",
        tail="closed the ribbon-lined box carefully",
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ella", "Zoe", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn", "Leo", "Owen", "Sam"]
TRAITS = ["curious", "gentle", "careful", "bright-eyed", "soft-spoken"]


ASP_RULES = r"""
item_at_risk(I) :- item(I), fragile(I).
gear_fits(G, I) :- protects(G, M), item(I), item_region(I, R), covers(G, R), mess_of(I, M).
valid_choice(S, I, G) :- setting(S), item_at_risk(I), gear_fits(G, I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, it.region))
        if it.fragile:
            lines.append(asp.fact("fragile", iid))
        lines.append(asp.fact("mess_of", iid, "dirty"))
        lines.append(asp.fact("mess_of", iid, "scuffed"))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in gear.covers:
            lines.append(asp.fact("covers", gid, c))
        for p in gear.protects:
            lines.append(asp.fact("protects", gid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i, item in ITEMS.items():
            if not item.fragile:
                continue
            for g, gear in GEAR.items():
                if item.region in gear.covers:
                    combos.append((s, i, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a curious child and a wig.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.item and args.gear:
        item = ITEMS[args.item]
        gear = GEAR[args.gear]
        if item.region not in gear.covers:
            raise StoryError("That gear would not really protect the item in this story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, item, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(ITEMS[item].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, item=item, gear=gear, name=name, gender=gender, parent=parent)


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id=item_cfg.id,
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=item_cfg.plural,
    ))
    gear_cfg = GEAR[params.gear]
    gear = world.add(Entity(
        id=gear_cfg.id,
        type="thing",
        label=gear_cfg.label,
        phrase=gear_cfg.phrase,
        owner=hero.id,
        protective=True,
    ))

    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a curious little {hero.type} who liked quiet, ordinary afternoons.")
    world.say(f"On the fourteenth, {hero.id} noticed {hero.pronoun('possessive')} {item.label} and wanted to try it on.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} reached for the {item.label} just as a small pile of shoes got moved across the floor.")
    world.say(f"{parent.label} looked over and worried that the {item.label} could get trampled or scuffed if it stayed on the low bench.")
    hero.memes["worry"] += 1

    world.para()
    world.say(f'"Let\'s be careful," {parent.label} said. "{hero.id}, you can enjoy it, but we should give it a safe place first."')
    gear.worn_by = hero.id

    if gear.id == "stand":
        world.say(f"{hero.id} nodded and {gear_cfg.prep}.")
    elif gear.id == "bag":
        world.say(f"{hero.id} nodded and {gear_cfg.prep}.")
    else:
        world.say(f"{hero.id} nodded and {gear_cfg.prep}.")

    world.para()
    hero.memes["joy"] += 1
    hero.memes["tenderness"] += 1
    world.say(f"Then {hero.id} took the {item.label} out again, held it up to the light, and smiled at the soft curls.")
    world.say(f"Nothing got trampled, and the {item.label} stayed neat while the two of them shared a calm little moment together.")

    world.facts.update(hero=hero, parent=parent, item=item, gear=gear, params=params)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item = f["hero"], f["parent"], f["item"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the story about on the fourteenth?",
            answer=f"It is about {hero.id}, a curious little {hero.type} who liked trying on {item.label}s in a calm way.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {item.label}?",
            answer=f"{parent.label} worried because the {item.label} could get trampled or scuffed if it stayed too low on the bench.",
        ),
        QAItem(
            question=f"What helped keep the {item.label} safe?",
            answer=f"The {gear.label} helped keep the {item.label} safe by giving it a protected place instead of leaving it where it could be stepped on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to look, learn, or ask about something new.",
        ),
        QAItem(
            question="What does trample mean?",
            answer="To trample something means to step on it hard and damage or flatten it.",
        ),
        QAItem(
            question="What is a wig?",
            answer="A wig is hair made to be worn on the head, often as a costume or for fun.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle slice-of-life story about a curious child, a wig, and a careful choice on the fourteenth.',
        f"Tell a small domestic story where {world.facts['hero'].id} wants to try on a wig, but {world.facts['parent'].label} worries it might get trampled.",
        'Write a child-facing story that includes the words wig, fourteenth, and trample, and ends with a safe, happy routine.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    generate_story(world, params)
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
        print("== Prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== Story Q&A ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== World Q&A ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_choice/3."))
    return sorted(set(asp.atoms(model, "valid_choice")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_choice/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(setting="bedroom", item="wig", gear="stand", name="Mia", gender="girl", parent="mother"),
        StoryParams(setting="playroom", item="wig", gear="bag", name="Theo", gender="boy", parent="father"),
        StoryParams(setting="living_room", item="crown", gear="ribbon", name="Nora", gender="girl", parent="mother"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
