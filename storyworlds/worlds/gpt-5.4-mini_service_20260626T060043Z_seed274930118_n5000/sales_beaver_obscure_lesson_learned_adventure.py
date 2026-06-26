#!/usr/bin/env python3
"""
storyworlds/worlds/sales_beaver_obscure_lesson_learned_adventure.py
===================================================================

A small adventure storyworld about a beaver, a sales goal, and an obscure
lesson learned.

Seed premise:
- A beaver wants to make sales at a small riverside market.
- An obscure little item seems worthless at first.
- The journey turns on trying, failing, noticing a clue, and learning the
  item matters in a surprising way.

The world is simulated with physical meters and emotional memes:
- meters track things like stock, miles, mud, sales, and demand
- memes track hope, worry, curiosity, pride, and relief
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "beaver":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    description: str = ""


@dataclass
class StoryParams:
    place: str
    item: str
    goal: int
    seed: Optional[int] = None


@dataclass
class SalesItem:
    id: str
    label: str
    phrase: str
    obscure_reason: str
    boost: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy
        return World(place=copy.deepcopy(self.place), entities=copy.deepcopy(self.entities), facts=copy.deepcopy(self.facts))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "riverside": Place("riverside", "the riverside market", description="stalls line the water and lanterns swing in the wind"),
    "pinepath": Place("pinepath", "the pinepath trading road", description="a narrow road through tall pines and mossy stones"),
    "harbor": Place("harbor", "the harbor bazaar", description="boats bob near bright booths and gulls shout overhead"),
}

ITEMS = {
    "whistle": SalesItem(
        id="whistle",
        label="a tiny bone whistle",
        phrase="a tiny bone whistle with a soft note",
        obscure_reason="most shoppers think it looks too plain to matter",
        boost="its note can call tired forest animals from far away",
        tags={"sound", "helper", "obscure"},
    ),
    "map": SalesItem(
        id="map",
        label="a folded trail map",
        phrase="a folded trail map marked with secret shortcuts",
        obscure_reason="the folds hide the tiny marks unless someone looks closely",
        boost="it shows the safest and fastest paths through the woods",
        tags={"path", "helper", "obscure"},
    ),
    "seedpack": SalesItem(
        id="seedpack",
        label="a packet of river seeds",
        phrase="a packet of river seeds wrapped in brown paper",
        obscure_reason="it looks like plain paper until the right season comes",
        boost="the seeds grow into tasty reeds and berry vines",
        tags={"growing", "helper", "obscure"},
    ),
}

GOAL_LABELS = {
    3: "three sales",
    4: "four sales",
    5: "five sales",
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    beaver = world.add(Entity(id="beaver", kind="character", type="beaver", label="the beaver"))
    stall = world.add(Entity(id="stall", kind="thing", type="stall", label="the little stall"))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=beaver.id,
        meters={"stock": 1.0, "sales": 0.0, "demand": 0.0, "travel": 0.0},
    ))
    beaver.meters.update({"energy": 3.0, "sales": 0.0, "steps": 0.0})
    beaver.memes.update({"hope": 1.0, "worry": 0.0, "curiosity": 1.0, "pride": 0.0, "relief": 0.0})
    stall.meters.update({"signs": 1.0, "coins": 0.0})
    world.facts.update(beaver=beaver, item=item, stall=stall, place=place, goal=params.goal)
    return world


def _rule_walk(world: World) -> list[str]:
    b = world.get("beaver")
    item = world.get("item")
    if b.meters["steps"] >= 1 and item.meters["travel"] < 1:
        item.meters["travel"] = 1
        item.meters["stock"] -= 0.2
        return ["The beaver set out with the little stall pack and headed down the road."]
    return []


def _rule_interest(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["travel"] >= 1 and item.memes.get("noticed", 0) < 1:
        item.memes["noticed"] = 1
        item.meters["demand"] += 1
        return [f"A few passersby stopped when they saw {item.label}, curious about what it could do."]
    return []


def _rule_sale(world: World) -> list[str]:
    b = world.get("beaver")
    item = world.get("item")
    if item.meters["demand"] > item.meters["sales"]:
        item.meters["sales"] += 1
        b.meters["sales"] += 1
        b.memes["pride"] += 1
        if b.meters["sales"] == 1:
            return [f"The beaver made one careful sale, and the first coin chimed into the tin cup."]
        return [f"Another sale rang out, and the coin cup grew heavier."]
    return []


def _rule_obscure_lesson(world: World) -> list[str]:
    b = world.get("beaver")
    item = world.get("item")
    if item.meters["sales"] >= 1 and b.memes.get("lesson", 0) < 1:
        b.memes["lesson"] = 1
        b.memes["relief"] += 1
        return [f"The beaver learned that an obscure thing can still help when it solves a real need."]
    return []


RULES = [_rule_walk, _rule_interest, _rule_sale, _rule_obscure_lesson]


def simulate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                for s in out:
                    world.say(s)


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    b = world.get("beaver")
    item = world.get("item")
    place = world.place

    goal_text = GOAL_LABELS.get(params.goal, f"{params.goal} sales")
    world.say(
        f"At {place.label}, a beaver dreamed of making {goal_text} before the day grew dark."
    )
    world.say(
        f"It had only {item.label}, and most shoppers passed by because {ITEMS[params.item].obscure_reason}."
    )
    world.say(
        f"Still, the beaver felt curious and brave, so it packed the stall and started for {place.label}."
    )

    b.meters["steps"] += 1
    b.memes["hope"] += 1
    simulate(world)

    world.say(
        f"At first, the beaver nearly worried itself into giving up, but it listened to the people around the stall."
    )
    world.say(
        f"When one visitor needed help, {ITEMS[params.item].boost}, and that changed the day."
    )

    # drive sales toward the goal using a simple causal sequence
    while b.meters["sales"] < params.goal:
        item.meters["demand"] += 1
        before = b.meters["sales"]
        simulate(world)
        if b.meters["sales"] == before:
            b.meters["sales"] += 1
            item.meters["sales"] += 1
            world.say(f"Another sale rang out, and the coin cup grew heavier.")
        stall = world.get("stall")
        stall.meters["coins"] = b.meters["sales"]
        if b.meters["sales"] >= params.goal:
            break

    world.say(
        f"By sunset, the beaver had reached {goal_text}, and the obscure little item was the star of the stall."
    )
    world.say(
        f"It went home with a full heart, wiser than before, because the adventure taught that small, strange things can matter a lot."
    )

    world.facts["goal_text"] = goal_text
    world.facts["made_goal"] = b.meters["sales"] >= params.goal
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f"Write a child-friendly adventure story about a beaver trying to make sales with {ITEMS[item.id].label}.",
        f"Tell a short story where a beaver learns a lesson after bringing an obscure item to market.",
        f"Create an adventure tale with a beaver, a small stall, and an obscure object that turns out to help people.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    b = f["beaver"]
    item = f["item"]
    place = f["place"]
    goal_text = f["goal_text"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a beaver who wanted to make {goal_text} at {place.label}.",
        ),
        QAItem(
            question=f"What did the beaver hope to sell?",
            answer=f"The beaver hoped to sell {item.label}, which was {ITEMS[item.id].phrase}.",
        ),
        QAItem(
            question=f"Why did the beaver think the item was hard to sell at first?",
            answer=f"Most shoppers passed it by because {ITEMS[item.id].obscure_reason}.",
        ),
        QAItem(
            question="What changed the beaver's day?",
            answer=f"A visitor needed the item's help, so the beaver made a sale and learned the item could matter a lot.",
        ),
    ]
    if f.get("made_goal"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"The beaver reached {goal_text} by sunset, felt proud, and went home with a lesson learned.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    knowledge = {
        "obscure": [
            QAItem(
                question="What does obscure mean?",
                answer="If something is obscure, it is not well known or easy for people to notice at first.",
            )
        ],
        "beaver": [
            QAItem(
                question="What does a beaver like to do?",
                answer="A beaver likes to build, gather, and work with wood and water in its home area.",
            )
        ],
        "sales": [
            QAItem(
                question="What are sales?",
                answer="Sales are times when someone gives a thing to a customer in exchange for money.",
            )
        ],
        "lesson": [
            QAItem(
                question="What is a lesson learned?",
                answer="A lesson learned is something a character understands better after an experience changes their mind.",
            )
        ],
    }
    tags = {"obscure", "beaver", "sales", "lesson"}
    out: list[QAItem] = []
    for tag in ["beaver", "sales", "obscure", "lesson"]:
        if tag in tags:
            out.extend(knowledge[tag])
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(riverside). place(pinepath). place(harbor).
item(whistle). item(map). item(seedpack).
goal(3). goal(4). goal(5).

obscure(whistle).
obscure(map).
obscure(seedpack).

can_sell(whistle).
can_sell(map).
can_sell(seedpack).

valid(P,I,G) :- place(P), item(I), goal(G), obscure(I), can_sell(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("obscure", iid))
        lines.append(asp.fact("can_sell", iid))
    for g in GOAL_LABELS:
        lines.append(asp.fact("goal", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, i, g) for p in PLACES for i in ITEMS for g in GOAL_LABELS}
    asp_set = set(asp_valid_combos())
    if asp_set == py:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a beaver, sales, and an obscure lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--goal", type=int, choices=sorted(GOAL_LABELS))
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
    item = args.item or rng.choice(list(ITEMS))
    goal = args.goal or rng.choice(list(GOAL_LABELS))
    return StoryParams(place=place, item=item, goal=goal)


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


CURATED = [
    StoryParams(place="riverside", item="whistle", goal=3),
    StoryParams(place="pinepath", item="map", goal=4),
    StoryParams(place="harbor", item="seedpack", goal=5),
]


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
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
