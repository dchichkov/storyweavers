#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a historic harbor shutter, friendship,
and solving a problem together.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    historic: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    captain: str
    friend: str
    seed: Optional[int] = None
    problem: int = 0
    opening: int = 0
    exchange: int = 0
    ending: int = 0


SETTINGS = {
    "old_harbor": Setting(
        "the old harbor", True, {"historic_shutter", "lantern", "rope"}
    ),
    "fort_cove": Setting(
        "Fort Cove", True, {"historic_shutter", "lantern", "rope"}
    ),
    "bell_island": Setting(
        "Bell Island", True, {"historic_shutter", "lantern", "rope"}
    ),
}

CAPTAIN_NAMES = ["Luna", "Mara", "Tess", "Coral", "Sable", "Pip"]
FRIEND_NAMES = ["Finn", "Jo", "Nico", "Bram", "Wren", "Kit"]

OPENINGS = [
    "At sunrise, Captain {captain} sailed into {place}, where an old watchhouse stood above the waves.",
    "The Sea Wren rocked beside {place} while Captain {captain} and {friend} climbed toward the weathered watchhouse.",
    "A salty wind curled around {place}. Captain {captain} had promised {friend} a look at the historic watchhouse before supper.",
    "Near the edge of {place}, Captain {captain} found {friend} studying a crooked wooden shutter.",
    "The tide was low at {place}, and Captain {captain} brought {friend} ashore to inspect the watchhouse that sailors had used long ago.",
]

PROBLEMS = [
    {
        "sign": "The historic shutter hung crooked, banging whenever the wind blew.",
        "risk": "climb the slippery wall and force it back into place",
        "clue": "one hinge pin was missing, while a coil of spare rope lay beside the door",
        "plan": "They tied a safety line, measured the loose hinge, and searched the shed instead of climbing.",
        "solution": "a spare iron pin had rolled beneath a barrel",
        "repair": "Together they slid the pin through the hinge and tied the shutter open with the rope.",
        "lesson": "a hard problem becomes smaller when friends share clues and make a safe plan",
        "ending": "The historic shutter rested straight, tapping softly in the sea breeze.",
    },
    {
        "sign": "A bright red flag was trapped behind the historic shutter.",
        "risk": "yank the shutter wide before the rising tide reached the rocks",
        "clue": "the flag's rope ran through a cracked pulley above the window",
        "plan": "They kept their feet on the dry stones, followed the rope with their eyes, and fetched a boat hook.",
        "solution": "the pulley had caught on a splinter",
        "repair": "They freed the splinter with the boat hook and lowered the flag gently.",
        "lesson": "careful teamwork can solve a puzzle without turning it into a chase",
        "ending": "The red flag waved proudly above the quiet watchhouse.",
    },
    {
        "sign": "A faint knocking came from behind the historic shutter.",
        "risk": "smash the boards with a heavy oar",
        "clue": "the knocking matched the rhythm of a loose sign swinging outside",
        "plan": "They held the oar still, listened again, and checked every moving part.",
        "solution": "the wind was tapping an old sign against the shutter",
        "repair": "They fastened the sign with a short length of rope and left the old boards unharmed.",
        "lesson": "listening together can reveal an ordinary answer hidden inside a scary sound",
        "ending": "Only gulls called as the historic shutter stood quiet beneath the clouds.",
    },
    {
        "sign": "A map corner poked from under the historic shutter.",
        "risk": "pull it free before another pirate spotted the treasure map",
        "clue": "the visible mark was a drawing of the watchhouse, not a treasure chest",
        "plan": "They held the paper flat, read the old words, and asked the harbor keeper for help.",
        "solution": "the map showed a safe path used by sailors during storms",
        "repair": "They placed the map in a dry case and used its path to guide a lost fishing boat.",
        "lesson": "a friend helps protect important clues instead of snatching them",
        "ending": "The historic shutter guarded the dry map while the fishing boat found its way home.",
    },
]

EXCHANGES = [
    '"We need a plan, not a scramble," said {captain}. "I see the missing piece," replied {friend}. "Then you lead the search, and I will keep us safe," said the captain.',
    '"What do you notice?" asked {captain}. "{clue}," said {friend}. "Good spotting. Let us test that clue together," answered the captain.',
    '"Should we rush?" asked {friend}. "No," said {captain}. "Friends solve more when they listen first."',
    '"I can hold the rope," said {friend}. "And I can check the hinge," replied {captain}. "Two jobs, one safe plan!"',
]

ENDINGS = [
    '"We did not need a treasure chest," said {friend}. "We found a way to help the harbor."',
    '"The best crew shares the work," said {captain}. {friend} smiled as the tide slipped out.',
    "They sailed away with the repaired watchhouse behind them and a new plan for tomorrow.",
    "The two friends marked the solution in the harbor log so the next crew would know what to do.",
]


ASP_RULES = r"""
#show valid/2.
setting(old_harbor). setting(fort_cove). setting(bell_island).
historic(old_harbor). historic(fort_cove). historic(bell_island).
affords(old_harbor,historic_shutter). affords(old_harbor,lantern). affords(old_harbor,rope).
affords(fort_cove,historic_shutter). affords(fort_cove,lantern). affords(fort_cove,rope).
affords(bell_island,historic_shutter). affords(bell_island,lantern). affords(bell_island,rope).
valid(P, O) :- historic(P), affords(P, O).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        if setting.historic:
            lines.append(asp.fact("historic", name))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", name, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted(
        (place, affordance)
        for place, setting in SETTINGS.items()
        if setting.historic
        for affordance in setting.affords
    )


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(python_valid())
    actual = set(asp_valid())
    if expected == actual:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in python:", sorted(expected - actual))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown harbor setting: {params.place}")
    if params.captain == params.friend:
        raise StoryError("The captain and friend must have different names.")

    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem % len(PROBLEMS)]
    world = StoryState(setting)

    captain = world.add(
        Entity(
            params.captain,
            "character",
            "captain",
            traits=["brave", "thoughtful"],
            meters={"balance": 1.0},
            memes={"friendship": 1.0, "confidence": 0.5},
        )
    )
    friend = world.add(
        Entity(
            params.friend,
            "character",
            "friend",
            traits=["curious", "observant"],
            meters={"balance": 1.0},
            memes={"friendship": 1.0, "confidence": 0.5},
        )
    )
    shutter = world.add(
        Entity(
            "historic_shutter",
            "thing",
            "shutter",
            label="the historic shutter",
            owner="harbor",
            meters={"stability": 0.3},
            memes={"memory": 1.0},
        )
    )
    harbor = world.add(
        Entity(
            "harbor",
            "place",
            "harbor",
            label=setting.place,
            traits=["old", "important"],
            meters={"safety": 0.7},
            memes={"history": 1.0},
        )
    )

    world.say(
        OPENINGS[params.opening % len(OPENINGS)].format(
            place=setting.place, captain=captain.id, friend=friend.id
        )
    )
    world.say(problem["sign"])
    world.say(
        f'"Maybe it hides a pirate secret," said {friend.id}. '
        f'"Maybe," replied {captain.id}, "but first we must keep everyone safe."'
    )

    world.para()
    world.say(
        f"{friend.id} wanted to {problem['risk']}. "
        f"{captain.id} raised a hand and pointed to the danger near the water."
    )
    world.say(
        EXCHANGES[params.exchange % len(EXCHANGES)].format(
            captain=captain.id, friend=friend.id, clue=problem["clue"]
        )
    )
    world.say(f"From the ground, they noticed that {problem['clue']}.")
    world.say(problem["plan"])
    world.facts["tension"] = problem["risk"]
    world.facts["clue"] = problem["clue"]
    world.facts["friendship"] = True

    world.para()
    world.say(
        f"Working side by side, {captain.id} and {friend.id} discovered that "
        f"{problem['solution']}."
    )
    world.say(problem["repair"])
    shutter.meters["stability"] = 1.0
    harbor.meters["safety"] = 1.0
    captain.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    world.say(
        f'"I learned that {problem["lesson"]}," {friend.id} told {captain.id}. '
        f"{captain.id} nodded as the old harbor seemed to breathe more easily."
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(
        captain=captain.id, friend=friend.id
    ))
    world.say(problem["ending"])

    world.facts.update(
        captain=captain,
        friend=friend,
        shutter=shutter,
        harbor=harbor,
        problem=problem,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    problem = world.facts["problem"]
    return [
        f"Write a pirate tale about {world.setting.place} and a historic shutter.",
        f"Tell a friendship story in which {world.facts['captain'].id} and {world.facts['friend'].id} solve a harbor problem together.",
        f"Write a child-friendly pirate adventure featuring this clue: {problem['clue']}.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    problem = facts["problem"]
    captain = facts["captain"].id
    friend = facts["friend"].id
    return [
        QAItem(
            "Who worked together to help the harbor?",
            f"{captain} and {friend} worked together. Their friendship helped them share observations and make a safe plan.",
        ),
        QAItem(
            f"What problem did {captain} and {friend} find?",
            f"They found that {problem['sign'].lower()}",
        ),
        QAItem(
            "What clue helped them solve the problem?",
            f"They noticed that {problem['clue']}. That clue showed them where to investigate.",
        ),
        QAItem(
            "How did the friends solve the problem?",
            problem["repair"],
        ),
        QAItem(
            "What did the friends learn?",
            f"They learned that {problem['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a wooden or metal cover that can close over a window.",
        ),
        QAItem(
            "Why might a historic building need careful repairs?",
            "A historic building needs careful repairs so its old materials and important memories are protected.",
        ),
        QAItem(
            "What makes a good pirate crew?",
            "A good pirate crew listens, shares work, and solves problems without putting people in unnecessary danger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:18} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if captain == friend:
        choices = [name for name in FRIEND_NAMES if name != captain]
        if not choices:
            raise StoryError("No distinct friend name is available.")
        friend = rng.choice(choices)
    return StoryParams(
        place=place,
        captain=captain,
        friend=friend,
        problem=rng.randrange(len(PROBLEMS)),
        opening=rng.randrange(len(OPENINGS)),
        exchange=rng.randrange(len(EXCHANGES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale world about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--captain")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combinations = asp_valid()
        print(f"{len(combinations)} valid combinations:\n")
        for place, affordance in combinations:
            print(f"  {place:12} {affordance}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                captain=f"{place.title()}Captain",
                friend=f"{place.title()}Friend",
                problem=index % len(PROBLEMS),
                opening=index % len(OPENINGS),
                exchange=index % len(EXCHANGES),
                ending=index % len(ENDINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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
