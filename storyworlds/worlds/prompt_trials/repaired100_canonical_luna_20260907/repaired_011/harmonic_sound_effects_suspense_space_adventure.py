#!/usr/bin/env python3
"""
A small storyworld about a harmonic space rescue, suspense, and sound effects.

A young space explorer hears a strange musical signal beyond a moon and must
use its pattern to guide a drifting satellite home.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    pilot: str
    robot: str
    moon: str
    satellite: str
    signal: str
    incident: int = 0
    premise: int = 0
    sound: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Luna", "Milo", "Suri", "Nova", "Tavi", "Pia", "Orin", "Kiko"]
PILOTS = ["Captain Vale", "Pilot Juno", "Commander Sol", "Pilot Mira"]
ROBOTS = ["Bleep", "Orbit", "Tink", "Mica", "Zee"]
MOONS = ["Moon Rilla", "the blue moon", "Moon Pebble", "the silver moon"]
SATELLITES = ["weather satellite", "garden satellite", "star-map satellite", "message satellite"]
SIGNALS = ["a bright three-note hum", "a soft bell-like pulse", "a rising radio song", "a chiming space rhythm"]

PREMISES = [
    "{name} was helping {pilot} chart the stars when a lonely sound floated past the ship. It was not a beep or a buzz. It was a harmonic little tune.",
    "The spaceship sailed quietly beside {moon}. {name} watched the craters while {robot} listened to the radio, and then the speakers sang three shining notes.",
    "{name} and {robot} were delivering supplies near {moon} when {pilot} pointed at a blinking dot. A lost {satellite} was drifting beyond the moon.",
    "During a calm night flight, {name} heard {signal}. The sound seemed to answer itself, as if two invisible bells were talking across space.",
    "{pilot} let {name} sit in the navigator's chair for the first time. Just then, a strange musical signal warned them that a {satellite} had slipped from its orbit.",
    "The stars looked like tiny lamps outside the window. Then the ship's radio made a curious sound: 'Ding-dong-ding!' {name} knew someone, or something, needed help.",
]

INCIDENTS = [
    {
        "lead": "{robot} found the drifting {satellite} spinning slowly near the shadow side of {moon}.",
        "trigger": "Without warning, the satellite's light blinked out, and its path bent toward a field of floating rocks.",
        "risk": "If it crossed the rocks, its delicate antenna could snap before anyone could reach it.",
        "action": "{name} listened to the satellite's three-note signal and matched it with the ship's gentle thrusters.",
        "resolution": "The matching rhythm nudged the satellite away from the rocks and back into a safe orbit.",
        "cause": "the satellite lost its light and drifted toward floating rocks",
        "deed": "matched the satellite's harmonic signal with gentle thruster bursts",
        "result": "the satellite returned safely to orbit",
    },
    {
        "lead": "The {satellite} flashed a message beside {moon}, but its radio song came out in crooked pieces.",
        "trigger": "A dark cloud of space dust covered the view, and the ship began to lose the satellite's blinking signal.",
        "risk": "For a moment, the crew could hear the satellite but could not see where it was.",
        "action": "{name} asked {robot} to repeat each note. By comparing the echoes, {name} located the satellite behind the dust.",
        "resolution": "{pilot} steered around the cloud, and the hidden satellite appeared like a tiny lantern.",
        "cause": "space dust hid the satellite while its broken signal echoed",
        "deed": "used repeated echoes to locate the hidden satellite",
        "result": "the pilot steered around the dust and found the satellite",
    },
    {
        "lead": "{robot} detected a loose solar panel wobbling on the {satellite}.",
        "trigger": "The panel swung wider and wider as the satellite spun toward the cold side of {moon}.",
        "risk": "If the panel tore away, the satellite would have no power to send its song home.",
        "action": "{name} counted the satellite's harmonic pulses and timed a careful grappling line between the swings.",
        "resolution": "The line caught the panel at the quiet part of the rhythm, and {pilot} pulled it gently into place.",
        "cause": "a loose solar panel swung as the satellite spun toward the moon's cold side",
        "deed": "timed a grappling line to the quiet part of the harmonic rhythm",
        "result": "the panel was secured before the satellite lost power",
    },
    {
        "lead": "A tiny rescue beacon on the {satellite} played a cheerful chime.",
        "trigger": "Then the chime slowed until each note sounded far apart, and the satellite began sinking into a deep shadow.",
        "risk": "The shadow could make the beacon too weak for the ship's receiver to follow.",
        "action": "{name} tapped the same rhythm on the navigation panel while {robot} aimed the receiver toward the fading notes.",
        "resolution": "The receiver locked on just before the last note vanished, and the crew guided the satellite into starlight.",
        "cause": "the rescue beacon slowed while the satellite sank into deep shadow",
        "deed": "repeated the rhythm while the robot aimed the receiver at the fading notes",
        "result": "the receiver found the satellite and guided it back into starlight",
    },
    {
        "lead": "{pilot} spotted the {satellite} tumbling above a bright ring of ice around {moon}.",
        "trigger": "A burst of static filled the radio, and the satellite's careful song became a jumble of crackles.",
        "risk": "The ship could mistake the static for a new signal and turn the wrong way.",
        "action": "{name} separated the high note from the crackles and called, 'Follow the clear tone!'",
        "resolution": "{pilot} followed the clean note, and the satellite drifted out from the ice ring.",
        "cause": "static mixed with the satellite's song near a bright ice ring",
        "deed": "separated the clear high note from the crackles",
        "result": "the pilot followed the true signal out of the ice ring",
    },
    {
        "lead": "The {satellite} was almost home when its navigation light began blinking in a nervous pattern.",
        "trigger": "Each blink made the ship's map redraw, sending the suggested route closer to a dark gravity pocket.",
        "risk": "One wrong turn could pull both machines off course.",
        "action": "{name} noticed that every safe note was followed by a pause and told {pilot} to trust the pauses, not the flashing map.",
        "resolution": "The ship waited through the pauses, then guided the satellite around the gravity pocket.",
        "cause": "the satellite's faulty light suggested a dangerous route near a gravity pocket",
        "deed": "trusted the safe pauses in the signal instead of the faulty map",
        "result": "the ship guided the satellite around the gravity pocket",
    },
    {
        "lead": "{robot} heard the {satellite} singing from beyond {moon}, where the stars looked thin and far away.",
        "trigger": "The song suddenly echoed twice, making it seem as if two satellites were drifting in opposite directions.",
        "risk": "Choosing the wrong echo could send the rescue ship away from the real satellite.",
        "action": "{name} compared the volume of each echo and chose the stronger one, which came from the nearby satellite.",
        "resolution": "The false echo faded, and the real satellite answered with a bright, steady note.",
        "cause": "two echoes made the satellite seem to be in opposite directions",
        "deed": "compared the echoes and followed the stronger signal",
        "result": "the false echo faded and the real satellite answered clearly",
    },
    {
        "lead": "The crew flew beneath {moon} while the {satellite} sent a slow, beautiful melody.",
        "trigger": "A sudden solar gust pushed the satellite sideways, away from the ship's guiding beam.",
        "risk": "The beam reached only a little farther, and the satellite was sliding beyond it.",
        "action": "{name} and {robot} sang the melody together so the guidance system could stretch the beam toward the sound.",
        "resolution": "The beam touched the satellite again, and its orbit curved gently back toward the ship.",
        "cause": "a solar gust pushed the satellite beyond the ship's guiding beam",
        "deed": "sang the melody with the robot to extend the guidance beam",
        "result": "the beam reached the satellite and curved it safely home",
    },
]

SOUNDS = [
    "The ship replied, 'Bwoo-whee, bwoo-whee!' The two sounds fit together like puzzle pieces.",
    "'Ding, ding, whoosh!' went the receiver. 'That is not random,' said {name}. 'It is a pattern we can follow.'",
    "{robot} made a careful imitation: 'Loo-la-lum.' {name} answered, 'Again, but softer.' The receiver steadied.",
    "The controls played a tiny fanfare: 'Pip-pip, shuuu!' Everyone listened until the next note arrived.",
    "'Hummm-pop-hummm!' sang the satellite. {pilot} smiled. 'A good rescue can have a good rhythm.'",
    "{name} clapped once, and {robot} clicked twice. 'Clap, click, clap,' they said, turning the rescue into a calm beat.",
    "The radio whispered, 'Zee-oo-zah.' Then the ship echoed it, and the dark window seemed less lonely.",
    "'Brrr-ring!' cried the alarm. {name} answered, 'Not panic—listen!' The crew grew quiet enough to hear the true signal.",
]

ENDINGS = [
    "When the rescue was done, the {satellite} blinked three happy lights above {moon}. Its harmonic song became a thank-you heard across the stars.",
    "Back aboard the ship, {name} drew the signal as three golden waves. {robot} added a tiny music note, and the rescued satellite shone outside.",
    "The {satellite} settled into its new orbit and sent one clear chime. This time, the sound did not mean danger. It meant home.",
    "As the ship flew away, {moon} glowed below them. The crew heard the rescued satellite humming safely behind their trail of silver starlight.",
    "{pilot} gave {name} a navigator badge shaped like a little speaker. It jingled whenever the ship made a careful turn.",
    "The next morning, the ship's radio played the same three notes. Everyone smiled, because now they knew exactly what the music meant.",
    "{robot} recorded the rescue song, but left space at the end for a new note. 'For the next adventure,' said {name}.",
    "The stars seemed to sway with the final melody. The satellite was safe, the ship was steady, and the strange sound had become a friendly hello.",
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child(N) :- name(N).
pilot(P) :- pilot_name(P).
robot(R) :- robot_name(R).
moon(M) :- moon_name(M).
satellite(S) :- satellite_name(S).
signal(X) :- signal_name(X).

compatible(S, X) :- satellite_name(S), signal_name(X), harmonic(S, X).
valid(N, S, X) :- name(N), compatible(S, X).
valid_story(N, P, R, M) :- valid(N, S, X), pilot_name(P), robot_name(R), moon_name(M).
"""


HARMONIC_PAIRS = [
    ("weather satellite", "a bright three-note hum"),
    ("garden satellite", "a soft bell-like pulse"),
    ("star-map satellite", "a rising radio song"),
    ("message satellite", "a chiming space rhythm"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in NAMES:
        lines.append(asp.fact("name", value))
    for value in PILOTS:
        lines.append(asp.fact("pilot_name", value))
    for value in ROBOTS:
        lines.append(asp.fact("robot_name", value))
    for value in MOONS:
        lines.append(asp.fact("moon_name", value))
    for value in SATELLITES:
        lines.append(asp.fact("satellite_name", value))
    for value in SIGNALS:
        lines.append(asp.fact("signal_name", value))
    for satellite, signal in HARMONIC_PAIRS:
        lines.append(asp.fact("harmonic", satellite, signal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return list(HARMONIC_PAIRS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({(satellite, signal) for _, satellite, signal in asp.atoms(model, "valid")})


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    clingo_pairs = set(asp_valid_combos())
    if python_pairs == clingo_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_pairs - clingo_pairs:
        print("  only in python:", sorted(python_pairs - clingo_pairs))
    if clingo_pairs - python_pairs:
        print("  only in clingo:", sorted(clingo_pairs - python_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.satellite and args.signal:
        if (args.satellite, args.signal) not in combos:
            raise StoryError("No story: that satellite and signal do not form a harmonic pair.")
    if args.satellite:
        combos = [pair for pair in combos if pair[0] == args.satellite]
    if args.signal:
        combos = [pair for pair in combos if pair[1] == args.signal]
    if not combos:
        raise StoryError("No harmonic satellite-and-signal pair matches the given options.")
    satellite, signal = rng.choice(sorted(combos))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        pilot=args.pilot or rng.choice(PILOTS),
        robot=args.robot or rng.choice(ROBOTS),
        moon=args.moon or rng.choice(MOONS),
        satellite=satellite,
        signal=signal,
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        sound=rng.randrange(len(SOUNDS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.sound = (seed // 3) % len(SOUNDS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    if (params.satellite, params.signal) not in valid_combos():
        raise StoryError("The requested satellite and signal are not a harmonic rescue pair.")

    values = {
        "name": params.name,
        "pilot": params.pilot,
        "robot": params.robot,
        "moon": params.moon,
        "satellite": params.satellite,
        "signal": params.signal,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(Entity(params.name, "character", params.name, memes={"curiosity": 1.0}))
    pilot = world.add(Entity(params.pilot, "character", params.pilot))
    robot = world.add(Entity(params.robot, "character", params.robot))
    moon = world.add(Entity("moon", "place", params.moon, meters={"distance": 1.0}))
    satellite = world.add(
        Entity(
            "satellite",
            "machine",
            params.satellite,
            meters={"orbit": 0.3, "signal_strength": 0.8},
            memes={"danger": 0.0, "belonging": 0.0},
        )
    )
    signal = world.add(
        Entity(
            "signal",
            "sound",
            params.signal,
            meters={"pitch": 0.6, "rhythm": 1.0},
            memes={"harmony": 1.0},
        )
    )

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(f"The ship's speakers answered with {params.signal}, while {params.robot} watched the instruments and {params.pilot} kept the engines gentle.")
    world.say(incident["lead"].format(**values))

    world.para()
    satellite.meters["orbit"] = 0.9
    satellite.memes["danger"] = 1.0
    signal.meters["signal_strength"] = 0.5
    child.memes["curiosity"] = 1.0
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(f"'{params.signal.capitalize()},' whispered {params.robot}. 'Can you hear the pattern?' asked {params.name}. 'I can hear it,' said {params.robot}.")
    world.say(incident["action"].format(**values))

    world.para()
    satellite.meters["orbit"] = 0.1
    satellite.meters["signal_strength"] = 1.0
    satellite.memes["danger"] = 0.0
    satellite.memes["belonging"] = 1.0
    child.memes["relief"] = 1.0
    world.say(incident["resolution"].format(**values))
    world.say(SOUNDS[params.sound % len(SOUNDS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        explorer=params.name,
        pilot=params.pilot,
        robot=params.robot,
        moon=params.moon,
        satellite=params.satellite,
        signal=params.signal,
        incident=params.incident % len(INCIDENTS),
        suspense_cause=incident["cause"],
        helpful_action=incident["deed"],
        result=incident["result"],
        harmonic=True,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly harmonic space adventure with suspense and playful sound effects.",
        f"Tell a space rescue story in which {params.name} uses a harmonic signal to help a drifting {params.satellite}.",
        f"Write a suspenseful space adventure featuring {params.moon}, {params.robot}, sound effects, and a safe rescue.",
    ]

    story_qa = [
        QAItem(
            question="Who helped with the space rescue?",
            answer=f"{params.name} helped {params.pilot} and {params.robot} rescue the drifting {params.satellite}.",
        ),
        QAItem(
            question="What made the rescue suspenseful?",
            answer=f"It was suspenseful because {incident['cause']}. The crew had to listen carefully before the danger grew.",
        ),
        QAItem(
            question=f"What did {params.name} do?",
            answer=f"{params.name} {incident['deed']}. That choice gave the crew a safe way to find or guide the satellite.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"In the end, {incident['result']}. The satellite was safe, and its harmonic sound became a friendly signal.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does harmonic mean?",
            answer="Harmonic means that sounds fit together in a pleasing pattern, like notes in a simple song.",
        ),
        QAItem(
            question="Why are sound effects useful in a space adventure?",
            answer="Sound effects help readers imagine what the ship, radio, alarms, and machines are doing.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while a problem is still dangerous or uncertain.",
        ),
        QAItem(
            question="Why might a spacecraft use a signal?",
            answer="A spacecraft might use a signal to send information, show its location, or ask another spacecraft for help.",
        ),
        QAItem(
            question="What is an orbit?",
            answer="An orbit is the curved path an object follows around a planet, moon, or another large object.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        pieces = []
        if entity.meters:
            pieces.append(f"meters={entity.meters}")
        if entity.memes:
            pieces.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(pieces)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            name="Luna",
            pilot="Captain Vale",
            robot="Bleep",
            moon="Moon Rilla",
            satellite="weather satellite",
            signal="a bright three-note hum",
            incident=0,
            premise=0,
            sound=0,
            ending=0,
        ),
        StoryParams(
            name="Milo",
            pilot="Pilot Juno",
            robot="Orbit",
            moon="the blue moon",
            satellite="garden satellite",
            signal="a soft bell-like pulse",
            incident=2,
            premise=2,
            sound=2,
            ending=2,
        ),
        StoryParams(
            name="Suri",
            pilot="Commander Sol",
            robot="Tink",
            moon="Moon Pebble",
            satellite="star-map satellite",
            signal="a rising radio song",
            incident=5,
            premise=3,
            sound=5,
            ending=5,
        ),
        StoryParams(
            name="Nova",
            pilot="Pilot Mira",
            robot="Mica",
            moon="the silver moon",
            satellite="message satellite",
            signal="a chiming space rhythm",
            incident=7,
            premise=5,
            sound=7,
            ending=7,
        ),
    ]


CURATED = build_curated()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A harmonic space-adventure storyworld with suspense and sound effects."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--pilot", choices=PILOTS)
    parser.add_argument("--robot", choices=ROBOTS)
    parser.add_argument("--moon", choices=MOONS)
    parser.add_argument("--satellite", choices=SATELLITES)
    parser.add_argument("--signal", choices=SIGNALS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


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
        print(asp_program("#show valid_story/4."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story.split()) < 40:
                print("Generated story check failed.")
                sys.exit(1)
        print("OK: generated stories passed the reasonableness check.")
        return

    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} harmonic satellite-and-signal pairs:\n")
        for satellite, signal in pairs:
            print(f"  {satellite:20} -> {signal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name}: harmonic rescue of the {params.satellite}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
