#!/usr/bin/env python3
"""
storyworlds/worlds/awake_sound_effects_suspense_heartwarming.py
===============================================================

A small storyworld about waking up to strange sound effects, following the
noisy clues with a little suspense, and ending in a warm, comforting reveal.

The seed premise:
- Someone wakes up.
- The house or room makes small, mysterious sounds.
- The listener feels suspense and goes to check.
- The mystery turns out to be kind and heartwarming.

The world is deliberately tiny and constraint-checked:
- A sound source must be plausibly audible from the room.
- The source can be mysterious at first.
- The ending reveal must be safe and caring, not scary.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    cozy: bool = True
    dark: bool = True
    has_window: bool = True


@dataclass
class SoundSource:
    id: str
    label: str
    phrase: str
    sound: str
    source_kind: str
    clue: str
    reveal: str
    safe: bool = True
    warm: bool = True
    location: str = ""


@dataclass
class StoryParams:
    room: str
    source: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


ROOMS = {
    "bedroom": Room("the bedroom", cozy=True, dark=True, has_window=True),
    "hallway": Room("the hallway", cozy=True, dark=True, has_window=False),
    "kitchen": Room("the kitchen", cozy=True, dark=False, has_window=True),
    "cabin": Room("the little cabin", cozy=True, dark=True, has_window=True),
}

SOURCES = {
    "cat": SoundSource(
        id="cat",
        label="a sleepy cat",
        phrase="a sleepy cat curled on a cushion",
        sound="mrrp",
        source_kind="pet",
        clue="soft paws tap-tapping on the floor",
        reveal="the cat had been looking for a warm lap",
        safe=True,
        warm=True,
        location="near the bed",
    ),
    "kettle": SoundSource(
        id="kettle",
        label="the kettle",
        phrase="a kettle on the stove",
        sound="whistle",
        source_kind="appliance",
        clue="a tiny steam hiss from the kitchen",
        reveal="the kettle was singing because the grown-up was making warm milk",
        safe=True,
        warm=True,
        location="in the kitchen",
    ),
    "rain": SoundSource(
        id="rain",
        label="the rain",
        phrase="rain at the window",
        sound="tap-tap-tap",
        source_kind="weather",
        clue="little drops ticked against the glass",
        reveal="rain was dancing softly on the window",
        safe=True,
        warm=True,
        location="outside",
    ),
    "toy": SoundSource(
        id="toy",
        label="a toy",
        phrase="a tiny toy with a loose button",
        sound="beep-beep",
        source_kind="toy",
        clue="a blinking light flashed from under the blanket",
        reveal="the toy had turned itself on and needed a hug from the child",
        safe=True,
        warm=True,
        location="by the pillow",
    ),
    "windchime": SoundSource(
        id="windchime",
        label="wind chimes",
        phrase="wind chimes by the porch",
        sound="ting-ting",
        source_kind="outdoor",
        clue="a silver ring drifted through the open window",
        reveal="the wind chimes were singing in the night breeze",
        safe=True,
        warm=True,
        location="outside the room",
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Max", "Noah", "Eli"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "careful", "kind"]


def audibility(room: Room, source: SoundSource) -> bool:
    if source.id == "kettle":
        return room.name in {"the kitchen", "the hallway", "the little cabin"}
    if source.id == "rain":
        return room.has_window
    if source.id == "windchime":
        return room.has_window
    return True


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for room_id, room in ROOMS.items():
        for src_id, src in SOURCES.items():
            if audibility(room, src):
                out.append((room_id, src_id))
    return out


def explain_rejection(room_id: str, source_id: str) -> str:
    room = ROOMS[room_id]
    src = SOURCES[source_id]
    return (
        f"(No story: {src.label} would not plausibly be heard from {room.name}. "
        f"Choose a different room or a different sound source.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: waking up to mysterious sound effects, suspense, and a heartwarming reveal."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.room and args.source and not audibility(ROOMS[args.room], SOURCES[args.source]):
        raise StoryError(explain_rejection(args.room, args.source))
    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.source is None or c[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room_id, source_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room_id, source=source_id, name=name, gender=gender, parent=parent, trait=trait)


def _setup_world(params: StoryParams) -> World:
    world = World(copy.deepcopy(ROOMS[params.room]))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    src = SOURCES[params.source]
    source = world.add(Entity(
        id=src.id,
        type=src.source_kind,
        label=src.label,
        phrase=src.phrase,
        location=src.location,
    ))
    world.facts.update(child=child, parent=parent, source=source, source_cfg=src, params=params)
    return world


def _wake(world: World) -> None:
    child = world.facts["child"]
    child.memes["sleepiness"] = max(0.0, child.memes.get("sleepiness", 0.0) - 1.0)
    child.memes["awake"] = child.memes.get("awake", 0.0) + 1.0
    world.say(f"{child.id} was asleep in {world.room.name} when a small sound tickled the dark.")


def _listen(world: World) -> None:
    child = world.facts["child"]
    src: SoundSource = world.facts["source_cfg"]
    child.memes["suspense"] = child.memes.get("suspense", 0.0) + 1.0
    world.say(f"{child.id} held still and listened. {src.sound}, {src.sound} went the night, soft and tiny.")
    world.say(f"It sounded close enough to matter, but far enough to make {child.id} wonder.")


def _ask(parent: Entity, child: Entity, src: SoundSource) -> str:
    if src.id == "cat":
        return f'"Did you hear that little {src.label.split()[-1]} sound?" {parent.pronoun("subject").capitalize()} whispered.'
    if src.id == "kettle":
        return f'"Do you hear the {src.sound} from the kitchen?" {parent.pronoun("subject").capitalize()} asked softly.'
    if src.id == "rain":
        return f'"Hear the {src.sound} on the window?" {parent.pronoun("subject").capitalize()} murmured.'
    if src.id == "toy":
        return f'"Was that your toy?" {parent.pronoun("subject").capitalize()} asked, smiling in the dark.'
    return f'"Do you hear the {src.sound} outside?" {parent.pronoun("subject").capitalize()} said gently.'


def _follow_clue(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    src: SoundSource = world.facts["source_cfg"]
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    world.say(f"{child.id} slid out of bed and followed the clue: {src.clue}.")
    world.say(_ask(parent, child, src))


def _reveal(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    src: SoundSource = world.facts["source_cfg"]
    child.memes["suspense"] = 0.0
    child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1.0
    world.say(f"At last, {child.id} found out that {src.reveal}.")
    if src.id == "cat":
        world.say(f"The sleepy cat purred, and {child.id} scooped {src.label} up for a cozy cuddle.")
    elif src.id == "kettle":
        world.say(f"The warm milk steamed, and {child.id} smiled at the sweet smell in the kitchen.")
    elif src.id == "rain":
        world.say(f"The rain made the room feel like a lullaby, and both of them watched the silver window.")
    elif src.id == "toy":
        world.say(f"{child.id} tucked the toy in close, and its little beeps became a sleepy song.")
    else:
        world.say(f"The wind chimes sang once more, and {child.id} listened until the room felt calm again.")
    world.say(f"{parent.id if False else parent.label} gave {child.id} a warm hug, and the night felt safe again.")


def tell(room: Room, source: SoundSource, name: str, gender: str, trait: str, parent_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    src = world.add(Entity(id=source.id, type=source.source_kind, label=source.label, phrase=source.phrase, location=source.location))
    world.facts.update(child=child, parent=parent, source=src, source_cfg=source)
    _wake(world)
    world.para()
    _listen(world)
    _follow_clue(world)
    world.para()
    _reveal(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["child"]
    src: SoundSource = world.facts["source_cfg"]
    return [
        f'Write a short heartwarming story for a young child about waking up to the sound "{src.sound}" and finding out what made it.',
        f"Tell a suspenseful-but-gentle bedtime story where {p.id} hears a strange noise, follows the clue, and learns it is something safe and loving.",
        f'Write a cozy story that includes the sound effect "{src.sound}" and ends with a warm reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["child"]
    parent = world.facts["parent"]
    src: SoundSource = world.facts["source_cfg"]
    return [
        QAItem(
            question=f"What woke {p.id} up?",
            answer=f"{p.id} woke up to a small mysterious sound that turned out to be {src.label}.",
        ),
        QAItem(
            question=f"How did {p.id} feel while listening in the dark?",
            answer=f"{p.id} felt suspense at first, because the sound was soft and strange, but then {p.id} grew brave and followed the clue.",
        ),
        QAItem(
            question=f"What made the ending heartwarming?",
            answer=f"The ending was heartwarming because the sound was safe and kind, and {parent.label} gave {p.id} a warm hug after the reveal.",
        ),
        QAItem(
            question=f"What sound effect was heard in the story?",
            answer=f'The story used the sound effect "{src.sound}".',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    src: SoundSource = world.facts["source_cfg"]
    if src.id == "cat":
        return [QAItem(question="Why do cats sometimes make soft sounds at night?", answer="Cats may make soft sounds when they are looking for comfort, attention, or a cozy place to rest.")]
    if src.id == "kettle":
        return [QAItem(question="What does a kettle do when it is ready?", answer="A kettle can whistle or sing when the water is hot and ready.")]
    if src.id == "rain":
        return [QAItem(question="What sound does rain make on a window?", answer="Rain can make tapping or drumming sounds when it hits a window.")]
    if src.id == "toy":
        return [QAItem(question="Why might a toy beep at night?", answer="Some toys have batteries or buttons, so they can make little beeping sounds if they turn on.")]
    return [QAItem(question="What do wind chimes sound like?", answer="Wind chimes make light ringing sounds when the wind moves them.")]


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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="bedroom", source="cat", name="Lily", gender="girl", parent="mother", trait="curious"),
    StoryParams(room="kitchen", source="kettle", name="Leo", gender="boy", parent="father", trait="sleepy"),
    StoryParams(room="bedroom", source="rain", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(room="bedroom", source="toy", name="Finn", gender="boy", parent="father", trait="brave"),
    StoryParams(room="cabin", source="windchime", name="Nora", gender="girl", parent="mother", trait="kind"),
]


ASP_RULES = r"""
room(R) :- room_fact(R).
source(S) :- source_fact(S).
can_hear(R,S) :- room_sound(R,S).
interesting(R,S) :- can_hear(R,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room_fact", room_id))
        if room.cozy:
            lines.append(asp.fact("cozy", room_id))
        if room.dark:
            lines.append(asp.fact("dark", room_id))
        if room.has_window:
            lines.append(asp.fact("window", room_id))
    for src_id, src in SOURCES.items():
        lines.append(asp.fact("source_fact", src_id))
        lines.append(asp.fact("sound_effect", src_id, src.sound))
        for room_id, room in ROOMS.items():
            if audibility(room, src):
                lines.append(asp.fact("room_sound", room_id, src_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show room_sound/2."))
    return sorted(set(asp.atoms(model, "room_sound")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == {(x, y) for x, y in b}:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - {(x, y) for x, y in b}))
    print("only in python:", sorted({(x, y) for x, y in b} - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], SOURCES[params.source], params.name, params.gender, params.trait, params.parent)
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
        print(asp_program("#show room_sound/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible room/source combos:")
        for room, source in valid_combos():
            print(f"  {room:9} {source}")
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
            header = f"### {p.name}: {p.source} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
