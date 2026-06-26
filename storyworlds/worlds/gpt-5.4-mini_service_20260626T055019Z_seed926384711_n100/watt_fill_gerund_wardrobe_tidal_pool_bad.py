#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure mystery at a tidal pool.

Premise:
- A junior space scout and a captain arrive at a moon tidal pool.
- Their portable wardrobe locker is supposed to hold spare suits and a power cell.
- The station beacon is dim, measured in watts, and someone has been quietly draining it.
- The crew shares equipment and tries to solve the mystery.

Tone:
- Child-facing, concrete, and space-adventure flavored.
- The ending is a bad ending: they learn the truth, but the tide takes the locker and the beacon still fails.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "scout", "robot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tidal pool"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_word: str
    event: str
    cause: str
    solved_by: str
    bad_end: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    shareable: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the tidal pool", affords={"inspect", "share", "repair"})

MYSTERY = Mystery(
    id="power-drain",
    clue_word="watt",
    event="the beacon was fading",
    cause="a tiny leak in the wardrobe battery line",
    solved_by="opening the wardrobe and sharing one power cell",
    bad_end="the tide flooded the wardrobe before the fix could hold",
)

GEAR = {
    "wardrobe": Gear(
        id="wardrobe",
        label="wardrobe locker",
        phrase="a white wardrobe locker with a humming latch",
    ),
    "cell": Gear(
        id="cell",
        label="power cell",
        phrase="a small power cell with one bright blue stripe",
    ),
    "lamp": Gear(
        id="lamp",
        label="signal lamp",
        phrase="a pocket signal lamp",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Luna", "Tess"]
BOY_NAMES = ["Jace", "Oren", "Pax", "Finn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = _meter(e, key) + amount


def _add_meme(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _story_intro(world: World, scout: Entity, partner: Entity) -> None:
    world.say(
        f"{scout.id} was a little space scout who liked shiny buttons, calm maps, and moon water that glittered like glass."
    )
    world.say(
        f"{scout.pronoun().capitalize()} and {partner.id} came to {world.setting.place} to check a dim station beacon and keep the night safe."
    )


def _mystery_setup(world: World, scout: Entity) -> None:
    _add_meme(scout, "curiosity", 1)
    _add_meter(scout, "attention", 1)
    world.say(
        f"But the beacon only gave a weak blink. It used just a few watt-sparks, and nobody knew where the missing power went."
    )
    world.say(
        f"{scout.id} leaned toward the damp stones and said, \"Something here is hiding a clue.\""
    )


def _inspect_wardrobe(world: World, scout: Entity, wardrobe: Entity) -> None:
    _add_meme(scout, "worry", 1)
    world.say(
        f"Near the water stood a wardrobe locker, and its latch trembled each time the tide licked the metal feet."
    )
    world.say(
        f"{scout.id} opened {wardrobe.it()} carefully and found one empty shelf, one warm cable, and a tiny blue sticker marked with {MYSTERY.clue_word}s."
    )


def _share_gear(world: World, scout: Entity, partner: Entity, cell: Entity, lamp: Entity) -> None:
    _add_meme(scout, "sharing", 1)
    _add_meme(partner, "sharing", 1)
    _add_meter(cell, "used", 1)
    world.say(
        f"{partner.id} passed over {cell.phrase}, and {scout.id} held up {lamp.phrase} so they could work together."
    )
    world.say(
        f"They shared the lamp beam across the wet floor, looking for the place where the watt trail had gone thin."
    )


def _reveal_cause(world: World, scout: Entity, wardrobe: Entity) -> None:
    _add_meme(scout, "aha", 1)
    world.say(
        f"At last, {scout.id} spotted the trouble: a loose wire behind the wardrobe panel had been sipping power all night."
    )
    world.say(
        f"The mystery was solved, and the clue made sense at once. {MYSTERY.solved_by.capitalize()} was the right answer."
    )


def _bad_ending(world: World, scout: Entity, partner: Entity, wardrobe: Entity) -> None:
    _add_meme(scout, "disappointment", 1)
    _add_meme(partner, "disappointment", 1)
    _add_meter(wardrobe, "flooded", 1)
    world.say(
        f"But just then the tide rushed in faster than the fix could hold."
    )
    world.say(
        f"The wardrobe locker slipped on the slick stones and toppled into the salt water."
    )
    world.say(
        f"{MYSTERY.bad_end.capitalize()}, so the beacon stayed dim and the two friends carried their shared tools back to the ship in the gray moon-dark."
    )


def tell_story(world: World, scout: Entity, partner: Entity) -> None:
    wardrobe = world.add(Entity(id="wardrobe", type="thing", label="wardrobe locker", phrase=GEAR["wardrobe"].phrase))
    cell = world.add(Entity(id="cell", type="thing", label="power cell", phrase=GEAR["cell"].phrase))
    lamp = world.add(Entity(id="lamp", type="thing", label="signal lamp", phrase=GEAR["lamp"].phrase))

    _story_intro(world, scout, partner)
    world.para()
    _mystery_setup(world, scout)
    _inspect_wardrobe(world, scout, wardrobe)
    world.para()
    _share_gear(world, scout, partner, cell, lamp)
    _reveal_cause(world, scout, wardrobe)
    world.para()
    _bad_ending(world, scout, partner, wardrobe)

    world.facts.update(
        scout=scout,
        partner=partner,
        wardrobe=wardrobe,
        cell=cell,
        lamp=lamp,
        mystery=MYSTERY,
        solved=True,
        bad_end=True,
    )


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_name_gender(name: str, gender: str) -> bool:
    if gender == "girl":
        return name in GIRL_NAMES
    return name in BOY_NAMES


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scout = f["scout"]
    partner = f["partner"]
    return [
        f'Write a short space-adventure story for a young child about {scout.id}, {partner.id}, and a mystery measured in watt-sparks.',
        f"Tell a gentle tale at the tidal pool where two crew members share gear, find a clue in a wardrobe locker, and lose the rescue to the tide.",
        f'Write a story that includes the words "{MYSTERY.clue_word}", "sharing", and "wardrobe".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scout = f["scout"]
    partner = f["partner"]
    wardrobe = f["wardrobe"]
    return [
        QAItem(
            question=f"Where did {scout.id} and {partner.id} go to check the beacon?",
            answer=f"They went to {world.setting.place} to check the beacon and look for the missing power.",
        ),
        QAItem(
            question=f"What did {scout.id} find inside the wardrobe locker?",
            answer=f"{scout.id} found an empty shelf, a warm cable, and a clue marked with {MYSTERY.clue_word}s.",
        ),
        QAItem(
            question=f"How did {scout.id} and {partner.id} work together?",
            answer=f"They shared a power cell and a signal lamp, then searched the wardrobe locker side by side.",
        ),
        QAItem(
            question=f"Did the story end happily?",
            answer="No. The mystery was solved, but the tide flooded the wardrobe locker and the beacon still stayed dim.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a watt?",
            answer="A watt is a way to measure power, like how strongly a light or machine is running.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means using or giving something together so more than one person can help or enjoy it.",
        ),
        QAItem(
            question="What is a wardrobe?",
            answer="A wardrobe is a cupboard or locker used for storing clothes, suits, or gear.",
        ),
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind near rocks when the tide goes out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(tidal_pool).
mystery(power_drain).

valid_story(Name, Gender) :- name(Name), gender(Gender), wears(Name, Gender).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "tidal_pool"), asp.fact("mystery", "power_drain")]
    for n in GIRL_NAMES:
        lines.append(asp.fact("name", n))
        lines.append(asp.fact("gender", "girl"))
        lines.append(asp.fact("wears", n, "girl"))
    for n in BOY_NAMES:
        lines.append(asp.fact("name", n))
        lines.append(asp.fact("gender", "boy"))
        lines.append(asp.fact("wears", n, "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_names() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_names())
    python_set = {(n, "girl") for n in GIRL_NAMES} | {(n, "boy") for n in BOY_NAMES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} names).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld at a tidal pool.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
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
    if args.name and not valid_name_gender(args.name, gender):
        raise StoryError("The chosen name does not match the chosen gender for this storyworld.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    return StoryParams(name=name, gender=gender, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    scout = world.add(Entity(id=params.name, kind="character", type="scout"))
    partner = world.add(Entity(id=params.partner, kind="character", type="captain"))
    tell_story(world, scout, partner)
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


def _curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mira", gender="girl", partner="Jace"),
        StoryParams(name="Nia", gender="girl", partner="Finn"),
        StoryParams(name="Pax", gender="boy", partner="Luna"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_names())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in _curated()]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
