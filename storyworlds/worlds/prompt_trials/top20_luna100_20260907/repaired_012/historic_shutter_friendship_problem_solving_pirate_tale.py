#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str = "a historic harbor"
    friendship: float = 0.0
    problem_solved: bool = False
    shutter_open: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    seed: Optional[int] = None


NAMES = ["Mara", "Nell", "Finn", "Pip", "Rory", "Tess", "Jory", "Bram"]
SHIP_NAMES = ["The Brass Gull", "The Old Lantern", "The Shutter Star", "The Harbor Fox"]


ARCS = [
    {
        "key": "lighthouse_shutter",
        "premise": [
            "At dawn, Captain {captain} sailed {ship} toward an old lighthouse in the historic harbor. First mate {mate} carried a brass key while gulls cried above the deck.",
            "The pirate ship {ship} glided toward the harbor's historic lighthouse. Captain {captain} checked the chart, and {mate} polished the little brass key meant for the tower.",
        ],
        "problem": [
            "The lighthouse's heavy shutter had jammed closed, hiding the lamp from every ship at sea. A storm was coming, and the harbor needed its guiding light.",
            "A rusted shutter covered the historic lamp. Without it, boats could not see the safe channel through the rocks.",
        ],
        "conflict": [
            "\"Break the shutter with an axe,\" said {captain}. \"We might damage the old lighthouse,\" replied {mate}. Their friendship felt wobbly as the wind pushed harder.",
            "{captain} wanted to pull the shutter open at once, but {mate} wanted to study its hinges. Their disagreement delayed the work.",
        ],
        "turn": [
            "{mate} noticed a narrow trail of bright oil beneath one hinge. {captain} listened instead of arguing and found a tiny release pin hidden behind the frame.",
            "They paused beside the tower door. {mate} saw that the shutter was not locked; a sea-salt crust held one hinge fast.",
        ],
        "action": [
            "\"You found the clue,\" {captain} said. \"You have the steady hands,\" answered {mate}. Together they brushed away the salt, oiled the hinge, and lifted the release pin.",
            "{captain} held the shutter steady while {mate} cleaned the hinge with cloth and oil. Then they pulled together on the count of three.",
        ],
        "resolution": [
            "The historic shutter swung open, and the lamp shone across the darkening water. The pirates solved the problem without harming the old tower, and their friendship grew strong again.",
            "The lighthouse beam swept over the safe channel. {captain} thanked {mate} for careful thinking, and {mate} smiled because they had solved the problem together.",
        ],
        "ending": [
            "That night, the open shutter gleamed above the harbor while {ship} rested beneath a sky full of stars.",
            "The old lighthouse blinked warmly through its open shutter, and the two friends shared tea on the quiet deck.",
        ],
        "problem_fact": "a rusted historic shutter hid the lighthouse lamp",
        "clue_fact": "a salt crust and a hidden release pin explained why the shutter was stuck",
        "action_fact": "they cleaned the hinge and lifted the release pin together",
        "outcome_fact": "the lighthouse lamp shone safely across the harbor",
    },
    {
        "key": "museum_window",
        "premise": [
            "{captain} and {mate} brought {ship} to a historic island museum where an old pirate window displayed a silver compass.",
            "The pirate ship {ship} anchored beside a historic museum. Captain {captain} and friend {mate} had promised to return a compass before sunset.",
        ],
        "problem": [
            "A wooden shutter had fallen across the museum window, and the caretaker could not open it. The compass inside was needed to guide a rescue boat home.",
            "The window's old shutter was wedged tight by a fallen rope. Until it opened, the historic compass could not be seen from the bay.",
        ],
        "conflict": [
            "\"We should cut the rope,\" said {captain}. \"Let us lift it gently first,\" said {mate}. Their friendship trembled while the tide rose.",
            "{captain} pulled at the shutter, but {mate} warned that the ancient wood might crack. Neither pirate knew which plan was safer.",
        ],
        "turn": [
            "{mate} watched the rope bob with the tide and saw that it loosened every time a wave touched the dock. {captain} agreed to wait for the right moment.",
            "They spoke calmly and inspected the frame. A small wooden peg, not the rope, was pressing the shutter against the wall.",
        ],
        "action": [
            "On the next wave, {captain} lifted the rope while {mate} slid the peg free. The old shutter opened without a splinter.",
            "{captain} steadied the frame, and {mate} eased out the peg. Their careful teamwork freed the shutter.",
        ],
        "resolution": [
            "The silver compass flashed in the window and guided the rescue boat toward shore. The friends solved the problem by trusting each other's careful ideas.",
            "The caretaker cheered as the window opened. {captain} and {mate} felt proud that their friendship had protected the historic wood.",
        ],
        "ending": [
            "Moonlight rested on the open museum shutter, and the compass pointed toward two smiling friends.",
            "The old window stayed open to the sea breeze while {ship} sailed home beneath a silver moon.",
        ],
        "problem_fact": "a rope and peg jammed a historic museum shutter",
        "clue_fact": "careful watching revealed that the peg, not the rope, held the shutter shut",
        "action_fact": "they lifted the rope and removed the peg together",
        "outcome_fact": "the window opened and the compass guided a rescue boat",
    },
    {
        "key": "stormy_signal",
        "premise": [
            "Pirate captain {captain} steered {ship} toward a historic signal house with first mate {mate}. Its colored shutters once warned sailors about dangerous reefs.",
            "A historic signal house stood above the sea as {ship} approached. {captain} brought a crate of flags, while {mate} carried tools for the old shutters.",
        ],
        "problem": [
            "The red warning shutter was stuck open, making every ship think the reef was dangerous even though the safe channel had shifted.",
            "A storm had bent the signal shutter. It showed the wrong color and sent boats toward the long route around the island.",
        ],
        "conflict": [
            "\"Replace the whole shutter,\" said {captain}. \"First straighten the hinge,\" said {mate}. Their friendship felt strained as sailors waited below.",
            "{captain} wanted speed, but {mate} wanted to preserve the historic signal. Their argument made the repair stand still.",
        ],
        "turn": [
            "{mate} found a loose bronze washer beneath the hinge. {captain} realized the old shutter was sound; only its hinge needed support.",
            "When the wind paused, {captain} saw the shutter move slightly. {mate} understood that one bent hinge was catching on a nail.",
        ],
        "action": [
            "{captain} held the shutter against the wind while {mate} fitted the washer and bent the nail aside. Then they tested the signal together.",
            "{mate} braced the frame, and {captain} loosened the nail. The shutter swung to green, showing the safe channel.",
        ],
        "resolution": [
            "The green signal shone across the water, and the waiting boats chose the safe route. The friends had solved the problem while saving the historic signal.",
            "Sailors cheered from the bay. {captain} and {mate} apologized for arguing and celebrated their friendship beside the repaired shutter.",
        ],
        "ending": [
            "The historic signal house waved green above the reef while {ship} sailed through calm water.",
            "At sunset, the green shutter flashed like a friendly eye over the sea.",
        ],
        "problem_fact": "a bent historic signal shutter showed the wrong warning",
        "clue_fact": "a loose washer and catching nail were causing the trouble",
        "action_fact": "they supported the hinge and moved the nail aside",
        "outcome_fact": "the green signal guided boats through the safe channel",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.captain_name, params.mate_name, params.ship_name))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def tell(params: StoryParams) -> World:
    ship = Ship(name=params.ship_name)
    world = World(ship)
    captain = world.add(Entity(params.captain_name, "character", "captain", "captain"))
    mate = world.add(Entity(params.mate_name, "character", "pirate", "first mate"))
    shutter = world.add(Entity("historic_shutter", "thing", "shutter", "historic shutter", "the historic shutter"))
    key = world.add(Entity("brass_key", "thing", "tool", "brass key", "a brass key"))

    rng = _rng_for(params)
    arc = ARCS[(params.seed or rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    chosen = {}
    for index, beat in enumerate(beats):
        if params.seed is None:
            chosen[beat] = rng.choice(arc[beat])
        else:
            chosen[beat] = arc[beat][((params.seed // len(ARCS)) >> index) % len(arc[beat])]
        if index:
            world.para()
        world.say(chosen[beat].format(captain=captain.id, mate=mate.id, ship=ship.name))

    captain.meters["energy"] = 3.0
    mate.meters["energy"] = 3.0
    captain.memes["friendship"] = 1.0
    mate.memes["friendship"] = 1.0
    shutter.meters["stuck"] = 0.0
    shutter.memes["historic"] = 1.0
    key.meters["used"] = 1.0
    ship.friendship = 1.0
    ship.problem_solved = True
    ship.shutter_open = True
    ship.facts = {
        "captain": captain,
        "mate": mate,
        "shutter": shutter,
        "key": key,
        "arc": arc,
        "problem_event": chosen["problem"].format(captain=captain.id, mate=mate.id, ship=ship.name),
        "turn_event": chosen["turn"].format(captain=captain.id, mate=mate.id, ship=ship.name),
        "action_event": chosen["action"].format(captain=captain.id, mate=mate.id, ship=ship.name),
        "resolution_event": chosen["resolution"].format(captain=captain.id, mate=mate.id, ship=ship.name),
    }
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly pirate tale about a historic shutter and two friends solving a problem.",
        f"Tell a pirate story in which {world.ship.facts['captain'].id} and {world.ship.facts['mate'].id} protect an old harbor landmark.",
        "Write a short adventure where friendship leads to a careful repair and a bright ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    captain = f["captain"].id
    mate = f["mate"].id
    return [
        QAItem(f"Who worked together on {world.ship.name}?", f"{captain} and {mate} worked together as friends aboard {world.ship.name}."),
        QAItem("What was the problem?", f["problem_event"]),
        QAItem("What clue helped them?", f["turn_event"]),
        QAItem("How did they solve the problem?", f"{f['action_event']} {f['resolution_event']}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a shutter?", "A shutter is a movable cover for a window or opening. It can protect an opening or control light."),
        QAItem("What does historic mean?", "Historic means important because it belongs to or reminds us of the past."),
        QAItem("What is friendship?", "Friendship is a caring bond in which people trust, help, and listen to one another."),
        QAItem("What is problem solving?", "Problem solving means noticing a difficulty, finding clues, and choosing actions that can fix it."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id:16} ({entity.type:8}) meters={entity.meters} memes={entity.memes}")
    lines.append(f"  ship.friendship={world.ship.friendship}")
    lines.append(f"  ship.problem_solved={world.ship.problem_solved}")
    lines.append(f"  ship.shutter_open={world.ship.shutter_open}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    theme(historic),
    theme(shutter),
    feature(friendship),
    feature(problem_solving),
    resolved.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "historic"),
            asp.fact("theme", "shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(StoryParams("Mara", "Finn", "The Brass Gull", seed=7))
        if sample.world and sample.world.ship.problem_solved and sample.world.ship.shutter_open:
            print("OK: ASP and Python agree on the historic shutter story.")
            return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Historic shutter pirate friendship world.")
    parser.add_argument("--captain-name", choices=NAMES)
    parser.add_argument("--mate-name", choices=NAMES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != captain]
    mate = args.mate_name or rng.choice(choices)
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(captain, mate, ship)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible pirate story pattern: historic + shutter + friendship + problem solving")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Mara", "Finn", "The Brass Gull", seed=0),
            StoryParams("Nell", "Pip", "The Old Lantern", seed=1),
            StoryParams("Tess", "Bram", "The Shutter Star", seed=2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
