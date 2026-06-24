#!/usr/bin/env python3
"""
storyworlds/worlds/fluorescent_crystallite_telescope_bad_ending_conflict_nursery.py
===================================================================================

A small nursery-rhyme story world about a child, a glowing crystallite trinket,
and a telescope that leads to a conflict and a bad ending.

Seed tale:
---
Little June had a bright little telescope and a cup of fluorescent crystallite
stones that glimmered like tiny stars. At night, June wanted to look at the sky,
but her brother wanted to shake the stones and make them sparkle on the windowsill.
They argued over the telescope, the glow spread everywhere, and the glass tipped
over. In the end, the moon vanished behind clouds, the telescope lens got smudged,
and nobody got the perfect starry view they wanted.
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


THRESHOLD = 1.0


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


@dataclass
class Setting:
    place: str = "the nursery window"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    mess: str
    is_special: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    prize: str
    hero: str
    hero_type: str
    sibling: str
    sibling_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "nursery_window": Setting(place="the nursery window", indoor=True, affords={"stargaze"}),
}

ITEMS = {
    "telescope": Item(
        id="telescope",
        label="telescope",
        phrase="a bright little telescope",
        type="telescope",
        risk="smudged",
        mess="smudge",
        is_special=True,
    ),
    "crystallite": Item(
        id="crystallite",
        label="crystallite stones",
        phrase="a cup of fluorescent crystallite stones",
        type="stones",
        risk="spilled",
        mess="spill",
        is_special=True,
    ),
}

GIRL_NAMES = ["June", "Mina", "Lily", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Milo", "Ned"]
TRAITS = ["tiny", "cheery", "sleepy", "bouncy"]


def make_prize(item: Item) -> Item:
    return item


def valid_combos() -> list[tuple[str, str, str]]:
    return [("nursery_window", "telescope", "crystallite")]


def explain_rejection(item: str, prize: str) -> str:
    return "(No story: this nursery-rhyme world only supports a telescope, fluorescent crystallite stones, and a conflict at the nursery window.)"


def generate_story(world: World, hero: Entity, sibling: Entity, telescope: Entity, stones: Entity) -> None:
    world.say(
        f"Little {hero.id} was a {next(t for t in ['tiny', 'cheery', 'sleepy', 'bouncy'] if t in hero.memes or True)} child who loved a bright little telescope."
    )


def _story(world: World) -> None:
    hero = world.get("June")
    sibling = world.get("Milo")
    telescope = world.get("telescope")
    stones = world.get("crystallite")

    world.say(
        f"Little {hero.id} loved the telescope by the nursery window, and {hero.pronoun('possessive')} eyes were wide as buttons."
    )
    world.say(
        f"{hero.id} also loved the fluorescent crystallite stones, for they shone like crumbs of a fairy moon."
    )

    world.para()
    hero.memes["wish"] = 1
    sibling.memes["wish"] = 1
    world.say(
        f"One night, {hero.id} wanted to look at the stars, but {sibling.id} wanted to shake the crystallite stones so they would glitter and sing."
    )
    hero.memes["conflict"] = 1
    sibling.memes["conflict"] = 1
    world.say(
        f"They tugged and talked in tiny sharp voices, and the telescope wobbled on the sill."
    )
    stones.meters["spill"] = 1
    telescope.meters["smudge"] = 1

    world.para()
    world.say(
        f"Then the cup tipped over with a little clink and a clatter, and the fluorescent crystallite stones rolled everywhere like escaped stars."
    )
    world.say(
        f"The lens got smudged, the moon hid behind a cloud, and the nursery went quiet in a sad, soft way."
    )
    hero.memes["sad"] = 1
    sibling.memes["sad"] = 1
    world.say(
        f"In the end, {hero.id} could not count the stars, and {sibling.id} could not make the shiny stones dance; the best little view was gone for the night."
    )

    world.facts.update(hero=hero, sibling=sibling, telescope=telescope, stones=stones)


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sibling = world.facts["sibling"]
    return [
        QAItem(
            question="Why did the child get upset at the nursery window?",
            answer=f"Because {hero.id} wanted to use the telescope to look at the stars, but {sibling.id} wanted the fluorescent crystallite stones instead, so they began to argue.",
        ),
        QAItem(
            question="What happened when the crystallite cup tipped over?",
            answer="The fluorescent crystallite stones rolled everywhere, the telescope lens got smudged, and the moon view was ruined.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly and sadly: nobody got a clear starry look, and the nursery window stayed quiet with the telescope smudged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a telescope for?",
            answer="A telescope helps you see faraway things, like the moon and stars, more closely.",
        ),
        QAItem(
            question="What does fluorescent mean?",
            answer="Fluorescent means it glows brightly, often with a vivid shine that stands out in the dark.",
        ),
        QAItem(
            question="What are crystallites like?",
            answer="Crystallites are tiny crystal pieces, and they can sparkle like little bits of glass or starshine.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about a fluorescent crystallite sparkle, a telescope, and a child who wants to look at the stars.',
        "Tell a gentle but sad story where two children argue over a glowing crystallite cup and a telescope by the window.",
        "Write a simple rhyming tale that ends with a smudged telescope and a bad night for star-watching.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def tell() -> World:
    world = World(SETTINGS["nursery_window"])
    hero = world.add(Entity(id="June", kind="character", type="girl"))
    sibling = world.add(Entity(id="Milo", kind="character", type="boy"))
    telescope = world.add(Entity(id="telescope", type="telescope", label="telescope", phrase="a bright little telescope"))
    stones = world.add(Entity(id="crystallite", type="stones", label="crystallite stones", phrase="a cup of fluorescent crystallite stones"))
    _story(world)
    return world


def valid_story_params(place: str, item: str, prize: str) -> bool:
    return (place, item, prize) in valid_combos()


@dataclass
class ASPRules:
    pass


ASP_RULES = r"""
place(nursery_window).
item(telescope).
prize(crystallite).
affords(nursery_window,stargaze).
glows(crystallite,fluorescent).
at_risk(telescope,crystallite) :- item(telescope), prize(crystallite).
valid_story(nursery_window,telescope,crystallite) :- at_risk(telescope,crystallite).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "nursery_window"),
        asp.fact("item", "telescope"),
        asp.fact("prize", "crystallite"),
        asp.fact("glows", "crystallite", "fluorescent"),
        asp.fact("affords", "nursery_window", "stargaze"),
        asp.fact("at_risk", "telescope", "crystallite"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with a fluorescent crystallite telescope conflict.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=["telescope"])
    ap.add_argument("--prize", choices=["crystallite"])
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
    if args.place and args.place != "nursery_window":
        raise StoryError("(No story: this world only takes place at the nursery window.)")
    if args.activity and args.activity != "telescope":
        raise StoryError("(No story: only the telescope action is supported.)")
    if args.prize and args.prize != "crystallite":
        raise StoryError("(No story: only fluorescent crystallite stones are supported.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling = "Milo" if name != "Milo" else "June"
    sibling_type = "boy" if sibling in BOY_NAMES else "girl"
    return StoryParams(
        place="nursery_window",
        item="telescope",
        prize="crystallite",
        hero=name,
        hero_type=gender,
        sibling=sibling,
        sibling_type=sibling_type,
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="nursery_window",
            item="telescope",
            prize="crystallite",
            hero="June",
            hero_type="girl",
            sibling="Milo",
            sibling_type="boy",
            trait="tiny",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
