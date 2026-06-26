#!/usr/bin/env python3
"""
Porridge Kindness Pirate Tale
==============================

A small standalone storyworld about a pirate crew, a bowl of porridge, and a
kind act that turns a grumbly morning into a better one.

The world is intentionally tiny:
- a captain or shipmate wants porridge
- something about the porridge situation goes wrong
- kindness changes the state of the crew
- the ending proves the change with a concrete image
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ship"
    aboard: bool = True
    affords: set[str] = field(default_factory=lambda: {"porridge", "storm", "share"})


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    warmth: str
    sweetness: str
    mess: str
    emoji: str = ""


@dataclass
class StoryParams:
    setting: str
    food: str
    hero: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the ship", aboard=True, affords={"porridge", "share"}),
    "dock": Setting(place="the dock", aboard=False, affords={"porridge", "share"}),
    "cabin": Setting(place="the captain's cabin", aboard=True, affords={"porridge", "share"}),
}

FOODS = {
    "porridge": Food(
        id="porridge",
        label="porridge",
        phrase="a warm bowl of porridge",
        warmth="warm",
        sweetness="sweet",
        mess="sticky",
        emoji="🥣",
    ),
}

HERO_NAMES = ["Molly", "Tessa", "Ned", "Finn", "Ruby", "Jory", "Pip", "Sailor", "Mara", "Ben"]
CAPTAIN_NAMES = ["Captain Salt", "Captain Bluebeard", "Captain Tilly", "Captain Rook"]
TRAITS = ["brave", "kind", "cheerful", "sly", "curious", "stubborn"]


# ---------------------------------------------------------------------------
# Contract helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def valid_combos() -> list[tuple[str, str]]:
    return [(s, f) for s in SETTINGS for f in FOODS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.food not in FOODS:
        raise StoryError("Unknown food.")
    if params.food != "porridge":
        raise StoryError("This storyworld is about porridge.")
    if params.captain == params.hero:
        raise StoryError("The hero and captain must be different characters.")


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _story_intro(world: World) -> None:
    hero = world.get("hero")
    cap = world.get("captain")
    food = world.get("porridge")
    world.say(
        f"{hero.id} was a {hero.traits[0]} little pirate who liked the smell of breakfast on deck."
    )
    world.say(
        f"{cap.id} kept {hero.pronoun('possessive')} {food.label} close, because a pirate day felt better with a full belly."
    )


def _offer_porridge(world: World) -> None:
    hero = world.get("hero")
    cap = world.get("captain")
    food = world.get("porridge")
    world.say(
        f"One morning, {hero.id} climbed up to {world.setting.place} and found {cap.id} holding {food.phrase}."
    )
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to eat {food.label} right away.")


def _problem(world: World) -> None:
    hero = world.get("hero")
    cap = world.get("captain")
    food = world.get("porridge")
    hero.memes["grumble"] = hero.memes.get("grumble", 0.0) + 1
    food.meters["spoon"] = food.meters.get("spoon", 0.0) + 1
    world.say(
        f"But the porridge was meant for the whole crew, and the biggest spoon was missing."
    )
    world.say(
        f"{hero.id} frowned and stared at the bowl, while {cap.id} looked out at the deck and thought."
    )


def _kindness_turn(world: World) -> None:
    hero = world.get("hero")
    cap = world.get("captain")
    food = world.get("porridge")
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    cap.memes["relief"] = cap.memes.get("relief", 0.0) + 1
    food.meters["shared"] = food.meters.get("shared", 0.0) + 1
    if "kindness" in world.facts:
        pass
    world.say(
        f"Then {hero.id} found a little ladle, smiled, and said, 'I can share.'"
    )
    world.say(
        f"{hero.id} scooped the porridge into smaller bowls so nobody had to wait."
    )


def _resolution(world: World) -> None:
    hero = world.get("hero")
    cap = world.get("captain")
    food = world.get("porridge")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    cap.memes["joy"] = cap.memes.get("joy", 0.0) + 1
    world.say(
        f"That made {cap.id} grin, and the whole deck felt warmer than the morning sun."
    )
    world.say(
        f"Before long, {hero.id} was eating {food.label} with a happy crew, and the empty bowl shone like treasure."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.hero, kind="character", type="pirate", traits=[params.trait, "little"]
    ))
    captain = world.add(Entity(
        id=params.captain, kind="character", type="captain", traits=["gruff", "kind"]
    ))
    porridge = world.add(Entity(
        id="porridge", type="food", label="porridge", phrase="a warm bowl of porridge"
    ))
    hero.memes["kindness"] = 0.0
    captain.memes["kindness"] = 0.0
    world.facts.update(hero=hero, captain=captain, porridge=porridge, params=params)

    _story_intro(world)
    world.para()
    _offer_porridge(world)
    _problem(world)
    world.para()
    _kindness_turn(world)
    _resolution(world)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short pirate story for children about {p.hero}, {p.captain}, and porridge.",
        "Tell a gentle tale where kindness helps a hungry pirate crew share breakfast.",
        "Make the ending show the porridge being shared instead of wasted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who wanted the porridge in this pirate story?",
            answer=f"{p.hero} wanted the porridge, but the bowl was meant for the whole crew.",
        ),
        QAItem(
            question=f"What problem happened before the kindness part?",
            answer="The biggest spoon was missing, so the porridge could not be served easily at first.",
        ),
        QAItem(
            question="What did the hero do that changed the mood?",
            answer=f"{p.hero} found a little ladle and shared the porridge into smaller bowls.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The crew ate together happily, and the empty bowl shone like treasure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is porridge?",
            answer="Porridge is soft food made by cooking grains in water or milk until it becomes thick and warm.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or be gentle with someone else.",
        ),
        QAItem(
            question="What is a pirate crew?",
            answer="A pirate crew is a group of sailors who work together on a ship.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(ship).
setting(dock).
setting(cabin).

food(porridge).

valid_story(S,F) :- setting(S), food(F), F = porridge.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Porridge, kindness, and a pirate crew.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--food", choices=FOODS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--captain")
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    food = args.food or "porridge"
    hero = args.hero or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    if hero == captain:
        captain = rng.choice([c for c in CAPTAIN_NAMES if c != hero])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, food=food, hero=hero, captain=captain, trait=trait)
    reasonableness_gate(params)
    return params


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(setting="ship", food="porridge", hero="Molly", captain="Captain Salt", trait="kind"),
            StoryParams(setting="dock", food="porridge", hero="Ned", captain="Captain Bluebeard", trait="brave"),
            StoryParams(setting="cabin", food="porridge", hero="Mara", captain="Captain Tilly", trait="cheerful"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
