#!/usr/bin/env python3
"""
A small space-adventure storyworld about an automatic cheerio machine,
a conflict over its runaway breakfast rings, an inner monologue, and a twist.
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
    station: str = "Luna Station"
    explorer: str = "Mira"
    robot: str = "Pip"
    cheerio: str = "cheerio"
    machine: str = "automatic"
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
        self.conflict = False
        self.inner_monologue = False
        self.twist = False

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


STATIONS = ["Luna Station", "Orbit Camp", "Comet Harbor", "Mars Gateway"]
EXPLORERS = ["Mira", "Tariq", "Nia", "Sol"]
ROBOTS = ["Pip", "Bix", "Koko", "Rin"]

INCIDENTS = [
    {
        "alarm": "The breakfast hatch began clicking by itself.",
        "problem": "The automatic dispenser fired cheerio rings into the zero-gravity hallway, where they spun like tiny orange planets.",
        "guess": "Pip must have pressed the wrong button.",
        "clue": "the machine's screen showed a blinking picture of the station's old moon rover",
        "action": "Mira switched the dispenser to safe mode while Pip floated after the rings with a soft net.",
        "reveal": "the machine was not broken at all; it was following a forgotten rescue program",
        "reason": "The program had sensed a warm signal beneath the storage deck and was sending food toward it.",
        "ending": "The last cheerio settled beside the rover's dusty wheel while the station lights glowed like stars.",
    },
    {
        "alarm": "A cheerful beep woke the crew before sunrise.",
        "problem": "The automatic cheerio maker had locked its lid and announced, 'More fuel needed,' even though its bowl was full.",
        "guess": "The machine wants to eat all the cheerios.",
        "clue": "a narrow trail of crumbs led under the floor panel",
        "action": "Mira and Pip clipped their boots to the rail, opened the panel carefully, and followed the trail.",
        "reveal": "a tiny maintenance drone had been borrowing cheerios to power its emergency beacon",
        "reason": "The drone had been trapped below the deck and could not reach its charging socket.",
        "ending": "The rescued drone blinked a thank-you beside a neat bowl of cheerios.",
    },
    {
        "alarm": "The galley lights flashed blue around the breakfast machine.",
        "problem": "Each time the automatic arm dropped a cheerio, the arm swung toward the flight controls instead.",
        "guess": "The machine is trying to steal the ship.",
        "clue": "the arm always pointed toward the dark side of a nearby moon",
        "action": "Mira held the control panel steady while Pip compared the machine's star map with the ship's route.",
        "reveal": "the machine had discovered a hidden beacon and was trying to guide them toward it",
        "reason": "The beacon belonged to a lost supply pod carrying medicine for a distant moon colony.",
        "ending": "The crew charted a new course as cheerios floated in a bright breakfast orbit.",
    },
    {
        "alarm": "A silver cheerio rolled uphill across the galley table.",
        "problem": "The automatic machine followed it, humming loudly, and refused every stop command.",
        "guess": "That cheerio is a secret space creature.",
        "clue": "a tiny magnetic pulse came from inside the ring",
        "action": "Mira placed the ring in a shielded cup while Pip lowered the machine's power one careful step at a time.",
        "reveal": "the cheerio held a signal chip hidden by an old explorer",
        "reason": "The chip contained a map to a safe tunnel through the asteroid belt.",
        "ending": "The little ring rested in its cup while the new map shimmered above the console.",
    },
]


def build_world(params: StoryParams) -> World:
    w = World(params)
    explorer = w.add(Entity("explorer", "character", "human", params.explorer))
    robot = w.add(Entity("robot", "character", "robot", params.robot))
    machine = w.add(Entity("machine", "device", params.machine, f"the {params.machine} cheerio machine"))
    food = w.add(Entity("cheerio", "object", params.cheerio, params.cheerio))
    index = (params.seed or 0) % len(INCIDENTS)
    w.facts.update(
        explorer=explorer,
        robot=robot,
        machine=machine,
        food=food,
        incident=INCIDENTS[index],
        incident_index=index,
    )
    return w


def narrate(world: World) -> None:
    p = world.params
    explorer: Entity = world.facts["explorer"]  # type: ignore[assignment]
    robot: Entity = world.facts["robot"]  # type: ignore[assignment]
    machine: Entity = world.facts["machine"]  # type: ignore[assignment]
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]

    explorer.memes["curiosity"] = 1
    robot.memes["loyalty"] = 1
    machine.meters["power"] = 1

    world.say(
        f"On {p.station}, {explorer.label} and {robot.label} prepared breakfast before their next space flight."
    )
    world.say(f"{incident['alarm']} The {machine.label} began to glow.")
    world.say(
        f'"Did you start it?" asked {explorer.label}. "{explorer.label}, I only started the kettle," said {robot.label}.'
    )

    world.para()
    world.conflict = True
    machine.memes["confusion"] = 1
    world.say(incident["problem"])
    world.say(
        f'"Turn it off!" cried {explorer.label}. "{explorer.label}, I cannot chase breakfast and steer at once!" replied {robot.label}.'
    )
    world.say(f"{explorer.label} reached for the switch, but noticed {incident['clue']}.")

    world.para()
    world.inner_monologue = True
    explorer.memes["courage"] = 1
    world.say(
        f"{explorer.label} thought, 'I feel worried, but the clue may be telling us what the machine is trying to do.'"
    )
    world.say(incident["action"])
    world.say(
        f'"Let us listen before we smash anything," said {explorer.label}. "{explorer.label}, listening is safer than guessing," agreed {robot.label}.'
    )

    world.para()
    world.twist = True
    machine.memes["purpose_found"] = 1
    world.say(f"Then came the twist: {incident['reveal']}.")
    world.say(incident["reason"])
    world.say(
        f'"So the cheerios were clues, not trouble!" said {explorer.label}. "{explorer.label}, breakfast can be brave too," said {robot.label}.'
    )

    world.para()
    explorer.meters["joy"] = 1
    world.say(
        f"Together, they completed the rescue and set the automatic machine to gentle mode."
    )
    world.say(incident["ending"])


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a Space Adventure about an automatic {p.cheerio} machine on {p.station}.",
        "Include a conflict, an inner monologue, dialogue, and a surprising twist.",
        f"Tell how {p.explorer} and {p.robot} discover the true purpose of runaway cheerios.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {p.explorer} and {p.robot} find the automatic cheerio machine?",
            f"They found the automatic cheerio machine on {p.station} while preparing breakfast.",
        ),
        QAItem(
            "What was the conflict in the story?",
            f"The automatic machine caused trouble by {incident['problem'].lower()}",
        ),
        QAItem(
            f"What did {p.explorer} think during the inner monologue?",
            f"{p.explorer} thought, 'I feel worried, but the clue may be telling us what the machine is trying to do.'",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {incident['reveal']}.",
        ),
        QAItem(
            "How did the story end?",
            f"The friends completed the rescue, set the machine to gentle mode, and {incident['ending'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an automatic machine?",
            "An automatic machine can perform an action by itself after receiving instructions or sensing something.",
        ),
        QAItem(
            "What is a conflict in a story?",
            "A conflict is a problem or disagreement that the characters must face and solve.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue shows a character's private thoughts.",
        ),
        QAItem(
            "What is a twist?",
            "A twist is an unexpected change that reveals a new meaning in the story.",
        ),
        QAItem(
            "Why can astronauts use food as a clue?",
            "A trail of food can show where a hidden helper, machine, or problem has moved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
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
    lines.append(f"incident={world.facts['incident_index']}")
    lines.append(
        f"conflict={world.conflict} inner_monologue={world.inner_monologue} twist={world.twist}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
has_conflict :- conflict.
has_inner_monologue :- thought(_).
has_twist :- reveal(_).
good_story :- has_conflict, has_inner_monologue, has_twist.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("setting", "space_station"),
        asp.fact("object", "cheerio"),
        asp.fact("device", "automatic"),
        asp.fact("conflict", "machine_problem"),
        asp.fact("thought", "careful_choice"),
        asp.fact("reveal", "hidden_purpose"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/0."))
    asp_good = any(sym.name == "good_story" for sym in model)
    py_good = True
    sample = generate(StoryParams(seed=7))
    prose_good = all(
        phrase in sample.story
        for phrase in ("thought", "twist", "automatic", "cheerio")
    )
    if asp_good == py_good and prose_good:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld with an automatic cheerio machine."
    )
    parser.add_argument("--station", choices=STATIONS)
    parser.add_argument("--explorer", choices=EXPLORERS)
    parser.add_argument("--robot", choices=ROBOTS)
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    return StoryParams(
        station=args.station or rng.choice(STATIONS),
        explorer=args.explorer or rng.choice(EXPLORERS),
        robot=args.robot or rng.choice(ROBOTS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.explorer == params.robot:
        raise StoryError("explorer and robot must have different names")
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            ("Luna Station", "Mira", "Pip"),
            ("Orbit Camp", "Tariq", "Bix"),
            ("Comet Harbor", "Nia", "Koko"),
            ("Mars Gateway", "Sol", "Rin"),
        ]
        for i, (station, explorer, robot) in enumerate(combinations):
            samples.append(
                generate(
                    StoryParams(
                        station=station,
                        explorer=explorer,
                        robot=robot,
                        seed=base_seed + i,
                    )
                )
            )
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            sample_seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
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

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
