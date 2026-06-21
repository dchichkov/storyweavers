#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/epee_timid_happy_ending_sharing_bravery_slice.py
=================================================================================

A tiny slice-of-life storyworld about two children sharing an epee for a gentle
practice duel, where a timid child finds bravery and both end up smiling.

Seed words: epee, timid
Features: Happy Ending, Sharing, Bravery
Style: Slice of Life
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"use": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "bravery": 0.0, "joy": 0.0, "share": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    shiny: str
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    parent_gender: str
    room: str
    toy: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.rooms = copy.deepcopy(self.rooms)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


ROOMS = {
    "living_room": "the living room",
    "game_room": "the game room",
    "hall": "the sunny hall",
}

TOYS = {
    "epee": Toy(id="epee", label="epee", phrase="an epee", shiny="shone like a little silver line"),
    "foam_epee": Toy(id="foam_epee", label="foam epee", phrase="a foam epee", shiny="looked soft and safe"),
}

NAMES = {
    "girl": ["Lina", "Mia", "Nora", "Ava"],
    "boy": ["Ben", "Theo", "Milo", "Noah"],
}

TRAITS = ["timid", "quiet", "careful", "gentle", "shy"]
PARENT_NAMES = {"mother": "Mom", "father": "Dad"}


def valid_combos() -> list[tuple[str, str]]:
    return [(room, toy) for room in ROOMS for toy in TOYS if TOYS[toy].safe]


def explain_rejection(room: str, toy: str) -> str:
    return "(No story: that combination is not reasonable for this gentle sharing tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life storyworld about sharing an epee, timidness, and bravery."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in NAMES[gender] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.room and args.toy and (args.room, args.toy) not in combos:
        raise StoryError(explain_rejection(args.room, args.toy))
    if not combos:
        raise StoryError("(No valid combinations available.)")
    room, toy = (args.room, args.toy) if args.room and args.toy else rng.choice(combos)
    c1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    c2_gender = args.child2_gender or ("boy" if c1_gender == "girl" else "girl")
    child1 = args.child1 or _pick_name(rng, c1_gender)
    child2 = args.child2 or _pick_name(rng, c2_gender, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        child1=child1,
        child1_gender=c1_gender,
        child2=child2,
        child2_gender=c2_gender,
        parent=parent,
        parent_gender=parent,
        room=room,
        toy=toy,
    )


def story_seed(params: StoryParams) -> dict:
    return {
        "shared": 0.0,
        "timid_child": params.child2,
        "brave_child": params.child1,
        "toy": params.toy,
    }


def tell(params: StoryParams) -> World:
    world = World()
    room = world.add_room(Room(id=params.room, label=ROOMS[params.room]))
    brave = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="brave", traits=["bright"]))
    timid = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="timid", traits=["timid"]))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent", label=PARENT_NAMES[params.parent]))
    toy = world.add(Entity(id=params.toy, kind="thing", type="toy", label=TOYS[params.toy].label, attrs={"phrase": TOYS[params.toy].phrase}))
    brave.memes["bravery"] = 1.0
    timid.memes["fear"] = 1.0
    world.facts.update(room=room, brave=brave, timid=timid, parent=parent, toy=toy)

    world.say(
        f"On a quiet afternoon, {brave.id} and {timid.id} sat in {room.label} with {toy.attrs['phrase']} on the rug."
    )
    world.say(
        f"{toy.label.capitalize()} {TOYS[params.toy].shiny}, and {brave.id} wanted to share it for a tiny pretend duel."
    )
    world.para()
    world.say(
        f'{timid.id} looked at it and said, "I want to try, but I am a little timid."'
    )
    brave.memes["share"] += 1
    world.say(
        f'{brave.id} smiled. "We can go slowly," {brave.id} said. "I will show you first, and then you can copy me."'
    )
    timid.memes["fear"] += 1
    timid.memes["bravery"] += 1
    timid.memes["joy"] += 1
    timid.meters["use"] += 1
    brave.meters["use"] += 1
    world.para()
    world.say(
        f"{brave.id} handed over the epee with both hands, and {timid.id} took it carefully."
    )
    world.say(
        f"At first {timid.id} was shaky, but {params.parent.capitalize() if False else PARENT_NAMES[params.parent]} watched from the doorway and nodded."
    )
    world.say(
        f'Soon {timid.id} made one brave little step, then another, and laughed, "I did it!"'
    )
    world.para()
    world.say(
        f"After that, they traded turns, took a careful bow, and put {toy.label} back together with their other toys."
    )
    world.say(
        f"{timid.id} still felt timid sometimes, but now {timid.pronoun()} knew bravery could be as small as asking for a turn."
    )
    world.say(
        f"{PARENT_NAMES[params.parent]} smiled at the two children in the warm room, where sharing had turned the whole game into a happy one."
    )
    world.facts["ending"] = "happy"
    world.facts["bravery"] = timid.memes["bravery"]
    world.facts["sharing"] = brave.memes["share"]
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    brave = f["brave"]
    timid = f["timid"]
    toy = f["toy"]
    room = f["room"]
    return [
        f'Write a slice-of-life story for a young child that includes "{toy.label}" and the word "timid".',
        f"Tell a warm story where {brave.id} shares {toy.label} with {timid.id} in {room.label}, and {timid.id} finds bravery.",
        f"Write a happy ending story about children sharing a toy and being brave together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    brave, timid, parent, toy, room = f["brave"], f["timid"], f["parent"], f["toy"], f["room"]
    return [
        QAItem(
            question="Who wanted to share the epee?",
            answer=f"{brave.id} wanted to share {toy.label} so the two children could play together."
        ),
        QAItem(
            question="Why was the other child unsure at first?",
            answer=f"{timid.id} felt timid at the start, so {timid.pronoun()} needed a gentle first step and a kind invitation."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{timid.id} found a little bravery, took a turn, and the children ended up smiling together in {room.label}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an epee?",
            answer="An epee is a fencing sword used for sport practice. In a children's story, it can be a pretend-play prop if everyone is careful."
        ),
        QAItem(
            question="What does timid mean?",
            answer="Timid means shy or nervous. A timid child may want to try something but need a gentle encouragement first."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something a little scary even when your heart feels nervous. It can be as small as trying a new turn or speaking up kindly."
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
        lines.append(f"  {e.id:10} {e.type:8} meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
toy(epee).
toy(foam_epee).
safe(epee).
safe(foam_epee).
valid(Room,Toy) :- room(Room), toy(Toy), safe(Toy).
"""

def asp_facts() -> str:
    import asp
    parts = []
    for rid in ROOMS:
        parts.append(asp.fact("room", rid))
    for tid in TOYS:
        parts.append(asp.fact("toy", tid))
        if TOYS[tid].safe:
            parts.append(asp.fact("safe", tid))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combo gates.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(child1="Lina", child1_gender="girl", child2="Noah", child2_gender="boy", parent="mother", parent_gender="mother", room="living_room", toy="epee"),
    StoryParams(child1="Theo", child1_gender="boy", child2="Mia", child2_gender="girl", parent="father", parent_gender="father", room="game_room", toy="foam_epee"),
]


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.toy not in TOYS:
        raise StoryError("Invalid story parameters.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible room/toy combos:\n")
        for room, toy in combos:
            print(f"  {room:12} {toy}")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} and {p.child2} in {p.room} with {p.toy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
