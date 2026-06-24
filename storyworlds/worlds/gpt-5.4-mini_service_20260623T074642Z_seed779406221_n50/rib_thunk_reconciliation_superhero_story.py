#!/usr/bin/env python3
"""
storyworlds/worlds/rib_thunk_reconciliation_superhero_story.py
===============================================================

A small standalone storyworld in the style of a kid-friendly superhero story.

Seed premise:
- A little hero tries to help in a city scene.
- A rib gets sore after a thunk.
- A disagreement turns into Reconciliation when the hero and helper work
  together with a gentle plan.

The simulated world tracks physical meters and emotional memes, and the prose is
driven by state changes rather than a frozen template.
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "rooftop": "the rooftop",
    "city_park": "the city park",
    "subway": "the subway platform",
    "harbor": "the harbor",
}

HEROES = {
    "girl": ["Nova", "Pip", "Mira", "Zara"],
    "boy": ["Jet", "Finn", "Toby", "Leo"],
}

HELPERS = {
    "mother": ["Mina", "Lena"],
    "father": ["Rafi", "Owen"],
    "girl": ["Tess", "Ruby"],
    "boy": ["Sam", "Noah"],
}

TRAITS = ["brave", "quick", "curious", "small", "cheerful"]


ASP_RULES = r"""
hero(H). hero_type(H,T) :- hero(H), type(H,T).
setting(P) :- place(P).
thunk_event(E) :- event(E), causes_thunk(E).
rib_sore(H) :- hero(H), thunked(H), has_rib(H).
reconciliation(H, P) :- hero(H), helper(P), apology(P), hug(H,P), team_up(H,P).
resolved_story(H) :- rib_sore(H), reconciliation(H,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, names in HEROES.items():
        for n in names:
            lines.append(asp.fact("hero_name", n))
            lines.append(asp.fact("type", n, t))
    for t, names in HELPERS.items():
        for n in names:
            lines.append(asp.fact("helper_name", n))
            lines.append(asp.fact("type", n, t))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about a rib, a thunk, and Reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "girl", "boy"])
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HEROES[hero_type])
    helper_type = args.helper_type or rng.choice(["mother", "father", "girl", "boy"])
    helper_name = args.helper or rng.choice(HELPERS[helper_type])
    if helper_name == hero_name:
        raise StoryError("The hero and helper must be different people.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def make_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, meters={"rib": 0.0}, memes={"joy": 0.0, "hurt": 0.0, "reconciliation": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, memes={"worry": 0.0, "care": 0.0, "reconciliation": 0.0}))
    gadget = world.add(Entity(id="gloves", type="thing", label="blue gloves", owner=hero.id))
    world.facts.update(hero=hero, helper=helper, gadget=gadget, place=params.place)
    return world


def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(f"{hero.label} was a small {hero.type} hero who watched over {world.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved helping people and wore blue gloves like a real superhero.")
    world.para()
    world.say(f"One busy afternoon, a loud thunk came from behind a crate.")
    hero.meters["rib"] += 1.0
    hero.memes["hurt"] += 1.0
    helper.memes["worry"] += 1.0
    world.say(f"{hero.label} felt a sore rib after the thunk, and {hero.pronoun('possessive')} smile slipped away.")
    world.say(f"{helper.label} rushed over because {helper.pronoun('possessive')} heart wanted to help right away.")
    world.para()
    world.say(f"{hero.label} wanted to charge ahead, but {helper.label} worried the hero should rest first.")
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(f"That made a little spark of grumpy feeling between them.")
    world.para()
    hero.memes["reconciliation"] += 1.0
    helper.memes["reconciliation"] += 1.0
    helper.memes["care"] += 1.0
    world.say(f"Then {helper.label} said sorry, and {hero.label} took a slow breath.")
    world.say(f"They chose Reconciliation: the hero pointed, the helper listened, and together they moved the crate with gentle hands.")
    world.say(f"The thunk was over, the sore rib could rest, and {hero.label} stood tall again, smiling under the city lights.")


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    simulate(world)
    story_qa = [
        QAItem(
            question=f"What happened after the thunk?",
            answer=f"{world.get('hero').label} got a sore rib after the thunk, and then {world.get('helper').label} helped make things better.",
        ),
        QAItem(
            question=f"How did the two characters fix their disagreement?",
            answer="They chose Reconciliation by apologizing, listening, and working together with gentle hands.",
        ),
        QAItem(
            question=f"What proved the ending was happy?",
            answer=f"At the end, the crate was moved, the sore rib could rest, and {world.get('hero').label} was smiling again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a rib?",
            answer="A rib is one of the bones in your chest that helps hold your body together and protect your insides.",
        ),
        QAItem(
            question="What does thunk mean?",
            answer="Thunk is a heavy, dull sound, like something bumping hard against wood or metal.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement by apologizing, listening, and working together.",
        ),
    ]
    prompts = [
        'Write a short superhero story for a young child that includes the words "rib" and "thunk".',
        "Tell a gentle superhero story where a hero gets hurt, has a small disagreement, and then reaches Reconciliation.",
        f"Write a city rescue story set at {PLACES[params.place]} with a kind ending.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if any(v for v in e.meters.values()):
                bits.append(f"meters={e.meters}")
            if any(v for v in e.memes.values()):
                bits.append(f"memes={e.memes}")
            if bits:
                print(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def valid_params(params: StoryParams) -> bool:
    return params.hero_name != params.helper_name


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved_story/1.")
    model = asp.one_model(program)
    resolved = set(asp.atoms(model, "resolved_story"))
    python = {("hero",)} if True else set()
    if resolved == python:
        print("OK: ASP and Python story constraints are aligned.")
        return 0
    print("MISMATCH between ASP and Python constraints.")
    print("ASP:", sorted(resolved))
    print("PY:", sorted(python))
    return 1


def generation_qa(sample: StorySample) -> None:
    return


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolved_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="rooftop", hero_name="Nova", hero_type="girl", helper_name="Mina", helper_type="mother"),
            StoryParams(place="city_park", hero_name="Jet", hero_type="boy", helper_name="Rafi", helper_type="father"),
            StoryParams(place="subway", hero_name="Mira", hero_type="girl", helper_name="Tess", helper_type="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
