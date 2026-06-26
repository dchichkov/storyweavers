#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/baptize_moral_value_rhyming_story.py
====================================================================================

A small story world for a rhyming, moral-value tale about a gentle baptism:
a child learns that the blessing matters most when it is kind, calm, and true.

The seed word is "baptize"; the moral value is "kindness".
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the chapel garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    verb: str
    action: str
    rhyme: str
    token: str
    mood: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    may_get_wet: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "chapel_garden": Setting(place="the chapel garden", indoor=False, affords={"baptize"}),
    "quiet_pond": Setting(place="the quiet pond", indoor=False, affords={"baptize"}),
    "sunroom_font": Setting(place="the sunroom by the font", indoor=True, affords={"baptize"}),
}

RITES = {
    "baptize": Rite(
        id="baptize",
        verb="baptize",
        action="pour a little water and say a kind blessing",
        rhyme="bright and light",
        token="baptize",
        mood="gentle",
        tags={"baptize", "kindness"},
    ),
}

GIFTS = {
    "lily": Gift(id="lily", label="lily", phrase="a small white lily"),
    "candle": Gift(id="candle", label="candle", phrase="a little candle"),
    "banner": Gift(id="banner", label="banner", phrase="a stitched welcome banner"),
}

NAMES = ["Maya", "Nina", "Eli", "Pia", "Theo", "Luca"]
PARENTS = ["mother", "father"]
TRAITS = ["kind", "bright", "gentle", "small", "cheerful"]


@dataclass
class StoryParams:
    place: str
    rite: str
    gift: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
class StoryWorld(World):
    pass


def build_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    gift = world.add(Entity(
        id=params.gift,
        kind="thing",
        type=params.gift,
        label=GIFTS[params.gift].label,
        phrase=GIFTS[params.gift].phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    rite = RITES[params.rite]

    # Act 1: setup
    world.say(f"{hero.id} was a {params.trait} child with a heart so true, / who loved kind words and wishes that came through.")
    world.say(f"{hero.pronoun().capitalize()} held {hero.pronoun('possessive')} {gift.label} and smiled in the glow, / for today was a day for a blessing to flow.")
    world.say(f"{hero.id} hoped to {rite.verb} the gift with care, / to give it a name and a hopeful prayer.")

    # Act 2: tension
    world.para()
    hero.memes["wish"] = hero.memes.get("wish", 0) + 1
    hero.meters["excited"] = hero.meters.get("excited", 0) + 1
    world.say(f"But {hero.pronoun('possessive')} {parent.label} said, soft as the dew, / \"A blessing should be gentle, and kind through and through.\"")
    world.say(f"\"Not rushed like a splash, not loud like a drum, / but calm as a song when the day has begun.\"")
    hero.memes["impatience"] = hero.memes.get("impatience", 0) + 1
    world.say(f"{hero.id} paused for a breath and slowed down the pace, / then softened {hero.pronoun('possessive')} hands and brightened {hero.pronoun('possessive')} face.")

    # Act 3: resolution
    world.para()
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.meters["water"] = hero.meters.get("water", 0) + 1
    gift.meters["wet"] = gift.meters.get("wet", 0) + 1
    world.say(f"Together they {rite.action}, / and the little room seemed warmer at once.")
    world.say(f"The water went down in a tender, tiny stream, / and {hero.id} spoke the blessing like a sweet, clear dream.")
    world.say(f"The {gift.label} stayed safe, and the moment felt right, / {rite.rhyme} in the soft evening light.")
    world.say(f"{hero.id} learned that a kind heart makes a blessing shine, / and {hero.pronoun('possessive')} happy new promise was gentle and fine.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "gift": gift,
        "rite": rite,
        "setting": world.setting,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    gift = f["gift"]
    rite = f["rite"]
    return [
        f'Write a short rhyming story for a child named {hero.id} that includes the word "{rite.token}".',
        f"Tell a gentle story where {hero.id} wants to {rite.verb} {gift.phrase} and learns the moral value of kindness.",
        f'Write a simple rhyming story about a blessing, a child, and the word "{rite.token}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, gift, rite = f["hero"], f["parent"], f["gift"], f["rite"]
    return [
        QAItem(
            question=f"Who wanted to {rite.verb} the {gift.label}?",
            answer=f"{hero.id} wanted to {rite.verb} the {gift.label} with a gentle blessing.",
        ),
        QAItem(
            question=f"What did the {parent.type} remind {hero.id} to show?",
            answer=f"The {parent.type} reminded {hero.id} to show kindness and not rush the blessing.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} slowed down, spoke kindly, and the {gift.label} was blessed in a calm, happy way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means using gentle words, helping others, and caring about how they feel.",
        ),
        QAItem(
            question="What is a blessing?",
            answer="A blessing is a good wish or a kind moment that is meant to bring peace and hope.",
        ),
        QAItem(
            question="What does baptize mean?",
            answer="To baptize means to give a special blessing with water as part of a caring ceremony.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
rite_ok(R) :- rite(R), moral_value(kindness), baptize_rite(R).

valid_story(P, R, G) :- place_ok(P), rite_ok(R), gift(G).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for rid in RITES:
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("baptize_rite", rid))
    lines.append(asp.fact("moral_value", "kindness"))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for r in RITES:
            for g in GIFTS:
                out.append((p, r, g))
    return out


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    # ASP is permissive but deterministic here; compare the projected shapes we expect.
    expected = {(p, r, g) for p, r, g in python_set}
    found = {(a[0], a[1], a[2]) for a in clingo_set}
    if found == expected:
        print(f"OK: clingo gate matches valid story space ({len(found)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if found - expected:
        print("  only in clingo:", sorted(found - expected))
    if expected - found:
        print("  only in python:", sorted(expected - found))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming moral-value baptism story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    rite = args.rite or rng.choice(list(RITES))
    gift = args.gift or rng.choice(list(GIFTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, rite=rite, gift=gift, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, r, g in stories:
            print(f"  {p:16} {r:10} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=p, rite=r, gift=g, name="Maya", gender="girl", parent="mother", trait="kind")
            for p in SETTINGS for r in RITES for g in GIFTS
        ]
        samples = [generate(p) for p in combos]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
