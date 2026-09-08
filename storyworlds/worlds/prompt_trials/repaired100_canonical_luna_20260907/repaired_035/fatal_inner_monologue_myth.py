#!/usr/bin/env python3
"""
A tiny mythic world about a fatal shadow, a moon child, and the courage to speak.
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


@dataclass(frozen=True)
class Setting:
    key: str
    place: str
    omen: str
    blessing: str


@dataclass(frozen=True)
class Quest:
    key: str
    relic: str
    danger: str
    truth: str
    deed: str
    ending: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, text: str) -> None:
        self.trace.append(text)


SETTINGS = {
    "moon_valley": Setting(
        "moon_valley",
        "the valley beneath the moon",
        "a black star fell without making a sound",
        "silver grass bent toward every honest voice",
    ),
    "ash_mountain": Setting(
        "ash_mountain",
        "the slope of Ash Mountain",
        "the mountain breathed one cold breath",
        "a red flower opened in the gray stone",
    ),
    "whispering_forest": Setting(
        "whispering_forest",
        "the Whispering Forest",
        "the oldest trees whispered a child's name",
        "the roots made a path beneath the leaves",
    ),
}

QUESTS = {
    "black_star": Quest(
        "black_star",
        "the fallen black star",
        "a fatal shadow that could turn a living heart to stone",
        "the shadow grew strong only when fear was hidden",
        "name the fear aloud and place the star in the river",
        "the black star became a quiet lamp for travelers",
    ),
    "sleeping_flame": Quest(
        "sleeping_flame",
        "the sleeping flame",
        "a fatal frost that could stop every fire in the world",
        "the flame needed a true memory, not dry wood",
        "remember the first warm hand and breathe that memory into the ember",
        "the flame rose like a golden bird over the mountain",
    ),
    "root_crown": Quest(
        "root_crown",
        "the crown of roots",
        "a fatal silence that could make every creature forget its name",
        "names survive when they are spoken together",
        "ask the forest creatures to call one another home",
        "the forest remembered itself in a thousand bright voices",
    ),
}

NAMES = ["Luna", "Mira", "Tavi", "Neri", "Orin", "Sela"]
HELPERS = ["the Moon Owl", "the River Giant", "the Old Fox", "the Star Shepherd"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, quest) for setting in SETTINGS for quest in QUESTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None)
    quest = getattr(args, "quest", None)
    if setting is not None and setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if quest is not None and quest not in QUESTS:
        raise StoryError(f"Unknown quest: {quest}")
    choices = [
        pair for pair in valid_combos()
        if (setting is None or pair[0] == setting)
        and (quest is None or pair[1] == quest)
    ]
    if not choices:
        raise StoryError("No compatible mythic setting and quest were found.")
    chosen_setting, chosen_quest = rng.choice(choices)
    return StoryParams(
        setting=chosen_setting,
        quest=chosen_quest,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        seed=getattr(args, "seed", None),
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting)
    hero = world.add(Entity("hero", "mortal", params.name))
    helper = world.add(Entity("helper", "guide", params.helper))
    relic = world.add(Entity("relic", "relic", quest.relic))
    shadow = world.add(Entity("shadow", "danger", quest.danger))
    hero.memes["fear"] = 1.0
    relic.meters["cold"] = 1.0
    shadow.meters["fatal"] = 1.0
    world.facts.update({"hero": hero, "helper": helper, "relic": relic, "shadow": shadow, "quest": quest})
    return world


def _story_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA71C)
    text = "|".join((params.setting, params.quest, params.name, params.helper))
    return random.Random(sum((i + 1) * ord(char) for i, char in enumerate(text)))


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")

    rng = _story_rng(params)
    world = build_world(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    relic = world.entities["relic"]
    shadow = world.entities["shadow"]
    quest: Quest = world.facts["quest"]  # type: ignore[assignment]
    place = world.setting.place

    opening_choices = [
        f"In the first age, {params.name} walked through {place}, where {world.setting.omen}.",
        f"Long ago, when the moon still listened to mortals, {params.name} entered {place}. There, {world.setting.omen}.",
        f"At the edge of the old world, {params.name} found {place} waiting under a dark sky. Then {world.setting.omen}.",
    ]
    opening = rng.choice(opening_choices)

    inner_choices = [
        f"Inside {params.name}'s heart, a small voice whispered, “If I fail, the danger will be fatal.”",
        f"{params.name} thought, “I must not let anyone see my fear, or this fatal danger will win.”",
        f"The inner voice of {params.name} said, “Run from the shadow.” A quieter voice answered, “But who will guard the world?”",
    ]
    inner = rng.choice(inner_choices)

    world.record("The hero sees the fatal danger.")
    discovery = (
        f"At the center of the place lay {quest.relic}, and around it curled {quest.danger}. "
        f"It had already dimmed the stones beneath it."
    )

    dialogue = (
        f"{helper.label} stepped from the dark and said, “Do not hide your fear. Tell me what you know.” "
        f"{params.name} answered, “The danger is fatal, and I do not know how to defeat it.” "
        f"{helper.label} replied, “Then your truth is the first light.”"
    )

    world.record("The guide asks the hero to speak the hidden fear.")
    explanation = (
        f"{helper.label} revealed the ancient truth: {quest.truth}. "
        f"The fatal shadow fed on silence, but it could not swallow a fear that had been named."
    )

    inner_turn = rng.choice([
        f"Inside, {params.name} thought, “I wanted to be fearless. Now I understand that courage can carry fear in the open.”",
        f"{params.name}'s inner voice changed: “I am afraid, but fear is not my master.”",
        f"The thought in {params.name}'s heart became clear: “A hidden fear grows teeth. A spoken fear can become a road.”",
    ])

    world.record("The hero changes from hiding fear to naming it.")
    deed = (
        f"{params.name} lifted {quest.relic}, spoke the fear aloud, and {quest.deed}. "
        f"The fatal shadow cracked like thin ice."
    )
    world.record("The hero performs the truthful deed.")
    resolution = (
        f"The shadow vanished, and {quest.ending}. "
        f"Across the land, {world.setting.blessing}."
    )
    world.record("The fatal danger is transformed into a blessing.")
    ending = (
        f"{params.name} did not become a person without fear. "
        f"{params.name} became a person who could face fear and still choose the light."
    )

    story = "\n\n".join([
        opening,
        inner,
        discovery,
        dialogue,
        explanation,
        inner_turn,
        deed,
        resolution,
        ending,
    ])

    prompts = [
        "Write a short myth about a fatal danger that is changed by courage.",
        f"Tell a mythic story in which {params.name} speaks an inner fear and saves the world.",
        f"Write a child-facing myth set in {place}, with a guide, a relic, and a hopeful ending.",
    ]
    story_qa = [
        QAItem(
            question="Who faced the fatal danger?",
            answer=f"{params.name} faced the fatal danger in {place}.",
        ),
        QAItem(
            question="What made the danger powerful?",
            answer="The danger became powerful when fear was hidden and left unspoken.",
        ),
        QAItem(
            question="What did the guide tell the hero?",
            answer=f"{helper.label} told {params.name} to speak the hidden fear because truth could become the first light.",
        ),
        QAItem(
            question="What did the hero do to save the world?",
            answer=f"{params.name} named the fear aloud and {quest.deed}.",
        ),
        QAItem(
            question="How did the ending prove that the world changed?",
            answer=f"{quest.ending.capitalize()}, and {world.setting.blessing}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story that uses wondrous events to explain a truth about people or the world.",
        ),
        QAItem(
            question="What does fatal mean?",
            answer="Fatal means deadly or able to cause death, so a fatal danger is one that must be treated with great care.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="What lesson does this myth teach?",
            answer="It teaches that speaking an honest fear can turn it into courage and make help possible.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append("events:")
    lines.extend(f"- {event}" for event in world.trace)
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_quest(Q) :- quest(Q).
valid(S,Q) :- setting(S), quest(Q).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for quest in QUESTS:
        lines.append(asp.fact("quest", quest))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values != asp_values:
        print("Mismatch between Python and ASP compatibility.")
        print("Only in Python:", sorted(python_values - asp_values))
        print("Only in ASP:", sorted(asp_values - python_values))
        return 1
    for index, (setting, quest) in enumerate(sorted(python_values)):
        sample = generate(
            StoryParams(
                setting=setting,
                quest=quest,
                name=NAMES[index % len(NAMES)],
                helper=HELPERS[index % len(HELPERS)],
                seed=index,
            )
        )
        if "fatal" not in sample.story.lower():
            print("Generated story did not contain the required word: fatal")
            return 1
        if not sample.story_qa:
            print("Generated story had no story QA.")
            return 1
    print(f"OK: ASP/Python parity and {len(python_values)} generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a small myth about a fatal shadow and inner courage.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (setting, quest) in enumerate(valid_combos()):
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        quest=quest,
                        name=NAMES[index % len(NAMES)],
                        helper=HELPERS[index % len(HELPERS)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
