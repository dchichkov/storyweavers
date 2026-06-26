#!/usr/bin/env python3
"""
Tiny storyworld: a cautionary, humorous tall tale about a gross souvlaki fumble.

A child wants to carry and eat a sky-high souvlaki skewer. The snack is too tall,
too slippery, and too saucy. A warning follows, a fumble makes a mess, and a
clever safer choice turns the day around. The world is intentionally small and
state-driven, with physical meters and emotional memes shaping the prose.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    dirty: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "spill", "weight", "height", "heat"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "embarrassment", "warning", "relief", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    messiness: str
    height: str
    warning: str
    caution: str
    fix: str
    safer: str


@dataclass
class StoryParams:
    place: str
    food: str
    name: str
    gender: str
    parent: str
    trait: str
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
        w = World(self.setting)
        w.entities = json.loads(json.dumps({k: asdict(v) for k, v in self.entities.items()}))
        rebuilt: dict[str, Entity] = {}
        for k, d in w.entities.items():
            rebuilt[k] = Entity(**d)
        w.entities = rebuilt
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "market": Setting(place="the bazaar", indoor=False),
    "pier": Setting(place="the windy pier", indoor=False),
    "courtyard": Setting(place="the courtyard", indoor=False),
    "kitchen": Setting(place="the kitchen", indoor=True),
}

FOODS = {
    "souvlaki": Food(
        id="souvlaki",
        label="souvlaki",
        phrase="a towering souvlaki stacked so high it looked like a parade on a stick",
        messiness="greasy",
        height="tall",
        warning="You’ll drop that giant souvlaki if you wave it around like a flag",
        caution="a greasy fumble would splatter sauce and skewer bits everywhere",
        fix="set the souvlaki down on a plate and take smaller bites",
        safer="held it steady on a plate",
    ),
    "gyro": Food(
        id="gyro",
        label="gyro",
        phrase="a saucy gyro wrapped tight in warm bread",
        messiness="saucy",
        height="medium",
        warning="You’ll smear sauce all over yourself if you juggle that gyro",
        caution="a slippery fumble would paint the floor in sauce",
        fix="wrap it carefully and eat it with two hands",
        safer="wrapped it carefully in both hands",
    ),
    "kabob": Food(
        id="kabob",
        label="kabob",
        phrase="a smoky kabob with onions that dangled like tiny moons",
        messiness="charred",
        height="tall",
        warning="You’ll clatter the kabob if you climb the bench with it",
        caution="a clumsy fumble would send onions flying like little hats",
        fix="sit down before eating and keep your elbows tucked in",
        safer="sat down before eating it",
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Zuri", "Tessa"],
    "boy": ["Milo", "Eli", "Jasper", "Theo", "Finn"],
}

TRAITS = ["curious", "bold", "cheerful", "stubborn", "playful", "spirited"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
food_risky(F) :- food(F), tall(F), greasy(F).
warning_needed(F) :- food_risky(F).
fumble_happens(F) :- warning_needed(F), held_loosely(F).
safe_choice(F) :- food(F), plated(F).
good_story(F) :- food(F), warning_needed(F), fumble_happens(F), safe_choice(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.height == "tall":
            lines.append(asp.fact("tall", fid))
        if food.messiness in {"greasy", "saucy", "charred"}:
            lines.append(asp.fact(food.messiness, fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_foods() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_foods())
    cl = set(asp_good_foods())
    if py == cl:
        print(f"OK: clingo gate matches valid_foods() ({len(py)} foods).")
        return 0
    print("MISMATCH between clingo and valid_foods():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_foods() -> list[tuple[str]]:
    return [(fid,) for fid, f in FOODS.items() if f.height == "tall" and f.messiness in {"greasy", "saucy", "charred"}]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary, humorous tall-tale about a souvlaki fumble.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.food:
        food = FOODS[args.food]
        if food.id != "souvlaki":
            raise StoryError("This tiny world is built around the souvlaki fumble, so choose souvlaki.")
    place = args.place or rng.choice(list(SETTINGS))
    food = args.food or "souvlaki"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, food=food, name=name, gender=gender, parent=parent, trait=trait)


def _introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.meme_type} if not for the fact that the whole town knew {hero.pronoun('subject')} could spot a snack from a mile away.".replace("meme_type", hero.type))


def _desire(world: World, hero: Entity, food: Food) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved grand food, and {hero.id} wanted {food.phrase}. "
        f"It was a mighty {food.height} treat, shiny with juice and too tempting to ignore."
    )


def _warning(world: World, parent: Entity, hero: Entity, food: Food) -> None:
    hero.memes["warning"] += 1
    world.say(
        f"{parent.pronoun().capitalize()} pointed at the snack and said, "
        f"\"{food.warning}.\" "
        f"That was a cautionary warning, plain as thunder in a teacup."
    )
    world.facts["warning"] = food.caution


def _fumble(world: World, hero: Entity, food: Food) -> None:
    hero.memes["worry"] += 1
    hero.meters["mess"] += 1
    hero.meters["spill"] += 1
    world.say(
        f"But {hero.id} gave the souvlaki a proud little swing, and—fumble!—"
        f"the skewer tipped, the sauce slid, and the whole thing made a gross splat."
    )
    world.say(
        f"By the time {hero.id} grabbed for it, {food.caution}."
    )


def _aftermath(world: World, hero: Entity, parent: Entity, food: Food) -> None:
    hero.memes["embarrassment"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{hero.id} looked down at {hero.pronoun('possessive')} sticky hands and made a face like a cat in a pickle jar. "
        f"{parent.pronoun().capitalize()} sighed, not angry, just ready to help."
    )
    world.say(
        f"\"Let’s do this the sensible way,\" {parent.id} said. "
        f"They set the souvlaki down, wiped the mess, and used a plate so the next bite would not go wandering."
    )
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["embarrassment"] = 0.0
    world.say(
        f"So {hero.id} {food.safer}, took smaller bites, and finally got to enjoy dinner without another wild fumble."
    )


def tell_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    food = FOODS[params.food]
    snack = world.add(
        Entity(
            id=food.id,
            kind="thing",
            type="food",
            label=food.label,
            phrase=food.phrase,
            owner=hero.id,
            caretaker=parent.id,
            edible=True,
        )
    )
    snack.meters["height"] = 2.0
    snack.meters["weight"] = 1.0
    snack.meters["heat"] = 1.0

    world.facts.update(hero=hero, parent=parent, food=food, setting=world.setting)

    world.say(
        f"In {world.setting.place}, {hero.id} was a {params.trait} little {params.gender} who talked about food as if every meal were a parade."
    )
    _desire(world, hero, food)

    world.para()
    world.say(
        f"One day, the air smelled of grilled onions and warm bread, and {hero.id} found a {food.height} souvlaki that looked almost too grand to be real."
    )
    _warning(world, parent, hero, food)
    _fumble(world, hero, food)

    world.para()
    _aftermath(world, hero, parent, food)

    world.facts.update(resolved=True, mess=hero.meters["mess"] >= THRESHOLD)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    food = f["food"]
    return [
        f"Write a short tall tale for children about {hero.id} and a gross {food.label} fumble.",
        f"Tell a cautionary humorous story in which a child tries to handle a {food.height} {food.label} and learns a safer way.",
        f"Write a lively story that includes the words gross, souvlaki, and fumble, ending with a calmer meal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    food = f["food"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the souvlaki?",
            answer=f"{hero.id} wanted to carry and eat {food.phrase}, but the snack was too tall and slippery for that kind of showy handling.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id}?",
            answer=f"{parent.id} warned {hero.id} because {food.warning.lower()}. The warning was meant to stop a messy mistake before it happened.",
        ),
        QAItem(
            question=f"What happened when {hero.id} made the fumble?",
            answer=f"The souvlaki tipped, sauce splashed, and the whole thing made a gross mess. That little fumble turned the snack into dinner-time chaos.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They set the souvlaki on a plate, cleaned up, and took smaller bites. In the end, {hero.id} got to eat safely without another spill.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is souvlaki?",
            answer="Souvlaki is a grilled food, usually served on a skewer or in pieces, with meat and sometimes vegetables.",
        ),
        QAItem(
            question="Why can greasy food be messy?",
            answer="Greasy food can drip and slip because the oil makes it slick, so it can spill onto hands, plates, or clothes.",
        ),
        QAItem(
            question="What does a cautionary story teach?",
            answer="A cautionary story gives a warning by showing what can go wrong, so readers can learn a safer choice.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.kind:8}/{e.type:6}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_foods() -> list[tuple[str]]:
    return [(fid,) for fid, food in FOODS.items() if food.id == "souvlaki"]


def asp_valid_foods() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_full("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program_full("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        foods = asp_valid_foods()
        print(f"{len(foods)} compatible food story(s):")
        for item in foods:
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for fid in valid_foods():
            params = StoryParams(
                place="market",
                food=fid[0],
                name="Milo",
                gender="boy",
                parent="mother",
                trait="curious",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_args(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
