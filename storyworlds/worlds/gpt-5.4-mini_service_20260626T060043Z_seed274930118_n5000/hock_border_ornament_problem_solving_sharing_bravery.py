#!/usr/bin/env python3
"""
storyworlds/worlds/hock_border_ornament_problem_solving_sharing_bravery.py
===========================================================================

A small adventure storyworld about a child, a border path, and a fragile
ornament that needs brave hands, sharing, and a clever fix.

Seed tale imagined for this world:
---
A child and a friend travel to a windy border trail to look for a missing
ornament that once marked the path. The wind loosens it, and the child must
solve the problem without crossing the border carelessly. They borrow rope,
share the task, and bravely climb the gate to save the ornament before it falls
into the ditch.

World design:
---
- Physical meters model things like height, balance, looseness, wind, distance,
  and repair progress.
- Emotional memes model worry, bravery, trust, generosity, and relief.
- The story is generated from state changes, not from a frozen paragraph.
- The key narrative instruments are Problem Solving, Sharing, and Bravery.
- The seed words hock, border, and ornament are baked into the world vocabulary.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    border: bool = False
    windy: bool = False
    high_ground: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    danger: str
    verb: str
    fix: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    shares: bool = True
    bravery_need: float = 1.0
    prep: str = ""
    tail: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.lines = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


PROBLEM = Problem(
    id="ornament_fall",
    name="the ornament might fall off the border gate",
    danger="the ornament could drop into the ditch",
    verb="fix the ornament",
    fix="tie it back on with a shared rope",
    clue="the wind keeps shaking the ribbon loose",
    tags={"ornament", "border", "wind"},
)

TOOLS = [
    Tool(
        id="rope",
        label="a short rope",
        helps={"ornament_fall"},
        shares=True,
        bravery_need=1.0,
        prep="hold the rope together",
        tail="tied the ornament back in place",
    ),
    Tool(
        id="hook",
        label="a little hook",
        helps={"ornament_fall"},
        shares=True,
        bravery_need=1.2,
        prep="use the hook carefully",
        tail="set the ornament safely back on its peg",
    ),
]

PLACES = {
    "border_gate": Place(
        id="border_gate",
        label="the windy border gate",
        border=True,
        windy=True,
        high_ground=True,
        affords={"climb", "repair", "share"},
    ),
    "orchard_edge": Place(
        id="orchard_edge",
        label="the orchard edge",
        border=True,
        windy=False,
        high_ground=False,
        affords={"climb", "repair", "share"},
    ),
}

NAMES = ["Nora", "Milo", "Ada", "Leo", "Ivy", "Finn", "Zoe", "Ben"]
FRIEND_NAMES = ["Pip", "Bea", "Jory", "Mina", "Tess", "Oren"]
TRAITS = ["curious", "kind", "careful", "brave", "quick-thinking", "helpful"]


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a border ornament and brave problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TOOLS if p in ("border_gate", "orchard_edge")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hero=hero, friend=friend, trait=trait)


def _m(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _q(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="child", traits=["little", params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", traits=["little", "helpful"]))
    keeper = world.add(Entity(id="keeper", kind="character", type="adult", label="the gate keeper"))
    ornament = world.add(Entity(
        id="ornament",
        type="ornament",
        label="a bright glass ornament",
        phrase="a bright glass ornament with a red ribbon",
        owner="keeper",
        caretaker="keeper",
    ))
    border = world.add(Entity(
        id="border",
        type="border",
        label="the border gate",
        phrase=world.place.label,
    ))
    rope = world.add(Entity(id="rope", type="tool", label="rope", phrase="a short rope"))
    hook = world.add(Entity(id="hook", type="tool", label="hook", phrase="a little hook"))
    world.facts.update(hero=hero, friend=friend, keeper=keeper, ornament=ornament, border=border, rope=rope, hook=hook)
    return world


def predict_fall(world: World, tool: Tool) -> bool:
    return world.place.windy and "ornament" in tool.helps


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    keeper = world.facts["keeper"]
    ornament = world.facts["ornament"]

    _q(hero, "curiosity", 1)
    _q(hero, "trust", 1)
    world.say(f"{hero.id} was a {params.trait} child who loved adventures near {world.place.label}.")
    world.say(f"{friend.id} was the sort of friend who stayed close when a trail looked tricky.")
    world.say(f"At the border gate, {world.place.label.lower()} held {ornament.phrase}, and everyone liked how it shone.")

    world.para()
    _m(ornament, "looseness", 1.0 if world.place.windy else 0.5)
    _q(hero, "worry", 1)
    world.say(f"Then the wind tugged at the ribbon, and the ornament began to wobble.")
    world.say(f"{keeper.pronoun('subject').capitalize()} said, \"The border wind can shake it loose if nobody helps.\"")
    world.say(f"{hero.id} looked up and saw the problem right away: {PROBLEM.clue}.")

    world.para()
    _q(hero, "bravery", 1)
    _q(friend, "sharing", 1)
    world.say(f"{hero.id} took a deep breath and said, \"We can solve this together.\"")
    world.say(f"{friend.id} shared the rope, and {hero.id} shared the hard job of climbing first.")
    if world.place.high_ground:
        world.say(f"Together they stepped carefully up to the gate beam, where the wind felt strong but not scary.")
    else:
        world.say(f"Together they reached the low stone post beside the gate, where the wind still pushed at their sleeves.")

    tool = TOOLS[0]
    if predict_fall(world, tool):
        _m(ornament, "repair", 1.0)
        _q(hero, "problem_solving", 1)
        _q(friend, "bravery", 1)
        world.say(f"{hero.id} and {friend.id} used {tool.label} to hold the ribbon steady.")
        world.say(f"They {tool.tail}, and the bright ornament stopped shaking.")
    else:
        tool = TOOLS[1]
        _m(ornament, "repair", 1.0)
        _q(hero, "problem_solving", 1)
        world.say(f"At last {hero.id} chose {tool.label}, which fit the little peg better.")
        world.say(f"With a careful twist, they {tool.tail}.")

    world.para()
    _q(keeper, "relief", 1)
    _q(hero, "joy", 1)
    _q(friend, "joy", 1)
    world.say(f"{keeper.id} smiled with relief, because the ornament was safe again at the border.")
    world.say(f"{hero.id} and {friend.id} climbed down, sharing one proud grin and one dusty rope.")
    world.say(f"The gate still stood in the evening breeze, and the ornament flashed like a tiny star over the trail.")

    world.facts.update(place=world.place, tool=tool, resolved=True)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    keeper = f["keeper"]
    ornament = f["ornament"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who solved the problem at {place} when the ornament started to wobble?",
            answer=f"{hero.id} solved it with {friend.id} by sharing the work and fixing the ribbon together.",
        ),
        QAItem(
            question=f"What was the problem near the border gate?",
            answer=f"The problem was that {ornament.label} could fall off the gate when the wind tugged at it.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} show sharing?",
            answer=f"They shared the rope, shared the climbing, and worked together instead of leaving one child to do everything.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by taking a deep breath, climbing up first, and helping fix the ornament even though the wind was strong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a border?",
            answer="A border is a line or edge that separates one place from another, like the edge of a path or gate.",
        ),
        QAItem(
            question="What is an ornament?",
            answer="An ornament is a decoration that is made to look pretty, like something bright hanging on a gate or tree.",
        ),
        QAItem(
            question="What does hock mean?",
            answer="Hock can mean to sell something for money, but in this story world it is also a word that belongs to the adventure theme and helps name the world.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write an adventure story for young children about {hero.id} and {friend.id} at a border gate with a shining ornament.",
        f"Tell a brave, child-friendly story where friends solve a problem by sharing a rope and fixing an ornament at the border.",
        f"Write a short adventure tale that includes the words hock, border, and ornament, and ends with a safe solution.",
    ]


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
place(border_gate).
place(orchard_edge).

problem(ornament_fall).
tool(rope).
tool(hook).

border_place(border_gate).
border_place(orchard_edge).

windy(border_gate).

helps(rope, ornament_fall).
helps(hook, ornament_fall).

shareable(rope).
shareable(hook).

brave_fix(T) :- tool(T), helps(T, ornament_fall), shareable(T).

valid_story(P, T) :- place(P), border_place(P), brave_fix(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.border:
            lines.append(asp.fact("border_place", p.id))
        if p.windy:
            lines.append(asp.fact("windy", p.id))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in t.helps:
            lines.append(asp.fact("helps", t.id, g))
        if t.shares:
            lines.append(asp.fact("shareable", t.id))
    lines.append(asp.fact("problem", PROBLEM.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, t.id) for p in PLACES.values() for t in TOOLS if p.border and t.id in {"rope", "hook"}}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


CURATED = [
    StoryParams(place="border_gate", hero="Nora", friend="Pip", trait="brave"),
    StoryParams(place="orchard_edge", hero="Milo", friend="Bea", trait="curious"),
    StoryParams(place="border_gate", hero="Ivy", friend="Tess", trait="helpful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid story pairs:")
        for p, t in vals:
            print(f"  {p} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} (friend: {p.friend})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
