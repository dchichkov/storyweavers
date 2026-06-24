#!/usr/bin/env python3
"""
storyworlds/worlds/ratio_reconciliation_curiosity_ghost_story.py
===============================================================

A standalone storyworld about a child, a curious ghost, and a ratio riddle
that only settles when everyone agrees on the numbers.

Premise:
- A child finds a ghostly counting board in an old room.
- The ghost is worried because a "ratio" between two collections feels wrong.
- Curiosity pulls the child into the puzzle.
- Reconciliation happens when the child and ghost compare the parts carefully,
  admit the mistake, and repair the balance together.

The domain is intentionally small:
- one setting
- one ghost
- one child
- one ratio board made of two stacks of glowing pebbles
- one tension: the stacks do not match the stated ratio
- one turn: curious checking reveals the true balance
- one resolution: both sides reconcile and restore the board

The style aims for a gentle ghost story: dim hallway, moonlight, whispers, soft
glow, a little mystery, and a warm ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def label_word(self) -> str:
        return self.label


@dataclass
class Setting:
    label: str
    room_detail: str
    mood: str


@dataclass
class RatioBoard:
    left_label: str
    right_label: str
    target_ratio_num: int
    target_ratio_den: int
    left_count: int
    right_count: int
    material: str
    glow: str

    def as_tuple(self) -> tuple[int, int]:
        return self.left_count, self.right_count


@dataclass
class StoryParams:
    setting: str
    child_name: str
    ghost_name: str
    left_label: str
    right_label: str
    target_ratio_num: int
    target_ratio_den: int
    left_count: int
    right_count: int
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(
        label="the attic",
        room_detail="Old beams crossed the ceiling, and moonlight slipped through a round window.",
        mood="quiet and dusty",
    ),
    "hall": Setting(
        label="the hallway",
        room_detail="The wallpaper was faded, and a silver lamp made the shadows look long.",
        mood="still and sleepy",
    ),
    "library": Setting(
        label="the library",
        room_detail="Tall shelves leaned close, and every page seemed to whisper in the dark.",
        mood="soft and watchful",
    ),
}

CHILD_NAMES = ["Mina", "Nico", "Pia", "Leo", "Ivy", "Ari", "June", "Tess"]
GHOST_NAMES = ["Murmur", "Wisp", "Mallow", "Pale", "Flicker"]
LEFT_LABELS = ["blue stones", "white shells", "tiny bones"]
RIGHT_LABELS = ["green stones", "glass beads", "small keys"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.child = Entity(id="child", kind="child", label="", meters={}, memes={})
        self.ghost = Entity(id="ghost", kind="ghost", label="", meters={}, memes={})
        self.board = Entity(id="board", kind="object", label="ratio board", meters={}, memes={})
        self.facts: dict[str, object] = {}
        self.history: list[str] = []

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


def clean_name(name: str, fallback: str) -> str:
    if not name or not name.strip():
        return fallback
    return name.strip()


def ratio_matches(board: RatioBoard) -> bool:
    return board.left_count * board.target_ratio_den == board.right_count * board.target_ratio_num


def ratio_text(board: RatioBoard) -> str:
    return f"{board.left_count}:{board.right_count}"


def build_board(params: StoryParams) -> RatioBoard:
    return RatioBoard(
        left_label=params.left_label,
        right_label=params.right_label,
        target_ratio_num=params.target_ratio_num,
        target_ratio_den=params.target_ratio_den,
        left_count=params.left_count,
        right_count=params.right_count,
        material="glowing pebbles",
        glow="faint gold light",
    )


def tell(setting: Setting, board: RatioBoard, child_name: str, ghost_name: str) -> World:
    world = World(setting)
    child = world.child
    ghost = world.ghost
    child.label = child_name
    ghost.label = ghost_name

    child.memes["curiosity"] = 1.0
    ghost.memes["worry"] = 1.0

    world.say(
        f"{child_name} wandered into {setting.label}, where {setting.room_detail}"
    )
    world.say(
        f"Under the moonlight, {ghost_name} hovered beside a small board made of {board.material}."
    )
    world.say(
        f"Two little piles rested there: {board.left_count} {board.left_label} on one side and "
        f"{board.right_count} {board.right_label} on the other."
    )
    world.say(
        f'"The ratio should be {board.target_ratio_num}:{board.target_ratio_den}," whispered {ghost_name}, '
        f'"but these piles feel wrong."'
    )

    world.say(
        f"{child_name} leaned closer, curious instead of scared, and counted the pebbles one by one."
    )
    child.meters["steps"] = 2
    child.memes["curiosity"] += 1.0

    if ratio_matches(board):
        ghost.memes["worry"] = 0.0
        ghost.memes["relief"] = 1.0
        child.memes["joy"] = 1.0
        world.say(
            f"The numbers matched after all: {ratio_text(board)} was the same careful shape as "
            f"{board.target_ratio_num}:{board.target_ratio_den}."
        )
        world.say(
            f"{ghost_name} gave a soft little laugh, and {child_name} smiled back, glad the room had not been mistaken."
        )
        world.say(
            f"Together they left the glowing piles untouched, and the attic felt calm again."
        )
        world.facts["outcome"] = "matched"
    else:
        ghost.memes["worry"] = 0.0
        ghost.memes["relief"] = 1.0
        child.memes["curiosity"] += 1.0
        child.memes["reconciliation"] = 1.0
        ghost.memes["reconciliation"] = 1.0
        world.say(
            f"{child_name} shook their head gently. The piles did not match the promised ratio after all."
        )
        world.say(
            f"One side needed more pieces, so {child_name} moved a few glowing pebbles until the balance was right."
        )
        world.say(
            f"{ghost_name} stopped worrying, and the two of them reconciled over the board, side by side, as the glow turned even."
        )
        world.say(
            f"In the end, the little piles shone in a true {board.target_ratio_num}:{board.target_ratio_den} balance, "
            f"and the room looked peaceful instead of puzzled."
        )
        world.facts["outcome"] = "reconciled"

    world.facts.update(
        child=child,
        ghost=ghost,
        board=board,
        setting=setting,
        ratio=f"{board.left_count}:{board.right_count}",
        target_ratio=f"{board.target_ratio_num}:{board.target_ratio_den}",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    board: RatioBoard = world.facts["board"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old about {child.label} and {ghost.label} in {setting.label}, with a ratio puzzle.',
        f'Tell a small mystery where a child notices that {board.left_count}:{board.right_count} does not fit {board.target_ratio_num}:{board.target_ratio_den}, then helps the ghost fix it.',
        f'Write a child-facing story about curiosity and reconciliation set in {setting.label}, ending with glowing piles that finally match.',
    ]


def story_qa(world: World) -> list[QAItem]:
    board: RatioBoard = world.facts["board"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    outcome = world.facts["outcome"]

    qa = [
        QAItem(
            question=f"Where did {child.label} meet {ghost.label}?",
            answer=f"{child.label} met {ghost.label} in {setting.label}, where the room was quiet and a little mysterious.",
        ),
        QAItem(
            question=f"What was strange about the glowing piles in {setting.label}?",
            answer=f"The piles were {board.left_count}:{board.right_count}, but they were supposed to fit a {board.target_ratio_num}:{board.target_ratio_den} ratio.",
        ),
        QAItem(
            question=f"Why did {ghost.label} worry at first?",
            answer=f"{ghost.label} worried because the two piles did not seem to match the promised ratio, so the board felt unbalanced.",
        ),
        QAItem(
            question=f"What did {child.label} bring to the problem?",
            answer=f"{child.label} brought curiosity and careful counting, which helped everyone see the numbers clearly.",
        ),
    ]

    if outcome == "reconciled":
        qa.append(
            QAItem(
                question=f"How did {child.label} and {ghost.label} fix the board?",
                answer=f"{child.label} moved a few glowing pebbles, and then {ghost.label} relaxed because the board finally matched the right ratio.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"The worry turned into reconciliation, and the board ended in a neat {board.target_ratio_num}:{board.target_ratio_den} balance.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"What did {child.label} learn after counting the pebbles?",
                answer=f"{child.label} learned that the piles were already balanced, so the ghost's worry could turn into a happy, gentle laugh.",
            )
        )
        qa.append(
            QAItem(
                question=f"What was the ending image?",
                answer=f"The glowing piles stayed still and even, and the room felt calm again.",
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratio?",
            answer="A ratio tells how many parts one group has compared with another group. It helps people compare sizes and amounts.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn more about something. A curious child keeps noticing details and asking gentle questions.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were worried or apart make peace again. They listen, fix the trouble, and feel close once more.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale with a spooky feeling, like dim light, whispers, or a ghostly character, but it can still end safely and kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    board: RatioBoard = world.facts["board"]  # type: ignore[assignment]
    lines = ["--- world model state ---"]
    lines.append(f"setting: {world.setting.label}")
    lines.append(f"child: meters={world.child.meters} memes={world.child.memes}")
    lines.append(f"ghost: meters={world.ghost.meters} memes={world.ghost.memes}")
    lines.append(
        f"board: {board.left_label}={board.left_count}, {board.right_label}={board.right_count}, target={board.target_ratio_num}:{board.target_ratio_den}"
    )
    lines.append(f"outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for left_label in LEFT_LABELS:
            for right_label in RIGHT_LABELS:
                for num, den in [(1, 2), (2, 3), (3, 4)]:
                    for left_count in range(1, 5):
                        for right_count in range(1, 5):
                            if left_count * den == right_count * num:
                                combos.append((setting, left_label, right_label))
                                break
    return sorted(set(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about ratio, curiosity, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("--left-label", choices=LEFT_LABELS)
    ap.add_argument("--right-label", choices=RIGHT_LABELS)
    ap.add_argument("--target-num", type=int, choices=[1, 2, 3])
    ap.add_argument("--target-den", type=int, choices=[2, 3, 4])
    ap.add_argument("--left-count", type=int)
    ap.add_argument("--right-count", type=int)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    left_label = args.left_label or rng.choice(LEFT_LABELS)
    right_label = args.right_label or rng.choice(RIGHT_LABELS)
    target_num = args.target_num or rng.choice([1, 2, 3])
    target_den = args.target_den or rng.choice([2, 3, 4])

    if args.left_count is not None and args.right_count is not None:
        left_count, right_count = args.left_count, args.right_count
    else:
        factor = rng.choice([1, 2, 3])
        left_count = args.left_count or target_num * factor
        right_count = args.right_count or target_den * factor

    if left_count <= 0 or right_count <= 0:
        raise StoryError("Counts must be positive.")
    if left_count > 9 or right_count > 9:
        raise StoryError("Counts are too large for this small ghost story.")
    return StoryParams(
        setting=setting,
        child_name=child_name,
        ghost_name=ghost_name,
        left_label=left_label,
        right_label=right_label,
        target_ratio_num=target_num,
        target_ratio_den=target_den,
        left_count=left_count,
        right_count=right_count,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    board = build_board(params)
    world = tell(setting, board, params.child_name, params.ghost_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
setting(s1). child(c1). ghost(g1). board(b1).
ratio_target(b1, N, D) :- target_ratio(N, D).
ratio_board(b1, L, R) :- left_count(L), right_count(R).
ratio_match(b1) :- ratio_board(b1, L, R), ratio_target(b1, N, D), L * D == R * N.
curious(c1) :- curiosity(c1).
reconcile(c1, g1) :- curious(c1), ghost_worry(g1), ratio_match(b1).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "attic"),
        asp.fact("setting", "hall"),
        asp.fact("setting", "library"),
        asp.fact("curiosity", "child"),
        asp.fact("ghost_worry", "ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(
        setting="library",
        child_name="Mina",
        ghost_name="Wisp",
        left_label="blue stones",
        right_label="green stones",
        target_ratio_num=2,
        target_ratio_den=3,
        left_count=4,
        right_count=6,
    ),
    StoryParams(
        setting="attic",
        child_name="Leo",
        ghost_name="Murmur",
        left_label="white shells",
        right_label="glass beads",
        target_ratio_num=1,
        target_ratio_den=2,
        left_count=2,
        right_count=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show ratio_match/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
