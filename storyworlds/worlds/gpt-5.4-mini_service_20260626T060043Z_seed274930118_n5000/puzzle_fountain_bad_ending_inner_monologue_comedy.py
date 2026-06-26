#!/usr/bin/env python3
"""
A small comedy storyworld about a puzzle, a fountain, and a very confident plan
that goes slightly wrong.

Seed premise:
- A child wants to finish a puzzle near a fountain.
- The fountain seems harmless and funny.
- The child thinks they can manage it.
- In the end, the fountain causes a bad ending: puzzle pieces get wet and blow away.
- The tone stays child-facing and comedic, with inner monologue included in the prose.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the courtyard"
    has_fountain: bool = True


@dataclass
class Puzzle:
    label: str
    phrase: str
    pieces: int
    risk: str


@dataclass
class StoryParams:
    place: str
    puzzle: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "courtyard": Setting(place="the courtyard", has_fountain=True),
    "plaza": Setting(place="the plaza", has_fountain=True),
    "garden": Setting(place="the garden path", has_fountain=True),
}

PUZZLES = {
    "jigsaw": Puzzle(label="jigsaw puzzle", phrase="a bright jigsaw puzzle", pieces=12, risk="wet and slippery"),
    "floor": Puzzle(label="floor puzzle", phrase="a big floor puzzle", pieces=16, risk="scattered"),
    "animal": Puzzle(label="animal puzzle", phrase="a funny animal puzzle", pieces=20, risk="blown away"),
}

NAMES = {
    "girl": ["Mia", "Lina", "Zoe", "Ada", "Nina"],
    "boy": ["Max", "Owen", "Leo", "Eli", "Theo"],
}
TRAITS = ["curious", "cheerful", "silly", "brave", "busy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Puzzle + fountain comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    puzzle = args.puzzle or rng.choice(list(PUZZLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, puzzle=puzzle, name=name, gender=gender, parent=parent, trait=trait)


def _inner(thought: str) -> str:
    return f'({thought})'


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    puzzle_cfg = PUZZLES[params.puzzle]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    puzzle = world.add(Entity(
        id="puzzle", type=puzzle_cfg.label, label=puzzle_cfg.label,
        phrase=puzzle_cfg.phrase, owner=child.id, caretaker=parent.id, plural=True
    ))
    fountain = world.add(Entity(id="fountain", type="fountain", label="fountain"))

    child.memes["pride"] = 1.0
    child.memes["hope"] = 1.0

    world.say(f"{child.id} was a {params.trait} {params.gender} who loved quiet games and loud ideas.")
    world.say(f"One day, {child.id} found {puzzle.phrase} near {world.setting.place}.")
    world.say(f"{child.pronoun().capitalize()} wanted to finish the {puzzle.label} right there, because the pieces looked so neat and serious.")
    world.say(f"{_inner('This will be easy,' )} {child.id} thought. {_inner('I am an expert at one puzzle and two snacks.')}")

    world.para()
    world.say(f"{child.id} set the puzzle beside the fountain and started matching corners.")
    world.say(f"The fountain went splish-splash like it was trying out for a silly song.")
    world.say(f"{_inner('It is only water,' )} {child.id} thought. {_inner('Water is polite. Water knows about manners.')}")

    child.memes["confidence"] = 1.0
    puzzle.meters["dry"] = 1.0
    fountain.meters["spray"] = 1.0

    world.para()
    world.say(f"Then the wind gave one tiny puff.")
    puzzle.meters["wet"] = 1.0
    puzzle.meters["scattered"] = 1.0
    child.memes["alarm"] = 1.0
    world.say(f"A few puzzle pieces skated across the stone and landed too close to the fountain.")
    world.say(f"{_inner('Oops,' )} {child.id} thought. {_inner('That is not a neat and serious sound. That is a slipper-y sound.')}")

    world.say(
        f"{params.parent.capitalize()} hurried over and reached for the wet pieces, but by then "
        f"one piece had already drifted into a puddle and another had turned up under a bench."
    )
    world.say(
        f"{_inner('I should have moved the puzzle,' )} {child.id} thought. "
        f"{_inner('Now the fountain has become the main character, which is very rude of it.')}")

    world.para()
    world.say(
        f"In the end, the puzzle was unfinished, the stone was damp, and {child.id} had to help gather pieces one by one."
    )
    world.say(
        f"{child.id} laughed anyway, because the fountain had won the battle, but only by being splashy and annoying."
    )
    world.say(
        f"{_inner('Next time,' )} {child.id} thought, {_inner('I will pick a place far away from fountains, winds, and my own big ideas.')}")

    world.facts.update(
        child=child, parent=parent, puzzle=puzzle, fountain=fountain, setting=setting,
        puzzle_cfg=puzzle_cfg, bad_ending=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    puzzle_cfg = f["puzzle_cfg"]
    return [
        f'Write a short comedy story for a child named {child.id} who tries to finish {puzzle_cfg.phrase} near a fountain.',
        f'Tell a gentle funny story about a {child.type} named {child.id} and a fountain that ruins a puzzle.',
        f'Write a story with an inner monologue where {child.id} thinks the fountain will be harmless, but the puzzle goes wrong.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    puzzle_cfg = f["puzzle_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} try to finish near the fountain?",
            answer=f"{child.id} tried to finish {puzzle_cfg.phrase} near the fountain.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer="It ended badly because the fountain and a little wind made the puzzle pieces wet and scattered, so the puzzle could not be finished.",
        ),
        QAItem(
            question=f"What did {child.id} think inside {child.pronoun('possessive')} head?",
            answer=f"{child.id} thought the water would be polite and that finishing the puzzle would be easy, but the fountain proved that idea wrong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a fountain do?",
            answer="A fountain sprays or shoots water upward or outward, so it can make nearby things wet.",
        ),
        QAItem(
            question="What is a puzzle?",
            answer="A puzzle is a game or picture made from pieces that must be put together in the right way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A puzzle is ruined when fountain spray makes it wet and scattered.
ruined(P) :- puzzle(P), wet(P), scattered(P).

% A bad ending is present when the child's puzzle is ruined.
bad_ending(C, P) :- child(C), puzzle(P), ruined(P).

#show ruined/1.
#show bad_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for pid in PUZZLES:
        lines.append(asp.fact("puzzle", pid))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ruined/1.\n#show bad_ending/2."))
    atoms = set((sym.name, tuple(a.number if a.type == a.type.Number else a.string for a in sym.arguments)) for sym in model)
    expected = {("ruined", ("puzzle",)), ("bad_ending", ("child", "puzzle"))}
    if atoms == expected:
        print("OK: ASP gate matches Python story shape.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="courtyard", puzzle="jigsaw", name="Mia", gender="girl", parent="mother", trait="silly"),
    StoryParams(place="plaza", puzzle="floor", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="garden", puzzle="animal", name="Ada", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ruined/1.\n#show bad_ending/2."))
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
