#!/usr/bin/env python3
"""A small space-adventure story world about a newborn moon-moth and a mop."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    ship: str
    destination: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    ship: str
    destination: str
    leak: str
    sound: str
    helper: str
    danger: float = 0.0
    confidence: float = 0.0
    mop_ready: bool = False
    course_safe: bool = False
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Pip", "Mira", "Tavi", "Sol", "Nori", "Zuzu", "Orin"]
SHIPS = ["the Comet Kite", "the Starling", "the Blue Button", "the Moon Skipper"]
DESTINATIONS = ["the moon garden", "Saturn's lantern ring", "the quiet red planet", "the comet nursery"]
LEAKS = [
    {
        "name": "a fizzing puddle of moon-melon juice",
        "sound": "PLOOP—SPLASH!",
        "clue": "the juice bubbled toward the ship's warm air vent",
        "repair": "mop up the juice before it could freeze into a slippery patch",
    },
    {
        "name": "a trail of shiny stardust syrup",
        "sound": "TINKLE—SPLOSH!",
        "clue": "the syrup glittered beneath a cracked starberry jar",
        "repair": "mop up the syrup and seal the jar inside its travel crate",
    },
    {
        "name": "a little stream of melted comet snow",
        "sound": "DRIP-DROP—WHOOSH!",
        "clue": "the drops led back to a snowball wedged beside the heater",
        "repair": "mop up the meltwater and move the snowball into the cold locker",
    },
    {
        "name": "a wobbling puddle of blue paint",
        "sound": "SPLOP—SQUEAK!",
        "clue": "a floating brush had left blue dabs beside the map console",
        "repair": "mop up the paint before it could cover the route home",
    },
]
HELPERS = ["the patient robot Pip", "Captain Mira", "the tiny moon-moth", "the ship's cheerful navigation computer"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Newborn moon-moth space-adventure story world.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--destination", choices=DESTINATIONS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        ship=args.ship or rng.choice(SHIPS),
        destination=args.destination or rng.choice(DESTINATIONS),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError("Choose a name from the moon-moth crew list.")
    if params.ship not in SHIPS:
        raise StoryError("That ship is not part of this little space fleet.")
    if params.destination not in DESTINATIONS:
        raise StoryError("That destination is beyond this story's star map.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    leak = rng.choice(LEAKS)
    helper = rng.choice(HELPERS)
    hero = Character(
        name=params.name,
        kind="newborn moon-moth",
        meters={"wings": 0.2, "curiosity": 0.9, "alarm": 0.6},
        memes={"brave": 0.8, "helpful": 0.9},
    )
    world = World(
        hero=hero,
        ship=params.ship,
        destination=params.destination,
        leak=leak["name"],
        sound=leak["sound"],
        helper=helper,
        danger=0.7,
        confidence=0.3,
    )

    opening = rng.choice([
        f"On the night {hero.name} was born, a bright little moon-moth opened its wings aboard {params.ship}.",
        f"{hero.name} had been born among the stars only that morning, and already the tiny moon-moth was exploring {params.ship}.",
        f"Born beneath the ship's silver nursery lamp, {hero.name} was the newest moon-moth on {params.ship}.",
    ])
    lines = [
        opening,
        f"The crew was sailing toward {params.destination}, where moon-flowers waited to open.",
        f"Then came a sound from the galley: {leak['sound']} A puddle of {leak['name']} slid across the deck.",
        f"“That shiny trail is taking us toward the map console!” chirped {hero.name}.",
        f"“And the ship is turning!” said {helper}. “I thought the floor was only reflecting the stars.”",
        f"{hero.name} fluttered close to the puddle but kept clear of the slippery edge. “Look—the spill is moving toward the vent!”",
        f"Together they checked the galley. The clue was plain: {leak['clue']}.",
        f"“I can fetch the mop,” said {helper}. “I’ll keep the route steady,” promised {hero.name}.",
        f"The helper brought the little silver mop, and {hero.name} pointed out each glimmering drop while the crew slowed the ship.",
        f"With careful swishes—SWISH, SWISH!—they could {leak['repair']}.",
        f"The puddle disappeared, the map console stayed clear, and the ship stopped drifting off course.",
        f"“You noticed the clue before the mess reached the controls,” said {helper}. “We made a good team,” {hero.name} replied.",
        f"When {params.ship} reached {params.destination}, the moon-flowers opened like tiny lamps. The clean deck shone beneath {hero.name}'s new wings.",
    ]
    world.mop_ready = True
    world.course_safe = True
    world.danger = 0.0
    world.confidence = 1.0
    world.facts.update({
        "clue": leak["clue"],
        "repair": leak["repair"],
        "ending": f"the moon-flowers opened like tiny lamps at {params.destination}",
        "story": " ".join(lines),
    })

    prompts = [
        f"Tell a gentle space adventure about {hero.name}, born aboard {params.ship}.",
        f"Include the sound effect {leak['sound']} and a problem that needs a mop.",
        f"Show how a clue and teamwork help the crew reach {params.destination}.",
    ]
    story_qa = [
        QAItem(question=f"What happened aboard {params.ship}?", answer=f"A puddle of {leak['name']} spread across the deck, and it threatened the ship's safe route."),
        QAItem(question="What clue helped the crew find the cause?", answer=f"They noticed that {leak['clue']}."),
        QAItem(question="How did the crew solve the problem?", answer=f"They slowed the ship, used the silver mop, and worked together to {leak['repair']}."),
        QAItem(question="What did the crew do while the mess was cleaned?", answer=f"{hero.name} watched the drops and helped keep the route steady while the helper mopped."),
        QAItem(question=f"What happened when they reached {params.destination}?", answer=f"The ship arrived safely, and the moon-flowers opened like tiny lamps."),
    ]
    world_qa = [
        QAItem(question="Why is a spill dangerous on a spaceship?", answer="A spill can make a deck slippery or damage equipment, so the crew should keep clear of it and clean it safely."),
        QAItem(question="What does a mop do?", answer="A mop has an absorbent head on a handle and is used to wipe up liquid from a floor."),
        QAItem(question="What is a moon-moth?", answer="A moon-moth is an imaginary space creature in this story, with tiny wings and a curious nature."),
        QAItem(question="What should a crew do if a spill is near spaceship controls?", answer="The crew should alert one another, protect the controls, and clean the spill carefully before it can cause trouble."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
valid_ship(S) :- ship(S).
valid_destination(D) :- destination(D).
safe_repair :- mop, clue, teamwork.
#show valid_ship/1.
#show valid_destination/1.
#show safe_repair/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("ship", value) for value in SHIPS]
    facts += [asp.fact("destination", value) for value in DESTINATIONS]
    facts += [asp.fact("mop"), asp.fact("clue"), asp.fact("teamwork")]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    py_ships = {(value,) for value in SHIPS}
    py_destinations = {(value,) for value in DESTINATIONS}
    cl_ships = set(asp.atoms(model, "valid_ship"))
    cl_destinations = set(asp.atoms(model, "valid_destination"))
    if py_ships != cl_ships or py_destinations != cl_destinations or not asp.atoms(model, "safe_repair"):
        print("MISMATCH: ASP choices or safe-repair rule differ from the Python world.")
        return 1
    for i in range(12):
        params = StoryParams(NAMES[i % len(NAMES)], SHIPS[i % len(SHIPS)], DESTINATIONS[i % len(DESTINATIONS)], i)
        sample = generate(params)
        required = (params.name, "mop", "SWISH", params.destination)
        if not all(word.lower() in sample.story.lower() for word in required):
            print(f"MISMATCH: generated story {i + 1} is missing a required story element.")
            return 1
    print(f"OK: ASP matches {len(SHIPS)} ships and {len(DESTINATIONS)} destinations; 12 generated stories passed.")
    return 0


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.n < 1 and not args.all:
        raise StoryError("Request at least one story with -n.")
    if args.all:
        return [
            StoryParams(NAMES[i % len(NAMES)], SHIPS[i % len(SHIPS)], DESTINATIONS[i % len(DESTINATIONS)])
            for i in range(max(len(SHIPS), len(DESTINATIONS)))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        w = sample.world
        print("\n--- trace ---")
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"ship={w.ship}, destination={w.destination}, leak={w.leak}, sound={w.sound}")
        print(f"helper={w.helper}, danger={w.danger}, confidence={w.confidence}, mop_ready={w.mop_ready}, course_safe={w.course_safe}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.show_asp:
            print(asp_program("#show valid_ship/1.\n#show valid_destination/1.\n#show safe_repair/0."))
            return
        if args.verify:
            sys.exit(asp_verify())
        if args.asp:
            import asp
            model = asp.one_model(asp_program())
            for atom in sorted(asp.atoms(model, "valid_ship")):
                print(atom[0])
            for atom in sorted(asp.atoms(model, "valid_destination")):
                print(atom[0])
            print("safe_repair" if asp.atoms(model, "safe_repair") else "unsafe_repair")
            return
        params_list = generation_samples(args)
        samples = []
        for i, params in enumerate(params_list):
            params.seed = (args.seed if args.seed is not None else 0) + i
            samples.append(generate(params))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return
        for i, sample in enumerate(samples):
            emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
            if i < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
