#!/usr/bin/env python3
"""
A small fable-world about surprise moisture: a careful little animal expects a dry
day, meets an unexpected wet patch, and learns a kind, practical lesson.

The world is built as a tiny simulation:
- a character with hopes and feelings
- a place with a moisture risk
- an object that can hide moisture
- a surprise turn caused by state, not by fixed prose
- a gentle resolution with a moral-like closing image
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "cat", "dog", "hare", "rabbit"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
    moisture: float = 0.0
    surprise: float = 0.0


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    region: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object_id: str
    hero: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(copy.deepcopy(self.place))
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


OBJECTS = {
    "cloak": ObjectDef(
        id="cloak",
        label="cloak",
        phrase="a bright little cloak",
        region="torso",
        guards={"moisture"},
        covers={"torso"},
    ),
    "satchel": ObjectDef(
        id="satchel",
        label="satchel",
        phrase="a tidy satchel",
        region="side",
        guards={"moisture"},
        covers={"side"},
    ),
    "book": ObjectDef(
        id="book",
        label="book",
        phrase="a careful little book",
        region="paws",
        guards={"moisture"},
        covers={"paws"},
    ),
}

PLACES = {
    "meadow": Place(name="the meadow", affords={"walk", "rest", "listen"}, moisture=0.4, surprise=0.8),
    "orchard": Place(name="the orchard", affords={"walk", "rest", "listen"}, moisture=0.3, surprise=0.9),
    "riverbank": Place(name="the riverbank", affords={"walk", "rest", "listen"}, moisture=0.6, surprise=1.0),
}

HEROES = {
    "fox": {"type": "fox", "name": "Fennel", "traits": ["small", "careful", "bright-eyed"]},
    "hare": {"type": "hare", "name": "Tansy", "traits": ["small", "quick", "gentle"]},
    "badger": {"type": "badger", "name": "Moss", "traits": ["small", "patient", "steady"]},
}

MORAL_LINES = {
    "moisture": "The smallest wetness can become the biggest surprise if no one looks closely.",
    "surprise": "A wise creature checks the ground before it trusts the day.",
}


def moisture_risk(place: Place, obj: ObjectDef) -> bool:
    return place.moisture >= 0.5 and "moisture" in obj.guards


def select_surprise(place: Place, obj: ObjectDef) -> bool:
    return place.surprise >= 0.75 and moisture_risk(place, obj)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
        if p.moisture >= 0.5:
            lines.append(asp.fact("moist_place", pid))
        if p.surprise >= 0.75:
            lines.append(asp.fact("surprise_place", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("guards", oid, "moisture"))
        for r in sorted(o.covers):
            lines.append(asp.fact("covers", oid, r))
    return "\n".join(lines)


ASP_RULES = r"""
risk(P,O) :- moist_place(P), object(O), guards(O, moisture).
surprising(P,O) :- surprise_place(P), risk(P,O).
valid(P,O) :- risk(P,O), surprising(P,O).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for pid, p in PLACES.items():
        for oid, o in OBJECTS.items():
            if moisture_risk(p, o) and select_surprise(p, o):
                out.append((pid, oid))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world of moisture and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, o) for p in PLACES for o in OBJECTS if moisture_risk(PLACES[p], OBJECTS[o]) and select_surprise(PLACES[p], OBJECTS[o])]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_id:
        combos = [c for c in combos if c[1] == args.object_id]
    if not combos:
        raise StoryError("No valid moisture-surprise story matches those options.")
    place, object_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(place=place, object_id=object_id, hero=hero)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero_cfg = HEROES[params.hero]
    obj_cfg = OBJECTS[params.object_id]
    world = World(Place(name=place.name, affords=set(place.affords), moisture=place.moisture, surprise=place.surprise))
    hero = world.add(Entity(id=hero_cfg["name"], kind="character", type=hero_cfg["type"], traits=list(hero_cfg["traits"])))
    obj = world.add(Entity(id=obj_cfg.id, type=obj_cfg.label, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, obj=obj, place=world.place, moral=MORAL_LINES["moisture"])
    hero.memes["curiosity"] = 1.0
    hero.memes["hope"] = 1.0
    obj.meters["dry"] = 1.0
    return world


def predict_surprise(world: World, obj: Entity) -> dict:
    sim = world.copy()
    p = sim.place
    o = sim.get(obj.id)
    wet = p.moisture >= 0.5
    surprise = p.surprise >= 0.75
    if wet:
        o.meters["wet"] = o.meters.get("wet", 0.0) + 1.0
    return {"wet": wet, "surprise": surprise, "spoiled": bool(wet and surprise)}


def generate_story(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    place = world.place

    world.say(f"Once in {place.name}, {hero.id} liked to walk where the grass was soft and the air was kind.")
    world.say(f"{hero.id} carried {obj.phrase} and believed the day would stay dry and neat.")

    if place.surprise >= 0.75:
        world.say(f"But the ground held a secret surprise.")
    if place.moisture >= 0.5:
        world.say(f"Under the leaves, a cool patch of moisture waited quietly.")

    pred = predict_surprise(world, obj)
    if pred["wet"]:
        obj.meters["wet"] = 1.0
        hero.memes["surprised"] = 1.0
        world.say(f"When {hero.id} stepped there, the dampness touched {obj.it()} at once.")
    if pred["spoiled"]:
        hero.memes["worry"] = 1.0
        world.say(f"{hero.id} paused, then saw that {obj.label} had grown a little wet and would need care.")

    if pred["spoiled"]:
        hero.memes["wisdom"] = 1.0
        world.say(f"So {hero.id} chose a wiser path, lifting {obj.it()} high and walking around the hidden patch.")
        world.say(f"The surprise did not spoil the day; it only taught {hero.id} to look before stepping.")
    else:
        world.say(f"The day stayed steady, and {hero.id} passed by without trouble.")

    world.say(f"In the end, the little fable was plain: {world.facts['moral']}")


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    place = world.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who walked through {place.name} with {obj.phrase}.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find?",
            answer=f"{hero.id} found a hidden patch of moisture in {place.name} that made {obj.label} wet.",
        ),
        QAItem(
            question=f"What did {hero.id} do after noticing the wetness?",
            answer=f"{hero.id} chose a wiser path, lifted {obj.label} carefully, and walked around the wet place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moisture?",
            answer="Moisture is a little bit of water or dampness that can make things wet.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that appears when you thought the day would be different.",
        ),
        QAItem(
            question="Why should a creature check the ground in a moist place?",
            answer="Checking the ground helps a creature avoid wet patches, slipping, and spoiled things.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    return [
        f"Write a short fable about {hero.id}, a small animal, and a surprising patch of moisture.",
        f"Tell a gentle story in which {hero.id} learns to protect {obj.label} from hidden wetness.",
        "Write a child-friendly fable with a surprise, a wet patch, and a wise ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.name} moisture={world.place.moisture} surprise={world.place.surprise}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
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


CURATED = [
    StoryParams(place="meadow", object_id="cloak", hero="fox"),
    StoryParams(place="orchard", object_id="book", hero="hare"),
    StoryParams(place="riverbank", object_id="satchel", hero="badger"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, obj in asp_valid():
            print(f"{place} {obj}")
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
