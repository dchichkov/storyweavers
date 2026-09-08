#!/usr/bin/env python3
"""
A small humorous space-adventure storyworld about a careful surgery aboard a
starship, where an annoying alarm helps a crew discover the real problem.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    ship: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Luna"
    medic_name: str = "Dr. Vega"
    robot_name: str = "Bloop"
    ship: str = "the Starling"
    planet: str = "Jupiter's moon Europa"


CAPTAIN_NAMES = ["Luna", "Mira", "Nova", "Sol"]
MEDIC_NAMES = ["Dr. Vega", "Dr. Quill", "Dr. Orbit", "Dr. Comet"]
ROBOT_NAMES = ["Bloop", "Tock", "Noodle", "Beep"]
SHIPS = ["the Starling", "the Comet Finch", "the Silver Rocket", "the Moon Moth"]
PLANETS = ["Jupiter's moon Europa", "Mars", "the blue planet Neptune", "a tiny moon called Pebble"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a humorous space adventure about surgery and an annoying alarm."
    )
    parser.add_argument("--captain-name")
    parser.add_argument("--medic-name")
    parser.add_argument("--robot-name")
    parser.add_argument("--ship")
    parser.add_argument("--planet")
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
        seed=args.seed,
        captain_name=args.captain_name or rng.choice(CAPTAIN_NAMES),
        medic_name=args.medic_name or rng.choice(MEDIC_NAMES),
        robot_name=args.robot_name or rng.choice(ROBOT_NAMES),
        ship=args.ship or rng.choice(SHIPS),
        planet=args.planet or rng.choice(PLANETS),
    )


def make_world(params: StoryParams) -> World:
    world = World(params.ship)
    captain = world.add(Entity(
        "captain", "character", "human", params.captain_name,
        meters={"calm": 0.8}, memes={"responsibility": 1.0, "humor": 0.5},
    ))
    medic = world.add(Entity(
        "medic", "character", "doctor", params.medic_name,
        meters={"precision": 1.0}, memes={"confidence": 0.8, "humor": 0.4},
    ))
    robot = world.add(Entity(
        "robot", "character", "robot", params.robot_name,
        meters={"battery": 0.9, "alarm_volume": 1.0}, memes={"embarrassment": 0.0, "humor": 0.9},
    ))
    patient = world.add(Entity(
        "patient", "character", "space_penguin", "the space penguin",
        meters={"breathing": 0.5, "comfort": 0.3}, memes={"worry": 0.8, "relief": 0.0},
    ))
    tool = world.add(Entity(
        "tool", "thing", "surgical_tool", "the moon-shaped surgical tool",
        meters={"clean": 1.0, "sharpness": 0.9}, memes={},
    ))
    alarm = world.add(Entity(
        "alarm", "thing", "alarm", "the squeaky alarm",
        meters={"volume": 1.0, "annoyance": 1.0}, memes={"urgency": 0.8},
    ))
    world.facts.update(
        captain=captain,
        medic=medic,
        robot=robot,
        patient=patient,
        tool=tool,
        alarm=alarm,
        surgery_needed=True,
        alarm_annoying=True,
        surgery_complete=False,
    )
    return world


ADVENTURES = [
    {
        "title": "The Squeak in the Nebula",
        "problem": "a tiny crystal was stuck beneath the penguin's left flipper",
        "alarm": "a high-pitched squeak that sounded like a mouse arguing with a trumpet",
        "procedure": "remove the crystal with the moon-shaped tool",
        "cause": "a loose spring inside its emergency hatch",
        "repair": "tightened the spring and gave the hatch a polite warning label",
        "ending": "the penguin waddled beneath the stars wearing a tiny bandage like a heroic sash",
        "joke": "If the alarm squeaks again, I shall prescribe it a nap.",
    },
    {
        "title": "The Wiggle-Wobble Operation",
        "problem": "a jellybean-sized meteor pebble was lodged in the penguin's boot",
        "alarm": "a ridiculous wobble-whistle that made every spoon float in circles",
        "procedure": "slide out the pebble and wrap the sore foot in a soft space sock",
        "cause": "the robot had accidentally balanced its alarm on a vibrating lunch tray",
        "repair": "moved the alarm to a steady shelf and apologized to the spoons",
        "ending": "the healed penguin danced while the spoons finally returned to the soup",
        "joke": "That was not a medical emergency. That was lunch trying to escape.",
    },
    {
        "title": "Operation Moon Moustache",
        "problem": "a silver seed from the ship's salad garden was tickling the penguin's nose",
        "alarm": "a repeated beep-beep that sounded exactly like a duck learning Morse code",
        "procedure": "carefully lift out the seed during a gentle surgery",
        "cause": "a button had become stuck under the robot's elbow panel",
        "repair": "unstuck the button and taught the robot to keep elbows away from emergencies",
        "ending": "the penguin sneezed once, smiled, and sailed home with a silver seedling",
        "joke": "The patient is cured. The duck is still learning Morse code.",
    },
]


def tell(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random((params.seed or 0) ^ 0xA51CE)

    adventure = rng.choice(ADVENTURES)
    captain = world.get("captain")
    medic = world.get("medic")
    robot = world.get("robot")
    patient = world.get("patient")
    tool = world.get("tool")
    alarm = world.get("alarm")

    world.facts.update(
        title=adventure["title"],
        problem=adventure["problem"],
        alarm_description=adventure["alarm"],
        procedure=adventure["procedure"],
        cause=adventure["cause"],
        repair=adventure["repair"],
        ending=adventure["ending"],
        joke=adventure["joke"],
        planet=params.planet,
    )

    world.say(
        f"Captain {captain.label} piloted {world.ship} toward {params.planet}, "
        f"where the crew was delivering supplies to a floating research station."
    )
    world.say(
        f"Then {patient.label} waddled into the medical bay because {adventure['problem']}."
    )
    world.say(
        f"Dr. {medic.label.removeprefix('Dr. ')} examined the patient and said, "
        f"\"A careful surgery should fix this. We will be gentle, quick, and very clean.\""
    )
    world.para()

    world.say(
        f"Just as {medic.label} prepared the {tool.label}, {robot.label}'s alarm began making "
        f"{adventure['alarm']}."
    )
    world.say(
        f"Captain {captain.label} covered one ear. \"That alarm is trying to annoy the whole galaxy!\""
    )
    world.say(
        f"{robot.label} blinked. \"I am not trying to annoy anyone. I am succeeding by accident.\""
    )
    world.say(
        f"The noise made the surgical lamp wobble, so {captain.label} ordered everyone to pause."
    )
    world.para()

    world.say(
        f"Instead of guessing, {captain.label} followed the sound while {medic.label} kept "
        f"the patient warm and still."
    )
    world.say(
        f"They discovered that the alarm was not warning about the surgery at all. "
        f"It was ringing because {adventure['cause']}."
    )
    world.say(
        f"\"Aha!\" said {medic.label}. \"The annoying clue has helped us find the real problem.\""
    )
    world.say(
        f"{robot.label} lowered its metal head. \"I meant to be useful. I did not mean to become a musical sandwich.\""
    )
    world.para()

    world.say(
        f"Captain {captain.label} steadied the lamp while {medic.label} performed the surgery "
        f"to {adventure['procedure']}."
    )
    world.say(
        f"The operation went smoothly. {patient.label} gave a happy little chirp, and the alarm "
        f"went quiet after the crew {adventure['repair']}."
    )
    world.say(
        f"\"How do you feel?\" asked {captain.label}. \"Much better,\" said {patient.label}. "
        f"\"And the alarm?\" \"Also much better,\" replied {robot.label}. \"It has stopped singing.\""
    )
    world.para()

    world.say(
        f"{adventure['joke']} said {medic.label}, and everyone laughed, even the robot's blinking lights."
    )
    world.say(
        f"With the surgery complete and the ship peaceful again, {adventure['ending']}."
    )

    patient.meters["breathing"] = 1.0
    patient.meters["comfort"] = 1.0
    patient.memes["worry"] = 0.0
    patient.memes["relief"] = 1.0
    alarm.meters["annoyance"] = 0.0
    alarm.meters["volume"] = 0.1
    robot.memes["embarrassment"] = 0.2
    world.facts["surgery_complete"] = True
    world.facts["alarm_repaired"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a humorous Space Adventure about surgery for a space penguin with {f['alarm_description']}.",
        f"Tell a child-friendly story in which an annoying alarm helps a crew discover {f['cause']}, then complete a careful surgery.",
        f"Write a short space story featuring Captain {world.get('captain').label}, Dr. {world.get('medic').label.removeprefix('Dr. ')}, and a robot who accidentally annoys everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = world.get("captain").label
    medic = world.get("medic").label
    robot = world.get("robot").label
    patient = world.get("patient").label

    return [
        QAItem(
            question=f"What surgery did {medic} perform?",
            answer=f"{medic} performed a careful surgery to {f['procedure']}.",
        ),
        QAItem(
            question=f"How did {robot} annoy the crew?",
            answer=f"{robot} made {f['alarm_description']}, which disturbed the surgical lamp and the crew.",
        ),
        QAItem(
            question="What did the crew discover about the alarm?",
            answer=f"They discovered that the alarm was ringing because {f['cause']}.",
        ),
        QAItem(
            question=f"How did {captain} help during the operation?",
            answer=f"{captain} followed the alarm to find the real problem and then steadied the lamp while the surgery was performed.",
        ),
        QAItem(
            question=f"How did {patient} feel at the end?",
            answer=f"{patient} felt better after the surgery, and the ending showed the patient happily waddling away with a tiny bandage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is surgery?",
            answer="Surgery is careful medical work that repairs or removes a problem inside or on a body.",
        ),
        QAItem(
            question="What does annoy mean?",
            answer="Annoy means to bother someone or make them feel irritated.",
        ),
        QAItem(
            question="Why can an alarm be useful?",
            answer="An alarm can warn people about danger or point them toward a problem that needs attention.",
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
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        lines.append(
            f"  {entity.id:8} ({entity.type:14}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  surgery_complete={world.facts.get('surgery_complete')}")
    lines.append(f"  alarm_repaired={world.facts.get('alarm_repaired')}")
    return "\n".join(lines)


ASP_RULES = r"""
surgery_needed(patient).
alarm_annoying(alarm).
problem_found(alarm) :- alarm_annoying(alarm), surgery_needed(patient).
surgery_safe(patient) :- problem_found(alarm), surgery_needed(patient).
mission_successful :- surgery_safe(patient), not unresolved_alarm.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join([
        asp.fact("surgery_needed", "patient"),
        asp.fact("alarm_annoying", "alarm"),
        asp.fact("problem_found", "alarm"),
        asp.fact("surgery_safe", "patient"),
    ])


def asp_program(show: str = "#show mission_successful/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show surgery_safe/1. #show mission_successful/0."))
    names = {symbol.name for symbol in model}
    expected = {"surgery_safe", "mission_successful"}
    if expected.issubset(names):
        print("OK: ASP gate matches the Python surgery resolution.")
        return 0
    print("MISMATCH between ASP and Python resolution.")
    print("  got:", sorted(names))
    print("  expected to include:", sorted(expected))
    return 1


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
    StoryParams(
        seed=11,
        captain_name="Luna",
        medic_name="Dr. Vega",
        robot_name="Bloop",
        ship="the Starling",
        planet="Jupiter's moon Europa",
    ),
    StoryParams(
        seed=22,
        captain_name="Mira",
        medic_name="Dr. Quill",
        robot_name="Tock",
        ship="the Silver Rocket",
        planet="Mars",
    ),
    StoryParams(
        seed=33,
        captain_name="Nova",
        medic_name="Dr. Orbit",
        robot_name="Noodle",
        ship="the Moon Moth",
        planet="a tiny moon called Pebble",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surgery_safe/1. #show mission_successful/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show surgery_safe/1. #show mission_successful/0."))
        print("ASP atoms:")
        for symbol in model:
            print(symbol)
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
