#!/usr/bin/env python3
"""
storyworlds/worlds/burglary_flashback_teamwork_tall_tale.py
===========================================================

A tiny tall-tale storyworld about a burglary scare, a flashback to an earlier
teamwork promise, and a cooperative ending where the town outsmarts the trouble
without turning mean.

The world is built from one seed tale:
- a small town wakes to a burglary at the lantern shop
- the mayor remembers, in a flashback, how the neighbors once worked together
- the same teamwork returns to gather clues, protect the shop, and recover the
  missing goods
- the ending proves the town is safer, brighter, and more united than before

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared result containers eagerly
- imports ASP helpers lazily
- provides StoryParams, registries, parser, resolver, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "mayor"}
        male = {"boy", "father", "man", "uncle", "marshal"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Plan:
    id: str
    clue: str
    method: str
    flashback: str
    teamwork: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    place: str
    plan: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "lantern_shop": Setting(place="the lantern shop", indoors=True),
    "grain_store": Setting(place="the grain store", indoors=True),
    "train_depot": Setting(place="the train depot", indoors=True),
}

PLANS = {
    "lantern_tracks": Plan(
        id="lantern_tracks",
        clue="fresh boot tracks in flour",
        method="follow the flour tracks",
        flashback="the mayor remembered the flood year, when every neighbor shared buckets and ropes",
        teamwork="the whole town split into pairs, one to watch the door and one to follow the clues",
        ending="the lanterns were found tucked safely in the bell cart",
        tags={"burglary", "flashback", "teamwork"},
    ),
    "window_whistle": Plan(
        id="window_whistle",
        clue="a whistle stuck in the window latch",
        method="listen for the whistle and the scraping cart wheel",
        flashback="the sheriff remembered the storm picnic, when everyone had worked together to save the pies",
        teamwork="the townsfolk formed a chain from the porch to the alley",
        ending="the missing satchels were returned before sunrise",
        tags={"burglary", "flashback", "teamwork"},
    ),
    "muddy_milk": Plan(
        id="muddy_milk",
        clue="muddy milk caps near the side door",
        method="trace the muddy caps to the creek road",
        flashback="the baker remembered the bridge repair day, when small hands and big hands had pulled the same rope",
        teamwork="the neighbors walked in a long line, lantern to lantern, like a bright snake",
        ending="the stolen jars were back on the shelf by breakfast",
        tags={"burglary", "flashback", "teamwork"},
    ),
}

HEROES = ["Mayor Maple", "Sheriff June", "Baker Tom", "Aunt Cora"]
SIDEKICKS = ["Deputy Pip", "Millie the Mouse", "Old Ben", "Captain Fern"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for tag in sorted(plan.tags):
            lines.append(asp.fact("tag", pid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, P) :- setting(S), plan(P), tag(P, burglary), tag(P, flashback), tag(P, teamwork).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set((sid, pid) for sid in SETTINGS for pid in PLANS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python registry:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale burglary storyworld with flashback and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    combos = [(s, p) for s in SETTINGS for p in PLANS]
    if args.place:
        combos = [(s, p) for s, p in combos if s == args.place]
    if args.plan:
        combos = [(s, p) for s, p in combos if p == args.plan]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, plan = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, plan=plan, hero=hero, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    plan = PLANS[params.plan]
    hero = world.add(Entity(id=params.hero, kind="character", type="mayor" if "Mayor" in params.hero else "woman" if "Aunt" in params.hero else "man", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="mouse" if "Mouse" in params.sidekick else "boy", label=params.sidekick))
    loot = world.add(Entity(id="loot", kind="thing", type="lanterns", label="lanterns", phrase="a bundle of shining lanterns", plural=True, owner=hero.id))

    hero.memes["worry"] = 1.0
    hero.memes["resolve"] = 1.0

    world.say(f"Down at {world.setting.place}, the morning began with a burglary scare so big it might have made the coffee cup jump off the shelf.")
    world.say(f"{params.hero} found the clue: {plan.clue}.")
    world.say(f"That was enough to make {params.hero} stop and think back for a moment.")

    world.para()
    world.say(f"In a flashback, {plan.flashback}.")
    world.say(f"So {params.hero} knew the town had done hard things together before, and this trouble could be handled the same way.")

    world.para()
    world.say(f"{plan.teamwork}.")
    world.say(f"{params.hero} used {plan.method}, and {params.sidekick} helped by keeping every door count and every hallway honest.")
    world.say(f"At last, {plan.ending}.")
    world.say(f"By sundown, the shop was brighter than a basket of fireflies, and nobody stood alone.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        loot=loot,
        plan=plan,
        setting=world.setting,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    plan = f["plan"]
    return [
        f"Write a tall tale for young children about a burglary scare that is solved with {plan.method}.",
        f"Tell a story that includes a flashback to an earlier time when people worked together, then returns to the present.",
        f"Write a gentle small-town adventure where teamwork helps recover the missing lanterns.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    plan = f["plan"]
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        QAItem(
            question=f"What kind of trouble started the story at {world.setting.place}?",
            answer=f"It started with a burglary scare, when something important went missing and everyone had to pay attention.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered that {plan.flashback}. That memory helped {hero.id} stay calm and choose teamwork.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.id} solve the problem?",
            answer=f"They worked together by using {plan.method} and keeping watch as a team until the missing goods were found.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The ending showed that {plan.ending}, and the town felt safer and brighter after everyone helped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and each person does a small part so the whole job gets done.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when a story pauses to show something that happened earlier, before the present part of the story.",
        ),
        QAItem(
            question="What is a burglary?",
            answer="A burglary is when someone sneaks in and takes things that are not theirs.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lantern_shop", plan="lantern_tracks", hero="Mayor Maple", sidekick="Deputy Pip"),
    StoryParams(place="grain_store", plan="muddy_milk", hero="Sheriff June", sidekick="Millie the Mouse"),
    StoryParams(place="train_depot", plan="window_whistle", hero="Baker Tom", sidekick="Old Ben"),
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, plan in stories:
            print(f"  {place:12} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
