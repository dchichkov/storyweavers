#!/usr/bin/env python3
"""
A small mythic story world about a nurse, a strange transformation, and the
sound effects that break a spell.

The seed words are honored in a child-safe, nonsexual medical framing:
a nurse helps a cursed child whose body is transformed by a spell, and the
nurse makes sure every part of the body, including the vagina, is safe and
restored.

The world is intentionally narrow: a few plausible combinations, a strong
turn, and a clear ending image.
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
# Domain model
# ---------------------------------------------------------------------------
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "nurse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    echoes: bool = False


@dataclass
class Curse:
    id: str
    label: str
    sound: str
    effect: str
    target_form: str
    reverse_sound: str


@dataclass
class StoryParams:
    place: str
    curse: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "temple": Place(name="the temple of reeds", kind="temple", echoes=True),
    "cave": Place(name="the listening cave", kind="cave", echoes=True),
    "spring": Place(name="the moon spring", kind="spring", echoes=False),
}

CURSES = {
    "goose": Curse(
        id="goose",
        label="goose spell",
        sound="HONK-HONK!",
        effect="turned the child into a goose",
        target_form="goose",
        reverse_sound="soft wind and a lullaby",
    ),
    "stone": Curse(
        id="stone",
        label="stone spell",
        sound="KRRR-CHUNK!",
        effect="turned the child stiff as stone",
        target_form="stone statue",
        reverse_sound="a warm drumbeat",
    ),
    "echo": Curse(
        id="echo",
        label="echo spell",
        sound="WHOOO-WHOOO!",
        effect="filled the air with looping voices",
        target_form="echo-shadow",
        reverse_sound="one clear bell note",
    ),
}

NURSE_NAMES = ["Mira", "Iris", "Nera", "Sora", "Lena", "Tala"]
CHILD_NAMES = ["Pip", "Noa", "Lumi", "Kea", "Rin", "Mina"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def recite(world: World, text: str) -> None:
    world.say(text)


def transformation_intro(world: World, nurse: Entity, child: Entity, curse: Curse) -> None:
    recite(
        world,
        f"Long ago, in {world.place.name}, there lived a nurse named {nurse.id} who "
        f"listened for trouble the way owls listen for moonlight."
    )
    recite(
        world,
        f"One dusk, {child.id} was struck by a {curse.label}. "
        f"It flashed {curse.sound} and {curse.effect}."
    )


def nurse_checks(world: World, nurse: Entity, child: Entity) -> None:
    child.memes["fear"] = 1
    nurse.memes["care"] = 1
    recite(
        world,
        f"{nurse.id} knelt beside {child.id} and checked every part of the body with a "
        f"gentle hand. Even the vagina was safe, because this was a healing spell and "
        f"not a cruel one."
    )
    recite(
        world,
        f"{child.id} blinked from behind the wrong shape and whispered, "
        f"\"Will I stay this way forever?\""
    )


def diagnosis(world: World, nurse: Entity, curse: Curse) -> None:
    world.facts["curse_sound"] = curse.sound
    world.facts["reverse_sound"] = curse.reverse_sound
    recite(
        world,
        f"{nurse.id} answered, \"No. Every spell has a sound that can wake the old self. "
        f"We only have to find the right one.\""
    )


def cast_sound(world: World, nurse: Entity, child: Entity, curse: Curse) -> None:
    if world.place.echoes:
        recite(world, f"She clapped once: clap!")
        recite(world, f"Then she stamped the floor: thud!")
        recite(world, f"Finally she sang the old counter-song: {curse.reverse_sound}.")
    else:
        recite(world, f"She tapped a shell: tink!")
        recite(world, f"Then she breathed a steady note: hummm.")
        recite(world, f"At last she sang the old counter-song: {curse.reverse_sound}.")

    child.memes["hope"] = 1
    world.facts["attempted"] = True


def undo_transformation(world: World, nurse: Entity, child: Entity, curse: Curse) -> None:
    if "healed" in world.fired:
        return
    world.fired.add("healed")
    child.type = "child"
    child.label = child.id
    child.phrase = f"a {child.id}"
    child.meters["transformed"] = 0
    child.memes["fear"] = 0
    child.memes["joy"] = 1
    recite(
        world,
        f"The sound rolled through the stones. {curse.sound} broke apart like a cracked shell, "
        f"and the spell let go."
    )
    recite(
        world,
        f"At once, {child.id} returned to {child.id}'s own shape, warm and breathing. "
        f"{nurse.id} smiled, because the body was whole again, and the vagina was just one "
        f"more safe and ordinary part of it."
    )
    recite(
        world,
        f"{child.id} laughed, hugged {nurse.id}, and listened to the last echo fade into the dark."
    )


def tell(place: Place, curse: Curse, name: str) -> World:
    world = World(place)
    nurse = world.add(Entity(id="Nurse", kind="character", type="nurse", label="nurse"))
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    child.meters["transformed"] = 1
    child.memes["fear"] = 1

    transformation_intro(world, nurse, child, curse)
    world.para()
    nurse_checks(world, nurse, child)
    diagnosis(world, nurse, curse)
    world.para()
    cast_sound(world, nurse, child, curse)
    undo_transformation(world, nurse, child, curse)

    world.facts.update(
        nurse=nurse,
        child=child,
        curse=curse,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["curse"]
    return [
        'Write a short myth about a nurse who hears a strange spell and breaks it with sound effects.',
        f"Tell a gentle legend where a nurse saves a child from a {c.label} by using careful listening and a counter-song.",
        "Write a child-friendly mythical story with transformation, healing, and loud magical sound effects.",
    ]


def story_qa(world: World) -> list[QAItem]:
    nurse: Entity = world.facts["nurse"]
    child: Entity = world.facts["child"]
    curse: Curse = world.facts["curse"]
    return [
        QAItem(
            question=f"Who helped {child.id} after the {curse.label} changed {child.id}?",
            answer=f"{nurse.id} helped {child.id}. {nurse.id} was the nurse who stayed calm and listened for the right way to break the spell.",
        ),
        QAItem(
            question=f"What sound did the curse make when it struck {child.id}?",
            answer=f"It made a loud {curse.sound} sound, and that was the first sign of the transformation.",
        ),
        QAItem(
            question=f"How did {nurse.id} fix the transformation?",
            answer=f"{nurse.id} used careful sound effects, including a counter-song, and the spell let go when the right note was sung.",
        ),
        QAItem(
            question=f"What was safe about {child.id}'s body while the spell was active?",
            answer="The nurse checked the whole body carefully, including the vagina, and made sure nothing about the healing was harmful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nurse?",
            answer="A nurse is a person who helps care for sick or hurt people and checks that they are safe.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is when one shape or form changes into another shape or form.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that suggest noises, like clap, thud, or whoosh, so a listener can imagine the sound.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story about special events, magic, or heroes from long ago.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
curse(C) :- curse_id(C).

healed(P,C) :- place(P), curse(C), counter_sound(C).
safe_body(C) :- healed(_,C), checked_vagina(C).

valid_story(P,C) :- place(P), curse(C), counter_sound(C), safe_body(C).

#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for cid in CURSES:
        lines.append(asp.fact("curse_id", cid))
        lines.append(asp.fact("counter_sound", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_stories() -> list[tuple]:
    return sorted((p, c) for p in PLACES for c in CURSES)


def asp_verify() -> int:
    py = set(python_valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: nurse, transformation, sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--name", choices=CHILD_NAMES + NURSE_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    curse = args.curse or rng.choice(list(CURSES))
    name = args.name or rng.choice(CHILD_NAMES)
    if name in NURSE_NAMES:
        raise StoryError("The child must be a child name, not a nurse name.")
    return StoryParams(place=place, curse=curse, name=name, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CURSES[params.curse], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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
    StoryParams(place="temple", curse="goose", name="Mina"),
    StoryParams(place="cave", curse="stone", name="Pip"),
    StoryParams(place="spring", curse="echo", name="Lumi"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, c in asp_valid_stories():
            print(f"{p} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.curse} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
