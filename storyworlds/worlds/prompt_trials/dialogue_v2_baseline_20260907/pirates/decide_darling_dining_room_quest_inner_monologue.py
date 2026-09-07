#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

ASP_RULES = r"""
safe_tool(T) :- tool(T), safe(T).
valid(Q,Tool) :- quest(Q), tool(Tool), safe_tool(Tool), affords(Q,Tool).
resolved(Q) :- valid(Q,Tool).
"""


@dataclass
class Quest:
    id: str
    goal: str
    dark_place: str
    keepsake: str


@dataclass
class Tool:
    id: str
    label: str
    safe: bool


@dataclass
class World:
    quest: Quest
    tool: Tool
    child: str
    darling: str
    beats: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)

    def beat(self, text: str) -> None:
        self.beats.append(text)

    def render(self) -> str:
        return "\n\n".join(self.beats)


@dataclass
class StoryParams:
    quest: str
    tool: str
    child: str
    darling: str
    mood: str = "gentle"
    seed: Optional[int] = None


QUESTS = {
    "silver_spoon": Quest(
        "silver_spoon",
        "find the moon-silver spoon",
        "the shadow beneath the dining table",
        "a blue napkin folded like a tiny sail",
    ),
    "lost_button": Quest(
        "lost_button",
        "find the captain's lost button",
        "the quiet corner beside the china cabinet",
        "a red ribbon tied around a teacup",
    ),
    "crumb_treasure": Quest(
        "crumb_treasure",
        "rescue the last golden crumb",
        "the dim space beneath the sideboard",
        "a little wooden bead",
    ),
}

TOOLS = {
    "candle": Tool("candle", "a candle", False),
    "flashlight": Tool("flashlight", "a flashlight", True),
    "lantern": Tool("lantern", "a small battery lantern", True),
}

NAMES = ["Mia", "Lily", "Nora", "Ava", "Tom", "Sam", "Leo", "Ben"]
DARLINGS = ["Darling", "dear friend", "sweet captain"]


def affords(quest: Quest, tool: Tool) -> bool:
    return tool.safe and bool(quest.goal)


def valid_combos() -> list[tuple[str, str]]:
    return [
        (qid, tid)
        for qid, quest in QUESTS.items()
        for tid, tool in TOOLS.items()
        if affords(quest, tool)
    ]


def build_world(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    tool = TOOLS[params.tool]
    if not affords(quest, tool):
        raise StoryError(
            f"{tool.label.capitalize()} is not a safe choice for this dining-room quest."
        )

    world = World(quest, tool, params.child, params.darling)
    world.meters.update({"darkness": 1.0, "distance": 1.0, "warmth": 0.0})
    world.memes.update({"hope": 1.0, "worry": 0.0, "trust": 1.0})

    world.beat(
        f"After supper, {params.child} stayed in the dining room while the plates "
        f"waited quietly on the table. Tonight's quest was to {quest.goal}."
    )
    world.beat(
        f"The room felt bigger than usual. {quest.dark_place} held the treasure, "
        f"and the evening shadows made every chair seem to lean closer."
    )
    world.beat(
        f'"I could use {tool.label}," thought {params.child}. '
        f'"But should I decide alone, darling?"'
    )
    world.memes["worry"] += 1
    world.beat(
        f"{params.child} held {quest.keepsake} close and listened to the small "
        f"sound of the clock. The suspense made the quest feel important, not scary."
    )
    world.beat(
        f'"{params.darling}, I need your help," {params.child} whispered. '
        f'"Let us choose the safe way together."'
    )
    world.memes["trust"] += 1
    world.memes["worry"] -= 1
    world.meters["darkness"] = 0.0
    world.meters["warmth"] = 1.0
    world.beat(
        f"{params.darling} brought {tool.label}, and its friendly light slipped "
        f"across the dining table. The shadows shrank beneath the chairs."
    )
    world.beat(
        f"Together they looked slowly and carefully. At last, beneath the table, "
        f"they found what the quest had promised."
    )
    world.meters["distance"] = 0.0
    world.memes["hope"] += 1
    world.beat(
        f"{params.child} smiled. The treasure was safe, the dining room was warm, "
        f"and the best part of the adventure was having a darling friend nearby."
    )
    world.facts.update(
        outcome="resolved",
        goal=quest.goal,
        tool=tool.label,
        safe_tool=tool.label,
        decision="asked for help and chose safe light",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming dining-room quest in which {world.child} must decide whether to use unsafe light.",
        f"Include an inner monologue with the word darling and a suspenseful search for {world.quest.goal}.",
        "End with a safe choice, shared courage, and a warm image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            f"What quest did {world.child} have?",
            f"{world.child} was trying to {world.quest.goal} in the dining room.",
        ),
        QAItem(
            "What decision did the child make?",
            f"The child decided not to act alone and asked for help before choosing safe light.",
        ),
        QAItem(
            "Why did the dining room feel suspenseful?",
            f"The treasure was hidden in {world.quest.dark_place}, and the evening shadows made the familiar room feel mysterious.",
        ),
        QAItem(
            "What helped solve the quest?",
            f"{world.darling} brought {world.tool.label}, so they could search together safely.",
        ),
        QAItem(
            "How did the story end?",
            "They found the treasure and felt warm and happy because they had shared the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should children ask for help with a risky idea?",
            "Asking a trusted grown-up or friend can make a choice safer and helps everyone think clearly.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the quiet thought a character says inside their mind.",
        ),
        QAItem(
            "What makes a quest?",
            "A quest is a journey with a goal, a problem to solve, and something important to find or do.",
        ),
    ]


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


def asp_facts() -> str:
    lines = []
    for qid, quest in QUESTS.items():
        lines.append(f"quest({qid}).")
        for tid, tool in TOOLS.items():
            lines.append(f"tool({tid}).")
            if tool.safe:
                lines.append(f"safe({tid}).")
            if affords(quest, tool):
                lines.append(f"affords({qid},{tid}).")
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n#show valid/2.\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    try:
        import asp
        model = asp.one_model(asp_program())
        return sorted(asp.atoms(model, "valid"))
    except ImportError as exc:
        raise StoryError("ASP mode requires clingo to be installed.") from exc


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("\n== Story questions ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("\n== World knowledge ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"  quest: {world.quest.id}\n"
        f"  tool: {world.tool.id} (safe={world.tool.safe})\n"
        f"  child: {world.child}\n"
        f"  darling: {world.darling}\n"
        f"  meters: {world.meters}\n"
        f"  memes: {world.memes}\n"
        f"  facts: {world.facts}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming dining-room quest storyworld.")
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--child")
    parser.add_argument("--darling", choices=DARLINGS)
    parser.add_argument("--mood", default="gentle")
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
    quests = [args.quest] if args.quest else sorted(QUESTS)
    tools = [args.tool] if args.tool else sorted(TOOLS)
    combos = [(q, t) for q, t in valid_combos() if q in quests and t in tools]
    if not combos:
        raise StoryError("No safe quest and tool combination matches those choices.")
    quest, tool = rng.choice(combos)
    child = args.child or rng.choice(NAMES)
    darling = args.darling or rng.choice(DARLINGS)
    return StoryParams(
        quest=quest,
        tool=tool,
        child=child,
        darling=darling,
        mood=args.mood,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    py = set(valid_combos())
    try:
        asp = set(asp_valid_combos())
    except StoryError as exc:
        print(exc)
        return 1
    if py != asp:
        print(f"Mismatch: Python={sorted(py)} ASP={sorted(asp)}")
        return 1
    for seed in range(10):
        args = build_parser().parse_args(["--seed", str(seed)])
        generate(resolve_params(args, random.Random(seed)))
    print(f"OK: ASP/Python parity and generated stories verified ({len(py)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        for quest, tool in asp_valid_combos():
            print(f"{quest}: {tool}")
        return

    rng = random.Random(args.seed)
    if args.all:
        params_list = [
            StoryParams(q, t, child, darling)
            for q, t in valid_combos()
            for child, darling in [(NAMES[len(params_list) % len(NAMES)] if False else "Mia", "darling")]
        ]
        params_list = [
            StoryParams(q, t, NAMES[i % len(NAMES)], DARLINGS[i % len(DARLINGS)])
            for i, (q, t) in enumerate(valid_combos())
        ]
    else:
        params_list = [resolve_params(args, rng) for _ in range(args.n)]

    samples = []
    for i, params in enumerate(params_list):
        params.seed = (args.seed + i) if args.seed is not None else None
        samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### quest {i + 1}\n")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
