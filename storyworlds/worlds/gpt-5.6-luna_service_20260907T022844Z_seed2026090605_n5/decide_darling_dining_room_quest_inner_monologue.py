#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding with care."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    cause: str
    result: str


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class Setting:
    id: str
    label: str
    detail: str


@dataclass
class Quest:
    id: str
    object_label: str
    location: str
    clue: str
    reward: str


SETTINGS = {
    "dining_room": Setting(
        "dining_room",
        "the dining room",
        "The round table gleamed beneath the warm yellow light, and one empty chair waited beside it.",
    )
}

QUESTS = {
    "missing_spoon": Quest(
        "missing_spoon",
        "darling's silver spoon",
        "the sideboard",
        "a tiny shining mark near the napkin basket",
        "a place at the family table",
    ),
    "lost_recipe": Quest(
        "lost_recipe",
        "Grandma's recipe card",
        "the buffet drawer",
        "a curl of blue paper beneath a folded cloth",
        "the first warm biscuit",
    ),
    "empty_place": Quest(
        "empty_place",
        "a little welcome card",
        "the table drawer",
        "a red crayon star on the floor",
        "a new friend at dinner",
    ),
}

NAMES = ["Luna", "Milo", "Iris", "Theo", "Nora", "Eli"]
QUEST_IDS = list(QUESTS)
MOODS = ["curious", "thoughtful", "brave", "gentle"]

SOLUTIONS = {
    "follow_clue": "follows the small clue carefully",
    "ask_helper": "asks a trusted helper before guessing",
    "search_together": "invites someone to search together",
}

KNOWLEDGE = {
    "dining_room": [
        QAItem(
            "Why do families gather around a dining table?",
            "Families gather around a dining table to share food, talk together, and enjoy one another's company.",
        )
    ],
    "quest": [
        QAItem(
            "What is a quest?",
            "A quest is a careful search or journey toward a goal, often guided by clues.",
        )
    ],
    "feelings": [
        QAItem(
            "Why can waiting for an answer feel suspenseful?",
            "Waiting can feel suspenseful because you do not know what will happen, so each small clue seems important.",
        )
    ],
}


@dataclass
class StoryParams:
    quest: str
    name: str
    mood: str
    solution: str
    seed: Optional[int] = None


def valid_quests() -> list[str]:
    return sorted(QUESTS)


def build_world(params: StoryParams) -> World:
    if params.quest not in QUESTS:
        raise StoryError("That dining-room quest is not available.")
    if params.solution not in SOLUTIONS:
        raise StoryError("That solution is not a valid way to face the quest.")
    if not params.name.strip() or params.name in {"table", "darling"}:
        raise StoryError("The child's name must be a friendly, distinct name.")

    setting = SETTINGS["dining_room"]
    quest = QUESTS[params.quest]
    world = World(setting.label)
    child = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity("darling", "character", "darling"))
    goal = world.add(Entity("quest_object", "object", quest.object_label))
    child.memes.update(care=1.0, courage=0.0, worry=0.0)
    helper.memes.update(care=1.0)
    goal.meters.update(found=0.0, treasured=1.0)
    world.facts.update(child=child, helper=helper, goal=goal, quest=quest, setting=setting)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.facts["child"]
    helper = world.facts["helper"]
    goal = world.facts["goal"]
    quest = world.facts["quest"]
    setting = world.facts["setting"]

    world.record(
        "begin",
        f"{setting.detail} {child.label} had promised to find {goal.label} before dinner. "
        f"Everyone called the child darling, but the little quest still felt important.",
        f"{goal.label.capitalize()} was missing before the family meal.",
        f"{child.label} began a search through the dining room.",
    )

    child.memes["worry"] += 1.0
    world.record(
        "suspense",
        f"{child.label} looked beneath the table, then at the quiet sideboard. "
        f"Inside, a small thought whispered, “I must decide, darling. I can rush, or I can notice.” "
        f"The room seemed to hold its breath.",
        "The first glance had not revealed the missing treasure.",
        "A careful decision became more useful than a hurried guess.",
    )

    if params.solution == "follow_clue":
        child.memes["courage"] += 1.0
        text = (
            f"{child.label} decided to follow {quest.clue}. "
            f"The clue led toward {quest.location}, where a soft glimmer waited behind the cloth."
        )
        cause = f"The clue connected the dining-room mark with {goal.label}."
        result = f"{child.label} reached {quest.location} without disturbing the other table things."
    elif params.solution == "ask_helper":
        child.memes["courage"] += 1.0
        text = (
            f"{child.label} decided to ask darling for help. "
            f"Darling knelt beside the chair and said, “Let us look with patient eyes.” "
            f"Together they noticed {quest.clue}."
        )
        cause = f"The search felt uncertain, so {child.label} asked a trusted helper."
        result = "The shared search uncovered a clue."
    else:
        child.memes["courage"] += 1.0
        text = (
            f"{child.label} decided not to search alone. "
            f"Darling carried a napkin basket while {child.label} checked each safe corner. "
            f"At last, they spotted {quest.clue}."
        )
        cause = "A gentle search together made the quiet room feel less large."
        result = "The child and darling found the clue side by side."

    world.record("decision", text, cause, result)

    goal.meters["found"] = 1.0
    child.memes["worry"] = 0.0
    world.record(
        "resolution",
        f"Behind the cloth was {goal.label}. {child.label} lifted it carefully and smiled. "
        f"Darling gave a happy little clap, and the family made room for the treasure beside {quest.reward}.",
        f"The clue led the search to the correct place.",
        f"{goal.label.capitalize()} was found and ready for the family gathering.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    quest = world.facts["quest"]
    return [
        f"Write a heartwarming dining-room quest in which {child.label} must decide what to do when {quest.object_label} goes missing.",
        f"Tell a suspenseful story with an inner monologue, darling, and a gentle ending after {child.label} follows a clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    out = []
    for event in world.history:
        if event.kind == "begin":
            out.append(QAItem("What quest did the child begin?", f"{event.cause} {event.result}"))
        elif event.kind == "suspense":
            out.append(QAItem("What made the search feel suspenseful?", f"{event.cause} {event.result}"))
        elif event.kind == "decision":
            out.append(QAItem("How did the child decide to search?", f"{event.cause} {event.result}"))
        elif event.kind == "resolution":
            out.append(QAItem("What happened at the end of the quest?", f"{event.cause} {event.result}"))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE["dining_room"] + KNOWLEDGE["quest"] + KNOWLEDGE["feelings"]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(Q) :- quest_object(Q).
valid(Q) :- quest(Q).
found(Q) :- valid(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest_object", quest_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = sorted(a[0] for a in asp.atoms(model, "valid"))
    expected = valid_quests()
    if found != expected:
        print("MISMATCH: ASP and Python quest registries differ.")
        return 1
    for quest_id in expected:
        sample = generate(StoryParams(quest_id, "Luna", "thoughtful", "follow_clue"))
        assert sample.story and sample.story_qa
        assert sample.world.facts["goal"].meters["found"] == 1.0
    print(f"OK: {len(expected)} quests and generated story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming dining-room decision quest.")
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--name")
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--solution", choices=sorted(SOLUTIONS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    quest = args.quest or rng.choice(valid_quests())
    name = args.name or rng.choice(NAMES)
    mood = args.mood or rng.choice(MOODS)
    solution = args.solution or rng.choice(sorted(SOLUTIONS))
    return StoryParams(quest, name, mood, solution)


CURATED = [
    StoryParams("missing_spoon", "Luna", "thoughtful", "follow_clue"),
    StoryParams("lost_recipe", "Milo", "curious", "ask_helper"),
    StoryParams("empty_place", "Iris", "gentle", "search_together"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("Available dining-room quests:")
        for item in sorted(asp.atoms(model, "valid")):
            print(f"  {item[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(payload)
        return

    for index, sample in enumerate(samples):
        header = f"### quest {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
