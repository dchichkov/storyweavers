#!/usr/bin/env python3
"""
storyworlds/worlds/thermos_twist_tall_tale.py
=============================================

A tiny tall-tale storyworld about a thermos, a twist, and a clever fix.

Seed image:
- A big thermos keeps a drink hot or cold.
- A child wants to carry it somewhere.
- The lid twist matters: too loose and it spills, too tight and nobody can open it.
- A careful twist turns trouble into a happy ending.

The simulation keeps physical meters and emotional memes on typed entities.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Thermos:
    label: str
    phrase: str
    contents: str
    twist_dir: str = "clockwise"
    hot: bool = True
    sealed: bool = True


@dataclass
class Setting:
    place: str
    journey: str
    afford: str


@dataclass
class StoryParams:
    place: str
    drink: str
    name: str
    gender: str
    helper: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "hill": Setting(place="the hill", journey="up the road", afford="carry"),
    "fair": Setting(place="the county fair", journey="through the crowd", afford="carry"),
    "river": Setting(place="the riverbank", journey="past the reeds", afford="carry"),
}

DRINKS = {
    "cocoa": Thermos(label="thermos", phrase="a shiny thermos", contents="hot cocoa", twist_dir="clockwise", hot=True),
    "lemonade": Thermos(label="thermos", phrase="a sturdy thermos", contents="cold lemonade", twist_dir="clockwise", hot=False),
    "soup": Thermos(label="thermos", phrase="a tall thermos", contents="bean soup", twist_dir="clockwise", hot=True),
}

NAMES_BOY = ["Milo", "Ben", "Jasper", "Otis", "Theo"]
NAMES_GIRL = ["Maya", "Nina", "June", "Lila", "Ruby"]
TWISTS = ["twist", "turn", "spin"]


def _seal_loss(world: World, child: Entity, thermos: Entity) -> None:
    if thermos.m("loose") >= THRESHOLD and thermos.id not in world.fired:
        world.fired.add(thermos.id + ":spill")
        thermos.meters["spill"] = 1.0
        child.memes["worry"] = child.e("worry") + 1
        world.say(f"The lid was loose, and a little splash slipped out like a runaway creek.")


def _tight_trouble(world: World, child: Entity, thermos: Entity, helper: Entity) -> None:
    if thermos.m("stuck") >= THRESHOLD and thermos.id + ":stuck" not in world.fired:
        world.fired.add(thermos.id + ":stuck")
        child.memes["frustration"] = child.e("frustration") + 1
        world.say(f"But the lid was stuck fast, and even the strongest hands in town could not budge it.")


def set_loose(world: World, thermos: Entity) -> None:
    thermos.meters["loose"] = 1.0
    _seal_loss(world, world.get(world.facts["child"].id), thermos)


def set_stuck(world: World, thermos: Entity) -> None:
    thermos.meters["stuck"] = 1.0
    _tight_trouble(world, world.get(world.facts["child"].id), thermos, world.get(world.facts["helper"].id))


def twirl_fix(world: World, child: Entity, thermos: Entity, helper: Entity) -> None:
    thermos.meters["loose"] = 0.0
    thermos.meters["stuck"] = 0.0
    thermos.memes["trust"] = thermos.e("trust") + 1
    child.memes["joy"] = child.e("joy") + 1
    child.memes["pride"] = child.e("pride") + 1
    world.say(
        f"{helper.pronoun().capitalize()} showed {child.pronoun('object')} a careful twist, "
        f"and the thermos gave a neat little click."
    )
    world.say(
        f"After that, the drink stayed snug inside, and {child.pronoun('subject')} carried "
        f"{child.pronoun('possessive')} thermos all the way to {world.setting.place}."
    )


def tell(setting: Setting, drink: Thermos, name: str, gender: str, helper_type: str, twist_word: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    thermos = world.add(Entity(id="thermos", type="thermos", label="thermos", phrase=drink.phrase))
    thermos.owner = child.id
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["thermos"] = thermos
    world.facts["drink"] = drink
    world.facts["twist_word"] = twist_word

    world.say(
        f"{name} had a thermos as grand as a chimney and a grin as wide as a barn door."
    )
    world.say(
        f"Inside it was {drink.contents}, kept {('hot as a stove' if drink.hot else 'cool as a cellar')}."
    )
    world.say(
        f"One day {name} set out {setting.journey} to {setting.place}, carrying the thermos like a prize."
    )

    if twist_word == "twist":
        thermos.meters["loose"] = 1.0
        _seal_loss(world, child, thermos)
        world.say(f"But the lid only wanted a {twist_word}, and without it the thermos began to misbehave.")
        world.say(f"{name} frowned, then asked for help.")
        twirl_fix(world, child, thermos, helper)
    elif twist_word == "turn":
        thermos.meters["stuck"] = 1.0
        _tight_trouble(world, child, thermos, helper)
        world.say(f"The lid would not {twist_word}, as stubborn as an old mule on market day.")
        world.say(f"{helper.label.capitalize()} came close, gave it one patient try, and then another.")
        twirl_fix(world, child, thermos, helper)
    else:
        thermos.meters["loose"] = 1.0
        _seal_loss(world, child, thermos)
        world.say(f"The cap needed a steady {twist_word}, and the child learned that a small motion could save a grand drink.")
        twirl_fix(world, child, thermos, helper)

    world.say(
        f"By sunset, the thermos was still full, the path was dry, and {name} walked home tall as a fence post."
    )
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for drink in DRINKS:
            for twist in TWISTS:
                out.append((place, drink, twist))
    return out


@dataclass
class StorySpec:
    place: str
    drink: str
    name: str
    gender: str
    helper: str
    twist: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "thermos": [
        QAItem(
            question="What is a thermos?",
            answer="A thermos is a container that keeps a drink hot or cold for a long time.",
        ),
        QAItem(
            question="Why do people use a thermos?",
            answer="People use a thermos to carry soup, cocoa, or other drinks without letting them cool off too fast.",
        ),
    ],
    "twist": [
        QAItem(
            question="What does it mean to twist a lid?",
            answer="To twist a lid means to turn it so it opens or closes tightly.",
        ),
        QAItem(
            question="Why can a twist matter on a bottle or thermos?",
            answer="A good twist can keep the lid sealed so the drink stays inside instead of spilling out.",
        ),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale thermos storyworld with a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--twist", choices=TWISTS)
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
    drink = args.drink or rng.choice(list(DRINKS))
    twist = args.twist or rng.choice(TWISTS)
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES_BOY if gender == "boy" else NAMES_GIRL)
    helper = args.helper or rng.choice(["mother", "father", "grandma", "grandpa"])
    return StoryParams(place=place, drink=drink, name=name, gender=gender, helper=helper, twist=twist)


def story_prompts(p: StoryParams) -> list[str]:
    return [
        f"Write a tall-tale story about {p.name}, a thermos, and a small twist that saves the day.",
        f"Tell a child-friendly story where a thermos must be carried to {p.place} without spilling.",
        f"Make a funny, exaggerated story about {p.name} learning how to {p.twist} a thermos lid.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    thermos: Entity = world.facts["thermos"]  # type: ignore[assignment]
    drink: Thermos = world.facts["drink"]  # type: ignore[assignment]
    twist_word: str = world.facts["twist_word"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who carried the thermos in the story?",
            answer=f"{child.id} carried the thermos, and {helper.label} helped when the lid gave trouble.",
        ),
        QAItem(
            question=f"What was inside the thermos?",
            answer=f"It held {drink.contents}, so the thermos had to stay sealed on the way to {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the child need to do with the lid?",
            answer=f"{child.id} needed to {twist_word} the lid just right so the drink would stay inside.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["thermos"])
    out.extend(KNOWLEDGE["twist"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DRINKS[params.drink], params.name, params.gender, params.helper, params.twist)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(params),
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


ASP_RULES = r"""
% A combination is valid in every registered setting, drink, and twist.
valid(Place, Drink, Twist) :- setting(Place), drink(Drink), twist(Twist).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for drink in DRINKS:
        lines.append(asp.fact("drink", drink))
    for twist in TWISTS:
        lines.append(asp.fact("twist", twist))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hill", drink="cocoa", name="Milo", gender="boy", helper="grandpa", twist="twist"),
            StoryParams(place="fair", drink="lemonade", name="Maya", gender="girl", helper="mother", twist="turn"),
            StoryParams(place="river", drink="soup", name="June", gender="girl", helper="father", twist="spin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
