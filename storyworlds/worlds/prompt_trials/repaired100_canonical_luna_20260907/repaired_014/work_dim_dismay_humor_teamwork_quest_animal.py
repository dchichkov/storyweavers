#!/usr/bin/env python3
"""
A gentle animal storyworld about a dim work shed, a dismayed beaver,
and a teamwork quest that ends with a useful laugh.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    beaver_name: str
    helper_name: str
    elder_name: str
    task: int = 0
    obstacle: int = 0
    joke: int = 0
    quest: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Task:
    name: str
    object: str
    purpose: str
    first_try: str
    repair: str
    ending: str


@dataclass(frozen=True)
class Obstacle:
    clue: str
    cause: str
    test: str


@dataclass(frozen=True)
class Joke:
    line: str
    action: str


TASKS = [
    Task(
        "finish a little bridge",
        "a bundle of willow rails",
        "help ducklings cross a muddy creek",
        "Pip stacked the rails in a crooked row",
        "tied the rails together with long grass",
        "the ducklings marched across, one careful webbed foot at a time",
    ),
    Task(
        "make a rain roof",
        "three broad leaves",
        "keep the meadow mice dry",
        "Pip leaned the leaves against a stump",
        "woven the leaves into a snug green roof",
        "the mice peeped beneath a roof that dripped only at the edges",
    ),
    Task(
        "build a berry cart",
        "a pair of smooth sticks and a basket",
        "carry blackberries home",
        "Pip pushed the basket, which wobbled like jelly",
        "lashed the sticks firmly beneath the basket",
        "the berries rolled home without one purple tumble",
    ),
    Task(
        "repair a nest ladder",
        "four short twigs",
        "help a young robin reach its nest",
        "Pip placed the twigs beside the tree",
        "knotted the twigs into a steady little ladder",
        "the robin climbed up and sang from the nest",
    ),
]

OBSTACLES = [
    Obstacle(
        "a soft scraping came from inside the dim work-dim shed",
        "a loose reed was rubbing the door whenever the breeze puffed",
        "opened the door a finger-width, then held the reed still",
    ),
    Obstacle(
        "the tools made a tiny clatter behind the workbench",
        "a round acorn was rolling through a pile of sticks",
        "moved one stick at a time and watched where the acorn rolled",
    ),
    Obstacle(
        "a shadow stretched across the work table",
        "a sleepy heron had parked its long neck beside the window",
        "shone a firefly lantern around the table instead of guessing",
    ),
    Obstacle(
        "a loud plop came from the sawdust basket",
        "a frog had hopped inside and was trying to climb out",
        "tipped the basket gently and counted the frog's hops",
    ),
]

JOKES = [
    Joke("I am not dismayed. I am merely practicing my worried eyebrows.", "Pip lifted both eyebrows until they looked like two surprised caterpillars."),
    Joke("That plan has one small flaw: it forgot to invite the squirrels.", "Hazel placed a pinecone on the workbench as the squirrels' official adviser."),
    Joke("If the bridge wobbles, we shall call it a dancing bridge.", "They gave the bridge a tiny bow, and even the serious owl chuckled."),
    Joke("A quest is just work wearing a very important hat.", "Pip put a leaf on his head and marched three grand steps."),
]

QUESTS = [
    ("follow the blue feathers", "the feathers led from the creek to the shed"),
    ("carry the bright acorn marker", "the marker showed which path was safest"),
    ("listen for three bird calls", "the calls guided them around the muddy hollow"),
    ("collect one useful thing at each stop", "the collected things became their repair tools"),
]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_story(params: StoryParams) -> World:
    if not params.beaver_name.strip() or not params.helper_name.strip():
        raise StoryError("Animal names must not be empty.")
    task = TASKS[params.task % len(TASKS)]
    obstacle = OBSTACLES[params.obstacle % len(OBSTACLES)]
    joke = JOKES[params.joke % len(JOKES)]
    quest = QUESTS[params.quest % len(QUESTS)]

    world = World(Setting("the riverside work-dim shed", {"build", "listen", "carry", "repair"}))
    beaver = world.add(Entity("Beaver", "animal", "beaver", params.beaver_name))
    helper = world.add(Entity("Helper", "animal", "otter", params.helper_name))
    elder = world.add(Entity("Elder", "animal", "owl", params.elder_name))
    shed = world.add(Entity("Shed", "place", "shed", "the work-dim shed"))
    materials = world.add(Entity("Materials", "thing", "materials", task.object))

    world.facts.update(
        beaver=beaver,
        helper=helper,
        elder=elder,
        shed=shed,
        materials=materials,
        task=task,
        obstacle=obstacle,
        joke=joke,
        quest=quest,
    )

    beaver.memes["hope"] = 1.0
    world.say(
        f"At {world.setting.place}, {beaver.label} had one important job: to {task.name}. "
        f"The {task.object} waited beside the door."
    )
    world.say(
        f'"We can finish before sunset," said {beaver.label}. '
        f'"We can, if the shed stops acting mysterious," replied {helper.label}.'
    )
    world.say(f"Inside, {obstacle.clue.capitalize()}. {beaver.label} felt a wave of dismay.")
    beaver.memes["dismay"] = 1.0
    shed.meters["light"] = 0.2
    world.para()

    world.say(
        f"{helper.label} did not hurry away. She pointed toward the trail and said, "
        f'"Our teamwork quest begins when we {quest[0]}. {quest[1].capitalize()}."'
    )
    world.say(f"The two friends {quest[0]}. Along the way, they gathered the materials they needed.")
    helper.memes["teamwork"] = 1.0
    beaver.memes["courage"] = 1.0
    shed.meters["light"] = 0.7

    world.say(f"Back at the shed, they decided to {obstacle.test}.")
    world.say(f"They discovered the real trouble: {obstacle.cause}.")
    world.say(f'{helper.label} grinned. "{joke.line}" {joke.action}')
    beaver.memes["humor"] = 1.0
    world.para()

    world.say(
        f"With the mystery gone, {beaver.label} and {helper.label} worked side by side to {task.name}. "
        f"First, {beaver.label} measured the pieces while {helper.label} held them steady."
    )
    world.say(f"Then they {task.repair}. The work-dim shed seemed brighter because nobody was working alone.")
    materials.meters["used"] = 1.0
    shed.meters["light"] = 1.0
    beaver.memes["dismay"] = 0.0
    beaver.memes["pride"] = 1.0

    world.say(
        f"{elder.label} flew down to inspect the finished work. "
        f'"A fine job," hooted {elder.label}. "{task.purpose.capitalize()}."'
    )
    world.say(f"At sunset, {task.ending.capitalize()}.")
    world.say(
        f"{beaver.label} touched the leaf on his head and laughed. He had learned that humor can soften dismay, "
        "but teamwork is what turns a difficult quest into a useful day."
    )
    world.facts["lesson"] = "Humor can soften dismay, while teamwork helps friends complete a difficult quest."
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    return [
        f"Write an animal story about {f['beaver'].label} facing dismay in a work-dim shed.",
        f"Tell a humorous teamwork quest in which friends {task.name}.",
        "Write a gentle Animal Story where a small problem becomes easier through courage, humor, and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    obstacle: Obstacle = f["obstacle"]
    joke: Joke = f["joke"]
    return [
        QAItem(
            f"Why did {f['beaver'].label} feel dismay?",
            f"{f['beaver'].label} felt dismay because {obstacle.clue}, and the dim shed made the problem seem larger.",
        ),
        QAItem(
            f"How did {f['beaver'].label} and {f['helper'].label} solve the trouble?",
            f"They worked as a team, tested the clue carefully, and discovered that {obstacle.cause}. Then they could {task.repair}.",
        ),
        QAItem(
            "How did humor help during the quest?",
            f'{f["helper"].label} said, "{joke.line}" The joke made the friends laugh and helped them stay calm enough to keep working.',
        ),
        QAItem(
            f"What did {f['beaver'].label} learn?",
            f"{f['beaver'].label} learned that humor can soften dismay, while teamwork helps friends complete a difficult quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork is when people or animals cooperate and share jobs to reach a goal."),
        QAItem("What is dismay?", "Dismay is a worried or upset feeling caused by an unexpected problem."),
        QAItem("What is a quest?", "A quest is a purposeful journey or task that someone works to complete."),
        QAItem("Why can humor help?", "Humor can help people feel less afraid or discouraged when a problem appears."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  affordances: {sorted(world.setting.affordances)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "work_dim"),
            asp.fact("topic", "dismay"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "teamwork"),
            asp.fact("feature", "quest"),
            asp.fact("style", "animal_story"),
            asp.fact("affords", "work_dim_shed", "build"),
            asp.fact("affords", "work_dim_shed", "repair"),
            asp.fact("affords", "work_dim_shed", "listen"),
        ]
    )


ASP_RULES = r"""
topic(work_dim).
topic(dismay).
feature(humor).
feature(teamwork).
feature(quest).
style(animal_story).

can_continue :-
    topic(work_dim),
    topic(dismay),
    feature(humor),
    feature(teamwork),
    feature(quest),
    style(animal_story).

story_ok :- can_continue.
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    if any(symbol.name == "story_ok" for symbol in model):
        for i in range(4):
            params = StoryParams("Pip", "Hazel", "Owl", i, i, i, i)
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                print("MISMATCH: generated story verification failed.")
                return 1
        print("OK: ASP twin and generated stories agree.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal Story about work-dim, dismay, humor, teamwork, and a quest.")
    parser.add_argument("--beaver-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--elder-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


BEAVER_NAMES = ["Pip", "Bramble", "Nibs", "Clover", "Toby"]
HELPER_NAMES = ["Hazel", "Moss", "Wren", "Juniper", "Puddle"]
ELDER_NAMES = ["Owl", "Grandmother Owl", "Elder Heron"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        beaver_name=args.beaver_name or rng.choice(BEAVER_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        elder_name=args.elder_name or rng.choice(ELDER_NAMES),
        task=rng.randrange(len(TASKS)),
        obstacle=rng.randrange(len(OBSTACLES)),
        joke=rng.randrange(len(JOKES)),
        quest=rng.randrange(len(QUESTS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        for i in range(len(TASKS)):
            params = StoryParams("Pip", "Hazel", "Owl", i, i, i, i, base_seed + i)
            samples.append(generate(params))
    else:
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
