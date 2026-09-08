#!/usr/bin/env python3
"""A small rhyming storyworld about an angry feeling, a brave quest, and a surprise."""

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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Setting:
    place: str
    landmark: str
    weather: str


@dataclass(frozen=True)
class Quest:
    id: str
    object_name: str
    obstacle: str
    clue: str
    action: str
    surprise: str
    ending: str


@dataclass
class StoryParams:
    setting: str = "willow_vale"
    quest: str = "moon_key"
    hero_name: str = "Luna"
    friend_name: str = "Pip"
    rhyme: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


SETTINGS = {
    "willow_vale": Setting(
        place="Willow Vale",
        landmark="the crooked willow",
        weather="a silver drizzle",
    ),
    "ember_hill": Setting(
        place="Ember Hill",
        landmark="the old red bell",
        weather="a warm sunset wind",
    ),
    "pebble_marsh": Setting(
        place="Pebble Marsh",
        landmark="the lantern bridge",
        weather="a misty morning",
    ),
}

QUESTS = {
    "moon_key": Quest(
        id="moon_key",
        object_name="the moon-shaped key",
        obstacle="a brook had swollen across the path",
        clue="three blue reeds bent in the same direction",
        action="she used a fallen branch to make a safe little bridge",
        surprise="the key opened a tiny music box hidden beneath the willow's roots",
        ending="soft bells chimed while moonlight silvered every puddle",
    ),
    "red_feather": Quest(
        id="red_feather",
        object_name="the red feather",
        obstacle="a gust had scattered the trail markers",
        clue="one bright berry was scratched beside each true stone",
        action="she followed the berry marks and tied the stones together with grass",
        surprise="the feather belonged to a shy firebird waiting in a nest of moss",
        ending="the firebird rose like a spark and warmed the darkening sky",
    ),
    "singing_pebble": Quest(
        id="singing_pebble",
        object_name="the singing pebble",
        obstacle="the marsh path was covered by ripples and reeds",
        clue="a line of patient frogs blinked beside the safest stepping stones",
        action="she asked the frogs for room and crossed one careful step at a time",
        surprise="the pebble sang only when two friends held it together",
        ending="its tiny tune made the lantern bridge glow gold",
    ),
}

NAMES = ["Luna", "Mira", "Nia", "Tessa", "Pia"]
FRIENDS = ["Pip", "Ravi", "Milo", "Finn", "Theo"]

RHYMES = [
    ("She stamped her feet, then breathed in slow; "
     "bravery is choosing where to go."),
    ("Her anger roared, then lost its sting; "
     "a thoughtful heart can change a thing."),
    ("She felt the heat, but did not flee; "
     "she paused to choose what she could see."),
    ("A wrinkled brow is not the end; "
     "a brave new thought can be a friend."),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a rhyming quest about anger, bravery, and surprise."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
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
    hero = args.hero_name or rng.choice(NAMES)
    choices = [name for name in FRIENDS if name != hero]
    friend = args.friend_name or rng.choice(choices or FRIENDS)
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        quest=args.quest or rng.choice(list(QUESTS)),
        hero_name=hero,
        friend_name=friend,
        rhyme=rng.randrange(len(RHYMES)),
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Hero and friend names must not be empty.")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend need different names.")

    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting)
    hero = world.add(Entity(params.hero_name, "hero", params.hero_name))
    friend = world.add(Entity(params.friend_name, "friend", params.friend_name))
    hero.memes["bravery"] = 0.0
    hero.memes["anger"] = 0.0
    friend.memes["kindness"] = 1.0
    world.facts.update(hero=hero, friend=friend, quest=quest)

    world.say(
        f"In {setting.place}, where {setting.weather} fell, "
        f"{hero.label} stood near {setting.landmark} with a frown and a yell. "
        f"The village bell had lost {quest.object_name}, and the coming night felt dull."
    )
    world.say(
        f"{hero.label} was angry and began to wring her hands. "
        f'"It is not fair!" she cried. "{quest.object_name} should be in our hands!"'
    )
    world.say(
        f'"Anger can speak, but it need not steer," said {friend.label}. '
        f'"Let us seek a clue, then choose with care."'
    )
    world.para()

    hero.memes["anger"] = 1.0
    world.say(f"The Quest began, but {quest.obstacle} blocked the way.")
    world.say(
        f"{hero.label} nearly turned back and nearly gave a furious shout, "
        f"but {friend.label} pointed ahead: {quest.clue}."
    )
    world.say(
        f'"I see it now," said {hero.label}. '
        f'"I can be angry and still be brave."'
    )
    world.say(
        f"Together they {quest.action}. "
        f"The careful choice made the dangerous path safe."
    )
    world.para()

    hero.memes["anger"] = 0.25
    hero.memes["bravery"] = 1.0
    world.fired.add("brave_choice")
    world.say(
        f"At last, {hero.label} found {quest.object_name}. "
        f"But then came a Surprise: {quest.surprise}."
    )
    world.say(
        f"{friend.label} gasped, and {hero.label} laughed. "
        f"{RHYMES[params.rhyme % len(RHYMES)][0]}"
    )
    world.say(
        f"They returned before the stars grew bright. "
        f"The village cheered their brave delight, and {quest.ending}."
    )
    world.facts["resolved"] = True
    world.facts["surprise"] = quest.surprise
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    quest = world.facts["quest"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly rhyming story in which anger is noticed but bravery guides the next choice.",
            f"Tell how {hero.label} and {friend.label} complete a quest for {quest.object_name}.",
            "Include a spoken exchange, a concrete clue, and a gentle surprise ending.",
        ],
        story_qa=[
            QAItem(
                question=f"Why was {hero.label} angry?",
                answer=(
                    f"{hero.label} was angry because the village bell had lost "
                    f"{quest.object_name}, and the missing object threatened the night's celebration."
                ),
            ),
            QAItem(
                question="What clue helped the friends?",
                answer=f"The clue was that {quest.clue}.",
            ),
            QAItem(
                question="How did bravery change the quest?",
                answer=(
                    f"Bravery helped the hero pause instead of letting anger steer, "
                    f"then {quest.action}."
                ),
            ),
            QAItem(
                question="What was the surprise?",
                answer=f"The surprise was that {quest.surprise}.",
            ),
            QAItem(
                question="How did the story end?",
                answer=f"The friends returned safely, and {quest.ending}.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is bravery?",
                answer="Bravery is choosing a careful or kind action even when a difficult feeling or danger is present.",
            ),
            QAItem(
                question="What does it mean to wring your hands?",
                answer="To wring your hands means to twist or squeeze them, often because you are worried, upset, or impatient.",
            ),
            QAItem(
                question="What is a quest?",
                answer="A quest is a purposeful journey taken to find, solve, rescue, or achieve something important.",
            ),
            QAItem(
                question="What is a surprise?",
                answer="A surprise is something unexpected that suddenly changes what someone knows or feels.",
            ),
        ],
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.label}: kind={entity.kind}, memes={memes}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
anger_present(H) :- hero(H), angry(H).
brave_choice(H) :- hero(H), anger_present(H), pauses(H), chooses_care(H).
quest_complete(H) :- brave_choice(H), finds_object(H).
surprise_seen(H) :- quest_complete(H), hidden_gift(H).
#show anger_present/1.
#show brave_choice/1.
#show quest_complete/1.
#show surprise_seen/1.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("hero", "luna"),
        asp.fact("angry", "luna"),
        asp.fact("pauses", "luna"),
        asp.fact("chooses_care", "luna"),
        asp.fact("finds_object", "luna"),
        asp.fact("hidden_gift", "luna"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    expected = {
        ("anger_present", ("luna",)),
        ("brave_choice", ("luna",)),
        ("quest_complete", ("luna",)),
        ("surprise_seen", ("luna",)),
    }
    symbols = asp.one_model(
        asp_program(
            "#show anger_present/1. #show brave_choice/1. "
            "#show quest_complete/1. #show surprise_seen/1."
        )
    )
    actual = {
        (symbol.name, tuple(argument.name for argument in symbol.arguments))
        for symbol in symbols
        if symbol.name in {"anger_present", "brave_choice", "quest_complete", "surprise_seen"}
    }
    if actual != expected:
        print("MISMATCH between ASP and Python.")
        print("  asp:", sorted(actual))
        print("  expected:", sorted(expected))
        return 1

    sample = generate(StoryParams())
    if not sample.story or "surprise" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP twin matches the Python story gate.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(
            asp_program(
                "#show anger_present/1. #show brave_choice/1. "
                "#show quest_complete/1. #show surprise_seen/1."
            )
        )
        return
    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show anger_present/1. #show brave_choice/1. "
                "#show quest_complete/1. #show surprise_seen/1."
            )
        )
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                setting=setting_id,
                quest=quest_id,
                hero_name="Luna",
                friend_name="Pip",
                rhyme=(index % len(RHYMES)),
                seed=base_seed + index,
            )
            for index, (setting_id, quest_id) in enumerate(
                (("willow_vale", "moon_key"), ("ember_hill", "red_feather"), ("pebble_marsh", "singing_pebble"))
            )
        ]
    else:
        params_list = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
