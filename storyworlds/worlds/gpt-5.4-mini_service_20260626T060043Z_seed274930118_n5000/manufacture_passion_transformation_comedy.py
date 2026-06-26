#!/usr/bin/env python3
"""
storyworlds/worlds/manufacture_passion_transformation_comedy.py
===============================================================

A small comedy storyworld about making something, following a burst of
passion, and accidentally transforming the result in a funny way.

Premise:
- A child or cheerful maker wants to manufacture a small prize.
- A strong passion pushes them to rush the work.
- The work goes a little wrong, then a helper or simple fix changes the result
  into a new, better form.

The story is modeled as a tiny simulation with meters and memes:
- physical meters: progress, mess, shine, wobble, transformed
- emotional memes: excitement, pride, worry, laughter, affection

The central transformation is state-driven, not just a cosmetic rename:
- items can be made
- items can be transformed by the maker's passion or a helper's fix
- the ending proves the world changed
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
    made_by: Optional[str] = None
    transformed_from: Optional[str] = None
    transformed_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"progress": 0.0, "mess": 0.0, "shine": 0.0, "wobble": 0.0, "transformed": 0.0}
        if not self.memes:
            self.memes = {"passion": 0.0, "excitement": 0.0, "worry": 0.0, "pride": 0.0, "laughter": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Workshop:
    place: str = "the tiny workshop"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"manufacture", "transform"})


@dataclass
class Product:
    label: str
    phrase: str
    type: str
    kind: str = "thing"


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    fix: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    product: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get(world.facts["maker"].id)
    product = world.get(world.facts["product"].id)
    if maker.memes["passion"] < THRESHOLD or product.meters["progress"] < THRESHOLD:
        return out
    sig = ("wobble", product.id)
    if sig in world.fired:
        return out
    if product.meters["mess"] > 0:
        world.fired.add(sig)
        product.meters["wobble"] += 1
        maker.memes["worry"] += 1
        out.append(f"The {product.label} wobbled a little on the table.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get(world.facts["maker"].id)
    product = world.get(world.facts["product"].id)
    tool = world.get(world.facts["tool"].id)
    if product.meters["progress"] < THRESHOLD:
        return out
    if product.meters["transformed"] >= THRESHOLD:
        return out
    if maker.memes["passion"] < THRESHOLD and product.meters["wobble"] < THRESHOLD:
        return out
    if tool.id not in world.entities:
        return out
    sig = ("transform", product.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    product.meters["transformed"] += 1
    product.meters["shine"] += 1
    maker.memes["pride"] += 1
    maker.memes["laughter"] += 1
    out.append(f"The {product.label} turned into something even funnier and shinier.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def make_passion_story(world: World, maker: Entity, product: Entity) -> None:
    maker.memes["passion"] += 1
    maker.memes["excitement"] += 1
    world.say(
        f"{maker.id} had a big passion for making things that looked a little silly and a little wonderful."
    )
    world.say(
        f"{maker.pronoun().capitalize()} wanted to manufacture {product.phrase} all by {maker.pronoun('object')}."
    )


def build(world: World, maker: Entity, product: Entity, tool: Entity) -> None:
    product.meters["progress"] += 1
    world.say(
        f"In {world.workshop.place}, {maker.id} began to manufacture the {product.label} with {tool.label}."
    )
    product.meters["mess"] += 1
    world.say(
        f"The first try left a tiny mess, because the glue was too eager and the pieces stuck to the wrong spots."
    )
    propagate(world, narrate=True)


def helper_fix(world: World, helper: Entity, maker: Entity, product: Entity, tool: Entity) -> None:
    helper.memes["laughter"] += 1
    world.say(
        f"{helper.id} peeked in, giggled, and said, \"That {product.label} looks like it is trying to tell a joke.\""
    )
    world.say(
        f"Then {helper.id} showed {maker.pronoun('object')} how to use the {tool.label} more gently."
    )
    product.meters["shine"] += 1
    propagate(world, narrate=True)


def finish(world: World, maker: Entity, product: Entity) -> None:
    maker.memes["pride"] += 1
    world.say(
        f"At last, the {product.label} stood up straight, all transformed and shining."
    )
    world.say(
        f"{maker.id} laughed, because the new shape was not the one {maker.pronoun('subject')} planned, but it was the one the day wanted."
    )


def tell(workshop: Workshop, product_cfg: Product, tool_cfg: Tool,
         name: str = "Milo", gender: str = "boy",
         helper: str = "Aunt Nia", trait: str = "cheerful") -> World:
    world = World(workshop)
    maker = world.add(Entity(id=name, kind="character", type=gender))
    helper_ent = world.add(Entity(id=helper, kind="character", type="adult"))
    product = world.add(Entity(
        id="product",
        type=product_cfg.type,
        label=product_cfg.label,
        phrase=product_cfg.phrase,
        owner=maker.id,
        caretaker=maker.id,
    ))
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label))

    world.facts.update(maker=maker, helper=helper_ent, product=product, tool=tool, workshop=workshop)

    world.say(f"{maker.id} was a {trait} little maker who loved jokes almost as much as {maker.pronoun('possessive')} workbench.")
    make_passion_story(world, maker, product)
    world.para()
    build(world, maker, product, tool)
    world.para()
    helper_fix(world, helper_ent, maker, product, tool)
    finish(world, maker, product)
    return world


WORKSHOPS = {
    "tiny": Workshop(place="the tiny workshop", indoors=True),
    "garage": Workshop(place="the garage", indoors=True),
    "sunroom": Workshop(place="the sunroom", indoors=True),
}


PRODUCTS = {
    "kite": Product(label="kite", phrase="a bright paper kite", type="kite"),
    "robot": Product(label="robot", phrase="a wobble-legged toy robot", type="robot"),
    "crown": Product(label="crown", phrase="a glittery cardboard crown", type="crown"),
    "boat": Product(label="boat", phrase="a tiny sailboat", type="boat"),
}


TOOLS = {
    "glue": Tool(id="glue", label="glue", helps={"manufacture"}, fix="stick"),
    "tape": Tool(id="tape", label="tape", helps={"manufacture", "transform"}, fix="patch"),
    "paint": Tool(id="paint", label="paint", helps={"transform"}, fix="brighten"),
    "scissors": Tool(id="scissors", label="scissors", helps={"manufacture"}, fix="cut"),
}


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Poppy", "Zoe"]
BOY_NAMES = ["Milo", "Owen", "Theo", "Ben", "Finn", "Leo"]
TRAITS = ["cheerful", "curious", "spirited", "silly", "patient", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, ws in WORKSHOPS.items():
        for pid in PRODUCTS:
            for tid, tool in TOOLS.items():
                if "manufacture" in tool.helps and "transform" in tool.helps:
                    combos.append((place, pid, tid))
                elif pid in {"robot", "crown"} and tid in {"tape", "paint"}:
                    combos.append((place, pid, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    product: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "glue": [("What does glue do?", "Glue helps pieces stick together so they can become one thing.")],
    "tape": [("What does tape do?", "Tape helps hold things in place for a little while.")],
    "paint": [("Why do people use paint?", "Paint adds color and can make something look bright and new.")],
    "scissors": [("What are scissors for?", "Scissors cut paper, string, and other thin things.")],
    "kite": [("What is a kite?", "A kite is a light toy that can fly in the wind when a person holds the string.")],
    "robot": [("What is a toy robot?", "A toy robot is a pretend robot made for play, not for real work.")],
    "crown": [("What is a crown?", "A crown is a special hat that people wear when they want to feel fancy.")],
    "boat": [("What is a boat?", "A boat is something that can float on water.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    product = f["product"]
    tool = f["tool"]
    return [
        f'Write a funny story for a small child about a maker who wants to manufacture {product.phrase}.',
        f"Tell a comedy story where {maker.id} has a burst of passion, uses {tool.label}, and the result transforms in a surprising way.",
        f"Write a short, cheerful story set in {world.workshop.place} with a playful transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker: Entity = f["maker"]
    helper: Entity = f["helper"]
    product: Entity = f["product"]
    tool: Entity = f["tool"]
    qa = [
        QAItem(
            question=f"What did {maker.id} want to manufacture?",
            answer=f"{maker.id} wanted to manufacture {product.phrase} in {world.workshop.place}.",
        ),
        QAItem(
            question=f"Why was {maker.id}'s work a little funny at first?",
            answer=f"The first try made a tiny mess, so the {product.label} wobbled and looked silly before it was fixed.",
        ),
        QAItem(
            question=f"Who helped turn the {product.label} into something new?",
            answer=f"{helper.id} helped by showing {maker.id} how to use the {tool.label} more gently.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {product.label} became transformed, shinier, and funnier than it was at the start.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["product"].label, world.facts["tool"].label}
    out: list[QAItem] = []
    for tag in ["glue", "tape", "paint", "scissors", "kite", "robot", "crown", "boat"]:
        if tag in tags or tag == world.facts["product"].label or tag == world.facts["tool"].label:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(P, Prod, Tool) :- place(P), product(Prod), tool(Tool), helps(Tool, manufacture), helps(Tool, transform).
valid(P, Prod, Tool) :- place(P), product(Prod), tool(Tool), Prod = robot, (Tool = tape; Tool = paint).
valid_story(P, Prod, Tool, G) :- valid(P, Prod, Tool), gender(G), can_wear(G, Prod).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in WORKSHOPS:
        lines.append(asp.fact("place", place))
    for pid in PRODUCTS:
        lines.append(asp.fact("product", pid))
        for g in ["girl", "boy"]:
            lines.append(asp.fact("can_wear", g, pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def explain_rejection(place: str, product: str, tool: str) -> str:
    return (
        f"(No story: the combination {place}, {product}, and {tool} does not give a "
        f"funny manufacture-then-transformation path that is strong enough to tell.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld about manufacture, passion, and transformation.")
    ap.add_argument("--place", choices=WORKSHOPS)
    ap.add_argument("--product", choices=PRODUCTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.product is None or c[1] == args.product)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, product, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Aunt Nia", "Uncle Jo", "Grandpa Pip", "Ms. Ruby"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, product=product, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(WORKSHOPS[params.place], PRODUCTS[params.product], TOOLS[params.tool],
                 params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="tiny", product="robot", tool="tape", name="Milo", gender="boy", helper="Aunt Nia", trait="cheerful"),
    StoryParams(place="garage", product="crown", tool="paint", name="Mina", gender="girl", helper="Uncle Jo", trait="bouncy"),
    StoryParams(place="sunroom", product="kite", tool="glue", name="Theo", gender="boy", helper="Grandpa Pip", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, product, tool) combos ({len(stories)} with gender):\n")
        for place, prod, tool in triples:
            genders = sorted(g for (p, pr, t, g) in stories if (p, pr, t) == (place, prod, tool))
            print(f"  {place:8} {prod:8} {tool:8} [{', '.join(genders)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.product} in {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
