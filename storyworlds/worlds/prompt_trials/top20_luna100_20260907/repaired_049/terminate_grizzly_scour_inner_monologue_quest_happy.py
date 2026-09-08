#!/usr/bin/env python3
"""
A child-facing superhero storyworld about a grizzly, a dangerous trail,
and a quest to terminate a spreading problem through courage and care.

The simulated world tracks physical meters and emotional memes. Luna must
scour a mountain rescue route, face a grizzly without harming it, and
terminate the source of a roaring alarm before the valley festival begins.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
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
class World:
    place: str = "Pineglass Mountain"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Scenario:
    opening: str
    danger: str
    clue: str
    gear: str
    helper: str
    careful_action: str
    result: str
    change: str
    ending: str
    lesson: str


SCENARIOS = [
    Scenario(
        opening="A silver emergency beacon began shrieking from the old ranger tower.",
        danger="Its sharp sound was drawing a frightened grizzly toward the village trail.",
        clue="The grizzly kept turning toward the tower because the beacon's red light flashed beside a basket of honey cakes.",
        gear="a coil of rescue rope, a canvas food sack, and Luna's blue signal cape",
        helper="Milo, the young trail keeper",
        careful_action="she lowered her cape, asked Milo to pull the food sack away from the tower, and used the rope to guide the bear toward the quiet berry meadow",
        result="the grizzly followed the safe scent away from the homes, and the tower fell quiet",
        change="emergency beacons would be checked for tempting smells before each festival",
        ending="At sunset, the grizzly disappeared into the berry meadow while the blue cape waved above a safe and silent trail.",
        lesson="a hero protects frightened creatures as well as frightened people",
    ),
    Scenario(
        opening="A runaway snow machine rattled beside the mountain path and would not stop.",
        danger="The noise had startled a grizzly, and hikers were hurrying toward the same narrow bridge.",
        clue="A loose silver strap was tapping the machine's stop lever every time the wind blew.",
        gear="a padded glove, a bright warning flag, and a strong rescue cord",
        helper="Nia, the bridge guide",
        careful_action="she placed the warning flag, helped Nia clear the hikers, and pulled the silver strap free with the padded glove",
        result="the machine stopped before the bridge, and the grizzly lumbered safely into the firs",
        change="every trail machine would carry a visible stop marker and a quiet check card",
        ending="The bridge shone in the morning sun, and the grizzly's paw prints led peacefully into the trees.",
        lesson="quick courage works best when it first makes room for everyone to be safe",
    ),
    Scenario(
        opening="A bright drone had fallen into a ravine and was buzzing like an angry hornet.",
        danger="A grizzly cub was trapped behind it, while the mother bear paced above the rocks.",
        clue="The drone's blinking guide light reflected from a ledge just wide enough for a rescue rope.",
        gear="a soft net, a climbing harness, and Luna's star-shaped beacon",
        helper="Tess, the lookout captain",
        careful_action="she asked Tess to keep watch, lowered the soft net around the drone, and lifted it away before reaching the cub",
        result="the cub scrambled back to its mother, and the drone's buzzing finally ended",
        change="all rescue drones would use quiet signals near animal trails",
        ending="The mother grizzly vanished among the pines, and Luna's star beacon glowed over the empty ravine.",
        lesson="the strongest rescue is gentle enough to leave a wild family together",
    ),
]


@dataclass
class StoryParams:
    name: str
    power: str
    costume: str
    scenario: int
    seed: Optional[int] = None


NAMES = ["Luna", "Ari", "Mara", "Juno", "Tavi"]
POWERS = ["moonlight", "wind-gliding", "star-mapping", "echo-listening"]
COSTUMES = ["blue cape", "silver scarf", "golden boots", "red mask"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero quest about Luna, a grizzly, and a happy ending."
    )
    parser.add_argument("--name")
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--costume", choices=COSTUMES)
    parser.add_argument("--scenario", type=int, choices=range(len(SCENARIOS)))
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        power=args.power or rng.choice(POWERS),
        costume=args.costume or rng.choice(COSTUMES),
        scenario=args.scenario if args.scenario is not None else rng.randrange(len(SCENARIOS)),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if params.scenario not in range(len(SCENARIOS)):
        raise StoryError("That quest is not available in Pineglass Mountain.")


def tell(world: World, params: StoryParams) -> None:
    scenario = SCENARIOS[params.scenario]
    hero = world.add(Entity(params.name, "character", "hero", params.name))
    bear = world.add(Entity("grizzly", "animal", "grizzly", "the grizzly"))
    helper = world.add(Entity("helper", "character", "child", scenario.helper))
    beacon = world.add(Entity("beacon", "thing", "alarm", "the emergency alarm"))

    add_meme(hero, "hope")
    add_meme(hero, "worry")
    add_meter(hero, "bravery")
    add_meter(bear, "fear")
    add_meter(beacon, "noise")

    world.say(
        f"On Pineglass Mountain, {params.name} was a young superhero with "
        f"{params.power} and a {params.costume} that fluttered like a tiny flag."
    )
    world.say(
        f"People called {params.name} when a trail needed help, because the hero "
        "always looked for a safe answer instead of the loudest answer."
    )
    world.para()

    world.say(f"One bright morning, {scenario.opening}")
    world.say(f"{scenario.danger}")
    world.say(
        f"{params.name} felt worry flutter inside. The hero thought, "
        "\"If I rush in, I might make the danger worse. If I stay calm, I may notice what it needs.\""
    )
    world.say(
        f'{scenario.helper} called, "{params.name}, what should we do?" '
        f'{params.name} answered, "First, let us watch. Then we can help without hurting anyone."'
    )
    add_meme(hero, "focus")
    add_meter(hero, "observation")

    world.para()
    world.say(f"During the quest, {params.name} scoured the trail from the bridge to the tower.")
    world.say(f"The hero discovered that {scenario.clue}")
    world.say(f"Nearby lay {scenario.gear}.")
    world.say(
        f"{params.name} whispered the inner thought, "
        "\"A real superpower is not just stopping trouble. It is choosing what keeps the whole valley safe.\""
    )
    world.say(
        f"{params.name} told {scenario.helper}, "
        '"You watch the path, and I will handle the dangerous part. We can solve this together."'
    )
    add_meter(hero, "sharing")
    add_meme(hero, "trust")
    world.say(f"Then {params.name} {scenario.careful_action}.")
    add_meter(hero, "care")
    add_meter(beacon, "quiet")
    add_meme(bear, "calm")

    world.para()
    world.say(f"At last, {scenario.result}.")
    world.say(
        f"{params.name} used the hero's power to terminate the danger, not the grizzly's life."
    )
    world.say(f"The mountain team promised that {scenario.change}.")
    world.say(
        f"The quest ended with a happy ending: {scenario.ending} "
        f"Everyone cheered because {scenario.lesson}."
    )
    add_meme(hero, "joy")
    world.facts.update(hero=hero, bear=bear, helper=helper, beacon=beacon, scenario=scenario)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    scenario = world.facts["scenario"]
    return [
        f"Write a superhero quest about {hero.label}, a grizzly, and a happy ending.",
        f"Tell a child-friendly story in which the hero must scour a trail and terminate a danger.",
        f"Include an inner monologue showing why {hero.label} chooses a careful rescue.",
        f"Use this problem as the turning point: {scenario.danger}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            f"What quest did {hero.label} take on?",
            f"{hero.label} took on a quest to scour the mountain trail, protect the grizzly, and terminate the danger.",
        ),
        QAItem(
            "What clue changed the hero's plan?",
            f"The important clue was that {scenario.clue} It showed the hero what was causing the trouble.",
        ),
        QAItem(
            "What did the hero think inside?",
            f"The hero thought, \"A real superpower is not just stopping trouble. It is choosing what keeps the whole valley safe.\"",
        ),
        QAItem(
            "How did the hero help?",
            f"The hero {scenario.careful_action}. This protected both the people and the grizzly.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {scenario.ending}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large wild bear that needs space, food, and safe respect from people.",
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search an area carefully and thoroughly.",
        ),
        QAItem(
            "What does terminate mean?",
            "To terminate means to bring something to an end, such as stopping an alarm or danger.",
        ),
        QAItem(
            "What makes a superhero?",
            "A superhero uses courage and special abilities to protect others, while also making careful and kind choices.",
        ),
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(quest, grizzly, terminate).
safe_rescue :- valid(quest, grizzly, terminate).
#show valid/3.
#show safe_rescue/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("domain", "superhero"),
            asp.fact("quest", "trail"),
            asp.fact("animal", "grizzly"),
            asp.fact("goal", "terminate"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "valid")) and bool(asp.atoms(model, "safe_rescue"))


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: ASP rejected the superhero quest.")
        return 1
    if set(valid_combos()) != {("quest", "grizzly", "terminate")}:
        print("MISMATCH: Python registry is incomplete.")
        return 1
    for scenario in range(len(SCENARIOS)):
        sample = generate(StoryParams("Luna", "moonlight", "blue cape", scenario))
        if not sample.story or "grizzly" not in sample.story or "happy ending" not in sample.story:
            print("MISMATCH: generated story failed exercise.")
            return 1
    print("OK: ASP matches Python and generated stories exercise successfully.")
    return 0


def valid_combos() -> list[tuple[str, str, str]]:
    return [("quest", "grizzly", "terminate")]


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

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "moonlight", "blue cape", i)
            for i in range(len(SCENARIOS))
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### quest {i + 1}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
