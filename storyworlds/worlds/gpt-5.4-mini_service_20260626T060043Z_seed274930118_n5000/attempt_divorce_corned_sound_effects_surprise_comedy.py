#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/attempt_divorce_corned_sound_effects_surprise_comedy.py
===============================================================================================================

A small comedy storyworld about a surprise dinner mishap that leads to a very
silly attempt at divorce, noisy sound effects, and a happy reset.

Seed words:
- attempt
- divorce
- corned

Narrative instruments:
- Sound Effects
- Surprise

Style:
- Comedy

The core premise:
A pair of co-parents / spouses plans a special corned dinner. A loud, messy,
unexpected surprise makes one partner dramatically attempt a divorce. The other
partner responds with humor, sound effects, and a simple fix: admit the mix-up,
clean up the kitchen, and laugh together.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- ASCII-friendly prose and QA
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"woman", "mother", "mom", "wife", "girl"}
        masculine = {"man", "father", "dad", "husband", "boy"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Meal:
    id: str
    label: str
    phrase: str
    smell: str
    sound: str
    surprise: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    can_use: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.noise_level: float = 0.0
        self.surprise_level: float = 0.0
        self.mess_level: float = 0.0

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"cook"}),
    "dining_room": Setting(place="the dining room", affords={"cook"}),
    "patio": Setting(place="the patio", affords={"cook"}),
}

MEALS = {
    "corned_supper": Meal(
        id="corned_supper",
        label="corned supper",
        phrase="a steaming corned supper",
        smell="savory and salty",
        sound="sizzle-sizzle",
        surprise="a wobbly lid popped open by accident",
        mess="broth spilled across the floor",
        tags={"corned", "surprise"},
    ),
    "corned_sandwiches": Meal(
        id="corned_sandwiches",
        label="corned sandwiches",
        phrase="a tower of corned sandwiches",
        smell="warm and buttery",
        sound="crinkle-crunch",
        surprise="the sandwich stack slid like a tiny avalanche",
        mess="mustard spotted the tablecloth",
        tags={"corned", "surprise"},
    ),
    "corned_hash": Meal(
        id="corned_hash",
        label="corned hash",
        phrase="a pan of corned hash",
        smell="toasty and peppery",
        sound="chop-chop",
        surprise="the pan hissed like a snake with manners",
        mess="a potato bounced onto the chair",
        tags={"corned", "sound effects"},
    ),
}

PROPS = {
    "lid": Prop(
        id="lid",
        label="lid",
        phrase="a shiny lid",
        sound="pop!",
        can_use={"cook"},
        tags={"sound effects", "surprise"},
    ),
    "spatula": Prop(
        id="spatula",
        label="spatula",
        phrase="a long spatula",
        sound="tap-tap",
        can_use={"cook"},
        tags={"sound effects"},
    ),
    "napkin": Prop(
        id="napkin",
        label="napkin",
        phrase="a stack of napkins",
        sound="fwap!",
        can_use={"clean"},
        tags={"sound effects"},
    ),
}

NAMES = ["Maya", "Noah", "Lena", "Ben", "Ivy", "Theo", "Ada", "Milo"]
TRAITS = ["silly", "cheerful", "dramatic", "bouncy", "curious", "goofy"]


@dataclass
class StoryParams:
    place: str
    meal: str
    name1: str
    name2: str
    type1: str
    type2: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A meal is noisy or surprising when it has the matching tag.
noisy(M) :- meal(M), tags(M, sound_effects).
surprising(M) :- meal(M), tags(M, surprise).

% An attempt at divorce is reasonable only if a surprising, noisy mess occurs.
valid_story(P, M) :- setting(P), meal(M), noisy(M), surprising(M), corned(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, meal in MEALS.items():
        lines.append(asp.fact("meal", mid))
        if "corned" in meal.tags:
            lines.append(asp.fact("corned", mid))
        for tag in sorted(meal.tags):
            lines.append(asp.fact("tags", mid, tag.replace(" ", "_")))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m) for p in SETTINGS for m in MEALS if reasonableness_gate(p, m)}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches Python gate ({len(python_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def reasonableness_gate(place: str, meal: str) -> bool:
    if place not in SETTINGS:
        return False
    if meal not in MEALS:
        return False
    return True


def explain_invalid(place: str, meal: str) -> str:
    return f"(No story: the setting {place!r} or meal {meal!r} is not valid for this comedy world.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def intro_line(a: Entity, b: Entity, meal: Meal) -> str:
    return (
        f"{a.id} and {b.id} were a pair of partners who loved making dinner sound funny. "
        f"Tonight they planned {meal.phrase}."
    )


def cook_line(a: Entity, meal: Meal) -> str:
    return (
        f"{a.id} gave the pan a careful shake, and the kitchen answered with "
        f'"{meal.sound}!"'
    )


def surprise_line(meal: Meal) -> str:
    return f"Then {meal.surprise}, and everybody blinked."


def divorce_attempt_line(a: Entity, b: Entity) -> str:
    return (
        f"{a.id} pointed at the spill and said, \"I attempt divorce!\" "
        f"{b.id} gasped so hard it sounded like a squeaky trumpet."
    )


def comic_fix_line(a: Entity, b: Entity, prop: Prop, meal: Meal) -> str:
    return (
        f"Then {b.id} grabbed {prop.phrase}, went \"fwap-fwap!\", and laughed. "
        f"{a.id} laughed too, because the trouble was only a silly kitchen mess."
    )


def ending_line(a: Entity, b: Entity, meal: Meal) -> str:
    return (
        f"Soon the floor was clean, the corned smell still hung in the air, and "
        f"{a.id} and {b.id} sat down to eat while the last little \"pop!\" of the lid "
        f"echoed like a joke."
    )


def tell(world: World, params: StoryParams) -> World:
    meal = MEALS[params.meal]
    a = world.add(Entity(id=params.name1, kind="character", type=params.type1, role="partner"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.type2, role="partner"))
    prop = world.add(Entity(id="napkin", kind="thing", type="thing", label="napkin", phrase=PROPS["napkin"].phrase))
    world.facts.update(
        a=a,
        b=b,
        meal=meal,
        prop=prop,
        place=params.place,
        surprise=True,
        attempt_divorce=True,
    )

    a.memes["anticipation"] = 1.0
    b.memes["anticipation"] = 1.0

    world.say(intro_line(a, b, meal))
    world.say(cook_line(a, meal))
    world.para()
    world.say(surprise_line(meal))
    world.say(f"The room felt extra loud, with a little surprise and a lot of clatter.")
    world.say(divorce_attempt_line(a, b))
    a.memes["drama"] = 1.0
    b.memes["shock"] = 1.0

    world.para()
    world.say(comic_fix_line(a, b, PROPS["napkin"], meal))
    a.memes["drama"] = 0.0
    a.memes["joy"] = 1.0
    b.memes["shock"] = 0.0
    b.memes["joy"] = 1.0

    world.say(ending_line(a, b, meal))
    world.mess_level = 0.0
    world.noise_level = 1.0
    world.surprise_level = 0.0
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    meal: Meal = f["meal"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    return [
        f"Write a funny story where {a.id} and {b.id} try to cook {meal.phrase} and something surprising goes wrong.",
        f"Tell a comedy story with a big sound effect, a surprise, and an attempt at divorce over {meal.label}.",
        f"Write a short child-friendly story that includes the words attempt, divorce, and corned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["a"]
    b: Entity = f["b"]
    meal: Meal = f["meal"]

    return [
        QAItem(
            question=f"Who were the story partners in the kitchen?",
            answer=f"The story was about {a.id} and {b.id}, who were cooking together in {world.setting.place}.",
        ),
        QAItem(
            question=f"What kind of meal were they making?",
            answer=f"They were making {meal.phrase}, which was a corned dinner with a funny smell and sound.",
        ),
        QAItem(
            question=f"What made the story turn into a silly mess?",
            answer=f"A surprise happened in the kitchen, and that loud, messy moment made {a.id} dramatically attempt divorce.",
        ),
        QAItem(
            question=f"How did the problem end?",
            answer=f"They used a napkin, cleaned up, laughed, and stayed together after the silly kitchen mix-up.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "corned": [
        QAItem(
            question="What does corned usually mean in a meal?",
            answer="Corned usually means the meat or food was cured with salt, so it tastes salty and savory.",
        ),
    ],
    "sound effects": [
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that pretend to be noises, like pop, bang, swish, or fwap.",
        ),
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it makes people pause and look twice.",
        ),
    ],
    "divorce": [
        QAItem(
            question="What is a divorce?",
            answer="A divorce is when married adults decide to end their marriage and live apart.",
        ),
    ],
    "attempt": [
        QAItem(
            question="What does it mean to attempt something?",
            answer="To attempt something means to try to do it, even if it may not work the first time.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    meal: Meal = f["meal"]
    out: list[QAItem] = []
    tags = set(meal.tags) | {"attempt", "divorce"}
    for key in ["attempt", "divorce", "corned", "sound effects", "surprise"]:
        if key in tags or key in meal.tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  noise_level={world.noise_level}")
    lines.append(f"  surprise_level={world.surprise_level}")
    lines.append(f"  mess_level={world.mess_level}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with corned dinner, surprise, sound effects, and a fake attempt at divorce.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--meal", choices=MEALS.keys())
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--type1", choices=["woman", "man", "mother", "father", "wife", "husband"])
    ap.add_argument("--type2", choices=["woman", "man", "mother", "father", "wife", "husband"])
    ap.add_argument("--trait1", choices=TRAITS)
    ap.add_argument("--trait2", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    meal = args.meal or rng.choice(list(MEALS.keys()))
    if not reasonableness_gate(place, meal):
        raise StoryError(explain_invalid(place, meal))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    type1 = args.type1 or rng.choice(["woman", "man", "wife", "husband"])
    type2 = args.type2 or rng.choice(["man", "woman", "husband", "wife"])
    trait1 = args.trait1 or rng.choice(TRAITS)
    trait2 = args.trait2 or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        meal=meal,
        name1=name1,
        name2=name2,
        type1=type1,
        type2=type2,
        trait1=trait1,
        trait2=trait2,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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


CURATED = [
    StoryParams(
        place="kitchen",
        meal="corned_supper",
        name1="Maya",
        name2="Noah",
        type1="wife",
        type2="husband",
        trait1="dramatic",
        trait2="cheerful",
    ),
    StoryParams(
        place="dining_room",
        meal="corned_sandwiches",
        name1="Lena",
        name2="Ben",
        type1="woman",
        type2="man",
        trait1="goofy",
        trait2="curious",
    ),
    StoryParams(
        place="patio",
        meal="corned_hash",
        name1="Ivy",
        name2="Theo",
        type1="wife",
        type2="husband",
        trait1="bouncy",
        trait2="silly",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combinations:\n")
        for p, m in stories:
            print(f"  {p:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
