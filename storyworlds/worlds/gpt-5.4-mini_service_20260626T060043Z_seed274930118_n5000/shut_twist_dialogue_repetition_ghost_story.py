#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shut_twist_dialogue_repetition_ghost_story.py
===============================================================================================================

A small ghost-story world with a shut door, a spoken warning, a repeated pattern,
and one twist that changes what the "ghost" really is.

The seed suggests a ghost-story feel with dialogue, repetition, and a shut motif.
This world builds a tiny simulation around a child, a closed place, a repeated
sound, and a final turn that re-frames the haunting.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    open_state: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    shutable: bool = True
    echo: bool = False
    dark: bool = False


@dataclass
class Sound:
    id: str
    word: str
    source: str
    repeat: str
    volume: str
    mislead: str
    reveal: str


@dataclass
class StoryParams:
    place: str
    sound: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        other = World(self.place)
        import copy as _copy

        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "house": Place(name="the old house", shutable=True, echo=True, dark=True),
    "hall": Place(name="the narrow hall", shutable=True, echo=True, dark=True),
    "attic": Place(name="the attic", shutable=True, echo=True, dark=True),
    "shed": Place(name="the backyard shed", shutable=True, echo=False, dark=True),
}

SOUNDS = {
    "tap": Sound(
        id="tap",
        word="tap-tap",
        source="the window",
        repeat="again and again",
        volume="soft",
        mislead="a ghost scratching at the glass",
        reveal="rain tapping on the window",
    ),
    "knock": Sound(
        id="knock",
        word="knock-knock",
        source="the shut door",
        repeat="three times",
        volume="loud",
        mislead="a ghost knocking from the dark",
        reveal="a branch knocking the door",
    ),
    "thump": Sound(
        id="thump",
        word="thump-thump",
        source="the floorboards",
        repeat="over and over",
        volume="heavy",
        mislead="a ghost walking close by",
        reveal="a loose board bumping in the wind",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ella", "Nora", "June"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Finn", "Owen"]
TRAITS = ["brave", "curious", "small", "sleepy", "steady"]


# ---------------------------------------------------------------------------
# The ghost-story simulation
# ---------------------------------------------------------------------------
def shut_place(world: World) -> None:
    world.say(
        f"The {world.place.name.removeprefix('the ')} was quiet, and everything felt "
        f"shut tight."
    )
    world.place.shutable = True
    world.facts["shut"] = True


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next((t for t in child.meters if False), '')}"
        f"{child.type} who liked listening when the house went silent."
    )


def set_scene(world: World, child: Entity, companion: Entity, sound: Sound) -> None:
    world.say(
        f"One evening, {child.id} and {child.pronoun('possessive')} {companion.label} "
        f"stood in the shut house and heard {sound.word}."
    )
    world.say(
        f"{sound.word}, {sound.word}."
        f" The noise came {sound.repeat}, from {sound.source}."
    )
    world.facts["heard_word"] = sound.word
    world.facts["sound_id"] = sound.id


def fear(world: World, child: Entity, sound: Sound) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    world.say(
        f"{child.id} whispered, \"Did you hear that?\""
    )
    world.say(
        f"{child.pronoun().capitalize()} clutched {child.pronoun('possessive')} hands and "
        f"listened to the {sound.word} again."
    )


def caution(world: World, companion: Entity, child: Entity, sound: Sound) -> None:
    companion.memes["calm"] = companion.memes.get("calm", 0.0) + 1.0
    world.say(
        f"\"Stay close,\" {companion.id} said. \"We should not open anything "
        f"when the house is shut and the sound keeps coming.\""
    )
    world.say(
        f"\"But it sounds like a ghost,\" {child.id} said."
    )


def twist(world: World, child: Entity, sound: Sound) -> None:
    reveal = sound.reveal
    world.say(
        f"Then the biggest twist came: the ghosty sound was not a ghost at all."
    )
    world.say(
        f"It was {reveal}, and the old house had been making the same tricking sound "
        f"all along."
    )
    world.facts["reveal"] = reveal


def resolve(world: World, child: Entity, companion: Entity, sound: Sound) -> None:
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{child.id} laughed softly. \"So it was only {sound.reveal},\" {child.pronoun()} said."
    )
    world.say(
        f"{companion.id} smiled and said, \"Yes. Sometimes a shut room makes small "
        f"things sound spooky.\""
    )
    world.say(
        f"At the end, the house was still shut, but the scary feeling was gone."
    )


def tell(place: Place, sound: Sound, name: str = "Lily", gender: str = "girl",
         companion_type: str = "father", trait: str = "curious") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type, label=companion_type))
    world.facts["child"] = child
    world.facts["companion"] = companion
    world.facts["sound"] = sound
    world.facts["trait"] = trait
    shut_place(world)
    world.para()
    set_scene(world, child, companion, sound)
    fear(world, child, sound)
    caution(world, companion, child, sound)
    world.para()
    twist(world, child, sound)
    resolve(world, child, companion, sound)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    sound: Sound = world.facts["sound"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        f'Write a short ghost story for a young child that repeats "{sound.word}" and ends with a twist.',
        f"Tell a spooky-but-gentle story where {child.id} hears {sound.word} in a shut house and {companion.label} helps explain it.",
        f'Write a simple story with dialogue, repetition, and a surprise reveal about "{sound.word}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    sound: Sound = world.facts["sound"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.id} hear in the shut house?",
            answer=f"{child.id} heard {sound.word} coming from {sound.source}, and it sounded spooky at first.",
        ),
        QAItem(
            question=f"Who told {child.id} to stay close?",
            answer=f"{companion.id} told {child.id} to stay close and not open things in the dark house.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the scary sound was not a ghost at all. It was {sound.reveal}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the child feeling relieved, because the house was still shut but the ghost feeling was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does shut mean?",
            answer="Shut means closed so something cannot be opened right away.",
        ),
        QAItem(
            question="Why can a small sound seem scary in the dark?",
            answer="A small sound can seem scary in the dark because people cannot see it clearly, so their minds may imagine something bigger.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes you understand the story in a new way.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
sound(S) :- sound_fact(S).
shut_scene(P,S) :- place(P), sound(S), shutable(P).
twist_story(S) :- sound(S), reveal(S,_).
valid_story(P,S) :- shut_scene(P,S), twist_story(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if place.shutable:
            lines.append(asp.fact("shutable", pid))
        if place.echo:
            lines.append(asp.fact("echo", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound_fact", sid))
        lines.append(asp.fact("word", sid, sound.word))
        lines.append(asp.fact("source", sid, sound.source))
        lines.append(asp.fact("repeat", sid, sound.repeat))
        lines.append(asp.fact("mislead", sid, sound.mislead))
        lines.append(asp.fact("reveal", sid, sound.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if not asp_valid_stories():
        print("MISMATCH: ASP produced no valid stories.")
        return 1
    print(f"OK: ASP produced {len(asp_valid_stories())} valid story combinations.")
    return 0


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny shut-house ghost story with dialogue, repetition, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    sound = args.sound or rng.choice(list(SOUNDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, sound=sound, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        SOUNDS[params.sound],
        name=params.name,
        gender=params.gender,
        companion_type=params.companion,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.name}")
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


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
    StoryParams(place="house", sound="tap", name="Lily", gender="girl", companion="father", trait="curious"),
    StoryParams(place="hall", sound="knock", name="Leo", gender="boy", companion="mother", trait="brave"),
    StoryParams(place="attic", sound="thump", name="Mia", gender="girl", companion="father", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a[0]} {a[1]}" for a in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
