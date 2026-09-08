#!/usr/bin/env python3
"""
A standalone Ghost Story world about a mission, a little moisture, and an
exchange that turns bravery into understanding.

The seed premise:
Luna enters an old bell house to moisten a dry ghost's fading memory. A brave
exchange and a flashback reveal what the ghost has been waiting to say.
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


HERO_NAMES = ["Luna", "Mara", "Nell", "Ivo", "Sora", "Tavi"]
GHOST_NAMES = ["Elias", "Moss", "Ada", "Wren", "Orin"]
PLACES = ["the old bell house", "the moonlit station", "the shuttered museum", "the misty lighthouse"]
WATER_SOURCES = ["a silver flask", "a rain jar", "a blue watering can", "a tiny spring"]
MEMORIES = ["a lost lantern", "a promise to return", "a song for the ferryman", "a blue scarf"]
BRAVERY_WORDS = ["steady", "bold", "patient", "kind", "fearless"]

MISSIONS = {
    "a lost lantern": {
        "dry": "The ghost's memory had become dry and pale, like paper left in the sun.",
        "flashback": "Luna saw a little lantern swinging beside a flooded path while a child waited under a cedar tree.",
        "exchange": "The ghost offered the lantern's warm glow, and Luna offered the name of the waiting child.",
        "resolution": "the ghost remembered that returning the lantern had mattered more than keeping it",
        "ending": "a small golden light shone in the bell-house window",
    },
    "a promise to return": {
        "dry": "The ghost could remember the promise but not the face it had been made to.",
        "flashback": "Luna saw two friends pressing their hands to the same frosted window before dawn.",
        "exchange": "The ghost gave Luna the promise's final words, and Luna gave the ghost permission to finish them.",
        "resolution": "the ghost remembered that it had kept the promise by coming back",
        "ending": "two pale footprints appeared beside Luna's fresh ones",
    },
    "a song for the ferryman": {
        "dry": "The ghost's song had lost its middle, leaving only three cold notes in the air.",
        "flashback": "Luna saw a wooden boat waiting below a bridge while a ferryman hummed into the fog.",
        "exchange": "The ghost hummed the beginning, and Luna bravely hummed the ending she heard in the rain.",
        "resolution": "the ghost remembered that songs could cross water even when voices could not",
        "ending": "the last note drifted across the river and came back warm",
    },
    "a blue scarf": {
        "dry": "The ghost remembered a blue scarf but not why its color made the room feel safe.",
        "flashback": "Luna saw a child tying the scarf around a cold statue before the first snow.",
        "exchange": "The ghost described the scarf's soft edge, and Luna described the kindness of sharing it.",
        "resolution": "the ghost remembered that the scarf had been given away to keep someone else warm",
        "ending": "a blue thread curled around the old doorknob",
    },
}

OPENINGS = [
    "At moonrise, the village windows went dark one by one.",
    "Rain whispered over the roofs when Luna reached the locked gate.",
    "The church bell had stopped, but its silence still filled the valley.",
    "A silver fog rolled down the hill and gathered around the empty house.",
]

GHOST_GREETINGS = [
    '"Do not come closer," whispered the ghost. "My memory is too thin."',
    '"Who walks there?" asked the ghost. "The floor remembers every footstep."',
    '"I have been waiting," said the ghost, though its voice sounded far away.',
]

BRAVERY_LINES = [
    '"I am frightened," Luna said, "but I can still listen."',
    '"Bravery does not mean I cannot shake," Luna said. "It means I will stay kind."',
    '"You may be lonely," Luna said. "I will not let fear make me leave."',
]

@dataclass
class Person:
    name: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Ghost:
    name: str
    memory: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mission:
    place: str
    memory: str
    water: str
    risk: str
    completed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Person
    ghost: Ghost
    mission: Mission
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.facts.setdefault("lines", []).append(text)

    def render(self) -> str:
        return " ".join(self.facts.get("lines", []))


@dataclass
class StoryParams:
    hero: str
    ghost: str
    place: str
    memory: str
    water: str
    bravery: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ghost Story mission world.")
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--ghost", choices=GHOST_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--memory", choices=MEMORIES)
    parser.add_argument("--water", choices=WATER_SOURCES)
    parser.add_argument("--bravery", choices=BRAVERY_WORDS)
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


def valid_combo(params: StoryParams) -> bool:
    return params.memory in MEMORIES and params.water in WATER_SOURCES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        ghost=args.ghost or rng.choice(GHOST_NAMES),
        place=args.place or rng.choice(PLACES),
        memory=args.memory or rng.choice(MEMORIES),
        water=args.water or rng.choice(WATER_SOURCES),
        bravery=args.bravery or rng.choice(BRAVERY_WORDS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The mission needs a known memory and a safe source of water.")
    return params


def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    mission_data = MISSIONS[params.memory]
    hero = Person(
        params.hero,
        params.bravery,
        meters={"courage": 1.0, "distance": 0.0},
        memes={"worry": 0.5, "trust": 0.0},
    )
    ghost = Ghost(
        params.ghost,
        params.memory,
        meters={"fading": 1.0},
        memes={"loneliness": 1.0, "hope": 0.0},
    )
    mission = Mission(
        params.place,
        params.memory,
        params.water,
        "the ghost's memory may vanish if it is handled roughly",
        meters={"water": 0.0},
        memes={"bravery": 0.0},
    )
    return World(
        hero,
        ghost,
        mission,
        facts={
            "opening": rng.choice(OPENINGS),
            "greeting": rng.choice(GHOST_GREETINGS),
            "bravery_line": rng.choice(BRAVERY_LINES),
            "mission_data": mission_data,
        },
    )


def generate_story(world: World) -> None:
    h = world.hero
    g = world.ghost
    m = world.mission
    data = world.facts["mission_data"]

    world.say(f"{world.facts['opening']} {h.name} carried {m.water} toward {m.place}.")
    world.say(
        f"The mission was to moisten {g.name}'s fading memory of {m.memory}. "
        f"{data['dry']} {m.risk.capitalize()}."
    )
    world.say(f"Inside, {g.name} appeared beside a silent bell. {world.facts['greeting']}")
    world.say(
        f"{h.name} held the water close, though the cold made {h.name}'s hands tremble. "
        f"{world.facts['bravery_line']}"
    )
    h.memes["trust"] += 1.0
    m.memes["bravery"] += 1.0

    world.say(
        f"Before pouring, {h.name} asked, \"What should I remember first?\" "
        f"{g.name} answered, \"Remember the feeling, not only the picture.\""
    )
    world.say(
        f"Luna's question opened a flashback: {data['flashback']} "
        "For one breath, the old room smelled of wet leaves and candle smoke."
    )
    h.meters["distance"] += 1.0
    g.meters["fading"] -= 0.4

    world.say(
        f"{h.name} touched one drop of water to the ghost's pale hand. "
        f"The drop did not fall; it spread like a small moon. "
        f"{data['exchange']}"
    )
    m.meters["water"] = 1.0
    g.memes["loneliness"] -= 0.7
    g.memes["hope"] += 1.0

    world.say(
        f"Then {h.name} moistened the memory slowly, one careful drop at a time. "
        f"At last, {g.name} {data['resolution']}."
    )
    m.completed = True
    g.meters["fading"] = 0.0
    h.memes["worry"] = 0.0

    world.say(
        f"The ghost smiled. \"You were brave because you stayed gentle,\" {g.name} said. "
        f"{h.name} replied, \"And you were brave because you told me what was missing.\""
    )
    world.say(f"When Luna left {m.place}, {data['ending']}.")


def story_qa(world: World) -> list[QAItem]:
    h, g, m = world.hero, world.ghost, world.mission
    data = world.facts["mission_data"]
    return [
        QAItem(
            "Who went on the mission?",
            f"{h.name} went on the mission to {m.place}.",
        ),
        QAItem(
            f"What did {h.name} use to moisten the ghost's memory?",
            f"{h.name} used {m.water} and added the water slowly so the fading memory would not be harmed.",
        ),
        QAItem(
            "What happened in the flashback?",
            f"The flashback showed that {data['flashback'].lower()}",
        ),
        QAItem(
            "What did the exchange reveal?",
            f"The exchange helped the ghost remember that {data['resolution']}.",
        ),
        QAItem(
            "Why was Luna brave?",
            f"Luna was brave because Luna felt frightened but stayed gentle, listened, and finished the mission.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mission?", "A mission is an important task someone chooses to complete."),
        QAItem("What does moisten mean?", "To moisten something means to make it a little wet."),
        QAItem("What is an exchange?", "An exchange is when people give or share something with one another."),
        QAItem("What is bravery?", "Bravery means doing what is right even when you feel afraid."),
        QAItem("What is a flashback?", "A flashback is a return to an earlier memory or event."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly ghost story about a brave mission that changes a fading memory.",
        f"Tell how {world.hero.name} uses {world.mission.water} to moisten {world.ghost.name}'s memory.",
        f"Include a flashback and a spoken exchange about {world.mission.memory}.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"hero={world.hero.name} bravery={world.hero.memes.get('trust', 0):.1f} worry={world.hero.memes.get('worry', 0):.1f}",
            f"ghost={world.ghost.name} memory={world.ghost.memory} fading={world.ghost.meters.get('fading', 0):.1f}",
            f"place={world.mission.place} water={world.mission.water} completed={world.mission.completed}",
            f"exchange={world.facts['mission_data']['exchange']}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for memory in MEMORIES:
        lines.append(asp.fact("memory", memory))
    for water in WATER_SOURCES:
        lines.append(asp.fact("water", water))
    for bravery in BRAVERY_WORDS:
        lines.append(asp.fact("bravery", bravery))
    return "\n".join(lines)


ASP_RULES = r"""
mission(M,W,B) :- memory(M), water(W), bravery(B).
valid(M,W,B) :- mission(M,W,B).
#show valid/3.
"""


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python = {(m, w, b) for m in MEMORIES for w in WATER_SOURCES for b in BRAVERY_WORDS}
    try:
        clingo_set = asp_valid()
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    if python != clingo_set:
        print("MISMATCH")
        print("only in Python:", sorted(python - clingo_set))
        print("only in ASP:", sorted(clingo_set - python))
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(python)} combinations).")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Elias", PLACES[0], "a lost lantern", WATER_SOURCES[0], "steady", 101),
        StoryParams("Mara", "Moss", PLACES[2], "a blue scarf", WATER_SOURCES[1], "kind", 202),
        StoryParams("Sora", "Wren", PLACES[3], "a song for the ferryman", WATER_SOURCES[2], "patient", 303),
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
