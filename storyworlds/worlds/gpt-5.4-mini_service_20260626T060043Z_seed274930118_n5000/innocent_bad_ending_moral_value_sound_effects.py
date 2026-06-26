#!/usr/bin/env python3
"""
A small story world for ghost-story-style tales with an innocent child,
sound effects, a moral value, and a bad ending.
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
    kind: str
    type: str
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    shadow: str
    sound: str
    omen: str
    eerie: bool = True


@dataclass
class Omen:
    id: str
    sound_effect: str
    scare: str
    consequence: str
    bad_ending: str
    moral_value: str
    risk: str


@dataclass
class StoryParams:
    place: str
    omen: str
    name: str
    age: int
    seed: Optional[int] = None


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        shadow="the rafters cast long toothy shadows",
        sound="the floor gave a soft creak",
        omen="a cold draft slipped under the door",
    ),
    "cellar": Place(
        id="cellar",
        label="the cellar",
        shadow="the walls looked damp and dim",
        sound="water ticked somewhere in the dark",
        omen="the lantern flame shrank to a pin",
    ),
    "hall": Place(
        id="hall",
        label="the old hallway",
        shadow="the wallpaper seemed to lean closer",
        sound="the boards went knock-knock under tiny steps",
        omen="a picture frame tilted by itself",
    ),
    "garden": Place(
        id="garden",
        label="the moonlit garden",
        shadow="the bushes shook like whispering faces",
        sound="the leaves went hiss-hiss in the wind",
        omen="a gate creaked open on its own",
    ),
}

OMENS = {
    "whisper": Omen(
        id="whisper",
        sound_effect="shh-shh",
        scare="the whisper sounded like someone calling from behind the wall",
        consequence="the little listener stepped closer and lost the way back",
        bad_ending="no one found the brave little child before the night went deep",
        moral_value="it is wise to stay with a trusted grown-up when a place feels wrong",
        risk="followed the whisper",
    ),
    "thump": Omen(
        id="thump",
        sound_effect="thump-thump",
        scare="something heavy banged once, then twice, in the dark",
        consequence="the startled child dropped the lantern and the flame winked out",
        bad_ending="the dark swallowed the room, and the door never opened again",
        moral_value="it is kinder and safer to ask for help than to hide your fear alone",
        risk="walked farther into the noise",
    ),
    "knock": Omen(
        id="knock",
        sound_effect="knock-knock",
        scare="the knocking came from the wrong side of the door",
        consequence="the curious child touched the latch and the cold handle turned",
        bad_ending="the door closed with a sigh, and the hallway stayed empty afterward",
        moral_value="curiosity should listen to caution",
        risk="reached for the latch",
    ),
    "rattle": Omen(
        id="rattle",
        sound_effect="rat-a-tat",
        scare="a little rattle danced through the jars like tiny bones",
        consequence="the child shook, spilled the keys, and could not gather them again",
        bad_ending="the keys vanished into the dark cracks, and the way out was lost",
        moral_value="careful hands keep trouble small",
        risk="jiggled the box too hard",
    ),
}

NAMES = ["Mina", "Toby", "Nina", "Eli", "Lia", "Otto", "Pia", "Owen"]
AGES = [5, 6, 7, 8]


class World:
    def __init__(self, place: Place, omen: Omen) -> None:
        self.place = place
        self.omen = omen
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ASP_RULES = r"""
#show valid_story/2.

valid_story(P, O) :- place(P), omen(O).
"""


def asp_facts() -> str:
    import asp
    out = []
    for pid in PLACES:
        out.append(asp.fact("place", pid))
    for oid in OMENS:
        out.append(asp.fact("omen", oid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with an innocent child and a bad ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--name")
    ap.add_argument("--age", type=int, choices=AGES)
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
    place = args.place or rng.choice(sorted(PLACES))
    omen = args.omen or rng.choice(sorted(OMENS))
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.choice(AGES)
    return StoryParams(place=place, omen=omen, name=name, age=age)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.age < 5 or params.age > 8:
        raise StoryError("This world only tells stories about very young children, ages 5 to 8.")
    if params.place not in PLACES or params.omen not in OMENS:
        raise StoryError("Unknown place or omen.")
    if not params.name:
        raise StoryError("A child needs a name.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    place = PLACES[params.place]
    omen = OMENS[params.omen]
    world = World(place, omen)

    child = world.add(Entity(id=params.name, kind="character", type="child"))
    child.memes["innocent"] = 1.0
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0

    world.facts.update(
        child=child,
        place=place,
        omen=omen,
        bad_ending=omen.bad_ending,
        moral_value=omen.moral_value,
    )

    world.say(
        f"Little {params.name} was an innocent child who wandered into {place.label} after sunset."
    )
    world.say(
        f"{place.shadow.capitalize()}. {place.sound.capitalize()}, and then {place.omen}."
    )
    world.say(
        f"{params.name} heard {omen.sound_effect} from the dark and felt a tiny shiver."
    )
    world.say(
        f"The sound was so strange that {params.name} made a mistake and {omen.risk}."
    )
    world.say(
        f"That only made it worse: {omen.scare}."
    )
    world.say(
        f"{omen.consequence.capitalize()}."
    )
    world.say(
        f"In the end, {omen.bad_ending}, and the moon kept watch over the empty place."
    )
    world.say(
        f"The moral value was simple: {omen.moral_value}."
    )

    prompts = [
        f"Write a short ghost story about an innocent child named {params.name} in {place.label}.",
        f"Tell a scary but gentle story that includes the sound effect '{omen.sound_effect}'.",
        f"Make the ending bad, but finish with a clear moral value for young readers.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {params.name}, an innocent {params.age}-year-old child.",
        ),
        QAItem(
            question=f"What sound effect was heard in {place.label}?",
            answer=f"The story used the sound effect '{omen.sound_effect}'.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{omen.bad_ending.capitalize()}.",
        ),
        QAItem(
            question=f"What moral value does the story give?",
            answer=omen.moral_value.capitalize() + ".",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an innocent child?",
            answer="An innocent child is a child who is not trying to do harm and usually trusts the world around them.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a written sound like 'knock-knock' or 'shh-shh' that helps readers imagine what they would hear.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a lesson about how to act kindly, safely, or wisely.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: kind={e.kind} type={e.type} memes={e.memes} meters={e.meters}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


CURATED = [
    StoryParams(place="attic", omen="whisper", name="Mina", age=6),
    StoryParams(place="cellar", omen="thump", name="Toby", age=7),
    StoryParams(place="hall", omen="knock", name="Lia", age=5),
    StoryParams(place="garden", omen="rattle", name="Eli", age=8),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in PLACES for o in OMENS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(format_json(samples))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
