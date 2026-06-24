#!/usr/bin/env python3
"""
storyworlds/worlds/center_superstition_imaginary_twist_mystery.py
==================================================================

A standalone storyworld: a small mystery about the center of a place, a
superstition, and an imaginary twist that turns out to matter.

Premise:
- A child hears an old superstition about the center of a place.
- Something seems missing or moved.
- The child investigates with a helper and a clue.
- The twist is that the "haunting" is imaginary; a simple physical cause was
  hiding in the center of the room/garden/court.
- The ending proves what changed: the clue is found, the superstition is
  gently explained, and the center is set right.

The world model uses typed entities with physical meters and emotional memes.
It includes a Python reasonableness gate and an inline ASP twin.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    center: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    center_noun: str
    surface: str
    hidden_space: str
    sound: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    type: str
    can_be_hidden: bool = True
    can_shift: bool = True


@dataclass
class Twist:
    id: str
    hint: str
    reveal: str
    cause: str


@dataclass
class StoryParams:
    place: str
    clue: str
    twist: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "room": Setting(
        place="the quiet room",
        center_noun="the center of the rug",
        surface="rug",
        hidden_space="under the rug",
        sound="a soft thump",
        affords={"search", "inspect"},
    ),
    "garden": Setting(
        place="the back garden",
        center_noun="the center stone",
        surface="stone path",
        hidden_space="behind the center stone",
        sound="a tiny click",
        affords={"search", "inspect"},
    ),
    "court": Setting(
        place="the old court",
        center_noun="the center mark",
        surface="stone tiles",
        hidden_space="in a crack by the center mark",
        sound="a faint scrape",
        affords={"search", "inspect"},
    ),
}

CLUES = {
    "coin": Clue(
        id="coin",
        label="coin",
        phrase="a bright penny",
        type="coin",
    ),
    "key": Clue(
        id="key",
        label="key",
        phrase="a little brass key",
        type="key",
    ),
    "marble": Clue(
        id="marble",
        label="marble",
        phrase="a glass marble",
        type="marble",
    ),
}

TWISTS = {
    "draft": Twist(
        id="draft",
        hint="The little noise seemed to drift from the center.",
        reveal="It was only a loose board or stone making a sound when someone stepped near the center.",
        cause="a hidden gap under the center spot",
    ),
    "string": Twist(
        id="string",
        hint="The clue looked as if it had been tugged by an unseen hand.",
        reveal="A string had caught the clue and pulled it toward the center.",
        cause="a simple string snag",
    ),
    "shadow": Twist(
        id="shadow",
        hint="The child thought the center looked strange in the dim light.",
        reveal="The strange shape was only a shadow; the clue had been there the whole time.",
        cause="an imaginary shadow trick",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "June", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Max", "Leo", "Noah", "Eli", "Sam"]
TRAITS = ["curious", "careful", "brave", "quiet", "wiry", "thoughtful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def clue_at_risk(setting: Setting, clue: Clue) -> bool:
    return clue.can_be_hidden and clue.can_shift and setting.surface in {"rug", "stone path", "stone tiles"}


def select_twist(setting: Setting, clue: Clue) -> Optional[Twist]:
    if setting.place == "the quiet room":
        return TWISTS["shadow"] if clue.id == "marble" else TWISTS["draft"]
    if setting.place == "the back garden":
        return TWISTS["string"] if clue.id in {"coin", "key"} else TWISTS["draft"]
    return TWISTS["draft"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            if clue_at_risk(setting, clue) and select_twist(setting, clue):
                combos.append((place, clue_id, select_twist(setting, clue).id))
    return combos


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return (
        f"(No story: the {clue.label} would not plausibly become a center mystery "
        f"in {setting.place}. Try a clue that can hide near the center and be found with a simple twist.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
clue_at_risk(P, C) :- setting(P), clue(C), surface(P, S), can_hide(C), can_shift(C), center_surface(S).
twist_ok(P, C, T) :- clue_at_risk(P, C), twist(T), setting(P).

valid(P, C, T) :- clue_at_risk(P, C), twist_ok(P, C, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("surface", pid, s.surface))
        lines.append(asp.fact("center_noun", pid, s.center_noun))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
        if s.surface in {"rug", "stone path", "stone tiles"}:
            lines.append(asp.fact("center_surface", s.surface))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.can_be_hidden:
            lines.append(asp.fact("can_hide", cid))
        if c.can_shift:
            lines.append(asp.fact("can_shift", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def story_intro(world: World, hero: Entity, parent: Entity, clue: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who liked quiet places and careful looking."
    )
    world.say(
        f"One afternoon, {hero.id}'s {parent.label} told {hero.pronoun('object')} an old superstition: "
        f"if something went missing, the answer was often waiting near the center."
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} breath and stared at {world.setting.place}, "
        f"because {clue.label} had vanished and everyone kept whispering about the center."
    )


def story_middle(world: World, hero: Entity, parent: Entity, clue: Entity, twist: Twist) -> None:
    hero.memes["worry"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.para()
    world.say(
        f"{hero.id} looked again and again, first by the door, then by the wall, and then right at the center."
    )
    world.say(
        f"Each time, {world.setting.sound} seemed to answer back, which made the superstition feel almost real."
    )
    world.say(twist.hint)
    world.say(
        f"{hero.id} asked {hero.pronoun('possessive')} {parent.label}, "
        f"\"Do you think the center is hiding it?\""
    )


def story_twist(world: World, hero: Entity, parent: Entity, clue: Entity, twist: Twist) -> None:
    world.para()
    world.say(
        f"{hero.pronoun().capitalize()} stepped closer and found the truth."
    )
    if twist.id == "shadow":
        world.say(
            f"The mystery was imaginary: a shadow had made the empty spot look strange, but the clue was still there."
        )
    elif twist.id == "string":
        world.say(
            f"The mystery was not spooky at all. A string had tugged the clue toward the center and left it caught."
        )
    else:
        world.say(
            f"The mystery was only a small thing hiding in the middle: a loose place under the center spot made the noise."
        )
    world.say(
        f"{hero.id} reached to the {world.setting.hidden_space} and found {clue.phrase}."
    )
    clue.meters["found"] = 1.0


def story_end(world: World, hero: Entity, parent: Entity, clue: Entity, twist: Twist) -> None:
    hero.memes["relief"] = 1.0
    hero.memes["bravery"] = 1.0
    world.para()
    world.say(
        f"{hero.id} smiled, because the superstition had a harmless answer after all."
    )
    world.say(
        f"{hero.id} showed {hero.pronoun('object')} {clue.label} and set it back at the center where it belonged."
    )
    world.say(
        f"Now the center looked ordinary again, and the old worry felt imaginary."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    clue = CLUES[params.clue]
    twist = TWISTS[params.twist]

    world = World(setting)
    gender = params.gender
    hero_type = gender
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        label=params.name,
        meters={"feet": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "bravery": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    clue_ent = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.type,
        label=clue.label,
        phrase=clue.phrase,
        owner=parent.id,
        caretaker=parent.id,
        location=setting.hidden_space,
        center=True,
        meters={"found": 0.0},
    ))

    world.facts.update(hero=hero, parent=parent, clue=clue_ent, twist=twist, setting=setting)
    story_intro(world, hero, parent, clue_ent)
    story_middle(world, hero, parent, clue_ent, twist)
    story_twist(world, hero, parent, clue_ent, twist)
    story_end(world, hero, parent, clue_ent, twist)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    twist = f["twist"]
    setting = f["setting"]
    return [
        f'Write a short mystery story for a young child about a center, a superstition, and an imaginary scare in {setting.place}.',
        f"Tell a gentle story where {hero.id} searches for {clue.label} near the center and learns the strange thing was only {twist.cause}.",
        f'Write a simple, child-facing story that uses the word "center" and ends with the clue being found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    clue = f["clue"]
    twist = f["twist"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for in {setting.place}?",
            answer=f"{hero.id} was looking for {clue.phrase}. It had been missing near the center.",
        ),
        QAItem(
            question=f"What old superstition did the {parent.label} mention?",
            answer=(
                f"The {parent.label} said that when something goes missing, the answer is often near the center. "
                f"That made the search feel mysterious."
            ),
        ),
        QAItem(
            question="What made the mystery turn out to be harmless?",
            answer=(
                f"The mystery had an imaginary twist. {twist.reveal} "
                f"After {hero.id} checked carefully, the clue was found and the spooky feeling went away."
            ),
        ),
        QAItem(
            question=f"Where did {hero.id} finally find {clue.label}?",
            answer=f"{hero.id} found it at the center again, where it belonged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does center mean?",
            answer="The center is the middle part of something, the place that is equally far from the edges.",
        ),
        QAItem(
            question="What is a superstition?",
            answer="A superstition is an old belief about things that are lucky, unlucky, or mysterious, even when there is a simple reason.",
        ),
        QAItem(
            question="What does imaginary mean?",
            answer="Imaginary means made up in the mind or not real, like a pretend monster or a scary idea that turns out to be harmless.",
        ),
    ]


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.center:
            bits.append("center=True")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    twist: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about center, superstition, and an imaginary twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, clue=clue, twist=twist, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="room", clue="coin", twist="shadow", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="garden", clue="key", twist="string", name="Theo", gender="boy", parent="father"),
    StoryParams(place="court", clue="marble", twist="draft", name="Nora", gender="girl", parent="mother"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
