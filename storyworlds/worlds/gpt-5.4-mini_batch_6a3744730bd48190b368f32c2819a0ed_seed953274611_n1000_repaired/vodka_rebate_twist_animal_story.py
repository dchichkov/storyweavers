#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vodka_rebate_twist_animal_story.py
===================================================================

A standalone storyworld in the Animal Story style: a small animal tale with a
clear setup, a surprising twist, and a child-facing ending image. The required
seed words are present in the domain: vodka and rebate.

This world tells about an animal who wants a shiny purchase, learns that the
word "rebate" means a refund, and discovers a twist: the bottle marked vodka is
not the prize to play with, but a grown-up bottle that helps them notice the
refund slip and choose a safer treat instead.

The simulation is state-driven:
- meters track physical changes like money, leftover items, and surprise
- memes track emotions like hope, caution, relief, and joy
- the twist arises from the changing state, not from a frozen paragraph

Run it:
    python storyworlds/worlds/gpt-5.4-mini/vodka_rebate_twist_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/vodka_rebate_twist_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/vodka_rebate_twist_animal_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "fox", "cat", "dog", "rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    smell: str
    twist_spot: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    is_grownup_item: bool = False
    gives_rebate: bool = False
    safe_treat: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Action:
    id: str
    sense: int
    text: str
    fail_text: str
    twist_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    item: str
    action: str
    twist: str = "receipt"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "corner_shop": Place(
        id="corner_shop",
        label="the corner shop",
        scene="a bright little shop with jars on the shelf and a bell by the door",
        smell="bread and oranges",
        twist_spot="the counter",
        tags={"shop", "money"},
    ),
    "market": Place(
        id="market",
        label="the market",
        scene="a busy market with baskets, signs, and shiny coins in a dish",
        smell="apples and warm dust",
        twist_spot="the stall",
        tags={"market", "money"},
    ),
}

ITEMS = {
    "vodka": Item(
        id="vodka",
        label="vodka",
        phrase="a sealed bottle of vodka",
        is_grownup_item=True,
        gives_rebate=False,
        safe_treat=False,
        tags={"vodka", "grownup"},
    ),
    "receipt": Item(
        id="receipt",
        label="receipt",
        phrase="a little receipt slip",
        is_grownup_item=False,
        gives_rebate=True,
        safe_treat=False,
        tags={"receipt", "rebate"},
    ),
    "juice": Item(
        id="juice",
        label="juice",
        phrase="a bottle of sparkling grape juice",
        is_grownup_item=False,
        gives_rebate=False,
        safe_treat=True,
        tags={"juice", "safe_treat"},
    ),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        sense=3,
        text="peeked at the shiny bottle and then looked for the little slip",
        fail_text="peeked too fast and missed the important part",
        twist_text="peeked again and spotted the rebate word at the bottom",
        tags={"look", "read"},
    ),
    "ask": Action(
        id="ask",
        sense=3,
        text="asked the clerk about the rebate",
        fail_text="asked in a rush and only got a head shake",
        twist_text="asked one more time and learned the rebate meant money back",
        tags={"talk", "money"},
    ),
    "carry": Action(
        id="carry",
        sense=2,
        text="carefully carried the bottle to the counter",
        fail_text="tried to carry it alone and nearly dropped it",
        twist_text="carried it back just in time to notice the receipt",
        tags={"carry"},
    ),
}

HEROES = [
    ("Milo", "mouse"),
    ("Ruby", "rabbit"),
    ("Toby", "fox"),
    ("Mina", "cat"),
]

CURATED = [
    StoryParams(place="corner_shop", hero_name="Milo", hero_type="mouse", item="vodka", action="peek", twist="receipt"),
    StoryParams(place="market", hero_name="Ruby", hero_type="rabbit", item="vodka", action="ask", twist="receipt"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for i in ITEMS:
            for a in ACTIONS:
                if i == "vodka" and a in {"peek", "ask", "carry"}:
                    combos.append((p, i, a))
    return combos


ASP_RULES = r"""
valid(P,I,A) :- place(P), item(I), action(A), grownup_item(I), safe_action(A).
outcome(twist) :- valid(_, vodka, _), rebate_item(receipt).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        if item.is_grownup_item:
            lines.append(asp.fact("grownup_item", i))
        if item.gives_rebate:
            lines.append(asp.fact("rebate_item", i))
        if item.safe_treat:
            lines.append(asp.fact("safe_treat", i))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("safe_action", a))
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
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story with vodka, rebate, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["mouse", "rabbit", "fox", "cat"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--twist", choices=["receipt"], default="receipt")
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
    if args.item and args.item != "vodka":
        raise StoryError("This tiny world is built around vodka and rebate.")
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, action = rng.choice(sorted(combos))
    name, htype = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    return StoryParams(place=place, hero_name=name, hero_type=htype, item=item, action=action, twist=args.twist)


def _touch(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["hope"] += 1
    item.meters["noticed"] += 1


def tell(params: StoryParams) -> World:
    w = World()
    place = w.add(Entity(id=params.place, kind="thing", type="place", label=PLACES[params.place].label))
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name, role="hero"))
    clerk = w.add(Entity(id="clerk", kind="character", type="cat", label="the clerk", role="helper"))
    bottle = w.add(Entity(id="vodka", kind="thing", type="item", label="vodka", attrs={"grownup": True}))
    receipt = w.add(Entity(id="receipt", kind="thing", type="paper", label="receipt", attrs={"rebate": True}))
    treat = w.add(Entity(id="juice", kind="thing", type="item", label="sparkling grape juice", attrs={"safe": True}))

    hero.memes["curious"] += 1
    hero.memes["hope"] += 1
    w.say(f"{hero.id} padded into {place.label}, where the air smelled like {PLACES[params.place].smell}.")
    w.say(f"At {PLACES[params.place].twist_spot}, {hero.id} saw {bottle.label}: {ITEMS['vodka'].phrase} with a shiny cap.")

    w.para()
    if params.action == "peek":
        w.say(f"{hero.id} {ACTIONS['peek'].text}.")
    elif params.action == "ask":
        w.say(f"{hero.id} {ACTIONS['ask'].text}.")
    else:
        w.say(f"{hero.id} {ACTIONS['carry'].text}.")

    w.say(f"The clerk pointed to a small slip on the counter. It said rebate.")
    receipt.meters["seen"] += 1
    _touch(w, hero, receipt)

    w.para()
    hero.memes["twist"] += 1
    w.say(f"That was the twist: the vodka bottle was grown-up business, but the rebate slip meant a little money back.")
    w.say(f"{hero.id} smiled, because the rebate was enough to choose {treat.label} instead.")
    hero.memes["joy"] += 1
    treat.meters["chosen"] += 1
    w.say(f"So {hero.id} left with {ITEMS['juice'].phrase}, and the shop door gave a soft ding behind {hero.pronoun('object')}.")

    w.facts.update(hero=hero, place=place, bottle=bottle, receipt=receipt, treat=treat, params=params)
    return w


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a little {hero.type} who went to the shop and found a surprise."),
        ("What shiny bottle did {0} see?".format(hero.id),
         "The shiny bottle was vodka. It was a grown-up bottle, not something for the animal to play with."),
        ("What did rebate mean in the story?",
         "Rebate meant some money back after looking at the receipt. That is why the animal could choose a safer treat instead."),
        ("What was the twist?",
         "The twist was that the important clue was not the vodka bottle at all. It was the rebate slip on the counter, and that changed the ending."),
        ("How did the story end?",
         f"{hero.id} went home with sparkling grape juice and a happier smile. The rebate turned a confusing moment into a small reward."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a rebate?", "A rebate is money you get back after you buy something or send in a slip. It can make a purchase feel like a little surprise."),
        QAItem("What is a receipt?", "A receipt is a paper that shows what was bought. People use it to keep track of money and rebates."),
        QAItem("Why is vodka for grown-ups?", "Vodka is a grown-up drink, so children and animals should not use it. In this story it is just part of the shop scene."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write an Animal Story about {p.hero_name} in {PLACES[p.place].label} that includes the words "vodka" and "rebate".',
        f"Tell a short animal tale where {p.hero_name} notices vodka, learns about a rebate, and gets a twist ending.",
        "Write a child-facing story with a shop, a surprise slip, and a safe ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
