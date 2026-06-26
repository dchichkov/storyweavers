#!/usr/bin/env python3
"""
storyworlds/worlds/gooey_pish_moral_value_folk_tale.py
=======================================================

A small folk-tale storyworld about a gooey pish of porridge, a moral choice,
and the way kindness changes a hungry village.

Premise:
- A child or villager loves a warm, gooey treat.
- A tempting plan risks leaving someone else without enough.
- A warning, refusal, and then a wiser share lead to a happier ending.

The story is intentionally tiny and classical: it simulates a few entities,
their physical quantities (meters) and emotional feelings (memes), and then
renders a child-facing folk tale whose ending proves the moral value changed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Village:
    place: str
    hunger: float = 0.0
    pot_fullness: float = 0.0
    spoon_used: bool = False


class World:
    def __init__(self, village: Village) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        clone = World(Village(self.village.place, self.village.hunger, self.village.pot_fullness, self.village.spoon_used))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    food: str
    moral: str
    seed: Optional[int] = None


PLACES = {
    "cottage": Village(place="the cottage"),
    "mill": Village(place="the mill"),
    "market": Village(place="the market"),
    "oak": Village(place="the old oak tree"),
}

HEROES = [
    ("Mira", "girl"),
    ("Tobin", "boy"),
    ("Sella", "girl"),
    ("Bram", "boy"),
]

HELPERS = [
    ("Grandmother", "mother"),
    ("Farmer", "father"),
    ("Wren", "woman"),
    ("Ivo", "man"),
]

FOODS = {
    "porridge": {
        "label": "porridge",
        "phrase": "a bowl of warm porridge",
        "gooey": True,
    },
    "honeycake": {
        "label": "honeycake",
        "phrase": "a sticky honeycake",
        "gooey": True,
    },
    "stew": {
        "label": "stew",
        "phrase": "a pot of thick stew",
        "gooey": True,
    },
}

MORALS = {
    "share": "share the good things",
    "greedy": "keep too much for oneself",
    "kind": "be kind when someone is hungry",
}

TRACES = {}


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_grow_hunger(world: World) -> list[str]:
    out = []
    village = world.village
    if village.pot_fullness < THRESHOLD and ("hunger", "rise") not in world.fired:
        world.fired.add(("hunger", "rise"))
        village.hunger += 1.0
        out.append("The village bellies began to rumble.")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("gooey", 0.0) >= THRESHOLD and not world.village.spoon_used:
            sig = ("spill", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["mess"] = ent.meters.get("mess", 0.0) + 1.0
            out.append(f"Some of the gooey {ent.label} went pish onto the tablecloth.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.memes.get("stingy", 0.0) >= THRESHOLD and world.village.hunger >= THRESHOLD:
            sig = ("guilt", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1.0
            out.append(f"{ent.id} felt a little pang of worry.")
    return out


CAUSAL_RULES = [
    Rule("grow_hunger", _r_grow_hunger),
    Rule("spill", _r_spill),
    Rule("calm", _r_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_share(world: World, giver: Entity, helper: Entity, food: Entity) -> dict:
    sim = world.copy()
    sim.get(giver.id).memes["stingy"] = 0.0
    sim.get(giver.id).memes["generous"] = 1.0
    sim.village.pot_fullness += 1.0
    sim.village.hunger = max(0.0, sim.village.hunger - 1.0)
    return {
        "hunger": sim.village.hunger,
        "mess": sim.get(food.id).meters.get("mess", 0.0),
    }


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"Once, {hero.id} was a little {hero.type} who listened closely to every tale the wind brought."
    )


def love_food(world: World, hero: Entity, food: Entity) -> None:
    hero.memes["want"] = 1.0
    world.say(
        f"{hero.id} loved {food.phrase} because it was soft, warm, and wonderfully gooey."
    )


def arrive(world: World, hero: Entity, helper: Entity, village: Village) -> None:
    world.say(
        f"One evening, {hero.id} and {helper.id} came to {village.place} where the fire was already purring."
    )


def temptation(world: World, hero: Entity, food: Entity) -> None:
    hero.memes["stingy"] = 1.0
    world.say(
        f"{hero.id} saw the big bowl and thought, 'If I keep this all to myself, I will have the sweetest pish of the day.'"
    )


def warning(world: World, helper: Entity, hero: Entity, food: Entity) -> None:
    if world.village.hunger >= THRESHOLD:
        world.say(
            f'{helper.id} shook {helper.pronoun("possessive")} head and said, "A full belly grows better when it is not the only belly that eats."'
        )


def choice(world: World, hero: Entity, helper: Entity, food: Entity) -> None:
    if hero.memes.get("stingy", 0.0) >= THRESHOLD:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        world.say(f"{hero.id} stared at the bowl and felt the first prick of shame.")
        world.say(f"Then {hero.id} took a breath and reached for a spoon instead of a greedy grin.")
        world.village.spoon_used = True
        food.meters["gooey"] = 1.0
        world.village.pot_fullness = 1.0
        world.village.hunger = max(0.0, world.village.hunger - 1.0)
        hero.memes["generous"] = 1.0
        hero.memes["stingy"] = 0.0
        propagate(world, narrate=True)
    else:
        world.say(f"{hero.id} was already ready to share.")


def ending(world: World, hero: Entity, helper: Entity, food: Entity) -> None:
    world.say(
        f"In the end, {hero.id} gave out bowls to the hungry folk, and the gooey pish of porridge fed more than one happy heart."
    )
    world.say(
        f"{hero.id} learned that a kind hand can make a small meal feel big enough for a whole village."
    )


def tell(params: StoryParams) -> World:
    village = Village(place=PLACES[params.place].place)
    world = World(village)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    food_cfg = FOODS[params.food]
    food = world.add(Entity(
        id="food",
        kind="thing",
        type=params.food,
        label=food_cfg["label"],
        phrase=food_cfg["phrase"],
    ))

    intro(world, hero)
    love_food(world, hero, food)
    world.para()
    arrive(world, hero, helper, village)
    temptation(world, hero, food)
    warning(world, helper, hero, food)
    choice(world, hero, helper, food)
    world.para()
    ending(world, hero, helper, food)

    world.facts.update(
        hero=hero,
        helper=helper,
        food=food,
        params=params,
        moral=params.moral,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short folk tale for a child about {p.hero} learning the moral value of {p.moral}.',
        f'Tell a gentle story that includes the words "gooey" and "pish" and ends with a kind choice.',
        f'Write a village tale where {p.hero} almost keeps a tasty treat alone, but shares it in the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    food = f["food"]
    params = f["params"]
    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved {food.phrase}, which was soft, warm, and gooey.",
        ),
        QAItem(
            question=f"Who reminded {hero.id} about being generous?",
            answer=f"{helper.id} reminded {hero.id} that a meal feels better when it is shared.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn?",
            answer=f"{hero.id} learned to {params.moral} and not keep everything only for oneself.",
        ),
        QAItem(
            question=f"Why did the story mention pish?",
            answer="It showed the sticky little spill and helped the tale feel lively and real.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gooey mean?",
            answer="Gooey means soft, sticky, and a little bit wet, like thick porridge or warm honey.",
        ),
        QAItem(
            question="What can pish mean in a folk tale?",
            answer="Pish can be a tiny splash or spill, like something slipping out with a soft plop.",
        ),
        QAItem(
            question="Why is sharing a good moral value?",
            answer="Sharing is good because it helps everyone have enough and makes people feel cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  village: hunger={world.village.hunger}, pot_fullness={world.village.pot_fullness}, spoon_used={world.village.spoon_used}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

at_risk(F) :- food(F), gooey(F), wants_share(F).
good_moral(F) :- food(F), at_risk(F), has_spoon(F).

valid(P, F, M) :- place(P), food(F), moral(M), good_moral(F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f["gooey"]:
            lines.append(asp.fact("gooey", fid))
        lines.append(asp.fact("wants_share", fid))
        lines.append(asp.fact("has_spoon", fid))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    python_set = set((p, f, m) for p in PLACES for f in FOODS for m in MORALS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python registry:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk tale storyworld about gooey porridge and moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--moral", choices=MORALS)
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
    food = args.food or rng.choice(list(FOODS))
    moral = args.moral or rng.choice(list(MORALS))
    hero_name, hero_type = (args.hero, args.hero_type) if args.hero and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else rng.choice(HELPERS)
    return StoryParams(
        place=place,
        hero=hero_name,
        hero_type=hero_type,
        helper=helper_name,
        helper_type=helper_type,
        food=food,
        moral=moral,
    )


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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, f, m) for p in PLACES for f in FOODS for m in MORALS]


CURATED = [
    StoryParams(place="cottage", hero="Mira", hero_type="girl", helper="Grandmother", helper_type="mother", food="porridge", moral="share"),
    StoryParams(place="market", hero="Tobin", hero_type="boy", helper="Farmer", helper_type="father", food="honeycake", moral="kind"),
    StoryParams(place="mill", hero="Sella", hero_type="girl", helper="Wren", helper_type="woman", food="stew", moral="greedy"),
]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
