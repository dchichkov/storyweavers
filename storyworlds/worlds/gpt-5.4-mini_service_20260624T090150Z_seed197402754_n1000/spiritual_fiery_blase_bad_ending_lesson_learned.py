#!/usr/bin/env python3
"""
storyworlds/worlds/spiritual_fiery_blase_bad_ending_lesson_learned.py
======================================================================

A small space-adventure storyworld about a fiery emergency, a blase crew
member, and a spiritual lesson learned after a bad ending.

Premise source sketch:
---
A tiny starship drifts past a bright comet temple. The captain wants to
collect a glowing ember from a sacred solar shrine, but the engine room is
already running hot. One crew member treats the warning very casually, while
another feels the moment is spiritually important and insists they should
listen to the old ship-prayers before touching anything sacred or fiery.
---

World model:
- physical meters: heat, damage, charge, drift, soot
- emotional memes: awe, calm, fear, blase, faith, regret, resolve

Story shape:
- setup: the ship approaches a sacred fiery place in space
- tension: a casual mistake makes the situation worse
- turn: the crew tries a ritual-tinged repair, but the danger already spreads
- resolution: a bad ending occurs, and the final line makes the lesson clear

The world intentionally supports a bad ending rather than a happy fix.
That makes the lesson learned the important ending change.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"pilot", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    name: str
    location: str
    sacred_site: str
    allow_ritual: bool = True
    danger: str = "flare"
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "Ship":
        clone = Ship(self.name, self.location, self.sacred_site, self.allow_ritual, self.danger)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    ship: str
    location: str
    sacred_site: str
    crew_name: str
    crew_role: str
    skeptic_name: str
    skeptic_role: str
    seed: Optional[int] = None


@dataclass
class Place:
    name: str
    aura: str
    heat: int
    sacred: bool
    view: str


@dataclass
class Action:
    id: str
    verb: str
    risk: str
    ritual: str
    mess: str
    consequence: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "comet_temple": Place(
        name="the comet temple",
        aura="glowing and old",
        heat=2,
        sacred=True,
        view="A bright comet drifted by the temple like a candle in black water.",
    ),
    "sun_gate": Place(
        name="the sun gate",
        aura="blazing and silent",
        heat=3,
        sacred=True,
        view="A gold ring of light burned at the center of space.",
    ),
    "ember_dock": Place(
        name="the ember dock",
        aura="warm and dusty",
        heat=1,
        sacred=False,
        view="A small dock floated near a red rock and a trail of sparks.",
    ),
}

ACTIONS = {
    "touch_ember": Action(
        id="touch_ember",
        verb="touch the sacred ember",
        risk="heat",
        ritual="say a ship-prayer first",
        mess="scorching",
        consequence="the ember flared out of control",
        tags={"fiery", "spiritual"},
    ),
    "open_shrine": Action(
        id="open_shrine",
        verb="open the shrine door",
        risk="damage",
        ritual="bow before the shrine",
        mess="broken",
        consequence="the shrine cracked and hissed",
        tags={"spiritual"},
    ),
    "vent_core": Action(
        id="vent_core",
        verb="vent the hot core",
        risk="heat",
        ritual="cool the vents with a blessing",
        mess="overheated",
        consequence="the core spat sparks into the hallway",
        tags={"fiery"},
    ),
}

NAMES = ["Ari", "Mina", "Jules", "Tavi", "Niko", "Rin", "Sol", "Iris"]
ROLES = ["captain", "pilot", "engineer", "navigator", "scout"]
SHIP_NAMES = ["the Star Lantern", "the Quiet Comet", "the Ember Kite", "the Little Orbit"]


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.story: list[str] = []

    def say(self, text: str) -> None:
        self.ship.say(text)

    def para(self) -> None:
        self.ship.para()

    def render(self) -> str:
        return self.ship.render()


def seed_ship(params: StoryParams) -> World:
    ship = Ship(name=params.ship, location=params.location, sacred_site=params.sacred_site)
    world = World(ship)

    hero = ship.add(Entity(
        id=params.crew_name,
        kind="character",
        type=params.crew_role,
        traits=["spiritual", "gentle"],
        memes={"awe": 1.0, "faith": 1.0, "resolve": 0.0, "regret": 0.0},
        meters={"heat": 0.0, "damage": 0.0, "charge": 0.0},
    ))
    skeptic = ship.add(Entity(
        id=params.skeptic_name,
        kind="character",
        type=params.skeptic_role,
        traits=["blase", "easygoing"],
        memes={"blase": 1.0, "calm": 1.0, "regret": 0.0},
        meters={"heat": 0.0, "damage": 0.0},
    ))
    shard = ship.add(Entity(
        id="ember",
        kind="thing",
        type="artifact",
        label="ember",
        phrase="a sacred glowing ember",
        owner=None,
        caretaker=params.crew_name,
        meters={"heat": 0.0, "charge": 1.0},
    ))
    ship.facts.update(hero=hero, skeptic=skeptic, ember=shard)
    return world


def predict_badness(world: World, action: Action) -> bool:
    sim = world.ship.copy()
    hero = sim.get(world.ship.facts["hero"].id)
    hero.meters[action.risk] = hero.meters.get(action.risk, 0.0) + 1.0
    if action.id == "touch_ember":
        sim.get("ember").meters["heat"] = 2.0
    return True


def apply_action(world: World, action: Action) -> None:
    hero = world.ship.facts["hero"]
    skeptic = world.ship.facts["skeptic"]
    ember = world.ship.facts["ember"]

    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    hero.meters[action.risk] = hero.meters.get(action.risk, 0.0) + 1.0
    ember.meters["heat"] = ember.meters.get("heat", 0.0) + 2.0
    skeptic.memes["blase"] = skeptic.memes.get("blase", 0.0) + 1.0

    if action.id == "touch_ember":
        world.ship.facts["bad"] = True
        world.ship.facts["lesson"] = "Even a sacred thing can burn if no one takes the warning seriously."
        world.ship.facts["ruin"] = "the ember flared and scorched the shrine"
    elif action.id == "open_shrine":
        world.ship.facts["bad"] = True
        world.ship.facts["lesson"] = "Respect matters when you enter a sacred place."
        world.ship.facts["ruin"] = "the shrine cracked open with a loud hiss"
    else:
        world.ship.facts["bad"] = True
        world.ship.facts["lesson"] = "Hot danger needs care, not casual shrugging."
        world.ship.facts["ruin"] = "sparks ran through the hallway"

    world.ship.facts["ending"] = "bad"
    world.ship.facts["change"] = "lesson_learned"


def tell(params: StoryParams) -> World:
    world = seed_ship(params)
    hero: Entity = world.ship.facts["hero"]
    skeptic: Entity = world.ship.facts["skeptic"]
    action = ACTIONS["touch_ember"] if world.ship.location != "ember_dock" else ACTIONS["vent_core"]

    world.say(
        f"On the starship {world.ship.name}, {hero.id} was a {hero.type} who felt the old spaceways deeply. "
        f"{hero.pronoun().capitalize()} called the glowing place ahead {world.ship.location.replace('_', ' ')}."
    )
    world.say(
        f"{world.ship.facts['ember'].phrase.capitalize()} waited near {world.ship.sacred_site}, and the air felt {PLACES[params.location].aura}."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to {action.verb}, but {skeptic.id} only looked {skeptic.traits[0]} and said it was no big deal."
    )
    world.say(
        f"Still, {hero.id} felt the site was spiritual, so {hero.pronoun()} whispered that they should {action.ritual}."
    )
    world.para()
    if predict_badness(world, action):
        world.say(
            f"{skeptic.id} shrugged and moved too soon. That blase choice made the ship's {action.risk} climb fast."
        )
        apply_action(world, action)
        world.say(
            f"Then {world.ship.facts['ruin']}."
        )
    world.para()
    world.say(
        f"In the end, the trip had a bad ending: the crew did not save the shrine, and the glowing ember was lost."
    )
    world.say(
        f"But {hero.id} learned a lesson learned the hard way: sacred things need care, and fiery places need respect."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.ship.facts
    hero: Entity = f["hero"]
    skeptic: Entity = f["skeptic"]
    return [
        "Write a short space-adventure story with a spiritual warning, a fiery danger, and a blase mistake.",
        f"Tell a child-friendly starship story where {hero.id} wants to approach a sacred ember, but {skeptic.id} shrugs too casually.",
        "Write a story that ends badly but still teaches a lesson learned about respect and caution in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    hero: Entity = f["hero"]
    skeptic: Entity = f["skeptic"]
    return [
        QAItem(
            question=f"Who was the spiritual crew member in the story?",
            answer=f"It was {hero.id}, the {hero.type}, who felt the sacred place was important and wanted to be careful.",
        ),
        QAItem(
            question=f"Why was {skeptic.id} described as blase?",
            answer=f"{skeptic.id} was blase because {skeptic.pronoun()} treated the warning like it was no big deal.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer="The story ended badly: the shrine was damaged, the ember was lost, and the crew learned a serious lesson.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for something to be sacred?",
            answer="Sacred means something is special, respected, and treated with care, like a holy place or object.",
        ),
        QAItem(
            question="What is a flare in space?",
            answer="A flare is a burst of bright, hot light or energy, and it can be dangerous near a ship.",
        ),
        QAItem(
            question="Why should people be careful around fire?",
            answer="Fire can spread fast and cause damage, so people should handle it carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.ship.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.ship.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(ship="the Star Lantern", location="comet_temple", sacred_site="the comet temple", crew_name="Ari", crew_role="captain", skeptic_name="Mina", skeptic_role="engineer"),
    StoryParams(ship="the Ember Kite", location="sun_gate", sacred_site="the sun gate", crew_name="Rin", crew_role="pilot", skeptic_name="Jules", skeptic_role="navigator"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: spiritual, fiery, blase, bad ending, lesson learned.")
    ap.add_argument("--ship", choices=sorted(SHIP_NAMES))
    ap.add_argument("--location", choices=sorted(PLACES))
    ap.add_argument("--site", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--skeptic")
    ap.add_argument("--skeptic-role", choices=ROLES)
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
    location = args.location or args.site or rng.choice(sorted(PLACES))
    ship = args.ship or rng.choice(SHIP_NAMES)
    crew_name = args.name or rng.choice(NAMES)
    crew_role = args.role or rng.choice(ROLES)
    skeptic_name = args.skeptic or rng.choice([n for n in NAMES if n != crew_name])
    skeptic_role = args.skeptic_role or rng.choice([r for r in ROLES if r != crew_role])

    if location not in PLACES:
        raise StoryError("Unknown location.")
    place = PLACES[location]
    if not place.sacred:
        raise StoryError("This world needs a sacred fiery place to make the spiritual warning honest.")

    return StoryParams(
        ship=ship,
        location=location,
        sacred_site=place.name,
        crew_name=crew_name,
        crew_role=crew_role,
        skeptic_name=skeptic_name,
        skeptic_role=skeptic_role,
    )


def generate(params: StoryParams) -> StorySample:
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
