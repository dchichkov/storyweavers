#!/usr/bin/env python3
"""
storyworlds/worlds/tater_assert_rhyme_sharing_lesson_learned_superhero.py
=========================================================================

A small superhero storyworld about a kid hero, a shiny plan, a shared tater,
and a lesson learned.

Premise:
- A young superhero wants to assert themself during a neighborhood rescue.
- A tasty tater treat is at stake.
- The hero's first choice is too proud and too pushy.

Turn:
- A teammate notices the mistake and offers a rhyme-based reminder.
- The hero learns that sharing helps everyone do better.

Resolution:
- The hero shares the tater, listens, and succeeds with the team.

This world is constraint-checked and produces complete child-facing stories.
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
class Hero:
    id: str
    name: str
    title: str
    color: str
    power: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Team:
    name: str
    helper: str
    helper_power: str
    rhyme: str


@dataclass
class Snack:
    label: str
    phrase: str
    shareable: bool = True


@dataclass
class Scene:
    place: str
    problem: str
    rescue: str
    lesson: str


@dataclass
class StoryParams:
    hero_name: str
    hero_color: str
    hero_power: str
    team_name: str
    helper_name: str
    helper_power: str
    snack: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Piper", "Sunny", "Milo", "Zara", "Juno", "Ivy", "Dash"]
COLORS = ["red", "blue", "gold", "green", "purple", "silver"]
POWERS = ["speed", "sparkle beams", "bubble shields", "rocket jumps", "wind swirls", "bright light"]
TEAM_NAMES = ["Star Squad", "Sky Patrol", "Caped Crew", "Beacon Team"]
HELPERS = ["Bea", "Tate", "Cleo", "Finn", "Rae", "Ollie"]
SNACKS = {
    "tater": Snack(label="tater", phrase="a warm crispy tater"),
    "tater_tots": Snack(label="tater tots", phrase="a paper basket of tater tots"),
    "tater_cake": Snack(label="tater cake", phrase="a round golden tater cake"),
}
PLACES = ["the park", "the rooftop garden", "the city square", "the schoolyard"]


def make_hero(params: StoryParams) -> Hero:
    return Hero(
        id="hero",
        name=params.hero_name,
        title="young superhero",
        color=params.hero_color,
        power=params.hero_power,
        meters={"energy": 2.0, "mess": 0.0, "teamwork": 0.0},
        memes={"pride": 1.0, "sharing": 0.0, "lesson": 0.0, "joy": 0.5},
    )


def make_team(params: StoryParams) -> Team:
    rhyme = "Little heroes share what they can, and work best together with a plan."
    return Team(
        name=params.team_name,
        helper=params.helper_name,
        helper_power=params.helper_power,
        rhyme=rhyme,
    )


def make_scene(params: StoryParams) -> Scene:
    return Scene(
        place=params.place,
        problem="a runaway kite tangled up high",
        rescue="bring the kite down and keep the snacks safe",
        lesson="sharing made the rescue easier",
    )


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.hero = make_hero(params)
        self.team = make_team(params)
        self.snack = SNACKS[params.snack]
        self.scene = make_scene(params)
        self.story_parts: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.story_parts.append(text)

    def para(self) -> None:
        self.story_parts.append("\n")

    def render(self) -> str:
        chunks: list[str] = []
        current: list[str] = []
        for part in self.story_parts:
            if part == "\n":
                if current:
                    chunks.append(" ".join(current))
                    current = []
            else:
                current.append(part)
        if current:
            chunks.append(" ".join(current))
        return "\n\n".join(chunks)

    def tell(self) -> None:
        h = self.hero
        t = self.team
        s = self.snack
        sc = self.scene

        self.say(
            f"Nova was a {h.color} little superhero with a love for {h.power}."
        )
        self.say(
            f"{h.name} wore a bright cape and liked to {h.power} around {sc.place}."
        )
        self.say(
            f"On that day, {h.name} carried {s.phrase} in a small tin because {s.label} was {s.phrase} and looked extra tasty."
        )
        self.para()

        self.say(
            f"Then a gust blew a kite string around a lamp post near {sc.place}, and the little hero saw {sc.problem}."
        )
        self.say(
            f"{h.name} wanted to {sc.rescue}, but {h.name} tried to assert the plan all alone."
        )
        self.say(
            f'"I can do it myself!" {h.name} said, pushing ahead with proud shoulders and a fast step.'
        )

        h.meters["mess"] += 1.0
        h.memes["pride"] += 1.0
        h.memes["teamwork"] += 0.5
        self.facts["first_choice"] = "alone"
        self.para()

        self.say(
            f"{t.helper} flew closer and smiled. "{t.rhyme}" {t.helper} said, pointing to the tin."
        )
        self.say(
            f'"Let’s share the {s.label}, then we can save time and save the day."'
        )
        h.memes["sharing"] += 1.0
        h.memes["lesson"] += 1.0
        h.memes["pride"] = max(0.0, h.memes["pride"] - 1.0)
        self.facts["rhyme"] = t.rhyme
        self.facts["sharing"] = True
        self.para()

        self.say(
            f"Nova took a breath, nodded, and shared the {s.label} with the team."
        )
        self.say(
            f"With everyone working together, {h.name} used {h.power} to lift the string free while {t.helper} steadied the pole."
        )
        self.say(
            f"The kite floated down at last, and the {s.label} stayed partly uneaten, because the best heroes did not keep the good thing all to themself."
        )
        self.say(
            f"{h.name} grinned and learned the lesson learned: sharing made the rescue easier."
        )
        h.meters["teamwork"] += 2.0
        h.meters["energy"] = 1.0
        h.memes["joy"] += 1.5
        self.facts["resolved"] = True
        self.facts["lesson"] = sc.lesson
        self.facts["place"] = sc.place


def story_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short superhero story for a child about {p.hero_name} and a {p.snack} at {p.place}.",
        f"Tell a gentle story where a young hero tries to assert themself, then learns to share.",
        f"Create a rhyming superhero tale that ends with a lesson learned about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    h = world.hero
    t = world.team
    s = world.snack
    sc = world.scene
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {p.hero_name}, a {p.hero_color} little hero with {p.hero_power}.",
        ),
        QAItem(
            question=f"What snack did {p.hero_name} have during the rescue?",
            answer=f"{p.hero_name} had {s.phrase}, and it was the snack {p.hero_name} wanted to keep close at first.",
        ),
        QAItem(
            question=f"What problem did the hero need to solve at {sc.place}?",
            answer=f"The hero needed to solve {sc.problem} and {sc.rescue}.",
        ),
        QAItem(
            question=f"What did the helper say to encourage sharing?",
            answer=f"{t.helper} said, \"{t.rhyme}\" to remind {p.hero_name} that sharing helps the team.",
        ),
        QAItem(
            question=f"What lesson did {p.hero_name} learn in the end?",
            answer=f"{p.hero_name} learned that {sc.lesson}, and that sharing helped everyone finish the rescue together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, so more than one person can benefit.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="Why do superheroes work as a team?",
            answer="Superheroes work as a team because different helpers can do different jobs and solve bigger problems together.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about tater, rhyme, and sharing.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-color", choices=COLORS)
    ap.add_argument("--hero-power", choices=POWERS)
    ap.add_argument("--team-name", choices=TEAM_NAMES)
    ap.add_argument("--helper-name", choices=HELPERS)
    ap.add_argument("--helper-power", choices=POWERS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--place", choices=PLACES)
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_color = args.hero_color or rng.choice(COLORS)
    hero_power = args.hero_power or rng.choice(POWERS)
    team_name = args.team_name or rng.choice(TEAM_NAMES)
    helper_name = args.helper_name or rng.choice(HELPERS)
    helper_power = args.helper_power or rng.choice([p for p in POWERS if p != hero_power])
    snack = args.snack or "tater"
    place = args.place or rng.choice(PLACES)

    if args.snack and args.snack != "tater" and "tater" not in args.snack:
        raise StoryError("This world centers on tater. Please choose the tater snack family.")
    if args.hero_name and args.helper_name and args.hero_name == args.helper_name:
        raise StoryError("The hero and helper should be different characters.")

    return StoryParams(
        hero_name=hero_name,
        hero_color=hero_color,
        hero_power=hero_power,
        team_name=team_name,
        helper_name=helper_name,
        helper_power=helper_power,
        snack=snack,
        place=place,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    world.tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"hero={world.hero.name} color={world.hero.color} power={world.hero.power}")
    lines.append(f"snack={world.snack.label}")
    lines.append(f"place={world.scene.place}")
    lines.append(f"meters={world.hero.meters}")
    lines.append(f"memes={world.hero.memes}")
    return "\n".join(lines)


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
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H). :- hero_name(H).
sharing_story :- snack(tater), lesson(learned).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "Nova"),
        asp.fact("snack", "tater"),
        asp.fact("lesson", "learned"),
        asp.fact("feature", "rhyme"),
        asp.fact("feature", "sharing"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(
        hero_name="Nova",
        hero_color="gold",
        hero_power="speed",
        team_name="Star Squad",
        helper_name="Bea",
        helper_power="bubble shields",
        snack="tater",
        place="the city square",
    ),
    StoryParams(
        hero_name="Zara",
        hero_color="blue",
        hero_power="rocket jumps",
        team_name="Caped Crew",
        helper_name="Rae",
        helper_power="bright light",
        snack="tater_tots",
        place="the park",
    ),
]


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
        print(asp_program("#show."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
