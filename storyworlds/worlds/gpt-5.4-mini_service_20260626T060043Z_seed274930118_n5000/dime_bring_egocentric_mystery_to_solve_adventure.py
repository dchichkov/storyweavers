#!/usr/bin/env python3
"""
Standalone storyworld: a small Adventure-style Mystery to Solve built around a
lost dime, a bringing task, and an egocentric suspect who must learn to share
the spotlight.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
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
    place: str = "the old market lane"
    mood: str = "sunlit"
    has_clues: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    suspect_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the old market lane", mood="sunlit", has_clues=True),
    "pier": Setting(place="the windy pier", mood="breezy", has_clues=True),
    "garden": Setting(place="the garden path", mood="quiet", has_clues=True),
}

HERO_NAMES = ["Mina", "Leo", "Pip", "Nora", "Toby", "June"]
HELPER_NAMES = ["Ari", "Bea", "Finn", "Luz", "Milo", "Zara"]
SUSPECT_NAMES = ["Rex", "Mona", "Jett", "Vera", "Otto", "Cora"]

HERO_TYPES = {
    "girl": "girl",
    "boy": "boy",
}
HELPER_TYPES = {
    "girl": "girl",
    "boy": "boy",
}
SUSPECT_TYPES = {
    "girl": "girl",
    "boy": "boy",
}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, suspect: Entity) -> None:
    world.say(
        f"{hero.id} was a curious {hero.type} who loved a good adventure."
    )
    world.say(
        f"{hero.id}'s friend {helper.id} was patient, but {suspect.id} was a little egocentric and liked to be the center of every story."
    )


def bring_dime(world: World, hero: Entity) -> Entity:
    dime = world.add(Entity(
        id="dime",
        kind="thing",
        type="coin",
        label="dime",
        phrase="a shiny dime",
        owner=hero.id,
        location="pocket",
    ))
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"Before they left, {hero.id} took a shiny dime and said they would bring it along for luck."
    )
    return dime


def mystery_setup(world: World, hero: Entity, helper: Entity, suspect: Entity, dime: Entity) -> None:
    world.para()
    world.say(
        f"At {world.setting.place}, the three friends found a puzzle: the dime was gone from {hero.id}'s pocket, and nobody wanted the little mystery to stay unsolved."
    )
    world.say(
        f"{helper.id} bent down to look for tiny tracks, while {suspect.id} kept talking loudly about how they had probably noticed the clue first."
    )


def search_clues(world: World, helper: Entity) -> str:
    helper.memes["focus"] = helper.memes.get("focus", 0) + 1
    clue = "under a bench"
    world.say(
        f"{helper.id} listened instead of boasting, then found a faint glint under a bench."
    )
    return clue


def reveal(world: World, hero: Entity, helper: Entity, suspect: Entity, dime: Entity, clue: str) -> None:
    world.para()
    world.say(
        f"The glint was the dime, tucked {clue} after {suspect.id} had brushed past in a hurry."
    )
    world.say(
        f"{suspect.id} went quiet. The egocentric guessing had been wrong, and {helper.id}'s careful looking had solved the mystery."
    )
    world.say(
        f"{hero.id} smiled, picked up the dime, and thanked {helper.id} for helping without making it all about themselves."
    )


def ending(world: World, hero: Entity, helper: Entity, suspect: Entity) -> None:
    world.para()
    world.say(
        f"In the end, the friends walked on together through {world.setting.place}, with the dime safely in {hero.id}'s pocket and a better lesson shining brighter than the coin: an adventure goes farther when everyone shares the hunt."
    )


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    suspect = world.add(Entity(id=params.suspect_name, kind="character", type="boy"))

    intro(world, hero, helper, suspect)
    dime = bring_dime(world, hero)
    mystery_setup(world, hero, helper, suspect, dime)
    clue = search_clues(world, helper)
    reveal(world, hero, helper, suspect, dime, clue)
    ending(world, hero, helper, suspect)

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        dime=dime,
        clue=clue,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Questions / answers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short Adventure-style mystery story for children that includes the word "dime".',
        f"Tell a story where {hero.id} brings a dime on an outing, and {helper.id} helps solve a small mystery.",
        f'Write a simple story about an egocentric suspect and a clue hidden near a dime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who brought the dime along at {setting.place}?",
            answer=f"{hero.id} brought the dime along for luck."
        ),
        QAItem(
            question=f"Who solved the mystery by looking carefully instead of talking the most?",
            answer=f"{helper.id} solved the mystery by looking carefully."
        ),
        QAItem(
            question=f"Why was {suspect.id} important to the mystery?",
            answer=f"{suspect.id} was important because they were egocentric and had brushed past the spot where the dime ended up."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dime?",
            answer="A dime is a small coin."
        ),
        QAItem(
            question="What does it mean to be egocentric?",
            answer="An egocentric person pays too much attention to themselves and not enough to others."
        ),
        QAItem(
            question="What does it mean to bring something?",
            answer="To bring something means to carry it with you to a place."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
suspect(S) :- suspect_name(S).

egocentric(S) :- suspect(S), egocentric_name(S).
brought_dime(H) :- hero(H), carries_dime(H).
mystery_solved(H,He) :- brought_dime(H), helper(He), careful(He), found_dime(He).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("helper_name", "helper"))
    lines.append(asp.fact("suspect_name", "suspect"))
    lines.append(asp.fact("egocentric_name", "suspect"))
    lines.append(asp.fact("carries_dime", "hero"))
    lines.append(asp.fact("careful", "helper"))
    lines.append(asp.fact("found_dime", "helper"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery_solved/2. #show egocentric/1.")
    model = asp.one_model(program)
    sol = set(asp.atoms(model, "mystery_solved"))
    if ("hero", "helper") not in sol:
        print("MISMATCH: ASP twin did not recognize the mystery solution.")
        return 1
    print("OK: ASP twin recognizes the mystery solution.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style mystery about a dime.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    suspect_name = args.suspect or rng.choice(SUSPECT_NAMES)
    if hero_name == helper_name or hero_name == suspect_name or helper_name == suspect_name:
        raise StoryError("Please choose different names for the hero, helper, and suspect.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type="girl" if gender == "boy" else "boy",
        suspect_name=suspect_name,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
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
    StoryParams(place="lane", hero_name="Mina", hero_type="girl", helper_name="Ari", helper_type="boy", suspect_name="Rex"),
    StoryParams(place="pier", hero_name="Leo", hero_type="boy", helper_name="Bea", helper_type="girl", suspect_name="Mona"),
    StoryParams(place="garden", hero_name="June", hero_type="girl", helper_name="Finn", helper_type="boy", suspect_name="Vera"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/2. #show egocentric/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/2."))
        print(asp.atoms(model, "mystery_solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
