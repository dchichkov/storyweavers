#!/usr/bin/env python3
"""
storyworlds/worlds/urinate_journal_teamwork_friendship_ghost_story.py
======================================================================

A small storyworld about a spooky-but-gentle ghost tale.

Seed tale used to shape the simulation:
---
A child keeps a journal about a friendly ghost in the attic. One dark evening,
the child gets scared, urinates in their pajamas, and feels embarrassed. A best
friend notices, helps with teamwork, and together they clean up, write in the
journal, and learn the ghost was only trying to leave a kind message.

This world models:
- fear and comfort around a ghostly setting
- a wet accident caused by fear
- a journal that can record clues and feelings
- teamwork and friendship as the resolution
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


THRESHOLD = 1.0


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    spooky: bool = False
    has_attic_stairs: bool = False
    has_bathroom: bool = False


@dataclass
class Ghost:
    id: str
    label: str
    kind: str
    gentle: bool = True
    clue: str = "hello"
    friendly: bool = True


@dataclass
class StoryParams:
    room: str
    ghost: str
    journal: str
    name: str
    friend_name: str
    gender: str
    seed: Optional[int] = None


ROOMS = {
    "attic": Room(name="the attic", spooky=True, has_attic_stairs=True),
    "hallway": Room(name="the hallway", spooky=True),
    "bedroom": Room(name="the bedroom", spooky=False),
    "garden": Room(name="the moonlit garden", spooky=True),
}

GHOSTS = {
    "lantern": Ghost(id="lantern", label="a lantern ghost", kind="ghost", clue="a warm light"),
    "pillow": Ghost(id="pillow", label="a pillow ghost", kind="ghost", clue="be kind"),
    "bell": Ghost(id="bell", label="a little bell ghost", kind="ghost", clue="listen closely"),
}

JOURNALS = {
    "blue": "a blue journal with a star on the cover",
    "red": "a red journal with a moon on the cover",
    "green": "a green journal tied with string",
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Noah", "Finn", "Eli", "Max", "Leo"]
FRIEND_NAMES = ["Pip", "June", "Bo", "Sadie", "Owen", "Rae"]


class World:
    def __init__(self, room: Room, ghost: Ghost, journal_label: str) -> None:
        self.room = room
        self.ghost = ghost
        self.journal_label = journal_label
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.room, self.ghost, self.journal_label)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _say_bedtime(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} kept {child.pronoun('possessive')} {world.journal_label} by the pillow and wrote down every ghostly clue."
    )


def _feel_fear(world: World, child: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    world.say(
        f"That night, the shadows in {world.room.name} felt taller, and {child.id}'s stomach fluttered with fear."
    )


def _urinate(world: World, child: Entity) -> None:
    child.meters["urine"] = child.meters.get("urine", 0.0) + 1
    child.memes["embarrassment"] = child.memes.get("embarrassment", 0.0) + 1
    world.say(
        f"Before {child.id} could reach the bathroom, {child.pronoun()} urinated in {child.pronoun('possessive')} pajamas."
    )


def _teamwork(world: World, child: Entity, friend: Entity) -> None:
    if child.meters.get("urine", 0.0) < THRESHOLD:
        return
    sig = ("teamwork", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["comfort"] = child.memes.get("comfort", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{friend.id} hurried over with a towel, and together they cleaned up with careful teamwork."
    )


def _journal_clue(world: World, child: Entity, friend: Entity) -> None:
    sig = ("journal", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.say(
        f"Then {child.id} opened the {world.journal_label} and wrote that the ghost had left {world.ghost.clue} behind."
    )


def _ghost_message(world: World, child: Entity) -> None:
    sig = ("ghost", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        f"When they looked again, the ghost was not frightening at all; it was only trying to leave a kind message."
    )


def tell(room: Room, ghost: Ghost, journal_label: str, name: str, friend_name: str, gender: str) -> World:
    world = World(room, ghost, journal_label)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label=friend_name))
    journal = world.add(Entity(id="journal", type="journal", label=journal_label, owner=child.id))

    world.say(
        f"{child.id} loved the {journal.label} because it held all the stories about {ghost.label}."
    )
    world.say(
        f"{child.id} and {friend.id} made a promise to be brave together whenever {world.room.name} felt spooky."
    )
    world.para()

    _say_bedtime(world, child)
    _feel_fear(world, child)
    _urinate(world, child)
    world.say(
        f"{friend.id} did not laugh. {friend.id} only squeezed {child.pronoun('possessive')} hand and stayed close."
    )
    _teamwork(world, child, friend)
    _ghost_message(world, child)
    _journal_clue(world, child, friend)
    world.para()
    world.say(
        f"By morning, {child.id} had a clean bed, a fuller journal, and a truer idea of the ghost: scary-looking, but kind."
    )

    world.facts.update(
        child=child,
        friend=friend,
        journal=journal,
        ghost=ghost,
        room=room,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    ghost = f["ghost"]
    return [
        f'Write a gentle ghost story for a young child that includes a journal, teamwork, and the word "{ghost.id}".',
        f"Tell a spooky-but-kind story where {child.id} gets scared, needs help, and {friend.id} shows friendship and teamwork.",
        f"Write a short story about a child who keeps a journal about {ghost.label} and learns the ghost is not mean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    ghost = f["ghost"]
    room = f["room"]
    return [
        QAItem(
            question=f"What was {child.id} writing in before the spooky night in {room.name}?",
            answer=f"{child.id} was writing in {child.pronoun('possessive')} {world_name(world)} journal about {ghost.label}.",
        ),
        QAItem(
            question=f"Who showed friendship when {child.id} felt embarrassed after the accident?",
            answer=f"{friend.id} showed friendship by staying close, not laughing, and helping with teamwork.",
        ),
        QAItem(
            question=f"What happened to {child.id} because {child.id} got so scared?",
            answer=f"{child.id} urinated in {child.pronoun('possessive')} pajamas before reaching the bathroom.",
        ),
        QAItem(
            question=f"What did the ghost turn out to be like at the end?",
            answer=f"The ghost turned out to be gentle and kind, not scary at all.",
        ),
    ]


def world_name(world: World) -> str:
    return world.journal_label.replace("a ", "").replace("an ", "")


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a journal?",
            answer="A journal is a book where someone can write thoughts, stories, or notes to remember later.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help one another reach the same goal.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, being kind to them, and helping them when they need it.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky?",
            answer="A ghost story can feel spooky because it may have shadows, strange sounds, or surprises in the dark.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  room: {world.room.name}")
    lines.append(f"  ghost: {world.ghost.label}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(room: Room, ghost: Ghost) -> str:
    return f"(No story: the room {room.name} and ghost {ghost.label} do not make a reasonable ghost tale.)"


def explain_gender(gender: str) -> str:
    return f"(No story: unsupported gender option {gender!r}.)"


SETTINGS = ROOMS
GHOST_REGISTRY = GHOSTS
JOURNAL_REGISTRY = JOURNALS


@dataclass
class StorySeed:
    room: str
    ghost: str
    journal: str
    name: str
    friend_name: str
    gender: str
    seed: Optional[int] = None


ASP_RULES = r"""
room(R) :- room_name(R).
ghost(G) :- ghost_name(G).
journal(J) :- journal_name(J).

spooky_story(R,G,J) :- room(R), ghost(G), journal(J).
valid_story(R,G,J,Gender) :- spooky_story(R,G,J), gender_ok(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room_name", rid))
        if room.spooky:
            lines.append(asp.fact("spooky", rid))
        if room.has_attic_stairs:
            lines.append(asp.fact("stairs", rid))
        if room.has_bathroom:
            lines.append(asp.fact("bathroom", rid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost_name", gid))
    for jid in JOURNALS:
        lines.append(asp.fact("journal_name", jid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender_ok", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(r, g, j, gender) for r in ROOMS for g in GHOSTS for j in JOURNALS for gender in ["girl", "boy"]}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python registry space ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python registry space.")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with journaling, teamwork, and friendship.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--journal", choices=JOURNALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StorySeed:
    room = args.room or rng.choice(list(ROOMS))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    journal = args.journal or rng.choice(list(JOURNALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.gender))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StorySeed(room=room, ghost=ghost, journal=journal, name=name, friend_name=friend_name, gender=gender)


def generate(params: StorySeed) -> StorySample:
    world = tell(ROOMS[params.room], GHOSTS[params.ghost], JOURNALS[params.journal], params.name, params.friend_name, params.gender)
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
    StorySeed(room="attic", ghost="lantern", journal="blue", name="Mina", friend_name="Pip", gender="girl"),
    StorySeed(room="hallway", ghost="bell", journal="red", name="Theo", friend_name="June", gender="boy"),
    StorySeed(room="garden", ghost="pillow", journal="green", name="Ivy", friend_name="Rae", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all and sample.params:
            p = sample.params
            header = f"### {p.name}: {p.ghost} in {p.room} (journal: {p.journal})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
