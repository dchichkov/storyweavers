#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a bit of everyday magic and an unhappy
transformation that gets turned into a gentle fix.

Seed tale sketch:
- A child has an ordinary day and feels miserable because a little magic goes
  wrong.
- The wrong magic transforms something important into the wrong shape.
- The child and a helper search for a calm, practical way to undo it.
- The ending proves the transformation changed back and the day became normal
  again, but with a little more care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    transformed_from: str = ""
    transformed_to: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    target_from: str
    target_to: str
    undo_word: str
    helper_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Room:
    name: str = "the kitchen"
    places: set[str] = field(default_factory=lambda: {"kitchen"})


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic: str = ""
        self.misfire: bool = False

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
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.magic = self.magic
        w.misfire = self.misfire
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "kitchen": Room(name="the kitchen", places={"kitchen"}),
    "bedroom": Room(name="the bedroom", places={"bedroom"}),
    "laundry": Room(name="the laundry room", places={"laundry"}),
    "garden": Room(name="the garden", places={"garden"}),
}

CHARACTERS = {
    "girl": ("Mina", "girl"),
    "boy": ("Perry", "boy"),
}

TRAITS = ["quiet", "patient", "curious", "gentle", "careful", "soft-spoken"]

CHART = {
    "spoon": ("spoon", "a shiny spoon", "metal"),
    "sock": ("sock", "a striped sock", "cloth"),
    "plant": ("plant", "a small potted plant", "leaf"),
    "cup": ("cup", "a little blue cup", "ceramic"),
}

CHARMS = {
    "reverse": Charm(
        id="reverse",
        label="a reverse charm",
        phrase="a tiny reverse charm",
        target_from="mismatched",
        target_to="normal",
        undo_word="reverse",
        helper_word="straighten",
        tags={"magic", "undo"},
    ),
    "undo": Charm(
        id="undo",
        label="an undo charm",
        phrase="an undo charm drawn in the air",
        target_from="swapped",
        target_to="right",
        undo_word="undo",
        helper_word="fix",
        tags={"magic", "undo"},
    ),
    "wake": Charm(
        id="wake",
        label="a wake-up charm",
        phrase="a gentle wake-up charm",
        target_from="sleepy",
        target_to="awake",
        undo_word="wake",
        helper_word="soothe",
        tags={"magic", "small"},
    ),
}

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    charm: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
def _mood_words(value: float) -> str:
    if value >= 2:
        return "miserable"
    if value >= 1:
        return "sad"
    return "a little off"


def build_world(params: StoryParams) -> World:
    world = World(ROOMS[params.room])
    hero_type = params.gender
    hero_name = params.name
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"calm": 0.0},
        memes={"mood": 0.0, "worry": 0.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))
    obj_type, obj_label, obj_material = CHART[params.object]
    obj = world.add(Entity(
        id="object",
        type=obj_type,
        label=obj_label,
        phrase=obj_label,
        owner=hero.id,
        caretaker=helper.id,
        meters={"whole": 1.0, "wrong_shape": 0.0, "bright": 0.0},
        memes={"familiar": 1.0},
    ))
    charm = CHARMS[params.charm]
    world.facts.update(hero=hero, helper=helper, obj=obj, charm=charm, material=obj_material)
    return world


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    trait = world.facts.get("trait", "")
    if trait:
        world.say(f"{hero.id} was a {trait} little {hero.type} who liked quiet corners and small routines.")
    else:
        world.say(f"{hero.id} was a little {hero.type} who liked quiet corners and small routines.")
    world.say(f"{hero.pronoun('possessive').capitalize()} favorite thing was {obj.label}, kept right where {hero.id} could see it.")


def miscast(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    charm = world.facts["charm"]
    hero.memes["mood"] += 2.0
    hero.memes["worry"] += 1.0
    obj.meters["wrong_shape"] = 1.0
    obj.memes["familiar"] = 0.0
    world.magic = charm.id
    world.misfire = True
    world.say(
        f"One afternoon, {hero.id} tried a tiny bit of magic and whispered {charm.undo_word} too quickly."
    )
    world.say(
        f"The spell slipped, and {obj.pronoun('possessive')} {obj.label} became the wrong shape."
    )


def feel_miserable(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    world.say(
        f"{hero.id} looked at {obj.label} and felt miserable."
    )
    world.say(
        f"Nothing about the room felt fun anymore, because the ordinary little thing had stopped looking like itself."
    )


def help_fix(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["obj"]
    charm = world.facts["charm"]
    hero.memes["hope"] += 1.0
    helper.memes["care"] += 1.0
    world.say(
        f"Then {helper.label} came over, spoke softly, and said, \"Let's not hurry. We can {charm.helper_word} it together.\""
    )
    world.say(
        f"They held still, took a slow breath, and traced the {charm.label} again, this time carefully."
    )
    obj.meters["wrong_shape"] = 0.0
    obj.meters["whole"] = 1.0
    obj.memes["familiar"] = 1.0
    hero.memes["mood"] = 0.0
    hero.memes["worry"] = 0.0
    world.say(
        f"The magic settled down, and {obj.label} came back to normal."
    )


def ending(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["obj"]
    world.say(
        f"{hero.id} smiled, picked up {obj.it()}, and felt better right away."
    )
    world.say(
        f"{helper.label} stayed nearby while the room went back to its calm, everyday quiet."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    world.facts["trait"] = params.trait
    introduce(world)
    world.para()
    miscast(world)
    feel_miserable(world)
    world.para()
    help_fix(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------
def valid_choices() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for charm in CHARMS:
            for obj in CHART:
                combos.append((room, charm, obj))
    return combos


ASP_RULES = r"""
room(Room) :- setting(Room).
charm(Charm) :- magic(Charm).
thing(Obj) :- object(Obj).

valid(Room,Charm,Obj) :- room(Room), charm(Charm), thing(Obj).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for room in ROOMS:
        lines.append(asp.fact("setting", room))
    for charm in CHARMS:
        lines.append(asp.fact("magic", charm))
    for obj in CHART:
        lines.append(asp.fact("object", obj))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_choices() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_choices())
    cl = set(asp_valid_choices())
    if py == cl:
        print(f"OK: clingo gate matches valid_choices() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_choices():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    charm = f["charm"]
    return [
        f'Write a short slice-of-life story where {hero.id} uses {charm.phrase} and feels miserable when {obj.label} changes shape.',
        f"Tell a gentle story about a little {hero.type} whose {obj.label} gets transformed by magic, then fixed with help.",
        f'Write a story with the words "miserable", "magic", and "transformation" about a small everyday problem that gets better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"What made {hero.id} feel miserable in the story?",
            answer=f"{hero.id} felt miserable because {obj.label} was transformed into the wrong shape by magic.",
        ),
        QAItem(
            question=f"Who helped {hero.id} fix the magic transformation?",
            answer=f"{helper.label} helped {hero.id} calm down and trace the {charm.label} carefully.",
        ),
        QAItem(
            question=f"What happened at the end to {obj.label}?",
            answer=f"{obj.label} changed back to normal, and {hero.id} smiled again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising or impossible in real life that can make unusual things happen in a story.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one shape, form, or state into another one.",
        ),
        QAItem(
            question="What does miserable mean?",
            answer="Miserable means feeling very unhappy, uncomfortable, or upset.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    charm: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.room not in ROOMS:
        raise StoryError("Unknown room.")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    if args.object and args.object not in CHART:
        raise StoryError("Unknown object.")
    room = args.room or rng.choice(list(ROOMS))
    charm = args.charm or rng.choice(list(CHARMS))
    obj = args.object or rng.choice(list(CHART))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or CHARACTER_NAMES[gender][rng.randrange(len(CHARACTER_NAMES[gender]))]
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, charm=charm, object=obj, name=name, gender=gender, helper=helper, trait=trait)


CHARACTER_NAMES = {
    "girl": ["Mina", "Lena", "Tia", "Nora", "Ava"],
    "boy": ["Eli", "Noah", "Sam", "Theo", "Finn"],
}


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  magic={world.magic!r} misfire={world.misfire}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about miserable magic transformations.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--object", choices=CHART)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    StoryParams(room="kitchen", charm="reverse", object="spoon", name="Mina", gender="girl", helper="mother", trait="careful"),
    StoryParams(room="bedroom", charm="undo", object="sock", name="Eli", gender="boy", helper="father", trait="quiet"),
    StoryParams(room="laundry", charm="wake", object="cup", name="Nora", gender="girl", helper="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_choices())} compatible choices")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.charm} in {p.room} with {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
