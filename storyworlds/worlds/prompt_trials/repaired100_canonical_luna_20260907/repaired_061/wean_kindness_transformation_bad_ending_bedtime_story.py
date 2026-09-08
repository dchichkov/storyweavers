#!/usr/bin/env python3
"""
A gentle bedtime storyworld about weaning a little moon moth from a harmful
habit. Kindness brings a transformation, but a bad ending reminds everyone
that care must continue after the first success.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "moonlit bedroom"
    child: str = "Luna"
    helper: str = "Mira"
    habit: str = "night bottle"
    comfort: str = "silver cup of warm water"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.kindness_shown = False
        self.transformed = False
        self.bad_ending = False

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


PLACES = ["moonlit bedroom", "little cottage", "quiet nursery", "house beside the pond"]
CHILDREN = ["Luna", "Nora", "Pip", "Suri"]
HELPERS = ["Mira", "Grandma", "Theo", "Aunt Rose"]
HABITS = ["night bottle", "late-night pacifier", "sugary bedtime drink"]
COMFORTS = ["silver cup of warm water", "soft moon pillow", "warm sip of milk"]


def build_world(params: StoryParams) -> World:
    if params.child == params.helper:
        raise StoryError("the child and helper must have different names")
    if params.habit not in HABITS:
        raise StoryError("habit must be one of the registered bedtime habits")
    if params.comfort not in COMFORTS:
        raise StoryError("comfort must be one of the registered gentle comforts")

    world = World(params)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=params.child,
        meters={"sleepiness": 0.2, "steadiness": 0.3},
        memes={"worry": 0.6, "trust": 0.5},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="caregiver",
        label=params.helper,
        meters={"patience": 1.0},
        memes={"kindness": 1.0},
    ))
    habit = world.add(Entity(
        id="habit",
        kind="thing",
        type="old_comfort",
        label=params.habit,
        meters={"availability": 1.0},
        memes={"pull": 1.0},
    ))
    comfort = world.add(Entity(
        id="comfort",
        kind="thing",
        type="new_comfort",
        label=params.comfort,
        meters={"warmth": 0.8},
        memes={"safety": 0.8},
    ))
    world.facts.update(child=child, helper=helper, habit=habit, comfort=comfort)
    return world


def narrate(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    habit: Entity = world.facts["habit"]  # type: ignore[assignment]
    comfort: Entity = world.facts["comfort"]  # type: ignore[assignment]

    world.say(
        f"At bedtime, {child.label} curled beneath a quilt in the {p.place}. "
        f"{child.label} still reached for a {habit.label} whenever the room grew dark."
    )
    world.say(
        f'"I am ready to wean from it, but I feel wobbly," said {child.label}. '
        f'"You do not have to hurry alone," replied {helper.label}. "We can try one small change together."'
    )
    world.events.append("the child asked for help")
    world.para()

    world.kindness_shown = True
    helper.memes["kindness"] = 1.0
    child.memes["trust"] = 0.9
    child.meters["steadiness"] = 0.5
    world.say(
        f"{helper.label} listened without scolding. They put the {habit.label} on a high shelf "
        f"and placed a {comfort.label} beside the bed."
    )
    world.say(
        f'"If I miss the old way, may I call you?" asked {child.label}. '
        f'"Yes," said {helper.label}, holding a hand. "A kind plan can change when you need it."'
    )
    world.events.append("kindness made the change feel safe")
    world.para()

    world.transformed = True
    child.meters["steadiness"] = 0.9
    child.memes["worry"] = 0.2
    habit.meters["availability"] = 0.0
    comfort.memes["safety"] = 1.0
    world.say(
        f"For three quiet nights, {child.label} practiced the new bedtime rhythm. "
        f"Warm water, a story, and three slow breaths helped the old reaching grow smaller."
    )
    world.say(
        f"On the fourth night, {child.label} smiled and said, "
        f'"I can fall asleep without the {habit.label}." {helper.label} smiled too, '
        f"because the child had transformed a frightened wish into a brave choice."
    )
    world.events.append("the child slept with the new comfort")
    world.para()

    world.bad_ending = True
    child.meters["steadiness"] = 0.45
    child.memes["worry"] = 0.7
    world.say(
        f"But the next evening, {helper.label} became busy and left the {habit.label} within reach. "
        f"When {child.label} woke, tired and lonely, the old comfort called from the chair."
    )
    world.say(
        f"{child.label} used it again and felt sad when morning came. "
        f'"I thought I had changed forever," whispered {child.label}. '
        f'"One hard night does not erase your work," said {helper.label}. '
        f'"Tomorrow we will make the kind plan safer."'
    )
    world.events.append("an unplanned return caused a bad ending")
    world.say(
        f"The night did not end perfectly. Still, {helper.label} moved the {habit.label} away, "
        f"held {child.label} close, and left the {comfort.label} glowing softly by the bed. "
        f"The moon watched over them while they began again."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a bedtime story about {p.child} learning to wean from a {p.habit}.",
        f"Show kindness and transformation, but give the story a bad ending that leaves room to try again.",
        f"Include gentle dialogue between {p.child} and {p.helper} about replacing an old comfort with a new one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    habit: Entity = world.facts["habit"]  # type: ignore[assignment]
    comfort: Entity = world.facts["comfort"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {child.label} talk with {helper.label} at bedtime?",
            answer=f"{child.label} wanted to wean from the {habit.label} but felt unsure and asked {helper.label} for help.",
        ),
        QAItem(
            question=f"How did {helper.label} show kindness?",
            answer=f"{helper.label} listened without scolding, made a small plan, and offered the {comfort.label} as a gentle replacement.",
        ),
        QAItem(
            question=f"What transformation happened to {child.label}?",
            answer=f"{child.label} learned to sleep for several nights without the {habit.label}, using warm water, a story, and slow breaths instead.",
        ),
        QAItem(
            question=f"Why did the story have a bad ending?",
            answer=f"The {habit.label} was left within reach, and when {child.label} woke tired and lonely, the child used it again.",
        ),
        QAItem(
            question="What hopeful idea remained at the end?",
            answer=f"{helper.label} explained that one hard night did not erase {child.label}'s work, so they could make the kind plan safer and begin again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to wean?",
            answer="To wean means to gently move away from a familiar feeding or comfort habit and learn a new way.",
        ),
        QAItem(
            question="What is kindness in a bedtime story?",
            answer="Kindness means listening, helping without shame, and giving someone patient support.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change in how a character feels, thinks, or acts.",
        ),
        QAItem(
            question="Can a bad ending still leave hope?",
            answer="Yes. A bad ending can show a setback while leaving the characters with care, learning, and a chance to try again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"kindness={world.kindness_shown} transformation={world.transformed} "
        f"bad_ending={world.bad_ending}"
    )
    lines.append("events=" + " | ".join(world.events))
    return "\n".join(lines)


ASP_RULES = r"""
character(child).
character(helper).
habit(old_comfort).
comfort(new_comfort).
kindness :- listened, gentle_plan.
transformation :- slept_without_habit, learned_new_rhythm.
bad_ending :- habit_returned, setback.
good_story :- kindness, transformation, bad_ending.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("character", "child"),
            asp.fact("character", "helper"),
            asp.fact("habit", "old_comfort"),
            asp.fact("comfort", "new_comfort"),
            asp.fact("listened"),
            asp.fact("gentle_plan"),
            asp.fact("slept_without_habit"),
            asp.fact("learned_new_rhythm"),
            asp.fact("habit_returned"),
            asp.fact("setback"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show kindness/0.\n#show transformation/0.\n#show bad_ending/0."))
    names = {symbol.name for symbol in model}
    expected = {"kindness", "transformation", "bad_ending"}
    if names == expected:
        print("OK: ASP and Python parity verified.")
        return 0
    print(f"MISMATCH between ASP and Python: expected {sorted(expected)}, got {sorted(names)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about weaning, kindness, transformation, and a bad ending."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--habit", choices=HABITS)
    parser.add_argument("--comfort", choices=COMFORTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    if child == helper:
        helper = rng.choice([name for name in HELPERS if name != child])
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        child=child,
        helper=helper,
        habit=args.habit or rng.choice(HABITS),
        comfort=args.comfort or rng.choice(COMFORTS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
        print(asp_program("#show kindness/0.\n#show transformation/0.\n#show bad_ending/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show kindness/0.\n#show transformation/0.\n#show bad_ending/0."))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            StoryParams(
                place=PLACES[i % len(PLACES)],
                child=CHILDREN[i % len(CHILDREN)],
                helper=HELPERS[i % len(HELPERS)],
                habit=HABITS[i % len(HABITS)],
                comfort=COMFORTS[i % len(COMFORTS)],
                seed=base_seed + i,
            )
            for i in range(4)
        ]
        samples = [generate(params) for params in combinations]
    else:
        seen: set[str] = set()
        for index in range(args.n):
            sample_seed = base_seed + index
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
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
