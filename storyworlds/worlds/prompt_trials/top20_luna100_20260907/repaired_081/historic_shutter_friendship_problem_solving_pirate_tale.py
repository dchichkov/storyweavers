#!/usr/bin/env python3
"""
A tiny pirate tale about a historic shutter, friendship, and problem solving.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    ship: str = "The Bright Minnow"
    hero_name: str = "Luna"
    friend_name: str = "Pip"
    treasure: str = "the friendship compass"
    problem: str = "jammed"
    telling_mode: str = "stormy opening"
    seed: Optional[int] = None


@dataclass
class Ship:
    name: str
    deck: str
    harbor: str


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


SHIP_REGISTRY = {
    "The Bright Minnow": Ship("The Bright Minnow", "the salt-sprayed deck", "Pebblehook Harbor"),
    "The Laughing Gull": Ship("The Laughing Gull", "the creaking main deck", "Old Lantern Harbor"),
    "The Moonlit Kettle": Ship("The Moonlit Kettle", "the moon-bright deck", "Coral Key"),
}

HERO_NAMES = ["Luna", "Mara", "Tess", "Nell", "Sable"]
FRIEND_NAMES = ["Pip", "Finn", "Cora", "Bram", "Wren"]

TREASURES = [
    "the friendship compass",
    "the silver harbor bell",
    "the captain's blue map",
    "the pearl of good courage",
]

PROBLEMS = {
    "jammed": {
        "premise": "The historic shutter over the old lookout window was jammed tight with salt and sand.",
        "mistake": "{hero} pulled it harder, and a rusty hinge gave a sharp crack.",
        "clue": "{friend} noticed that the shutter moved a little whenever the tide-water dripped from a nearby rope.",
        "repair": "They brushed away the sand, softened the hinge with lamp oil, and used a spare oar as a gentle lever.",
        "result": "The historic shutter opened without breaking, revealing a faded star carved into the lookout wall.",
        "lesson": "patient friends solve problems better than hurried hands",
        "ending": "Together they watched the sunset through the rescued shutter, while the compass needle pointed toward home.",
    },
    "missing_latch": {
        "premise": "The historic shutter had lost its iron latch, so the sea wind kept banging it against the lookout tower.",
        "mistake": "{hero} tied it shut with a thin ribbon, but the first gust snapped the ribbon in two.",
        "clue": "{friend} found matching holes in the wood where an old brass latch had once rested.",
        "repair": "They shaped a sturdy hook from a spare belt buckle and fastened it through the old holes.",
        "result": "The shutter stayed closed during the gale and opened smoothly when the crew needed the lookout.",
        "lesson": "a good solution begins by studying what is already there",
        "ending": "The repaired shutter clicked softly in the evening breeze as the two friends shared the treasure map.",
    },
    "crooked": {
        "premise": "The historic shutter hung crooked over the lookout window and blocked the crew's view of a reef.",
        "mistake": "{hero} pushed one corner while {friend} pulled the other, making the wood scrape louder.",
        "clue": "A straight line in the old paint showed that the shutter frame, not the wood, had shifted.",
        "repair": "They lifted the frame together, packed a flat piece of driftwood beneath it, and checked the line again.",
        "result": "The shutter sat square, leaving the reef clearly visible from the deck.",
        "lesson": "friends make progress when they share a plan instead of tugging apart",
        "ending": "Luna and her friend sailed safely past the reef beneath the open historic shutter.",
    },
    "painted": {
        "premise": "The historic shutter's faded paint hid the tiny symbols that once guided sailors into the harbor.",
        "mistake": "{hero} scraped at every mark, nearly rubbing away the oldest star.",
        "clue": "{friend} held a lantern at different angles and saw the symbols glow in the side light.",
        "repair": "They cleaned the wood with soft cloths and traced the surviving symbols with harmless chalk.",
        "result": "The old guidance marks became clear without damaging the historic shutter.",
        "lesson": "careful problem solving protects the things we are trying to save",
        "ending": "At dawn, the chalk stars led the ship safely between the harbor rocks.",
    },
}

TELLING_MODES = ["stormy opening", "mystery opening", "dialogue opening", "quiet opening"]

ASP_RULES = r"""
ship(S) :- ship_name(S).
historic_shutter(S) :- shutter_name(S), historic(S).
friendship(H,F) :- hero(H), friend(F), trusts(H,F).
problem_solved(S) :- historic_shutter(S), repaired(S), safe(S).
lesson_learned(H) :- hero(H), learned(H).
safe_harbor(S) :- problem_solved(S), guided(S).
"""


def asp_facts() -> str:
    import asp

    facts = []
    for name in SHIP_REGISTRY:
        facts.append(asp.fact("ship_name", name))
    facts.extend(
        [
            asp.fact("shutter_name", "lookout_shutter"),
            asp.fact("historic", "lookout_shutter"),
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("trusts", "hero", "friend"),
            asp.fact("repaired", "lookout_shutter"),
            asp.fact("safe", "lookout_shutter"),
            asp.fact("learned", "hero"),
            asp.fact("guided", "ship"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show friendship/2.\n"
            "#show problem_solved/1.\n"
            "#show lesson_learned/1.\n"
            "#show safe_harbor/1."
        )
    )
    names = set()
    for symbol in model:
        args = []
        for arg in symbol.arguments:
            if arg.type == arg.type.String:
                args.append(arg.string)
            elif arg.type == arg.type.Number:
                args.append(arg.number)
            else:
                args.append(arg.name)
        names.add((symbol.name, tuple(args)))
    expected = {
        ("friendship", ("hero", "friend")),
        ("problem_solved", ("lookout_shutter",)),
        ("lesson_learned", ("hero",)),
        ("safe_harbor", ("ship",)),
    }
    if names == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--ship", choices=list(SHIP_REGISTRY))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=list(PROBLEMS))
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
    hero = args.name or rng.choice(HERO_NAMES)
    choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if friend == hero:
        raise StoryError("The friend must be a different pirate from the hero.")
    return StoryParams(
        ship=args.ship or rng.choice(list(SHIP_REGISTRY)),
        hero_name=hero,
        friend_name=friend,
        treasure=rng.choice(TREASURES),
        problem=args.problem or rng.choice(list(PROBLEMS)),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIP_REGISTRY:
        raise StoryError(f"Unknown ship: {params.ship}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown shutter problem: {params.problem}")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend must be different characters.")

    ship = SHIP_REGISTRY[params.ship]
    problem = PROBLEMS[params.problem]
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.ship}:{params.hero_name}:{params.friend_name}:{params.problem}"
    )
    world = World(ship)

    hero = world.add(
        Entity(
            "hero",
            params.hero_name,
            "pirate",
            meters={"courage": 1.0, "haste": 0.5},
            memes={"worry": 0.0, "trust": 1.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            params.friend_name,
            "pirate",
            meters={"observation": 1.0, "patience": 1.0},
            memes={"trust": 1.0, "hope": 1.0},
        )
    )
    shutter = world.add(
        Entity(
            "shutter",
            "the historic shutter",
            "historic wooden shutter",
            meters={"damage": 0.5, "safety": 0.0},
            memes={"memory": 1.0, "importance": 1.0},
        )
    )

    openings = {
        "stormy opening": (
            f"Rain slapped {ship.name} as {params.hero_name} and {params.friend_name} hurried "
            f"across {ship.deck} toward the old lookout."
        ),
        "mystery opening": (
            f"Nobody knew why the lookout window on {ship.name} would not open, but "
            f"{params.hero_name} had noticed its historic shutter trembling in the wind."
        ),
        "dialogue opening": (
            f"“The treasure map says the clue is in the lookout,” {params.hero_name} told "
            f"{params.friend_name} aboard {ship.name}."
        ),
        "quiet opening": (
            f"At first light, {params.hero_name} and {params.friend_name} climbed toward the "
            f"lookout on {ship.name}, where a historic shutter watched the harbor."
        ),
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"They were searching for {params.treasure}, a prize said to reward pirates who "
        "worked bravely together."
    )
    world.say(problem["premise"])
    shutter.meters["damage"] += 0.5
    hero.memes["worry"] += 1.0
    world.say(problem["mistake"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(
        f"“Stop, matey,” {params.friend_name} said. “If we hurry, we may damage the very "
        "clue we came to find.”"
    )
    world.say(
        f"“Then help me look instead of pull,” {params.hero_name} replied. "
        "The two pirates lowered their tools and examined the wood."
    )
    world.say(problem["clue"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(
        f"{params.hero_name} listened to {params.friend_name}'s idea, and their plan changed: "
        "they would repair the shutter gently before seeking the treasure."
    )
    world.say(problem["repair"].format(hero=params.hero_name, friend=params.friend_name))
    shutter.meters["damage"] = 0.0
    shutter.meters["safety"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 2.0
    friend.memes["hope"] = 2.0
    world.say(problem["result"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(
        f"Behind the shutter they found a small brass tube. Inside was a map leading to "
        f"{params.treasure}."
    )
    world.say(
        f"“You saw the clue because you were patient,” {params.hero_name} said. "
        f"“And you listened when I spoke,” {params.friend_name} answered. "
        "“That is how we found the way together.”"
    )
    world.say(
        f"{params.hero_name} learned that {problem['lesson']}. "
        f"With {params.friend_name} beside them, the pirates followed the map home."
    )
    world.say(problem["ending"].format(hero=params.hero_name, friend=params.friend_name))

    world.facts.update(
        hero=hero,
        friend=friend,
        shutter=shutter,
        problem=params.problem,
        clue=problem["clue"].format(hero=params.hero_name, friend=params.friend_name),
        repair=problem["repair"].format(hero=params.hero_name, friend=params.friend_name),
        result=problem["result"].format(hero=params.hero_name, friend=params.friend_name),
        lesson=problem["lesson"],
        solved=True,
    )

    prompts = [
        f"Write a pirate tale about {params.hero_name} and {params.friend_name} repairing a historic shutter.",
        f"Show how friendship helps solve this problem: {problem['premise']}",
        f"End with the lesson that {problem['lesson']}.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the pirates discover?",
            answer=problem["premise"],
        ),
        QAItem(
            question=f"What clue did {params.friend_name} notice?",
            answer=problem["clue"].format(hero=params.hero_name, friend=params.friend_name),
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=problem["repair"].format(hero=params.hero_name, friend=params.friend_name),
        ),
        QAItem(
            question="What did the repaired shutter reveal?",
            answer=f"It revealed a map leading to {params.treasure}.",
        ),
        QAItem(
            question=f"What did {params.hero_name} learn?",
            answer=f"{params.hero_name} learned that {problem['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable wooden or metal cover placed over a window.",
        ),
        QAItem(
            question="Why is the shutter historic?",
            answer="It is historic because it is old and carries memories or clues from earlier sailors.",
        ),
        QAItem(
            question="How can friendship help with problem solving?",
            answer="Friends can listen to different ideas, notice different clues, and work together on a safer solution.",
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show friendship/2.\n"
                "#show problem_solved/1.\n"
                "#show lesson_learned/1.\n"
                "#show safe_harbor/1."
            )
        )
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, problem in enumerate(PROBLEMS):
            params = StoryParams(
                ship=list(SHIP_REGISTRY)[index % len(SHIP_REGISTRY)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                treasure=TREASURES[index % len(TREASURES)],
                problem=problem,
                telling_mode=TELLING_MODES[index % len(TELLING_MODES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
