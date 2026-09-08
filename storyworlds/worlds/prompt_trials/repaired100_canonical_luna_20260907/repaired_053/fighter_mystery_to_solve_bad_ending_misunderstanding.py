#!/usr/bin/env python3
"""
A small space-adventure storyworld about a fighter, a mystery, a bad first
ending, and a misunderstanding repaired through careful teamwork.

Seed word: fighter
Features: Mystery to Solve, Bad Ending, Misunderstanding
Style: Space Adventure
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


FIGHTER_NAMES = ["Comet", "Swiftwing", "Blue Finch", "Arrow", "Starling", "Nova Kite"]
PILOT_NAMES = ["Luna", "Mara", "Tavi", "Orin", "Sela", "Pax"]
HELPER_NAMES = ["Miko", "Juno", "Rin", "Bex", "Toma", "Iri"]
SPACE_PLACES = [
    "the Moon's silver repair dock",
    "the quiet orbit above Mars",
    "the Lantern Asteroid Belt",
    "the blue side of Saturn",
    "the station beside a sleeping comet",
]
MYSTERIES = [
    {
        "object": "the navigation beacon",
        "problem": "its green guide light vanished before the fleet could return",
        "guess": "Luna had flown the fighter too close and damaged the beacon",
        "clue": "the beacon's outer shell was cold, but a trail of warm dust led toward the cargo ring",
        "truth": "a loose cargo panel had covered the beacon's sensor",
        "failed": "restarting the beacon made its light blink once and then disappear again",
        "repair": "they secured the cargo panel, brushed the sensor clean, and tested the beacon from three safe distances",
        "ending": "the green beacon shone across the dark, guiding every little ship home",
        "safe": "the returning fleet",
    },
    {
        "object": "the moon-map capsule",
        "problem": "it sent a warning that the landing moon had moved",
        "guess": "Luna had entered the wrong orbit in the fighter",
        "clue": "the stars matched the map, but a bright metal reflection covered one corner of its lens",
        "truth": "a silver tool had slipped across the capsule's camera",
        "failed": "turning the capsule upside down made the warning grow louder",
        "repair": "they removed the tool with a magnet, wiped the lens, and compared the map with the lookout's star chart",
        "ending": "the moon-map settled into a steady picture of the safe landing place",
        "safe": "the landing route",
    },
    {
        "object": "the rescue signal",
        "problem": "it pointed toward an empty patch of space",
        "guess": "Luna had chased the fighter's shadow and pressed the wrong signal key",
        "clue": "the signal grew strong whenever the station's old dish turned toward the engine room",
        "truth": "a loose wire was sending the rescue call through the wrong antenna",
        "failed": "pressing the signal key again sent three confusing arrows in different directions",
        "repair": "they switched off the dish, traced the wire, and connected the rescue call to the bright outer antenna",
        "ending": "a clear red signal reached the lost shuttle, and its tiny lights answered",
        "safe": "the lost shuttle",
    },
    {
        "object": "the star-sample case",
        "problem": "it looked empty after the fighter returned from a crystal moon",
        "guess": "Luna had dropped the sample while showing off a fast turn",
        "clue": "the case was locked, yet blue sparkles floated inside its double wall",
        "truth": "the sample had slipped into the case's hidden safety pocket",
        "failed": "shaking the case made the sparkles swirl but did not open the pocket",
        "repair": "they read the tiny safety mark, opened the pocket gently, and placed the sample in a padded tube",
        "ending": "the star sample glowed safely while the science team cheered behind the window",
        "safe": "the moon crystal",
    },
]

OPENINGS = [
    "Luna's fighter hummed above the stars while the little space fleet prepared to travel home.",
    "Beyond the station windows, planets shone like marbles in a velvet sky.",
    "The night shift had just begun when a strange warning flashed across the control screen.",
    "Luna loved her small fighter, but even a brave pilot could meet a puzzling problem in space.",
    "At the edge of the quiet orbit, the station lights blinked in a careful golden line.",
    "A mystery waited among the stars, and it began with one light behaving in a very odd way.",
]

DIALOGUE = [
    '"You caused this trouble," said Miko. "Your fighter was the last ship near it."',
    'Miko pointed at the screen. "I saw your fighter turn there. I thought that was the answer."',
    '"Please do not decide yet," Luna said. "A nearby ship is not proof."',
    'Luna took a breath. "Tell me exactly what you saw, and I will tell you what I know."',
    '"I was afraid the fleet would be lost," Miko admitted. "That made my guess feel certain."',
]

APOLOGIES = [
    '"I am sorry I blamed you before checking the clues," Miko said.',
    'Miko lowered the scanner. "I mistook a quick guess for the truth. Will you help me look again?"',
    '"You deserved a question, not an accusation," Miko said, joining the investigation.',
    'After hearing Luna explain, Miko apologized and offered to inspect the station beside her.',
]

LESSONS = [
    "They learned that a mystery needs patient questions, especially when fear makes one guess seem easy.",
    "The crew remembered that a nearby fighter is only a clue, not a reason to blame its pilot.",
    "A careful check repaired both the space equipment and the trust between the two friends.",
    "They discovered that the best way past a bad first ending is to stop, listen, and try again together.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "object"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    gravity: float = 0.2
    air: bool = True


@dataclass
class Mood:
    mystery: bool = True
    misunderstanding: bool = True
    repaired_trust: bool = False
    bad_ending_avoided: bool = False


@dataclass
class StoryParams:
    place: str
    fighter: str
    pilot_name: str
    helper_name: str
    mystery_index: int
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(line) for line in self.lines if line)


def tell(params: StoryParams) -> World:
    if params.mystery_index < 0 or params.mystery_index >= len(MYSTERIES):
        raise StoryError("mystery_index must select a known space mystery")
    if params.fighter.strip() == "":
        raise StoryError("fighter must have a name")
    if params.pilot_name == params.helper_name:
        raise StoryError("pilot and helper must have different names")

    world = World(Setting(params.place), Mood())
    fighter = world.add(
        Entity(
            id=params.fighter,
            kind="fighter",
            species="space fighter",
            label="small star fighter",
            owner=params.pilot_name,
            meters={"fuel": 0.72, "hull": 0.94},
            memes={"readiness": 1.0, "pride": 1.0},
        )
    )
    pilot = world.add(
        Entity(
            id=params.pilot_name,
            kind="character",
            species="pilot",
            label="careful pilot",
            memes={"hope": 1.0, "hurt": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            species="station helper",
            label="worried helper",
            memes={"fear": 1.0, "certainty": 1.0},
        )
    )
    mystery = MYSTERIES[params.mystery_index]

    rng_seed: object = params.seed
    if rng_seed is None:
        rng_seed = "|".join(
            [params.place, params.fighter, params.pilot_name, params.helper_name, str(params.mystery_index)]
        )
    rng = random.Random(rng_seed)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)
    apology = rng.choice(APOLOGIES)
    lesson = rng.choice(LESSONS)
    helper_tool = rng.choice(["a soft brush", "a magnetic wand", "a silver checklist", "a quiet scanner"])
    investigation = rng.choice(
        [
            "they followed the warm dust one careful step at a time",
            "they compared the station's old readings with the new ones",
            "they checked every panel before touching the controls",
            "they listened to the hum of each machine and marked what changed",
        ]
    )

    world.say(opening)
    world.say(
        f"From {params.place}, {params.fighter}, a nimble fighter piloted by {params.pilot_name}, watched the fleet's lights."
    )
    world.say(f"Then {mystery['object']} sent a strange warning: {mystery['problem']}.")
    world.para()
    world.say(dialogue)
    world.say(f"{params.helper_name} guessed that {mystery['guess']}.")
    world.say(
        f"The accusation hurt {params.pilot_name}, but the pilot answered, \"Let us solve the mystery before we choose someone to blame.\""
    )
    world.say(
        f"They tried one quick fix, but it led to a bad ending: {mystery['failed']} The fleet had to wait in a dark, chilly holding orbit."
    )
    world.para()
    world.say(
        f"That failure showed them that guessing was not enough. With {helper_tool}, {investigation}."
    )
    world.say(f"At last, they found the important clue: {mystery['clue']}.")
    world.say(f"The real answer was simple but hidden: {mystery['truth']}.")
    world.say(apology)
    world.say(
        f"{params.pilot_name} and {params.helper_name} worked side by side. They {mystery['repair']}."
    )
    world.say(
        f"The repaired system worked, and {mystery['safe']} was safe again. {mystery['ending']}."
    )
    world.say(lesson)

    fighter.meters.update(fuel=0.61, hull=0.94)
    fighter.memes.update(relief=1.0, teamwork=1.0)
    pilot.memes.update(hurt=0.0, trust=1.0, courage=1.0)
    helper.memes.update(fear=0.0, certainty=0.0, trust=1.0)
    world.mood.repaired_trust = True
    world.mood.bad_ending_avoided = True
    world.facts.update(
        fighter=fighter,
        pilot=pilot,
        helper=helper,
        mystery=mystery,
        tool=helper_tool,
        lesson=lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    fighter = world.facts["fighter"]
    return [
        f"Write a child-friendly space adventure featuring the fighter {fighter.id}.",
        "Include a mystery to solve, a misunderstanding, and a bad first attempt that is repaired.",
        f"Make the central problem concrete: {mystery['problem']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    pilot = world.facts["pilot"]
    helper = world.facts["helper"]
    fighter = world.facts["fighter"]
    mystery = world.facts["mystery"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Why did {helper.id} misunderstand what happened?",
            answer=f"{helper.id} saw {fighter.id} near the trouble and assumed that {mystery['guess']}. The guess was made before the station clues were checked.",
        ),
        QAItem(
            question=f"What bad ending happened after the first attempt?",
            answer=f"The first fix failed because {mystery['failed']} As a result, the fleet had to wait in a dark, chilly holding orbit.",
        ),
        QAItem(
            question=f"What clue helped {pilot.id} and {helper.id} solve the mystery?",
            answer=f"They noticed that {mystery['clue']}. This revealed that {mystery['truth']}.",
        ),
        QAItem(
            question="How did the space crew repair the problem?",
            answer=f"They used {tool} and worked together. {mystery['repair'].capitalize()}.",
        ),
        QAItem(
            question="What changed by the end of the adventure?",
            answer=f"{mystery['safe'].capitalize()} was safe again, and {mystery['ending']}. The pilot and helper also rebuilt their trust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fighter in a space adventure?",
            answer="A fighter is a small, quick spacecraft designed to move through space and protect or help a larger fleet.",
        ),
        QAItem(
            question="Why should a crew check clues before blaming someone?",
            answer="A nearby person or vehicle may only be part of the situation. Checking clues helps the crew find the real cause and avoid an unfair accusation.",
        ),
        QAItem(
            question="What does a beacon do?",
            answer="A beacon sends out a visible or electronic signal that helps spacecraft find a place or a safe route.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        owner = f" owner={entity.owner}" if entity.owner else ""
        lines.append(f"  {entity.id} ({entity.species}{owner}) {' '.join(parts)}")
    lines.append(
        f"  mood repaired_trust={world.mood.repaired_trust} bad_ending_avoided={world.mood.bad_ending_avoided}"
    )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space adventure world about a fighter, a mystery, and repaired trust."
    )
    parser.add_argument("--place", choices=SPACE_PLACES)
    parser.add_argument("--fighter", choices=FIGHTER_NAMES)
    parser.add_argument("--pilot", choices=PILOT_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--mystery", type=int, choices=range(len(MYSTERIES)))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(SPACE_PLACES)
    fighter = args.fighter or rng.choice(FIGHTER_NAMES)
    pilot = args.pilot or rng.choice(PILOT_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != pilot]
    helper = args.helper or rng.choice(helper_choices)
    if helper == pilot:
        raise StoryError("pilot and helper must have different names")
    mystery_index = args.mystery if args.mystery is not None else rng.randrange(len(MYSTERIES))
    return StoryParams(
        place=place,
        fighter=fighter,
        pilot_name=pilot,
        helper_name=helper,
        mystery_index=mystery_index,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    return "\n".join(
        [
            "domain(space_adventure).",
            "feature(mystery_to_solve).",
            "feature(bad_ending).",
            "feature(misunderstanding).",
            "vehicle(fighter).",
            "resolution(teamwork).",
            "resolution(repaired_trust).",
        ]
    )


ASP_RULES = r"""
valid_world :-
    domain(space_adventure),
    vehicle(fighter),
    feature(mystery_to_solve),
    feature(bad_ending),
    feature(misunderstanding),
    resolution(teamwork),
    resolution(repaired_trust).
#show valid_world/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_world/0."))
    values = set(asp.atoms(model, "valid_world"))
    expected = {()}
    if values != expected:
        print("MISMATCH:", values, expected)
        return 1

    rng = random.Random(274930118)
    for index in range(len(MYSTERIES)):
        params = StoryParams(
            place=SPACE_PLACES[index % len(SPACE_PLACES)],
            fighter=FIGHTER_NAMES[index],
            pilot_name=PILOT_NAMES[index],
            helper_name=HELPER_NAMES[index],
            mystery_index=index,
            seed=1000 + index,
        )
        sample = generate(params)
        if not sample.story or "mystery" not in sample.story.lower():
            print("MISMATCH: generated story missing mystery content")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story missing QA")
            return 1
        if sample.world is None or not sample.world.mood.bad_ending_avoided:
            print("MISMATCH: Python world did not repair bad ending")
            return 1
        rng.random()

    print("OK: ASP/Python parity and generated stories agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/0."))
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_world/0."))
        print("\n".join(str(atom) for atom in model))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(MYSTERIES)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.mystery_index = index
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1
        if len(samples) < args.n:
            raise StoryError("could not produce the requested number of distinct stories")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
