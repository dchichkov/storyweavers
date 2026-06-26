#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/board_resident_yum_dialogue_ghost_story.py
================================================================================================

A small, constraint-checked ghost-story world with dialogue.

Seed-tale premise:
- A resident hears spooky tapping from a board in a quiet old building.
- The board seems to whisper near a tasty "yum" smell from the kitchen.
- The resident and a gentle helper discover the board is not haunted by harm,
  but by a lonely little ghost who wants attention, warmth, and a snack.

This script turns that premise into a tiny simulation where physical meters and
emotional memes drive the story:
- the board can creak, tap, and reveal a hidden note
- the resident can feel fear, then curiosity, then kindness
- "yum" means a warm snack that softens the ghost's loneliness
- dialogue is central, and the ending proves the feeling changed
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old boarding house"
    affords: set[str] = field(default_factory=lambda: {"tap", "listen", "snack"})


@dataclass
class StoryParams:
    place: str
    resident_name: str
    resident_type: str
    helper_name: str
    helper_type: str
    snack: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _spooky_boards(world: World) -> list[str]:
    out = []
    board = world.get("board")
    resident = world.get("resident")
    if board.meters.get("creak", 0.0) >= THRESHOLD and resident.memes.get("fear", 0.0) >= THRESHOLD:
        sig = ("spook",)
        if sig not in world.fired:
            world.fired.add(sig)
            resident.memes["curiosity"] = resident.memes.get("curiosity", 0.0) + 1
            out.append("The board gave a low creak, and the resident took a careful step closer.")
    return out


def _ghost_revealed(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    snack = world.get("snack")
    if ghost.memes.get("lonely", 0.0) >= THRESHOLD and snack.meters.get("warm", 0.0) >= THRESHOLD:
        sig = ("ghost_revealed",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.memes["hope"] = ghost.memes.get("hope", 0.0) + 1
            out.append("A soft little glow drifted out from behind the board.")
    return out


def _resolve(world: World) -> list[str]:
    out = []
    resident = world.get("resident")
    ghost = world.get("ghost")
    board = world.get("board")
    if ghost.memes.get("hope", 0.0) >= THRESHOLD and resident.memes.get("kindness", 0.0) >= THRESHOLD:
        sig = ("resolve",)
        if sig not in world.fired:
            world.fired.add(sig)
            board.meters["steady"] = 1.0
            resident.memes["fear"] = 0.0
            ghost.memes["lonely"] = 0.0
            out.append("The board stopped rattling, as if it had finally finished telling its secret.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_spooky_boards, _ghost_revealed, _resolve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_board(world: World) -> None:
    board = world.add(Entity(
        id="board",
        type="board",
        label="the old board",
        kind="thing",
        meters={"creak": 0.0, "steady": 0.0},
    ))
    board.meters["creak"] = 1.0


def build_resident(world: World, params: StoryParams) -> Entity:
    resident = world.add(Entity(
        id="resident",
        kind="character",
        type=params.resident_type,
        label=params.resident_name,
        meters={"feet": 1.0},
        memes={"fear": 0.0, "curiosity": 0.0, "kindness": 0.0, "relief": 0.0},
    ))
    return resident


def build_helper(world: World, params: StoryParams) -> Entity:
    return world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"lamp": 1.0},
        memes={"brave": 1.0},
    ))


def build_ghost(world: World) -> Entity:
    return world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="a small ghost",
        meters={"glow": 0.0},
        memes={"lonely": 1.0, "hope": 0.0},
    ))


def build_snack(world: World, snack: str) -> Entity:
    return world.add(Entity(
        id="snack",
        type="snack",
        label=snack,
        phrase=f"a warm {snack}",
        meters={"warm": 1.0},
    ))


def scene_open(world: World) -> None:
    resident = world.get("resident")
    board = world.get("board")
    world.say(
        f"{resident.label} lived at {world.setting.place}, where the hallway was quiet and the old board hung by the stairs."
    )
    world.say(
        f"At night, the board made tiny tapping sounds, as if someone behind it wanted to say hello."
    )
    resident.memes["fear"] += 1
    resident.memes["curiosity"] += 1
    propagate(world)


def scene_dialogue(world: World) -> None:
    resident = world.get("resident")
    helper = world.get("helper")
    ghost = world.get("ghost")
    snack = world.get("snack")

    world.para()
    world.say(f'"Did you hear that?" {resident.label} whispered.')
    world.say(f'"Hear what?" {helper.label} asked, holding up a little lamp.')
    world.say(f'"The board," {resident.label} said. "It sounds like a ghost."')
    world.say(f'"Maybe," {helper.label} said, "but ghosts can be lonely too."')

    world.para()
    world.say(f"{helper.label} set down {snack.phrase} near the board.")
    resident.memes["kindness"] += 1
    ghost.memes["lonely"] += 0.0
    propagate(world)

    world.say(f'"If you are there," {resident.label} said softly, "you can come out. We brought something yum."')
    ghost.memes["lonely"] = 1.0
    ghost.meters["glow"] = 1.0
    world.say(f'"Yum?" a tiny voice asked from the dark.')
    world.say(f'"Yes," {helper.label} said. "Warm and easy to share."')
    propagate(world)


def scene_turn(world: World) -> None:
    resident = world.get("resident")
    ghost = world.get("ghost")
    board = world.get("board")
    world.para()
    world.say(f"The board gave one last wobble, then a little ghost floated out with a shy smile.")
    world.say(f'"I only tapped because I was alone," the ghost said. "I wanted someone to notice me."')
    resident.memes["fear"] = 0.0
    resident.memes["kindness"] += 1
    resident.memes["relief"] += 1
    board.meters["steady"] = 1.0
    propagate(world)


def scene_end(world: World) -> None:
    resident = world.get("resident")
    helper = world.get("helper")
    ghost = world.get("ghost")
    snack = world.get("snack")

    world.para()
    world.say(f'{resident.label} smiled. "You can stay near us," {resident.pronoun("subject")} said.')
    world.say(f'{helper.label} nodded. "And you can have the last bite of the {snack.label}."')
    world.say(f'The ghost took a tiny taste and sighed, "Yum."')
    world.say(
        f"After that, the board stayed quiet, the hallway felt friendly, and the little ghost drifted beside them like a new friend."
    )
    ghost.memes["hope"] += 1
    propagate(world)


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    build_board(world)
    build_resident(world, params)
    build_helper(world, params)
    build_ghost(world)
    build_snack(world, params.snack)

    scene_open(world)
    scene_dialogue(world)
    scene_turn(world)
    scene_end(world)

    world.facts.update(
        resident=world.get("resident"),
        helper=world.get("helper"),
        ghost=world.get("ghost"),
        board=world.get("board"),
        snack=world.get("snack"),
        place=params.place,
    )
    return world


PLACES = {
    "old boarding house": Setting(place="the old boarding house", affords={"tap", "listen", "snack"}),
    "quiet library": Setting(place="the quiet library", affords={"tap", "listen", "snack"}),
    "moonlit school": Setting(place="the moonlit school", affords={"tap", "listen", "snack"}),
}

SNACKS = ["bun", "muffin", "cookie", "cocoa"]
RESIDENT_TYPES = ["boy", "girl", "woman", "man"]
HELPER_TYPES = ["woman", "man", "girl", "boy"]
RESIDENT_NAMES = ["Mina", "Eli", "Nora", "Toby", "Lena", "Seth"]
HELPER_NAMES = ["Iris", "Pax", "Milo", "June", "Rae", "Owen"]


CURATED = [
    StoryParams(place="the old boarding house", resident_name="Mina", resident_type="girl",
                helper_name="Iris", helper_type="woman", snack="bun"),
    StoryParams(place="the quiet library", resident_name="Eli", resident_type="boy",
                helper_name="Pax", helper_type="man", snack="cookie"),
    StoryParams(place="the moonlit school", resident_name="Nora", resident_type="girl",
                helper_name="Milo", helper_type="boy", snack="cocoa"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [("board", "resident"), ("board", "yum"), ("resident", "yum")]


@dataclass
class StoryParamsRegistry:
    place: list[str] = field(default_factory=lambda: list(PLACES))
    snack: list[str] = field(default_factory=lambda: SNACKS)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    resident = f["resident"]
    return [
        f'Write a gentle ghost story for young children that includes the words "board", "resident", and "yum".',
        f"Tell a dialogue-heavy spooky story about {resident.label} in {f['place']} where a creaky board turns out to hide a lonely ghost.",
        f"Write a short story with a soft ghostly mood, a mysterious board, and a warm yum snack shared at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    resident: Entity = f["resident"]
    helper: Entity = f["helper"]
    ghost: Entity = f["ghost"]
    board: Entity = f["board"]
    snack: Entity = f["snack"]

    return [
        QAItem(
            question=f"Who was the resident in the story?",
            answer=f"The resident was {resident.label}, who lived in {f['place']} and heard the board tapping at night.",
        ),
        QAItem(
            question=f"What did the helper bring near the board?",
            answer=f"{helper.label} brought {snack.phrase} near the board so the lonely ghost would have something warm and yummy.",
        ),
        QAItem(
            question=f"What did the ghost want before it felt better?",
            answer=f"The ghost wanted someone to notice it because it was lonely behind the board.",
        ),
        QAItem(
            question=f"How did the story end for the board?",
            answer=f"The board became quiet and steady after the resident and helper learned the ghost was harmless.",
        ),
        QAItem(
            question=f"Why did the resident stop feeling afraid?",
            answer=f"{resident.label} stopped feeling afraid because the ghost spoke kindly, got a warm snack, and became a friend instead of a fright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a board?",
            answer="A board is a flat piece of wood or similar material. It can be used for a sign, a wall, or a surface that can creak when it is old.",
        ),
        QAItem(
            question="What does resident mean?",
            answer="A resident is a person who lives in a place, like a house, school, or apartment building.",
        ),
        QAItem(
            question="What does yum mean?",
            answer="Yum is a word people say when food tastes good and feels pleasant to eat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
board( board ).
resident( resident ).
ghost( ghost ).
snack( snack ).

at_risk(resident) :- resident(resident).
spooky(board) :- board(board).
yum(snack) :- snack(snack).

can_soothe(ghost) :- yum(snack), resident(resident).
good_end :- spooky(board), at_risk(resident), can_soothe(ghost).
#show good_end/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("board", "board"),
        asp.fact("resident", "resident"),
        asp.fact("ghost", "ghost"),
        asp.fact("snack", "snack"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small dialogue-heavy ghost story world.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--resident-name")
    ap.add_argument("--resident-type", choices=RESIDENT_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    resident_name = args.resident_name or rng.choice(RESIDENT_NAMES)
    resident_type = args.resident_type or rng.choice(RESIDENT_TYPES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    snack = args.snack or rng.choice(SNACKS)
    return StoryParams(
        place=place,
        resident_name=resident_name,
        resident_type=resident_type,
        helper_name=helper_name,
        helper_type=helper_type,
        snack=snack,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show good_end/0."))
    return any(sym.name == "good_end" for sym in model)


def asp_verify() -> int:
    py = True
    asp_ok = asp_valid()
    if py == asp_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH: ASP and Python reasonableness disagree.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP says the ghost story's ending is reasonable:", "yes" if asp_valid() else "no")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.resident_name} at {p.place} with {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
