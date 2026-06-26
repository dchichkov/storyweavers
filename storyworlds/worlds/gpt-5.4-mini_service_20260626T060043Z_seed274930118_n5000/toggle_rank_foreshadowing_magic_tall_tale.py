#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/toggle_rank_foreshadowing_magic_tall_tale.py
=========================================================================================================================

A tiny tall-tale storyworld about a magical rank toggle, a humble setting, and
a foreshadowed turn that becomes true by the end.

Premise:
- A young worker in a river town wears a brass rank toggle that can raise or
  lower their official rank.
- The town values rank because it decides who rings bells, who leads boats, and
  who gets the first warm loaf.
- A magic sign from the river hints that the toggle is not just for show.

Story engine:
- The simulated world tracks physical state in meters and emotional state in
  memes.
- The protagonist can choose to toggle rank.
- High rank helps with responsibility but can also create pressure.
- The resolution proves the foreshadowing: the humble choice reveals the true
  magic, and the character ends with a better place in the town without bragging.

This file is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    rank: int = 0
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the river town"
    afford_toggle: bool = True
    magic: bool = True
    foreshadowing: bool = True


@dataclass
class ToggleItem:
    label: str
    phrase: str
    low_rank: int
    high_rank: int
    owns_magic: bool = True
    charm: str = "brass"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    "river_town": Setting(place="the river town", afford_toggle=True, magic=True, foreshadowing=True),
    "harbor": Setting(place="the harbor", afford_toggle=True, magic=True, foreshadowing=True),
    "hill_village": Setting(place="the hill village", afford_toggle=True, magic=True, foreshadowing=True),
}

TRUTHS = {
    "cap": ToggleItem(label="rank cap", phrase="a brass rank cap", low_rank=1, high_rank=3, owns_magic=True),
    "sash": ToggleItem(label="rank sash", phrase="a bright rank sash", low_rank=2, high_rank=4, owns_magic=True),
    "pin": ToggleItem(label="rank pin", phrase="a polished rank pin", low_rank=0, high_rank=2, owns_magic=True),
}

GIRL_NAMES = ["Mara", "Nina", "Lena", "Tess", "June", "Poppy"]
BOY_NAMES = ["Otis", "Evan", "Benn", "Toby", "Jules", "Arlo"]
TRAITS = ["plucky", "curious", "steady", "bold", "bright"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def initial_rank(trait: str) -> int:
    return {"plucky": 1, "curious": 0, "steady": 2, "bold": 1, "bright": 0}.get(trait, 0)


def rank_title(rank: int) -> str:
    return {
        0: "lantern helper",
        1: "dock runner",
        2: "bell keeper",
        3: "river captain",
        4: "sky captain",
    }.get(rank, "town hand")


def rank_noun(rank: int) -> str:
    return {
        0: "helper",
        1: "runner",
        2: "keeper",
        3: "captain",
        4: "grand captain",
    }.get(rank, "hand")


def rank_change_ok(old: int, new: int) -> bool:
    return 0 <= new <= 4 and abs(new - old) == 1


def foreshadow(world: World, hero: Entity, item: ToggleItem) -> None:
    if not world.setting.foreshadowing:
        return
    world.say(
        f"Long before the town knew what to make of it, {hero.id} noticed the {item.label} "
        f"warm whenever the river bells sang."
    )
    world.say(
        f"Old fishers said that was a sign: when brass warmed like bread, rank was about to tell the truth."
    )


def introduce(world: World, hero: Entity, parent: Entity, item: ToggleItem) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('possessive')} {rank_title(hero.rank)} in {world.setting.place}, "
        f"and {hero.pronoun('possessive')} {parent.label} had given {hero.pronoun('object')} a {item.phrase}."
    )
    world.say(
        f"{hero.id} liked that little charm because it could toggle rank with a quick press, "
        f"though nobody in town agreed whether that was clever or risky."
    )


def wants_rank(world: World, hero: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} wanted to see what happened at a higher rank, not to boast, but to learn "
        f"why the bells bowed to some folks and not to others."
    )


def press_toggle(world: World, hero: Entity, item: ToggleItem) -> None:
    old = hero.rank
    new = old + 1 if old < item.high_rank else old - 1
    if not rank_change_ok(old, new):
        raise StoryError("the toggle cannot move the rank farther without snapping the charm")
    hero.rank = new
    world.facts["toggled_from"] = old
    world.facts["toggled_to"] = new
    world.say(
        f"{hero.id} pressed the brass toggle and the rank on the {item.label} clicked from {rank_noun(old)} to {rank_noun(new)}."
    )


def magic_response(world: World, hero: Entity, item: ToggleItem) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    if item.owns_magic and hero.rank >= 2:
        world.say(
            f"At once the river wind curled around {hero.id}'s shoulders like a ribbon, "
            f"and a silver gull landed on the post beside {hero.id} as if it had been waiting for orders."
        )
    else:
        world.say(
            f"The charm gave a tiny bell-note, as if it were warning {hero.id} that rank alone was not the whole story."
        )


def town_reacts(world: World, hero: Entity, parent: Entity) -> None:
    if hero.rank >= 2:
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        world.say(
            f"The dock hands stood a little straighter, and even {parent.label} smiled, "
            f"for {hero.id} now wore a higher rank than before."
        )
    else:
        world.say(
            f"The town did not laugh, because the river had already taught everyone that small ranks can carry big jobs."
        )


def turn_back(world: World, hero: Entity, item: ToggleItem, parent: Entity) -> None:
    if hero.rank > item.low_rank:
        old = hero.rank
        hero.rank = item.low_rank
        world.say(
            f"Then {hero.id} did something nobody expected: {hero.pronoun()} toggled back down, "
            f"because {hero.pronoun('possessive')} {parent.label} needed a hand with the lantern boats."
        )
        world.facts["returned_from"] = old
        world.facts["returned_to"] = hero.rank


def resolution(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"That was the truest kind of magic in the river town. {hero.id} learned that rank could be changed, "
        f"but worth was shown by what {hero.pronoun()} did after the click."
    )
    world.say(
        f"By sunset, {hero.id} was back to {rank_title(hero.rank)}, carrying the lantern rope for {parent.label}, "
        f"and the gull kept watch above the water like a bright white exclamation point."
    )


def tell(setting: Setting, hero_name: str, gender: str, trait: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, rank=initial_rank(trait)))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    item = TRUTHS["cap"] if setting.place == "the river town" else TRUTHS["sash"]
    toggle = world.add(Entity(id="toggle", type="thing", label=item.label, phrase=item.phrase, owner=hero.id))
    toggle.meters = {"shine": 1.0, "warmth": 0.0}
    toggle.memes = {"mystery": 1.0}

    world.facts.update(hero=hero, parent=parent, item=toggle, setting=setting, item_def=item, trait=trait)

    foreshadow(world, hero, item)
    world.para()
    introduce(world, hero, parent, item)
    wants_rank(world, hero)
    press_toggle(world, hero, item)
    magic_response(world, hero, item)
    town_reacts(world, hero, parent)

    world.para()
    turn_back(world, hero, item, parent)
    resolution(world, hero, parent)
    world.facts["final_rank"] = hero.rank
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_def = f["item_def"]
    return [
        f'Write a tall tale for a child about a {hero.type} who uses a "{item_def.label}" to toggle rank.',
        f'Tell a magical story in which {hero.id} learns what rank means in {world.setting.place}.',
        f'Write a foreshadowing-heavy story where a small brass charm turns out to matter more than bragging.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item_def = f["item_def"]
    return [
        QAItem(
            question=f"What did {hero.id} use to toggle rank?",
            answer=f"{hero.id} used {item_def.phrase}, a small magic charm that could raise or lower rank by one step."
        ),
        QAItem(
            question=f"Why did {hero.id} press the toggle?",
            answer=f"{hero.id} pressed it to see what a higher rank felt like, but also to learn what the town expected from a rank holder."
        ),
        QAItem(
            question=f"What changed when {hero.id} turned back down?",
            answer=f"{hero.id} stopped trying to hold the higher rank and chose to help {parent.label} with the lantern boats instead."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rank in a town?",
            answer="Rank is a place in an order. It can show who has more duty, who leads, or who is trusted with bigger jobs."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important later."
        ),
        QAItem(
            question="What makes magic in a story feel special?",
            answer="Magic feels special when it changes things in a surprising way, like making a charm warm or making a gull appear at the right moment."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.rank:
            bits.append(f"rank={e.rank}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

place(river_town;harbor;hill_village).
hero_gender(girl;boy).

rank_step(0..4).

valid(P, H, R) :- place(P), hero_gender(H), rank_step(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("hero_gender", g))
    for r in range(5):
        lines.append(asp.fact("rank_step", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, g, r) for p in SETTINGS for g in ["girl", "boy"] for r in range(5)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about a magic rank toggle.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.trait, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            p = StoryParams(
                place=place,
                name="Mara",
                gender="girl",
                parent="mother",
                trait="curious",
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
