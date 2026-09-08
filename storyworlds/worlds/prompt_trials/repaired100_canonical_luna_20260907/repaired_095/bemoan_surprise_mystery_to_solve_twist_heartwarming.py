#!/usr/bin/env python3
"""A heartwarming storyworld about a bemoaned surprise, a solvable mystery, and a kind twist."""

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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("hope", "worry", "joy", "kindness", "curiosity"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    id: str
    label: str
    detail: str


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    first_guess: str
    true_reason: str
    search: str
    discovery: str
    twist: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


SETTINGS = {
    "lantern_square": Setting(
        "lantern_square",
        "the Lantern Square",
        "where paper lanterns glowed above a little fountain",
    ),
    "willow_garden": Setting(
        "willow_garden",
        "the Willow Garden",
        "where silver leaves whispered over a wooden bench",
    ),
}

MYSTERIES = {
    "missing_blue_ribbon": Mystery(
        "missing_blue_ribbon",
        "a blue ribbon meant for the town's kindness wreath",
        "a tiny trail of blue threads beside the fountain",
        "the wind had carried the ribbon away",
        "someone had borrowed it to mend a comfort blanket for a lonely neighbor",
        "followed the threads past the flower stall and listened for the soft snip of scissors",
        "found the ribbon stitched into a warm blanket in the tailor's window",
        "the ribbon had not been lost at all; it had become part of a gift for the person who needed kindness most",
        "the ribbon was returned to the wreath only after the new blanket was admired and its recipient was welcomed",
    ),
    "unopened_song_box": Mystery(
        "unopened_song_box",
        "the small music box planned for the evening celebration",
        "one silver music note lay beneath the baker's cart",
        "someone had forgotten to bring the music box",
        "the music box had been opened so its tune could be copied onto a card for a child who could not attend",
        "searched along the cobbles, asking each shopkeeper what they had heard that morning",
        "found the music box beside a stack of hand-drawn song cards",
        "the missing music was being shared with someone far away before the celebration began",
        "the box played while the child received the song card, and the square sang together",
    ),
    "vanished_honey_cakes": Mystery(
        "vanished_honey_cakes",
        "a basket of honey cakes prepared for the tired lantern keepers",
        "a smear of honey on the handle of the empty basket",
        "the cakes had been taken by hungry squirrels",
        "the baker had sent them early to the night-watch children after hearing they had skipped supper",
        "checked the warm bakery ovens and followed the honey scent toward the watch hut",
        "found the children sharing the cakes beneath a wool blanket",
        "the surprise was not theft but a quiet act of care that nobody had announced",
        "the lantern keepers saved the last cake for the baker and hung a golden lantern in thanks",
    ),
}

NAMES = ["Luna", "Mira", "Nia", "Tessa", "Pip", "Owen"]
FRIENDS = ["Ari", "Bea", "Noah", "Sami", "Ivy", "Theo"]

OPENINGS = [
    "Luna had planned every part of the little celebration.",
    "The square was ready for a gentle evening of sharing.",
    "A warm surprise was supposed to begin at sunset.",
    "Luna arrived early, carrying a basket and a hopeful smile.",
]

REFLECTIONS = [
    "Sometimes a mystery feels frightening only because its kindness is still hidden.",
    "A bemoaned mistake can become a doorway to understanding when friends look closely.",
    "The sweetest surprises are often made from quiet care.",
    "Luna learned that an empty place does not always mean something has gone wrong.",
]


@dataclass
class StoryParams:
    place: str = "lantern_square"
    mystery: str = "missing_blue_ribbon"
    name: str = "Luna"
    friend_name: str = "Ari"
    opening: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming mystery about a bemoaned surprise."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
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
    name = args.name or rng.choice(NAMES)
    choices = [person for person in FRIENDS if person != name]
    friend_name = args.friend_name or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        name=name,
        friend_name=friend_name,
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def validate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if not params.name.strip() or not params.friend_name.strip():
        raise StoryError("Both children need names.")
    if params.name == params.friend_name:
        raise StoryError("The child and friend must have different names.")


def tell(params: StoryParams) -> World:
    validate(params)
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(params.name, "child", params.name))
    friend = world.add(Entity(params.friend_name, "friend", params.friend_name))
    world.facts.update(hero=hero, friend=friend, mystery=mystery)

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]} "
        f"It was the evening of the kindness celebration in {setting.label}, "
        f"{setting.detail}."
    )
    world.say(
        f"She had brought a place for {mystery.missing}, but when she opened her basket, "
        f"the important surprise was gone."
    )
    hero.memes["worry"] += 1
    hero.meters["worry"] += 1
    world.para()

    world.say(
        f'"Oh dear," said {hero.label}. "I must bemoan this whole evening. '
        f'How can I welcome everyone when the best part has disappeared?"'
    )
    world.say(
        f'"Let us not decide the ending yet," {friend.label} replied. '
        f'"A mystery is a question waiting for careful eyes."'
    )
    friend.memes["kindness"] += 1
    friend.meters["kindness"] += 1
    hero.memes["curiosity"] += 1
    hero.meters["curiosity"] += 1
    world.para()

    world.say(
        f"They found {mystery.clue}. {hero.label} first thought that {mystery.first_guess}, "
        f"but {friend.label} shook their head gently."
    )
    world.say(
        f'"The clue tells us where to look, not whom to blame," said {friend.label}. '
        f'"Will you search with me?"'
    )
    world.say(
        f'"Yes," said {hero.label}. "I can be disappointed and still be curious."'
    )
    world.para()

    world.say(f"{mystery.search.capitalize()}.")
    world.say(
        f"At last, they {mystery.discovery}. {mystery.true_reason.capitalize()}."
    )
    hero.memes["worry"] = 0
    hero.meters["worry"] = 0
    hero.memes["hope"] += 1
    hero.meters["hope"] += 1
    world.para()

    world.say(
        f"Then came the twist: {mystery.twist.capitalize()}. "
        f"{hero.label} looked at the empty place in the celebration and understood that "
        f"the missing thing had already made the world kinder."
    )
    world.say(
        f"They finished the plan together. {mystery.ending.capitalize()} "
        f"{REFLECTIONS[params.reflection % len(REFLECTIONS)]}"
    )
    hero.memes["joy"] += 1
    hero.meters["joy"] += 1
    friend.memes["joy"] += 1
    friend.meters["joy"] += 1
    world.fired.update({"mystery_solved", "twist_revealed", "heartwarming_ending"})
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        "Write a heartwarming child-friendly story in which a character may bemoan a problem without giving up.",
        f"Give {hero.label} and {friend.label} a mystery to solve involving {mystery.missing}.",
        f"Reveal a gentle twist based on this clue: {mystery.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery = world.facts["mystery"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            f"Why did {hero.label} bemoan the missing surprise?",
            f"{hero.label} bemoaned it because {mystery.missing} was gone and the child feared the celebration would fail.",
        ),
        QAItem(
            "What clue began the mystery?",
            f"The clue was {mystery.clue}.",
        ),
        QAItem(
            f"How did {hero.label} and {friend.label} solve the mystery?",
            mystery.search.capitalize() + ". " + mystery.discovery.capitalize() + ".",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {mystery.twist}.",
        ),
        QAItem(
            "How did the story end?",
            mystery.ending.capitalize(),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does bemoan mean?",
            "To bemoan something means to complain sadly about it or express sorrow that it happened.",
        ),
        QAItem(
            "What is a mystery to solve?",
            "It is a question or puzzling event that can be understood by noticing clues and testing careful ideas.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is an unexpected change in what the reader thinks is happening, often revealed by a new fact.",
        ),
        QAItem(
            "What makes an ending heartwarming?",
            "A heartwarming ending shows care, connection, or hope bringing comfort to the characters.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"  setting: {world.setting.label}"]
    for entity in world.entities.values():
        active = {
            key: value
            for key, value in entity.meters.items()
            if value
        }
        lines.append(f"  {entity.label}: {active or {'steady': 1}}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_present.
kind_friend.
careful_search.
mystery_solved :- mystery_present, kind_friend, careful_search.
twist_revealed :- mystery_solved.
heartwarming_ending :- twist_revealed.
#show mystery_solved/0.
#show twist_revealed/0.
#show heartwarming_ending/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("mystery_present"),
            asp.fact("kind_friend"),
            asp.fact("careful_search"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program(
            "#show mystery_solved/0. "
            "#show twist_revealed/0. "
            "#show heartwarming_ending/0."
        )
    )
    actual = {str(symbol) for symbol in symbols}
    expected = {"mystery_solved", "twist_revealed", "heartwarming_ending"}
    if actual == expected:
        sample = generate(StoryParams())
        if not sample.story or "bemoan" not in sample.story:
            print("Generated story exercise failed.")
            return 1
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(actual))
    print("  expected:", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(
            asp_program(
                "#show mystery_solved/0. "
                "#show twist_revealed/0. "
                "#show heartwarming_ending/0."
            )
        )
        return
    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show mystery_solved/0. "
                "#show twist_revealed/0. "
                "#show heartwarming_ending/0."
            )
        )
        print("\n".join(sorted(str(symbol) for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for mystery in MYSTERIES:
                samples.append(
                    generate(
                        StoryParams(
                            place=place,
                            mystery=mystery,
                            name="Luna",
                            friend_name="Ari",
                        )
                    )
                )
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

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
