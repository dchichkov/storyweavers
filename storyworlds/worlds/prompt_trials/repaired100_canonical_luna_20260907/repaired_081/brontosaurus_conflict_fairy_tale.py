#!/usr/bin/env python3
"""
Story world: a small fairy tale about a brontosaurus, a conflict, and a bridge
built by listening.
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
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    kingdom: str = "Mossbell Vale"
    conflict: str = "bridge"
    style: str = "fairy tale"
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


HERO_NAMES = ["Luna", "Mira", "Tessa", "Nell", "Ivy"]
HELPER_NAMES = ["Pip", "Oren", "Fia", "Bram", "Clover"]
KINGDOMS = ["Mossbell Vale", "Thimblewood", "Mooncake Meadow", "Roseglass Glen"]
CONFLICTS = ["bridge", "orchard", "bell", "garden"]

CONFLICTS_DATA = {
    "bridge": {
        "premise": "A deep silver stream had split the valley, and the villagers argued about who should cross the old bridge first.",
        "mistake": "Luna tried to settle the quarrel by asking the tallest voice to decide, but the brontosaurus lowered its long neck sadly and stepped away.",
        "clue": "Pip noticed that the bridge sagged whenever everyone crowded onto one side, while it held steady when the weight was shared.",
        "change": "Luna invited each side to speak, then they placed light stepping stones in two paths so travelers could cross in turns.",
        "result": "The bridge stopped groaning, and the villagers discovered that taking turns made room for every traveler, including the brontosaurus.",
        "lesson": "a conflict grows smaller when people listen for a fair way to share",
        "ending": "That evening, the brontosaurus carried lanterns over the calm bridge, and both sides of the valley sang together.",
    },
    "orchard": {
        "premise": "The royal orchard had one golden pear left, and two families quarreled over who deserved it.",
        "mistake": "Luna gave the pear to the loudest family, but the brontosaurus gently nudged it away because the choice had not been fair.",
        "clue": "Pip saw that the pear had enough seeds for a whole new tree.",
        "change": "They cut the pear into a shared feast and planted its seeds in a common garden.",
        "result": "Both families tasted the fruit and gained a promise of many future pears.",
        "lesson": "sharing the future can be kinder than fighting over one prize",
        "ending": "Years later, golden pears hung over the garden gate, where everyone could pick one.",
    },
    "bell": {
        "premise": "The kingdom's moon bell rang at the wrong hour, and sleepy villagers blamed one another for the trouble.",
        "mistake": "Luna accused the smallest bell keeper, but the brontosaurus shook its head and pointed toward the windy hill.",
        "clue": "Pip found a loose silver ribbon caught in the bell rope, pulling it whenever the wind blew.",
        "change": "They removed the ribbon, repaired the rope, and made a quiet listening circle before choosing anyone to blame.",
        "result": "The bell rang only at moonrise, and the frightened bell keeper was welcomed back.",
        "lesson": "look for a cause before placing blame",
        "ending": "At moonrise, the bell chimed clearly while the brontosaurus smiled beneath the stars.",
    },
    "garden": {
        "premise": "Two groups of fairies fought over a garden path, because each wanted its flowers to grow in the sunniest place.",
        "mistake": "Luna tried to move every flower herself, but the brontosaurus brushed the seedlings with its tail.",
        "clue": "Pip noticed that morning sun reached one side while afternoon sun reached the other.",
        "change": "They drew a winding path and planted sun-loving flowers on one side and shade-loving flowers on the other.",
        "result": "The garden became brighter, and both groups had a special place to tend.",
        "lesson": "different needs can fit together when everyone studies the whole problem",
        "ending": "The brontosaurus watered the winding garden while fairies danced between two kinds of blossoms.",
    },
}

ASP_RULES = r"""
brontosaurus(B) :- creature(B), species(B, brontosaurus).
listened(H) :- hero(H), heard_both_sides(H).
shared_solution(C) :- conflict(C), solution(C, shared).
resolved(C) :- shared_solution(C), no_blame(C).
happy_ending(C) :- resolved(C), celebration(C).
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("creature", "brontosaurus"),
        asp.fact("species", "brontosaurus", "brontosaurus"),
        asp.fact("hero", "luna"),
        asp.fact("heard_both_sides", "luna"),
        asp.fact("conflict", "valley_conflict"),
        asp.fact("solution", "valley_conflict", "shared"),
        asp.fact("no_blame", "valley_conflict"),
        asp.fact("celebration", "valley_conflict"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program(
        "#show brontosaurus/1.\n#show listened/1.\n#show happy_ending/1."
    ))
    actual = {
        (sym.name, tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in sym.arguments
        ))
        for sym in model
        if sym.name in {"brontosaurus", "listened", "happy_ending"}
    }
    expected = {
        ("brontosaurus", ("brontosaurus",)),
        ("listened", ("luna",)),
        ("happy_ending", ("valley_conflict",)),
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
        description="A fairy tale about a brontosaurus and a conflict solved by listening."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--kingdom", choices=KINGDOMS)
    parser.add_argument("--conflict", choices=list(CONFLICTS_DATA))
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
    choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(choices)
    if helper == hero:
        raise StoryError("The helper must be different from the hero.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        kingdom=args.kingdom or rng.choice(KINGDOMS),
        conflict=args.conflict or rng.choice(list(CONFLICTS_DATA)),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.conflict not in CONFLICTS_DATA:
        raise StoryError(f"Unknown conflict: {params.conflict}.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")

    rng = random.Random(
        params.seed if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.kingdom}:{params.conflict}"
    )
    data = CONFLICTS_DATA[params.conflict]
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        phrase=f"the young storyteller {params.hero_name}",
        meters={"courage": 1.0, "listening": 0.0},
        memes={"worry": 0.0, "kindness": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper_name,
        phrase=f"the bright-eyed helper {params.helper_name}",
        meters={"attention": 1.0},
        memes={"curiosity": 1.0},
    ))
    dinosaur = world.add(Entity(
        id="brontosaurus",
        kind="creature",
        label="brontosaurus",
        phrase=rng.choice([
            "a gentle brontosaurus with a neck like a castle tower",
            "a kindly brontosaurus whose footsteps sounded like soft drums",
            "a shy brontosaurus with leaves tucked behind one ear",
        ]),
        meters={"strength": 4.0, "reach": 5.0, "sadness": 0.0},
        memes={"patience": 1.0, "hope": 1.0},
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        brontosaurus=dinosaur,
        conflict=params.conflict,
        resolved=False,
    )

    openings = [
        f"Once, in {params.kingdom}, {params.hero_name} lived beneath a roof painted with stars.",
        f"In the old days, when wishes still fluttered like moths, {params.hero_name} came to {params.kingdom}.",
        f"Beyond seven hills stood {params.kingdom}, where {params.hero_name} was learning how to solve quarrels kindly.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"One morning, {params.hero_name} met {dinosaur.phrase} beside the kingdom's silver stream."
    )
    world.say(data["premise"])
    world.say(
        f"“We cannot let this quarrel grow teeth,” {params.hero_name} said. "
        f"“Can you help me understand it?”"
    )
    world.say(
        f"“I can listen,” {params.helper_name} replied, “but we must hear every side.”"
    )
    world.say(data["mistake"].format(
        hero=params.hero_name, helper=params.helper_name
    ))
    dinosaur.meters["sadness"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"{params.helper_name} placed a hand on {params.hero_name}'s sleeve. "
        f"“A loud answer is not always a wise answer.”"
    )
    world.say(data["clue"].format(
        hero=params.hero_name, helper=params.helper_name
    ))
    hero.meters["listening"] = 2.0
    helper.meters["attention"] = 2.0
    world.say(
        f"So {params.hero_name} listened first to one side, then to the other, "
        f"while {params.helper_name} drew the clues in the dust."
    )
    world.say(
        f"The brontosaurus watched quietly, its long shadow reaching across both groups."
    )
    world.say(
        f"“What would let everyone belong?” {params.hero_name} asked."
    )
    world.say(
        f"“A shared plan,” said {params.helper_name}. “Not a victory for only one side.”"
    )
    world.say(data["change"].format(
        hero=params.hero_name, helper=params.helper_name
    ))
    dinosaur.meters["sadness"] = 0.0
    dinosaur.memes["joy"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["wisdom"] = 1.0
    world.facts["resolved"] = True
    world.say(data["result"].format(
        hero=params.hero_name, helper=params.helper_name
    ))
    world.say(
        f"{params.hero_name} understood the lesson: {data['lesson']}."
    )
    world.say(data["ending"].format(
        hero=params.hero_name, helper=params.helper_name
    ))

    prompts = [
        f"Write a fairy tale about {params.hero_name}, a brontosaurus, and a conflict in {params.kingdom}.",
        f"Show how {params.hero_name} and {params.helper_name} solve the {params.conflict} conflict by listening.",
        f"End with a concrete image proving that the conflict was resolved fairly.",
    ]
    story_qa = [
        QAItem(
            question="What conflict troubled the kingdom?",
            answer=data["premise"],
        ),
        QAItem(
            question="What clue helped the characters understand the conflict?",
            answer=data["clue"],
        ),
        QAItem(
            question="How was the conflict resolved?",
            answer=data["change"],
        ),
        QAItem(
            question=f"What did {params.hero_name} learn?",
            answer=f"{params.hero_name} learned that {data['lesson']}.",
        ),
        QAItem(
            question="What showed that peace had returned?",
            answer=data["ending"],
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a brontosaurus?",
            answer="A brontosaurus was a very large plant-eating dinosaur with a long neck and a long tail.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement or struggle between people who want different things.",
        ),
        QAItem(
            question="Why can listening help during a conflict?",
            answer="Listening helps people understand each other's needs and discover a fair solution.",
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}"
            )
        print(f"facts: {sample.world.facts}")
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
        print(asp_program(
            "#show brontosaurus/1.\n#show listened/1.\n#show happy_ending/1."
        ))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, conflict in enumerate(CONFLICTS_DATA):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                kingdom=KINGDOMS[index % len(KINGDOMS)],
                conflict=conflict,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
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
