#!/usr/bin/env python3
"""
A tiny storyworld: a nap room space adventure with foreshadowing, twist, and sharing.
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

ROOMS = {
    "nap_room": {
        "label": "the nap room",
        "props": {"quiet", "soft"},
        "hints": {"whisper", "moonlight", "blanket", "rocket"},
    }
}

CHAR_TYPES = ["child", "caretaker"]
NAMES = ["Mila", "Noah", "Ivy", "Leo", "Zuri", "Finn", "June", "Owen"]
MOOD_WORDS = ["curious", "sleepy", "brave", "gentle", "careful", "sly"]
SPACE_OBJECTS = {
    "pillow": {"kind": "soft", "role": "rest place"},
    "blanket": {"kind": "soft", "role": "cover"},
    "rocket book": {"kind": "story", "role": "imaginary ship"},
    "moon lamp": {"kind": "light", "role": "small moon"},
    "toy comet": {"kind": "toy", "role": "shared treasure"},
}

ASP_RULES = r"""
#show valid_story/3.

valid_story(Room, Object, Twist) :- room(Room), object(Object), twist(Twist), shares(Object), foreshadows(Room, Object).
"""

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        return "\n".join(lines)

@dataclass
class StoryParams:
    room: str = "nap_room"
    hero: str = "Mila"
    hero_kind: str = "child"
    caretaker: str = "June"
    object: str = "toy comet"
    mood: str = "curious"
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A succinct nap-room space-adventure storyworld.")
    ap.add_argument("--room", choices=ROOMS.keys())
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--caretaker", choices=NAMES)
    ap.add_argument("--object", choices=SPACE_OBJECTS.keys())
    ap.add_argument("--mood", choices=MOOD_WORDS)
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

def reasonableness_gate(params: StoryParams) -> None:
    if params.hero == params.caretaker:
        raise StoryError("The child and caretaker must be different characters.")
    if params.object not in SPACE_OBJECTS:
        raise StoryError("Unknown shared object.")
    if params.room not in ROOMS:
        raise StoryError("Unknown room.")
    if params.room != "nap_room":
        raise StoryError("This world only supports the nap room setting.")
    if params.object == "moon lamp" and params.mood == "sly":
        raise StoryError("A moon lamp story needs a gentler mood than sly.")

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or "nap_room"
    hero = args.hero or rng.choice(NAMES)
    caretaker = args.caretaker or rng.choice([n for n in NAMES if n != hero])
    obj = args.object or rng.choice(list(SPACE_OBJECTS.keys()))
    mood = args.mood or rng.choice(MOOD_WORDS)
    params = StoryParams(room=room, hero=hero, caretaker=caretaker, object=obj, mood=mood)
    reasonableness_gate(params)
    return params

def make_world(params: StoryParams) -> World:
    world = World(room=params.room)
    hero = world.add(Entity("hero", "character", params.hero))
    caretaker = world.add(Entity("caretaker", "character", params.caretaker))
    obj = world.add(Entity("object", "thing", params.object))
    world.facts.update(hero=hero, caretaker=caretaker, obj=obj, params=params)
    return world

def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    hero = world.facts["hero"]
    caretaker = world.facts["caretaker"]
    obj = world.facts["obj"]
    room = ROOMS[params.room]["label"]

    hero.memes["curiosity"] = 1.0
    hero.memes["joy"] = 0.5
    world.say(
        f"{hero.label} was a {params.mood} little child in {room}, where the blankets felt like clouds."
    )
    world.say(
        f"On a quiet evening, {hero.label} noticed the {obj.label} beside the low cot and kept glancing at it."
    )
    world.say(
        f"The first clue was tiny: the {obj.label} had a bright stripe like a comet tail, and that made {hero.label} smile."
    )

    world.para()
    hero.memes["desire"] = 1.0
    world.say(
        f"{hero.label} wanted to take the {obj.label} and fly it around the room, but {caretaker.label} had a softer idea."
    )
    hero.meters["reach"] = 1.0
    world.say(
        f"{caretaker.label} said the room was for resting, then pointed to the blanket nest and the moon lamp."
    )

    world.para()
    hero.memes["twist"] = 1.0
    world.say(
        f"Then came the twist: the {obj.label} was not a toy ship at all, but the missing sharing star for the room's night map."
    )
    world.say(
        f"{hero.label} and {caretaker.label} shared it, and the star marked a path to the pillow fort."
    )
    hero.memes["love"] = 1.0
    caretaker.memes["relief"] = 1.0
    world.say(
        f"By the end, {hero.label} tucked the {obj.label} between the pillows, and the whole nap room felt ready for a calm trip through space."
    )

    world.facts["story"] = {
        "room": room,
        "twist": "sharing star",
        "foreshadowing": "bright stripe like a comet tail",
    }
    story = world.render()
    prompts = [
        "Write a succinct space-adventure story set in a nap room with foreshadowing, a twist, and sharing.",
        f"Tell a child-sized story where {params.hero} notices a clue, learns a surprise, and shares {params.object}.",
        "Make the ending calm, concrete, and gently surprising.",
    ]
    story_qa = [
        QAItem(
            question=f"What clue foreshadowed the twist in the story?",
            answer="The foreshadowing clue was the bright stripe on the object that looked like a comet tail.",
        ),
        QAItem(
            question=f"What was the twist about the {params.object}?",
            answer="The twist was that the object was really the missing sharing star for the room's night map.",
        ),
        QAItem(
            question=f"How did the characters solve the problem?",
            answer=f"{params.hero} and {params.caretaker} shared the object, and that made the nap room peaceful again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints at something important that will happen later.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("room", "nap_room")]
    for name in SPACE_OBJECTS:
        lines.append(asp.fact("object", name))
    lines.append(asp.fact("twist", "sharing"))
    lines.append(asp.fact("shares", "toy_comet"))
    lines.append(asp.fact("foreshadows", "nap_room", "toy_comet"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("nap_room", "toy_comet", "sharing")}
    if atoms == expected:
        print("OK: ASP parity holds.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(triples)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for name in NAMES[:3]:
            params = StoryParams(hero=name, caretaker=next(n for n in NAMES if n != name), object="toy comet", mood="curious")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
