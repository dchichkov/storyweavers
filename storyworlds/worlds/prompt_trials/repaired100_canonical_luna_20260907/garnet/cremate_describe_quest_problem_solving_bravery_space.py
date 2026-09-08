#!/usr/bin/env python3
"""
A small space-adventure storyworld about a brave child astronaut, a lost comet
sample, and the careful problem solving that brings it home.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str = ""


@dataclass
class World:
    hero: Entity
    robot: Entity
    comet: Entity
    ship: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    robot_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Zara", "Tavi", "Nia", "Orin", "Pia", "Sol"]
ROBOTS = ["BEEP", "Orbit", "Pip", "Nova", "Kite"]
PLACES = [
    "the Moon's quiet rim",
    "the blue repair bay",
    "the Red Planet station",
    "the comet garden",
    "the starlit launch deck",
]


ASP_RULES = r"""
#show quest_ready/1.
#show brave/1.
#show solved/1.
#show recovered/1.

quest_ready(H) :- has_quest(H), has_clue(H).
brave(H) :- faces_danger(H), speaks_clearly(H).
solved(H) :- describes_problem(H), uses_plan(H).
recovered(H) :- solved(H), returns_sample(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("has_quest", "hero"),
            asp.fact("has_clue", "hero"),
            asp.fact("faces_danger", "hero"),
            asp.fact("speaks_clearly", "hero"),
            asp.fact("describes_problem", "hero"),
            asp.fact("uses_plan", "hero"),
            asp.fact("returns_sample", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show quest_ready/1.\n"
            "#show brave/1.\n"
            "#show solved/1.\n"
            "#show recovered/1."
        )
    )
    actual = set()
    for atom in model:
        if atom.name == "quest_ready":
            actual.add(("quest_ready", ("hero",)))
        elif atom.name == "brave":
            actual.add(("brave", ("hero",)))
        elif atom.name == "solved":
            actual.add(("solved", ("hero",)))
        elif atom.name == "recovered":
            actual.add(("recovered", ("hero",)))
    expected = {
        ("quest_ready", ("hero",)),
        ("brave", ("hero",)),
        ("solved", ("hero",)),
        ("recovered", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space-adventure storyworld about a brave comet-sample quest."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--robot-name", choices=ROBOTS)
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
        robot_name=args.robot_name or rng.choice(ROBOTS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.robot_name:
        raise StoryError("The astronaut and robot need different names.")
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.robot_name}|{params.place}")
    hero = Entity(
        id="hero",
        label=params.name,
        kind="astronaut",
        meters={"oxygen": 88.0, "distance_to_ship": 12.0, "courage": 0.7},
        memes={"curiosity": 0.9, "bravery": 0.8, "worry": 0.25},
    )
    robot = Entity(
        id="robot",
        label=params.robot_name,
        kind="helper_robot",
        meters={"battery": 0.82, "signal": 0.4},
        memes={"loyalty": 0.9, "confidence": 0.5},
    )
    comet = Entity(
        id="comet_sample",
        label="comet sample",
        kind="specimen",
        owner="ship",
        meters={"temperature": -180.0, "distance_to_ship": 12.0, "signal": 0.0},
        memes={"importance": 1.0, "mystery": 0.9},
    )
    ship = Entity(
        id="ship",
        label="Starling",
        kind="spaceship",
        meters={"fuel": 0.74, "hull": 0.96, "distance_to_sample": 12.0},
        memes={"safety": 0.8, "home": 1.0},
    )
    return World(
        hero=hero,
        robot=robot,
        comet=comet,
        ship=ship,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    problem: str,
    cause: str,
    plan: str,
    resolution: str,
    ending: str,
    danger: str,
    object_name: str,
) -> None:
    world.facts.update(
        discovery=discovery,
        problem=problem,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        danger=danger,
        object_name=object_name,
        quest=True,
        solved=True,
        brave=True,
        recovered=True,
    )


def _magnet_arc(world: World, rng: random.Random) -> str:
    h, r, p = world.hero.label, world.robot.label, world.place
    object_name = _choice(
        rng, ["a silver tether", "a coil of copper wire", "a moon-magnet wand"]
    )
    danger = "a field of sharp ice crystals spinning across the route"
    discovery = f"the sample was caught in a weak magnetic pocket beside {object_name}"
    problem = "the sample could not be reached by simply flying closer"
    cause = "the comet's metal grains were pulling the container sideways"
    plan = f"describe the pull, follow the signal, and use {object_name} as a gentle guide"
    resolution = (
        f"{h} described the sideways pull aloud, and {r} matched the signal while "
        f"{h} guided {object_name} around the magnetic pocket"
    )
    ending = "the sample clicked safely into its padded case as the stars steadied"
    lines = [
        f"At {p}, {h} received a very important quest: bring home a tiny comet sample.",
        f"The sample drifted beyond the ship's landing rail, while {danger} glittered between it and the airlock.",
        f'"The problem is not distance," said {h}. "It is the way the sample keeps sliding sideways."',
        f'"I can describe the signal," said {r}. "But I cannot be brave for both of us."',
        f"{h} took a slow breath and made a careful plan: {plan}.",
        f"The astronaut moved into the sparkling ice field. It hissed against the suit, but the tether stayed bright and tight.",
        f"{r} called, \"Left two steps! Now hold!\" {h} answered, \"I hear you,\" and changed direction.",
        f"Together they guided the sample away from the magnetic pocket. {resolution}.",
        f"Back aboard the Starling, {h} labeled the case and thanked {r}. By the time the engines hummed, {ending}.",
    ]
    _record(
        world,
        discovery=discovery,
        problem=problem,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        danger=danger,
        object_name=object_name,
    )
    world.hero.meters["oxygen"] -= 19
    world.hero.meters["courage"] += 0.15
    world.comet.meters["distance_to_ship"] = 0.0
    world.comet.meters["signal"] = 1.0
    world.robot.meters["signal"] = 1.0
    return " ".join(lines)


def _shadow_arc(world: World, rng: random.Random) -> str:
    h, r, p = world.hero.label, world.robot.label, world.place
    object_name = _choice(
        rng, ["a folded solar sail", "a silver blanket", "a spare antenna panel"]
    )
    danger = "the station's long shadow, where the heaters were almost silent"
    discovery = f"the sample was hidden beneath {object_name} on the dark side of a crater"
    problem = "the search lights made several false samples shine"
    cause = "frozen bubbles on the crater floor reflected the beam like tiny moons"
    plan = f"describe the true sample's shape and use the sample's faint warmth instead of sight"
    resolution = (
        f"{h} described the real sample as a warm blue dot, and {r} turned off the "
        f"bright lamps so its small heat signal could be heard"
    )
    ending = "the comet sample glowed softly in the warm case while the crater lights went dark"
    lines = [
        f"At {p}, {h} began a quest to retrieve a comet sample before the station's research window closed.",
        f"The sample had vanished into {danger}. In the darkness, {object_name} cast a long, crooked shadow.",
        f"Every bright spot looked promising, but every bright spot was only ice.",
        f'"I cannot tell which sparkle is real," said {r}.',
        f'"Then I will describe what we know," said {h}. "The sample is small, warm, and humming near the crater wall."',
        f"The problem became clear: {cause}. So the pair chose a better plan: {plan}.",
        f"{r} dimmed the lamps. {h} crossed the shadow with one hand on the guide rope and one hand on the scanner.",
        f'"There!" whispered {h}. "A warm blue dot."',
        f"They lifted the sample together. {resolution}. On the return walk, bravery felt less like shouting and more like taking the next careful step.",
    ]
    _record(
        world,
        discovery=discovery,
        problem=problem,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        danger=danger,
        object_name=object_name,
    )
    world.hero.meters["oxygen"] -= 16
    world.hero.meters["courage"] += 0.12
    world.comet.meters["distance_to_ship"] = 0.0
    world.comet.meters["signal"] = 1.0
    return " ".join(lines)


def _dust_arc(world: World, rng: random.Random) -> str:
    h, r, p = world.hero.label, world.robot.label, world.place
    object_name = _choice(
        rng, ["a soft scoop", "a cargo net", "a pair of moon boots"]
    )
    danger = "a quick cloud of red dust racing over the plain"
    discovery = f"the sample's case had sunk into a shallow drift beside {object_name}"
    problem = "the dust kept filling the case's latch before it could be opened"
    cause = "the cloud's static charge pulled every loose grain toward the metal latch"
    plan = f"describe the dust's movement, ground the charge, and use {object_name} to clear the latch"
    resolution = (
        f"{h} described the dust as a red river, while {r} grounded the charge and "
        f"{h} used {object_name} to sweep the latch clean"
    )
    ending = "the sample rested under glass, and the last red grains settled like a quiet sunset"
    lines = [
        f"On a lonely plain near {p}, {h} carried out the next step of the comet quest.",
        f"Then {danger} rushed toward the research sled.",
        f"The sample's case tipped into the drift. Each time {h} opened it, dust snapped into the latch.",
        f'"We are losing time," said {r}. "Tell me exactly what you see."',
        f'"The dust is not falling," said {h}. "It is being pulled sideways by the case."',
        f"The cause was clear: {cause}. {h} made a plan to {plan}.",
        f"The dust roared around the astronaut's boots. For one moment, {h} wanted to run back to the sled.",
        f'"I am frightened," {h} admitted. "But I can still solve one small part."',
        f"That brave sentence became an action. {r} grounded the charge, and {h} worked the tool slowly. {resolution}.",
        f"When the cloud passed, {ending}. The quest was complete because the astronaut had turned fear into a useful plan.",
    ]
    _record(
        world,
        discovery=discovery,
        problem=problem,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        danger=danger,
        object_name=object_name,
    )
    world.hero.meters["oxygen"] -= 21
    world.hero.meters["courage"] += 0.18
    world.comet.meters["distance_to_ship"] = 0.0
    world.comet.meters["signal"] = 1.0
    return " ".join(lines)


def _ring_arc(world: World, rng: random.Random) -> str:
    h, r, p = world.hero.label, world.robot.label, world.place
    object_name = _choice(
        rng, ["a blue guide flare", "a spool of golden thread", "a blinking pebble beacon"]
    )
    danger = "the wide ring shadow between two tumbling rocks"
    discovery = f"the sample's beacon was circling inside {danger}"
    problem = "the rocks made the beacon appear in three places at once"
    cause = "reflected starlight bounced from the ring dust and copied the signal"
    plan = f"describe the signal's rhythm and send {object_name} on a slow test path"
    resolution = (
        f"{h} described the true signal as two short blinks and one long blink, "
        f"then sent {object_name} along the safe path until the false lights faded"
    )
    ending = "the real beacon blinked beside the recovered sample like a tiny promise"
    lines = [
        f"Beyond {p}, {h} entered a ring of floating rocks to finish a comet-sample quest.",
        f"The beacon flashed inside the ring, but {danger} made the route look strange.",
        f'"I see three samples," said {r}. "Only one can be real."',
        f'"Then we will ask the lights a better question," said {h}.',
        f"{h} watched the rhythm instead of chasing the brightest flash. The problem was clear: {cause}.",
        f"The plan was to {plan}. A rock the size of a house drifted past, and the ship's warning bell chirped.",
        f'"Stay with me," said {h}. "Count the blinks."',
        f"{r} counted, \"Short, short, long!\" The false lights flickered out. {resolution}.",
        f"The astronaut brought the case home through the quiet ring. At the airlock, {ending}.",
    ]
    _record(
        world,
        discovery=discovery,
        problem=problem,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        danger=danger,
        object_name=object_name,
    )
    world.hero.meters["oxygen"] -= 18
    world.hero.meters["courage"] += 0.14
    world.comet.meters["distance_to_ship"] = 0.0
    world.comet.meters["signal"] = 1.0
    return " ".join(lines)


ARC_BUILDERS = [_magnet_arc, _shadow_arc, _dust_arc, _ring_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7D)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.facts
    return [
        QAItem(
            question=f"What quest did {h} receive?",
            answer=f"{h} received the quest to bring a tiny comet sample safely back to the ship.",
        ),
        QAItem(
            question="What problem did the astronaut have to solve?",
            answer=f"The main problem was that {f['problem']}, because {f['cause']}.",
        ),
        QAItem(
            question=f"How did {h} show bravery?",
            answer=f"{h} showed bravery by facing {f['danger']} and following a careful plan instead of giving up.",
        ),
        QAItem(
            question="How did describing the problem help?",
            answer=f"Describing the problem helped because {f['plan']}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The comet sample returned safely to the ship, and {h} learned that careful problem solving can guide brave actions.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comet?",
            answer="A comet is a small space object made of ice, dust, and rock that travels around the Sun.",
        ),
        QAItem(
            question="Why do astronauts wear spacesuits?",
            answer="Astronauts wear spacesuits for air, temperature control, and protection from the dangers of space.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding what is wrong, making a plan, testing it carefully, and changing the plan when needed.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a careful, helpful thing even when something feels frightening.",
        ),
        QAItem(
            question="Why should a space sample be kept in a case?",
            answer="A case protects a sample from being lost, contaminated, overheated, or damaged during the journey home.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly space adventure about a brave astronaut on a comet-sample quest.",
        f"Tell a story set at {world.place} where describing a problem leads to a clever solution.",
        "Create a space story that uses quest, problem solving, bravery, and a helpful robot.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.robot, world.comet, world.ship]:
        lines.append(
            f"  {entity.id:13} {entity.kind:13} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        output.append(f"{i}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
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
                "#show quest_ready/1.\n"
                "#show brave/1.\n"
                "#show solved/1.\n"
                "#show recovered/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "4 compatible logical atoms: "
            "quest_ready(hero), brave(hero), solved(hero), recovered(hero)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", robot_name="BEEP", place="the Moon's quiet rim"),
            StoryParams(name="Milo", robot_name="Orbit", place="the blue repair bay"),
            StoryParams(name="Zara", robot_name="Pip", place="the Red Planet station"),
            StoryParams(name="Nia", robot_name="Nova", place="the comet garden"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
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

        if len(samples) < args.n:
            raise StoryError("Could not generate enough distinct story variants.")

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
