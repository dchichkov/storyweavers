#!/usr/bin/env python3
"""
storyworlds/worlds/lunch_dialogue_animal_story.py
=================================================

A small story world about animal friends, lunch, and a spoken misunderstanding
that gets repaired with a kind dialogue.

Premise:
- Two animal characters share lunch in a simple setting.
- One character wants a certain lunch food or seat arrangement.
- A mismatch or hurt feeling appears through dialogue.
- The characters talk it out, share food, and end with a warm lunch image.

This world keeps the prose close to an Animal Story tone: concrete, gentle,
and driven by what the characters say and do.
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
@dataclass
class Entity:
    id: str
    kind: str = "character"
    species: str = "animal"
    name: str = ""
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Setting:
    place: str
    indoors: bool
    lunch_spot: str
    table_item: str


@dataclass
class Lunch:
    main_food: str
    side_food: str
    drink: str
    shared_food: str
    wants_share: bool
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    lunch: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, lunch: Lunch) -> None:
        self.setting = setting
        self.lunch = lunch
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", indoors=False, lunch_spot="a red picnic blanket", table_item="basket"),
    "porch": Setting(place="the porch", indoors=False, lunch_spot="a low wooden bench", table_item="tray"),
    "kitchen": Setting(place="the kitchen", indoors=True, lunch_spot="a small round table", table_item="plate"),
}

LUNCHES = {
    "sandwiches": Lunch(
        main_food="jam sandwiches",
        side_food="apple slices",
        drink="milk",
        shared_food="a cookie",
        wants_share=True,
        smell="sweet",
        tags={"bread", "sweet", "share"},
    ),
    "carrots": Lunch(
        main_food="carrot sticks",
        side_food="peas",
        drink="water",
        shared_food="a cracker",
        wants_share=True,
        smell="fresh",
        tags={"crunchy", "garden", "share"},
    ),
    "soup": Lunch(
        main_food="warm soup",
        side_food="soft bread",
        drink="tea",
        shared_food="a bun",
        wants_share=False,
        smell="cozy",
        tags={"warm", "cozy"},
    ),
    "berries": Lunch(
        main_food="berries and rice cakes",
        side_food="banana pieces",
        drink="juice",
        shared_food="a little muffin",
        wants_share=True,
        smell="bright",
        tags={"sweet", "fruit", "share"},
    ),
}

ANIMALS = {
    "rabbit": {"name_pool": ["Ruby", "Milo", "Bunny", "Pip", "Hazel"], "role": "rabbit"},
    "bear": {"name_pool": ["Teddy", "Bruno", "Mabel", "Nori", "Bram"], "role": "bear"},
    "fox": {"name_pool": ["Fiona", "Finn", "Rusty", "Poppy", "Jasper"], "role": "fox"},
    "cat": {"name_pool": ["Coco", "Mittens", "Luna", "Toby", "Maya"], "role": "cat"},
    "dog": {"name_pool": ["Scout", "Penny", "Baxter", "Lily", "Rufus"], "role": "dog"},
}

TRAITS = ["gentle", "cheerful", "curious", "tidy", "patient", "shy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def lunch_is_reasonable(setting: Setting, lunch: Lunch) -> bool:
    if setting.indoors and lunch.main_food == "warm soup":
        return True
    if not setting.indoors and lunch.main_food in {"jam sandwiches", "carrot sticks", "berries and rice cakes"}:
        return True
    return True


def choose_compromise(lunch: Lunch) -> str:
    if lunch.wants_share:
        return f"share {lunch.shared_food}"
    return f"split the {lunch.shared_food}"


def explain_rejection(setting: Setting, lunch: Lunch) -> str:
    return f"(No story: lunch and setting do not make a gentle animal lunch scene together.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.name} the {hero.role} and {friend.name} the {friend.role} were friends."
    )
    world.say(
        f"They liked quiet lunches because {world.lunch.smell} food made the day feel calm."
    )


def setup_lunch(world: World, hero: Entity, friend: Entity) -> None:
    s = world.setting
    l = world.lunch
    world.say(
        f"At {s.place}, they sat at {s.lunch_spot} and looked at a lunch of {l.main_food}, {l.side_food}, and {l.drink}."
    )
    world.say(
        f"{hero.name} smiled and said, \"This smells {l.smell}!\""
    )
    world.say(
        f"{friend.name} nodded. \"It looks nice,\" {friend.pronoun()} said."
    )


def conflict(world: World, hero: Entity, friend: Entity) -> None:
    l = world.lunch
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(
        f"{hero.name} reached for {l.shared_food}. \"Can we have that for both of us?\" {hero.pronoun()} asked."
    )
    if l.wants_share:
        world.say(
            f"{friend.name} paused. \"I wanted to keep it for later,\" {friend.pronoun()} said softly."
        )
    else:
        world.say(
            f"{friend.name} shook {friend.possessive()} head. \"I was saving it for after lunch,\" {friend.pronoun()} said."
        )
    world.say(
        f"{hero.name} looked down. \"Oh,\" {hero.pronoun()} said, and the table went quiet."
    )


def resolution(world: World, hero: Entity, friend: Entity) -> None:
    l = world.lunch
    world.say(
        f"{friend.name} took a breath and said, \"We can still make this lunch kind.\""
    )
    if l.wants_share:
        world.say(
            f"\"Let's share {l.shared_food} now,\" {friend.name} said, \"and save the last bite for later.\""
        )
    else:
        world.say(
            f"\"Let's split the {l.shared_food} now,\" {friend.name} said, \"so we both get a little treat.\""
        )
    world.say(
        f"{hero.name}'s ears perked up. \"Yes, please,\" {hero.pronoun()} said."
    )
    world.say(
        f"They laughed, passed the food across the table, and finished lunch together."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    l = world.lunch
    s = world.setting
    world.say(
        f"By the end, the lunch box was lighter, the air felt calmer, and {s.place} looked warm and friendly."
    )
    world.say(
        f"{hero.name} and {friend.name} sat side by side, happy to have a lunch that tasted even better after the talking."
    )


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.lunch not in LUNCHES:
        raise StoryError(f"Unknown lunch: {params.lunch}")
    setting = SETTINGS[params.setting]
    lunch = LUNCHES[params.lunch]
    if not lunch_is_reasonable(setting, lunch):
        raise StoryError(explain_rejection(setting, lunch))

    world = World(setting, lunch)

    hero_species = rng.choice(list(ANIMALS.keys()))
    friend_species = rng.choice([k for k in ANIMALS.keys() if k != hero_species])

    hero = world.add(Entity(
        id="hero",
        species=hero_species,
        name=params.hero or rng.choice(ANIMALS[hero_species]["name_pool"]),
        label=hero_species,
        role=ANIMALS[hero_species]["role"],
    ))
    friend = world.add(Entity(
        id="friend",
        species=friend_species,
        name=params.friend or rng.choice(ANIMALS[friend_species]["name_pool"]),
        label=friend_species,
        role=ANIMALS[friend_species]["role"],
    ))

    hero.memes["fondness"] = 1
    friend.memes["fondness"] = 1

    introduce(world, hero, friend)
    setup_lunch(world, hero, friend)
    world.say("")
    conflict(world, hero, friend)
    world.say("")
    resolution(world, hero, friend)
    ending(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
        lunch=lunch,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    lunch: Lunch = f["lunch"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short animal story about {hero.name} and {friend.name} sharing lunch at {setting.place}.',
        f'Tell a gentle dialogue story where two animals disagree about {lunch.shared_food} during lunch, then fix it kindly.',
        f'Write a small story with lunch, talking, and a happy ending at {setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    lunch: Lunch = f["lunch"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.name} the {hero.role} and {friend.name} the {friend.role}.",
        ),
        QAItem(
            question=f"What food was on the table for lunch?",
            answer=f"The lunch had {lunch.main_food}, {lunch.side_food}, {lunch.drink}, and {lunch.shared_food}.",
        ),
        QAItem(
            question=f"What did {hero.name} ask about during lunch?",
            answer=f"{hero.name} asked if they could have {lunch.shared_food} for both of them.",
        ),
        QAItem(
            question=f"How did the animals solve the lunch problem?",
            answer=f"They talked kindly and decided to share the food so both animals could enjoy lunch together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "lunch": [
        QAItem(
            question="What is lunch?",
            answer="Lunch is the meal people and animals eat in the middle of the day.",
        )
    ],
    "share": [
        QAItem(
            question="Why do friends share food?",
            answer="Friends share food to be kind and make sure everyone gets some.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other in their own words.",
        )
    ],
    "animal": [
        QAItem(
            question="What makes an animal story feel friendly?",
            answer="An animal story feels friendly when the animals talk, have feelings, and solve a small problem kindly.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["lunch"])
    out.extend(WORLD_KNOWLEDGE["share"])
    out.extend(WORLD_KNOWLEDGE["dialogue"])
    out.extend(WORLD_KNOWLEDGE["animal"])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A lunch scene is valid when a setting and lunch fit together.
valid_scene(S, L) :- setting(S), lunch(L), compatible(S, L).

% Two animal characters can have a dialogue story in any valid scene.
valid_story(S, L) :- valid_scene(S, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        lines.append(asp.fact("lunch_spot", sid, s.lunch_spot))
    for lid, l in LUNCHES.items():
        lines.append(asp.fact("lunch", lid))
        for tag in sorted(l.tags):
            lines.append(asp.fact("tag", lid, tag))
    for sid, s in SETTINGS.items():
        for lid, l in LUNCHES.items():
            if lunch_is_reasonable(s, l):
                lines.append(asp.fact("compatible", sid, lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_scene/2."))
    return sorted(set(asp.atoms(model, "valid_scene")))


def asp_verify() -> int:
    python_set = {(s, l) for s in SETTINGS for l in LUNCHES if lunch_is_reasonable(SETTINGS[s], LUNCHES[l])}
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches lunch scenes ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal lunch dialogue storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lunch", choices=LUNCHES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    lunch = args.lunch or rng.choice(list(LUNCHES.keys()))
    if setting not in SETTINGS or lunch not in LUNCHES:
        raise StoryError("Unknown setting or lunch.")
    if not lunch_is_reasonable(SETTINGS[setting], LUNCHES[lunch]):
        raise StoryError(explain_rejection(SETTINGS[setting], LUNCHES[lunch]))
    hero = args.hero or ""
    friend = args.friend or ""
    return StoryParams(setting=setting, lunch=lunch, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
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
        lines.append(f"  {e.id}: {e.name} the {e.role} ({e.species}) memes={dict(e.memes)} meters={dict(e.meters)}")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  lunch: {world.lunch.main_food}, {world.lunch.side_food}, {world.lunch.drink}, {world.lunch.shared_food}")
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
        print(asp_program("#show valid_scene/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible scenes:")
        for s, l in combos:
            print(f"  {s:8} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in SETTINGS:
            for lid in LUNCHES:
                if lunch_is_reasonable(SETTINGS[sid], LUNCHES[lid]):
                    samples.append(generate(StoryParams(setting=sid, lunch=lid, seed=base_seed)))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
