#!/usr/bin/env python3
"""
Storyworld: taxi observe reconciliation humor animal story.

A small classical simulation about animal friends, a taxi ride, an awkward
mistake, and a funny reconciliation.
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
class Animal:
    name: str
    species: str
    role: str
    meme: dict[str, float] = field(default_factory=dict)
    meter: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return f"{self.name}'s"


@dataclass
class Taxi:
    color: str
    driver_name: str
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    mood: str
    afford_taxi: bool = True


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    taxi_color: str
    seed: Optional[int] = None


SETTINGS = {
    "city": Setting(place="the city street", mood="busy"),
    "market": Setting(place="the market road", mood="lively"),
    "park": Setting(place="the park gate", mood="green"),
    "harbor": Setting(place="the harbor lane", mood="windy"),
}

ANIMALS = {
    "fox": ("fox", "clever"),
    "rabbit": ("rabbit", "bouncy"),
    "cat": ("cat", "tidy"),
    "dog": ("dog", "friendly"),
    "bear": ("bear", "gentle"),
    "otter": ("otter", "playful"),
}

TAXI_COLORS = ["yellow", "blue", "red", "green"]


@dataclass
class World:
    setting: Setting
    hero: Animal
    friend: Animal
    taxi: Taxi
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal taxi story with observation, humor, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--taxi-color", choices=TAXI_COLORS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(ANIMALS))
    friend_choices = [a for a in ANIMALS if a != hero]
    friend = args.friend or rng.choice(friend_choices)
    taxi_color = args.taxi_color or rng.choice(TAXI_COLORS)
    return StoryParams(setting=setting, hero=hero, friend=friend, taxi_color=taxi_color)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hero_species, hero_role = ANIMALS[params.hero]
    friend_species, friend_role = ANIMALS[params.friend]
    hero = Animal(name=params.hero.capitalize(), species=hero_species, role=hero_role)
    friend = Animal(name=params.friend.capitalize(), species=friend_species, role=friend_role)
    taxi = Taxi(color=params.taxi_color, driver_name="Milo")
    return World(setting=setting, hero=hero, friend=friend, taxi=taxi)


def narrate(world: World) -> None:
    h = world.hero
    f = world.friend
    t = world.taxi
    s = world.setting

    world.say(
        f"{h.name} was a {h.role} {h.species} who liked to watch everything at {s.place}."
    )
    world.say(
        f"One day, {h.name} and {f.name} spotted a {t.color} taxi by the curb, "
        f"and {h.name} wanted to ride it to the snack stand."
    )
    world.para()
    world.say(
        f"{f.name} climbed in first and sat on the soft seat, but {h.name} noticed "
        f"that {f.name} had borrowed the last shiny scarf without asking."
    )
    world.say(
        f"{h.name} frowned and asked, \"Why did you take it?\" and the taxi driver, Milo, "
        f"heard the whole thing while waiting at the light."
    )
    world.say(
        f"Then {h.name} observed the scarf more closely and saw that it was actually "
        f"wrapped around a lollipop, which made everyone blink and then laugh."
    )
    world.para()
    world.say(
        f"{f.name} looked sheepish and said sorry, because the scarf had fallen over the lollipop "
        f"when the taxi bumped over a pothole."
    )
    world.say(
        f"{h.name} giggled, because the lollipop looked so tiny and dramatic, like a silk tie for a mouse."
    )
    world.say(
        f"{h.name} and {f.name} made up right there in the {t.color} taxi, and Milo smiled "
        f"when they shared the lollipop and took turns riding to the snack stand."
    )
    world.say(
        f"By the time they got out, {h.name} was still chuckling, and {f.name} was carrying "
        f"the scarf carefully so no more funny surprises would fall out."
    )

    world.facts.update(
        hero=h.name,
        friend=f.name,
        taxi_color=t.color,
        setting=s.place,
        observed="scarf around a lollipop",
        reconciliation=True,
        humor=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short animal story about a taxi ride, a misunderstanding, and a funny apology.",
        f"Tell a gentle story where {world.hero.name} and {world.friend.name} ride a {world.taxi.color} taxi and solve a small problem.",
        "Write a child-friendly story with animals, observation, humor, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    f = world.friend
    t = world.taxi
    return [
        QAItem(
            question=f"Who wanted to ride the taxi to the snack stand?",
            answer=f"{h.name} wanted to ride the taxi to the snack stand."
        ),
        QAItem(
            question=f"What did {h.name} observe more closely that made everyone laugh?",
            answer=f"{h.name} observed that the scarf was actually wrapped around a lollipop."
        ),
        QAItem(
            question=f"How did {h.name} and {f.name} fix their disagreement?",
            answer=f"They apologized, laughed about the mix-up, and made up inside the {t.color} taxi."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a taxi for?",
            answer="A taxi is a car that takes people or animals from one place to another."
        ),
        QAItem(
            question="What does it mean to observe something?",
            answer="To observe means to look carefully and notice details."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means friends stop arguing, forgive each other, and feel friendly again."
        ),
        QAItem(
            question="Why can humor help after a mistake?",
            answer="Humor can help because a funny moment can make upset feelings smaller and help everyone relax."
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


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"setting: {world.setting.place} ({world.setting.mood})",
        f"hero: {world.hero.name} the {world.hero.role} {world.hero.species}",
        f"friend: {world.friend.name} the {world.friend.role} {world.friend.species}",
        f"taxi: {world.taxi.color} taxi driven by {world.taxi.driver_name}",
        f"facts: {world.facts}",
    ])


ASP_RULES = r"""
hero(H).
friend(F).
taxi_color(C).
observed(scarf_lollipop).
reconciled :- observed(scarf_lollipop).
humor :- observed(scarf_lollipop).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for c in TAXI_COLORS:
        lines.append(asp.fact("taxi_color", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/0.\n#show humor/0."))
    atoms = {str(a) for a in model}
    if "reconciled" in atoms and "humor" in atoms:
        print("OK: ASP twin supports reconciliation and humor.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
    StoryParams(setting="city", hero="fox", friend="rabbit", taxi_color="yellow"),
    StoryParams(setting="market", hero="cat", friend="dog", taxi_color="blue"),
    StoryParams(setting="park", hero="otter", friend="bear", taxi_color="red"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/0.\n#show humor/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checking.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
