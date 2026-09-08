#!/usr/bin/env python3
"""
Storyworld: meddlesome_piazza_quest_tall_tale

A tall tale about a meddlesome child, a lively piazza, and a quest that turns
interference into useful help.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"curiosity": 0.0, "risk": 0.0, "helpfulness": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"mischief": 0.0, "worry": 0.0, "pride": 0.0}
    )


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"importance": 0.0, "risk": 0.0, "brightness": 0.0}
    )
    owner: str = ""


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    piazza: str
    quest_object: str
    obstacle: str
    tall_detail: str
    route: str
    seed: Optional[int] = None


HERO_NAMES = ("Pia", "Luna", "Nico", "Mara", "Tavi", "Zeno")
HELPER_NAMES = ("Bello", "Sera", "Mina", "Toma", "Rafi", "Nella")
PIAZZAS = (
    "Piazza Bellavista",
    "Piazza of the Seven Fountains",
    "Piazza Sunwheel",
    "Piazza Marzipan",
    "Piazza Grande",
)
QUEST_OBJECTS = (
    "the silver festival bell",
    "the mayor's blue umbrella",
    "the moon-shaped key",
    "the golden recipe book",
    "the red ribbon of welcome",
)
OBSTACLES = (
    "a fountain that sneezed whenever anyone lied",
    "a flock of stubborn pigeons guarding the clock tower",
    "a bakery cart rolling downhill without its baker",
    "a sudden whirl of banners above the square",
    "a sleepy stone lion blocking the narrow arch",
)
TALL_DETAILS = (
    "so tall that birds used the hero's hat as a weather lookout",
    "so loudly that the paving stones hummed three streets away",
    "so quickly that three grandmothers saw the same moment yesterday",
    "so widely that the quest crossed the piazza before its shadow did",
    "so brightly that the afternoon moon came out to watch",
)
ROUTES = (
    "through the fountain arcade",
    "around the clock tower",
    "beneath the striped market awnings",
    "past the old bellmaker's steps",
    "along the sunny side of the square",
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        raise StoryError("The quest hero and helper must have different names.")
    if not params.piazza.lower().startswith("piazza"):
        raise StoryError("The setting must be a piazza.")
    if not params.quest_object or not params.obstacle:
        raise StoryError("A quest needs both a goal and an obstacle.")

    world = World(params)
    hero = Person("hero", params.hero_name, "meddlesome quester")
    helper = Person("helper", params.helper_name, "patient piazza keeper")
    goal = Thing("goal", params.quest_object, "quest treasure", owner="piazza")
    obstacle = Thing("obstacle", params.obstacle, "quest obstacle")
    banner = Thing("banner", "a long yellow festival banner", "helping tool")

    world.people[hero.id] = hero
    world.people[helper.id] = helper
    world.things[goal.id] = goal
    world.things[obstacle.id] = obstacle
    world.things[banner.id] = banner

    world.say(
        f"In {params.piazza}, where the sun polished every stone, {hero.name} was famous for being meddlesome."
    )
    world.say(
        f"If a baker stacked buns, {hero.name} rearranged them into a tower; if a musician tuned a lute, "
        f"{hero.name} plucked the loudest string. The whole piazza knew that {hero.name} could not leave a mystery alone."
    )
    world.say(
        f"One morning, the town's quest began when {params.quest_object} vanished from the square."
    )
    world.say(
        f"The missing treasure had to be found before the evening welcome feast, but {params.obstacle} stood in the way "
        f"of the only sensible route."
    )
    world.para()

    hero.meters["curiosity"] += 1
    hero.meters["risk"] += 1
    hero.memes["mischief"] += 1
    obstacle.meters["risk"] += 1
    world.say(
        f'"I will fix everything myself!" cried {hero.name}, grabbing at the nearest rope before anyone could explain the plan.'
    )
    world.say(
        f'{helper.name} caught the other end and said, "A quest is not a race to touch every interesting thing. '
        f'First tell me what you see."'
    )
    world.say(
        f'{hero.name} frowned. "I see {params.obstacle}."'
    )
    world.say(
        f'"And what does it need?" asked {helper.name}. "Not a meddlesome tug, but a careful idea."'
    )
    world.para()

    world.say(
        f"That was when {hero.name} noticed a thin trail of blue flour leading {params.route}."
    )
    world.say(
        f"The trail curved around the obstacle and ended beneath a bench, while the festival banner fluttered above it "
        f"like a waving finger."
    )
    world.say(
        f'"The treasure did not disappear by magic," said {hero.name}. "Someone carried it along the flour trail."'
    )
    world.say(
        f'"Exactly," said {helper.name}. "Now meddle with the problem, not with everybody else\'s work."'
    )
    world.say(
        f"Together they used the banner as a bright marker, stayed clear of the moving danger, and followed the clue "
        f"from {params.route}."
    )
    hero.meters["helpfulness"] += 1
    hero.meters["risk"] -= 1
    helper.meters["helpfulness"] += 1
    banner.meters["importance"] += 1
    world.para()

    world.say(
        f"Under the bench they found {params.quest_object}, tucked beside a sleepy kitten and three floury paw prints."
    )
    world.say(
        f"The kitten had dragged the treasure away from the obstacle because the noise frightened it."
    )
    world.say(
        f"{hero.name} wanted to scoop up the kitten, the treasure, the bench, and perhaps the whole piazza at once, "
        f"but stopped and asked {helper.name} what would help."
    )
    world.say(
        f'"Make a quiet path," said {helper.name}.'
    )
    world.say(
        f"{hero.name} held the banner high while the townspeople guided the obstacle away and the kitten padded safely "
        f"toward its baker."
    )
    goal.meters["importance"] += 1
    goal.meters["brightness"] += 1
    hero.memes["worry"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.para()

    world.say(
        f"The quest succeeded just before sunset. {params.quest_object} returned to its place, and the kitten received "
        f"a saucer of milk beside the fountain."
    )
    world.say(
        f"From that day on, {hero.name} was still curious, but the piazza called the child a useful meddler: someone "
        f"who asked questions, followed clues, and made room for careful helpers."
    )
    world.say(
        f'"I can meddle with a mystery," {hero.name} promised, "but I will not meddle with danger."'
    )
    world.say(
        f'{helper.name} smiled. "That is the beginning of every good quest."'
    )
    world.say(
        f"And the tall tale grew taller: {params.tall_detail}, while the recovered treasure shone above the quiet square."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        goal=goal,
        obstacle=obstacle,
        banner=banner,
        piazza=params.piazza,
        route=params.route,
        tall_detail=params.tall_detail,
        clue=f"a thin trail of blue flour leading {params.route}",
        solution="used the banner as a marker, followed the flour clue, and made a quiet path",
        result=f"{params.quest_object} returned to its place and the frightened kitten reached its baker",
        lesson="curiosity becomes helpful when it follows clues and respects danger",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Person = f["hero"]
    goal: Thing = f["goal"]
    return [
        f"Write a tall tale about {hero.name}, a meddlesome quester in {f['piazza']}, searching for {goal.label}.",
        f"Tell a child-friendly Quest story where {hero.name} notices {f['clue']} and helps without grabbing at danger.",
        f"Write a piazza adventure showing that {hero.name} learns that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    helper: Person = f["helper"]
    goal: Thing = f["goal"]
    obstacle: Thing = f["obstacle"]
    return [
        QAItem(
            question=f"Why did {hero.name} begin a quest?",
            answer=f"{hero.name} began a quest because {goal.label} had vanished from {f['piazza']} and needed to be found before the welcome feast.",
        ),
        QAItem(
            question=f"What danger did {hero.name} face?",
            answer=f"{hero.name} faced {obstacle.label}, which blocked the route and could become worse if handled with a careless tug.",
        ),
        QAItem(
            question=f"What clue changed {hero.name}'s plan?",
            answer=f"{hero.name} noticed {f['clue']}. The clue showed that the missing treasure had been carried rather than magically lost.",
        ),
        QAItem(
            question=f"How did {hero.name} help solve the quest?",
            answer=f"{hero.name} {f['solution']}. This let the townspeople move the danger while the kitten and treasure stayed safe.",
        ),
        QAItem(
            question="What lesson did the meddlesome quest teach?",
            answer=f"The quest taught that {f['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a piazza?",
            answer="A piazza is an open public square where people can meet, walk, trade, and celebrate.",
        ),
        QAItem(
            question="What does meddlesome mean?",
            answer="Meddlesome means interfering in other people's work or problems, often without being asked.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or search with a goal to accomplish.",
        ),
        QAItem(
            question="What makes this story a tall tale?",
            answer="It is a tall tale because its lively adventure uses playful exaggeration while still giving the hero a clear lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for person in world.people.values():
        lines.append(
            f"{person.id}: name={person.name} role={person.role} "
            f"meters={dict(person.meters)} memes={dict(person.memes)}"
        )
    for thing in world.things.values():
        lines.append(
            f"{thing.id}: label={thing.label} kind={thing.kind} owner={thing.owner} "
            f"meters={dict(thing.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
quest_story(S) :- story(S), missing_goal(S), meddlesome_hero(S), careful_help(S).
missing_goal(S) :- story(S), quest_goal(S).
meddlesome_hero(S) :- story(S), meddlesome(S).
careful_help(S) :- story(S), follows_clue(S), avoids_danger(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("quest_goal", "s1"),
            asp.fact("missing_goal", "s1"),
            asp.fact("meddlesome", "s1"),
            asp.fact("follows_clue", "s1"),
            asp.fact("avoids_danger", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        helper_name="Bello",
        piazza="Piazza Grande",
        quest_object="the silver festival bell",
        obstacle="a fountain that sneezed whenever anyone lied",
        tall_detail="so brightly that the afternoon moon came out to watch",
        route="through the fountain arcade",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show quest_story/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "quest_story"))
    if found == {("s1",)}:
        print("OK: ASP gate matches the Python quest pattern.")
        return 0
    print("MISMATCH: ASP did not recognize the quest pattern.")
    return 1


def verify_generation() -> int:
    samples = [
        generate(
            StoryParams(
                hero_name="Luna",
                helper_name="Bello",
                piazza="Piazza Grande",
                quest_object="the silver festival bell",
                obstacle="a fountain that sneezed whenever anyone lied",
                tall_detail="so brightly that the afternoon moon came out to watch",
                route="through the fountain arcade",
                seed=11,
            )
        ),
        generate(
            StoryParams(
                hero_name="Pia",
                helper_name="Sera",
                piazza="Piazza Sunwheel",
                quest_object="the moon-shaped key",
                obstacle="a flock of stubborn pigeons guarding the clock tower",
                tall_detail="so widely that the quest crossed the piazza before its shadow did",
                route="around the clock tower",
                seed=12,
            )
        ),
    ]
    for sample in samples:
        if not sample.story.strip():
            print("MISMATCH: generated story is empty.")
            return 1
        if "meddlesome" not in sample.story.lower():
            print("MISMATCH: generated story lost the required seed word.")
            return 1
        if "piazza" not in sample.story.lower():
            print("MISMATCH: generated story lost the required setting word.")
            return 1
        if len(sample.story_qa) < 3:
            print("MISMATCH: generated story lacks grounded QA.")
            return 1
    print("OK: Python generation gate passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall-tale quest world about a meddlesome piazza helper."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--piazza", choices=PIAZZAS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(
        tuple(name for name in HELPER_NAMES if name != hero_name)
    )
    piazza = args.piazza or rng.choice(PIAZZAS)
    quest_object = rng.choice(QUEST_OBJECTS)
    obstacle = rng.choice(OBSTACLES)
    tall_detail = rng.choice(TALL_DETAILS)
    route = rng.choice(ROUTES)
    return StoryParams(
        hero_name=hero_name,
        helper_name=helper_name,
        piazza=piazza,
        quest_object=quest_object,
        obstacle=obstacle,
        tall_detail=tall_detail,
        route=route,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        hero_name="Luna",
        helper_name="Bello",
        piazza="Piazza Grande",
        quest_object="the silver festival bell",
        obstacle="a fountain that sneezed whenever anyone lied",
        tall_detail="so brightly that the afternoon moon came out to watch",
        route="through the fountain arcade",
        seed=101,
    ),
    StoryParams(
        hero_name="Pia",
        helper_name="Sera",
        piazza="Piazza Sunwheel",
        quest_object="the moon-shaped key",
        obstacle="a flock of stubborn pigeons guarding the clock tower",
        tall_detail="so widely that the quest crossed the piazza before its shadow did",
        route="around the clock tower",
        seed=102,
    ),
    StoryParams(
        hero_name="Nico",
        helper_name="Mina",
        piazza="Piazza Marzipan",
        quest_object="the golden recipe book",
        obstacle="a bakery cart rolling downhill without its baker",
        tall_detail="so loudly that the paving stones hummed three streets away",
        route="beneath the striped market awnings",
        seed=103,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        status = verify_generation()
        if status:
            sys.exit(status)
        sys.exit(asp_verify())

    if args.asp:
        import asp

        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
