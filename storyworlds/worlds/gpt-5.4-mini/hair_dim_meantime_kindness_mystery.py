#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py
=====================================================================

A standalone story world for a small mystery tale:
a child notices a hair-dim clue in a quiet house, chooses kindness in the
meantime, and the gentle choice helps solve the mystery.

The world keeps two tracked dimensions on entities:
- meters: physical state like dimness, hiddenness, foundness, warmth
- memes: emotional state like worry, kindness, trust, relief

The story is built from a live simulation, not a frozen paragraph.  A dim clue
creates tension, a kind act changes trust, and the ending image proves what was
found and how the room changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/hair_dim_meantime_kindness_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Room:
    id: str
    label: str
    dimness: int
    mystery: str
    hidden_place: str
    ending_image: str
    clues: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class KindnessMove:
    id: str
    label: str
    action: str
    effect: str
    trust_gain: int
    clue_reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_dimness(world: World) -> list[str]:
    out: list[str] = []
    if world.room.dimness >= THRESHOLD and ("dim_room", world.room.id) not in world.fired:
        world.fired.add(("dim_room", world.room.id))
        for e in world.characters():
            e.memes["worry"] += 1
        out.append("__dim__")
    return out


def _r_kindness_trust(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("trust", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] += 1
        out.append("__trust__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched") and world.facts.get("kind_move_used"):
        sig = ("reveal", world.room.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.room.clues.append("found")
            out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("dimness", "physical", _r_dimness),
    Rule("kindness_trust", "social", _r_kindness_trust),
    Rule("reveal", "mystery", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_move(move: KindnessMove) -> bool:
    return move.trust_gain >= 1


def valid_combos() -> list[tuple[str, str]]:
    return [(room_id, move_id) for room_id in ROOMS for move_id, mv in KIND_MOVES.items() if reasonable_move(mv)]


def mystery_note(room: Room) -> str:
    return f"The room was {room.mystery}, and the light was hair-dim."


def predict(world: World, move_id: str) -> dict:
    sim = world.copy()
    do_kindness(sim, sim.get("child"), KIND_MOVES[move_id], narrate=False)
    return {
        "trust": sim.get("child").memes["trust"],
        "revealed": bool(sim.room.clues),
    }


def set_scene(world: World, child: Entity, helper: Entity, room: Room) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} stepped into {room.label}. "
        f"{mystery_note(room)}"
    )
    world.say(
        f"The {room.label_word} felt quiet while they looked for the clue."
    )


def do_kindness(world: World, child: Entity, move: KindnessMove, narrate: bool = True) -> None:
    child.memes["kindness"] += 1
    world.facts["kind_move_used"] = True
    world.say(
        f'In the meantime, {child.id} chose to {move.action}, and {move.effect}.'
    )
    propagate(world, narrate=narrate)


def search(world: World, child: Entity, helper: Entity, room: Room) -> None:
    world.facts["searched"] = True
    world.say(
        f'Together they searched the {room.hidden_place}, where the clue had been hiding.'
    )
    if world.room.clues:
        world.say(
            f'Soon {child.id} noticed the small thing tucked there, just as if the room had been waiting to speak.'
        )


def explain(world: World, helper: Entity, child: Entity, move: KindnessMove) -> None:
    helper.memes["relief"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} smiled and thanked {child.id} for being kind first. "
        f"That gentle choice made the waiting easier."
    )
    world.say(
        f'When {move.clue_reveal} turned up, the mystery finally made sense.'
    )


def ending(world: World, child: Entity, helper: Entity, room: Room) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(room.ending_image)
    world.say(
        f"{child.id} and {helper.id} left with a warm feeling, because kindness had helped them find the answer."
    )


def tell(room: Room, move: KindnessMove, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="clue", label="the clue"))
    child.memes["kindness"] = 0.0
    child.memes["curiosity"] = 0.0
    helper.memes["calm"] = 1.0

    set_scene(world, child, helper, room)
    world.para()
    world.say(f"{child.id} wondered what the strange clue meant, but {helper.id} looked a little worried.")
    do_kindness(world, child, move)
    world.para()
    search(world, child, helper, room)
    explain(world, helper, child, move)
    world.para()
    ending(world, child, helper, room)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        move=move,
        room=room,
        outcome="revealed" if room.clues else "unrevealed",
    )
    return world


ROOMS = {
    "hall": Room(
        "hall", "the old hall", 2, "full of whispers", "hat shelf",
        "At last, the lamp flicked on, and the old hall looked gentle instead of strange.",
        clues=[],
    ),
    "library": Room(
        "library", "the little library", 2, "as quiet as a breath", "back reading nook",
        "At the end, the bookshelf stood steady and bright, with the clue found neatly beside it.",
        clues=[],
    ),
    "attic": Room(
        "attic", "the dusty attic", 3, "full of creaks and shadows", "wooden trunk",
        "By the end, the attic no longer felt spooky, because the hidden clue had been found.",
        clues=[],
    ),
}

KIND_MOVES = {
    "share_lantern": KindnessMove(
        "share_lantern", "share the lantern", "share the lantern", "the waiting felt softer", 2,
        "the small paper note in the trunk", {"kindness", "light"},
    ),
    "comfort_friend": KindnessMove(
        "comfort_friend", "comfort the friend", "sit beside the friend and speak gently",
        "the friend stopped trembling", 2, "the tiny key under the book", {"kindness"},
    ),
    "help_search": KindnessMove(
        "help_search", "help search", "look carefully without teasing",
        "the search became calmer", 2, "the folded map behind the vase", {"kindness", "search"},
    ),
}

CHILD_NAMES = ["Mina", "Leo", "Iris", "Noah", "Ada", "Eli", "Nia", "Theo"]
HELPER_NAMES = ["Jun", "Mara", "Seth", "Luna", "Owen", "Tess", "Milo", "Rae"]


@dataclass
@dataclass
class StoryParams:
    room: str
    move: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room, move, child, helper = f["room"], f["move"], f["child"], f["helper"]
    return [
        f'Write a small mystery story for a child that uses the words "hair-dim" and "meantime".',
        f"Tell a gentle mystery where {child.id} is in {room.label} and chooses to {move.action} in the meantime.",
        f"Write a story about kindness helping solve a clue in {room.label}, with a dim, quiet mood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, move, room = f["child"], f["helper"], f["move"], f["room"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer=f"It was set in {room.label}, a place that felt {room.mystery}. The dim light made the mystery feel bigger at first.",
        ),
        QAItem(
            question=f"What did {child.id} do in the meantime?",
            answer=f"{child.id} chose to {move.action}. That kindness made the waiting calmer and helped the two of them keep looking together.",
        ),
        QAItem(
            question="How did the mystery get solved?",
            answer=f"They searched the hiding place and found the clue that had been waiting there. Because {child.id} was kind first, {helper.id} felt safe enough to keep searching and notice it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else. A kind choice can make a scary moment feel safer.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little piece of information that helps you figure out what happened. Mysteries are often solved by finding clues and thinking carefully.",
        ),
        QAItem(
            question="What does meantime mean?",
            answer="Meantime means the time while something else is happening or before the next thing is ready. People say it when they are waiting and doing something else first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  room: {world.room.label} dimness={world.room.dimness} clues={world.room.clues}")
    lines.append(f"  fired rules: {sorted(sig[0] for sig in world.fired)}")
    return "\n".join(lines)


def explain_rejection(move: KindnessMove) -> str:
    return f"(No story: the move '{move.id}' is not reasonable enough for this mystery.)"


ASP_RULES = r"""
valid(Room, Move) :- room(Room), move(Move), trust_gain(Move, G), G >= 1.
dim_room(Room) :- room(Room), dimness(Room, D), D >= 1.
trust_up(Move) :- move(Move), trust_gain(Move, G), G >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("dimness", rid, room.dimness))
    for mid, move in KIND_MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("trust_gain", mid, move.trust_gain))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small kindness-and-mystery storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--move", choices=KIND_MOVES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.room and args.move and (args.room, args.move) not in combos:
        raise StoryError("That room and kindness move do not fit this mystery.")
    room = args.room or rng.choice(sorted(ROOMS))
    move = args.move or rng.choice(sorted(KIND_MOVES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room, move, child, child_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    move = KIND_MOVES[params.move]
    world = tell(room, move, params.child, params.child_gender, params.helper, params.helper_gender, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible room/move combos:")
        for room, move in asp_valid_combos():
            print(f"  {room:8} {move}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("hall", "share_lantern", "Mina", "girl", "Jun", "boy", "mother"),
            StoryParams("library", "help_search", "Leo", "boy", "Mara", "girl", "father"),
            StoryParams("attic", "comfort_friend", "Iris", "girl", "Seth", "boy", "mother"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
