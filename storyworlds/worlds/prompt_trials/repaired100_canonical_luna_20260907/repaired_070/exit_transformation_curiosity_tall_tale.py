#!/usr/bin/env python3
"""
A tall tale storyworld about curiosity, transformation, and finding an exit.
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


PLACES = ["the upside-down museum", "the giant greenhouse", "the cloud castle"]
NAMES = ["Luna", "Pip", "Mara", "Tavi", "Nell", "Bram"]
ANIMAL_NAMES = ["a moon moth", "a singing fox", "a pocket-sized dragon"]
OBJECTS = ["a brass key", "a blue button", "a silver spoon"]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("size", "glow", "open", "changed"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "bravery", "worry", "wonder"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.lines if part)


@dataclass
class StoryParams:
    place: str
    name: str
    companion: str
    object_name: str
    creature: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Episode:
    title: str
    oddity: str
    obstacle: str
    clue: str
    transformation: str
    final_image: str


EPISODES = [
    Episode(
        "The Door That Grew",
        "every door in the museum had grown as tall as a mountain",
        "the only exit was a tiny handle far above their heads",
        "a trail of golden fingerprints climbed the wall beside it",
        "curiosity made Luna stretch taller each time she asked a careful question",
        "the children stepped through the exit while their new long shadows bowed behind them",
    ),
    Episode(
        "The Whispering Hall",
        "the greenhouse whispered every time a leaf turned",
        "the exit had hidden itself behind a curtain of enormous vines",
        "the vines opened whenever someone listened instead of pulling",
        "Luna changed from a hurried climber into a patient listener with ears as wide as umbrellas",
        "the exit bloomed like a flower and released a warm puff of summer air",
    ),
    Episode(
        "The Backward Stair",
        "the castle stairs went down whenever anyone tried to climb up",
        "the exit seemed to move one step farther away",
        "a small arrow pointed toward the step nobody had inspected",
        "curiosity turned Luna's fear into a bright compass in her chest",
        "the final stair flipped upright and became the doorway home",
    ),
    Episode(
        "The Giant Pocket",
        "a friendly dragon had swallowed the map to the exit by accident",
        "the map was folded inside a pocket the size of a pond",
        "the dragon's hiccups marked the map's location with tiny blue sparks",
        "Luna grew as wide as a wagon so she could reach the map without tearing it",
        "she returned to normal beside the exit, carrying the dragon's map like a picnic blanket",
    ),
]


def choose_episode(params: StoryParams) -> Episode:
    value = (params.seed or 0) + sum(ord(c) for c in params.name + params.place)
    return EPISODES[value % len(EPISODES)]


def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown name: {params.name}")
    if params.companion == params.name:
        raise StoryError("The traveler and companion must have different names.")
    if not params.object_name:
        raise StoryError("The traveler needs a curious object to investigate.")
    if not params.creature:
        raise StoryError("The story needs a creature helper.")


def tell(params: StoryParams) -> World:
    validate(params)
    episode = choose_episode(params)
    world = World(params.place)

    traveler = world.add(Entity("traveler", "character", "child", params.name))
    companion = world.add(Entity("companion", "character", "companion", params.companion))
    token = world.add(Entity("token", "thing", "object", params.object_name))
    creature = world.add(Entity("creature", "animal", "helper", params.creature))
    exit_entity = world.add(Entity("exit", "place", "doorway", "the exit"))

    traveler.memes["curiosity"] = 2
    traveler.memes["worry"] = 1
    traveler.meters["size"] = 1
    token.meters["glow"] = 1
    creature.memes["wonder"] = 1

    world.facts.update(
        traveler=traveler,
        companion=companion,
        token=token,
        creature=creature,
        exit=exit_entity,
        episode=episode,
        transformed=False,
        exit_found=False,
    )

    world.say(
        f"One morning, {params.name} and {params.companion} wandered into {params.place}, "
        f"where even the dust had a habit of telling tall tales."
    )
    world.say(
        f"{episode.title} began when {episode.oddity}. {params.name} held {params.object_name}, "
        f"which glowed whenever curiosity got close."
    )

    world.para()
    world.say(
        f"They searched for the exit, but {episode.obstacle}. "
        f"{params.name} wanted to rush ahead, while {params.companion} wisely held back."
    )
    world.say(
        f'"Should we follow the strange thing, or pretend we never saw it?" {params.companion} asked.'
    )
    world.say(
        f'"We should ask it one good question," {params.name} replied. '
        f'"Curiosity may be enormous, but it is not the same as guessing."'
    )
    world.say(
        f"The question woke {params.creature}, who had been hiding nearby. "
        f"The creature blinked twice and revealed that {episode.clue}."
    )

    world.para()
    traveler.memes["curiosity"] += 1
    traveler.memes["bravery"] += 1
    token.meters["glow"] = 2
    world.say(f"{params.name} investigated instead of turning back. {episode.transformation}.")
    traveler.meters["size"] = 3
    traveler.meters["changed"] = 1
    world.facts["transformed"] = True
    world.say(
        f"{params.companion} stared. '{params.name}, you have changed!' "
        f"{params.name} answered, 'Only enough to reach the truth.'"
    )
    world.say(
        f"With {params.companion} guiding the way and {params.creature} cheering, "
        f"{params.name} used the glowing {params.object_name} to reveal the exit."
    )
    exit_entity.meters["open"] = 1
    world.facts["exit_found"] = True

    world.para()
    world.say(f"They crossed the exit together. {episode.final_image}.")
    world.say(
        f"After that day, {params.name} still asked questions, but always looked for clues, "
        f"listened to helpers, and made sure no companion was left behind."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    episode: Episode = f["episode"]  # type: ignore[assignment]
    traveler: Entity = f["traveler"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    return [
        "Write a child-facing tall tale about curiosity leading to a surprising transformation and an exit.",
        f"Tell a tall tale in which {traveler.label} and {companion.label} investigate {episode.oddity}, speak to each other, and discover the exit.",
        "Make the transformation solve a concrete problem while preserving a warm, adventurous ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    episode: Episode = f["episode"]  # type: ignore[assignment]
    traveler: Entity = f["traveler"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    creature: Entity = f["creature"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did {traveler.label} and {companion.label} face?",
            answer=f"They needed to find the exit because {episode.obstacle}.",
        ),
        QAItem(
            question="How did curiosity help them?",
            answer=f"They stopped guessing and investigated. They learned that {episode.clue}.",
        ),
        QAItem(
            question=f"What transformation happened to {traveler.label}?",
            answer=episode.transformation + ".",
        ),
        QAItem(
            question=f"Who helped the travelers?",
            answer=f"{creature.label} helped by revealing the clue and cheering them toward the exit.",
        ),
        QAItem(
            question="How did the story end?",
            answer=episode.final_image + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an exit?",
            answer="An exit is a way out of a place, such as a doorway or gate.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is a wish to learn or find out more about something.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form, condition, or appearance into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  exit_found={world.facts.get('exit_found')}")
    lines.append(f"  transformed={world.facts.get('transformed')}")
    return "\n".join(lines)


ASP_RULES = r"""
investigated :- curious, clue.
transformed :- investigated.
exit_open :- transformed, helper.
good_tall_tale :- exit_open.
#show good_tall_tale/0.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [
            fact("curious"),
            fact("clue"),
            fact("helper"),
        ]
    )


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        from asp import atoms, one_model
        model = one_model(asp_program())
        if not atoms(model, "good_tall_tale"):
            raise StoryError("ASP twin did not derive good_tall_tale.")
    except ImportError:
        return 0
    for seed in range(5):
        params = StoryParams(
            place=PLACES[seed % len(PLACES)],
            name=NAMES[seed % len(NAMES)],
            companion=NAMES[(seed + 1) % len(NAMES)],
            object_name=OBJECTS[seed % len(OBJECTS)],
            creature=ANIMAL_NAMES[seed % len(ANIMAL_NAMES)],
            seed=seed,
        )
        sample = generate(params)
        if "exit" not in sample.story.lower():
            raise StoryError("Generated story omitted the exit.")
        if not sample.world.facts["exit_found"]:
            raise StoryError("Generated world did not find the exit.")
    print("OK: Python and ASP agree that curiosity and transformation open the exit.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall tale storyworld about curiosity, transformation, and an exit."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=NAMES)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("--creature", choices=ANIMAL_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice([n for n in NAMES if n != name])
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        name=name,
        companion=companion,
        object_name=args.object_name or rng.choice(OBJECTS),
        creature=args.creature or rng.choice(ANIMAL_NAMES),
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


CURATED = [
    StoryParams("the upside-down museum", "Luna", "Pip", "a brass key", "a moon moth", 1),
    StoryParams("the giant greenhouse", "Mara", "Tavi", "a blue button", "a singing fox", 2),
    StoryParams("the cloud castle", "Nell", "Bram", "a silver spoon", "a pocket-sized dragon", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        try:
            from asp import atoms, one_model
            model = one_model(asp_program())
            if not atoms(model, "good_tall_tale"):
                raise StoryError("ASP rejected the story conditions.")
        except ImportError:
            raise StoryError("--asp requires clingo and storyworlds/asp.py.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
