#!/usr/bin/env python3
"""
storyworlds/worlds/brat_bless_import_dialogue_bedtime_story.py
==============================================================

A tiny bedtime-story world with dialogue, a grumbly little brat of a child,
a gentle blessing, and an "import" of comfort from the hallway lamp to the bed.

Seed tale used to shape the simulation:
---
At bedtime, Pip was being a little brat. Pip did not want to put on pajamas or
brush teeth. Mom said, "Let's bless the bedtime first." Then Dad came back from
the hallway and said he would import the soft lamp light into Pip's room by
moving the nightlight closer. Pip listened, laughed, and climbed into bed.

World idea:
- A child can build up grumpiness and resistance at bedtime.
- A parent can lower that resistance by offering a blessing and a comfort move.
- The "import" is a small, child-safe act of bringing something helpful from
  outside the room into the bedtime space.
- Dialogue is essential; the story should sound like a bedtime exchange, not a
  dry event log.

This file follows the Storyweavers contract and includes:
- StoryParams and registries
- build_parser / resolve_params / generate / emit / main
- Python reasonableness gate
- inline ASP twin via ASP_RULES
- --verify parity checks
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

BEDROOMS = {
    "nursery": {"lamp", "blanket", "pillow"},
    "small_room": {"lamp", "blanket", "teddy"},
    "shared_room": {"lamp", "blanket", "book"},
}

CALM_WORDS = ["soft", "gentle", "warm", "tiny", "sleepy"]
KIDS = ["Pip", "Milo", "Nina", "Ivy", "Theo", "Luna", "Maya", "Owen"]
PARENTS = ["mom", "dad", "mother", "father"]
NIGHTLY_ITEMS = ["pajamas", "teeth brush", "blanket", "nightlight", "storybook"]


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = {"grit": 0.0, "cozy": 0.0, "sleep": 0.0, **self.meters}
        self.memes = {"grump": 0.0, "trust": 0.0, "love": 0.0, "relief": 0.0, **self.memes}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    night_weather: str
    cozy_items: set[str] = field(default_factory=set)


@dataclass
class ComfortMove:
    id: str
    label: str
    act: str
    result: str
    helps: set[str]


@dataclass
class StoryParams:
    room: str
    move: str
    child: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Character) -> Character:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Character:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _child_pronoun(name: str) -> str:
    return "they"


def brighten(word: str) -> str:
    return word.capitalize()


def reasonableness_gate(room: Room, move: ComfortMove) -> bool:
    return move.id in room.cozy_items


def simulate_bedtime(world: World, child: Character, parent: Character, move: ComfortMove) -> None:
    child.memes["grump"] += 1
    child.meters["grit"] += 1
    world.say(
        f"It was bedtime in the {world.room.name}, and {child.id} was being a little brat."
    )
    world.say(
        f'"No," {child.id} said, hugging the pillow tight. "I do not want pajamas."'
    )
    world.say(
        f'"No teeth," {child.id} said next, and {parent.id} gave a patient sigh.'
    )
    world.para()

    world.say(
        f'"Let us bless bedtime first," {parent.id} said softly. "A small blessing can make a big night."'
    )
    child.memes["trust"] += 1
    child.memes["grump"] += 1  # still grumpy, but the blessing begins to work
    world.say(
        f'{parent.id} touched the blanket and said, "May this room stay soft, warm, and safe."'
    )
    child.meters["cozy"] += 1
    child.memes["relief"] += 1

    world.para()
    world.say(
        f'"Then I can import the lamp light," {parent.id} said.'
    )
    world.say(
        f'{parent.id} carried the little lamp from the hall and set it by the bed, '
        f"so the room would feel less dark and more sleepy."
    )
    child.meters["cozy"] += 1
    child.memes["love"] += 1
    world.say(
        f'"See?" {parent.id} asked. "{move.act}"'
    )
    world.say(
        f'"Okay," {child.id} whispered at last. "Maybe I can try."'
    )

    child.memes["grump"] = max(0.0, child.memes["grump"] - 2)
    child.meters["sleep"] += 1
    world.para()
    world.say(
        f'{child.id} put on pajamas, brushed teeth, and climbed into bed. '
        f'The {move.label} helped, and {child.id} curled up under the blanket with a small yawn.'
    )
    world.say(
        f'"Good night, little one," {parent.id} said. "{move.result}"'
    )
    world.say(
        f'{child.id} smiled in the soft lamp glow and fell asleep before the story was done.'
    )

    world.facts.update(
        child=child,
        parent=parent,
        move=move,
        room=world.room,
        resolved=True,
    )


def tell(room: Room, move: ComfortMove, child_name: str, parent_name: str, trait: str) -> World:
    world = World(room)
    child = world.add(Character(id=child_name, type="child", traits=["little", trait, "sleepy"]))
    parent = world.add(Character(id=parent_name, type="parent", label=parent_name))
    child.memes["grump"] = 2.0
    simulate_bedtime(world, child, parent, move)
    return world


ROOMS = {
    "nursery": Room(name="the nursery", night_weather="quiet", cozy_items={"lamp", "blanket"}),
    "small_room": Room(name="the small room", night_weather="still", cozy_items={"lamp", "blanket", "teddy"}),
    "shared_room": Room(name="the shared room", night_weather="calm", cozy_items={"lamp", "blanket", "book"}),
}

MOVES = {
    "lamp": ComfortMove(
        id="lamp",
        label="lamp light",
        act="the lamp light can make the dark corners feel friendly",
        result="The lamp stayed close, and the room felt safer for sleep.",
        helps={"dark", "fear"},
    ),
    "blanket": ComfortMove(
        id="blanket",
        label="blanket blessing",
        act="the blanket can help a child settle and feel tucked in",
        result="The blanket blessing kept the bed warm and cozy all night.",
        helps={"cold", "restless"},
    ),
    "book": ComfortMove(
        id="book",
        label="storybook import",
        act="a story can carry a sleepy mind from fussing into listening",
        result="The storybook stayed beside the pillow, ready for tomorrow too.",
        helps={"fuss", "worry"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room_name, room in ROOMS.items():
        for move_id, move in MOVES.items():
            if reasonableness_gate(room, move):
                combos.append((room_name, move_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world with a bratty child, a blessing, and an import of comfort."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=CALM_WORDS)
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
    if args.move and args.room:
        if not reasonableness_gate(ROOMS[args.room], MOVES[args.move]):
            raise StoryError(f"(No story: {MOVES[args.move].label} does not fit naturally in {ROOMS[args.room].name}.)")

    combos = [
        (r, m) for (r, m) in valid_combos()
        if (args.room is None or r == args.room)
        and (args.move is None or m == args.move)
    ]
    if not combos:
        raise StoryError("(No valid bedtime combination matches the given options.)")
    room, move = rng.choice(sorted(combos))
    child = args.child or rng.choice(KIDS)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(CALM_WORDS)
    return StoryParams(room=room, move=move, child=child, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short bedtime story with dialogue about a bratty child who learns to calm down.',
        f'Write a gentle story where {f["child"].id} resists bedtime until {f["parent"].id} offers a blessing and a comfort move.',
        'Tell a bedtime tale that includes the words "brat", "bless", and "import" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    move = f["move"]
    room = f["room"]
    return [
        QAItem(
            question=f"Why was {child.id} acting bratty at bedtime?",
            answer=f"{child.id} did not want pajamas or teeth brushing, so {child.id} fussed until {parent.id} helped make bedtime feel safer and softer.",
        ),
        QAItem(
            question=f"What did {parent.id} bless before the bedtime routine settled down?",
            answer=f"{parent.id} blessed the bedtime in {room.name} so the room would feel soft, warm, and safe.",
        ),
        QAItem(
            question=f"What did it mean to import the lamp light?",
            answer=f"It meant {parent.id} carried the lamp from the hall into the room so the bedtime space felt less dark and more cozy.",
        ),
        QAItem(
            question=f"How did the {move.label} help {child.id}?",
            answer=f"The {move.label} helped {child.id} relax enough to put on pajamas, brush teeth, and climb into bed without more fussing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blessing?",
            answer="A blessing is a kind wish or gentle saying that asks for good things like safety, peace, or comfort.",
        ),
        QAItem(
            question="What does import mean in this story?",
            answer="In this story, import means bringing something helpful from one place into another place, like moving lamp light into the bedroom.",
        ),
        QAItem(
            question="Why do children use blankets at bedtime?",
            answer="Blankets help children stay warm, feel tucked in, and settle down for sleep.",
        ),
    ]


ASP_RULES = r"""
room(Room) :- room_fact(Room).
move(Move) :- move_fact(Move).

reasonable(Room, Move) :- room_cozy(Room, Move).
valid_story(Room, Move) :- reasonable(Room, Move).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_name, room in ROOMS.items():
        lines.append(asp.fact("room_fact", room_name))
        for item in sorted(room.cozy_items):
            lines.append(asp.fact("room_cozy", room_name, item))
    for move_id in MOVES:
        lines.append(asp.fact("move_fact", move_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], MOVES[params.move], params.child, params.parent, params.trait)
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
    StoryParams(room="nursery", move="lamp", child="Pip", parent="mom", trait="soft"),
    StoryParams(room="small_room", move="blanket", child="Milo", parent="dad", trait="tiny"),
    StoryParams(room="shared_room", move="book", child="Nina", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible room/move combos:\n")
        for room, move in combos:
            print(f"  {room:11} {move}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child}: {p.move} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
