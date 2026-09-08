#!/usr/bin/env python3
"""
A standalone Storyweavers world about a friendship program and an enormous
alfalfa patch, told in a playful tall-tale voice.
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
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    farmer_name: str
    seed: Optional[int] = None
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


NAMES = ["Luna", "Milo", "Pip", "Nell", "Toby", "Zara"]
FRIEND_NAMES = ["Bea", "Ollie", "June", "Sami", "Wren", "Theo"]
FARMER_NAMES = ["Farmer Ada", "Farmer Gus", "Farmer Mae", "Farmer Sol"]

SCENARIOS = [
    {
        "place": "a windy hill farm",
        "program": "a friendship program that paired every child with a growing partner",
        "problem": "Luna and Bea had been paired, but the program's chart blew away before either friend saw it",
        "alfalfa": "an alfalfa stalk taller than the barn",
        "task": "find the missing chart and water the giant alfalfa together",
        "turn": "Bea noticed that the chart was pinned beneath the alfalfa's broadest leaf",
        "repair": "Luna stopped rushing, listened to Bea, and let her choose the safest path",
        "result": "Together they tied the chart to a fence post and watered the alfalfa with a pump that made a river-sized splash",
        "image": "The friendship chart fluttered beneath the giant alfalfa, with both names written in the same bright green square",
    },
    {
        "place": "a valley farm beside a silver creek",
        "program": "a friendship program that asked partners to share one useful job",
        "problem": "Luna wanted to carry the water bucket alone, while Bea worried that the enormous alfalfa would bend the footbridge",
        "alfalfa": "a patch of alfalfa wide enough to shade three hay wagons",
        "task": "bring water across the creek without breaking the bridge",
        "turn": "Bea found a line of flat stones and showed that two small buckets would balance better than one large bucket",
        "repair": "Luna apologized for ignoring her friend and agreed that a shared plan could be stronger than a heroic guess",
        "result": "They crossed by taking turns on the stones, and the alfalfa drank every shining drop",
        "image": "The two empty buckets rested together while the alfalfa waved like a green crowd cheering for them",
    },
    {
        "place": "a sunny community farm",
        "program": "a friendship program that invited partners to make a welcome sign",
        "problem": "Luna painted a huge sign by herself and accidentally covered the space where Bea's name belonged",
        "alfalfa": "an alfalfa tower whose leaves tickled the low clouds",
        "task": "finish a welcome sign before the farm visitors arrived",
        "turn": "Bea used a thin twig to sketch letters around the leaf shapes, turning the mistake into a leafy border",
        "repair": "Luna made room for Bea's idea and repainted the middle so both friends could design it",
        "result": "Their sign welcomed every visitor in letters large enough for birds to read from above",
        "image": "The sign leaned against the alfalfa tower, and its two names curled together like vines",
    },
    {
        "place": "a moonlit farmyard",
        "program": "a friendship program that gave partners one mystery to solve",
        "problem": "Luna guessed the mystery answer loudly and Bea stopped sharing the clues she had collected",
        "alfalfa": "a moon-high alfalfa stalk that cast a shadow over the chicken coop",
        "task": "discover why the tallest alfalfa leaf kept pointing east",
        "turn": "Bea explained that the leaf bent toward the creek because the evening breeze came from the west",
        "repair": "Luna listened, thanked Bea for the careful clue, and changed the guess",
        "result": "They followed the leaf's direction to a lost basket and returned it to the farm kitchen",
        "image": "The tallest leaf pointed toward the recovered basket while Luna and Bea shared the last warm biscuit",
    },
]

OPENINGS = [
    "In a valley where the fences were straight and the stories were never small, Luna joined a new farm program.",
    "Everyone in the county knew that the farm's friendship program had unusual rules and unusually large vegetables.",
    "On the morning the rooster crowed loud enough to rattle the weather vane, Luna arrived at the community farm.",
    "The farm bell rang once for work, twice for lunch, and three times whenever a friendship needed mending.",
]

DIALOGUES = [
    '"A friendship is not a race," Bea said. "It is a road we build together."',
    '"Wait," Bea called. "My clue may be small, but it can still point us somewhere big."',
    '"I wanted to be helpful," Luna admitted. "I forgot that helping means listening too."',
    '"Let us try your plan and mine together," Luna said. "Then neither of us has to carry the whole story alone."',
]

ENDINGS = [
    "From that day forward, the farm's friendship program had one extra rule: every giant job needed two open ears.",
    "Afterward, the children measured their success not by the size of the alfalfa, but by the room they made for one another.",
    "The farm wrote the lesson into its program book, using letters so large that even the clouds could read them.",
    "And whenever the alfalfa rustled in the wind, Luna and Bea remembered that a good friend helps another friend grow.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall tale about alfalfa and friendship.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--farmer", choices=FARMER_NAMES)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    farmer = args.farmer or rng.choice(FARMER_NAMES)
    if name == friend:
        friend = rng.choice([x for x in FRIEND_NAMES if x != name])
    return StoryParams(
        name=name,
        friend_name=friend,
        farmer_name=farmer,
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name or not params.friend_name or not params.farmer_name:
        raise StoryError("Names must not be empty.")
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("scenario_id is outside the available story scenarios.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    scenario = SCENARIOS[params.scenario_id]
    world = World()

    hero = world.add(Entity("hero", "character", "child", params.name))
    friend = world.add(Entity("friend", "character", "child", params.friend_name))
    farmer = world.add(Entity("farmer", "character", "farmer", params.farmer_name))
    program = world.add(Entity("program", "thing", "program", "friendship program"))
    alfalfa = world.add(Entity("alfalfa", "plant", "alfalfa", "giant alfalfa"))

    hero.memes["hope"] = 1.0
    friend.memes["care"] = 1.0
    alfalfa.meters["height"] = 12.0
    alfalfa.meters["friendship_power"] = 0.0

    world.facts.update(
        hero=hero,
        friend=friend,
        farmer=farmer,
        program=program,
        alfalfa=alfalfa,
        scenario=scenario,
        resolved=False,
    )

    world.say(OPENINGS[params.opening_id])
    world.say(
        f"{params.name} met {params.friend_name} through {scenario['program']}. "
        f"At {scenario['place']}, they were asked to {scenario['task']}."
    )
    world.say(
        f"The farm's proudest plant was {scenario['alfalfa']}, and "
        f"{params.farmer_name} said even its smallest leaf deserved careful attention."
    )

    world.para()
    world.say(f"But {scenario['problem']}.")
    hero.memes["rushed"] = 1.0
    friend.memes["worried"] = 1.0
    world.say(
        f"{params.name} hurried toward the field, while {params.friend_name} stood beside the path with a worried look."
    )
    world.say(f"The first plan failed because neither friend had heard the other clearly.")

    world.para()
    world.say(DIALOGUES[params.dialogue_id])
    world.say(
        f"Then {scenario['turn']}. The tiny observation mattered because it showed the friends a safer way to finish the giant job."
    )
    friend.memes["agency"] = 1.0
    hero.memes["listening"] = 1.0
    world.say(f"{params.name} said sorry and {scenario['repair']}.")
    world.say(f"{scenario['result']}.")
    alfalfa.meters["watered"] = 1.0
    alfalfa.meters["friendship_power"] = 1.0
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(ENDINGS[params.ending_id])
    world.say(f"{scenario['image']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    return [
        f"Write a child-friendly Tall Tale about {world.facts['hero'].label} and {world.facts['friend'].label} using a friendship program.",
        f"Include giant alfalfa and the problem that {scenario['problem']}.",
        f"Show how the friends listen, repair their disagreement, and complete this task: {scenario['task']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scenario = facts["scenario"]
    hero = facts["hero"].label
    friend = facts["friend"].label
    return [
        QAItem(
            "What brought the two children together?",
            f"{hero} and {friend} met through a friendship program that paired children for useful farm work.",
        ),
        QAItem(
            "What enormous plant grew on the farm?",
            f"The farm had {scenario['alfalfa']}.",
        ),
        QAItem(
            f"What problem did {hero} and {friend} face?",
            f"They faced this problem: {scenario['problem']}. Their first plan failed because they did not listen carefully to each other.",
        ),
        QAItem(
            "What changed the friends' plan?",
            f"{friend} noticed that {scenario['turn']}. This clue helped both friends choose a better method.",
        ),
        QAItem(
            "How was the friendship repaired?",
            f"{hero} apologized, listened to {friend}, and {scenario['repair']}. They then worked together to {scenario['task']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is alfalfa?", "Alfalfa is a leafy plant often grown as food for farm animals."),
        QAItem("What is a program?", "A program is an organized plan or set of activities."),
        QAItem("What is friendship?", "Friendship is a caring relationship in which people trust, help, and enjoy one another."),
        QAItem("What is a tall tale?", "A tall tale is a playful story that uses impossible exaggeration for fun."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: {entity.label} meters={meters} memes={memes}"
        )
    lines.append(f"resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
seed_word(program).
seed_word(alfalfa).
feature(friendship).
style(tall_tale).
valid_story :- seed_word(program), seed_word(alfalfa), feature(friendship), style(tall_tale).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("seed_word", "program"),
            asp.fact("seed_word", "alfalfa"),
            asp.fact("feature", "friendship"),
            asp.fact("style", "tall_tale"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {()}
    if actual == expected:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("Luna", "Bea", "Farmer Ada", scenario_id=0),
    StoryParams("Milo", "June", "Farmer Gus", scenario_id=1),
    StoryParams("Pip", "Sami", "Farmer Mae", scenario_id=2),
    StoryParams("Nell", "Theo", "Farmer Sol", scenario_id=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
