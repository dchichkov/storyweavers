#!/usr/bin/env python3
"""
storyworlds/worlds/perambulator.py
===================================

A standalone story world for a gentle mystery: a child's toy perambulator
disappears, and the child searches the house with growing suspense,
finding it after several attempts (repetition of the search pattern).
The story is state-driven via a simulated world where each room search
updates the child's worry and hope.

Domain: perambulator, Repetition, Suspense, Mystery style.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

ROOMS = ["kitchen", "living room", "bedroom", "hallway", "garden"]

# Emotion / state keys
WORRY = "worry"
HOPE = "hope"
JOY = "joy"
SURPRISE = "surprise"
FOUND = "found"


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""             # current room for the perambulator
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom"}
        male = {"boy", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    description: str = ""
    props: list[str] = field(default_factory=list)   # e.g. "table", "couch"


ROOM_DETAILS = {
    "kitchen": Room("kitchen", "the warm kitchen with a big wooden table",
                    ["table", "cupboard", "fridge"]),
    "living room": Room("living room", "the cozy living room with a soft couch",
                        ["couch", "rug", "bookshelf"]),
    "bedroom": Room("bedroom", "the child's bedroom with a bed and toys",
                    ["bed", "wardrobe", "toy box"]),
    "hallway": Room("hallway", "the long hallway with a mirror",
                    ["mirror", "door", "rug"]),
    "garden": Room("garden", "the sunny garden with flowers",
                   ["flower pot", "bench", "tree"]),
}


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    hiding_room: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    searched_rooms: list[str] = field(default_factory=list)

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.searched_rooms = list(self.searched_rooms)
        clone.paragraphs = [[]]
        return clone


# ------------------------------------------------------------------
# Causal rules
# ------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_search_miss(world: World) -> list[str]:
    """If child searched a room that is not the hiding room, increase worry."""
    out: list[str] = []
    child = world.entities.get("child")
    pram = world.entities.get("perambulator")
    if not child or not pram:
        return out
    if pram.meters["found"] >= THRESHOLD:
        return out
    # Check whether the last searched room was a miss
    if not world.searched_rooms:
        return out
    last = world.searched_rooms[-1]
    if last != pram.location:
        if (WORRY, "miss") not in world.fired and child.memes[WORRY] < 2:
            world.fired.add((WORRY, "miss"))
            child.memes[WORRY] += 1
            out.append("The house stayed quiet. No sign of the perambulator.")
    return out


def _r_search_hit(world: World) -> list[str]:
    """If child searched the hiding room, mark found and celebrate."""
    out: list[str] = []
    child = world.entities.get("child")
    pram = world.entities.get("perambulator")
    if not child or not pram:
        return out
    if pram.meters["found"] >= THRESHOLD:
        return out
    if not world.searched_rooms:
        return out
    last = world.searched_rooms[-1]
    if last == pram.location:
        pram.meters["found"] = THRESHOLD
        child.memes[WORRY] = 0.0
        child.memes[JOY] = THRESHOLD
        out.append("There it was! The perambulator had been hiding in plain sight all along.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="search_miss", tag="emotion", apply=_r_search_miss),
    Rule(name="search_hit", tag="physical", apply=_r_search_hit),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ------------------------------------------------------------------
# Storytelling verbs
# ------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "")
    desc = f"little {trait} {child.type}".strip()
    world.say(f"{child.id} was a {desc} who loved {child.pronoun('possessive')} toy perambulator.")


def loves_perambulator(world: World, child: Entity, pram: Entity) -> None:
    world.say(f"{child.pronoun().capitalize()} pushed {pram.it()} through every room, "
              f"whispering adventures to {pram.it()}.")


def discover_missing(world: World, child: Entity, parent: Entity) -> None:
    world.say("One afternoon, the perambulator was nowhere to be found.")
    world.say(f"\"{child.id}?\" called {child.pronoun('possessive')} {parent.label_word}. "
              f"\"Where did you leave your little carriage?\"")
    world.para()
    world.say(f"{child.id} felt a knot of worry. Where could it be?")


def search_room(world: World, child: Entity, parent: Entity, room: str) -> None:
    detail = ROOM_DETAILS[room]
    world.say(f"{child.id} and {child.pronoun('possessive')} {parent.label_word} "
              f"went to {detail.description}.")
    world.searched_rooms.append(room)
    propagate(world)
    if world.entities["perambulator"].meters["found"] < THRESHOLD:
        # Add a bit of repetition: similar line but with slight variation
        world.say(f"\"Not here,\" {child.id} said, {child.pronoun('possessive')} glance sweeping the room.")
        world.para()
    else:
        world.para()
        world.say(f"{child.id} grabbed {child.pronoun('possessive')} perambulator and hugged it tight.")


def tell(child_name: str, gender: str, parent_type: str, hiding_room: str) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=gender,
        traits=["little", "curious"],
        label=child_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    pram = world.add(Entity(
        id="perambulator",
        kind="thing",
        type="perambulator",
        label="toy perambulator",
        phrase="a shiny red toy perambulator with a tiny handle",
        owner=child.id,
        caretaker=parent.id,
        location=hiding_room,
    ))

    # Act 1: setup
    introduce(world, child)
    loves_perambulator(world, child, pram)

    # Act 2: disappearance
    world.para()
    discover_missing(world, child, parent)

    # Act 3: search (repetition + suspense)
    # Determine search order: all rooms, with hiding room not first (to force suspense)
    all_rooms = list(ROOMS)
    random.shuffle(all_rooms)
    # Ensure hiding_room is not first (but if it is, swap with second)
    if all_rooms[0] == hiding_room:
        if len(all_rooms) > 1:
            all_rooms[0], all_rooms[1] = all_rooms[1], all_rooms[0]
    for room in all_rooms:
        world.para()
        search_room(world, child, parent, room)
        if pram.meters["found"] >= THRESHOLD:
            break

    # Record facts for QA
    world.facts.update(
        child=child,
        parent=parent,
        pram=pram,
        hiding_room=hiding_room,
        found=pram.meters["found"] >= THRESHOLD,
    )
    return world


# ------------------------------------------------------------------
# Registries (minimal -- only one world type)
# ------------------------------------------------------------------
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "patient", "brave", "gentle", "cheerful", "stubborn"]


# ------------------------------------------------------------------
# QA helpers
# ------------------------------------------------------------------
KNOWLEDGE = {
    "perambulator": [
        ("What is a perambulator?",
         "A perambulator is another word for a baby carriage or a toy stroller. "
         "Children push it around and pretend their toys are going for a walk.")
    ],
    "mystery": [
        ("What does it mean when something is a mystery?",
         "A mystery is something you do not know the answer to yet. "
         "It makes you curious and you have to look for clues.")
    ],
    "search": [
        ("Why do we look in each room when something is lost?",
         "When something is lost, we check one room at a time so we do not miss "
         "any hiding spot. It helps us find what we are looking for.")
    ],
}

KNOWLEDGE_ORDER = ["perambulator", "mystery", "search"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes '
        f'the word "perambulator" and a search through different rooms.',
        f'Tell a gentle suspense story where {child.id} loses a favorite toy '
        f'perambulator and looks for it with {child.pronoun("possessive")} '
        f'{f["parent"].label_word}.',
        f'Write a story that repeats the phrase "Not here" as the child searches '
        f'room after room for the missing perambulator.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent_lbl = f["parent"].label_word
    pram = f["pram"]
    hiding = f["hiding_room"]
    found = f["found"]
    sub, pos = child.pronoun("subject"), child.pronoun("possessive")
    trait = next((t for t in child.traits if t != "little"), child.type)

    qa = [
        QAItem(
            question=f"What toy did {trait} {child.id} lose in the story?",
            answer=f"{pos.capitalize()} shiny red toy perambulator. {sub} loved pushing it around the house."
        ),
        QAItem(
            question=f"Who helped {child.id} look for the perambulator?",
            answer=f"{parent_lbl.capitalize()} helped {sub} search every room."
        ),
        QAItem(
            question=f"How did {trait} {child.id} feel as {sub} looked and did not find the perambulator?",
            answer=f"{pos.capitalize()} worry grew with each room that did not have the perambulator. "
                   f"The house felt very quiet."
        ),
    ]
    if found:
        qa.append(QAItem(
            question=f"Where was the perambulator hiding at the end?",
            answer=f"It was hiding in {hiding}. {child.id} had looked there before but missed it!"
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"perambulator", "mystery", "search"}  # always present
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q=q, a=a) for q, a in KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if hasattr(e, 'location') and e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  searched rooms: {world.searched_rooms}")
    lines.append(f"  fired rules: {sorted(set((n, t) for n, t in world.fired))}")
    return "\n".join(lines)


# ------------------------------------------------------------------
# ASP twin (inline)
# ------------------------------------------------------------------
ASP_RULES = r"""
room(R) :- hide_room(R).
possible_story(R) :- room(R).
found_in(R) :- hide_room(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    # Hiding room is chosen randomly; we emit all possible as facts,
    # then the rule selects one per model.
    for r in ROOMS:
        lines.append(asp.fact("possible_hide", r))
    lines.append("% One hiding room per model (choice)")
    lines.append("{hide_room(R)} = 1 :- room(R).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show found_in/1."))
    return sorted(set(asp.atoms(model, "found_in")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    expected = {(r,) for r in ROOMS}
    if set(stories) == expected:
        print(f"OK: clingo matches {len(stories)} possible hiding rooms.")
        return 0
    print("MISMATCH")
    return 1


# ------------------------------------------------------------------
# Standard interface
# ------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a lost perambulator, repetition, suspense, mystery.")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--hiding-room", choices=ROOMS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    hiding = args.hiding_room or rng.choice(ROOMS)
    return StoryParams(
        child_name=name,
        child_gender=gender,
        parent_type=parent,
        hiding_room=hiding,
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    # Use a local RNG for room order inside tell; we reinitialize per story.
    # We'll pass the seed via the world's random? Simplest: use random.seed in tell.
    # We'll rely on global random state inside tell, but we set seed before call.
    random.seed(params.seed)
    world = tell(params.child_name, params.child_gender,
                 params.parent_type, params.hiding_room)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show found_in/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"Possible hiding rooms ({len(stories)}):")
        for (r,) in stories:
            print(f"  {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        # Generate one story per possible room
        for room in ROOMS:
            p = StoryParams(
                child_name=random.choice(GIRL_NAMES),
                child_gender="girl",
                parent_type="mother",
                hiding_room=room,
                seed=0,
            )
            samples.append(generate(p))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: perambulator hidden in {p.hiding_room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
