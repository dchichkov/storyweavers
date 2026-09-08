#!/usr/bin/env python3
"""
A pirate tale about a historic shutter, friendship, and problem solving.

Captain Luna must open a historic harbor shutter before a storm arrives.
When the old mechanism jams, she learns that a clever solution depends on
listening to friends, sharing tools, and solving the problem together.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "Moonwake Harbor"
    affords: set[str] = field(
        default_factory=lambda: {"shelter", "tide", "teamwork", "repair"}
    )


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    obstacle: str
    mistake: str
    clue: str
    shared_tool: str
    helper: str
    careful_action: str
    result: str
    harbor_change: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def propagate(world: World) -> None:
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    shutter = world.facts["shutter"]

    if meter(captain, "listening") >= 1 and meme(captain, "worry") >= 1:
        sig = ("trust", captain.id)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(captain, "trust")
            add_meme(friend, "trust")
            world.say(
                f"Because {captain.id} listened, {friend.id} trusted the plan enough to share the missing detail."
            )

    if meter(captain, "teamwork") >= 1 and meter(friend, "teamwork") >= 1:
        sig = ("repair", shutter.id)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meter(shutter, "working")
            add_meme(captain, "pride")
            world.say(
                f"Together, they gave the old shutter a careful turn, and its hinges began to move."
            )


SETTING = Setting()

SCENARIOS = [
    Scenario(
        "salt_hinge",
        "At dawn, Captain Luna sailed toward Moonwake Harbor with a chest of bright shells.",
        "The historic harbor shutter guarded the safest inner dock, but salt had crusted around its lower hinge.",
        "Luna nearly ordered everyone to pull the shutter with one thick rope.",
        "A pale line on the stone showed that the shutter had once been lifted from the opposite side.",
        "a rope, a small brush, and a tin of warm oil",
        "her old friend Pip, the ship's mapmaker",
        "brushed the salt away while Pip passed the rope through the older lifting ring",
        "the shutter rose smoothly before the storm tide reached the dock",
        "a second lifting ring and a shared repair box were added to the harbor wall",
        "a friend may remember the clue that haste overlooks",
        "When the storm came, Luna and Pip watched safe boats slip beneath the historic shutter.",
    ),
    Scenario(
        "hidden_latch",
        "A dark cloud rolled over the harbor while the crew prepared to shelter the fishing boats.",
        "The historic shutter would not close because its inner latch had slipped behind a stack of old crates.",
        "Luna wanted to smash the crates apart and finish before the rain.",
        "Pip heard a tiny rattle whenever the tide pulled the shutter backward.",
        "a lantern, a boat hook, and three wooden wedges",
        "Pip, her patient first mate",
        "held the lantern low while Pip listened, then wedged the shutter open just enough to reach the hidden latch",
        "the latch clicked into place and the boats rested safely behind the wall",
        "the harbor stored a labeled lantern beside every old latch",
        "careful listening can solve a problem without breaking what protects everyone",
        "Rain drummed on the roof as the crew shared cocoa behind the strong historic shutter.",
    ),
    Scenario(
        "moonbeam_gap",
        "Moonlight shone through a narrow gap in the harbor's historic shutter.",
        "The gap made the sailors think the shutter was broken, though the tide was rising fast.",
        "Luna planned to cover the opening with a sail and ignore the old wood.",
        "The moonbeam touched a faded star carved beside the shutter's real locking pin.",
        "a sailcloth, chalk, and a brass key",
        "Mara, Luna's childhood friend and cabin painter",
        "marked the star, folded the sailcloth aside, and fitted the brass key into the carved pin",
        "the shutter locked firmly and the sail remained ready for the next voyage",
        "the carved star was painted bright so every sailor could find the lock",
        "friends can turn a confusing sign into a useful guide",
        "By midnight, the painted star gleamed beside the closed shutter like a little moon.",
    ),
    Scenario(
        "broken_wheel",
        "The harbor bell rang for shelter as a squall raced toward the boats.",
        "The wheel that moved the historic shutter spun freely without lifting it.",
        "Luna first blamed the newest deckhand for pulling the wheel wrongly.",
        "A worn tooth on the wheel matched a spare tooth in the ship's old compass box.",
        "a compass box, a file, and a shared mallet",
        "Jory, the deckhand Luna had blamed",
        "apologized, invited Jory to hold the wheel, and filed the spare tooth until it matched",
        "the wheel caught again and the shutter swung safely across the harbor mouth",
        "repair duties were written down so every sailor could learn them",
        "friendship grows when a captain corrects a mistake instead of hiding it",
        "Jory grinned at the turning wheel, and Luna gave him the first watch by the shutter.",
    ),
    Scenario(
        "tide_mark",
        "The sea climbed the harbor steps while Luna's crew hurried to protect a row of tiny boats.",
        "The historic shutter had two possible positions, and nobody knew which one would block the highest waves.",
        "Luna almost chose the nearest mark because it was quicker to reach.",
        "Pip found a faded tide mark above the lower stone and remembered last winter's flood.",
        "a measuring cord, chalk, and a blue flag",
        "Pip, her tide-reading friend",
        "measured from the old mark, chalked the safer position, and tied the blue flag where all could see",
        "the shutter stopped the waves without trapping the boats inside",
        "the harbor kept a shared tide chart beside the shutter",
        "problem solving means using old knowledge when the present feels rushed",
        "The blue flag fluttered above calm water while the historic shutter held firm.",
    ),
]

NAMES = {
    "girl": ["Luna", "Mara", "Nessa", "Tala"],
    "boy": ["Pip", "Jory", "Tavi", "Rook"],
}

DIALOGUES = [
    "Wait, what does the old wood remember?",
    "Could we listen before we pull?",
    "Which mark tells us what the tide did last time?",
    "What can we try without breaking the harbor wall?",
    "Will you hold this while I check the other side?",
]

LESSONS = [
    "Luna learned that friendship makes clever hands even wiser.",
    "The crew learned that a good captain asks for help before choosing a plan.",
    "They discovered that problem solving works best when every careful observation is welcome.",
    "Luna saw that trust can open a stubborn path more gently than force.",
]


@dataclass
class StoryParams:
    place: str
    object: str
    feature: str
    name: str
    gender: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--place", choices=["harbor"])
    parser.add_argument("--object", choices=["shutter"])
    parser.add_argument(
        "--feature",
        choices=["friendship", "problem_solving"],
    )
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=["brave", "curious", "patient", "clever"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "harbor"
    obj = args.object or "shutter"
    feature = args.feature or "friendship"
    if place != "harbor":
        raise StoryError("This pirate tale takes place in Moonwake Harbor.")
    if obj != "shutter":
        raise StoryError("This tale centers on a historic shutter.")
    if feature not in {"friendship", "problem_solving"}:
        raise StoryError("Choose friendship or problem solving as the story feature.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    friend_choices = ["Pip", "Mara", "Jory", "Nessa"]
    friend_name = args.friend_name or rng.choice(
        [n for n in friend_choices if n != name] or ["Pip"]
    )
    trait = args.trait or rng.choice(["brave", "curious", "patient", "clever"])
    return StoryParams(place, obj, feature, name, gender, friend_name, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "harbor":
        raise StoryError("The shutter needs a harbor setting.")
    if params.object != "shutter":
        raise StoryError("The requested object must be a shutter.")
    if params.feature not in {"friendship", "problem_solving"}:
        raise StoryError("The story needs friendship or problem solving.")


def tell(world: World, params: StoryParams) -> World:
    value = params.seed
    if value is None:
        value = sum((i + 1) * ord(c) for i, c in enumerate(params.name + params.friend_name))
    scenario = SCENARIOS[value % len(SCENARIOS)]
    dialogue = DIALOGUES[(value // len(SCENARIOS)) % len(DIALOGUES)]
    lesson = LESSONS[(value // (len(SCENARIOS) * len(DIALOGUES))) % len(LESSONS)]

    captain = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            memes={"courage": 1.0, "worry": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="friend",
            label=params.friend_name,
        )
    )
    shutter = world.add(
        Entity(
            id="HistoricShutter",
            kind="object",
            type="historic_shutter",
            label="historic shutter",
            owner="Moonwake Harbor",
            meters={"age": 1.0},
        )
    )
    harbor = world.add(
        Entity(
            id="MoonwakeHarbor",
            kind="place",
            type="harbor",
            label="Moonwake Harbor",
        )
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        shutter=shutter,
        harbor=harbor,
        scenario=scenario,
        dialogue=dialogue,
        lesson=lesson,
    )

    world.say(
        f"Captain {captain.id}, a {params.trait} pirate, sailed into Moonwake Harbor before the storm bells rang."
    )
    world.say(
        f"At the harbor mouth stood a historic shutter, built by sailors long ago to protect every boat from wild tides."
    )
    world.say(
        f"Captain {captain.id} trusted {friend.id}, a friend who knew the harbor's old marks and quiet corners."
    )
    world.para()

    world.say(scenario.opening)
    world.say(scenario.obstacle)
    world.say(scenario.mistake)
    world.say(f'"{dialogue}" Captain {captain.id} asked {friend.id}.')
    world.say(
        f'"The old harbor may have left us a clue," {friend.id} replied. "Let us look together."'
    )
    add_meter(captain, "listening")
    add_meme(friend, "confidence")
    propagate(world)

    world.para()
    world.say(f"They discovered that {scenario.clue}")
    world.say(
        f"Instead of keeping the work aboard the captain's ship, they shared {scenario.shared_tool}."
    )
    world.say(f"Captain {captain.id} {scenario.careful_action}.")
    add_meter(captain, "teamwork")
    add_meter(friend, "teamwork")
    propagate(world)

    world.say(f"The plan worked: {scenario.result}.")
    add_meter(shutter, "safe", 1.0)
    world.para()

    world.say(
        f"Captain {captain.id} thanked {friend.id}, and the two friends recorded what they had learned."
    )
    world.say(f"From then on, {scenario.harbor_change}.")
    world.say(f"{lesson} {scenario.lesson}")
    world.say(scenario.ending)
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(World(SETTING), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    captain = world.facts["captain"]
    return [
        f"Write a pirate tale about {captain.id}, a historic shutter, friendship, and problem solving.",
        f"Tell a child-friendly harbor adventure in which {captain.id} solves this problem: {scenario.obstacle}",
        "Write a story where two pirate friends use an old clue instead of force to protect a harbor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    scenario = f["scenario"]
    return [
        QAItem(
            question="Who was the pirate captain in the story?",
            answer=f"Captain {captain.id} was the pirate who led the harbor rescue.",
        ),
        QAItem(
            question="What was historic about the harbor?",
            answer="A historic shutter stood at the harbor mouth, and it had protected boats from dangerous tides for many years.",
        ),
        QAItem(
            question="What problem did the friends face?",
            answer=f"They had to solve this problem: {scenario.obstacle}",
        ),
        QAItem(
            question=f"How did {friend.id} help?",
            answer=f"{friend.id} noticed that {scenario.clue} This gave the friends a useful direction.",
        ),
        QAItem(
            question="What did the friends share?",
            answer=f"They shared {scenario.shared_tool}, so both friends could take part in the repair.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"The captain listened to the friend, and together they {scenario.careful_action}. As a result, {scenario.result}.",
        ),
        QAItem(
            question="What changed in the harbor afterward?",
            answer=f"Afterward, {scenario.harbor_change}. The shared rule helped the harbor stay safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover that can close an opening and protect what is behind it.",
        ),
        QAItem(
            question="Why can historic objects be useful?",
            answer="Historic objects can preserve old knowledge about how people solved problems in the past.",
        ),
        QAItem(
            question="Why is friendship helpful during a hard task?",
            answer="Friendship is helpful because friends listen, share effort, and encourage one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, finding useful clues, and trying a careful plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {prompt}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(
            f"{entity.id}: {entity.type} {' '.join(details) if details else 'unchanged'}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor, shutter, friendship).
valid(harbor, shutter, problem_solving).
safe(harbor) :- valid(harbor, shutter, friendship).
safe(harbor) :- valid(harbor, shutter, problem_solving).
"""


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("harbor", "shutter", "friendship"),
        ("harbor", "shutter", "problem_solving"),
    ]


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "harbor"),
            asp.fact("object", "shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_values = set(valid_combos())
        asp_values = set(asp_valid_combos())
    except ImportError as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if python_values != asp_values:
        print("MISMATCH")
        print(f"Python: {sorted(python_values)}")
        print(f"ASP: {sorted(asp_values)}")
        return 1

    for seed in range(5):
        params = StoryParams(
            "harbor",
            "shutter",
            "friendship",
            "Luna",
            "girl",
            "Pip",
            "brave",
            seed,
        )
        sample = generate(params)
        if "historic shutter" not in sample.story or "friend" not in sample.story:
            print("MISMATCH: generated story failed content check")
            return 1

    print(f"OK: ASP matches Python ({len(python_values)} combos); stories passed.")
    return 0


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


CURATED = [
    StoryParams(
        "harbor",
        "shutter",
        "friendship",
        "Luna",
        "girl",
        "Pip",
        "brave",
        0,
    ),
    StoryParams(
        "harbor",
        "shutter",
        "problem_solving",
        "Jory",
        "boy",
        "Mara",
        "curious",
        1,
    ),
    StoryParams(
        "harbor",
        "shutter",
        "friendship",
        "Nessa",
        "girl",
        "patient",
        "Tavi",
        2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(20, args.n * 20):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.name}: {params.object} / {params.feature}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
