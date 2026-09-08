#!/usr/bin/env python3
"""
A small standalone Space Adventure storyworld about a rickety craft,
vibrating sound effects, and the sharing that helps everyone reach home.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str
    condition: str = "rickety"
    sound: str = "a vibrating hum"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    pilot: str
    helper: str
    ship_name: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    task: str
    trouble: str
    mistake: str
    consequence: str
    clue: str
    careful_action: str
    reveal: str
    sharing: str
    outcome: str
    lesson: str
    ending: str


PILOT_NAMES = ["Luna", "Mira", "Nova", "Ari", "Zia", "Tess"]
HELPER_NAMES = ["Pip", "Bo", "Jax", "Kio", "Tavi", "Rua"]
PLACES = [
    "the blue comet lane",
    "the quiet moon field",
    "the ringed planet's shadow",
    "the lantern asteroid belt",
]
SHIP_NAMES = ["Star Cricket", "Moon Kite", "Silver Acorn", "Bright Pebble"]
TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "mystery", "promise"]

SCENARIOS = [
    Scenario(
        "rescue_beacon",
        "carry a rescue beacon to a drifting family shuttle",
        "the ship's old engine began to vibrate beside a field of sleeping satellites",
        "turned up the engine until its rickety panels rattled",
        "the loud sound woke the satellites and made their signals overlap",
        "one soft vibration answered each clear beep from the family shuttle",
        "lowered the engine and tapped the ship's hull in the shuttle's rhythm",
        "the satellites were not attacking; they were sharing a map by echo",
        "shared the ship's quiet signal with every satellite and let the shuttle choose the safe path",
        "the family shuttle followed the joined map to the rescue beacon",
        "sharing a useful sound can make a confusing space feel safe",
        "the rescued family waved as the satellites blinked one gentle beat at a time",
    ),
    Scenario(
        "comet_garden",
        "bring water to a tiny garden growing on a comet",
        "a rickety cargo pump started to vibrate and shook loose the water hose",
        "grabbed the hose and pulled it tight without checking the pump",
        "the hose sprayed water into space while the comet flowers folded shut",
        "the pump's vibration matched the flowers' tiny ringing leaves",
        "shared the work between the pump and a hand bell so the rhythm stayed gentle",
        "the pump was asking the flowers when they were ready to drink",
        "shared water in small pulses while the flowers rang back",
        "the comet garden opened its silver petals and caught every drop",
        "listening and sharing can turn a noisy machine into a helpful friend",
        "silver petals bobbed in the starlight while the old pump hummed proudly",
    ),
    Scenario(
        "lost_moon_robot",
        "guide a small robot back to its moon workshop",
        "a rickety navigation dish began to vibrate whenever the robot spoke",
        "silenced the robot so the dish would stop shaking",
        "the robot lost its directions and rolled toward a dark asteroid",
        "the dish shook only when the robot said the names of safe stars",
        "asked the robot to share its star words while the crew recorded each vibration",
        "the dish was turning the robot's voice into a route home",
        "shared the recordings with the robot and let it choose the safest sequence",
        "the dish pointed home and the robot reached its workshop",
        "people solve more safely when the one who knows the path gets to speak",
        "the robot tapped a happy rhythm as a hundred workshop lights answered",
    ),
    Scenario(
        "festival_signal",
        "deliver a music signal to three planets preparing a space festival",
        "the ship's rickety speaker made every sound vibrate into a different pitch",
        "sent the whole song at once",
        "each planet heard a different piece and thought the others had refused to join",
        "the same little drumbeat appeared beneath all three broken songs",
        "asked each planet to share its drumbeat before sending the next sound",
        "the speaker had a loose coil, but its vibration could carry one shared rhythm",
        "joined the three drumbeats into a simple signal and repaired the coil together",
        "the planets heard one song and opened their festival domes",
        "sharing small parts can help everyone hear the whole idea",
        "three planets spun their lights together while the repaired speaker chimed",
    ),
    Scenario(
        "ice_cave_echo",
        "carry warm blankets through an ice moon cave",
        "a rickety rover began to vibrate near a maze of echoing tunnels",
        "drove faster toward the first bright opening",
        "the rover bounced into a dead end and the blankets slid from its cargo bed",
        "the rover's vibration changed whenever an echo came from a safe tunnel",
        "shared the steering between the pilot and the rover's listening drum",
        "the cave was using echoes to warn them away from thin ice",
        "shared the blankets between two stranded miners and followed the safe echoes together",
        "everyone crossed the cave warm and secure",
        "a careful shared plan is stronger than a fast guess",
        "the rover's rickety wheels rested beside a warm circle of grateful friends",
    ),
    Scenario(
        "shadow_meteor",
        "watch a meteor shower from a small research station",
        "a rickety observation platform began to vibrate as a dark meteor passed",
        "claimed the vibration meant the platform was breaking and sent everyone outside",
        "the researchers lost the shelter of the station during a glittering storm",
        "the vibration repeated whenever the meteor's shadow covered the platform",
        "shared the readings with the station's quiet computer and waited for its pattern",
        "the platform was safely tracking the meteor's hidden metal core",
        "shared the shelter and the readings so every researcher could watch from safety",
        "the meteor passed and revealed a shining core for everyone to study",
        "sharing evidence before fear can help a crew choose wisely",
        "inside the station, every face glowed in the reflected light of the meteor core",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld about vibrating rickety ships and sharing."
    )
    parser.add_argument("--pilot", choices=PILOT_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--ship-name")
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pilot = args.pilot or rng.choice(PILOT_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != pilot]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        pilot=pilot,
        helper=helper,
        ship_name=args.ship_name or rng.choice(SHIP_NAMES),
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("theme", "space_adventure"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "sharing"),
        asp.fact("seed_word", "vibrate"),
        asp.fact("seed_word", "rickety"),
        asp.fact("ship_trait", "rickety"),
        asp.fact("sound_action", "vibrate"),
        asp.fact("value", "sharing"),
    ]
    return "\n".join(facts)


ASP_RULES = r"""
required_feature(sound_effects) :- feature(sound_effects).
required_feature(sharing) :- feature(sharing).
required_seed(vibrate) :- seed_word(vibrate).
required_seed(rickety) :- seed_word(rickety).
valid_world :- required_feature(sound_effects),
               required_feature(sharing),
               required_seed(vibrate),
               required_seed(rickety).
#show required_feature/1.
#show required_seed/1.
#show valid_world/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(asp.atoms(model, "required_feature"))
    seeds = sorted(asp.atoms(model, "required_seed"))
    valid = bool(asp.atoms(model, "valid_world"))
    if (
        features == [("sharing",), ("sound_effects",)]
        and seeds == [("rickety",), ("vibrate",)]
        and valid
    ):
        print("OK: ASP and Python registries agree.")
        return 0
    print("MISMATCH: ASP twin is incomplete.")
    print({"features": features, "seeds": seeds, "valid": valid})
    return 1


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    pilot = params.pilot
    helper = params.helper
    ship = params.ship_name
    place = params.place
    mode = params.telling_mode or "arrival"

    if mode == "warning":
        return [
            f'"The hull is starting to vibrate," {helper} warned as {ship} entered {place}.',
            f"Captain {pilot} slowed the rickety ship. The crew had come to {scenario.task}.",
        ]
    if mode == "dialogue":
        return [
            f'"Ready for a careful trip?" Captain {pilot} asked. "Careful is best in a rickety ship," {helper} replied.',
            f"Together they crossed {place} to {scenario.task}.",
        ]
    if mode == "countdown":
        return [
            f"The ship's clock counted down as {ship} drifted through {place}.",
            f"Before it reached zero, Captain {pilot} and {helper} had to {scenario.task}.",
        ]
    if mode == "mystery":
        return [
            f"A strange vibration traveled through {ship}, even though the stars around {place} were still.",
            f"Captain {pilot} and {helper} were there to {scenario.task}.",
        ]
    if mode == "promise":
        return [
            f"Captain {pilot} had made a promise, so the rickety {ship} carried the crew through {place}.",
            f"They had come to {scenario.task}.",
        ]
    return [
        f"The rickety {ship} glided into {place}, making a soft vibrating sound.",
        f"Captain {pilot} and {helper} were there to {scenario.task}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.pilot or not params.helper:
        raise StoryError("A pilot and helper are required.")
    if params.pilot == params.helper:
        raise StoryError("The pilot and helper must have different names.")
    if params.scenario not in {s.key for s in SCENARIOS}:
        raise StoryError(f"Unknown scenario: {params.scenario!r}.")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode: {params.telling_mode!r}.")

    rng = random.Random(params.seed)
    scenario = next(s for s in SCENARIOS if s.key == params.scenario)
    ship = Ship(name=params.ship_name, setting=params.place)
    world = World(ship)

    pilot = world.add(
        Entity(
            id=params.pilot,
            kind="character",
            type="pilot",
            label="captain",
            location="cockpit",
            meters={"alertness": 0.8, "trust": 0.5},
            memes={"sharing": 0.4},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="engineer",
            label="helper",
            location="engine room",
            meters={"alertness": 0.8, "trust": 0.5},
            memes={"listening": 0.5},
        )
    )
    engine = world.add(
        Entity(
            id="engine",
            kind="machine",
            type="rickety_engine",
            label="rickety engine",
            location="engine room",
            meters={"vibration": 1.0, "stability": 0.35},
            memes={"warning": 0.7},
        )
    )
    world.facts.update(
        pilot=pilot,
        helper=helper,
        engine=engine,
        task=scenario.task,
        trouble=scenario.trouble,
        mistake=scenario.mistake,
        consequence=scenario.consequence,
        clue=scenario.clue,
        reveal=scenario.reveal,
        sharing=scenario.sharing,
        outcome=scenario.outcome,
        lesson=scenario.lesson,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(
        random.Random((params.seed or 0) + 11).choice(
            [
                f"Then a new sound filled the cabin: {scenario.trouble}.",
                f"Suddenly, the rickety ship gave a long vibrate-and-clank: {scenario.trouble}.",
                f"The calm trip changed when the instruments reported that {scenario.trouble}.",
            ]
        )
    )

    world.para()
    world.say(
        rng.choice(
            [
                f'"I can stop it quickly," {helper.id} said, and {helper.pronoun()} {scenario.mistake}.',
                f"Because the sound seemed dangerous, {helper.id} {scenario.mistake} before the crew could study it.",
                f'"That vibration is telling us something," Captain {pilot.id} said, but {helper.id} {scenario.mistake}.',
            ]
        )
    )
    world.say(f"The rushed choice caused trouble: {scenario.consequence}.")
    world.say(
        rng.choice(
            [
                f'"Wait," Captain {pilot.id} said. "Let us share what we know before we act again."',
                f'{helper.id} looked at Captain {pilot.id}. "I heard the vibration change." "Then we will listen together," Captain {pilot.id} replied.',
                f'"No one has to solve this alone," Captain {pilot.id} told the crew.',
            ]
        )
    )

    world.para()
    world.say(f"They listened carefully and discovered that {scenario.clue}.")
    world.say(f"Captain {pilot.id} {scenario.careful_action}.")
    world.say(
        rng.choice(
            [
                f"The sound became a clue. They learned that {scenario.reveal}.",
                f"Once the crew shared their observations, the hidden truth was clear: {scenario.reveal}.",
                f"The rickety noise was not only a problem. It was a message: {scenario.reveal}.",
            ]
        )
    )

    world.para()
    world.say(f"Together, the crew {scenario.sharing}.")
    world.say(
        rng.choice(
            [
                f'"Your idea helped us hear the next step," Captain {pilot.id} told {helper.id}.',
                f'"We fixed this by sharing," {helper.id} said. Captain {pilot.id} nodded. "And by listening."',
                f"Captain {pilot.id} thanked {helper.id}, and {helper.id} shared the final control with the whole crew.",
            ]
        )
    )
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(f"They carried one lesson onward: {scenario.lesson}.")
    world.say(f"As {ship.name} moved through space, {scenario.ending}.")

    engine.meters["vibration"] = 0.25
    engine.meters["stability"] = 0.95
    engine.location = "repaired engine room"
    pilot.meters["trust"] = 1.0
    helper.meters["trust"] = 1.0
    pilot.memes["sharing"] = 1.0
    helper.memes["sharing"] = 1.0
    world.facts.update(resolved=True, sound_effects=True, shared_solution=True)

    prompts = [
        f"Write a Space Adventure about {params.pilot} and {params.helper} solving a problem on a rickety ship.",
        f"Tell a child-friendly story using the sound effect of a ship that can vibrate and a solution based on sharing.",
        f"Write an ending image that proves the crew learned that {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the rickety ship have?",
            answer=f"The ship had a vibrating problem because {scenario.trouble}.",
        ),
        QAItem(
            question="What happened when the crew acted too quickly?",
            answer=f"They {scenario.mistake}, and {scenario.consequence}.",
        ),
        QAItem(
            question="What clue helped the crew?",
            answer=f"They noticed that {scenario.clue}. This showed them that {scenario.reveal}.",
        ),
        QAItem(
            question="How did sharing solve the problem?",
            answer=f"The crew {scenario.sharing}. As a result, {scenario.outcome}.",
        ),
        QAItem(
            question="What lesson did the crew learn?",
            answer=f"They learned that {scenario.lesson}. The repaired ship and shared plan showed that lesson.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean when something vibrates?",
            answer="It moves back and forth quickly, often making a hum, buzz, or rattle.",
        ),
        QAItem(
            question="What can sound effects do in a space story?",
            answer="Sound effects can show that a machine is working, warn of danger, or give characters a clue.",
        ),
        QAItem(
            question="Why is sharing useful during an adventure?",
            answer="Sharing observations, tools, and decisions lets a crew combine its knowledge and solve problems more safely.",
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            bits = [f"location={entity.location}"]
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(bits)}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _verify_python() -> None:
    params = StoryParams(
        pilot="Luna",
        helper="Pip",
        ship_name="Star Cricket",
        place=PLACES[0],
        seed=17,
        scenario="rescue_beacon",
        telling_mode="dialogue",
    )
    sample = generate(params)
    required = ["vibrate", "rickety", "sharing"]
    lower = sample.story.lower()
    missing = [word for word in required if word not in lower]
    if missing:
        raise StoryError(f"Generated story is missing required words: {', '.join(missing)}.")
    if len(sample.story_qa) < 3:
        raise StoryError("Generated story has too few grounded QA items.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/0."))
        return

    if args.verify:
        _verify_python()
        status = asp_verify()
        if status == 0:
            print("OK: generated story also passed Python checks.")
        sys.exit(status)

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for symbol in sorted(str(item) for item in model):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Pip", "Star Cricket", PLACES[0], 101, "rescue_beacon", "arrival"),
            StoryParams("Mira", "Bo", "Moon Kite", PLACES[1], 202, "comet_garden", "dialogue"),
            StoryParams("Nova", "Jax", "Silver Acorn", PLACES[2], 303, "festival_signal", "mystery"),
            StoryParams("Ari", "Kio", "Bright Pebble", PLACES[3], 404, "lost_moon_robot", "warning"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            seed = base_seed + attempt
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
        header = ""
        if args.all:
            header = f"### {sample.params.pilot} and {sample.params.helper}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
