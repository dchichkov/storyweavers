#!/usr/bin/env python3
"""
Storyworld: school library quest with a mosquito, a shock-dim lamp, and a clot.

This is a small, constraint-checked, classical story simulation in the style of a
rhyming children's tale. A child goes on a quest in the school library, meets a
tiny problem, and finds a gentle fix.
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
    label: str = ""
    type: str = ""
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the school library"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    verb: str
    rhyme1: str
    rhyme2: str
    reward: str
    risk: str
    fix: str
    keyword: str = "quest"


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the school library", affords={"quest"})

QUESTS = {
    "library_quest": Quest(
        id="library_quest",
        title="the reading quest",
        verb="seek the star-book",
        rhyme1="A hush in the stacks, a soft little breeze,",
        rhyme2="A quest in the library started with ease.",
        reward="the star-book",
        risk="the light would dim and the pages would sigh",
        fix="they used a bright lamp and kept the pages dry",
        keyword="quest",
    )
}

GEAR = {
    "lamp": Gear(
        id="lamp",
        label="a bright desk lamp",
        covers={"table"},
        guards={"shock-dim"},
        prep="turn on the bright desk lamp",
        tail="glowed and made the page lines clear",
    ),
    "fan": Gear(
        id="fan",
        label="a tiny fan",
        covers={"air"},
        guards={"mosquito"},
        prep="switch on a tiny fan",
        tail="whirred and chased the mosquito away",
    ),
    "cloth": Gear(
        id="cloth",
        label="a clean cloth",
        covers={"hand", "book"},
        guards={"clot"},
        prep="wipe the clot away with a clean cloth",
        tail="made the sticky spot slip loose",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ada", "Ivy"]
BOY_NAMES = ["Leo", "Max", "Ben", "Theo", "Noah", "Finn"]
TRAITS = ["brave", "curious", "bright", "gentle", "spry", "cheery"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [("the school library", "library_quest")]


def explain_rejection(place: str, quest: str) -> str:
    return (
        f"(No story: this tiny world only fits {quest!r} at {place!r}, in the school library quest.)"
    )


ASP_RULES = r"""
place(school_library).
quest(library_quest).
valid(P,Q) :- place(P), quest(Q).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import by contract

    return "\n".join(
        [
            asp.fact("place", "school_library"),
            asp.fact("quest", "library_quest"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp  # lazy import by contract

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Rhyming story engine
# ---------------------------------------------------------------------------
def setup_story(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} went to {world.setting.place} with a quest in mind, "
        f"to seek the star-book and be sweetly kind."
    )
    world.say(
        f"{quest.rhyme1} {quest.rhyme2}"
    )
    world.say(
        f"{hero.id} was a {hero.meters.get('age_word', 'young')} {hero.type} with {hero.memes.get('joy', 0)} bright cheer, "
        f"and {helper.id} stayed near with a smile and a cheer."
    )


def add_problem(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"But first came a mosquito, so tiny and sly, "
        f"that tickled {hero.pronoun('possessive')} nose and made {hero.pronoun('object')} sigh."
    )
    hero.memes["itchy"] = hero.memes.get("itchy", 0) + 1
    world.say(
        f"Then a shock-dim lamp flickered down to a gloom, "
        f"and the shelves went soft-gray in the library room."
    )
    world.say(
        f"Near the reading cart, there was a clot of old glue, "
        f"so the cart made a squeak and would not roll through."
    )
    world.facts["problem"] = "mosquito shock-dim clot"
    world.facts["quest"] = quest


def fix_story(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    fan = world.add(Entity(id="fan", kind="thing", label="tiny fan", type="fan"))
    lamp = world.add(Entity(id="lamp", kind="thing", label="bright desk lamp", type="lamp"))
    cloth = world.add(Entity(id="cloth", kind="thing", label="clean cloth", type="cloth"))

    world.say(
        f"Then {helper.id} said, \"Let's keep our spirits afloat; "
        f"we can stop the mosquito and save the big note.\""
    )
    world.say(
        f"They used {GEAR['fan'].label}, and {GEAR['lamp'].label} too, "
        f"and {GEAR['cloth'].label} for the clot that clung like glue."
    )
    world.say(
        f"{GEAR['fan'].prep.capitalize()}, {GEAR['lamp'].prep.capitalize()}, and {GEAR['cloth'].prep.capitalize()}; "
        f"{GEAR['fan'].tail}, {GEAR['lamp'].tail}, and {GEAR['cloth'].tail}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.facts["gear"] = {"fan": fan, "lamp": lamp, "cloth": cloth}
    world.facts["resolved"] = True
    world.say(
        f"So {hero.id} found the star-book at last with a grin, "
        f"and the quest felt like music from page to page in."
    )
    world.say(
        f"The mosquito flew off, the shock-dim glow shone bright, "
        f"and the clot was gone from the cart by night."
    )
    world.say(
        f"{hero.id} and {helper.id} left the library light, "
        f"with a happy new story tucked warm and tight."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    quest = QUESTS[params.quest]
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"age_word": "little"},
            memes={"joy": 1, "curiosity": 1},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="librarian",
            memes={"calm": 1, "helpfulness": 1},
        )
    )
    world.facts.update(hero=hero, helper=helper, quest=quest, setting=SETTING)
    setup_story(world, hero, helper, quest)
    world.say("")
    add_problem(world, hero, quest)
    world.say("")
    fix_story(world, hero, helper, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    return [
        f'Write a short rhyming story about {hero.id} on a {quest.keyword} in the school library.',
        f'Tell a gentle quest story where a {hero.type} named {hero.id} meets a mosquito, a shock-dim lamp, and a clot.',
        f'Create a child-friendly rhyme in the school library that ends with a happy fix for a sticky clot.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} go for the quest?",
            answer=f"{hero.id} went to the school library for the quest.",
        ),
        QAItem(
            question=f"What tiny problem bothered {hero.id} first?",
            answer=f"A mosquito bothered {hero.id} first and made the quest feel itchy.",
        ),
        QAItem(
            question=f"What helped fix the shock-dim light and the clot?",
            answer=f"{helper.id} helped use a bright desk lamp, a tiny fan, and a clean cloth to fix the trouble.",
        ),
        QAItem(
            question=f"What did {hero.id} find at the end of the quest?",
            answer=f"{hero.id} found the star-book at the end of the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mosquito?",
            answer="A mosquito is a tiny flying insect that can buzz around people and make them itchy when it bites.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like a light that makes the room look soft and shadowy.",
        ),
        QAItem(
            question="What is a clot?",
            answer="A clot is a sticky lump or clump that can make something hard to move or smooth out.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special trip or mission to look for something important or solve a problem.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming school-library quest storyworld.")
    ap.add_argument("--place", choices=["the school library"])
    ap.add_argument("--quest", choices=list(QUESTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "the school library":
        raise StoryError(explain_rejection(args.place, args.quest or "library_quest"))
    if args.quest and args.quest != "library_quest":
        raise StoryError(explain_rejection(args.place or "the school library", args.quest))
    if args.gender and args.name is None:
        pass
    place = "the school library"
    quest = "library_quest"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "Ms. Reed"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_verify_story() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(
            place="the school library",
            quest="library_quest",
            name="Mia",
            gender="girl",
            helper="Ms. Reed",
            trait="curious",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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
