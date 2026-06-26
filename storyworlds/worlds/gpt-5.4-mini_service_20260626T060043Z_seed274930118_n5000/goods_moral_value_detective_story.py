#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/goods_moral_value_detective_story.py
=================================================================================

A small detective-style storyworld about goods, clues, and moral value.

Seed premise:
- A little detective investigates a mystery about goods.
- The clues point to a simple moral problem: someone took goods without asking.
- The ending resolves through honesty, returning the goods, and making things right.

This world is intentionally small and constraint-checked:
- Typed entities carry physical meters and emotional memes.
- The world simulates evidence, suspicion, and repair.
- The story is child-facing, concrete, and ends with a changed state.
- Inline ASP rules mirror the Python reasonableness gate.

The domain is close to a tiny detective story:
- a shop, a shelf, a missing crate of goods,
- one detective, one worried shopkeeper, and one honest helper,
- a clue trail that leads to the goods being returned.

The moral value feature is central:
- the hidden turn is about honesty versus secrecy,
- the resolution proves that doing the right thing fixes the case.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

DETECTIVE_THRESHOLD = 1.0
CLUE_THRESHOLD = 1.0
MORAL_THRESHOLD = 1.0

ROLES = {"detective", "shopkeeper", "helper", "child"}
GOOD_KINDS = {"toy", "book", "apple", "marble", "kite"}
MORAL_VALUES = {"honesty", "kindness", "fairness", "helpfulness"}


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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "shopkeeper"}
        male = {"boy", "man", "father", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Goods:
    kind: str
    label: str
    phrase: str
    location: str
    worth: int
    plural: bool = True


@dataclass
class Clue:
    id: str
    text: str
    weight: float = 1.0


@dataclass
class StoryParams:
    place: str
    goods: str
    value: str
    detective_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues: list[Clue] = []
        self.suspect: str = ""
        self.moral_turn: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.clues = copy.deepcopy(self.clues)
        clone.suspect = self.suspect
        clone.moral_turn = self.moral_turn
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_clue_reveal(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.characters() if e.kind == "character" and e.type == "detective"), None)
    goods = world.get("goods")
    if detective is None:
        return out
    if detective.meters["clues"] < CLUE_THRESHOLD:
        return out
    sig = ("clue", goods.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goods.meters["found"] += 1
    out.append("The clues pointed straight to the missing goods.")
    return out


def _r_moral_repair(world: World) -> list[str]:
    out: list[str] = []
    goods = world.get("goods")
    helper = next((e for e in world.characters() if e.type == "helper"), None)
    shopkeeper = world.get("shopkeeper")
    if goods.meters["returned"] < MORAL_THRESHOLD:
        return out
    sig = ("repair", goods.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shopkeeper.memes["relief"] += 1
    shopkeeper.memes["trust"] += 1
    if helper is not None:
        helper.memes["pride"] += 1
    out.append("Putting the goods back made the shop feel calm again.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("clue_reveal", _r_clue_reveal),
    Rule("moral_repair", _r_moral_repair),
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


def story_setting_detail(place: Place) -> str:
    if place.name == "the corner shop":
        return "The corner shop was small, bright, and full of careful shelves."
    if place.name == "the market stall":
        return "The market stall had neat baskets and a wooden counter."
    return f"{place.name.capitalize()} looked tidy and full of clues."


def reasonableness_gate(place: Place, goods: Goods, value: str) -> bool:
    if goods.location not in {"shelf", "counter", "crate"}:
        return False
    if value not in MORAL_VALUES:
        return False
    if "detective_case" not in place.affords:
        return False
    return True


def explain_rejection(place: Place, goods: Goods, value: str) -> str:
    return (
        f"(No story: this place-goods-moral setup is not a good detective case. "
        f"{place.name} must support a clue trail, the goods must be shop goods, "
        f"and the moral value must be one of {sorted(MORAL_VALUES)}.)"
    )


def predict_case(world: World, detective: Entity, helper: Entity, goods: Entity) -> dict:
    sim = world.copy()
    sim.get(detective.id).meters["clues"] += 1
    sim.get(helper.id).memes["guilt"] += 1
    sim.get(goods.id).meters["returned"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get(goods.id).meters["found"] >= 1,
        "repaired": sim.get("shopkeeper").memes["trust"] >= 1,
    }


def introduce(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "sharp")
    world.say(
        f"{detective.id} was a little {trait} detective who loved finding small clues."
    )


def setup_goods(world: World, shopkeeper: Entity, goods: Entity) -> None:
    goods.owner = shopkeeper.id
    goods.caretaker = shopkeeper.id
    goods.location = "shelf"
    shopkeeper.memes["worry"] += 1
    world.say(
        f"The shopkeeper had a crate of {goods.phrase} on the shelf."
    )


def missing_goods(world: World, goods: Entity) -> None:
    goods.location = "unknown"
    goods.meters["missing"] += 1
    world.say(
        f"One morning, the goods were gone, and the little shop felt too quiet."
    )


def investigate(world: World, detective: Entity, helper: Entity, goods: Entity) -> None:
    detective.meters["clues"] += 1
    helper.meters["nervous"] += 1
    world.say(
        f"{detective.id} followed tiny signs on the floor, because detectives know that clues often start small."
    )
    world.say(
        f"{helper.id} had seen something odd, but {helper.pronoun('possessive')} voice shook when asked about it."
    )
    propagate(world, narrate=True)


def suspect_and_turn(world: World, detective: Entity, helper: Entity, goods: Entity, value: str) -> None:
    helper.memes["guilt"] += 1
    world.suspect = helper.id
    if value == "honesty":
        world.moral_turn = "truth"
        world.say(
            f"{helper.id} took a slow breath and said the truth: {helper.pronoun('subject').capitalize()} had moved the goods without asking."
        )
    elif value == "kindness":
        world.moral_turn = "care"
        world.say(
            f"{helper.id} admitted {helper.pronoun('subject')} had hidden the goods to keep them safe, but forgot to tell anyone."
        )
    elif value == "fairness":
        world.moral_turn = "balance"
        world.say(
            f"{helper.id} said {helper.pronoun('subject')} had borrowed the goods, then realized it was not fair to keep them."
        )
    else:
        world.moral_turn = "help"
        world.say(
            f"{helper.id} confessed that {helper.pronoun('subject')} wanted to help, but made the case confusing instead."
        )


def return_goods(world: World, shopkeeper: Entity, helper: Entity, goods: Entity) -> None:
    goods.location = "shelf"
    goods.meters["returned"] += 1
    goods.meters["found"] += 1
    helper.memes["guilt"] = 0.0
    helper.memes["relief"] += 1
    shopkeeper.memes["trust"] += 1
    world.say(
        f"Together, they put the goods back on the shelf, and the shopkeeper smiled with relief."
    )
    world.say(
        f"The case was solved, because the missing goods had been returned and the truth had been told."
    )


def closing_image(world: World, detective: Entity, shopkeeper: Entity, helper: Entity, goods: Entity) -> None:
    world.say(
        f"By the end, {detective.id} had a neat notebook, {helper.id} had a clear conscience, and the goods sat safely where they belonged."
    )


def tell(place: Place, goods_cfg: Goods, moral_value: str, detective_name: str, helper_name: str) -> World:
    world = World(place)

    detective = world.add(Entity(
        id=detective_name, kind="character", type="detective", traits=["little", "sharp", "careful"]
    ))
    shopkeeper = world.add(Entity(
        id="shopkeeper", kind="character", type="shopkeeper", label="the shopkeeper", traits=["worrying", "kind"]
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="helper", traits=["little", "nervous", "kind"]
    ))
    goods = world.add(Entity(
        id="goods", kind="thing", type=goods_cfg.kind, label=goods_cfg.label,
        phrase=goods_cfg.phrase, owner=shopkeeper.id, caretaker=shopkeeper.id,
        location=goods_cfg.location, plural=goods_cfg.plural,
    ))

    world.facts.update(
        place=place, goods_cfg=goods_cfg, moral_value=moral_value,
        detective=detective, shopkeeper=shopkeeper, helper=helper, goods=goods,
    )

    introduce(world, detective)
    setup_goods(world, shopkeeper, goods)

    world.para()
    world.say(story_setting_detail(place))
    missing_goods(world, goods)
    investigate(world, detective, helper, goods)

    world.para()
    suspect_and_turn(world, detective, helper, goods, moral_value)

    pred = predict_case(world, detective, helper, goods)
    if pred["found"]:
        return_goods(world, shopkeeper, helper, goods)
    closing_image(world, detective, shopkeeper, helper, goods)
    return world


PLACES = {
    "corner_shop": Place(name="the corner shop", affords={"detective_case"}),
    "market_stall": Place(name="the market stall", affords={"detective_case"}),
    "toy_counter": Place(name="the toy counter", affords={"detective_case"}),
}

GOODS = {
    "toy": Goods(kind="toy", label="toys", phrase="bright little toys", location="crate", worth=3),
    "book": Goods(kind="book", label="books", phrase="stacked story books", location="shelf", worth=2),
    "apple": Goods(kind="apple", label="apples", phrase="red apples", location="basket", worth=1),
    "marble": Goods(kind="marble", label="marbles", phrase="shiny marbles", location="jar", worth=2),
    "kite": Goods(kind="kite", label="kites", phrase="paper kites", location="crate", worth=2),
}

VALUES = ["honesty", "kindness", "fairness", "helpfulness"]
DETECTIVE_NAMES = ["Milo", "Nina", "Tess", "Arlo", "Ivy", "June"]
HELPER_NAMES = ["Pip", "Juno", "Bea", "Ollie", "Theo", "Zara"]


@dataclass
class StoryParams:
    place: str
    goods: str
    value: str
    detective_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        if "detective_case" not in p.affords:
            continue
        for g in GOODS.values():
            for v in VALUES:
                if reasonableness_gate(p, g, v):
                    combos.append((p.name, g.kind, v))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about goods and moral value.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--goods", choices=list(GOODS))
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
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
    if args.place and args.goods and args.value:
        p, g, v = PLACES[args.place], GOODS[args.goods], args.value
        if not reasonableness_gate(p, g, v):
            raise StoryError(explain_rejection(p, g, v))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0].replace("the ", "").replace(" ", "_") == args.place)
              and (args.goods is None or c[1] == args.goods)
              and (args.value is None or c[2] == args.value)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_name, goods_kind, value = rng.choice(sorted(combos))
    place_key = next(k for k, p in PLACES.items() if p.name == place_name)
    detective = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(place=place_key, goods=goods_kind, value=value, detective_name=detective, helper_name=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child about {f["goods_cfg"].phrase} and the moral value of {f["moral_value"]}.',
        f"Tell a gentle mystery where {f['detective'].id} searches for missing goods at {f['place'].name} and learns the truth.",
        f"Write a tiny detective tale with clues, a worried shopkeeper, and a happy ending where the goods are put back.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    shopkeeper = f["shopkeeper"]
    goods = f["goods"]
    place = f["place"]
    value = f["moral_value"]
    return [
        QAItem(
            question=f"Who solved the mystery about the missing {goods.label}?",
            answer=f"{detective.id} solved the mystery by following clues and listening carefully."
        ),
        QAItem(
            question=f"Why was the shopkeeper worried at {place.name}?",
            answer=f"The shopkeeper was worried because the {goods.label} were missing from the shelf."
        ),
        QAItem(
            question=f"What did {helper.id} do that made the case better?",
            answer=f"{helper.id} told the truth, helped return the goods, and made the story end with honesty."
        ),
        QAItem(
            question=f"What moral value was most important in this story?",
            answer=f"The most important moral value was {value}, because the truth helped fix the problem."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks carefully for clues to solve a mystery."
        ),
        QAItem(
            question="What are goods?",
            answer="Goods are things that people sell or buy, like toys, books, apples, kites, or marbles."
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth, even when it is hard."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="corner_shop", goods="toy", value="honesty", detective_name="Milo", helper_name="Pip"),
    StoryParams(place="market_stall", goods="book", value="kindness", detective_name="Nina", helper_name="Bea"),
    StoryParams(place="toy_counter", goods="kite", value="fairness", detective_name="Ivy", helper_name="Ollie"),
]


ASP_RULES = r"""
place_ok(P) :- setting(P), detective_case(P).
goods_ok(G) :- goods(G).
value_ok(V) :- moral_value(V).

valid(P, G, V) :- place_ok(P), goods_ok(G), value_ok(V).
valid_story(P, G, V) :- valid(P, G, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, place in PLACES.items():
        lines.append(asp.fact("setting", key))
        for a in sorted(place.affords):
            lines.append(asp.fact("detective_case", key))
            lines.append(asp.fact("affords", key, a))
    for key, g in GOODS.items():
        lines.append(asp.fact("goods", key))
        lines.append(asp.fact("goods_kind", key, g.kind))
        lines.append(asp.fact("goods_location", key, g.location))
    for v in VALUES:
        lines.append(asp.fact("moral_value", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def explain_genderless() -> str:
    return "(No story: this detective world does not use gendered constraints.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GOODS[params.goods], params.value, params.detective_name, params.helper_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, goods, moral value) combos:\n")
        for p, g, v in triples:
            print(f"  {p:14} {g:8} {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.goods} at {p.place} (value: {p.value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
