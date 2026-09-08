#!/usr/bin/env python3
"""
A gentle slice-of-life storyworld about an engineer, a curious appendage,
a small mystery, and the kindness that helps solve it.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


OPENERS = [
    "On an ordinary morning in a town of small workshops,",
    "Near the community repair room,",
    "On a bright weekday beside the bus stop,",
    "In a quiet neighborhood where people fixed things together,",
]

SCENES = [
    "The repair room smelled of warm wood, soap, and the lemon tea that someone had left by the window.",
    "Bicycles clicked past the open door while a sparrow hopped along the sill.",
    "A delivery cart rattled outside, and the workbench shone with careful little tools.",
    "The kettle hummed softly beside a shelf of jars, buttons, wires, and folded cloth.",
]

MYSTERIES = {
    "bell": {
        "clue": "a faint silver jingle beneath the workbench",
        "event": "The little bell on the welcome board had vanished.",
        "answer": "the bell had slipped behind a basket when the morning cart bumped the bench",
        "reveal": "Luna found the bell behind a basket of clean cloths.",
        "object": "bell",
    },
    "button": {
        "clue": "a blue thread caught on the edge of the tool drawer",
        "event": "A bright blue button was missing from the mending tin.",
        "answer": "the button had rolled beneath the low cabinet while someone reached for thread",
        "reveal": "Luna spotted the button beneath the low cabinet.",
        "object": "button",
    },
    "key": {
        "clue": "a square mark in the dust beside the flowerpot",
        "event": "The small key to the garden cupboard was gone.",
        "answer": "the key had been carried under the flowerpot when the window breeze moved a paper",
        "reveal": "Luna lifted the flowerpot and found the key beside its saucer.",
        "object": "key",
    },
}

LESSONS = {
    "listen": {
        "memory": "Before guessing, listen to the small sounds around you.",
        "action": "paused and listened carefully",
    },
    "notice": {
        "memory": "Kind eyes notice what others may have missed.",
        "action": "looked slowly at the floor, the shelves, and the people nearby",
    },
    "ask": {
        "memory": "A gentle question can open a door that a hurried guess cannot.",
        "action": "asked everyone what they remembered, one person at a time",
    },
}

KINDNESS = {
    "tea": "Luna carried a warm cup of tea to the tired volunteer before searching again.",
    "cleanup": "Luna moved the scattered tools back into their trays so nobody would trip.",
    "thanks": "Luna thanked each helper, even when the clue they offered seemed very small.",
}

ENDINGS = {
    "window": "By afternoon, the missing object rested on the welcome board again, and sunlight made its little shadow dance.",
    "tea": "When the kettle clicked off, everyone shared the last lemon biscuits beside the neatly mended basket.",
    "door": "At closing time, the repaired room felt brighter, as if kindness had opened an extra window.",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str = "repair_room"
    place: str = "the community repair room"
    affords: set[str] = field(default_factory=lambda: {"repair", "search", "tea"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

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
    setting: str = "repair_room"
    mystery: str = "bell"
    lesson: str = "listen"
    kindness: str = "tea"
    ending: str = "window"
    name: str = "Luna"
    engineer: str = "Mara"
    seed: Optional[int] = None


SETTINGS = {"repair_room": Setting()}
ENGINEERS = ["Mara", "Inez", "Theo", "Sam"]
CHILDREN = ["Luna", "Nia", "Owen", "Pia"]

KNOWLEDGE = {
    "engineer": [
        QAItem(
            "What does an engineer do?",
            "An engineer uses careful thinking and practical skills to design, build, test, or improve things.",
        )
    ],
    "appendage": [
        QAItem(
            "What is an appendage?",
            "An appendage is a part that extends from a larger body or object, such as an arm, handle, or movable tool.",
        )
    ],
    "flashback": [
        QAItem(
            "What is a flashback?",
            "A flashback is a short part of a story that remembers something that happened earlier.",
        )
    ],
    "kindness": [
        QAItem(
            "How can kindness help solve a problem?",
            "Kindness helps people feel safe enough to share ideas, notice details, and work together.",
        )
    ],
}


def build_world(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    luna = world.add(Entity(params.name, "character", "girl", location="repair_room"))
    engineer = world.add(Entity(params.engineer, "character", "woman", location="repair_room"))
    appendage = world.add(
        Entity(
            "helping_appendage",
            "object",
            "appendage",
            label="a small folding appendage",
            owner=engineer.id,
            location="workbench",
        )
    )
    mystery = MYSTERIES[params.mystery]
    world.facts.update(
        luna=luna,
        engineer=engineer,
        appendage=appendage,
        mystery=mystery,
        lesson=LESSONS[params.lesson],
        kindness=KINDNESS[params.kindness],
        ending=ENDINGS[params.ending],
        scene=rng.choice(SCENES),
        opener=rng.choice(OPENERS),
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    luna = f["luna"]
    engineer = f["engineer"]
    appendage = f["appendage"]
    mystery = f["mystery"]
    lesson = f["lesson"]

    world.say(
        f"{f['opener']} there lived {luna.id}, who loved watching {engineer.id}, an engineer, make useful things."
    )
    world.say(
        f"That morning, {engineer.id} was testing {appendage.label}, a jointed appendage that could hold a cup, lift a book, and turn a stiff knob."
    )
    world.say(f"{f['scene']}")

    world.para()
    world.say(f"Then {mystery['event']}")
    world.say(
        f'"I can solve it quickly," {luna.id} said, reaching toward the crowded workbench.'
    )
    world.say(
        f'"Let us solve it kindly and carefully," {engineer.id} replied. "A small clue may be waiting for us."'
    )
    world.say(
        f"{luna.id} remembered a day when {engineer.id} had shown her how to test the appendage one gentle movement at a time."
    )
    world.say(
        f"That old moment returned like a picture in a window. {engineer.id} had said, \"{lesson['memory']}\""
    )

    world.para()
    world.say(f"First, {luna.id} {f['kindness']}.")
    world.say(
        f"Then she {lesson['action']}. She noticed {mystery['clue']} and pointed without touching anything."
    )
    world.say(
        f'"Could the sound be telling us where to look?" {luna.id} asked.'
    )
    world.say(
        f'"Yes," said {engineer.id}. "You noticed it because you gave the room time to speak."'
    )
    world.say(
        f"Using the safe tip of the appendage, {engineer.id} moved one basket aside. {mystery['reveal']}"
    )
    world.say(
        f"The mystery was solved: {mystery['answer']}. Nobody had done anything wrong; the busy room had simply hidden a little thing."
    )

    world.para()
    world.say(
        f"{luna.id} placed the {mystery['object']} back where everyone could see it, while {engineer.id} folded the appendage beside the tools."
    )
    world.say(
        f'"I learned that careful hands need kind helpers," {luna.id} said.'
    )
    world.say(
        f'"And I learned to listen to your clues," {engineer.id} answered.'
    )
    world.say(f"{f['ending']}")

    luna.memes["confidence"] = 1
    luna.memes["kindness"] = 1
    engineer.memes["trust"] = 1
    appendage.meters["used_carefully"] = 1
    world.trace.extend(
        [
            "Luna offered kindness before searching.",
            "The engineer remembered an earlier lesson through a flashback.",
            "A clue led to the missing object.",
            "The appendage was used carefully to reveal the hiding place.",
        ]
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story about {f['luna'].id}, {f['engineer'].id} the engineer, and {f['appendage'].label}.",
        f"Include a flashback containing this lesson: {f['lesson']['memory']}",
        f"Make the mystery of {f['mystery']['object']} disappear through kindness and a concrete clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    luna = f["luna"]
    engineer = f["engineer"]
    mystery = f["mystery"]
    return [
        QAItem(
            "Who was Luna with in the repair room?",
            f"{luna.id} was with {engineer.id}, an engineer who was testing a small folding appendage.",
        ),
        QAItem(
            "What mystery did Luna and the engineer solve?",
            f"They solved the mystery of the missing {mystery['object']} by following {mystery['clue']}.",
        ),
        QAItem(
            "How did kindness help?",
            f"{luna.id} {f['kindness']} before searching, which helped everyone stay calm and notice useful clues.",
        ),
        QAItem(
            "What did the flashback teach Luna?",
            f"The flashback reminded {luna.id} that {f['lesson']['memory'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for items in KNOWLEDGE.values() for item in items]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id}: {'; '.join(details)}")
    lines.extend(f"  event: {entry}" for entry in world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        lesson=args.lesson or rng.choice(list(LESSONS)),
        kindness=args.kindness or rng.choice(list(KINDNESS)),
        ending=args.ending or rng.choice(list(ENDINGS)),
        name=args.name or rng.choice(CHILDREN),
        engineer=args.engineer or rng.choice(ENGINEERS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.lesson not in LESSONS:
        raise StoryError(f"Unknown lesson: {params.lesson}")
    if params.kindness not in KINDNESS:
        raise StoryError(f"Unknown kindness choice: {params.kindness}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")
    if params.name == params.engineer:
        raise StoryError("The child and engineer must have different names.")

    world = build_world(params, random.Random(params.seed or 0))
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
setting(repair_room).
role(engineer).
role(child).
object(appendage).
mystery(bell).
mystery(button).
mystery(key).
lesson(listen).
lesson(notice).
lesson(ask).
kindness(tea).
kindness(cleanup).
kindness(thanks).
has_feature(repair_room, engineer).
has_feature(repair_room, appendage).
solvable(M) :- mystery(M), kindness(K), lesson(L).
valid_story(S, M) :- setting(S), mystery(M), solvable(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "repair_room"),
            asp.fact("role", "engineer"),
            asp.fact("role", "child"),
            asp.fact("object", "appendage"),
            *[asp.fact("mystery", key) for key in MYSTERIES],
            *[asp.fact("lesson", key) for key in LESSONS],
            *[asp.fact("kindness", key) for key in KINDNESS],
            asp.fact("has_feature", "repair_room", "engineer"),
            asp.fact("has_feature", "repair_room", "appendage"),
        ]
    )


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str]]:
    return {("repair_room", mystery) for mystery in MYSTERIES}


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = valid_combos()
    actual = asp_valid_combos()
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for seed in range(3):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or "appendage" not in sample.story or "engineer" not in sample.story:
            print("Generated story exercise failed.")
            return 1
    print(f"OK: ASP matches Python ({len(expected)} valid combinations), and stories generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about an engineer, an appendage, kindness, and a small mystery."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--kindness", choices=KINDNESS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("--name")
    parser.add_argument("--engineer")
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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    count = len(MYSTERIES) if args.all else max(1, args.n)
    for index in range(count):
        if args.all:
            params = StoryParams(
                mystery=list(MYSTERIES)[index],
                lesson=list(LESSONS)[index % len(LESSONS)],
                kindness=list(KINDNESS)[index % len(KINDNESS)],
                ending=list(ENDINGS)[index % len(ENDINGS)],
                seed=base_seed + index,
            )
        else:
            params = resolve_params(args, random.Random(base_seed + index))
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
