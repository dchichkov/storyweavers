#!/usr/bin/env python3
"""
storyworlds/worlds/lasagna_philanthropy_bad_ending_mystery_to_solve.py
======================================================================

A small animal-story world about a charity lasagna dinner, a missing tray,
and a mystery that gets solved too late for the ending to be happy.

The seed idea is simple:
- animals make lasagna for a philanthropy supper
- something goes wrong and the lasagna becomes the thing to investigate
- the mystery is solved, but the final outcome is still a bad one

This script keeps the world tiny and classical: a few typed entities, physical
state in meters, emotional state in memes, and a story that is driven by those
changes rather than by a frozen paragraph with swapped nouns.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["warm", "dirty", "spilled", "hidden"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "worry", "relief", "sadness", "curiosity", "pride"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "hen"}
        male = {"boy", "father", "man", "king", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool = True


@dataclass
class Food:
    label: str
    phrase: str
    region: str = "table"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    helper_name: str
    donor_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story vocabulary
# ---------------------------------------------------------------------------

SETTINGS = {
    "shelter_kitchen": Setting(place="the animal shelter kitchen", cozy=True),
    "community_hall": Setting(place="the community hall", cozy=False),
    "school_gym": Setting(place="the school gym", cozy=False),
}

HEROES = [
    ("Milo", "mouse"),
    ("Pip", "rabbit"),
    ("Nia", "cat"),
    ("Toby", "dog"),
    ("Luna", "fox"),
]

HELPERS = [
    ("Mrs. Honey", "hen"),
    ("Mr. Paws", "bear"),
    ("Sage", "owl"),
    ("Roo", "koala"),
]

DONORS = [
    "the kindly baker",
    "the neighborhood squirrels",
    "the porch geese",
    "the old otter family",
]

LASAGNA = Food(
    label="lasagna",
    phrase="a big pan of cheesy lasagna",
    region="table",
    plural=False,
)


@dataclass
class Event:
    name: str
    verb: str
    danger: str
    clue: str


EVENTS = {
    "charity_dinner": Event(
        name="charity dinner",
        verb="serve the lasagna for the charity dinner",
        danger="the tray could go cold or disappear before the guests arrived",
        clue="a trail of tomato sauce",
    ),
}


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _do_worry(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["worry"] += amount


def _do_joy(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["joy"] += amount


def _do_sad(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["sadness"] += amount


def predict_failure(world: World, hero: Entity, helper: Entity) -> bool:
    sim = world.copy()
    tray = sim.get("lasagna")
    tray.meters["hidden"] += 1
    tray.meters["dirty"] += 1
    helper.memes["curiosity"] += 1
    return tray.meters["dirty"] >= THRESHOLD


def setup_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    donor = world.add(Entity(id="donor", kind="character", type="person", label=params.donor_name))
    tray = world.add(Entity(
        id="lasagna",
        kind="thing",
        type="food",
        label="lasagna",
        phrase=LASAGNA.phrase,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, donor=donor, tray=tray, params=params)
    return


def narrate_intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    donor: Entity = f["donor"]
    tray: Entity = f["tray"]
    world.say(
        f"{hero.id} was a little {hero.type} who loved big, warm meals and quiet helpful days."
    )
    world.say(
        f"At {world.setting.place}, {donor.label} brought {tray.phrase} for a philanthropy supper "
        f"to help animals who needed food and blankets."
    )
    world.say(
        f"{helper.id}, the {helper.type}, told {hero.id} that the lasagna had to stay safe "
        f"until the guests arrived."
    )
    _do_joy(world, hero)
    helper.memes["pride"] += 1


def narrate_problem(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tray: Entity = f["tray"]
    event: Event = EVENTS["charity_dinner"]
    world.para()
    world.say(
        f"Then the room filled with busy paws and fluttering wings, because it was time to "
        f"{event.verb}."
    )
    world.say(
        f"{hero.id} noticed that the lasagna was not where it should have been."
    )
    _do_worry(world, hero)
    helper.memes["worry"] += 1
    world.say(
        f"The tray was missing, and that meant the supper could fail."
    )
    world.say(
        f"{event.danger.capitalize()}."
    )
    if predict_failure(world, hero, helper):
        world.facts["predicted_failure"] = True


def narrate_mystery(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tray: Entity = f["tray"]
    world.para()
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} went looking for clues instead of giving up."
    )
    world.say(
        f"Near the doorway, {hero.id} found {EVENTS['charity_dinner'].clue} and a tiny smear of cheese."
    )
    world.say(
        f"{helper.id} found a second clue near the heater: the lasagna had been dragged there to keep it warm."
    )
    tray.meters["hidden"] += 1
    tray.meters["warm"] += 1
    world.facts["clue_sauce"] = True
    world.facts["clue_heater"] = True


def narrate_solution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tray: Entity = f["tray"]
    world.para()
    world.say(
        f"At last, {hero.id} solved the mystery: a hungry stray had nudged the tray behind the heater "
        f"to smell the steam, then bumped it until the pan tipped."
    )
    tray.meters["dirty"] += 1
    tray.meters["spilled"] += 1
    helper.memes["sadness"] += 1
    _do_sad(world, hero)
    world.say(
        f"The lasagna was found, but it had slid, splashed, and gone cold on the floor."
    )
    world.say(
        f"{helper.id} sighed because the donation supper could not be saved in time."
    )
    world.facts["solved"] = True
    world.facts["bad_ending"] = True


def narrate_ending(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tray: Entity = f["tray"]
    world.para()
    world.say(
        f"People still clapped for the effort, but the big lasagna dinner was over before anyone could eat much."
    )
    world.say(
        f"{hero.id} and {helper.id} cleaned up the cheesy mess together in a quiet, sad room."
    )
    world.say(
        f"In the end, the charity night ended with crumbs, a cold pan, and a mystery that was solved too late."
    )
    world.say(
        f"The shelter still needed help, and the lasagna was gone."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    setup_story(world, params)
    narrate_intro(world)
    narrate_problem(world)
    narrate_mystery(world)
    narrate_solution(world)
    narrate_ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write an animal story about a lasagna philanthropy supper where a mystery must be solved.',
        f"Tell a short story about {p.hero_name} the {p.hero_type} helping at {world.setting.place} "
        f"when the lasagna goes missing before the charity dinner.",
        "Create a gentle mystery with sauce clues, warm cheese, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    donor: Entity = f["donor"]
    tray: Entity = f["tray"]
    qas = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.type} who tried to help at the charity supper.",
        ),
        QAItem(
            question=f"What food was important in the story?",
            answer=f"The important food was {tray.phrase}, which was meant to be served at the philanthropy dinner.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} try to solve?",
            answer=f"{hero.id} tried to solve the mystery of where the lasagna went before the guests arrived.",
        ),
        QAItem(
            question=f"Why did {helper.id} feel worried?",
            answer=f"{helper.id} felt worried because the lasagna was needed for the charity supper and might not be ready in time.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"At the end, the mystery was solved, but the lasagna had spilled and the supper ended badly.",
        ),
    ]
    if world.facts.get("solved"):
        qas.append(
            QAItem(
                question=f"How was the mystery solved?",
                answer=f"{hero.id} found sauce clues and {helper.id} followed the warm trail to the heater, where the tray had tipped.",
            )
        )
    return qas


WORLD_KNOWLEDGE = {
    "lasagna": (
        "What is lasagna?",
        "Lasagna is a baked pasta dish with flat noodles, sauce, and cheese layered on top of each other.",
    ),
    "philanthropy": (
        "What is philanthropy?",
        "Philanthropy means giving help, money, food, or time to make life better for other people or animals.",
    ),
    "mystery": (
        "What is a mystery?",
        "A mystery is something puzzling that people try to figure out by looking for clues.",
    ),
    "animal": (
        "Why do animal stories often sound gentle?",
        "Animal stories often feel gentle because the animals act like friends and helpers, which makes the tale easy to follow.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting can host the philanthropy supper and the
% lasagna can be part of the tale.
valid_story(Place, Hero, Helper) :- setting(Place), animal(Hero), animal(Helper), Hero != Helper.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for name, kind in HEROES:
        lines.append(asp.fact("animal", name))
        lines.append(asp.fact("kind", name, kind))
    for name, kind in HELPERS:
        lines.append(asp.fact("animal", name))
        lines.append(asp.fact("kind", name, kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero_name, _ in HEROES:
            for helper_name, _ in HELPERS:
                if hero_name != helper_name:
                    combos.append((place, hero_name, helper_name))
    return combos


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if py == clingo_set:
        print(f"OK: ASP matches Python ({len(py)} valid story triples).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set)[:10])
    if clingo_set - py:
        print("  only in ASP:", sorted(clingo_set - py)[:10])
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story: lasagna, philanthropy, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero-name", choices=[n for n, _ in HEROES])
    ap.add_argument("--hero-type", choices=sorted({k for _, k in HEROES}))
    ap.add_argument("--helper-name", choices=[n for n, _ in HELPERS])
    ap.add_argument("--helper-type", choices=sorted({k for _, k in HELPERS}))
    ap.add_argument("--donor-name", choices=DONORS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.hero_name or rng.choice([n for n, _ in HEROES])
    hero_type = args.hero_type or dict(HEROES)[hero_name]
    helper_name = args.helper_name or rng.choice([n for n, _ in HELPERS])
    helper_type = args.helper_type or dict(HELPERS)[helper_name]
    if hero_name == helper_name:
        raise StoryError("Hero and helper must be different animals.")
    donor_name = args.donor_name or rng.choice(DONORS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        helper_name=helper_name,
        donor_name=donor_name,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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
    StoryParams(
        place="shelter_kitchen",
        hero_name="Milo",
        hero_type="mouse",
        helper_name="Mrs. Honey",
        helper_type="hen",
        donor_name="the kindly baker",
    ),
    StoryParams(
        place="community_hall",
        hero_name="Pip",
        hero_type="rabbit",
        helper_name="Sage",
        helper_type="owl",
        donor_name="the neighborhood squirrels",
    ),
    StoryParams(
        place="school_gym",
        hero_name="Nia",
        hero_type="cat",
        helper_name="Mr. Paws",
        helper_type="bear",
        donor_name="the porch geese",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} valid story triples:\n")
        for place, hero, helper in triples:
            print(f"  {place:16} {hero:10} {helper:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
