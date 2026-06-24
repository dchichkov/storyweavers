#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/cloak_hibernate_pepperoni_magic_curiosity_transformation_animal.py
=================================================================================================

A small animal-story world with a magical cloak, winter hibernation, pepperoni,
curiosity, and transformation.

The domain is intentionally tiny:
- an animal protagonist
- a family den / forest setting
- a magic cloak that can transform one harmless thing into another
- a winter turn where hibernation matters
- a pepperoni prize that creates the tension

The story engine simulates the world state first, then narrates from it.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "squirrel", "rabbit", "mink", "cat", "badger"}
        male = {"bear", "hedgehog", "wolf", "otter", "raccoon", "mouse"}
        # neutral animal handling isn't important here; just keep story readable.
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the forest den"
    indoor: bool = True


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str  # "table" | "basket" | "shelf" ...
    genderless: bool = True


@dataclass
class Cloak:
    id: str
    label: str
    prep: str
    tail: str
    transforms: tuple[str, str]  # from, to
    warmth: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "snowy"

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.weather = self.weather
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "den": Setting(place="the forest den", indoor=True),
    "cabin": Setting(place="the little cabin", indoor=True),
}

ANIMALS = {
    "bear": {"label": "bear", "gender": "male", "traits": ["curious", "sleepy"]},
    "fox": {"label": "fox", "gender": "female", "traits": ["curious", "quick"]},
    "raccoon": {"label": "raccoon", "gender": "male", "traits": ["curious", "clever"]},
    "squirrel": {"label": "squirrel", "gender": "female", "traits": ["curious", "spry"]},
}

PRIZES = {
    "pepperoni": Prize(
        label="pepperoni pizza",
        phrase="a warm pepperoni pizza",
        type="pizza",
        location="table",
    ),
    "pepperoni_slice": Prize(
        label="pepperoni slice",
        phrase="one pepperoni slice",
        type="slice",
        location="basket",
    ),
}

CLOAKS = {
    "magic_cloak": Cloak(
        id="magic_cloak",
        label="a magic cloak",
        prep="wear the magic cloak and make a careful wish",
        tail="pulled the cloak tight and whispered a cozy wish",
        transforms=("plain blanket", "warm nest"),
    )
}

TRAITS = ["curious", "gentle", "brave", "playful"]


# ---------------------------------------------------------------------------
# World model and narration helpers
# ---------------------------------------------------------------------------
def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def animal_name(gender: str, rng: random.Random) -> str:
    female = ["Mira", "Luna", "Pip", "Ivy", "Nori"]
    male = ["Otis", "Milo", "Roo", "Bram", "Theo"]
    return rng.choice(female if gender == "female" else male)


def story_start(world: World, hero: Entity, prize: Entity, cloak: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved to look closely at everything. "
        f"{hero.pronoun().capitalize()} noticed the shiny {cloak.label} in the den and the smell of {prize.label} nearby."
    )
    world.say(
        f"The {hero.type} family was getting ready for winter, because when the snow came, {hero.pronoun('subject')} needed to hibernate."
    )


def curiosity_beats(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} sniffed the air and peered at the {prize.label} on the {prize.location}. "
        f"{hero.pronoun().capitalize()} wanted to taste it right away."
    )


def winter_warning(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f'"Not yet," said {parent.id}. "The snow is coming, and now is the time to hibernate, not to nibble."'
    )
    world.say(
        f"{hero.id} looked at the {prize.label} again. It smelled yummy, but the den was growing very still."
    )


def use_cloak(world: World, hero: Entity, cloak: Entity, prize: Entity) -> None:
    hero.meters["warmth"] = hero.meters.get("warmth", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"Then {hero.id} got an idea. {hero.pronoun().capitalize()} could {cloak.prep}."
    )
    world.say(
        f"When {hero.id} {cloak.tail}, the cloak shimmered and the plain blanket in the corner changed into {cloak.transforms[1]}."
    )
    world.say(
        f"The magic did not make the pepperoni disappear. Instead, it turned the cold den into a cozy place for hibernation, so {hero.id} could stay warm while the family rested."
    )


def resolution(world: World, hero: Entity, prize: Entity, parent: Entity) -> None:
    hero.memes["curiosity"] = max(0, hero.memes.get("curiosity", 0) - 0.5)
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"{hero.id} took one tiny happy bite of {prize.label} and then curled up beside {parent.id}."
    )
    world.say(
        f"Outside, the snow drifted down softly. Inside, the {hero.type} family hibernated in a warm little pile, and the magic cloak stayed tucked over them like a cozy blanket."
    )


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    animal: str
    name: str
    prize: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="den", animal="bear", name="Milo", prize="pepperoni", parent="mother", trait="curious"),
    StoryParams(setting="cabin", animal="fox", name="Mira", prize="pepperoni_slice", parent="father", trait="curious"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the animal is in a winter setting, the prize is
% pepperoni, and a magic cloak exists to make the den cozy enough for hibernation.
winter(den).
winter(cabin).

reasonable(S, A, P) :- winter(S), animal(A), prize(P), cloak(magic_cloak).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if sid in {"den", "cabin"}:
            lines.append(asp.fact("winter", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid in CLOAKS:
        lines.append(asp.fact("cloak", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ANIMALS:
            for pid in PRIZES:
                combos.append((sid, aid, pid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    prize = args.prize or rng.choice(list(PRIZES))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or animal_name(ANIMALS[animal]["gender"], rng)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, animal=animal, name=name, prize=prize, parent=parent, trait=trait)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.animal,
            traits=[params.trait, "curious"],
        )
    )
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, label=params.parent))
    prize = world.add(
        Entity(
            id="pepperoni",
            type="pizza",
            label=PRIZES[params.prize].label,
            phrase=PRIZES[params.prize].phrase,
            owner=hero.id,
        )
    )
    cloak = world.add(
        Entity(id="magic_cloak", type="cloak", label=CLOAKS["magic_cloak"].label)
    )

    story_start(world, hero, prize, cloak)
    world.para()
    curiosity_beats(world, hero, prize)
    winter_warning(world, parent, hero, prize)
    world.para()
    use_cloak(world, hero, cloak, prize)
    resolution(world, hero, prize, parent)

    world.facts.update(hero=hero, parent=parent, prize=prize, cloak=cloak, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f"Write a short animal story about {hero.id}, a curious {hero.type}, who finds a magic cloak and smells {prize.label}.",
        f"Tell a gentle winter story where a little {hero.type} must hibernate but still wants {prize.label}.",
        f"Write an animal story with curiosity, magic, and transformation ending in a cozy hibernation den.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What kind of animal was {hero.id}?",
            answer=f"{hero.id} was a little {hero.type}, and {hero.pronoun()} was very curious.",
        ),
        QAItem(
            question=f"What smelled so good that {hero.id} wanted to taste it?",
            answer=f"{prize.label} smelled so good that {hero.id} wanted to taste it right away.",
        ),
        QAItem(
            question=f"Why did {parent.id} say it was time to hibernate?",
            answer="The snow was coming, so the family needed to get cozy and sleep through winter.",
        ),
        QAItem(
            question="What did the magic cloak change?",
            answer="It transformed the cold den into a cozy place for hibernation.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt peaceful and cozy, tucked in beside the family.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hibernate mean?",
            answer="Hibernate means to sleep for a long time during winter so an animal can stay safe and warm.",
        ),
        QAItem(
            question="What is a cloak?",
            answer="A cloak is a loose outer covering that you wear over your clothes or fur.",
        ),
        QAItem(
            question="What is pepperoni?",
            answer="Pepperoni is a spicy meat topping that is often put on pizza.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one thing into another.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about new things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with cloak, hibernation, pepperoni, magic, curiosity, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait")
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} in {p.setting} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
