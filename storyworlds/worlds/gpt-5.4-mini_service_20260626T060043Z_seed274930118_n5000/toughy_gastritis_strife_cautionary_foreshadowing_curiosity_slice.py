#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/toughy_gastritis_strife_cautionary_foreshadowing_curiosity_slice.py
======================================================================================================

A tiny slice-of-life story world about a curious child nicknamed Toughy,
a cautious grown-up, and a stomach that needs gentler choices.

The seed premise:
- Toughy feels curious about snacks and drinks.
- The grown-up notices signs that a tummy is getting irritated.
- A small strife grows when Toughy wants the exciting thing anyway.
- A safer, softer choice turns the evening calm again.

The story is built from state changes, not a frozen paragraph:
- hunger, comfort, curiosity, caution, and strife are tracked as memes
- stomach irritation, food temperature, and food spice are tracked as meters
- a warning can foreshadow what will happen if Toughy ignores the hint
- the resolution changes the ending image: quiet, warm, and settled

This world is intentionally compact and child-facing in a slice-of-life style.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_ID = "toughy_gastritis_strife_cautionary_foreshadowing_curiosity_slice"

# Physical thresholds.
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
    edible: bool = False
    safe_for_tummy: bool = True
    warm: bool = False
    spicy: bool = False
    sour: bool = False
    bitter: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    cozy: bool = True


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    safe_for_tummy: bool
    warm: bool = False
    spicy: bool = False
    sour: bool = False
    bitter: bool = False
    gentle: bool = False


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    safe_for_tummy: bool
    warm: bool = False
    fizzy: bool = False
    gentle: bool = False


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)  # "gastritis", "strife", "curiosity"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    food: str
    drink: str
    comfort: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, cozy=True),
    "table": Place(id="table", label="the breakfast table", indoor=True, cozy=True),
    "living_room": Place(id="living_room", label="the living room couch", indoor=True, cozy=True),
}

FOODS = {
    "toast": Food("toast", "toast", "a plain piece of toast", True, warm=True, gentle=True),
    "banana": Food("banana", "banana", "a soft banana", True, gentle=True),
    "soup": Food("soup", "soup", "a small bowl of warm soup", True, warm=True, gentle=True),
    "chips": Food("chips", "chips", "a spicy handful of chips", False, spicy=True),
    "candy": Food("candy", "candy", "a sour candy", False, sour=True),
}

DRINKS = {
    "water": Drink("water", "water", "a little glass of water", True, gentle=True),
    "tea": Drink("tea", "tea", "a warm cup of tea", True, warm=True, gentle=True),
    "soda": Drink("soda", "soda", "a fizzy soda", False, fizzy=True),
}

COMFORTS = {
    "blanket": Comfort("blanket", "blanket", "a soft blanket", helps={"strife", "gastritis"}),
    "book": Comfort("book", "book", "a picture book", helps={"curiosity", "strife"}),
    "heating_pad": Comfort("heating_pad", "heating pad", "a warm heating pad", helps={"gastritis"}),
}

NAMES = ["Toughy", "Milo", "June", "Poppy", "Nina", "Owen", "Ivy", "Leo"]
TRAITS = ["curious", "careful", "spunky", "quiet", "bright", "restless"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for food in FOODS:
            for drink in DRINKS:
                for comfort in COMFORTS:
                    if food in {"toast", "banana", "soup"} and drink in {"water", "tea"}:
                        combos.append((place, food, drink, comfort))
    return combos


def reasonableness_gate(food: Food, drink: Drink, comfort: Comfort) -> bool:
    return food.safe_for_tummy and drink.safe_for_tummy and (
        "gastritis" in comfort.helps or "strife" in comfort.helps
    )


def explain_rejection(food: Food, drink: Drink, comfort: Comfort) -> str:
    return (
        f"(No story: {food.label} and {drink.label} would not make a gentle slice-of-life "
        f"ending here, and {comfort.label} does not help the tummy concern enough.)"
    )


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes if t != 'curiosity'), 'child')} "
        f"who noticed everything in {world.place.label}."
    )


def desire(world: World, hero: Entity, food: Food, drink: Drink) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} kept looking at {food.phrase} and {drink.phrase}, because curiosity made the "
        f"bright things feel twice as interesting."
    )


def foreshadow(world: World, parent: Entity, hero: Entity, food: Food, drink: Drink) -> None:
    hero.memes["cautionary_hint"] += 1
    world.say(
        f"{parent.id} noticed {hero.id} rubbing {hero.pronoun('possessive')} stomach and said, "
        f'"Let\'s be careful. That spicy choice might make your tummy feel worse."'
    )
    world.facts["foreshadowed"] = True
    world.facts["foreshadow_food"] = food.label
    world.facts["foreshadow_drink"] = drink.label


def choose_wrong_then_strife(world: World, hero: Entity, food: Food) -> None:
    hero.memes["strife"] += 1
    hero.meters["gastritis"] += 1
    world.say(
        f"{hero.id} hesitated, then took a taste anyway. "
        f"That tiny choice made the stomach feeling more upset."
    )
    world.say(
        f"Pretty soon, {hero.id} looked less curious and more uncomfortable."
    )


def offer_comfort(world: World, parent: Entity, hero: Entity, comfort: Comfort, drink: Drink) -> None:
    if "gastritis" in comfort.helps:
        hero.meters["gastritis"] = max(0.0, hero.meters["gastritis"] - 1.0)
    if "strife" in comfort.helps:
        hero.memes["strife"] = max(0.0, hero.memes["strife"] - 1.0)
    if drink.safe_for_tummy:
        hero.meters["temperature"] = 0.0
    world.say(
        f"{parent.id} brought {comfort.phrase} and {drink.phrase}, then sat beside {hero.id} "
        f"until the room felt calm again."
    )


def resolve(world: World, hero: Entity, food: Food, drink: Drink, comfort: Comfort) -> None:
    hero.memes["curiosity"] += 0.5
    hero.memes["comfort"] += 1
    hero.memes["strife"] = 0.0
    world.say(
        f"{hero.id} chose the gentle snack instead: {food.phrase} with {drink.phrase}. "
        f"The tummy pinch faded, and the evening became quiet and warm."
    )
    world.say(
        f"By the end, {hero.id} could curl up with {comfort.phrase} and smile at the safe little meal."
    )


def tell(place: Place, food: Food, drink: Drink, comfort: Comfort,
         hero_name: str, gender: str, caretaker_kind: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        memes={"curiosity": 0.0, "strife": 0.0, "comfort": 0.0, "cautionary_hint": 0.0},
        meters={"gastritis": 0.0, "temperature": 0.0},
    ))
    parent = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_kind,
        label="the grown-up",
    ))
    food_ent = world.add(Entity(
        id=food.id,
        kind="thing",
        type=food.id,
        label=food.label,
        phrase=food.phrase,
        edible=True,
        safe_for_tummy=food.safe_for_tummy,
        warm=food.warm,
        spicy=food.spicy,
        sour=food.sour,
        bitter=food.bitter,
    ))
    drink_ent = world.add(Entity(
        id=drink.id,
        kind="thing",
        type=drink.id,
        label=drink.label,
        phrase=drink.phrase,
        edible=True,
        safe_for_tummy=drink.safe_for_tummy,
        warm=drink.warm,
    ))
    comfort_ent = world.add(Entity(
        id=comfort.id,
        kind="thing",
        type=comfort.id,
        label=comfort.label,
        phrase=comfort.phrase,
    ))
    world.facts.update(
        hero=hero, parent=parent, food=food_ent, drink=drink_ent, comfort=comfort_ent,
        place=place, trait=trait, gender=gender, caretaker_kind=caretaker_kind,
    )

    world.say(
        f"In {place.label}, {hero.id} was a {trait} little {gender} who loved noticing snacks "
        f"on the table."
    )
    world.say(
        f"{hero.id} had been feeling a bit of gastritis in {hero.pronoun('possessive')} tummy, so "
        f"the day already felt careful."
    )

    world.para()
    desire(world, hero, food, drink)
    foreshadow(world, parent, hero, food, drink)
    choose_wrong_then_strife(world, hero, food)

    world.para()
    offer_comfort(world, parent, hero, comfort, drink)
    resolve(world, hero, FOODS["toast"] if food.id != "toast" else food, drink, comfort)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    food = f["food"]
    drink = f["drink"]
    return [
        f'Write a short slice-of-life story for a child nicknamed "{hero.id}" about curiosity, caution, and a gentle tummy.',
        f"Tell a cozy story where {hero.id} wants {food.phrase} but {parent.label} warns that the tummy needs a softer choice.",
        f'Write a small cautionary story that includes "{food.label}", "{drink.label}", and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    food = f["food"]
    drink = f["drink"]
    comfort = f["comfort"]
    place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {hero.id}, a {trait} little child who notices snacks and feelings in the room.",
        ),
        QAItem(
            question=f"Why did the grown-up warn {hero.id} about {food.label}?",
            answer=(
                f"The grown-up warned {hero.id} because {food.phrase} was the risky choice, and "
                f"the tummy was already showing signs of gastritis."
            ),
        ),
        QAItem(
            question=f"What helped calm the strife after the warning?",
            answer=(
                f"{comfort.phrase} and {drink.phrase} helped calm things down, and the gentler snack "
                f"let the evening settle."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} choose at the end?",
            answer=(
                f"{hero.id} chose the gentler snack instead of the spicy one, so the tummy could rest "
                f"and the day could end quietly."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and paying attention so a choice does not cause trouble.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that something important may happen later.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is gastritis?",
            answer="Gastritis is when the stomach gets irritated or upset and can feel sore or uncomfortable.",
        ),
        QAItem(
            question="What does strife mean?",
            answer="Strife means a little fight or trouble between feelings or people.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        lines.append(f"  {ent.id} ({ent.kind}/{ent.type}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable only if the chosen food and drink are gentle for the tummy,
% and the comfort object can actually help with gastritis or strife.
gentle_story(P, F, D, C) :- food(F), drink(D), comfort(C),
                            safe_food(F), safe_drink(D), helpful(C).

% Foreshadowing is justified when the chosen food is risky and the child is curious.
foreshadow(P, F) :- risky_food(F), curiosity(P).

% A calm ending is possible when the comfort and drink are gentle.
calm_end(P, C, D) :- comfort(C), drink(D), safe_drink(D), helpful(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.safe_for_tummy:
            lines.append(asp.fact("safe_food", fid))
        if f.spicy:
            lines.append(asp.fact("risky_food", fid))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        if d.safe_for_tummy:
            lines.append(asp.fact("safe_drink", did))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        if "gastritis" in c.helps or "strife" in c.helps:
            lines.append(asp.fact("helpful", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_combos() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show gentle_story/4."))
    return sorted(set(asp.atoms(model, "gentle_story")))


def asp_verify() -> int:
    import asp
    py = set((p, f, d, c) for p, f, d, c in valid_combos())
    cl = set(asp_reasonable_combos())
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about Toughy, gastritis, and gentle choices.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.food and args.drink and args.comfort:
        if not reasonableness_gate(FOODS[args.food], DRINKS[args.drink], COMFORTS[args.comfort]):
            raise StoryError(explain_rejection(FOODS[args.food], DRINKS[args.drink], COMFORTS[args.comfort]))
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.food is None or c[1] == args.food)
        and (args.drink is None or c[2] == args.drink)
        and (args.comfort is None or c[3] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food, drink, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    name = args.name or "Toughy"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, food=food, drink=drink, comfort=comfort,
                       name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        FOODS[params.food],
        DRINKS[params.drink],
        COMFORTS[params.comfort],
        params.name,
        params.gender,
        params.caretaker,
        params.trait,
    )
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


CURATED = [
    StoryParams(place="kitchen", food="chips", drink="water", comfort="blanket", name="Toughy", gender="boy", caretaker="mother", trait="curious"),
    StoryParams(place="table", food="candy", drink="tea", comfort="book", name="Toughy", gender="boy", caretaker="father", trait="careful"),
    StoryParams(place="living_room", food="chips", drink="tea", comfort="heating_pad", name="Toughy", gender="boy", caretaker="mother", trait="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show gentle_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_reasonable_combos()
        print(f"{len(combos)} reasonable combos")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
