#!/usr/bin/env python3
"""
lopsided_cut_gerund_pharmacy_boat_ramp_dialogue.py
===================================================

A small Superhero Story world about a lopsided boat ramp, a careful cut,
and a pharmacy delivery saved by honest dialogue.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    name: str
    danger: str
    gerund: str
    reward: str


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
    "boat_ramp": Setting(place="the boat ramp", affords={"delivery"}),
}

MISSIONS = {
    "delivery": Mission(
        id="delivery",
        name="pharmacy delivery",
        danger="a storm has tilted the floating dock",
        gerund="crossing the ramp",
        reward="a bright rescue badge",
    ),
}

HERO_NAMES = ["Luna", "Mara", "Pia", "Nell", "Zara"]
HELPER_NAMES = ["Theo", "Sam", "Ivy", "Owen", "Bea"]
POWERS = ["steady hands", "bright signal", "wind listening", "rope strength"]
SCENARIOS = [
    {
        "id": "medicine_crate",
        "problem": "A lopsided cart carrying a pharmacy crate leaned toward the water.",
        "mistake": "grabbed the handle and pulled before checking the loose wheel",
        "clue": "a fresh cut in the rope beside the wheel",
        "repair": "cut the tangled rope neatly, wedged the wheel with a dry block, and asked the boat keeper to guide the cart",
        "ending": "the pharmacy crate rested safely in the boat while the repaired cart stood square on the ramp",
        "lesson": "a hero does not rush past a small danger when someone needs help",
    },
    {
        "id": "rainy_ramp",
        "problem": "Rain made the boat ramp slippery, and a pharmacy bag waited on the far dock.",
        "mistake": "ran down the ramp without telling the waiting helper",
        "clue": "one plank lifting higher than the others",
        "repair": "stopped, used a rope line, and crossed beside the helper one careful step at a time",
        "ending": "the medicine arrived under a dry jacket while rain tapped softly on the steady planks",
        "lesson": "clear words can be as powerful as a flying leap",
    },
    {
        "id": "lost_label",
        "problem": "A gust blew the pharmacy label from a small box near the boat ramp.",
        "mistake": "guessed which box belonged to the sick sailor",
        "clue": "the lopsided box had a blue mark hidden under its flap",
        "repair": "read the mark with the pharmacist over the radio and carried the right box across",
        "ending": "the sailor received the marked medicine, and the empty box became a tiny boat for a toy duck",
        "lesson": "asking before acting protects the people a hero serves",
    },
]

OPENINGS = [
    "{hero} arrived at the boat ramp wearing a red scarf and a promise to help.",
    "At sunrise, {hero}, the young hero with {power}, saw trouble gathering beside the boat ramp.",
    "The harbor bell rang once as {hero} hurried toward the boat ramp for a rescue mission.",
    "Everyone at the boat ramp knew {hero} could be brave, but today the rescue needed careful thinking.",
]

DIALOGUES = [
    '"Stop and look with me," {helper} said. "The ramp is telling us what is wrong."',
    '"I can help," {helper} called. "Tell me your plan before you pull."',
    '"The pharmacy box matters more than being fast," {helper} said. "Let us make it safe."',
    '"Use your words, hero," {helper} reminded. "Then we can use the rope."',
]

ADMISSIONS = [
    '"I rushed," {hero} admitted. "I should have listened first."',
    '"That was my mistake," {hero} said. "I will repair it carefully."',
    '{hero} took a breath. "I wanted to look strong, but helping means asking."',
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mission) for place, setting in SETTINGS.items() for mission in setting.affords]


ASP_RULES = r"""
place(boat_ramp).
affords(boat_ramp,delivery).
mission(delivery).
valid(Place,Mission) :- place(Place), affords(Place,Mission), mission(Mission).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for mission in sorted(setting.affords):
            lines.append(asp.fact("affords", place, mission))
    for mission in MISSIONS:
        lines.append(asp.fact("mission", mission))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


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


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    helper: str
    power: str
    scenario: str
    seed: Optional[int] = None
    telling: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero Story world at a boat ramp.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--power", choices=POWERS)
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
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.mission is None or combo[1] == args.mission
    ]
    if not combos:
        raise StoryError("No valid boat-ramp mission matches the requested options.")
    place, mission = rng.choice(combos)
    return StoryParams(
        place=place,
        mission=mission,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        power=args.power or rng.choice(POWERS),
        scenario=rng.choice(SCENARIOS)["id"],
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(params.name, "character", "child hero", memes={"courage": 1}))
    helper = world.add(Entity(params.helper, "character", "helper", memes={"trust": 1}))
    crate = world.add(Entity("crate", "thing", "pharmacy crate", meters={"safety": 0}))
    mission = MISSIONS[params.mission]
    rng = random.Random(params.telling)
    scenario = next(item for item in SCENARIOS if item["id"] == params.scenario)
    values = {
        "hero": hero.id,
        "helper": helper.id,
        "power": params.power,
    }

    opening = rng.choice(OPENINGS).format(**values)
    dialogue = rng.choice(DIALOGUES).format(**values)
    admission = rng.choice(ADMISSIONS).format(**values)
    turn = rng.choice([
        "The clue changed the rescue from a race into a plan.",
        f"{hero.id} realized that courage meant noticing what others might miss.",
        "For one quiet moment, the strongest power was listening.",
    ])
    final_thought = rng.choice([
        f"{hero.id} understood that a real hero protects people before pride.",
        f"{hero.id} learned that careful teamwork can steady a very lopsided problem.",
        f"{hero.id} discovered that dialogue turns fear into a shared plan.",
    ])

    world.say(opening)
    world.say(f"The mission was a {mission.name}: {mission.danger}.")
    world.para()
    world.say(scenario["problem"])
    world.say(f"In a hurry, {hero.id} {scenario['mistake']}.")
    world.say(dialogue)
    world.say(f"Then they noticed {scenario['clue']}. {turn}")
    world.say(admission)
    world.para()
    world.say(f"Together, {hero.id} {scenario['repair']}.")
    world.say(
        f"The helper nodded. \"That is the kind of rescue I trust,\" {helper.id} said. "
        f"{hero.id} kept one hand on the rope and one eye on the {mission.gerund}."
    )
    world.say(f"The pharmacy delivery reached the waiting sailor before the storm grew loud.")
    world.say(f"{final_thought} {scenario['lesson'].capitalize()}.")
    world.say(f"At the end, {scenario['ending']}.")

    hero.meters["care"] = 2
    hero.meters["danger_avoided"] = 1
    hero.memes["listening"] = 1
    hero.memes["teamwork"] = 1
    helper.memes["trust"] = 2
    crate.meters["safety"] = 1

    world.facts = {
        "hero": hero,
        "helper": helper,
        "mission": mission,
        "scenario": scenario,
        "mistake": scenario["mistake"],
        "clue": scenario["clue"],
        "repair": scenario["repair"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
        "reconciled": True,
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
    return [
        "Write a child-friendly Superhero Story set at a boat ramp.",
        "Include a lopsided danger, a cut, a pharmacy delivery, and meaningful dialogue.",
        "Show a hero changing from rushing to careful teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            f"Where did {hero.id}'s rescue happen?",
            f"The rescue happened at the boat ramp, where {hero.id} and {helper.id} worked beside the water.",
        ),
        QAItem(
            f"What problem did {hero.id} face?",
            f"{facts['scenario']['problem']} The problem threatened the pharmacy delivery.",
        ),
        QAItem(
            f"What clue helped {hero.id}?",
            f"The clue was {facts['clue']}. It showed {hero.id} that rushing would make the rescue less safe.",
        ),
        QAItem(
            f"How did {hero.id} solve the problem?",
            f"{hero.id} {facts['repair']}. The repair protected the medicine and made teamwork possible.",
        ),
        QAItem(
            f"What did {hero.id} learn?",
            f"{hero.id} learned that {facts['lesson']}. The ending showed this change because {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a lopsided object?", "A lopsided object leans or is uneven instead of being balanced."),
        QAItem("What is a pharmacy?", "A pharmacy is a place where medicines are prepared or provided."),
        QAItem("What is a boat ramp?", "A boat ramp is a sloping surface used to move boats into or out of the water."),
        QAItem("Why can a cut be useful?", "A careful cut can remove a tangled material, but it should be made safely and with help when needed."),
        QAItem("What is dialogue?", "Dialogue is spoken conversation between characters."),
        QAItem("What makes someone a hero?", "A hero notices danger, helps others, and chooses brave, caring actions."),
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: {entity.type} meters={meters} memes={memes}")
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
    StoryParams("boat_ramp", "delivery", "Luna", "Theo", "steady hands", "medicine_crate", telling=101),
    StoryParams("boat_ramp", "delivery", "Mara", "Ivy", "bright signal", "rainy_ramp", telling=202),
    StoryParams("boat_ramp", "delivery", "Pia", "Sam", "wind listening", "lost_label", telling=303),
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
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(20, args.n * 20):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
