#!/usr/bin/env python3
"""
A small superhero storyworld about a gal, a surprise, and the word squinch.

The seed image:
- A cheerful gal wants to help in a city.
- A surprise shows up and changes the mission.
- The turn is physical: the gal's gadget or power must fit the problem.
- The ending proves the city is safer and the gal feels brave.

This file keeps the story grounded in a tiny world model with meters and memes.
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("damage", "soot", "alarm", "joy", "brave", "surprise"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    place: str
    surprise: str
    danger: str
    rescue_tool: str
    tool_covers: set[str]
    tool_fixes: set[str]


@dataclass
class StoryParams:
    city: str
    hero_name: str
    hero_type: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.city)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a surprise.")
    ap.add_argument("--city", choices=CITIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl"])
    ap.add_argument("--sidekick", choices=["cat", "robot", "bird"])
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
    return [(cid, "girl") for cid in CITIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.city:
        combos = [c for c in combos if c[0] == args.city]
    if not combos:
        raise StoryError("No valid story matches the chosen options.")
    city, _ = rng.choice(combos)
    hero_name = args.name or rng.choice(["Mina", "Luna", "Rae", "Tess", "Nia"])
    sidekick = args.sidekick or rng.choice(["cat", "robot", "bird"])
    return StoryParams(city=city, hero_name=hero_name, hero_type="girl", sidekick=sidekick)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CITIES.items():
        lines.append(asp.fact("city", cid))
        lines.append(asp.fact("surprise", cid, c.surprise))
        lines.append(asp.fact("danger", cid, c.danger))
        lines.append(asp.fact("tool", cid, c.rescue_tool))
        for cov in sorted(c.tool_covers):
            lines.append(asp.fact("covers", c.rescue_tool, cov))
        for fix in sorted(c.tool_fixes):
            lines.append(asp.fact("fixes", c.rescue_tool, fix))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C) :- city(C), surprise(C,_), danger(C,_), tool(C,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = {(cid,) for cid, _ in valid_combos()}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def predict_damage(world: World, hero: Entity) -> bool:
    sim = world.copy()
    hero2 = sim.entities[hero.id]
    hero2.meters["surprise"] += 1
    return sim.city.danger in {"fire", "flood", "shadow"}


def tell(city: City, params: StoryParams) -> World:
    w = World(city)
    hero = w.add(Entity(id=params.hero_name, kind="character", type="girl"))
    side = w.add(Entity(id="sidekick", kind="character", type=params.sidekick, label=params.sidekick))
    tool = w.add(Entity(id="tool", type="tool", label=city.rescue_tool, protective=True, covers=set(city.tool_covers)))
    tool.worn_by = hero.id
    hero.memes["joy"] += 1
    w.say(f"{hero.id} was a brave gal who liked to squinch her shoulders before a big day.")
    w.say(f"She and her {side.label} sidekick watched the sun over {city.place}, ready to help.")
    w.say(f"Then a Surprise hit the city: {city.surprise}.")
    hero.meters["surprise"] += 1
    hero.memes["surprise"] += 1
    w.say(f"{hero.id} blinked fast, then said, 'I can fix this.'")
    if predict_damage(w, hero):
        hero.meters["damage"] += 1
    if city.danger == "fire":
        hero.memes["alarm"] += 1
        w.say(f"A crackly fire curled near the square, and smoke tried to cover the windows.")
    elif city.danger == "flood":
        hero.memes["alarm"] += 1
        w.say(f"Water rushed into the street, and the puddles kept growing.")
    else:
        w.say(f"A shadowy snatchy shape slipped along the roofs and grabbed bright things.")
    if city.rescue_tool == "squinch-shield":
        w.say(f"She lifted her squinch-shield, and the strange shimmer pushed the trouble back.")
    elif city.rescue_tool == "sky rope":
        w.say(f"She snapped out her sky rope and pulled the trapped cat to safety.")
    else:
        w.say(f"She used her bright lantern to show the right path and calm the crowd.")
    hero.memes["brave"] += 1
    hero.memes["joy"] += 1
    w.say(f"By the end, the Surprise was gone, the city was safe, and {hero.id} smiled at the quiet sky.")
    w.facts.update(hero=hero, sidekick=side, tool=tool, params=params)
    return w


def generate(params: StoryParams) -> StorySample:
    city = CITIES[params.city]
    world = tell(city, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short superhero story for a child about a gal named {params.hero_name} and a Surprise in {city.place}.",
            f"Tell a gentle superhero tale where a gal uses a {city.rescue_tool} to handle {city.surprise}.",
            f"Write a story that includes the word squinch and ends with a brave gal saving the day.",
        ],
        story_qa=[
            QAItem(
                question=f"Who is the story about?",
                answer=f"It is about a brave gal named {params.hero_name}.",
            ),
            QAItem(
                question=f"What surprise happened in {city.place}?",
                answer=f"The city got {city.surprise}.",
            ),
            QAItem(
                question=f"What helped {params.hero_name} fix the problem?",
                answer=f"The {city.rescue_tool} helped her handle the trouble.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What does squinch mean in the story?",
                answer="It means to squeeze your shoulders or face in a tiny determined way.",
            ),
            QAItem(
                question="What is a hero?",
                answer="A hero is someone who tries to help other people when things go wrong.",
            ),
        ],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    if qa:
        print("\n== Q&A ==")
        for q in sample.story_qa + sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for cid in CITIES:
            p = StoryParams(city=cid, hero_name="Mina", hero_type="girl", sidekick="robot")
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


CITIES = {
    "starport": City(
        name="Starport",
        place="Starport Square",
        surprise="a sudden confetti storm",
        danger="shadow",
        rescue_tool="squinch-shield",
        tool_covers={"air", "light"},
        tool_fixes={"shadow"},
    ),
    "sunharbor": City(
        name="Sunharbor",
        place="Sunharbor Avenue",
        surprise="a balloon parade gone wobbly",
        danger="fire",
        rescue_tool="bright lantern",
        tool_covers={"dark"},
        tool_fixes={"panic"},
    ),
    "rivergate": City(
        name="Rivergate",
        place="Rivergate Bridge",
        surprise="a splashy flood from the canal",
        danger="flood",
        rescue_tool="sky rope",
        tool_covers={"water"},
        tool_fixes={"flood"},
    ),
}


if __name__ == "__main__":
    main()
