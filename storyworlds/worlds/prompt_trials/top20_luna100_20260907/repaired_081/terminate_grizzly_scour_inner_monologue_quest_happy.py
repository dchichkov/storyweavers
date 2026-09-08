#!/usr/bin/env python3
"""
Story world: a tiny superhero quest about Grizzly, a dangerous scour, and the
choice to terminate a spreading mess without harming anyone.
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
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    district: str = "Moonbeam Market"
    threat: str = "grizzly"
    mission: str = "terminate the silver scour"
    telling_mode: str = "inner monologue"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


DISTRICTS = [
    "Moonbeam Market",
    "Sunrise Square",
    "Cloudberry Park",
    "Lantern Lane",
]

HERO_NAMES = ["Luna", "Nova", "Mira", "Sol", "Comet"]
HELPER_NAMES = ["Pip", "Bram", "Zee", "Tavi", "Moss"]

TELLING_MODES = [
    "inner monologue",
    "quest",
    "happy ending",
    "heroic opening",
]

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
threat(T) :- threat_name(T).
scour_active(S) :- scour_state(S, spreading).
scour_stopped(S) :- scour_state(S, terminated).
safe(S) :- scour_stopped(S), shielded(S).
happy_ending :- safe(silver_scour), helped(hero, town).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "hero"),
            asp.fact("helper_name", "helper"),
            asp.fact("threat_name", "grizzly"),
            asp.fact("scour_state", "silver_scour", "spreading"),
            asp.fact("scour_state", "silver_scour", "terminated"),
            asp.fact("shielded", "silver_scour"),
            asp.fact("helped", "hero", "town"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show scour_stopped/1.\n#show safe/1.\n#show happy_ending/0."
    )
    model = asp.one_model(program)
    found = {
        (sym.name, tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in sym.arguments
        ))
        for sym in model
    }
    wanted = {
        ("scour_stopped", ("silver_scour",)),
        ("safe", ("silver_scour",)),
        ("happy_ending", ()),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero quest about Luna, Grizzly, and a silver scour."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--district", choices=DISTRICTS)
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
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        district=args.district or rng.choice(DISTRICTS),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.threat != "grizzly":
        raise StoryError("This quest only supports the grizzly threat.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.district}"
    )
    world = World()

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            meters={"courage": 1.0, "energy": 1.0},
            memes={"worry": 0.0, "hope": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            meters={"courage": 1.0},
            memes={"trust": 1.0},
        )
    )
    grizzly = world.add(
        Entity(
            id="grizzly",
            kind="creature",
            label="the grizzly",
            meters={"strength": 3.0, "danger": 1.0},
            memes={"confusion": 1.0},
        )
    )
    scour = world.add(
        Entity(
            id="silver_scour",
            kind="threat",
            label="the silver scour",
            meters={"spread": 3.0, "shine": 1.0},
            memes={"alarm": 1.0},
        )
    )

    if params.telling_mode == "inner monologue":
        world.say(
            f"{params.hero_name} stood above {params.district} in a blue cape and thought, "
            f"“A true hero does not rush toward danger just because it looks frightening.”"
        )
    elif params.telling_mode == "quest":
        world.say(
            f"At dawn, {params.hero_name} received a quest: protect {params.district} "
            "before the silver scour reached the town fountain."
        )
    elif params.telling_mode == "happy ending":
        world.say(
            f"That evening, {params.district} prepared a glowing celebration for "
            f"{params.hero_name}, though the hardest part of the quest had come first."
        )
    else:
        world.say(
            f"When the warning bell rang over {params.district}, {params.hero_name} "
            "pulled on a bright cape and flew toward trouble."
        )

    world.say(
        "A silver scour was sliding across the cobbles, coating signs, benches, and flower pots "
        "with a slippery glitter."
    )
    world.say(
        f"Behind the fountain, a confused grizzly pawed at the shining trail and growled."
    )
    world.say(
        f"“Please do not frighten it,” {params.helper_name} called. "
        f"“The grizzly may be trapped by the scour.”"
    )
    world.say(
        f"“Then I will help both the town and the grizzly,” {params.hero_name} replied."
    )

    hero.memes["worry"] = 1.0
    scour.meters["spread"] += 1.0
    grizzly.memes["confusion"] += 1.0
    world.say(
        f"{params.hero_name} felt a hot spark of fear. “I could blast the whole mess away,” "
        "the hero thought, “but that might hurt the creature or scatter the scour farther.”"
    )
    world.say(
        f"{params.helper_name} pointed to a drain covered by a bronze grate. "
        f"“The wind is pushing the scour there. We can guide it into the old collection tank.”"
    )
    world.say(
        f"{params.hero_name} studied the trail, then chose patience over a powerful punch. "
        f"Together, the heroes rolled out shield cloth and made a safe path around the grizzly."
    )

    world.say(
        f"The grizzly followed the scent of apples from {params.helper_name}'s satchel "
        "and stepped away from the shining spill."
    )
    grizzly.memes["confusion"] = 0.0
    grizzly.meters["danger"] = 0.0
    world.say(
        f"{params.hero_name} lowered a moon-shaped shield over the drain and used a gentle wind "
        "to scour the silver scour into the tank."
    )
    scour.meters["spread"] = 0.0
    scour.memes["alarm"] = 0.0
    world.say(
        f"“The danger is contained,” {params.hero_name} said. "
        f"“Now I can terminate the scour without hurting anyone.”"
    )
    world.say(
        f"{params.helper_name} turned the tank's blue handle. The silver bubbles quieted, "
        "and the last shining ribbon folded safely inside."
    )
    world.say(
        f"The quest ended when {params.hero_name} sealed the tank, washed the street, "
        "and opened a gate so the grizzly could return to the forest."
    )

    hero.meters["energy"] = 0.5
    hero.memes["hope"] = 2.0
    scour.meters["spread"] = 0.0
    scour.meters["contained"] = 1.0
    scour.memes["finished"] = 1.0
    world.facts.update(
        hero=hero,
        helper=helper,
        grizzly=grizzly,
        scour=scour,
        scour_terminated=True,
        grizzly_safe=True,
        happy_ending=True,
        clue="The wind was pushing the silver scour toward the bronze drain.",
        method="The heroes used shield cloth, a moon-shaped shield, and a collection tank.",
        lesson="A superhero uses courage with care and protects frightened creatures as well as people.",
    )

    world.say(
        f"By sunset, every shop window in {params.district} gleamed again. "
        f"The grizzly gave {params.hero_name} one last curious look before padding home, "
        "and the town cheered for a hero whose strongest power was careful kindness."
    )

    prompts = [
        f"Write a superhero story about {params.hero_name} protecting {params.district} from a silver scour.",
        f"Tell how the hero handles a grizzly without hurting it and learns to terminate the spreading danger safely.",
        "Use inner monologue, a clear quest, and a happy ending in a child-facing superhero adventure.",
    ]
    story_qa = [
        QAItem(
            question="What danger threatened the town?",
            answer="A silver scour was spreading across the streets and heading toward a drain.",
        ),
        QAItem(
            question="Why was the grizzly in danger?",
            answer="The confused grizzly was pawing at the slippery silver scour and could have been hurt or trapped by it.",
        ),
        QAItem(
            question="How did the heroes stop the scour?",
            answer="They guided it with shield cloth and a gentle wind into a collection tank, then sealed the tank safely.",
        ),
        QAItem(
            question="What did the hero learn?",
            answer="The hero learned that courage works best with careful kindness, especially when frightened creatures need protection.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"The scour was terminated, {params.district} was clean again, and the grizzly returned safely to the forest.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities, good judgment, and kindness to help others.",
        ),
        QAItem(
            question="Why should a dangerous spill be contained?",
            answer="Containing a dangerous spill keeps it from spreading and gives people and animals a safer place to deal with it.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it completely.",
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
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
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
        print(asp_program("#show scour_stopped/1.\n#show safe/1.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show scour_stopped/1.\n#show safe/1.\n#show happy_ending/0.")
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, district in enumerate(DISTRICTS):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                district=district,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
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
