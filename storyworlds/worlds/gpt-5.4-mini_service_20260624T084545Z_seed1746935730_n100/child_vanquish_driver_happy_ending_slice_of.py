#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child, a driver, and a gentle act of
vanquishing a worry with help from an everyday ride.

The initial seed-tale idea:
A child needs a ride across town. The child feels too nervous to speak up and
almost stays quiet the whole way. The driver notices, makes space for a small
conversation, and helps the child vanquish the shyness. By the end, the child
feels brave enough to wave hello and enjoy the ride.

The world model tracks:
- physical meters: distance, motion, found/kept objects
- emotional memes: worry, courage, calm, pride, friendliness

The story stays close to slice-of-life: one ordinary outing, one little turn,
and a happy ending image that proves something changed.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    calm: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    from_place: str
    to_place: str
    distance_m: int
    can_vanquish: bool
    driver_help: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    route: str
    name: str
    gender: str
    driver: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, route: Route) -> None:
        self.place = place
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.place, self.route)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            traits=list(v.traits), owner=v.owner, meters=dict(v.meters), memes=dict(v.memes)
        ) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _em(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _inc_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _inc_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            sig = ("worry->quiet", actor.id)
            if _em(actor, "worry") >= THRESHOLD and sig not in world.fired:
                world.fired.add(sig)
                _inc_meme(actor, "quiet", 1.0)
                produced.append(f"{actor.label} sat still for a moment and listened.")
                changed = True

            sig = ("driver->calm", actor.id)
            if actor.type in {"boy", "girl"} and _em(actor, "worry") >= THRESHOLD and _em(actor, "courage") >= THRESHOLD and sig not in world.fired:
                world.fired.add(sig)
                _inc_meme(actor, "calm", 1.0)
                produced.append(f"The worry got smaller, like a pebble slipping into a pocket.")
                changed = True

            sig = ("vanquish", actor.id)
            if _em(actor, "courage") >= THRESHOLD and _em(actor, "worry") < THRESHOLD and sig not in world.fired:
                world.fired.add(sig)
                _inc_meme(actor, "pride", 1.0)
                produced.append(f"{actor.label} looked proud in a quiet, happy way.")
                changed = True

    if narrate:
        for line in produced:
            world.say(line)
    return produced


def can_vanquish(world: World) -> bool:
    return world.route.can_vanquish and world.place.id == world.route.from_place


def forecast(world: World, child: Entity) -> dict:
    sim = world.copy()
    _inc_meme(sim.get(child.id), "worry", 1.0)
    propagate(sim, narrate=False)
    return {
        "worry_remaining": _em(sim.get(child.id), "worry"),
        "courage": _em(sim.get(child.id), "courage"),
    }


def introduce(world: World, child: Entity, driver: Entity) -> None:
    world.say(
        f"{child.label} was a little {child.traits[0]} {child.type} who liked ordinary days and tidy routines."
    )
    world.say(
        f"That morning, {child.label} had a ride with {driver.label}, the {driver.label.lower()} driver, on {world.route.label}."
    )


def setup_problem(world: World, child: Entity) -> None:
    _inc_meme(child, "worry", 1.0)
    world.say(
        f"But {child.label} felt a flutter of worry and kept looking down at {child.pronoun('possessive')} shoes."
    )


def driver_notices(world: World, driver: Entity, child: Entity) -> None:
    _inc_meme(driver, "kindness", 1.0)
    world.say(
        f"{driver.label} noticed right away and spoke gently from the front seat."
    )
    world.say(
        f'"It is okay to feel shy," {driver.pronoun()} said. "We can take the ride one small step at a time."'
    )


def vanquish_turn(world: World, child: Entity, driver: Entity) -> None:
    if not can_vanquish(world):
        raise StoryError("This route does not support a happy vanquish ending.")

    forecasted = forecast(world, child)
    if forecasted["worry_remaining"] > 0 and world.route.can_vanquish:
        _inc_meme(child, "courage", 1.0)
    else:
        _inc_meme(child, "courage", 2.0)

    world.say(
        f"{child.label} took a breath, nodded, and tried to vanquish the worry instead of hiding from it."
    )
    world.say(
        f"{driver.label} made the little ride feel easy by pointing out the street trees and counting the stops together."
    )
    propagate(world, narrate=True)


def happy_ending(world: World, child: Entity, driver: Entity) -> None:
    _inc_meme(child, "worry", -1.0)
    _inc_meme(child, "courage", 1.0)
    _inc_meme(child, "pride", 1.0)
    _inc_meter(child, "distance", world.route.distance_m)
    world.say(
        f"By the time they reached {world.place.label}, {child.label} was smiling and waving at {driver.label}."
    )
    world.say(
        f'{world.route.ending_image} {child.label} felt brave, and the day stayed soft and bright.'
    )


PLACEs = {
    "corner_stop": Place(
        id="corner_stop",
        label="the corner stop",
        kind="bus stop",
        calm=True,
        affordances={"ride", "conversation"},
    ),
    "library_door": Place(
        id="library_door",
        label="the library door",
        kind="front step",
        calm=True,
        affordances={"ride", "conversation"},
    ),
    "market_curb": Place(
        id="market_curb",
        label="the market curb",
        kind="curb",
        calm=True,
        affordances={"ride", "conversation"},
    ),
}

ROUTES = {
    "short_loop": Route(
        id="short_loop",
        label="the short loop",
        from_place="corner_stop",
        to_place="library_door",
        distance_m=120,
        can_vanquish=True,
        driver_help="count the stops and look out the window",
        ending_image="The bus hummed softly, and the windows shone like warm squares.",
    ),
    "town_circle": Route(
        id="town_circle",
        label="the town circle",
        from_place="library_door",
        to_place="market_curb",
        distance_m=180,
        can_vanquish=True,
        driver_help="point out trees, signs, and passing bikes",
        ending_image="A few birds hopped near the curb while the engine ticked itself cool.",
    ),
    "sunny_return": Route(
        id="sunny_return",
        label="the sunny return",
        from_place="market_curb",
        to_place="corner_stop",
        distance_m=150,
        can_vanquish=True,
        driver_help="turn the ride into a counting game",
        ending_image="The last bit of sunlight rested on the seats like a blanket.",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo"]
TRAITS = ["quiet", "curious", "careful", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in PLACEs for r in ROUTES if PLACEs[p].id == ROUTES[r].from_place and ROUTES[r].can_vanquish]


def explain_rejection(place: str, route: str) -> str:
    return f"(No story: {place} does not fit the start of {route}, or the route does not support a gentle happy ending.)"


def explain_gender(gender: str, name: str) -> str:
    return f"(No story: the chosen name {name} does not fit the requested {gender} character.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a child, a driver, and a happy vanquishing.")
    ap.add_argument("--place", choices=PLACEs)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--driver", choices=["driver", "bus driver", "van driver"], default="driver")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.route:
        if (args.place, args.route) not in combos:
            raise StoryError(explain_rejection(args.place, args.route))
    valid = [c for c in combos if (args.place is None or c[0] == args.place) and (args.route is None or c[1] == args.route)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    place, route = rng.choice(valid)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, route=route, name=name, gender=gender, driver=args.driver, trait=trait)


def tell(params: StoryParams) -> World:
    place = PLACEs[params.place]
    route = ROUTES[params.route]
    world = World(place, route)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[params.trait, "child"],
        meters={"distance": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "calm": 0.0, "pride": 0.0},
    ))
    driver = world.add(Entity(
        id="driver",
        kind="character",
        type="adult",
        label=params.driver,
        traits=["kind", "steady"],
        memes={"kindness": 0.0},
    ))

    world.say(
        f"{child.label} was a {params.trait} child waiting at {place.label} for a ride."
    )
    world.say(
        f"{driver.label.capitalize()} was already there, ready to keep the day calm."
    )
    world.para()
    introduce(world, child, driver)
    setup_problem(world, child)
    driver_notices(world, driver, child)
    world.para()
    vanquish_turn(world, child, driver)
    happy_ending(world, child, driver)

    world.facts = {
        "child": child,
        "driver": driver,
        "place": place,
        "route": route,
        "resolved": _em(child, "pride") >= THRESHOLD and _em(child, "worry") <= THRESHOLD,
    }
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    route = f["route"]
    return [
        f'Write a short slice-of-life story for a child named {child.label} who rides the {route.label} with a kind driver and vanquishes a worry.',
        f"Tell a happy, everyday story where {child.label} feels shy at first, then grows brave with help from a driver.",
        f'Write a gentle story about a child, a driver, and a small moment of vanquishing shyness during a ride.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    driver = f["driver"]
    route = f["route"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.label}, a {child.traits[0]} child, and {driver.label}, the driver who helps make the ride feel safe.",
        ),
        QAItem(
            question=f"What did {child.label} need to do at {place.label}?",
            answer=f"{child.label} needed to take {route.label}, an ordinary ride from {place.label} to the next stop.",
        ),
        QAItem(
            question=f"What problem did {child.label} have at first?",
            answer=f"At first, {child.label} felt a little worried and shy, so even a simple ride felt bigger than usual.",
        ),
        QAItem(
            question=f"How did the driver help?",
            answer=f"{driver.label.capitalize()} helped by speaking gently, counting stops, and pointing out little things outside the window.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {child.label} felt brave, smiled at {driver.label}, and the worry had been vanquished.",
        ),
    ]


KNOWLEDGE = {
    "driver": [(
        "What does a driver do?",
        "A driver helps move a vehicle from one place to another and keeps an eye on the road.",
    )],
    "child": [(
        "What is a child?",
        "A child is a young person who is still growing and learning about the world.",
    )],
    "vanquish": [(
        "What does vanquish mean?",
        "To vanquish something means to beat it or overcome it completely.",
    )],
    "bus": [(
        "What is a bus?",
        "A bus is a big vehicle that carries many people together on streets and roads.",
    )],
    "worry": [(
        "Why do people feel worried sometimes?",
        "People feel worried when something seems hard, new, or uncertain, but gentle help can make it feel smaller.",
    )],
}


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for tag in ["child", "driver", "vanquish", "worry"] for q, a in KNOWLEDGE[tag]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P,R) :- start(P,R).
valid(P,R) :- place_ok(P,R), happy_end(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACEs.values():
        lines.append(asp.fact("place", p.id))
    for r in ROUTES.values():
        lines.append(asp.fact("route", r.id))
        lines.append(asp.fact("start", r.from_place, r.id))
        if r.can_vanquish:
            lines.append(asp.fact("happy_end", r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="corner_stop", route="short_loop", name="Mia", gender="girl", driver="driver", trait="quiet"),
            StoryParams(place="library_door", route="town_circle", name="Ben", gender="boy", driver="bus driver", trait="careful"),
            StoryParams(place="market_curb", route="sunny_return", name="Lily", gender="girl", driver="van driver", trait="thoughtful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.route} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
