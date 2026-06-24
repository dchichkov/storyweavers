#!/usr/bin/env python3
"""
Story world: a fairy tale of a stubborn chest, a pair of tweezers, and the
bravery that turns worry into relief.

A tiny world model drives the tale:
- A chest can be stuck shut by a thorny splinter.
- Tweezers can remove the splinter if someone is brave enough to try.
- A helper can join in, and teamwork helps the job finish.
- When the chest opens, a spell inside can transform a sad thing into a bright
  one, and the characters feel relief.

The story is deliberately classical: setup, tension, turn, resolution.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit glade"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale world of bravery, teamwork, transformation, and relief.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


SETTINGS = {
    "glade": Setting("the moonlit glade"),
    "brook": Setting("the silver brook"),
    "tower": Setting("the ivy tower"),
}

HEROES = [
    ("Lina", "girl"),
    ("Tarin", "boy"),
    ("Mira", "girl"),
    ("Pip", "boy"),
]
HELPERS = [
    ("Nell", "girl"),
    ("Oren", "boy"),
    ("Sage", "girl"),
    ("Finn", "boy"),
]


@dataclass
class Chest:
    label: str = "wooden chest"
    phrase: str = "an old wooden chest with a brass lock"


@dataclass
class Tweezers:
    label: str = "tweezers"
    phrase: str = "a pair of tiny silver tweezers"


ASP_RULES = r"""
#show valid/1.

valid(place) :- place(place).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_places() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(SETTINGS)
    asps = set(valid_places())
    if py == asps:
        print(f"OK: clingo matches Python ({len(py)} places).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - asps))
    print(" clingo only:", sorted(asps - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    name, hero_type = (args.name, "girl") if args.name else rng.choice(HEROES)
    helper = args.helper or rng.choice([n for n, _ in HELPERS if n != name])
    helper_type = next(t for n, t in HELPERS if n == helper)
    return StoryParams(place=place, hero_name=name, hero_type=hero_type, helper_name=helper, helper_type=helper_type)


def hero_intro(world: World, hero: Entity) -> None:
    world.say(f"Once, in {world.setting.place}, there lived a little {hero.type} named {hero.id}.")


def setup(world: World, hero: Entity, helper: Entity, chest: Entity, tweezers: Entity) -> None:
    world.say(f"{hero.id} loved wandering where the flowers bowed in the wind.")
    world.say(f"One morning, {hero.pronoun('possessive')} eye fell on {chest.phrase}.")
    world.say(f"Beside it lay {tweezers.phrase}.")
    chest.meters["stuck"] = 1
    chest.meters["thorn"] = 1
    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 1


def predict_open(world: World) -> bool:
    sim = world.copy()
    chest = sim.get("chest")
    return chest.meters.get("opened", 0) >= THRESHOLD


def warn(world: World, hero: Entity, helper: Entity, chest: Entity) -> None:
    world.say(f"{helper.id} peered closer and whispered that the lock might hide a thorn.")
    world.say(f"{hero.id} felt a flutter of fear, but {hero.pronoun()} still stepped nearer.")
    hero.memes["bravery"] = 1
    helper.memes["teamwork"] = 1


def use_tweezers(world: World, hero: Entity, helper: Entity, chest: Entity, tweezers: Entity) -> None:
    if chest.meters.get("thorn", 0) < THRESHOLD:
        raise StoryError("The chest has no thorn to remove.")
    chest.meters["thorn"] = 0
    chest.meters["opened"] = 1
    hero.memes["relief"] = 1
    helper.memes["relief"] = 1
    world.say(f"{hero.id} held the tweezers steady while {helper.id} guided {hero.pronoun('possessive')} hands.")
    world.say(f"Together they pinched the thorn and lifted it free.")
    world.say(f"The brass lock clicked, and the chest opened at last.")


def transformation(world: World, hero: Entity, helper: Entity, chest: Entity) -> None:
    world.say(f"Inside the chest was a pale, sleepy flower with a crumb of old spell-light on its petals.")
    world.say(f"When the lid opened, the spell woke up and changed the flower into a bright golden bloom.")
    world.say(f"Its leaves straightened, and the whole glade seemed warmer.")

def ending(world: World, hero: Entity, helper: Entity, chest: Entity) -> None:
    world.say(f"{hero.id} smiled with relief.")
    world.say(f"{helper.id} smiled too, because brave hands and teamwork had turned a stuck chest into a happy surprise.")
    world.say(f"By the end, the chest stood open, the golden bloom shone beside it, and the two friends walked home together.")


def tell(setting: Setting, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    chest = world.add(Entity(id="chest", type="chest", label="chest", phrase="a small wooden chest"))
    tweezers = world.add(Entity(id="tweezers", type="tool", label="tweezers", phrase="a pair of tiny silver tweezers"))

    hero_intro(world, hero)
    world.para()
    setup(world, hero, helper, chest, tweezers)
    world.para()
    warn(world, hero, helper, chest)
    use_tweezers(world, hero, helper, chest, tweezers)
    transformation(world, hero, helper, chest)
    world.para()
    ending(world, hero, helper, chest)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "chest": chest,
        "tweezers": tweezers,
    }
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        f"Write a short fairy tale about {hero.id}, a brave {hero.type}, who uses tweezers to free a stuck chest.",
        f"Tell a child-friendly story where {hero.id} and {helper.id} work together, show bravery, and find relief.",
        f"Write a magical story with a chest, tweezers, teamwork, and a surprising transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who was a little {hero.type}, and {helper.id}, who helped with the chest.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help the chest open?",
            answer=f"{hero.id} used tiny tweezers with {helper.id}'s help to pull out the thorn and open the chest.",
        ),
        QAItem(
            question=f"How did the characters feel when the chest finally opened?",
            answer=f"They felt relief, because their brave teamwork had freed the chest and everything worked at last.",
        ),
        QAItem(
            question="What changed inside the chest?",
            answer="A sleepy flower transformed into a bright golden bloom when the chest opened.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tweezers for?",
            answer="Tweezers are small tools used to pinch, grab, or pull out tiny things like splinters or thorns.",
        ),
        QAItem(
            question="What is relief?",
            answer="Relief is the happy, lighter feeling that comes after a worry, pain, or problem goes away.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to finish something hard.",
        ),
        QAItem(
            question="What is a transformation in a fairy tale?",
            answer="A transformation is when something changes into something new, often because of magic.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


def resolve_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible places:")
        for p in valid_places():
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, p in enumerate(sorted(SETTINGS)):
            params = StoryParams(place=p, hero_name=HEROES[i % len(HEROES)][0], hero_type=HEROES[i % len(HEROES)][1],
                                 helper_name=HELPERS[i % len(HELPERS)][0], helper_type=HELPERS[i % len(HELPERS)][1], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
