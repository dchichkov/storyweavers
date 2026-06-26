#!/usr/bin/env python3
"""
Storyworld: critter_community_garden_kindness_transformation_adventure.py

A small classical simulation about a critter in a community garden, where
kindness causes a visible transformation and the adventure ends with the garden
changed for the better.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "rabbit", "squirrel", "bird", "bee", "deer"}
        male = {"mouse", "rabbit", "squirrel", "bird", "bee", "deer"}
        if self.type in female or self.type in male:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the community garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    need: str
    result: str
    location: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    location: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]
    targets: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the community garden", affords={"water", "rescue", "harvest"}),
}

TASKS = {
    "water": Task(
        id="water",
        verb="water the thirsty beds",
        gerund="watering the thirsty beds",
        rush="run to the dry rows",
        need="water",
        result="fresh and green",
        location="the tomato row",
        keyword="water",
        tags={"water", "plant", "kindness"},
    ),
    "rescue": Task(
        id="rescue",
        verb="help the trapped seedlings",
        gerund="helping the trapped seedlings",
        rush="dash to the tangled trellis",
        need="clear path",
        result="free and standing tall",
        location="the bean trellis",
        keyword="kindness",
        tags={"kindness", "help", "vine"},
    ),
    "harvest": Task(
        id="harvest",
        verb="pick the ripe berries",
        gerund="picking ripe berries",
        rush="skip to the berry patch",
        need="steady paws",
        result="ready for a picnic",
        location="the berry patch",
        keyword="adventure",
        tags={"berry", "fruit", "harvest"},
    ),
}

REWARDS = {
    "seedling": Reward(
        id="seedling",
        label="seedlings",
        phrase="a tray of tiny seedlings",
        location="the bean trellis",
        plural=True,
    ),
    "flowers": Reward(
        id="flowers",
        label="flowers",
        phrase="a row of sleepy flowers",
        location="the herb path",
        plural=True,
    ),
    "basket": Reward(
        id="basket",
        label="basket",
        phrase="a small berry basket",
        location="the berry patch",
        plural=False,
    ),
}

HELPERS = [
    Helper(
        id="watering_can",
        label="a little watering can",
        prep="carry the watering can together",
        tail="walked back and forth with the watering can",
        fixes={"water"},
        targets={"water"},
    ),
    Helper(
        id="twine",
        label="a soft roll of twine",
        prep="use the soft twine to untangle the stems",
        tail="carefully unwound the soft twine",
        fixes={"clear path"},
        targets={"rescue"},
    ),
    Helper(
        id="basket",
        label="a woven basket",
        prep="bring the woven basket along",
        tail="trotted over with the woven basket",
        fixes={"steady paws"},
        targets={"harvest"},
    ),
]

CRITTER_NAMES = ["Pip", "Milo", "Mira", "Nico", "Luna", "Bram", "Hazel", "Toby"]
CRITTER_TYPES = ["mouse", "rabbit", "squirrel", "hedgehog", "chipmunk", "frog"]
TRAITS = ["curious", "brave", "gentle", "quick", "hopeful", "cheerful"]


# ---------------------------------------------------------------------------
# World model / narrative mechanics
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    reward: str
    name: str
    critter_type: str
    trait: str
    seed: Optional[int] = None


def task_at_risk(task: Task, reward: Reward) -> bool:
    return task.location == reward.location or task.id == "water" and reward.location == "the bean trellis"


def select_helper(task: Task, reward: Reward) -> Optional[Helper]:
    for helper in HELPERS:
        if task.need in helper.fixes and task.id in helper.targets:
            return helper
    return None


def reasonableness_gate(task: Task, reward: Reward) -> bool:
    return task_at_risk(task, reward) and select_helper(task, reward) is not None


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    reward = REWARDS[params.reward]
    if not reasonableness_gate(task, reward):
        raise StoryError("No valid story: the task and reward do not form a kindness-driven transformation.")

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.critter_type,
        traits=["little", params.trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="mouse",
        label="a shy garden friend",
        traits=["small", "nervous"],
    ))
    prize = world.add(Entity(
        id="reward",
        type="thing",
        label=reward.label,
        phrase=reward.phrase,
        location=reward.location,
        plural=reward.plural,
    ))

    helper = select_helper(task, reward)

    # Act 1: introduce the critter and the garden.
    world.say(f"{params.name} was a little {params.trait} {params.critter_type} who loved adventures in {setting.place}.")
    world.say(f"{params.name} liked the smell of soil, the buzz of bees, and the way every path in the garden seemed to lead to something new.")
    world.say(f"One bright morning, {params.name} noticed {prize.phrase} near {reward.location}.")

    # Act 2: a problem appears and kindness becomes the turning point.
    world.para()
    world.say(f"At the same time, {friend.label} was stuck near the trellis and looked worried.")
    world.say(f"{params.name} wanted to {task.verb}, but first {params.name} saw that the garden needed help.")
    world.say(f"So {params.name} chose kindness and went to {task.gerund} instead of rushing ahead alone.")

    # State changes
    hero.memes["kindness"] = 1.0
    hero.memes["desire"] = 1.0
    friend.memes["relief"] = 1.0

    if task.id == "water":
        world.say(f"{params.name} carried water to {task.location}, and the dry leaves slowly turned bright again.")
        world.say(f"As the soil drank the water, the tired bed became fresh and green.")
    elif task.id == "rescue":
        world.say(f"{params.name} used the twine carefully, and the tangled stems came loose one by one.")
        world.say(f"The seedlings straightened up, and the vine arch looked proud instead of stuck.")
    else:
        world.say(f"{params.name} brought the basket and picked the ripe berries without shaking the plants.")
        world.say(f"The basket filled up, and the berry patch stayed neat and happy.")

    # Act 3: transformation and ending image.
    world.para()
    world.say(f"That kindness changed the whole moment.")
    world.say(f"{friend.label} smiled, and the garden seemed to glow a little brighter.")
    world.say(f"By the end, {params.name} had gone from a curious visitor to a true helper, and the garden was {task.result}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        reward=prize,
        task=task,
        helper=helper,
        setting=setting,
        resolved=True,
        transformed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    reward = f["reward"]
    return [
        f"Write a short adventure story for a young child about a {hero.type} named {hero.id} in a community garden.",
        f"Tell a gentle story where kindness helps {hero.id} solve a problem while trying to {task.verb}.",
        f"Write a story that includes a community garden, a small critter, and a transformation that happens because someone chose kindness.",
        f"Create a simple adventure where {hero.id} notices {reward.phrase} and helps the garden become better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    reward = f["reward"]
    helper = f["helper"]
    friend = f["friend"]

    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is about {hero.id}, a little {hero.traits[1]} {hero.type} who explores the community garden.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {task.verb}, but {hero.id} first noticed that someone in the garden needed help.",
        ),
        QAItem(
            question=f"What did {hero.id} notice near {reward.location}?",
            answer=f"{hero.id} noticed {reward.phrase} near {reward.location}.",
        ),
        QAItem(
            question=f"What choice showed kindness in the story?",
            answer=f"{hero.id} chose to help {friend.label} and fix the garden problem before rushing to the prize.",
        ),
    ]
    if helper:
        qa.append(QAItem(
            question=f"What helped the problem get better?",
            answer=f"{helper.label} helped because it matched the kind of problem in the story and made the task possible.",
        ))
    qa.append(QAItem(
        question=f"How did the garden change by the end?",
        answer=f"The garden changed from stuck or tired to {task.result}, which showed the transformation caused by kindness.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a garden shared by neighbors, where people grow flowers, vegetables, and other plants together.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, and being gentle so someone else feels safer and happier.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new state, like a tired plant becoming fresh and bright after help and care.",
        ),
        QAItem(
            question="Why do plants need water?",
            answer="Plants need water so their stems and leaves can stay healthy, grow, and not wilt.",
        ),
        QAItem(
            question="Why do people use twine in a garden?",
            answer="People use twine to support plants or untangle stems so the plants can grow neatly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_reward_match(T, R) :- task(T), reward(R), at_risk(T, R), has_helper(T, R).
valid_story(T, R) :- task_reward_match(T, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_need", tid, t.need))
        lines.append(asp.fact("task_location", tid, t.location))
    for rid, r in REWARDS.items():
        lines.append(asp.fact("reward", rid))
        lines.append(asp.fact("reward_location", rid, r.location))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper.id))
        for fix in sorted(helper.fixes):
            lines.append(asp.fact("fixes", helper.id, fix))
        for tgt in sorted(helper.targets):
            lines.append(asp.fact("targets", helper.id, tgt))
    for tid, t in TASKS.items():
        for rid, r in REWARDS.items():
            if task_at_risk(t, r):
                lines.append(asp.fact("at_risk", tid, rid))
                if select_helper(t, r) is not None:
                    lines.append(asp.fact("has_helper", tid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((t, r) for t in TASKS for r in REWARDS if reasonableness_gate(TASKS[t], REWARDS[r]))
    asp_set = asp_valid_stories()
    if py == asp_set:
        print(f"OK: ASP matches Python gate for {len(py)} stories.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("python:", py)
    print("asp   :", asp_set)
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A critter adventure in a community garden, shaped by kindness and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--name")
    ap.add_argument("--critter-type", choices=CRITTER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.reward:
        if not reasonableness_gate(TASKS[args.task], REWARDS[args.reward]):
            raise StoryError("No valid story: that task and reward do not fit the kindness/transformation adventure.")
    valid = [
        (t, r)
        for t in TASKS
        for r in REWARDS
        if (args.task is None or t == args.task)
        and (args.reward is None or r == args.reward)
    ]
    if not valid:
        raise StoryError("No valid combination matches the chosen options.")
    task, reward = rng.choice(valid)
    name = args.name or rng.choice(CRITTER_NAMES)
    critter_type = args.critter_type or rng.choice(CRITTER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="garden", task=task, reward=reward, name=name, critter_type=critter_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
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


CURATED = [
    StoryParams(place="garden", task="water", reward="seedling", name="Pip", critter_type="mouse", trait="curious"),
    StoryParams(place="garden", task="rescue", reward="seedling", name="Mira", critter_type="rabbit", trait="gentle"),
    StoryParams(place="garden", task="harvest", reward="basket", name="Nico", critter_type="squirrel", trait="brave"),
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
        print(f"{len(stories)} valid stories:")
        for t, r in stories:
            print(f"  {t} + {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
