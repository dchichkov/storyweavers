#!/usr/bin/env python3
"""
Story world: heffalump, blank, skid — a small Adventure-style tale with
suspense and conflict driven by simulated world state.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    features: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    step: str
    ending: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    thing: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


THRESHOLD = 1.0


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


def covered(actor: Entity, region: str) -> bool:
    for e in actor_world_items(actor):
        if e.id in {"cloak", "mask"}:
            if region in GEARS[e.id].covers:
                return True
    return False


def actor_world_items(actor: Entity) -> list[Entity]:
    return []


SETTINGS = {
    "attic": Place("the attic", True, {"boxes", "dust", "beam"}),
    "pier": Place("the pier", False, {"wood", "waves", "wind"}),
    "garden": Place("the garden", False, {"hedge", "path", "gate"}),
    "cave": Place("the cave", True, {"echo", "stone", "dark"}),
}

THINGS = {
    "blank": Thing("blank", "blank map", "a blank map with one empty fold", "blank and torn", "paper"),
    "skid": Thing("skid", "skid toy", "a little skid toy with fast wheels", "skidded and scratched", "wheels"),
    "heffalump": Thing("heffalump", "heffalump kite", "a bright heffalump kite with long tails", "tangled and bent", "sky"),
}

GEARS = {
    "cloak": Gear("cloak", "cloak", "a thick cloak", {"torso"}, {"wind", "dust"}, "put on the thick cloak", "slipped on the thick cloak"),
    "gloves": Gear("gloves", "gloves", "soft gloves", {"hands"}, {"dust"}, "put on soft gloves", "pulled on the soft gloves", plural=True),
    "boots": Gear("boots", "boots", "sturdy boots", {"feet"}, {"skid"}, "lace up the sturdy boots", "laced up the sturdy boots", plural=True),
}

ACTORS = {
    "girl": ["Mina", "Luna", "Nori", "Ivy", "Pia"],
    "boy": ["Theo", "Jasper", "Owen", "Milo", "Ravi"],
}


def risky(thing: Thing, place: Place) -> bool:
    if thing.id == "blank":
        return "dust" in place.features or "wind" in place.features
    if thing.id == "skid":
        return "stone" in place.features or "wood" in place.features
    if thing.id == "heffalump":
        return "wind" in place.features or "beam" in place.features
    return False


def select_gear(thing: Thing, place: Place) -> Optional[Gear]:
    for g in GEARS.values():
        if thing.risk.split()[0] in g.guards:
            if thing.region in g.covers or thing.region == "wheels" and "feet" in g.covers:
                return g
    if thing.id == "skid":
        return GEARS["boots"]
    if thing.id == "blank":
        return GEARS["gloves"] if place.indoors else GEARS["cloak"]
    if thing.id == "heffalump":
        return GEARS["cloak"]
    return None


def predict_mess(world: World, thing: Thing) -> bool:
    return risky(thing, world.place)


def act_story(world: World, hero: Entity, parent: Entity, thing: Thing, gear: Gear) -> None:
    world.say(f"{hero.id} was a curious little {hero.type} who loved adventures in {world.place.name}.")
    if thing.id == "heffalump":
        world.say("One day, a heffalump kite waited near the edge of the path like a secret flag.")
    elif thing.id == "blank":
        world.say("One day, a blank map waited on the table, and it looked like a mystery with no answers.")
    else:
        world.say("One day, a skid toy sat by the steps, as if it were daring someone to try it.")
    world.para()
    if thing.id == "blank":
        world.say(f"{hero.id} wanted to fill the blank map with a trail, but the room was dusty and the paper could get blank and torn.")
    elif thing.id == "heffalump":
        world.say(f"{hero.id} wanted to fly the heffalump kite, but the wind tugged hard and the string could twist.")
    else:
        world.say(f"{hero.id} wanted to race the skid toy, but the stone path made the wheels bounce and skitter.")
    world.say(f"'{hero.id},' {parent.pronoun('subject')} said, 'that could go wrong.'")
    hero.memes["suspense"] = 1
    hero.memes["conflict"] = 1
    world.say(f"{hero.id} held still for a moment, listening to the worry in the air.")
    world.para()
    world.say(f"Then {parent.pronoun('subject')} smiled and said, 'Let's {gear.step} first.'")
    world.say(f"They {gear.ending}, and the adventure felt brave instead of risky.")
    world.say(f"At last, {hero.id} could play, and the {thing.label} stayed safe.")
    hero.memes["joy"] = 1
    hero.memes["conflict"] = 0
    world.facts.update(hero=hero, parent=parent, thing=thing, gear=gear)


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    thing = THINGS[params.thing]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    if not risky(thing, place):
        raise StoryError("This combination is too safe to make a real suspense story.")
    gear = select_gear(thing, place)
    if gear is None:
        raise StoryError("No reasonable gear can solve this problem.")
    act_story(world, hero, parent, thing, gear)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    thing = f["thing"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {thing.label}?",
            answer=f"{hero.id} wanted to have an adventure with the {thing.label} at {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} worry?",
            answer=f"{parent.pronoun('subject').capitalize()} worried because the {thing.label} could get {thing.risk} at {world.place.name}.",
        ),
        QAItem(
            question=f"What helped the adventure feel safe?",
            answer=f"The {gear.label} helped because it was the right thing to use before the adventure began.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    thing = world.facts["thing"]
    if thing.id == "blank":
        return [
            QAItem(
                question="What is a blank map?",
                answer="A blank map is an empty map that still needs marks, paths, or signs to show where to go.",
            )
        ]
    if thing.id == "skid":
        return [
            QAItem(
                question="What does skid mean?",
                answer="To skid means to slide or slip along a surface, often because the ground is smooth or slippery.",
            )
        ]
    return [
        QAItem(
            question="What is a heffalump?",
            answer="A heffalump is a made-up, elephant-like creature from a storybook style adventure.",
        )
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a child about {f['hero'].id}, a {f['thing'].label}, and a careful choice.",
        f"Tell a suspenseful but gentle tale set in {world.place.name} where a {f['thing'].label} might get hurt unless someone uses the right gear.",
        f"Create a child-friendly adventure with conflict that ends in a safe plan for the {f['thing'].label}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world with heffalump, blank, and skid.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--thing", choices=sorted(THINGS))
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
    if args.place and args.thing:
        if not risky(THINGS[args.thing], SETTINGS[args.place]):
            raise StoryError("That place and thing do not create enough suspense.")
    place = args.place or rng.choice(sorted(SETTINGS))
    thing = args.thing or rng.choice(sorted(THINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(ACTORS[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, thing=thing, name=name, gender=gender, parent=parent)


CURATED = [
    StoryParams(place="attic", thing="blank", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="pier", thing="skid", name="Theo", gender="boy", parent="father"),
    StoryParams(place="garden", thing="heffalump", name="Ivy", gender="girl", parent="mother"),
]


ASP_RULES = r"""
place(attic). place(pier). place(garden). place(cave).
thing(blank). thing(skid). thing(heffalump).

risky(blank,attic).
risky(blank,garden).
risky(skid,pier).
risky(skid,garden).
risky(heffalump,pier).
risky(heffalump,garden).
risky(heffalump,attic).

valid(P,T) :- place(P), thing(T), risky(T,P).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("place", p) for p in SETTINGS] +
                     [asp.fact("thing", t) for t in THINGS])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(p, t) for p in SETTINGS for t in THINGS if risky(THINGS[t], SETTINGS[p])}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} pairs).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(asp_set - py_set))
    print("PY only:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 30, 30)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError:
                continue
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
