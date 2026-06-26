#!/usr/bin/env python3
"""
A small superhero storyworld with sound effects, an ewok helper, and binoculars.

Seed premise:
- A brave hero watches a city with binoculars.
- A tiny ewok sidekick spots trouble and makes sound effects.
- A villain named Putz causes a problem.
- The hero uses a gadget and teamwork to save the day.

This script builds a compact simulation and emits a complete story plus QA.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaking: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    action: str
    helps_against: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    villain_name: str
    threat: str
    gadget: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


PLACES = {
    "city_rooftop": Place("the city rooftop", {"watch", "spot", "rescue"}),
    "moon_bridge": Place("the moon bridge", {"watch", "spot", "rescue"}),
    "harbor_tower": Place("the harbor tower", {"watch", "spot", "rescue"}),
}

THREATS = {
    "smoke": "a smoky cloud",
    "slippery": "a slippery spill",
    "alarm": "a ringing alarm",
}

GADGETS = {
    "binoculars": Gadget(
        id="binoculars",
        label="binoculars",
        phrase="a pair of shiny binoculars",
        action="looked through the binoculars",
        helps_against={"spot"},
    ),
    "grappler": Gadget(
        id="grappler",
        label="grappling hook",
        phrase="a small grappling hook",
        action="swung the grappling hook",
        helps_against={"rescue"},
    ),
    "sound_sprayer": Gadget(
        id="sound_sprayer",
        label="sound sprayer",
        phrase="a pocket sound sprayer",
        action="made brave sound effects",
        helps_against={"alarm"},
    ),
}

HEROES = ["Mira", "Juno", "Kite", "Nia", "Bo", "Tess"]
EWOK_NAMES = ["Wik", "Tee", "Pip", "Ruu", "Mok"]
VILLAINS = ["Putz", "Drift", "Crank", "Hush"]
TRAITS = ["brave", "quick", "kind", "clever", "steady"]


def sound_effect_for(threat: str) -> str:
    return {
        "smoke": "Whooosh!",
        "slippery": "Skkrrt!",
        "alarm": "Bing-bing-bong!",
    }.get(threat, "Zap!")


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["super"]))

    ewok = world.add(Entity(id=params.helper_name, kind="character", type="ewok", label="the ewok helper"))
    villain = world.add(Entity(id=params.villain_name, kind="character", type="villain", label=params.villain_name))

    gadget = world.add(Entity(
        id=params.gadget,
        type="gadget",
        label=GADGETS[params.gadget].label,
        phrase=GADGETS[params.gadget].phrase,
        owner=hero.id,
        worn_by=hero.id if params.gadget == "binoculars" else None,
        carried_by=hero.id,
    ))

    hero.meters["alertness"] = 1
    ewok.meters["noise"] = 0
    villain.meters["trouble"] = 1
    world.facts.update(hero=hero, ewok=ewok, villain=villain, gadget=gadget)

    world.say(f"{hero.id} stood on {world.place.name} and kept watch for trouble.")
    world.say(f"{hero.pronoun().capitalize()} held {gadget.phrase} close, ready to scan the sky.")
    world.say(f"Beside {hero.pronoun('object')}, {ewok.id} the ewok helper bounced on tiny feet and whispered, \"Putz is up to something.\"")
    world.say(f"The ewok made a soft sound effect: \"{sound_effect_for(params.threat)}\"")

    world.para()
    world.say(f"Then {villain.id} caused {THREATS[params.threat]} near the {world.place.name}.")
    world.say(f"{hero.id} {GADGETS[params.gadget].action} and spotted the trouble right away.")

    if params.gadget == "binoculars":
        world.say(f"The binoculars helped {hero.id} see past the smoke and find the right path.")
    else:
        world.say(f"The gadget helped {hero.id} stay focused while the city buzzed with worry.")

    world.para()
    world.say(f"{ewok.id} shouted, \"{sound_effect_for(params.threat)}\" and pointed at the safest spot.")
    world.say(f"{hero.id} sprang into action, caught the problem, and stopped {villain.id} before anyone got hurt.")
    world.say(f"In the end, the sky was calm again, and {ewok.id} smiled at the shining binoculars.")

    world.facts["threat"] = params.threat
    world.facts["place"] = params.place
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with sound effects and an ewok helper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-name", choices=EWOK_NAMES)
    ap.add_argument("--villain-name", choices=VILLAINS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gadget", choices=GADGETS)
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.hero_name or rng.choice(HEROES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_name = args.helper_name or rng.choice(EWOK_NAMES)
    villain_name = args.villain_name or "Putz"
    threat = args.threat or rng.choice(list(THREATS))
    gadget = args.gadget or "binoculars"
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        villain_name=villain_name,
        threat=threat,
        gadget=gadget,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "putz" and the sound "{sound_effect_for(f["threat"])}".',
        f"Tell a story where {f['hero'].id} uses binoculars, an ewok helper, and brave teamwork to stop Putz.",
        f"Write a simple rescue story with a clear problem, a noisy helper, and a happy ending at {PLACES[f['place']].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    ewok: Entity = f["ewok"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who watched for trouble at {PLACES[f['place']].name}?",
            answer=f"{hero.id} watched for trouble there and used binoculars to spot what was wrong.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with sound effects?",
            answer=f"The ewok helper named {ewok.id} helped by calling out \"{sound_effect_for(f['threat'])}\".",
        ),
        QAItem(
            question=f"Who caused the trouble in the story?",
            answer=f"The villain named {villain.id} caused the trouble, and everyone had to work together to stop it.",
        ),
        QAItem(
            question=f"What did the binoculars help {hero.id} do?",
            answer=f"The binoculars helped {hero.id} look far away and find the problem quickly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are binoculars for?",
            answer="Binoculars help you see things that are far away more clearly.",
        ),
        QAItem(
            question="What is an ewok?",
            answer="An ewok is a small furry space helper from a story world, and it can be a brave friend.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like boom, zap, or whoosh that help a story feel exciting.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(E) :- ewok(E).
villain(V) :- villain_name(V).
tool(G) :- gadget(G).
helps(G, spot) :- gadget(G), g_helps(G, spot).
helps(G, rescue) :- gadget(G), g_helps(G, rescue).
helps(G, alarm) :- gadget(G), g_helps(G, alarm).
compatible_story(P, T, G) :- place(P), threat(T), gadget(G), affords(P, watch), helps(G, spot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for a in sorted(PLACES[p].affordances):
            lines.append(asp.fact("affords", p, a))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for g, gd in GADGETS.items():
        lines.append(asp.fact("gadget", g))
        for h in sorted(gd.helps_against):
            lines.append(asp.fact("g_helps", g, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    python_set = {(p, t, g) for p in PLACES for t in THREATS for g in GADGETS if p in PLACES and g == "binoculars"}
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/3."))
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("city_rooftop", "Mira", "girl", "Wik", "Putz", "smoke", "binoculars"),
            StoryParams("moon_bridge", "Juno", "boy", "Tee", "Putz", "slippery", "binoculars"),
            StoryParams("harbor_tower", "Nia", "girl", "Pip", "Putz", "alarm", "binoculars"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
