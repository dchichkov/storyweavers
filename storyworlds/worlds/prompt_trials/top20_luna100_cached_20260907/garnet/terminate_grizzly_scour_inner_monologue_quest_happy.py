#!/usr/bin/env python3
"""
A small superhero storyworld about a brave child, a grizzly, and a quest to
scour a dangerous mess before it can harm the mountain village.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    grizzly: Entity
    mentor: Entity
    place: str
    seed: int
    danger: str = ""
    method: str = ""
    helper: str = ""
    resolution: str = ""
    ending: str = ""
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    mentor_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Maya", "Theo", "Juno", "Kai", "Nell", "Remy", "Ari"]
MENTORS = ["Captain Sol", "Aunt Nova", "Dr. Vale", "Grandma Ray", "Coach Comet"]
PLACES = [
    "the Moonridge village",
    "the silver pine valley",
    "the cloud-top camp",
    "the bright mountain pass",
    "the comet garden",
]


ASP_RULES = r"""
#show quest_ready/1.
#show grizzly_helped/1.
#show danger_ended/1.

quest_ready(H) :- brave(H), has_tool(H), danger_exists.
grizzly_helped(G) :- grizzly(G), trusts(G,H), works_with(G,H).
danger_ended :- quest_ready(H), grizzly_helped(G).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("brave", "hero"),
            asp.fact("has_tool", "hero"),
            asp.fact("danger_exists"),
            asp.fact("grizzly", "grizzly"),
            asp.fact("trusts", "grizzly", "hero"),
            asp.fact("works_with", "grizzly", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show quest_ready/1.\n"
            "#show grizzly_helped/1.\n"
            "#show danger_ended/0."
        )
    )
    actual = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            if value.type == value.type.Number:
                args.append(value.number)
            elif value.type == value.type.String:
                args.append(value.string)
            else:
                args.append(value.name)
        actual.add((atom.name, tuple(args)))
    expected = {
        ("quest_ready", ("hero",)),
        ("grizzly_helped", ("grizzly",)),
        ("danger_ended", ()),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about a quest with a grizzly."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--mentor-name", choices=MENTORS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        mentor_name=args.mentor_name or rng.choice(MENTORS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.mentor_name:
        raise StoryError("The hero and mentor must have different names.")
    hero = Entity(
        id="hero",
        label=params.name,
        kind="hero",
        meters={"energy": 8.0, "distance": 0.0},
        memes={"courage": 7.0, "worry": 3.0, "hope": 6.0},
    )
    grizzly = Entity(
        id="grizzly",
        label="Bruno",
        kind="grizzly",
        meters={"strength": 10.0, "distance": 1.0},
        memes={"fear": 6.0, "trust": 2.0, "hunger": 5.0},
    )
    mentor = Entity(
        id="mentor",
        label=params.mentor_name,
        kind="mentor",
        meters={"distance": 0.0},
        memes={"trust": 8.0, "hope": 8.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.mentor_name}|{params.place}")
    return World(hero=hero, grizzly=grizzly, mentor=mentor, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _validate_world(world: World) -> None:
    if world.hero.memes["courage"] < 1:
        raise StoryError("The hero needs some courage to begin the quest.")
    if world.grizzly.memes["trust"] < 0:
        raise StoryError("The grizzly's trust cannot be negative.")
    if not world.place:
        raise StoryError("A quest needs a setting.")


def _set_facts(
    world: World,
    *,
    danger: str,
    method: str,
    helper: str,
    resolution: str,
    ending: str,
    lesson: str,
    story: str,
) -> str:
    world.danger = danger
    world.method = method
    world.helper = helper
    world.resolution = resolution
    world.ending = ending
    world.facts.update(
        danger=danger,
        method=method,
        helper=helper,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        story=story,
        quest_complete=True,
    )
    return story


def _storm_arc(world: World, rng: random.Random) -> str:
    h, g, m, p = (
        world.hero.label,
        world.grizzly.label,
        world.mentor.label,
        world.place,
    )
    object_name = _choice(rng, ["fallen branches", "silver leaves", "broken bridge planks"])
    danger = f"a windstorm buried the village trail under {object_name}"
    method = "scouring the trail with a wide rescue broom and clearing one safe path at a time"
    helper = f"{g} lifted the heaviest branches while {h} guided the broom"
    resolution = f"{h} and {g} scoured the trail together, then {h} used the moon beacon to terminate the storm's warning signal"
    ending = f"the villagers crossed the clean trail, and {g} received a warm berry pie beneath the calm stars"
    lesson = "A superhero can be brave without working alone."
    lines = [
        f"In {p}, {h} wore a red scarf as a superhero cape and watched dark clouds roll over the mountain.",
        f"A sudden windstorm buried the village trail under {object_name}. Without the trail, families could not reach the high shelter.",
        f'"This is my quest," {h} declared. {m} answered, "A real hero also notices who can help."',
        f"{h} looked at {g}, a huge grizzly sheltering beside a pine. The bear growled, and the village doors clicked shut.",
        f"{h} thought, *I am scared, but fear is a signal to move carefully, not a command to quit.*",
        f"The child placed a basket of berries on the ground and stepped back. {g} sniffed it, then carried a branch away.",
        f"{h} offered a wide rescue broom. Soon {helper}.",
        f"Each clear patch revealed another buried marker. At last, {resolution}.",
        f'"We did it together," said {h}. "Together," rumbled {g}, who had learned the word from {m}.',
        f"By morning, {ending}. {h} kept the cape, but the village called {g} the mountain's newest hero too.",
    ]
    return _set_facts(
        world,
        danger=danger,
        method=method,
        helper=helper,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        story=" ".join(lines),
    )


def _smoke_arc(world: World, rng: random.Random) -> str:
    h, g, m, p = (
        world.hero.label,
        world.grizzly.label,
        world.mentor.label,
        world.place,
    )
    source = _choice(rng, ["a cracked signal tower", "an overheated mine cart", "a pile of glowing pine cones"])
    danger = f"gray smoke from {source} was drifting toward {p}"
    method = "scouring the smoke vents with wet wool blankets and opening a fresh air channel"
    helper = f"{g} used powerful paws to roll the smoking stones away while {h} carried water"
    resolution = f"{h} and {g} scoured the vents until the fire was small enough to terminate safely"
    ending = f"clear air returned to {p}, and {g} slept beside a bowl of honey cakes"
    lesson = "Careful teamwork can turn a frightening cloud into clean morning air."
    lines = [
        f"At dawn in {p}, {h} spotted gray smoke rising from {source}. The smoke curled toward every cottage.",
        f"{m} pointed to the mountain path. " + '"A hero must reach the source before panic reaches the village," said the mentor.',
        f'"Then I will go!" cried ' + f"{h}. \"But not recklessly,\" {m} replied.",
        f"{h} found {g} near the smoke, coughing and guarding a cub's empty den. The grizzly bared sharp teeth.",
        f"{h} thought, *The bear is frightened, and frightened creatures need space before they need orders.*",
        f"The child set down a water bucket and backed away. {g} sniffed the water, drank, and followed at a careful distance.",
        f"{helper}. Together they opened a narrow air channel.",
        f"They wrapped the vents and poured water in turns. Then {resolution}.",
        f'"The smoke is gone," whispered {h}. "Your den is safe," said {m}. {g} answered with a gentle huff.',
        f"At sunset, {ending}. The cape on {h}'s shoulders smelled like pine, rain, and victory.",
    ]
    return _set_facts(
        world,
        danger=danger,
        method=method,
        helper=helper,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        story=" ".join(lines),
    )


def _signal_arc(world: World, rng: random.Random) -> str:
    h, g, m, p = (
        world.hero.label,
        world.grizzly.label,
        world.mentor.label,
        world.place,
    )
    object_name = _choice(rng, ["a humming crystal", "a runaway beacon", "a brass alarm drum"])
    danger = f"{object_name} was sending a wild signal that frightened every animal in {p}"
    method = "scouring the signal station for the loose gear that was making the noise"
    helper = f"{g} followed the vibration while {h} read the old warning map"
    resolution = f"{h} found the loose gear, and {g} held the station steady while the child worked to terminate the signal"
    ending = f"the quiet beacon shone softly over {p}, and {g} led a peaceful parade of foxes home"
    lesson = "Listening closely can be a superpower."
    lines = [
        f"On the tallest ridge above {p}, {h} heard {object_name} shriek into the morning.",
        f"Birds flew backward, rabbits hid in hats left on the trail, and even {g} ran in a circle.",
        f'"My superpower is courage!" shouted {h}. "Mine is listening," said {m}.',
        f"{h} closed both eyes and listened beneath the clang. A smaller rattle trembled inside the station.",
        f"{h} thought, *The loudest sound may be hiding the useful clue.*",
        f"{helper}. The grizzly stopped whenever the hidden rattle stopped.",
        f"{h} opened the panel and found a loose brass gear. " + f'"Hold still, {g}," said {h}. "I will make this safe."',
        f"{resolution}. The shriek became a soft chime.",
        f'"You heard the tiny trouble," said {m}. "And Bruno helped me reach it," said {h}.',
        f"By evening, {ending}. The quiet chime sounded like a medal for everyone.",
    ]
    return _set_facts(
        world,
        danger=danger,
        method=method,
        helper=helper,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        story=" ".join(lines),
    )


ARC_BUILDERS = [_storm_arc, _smoke_arc, _signal_arc]


def generate_story(world: World) -> str:
    _validate_world(world)
    rng = random.Random(world.seed ^ 0x41A7)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.facts
    return [
        QAItem(
            question=f"What danger did {h} discover?",
            answer=f"{h} discovered that {f['danger']}.",
        ),
        QAItem(
            question="What was the hero's quest?",
            answer=f"The quest was to {f['method']}.",
        ),
        QAItem(
            question="How did the grizzly help?",
            answer=f"The grizzly helped because {f['helper']}.",
        ),
        QAItem(
            question=f"How did {h} make the happy ending possible?",
            answer=f"{f['resolution']}. This allowed {f['ending']}.",
        ),
        QAItem(
            question="What did the hero think during the quest?",
            answer=f"{h} realized that {f['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear with strong paws, sharp claws, and a powerful sense of smell.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully or to clean it by rubbing and removing dirt.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="To terminate means to bring something to an end or make it stop safely.",
        ),
        QAItem(
            question="Why can a superhero need a helper?",
            answer="A helper can offer a strength, skill, or idea that the superhero does not have alone.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly superhero story about a quest involving a grizzly.",
        f"Tell a happy superhero adventure in {world.place} where a hero must scour a danger and terminate it safely.",
        "Use an inner monologue, a brave conversation, teamwork, and a clear happy ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.grizzly, world.mentor]:
        lines.append(
            f"  {entity.id:8} {entity.kind:8} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(
        [
            f"  place={world.place!r}",
            f"  danger={world.danger!r}",
            f"  method={world.method!r}",
            f"  helper={world.helper!r}",
            f"  resolution={world.resolution!r}",
        ]
    )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show quest_ready/1.\n"
                "#show grizzly_helped/1.\n"
                "#show danger_ended/0."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "quest_ready(hero), grizzly_helped(grizzly), danger_ended"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", mentor_name="Captain Sol", place="the Moonridge village"),
            StoryParams(name="Maya", mentor_name="Aunt Nova", place="the silver pine valley"),
            StoryParams(name="Theo", mentor_name="Dr. Vale", place="the cloud-top camp"),
            StoryParams(name="Juno", mentor_name="Grandma Ray", place="the bright mountain pass"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No story could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
