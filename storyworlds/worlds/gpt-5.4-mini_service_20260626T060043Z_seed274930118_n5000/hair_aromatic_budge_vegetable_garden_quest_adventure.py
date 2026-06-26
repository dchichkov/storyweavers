#!/usr/bin/env python3
"""
storyworlds/worlds/hair_aromatic_budge_vegetable_garden_quest_adventure.py
===========================================================================

A small adventure storyworld: a child goes on a quest in a vegetable garden,
meets a stubborn obstacle, and finds a gentle way to budge it.

The world is built around a simple source-tale shape:
- a child with hair gets ready for a garden quest,
- something aromatic draws them onward,
- a small obstacle will not budge,
- the child learns how to solve the problem and ends with a change in state.

This script keeps the domain tiny and classical:
- physical state: objects have meters like stuck, ripe, fragrant, damp, muddy
- emotional state: characters have memes like curiosity, determination, delight

The generated story should feel like a short Adventure: concrete, child-facing,
and state-driven.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Garden:
    place: str = "the vegetable garden"
    aromas: set[str] = field(default_factory=set)
    grows: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    reason: str
    requires: str
    kind: str = "obstacle"


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    scent: str = ""
    reason: str = ""


@dataclass
class Tool:
    id: str
    label: str
    action: str
    fits: set[str]
    solves: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.garden)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _narrate_stuck(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    obstacle = world.facts["obstacle"]
    item = world.facts["quest_item"]
    if child.memes.get("determination", 0.0) < THRESHOLD:
        return out
    if obstacle.meters.get("stuck", 0.0) < THRESHOLD:
        return out
    sig = ("stuck", obstacle.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"But the {obstacle.label} would not budge.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    produced.extend(_narrate_stuck(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_setting_detail(garden: Garden, item: QuestItem) -> str:
    if item.scent:
        return f"The air in {garden.place} felt aromatic, with a sweet smell drifting past the bean rows."
    return f"{garden.place.capitalize()} was bright and busy, with leaves and stems reaching for the light."


def find_reasonable_tool(item: QuestItem, obstacle: Obstacle) -> Optional[Tool]:
    for tool in TOOLS:
        if item.reason in tool.fits and obstacle.requires in tool.solves:
            return tool
    return None


def predict_outcome(world: World, child: Entity, obstacle: Entity, item: Entity, tool: Optional[Tool]) -> bool:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_obstacle = sim.get(obstacle.id)
    sim_item = sim.get(item.id)
    sim_child.memes["determination"] = 1.0
    if tool is not None:
        sim_item.meters["safe"] = 1.0
        sim_obstacle.meters["stuck"] = 0.0
    else:
        sim_obstacle.meters["stuck"] = 1.0
    propagate(sim, narrate=False)
    return sim_obstacle.meters.get("stuck", 0.0) < THRESHOLD


def tell(garden: Garden, hero_name: str, hero_type: str, parent_type: str, item: QuestItem, obstacle: Obstacle) -> World:
    world = World(garden)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    quest_item = world.add(Entity(
        id="quest_item",
        type="thing",
        label=item.label,
        phrase=item.phrase,
        plural=item.plural,
        owner=hero.id,
        caretaker=parent.id,
        meters={"ripe": 1.0, "fragrant": 1.0 if item.scent else 0.0},
    ))
    obst = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.reason,
        meters={"stuck": 1.0},
    ))

    world.facts.update(child=hero, parent=parent, quest_item=quest_item, obstacle=obst, item_cfg=item)
    world.say(f"{hero_name} was a curious {hero_type} who loved any quest with a clear destination.")
    world.say(f"One day, {hero_name} stepped into {garden.place} for a small adventure and noticed {story_setting_detail(garden, item)}")
    world.say(f"{hero_name} carried a little plan: find the {item.label} before it was missed.")
    world.para()
    world.say(f"{hero_name} followed the aromatic breeze between the carrots and the beans.")
    hero.memes["curiosity"] = 1.0
    hero.memes["determination"] = 1.0
    world.say(f"{hero_name} wanted to reach the {item.label}, but the {obstacle.label} was in the way.")
    propagate(world, narrate=True)
    if not predict_outcome(world, hero, obst, quest_item, None):
        world.say(f"{parent.pronoun().capitalize()} noticed the problem and nodded toward a simple tool.")
    world.para()
    tool = find_reasonable_tool(item, obstacle)
    if tool is None:
        raise StoryError("No reasonable tool exists for this quest and obstacle.")
    if not predict_outcome(world, hero, obst, quest_item, tool):
        raise StoryError("The suggested tool would not solve the obstacle.")
    hero.memes["delight"] = 1.0
    world.say(f"{hero_name}'s {parent.type if parent.type != 'mother' else 'mom'} smiled and said, \"Let's {tool.prep}.\"")
    world.say(f"{hero_name} used the {tool.label} to {tool.action}, and the {obstacle.label} finally gave way.")
    obst.meters["stuck"] = 0.0
    quest_item.meters["safe"] = 1.0
    world.say(f"At last, {hero_name} reached the {item.label}, and the aromatic garden air seemed even sweeter.")
    world.say(f"{hero_name} went home with the {item.label}, proud that the little obstacle had budged at last.")
    world.facts["tool"] = tool
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    obstacle: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GARDENS = {
    "vegetable_garden": Garden(place="the vegetable garden", aromas={"herb", "tomato", "bean"}, grows={"bean", "carrot", "pea", "mint"}),
}

ITEMS = {
    "beanbasket": QuestItem(
        id="beanbasket",
        label="bean basket",
        phrase="a small bean basket",
        region="hands",
        scent="aromatic",
        reason="hands",
    ),
    "mintsprig": QuestItem(
        id="mintsprig",
        label="mint sprig",
        phrase="a little mint sprig",
        region="hands",
        scent="aromatic",
        reason="hands",
    ),
    "carrotbundle": QuestItem(
        id="carrotbundle",
        label="carrot bundle",
        phrase="a bright carrot bundle",
        region="hands",
        scent="earthy",
        reason="hands",
    ),
}

OBSTACLES = {
    "stuckgate": Obstacle(
        id="stuckgate",
        label="garden gate latch",
        reason="stuck",
        requires="lever",
    ),
    "buriedpot": Obstacle(
        id="buriedpot",
        label="buried plant pot",
        reason="stuck",
        requires="lift",
    ),
}

TOOLS = [
    Tool(
        id="little_hoe",
        label="a little hoe",
        action="wiggle the latch",
        fits={"hands"},
        solves={"lever"},
        prep="use a little hoe to wiggle the latch",
        tail="used the hoe and smiled",
    ),
    Tool(
        id="trowel",
        label="a small trowel",
        action="pry up the edge",
        fits={"hands"},
        solves={"lift"},
        prep="use a small trowel to pry it up",
        tail="used the trowel and laughed",
    ),
    Tool(
        id="watering_can",
        label="a watering can",
        action="soak the dirt around it",
        fits={"hands"},
        solves={"lift"},
        prep="pour a little water around the edge",
        tail="poured water and watched it loosen",
    ),
]

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ada", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Sam"]
TRAITS = ["curious", "brave", "gentle", "spirited", "patient", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, garden in GARDENS.items():
        for item_id in ITEMS:
            item = ITEMS[item_id]
            for obst_id in OBSTACLES:
                obst = OBSTACLES[obst_id]
                if find_reasonable_tool(item, obst) is not None:
                    combos.append((place, item_id, obst_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["child"]
    item = f["item_cfg"]
    return [
        f'Write a short adventure story for a preschooler set in {world.garden.place} with the word "{item.scent}".',
        f"Tell a gentle quest story where {hero.id} wants to find a {item.label} in {world.garden.place} and something would not budge.",
        f"Write a simple story about a child, an aromatic garden path, and a problem that can be solved with the right tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["child"]
    parent = f["parent"]
    item = f["quest_item"]
    obst = f["obstacle"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What kind of place was {world.facts['child'].id} exploring?",
            answer=f"{hero.id} was exploring {world.garden.place}, which is a vegetable garden full of growing plants and garden scents.",
        ),
        QAItem(
            question=f"What made the garden feel aromatic during the quest?",
            answer=f"The air felt aromatic because the garden had sweet smells drifting through it, especially near the herbs and beans.",
        ),
        QAItem(
            question=f"What would not budge in the story?",
            answer=f"The {obst.label} would not budge until the right tool was used.",
        ),
        QAItem(
            question=f"What did {parent.id} suggest to help?",
            answer=f"{parent.id} suggested using {tool.label}, which could solve the stuck problem and let the quest continue.",
        ),
        QAItem(
            question=f"What did {hero.id} finally reach at the end?",
            answer=f"{hero.id} finally reached the {item.label}, and the quest ended happily with the obstacle fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow vegetables like beans, carrots, and peas.",
        ),
        QAItem(
            question="What does aromatic mean?",
            answer="Aromatic means it smells pleasant or strong in a nice way.",
        ),
        QAItem(
            question="What does budge mean?",
            answer="To budge something means to move it a little when it is stuck or hard to move.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve a problem, or reach a goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="vegetable_garden", item="beanbasket", obstacle="stuckgate", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="vegetable_garden", item="mintsprig", obstacle="buriedpot", name="Leo", gender="boy", parent="father", trait="brave"),
]


def explain_rejection() -> str:
    return "(No story: this quest needs a reasonable obstacle and a tool that can budge it.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure in a vegetable garden quest world.")
    ap.add_argument("--place", choices=GARDENS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.obstacle is None or c[2] == args.obstacle)]
    if not combos:
        raise StoryError(explain_rejection())
    place, item, obstacle = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, obstacle=obstacle, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(GARDENS[params.place], params.name, params.gender, params.parent, ITEMS[params.item], OBSTACLES[params.obstacle])
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


ASP_RULES = r"""
% A quest item is at risk if the obstacle is stuck and the item is in the garden.
at_risk(I, O) :- item(I), obstacle(O), stuck(O), quest_item(I).

% A tool is reasonable when it fits the item's region and solves the obstacle type.
reasonable(T, I, O) :- tool(T), at_risk(I, O), fits(T, hands), solves(T, lever).
reasonable(T, I, O) :- tool(T), at_risk(I, O), fits(T, hands), solves(T, lift).

valid_story(P, I, O) :- place(P), item(I), obstacle(O), valid_combo(P, I, O).
valid_combo(P, I, O) :- garden(P), quest_item(I), obstacle(O), at_risk(I, O), reasonable(_, I, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, garden in GARDENS.items():
        lines.append(asp.fact("garden", pid))
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("quest_item", iid))
    for oid, obst in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("stuck", oid))
    for tid, tool in zip([t.id for t in TOOLS], TOOLS):
        lines.append(asp.fact("tool", tid))
        for f in sorted(tool.fits):
            lines.append(asp.fact("fits", tid, f))
        for s in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
