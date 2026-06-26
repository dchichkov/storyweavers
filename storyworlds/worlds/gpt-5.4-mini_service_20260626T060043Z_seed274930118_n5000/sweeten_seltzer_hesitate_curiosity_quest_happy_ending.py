#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero-style tale:
Curiosity opens a Quest, hesitation creates tension, and a Happy Ending
arrives when the hero learns how to sweeten seltzer without losing courage.

This world is intentionally small and constraint-checked. It models one child-
friendly comic-book domain with a few reusable parts:
- a hero with physical and emotional state
- a drink-making quest
- a moment of hesitation
- a satisfying happy ending image

The prose is state-driven rather than template-swapped: the story is built by
simulating a brief sequence of events in a world model and narrating the
resulting state changes.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Story ingredients
# ---------------------------------------------------------------------------
@dataclass
class Flavor:
    name: str
    sweetener: str
    base_drink: str = "seltzer"
    sparkle: str = "tiny bubbles"
    taste: str = "bright and fizzy"
    quest_verb: str = "sweeten"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    place: str
    flavor: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Milo", "Ari", "Zia", "Leo", "Tess", "Finn", "Mina"]
HELPER_NAMES = ["Beacon", "Comet", "Poppy", "Pulse", "Spark", "Orbit"]
HERO_TYPES = ["girl", "boy"]
PLACES = ["the rooftop lab", "the sunny kitchen", "the secret clubhouse"]
FLAVORS = {
    "strawberry": Flavor(name="strawberry", sweetener="honey", taste="sweet and fizzy"),
    "lemon": Flavor(name="lemon", sweetener="maple syrup", taste="bright and sweet"),
    "peach": Flavor(name="peach", sweetener="a swirl of sugar", taste="soft and sweet"),
}


class WorldState:
    def __init__(self, world: World, hero: Entity, helper: Entity, drink: Entity, flavor: Flavor) -> None:
        self.world = world
        self.hero = hero
        self.helper = helper
        self.drink = drink
        self.flavor = flavor
        self.fired: set[str] = set()

    def risk_level(self) -> float:
        return self.drink.meters.get("flat", 0.0) + self.hero.memes.get("hesitation", 0.0)

    def make_drink(self) -> None:
        self.drink.meters["sparkle"] = 1.0
        self.drink.meters["sweet"] = 1.0
        self.drink.meters["flat"] = 0.0
        self.hero.memes["joy"] = self.hero.memes.get("joy", 0.0) + 1.0
        self.world.say(
            f"{self.hero.id} poured a glass of {self.flavor.base_drink}, and the "
            f"{self.flavor.sparkle} danced like little stars."
        )

    def hesitate(self) -> None:
        self.hero.memes["hesitation"] = self.hero.memes.get("hesitation", 0.0) + 1.0
        self.world.say(
            f"{self.hero.id} held the spoon above the glass and hesitated."
        )
        self.world.say(
            f"{self.hero.pronoun().capitalize()} wanted the drink to be perfect, "
            f"but the first sip looked like a big decision."
        )

    def curiosity_calls(self) -> None:
        self.hero.memes["curiosity"] = self.hero.memes.get("curiosity", 0.0) + 1.0
        self.world.say(
            f"Then Curiosity in {self.hero.pronoun('possessive')} chest nudged "
            f"{self.hero.id} forward like a tiny superhero mask."
        )
        self.world.say(
            f"{self.hero.id} asked {self.helper.id}, 'What happens if we sweeten it just a little?'"
        )

    def quest_begins(self) -> None:
        self.helper.memes["helpful"] = self.helper.memes.get("helpful", 0.0) + 1.0
        self.world.say(
            f"{self.helper.id} smiled and called it a Quest: make the {self.flavor.base_drink} "
            f"{self.flavor.taste} without losing its sparkle."
        )

    def sweeten_seltzer(self) -> None:
        self.drink.meters["sweet"] = self.drink.meters.get("sweet", 0.0) + 1.0
        self.drink.meters["flat"] = max(0.0, self.drink.meters.get("flat", 0.0) - 1.0)
        self.world.say(
            f"So together they added {self.flavor.sweetener} one careful spoon at a time."
        )
        self.world.say(
            f"The {self.flavor.base_drink} stayed lively, and the bubbles kept popping."
        )

    def resolve(self) -> None:
        self.hero.memes["hesitation"] = 0.0
        self.hero.memes["joy"] = self.hero.memes.get("joy", 0.0) + 1.0
        self.hero.memes["pride"] = self.hero.memes.get("pride", 0.0) + 1.0
        self.world.say(
            f"{self.hero.id} took a brave sip and grinned. The drink was sweet, fizzy, "
            f"and just right."
        )
        self.world.say(
            f"That was the Happy Ending: {self.hero.id} and {self.helper.id} shared the "
            f"glass like a victory trophy, and the last bubbles winked in the light."
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Registry:
    places: dict[str, str]
    flavors: dict[str, Flavor]


REGISTRY = Registry(
    places={p: p for p in PLACES},
    flavors=FLAVORS,
)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is valid when the hero's curiosity can overcome hesitation and
% there is a flavorful way to sweeten seltzer without flattening it.
valid_story(P, F) :- place(P), flavor(F), possible(F).

possible(F) :- sweetener(F, _), base_drink(F, seltzer).
needs_curiosity(F) :- flavor(F).
happy_ending(F) :- possible(F), needs_curiosity(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in REGISTRY.places:
        lines.append(asp.fact("place", p))
    for name, flav in REGISTRY.flavors.items():
        lines.append(asp.fact("flavor", name))
        lines.append(asp.fact("sweetener", name, flav.sweetener))
        lines.append(asp.fact("base_drink", name, flav.base_drink))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, f) for p in REGISTRY.places for f in REGISTRY.flavors}
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python story gates:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> StorySample:
    flavor = REGISTRY.flavors[params.flavor]
    world = World(place=params.place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"spark": 0.0},
        memes={"curiosity": 0.0, "hesitation": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="friend",
        meters={},
        memes={"helpful": 0.0},
    ))
    drink = world.add(Entity(
        id="seltzer_glass",
        kind="thing",
        type="drink",
        label="glass of seltzer",
        phrase="a glass of fizzy seltzer",
        owner=hero.id,
        meters={"sparkle": 0.0, "sweet": 0.0, "flat": 0.0},
    ))

    state = WorldState(world, hero, helper, drink, flavor)

    world.say(
        f"In {params.place}, {hero.id} was a small {params.hero_type} superhero with a bright mind."
    )
    world.say(
        f"{hero.id} loved Curiosity because it made ordinary things feel like quests."
    )
    world.say(
        f"One day, {hero.id} found a cold glass of {flavor.base_drink} on the counter and wanted to "
        f"{flavor.name}-sweeten it."
    )

    world.para()
    state.make_drink()
    state.hesitate()
    state.curiosity_calls()
    state.quest_begins()

    world.para()
    state.sweeten_seltzer()
    state.resolve()

    world.facts.update(
        hero=hero,
        helper=helper,
        drink=drink,
        flavor=flavor,
        place=params.place,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
    )

    prompts = [
        f"Write a short superhero story about Curiosity leading a child through a Quest to sweeten seltzer.",
        f"Tell a gentle story where {params.hero_name} hesitates, then bravely makes {flavor.name} seltzer with {params.helper_name}.",
        f"Create a Happy Ending story set in {params.place} with bubbles, courage, and a little sweetness.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.hero_name} hesitate before adding the sweetener?",
            answer=(
                f"{params.hero_name} hesitated because {hero.pronoun()} wanted the seltzer to be perfect. "
                f"Curiosity helped {hero.pronoun('object')} take a brave step instead of staying frozen."
            ),
        ),
        QAItem(
            question=f"What was the Quest in the story?",
            answer=(
                f"The Quest was to sweeten the seltzer carefully so it tasted good while keeping its bubbles."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily: {params.hero_name} took a sip, smiled, and shared the sparkling drink with "
                f"{params.helper_name}."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is seltzer?",
            answer="Seltzer is plain fizzy water with bubbles in it.",
        ),
        QAItem(
            question="What does sweeten mean?",
            answer="To sweeten something means to make it taste sweeter, often by adding sugar, honey, or syrup.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes you want to learn, explore, and ask questions about new things.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny superhero storyworld about Curiosity, a Quest, and a Happy Ending."
    )
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flavor", choices=sorted(FLAVORS))
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    place = args.place or rng.choice(PLACES)
    flavor = args.flavor or rng.choice(sorted(FLAVORS))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != name] or HELPER_NAMES)

    if args.name and args.helper and args.name == args.helper:
        raise StoryError("The hero and helper should be different characters.")

    return StoryParams(
        hero_name=name,
        hero_type=gender,
        helper_name=helper,
        place=place,
        flavor=flavor,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(hero_name="Nova", hero_type="girl", helper_name="Beacon", place="the rooftop lab", flavor="strawberry"),
    StoryParams(hero_name="Milo", hero_type="boy", helper_name="Spark", place="the sunny kitchen", flavor="lemon"),
    StoryParams(hero_name="Zia", hero_type="girl", helper_name="Orbit", place="the secret clubhouse", flavor="peach"),
]


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_stories()
        print(f"{len(pairs)} compatible stories:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
