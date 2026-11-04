#!/usr/bin/env python3
"""
A small animal-story world set in a picnic meadow. A careless picnic ends badly
when a hungry animal scatters the food, but a kind response helps everyone
make amends.

Seed tale:
---
Tuvwxy the young fox smelled a picnic in the meadow and crept toward it.
When the picnic basket tipped and the food tumbled into the grass, the
picnickers were ready to send him away. One child noticed his empty bowl and
offered to help clean up. Together they gathered what was still clean, shared
some berries, and made a safer place for Tuvwxy to rest. The picnic ended
early, but it ended with a new friend.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _add_repo_root() -> None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "storyworlds" / "results.py").is_file():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Could not find storyworlds/results.py")


_add_repo_root()
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Setting:
    place: str
    affords: set[str]


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str = "picnic_meadow"
    child_name: str = "Mina"
    animal_name: str = "Tuvwxy"
    incident: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "picnic_meadow": Setting(
        place="the picnic meadow",
        affords={"picnic", "grass", "wild_berries"},
    ),
}

CHILD_NAMES = ["Mina", "Leo", "Nora", "Sam", "Ivy", "Ollie"]
ANIMAL_NAMES = ["Tuvwxy", "Pip", "Clover", "Nib", "Fern"]

INCIDENTS = [
    {
        "animal": "a young fox",
        "sign": "a rustle came from behind the picnic basket",
        "cause": "Tuvwxy had nosed the basket while looking for a bite",
        "mess": "the basket tipped, and sandwiches and napkins tumbled into the grass",
        "bad": "the picnic had to end early because the food was scattered",
        "kind": "offer a few clean berries and help gather the things that had not touched the ground",
        "repair": "They packed the clean food away and set a little bowl of water near the meadow's edge.",
        "ending": "The empty blanket fluttered in the breeze, while Tuvwxy rested safely beside a bowl of water.",
    },
    {
        "animal": "a round little rabbit",
        "sign": "a soft thump sounded beside the picnic blanket",
        "cause": "Tuvwxy had startled a rabbit while chasing a fallen apple",
        "mess": "the rabbit darted under the blanket and knocked over a cup of juice",
        "bad": "the juice soaked the blanket, and everyone had to stop eating",
        "kind": "give the frightened rabbit room and help blot the juice with a spare cloth",
        "repair": "They moved the food to a dry patch and left a quiet gap for the rabbit to hop away.",
        "ending": "The damp blanket dried in the sun, and the rabbit nibbled clover at a comfortable distance.",
    },
    {
        "animal": "a small, hungry fox",
        "sign": "a shadow slipped past the basket and vanished into the tall grass",
        "cause": "Tuvwxy had pulled at the picnic cloth while sniffing for food",
        "mess": "the cloth slid off the basket and dropped the clean plates into the grass",
        "bad": "the plates were too dirty to use, so the picnic dishes had to be packed away",
        "kind": "speak gently, then help brush off the plates and offer food only from their own lunch",
        "repair": "They washed the plates at home and left a little water outside, away from the food.",
        "ending": "The picnic was over, but the fox watched calmly from the meadow's edge as the family walked home.",
    },
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
setting(picnic_meadow).
affords(picnic_meadow,picnic).
affords(picnic_meadow,grass).
affords(picnic_meadow,wild_berries).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", place, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((place, affordance) for place, setting in SETTINGS.items()
                  for affordance in setting.affords)


def asp_valid() -> list[tuple]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        asp_result = set(asp_valid())
    except ImportError as exc:
        print(f"Cannot verify ASP rules because clingo is unavailable: {exc}")
        return 1
    py_result = set(python_valid())
    if asp_result != py_result:
        print("ASP/Python gate mismatch.")
        print("Only in ASP:", sorted(asp_result - py_result))
        print("Only in Python:", sorted(py_result - asp_result))
        return 1
    print(f"OK: ASP gate matches Python gate ({len(py_result)} combinations).")
    for i in range(len(INCIDENTS)):
        sample = generate(StoryParams(incident=i))
        if not sample.story or not sample.story_qa:
            print(f"Generated-story check failed for incident {i}.")
            return 1
        if "?" in sample.story:
            print(f"Unexpected unresolved text in incident {i}.")
            return 1
    print(f"OK: all {len(INCIDENTS)} incident stories generated.")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place {params.place!r}; choose picnic_meadow.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError(f"Incident must be between 0 and {len(INCIDENTS) - 1}.")
    if not params.child_name.strip() or not params.animal_name.strip():
        raise StoryError("Character names must not be empty.")

    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident]
    world = StoryState(setting=setting)
    child = world.add(Entity(
        params.child_name, "character", "child", params.child_name,
        meters={"kindness": 0.2, "picnic_order": 1.0},
        memes={"patience": 0.5, "care": 0.3},
    ))
    animal = world.add(Entity(
        params.animal_name, "animal", "fox", incident["animal"],
        meters={"hunger": 0.8, "distance_from_people": 0.7},
        memes={"worry": 0.7, "trust": 0.1},
    ))
    basket = world.add(Entity(
        "picnic basket", "thing", "basket", "the picnic basket",
        meters={"upright": 1.0, "food_clean": 1.0},
        owner=child.id,
    ))

    world.say(
        f"On a sunny afternoon, {child.id} spread a picnic blanket in "
        f"{setting.place}. Nearby, {animal.id}, {incident['animal']}, "
        f"was hungry and unsure whether it was safe to come closer."
    )
    world.say(f"Then {incident['sign']}. {incident['cause'].capitalize()}.")
    world.say(f"In a moment, {incident['mess']}.")
    world.facts.update(
        child=child, animal=animal, basket=basket, incident=incident,
        place=setting.place, bad_ending=incident["bad"],
    )
    child.meters["picnic_order"] = 0.0
    basket.meters["upright"] = 0.0
    basket.meters["food_clean"] = 0.3
    animal.meters["distance_from_people"] = 0.5
    world.say(f"It was a bad ending for the picnic: {incident['bad']}.")
    world.para()

    world.say(
        f'{child.id} frowned. "I wanted our picnic to last longer," '
        f'{child.id} said. "But Tuvwxy looks hungry," a friend replied.'
    )
    world.say(
        f'"We can be kind and still keep our food safe," {child.id} said. '
        f"They chose to {incident['kind']}."
    )
    child.memes["care"] = 1.0
    child.meters["kindness"] = 1.0
    animal.memes["trust"] = 0.8
    animal.meters["hunger"] = 0.4
    animal.meters["distance_from_people"] = 1.0
    world.say(incident["repair"])
    world.say(
        f'Tuvwxy blinked and settled at the meadow’s edge. "Thank you for '
        f'giving me space," seemed to say the fox. {child.id} smiled: '
        f'"Next time, we will keep the basket closed."'
    )
    world.para()
    world.say(
        f"The picnic could not be put back the way it was, but {child.id} "
        f"had made a kinder choice after things went wrong."
    )
    world.say(incident["ending"])
    world.facts["resolution"] = "The picnic ended early, and the animal was treated kindly."
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story set in {f['place']} about a picnic that goes wrong.",
        f"Include {f['animal'].id}, a bad ending for the picnic, and a child's kind response.",
        "Let a brief conversation change what the characters decide to do.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    child = f["child"].id
    return [
        QAItem(
            question="Where did the picnic take place?",
            answer=f"The picnic took place in {f['place']}, where {child} spread out a blanket.",
        ),
        QAItem(
            question="What went wrong at the picnic?",
            answer=f"{incident['mess'].capitalize()}. As a result, {incident['bad']}.",
        ),
        QAItem(
            question=f"How did {child} show kindness?",
            answer=f"{child} chose to {incident['kind']}. That helped without making the animal come closer than it wanted.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The picnic ended early, but the animal was safe and treated kindly. {incident['ending']}",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="Why should people keep picnic food covered?",
            answer="Keeping picnic food covered helps protect it from dirt and from animals that may be attracted by its smell.",
        ),
        QAItem(
            question="How can someone be kind to a wild animal?",
            answer="Someone can stay calm, give a wild animal space, and avoid feeding it by hand or trying to touch it.",
        ),
        QAItem(
            question="What is a meadow?",
            answer="A meadow is an open area of grass and wild plants where animals may find shelter and food.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, type={entity.type}, "
            f"meters={entity.meters}, memes={entity.memes}, owner={entity.owner}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "picnic_meadow"
    if place not in SETTINGS:
        raise StoryError(f"Unknown place {place!r}; choose picnic_meadow.")
    child_name = args.name or rng.choice(CHILD_NAMES)
    animal_name = args.animal or rng.choice(ANIMAL_NAMES)
    if child_name == animal_name:
        animal_name = next(name for name in ANIMAL_NAMES if name != child_name)
    return StoryParams(
        place=place,
        child_name=child_name,
        animal_name=animal_name,
        incident=rng.randrange(len(INCIDENTS)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal story world about a picnic meadow, a bad ending, and kindness."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name", help="Name of the child at the picnic.")
    parser.add_argument("--animal", help="Name of the visiting animal.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            model = asp_valid()
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print(f"{len(model)} valid place-and-affordance combinations:")
        for place, affordance in model:
            print(f"  {place}: {affordance}")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(StoryParams(incident=i, child_name=CHILD_NAMES[i],
                                 animal_name=ANIMAL_NAMES[i], seed=seed))
            for i in range(len(INCIDENTS))
        ]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(seed + i)
            params = resolve_params(args, rng)
            params.seed = seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
