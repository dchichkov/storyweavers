#!/usr/bin/env python3
"""
A small storyworld about an aperitif party, a magical transformation, and a
comedic happy ending.

The seed premise: someone is preparing an aperitif, but a magic mishap turns
the snacks into something surprising. The story resolves when the character
uses the magic kindly and ends with a cheerful, funny party image.
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

APERITIF_SNACKS = {
    "olives": "a bowl of olives",
    "crackers": "a plate of crackers",
    "cheese": "a little cheese board",
    "grapes": "a bunch of grapes",
    "nuts": "a small dish of nuts",
}

DRINKS = {
    "sparkling water": "sparkling water",
    "juice": "apple juice",
    "lemonade": "lemonade",
}

SETTINGS = {
    "garden": "the garden",
    "balcony": "the balcony",
    "kitchen": "the kitchen table",
    "living room": "the living room",
}

CHARACTER_NAMES = ["Mina", "Noah", "Lina", "Theo", "Pia", "Ben", "Zara", "Owen"]
CHARACTER_TYPES = ["girl", "boy"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    setting: str
    snack: str
    drink: str
    name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic aperitif magic story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=APERITIF_SNACKS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHARACTER_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    snack = args.snack or rng.choice(list(APERITIF_SNACKS))
    drink = args.drink or rng.choice(list(DRINKS))
    gender = args.gender or rng.choice(CHARACTER_TYPES)
    name = args.name or rng.choice(CHARACTER_NAMES)
    if snack == "nuts" and drink == "juice":
        # harmless, but a little too snacky/ordinary; keep the world varied.
        pass
    return StoryParams(setting=setting, snack=snack, drink=drink, name=name, gender=gender)


def _magic_transformation(item: Entity) -> None:
    item.meters["sparkle"] = item.meters.get("sparkle", 0.0) + 1.0


def generate_story(world: World, hero: Entity, snack: Entity, drink: Entity) -> None:
    world.say(
        f"{hero.id} was arranging an aperitif on {world.setting} with "
        f"{snack.phrase} and {drink.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted the little party to look fancy, "
        f"but the magic spoon on the tray twitched and sneezed."
    )
    snack.meters["transformed"] = 1.0
    snack.label = "party birds"
    snack.phrase = "a noisy flock of tiny party birds"
    _magic_transformation(snack)
    world.say(
        f"With a pop, {world.facts['snack_name']} turned into {snack.phrase}, "
        f"and everybody stared in surprised silence for one funny second."
    )
    world.para()
    world.say(
        f"{hero.id} blinked, then laughed so hard {hero.pronoun('possessive')} shoulders bounced."
    )
    world.say(
        f"{hero.pronoun().capitalize()} gave the birds a crumb, whispered a new magic word, "
        f"and kindly turned them back into {world.facts['snack_name']}."
    )
    snack.meters["transformed"] = 0.0
    snack.phrase = world.facts["original_snack_phrase"]
    snack.label = world.facts["snack_name"]
    world.say(
        f"At last, the aperitif looked just right again: snacks on the table, "
        f"{drink.phrase} in the glass, and one last crumb on {hero.pronoun('possessive')} nose."
    )
    world.say(
        f"The whole room laughed, and {hero.id} bowed like a very serious magician "
        f"who had definitely planned the joke all along."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    snack_phrase = APERITIF_SNACKS[params.snack]
    snack = world.add(Entity(id="snack", label=params.snack, phrase=snack_phrase, owner=hero.id))
    drink = world.add(Entity(id="drink", label=params.drink, phrase=DRINKS[params.drink], owner=hero.id))
    world.facts.update(
        hero=hero,
        snack=snack,
        drink=drink,
        snack_name=params.snack,
        original_snack_phrase=snack_phrase,
        setting=params.setting,
    )
    generate_story(world, hero, snack, drink)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short, funny story about an aperitif that changes by magic, and ends happily.",
        f"Tell a cheerful comedy where {world.facts['hero'].id} prepares an aperitif on {world.setting} "
        f"and the snack suddenly transforms.",
        f"Write a child-friendly story with magic, transformation, and a happy ending about an aperitif table.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    snack: Entity = world.facts["snack"]  # type: ignore[assignment]
    drink: Entity = world.facts["drink"]  # type: ignore[assignment]
    original = world.facts["snack_name"]
    return [
        QAItem(
            question=f"What was {hero.id} preparing on {world.setting}?",
            answer=f"{hero.id} was preparing an aperitif with {snack.phrase} and {drink.phrase}.",
        ),
        QAItem(
            question=f"What funny magic thing happened to the {original}?",
            answer=f"The {original} transformed into {snack.phrase} for a moment, which made everyone laugh.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the snack changed back, the table ready, and everyone laughing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aperitif?",
            answer="An aperitif is a small drink or light snack served before a meal to help start the gathering.",
        ),
        QAItem(
            question="What does transformation mean in a magic story?",
            answer="Transformation means something changes into something else, often suddenly because of magic.",
        ),
        QAItem(
            question="Why do comedy stories make people smile?",
            answer="Comedy stories use funny surprises, silly mistakes, and happy moments that make people smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
aperitif_story(H, S) :- hero(H), snack(S), transformed(S).
happy_ending(H) :- hero(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in APERITIF_SNACKS:
        lines.append(asp.fact("snack", s))
    for d in DRINKS:
        lines.append(asp.fact("drink", d))
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams(setting="garden", snack="olives", drink="sparkling water", name="Mina", gender="girl"),
    StoryParams(setting="balcony", snack="crackers", drink="lemonade", name="Theo", gender="boy"),
    StoryParams(setting="kitchen", snack="cheese", drink="juice", name="Lina", gender="girl"),
    StoryParams(setting="living room", snack="grapes", drink="sparkling water", name="Noah", gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
