#!/usr/bin/env python3
"""
caution_overalls_mystery_to_solve_cautionary_bedtime.py

A gentle bedtime mystery about caution, overalls, and listening before acting.
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


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_label: str
    clue: str
    danger: str
    safe_method: str
    reveal: str
    lesson: str


@dataclass
class World:
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


SETTINGS = {
    "bedroom": Setting("the moonlit bedroom", {"mystery"}),
    "cottage": Setting("the quiet cottage", {"mystery"}),
    "attic": Setting("the sleepy attic", {"mystery"}),
}

MYSTERIES = {
    "blue_button": Mystery(
        "blue_button",
        "a missing blue button",
        "a tiny thread shining beneath the rocking chair",
        "a loose floorboard that creaked beside the dark stairs",
        "use a lamp, stay low, and ask an adult to check the floor",
        "the button had slipped from a pocket and rolled beneath the chair",
        "caution helps a curious mind find the truth without making a new danger",
    ),
    "whispering_box": Mystery(
        "whispering_box",
        "a box that seemed to whisper",
        "a ribbon trembling whenever the window breeze passed",
        "the high window latch was open above a stack of wobbly books",
        "keep both feet on the floor and close the latch with a grown-up",
        "the box held a wind-up bird whose beak tapped the lid",
        "a mystery becomes clearer when we investigate safely instead of rushing",
    ),
    "vanished_star": Mystery(
        "vanished_star",
        "a vanished paper star",
        "silver paper caught on the pocket of a pair of overalls",
        "a chair had been dragged beneath the shelf to reach the star",
        "ask for help and move the chair back before searching",
        "the star was tucked inside the overalls pocket after a bedtime craft",
        "caution means checking what is near our feet before reaching for what is high",
    ),
}

NAMES = ["Luna", "Mira", "Nell", "Toby", "Ari"]
HELPERS = ["Mama", "Papa", "Grandma", "Grandpa"]
COLORS = ["blue", "green", "yellow", "red"]
TRAITS = ["curious", "thoughtful", "patient", "sleepy"]

OPENINGS = [
    "When the moon climbed over the roof, {hero} put on {color} overalls for one last bedtime check.",
    "The house grew quiet, but {hero}, a {trait} child, was still awake in {setting}.",
    "Under the soft lamp, {hero} smoothed {hero_poss} overalls and noticed something strange.",
    "Just before bedtime, {hero} heard a small sound in {setting} and sat up carefully.",
]

ASP_RULES = r"""
setting(bedroom).
setting(cottage).
setting(attic).
affords(bedroom,mystery).
affords(cottage,mystery).
affords(attic,mystery).
mystery(blue_button).
mystery(whispering_box).
mystery(vanished_star).
valid(S,M) :- setting(S), affords(S,mystery), mystery(M).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (setting, mystery)
        for setting, data in SETTINGS.items()
        for mystery in MYSTERIES
        if "mystery" in data.affords
    ]


def asp_facts() -> str:
    import asp

    lines = []
    for setting, data in SETTINGS.items():
        lines.append(asp.fact("setting", setting))
        for feature in sorted(data.affords):
            lines.append(asp.fact("affords", setting, feature))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP:")
    print("  only in Python:", sorted(py - clingo))
    print("  only in ASP:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary bedtime mystery about overalls."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--trait", choices=TRAITS)
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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    helper: str
    color: str
    trait: str
    seed: Optional[int] = None
    telling: int = 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo for combo in valid_combos()
        if args.setting is None or combo[0] == args.setting
        if args.mystery is None or combo[1] == args.mystery
    ]
    if not choices:
        raise StoryError("No safe bedtime mystery matches those choices.")
    setting, mystery = rng.choice(choices)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    color = args.color or rng.choice(COLORS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        name=name,
        helper=helper,
        color=color,
        trait=trait,
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(params.name, type="child", label=params.name))
    helper = world.add(Entity(params.helper, type="adult", label=params.helper))
    overalls = world.add(Entity("overalls", kind="thing", type="clothing", label=f"{params.color} overalls"))

    rng = random.Random(params.telling)
    hero_poss = "her" if params.name in {"Luna", "Mira", "Nell"} else "his"
    opening = rng.choice(OPENINGS).format(
        hero=params.name,
        trait=params.trait,
        setting=setting.place,
        color=params.color,
        hero_poss=hero_poss,
    )
    dialogue = rng.choice([
        f'"I hear it too," said {params.helper}. "We can look, but we will use caution."',
        f'"Should I climb up?" asked {params.name}. "No," said {params.helper}. "A safe mystery needs a safe plan."',
        f'"I want to know the answer," whispered {params.name}. "Then let us begin with our feet on the floor," replied {params.helper}.',
        f'"The clue is small," said {params.helper}. "Small clues still deserve careful eyes."',
    ])
    thought = rng.choice([
        f"{params.name} wanted to hurry, but the word caution felt warm and steady.",
        f"The mystery was exciting, yet {params.name} remembered that bedtime bravery includes knowing when to wait.",
        f"{params.name} took one slow breath and chose a careful question instead of a quick reach.",
    ])
    ending = rng.choice([
        f"Then {params.name} climbed into bed, with the {params.color} overalls folded neatly beside the moonlit pillow.",
        f"When the lamp went out, the {params.color} overalls rested on their peg, and the room felt peaceful again.",
        f"The mystery was solved, the dangerous chair was back in place, and the {params.color} overalls slept quietly until morning.",
    ])

    hero.memes["curiosity"] = 1
    world.say(opening)
    world.say(
        f"Something was wrong: {mystery.object_label} was not where it belonged, "
        f"and the room held its breath."
    )
    world.para()
    world.say(f"{params.name} searched too quickly and nearly faced {mystery.danger}.")
    world.say(dialogue)
    world.say(thought)
    world.para()
    world.say(f"Together they noticed {mystery.clue}.")
    world.say(
        f"{params.helper} helped {params.name} {mystery.safe_method}, "
        f"so the search stayed gentle and safe."
    )
    world.say(
        f"At last they discovered that {mystery.reveal}. "
        f"The mystery had an ordinary answer hiding inside an exciting question."
    )
    world.para()
    world.say(
        f"{params.name} smiled at {params.helper}. "
        f'"Thank you for helping me slow down," {params.name} said.'
    )
    world.say(
        f'"Caution is not being afraid," {params.helper} answered. '
        f'"It is caring enough to look wisely."'
    )
    world.say(f"{params.name} learned that {mystery.lesson}.")
    world.say(ending)

    hero.memes.update({"caution": 1, "relief": 1, "understanding": 1})
    helper.memes["care"] = 1
    overalls.memes["resting"] = 1
    world.facts = {
        "hero": hero,
        "helper": helper,
        "overalls": overalls,
        "mystery": mystery,
        "setting": setting,
        "clue": mystery.clue,
        "danger": mystery.danger,
        "method": mystery.safe_method,
        "reveal": mystery.reveal,
        "lesson": mystery.lesson,
        "ending": ending,
        "solved": True,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle cautionary bedtime story with a mystery to solve.",
        f"Tell a bedtime story about {f['hero'].id}, overalls, and a safe mystery in {f['setting'].place}.",
        "Show a child changing a risky choice into a careful one through dialogue and action.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    mystery = f["mystery"]
    return [
        QAItem(
            f"Where did {hero}'s mystery happen?",
            f"The mystery happened in {f['setting'].place}, where {hero} was getting ready for bed.",
        ),
        QAItem(
            f"What was {hero} trying to solve?",
            f"{hero} was trying to solve the mystery of {mystery.object_label}.",
        ),
        QAItem(
            f"What clue helped {hero}?",
            f"The clue was {f['clue']}. It guided {hero} toward the truth.",
        ),
        QAItem(
            f"How did {helper} help {hero} stay safe?",
            f"{helper} helped {hero} {f['method']}. This let them investigate without creating a new danger.",
        ),
        QAItem(
            f"What did {hero} learn?",
            f"{hero} learned that {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does caution mean?",
            "Caution means taking care, noticing risks, and choosing a safe way to act.",
        ),
        QAItem(
            "What are overalls?",
            "Overalls are clothing with a bib and straps that cover part of the body and are worn over a shirt.",
        ),
        QAItem(
            "What is a mystery?",
            "A mystery is something not yet understood that people investigate to discover an answer.",
        ),
        QAItem(
            "What is a bedtime story?",
            "A bedtime story is a gentle story read or told before sleep.",
        ),
        QAItem(
            "What does cautionary mean?",
            "Cautionary means giving a warning or lesson about making safe and thoughtful choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}".rstrip())
    lines.append(f"mystery_solved={world.facts.get('solved', False)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("bedroom", "blue_button", "Luna", "Mama", "blue", "curious", telling=101),
    StoryParams("cottage", "whispering_box", "Mira", "Grandpa", "green", "thoughtful", telling=202),
    StoryParams("attic", "vanished_star", "Toby", "Papa", "yellow", "patient", telling=303),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} compatible combos:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
