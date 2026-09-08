#!/usr/bin/env python3
"""A small fable StoryWorld about reflex, suspense, and moral value."""

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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


ANIMALS = ["Mara", "Tillo", "Suri", "Bram", "Nell", "Odo"]
PLACES = ["the old orchard", "the reed bridge", "the moonlit millpond", "the hill path"]
DANGERS = ["a falling beehive", "a rolling stone", "a snapping branch", "a loose lantern"]
VALUES = ["kindness", "courage", "patience", "honesty"]
SCENES = [
    ("honey", "a swarm of sleepy bees", "a jar of wild honey"),
    ("apples", "a basket of red apples", "the ripest apple"),
    ("feathers", "a pile of bright feathers", "a blue feather"),
    ("grain", "a sack of golden grain", "the fullest measure"),
]

OPENINGS = [
    "At dawn, when the dew still jeweled the grass",
    "One warm afternoon, while the shadows shortened",
    "As the first star blinked above the trees",
    "Before breakfast, when the valley was quiet",
    "On a windy morning beside the water",
]

@dataclass(frozen=True)
class Scenario:
    ident: str
    danger: str
    object_name: str
    reward: str
    helper: str
    value: str
    lesson: str
    image: str


SCENARIOS = (
    Scenario(
        "hive",
        "a falling beehive",
        "a frightened bee",
        "a jar of wild honey",
        "a tired old tortoise",
        "kindness",
        "a quick reflex is finest when it protects someone weaker",
        "bees humming peacefully above a repaired hive",
    ),
    Scenario(
        "stone",
        "a rolling stone",
        "a small field mouse",
        "the ripest apple",
        "a watchful crow",
        "courage",
        "courage is not rushing toward danger but choosing the safe brave act",
        "the mouse sharing an apple beneath the quiet tree",
    ),
    Scenario(
        "branch",
        "a snapping branch",
        "a nestling sparrow",
        "a blue feather",
        "a patient deer",
        "patience",
        "a good reflex must be guided by patience and care",
        "the sparrow singing from a steady branch",
    ),
    Scenario(
        "lantern",
        "a loose lantern",
        "a curious hedgehog",
        "the fullest measure",
        "a truthful fox",
        "honesty",
        "a clever reflex should serve truth rather than pride",
        "the lantern glowing safely beside the millpond",
    ),
)


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


@dataclass
class StoryParams:
    place: str
    hero_name: str
    scenario_id: str = "hive"
    opening_id: int = 0
    question_id: int = 0
    seed: Optional[int] = None


QUESTIONS = [
    '"Did you save the reward for yourself?" asked the tortoise.',
    '"Will you help me before you take your prize?" asked the crow.',
    '"What matters more, winning or protecting a friend?" asked the deer.',
    '"Shall we tell the truth about what happened?" asked the fox.',
]

REFLEX_LINES = [
    "Before thought could catch up, the fox sprang sideways and caught the rope.",
    "In one bright reflex, the fox planted both paws against the gate.",
    "The fox reacted at once, turning the danger away from the smaller creature.",
    "A swift reflex moved the fox between the danger and the helpless neighbor.",
]

def scenario_for(ident: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.ident == ident:
            return scenario
    raise StoryError(f"Unknown scenario: {ident}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fable StoryWorld about reflex, suspense, and moral value."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name", choices=ANIMALS)
    parser.add_argument("--scenario", choices=[s.ident for s in SCENARIOS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=args.hero_name or rng.choice(ANIMALS),
        scenario_id=args.scenario or rng.choice([s.ident for s in SCENARIOS]),
        opening_id=rng.randrange(len(OPENINGS)),
        question_id=rng.randrange(len(QUESTIONS)),
    )


def tell(params: StoryParams) -> World:
    scenario = scenario_for(params.scenario_id)
    world = World(params.place)
    hero = world.add(
        Entity(
            "hero",
            "animal",
            params.hero_name,
            "quick traveler",
            meters={"alertness": 1.0, "balance": 1.0},
            memes={"pride": 0.8, scenario.value: 0.3},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "animal",
            scenario.helper,
            "wise neighbor",
            meters={"strength": 0.7},
            memes={"trust": 0.8},
        )
    )
    victim = world.add(
        Entity(
            "victim",
            "animal",
            scenario.object_name,
            "neighbor in danger",
            memes={"fear": 1.0},
        )
    )
    world.facts.update(
        scenario=scenario,
        hero=hero,
        helper=helper,
        victim=victim,
        danger=scenario.danger,
        resolved=False,
        value=scenario.value,
    )
    return world


def render_story(world: World) -> str:
    facts = world.facts
    scenario: Scenario = facts["scenario"]
    hero: Entity = facts["hero"]
    helper: Entity = facts["helper"]
    victim: Entity = facts["victim"]
    place = world.place

    paragraphs = [
        (
            f"{OPENINGS[world.facts['opening_id'] if 'opening_id' in world.facts else 0]}, "
            f"{hero.label} walked through {place}. "
            f"{helper.label} followed slowly, carrying a little bell, while {victim.label} "
            f"waited near {scenario.reward}."
        ),
        (
            f"Suddenly, {scenario.danger} lurched toward {victim.label}. "
            f"The danger made the air still. Would {hero.label} move in time? "
            f"{hero.label} heard the frightened cry and felt a swift reflex seize their paws."
        ),
        (
            f"{REFLEX_LINES[world.facts['question_id'] % len(REFLEX_LINES)]} "
            f"The danger stopped just short of {victim.label}. "
            f"The small neighbor trembled, but was safe."
        ),
        (
            f'{QUESTIONS[world.facts["question_id"]]} '
            f'{hero.label} looked at {scenario.reward}, then looked at {victim.label}. '
            f'"A prize is not worth much if it is won by leaving a friend afraid," '
            f"{hero.label} replied."
        ),
        (
            f"{helper.label} nodded. \"Your reflex saved the day, but your choice gave it meaning.\" "
            f"{hero.label} shared {scenario.reward} with {victim.label} and helped make the place safe."
        ),
        (
            f"From then on, the neighbors remembered that {scenario.lesson}. "
            f"Their closing picture was {scenario.image}. "
            f"That was the moral value of the deed: quick hands may stop a danger, "
            f"but a caring heart decides what should be saved."
        ),
    ]
    facts["resolved"] = True
    facts["outcome"] = scenario.image
    hero.memes[scenario.value] = 1.0
    hero.memes["pride"] = 0.1
    victim.memes["fear"] = 0.0
    victim.memes["trust"] = 1.0
    return "\n\n".join(paragraphs)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["opening_id"] = params.opening_id
    world.facts["question_id"] = params.question_id
    story = render_story(world)
    scenario: Scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a fable about {hero.label} using a reflex to protect a smaller neighbor.",
            f"Create suspense when {scenario.danger} threatens {scenario.object_name}.",
            f"End with the moral value of {scenario.value} and the image {scenario.image}.",
        ],
        story_qa=[
            QAItem(
                "What created the suspense?",
                f"The suspense began when {scenario.danger} moved toward {scenario.object_name}, leaving little time to act.",
            ),
            QAItem(
                "How did the hero use reflex?",
                f"{hero.label} reacted quickly and moved the danger away before {scenario.object_name} was hurt.",
            ),
            QAItem(
                "Why did the deed have moral value?",
                f"The deed showed {scenario.value}: {hero.label} protected a neighbor instead of caring only about {scenario.reward}.",
            ),
            QAItem(
                "What changed at the end?",
                f"The danger was made safe, the prize was shared, and {scenario.image} showed that trust had returned.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a reflex?",
                "A reflex is a quick response to a sudden event. It can be helpful, but good judgment should guide what happens next.",
            ),
            QAItem(
                "What makes suspense?",
                "Suspense comes from uncertainty and risk. Readers wonder what will happen and whether someone will act in time.",
            ),
            QAItem(
                "What is a moral value?",
                "A moral value is a principle that helps guide good choices, such as kindness, courage, patience, or honesty.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("danger", "value", "resolved", "outcome"):
        if key in world.facts:
            lines.append(f"  fact.{key}={world.facts[key]}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "suspense"),
            asp.fact("feature", "moral_value"),
            asp.fact("feature", "reflex"),
            asp.fact("style", "fable"),
            asp.fact("safety", "neighbor_protected"),
            asp.fact("ending", "repair_and_sharing"),
        ]
    )


ASP_RULES = """
valid_story :-
    feature(suspense),
    feature(moral_value),
    feature(reflex),
    style(fable),
    safety(neighbor_protected),
    ending(repair_and_sharing).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the reflex fable.")
        return 1
    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip() or "reflex" not in sample.story.lower():
            print("Mismatch: generated story failed reflex verification.")
            return 1
    print("OK: ASP and Python accepted the reflex suspense fable.")
    return 0


CURATED = [
    StoryParams("the old orchard", "Mara", "hive", 0, 0),
    StoryParams("the reed bridge", "Tillo", "stone", 1, 1),
    StoryParams("the moonlit millpond", "Suri", "lantern", 2, 2),
    StoryParams("the hill path", "Bram", "branch", 3, 3),
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
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base + offset)
            params = resolve_params(args, rng)
            params.seed = base + offset
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
