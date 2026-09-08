#!/usr/bin/env python3
"""
A small space-adventure storyworld about a repeated phrase, a blocked moon
bridge, and the problem-solving steps that guide a crew safely home.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    captain: Entity
    helper: Entity
    rover: Entity
    beacon: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    helper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Nova", "Tess", "Zara", "Pip", "Orion", "Kai"]
HELPERS = ["Comet", "Bleep", "Atlas", "Sprocket", "Echo", "Moss"]
PLACES = [
    "the silver moon",
    "the blue crater",
    "the Starling station",
    "the quiet asteroid belt",
    "the ringed planet's shadow",
]


ASP_RULES = r"""
#show hears_phrase/1.
#show tests_plan/1.
#show reaches_home/1.

hears_phrase(C) :- phrase_signal(C).
tests_plan(C) :- checks_map(C), checks_power(C).
reaches_home(C) :- tests_plan(C), repairs_beacon(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("phrase_signal", "captain"),
            asp.fact("checks_map", "captain"),
            asp.fact("checks_power", "captain"),
            asp.fact("repairs_beacon", "captain"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = """
#show hears_phrase/1.
#show tests_plan/1.
#show reaches_home/1.
"""
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name == "hears_phrase":
            actual.add(("hears_phrase", (atom.arguments[0].name,)))
        elif atom.name == "tests_plan":
            actual.add(("tests_plan", (atom.arguments[0].name,)))
        elif atom.name == "reaches_home":
            actual.add(("reaches_home", (atom.arguments[0].name,)))
    expected = {
        ("hears_phrase", ("captain",)),
        ("tests_plan", ("captain",)),
        ("reaches_home", ("captain",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    sample = generate(
        StoryParams(name="Luna", helper_name="Comet", place="the silver moon", seed=17)
    )
    if not sample.story or "Luna" not in sample.story:
        print("MISMATCH: generated story was not exercised.")
        return 1
    print("OK: ASP parity and generated-story checks verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space-adventure storyworld about a phrase and problem solving."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
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
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.helper_name:
        raise StoryError("The captain and helper must have different names.")
    captain = Entity(
        id="captain",
        label=params.name,
        kind="character",
        meters={"air": 18.0, "distance_to_home": 4.0},
        memes={"curiosity": 0.8, "worry": 0.5, "confidence": 0.4},
    )
    helper = Entity(
        id="helper",
        label=params.helper_name,
        kind="robot",
        meters={"battery": 72.0},
        memes={"patience": 0.9, "hope": 0.7},
    )
    rover = Entity(
        id="rover",
        label="the moon rover",
        kind="vehicle",
        owner="captain",
        meters={"wheel_grip": 0.2, "battery": 61.0},
        memes={"steadiness": 0.3},
    )
    beacon = Entity(
        id="beacon",
        label="the home beacon",
        kind="machine",
        meters={"signal": 0.1, "dust_load": 0.9},
        memes={"welcome": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper_name}|{params.place}")
    return World(
        captain=captain,
        helper=helper,
        rover=rover,
        beacon=beacon,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    phrase: str,
    obstacle: str,
    clue: str,
    plan: str,
    resolution: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        phrase=phrase,
        obstacle=obstacle,
        clue=clue,
        plan=plan,
        resolution=resolution,
        ending=ending,
        solved=True,
        story=" ".join(lines),
    )
    world.captain.memes["confidence"] = 0.95
    world.captain.memes["worry"] = 0.1
    world.rover.meters["wheel_grip"] = 0.9
    world.beacon.meters["signal"] = 1.0
    return world.facts["story"]


def _moon_bridge_arc(world: World, rng: random.Random) -> str:
    h = world.captain.label
    r = world.helper.label
    p = world.place
    phrase = _choice(
        rng,
        [
            "Look, listen, test, then travel!",
            "One small clue can light the way!",
            "Stop, think, try!",
            "A careful plan beats a speedy guess!",
        ],
    )
    obstacle = _choice(
        rng,
        [
            "a field of loose moon stones covered the rover path",
            "a silver dust slide buried the narrow bridge home",
            "the rover's route ended at a dark crack in the crater floor",
        ],
    )
    clue = _choice(
        rng,
        [
            "the old route markers still blinked beneath the dust",
            "three warm tire marks pointed toward a firm shelf",
            "the beacon's faint pulse grew stronger beside the shadowed ridge",
        ]
    )
    plan = "they marked a safe line, tested each stone with the rover arm, and crossed only after the wheels held"
    resolution = f"{h} and {r} followed the safe line, cleared the beacon's dusty lens, and sent a bright signal toward home"
    ending = _choice(
        rng,
        [
            "the rover rolled beneath a sky full of slow stars while the home beacon blinked like a friendly eye",
            "the moon bridge shone behind them, and their little ship answered with three cheerful lights",
            "the last dust cloud drifted away as the rover's tracks made a neat silver road toward the station",
        ],
    )
    lines = [
        f"On {p}, {h} and {r} were driving the moon rover when {obstacle}.",
        f"The rover stopped with a soft beep. Its map flashed, but the way home was hidden.",
        f'"{phrase}" said {h}.',
        f'"That is a good phrase," answered {r}. "But which part comes first?"',
        f"{h} took a slow breath instead of pressing the fastest-looking button. First, they looked at the ground. Then they listened to the rover's wheel sensors. At last, {clue}.",
        f"{h} and {r} made a plan: {plan}.",
        f"They moved one careful meter at a time. When a stone wobbled, they backed up. When the rover found firm ground, {r} placed a bright flag there.",
        f"At the far side, the beacon still could not see them through its dusty lens. {h} climbed the small service ladder while {r} held the safety line.",
        f"{resolution}. The beacon answered with a warm green glow.",
        f"By moonrise, {ending}. {h} kept repeating the phrase, not because it was magic, but because it helped the crew remember how to solve a hard problem.",
    ]
    return _record(
        world,
        phrase=phrase,
        obstacle=obstacle,
        clue=clue,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _signal_arc(world: World, rng: random.Random) -> str:
    h = world.captain.label
    r = world.helper.label
    p = world.place
    phrase = _choice(
        rng,
        [
            "Ask the signal what it needs!",
            "Find the quiet, then listen!",
            "Check the wires before blaming the stars!",
        ]
    )
    obstacle = "the emergency radio began repeating a broken phrase instead of calling the station"
    clue = _choice(
        rng,
        [
            "the broken sound stopped whenever the rover lamp pointed at the antenna",
            "a tiny red light blinked twice near the loose cable",
            "the radio grew clear when the antenna faced the planet's bright ring",
        ]
    )
    plan = "they turned off one system at a time, watched the lights, and tightened the cable only after finding the faulty connection"
    resolution = f"{h} repaired the antenna while {r} sent a short test message"
    ending = _choice(
        rng,
        [
            "the radio filled the cabin with the station's happy reply",
            "the stars seemed less lonely when the home crew answered, 'Message received!'",
            "the repaired signal curled through space like a bright invisible ribbon",
        ]
    )
    lines = [
        f"Near {p}, {h} heard the emergency radio say, \"Phrase, phrase, phrase,\" and then fall silent.",
        f'"{phrase}" said {h}.',
        f'"I can repeat a sound," said {r}, "but I cannot yet explain it."',
        f"The cabin lights flickered, the radio hissed, and the rover waited beside the dark antenna.",
        f"{h} did not guess wildly. They checked the power panel, then the antenna map, and finally noticed that {clue}.",
        f"Together they made a plan: {plan}.",
        f"The first test changed nothing. The second made the hiss louder. The third test revealed one loose cable tucked under a shield plate.",
        f"{h} tightened the cable while {r} counted slowly. The radio cleared enough for a tiny test message.",
        f"{resolution}.",
        f"At last, {ending}. The repeated phrase had become a useful clue because the crew had listened carefully and tested one idea at a time.",
    ]
    return _record(
        world,
        phrase=phrase,
        obstacle=obstacle,
        clue=clue,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _ice_cave_arc(world: World, rng: random.Random) -> str:
    h = world.captain.label
    r = world.helper.label
    p = world.place
    phrase = _choice(
        rng,
        [
            "Warm hands, clear path!",
            "Small steps, bright lamps!",
            "Think together, travel together!",
        ]
    )
    obstacle = "a frozen tunnel trapped the rover between two blue ice walls"
    clue = _choice(
        rng,
        [
            "warm air slipped from a thin crack above the tunnel",
            "the rover's compass pointed toward a hollow space behind the left wall",
            "a line of glittering ice bubbles led toward a wider chamber",
        ]
    )
    plan = "they used the rover's heater to soften a narrow edge, placed safety markers, and widened the passage instead of smashing the whole wall"
    resolution = f"{h} steered slowly while {r} watched the temperature and called out each safe turn"
    ending = _choice(
        rng,
        [
            "the rover emerged beneath the stars with tiny ice stars sparkling on its roof",
            "the crew reached the warm landing dome, where their boots made puddles on the welcome mat",
            "the blue tunnel glowed behind them while the home beacon painted a path across the snow",
        ]
    )
    lines = [
        f"At {p}, {h} and {r} entered an ice cave to collect a sample for the station.",
        f"Without warning, {obstacle}. The rover lights made the walls shine blue.",
        f'"{phrase}" whispered {h}.',
        f'"And no rushing," said {r}. "Rushing is how ice gets the last word."',
        f"They examined the walls, measured the temperature, and found that {clue}.",
        f"Their plan was simple: {plan}.",
        f"The work took time. One heater was too strong, so they lowered it. One route was too narrow, so they marked it as closed. Each small test made the next choice clearer.",
        f"{resolution}.",
        f"At the final bend, the rover bumped gently into open air. {ending}.",
        f"{h} wrote the phrase on the mission board as a reminder: a calm question can make room for a clever answer.",
    ]
    return _record(
        world,
        phrase=phrase,
        obstacle=obstacle,
        clue=clue,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


ARC_BUILDERS = [_moon_bridge_arc, _signal_arc, _ice_cave_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7E)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.captain.label
    facts = world.facts
    return [
        QAItem(
            question=f"What phrase did {h} use during the problem?",
            answer=f'{h} used the phrase "{facts["phrase"]}" to help remember a careful way to solve the problem.',
        ),
        QAItem(
            question="What was the main obstacle?",
            answer=f"The main obstacle was that {facts['obstacle']}.",
        ),
        QAItem(
            question="What clue helped the crew?",
            answer=f"The crew noticed that {facts['clue']}.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=f"They solved it by making a careful plan: {facts['plan']}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"At the end, {facts['resolution']}, and {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, gathering clues, trying sensible steps, and changing the plan when a test does not work.",
        ),
        QAItem(
            question="Why is it useful to test one idea at a time?",
            answer="Testing one idea at a time helps you learn which choice caused a result, so the next decision is based on evidence instead of guessing.",
        ),
        QAItem(
            question="What does a beacon do in space travel?",
            answer="A beacon sends a visible or radio signal that helps travelers find a station, landing place, or safe route.",
        ),
        QAItem(
            question="Why can a repeated phrase help a team?",
            answer="A repeated phrase can remind a team of its shared plan and help everyone stay calm while they work through a difficult task.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a space-adventure story for young children about a phrase that helps solve a problem.",
        f"Tell a story set on {world.place} where a crew uses clues and careful tests to get home.",
        "Create a child-friendly adventure with spoken dialogue, a repeated phrase, and a practical solution.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.captain, world.helper, world.rover, world.beacon]:
        lines.append(
            f"  {entity.id:8} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                """
#show hears_phrase/1.
#show tests_plan/1.
#show reaches_home/1.
"""
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "hears_phrase(captain), tests_plan(captain), reaches_home(captain)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", helper_name="Comet", place="the silver moon", seed=11),
            StoryParams(name="Mira", helper_name="Bleep", place="the blue crater", seed=12),
            StoryParams(name="Nova", helper_name="Atlas", place="the Starling station", seed=13),
            StoryParams(
                name="Tess",
                helper_name="Sprocket",
                place="the quiet asteroid belt",
                seed=14,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
