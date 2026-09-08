#!/usr/bin/env python3
"""
A tiny adventure world about a fellow-ship, an imposed burden, reconciliation,
teamwork, and a quest for a lost bell.
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
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    captain: str
    deckmate: str
    harbor: str
    quest: str
    obstacle: str
    relic: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def note(self, text: str) -> None:
        self.trace.append(text)


NAMES = [
    ("Luna", "Milo"),
    ("Nia", "Owen"),
    ("Tara", "Felix"),
    ("Ari", "Pip"),
]

HARBORS = {
    "moonlit_cove": "Moonlit Cove",
    "whispering_isle": "Whispering Isle",
    "blue_shell_bay": "Blue Shell Bay",
}

QUESTS = {
    "bell": ("the silver bell", "a bell that could guide every boat home"),
    "map": ("the folded star map", "a map that could reveal a safe passage"),
    "pearl": ("the blue pearl", "a pearl said to shine through fog"),
}

OBSTACLES = {
    "rope_bridge": "a swaying rope bridge",
    "storm": "a sudden squall",
    "thorn_cave": "a thorny cave mouth",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a small fellow-ship adventure about reconciliation and teamwork."
    )
    parser.add_argument("--captain")
    parser.add_argument("--deckmate")
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--obstacle", choices=OBSTACLES)
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
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    pair = rng.choice(NAMES)
    captain = args.captain or pair[0]
    deckmate = args.deckmate or pair[1]
    if captain == deckmate:
        raise StoryError("The captain and deckmate must have different names.")

    harbor = args.harbor or rng.choice(sorted(HARBORS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    obstacle = args.obstacle or rng.choice(sorted(OBSTACLES))

    return StoryParams(
        captain=captain,
        deckmate=deckmate,
        harbor=harbor,
        quest=quest,
        obstacle=obstacle,
        relic=QUESTS[quest][0],
    )


def generate(params: StoryParams) -> StorySample:
    if params.captain == params.deckmate:
        raise StoryError("A fellow-ship needs two different companions.")

    harbor = HARBORS[params.harbor]
    relic, purpose = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]

    world = World()
    captain = world.add(Entity("captain", "character", params.captain))
    deckmate = world.add(Entity("deckmate", "character", params.deckmate))
    ship = world.add(Entity("ship", "place", "the little ship"))
    treasure = world.add(Entity("relic", "object", relic))

    captain.memes["pride"] = 1
    deckmate.memes["hurt"] = 1
    ship.meters["distance"] = 1

    world.facts.update(
        harbor=harbor,
        relic=relic,
        purpose=purpose,
        obstacle=obstacle,
        captain=captain,
        deckmate=deckmate,
        ship=ship,
        treasure=treasure,
    )

    story = (
        f"At {harbor}, {params.captain} and {params.deckmate} shared a little ship "
        f"and called their crew a fellow-ship. They set out on a quest to find {relic}, "
        f"{purpose}."
        f"\n\n"
        f'"I will steer," said {params.captain}. "You carry the sail." '
        f'"But you always choose everything," said {params.deckmate}. '
        f'"That is not teamwork."'
        f"\n\n"
        f"{params.captain} wanted to impose a plan: straight ahead, no questions. "
        f"But the sea grew dark, and {obstacle} blocked the way. The ship bumped and "
        f"swirled until both friends had to grab the rail."
        f"\n\n"
        f'"I cannot guide us alone," admitted {params.captain}. '
        f'"And I should not have imposed my plan," said {params.deckmate}. '
        f'"Can we listen to each other?"'
        f"\n\n"
        f"They made peace. {params.captain} watched the waves while {params.deckmate} "
        f"read the stars. Together they found a quiet path around the danger and reached "
        f"a small island."
        f"\n\n"
        f"Under a flat stone, they discovered {relic}. Each friend held one side of "
        f"the treasure box, and together they carried it back across the shining water."
        f"\n\n"
        f"At {harbor}, the silver sound of their prize rang over the boats. "
        f"{params.captain} smiled at {params.deckmate}. "
        f'"A quest is better with a true fellow-ship." '
        f'"And teamwork makes every adventure stronger," replied {params.deckmate}.'
    )

    captain.memes["pride"] = 0
    captain.memes["trust"] = 1
    deckmate.memes["hurt"] = 0
    deckmate.memes["trust"] = 1
    ship.meters["distance"] = 2
    world.note("The captain imposed a plan.")
    world.note("The companions reconciled through honest dialogue.")
    world.note("They used teamwork to cross the obstacle.")
    world.note("The quest ended with the relic safely returned.")

    prompts = [
        (
            f"Write an Adventure story for young children about {params.captain} and "
            f"{params.deckmate}, whose fellow-ship is tested when one friend tries to "
            f"impose a plan during a quest."
        ),
        (
            f"Tell a child-friendly tale in which two shipmates reconcile, listen to "
            f"one another, and use teamwork to find {relic} near {obstacle}."
        ),
    ]

    story_qa = [
        QAItem(
            question=f"Who formed the fellow-ship?",
            answer=(
                f"{params.captain} and {params.deckmate} formed the fellow-ship "
                f"aboard their little ship."
            ),
        ),
        QAItem(
            question=f"What did {params.captain} try to impose?",
            answer=(
                f"{params.captain} tried to impose a plan in which the ship would go "
                f"straight ahead and nobody would ask questions."
            ),
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=(
                f"They admitted their mistakes, apologized for the imposed plan, and "
                f"agreed to listen to each other."
            ),
        ),
        QAItem(
            question="How did teamwork help them finish the quest?",
            answer=(
                f"{params.captain} watched the waves while {params.deckmate} read the "
                f"stars, so together they found a safe path around {obstacle}."
            ),
        ),
        QAItem(
            question=f"What did the friends find?",
            answer=f"They found {relic}, the treasure they had crossed the sea to seek.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means sharing jobs, listening, and helping one another reach a goal.",
        ),
        QAItem(
            question="Why is reconciliation useful?",
            answer="Reconciliation repairs trust so friends can work together again.",
        ),
        QAItem(
            question="What does impose mean?",
            answer="To impose something means to force an idea, rule, or burden on someone without listening to them.",
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


ASP_RULES = r"""
valid :- fellow_ship, quest, teamwork, reconciliation.
fellow_ship.
quest.
teamwork.
reconciliation.
"""


def asp_program() -> str:
    return ASP_RULES + "\n#show valid/0.\n"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.extend(f"event: {event}" for event in world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    sample = generate(
        StoryParams(
            captain="Luna",
            deckmate="Milo",
            harbor="moonlit_cove",
            quest="bell",
            obstacle="rope_bridge",
            relic="the silver bell",
            seed=1,
        )
    )
    checks = [
        "fellow-ship" in sample.story,
        "impose" in sample.story,
        "teamwork" in sample.story.lower(),
        "reconcile" in sample.story.lower(),
        len(sample.story_qa) >= 5,
        len(sample.world_qa) >= 3,
    ]
    if all(checks):
        print("OK: storyworld verification passed.")
        return 0
    print("FAIL: storyworld verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        try:
            from storyworlds import asp
            models = asp.solve(asp_program(), models=1)
            print("ASP models:", len(models))
            for symbol in models[0] if models else []:
                print(symbol)
        except ImportError as exc:
            raise StoryError("ASP mode requires clingo to be installed.") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    for index in range(len(NAMES) if args.all else args.n):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### Adventure {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
