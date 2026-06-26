#!/usr/bin/env python3
"""
storyworlds/worlds/ramen_reference_kindness_conflict_bravery_whodunit.py
=========================================================================

A small whodunit-style storyworld about a ramen shop, a missing reference card,
and the brave, kind way a conflict gets solved.

Seed idea:
- A child visits a ramen shop that keeps a little reference notebook of orders.
- Something important goes missing right before dinner rush.
- The child notices clues, faces a tense moment, and bravely tells the truth.
- Kindness resolves the conflict and reveals the answer.

This script keeps the simulation small and concrete:
- physical meters: carried, hidden, spilled, warm, neat
- emotional memes: curiosity, conflict, kindness, bravery, relief, trust

The story is generated from world state, not from a frozen template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ramen shop"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    clue_word: str = ""


@dataclass
class CharacterCfg:
    name: str
    type: str
    role: str  # "kid" | "cook" | "parent"


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ramen_shop": Setting(place="the ramen shop", affords={"service", "cleanup", "search"}),
    "back_room": Setting(place="the back room", affords={"search", "cleanup"}),
}

OBJECTS = {
    "reference_card": ObjectCfg(
        label="reference card",
        phrase="a small reference card with the order marks",
        region="table",
        clue_word="reference",
    ),
    "ladle": ObjectCfg(
        label="ladle",
        phrase="the long soup ladle",
        region="hand",
        clue_word="ramen",
    ),
    "recipe_book": ObjectCfg(
        label="recipe book",
        phrase="the old reference book with noodle notes",
        region="shelf",
        clue_word="reference",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Aya", "Tori", "Nori"]
BOY_NAMES = ["Ken", "Sora", "Jin", "Riku", "Owen"]
HELPERS = [
    CharacterCfg(name="Chef Hana", type="woman", role="cook"),
    CharacterCfg(name="Dad", type="father", role="parent"),
    CharacterCfg(name="Mom", type="mother", role="parent"),
]

# ---------------------------------------------------------------------------
# Helper narration
# ---------------------------------------------------------------------------

def article(phrase: str) -> str:
    first = phrase.strip()[0].lower()
    return "an" if first in "aeiou" else "a"


def act_hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who liked to look closely at tiny clues."
    )


def act_setting(world: World) -> None:
    world.say(
        "The ramen shop was warm, with steam on the windows and little red bowls on the counter."
    )


def act_love_ramen(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved ramen, especially the smell of broth and noodles."
    )


def act_reference(world: World, obj: Entity) -> None:
    world.say(
        f"On the counter sat {article(obj.phrase)} {obj.phrase}, neat and ready for the dinner rush."
    )


def act_disappearance(world: World, obj: Entity, helper: Entity) -> None:
    obj.hidden_in = "under the tray"
    obj.meters["hidden"] = obj.meters.get("hidden", 0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1
    world.say(
        f"Then the {obj.label} slipped out of sight, and {helper.id} frowned because the next order had no mark."
    )


def act_search_clue(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} noticed a little trail of flour near the tray and looked under it."
    )
    if obj.hidden_in == "under the tray":
        world.say(
            f"Sure enough, the {obj.label} was tucked safely under there."
        )


def act_conflict(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1
    world.say(
        f"{helper.id} looked worried, because without the {obj.label} the kitchen could mix up the ramen orders."
    )
    world.say(
        f"{hero.id} wanted to help, but the room felt tense for a moment."
    )


def act_bravery(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"Bravely, {hero.id} pointed to the tray and said, \"I think the {obj.label} is under there.\""
    )


def act_kindness(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{helper.id} smiled, thanked {hero.id}, and lifted the tray gently."
    )


def act_resolution(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    obj.hidden_in = None
    obj.meters["hidden"] = 0
    world.say(
        f"The {obj.label} came back to the counter, the next bowl was served correctly, and the whole shop felt calm again."
    )
    world.say(
        f"{hero.id} watched the steam rise from a fresh bowl of ramen, feeling proud of being both kind and brave."
    )


def make_story(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    act_hero_intro(world, hero)
    act_setting(world)
    act_love_ramen(world, hero)
    act_reference(world, obj)
    world.para()
    act_disappearance(world, obj, helper)
    act_search_clue(world, hero, obj)
    act_conflict(world, hero, helper, obj)
    act_bravery(world, hero, helper, obj)
    world.para()
    act_kindness(world, hero, helper, obj)
    act_resolution(world, hero, helper, obj)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place,Object,HelperType) :- place(Place), obj(Object), helper(HelperType), setup_ok(Place,Object).
valid_story(Place,Object,HeroType,HelperType) :- valid(Place,Object,HelperType), hero(HeroType), hero_ok(HeroType,Object).

setup_ok(Place,Object) :- affords(Place,search), clue(Object).
hero_ok(girl,reference_card).
hero_ok(boy,reference_card).
hero_ok(girl,recipe_book).
hero_ok(boy,recipe_book).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        lines.append(asp.fact("clue", oid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.type))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("hero", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for obj in OBJECTS:
            for helper in {"woman", "father", "mother"}:
                out.append((place, obj, helper))
    return out


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper = rng.choice(HELPERS)
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    if not SETTINGS[place].affords or "search" not in SETTINGS[place].affords:
        raise StoryError("This setting cannot support the search needed for a whodunit.")

    return StoryParams(
        place=place,
        object=obj,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper.name,
        helper_type=helper.type,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    obj = world.add(Entity(
        id=params.object,
        type=params.object,
        label=OBJECTS[params.object].label,
        phrase=OBJECTS[params.object].phrase,
        owner=params.helper_name,
        caretaker=params.helper_name,
        hidden_in=None,
    ))
    world.facts.update(hero=hero, helper=helper, obj=obj, params=params)
    make_story(world, hero, helper, obj)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short whodunit for children that includes "{p.object}" and ramen.',
        f"Tell a gentle mystery where {p.hero_name} notices a missing {OBJECTS[p.object].label} at {SETTINGS[p.place].place}.",
        f"Write a simple story about kindness, conflict, and bravery in a ramen shop.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["obj"]
    return [
        QAItem(
            question=f"Who found the clue in the ramen shop?",
            answer=f"{hero.id} found the clue by noticing the flour trail under the tray.",
        ),
        QAItem(
            question=f"What was missing when the conflict started?",
            answer=f"The {obj.label} slipped out of sight, and that made the next ramen order hard to read.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} bravely pointed to where the {obj.label} was hidden and said what {hero.pronoun('subject')} thought.",
        ),
        QAItem(
            question=f"How did the story end for {helper.id} and {hero.id}?",
            answer=f"{helper.id} thanked {hero.id}, and the shop became calm again after the {obj.label} was put back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ramen?",
            answer="Ramen is a bowl of noodles in broth, often served hot with tasty toppings.",
        ),
        QAItem(
            question="What is a reference book for?",
            answer="A reference book helps people look up facts, names, or instructions quickly.",
        ),
        QAItem(
            question="What does kindness do in a problem?",
            answer="Kindness helps people speak gently, listen, and work together to solve a problem.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement that makes people tense until it is solved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly ramen-shop whodunit.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with hero type):\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("ramen_shop", "reference_card", "Mina", "girl", "Chef Hana"),
            StoryParams("ramen_shop", "recipe_book", "Ken", "boy", "Dad"),
            StoryParams("back_room", "reference_card", "Aya", "girl", "Mom"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
