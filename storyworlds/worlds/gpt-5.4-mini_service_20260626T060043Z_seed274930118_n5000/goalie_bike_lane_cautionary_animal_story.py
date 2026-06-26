#!/usr/bin/env python3
"""
Story world: a cautionary animal tale set in a bike lane.

A small creature wants to dart into the bike lane to chase a rolling ball.
A watchful goalie animal notices the danger, blocks the lane, and helps the
creature choose a safer place to play instead. The world model tracks whether
the bike lane is clear, who is in danger, and how the goalie's warning turns a
near-miss into a safe ending.
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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "fox", "mouse", "rabbit", "bird", "goat", "dog", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bike lane"
    loud: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    role: str = "toy"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.lane_open: bool = True
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.lane_open = self.lane_open
        clone.facts = dict(self.facts)
        return clone


SETTING = Setting(place="the bike lane", loud=True, affords={"dash", "play", "roll"})

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash into the bike lane",
        gerund="dashing into the bike lane",
        rush="run into the bike lane",
        danger="a bicycle could come too fast",
        keyword="bike lane",
        tags={"bike", "lane", "danger"},
    ),
    "play": Activity(
        id="play",
        verb="play beside the bike lane",
        gerund="playing beside the bike lane",
        rush="run beside the bike lane",
        danger="a bicycle could pass close by",
        keyword="bike lane",
        tags={"bike", "lane"},
    ),
    "roll": Activity(
        id="roll",
        verb="roll a ball in the bike lane",
        gerund="rolling a ball in the bike lane",
        rush="chase the ball into the lane",
        danger="the ball could roll straight under a wheel",
        keyword="ball",
        tags={"bike", "lane", "ball", "danger"},
    ),
}

PRIZES = {
    "ball": Prize(label="ball", phrase="a bright red ball", type="ball", role="toy"),
    "hat": Prize(label="hat", phrase="a tiny blue hat", type="hat", role="hat"),
}

GEAR = [
    Gear(id="cone", label="a bright cone", prep="set out a bright cone", tail="set the cone by the edge"),
    Gear(id="rope", label="a short rope", prep="stretch a short rope across the lane", tail="tied the rope where bikes should not go"),
]


@dataclass
class StoryParams:
    activity: str
    prize: str
    hero_name: str
    goalie_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary animal story in a bike lane.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--goalie-name")
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


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return activity.id == "roll" and prize.label == "ball"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not is_reasonable(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No reasonable cautionary story fits that activity and prize.")
    combos = [(a, p) for a in ACTIVITIES for p in PRIZES if is_reasonable(ACTIVITIES[a], PRIZES[p])]
    if args.activity:
        combos = [c for c in combos if c[0] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    activity, prize = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(["Milo", "Tia", "Pip", "Nori"])
    goalie_name = args.goalie_name or rng.choice(["Gus", "Wren", "Mira"])
    return StoryParams(activity=activity, prize=prize, hero_name=hero_name, goalie_name=goalie_name)


def predict_mistake(world: World, hero: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] = 1
    sim.get(hero.id).meters["speed"] = 1
    return activity.id == "roll"


def do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["speed"] = hero.meters.get("speed", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    if activity.id == "roll":
        hero.meters["risk"] = hero.meters.get("risk", 0) + 1
    if predict_mistake(world, hero, activity):
        world.lane_open = False


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero_name, kind="animal", type="rabbit", label=params.hero_name))
    goalie = world.add(Entity(id=params.goalie_name, kind="animal", type="fox", label=params.goalie_name, role="goalie"))
    prize = world.add(Entity(id="ball", type="ball", label="ball", phrase="a bright red ball", owner=hero.id))

    act = ACTIVITIES[params.activity]
    world.facts.update(hero=hero, goalie=goalie, prize=prize, activity=act)

    world.say(f"{hero.id} was a little rabbit who loved the {world.setting.place}.")
    world.say(f"{hero.id} loved to {act.gerund} and laugh when the day felt fast.")
    world.say(f"One day, {hero.id} chased {prize.phrase} near the {world.setting.place}.")

    world.para()
    world.say(f"But the {world.setting.place} was no safe place for a sudden game.")
    world.say(f"{act.danger.capitalize()}.")
    world.say(f"{goalie.id}, the goalie fox, saw the trouble and hurried over.")

    if predict_mistake(world, hero, act):
        world.say(f'"Stop," said {goalie.id}. "Do not {act.verb}."')
        world.say(f"{hero.id} slowed down and listened.")
        gear = GEAR[0]
        world.say(f"{goalie.id} helped by {gear.prep}.")
        world.say(f"Then {hero.id} played just beside the lane instead, with the ball kept safely near the edge.")
        world.para()
        world.say(f"In the end, {hero.id} smiled, {goalie.id} stood watch, and the bike lane stayed clear.")
    else:
        world.say(f"{hero.id} stayed back, and {goalie.id} nodded with relief.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short cautionary animal story set in a bike lane about a goalie who keeps a child safe.',
        f"Tell a story where {f['hero'].id} the rabbit wants to {f['activity'].verb} but {f['goalie'].id} the goalie fox warns about danger.",
        "Write a gentle animal story that ends with the bike lane staying clear and everyone choosing a safer place to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, goalie, prize, act = f["hero"], f["goalie"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} near the bike lane?",
            answer=f"{hero.id}, the little rabbit, wanted to {act.verb} near the bike lane.",
        ),
        QAItem(
            question=f"Who acted like the goalie and warned about danger?",
            answer=f"{goalie.id}, the goalie fox, warned that the bike lane was not a safe place for that game.",
        ),
        QAItem(
            question=f"What was the risky thing {hero.id} was chasing?",
            answer=f"{hero.id} was chasing {prize.phrase}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The rabbit listened, chose a safer place to play, and the bike lane stayed clear.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bike lane for?",
            answer="A bike lane is a part of the road or path marked for bicycles, so riders have a safer place to go.",
        ),
        QAItem(
            question="What does a goalie do?",
            answer="A goalie watches carefully, blocks danger, and tries to stop trouble from getting through.",
        ),
        QAItem(
            question="Why is it not safe to play in a bike lane?",
            answer="It is not safe because bicycles can move fast, and a child or toy could get hit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"lane_open={world.lane_open}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable_story(hero, goalie) :- hero_animal(hero), goalie_animal(goalie), bike_lane(place).
dangerous(activity) :- roll_ball(activity).
cautionary(hero, goalie, activity) :- dangerous(activity), hero_animal(hero), goalie_animal(goalie).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("bike_lane", "place"))
    lines.append(asp.fact("hero_animal", "hero"))
    lines.append(asp.fact("goalie_animal", "goalie"))
    lines.append(asp.fact("roll_ball", "roll_ball"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show cautionary/3."))
    atoms = set(asp.atoms(model, "cautionary"))
    expected = {("hero", "goalie", "roll_ball")}
    if atoms == expected:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


CURATED = [
    StoryParams(activity="roll", prize="ball", hero_name="Milo", goalie_name="Gus"),
    StoryParams(activity="roll", prize="ball", hero_name="Tia", goalie_name="Mira"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show cautionary/3."))
        return
    if args.asp:
        print("1 compatible cautionary story:\n")
        print("  bike lane  roll     ball")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {idx + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.hero_name} in the bike lane")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
