#!/usr/bin/env python3
"""
A small comedy storyworld about allegiance, friendship, and a mom who means
well but sometimes makes life feel like a tiny marching band in the kitchen.
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Friend:
    name: str
    type: str = "child"
    trait: str = "funny"


@dataclass
class Scenario:
    place: str
    event: str
    prop: str
    mom_reason: str
    friend_problem: str
    comic_turn: str


class World:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
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


@dataclass
class StoryParams:
    scenario: str
    name: str
    gender: str
    mom_name: str
    friend_name: str
    seed: Optional[int] = None


SCENARIOS = {
    "toy": Scenario(
        place="the kitchen table",
        event="finish the papier-mâché dinosaur",
        prop="glue stick",
        mom_reason="she says glue belongs on paper, not on eyebrows",
        friend_problem="the friend needs help finding a missing rocket sticker",
        comic_turn="the child accidentally salutes a spoon instead of making a decision",
    ),
    "team": Scenario(
        place="the school hallway",
        event="choose which team to cheer for",
        prop="foam finger",
        mom_reason="she does not want the child yelling so hard they sneeze confetti",
        friend_problem="the friend wants a partner for the three-legged potato sack race",
        comic_turn="the child tries to cheer for both sides and nearly spins in a circle",
    ),
    "cookies": Scenario(
        place="the porch",
        event="share the last two cookies fairly",
        prop="cookie tin",
        mom_reason="she wants everyone to use polite hands, not grabby pirate hands",
        friend_problem="the friend has a jam stain and needs one napkin and a pep talk",
        comic_turn="the child counts cookies twice and somehow gets a different answer each time",
    ),
}

NAMES_GIRL = ["Mia", "Nora", "Lena", "Ruby", "Ivy", "Zoe", "Ella", "Ava"]
NAMES_BOY = ["Leo", "Noah", "Finn", "Eli", "Owen", "Max", "Theo", "Jack"]
MOM_NAMES = ["Mom", "Mama", "Mum", "Mother"]
FRIENDS = ["Toby", "June", "Pip", "Milo", "Sage", "Maya", "Nina", "Otis"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about mom, allegiance, and friendship.")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mom-name", choices=MOM_NAMES)
    ap.add_argument("--friend-name")
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
    scenario = args.scenario or rng.choice(sorted(SCENARIOS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    mom_name = args.mom_name or rng.choice(MOM_NAMES)
    friend_name = args.friend_name or rng.choice(FRIENDS)
    return StoryParams(
        scenario=scenario,
        name=name,
        gender=gender,
        mom_name=mom_name,
        friend_name=friend_name,
    )


def _do_conflict(world: World, hero: Entity, mom: Entity, friend: Entity, s: Scenario) -> None:
    hero.memes["torn"] = hero.memes.get("torn", 0) + 1
    hero.memes["allegiance"] = hero.memes.get("allegiance", 0) + 1
    world.say(
        f"At {s.place}, {hero.id} wanted to {s.event}, but {mom.label} reminded {hero.pronoun('object')} that "
        f"{s.mom_reason}."
    )
    world.say(
        f"Then {friend.id} showed up with {s.friend_problem}, and {hero.id} suddenly felt pulled in two directions."
    )
    world.say(
        f"{s.comic_turn.capitalize()}, and {hero.id} made a face so serious it looked like a tiny mayor had been elected in {hero.pronoun('possessive')} cheeks."
    )


def _do_turn(world: World, hero: Entity, mom: Entity, friend: Entity, s: Scenario) -> None:
    hero.memes["honesty"] = hero.memes.get("honesty", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["torn"] = 0
    world.say(
        f"{hero.id} took a breath and said, \"I want to help my friend, and I also want to listen to my {mom.label}.\""
    )
    world.say(
        f"{mom.label.capitalize()} blinked, then laughed because that was a very honest answer and also a very wobbly one."
    )


def _do_resolution(world: World, hero: Entity, mom: Entity, friend: Entity, s: Scenario) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["relief"] = friend.memes.get("relief", 0) + 1
    mom.memes["pride"] = mom.memes.get("pride", 0) + 1
    world.say(
        f"So {mom.label} helped, {friend.id} helped, and {hero.id} helped too. Soon the {s.prop} was safe, the mess was smaller, "
        f"and everybody was choosing the same side: the kind one."
    )
    world.say(
        f"At the end, {hero.id} was smiling beside {mom.label} and {friend.id}, which was a much better kind of allegiance than marching around and saluting a spoon."
    )


def tell_story(params: StoryParams) -> World:
    s = SCENARIOS[params.scenario]
    world = World(s)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    mom = world.add(Entity(id=params.mom_name, kind="character", type="mother", label=params.mom_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child", label=params.friend_name))

    world.say(
        f"{hero.id} was a cheerful little {hero.type} who loved {s.prop}s, jokes, and helping people."
    )
    world.say(
        f"{hero.id} also loved {mom.label} and {friend.id}, which made {hero.pronoun('possessive')} heart feel a little crowded sometimes."
    )
    world.para()
    _do_conflict(world, hero, mom, friend, s)
    world.para()
    _do_turn(world, hero, mom, friend, s)
    _do_resolution(world, hero, mom, friend, s)

    world.facts.update(
        hero=hero,
        mom=mom,
        friend=friend,
        scenario=s,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mom = f["mom"]
    friend = f["friend"]
    s = f["scenario"]
    return [
        f"Write a short comedy story for a young child about {hero.id}, {mom.label}, and {friend.id} at {s.place}.",
        f"Tell a funny story where {hero.id} must choose between listening to {mom.label} and helping {friend.id}.",
        f"Write a gentle story about allegiance and friendship that ends with everyone laughing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mom = f["mom"]
    friend = f["friend"]
    s = f["scenario"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a cheerful little {hero.type} who cared about {mom.label} and {friend.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel torn at {s.place}?",
            answer=f"{hero.id} felt torn because {mom.label} wanted caution, while {friend.id} needed help, so {hero.id} had to think about allegiance and friendship at the same time.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of choosing in a silly rush?",
            answer=f"{hero.id} told the truth, asked for help, and found a kinder plan that let everyone stay happy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id}, {mom.label}, and {friend.id} smiling together after solving the problem the kind way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is allegiance?",
            answer="Allegiance means loyalty or support for someone or something you choose to stand with.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help, play, and look out for each other.",
        ),
        QAItem(
            question="Why can honesty help in a family argument?",
            answer="Honesty helps because it lets everyone say what they need, so they can find a fair and kind solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.type:8} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- hero(X).
character(X) :- mom(X).
character(X) :- friend(X).

torn(X) :- conflict(X), not resolved(X).
resolved(X) :- honesty(X), kindness(X).
best_side(X) :- resolved(X), kindness(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("place", sid, s.place))
    lines.append(asp.fact("value", "allegiance"))
    lines.append(asp.fact("value", "friendship"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show scenario/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("toy", "Mia", "girl", "Mom", "Pip"),
            StoryParams("team", "Leo", "boy", "Mama", "June"),
            StoryParams("cookies", "Nora", "girl", "Mum", "Milo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
