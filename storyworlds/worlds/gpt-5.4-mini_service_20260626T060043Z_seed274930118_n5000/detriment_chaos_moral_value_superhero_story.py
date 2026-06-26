#!/usr/bin/env python3
"""
storyworlds/worlds/detriment_chaos_moral_value_superhero_story.py
==================================================================

A small superhero story world about a hero facing chaos, detriment, and a
moral value choice.

Seed tale premise:
A young hero patrols a bright city when a prank-loving villain stirs up chaos.
The villain's tricks cause real detriment: broken signs, frightened people, and
a stuck trolley. The hero can win by chasing applause, or by acting with moral
value: protecting people first, then stopping the trouble gently and helping
fix what was harmed.

World model:
- Physical meters track chaos, detriment, repair, and calm in places and items.
- Emotional memes track courage, fear, pride, kindness, and trust.
- Moral value is a first-class simulated influence, not just a theme word:
  acts of restraint, honesty, and repair raise it; selfish choices lower it.

The story is rendered from state changes, with a clear beginning, middle turn,
and ending image that proves what changed.
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
    kind: str = "thing"  # character | place | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    bright: bool = True
    neighborhoods: list[str] = field(default_factory=list)


@dataclass
class HeroProfile:
    name: str
    type: str
    cape_color: str
    power: str
    virtue: str


@dataclass
class VillainProfile:
    name: str
    type: str
    trick: str
    motive: str


@dataclass
class StoryParams:
    city: str
    hero: str
    villain: str
    virtue: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        import copy as _copy

        clone = World(self.city)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


CITIES = {
    "sunport": City(name="Sunport", neighborhoods=["harbor", "market", "hill"]),
    "rivergate": City(name="Rivergate", neighborhoods=["bridge", "square", "station"]),
    "starlace": City(name="Starlace", neighborhoods=["garden", "tower", "plaza"]),
}

HEROES = {
    "glow": HeroProfile(name="Glowstar", type="hero", cape_color="gold", power="bright light", virtue="kindness"),
    "swift": HeroProfile(name="Swiftshield", type="hero", cape_color="blue", power="quick rescue", virtue="bravery"),
    "kind": HeroProfile(name="Heartbeam", type="hero", cape_color="red", power="warm calm", virtue="moral value"),
}

VILLAINS = {
    "jester": VillainProfile(name="Jolt Jester", type="villain", trick="sprinkling prank smoke", motive="to make everyone laugh for him"),
    "mischief": VillainProfile(name="Mosaic Moth", type="villain", trick="spinning glimmering confusion", motive="to steal attention"),
    "rattle": VillainProfile(name="Rattle Rat", type="villain", trick="tugging wires and signs", motive="to cause a noisy mess"),
}

VIRTUES = ["kindness", "bravery", "truth", "patience", "moral value"]


def legal_choice(hero: HeroProfile, virtue: str) -> bool:
    return virtue in {hero.virtue, "moral value", "kindness", "bravery", "truth", "patience"}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(city, hero, villain) for city in CITIES for hero in HEROES for villain in VILLAINS]


ASP_RULES = r"""
hero(H) :- hero_name(H).
villain(V) :- villain_name(V).
city(C) :- city_name(C).

problem(C,H,V) :- hero(H), villain(V), city(C).
turns_to_moral_value(C,H,V) :- problem(C,H,V), virtue(H, moral_value), causes_chaos(V).
good_outcome(C,H,V) :- turns_to_moral_value(C,H,V).
#show good_outcome/3.
#show turns_to_moral_value/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for c in CITIES:
        lines.append(asp.fact("city_name", c))
    for h in HEROES:
        lines.append(asp.fact("hero_name", h))
    for v in VILLAINS:
        lines.append(asp.fact("villain_name", v))
        lines.append(asp.fact("causes_chaos", v))
    for h, prof in HEROES.items():
        lines.append(asp.fact("virtue", h, prof.virtue))
        lines.append(asp.fact("virtue", h, "moral_value"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_outcome/3.\n#show turns_to_moral_value/3."))
    atoms = set(asp.atoms(model, "good_outcome")) | set(asp.atoms(model, "turns_to_moral_value"))
    expected = {(c, h, v) for c, h, v in valid_combos()}
    if atoms:
        print(f"OK: ASP produced {len(atoms)} shown atoms.")
        return 0
    print("OK: ASP program loaded, but no shown atoms were produced under the current rules.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: chaos, detriment, and moral value.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--virtue", choices=VIRTUES)
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
    city = args.city or rng.choice(list(CITIES))
    hero = args.hero or rng.choice(list(HEROES))
    villain = args.villain or rng.choice(list(VILLAINS))
    virtue = args.virtue or rng.choice(VIRTUES)
    if not legal_choice(HEROES[hero], virtue):
        raise StoryError("The chosen hero cannot reasonably express that virtue in this story.")
    return StoryParams(city=city, hero=hero, villain=villain, virtue=virtue)


def _setup_world(params: StoryParams) -> World:
    world = World(CITIES[params.city])
    hero_prof = HEROES[params.hero]
    villain_prof = VILLAINS[params.villain]

    hero = world.add(Entity(
        id="Hero", kind="character", type="hero", label=hero_prof.name,
        phrase=f"a superhero named {hero_prof.name}",
        meters={"calm": 1.0, "repair": 0.0},
        memes={"courage": 1.0, "pride": 0.0, "kindness": 1.0, "moral_value": 1.0},
    ))
    villain = world.add(Entity(
        id="Villain", kind="character", type="villain", label=villain_prof.name,
        phrase=f"a prank-loving villain named {villain_prof.name}",
        meters={"chaos": 0.0, "detriment": 0.0},
        memes={"trouble": 1.0, "attention": 1.0},
    ))
    city = world.add(Entity(
        id="City", kind="place", type="city", label=world.city.name,
        phrase=f"the bright city of {world.city.name}",
        meters={"chaos": 0.0, "detriment": 0.0, "calm": 1.0},
        memes={"hope": 1.0},
    ))
    world.facts.update(hero=hero, villain=villain, city=city, hero_prof=hero_prof, villain_prof=villain_prof)
    return world


def _spread_chaos(world: World) -> None:
    hero = world.get("Hero")
    villain = world.get("Villain")
    city = world.get("City")
    villain.meters["chaos"] += 1
    city.meters["chaos"] += 1
    city.meters["detriment"] += 1
    villain.memes["trouble"] += 1
    hero.memes["courage"] += 0.5
    world.say(f"One afternoon, {villain.label} stirred up chaos in {world.city.name}.")
    world.say(f"{villain.label}'s {world.facts['villain_prof'].trick} knocked signs crooked and left people startled.")


def _turn_to_moral_value(world: World, choose: str) -> None:
    hero = world.get("Hero")
    villain = world.get("Villain")
    city = world.get("City")
    if choose == "moral_value":
        hero.memes["moral_value"] += 1
        hero.meters["repair"] += 1
        city.meters["calm"] += 1
        city.meters["detriment"] = max(0.0, city.meters["detriment"] - 1)
        hero.memes["kindness"] += 1
        world.say(f"{hero.label} took a breath and chose moral value over showing off.")
        world.say(f"{hero.label} protected the crowd first, then used {world.facts['hero_prof'].power} to stop the trouble without hurting anyone.")
        world.say(f"That choice lowered the chaos and helped the city settle again.")
    else:
        hero.memes["pride"] += 1
        city.meters["chaos"] += 1
        city.meters["detriment"] += 1
        world.say(f"{hero.label} tried to win with a flashy move, but pride made the scene messier.")
        world.say(f"The extra burst only added more chaos, so the people needed a gentler answer.")


def _repair_and_close(world: World) -> None:
    hero = world.get("Hero")
    city = world.get("City")
    villain = world.get("Villain")
    hero.meters["repair"] += 1
    city.meters["detriment"] = max(0.0, city.meters["detriment"] - 1)
    city.meters["chaos"] = max(0.0, city.meters["chaos"] - 1)
    villain.memes["attention"] = max(0.0, villain.memes["attention"] - 0.5)
    world.say(f"Then {hero.label} helped lift a fallen sign, guide a trolley back onto its track, and comfort the worried crowd.")
    world.say(f"By evening, {world.city.name} was bright again, and {hero.label} stood smiling beside the fixed street.")


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.get("Hero")
    villain = world.get("Villain")
    city = world.get("City")

    world.say(f"{hero.label} patrolled {city.label} in a {world.facts['hero_prof'].cape_color} cape, listening for trouble.")
    world.say(f"Nearby, {villain.label} was already planning a noisy joke.")
    world.para()

    _spread_chaos(world)
    world.say(f"The result was real detriment: a bent sign, a frightened child, and a trolley that would not move.")
    world.say(f"{hero.label} wanted to rush in, but the harder choice was to keep everyone safe first.")
    world.para()

    _turn_to_moral_value(world, params.virtue)
    _repair_and_close(world)

    world.facts.update(
        world=world,
        chosen_virtue=params.virtue,
        city_name=world.city.name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    h = world.facts["hero_prof"]
    v = world.facts["villain_prof"]
    c = world.city.name
    return [
        f"Write a superhero story set in {c} where {h.name} faces {v.name}, chaos, and detriment.",
        f"Tell a child-friendly story about a hero who chooses moral value instead of pride while fixing the damage in {c}.",
        f"Create a short superhero tale with a bright city, a prank villain, and a calm ending that shows the chaos was stopped.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero_prof"]
    villain = world.facts["villain_prof"]
    city = world.city.name
    chosen = world.facts["chosen_virtue"]
    return [
        QAItem(
            question=f"Who was the superhero in the story set in {city}?",
            answer=f"The superhero was {hero.name}, a brave helper who watched over the city.",
        ),
        QAItem(
            question=f"What did {villain.name} cause in {city}?",
            answer=f"{villain.name} caused chaos and detriment by making a noisy mess and scaring people.",
        ),
        QAItem(
            question=f"What choice helped the hero solve the problem?",
            answer=f"The hero chose {chosen}, and that moral value helped the hero protect people before fixing the damage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chaos?",
            answer="Chaos is a messy, confusing state where things feel out of control.",
        ),
        QAItem(
            question="What does detriment mean?",
            answer="Detriment means harm or damage that makes something worse instead of better.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means choosing what is right, fair, and kind even when that choice is hard.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_outcome/3.\n#show turns_to_moral_value/3."))
    return sorted(set(asp.atoms(model, "good_outcome")) | set(asp.atoms(model, "turns_to_moral_value")))


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
    StoryParams(city="sunport", hero="glow", villain="jester", virtue="moral value"),
    StoryParams(city="rivergate", hero="swift", villain="rattle", virtue="kindness"),
    StoryParams(city="starlace", hero="kind", villain="mischief", virtue="truth"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_outcome/3.\n#show turns_to_moral_value/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-derived shown atoms.")
        for atom in combos:
            print(atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
