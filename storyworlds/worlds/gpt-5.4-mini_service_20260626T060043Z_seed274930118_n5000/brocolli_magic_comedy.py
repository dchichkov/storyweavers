#!/usr/bin/env python3
"""
A small comedy storyworld about broccoli, magic, and a very silly problem.

Premise:
A child dislikes broccoli, but a magic trick turns dinner into a laughing
contest. The twist is that the spell does not make the broccoli disappear;
it makes it impossible to stop giggling long enough to finish it.

The world model tracks:
- physical state: servings, sparkle, wobble, eaten/untouched
- emotional state: disgust, curiosity, delight, pride, relief

The story should read like a complete tiny tale with a setup, turn, and end.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    time_of_day: str = "dinnertime"
    table_name: str = "the table"


@dataclass
class Spell:
    id: str
    name: str
    method: str
    effect: str
    sparkle: str
    undo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    taste: str
    can_be_transformed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    spell: str
    food: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="dinnertime", table_name="the table"),
    "backyard": Setting(place="the backyard", time_of_day="picnic time", table_name="the picnic blanket"),
    "cafeteria": Setting(place="the cafeteria", time_of_day="lunch time", table_name="the tray"),
}

SPELLS = {
    "giggle": Spell(
        id="giggle",
        name="giggle-glimmer spell",
        method="waved a spoon in a circle and whispered 'brocolli, bloop!'",
        effect="made the broccoli wobble and sparkle",
        sparkle="green sparkles",
        undo="stop laughing",
        tags={"magic", "comedy", "brocolli"},
    ),
    "polish": Spell(
        id="polish",
        name="shine-silly spell",
        method="tapped the bowl twice and said 'twinkle, twiddle, tidy!'",
        effect="made every broccoli floret shine like a tiny jewel",
        sparkle="gold sparkles",
        undo="wipe the bowl",
        tags={"magic", "comedy"},
    ),
    "bounce": Spell(
        id="bounce",
        name="bounce-and-boom spell",
        method="snapped fingers over the plate and whispered 'hop, hop, hooray!'",
        effect="made the broccoli bounce like tiny green springs",
        sparkle="mint sparks",
        undo="hold the plate still",
        tags={"magic", "comedy"},
    ),
}

FOODS = {
    "brocolli": Food(
        id="brocolli",
        label="brocolli",
        phrase="a little mountain of brocolli",
        taste="green and crunchy",
        can_be_transformed=True,
        tags={"brocolli", "green", "vegetable"},
    ),
    "peas": Food(
        id="peas",
        label="peas",
        phrase="a bowl of peas",
        taste="sweet and soft",
        can_be_transformed=True,
        tags={"vegetable"},
    ),
    "carrots": Food(
        id="carrots",
        label="carrots",
        phrase="a plate of carrots",
        taste="sweet and bright",
        can_be_transformed=True,
        tags={"vegetable"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Max", "Theo"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def food_is_eligible(food: Food, spell: Spell) -> bool:
    return food.can_be_transformed and "magic" in spell.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for spell_id, spell in SPELLS.items():
            for food_id, food in FOODS.items():
                if food_is_eligible(food, spell):
                    combos.append((place, spell_id, food_id))
    return combos


def explain_rejection(place: str, spell: Spell, food: Food) -> str:
    return (
        f"(No story: the {spell.name} needs a transformable food, and {food.label} "
        f"would not make a sensible comedy scene here.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={
        "disgust": 0.0,
        "curiosity": 0.0,
        "delight": 0.0,
        "pride": 0.0,
        "relief": 0.0,
    }))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    food = world.add(Entity(id=params.food, kind="thing", type="food", label=params.food, phrase=FOODS[params.food].phrase, owner=params.name, meters={
        "servings": 1.0,
        "sparkle": 0.0,
        "wobble": 0.0,
        "eaten": 0.0,
        "untouched": 1.0,
    }, memes={
        "magic": 0.0,
    }))
    spell = SPELLS[params.spell]

    world.facts.update(hero=hero, parent=parent, food=food, spell=spell, params=params)

    # Setup
    world.say(f"It was {world.setting.time_of_day} in {world.setting.place}, and {hero.id} sat at {world.setting.table_name} with a tiny sigh.")
    world.say(f"On the plate was {food.phrase}, and {food.label} looked very {FOODS[params.food].taste}.")
    world.say(f"{hero.id} made a face, because {food.label} was exactly the sort of thing a picky kid might poke with a fork and ignore.")

    # Turn
    hero.memes["disgust"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"Then {parent.label} smiled and tried a silly trick: {spell.method}.")
    food.meters["sparkle"] += 1
    food.meters["wobble"] += 1
    food.memes["magic"] += 1
    hero.memes["delight"] += 1
    world.say(f"At once, the {food.label} {spell.effect}, and the whole table flashed with {spell.sparkle}.")
    world.say(f"{hero.id} blinked, then snorted. The spell was so goofy that even the broccoli seemed to be laughing.")

    # Resolution
    if params.food == "brocolli":
        hero.memes["delight"] += 1
        hero.memes["pride"] += 1
        food.meters["eaten"] = 1.0
        food.meters["untouched"] = 0.0
        world.say(f"{hero.id} laughed so hard that {hero.pronoun('subject')} took a bite without even noticing the first one.")
        world.say(f"After a few more giggles, the whole plate was gone, and {hero.id} held up an empty fork like a trophy.")
        world.say(f"{parent.label} laughed too and said that sometimes the best way to beat broccoli was to make it funny first.")
    else:
        food.meters["eaten"] = 1.0
        food.meters["untouched"] = 0.0
        hero.memes["relief"] += 1
        world.say(f"{hero.id} decided the magic made dinner interesting enough to try a bite.")
        world.say(f"By the end, the plate was clean, {hero.id}'s grin was wide, and the sparkles had faded like a joke told just right.")

    world.say(f"The last thing anyone saw was {hero.id} wiping a happy mouth while the green sparkles drifted away above {world.setting.table_name}.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    spell = f["spell"]
    food = f["food"]
    return [
        f"Write a short comedy story for a child who meets {food.label} at dinner and discovers a magic trick.",
        f"Tell a silly story where {hero.id} is surprised by {spell.name} and learns to like {food.label}.",
        f"Make a funny tiny tale about a child, a plate of {food.label}, and a magical dinner moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    food = f["food"]
    spell = f["spell"]
    return [
        QAItem(
            question=f"What did {hero.id} see on the table at the start?",
            answer=f"{hero.id} saw {food.phrase} at {world.setting.table_name}, and it looked very green and crunchy.",
        ),
        QAItem(
            question=f"What silly magic did {parent.label} use?",
            answer=f"{parent.label.capitalize()} used the {spell.name}, which {spell.effect}.",
        ),
        QAItem(
            question=f"Why did the dinner turn funny instead of gloomy?",
            answer=f"It turned funny because the magic made {food.label} sparkle and wobble, so {hero.id} started laughing instead of complaining.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is broccoli?",
            answer="Broccoli is a green vegetable with little tree-like florets. People often eat it cooked, steamed, or roasted.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic in a story means something impossible or surprising happens, like sparkles, spells, or a funny change that could not happen in real life.",
        ),
        QAItem(
            question="Why can comedy stories be fun for kids?",
            answer="Comedy stories are fun because they include silly surprises, funny words, and happy endings that make people smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
food_ok(F) :- food(F).
spell_ok(S) :- spell(S).
valid_story(P, S, F) :- setting(P), spell_ok(S), food_ok(F), transformable(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sp in SPELLS.items():
        lines.append(asp.fact("spell", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.can_be_transformed:
            lines.append(asp.fact("transformable", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with broccoli and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--food", choices=FOODS)
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
    if args.spell and args.food:
        if not food_is_eligible(FOODS[args.food], SPELLS[args.spell]):
            raise StoryError(explain_rejection(args.place or "kitchen", SPELLS[args.spell], FOODS[args.food]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spell is None or c[1] == args.spell)
              and (args.food is None or c[2] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell, food = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, spell=spell, food=food, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={dict(e.meters)}")
        if e.memes:
            parts.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("kitchen", "giggle", "brocolli", "Mia", "girl", "mother"),
            StoryParams("backyard", "polish", "peas", "Leo", "boy", "father"),
            StoryParams("cafeteria", "bounce", "carrots", "Nora", "girl", "mother"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
