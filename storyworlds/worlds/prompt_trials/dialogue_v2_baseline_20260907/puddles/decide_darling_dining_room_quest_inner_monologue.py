#!/usr/bin/env python3
"""A small dining-room quest about deciding with care.

Darling finds a lost spoon before supper. The quest is tiny, but suspense grows
as a hungry family waits. An inner monologue helps Darling compare hurrying with
asking for help, and a warm decision restores the table's missing sparkle.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, *, cause: str = "",
               result: str = "") -> None:
        self.history.append(Event(kind, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    child: str
    darling: str
    helper: str
    object_name: str
    hiding_place: str
    mood: str
    seed: Optional[int] = None


SETTINGS = {
    "dining_room": {
        "label": "the dining room",
        "table": "the long wooden table",
        "light": "golden lamplight",
    },
}

CHILDREN = ["Mara", "Nell", "Toby", "Iris", "Pip", "June"]
DARLINGS = ["darling", "sweetheart", "dear one"]
HELPERS = ["Mom", "Dad", "Grandma", "Auntie"]
OBJECTS = ["silver spoon", "blue napkin ring", "tiny serving fork"]
PLACES = ["beneath a chair", "behind the bread basket", "under the sideboard"]
MOODS = ["thoughtful", "brave", "patient", "hopeful"]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("The story must take place in the dining room.")
    if params.child == params.helper:
        raise StoryError("The child and helper need different names.")
    if not params.object_name or not params.hiding_place:
        raise StoryError("The quest needs a lost object and a hiding place.")

    world = World()
    child = world.add(Entity(params.child, "character", params.child))
    helper = world.add(Entity(params.helper, "character", params.helper))
    treasure = world.add(Entity("lost_object", "thing", params.object_name))
    table = world.add(Entity("table", "furniture", "the long wooden table"))
    room = world.add(Entity("room", "setting", "the dining room"))
    child.memes.update(warmth=1.0, worry=0.0, courage=0.0)
    helper.memes.update(patience=1.0)
    treasure.meters.update(found=0.0, safe=0.0)
    world.facts.update(
        child=child,
        helper=helper,
        treasure=treasure,
        table=table,
        room=room,
        darling=params.darling,
        hiding_place=params.hiding_place,
        mood=params.mood,
        decided=False,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    darling = str(f["darling"])
    place = str(f["hiding_place"])

    world.record(
        "arrival",
        f'In the dining room, {child.label} helped set the table while '
        f'{helper.label} carried warm bread beneath {SETTINGS[params.setting]["light"]}. '
        f'"Thank you, darling," {helper.label} said. '
        f'Everyone was nearly ready for supper, and {child.label} felt proud to be useful.',
        cause="Supper was almost ready and the table needed one last place setting.",
        result="The dining room glowed with welcome.",
    )

    world.para()
    child.memes["worry"] += 1
    treasure.meters["missing"] = 1.0
    world.record(
        "discovery",
        f'Then {child.label} noticed that the {treasure.label} was missing. '
        f'The room suddenly seemed very quiet. "{darling.capitalize()}, where did it go?" '
        f'{child.label} whispered, looking at the empty place beside the plate.',
        cause=f"The {treasure.label} was not beside its plate.",
        result=f"{child.label} realized the table could not be finished without it.",
    )

    world.para()
    child.memes["worry"] += 1
    world.record(
        "suspense",
        f'{child.label} searched near the plates, then paused. '
        f'Inside, a little voice wondered, "Should I hurry and look everywhere, '
        f'or should I decide on one careful place at a time?" '
        f'Behind the bread basket there was nothing. The family waited kindly, '
        f'but the empty place still shone like a question.',
        cause="Hurrying could make the small search harder.",
        result=f"{child.label} chose to search calmly instead of scattering the table.",
    )

    world.para()
    child.memes["courage"] += 1
    child.memes["worry"] -= 1
    world.record(
        "decision",
        f'"I will decide carefully," said {child.label}. '
        f'"{darling.capitalize()}, can you help me remember where we used it?" '
        f'{helper.label} smiled and pointed toward {place}. '
        f'Together they looked behind the chair, beneath its wooden legs, '
        f'and finally saw a bright little edge.',
        cause=f"{child.label} asked for help and followed the memory of the table setting.",
        result=f"The {treasure.label} was found {place}.",
    )

    world.para()
    treasure.meters["found"] = 1.0
    treasure.meters["safe"] = 1.0
    treasure.meters["missing"] = 0.0
    world.facts["decided"] = True
    world.record(
        "resolution",
        f'{child.label} picked up the {treasure.label} and carried it with both hands. '
        f'{helper.label} helped place it beside the plate. '
        f'The table looked whole again, and the waiting family gave a warm little cheer. '
        f'{child.label} felt the best part of the quest was not finding the treasure, '
        f'but deciding to be patient and ask for help.',
        cause=f"The careful search and shared memory led to the missing {treasure.label}.",
        result="The table was ready, and everyone could begin supper together.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    return [
        f'Write a heartwarming dining-room quest about {child.label}, who must decide '
        f'how to find a missing {treasure.label}. Include suspense and an inner monologue.',
        f'Tell a gentle story in which a child calls someone "{f["darling"]}", '
        f'pauses before rushing, asks for help, and restores the supper table.',
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "Why was the child helping in the dining room?",
        "discovery": "What problem did the child notice?",
        "suspense": "What choice did the child consider?",
        "decision": "How did the child search for the missing object?",
        "resolution": "How was the dining table made ready?",
    }
    return [
        QAItem(question=questions[event.kind],
                answer=f"{event.cause} {event.result}")
        for event in world.history
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it useful to decide before hurrying?",
            answer="Deciding first can help you choose a calm plan and avoid making a small problem harder.",
        ),
        QAItem(
            question="Why can asking for help be a good idea?",
            answer="Another person may remember something or notice a clue that is easy to miss alone.",
        ),
        QAItem(
            question="What is a dining room?",
            answer="A dining room is a place where people sit together to eat meals.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
found_object :- careful_search, remembered_place, asked_for_help.
ready_table :- found_object.
careful_search.
remembered_place.
asked_for_help.
#show ready_table/0.
#show found_object/0.
#show careful_search/0.
#show remembered_place/0.
#show asked_for_help/0.
"""


def asp_program() -> str:
    return ASP_RULES


def asp_check() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    expected = {"careful_search", "remembered_place", "asked_for_help",
                "found_object", "ready_table"}
    if not expected.issubset(names):
        print("ASP check failed.")
        return 1
    print("OK: ASP quest plan reaches a ready table.")
    return 0


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("Generated sample has no world.")
    treasure: Entity = world.facts["treasure"]  # type: ignore[assignment]
    assert world.facts["decided"] is True
    assert treasure.meters["found"] == 1.0
    assert treasure.meters["safe"] == 1.0
    assert len(world.history) == 5
    assert "decide" in sample.story.lower()
    assert "dining room" in sample.story.lower()
    assert "darling" in sample.story.lower()
    assert not any(mark in sample.story for mark in ("{", "}", "meters=", "memes="))


CURATED = [
    StoryParams("dining_room", "Mara", "darling", "Mom", "silver spoon",
                "behind the bread basket", "thoughtful"),
    StoryParams("dining_room", "Toby", "sweetheart", "Dad", "blue napkin ring",
                "beneath a chair", "brave"),
    StoryParams("dining_room", "Iris", "dear one", "Grandma", "tiny serving fork",
                "under the sideboard", "patient"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming dining-room decision quest."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--child", default=None)
    parser.add_argument("--darling", choices=DARLINGS, default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS, default=None)
    parser.add_argument("--place", dest="hiding_place", choices=PLACES, default=None)
    parser.add_argument("--mood", choices=MOODS, default=None)
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
    setting = args.setting or "dining_room"
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([h for h in HELPERS if h != child])
    return StoryParams(
        setting=setting,
        child=child,
        darling=args.darling or rng.choice(DARLINGS),
        helper=helper,
        object_name=args.object_name or rng.choice(OBJECTS),
        hiding_place=args.hiding_place or rng.choice(PLACES),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    check_sample(sample)
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        print("Quest plan: decide carefully, remember the place, ask for help, find the object, ready the table.")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child}'s dining-room quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
