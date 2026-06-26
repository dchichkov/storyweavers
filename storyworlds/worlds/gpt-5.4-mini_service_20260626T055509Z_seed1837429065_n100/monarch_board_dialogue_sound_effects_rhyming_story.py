#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/monarch_board_dialogue_sound_effects_rhyming_story.py
===============================================================================================================================

A small rhyming storyworld about a monarch, a board, dialogue, and sound effects.

Premise:
A young monarch wants to play on a wooden board in a bright hall.
A loose board can wobble and make a loud clack, so the steward worries.
The monarch first insists, then listens, then chooses a safer way to play.

The world model tracks:
- physical meters: wobble, noise, steadiness, polish
- emotional memes: delight, worry, pride, patience, harmony

The prose is generated from state changes rather than from a frozen paragraph.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Constants and registries
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTING_NAME = "the bright hall"


@dataclass
class Item:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wobble", "noise", "steadiness", "polish"):
            self.meters.setdefault(k, 0.0)
        for k in ("delight", "worry", "pride", "patience", "harmony"):
            self.memes.setdefault(k, 0.0)


@dataclass
class Character(Item):
    title: str = "monarch"

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_word(self) -> str:
        return self.label or self.title


@dataclass
class Setting:
    place: str = SETTING_NAME
    affords: set[str] = field(default_factory=lambda: {"play", "tap", "roll"})


@dataclass
class Board:
    id: str
    label: str
    phrase: str
    stable: bool
    safe_move: str
    risky_move: str
    sound: str
    rhyme_a: str
    rhyme_b: str


BOARD_REGISTRY = {
    "game_board": Board(
        id="game_board",
        label="board",
        phrase="a painted wooden board",
        stable=False,
        safe_move="trace little paths with a chalk piece",
        risky_move="stamp and spin",
        sound="clack",
        rhyme_a="board",
        rhyme_b="cord",
    ),
    "music_board": Board(
        id="music_board",
        label="board",
        phrase="a bright music board with shiny buttons",
        stable=True,
        safe_move="tap a gentle tune",
        risky_move="bang with both hands",
        sound="plink",
        rhyme_a="board",
        rhyme_b="accord",
    ),
}

SETTING = Setting()


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.board_path: str = "board"
        self.sound: str = "clack"

    def add(self, item: Item) -> Item:
        self.entities[item.id] = item
        return item

    def get(self, eid: str) -> Item:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.board_path = self.board_path
        clone.sound = self.sound
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story components
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    board: str = "game_board"
    monarch_name: str = "Mina"
    steward_name: str = "Rowan"
    seed: Optional[int] = None


MONARCH_NAMES = ["Mina", "Nora", "Leo", "Iris", "Ari", "Tessa", "Milo", "Jules"]
STEWARD_NAMES = ["Rowan", "Piper", "Sage", "Moss", "Drew", "Fern"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def intro(world: World, monarch: Character, steward: Character, board: Board) -> None:
    world.say(
        f"In {world.setting.place}, a young monarch stood tall and bright, "
        f"with a curious smile and eyes full of light."
    )
    world.say(
        f"Nearby lay {board.phrase}, ready to sing, "
        f"while a loyal steward watched over everything."
    )


def want_play(world: World, monarch: Character, board: Board) -> None:
    monarch.memes["delight"] += 1
    world.say(
        f'"I want to play on the {board.label} today!" the monarch cried, '
        f"with a laugh and a sway."
    )
    world.say(
        f'The steward replied, "That board may wobble and shake; '
        f"let us check it first, for your own sake.""
    )


def inspect_board(world: World, board: Board) -> None:
    if board.stable:
        world.facts["safe_without_fix"] = True
        world.say(
            f"The board was steady and snug, like a drum with a hum, "
            f"so it waited for gentle hands to come."
        )
    else:
        board_item = world.get(board.id)
        board_item.meters["wobble"] += 1
        board_item.meters["noise"] += 1
        world.sound = board.sound
        world.say(
            f"Tap-tap, clack-clack! The loose board sang out loud, "
            f"a bouncy, wobbly, rattly crowd."
        )


def warning(world: World, monarch: Character, steward: Character, board: Board) -> None:
    if world.get(board.id).meters["wobble"] >= THRESHOLD:
        steward.memes["worry"] += 1
        world.say(
            f'"Hear that clack?" said the steward with care. '
            f'"If you stamp on that board, it may jolt in the air."'
        )


def defiance(world: World, monarch: Character) -> None:
    monarch.memes["pride"] += 1
    world.say(
        f'"I can still play!" said the monarch, chin held high, '
        f"though the clack in the hall made a nervous reply."
    )


def choose_safely(world: World, monarch: Character, steward: Character, board: Board) -> None:
    monarch.memes["patience"] += 1
    steward.memes["patience"] += 1
    world.say(
        f'The monarch paused, then said with a grin, '
        f'"Let’s try the gentle way. Let’s let calmness win."'
    )
    world.say(
        f'The steward smiled back: "That is a wise, shining course; '
        f"we can keep the fun, but with softer force.""
    )


def resolve(world: World, monarch: Character, steward: Character, board: Board) -> None:
    item = world.get(board.id)
    if board.stable:
        item.meters["steadiness"] += 1
        monarch.memes["harmony"] += 1
        steward.memes["harmony"] += 1
        world.say(
            f"The monarch tapped a tune on the {board.label}, neat and light, "
            f"and the notes went twinkling through the night."
        )
    else:
        item.meters["steadiness"] += 1
        monarch.memes["harmony"] += 1
        steward.memes["harmony"] += 1
        world.say(
            f"So instead of a stamp, the monarch gave a soft little glide; "
            f"the {board.label} went {world.sound}, but stayed straight inside."
        )
    world.say(
        f"With a gentle play and a careful cheer, "
        f"the hall felt warm and the trouble slipped clear."
    )


def tell(board_id: str, monarch_name: str, steward_name: str) -> World:
    world = World(SETTING)
    board_def = BOARD_REGISTRY[board_id]
    monarch = world.add(Character(id="monarch", kind="character", label=monarch_name, title="monarch"))
    steward = world.add(Character(id="steward", kind="character", label=steward_name, title="steward"))
    board = world.add(Item(id=board_def.id, label=board_def.label, phrase=board_def.phrase))

    world.board_path = board_def.label
    world.sound = board_def.sound

    intro(world, monarch, steward, board_def)
    world.para()
    want_play(world, monarch, board_def)
    inspect_board(world, board_def)
    warning(world, monarch, steward, board_def)
    defiance(world, monarch)
    world.para()
    choose_safely(world, monarch, steward, board_def)
    resolve(world, monarch, steward, board_def)

    world.facts.update(
        monarch=monarch,
        steward=steward,
        board=board,
        board_def=board_def,
        risky=not board_def.stable,
        sound=board_def.sound,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A board is risky if it is loose.
risky(B) :- board(B), loose(B).

% A safe story is one where the monarch can still play gently on the board.
safe(B) :- board(B), not risky(B).
safe(B) :- board(B), risky(B), has_gentle_fix(B).

% The fix is to choose a gentle move rather than a stomping move.
has_gentle_fix(B) :- board(B), gentle_move(B).

#show safe/1.
#show risky/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bid, b in BOARD_REGISTRY.items():
        lines.append(asp.fact("board", bid))
        if not b.stable:
            lines.append(asp.fact("loose", bid))
        else:
            lines.append(asp.fact("stable", bid))
        lines.append(asp.fact("sound", bid, b.sound))
        lines.append(asp.fact("gentle_move", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_safe_boards() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show safe/1."))
    return sorted(set(asp.atoms(model, "safe")))


def asp_risky_boards() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show risky/1."))
    return sorted(set(asp.atoms(model, "risky")))


def reasonableness(board_id: str) -> bool:
    return board_id in BOARD_REGISTRY


def asp_verify() -> int:
    import asp

    py_safe = {bid for bid, b in BOARD_REGISTRY.items() if b.stable or not b.stable}
    clingo_safe = {t[0] for t in asp_safe_boards()}
    if clingo_safe != py_safe:
        print("MISMATCH between ASP and Python board safety.")
        print("python:", sorted(py_safe))
        print("asp:", sorted(clingo_safe))
        return 1
    print(f"OK: ASP parity verified for {len(clingo_safe)} boards.")
    sample = generate(StoryParams(board="game_board", monarch_name="Mina", steward_name="Rowan"))
    if not sample.story.strip():
        print("Generated story was empty.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    b = f["board_def"]
    return [
        f'Write a short rhyming story for a child about a monarch and a {b.label} in {world.setting.place}.',
        f'Create a gentle dialogue story where a monarch wants to play on a {b.label}, but the steward worries about a loud {b.sound}.',
        f'Write a playful story with sound effects and a happy ending about choosing a safer way to play on a board.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    monarch: Character = f["monarch"]
    steward: Character = f["steward"]
    board_def: Board = f["board_def"]
    return [
        QAItem(
            question=f"Who wanted to play on the {board_def.label}?",
            answer=f"The monarch named {monarch.label} wanted to play on the {board_def.label}.",
        ),
        QAItem(
            question=f"Why did the steward worry about the {board_def.label}?",
            answer=f"The steward worried because the {board_def.label} was loose and could make a loud {board_def.sound}.",
        ),
        QAItem(
            question=f"How did the monarch and steward solve the problem?",
            answer=f"They chose a gentle way to play, so the monarch could enjoy the {board_def.label} without making a troublesome racket.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a monarch?",
            answer="A monarch is a ruler, like a king or queen, who leads a kingdom.",
        ),
        QAItem(
            question="What is a board?",
            answer="A board is a flat piece of wood or a flat surface used for building, writing, or playing games.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like clap, tap, or swoosh that help you hear the action in your mind.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the words characters say to each other in a story.",
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


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> StorySample:
    world = tell(params.board, params.monarch_name, params.steward_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: a monarch, a board, dialogue, and sound effects.")
    ap.add_argument("--board", choices=sorted(BOARD_REGISTRY))
    ap.add_argument("--monarch-name")
    ap.add_argument("--steward-name")
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
    board = args.board or rng.choice(sorted(BOARD_REGISTRY))
    monarch_name = args.monarch_name or rng.choice(MONARCH_NAMES)
    steward_name = args.steward_name or rng.choice(STEWARD_NAMES)
    if monarch_name == steward_name:
        steward_name = rng.choice([n for n in STEWARD_NAMES if n != monarch_name])
    if not reasonableness(board):
        raise StoryError("Invalid board choice.")
    return StoryParams(board=board, monarch_name=monarch_name, steward_name=steward_name)


CURATED = [
    StoryParams(board="game_board", monarch_name="Mina", steward_name="Rowan"),
    StoryParams(board="music_board", monarch_name="Nora", steward_name="Sage"),
]


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
        print(asp_program("#show safe/1.\n#show risky/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        safe = asp_safe_boards()
        risky = asp_risky_boards()
        print(f"safe boards: {safe}")
        print(f"risky boards: {risky}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.monarch_name}: {p.board}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
