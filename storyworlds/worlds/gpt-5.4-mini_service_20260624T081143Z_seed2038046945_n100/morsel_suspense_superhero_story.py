#!/usr/bin/env python3
"""
storyworlds/worlds/morsel_suspense_superhero_story.py
=====================================================

A small superhero suspense storyworld about a hungry hero, a tiny morsel, and
a tense rescue that ends with a safe, satisfying bite.

Seed-tale sketch:
---
In a bright city, a young superhero named Spark wanted to keep the neighborhood
safe. One windy evening, Spark spotted a tiny golden morsel rolling across a
rooftop toward the edge of the skybridge. The morsel was special: it was the last
crumb from a lunch saved for the team, and it was about to vanish into the dark.

Spark had to choose fast. If the morsel fell, the little robot helper would be
sad and the city watch would lose their snack. Spark raced over the roof, used a
grappling line, and snatched the morsel just before it dropped. The helper cheered,
and Spark shared the rescued bite with the team.

Story shape:
- setup: introduce hero, helper, city, and the cherished morsel
- tension: a gust and a dangerous ledge create suspense
- turn: hero uses gear and clever movement to reach the morsel
- resolution: morsel is saved, the team calms down, and the ending image proves it
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    city: str = "the city"
    roof: str = "the rooftop"
    affords: set[str] = field(default_factory=lambda: {"swoop", "run", "glide"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


@dataclass
class HeroSpec:
    name: str
    type: str
    trait: str
    suit_color: str


@dataclass
class StoryParams:
    city: str
    hero: str
    sidekick: str
    gear: str
    morsel: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


HEROES = [
    HeroSpec("Spark", "boy", "brave", "red"),
    HeroSpec("Nova", "girl", "quick", "blue"),
    HeroSpec("Comet", "boy", "kind", "silver"),
    HeroSpec("Vector", "girl", "clever", "gold"),
]
SIDEKICKS = [
    ("Chip", "robot helper", "small and round"),
    ("Midge", "bat helper", "tiny and swift"),
    ("Pip", "bird helper", "bright-eyed"),
]
GAMES = {
    "morsel": Gear("gripline", "grappling line", "use the grappling line", "came back safely with the line"),
}
CITIES = ["Harbor City", "Bright Bay", "Sunbeam City"]


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
gear(G) :- gear_name(G).
morsel(M) :- morsel_name(M).
compatible_story(C,H,S,G,M) :- city(C), hero(H), sidekick(S), gear(G), morsel(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for c in CITIES:
        lines.append(asp.fact("city", c))
    for h in HEROES:
        lines.append(asp.fact("hero_name", h.name))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", s[0]))
    for g in GAMES.values():
        lines.append(asp.fact("gear_name", g.label))
    lines.append(asp.fact("morsel_name", "morsel"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero suspense storyworld with a rescued morsel.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=[h.name for h in HEROES])
    ap.add_argument("--sidekick", choices=[s[0] for s in SIDEKICKS])
    ap.add_argument("--gear", choices=[g.label for g in GAMES.values()])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    city = args.city or rng.choice(CITIES)
    hero = args.hero or rng.choice([h.name for h in HEROES])
    sidekick = args.sidekick or rng.choice([s[0] for s in SIDEKICKS])
    gear = args.gear or "grappling line"
    return StoryParams(city=city, hero=hero, sidekick=sidekick, gear=gear, morsel="morsel")

def reasonableness_gate(params: StoryParams) -> None:
    if params.morsel != "morsel":
        raise StoryError("This world only knows one tiny rescued morsel.")
    if params.gear != "grappling line":
        raise StoryError("The grappling line is the only gear that can catch the morsel in time.")

def tell(params: StoryParams) -> World:
    scene = Scene(city=params.city)
    world = World(scene)
    hero_spec = next(h for h in HEROES if h.name == params.hero)
    side_spec = next(s for s in SIDEKICKS if s[0] == params.sidekick)
    hero = world.add(Entity(id=hero_spec.name, kind="character", type=hero_spec.type))
    sidekick = world.add(Entity(id=side_spec[0], kind="character", type="robot"))
    morsel = world.add(Entity(id="morsel", type="morsel", label="morsel", owner=hero.id, caretaker=sidekick.id))
    gear = world.add(Entity(id="gear", type="gear", label=params.gear, owner=hero.id, protective=True))

    world.say(f"{hero.id} was a {hero_spec.trait} superhero in {params.city}, with a {sidekick.id} that hummed beside {hero.pronoun('object')}.")
    world.say(f"One evening, the team carried a tiny golden morsel for their late snack, and {sidekick.id} kept it on a tray near the roof door.")
    world.para()
    world.say(f"Then a hard wind swept over {scene.roof}, and the morsel began to roll toward the edge.")
    hero.memes["worry"] = 1
    sidekick.memes["fear"] = 1
    world.say(f"{hero.id} froze for one breath, because the ledge was narrow and the dark street yawned far below.")
    world.para()
    world.say(f"At once, {hero.id} snapped on the {gear.label} and leapt forward.")
    world.say(f"{hero.pronoun().capitalize()} swung the line, hooked the tray, and pulled the morsel back before it could fall.")
    hero.memes["relief"] = 1
    sidekick.memes["joy"] = 1
    morsel.meters["saved"] = 1
    world.para()
    world.say(f"{sidekick.id} beeped with joy, and {hero.id} smiled as the rescued morsel was shared in the warm light of the rooftop.")
    world.say(f"The wind kept blowing, but now the morsel sat safe in {hero.pronoun('possessive')} hand, and the night felt brave again.")

    world.facts.update(hero=hero, sidekick=sidekick, morsel=morsel, gear=gear, params=params, scene=scene)
    return world

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a suspenseful superhero story about {p.hero} in {p.city} who must rescue a tiny morsel.",
        f"Tell a child-friendly superhero tale where a gust of wind threatens a snack and a grappling line saves it.",
        f"Make a short story with a brave hero, a worried helper, and one precious morsel on a rooftop.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Who saved the morsel in {p.city}?",
            answer=f"{hero.id} saved the morsel with a grappling line after the wind pushed it toward the edge.",
        ),
        QAItem(
            question=f"Why was {sidekick.id} worried?",
            answer=f"{sidekick.id} was worried because the morsel rolled toward the rooftop edge, and a fall into the street would have lost the team's snack.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The hero pulled the morsel back, the helper beeped with joy, and the snack stayed safe in the hero's hand.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a morsel?",
            answer="A morsel is a tiny bite of food, small enough to be eaten in one or two bites.",
        ),
        QAItem(
            question="What does a grappling line do?",
            answer="A grappling line helps a hero reach, पकड़, or pull something from far away or from a hard-to-reach place.",
        ),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)

def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print()
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    if not model:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program is satisfiable.")
    return 0

CURATED = [
    StoryParams(city="Harbor City", hero="Spark", sidekick="Chip", gear="grappling line", morsel="morsel"),
    StoryParams(city="Bright Bay", hero="Nova", sidekick="Pip", gear="grappling line", morsel="morsel"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show compatible_story/5."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
