#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, a stubborn alarm, a surprising twist,
and reconciliation between two young heroes.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    partner_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    argument: int = 0
    twist: int = 0
    reconciliation: int = 0


SETTINGS = {
    "rooftop": Setting("the rooftop rescue station", {"bacon", "alarm"}),
    "firehouse": Setting("the bright firehouse kitchen", {"bacon", "alarm"}),
    "skybridge": Setting("the city's glass skybridge", {"alarm", "signal"}),
}

HERO_NAMES = ["Luna", "Nova", "Maya", "Zara", "Pia", "Rin"]
PARTNER_NAMES = ["Bolt", "Echo", "Sunny", "Comet", "Atlas", "Skye"]

OPENINGS = [
    "At sunrise, {hero} watched over {place} with her silver cape snapping in the wind.",
    "The city was waking when {hero}, the young superhero, checked the rescue station at {place}.",
    "High above the streets, {hero} and her teammate {partner} began their morning patrol at {place}.",
    "A warm breakfast smell floated through {place} as superhero {hero} prepared for the day's first rescue.",
]

INCIDENTS = [
    {
        "clue": "the emergency alarm began chirping beside a tray of crisp bacon",
        "problem": "remove the noisy alarm before it woke every sleeping neighbor",
        "wrong": "the alarm's red button was flashing like a tiny villain's eye",
        "twist": "the alarm was not broken at all; a strip of bacon had slipped across its heat sensor",
        "repair": "They lifted the bacon with tongs, wiped the sensor, and carried the breakfast tray away from the control panel.",
        "ending": "The alarm fell silent, and the rescued bacon sizzled safely on a clean plate.",
        "lesson": "a loud problem can have a small cause",
    },
    {
        "clue": "a bacon basket rolled toward the launch lever while the warning bell rang",
        "problem": "remove the basket before the rescue rocket blasted off by mistake",
        "wrong": "the basket seemed to be charging like a runaway robot",
        "twist": "a loose apron string was pulling the basket downhill, not a robot at all",
        "repair": "They stopped the basket with a padded shield, tied the apron, and moved the food to a steady table.",
        "ending": "The rocket stayed parked while the bacon basket rested under a cheerful yellow cloth.",
        "lesson": "looking closely can turn a frightening guess into a helpful plan",
    },
    {
        "clue": "a smoky smell curled from the breakfast room while the city siren flashed",
        "problem": "remove the bacon pan from the hot plate",
        "wrong": "the heroes thought a shadow creature had invaded the kitchen",
        "twist": "the shadow was only steam making the hanging cape look enormous",
        "repair": "They opened the window, switched off the hot plate, and used a mitt to move the pan.",
        "ending": "Fresh air filled the room, and the bacon cooled beside a bowl of fruit.",
        "lesson": "calm teamwork helps when shadows make a small danger seem huge",
    },
    {
        "clue": "a silver beacon blinked whenever someone reached for the bacon",
        "problem": "remove the beacon from the snack shelf",
        "wrong": "each hero suspected the other had secretly activated a villain tracker",
        "twist": "the beacon was a forgotten training tag stuck beneath the tray",
        "repair": "They peeled off the tag, checked its harmless training label, and returned it to the equipment box.",
        "ending": "The shelf blinked no more, and both heroes shared the bacon after washing their hands.",
        "lesson": "blame can hide the simple truth from good friends",
    },
]

ARGUMENTS = [
    '"I can remove it faster," {hero} said. "You always rush," {partner} replied.',
    '"Stand back and let me handle this," {hero} said. "{partner} answered, "We both need to understand the danger first."',
    '"You moved the tray without asking!" {hero} cried. "{partner} lowered their eyes. "I thought I was helping."',
    '"The alarm is your fault," {hero} said. "{partner} shook their head. "Let us find out before we choose a culprit."',
]

TWISTS = [
    "Then {partner} noticed a greasy mark beneath the sensor.",
    "Just before {hero} pulled the lever, {partner} spotted a loose string near the wheels.",
    "A cool breeze cleared the steam, and the frightening shadow shrank to the size of a cape.",
    "The blinking light reflected on the tray, revealing a small training tag underneath.",
]

RECONCILIATIONS = [
    '"I am sorry I blamed you," {hero} said. "{partner} smiled. "I am sorry I acted without telling you. Next time, we check together."',
    '"Your careful clue saved us," {hero} said. "{partner} replied, "Your brave hands made the repair safe. We are stronger as a team."',
    '"I should have listened before I shouted," {hero} admitted. "{partner} answered, "And I should have explained before I moved anything."',
    '"Friends do not have to guess alone," {hero} said. "{partner} nodded. "We can ask, listen, and help each other."',
]


ASP_RULES = r"""
#show valid/2.
setting(rooftop). setting(firehouse). setting(skybridge).
affords(rooftop,bacon). affords(rooftop,alarm).
affords(firehouse,bacon). affords(firehouse,alarm).
affords(skybridge,alarm). affords(skybridge,signal).
valid(P,A) :- affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", name, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    left = set(asp_valid())
    right = set(python_valid())
    if left == right:
        print(f"OK: clingo gate matches python gate ({len(left)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(left - right))
    print("  only in python:", sorted(right - left))
    return 1


def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = StoryState(setting)
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    hero = world.add(Entity(
        params.hero_name,
        kind="character",
        type="superhero",
        label=params.hero_name,
        memes={"courage": 1.0, "frustration": 0.0},
    ))
    partner = world.add(Entity(
        params.partner_name,
        kind="character",
        type="superhero",
        label=params.partner_name,
        memes={"courage": 1.0, "trust": 1.0},
    ))
    bacon = world.add(Entity(
        "bacon",
        type="food",
        label="bacon",
        owner="rescue_station",
        meters={"temperature": 0.7},
    ))
    alarm = world.add(Entity(
        "alarm",
        type="device",
        label="emergency alarm",
        meters={"noise": 0.8},
    ))

    place = setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        hero=hero.label, partner=partner.label, place=place
    ))
    world.say(f"Then {incident['clue']}.")
    world.say(f'{hero.label} decided to {incident["problem"]}.')
    world.say(ARGUMENTS[params.argument % len(ARGUMENTS)].format(
        hero=hero.label, partner=partner.label
    ))

    world.para()
    world.say(
        f"The two heroes froze. The alarm grew louder, and {hero.label}'s "
        "frustration made the emergency feel bigger."
    )
    world.say(TWISTS[params.twist % len(TWISTS)].format(
        hero=hero.label, partner=partner.label
    ))
    world.say(f'"Wait," said {partner.label}. "The clue changes what we should do."')
    world.say(f'"You are right," said {hero.label}. "Let us solve it together."')
    world.say(incident["twist"])
    world.say(incident["repair"])

    world.para()
    world.say(RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)].format(
        hero=hero.label, partner=partner.label
    ))
    world.say(
        f"Together, {hero.label} and {partner.label} checked the station, "
        "because a superhero team protects people by sharing what it knows."
    )
    world.say(incident["ending"])
    world.say(
        f"The city brightened below them, and {hero.label} and {partner.label} "
        "stood side by side, ready for the next call."
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        bacon=bacon,
        alarm=alarm,
        place=place,
        incident=incident,
        reconciled=True,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    return [
        f"Write a superhero story about {hero.label} and {partner.label} trying to {incident['problem']}.",
        f"Tell a child-friendly story with bacon, a surprising twist, dialogue, and reconciliation.",
        f"Write a story set at {world.facts['place']} where two heroes solve a noisy problem by listening to each other.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    hero = f["hero"].label
    partner = f["partner"].label
    return [
        QAItem(
            f"Who were the two superheroes?",
            f"The superheroes were {hero} and {partner}. They worked together after realizing that cooperation made the repair safer.",
        ),
        QAItem(
            f"What did {hero} first want to do?",
            f"{hero} wanted to {incident['problem']}. The heroes paused when they realized they needed more information.",
        ),
        QAItem(
            "What was the twist in the problem?",
            f"The twist was that {incident['twist']}. The ordinary cause changed the heroes' plan.",
        ),
        QAItem(
            "How did the heroes reconcile?",
            f"They apologized for blaming or rushing, listened to each other, and agreed to check clues together before acting.",
        ),
        QAItem(
            "What happened to the bacon at the end?",
            f"{incident['ending']} The bacon was kept safely away from the emergency equipment.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "Why should food be kept away from emergency equipment?",
            "Food should be kept away from emergency equipment so crumbs, grease, heat, or spills do not interfere with important safety devices.",
        ),
        QAItem(
            "What does reconciliation mean?",
            "Reconciliation means repairing a disagreement by listening, apologizing when needed, and finding a peaceful way to move forward.",
        ),
        QAItem(
            "Why is teamwork useful for superheroes?",
            "Teamwork is useful because people can share observations, balance one another's strengths, and make safer decisions together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    hero = args.name or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice(PARTNER_NAMES)
    if hero == partner:
        raise StoryError("The superhero and partner must have different names.")
    return StoryParams(
        place=place,
        hero_name=hero,
        partner_name=partner,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        argument=rng.randrange(len(ARGUMENTS)),
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld with bacon, a twist, and reconciliation."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--partner")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:\n")
        for place, item in asp_valid():
            print(f"  {place:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name=f"{place.title()}Hero",
                partner_name=f"{place.title()}Partner",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n) and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
