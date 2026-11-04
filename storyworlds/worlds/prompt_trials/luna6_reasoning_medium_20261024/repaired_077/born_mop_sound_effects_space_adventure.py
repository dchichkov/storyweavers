#!/usr/bin/env python3
"""
A small space-adventure story world about Luna, born among the stars, and Mop,
the soft-headed robot who helps her find a safe route through a station.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_STORYWORLDS_DIR = next(
    (parent for parent in Path(__file__).resolve().parents if parent.name == "storyworlds"),
    Path(__file__).resolve().parents[3],
)
sys.path.insert(0, str(_STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Being:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    station: str
    incident: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Being
    mop: Being
    station: str
    incident: str
    rover_safe: bool = False
    path_clear: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Luna", "Mira", "Tavi", "Niko", "Suri", "Pip"]
STATIONS = ["the Starling", "the Little Orbit", "the Comet"]
INCIDENTS = [
    {
        "key": "moon_dust",
        "title": "The Dusty Beacon Trail",
        "obstacle": "a drift of moon dust had blurred the blue guide stripe",
        "wrong_turn": "started toward the dark service hatch instead of the beacon corridor",
        "clue": "Mop's scanner found the blue stripe shining faintly beneath the powder",
        "sound": "KRR-SH, went the dust against the rover wheels",
        "robot_line": "Wait, Luna. My scanner sees the beacon stripe under that dust.",
        "choice": "stopped the rover and asked Mop to clear the stripe a little at a time",
        "repair": "Mop lowered its soft mop head and swept the dust into a sealed floor bin",
        "risk": "loose moon dust could scratch the rover's wheels and hide the safe route",
        "ending": "the blue stripe led the rover to the blinking beacon, while the dust rested behind a closed bin lid",
        "lesson": "Luna learned that a quiet scan can be more useful than a fast guess.",
        "trace": "The rover followed the stripe Mop uncovered, so its wheels stayed out of the loose dust.",
    },
    {
        "key": "berry_spill",
        "title": "The Berry-Slick Charging Lane",
        "obstacle": "a pouch of bright space berries had spilled across the rover's charging lane",
        "wrong_turn": "reached for the rover's controls before noticing the shiny patch under its wheels",
        "clue": "Mop's floor lamp showed that the red shine was berry juice, not a flashing signal",
        "sound": "PLOP, plip, plop, went the last berry against the deck",
        "robot_line": "Luna, that red blink is a slippery spill. The charging arrow is underneath it.",
        "choice": "told the rover to hold still and asked Mop to clean before anyone crossed",
        "repair": "Mop mopped the juice with its absorbent pad and rolled the berries into a covered tray",
        "risk": "a slick charging lane could send the small rover skidding into the tool rack",
        "ending": "the dry charging arrow gleamed beneath the rover as its little green charge light came on",
        "lesson": "Luna learned that stopping for one careful look can keep a small spill from becoming a big tumble.",
        "trace": "Mop cleaned the juice before the rover moved, leaving the charging lane dry and clear.",
    },
    {
        "key": "frost_beads",
        "title": "The Frosty Greenhouse Passage",
        "obstacle": "tiny frost beads had scattered across the passage outside the greenhouse",
        "wrong_turn": "hurried to the rover's distant signal without checking the slippery floor",
        "clue": "Mop's temperature light showed that the beads came from the chilly greenhouse vent",
        "sound": "TIK-tik-tik, chimed the frost beads beneath the station fan",
        "robot_line": "Luna, the floor is slick by the vent. Let's make a dry path first.",
        "choice": "paused the rover and asked Mop to dry the passage from the wall inward",
        "repair": "Mop used its warm, soft pad to gather the frost beads into a small covered cup",
        "risk": "frost on the floor could make Luna or the rover slide near the greenhouse door",
        "ending": "a dry path curved safely past the greenhouse, and the rover's signal blinked beside a row of green leaves",
        "lesson": "Luna learned that helping quickly also means making sure the way there is safe.",
        "trace": "Mop dried the passage before Luna guided the rover through it.",
    },
    {
        "key": "paper_stars",
        "title": "The Paper-Star Rescue",
        "obstacle": "a burst of paper stars had covered the tiny rover's floor arrow",
        "wrong_turn": "pointed the rover toward the airlock before checking whether the arrow was covered",
        "clue": "Mop's scanner spotted the real arrow beneath the paper stars",
        "sound": "FWOOP! The station fan sent the paper stars twirling like a tiny galaxy",
        "robot_line": "Luna, those are craft stars, not the rover's silver direction lights.",
        "choice": "held the rover still and asked Mop to uncover the arrow without chasing the flying stars",
        "repair": "Mop gathered the paper stars with its dry mop head and tucked them into their craft envelope",
        "risk": "a hidden floor arrow could send the rover toward the wrong hatch",
        "ending": "the silver arrow pointed home again, and the paper stars sparkled safely inside their envelope",
        "lesson": "Luna learned that even a beautiful distraction can hide an important sign.",
        "trace": "Mop uncovered the silver arrow and put the paper stars away before the rover rolled.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gentle space adventure with Luna and Mop."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--station", choices=STATIONS)
    parser.add_argument("--incident", choices=[item["key"] for item in INCIDENTS])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        station=args.station or rng.choice(STATIONS),
        incident=args.incident or rng.choice(INCIDENTS)["key"],
        seed=args.seed,
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("Choose a hero name from the station's crew list.")
    if params.station not in STATIONS:
        raise StoryError("That station is not part of this little space adventure.")
    if params.incident not in {item["key"] for item in INCIDENTS}:
        raise StoryError("That space mishap is not in Mop's mission log.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = next(item for item in INCIDENTS if item["key"] == params.incident)
    hero = Being(
        name=params.hero_name,
        kind="young space explorer",
        meters={"worry": 0.65, "confidence": 0.35},
        memes={"curious": 1.0, "careful": 0.7},
    )
    mop = Being(
        name="Mop",
        kind="soft-headed cleaning robot",
        meters={"battery": 0.82, "pad_cleanliness": 0.75},
        memes={"patient": 1.0, "observant": 1.0},
    )
    world = World(
        hero=hero,
        mop=mop,
        station=params.station,
        incident=params.incident,
        meters={"route_visibility": 0.2, "rover_safety": 0.35},
        memes={"teamwork": 0.6, "bravery": 0.5},
    )

    born_detail = rng.choice(
        [
            f"{hero.name} was born aboard {params.station}, where the window showed stars instead of rooftops.",
            f"{hero.name}, born among the stars aboard {params.station}, knew the station's gentle nighttime hum by heart.",
            f"Since {hero.name} was born on {params.station}, the soft blue lights of its corridors had always felt like home.",
        ]
    )
    opening_sound = rng.choice(["WHUMM, hummed the station fans.", "BIP-bip, blinked the rover beacon.", "TUNK, tapped a loose tool against its rack."])
    listening_line = rng.choice(
        [
            f'"You heard that before I did," {hero.name} said. "Show me what you found."',
            f'"Good catch, Mop," {hero.name} replied. "I will wait while you check."',
            f'{hero.name} took a breath. "Then I should not rush the rover. Let us make the route safe first."',
        ]
    )
    followup = rng.choice(
        [
            f'"Ready when you are," said {hero.name}. "I can guide the rover once the way is clear."',
            f'"I see it now," {hero.name} said. "The clue changes what we should do."',
            f'"Thank you for checking," {hero.name} said. "Let us use the safe path, not the quickest guess."',
        ]
    )

    lines = [
        born_detail,
        f"That shift, {hero.name} was helping Mop guide a little scout rover back to its beacon.",
        opening_sound,
        f"Then {incident['obstacle']}. {incident['sound']}.",
        f"In the hurry, {hero.name} {incident['wrong_turn']}.",
        f"Mop's round lamp blinked amber. \"{incident['robot_line']}\"",
        listening_line,
        f"Instead of rushing, {hero.name} {incident['choice']}.",
        f"The clue was clear: {incident['clue']}.",
        f"That mattered because {incident['risk']}.",
        f"With the route checked, {incident['repair']}.",
        followup,
        f"At last, {incident['ending']}.",
        incident["lesson"],
        f"From the station window, the stars looked just as bright, but {hero.name} now knew that a good space team made room for a careful check.",
    ]

    world.path_clear = True
    world.rover_safe = True
    world.meters.update({"route_visibility": 1.0, "rover_safety": 1.0})
    hero.meters.update({"worry": 0.15, "confidence": 0.9})
    mop.meters.update({"battery": 0.68, "pad_cleanliness": 0.35})
    world.memes.update({"teamwork": 1.0, "bravery": 0.9})
    world.facts.update(
        {
            "obstacle": incident["obstacle"],
            "clue": incident["clue"],
            "risk": incident["risk"],
            "method": incident["repair"],
            "ending": incident["ending"],
            "lesson": incident["lesson"],
        }
    )
    story = " ".join(lines)
    world.facts["story"] = story

    prompts = [
        f"Write a child-friendly space adventure about {params.hero_name}, born aboard {params.station}, and a helpful mop robot.",
        f"Tell how the crew handles {incident['obstacle']} after Mop notices a clue.",
        "Use sound effects and spoken dialogue that helps the explorer make a safer choice.",
    ]
    story_qa = [
        QAItem(
            question=f"Where was {params.hero_name} born?",
            answer=f"{params.hero_name} was born aboard {params.station}, where the stars shone beyond the station windows.",
        ),
        QAItem(
            question=f"What space mishap did {params.hero_name} and Mop face?",
            answer=f"They faced a problem when {incident['obstacle']}.",
        ),
        QAItem(
            question="What clue helped them understand what was happening?",
            answer=f"Mop's clue was that {incident['clue']}.",
        ),
        QAItem(
            question="How did Mop help make the route safe?",
            answer=f"Mop helped by doing this: {incident['repair']}.",
        ),
        QAItem(
            question="Why did they check the route before moving the rover?",
            answer=f"They checked first because {incident['risk']}.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"It ended when {incident['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a mop do?",
            answer="A mop uses a soft or absorbent head to clean a floor and gather spills or dirt.",
        ),
        QAItem(
            question="Why should a rover follow a marked route inside a station?",
            answer="A marked route helps a rover avoid hazards and reach the right place without wandering toward a dangerous hatch or piece of equipment.",
        ),
        QAItem(
            question="Why can loose dust be a problem in a space station?",
            answer="Loose dust can hide markings and may scratch or interfere with equipment, so station crews carefully contain and clean it.",
        ),
        QAItem(
            question="What is a beacon?",
            answer="A beacon is a signal or light that helps people or machines find a location.",
        ),
        QAItem(
            question="What is a safe first step when a route looks blocked?",
            answer="Pause, look for a reliable clue, and ask a teammate for help before moving through a possibly unsafe area.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        world = sample.world
        print("\n--- trace ---")
        print(
            f"hero={world.hero.name}, kind={world.hero.kind}, "
            f"meters={world.hero.meters}, memes={world.hero.memes}"
        )
        print(
            f"mop={world.mop.name}, kind={world.mop.kind}, "
            f"meters={world.mop.meters}, memes={world.mop.memes}"
        )
        print(
            f"station={world.station}, incident={world.incident}, "
            f"path_clear={world.path_clear}, rover_safe={world.rover_safe}"
        )
        print(f"world_meters={world.meters}, world_memes={world.memes}")
        for key, value in world.facts.items():
            if key != "story":
                print(f"{key}={value}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_station(S) :- station(S).
valid_incident(I) :- incident(I).
valid_pair(S,I) :- station(S), incident(I), supports(S,I).
mission_can_finish(S,I) :- valid_pair(S,I), safe_method(I).
#show valid_pair/2.
#show mission_can_finish/2.
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("station", station) for station in STATIONS]
    facts.extend(asp.fact("incident", item["key"]) for item in INCIDENTS)
    facts.extend(
        asp.fact("supports", station, item["key"])
        for station in STATIONS
        for item in INCIDENTS
    )
    facts.extend(asp.fact("safe_method", item["key"]) for item in INCIDENTS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid_pair/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_pair")))


def asp_verify() -> int:
    expected = {
        (station, item["key"])
        for station in STATIONS
        for item in INCIDENTS
    }
    try:
        actual = set(asp_valid_pairs())
        finish_model = _asp_finish_pairs()
    except Exception as exc:
        print(f"ASP verification could not run: {exc}")
        return 1

    expected_finish = expected
    if actual != expected or finish_model != expected_finish:
        print("MISMATCH between ASP rules and Python registries.")
        if expected - actual:
            print("  missing valid pairs:", sorted(expected - actual))
        if actual - expected:
            print("  unexpected valid pairs:", sorted(actual - expected))
        if expected_finish - finish_model:
            print("  missing finishable pairs:", sorted(expected_finish - finish_model))
        if finish_model - expected_finish:
            print("  unexpected finishable pairs:", sorted(finish_model - expected_finish))
        return 1

    try:
        for index, item in enumerate(INCIDENTS):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                station=STATIONS[index % len(STATIONS)],
                incident=item["key"],
                seed=100 + index,
            )
            sample = generate(params)
            story = sample.story
            if (
                not sample.world.path_clear
                or not sample.world.rover_safe
                or item["sound"] not in story
                or item["clue"] not in story
                or '"' not in story
                or "born" not in story.lower()
                or not sample.story_qa
                or not any("?" in qa.question for qa in sample.story_qa)
            ):
                raise AssertionError(f"Generated story failed checks for {item['key']}.")
    except Exception as exc:
        print(f"Story generation verification failed: {exc}")
        return 1

    print(
        f"OK: ASP matches Python for {len(expected)} station/incident pairs; "
        f"all {len(INCIDENTS)} incident stories passed generation checks."
    )
    return 0


def _asp_finish_pairs() -> set[tuple]:
    import asp

    model = asp.one_model(
        asp_program("#show mission_can_finish/2.")
    )
    return set(asp.atoms(model, "mission_can_finish"))


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.n < 0:
        raise StoryError("The number of requested stories cannot be negative.")
    if args.all:
        return [
            StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                station=STATIONS[index % len(STATIONS)],
                incident=item["key"],
                seed=(args.seed if args.seed is not None else 0) + index,
            )
            for index, item in enumerate(INCIDENTS)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(args.n)
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_pair/2.\n#show mission_can_finish/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for station, incident in asp_valid_pairs():
            print(f"{station}: {incident}")
        return

    try:
        params_list = generation_samples(args)
        samples: list[StorySample] = []
        for index, params in enumerate(params_list):
            if params.seed is None:
                params.seed = (args.seed if args.seed is not None else 0) + index
            samples.append(generate(params))
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)

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
