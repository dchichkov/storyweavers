#!/usr/bin/env python3
"""
A small storyworld for a gentle ghost-story about dream junk and dialogue.

Premise:
A child finds a box of junk in an old room and hears a ghost speaking from
inside a dream-like nook. The ghost wants its lost keepsake returned. The child
must sort the junk, understand the ghost's clues, and decide what to keep.

World model:
- Physical meters: dust, creak, glow, tidy, ruin
- Emotional memes: fear, curiosity, relief, trust

The prose is driven by state changes:
- rummaging through junk raises dust and curiosity
- speaking with the ghost lowers fear if the child answers kindly
- finding the right object lowers ruin and raises relief/trust
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.type


@dataclass
class Room:
    name: str
    mood: str
    has_dream_corner: bool = False
    has_junk_pile: bool = False


@dataclass
class StoryParams:
    room: str
    child_name: str
    ghost_name: str
    seed: Optional[int] = None


ROOMS = {
    "attic": Room(name="the attic", mood="old and sleepy", has_dream_corner=True, has_junk_pile=True),
    "basement": Room(name="the basement", mood="cold and hollow", has_dream_corner=False, has_junk_pile=True),
    "shed": Room(name="the shed", mood="quiet and dusty", has_dream_corner=True, has_junk_pile=True),
}

CHILD_NAMES = ["Mina", "Nora", "Eli", "Theo", "Lena", "Ivy"]
GHOST_NAMES = ["Mister Wisp", "Mrs. Pale", "Old Whisper", "Quiet Bell"]
JUNK_KINDS = [
    ("button tin", "a tin full of buttons"),
    ("broken key", "a broken brass key"),
    ("paper stars", "a pile of paper stars"),
    ("tiny bell", "a tiny cracked bell"),
]
DREAM_GIFTS = {
    "button tin": "dreams of a coat with shiny buttons",
    "broken key": "dreams of a door that should open again",
    "paper stars": "dreams of a sky made for wishing",
    "tiny bell": "dreams of a lullaby that was never finished",
}


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        out: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    out.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            out.append(" ".join(current))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


def _inc(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _dec(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = max(0.0, e.meters.get(key, 0.0) - amt)


def setup_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(id=params.child_name, kind="character", type="child", label=params.child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    junk_id, junk_phrase = random.choice(JUNK_KINDS)
    junk = world.add(Entity(id="junk", type="junk", label=junk_id, phrase=junk_phrase))
    dream = world.add(Entity(id="dream", type="dream", label="dream", phrase="a soft dream"))
    world.facts.update(child=child, ghost=ghost, junk=junk, dream=dream)
    return world


def _room_opening(world: World) -> None:
    world.say(f"{world.room.name} felt {world.room.mood}.")
    if world.room.has_junk_pile:
        world.say("A pile of junk waited in one corner, still as a nest.")
    if world.room.has_dream_corner:
        world.say("Near the back wall, a little dream-corner glimmered like moonlight on dust.")


def _introduce_child(world: World, child: Entity) -> None:
    _inc(child, "curiosity")
    world.say(f"{child.id} went in with slow steps and whispered, \"Hello?\"")


def _ghost_answers(world: World, ghost: Entity) -> None:
    _inc(ghost, "glow")
    world.say(f"A small voice came from the dark: \"I am {ghost.label}. Please do not be afraid.\"")


def _dialogue_turn(world: World, child: Entity, ghost: Entity) -> None:
    _inc(child, "fear")
    _inc(child, "curiosity")
    world.say(f"\"Why are you hiding in the junk?\" {child.id} asked.")
    world.say(f"\"I lost something in a dream,\" {ghost.label} said. \"It fell into the junk pile.\"")
    world.say(f"\"What did it look like?\" {child.id} asked.")
    world.say(f"\"It was small, dear, and it carried my last gentle dream,\" said {ghost.label}.")


def _search_junk(world: World, child: Entity, ghost: Entity, junk: Entity) -> None:
    _inc(child, "dust")
    _inc(child, "curiosity", 1.0)
    _inc(junk, "ruin", 1.0)
    world.say(f"{child.id} lifted the junk one piece at a time.")
    clue = random.choice(list(DREAM_GIFTS.items()))
    world.facts["clue"] = clue
    world.say(f"Under the junk, there was a {clue[0]}.")
    world.say(f"\"That looks like it belongs to your dream,\" {child.id} said.")


def _resolve(world: World, child: Entity, ghost: Entity) -> None:
    _dec(child, "fear", 1.0)
    _inc(child, "trust", 1.0)
    _inc(child, "relief", 1.0)
    _inc(ghost, "glow", 1.0)
    world.say(f"\"Yes,\" said {ghost.label}. \"You found it.\"")
    world.say(f"\"Then you can have it back,\" {child.id} said, holding the little thing out with both hands.")
    world.say(f"The room grew quieter, but not lonely. The ghost smiled like a candle that had found its flame again.")


def _ending(world: World, child: Entity, ghost: Entity, junk: Entity) -> None:
    _dec(junk, "ruin", 1.0)
    _inc(junk, "tidy", 1.0)
    world.say(f"{child.id} left the junk pile neater than before.")
    world.say(f"In the dream-corner, {ghost.label} faded into a soft, safe hush, and the room felt warm enough to sleep in.")


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.get(params.child_name)
    ghost = world.get("ghost")
    junk = world.get("junk")

    _room_opening(world)
    world.say("")
    _introduce_child(world, child)
    _ghost_answers(world, ghost)
    _dialogue_turn(world, child, ghost)
    world.say("")
    _search_junk(world, child, ghost, junk)
    _resolve(world, child, ghost)
    world.say("")
    _ending(world, child, ghost, junk)

    world.facts.update(
        child=child,
        ghost=ghost,
        junk=junk,
        resolved=True,
        room=params.room,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    room = world.facts["room"]
    return [
        'Write a short ghost story for a young child about a dream and some junk.',
        f'Write a gentle dialogue story where {child.id} finds a ghost in {room} and helps it.',
        f'Write a child-friendly haunted-room story with talk, junk, and a dream-like clue for {ghost.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    junk = world.facts["junk"]
    room = world.facts["room"]
    clue = world.facts.get("clue", ("unknown", "a clue"))
    return [
        QAItem(
            question=f"Where did {child.id} find {ghost.label}?",
            answer=f"{child.id} found {ghost.label} in {ROOMS[room].name}, near the junk pile.",
        ),
        QAItem(
            question=f"What was {ghost.label} looking for?",
            answer=f"{ghost.label} was looking for a small thing from a dream that had fallen into the junk.",
        ),
        QAItem(
            question=f"What did {child.id} find under the junk?",
            answer=f"{child.id} found a {clue[0]} under the junk, and that helped the ghost finish its search.",
        ),
        QAItem(
            question=f"How did the story end for {ghost.label}?",
            answer=f"{ghost.label} grew calm and faded into a soft hush after {child.id} helped return what was lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is junk?",
            answer="Junk is a collection of old, unwanted, or broken things that people may keep in a box or pile.",
        ),
        QAItem(
            question="What is a dream?",
            answer="A dream is a story the mind makes during sleep, with strange and vivid pictures.",
        ),
        QAItem(
            question="Why do ghosts talk in stories?",
            answer="Ghosts talk in stories so they can share a mystery, ask for help, or give a spooky clue.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


@dataclass
class StoryParamsRegistry:
    rooms: list[str] = field(default_factory=lambda: list(ROOMS))
    child_names: list[str] = field(default_factory=lambda: CHILD_NAMES)
    ghost_names: list[str] = field(default_factory=lambda: GHOST_NAMES)


REGISTRY = StoryParamsRegistry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with dream, junk, and dialogue.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child-name", dest="child_name", choices=CHILD_NAMES)
    ap.add_argument("--ghost-name", dest="ghost_name", choices=GHOST_NAMES)
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
    room = args.room or rng.choice(list(ROOMS))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(room=room, child_name=child_name, ghost_name=ghost_name)


ASP_RULES = r"""
room(attic). room(basement). room(shed).
child_name(mina). child_name(nora). child_name(eli). child_name(theo). child_name(lena). child_name(ivy).
ghost_name("Mister Wisp"). ghost_name("Mrs. Pale"). ghost_name("Old Whisper"). ghost_name("Quiet Bell").

valid(Room, Child, Ghost) :- room(Room), child_name(Child), ghost_name(Ghost).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for c in CHILD_NAMES:
        lines.append(asp.fact("child_name", c.lower()))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost_name", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    combos = set(asp.atoms(model, "valid"))
    expected = {(r, c.lower(), g) for r in ROOMS for c in CHILD_NAMES for g in GHOST_NAMES}
    if combos == expected:
        print(f"OK: ASP matches Python registry ({len(combos)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(combos - expected))
    print("only in python:", sorted(expected - combos))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for room in ROOMS:
            params = StoryParams(room=room, child_name=CHILD_NAMES[0], ghost_name=GHOST_NAMES[0], seed=base_seed)
            samples.append(generate(params))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
