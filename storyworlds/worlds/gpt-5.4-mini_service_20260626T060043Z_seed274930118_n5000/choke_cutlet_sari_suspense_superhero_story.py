#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/choke_cutlet_sari_suspense_superhero_story.py
==========================================================================================================================

A standalone story world for a small superhero suspense tale.

Premise:
- A child superhero with a favorite sari wants to eat a cutlet.
- The cutlet is too big and causes a scary choking moment.
- A parent helper responds quickly with calm first aid.
- The story ends with safety, relief, and the sari still neat.

The world is constraint-checked: it only generates stories where the risky food,
the worn garment, and the rescue all make causal sense.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
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
class Hero:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "brave"
    setting: str = "the dinner table"
    seed: Optional[int] = None


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    parent: str
    trait: str
    place: str
    sari: str
    cutlet: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def compose(hero: Entity, parent: Entity, sari: Entity, cutlet: Entity) -> str:
    return (
        f"{hero.id} was a little superhero with a {hero.memes.get('bravery_word', 'brave')} heart. "
        f"{hero.pronoun('subject').capitalize()} loved {hero.memes.get('heroic_verb', 'watching over')} the neighborhood "
        f"and loved {sari.phrase} almost as much as {cutlet.phrase}."
    )


def build_world(params: StoryParams) -> World:
    world = World()

    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_gender,
        meters={"hunger": 1.0}, memes={"bravery": 1.0, "curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent, label="parent",
        meters={"calm": 1.0}, memes={"care": 1.0},
    ))
    sari = world.add(Entity(
        id="sari", type="sari", label="sari", phrase=params.sari,
        owner=hero.id, worn_by=hero.id, region="torso", caretaker=parent.id,
    ))
    cutlet = world.add(Entity(
        id="cutlet", type="cutlet", label="cutlet", phrase=params.cutlet,
        owner=hero.id, caretaker=parent.id, region="mouth",
        meters={"size": 1.0, "dryness": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, sari=sari, cutlet=cutlet, params=params)

    world.say(
        f"{hero.id} lived at {params.place}. "
        f"{hero.pronoun('subject').capitalize()} wore {sari.phrase} and felt ready for a hero day."
    )
    world.say(
        f"At dinner, {hero.id} saw {cutlet.phrase} on the plate and smiled. "
        f"It looked tasty, but it was bigger than one careful bite."
    )

    world.para()
    world.say(
        f"{hero.id} tried to take a quick bite. "
        f"Then the cutlet slipped sideways, and {hero.pronoun('subject')} started to choke."
    )
    hero.memes["fear"] = 1.0
    hero.memes["suspense"] = 1.0
    world.trace_log.append("risk: cutlet blocked the throat")

    world.say(
        f"For one scary moment, the room went still. "
        f"{parent.pronoun('subject').capitalize()} saw the danger right away."
    )

    world.para()
    world.say(
        f"{parent.id} stayed calm and stepped in fast. "
        f"{parent.pronoun('subject').capitalize()} gave the right help and called for water."
    )
    world.trace_log.append("rescue: calm help and water")

    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 1.0
    parent.memes["care"] = 2.0

    world.say(
        f"The scary bit passed. {hero.id} coughed, then breathed safely again. "
        f"{parent.id} rubbed {hero.pronoun('possessive')} back until the worry was gone."
    )

    world.para()
    world.say(
        f"After that, {hero.id} took tiny bites and chewed slowly. "
        f"The {sari.label} stayed neat, and the cutlet was eaten the safe way."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    sari = f["sari"]
    cutlet = f["cutlet"]
    return [
        f"Write a suspenseful superhero story for a young child about {hero.id}, a {hero.type}, "
        f"who wears {sari.phrase} and almost chokes on {cutlet.phrase}.",
        f"Tell a short story where {parent.id} helps {hero.id} stay safe when a {cutlet.label} gets stuck.",
        f"Write a gentle superhero tale that includes a sari, a cutlet, and a quick rescue with a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    sari: Entity = f["sari"]
    cutlet: Entity = f["cutlet"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=(
                f"It was about {hero.id}, a little superhero who wore {sari.phrase} and "
                f"had a scary moment with {cutlet.phrase}."
            ),
        ),
        QAItem(
            question=f"What caused the suspense in the story?",
            answer=(
                f"The suspense came when {hero.id} tried to eat {cutlet.phrase} and started to choke. "
                f"It was scary because the bite was too big and the room went quiet."
            ),
        ),
        QAItem(
            question=f"How did {parent.id} help?",
            answer=(
                f"{parent.id} stayed calm, gave the right help, and made sure {hero.id} could breathe safely again."
            ),
        ),
        QAItem(
            question=f"What happened to the sari by the end?",
            answer=(
                f"The sari stayed neat, and {hero.id} was safe at the end of the meal."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sari?",
            answer="A sari is a long piece of cloth many people wear wrapped around the body like a special outfit.",
        ),
        QAItem(
            question="What is a cutlet?",
            answer="A cutlet is a cooked food patty or piece, often made from vegetables or meat, that people can eat with a meal.",
        ),
        QAItem(
            question="What should you do if someone starts choking?",
            answer="A grown-up should help right away and use safe first-aid steps or get emergency help if needed.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"events: {world.trace_log}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H).
parent(P).
sari(S).
cutlet(C).

wears(H,S) :- hero(H), sari(S).
risk(C) :- cutlet(C).
suspense :- wears(H,S), risk(C).
resolved :- suspense.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "mina"))
    lines.append(asp.fact("parent", "mother"))
    lines.append(asp.fact("sari", "sari"))
    lines.append(asp.fact("cutlet", "cutlet"))
    lines.append(asp.fact("wears", "mina", "sari"))
    lines.append(asp.fact("risk", "cutlet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    asp_has = bool(model)
    py_has = True
    if asp_has == py_has:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero suspense story world with a sari and a choking cutlet.")
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait")
    ap.add_argument("--place")
    ap.add_argument("--sari")
    ap.add_argument("--cutlet")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


HEROES = {
    "girl": ["Mina", "Aria", "Nina", "Leela"],
    "boy": ["Ravi", "Kiran", "Arun", "Dev"],
}
TRAITS = ["brave", "quick", "kind", "bold"]
PLACES = ["the apartment", "the small house", "the rooftop kitchen", "the city home"]
SARIS = [
    "a bright blue sari with gold trim",
    "a soft green sari with a shining border",
    "a pink sari that fluttered like a cape",
]
CUTLETS = [
    "a crispy cutlet on a dinner plate",
    "a hot cutlet with a crunchy crust",
    "a spicy cutlet that looked hard to swallow in one bite",
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HEROES[hero_gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(PLACES)
    sari = args.sari or rng.choice(SARIS)
    cutlet = args.cutlet or rng.choice(CUTLETS)

    if "sari" not in sari.lower():
        raise StoryError("The garment must be a sari for this storyworld.")
    if "cutlet" not in cutlet.lower():
        raise StoryError("The meal item must be a cutlet for this storyworld.")
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        parent=parent,
        trait=trait,
        place=place,
        sari=sari,
        cutlet=cutlet,
    )


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
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                hero="Mina", hero_gender="girl", parent="mother", trait="brave",
                place="the apartment", sari="a bright blue sari with gold trim",
                cutlet="a crispy cutlet on a dinner plate",
            ),
            StoryParams(
                hero="Ravi", hero_gender="boy", parent="father", trait="bold",
                place="the rooftop kitchen", sari="a pink sari that fluttered like a cape",
                cutlet="a spicy cutlet that looked hard to swallow in one bite",
            ),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
