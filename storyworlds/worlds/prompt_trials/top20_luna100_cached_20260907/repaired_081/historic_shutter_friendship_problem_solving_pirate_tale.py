#!/usr/bin/env python3
"""
A tiny pirate tale about a historic shutter, friendship, and solving a problem.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    island: str = "Cannon Cove"
    hero_name: str = "Luna"
    friend_name: str = "Pip"
    treasure: str = "the brass star map"
    problem: str = "storm"
    telling_mode: str = "moonlit opening"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ISLANDS = {
    "Cannon Cove": "a cove where old cannon towers guarded the harbor",
    "Whispering Key": "a green island wrapped in whispering palms",
    "Lantern Reef": "a reef lit by floating blue lanterns",
}

HERO_NAMES = ["Luna", "Mara", "Nell", "Tessa", "Jo"]
FRIEND_NAMES = ["Pip", "Finn", "Cora", "Bram", "Sailor Sam"]

TREASURES = [
    "the brass star map",
    "the captain's silver compass",
    "a chest of cinnamon coins",
    "the bell from the first harbor ship",
]

PROBLEMS = {
    "storm": {
        "premise": "A sudden storm slammed the old watchtower, and its historic wooden shutter jammed halfway open.",
        "mistake": "{hero} tugged the shutter with all her strength, but the swollen wood only groaned louder.",
        "clue": "{friend} noticed a thin line of dry salt around one hinge and found a rope wedged behind the frame.",
        "fix": "They loosened the rope, placed a smooth oar beneath the lower edge, and pushed together when the waves pulled back.",
        "result": "The shutter closed safely before the rain could soak the treasure room.",
        "lesson": "a strong friend listens for clues before pulling harder",
        "ending": "When the storm passed, moonlight slipped through the repaired shutter in a bright silver stripe.",
    },
    "hinge": {
        "premise": "The historic shutter's iron hinge had cracked just as the crew prepared to hide {treasure}.",
        "mistake": "{hero} tried to swing the heavy panel alone, and the loose hinge dropped a shower of rusty flakes.",
        "clue": "{friend} found an old repair mark shaped like a star beside a spare pin in the carpenter's chest.",
        "fix": "They supported the shutter with a barrel, fitted the spare pin, and tied a rope brace across the frame.",
        "result": "The repaired shutter held firm while the treasure rested safely inside.",
        "lesson": "asking a friend for help can reveal tools you missed",
        "ending": "The star-shaped repair mark gleamed beside the shutter as the friends shared a warm mug of cocoa.",
    },
    "map": {
        "premise": "The historic shutter hid a painted clue, but its boards would not open far enough for the crew to read it.",
        "mistake": "{hero} scraped at the boards with a dagger and nearly cut the painted sea serpent.",
        "clue": "{friend} saw tiny shell marks leading from the shutter to a loose stone beneath the sill.",
        "fix": "They lifted the stone, found the missing latch key, and opened the shutter without harming the painting.",
        "result": "The clue showed a safe path around the reef to {treasure}.",
        "lesson": "careful looking is better than a hurried guess",
        "ending": "The friends followed the painted stars while the historic shutter watched over the quiet cove.",
    },
    "parrot": {
        "premise": "A cheeky parrot had wedged a bright bead inside the historic shutter, keeping it from closing.",
        "mistake": "{hero} chased the parrot around the tower, which made it flap deeper into the rafters.",
        "clue": "{friend} copied the bird's whistle and noticed that it always returned when the bead jingled.",
        "fix": "They placed a cup of berries beside the sill, lured the parrot out, and rolled the bead free with a spoon.",
        "result": "The shutter closed, and the parrot received a safe toy bead instead.",
        "lesson": "gentle plans can solve problems that chasing makes worse",
        "ending": "The parrot perched above the shutter and whistled the friends' victory song.",
    },
}

TELLING_MODES = [
    "moonlit opening",
    "dialogue opening",
    "mystery opening",
    "storm opening",
    "friend viewpoint",
]

ASP_RULES = r"""
historic_shutter(S) :- shutter(S), age(S, historic).
ready(S) :- historic_shutter(S), repaired(S), closed(S).
friendship(A,B) :- friend(A,B), helped(A,B).
problem_solved(P) :- problem(P), clue_found(P), repair_done(P).
safe_treasure(T) :- ready(shutter), protected(T).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("shutter", "old_shutter"),
        asp.fact("age", "old_shutter", "historic"),
        asp.fact("repaired", "old_shutter"),
        asp.fact("closed", "old_shutter"),
        asp.fact("friend", "luna", "pip"),
        asp.fact("helped", "luna", "pip"),
        asp.fact("problem", "storm_problem"),
        asp.fact("clue_found", "storm_problem"),
        asp.fact("repair_done", "storm_problem"),
        asp.fact("protected", "brass_star_map"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = """
#show ready/1.
#show friendship/2.
#show problem_solved/1.
#show safe_treasure/1.
"""
    model = asp.one_model(asp_program(show))
    actual = set()
    for symbol in model:
        args = []
        for arg in symbol.arguments:
            if arg.type == arg.type.String:
                args.append(arg.string)
            elif arg.type == arg.type.Number:
                args.append(arg.number)
            else:
                args.append(arg.name)
        actual.add((symbol.name, tuple(args)))
    expected = {
        ("ready", ("old_shutter",)),
        ("friendship", ("luna", "pip")),
        ("problem_solved", ("storm_problem",)),
        ("safe_treasure", ("brass_star_map",)),
    }
    if actual == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--island", choices=list(ISLANDS))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--treasure", choices=TREASURES)
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
    friends = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friends)
    if hero == friend:
        raise StoryError("The pirate hero and friend must be different characters.")
    return StoryParams(
        island=args.island or rng.choice(list(ISLANDS)),
        hero_name=hero,
        friend_name=friend,
        treasure=args.treasure or rng.choice(TREASURES),
        problem=args.problem or rng.choice(list(PROBLEMS)),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.island not in ISLANDS:
        raise StoryError(f"Unknown island: {params.island}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.hero_name == params.friend_name:
        raise StoryError("Friendship needs two different characters.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.island}:{params.hero_name}:{params.friend_name}:{params.problem}"
    )
    problem = PROBLEMS[params.problem]
    world = World()

    hero = world.add(
        Entity(
            "hero",
            "pirate",
            params.hero_name,
            meters={"courage": 1.0, "worry": 0.0},
            memes={"friendship": 0.5, "curiosity": 0.7},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "pirate_friend",
            params.friend_name,
            meters={"helpfulness": 1.0},
            memes={"friendship": 0.8, "patience": 0.8},
        )
    )
    shutter = world.add(
        Entity(
            "shutter",
            "historic shutter",
            "historic shutter",
            meters={"openness": 0.4, "damage": 0.6},
            memes={"memory": 1.0, "danger": 0.5},
        )
    )
    treasure = world.add(
        Entity(
            "treasure",
            "treasure",
            params.treasure,
            meters={"safety": 0.4},
            memes={"hope": 1.0},
        )
    )

    setting = ISLANDS[params.island]
    openings = {
        "moonlit opening": f"Moonlight washed {setting} when {params.hero_name} climbed the old watchtower.",
        "dialogue opening": f"“The treasure must be safe before dawn,” {params.hero_name} said as {params.friend_name} joined her in the watchtower.",
        "mystery opening": f"Something strange had happened in the watchtower on {setting}, and {params.hero_name} could not explain the crooked historic shutter.",
        "storm opening": f"Rain lashed {setting}, and {params.hero_name} raced toward the watchtower with {params.friend_name} close behind.",
        "friend viewpoint": f"{params.friend_name} knew {params.hero_name} loved old pirate things, so he followed her up the watchtower on {setting}.",
    }
    world.say(openings[params.telling_mode])
    world.say(
        rng.choice(
            [
                "The tower smelled of salt, rope, and stories left behind by sailors long ago.",
                "Every board creaked like it remembered a different pirate voyage.",
                "The old tower was small, but it held a history bigger than the whole harbor.",
            ]
        )
    )
    world.say(
        f"They had come to protect {params.treasure}, which rested in a wooden chest beside the historic shutter."
    )
    world.say(problem["premise"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure))
    shutter.meters["damage"] = 1.0
    hero.memes["worry"] = 1.0
    treasure.meters["safety"] = 0.2
    world.say(problem["mistake"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure))
    world.say(
        f'“Wait, matey,” {params.friend_name} said. “The shutter is telling us where the trouble begins.”'
    )
    world.say(
        f'“Then let us listen together,” {params.hero_name} replied. She lowered her hands and looked closely.'
    )
    world.say(
        rng.choice(
            [
                f"{params.friend_name} held the lantern steady while {params.hero_name} traced the frame without touching the weak boards.",
                f"They checked the hinges, the sill, and the floor, changing only one thing at a time.",
                f"The two friends compared the old marks with the tools in their small repair chest.",
            ]
        )
    )
    clue = problem["clue"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure)
    world.say(clue)
    world.say(
        f"Now the pirates understood that the problem was not a battle of strength; it was a puzzle that needed teamwork."
    )
    world.say(
        f'“You saw the clue,” {params.hero_name} said. “And you helped me notice it.”'
    )
    world.say(
        f'“That is what shipmates do,” {params.friend_name} answered. “We solve the hard parts together.”'
    )

    shutter.meters["damage"] = 0.0
    shutter.meters["openness"] = 0.0
    shutter.memes["danger"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["confidence"] = 1.0
    friend.memes["friendship"] = 1.0
    treasure.meters["safety"] = 1.0
    world.say(problem["fix"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure))
    world.say(
        f"The historic shutter became steady again, and the chest holding {params.treasure} was safe behind it."
    )
    world.say(problem["result"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure))
    world.say(
        f"{params.hero_name} learned that {problem['lesson']}. She thanked {params.friend_name} with a proud pirate salute."
    )
    world.say(problem["ending"].format(hero=params.hero_name, friend=params.friend_name, treasure=params.treasure))

    world.facts.update(
        hero=hero,
        friend=friend,
        shutter=shutter,
        treasure=treasure,
        island=params.island,
        problem=params.problem,
        clue=clue,
        repaired=True,
        closed=True,
        friendship=True,
        solved=True,
    )

    prompts = [
        f"Write a child-friendly pirate tale about {params.hero_name} and {params.friend_name} protecting {params.treasure} on {params.island}.",
        f"Show how a historic shutter creates a problem and how friendship helps solve it using this clue: {clue}",
        f"Tell a pirate adventure with a clear problem, a careful solution, spoken dialogue, and the lesson that {problem['lesson']}.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the pirates face?",
            answer=problem["premise"].format(
                hero=params.hero_name, friend=params.friend_name, treasure=params.treasure
            ),
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=clue,
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"{params.hero_name} and {params.friend_name} worked together, listened to the clue, and repaired the historic shutter carefully.",
        ),
        QAItem(
            question="What happened to the treasure?",
            answer=f"The historic shutter closed safely, protecting {params.treasure} inside the watchtower.",
        ),
        QAItem(
            question="What lesson did the pirates learn?",
            answer=f"They learned that {problem['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that covers a window or opening and can be opened or closed.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or connected to the past and the stories of people who lived before us.",
        ),
        QAItem(
            question="Why is friendship useful when solving a problem?",
            answer="A friend can notice clues, offer help, and make a difficult problem easier to solve together.",
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
                "#show ready/1.\n#show friendship/2.\n#show problem_solved/1.\n#show safe_treasure/1."
            )
        )
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, problem_name in enumerate(PROBLEMS):
            params = StoryParams(
                island=list(ISLANDS)[index % len(ISLANDS)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                treasure=TREASURES[index % len(TREASURES)],
                problem=problem_name,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show ready/1.\n#show friendship/2.\n#show problem_solved/1.\n#show safe_treasure/1."
            )
        )
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

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
