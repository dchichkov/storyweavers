#!/usr/bin/env python3
"""
A small slice-of-life storyworld about Boog, a kind proposition, and teamwork.
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
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    helper: str
    task: str
    seed: Optional[int] = None
    telling: int = 0


NAMES = ["Luna", "Milo", "Nia", "Pip", "Sami"]
HELPERS = ["Boog", "Mara", "Tess", "Jo"]
TASKS = [
    "prepare a small fruit table for the apartment courtyard",
    "make a blanket fort for the rainy afternoon",
    "sort the donated books in the community room",
    "decorate the hallway for a neighbor's birthday",
    "carry herb pots from the porch to the sunny window",
]

SCENES = [
    {
        "object": "a wide picnic blanket",
        "problem": "the blanket kept folding under one corner while the fruit bowl waited on the table",
        "clue": "one corner was caught beneath a flowerpot",
        "plan": "hold the corners still, move the pot together, and smooth the blanket before setting down the bowl",
        "ending": "The blanket lay flat, and everyone found a sunny place to share the fruit.",
    },
    {
        "object": "a stack of picture books",
        "problem": "the tallest stack leaned toward the open door whenever somebody added another book",
        "clue": "three heavy books were resting on one narrow edge",
        "plan": "make two shorter stacks and let one person steady each while the third carried books",
        "ending": "The shelves filled evenly, and the last book went into place without a wobble.",
    },
    {
        "object": "a string of paper stars",
        "problem": "the stars stretched across the hall, but the tape kept peeling from the dusty wall",
        "clue": "the wall felt smooth only above the old coat hooks",
        "plan": "wipe the wall, move the string higher, and have one teammate hold it while another pressed the tape",
        "ending": "The paper stars hung in a bright line, and the hallway looked ready for the party.",
    },
    {
        "object": "three little herb pots",
        "problem": "the pots were heavier than they looked, and the sunny window was across a narrow room",
        "clue": "the soil shifted whenever one pot was carried by its rim",
        "plan": "put the pots in a shallow tray and carry the tray with two pairs of hands",
        "ending": "The herbs reached the sunny window together, with their leaves still upright.",
    },
]


def _choose_scene(params: StoryParams) -> dict[str, str]:
    return SCENES[(params.telling + len(params.task)) % len(SCENES)]


def tell(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.helper.strip():
        raise StoryError("helper must not be empty")
    if not params.task.strip():
        raise StoryError("task must not be empty")

    scene = _choose_scene(params)
    world = World()
    hero = world.add(Entity("hero", "character", params.name))
    boog = world.add(Entity("boog", "character", "Boog"))
    helper = world.add(Entity("helper", "character", params.helper))
    object_entity = world.add(Entity("shared_object", "thing", scene["object"]))

    hero.memes.update({"worry": 1.0, "belonging": 0.0})
    boog.memes.update({"care": 1.0, "belonging": 1.0})
    helper.memes.update({"care": 1.0, "belonging": 1.0})
    object_entity.meters["stability"] = 0.0

    openings = [
        f"{params.name} was helping to {params.task} in the shared room.",
        f"After lunch, {params.name} went to {params.task} while the room filled with ordinary afternoon sounds.",
        f"{params.name} had promised to help {params.task}, even though the job looked bigger up close.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say(f"{scene['object'].capitalize()} was waiting nearby, and {scene['problem']}.")

    world.para()
    world.say(f"Boog noticed the trouble before anyone began tugging.")
    world.say(f'"I have a proposition," Boog said. "What if we make this a team job instead of pulling harder?"')
    world.say(f'"I thought I had to finish it alone," {params.name} replied.')
    world.say(f'"You can start the plan," {params.helper} said, "and we can lend the hands it needs."')
    world.say(f"{params.name} looked closely and saw that {scene['clue']}.")

    hero.memes["worry"] = 0.0
    hero.memes["belonging"] = 1.0
    object_entity.meters["stability"] = 1.0
    world.fired.add("proposition_heard")

    world.para()
    world.say(f"They agreed on one small plan: {scene['plan']}.")
    world.say(f"{params.name} gave each person a clear part, and nobody had to guess when to move.")
    world.say(f"Boog counted softly, while {params.helper} watched the tricky side.")
    world.say(f"Together, they finished the job without rushing or blaming anyone.")

    world.para()
    world.say(scene["ending"])
    world.say(
        f"{params.name} smiled because the proposition had changed more than the task: "
        "it had made room for everyone's useful help."
    )

    world.facts.update(
        hero=hero,
        boog=boog,
        helper=helper,
        object=object_entity,
        scene=scene,
        task=params.task,
        proposition=True,
        teamwork=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a slice-of-life story about {hero.label} helping to {f['task']}.",
        f"Include Boog making a proposition that turns the problem into teamwork.",
        f"Show how the clue '{f['scene']['clue']}' changes the group's plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    boog: Entity = f["boog"]
    helper: Entity = f["helper"]
    scene = f["scene"]
    return [
        QAItem(
            "Who is the story about?",
            f"The story is about {hero.label}, who is helping to {f['task']}.",
        ),
        QAItem(
            "What proposition did Boog make?",
            f"Boog proposed making the task a team job instead of pulling harder alone.",
        ),
        QAItem(
            "What clue did the group notice?",
            f"They noticed that {scene['clue']}.",
        ),
        QAItem(
            "How did teamwork solve the problem?",
            f"{hero.label}, Boog, and {helper.label} divided the work into clear parts and followed this plan: {scene['plan']}.",
        ),
        QAItem(
            "What changed by the end?",
            f"The group finished safely, and {hero.label} learned that asking for useful help can make room for everyone's strengths.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What is teamwork?",
        "Teamwork is when people cooperate, share jobs, and help one another reach a goal.",
    ),
    QAItem(
        "What is a proposition?",
        "A proposition is an idea or suggestion offered for people to consider.",
    ),
    QAItem(
        "Why can dividing a task help?",
        "Dividing a task can make the work safer, clearer, and easier for each person to manage.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  teamwork={world.facts.get('teamwork')}")
    lines.append(f"  proposition={world.facts.get('proposition')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "boog"),
            asp.fact("character", "hero"),
            asp.fact("character", "helper"),
            asp.fact("proposition", "boog", "teamwork"),
            asp.fact("needs", "hero", "help"),
            asp.fact("teamwork", "hero", "boog", "helper"),
        ]
    )


ASP_RULES = r"""
suggests(Boog, teamwork) :- proposition(Boog, teamwork).
supported(hero) :- needs(hero, help), teamwork(hero, Boog, helper).
valid :- suggests(Boog, teamwork), supported(hero).
#show suggests/2.
#show supported/1.
#show valid/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid")
    supported = asp.atoms(model, "supported")
    if valid == [()] and supported == [("hero",)]:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP valid:", valid)
    print("ASP supported:", supported)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-life teamwork storyworld about Boog's proposition."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--telling", type=int, choices=range(3))
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
        helper=args.helper or rng.choice(HELPERS),
        task=args.task or rng.choice(TASKS),
        seed=args.seed,
        telling=args.telling if args.telling is not None else rng.randrange(3),
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, name in enumerate(NAMES):
            params = StoryParams(
                name=name,
                helper=HELPERS[index % len(HELPERS)],
                task=TASKS[index % len(TASKS)],
                seed=base_seed + index,
                telling=index % 3,
            )
            samples.append(generate(params))
    else:
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
