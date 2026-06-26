#!/usr/bin/env python3
"""
storyworlds/worlds/commemorate_pizzeria_gasoline_happy_ending_rhyming_story.py
==============================================================================

A small story world about a happy pizzeria celebration with one safety worry:
gasoline.

Seed tale:
---
Nina and her dad were helping the little pizzeria on Maple Street celebrate a
big day. They wanted to commemorate the grand opening with music, streamers,
and a bright little party. But then Nina noticed a strong gasoline smell by the
back door, where a delivery cart had been parked beside a lawn tool.

Dad said they could not keep the fuel near the party, because gasoline is not
for kids and should stay far away from flames, food, and feet. Nina felt sad
for a moment, then she found a safer idea: move the gasoline can to the shed,
sweep the doorway clean, and hang shiny paper stars instead of anything that
could burn.

Soon the pizzeria glowed with warm lanterns, the smell was gone, and the grand
opening became a cheerful rhyme-filled celebration.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    indoors: bool = True
    bright: bool = True
    rhyme_word: str = ""


@dataclass
class Hazard:
    id: str
    label: str
    smell: str
    risk: str
    safe_action: str
    avoid: str
    can_touch: bool = False


@dataclass
class SafeChoice:
    id: str
    label: str
    action: str
    effect: str


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.alerts: list[str] = []

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


LOCATIONS = {
    "pizzeria": Location(name="the pizzeria", indoors=True, bright=True, rhyme_word="pizza"),
    "patio": Location(name="the patio by the pizzeria", indoors=False, bright=True, rhyme_word="glow"),
    "kitchen": Location(name="the kitchen", indoors=True, bright=True, rhyme_word="yummy"),
}

HAZARDS = {
    "gasoline": Hazard(
        id="gasoline",
        label="gasoline",
        smell="sharp and strong",
        risk="can burn near sparks or flames",
        safe_action="move the gasoline far away from the party",
        avoid="keep it away from candles, ovens, and paper decorations",
        can_touch=False,
    ),
}

SAFE_CHOICES = {
    "shed": SafeChoice(
        id="shed",
        label="the shed",
        action="move the gasoline can to the shed",
        effect="the fuel was out of the way",
    ),
    "lanterns": SafeChoice(
        id="lanterns",
        label="paper lanterns",
        action="hang paper lanterns instead of anything flame-like",
        effect="the room stayed bright and safe",
    ),
    "stars": SafeChoice(
        id="stars",
        label="shiny paper stars",
        action="decorate with shiny paper stars",
        effect="the party looked festive without any sparks",
    ),
}


@dataclass
class StoryParams:
    location: str
    hazard: str
    hero: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(location="pizzeria", hazard="gasoline", hero="Nina", helper="Dad"),
    StoryParams(location="patio", hazard="gasoline", hero="Milo", helper="Mom"),
]


GIRL_NAMES = ["Nina", "Mina", "Lila", "Ruby", "Tia", "Zoe"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Leo", "Sam", "Noah"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming happy-ending story world about a pizzeria celebration and a safety fix."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    location = args.location or rng.choice(list(LOCATIONS))
    hazard = args.hazard or "gasoline"
    if hazard != "gasoline":
        raise StoryError("This world only models gasoline as the safety concern.")
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(["Mom", "Dad", "Aunt", "Uncle"])
    return StoryParams(location=location, hazard=hazard, hero=hero, helper=helper)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_world(params: StoryParams) -> World:
    world = World(LOCATIONS[params.location])
    hero_type = "girl" if params.hero in GIRL_NAMES else "boy"
    helper_type = "mother" if params.helper == "Mom" else "father" if params.helper == "Dad" else "aunt" if params.helper == "Aunt" else "uncle"

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero, traits=["cheerful", "curious"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    pizzeria = world.add(Entity(id="pizzeria", type="place", label="pizzeria", location=params.location))
    gas = world.add(Entity(id="gas", type="thing", label="gasoline can", phrase="a gasoline can", owner=helper.id, caretaker=helper.id, location="back door"))
    banner = world.add(Entity(id="banner", type="thing", label="party banner", phrase="a bright party banner", owner=hero.id, caretaker=helper.id, location="front window"))
    world.facts.update(hero=hero, helper=helper, pizzeria=pizzeria, gas=gas, banner=banner)
    return world


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    loc = world.location.name
    world.say(
        f"{hero.label} and {helper.label} came to {loc} to commemorate a grand opening, with a clap and a cheer and a happy tune."
    )
    world.say(
        f"They planned a little celebration, bright and light, with pizza, posters, and rhymes that felt just right."
    )


def detect_hazard(world: World) -> None:
    gas = world.facts["gas"]
    hero = world.facts["hero"]
    gas.meters["smell"] = 1.0
    hero.memes["unease"] = 1.0
    world.say(
        f"Then {hero.label} sniffed the air and frowned a bit: {HAZARDS['gasoline'].smell} gasoline sat by the back door, not fit."
    )


def warning(world: World) -> None:
    helper = world.facts["helper"]
    world.say(
        f"{helper.label} said, \"Gasoline must stay away; it can {HAZARDS['gasoline'].risk}, so let's move it out today.\""
    )
    world.say(
        f"\"We'll keep it from the oven, the candles, and the cart, so the happy little party can keep its sparkling heart.\""
    )


def safe_turn(world: World) -> None:
    hero = world.facts["hero"]
    gas = world.facts["gas"]
    helper = world.facts["helper"]
    choice = SAFE_CHOICES["shed"]
    choice2 = SAFE_CHOICES["lanterns"]
    gas.location = choice.label
    gas.meters["smell"] = 0.0
    hero.memes["joy"] = 1.0
    hero.memes["pride"] = 1.0
    world.say(
        f"{hero.label} found a better plan with a little gleam: {choice.action}, and that made a neat team."
    )
    world.say(
        f"Then {helper.label} helped with {choice2.action}, and soon the room was glowing in a lantern dream."
    )


def ending(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    world.say(
        f"The pizzeria shone with paper stars, and pizza smelled sweet, while the gasoline stayed hidden and safe from the heat."
    )
    world.say(
        f"So the celebration ended happy and bright: {hero.label} and {helper.label} laughed together in the warm, soft light."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    detect_hazard(world)
    warning(world)
    world.para()
    safe_turn(world)
    ending(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        'Write a short rhyming story for a child about a pizzeria celebration and a safe fix for gasoline.',
        f"Tell a happy-ending rhyme where {hero.label} and {helper.label} commemorate a pizzeria opening, notice gasoline, and choose a safe way to celebrate.",
        "Write a simple rhyming story with pizza, party decorations, and a careful move that keeps gasoline away from flames.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    gas = world.facts["gas"]
    return [
        QAItem(
            question=f"Who helped {hero.label} celebrate at the pizzeria?",
            answer=f"{helper.label} helped {hero.label} celebrate at the pizzeria and kept the party safe."
        ),
        QAItem(
            question="What safety problem did they notice?",
            answer="They noticed gasoline by the back door, and gasoline must stay far away from flames, candles, and ovens."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="They moved the gasoline can to the shed and used paper lanterns and paper stars instead."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the pizzeria bright, the gasoline out of the way, and everyone smiling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pizzeria?",
            answer="A pizzeria is a place where people make and sell pizza."
        ),
        QAItem(
            question="What is gasoline?",
            answer="Gasoline is a fuel used in some machines and vehicles, and it should be kept away from flames and children."
        ),
        QAItem(
            question="Why are paper decorations safer than flames at a party?",
            answer="Paper decorations can look bright and festive without making sparks or heat."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A gasoline hazard is story-worthy when it is near the celebration.
hazard_present(H) :- hazard(H), smell_near(H).

% A fix is compatible when it moves the hazard away and avoids flames.
safe_fix(C) :- choice(C), moves_away(C), no_flames(C).

valid_story(L,H,C) :- location(L), hazard_present(H), safe_fix(C), can_celebrate(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc.indoors:
            lines.append(asp.fact("can_celebrate", loc_id))
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("smell_near", hid))
    for cid, ch in SAFE_CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("moves_away", cid))
        lines.append(asp.fact("no_flames", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(loc, "gasoline", choice) for loc in LOCATIONS for choice in SAFE_CHOICES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            samples.append(generate(params))

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
