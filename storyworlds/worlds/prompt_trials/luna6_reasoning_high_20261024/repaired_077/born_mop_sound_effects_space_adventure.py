#!/usr/bin/env python3
"""A small, sound-filled space-adventure world about a newly born robot and a mop."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Rover:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Tool:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    robot_name: str
    pilot_name: str
    mission: str
    seed: Optional[int] = None


@dataclass
class World:
    robot: Character
    pilot: Character
    rover: Rover
    mop: Tool
    mission: str
    place: str
    pane_visibility: float = 0.14
    radio_working: bool = True
    beacon_visible: bool = False
    rover_route: str = "waiting for guidance"
    phase: str = "arrival"
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAME_REGISTRY = ("Miri", "Tavi", "Nori", "Pip", "Luma", "Roo", "Sola", "Kiko")
MISSION_REGISTRY = {
    "north_ridge": {
        "route_id": "crater_curve",
        "place": "the Moon's North Ridge outpost",
        "dust_cause": "a tray of gray samples brushed dust across the cabin side of the observation pane",
        "landmark": "the twin basalt boulders",
        "obstacle": "a shallow crater",
        "route": "curve around the shallow crater with the twin boulders on your left",
        "color": "green",
        "ending": "Finch rolled into the home circle beneath the clear pane, its green beacon blinking steadily",
    },
    "mare_plain": {
        "route_id": "silver_poles",
        "place": "the Moon's Mare Plain outpost",
        "dust_cause": "a sample satchel left a soft gray smear on the cabin side of the observation pane",
        "landmark": "a row of silver marker poles",
        "obstacle": "a low ridge",
        "route": "follow the silver poles and pass around the low ridge",
        "color": "blue",
        "ending": "Finch crossed the home circle beneath the clear pane, its blue beacon shining beside the silver poles",
    },
    "far_side": {
        "route_id": "guide_lights",
        "place": "the Moon's Far Side relay outpost",
        "dust_cause": "fine gray dust from a sample case clouded the cabin side of the observation pane",
        "landmark": "three white guide lights",
        "obstacle": "a shadowed hollow",
        "route": "keep to the three white guide lights and steer clear of the shadowed hollow",
        "color": "amber",
        "ending": "Finch reached the home circle beneath the clear pane, its amber beacon glowing beside the guide lights",
    },
}

PARAMETER_REGISTRY = {
    "robot_name": NAME_REGISTRY,
    "pilot_name": NAME_REGISTRY,
    "mission": tuple(MISSION_REGISTRY),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate a space adventure about a newborn robot, a rover, and a mop."
    )
    ap.add_argument("--robot-name", choices=NAME_REGISTRY)
    ap.add_argument("--pilot-name", choices=NAME_REGISTRY)
    ap.add_argument("--mission", choices=tuple(MISSION_REGISTRY))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    robot = args.robot_name or rng.choice(NAME_REGISTRY)
    possible_pilots = [name for name in NAME_REGISTRY if name != robot]
    pilot = args.pilot_name or rng.choice(possible_pilots)
    mission = args.mission or rng.choice(tuple(MISSION_REGISTRY))
    return StoryParams(robot_name=robot, pilot_name=pilot, mission=mission)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.robot_name not in NAME_REGISTRY:
        raise StoryError("Choose a robot name from this world's name registry.")
    if params.pilot_name not in NAME_REGISTRY:
        raise StoryError("Choose a pilot name from this world's name registry.")
    if params.robot_name == params.pilot_name:
        raise StoryError("The robot and pilot need different names for their conversation.")
    if params.mission not in MISSION_REGISTRY:
        raise StoryError("That mission is not part of this little Moon outpost world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    profile = MISSION_REGISTRY[params.mission]
    rng = random.Random(params.seed if params.seed is not None else 0)

    robot = Character(
        name=params.robot_name,
        kind="repair robot",
        meters={"position_m": 0.0, "battery_percent": 100.0},
        memes={"curiosity": 0.85, "confidence": 0.42, "kindness": 0.78},
    )
    pilot = Character(
        name=params.pilot_name,
        kind="space pilot",
        meters={"position_m": 0.0},
        memes={"calm": 0.72, "worry": 0.55, "trust": 0.62},
    )
    rover = Rover(
        name="Finch",
        kind="Moon rover",
        meters={"distance_to_hangar_m": 430.0, "wheel_speed_mps": 0.0},
        memes={"patience": 0.75},
    )
    mop = Tool(
        name="the soft cabin mop",
        kind="microfiber mop",
        meters={"head_dust_load_g": 0.0, "usable_fiber_percent": 100.0},
    )
    world = World(
        robot=robot,
        pilot=pilot,
        rover=rover,
        mop=mop,
        mission=params.mission,
        place=profile["place"],
    )

    opening = rng.choice(
        (
            "The Starling's workshop chimed awake before the Moon came into view.",
            "A bright morning began with a new light in the Starling's repair bay.",
            "The Starling hummed above the Moon, carrying one small, brand-new helper.",
        )
    )
    world.facts["birth"] = "The robot woke for the first time in the Starling's workshop."
    world.phase = "radio_check"
    world.facts["initial_visibility"] = world.pane_visibility
    world.facts["dust_cause"] = profile["dust_cause"]
    world.facts["initial_problem"] = "The dusty pane hid Finch's beacon from the outpost."

    # The radio still answers, so the missing view is not evidence of a broken beacon.
    if world.radio_working and world.pane_visibility < 0.5:
        world.facts["clue"] = "Finch's radio answered with a steady pip... pip..., while dust covered the inside of the pane."
        world.robot.memes["confidence"] = 0.82
        world.pilot.memes["worry"] = 0.3
        world.facts["diagnosis"] = "dust on the cabin-side pane"
    else:
        raise StoryError("The mission needs a working rover radio and a dusty observation pane.")

    world.phase = "cleaning"
    if mop.meters["usable_fiber_percent"] <= 0:
        raise StoryError("The soft mop needs a clean head before it can clear the pane.")
    world.pane_visibility = 0.96
    world.beacon_visible = True
    mop.meters["head_dust_load_g"] = 1.8
    mop.meters["usable_fiber_percent"] = 72.0
    robot.meters["battery_percent"] -= 4.0
    world.facts["method"] = "The robot used the soft cabin mop on the inside of the observation pane."
    world.facts["beacon"] = f"Finch's {profile['color']} beacon, near {profile['landmark']}."
    world.phase = "guidance"
    if world.beacon_visible:
        world.rover_route = profile["route"]
        rover.meters["wheel_speed_mps"] = 1.2
        world.facts["route"] = world.rover_route
        world.facts["later_consequence"] = "Finch followed the visible landmarks and reached the outpost."
    world.phase = "home"
    rover.meters["distance_to_hangar_m"] = 0.0
    world.facts["ending_image"] = profile["ending"]

    lines = [
        f"{opening} On the day {robot.name} was born, the workshop lights blinked on and went, \"BIP-BIP!\"",
        f"The little repair robot rolled to {pilot.name}, eager for a first space adventure at {world.place}.",
        (
            f"Outside, Finch was waiting for a safe route home around {profile['obstacle']}. "
            f"But {profile['dust_cause']}, hiding the rover's beacon from the window."
        ),
        f"{pilot.name} leaned toward the cloudy glass. \"I can't see Finch's beacon. Did its lamp fail?\"",
        (
            f"Then the radio sounded: \"Pip... pip...\" {robot.name} listened closely. "
            f"\"Finch is still calling. The dust is on our side of the glass. I can clear it with the mop!\""
        ),
        (
            f"\"Good catch,\" said {pilot.name}. \"Wipe the inside pane, and I'll keep Finch on the radio.\" "
            f"With a soft \"SHHK, SHHK!\", {robot.name} swept the mop across the glass."
        ),
        (
            f"The gray smear vanished. {robot.name} spotted Finch's {profile['color']} beacon near "
            f"{profile['landmark']}. \"I see the safe landmarks now! Tell Finch to {profile['route']}.\""
        ),
        (
            f"{pilot.name} relayed the directions. Finch answered, \"Route received—rolling home!\" "
            f"Its wheels gave a cheerful \"VRRRM\" as it followed the lights around {profile['obstacle']}."
        ),
        f"{profile['ending']}. The dusty mop hung by the door, ready for the next little mission.",
    ]
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a child-friendly space adventure about {robot.name}, who is born aboard the Starling.",
        f"Set the adventure at {world.place}, where a dusty window hides a rover's beacon.",
        "Include lively sound effects, a useful mop, spoken teamwork, and a clear, happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {pilot.name} first think had happened to Finch's beacon?",
            answer=f"{pilot.name} first thought Finch's beacon lamp might have failed because it could not be seen through the cloudy pane.",
        ),
        QAItem(
            question="What clue showed that Finch was still working?",
            answer=f"Finch's radio answered with a steady pip... pip..., showing that the rover was still calling even though its beacon was hidden from view.",
        ),
        QAItem(
            question=f"How did {robot.name} use the mop to help?",
            answer=f"{robot.name} used the soft cabin mop to clear dust from the inside of the observation pane, making Finch's beacon visible.",
        ),
        QAItem(
            question="What route did Finch follow to get home?",
            answer=f"Finch followed the visible landmarks and {profile['route']}.",
        ),
        QAItem(
            question="What changed by the end of the adventure?",
            answer=f"The observation pane was clear, and Finch reached the outpost with its {profile['color']} beacon shining.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a mop do?",
            answer="A mop has a soft or absorbent head on a handle and is used to clean surfaces by wiping them.",
        ),
        QAItem(
            question="Why can a rover beacon be useful?",
            answer="A rover beacon makes the rover easier to spot, which can help a crew locate it and guide it safely.",
        ),
        QAItem(
            question="What is a space rover?",
            answer="A space rover is a vehicle designed to travel over the surface of a world such as the Moon or Mars.",
        ),
        QAItem(
            question="Why did listening to the radio help the crew?",
            answer="The radio's steady reply showed that Finch was still communicating, so the crew could investigate the dusty window instead of assuming the rover had stopped working.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print()
        print("--- trace ---")
        print(f"phase={world.phase}, mission={world.mission}, place={world.place}")
        print(
            f"robot={world.robot.name} ({world.robot.kind}), "
            f"meters={world.robot.meters}, memes={world.robot.memes}"
        )
        print(
            f"pilot={world.pilot.name} ({world.pilot.kind}), "
            f"meters={world.pilot.meters}, memes={world.pilot.memes}"
        )
        print(
            f"rover={world.rover.name} ({world.rover.kind}), "
            f"meters={world.rover.meters}, memes={world.rover.memes}"
        )
        print(f"mop={world.mop.kind}, meters={world.mop.meters}")
        print(
            f"pane_visibility={world.pane_visibility}, beacon_visible={world.beacon_visible}, "
            f"radio_working={world.radio_working}, rover_route={world.rover_route}"
        )
        print(f"facts={world.facts}")
    if qa:
        print()
        print("== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_route(M, R) :- mission(M), route(M, R).
#show valid_route/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for mission, profile in MISSION_REGISTRY.items():
        facts.append(asp.fact("mission", mission))
        facts.append(asp.fact("route", mission, profile["route_id"]))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_route/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_routes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_route")))


def asp_verify() -> int:
    python_routes = {
        (mission, profile["route_id"])
        for mission, profile in MISSION_REGISTRY.items()
    }
    clingo_routes = set(asp_valid_routes())
    if python_routes != clingo_routes:
        print("MISMATCH between the Python mission registry and the ASP twin:")
        if python_routes - clingo_routes:
            print("  only in python:", sorted(python_routes - clingo_routes))
        if clingo_routes - python_routes:
            print("  only in clingo:", sorted(clingo_routes - python_routes))
        return 1

    for index, mission in enumerate(MISSION_REGISTRY):
        robot = NAME_REGISTRY[index]
        pilot = NAME_REGISTRY[(index + 1) % len(NAME_REGISTRY)]
        sample = generate(
            StoryParams(
                robot_name=robot,
                pilot_name=pilot,
                mission=mission,
                seed=100 + index,
            )
        )
        world = sample.world
        if (
            world is None
            or not world.beacon_visible
            or world.pane_visibility <= 0.5
            or world.rover.meters["distance_to_hangar_m"] != 0.0
            or "born" not in sample.story.lower()
            or "mop" not in sample.story.lower()
            or '"I can clear it with the mop!"' not in sample.story
            or not sample.story_qa
            or any(not item.answer.strip() for item in sample.story_qa + sample.world_qa)
        ):
            print(f"Generated-story verification failed for mission {mission}.")
            return 1

    print(
        f"OK: ASP and Python agree on {len(python_routes)} routes; "
        f"all {len(MISSION_REGISTRY)} generated mission stories passed."
    )
    return 0


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        samples = []
        for index, mission in enumerate(MISSION_REGISTRY):
            robot = args.robot_name or NAME_REGISTRY[index % len(NAME_REGISTRY)]
            default_pilot = NAME_REGISTRY[(index + 1) % len(NAME_REGISTRY)]
            if default_pilot == robot:
                default_pilot = NAME_REGISTRY[(index + 2) % len(NAME_REGISTRY)]
            pilot = args.pilot_name or default_pilot
            samples.append(
                StoryParams(
                    robot_name=robot,
                    pilot_name=pilot,
                    mission=args.mission or mission,
                    seed=(args.seed if args.seed is not None else 0) + index,
                )
            )
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        StoryParams(
            **{
                **resolve_params(args, random.Random(base_seed + index).__class__(base_seed + index).__dict__),
            }
        )
        for index in range(0)
    ]


def _ordinary_generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StoryParams] = []
    for index in range(args.n):
        sample = resolve_params(args, random.Random(base_seed + index))
        sample.seed = base_seed + index
        samples.append(sample)
    return samples


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for mission, route in asp_valid_routes():
            profile = MISSION_REGISTRY[mission]
            print(f"{profile['place']}: {route}")
        return
    if args.n < 1 and not args.all:
        ap.error("-n must be at least 1.")

    try:
        params_list = generation_samples(args) if args.all else _ordinary_generation_samples(args)
        samples = [generate(params) for params in params_list]
    except StoryError as exc:
        ap.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
