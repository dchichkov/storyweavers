#!/usr/bin/env python3
"""
storyworlds/worlds/fare_civil_dialogue_twist_surprise_tall_tale.py
===================================================================

A small tall-tale storyworld about a traveler, a fair fare, civil manners,
dialogue, and a surprising turn.

The seed idea:
- A big-voiced traveler reaches a little town.
- The town asks for a fare, but the traveler wants to pay fairly and stay civil.
- A misunderstanding grows into a twist.
- A surprise reveals the right person to pay, and the story ends with
  everyone speaking kindly and the road moving on.

This world keeps the story grounded in a simple simulated model:
- people have meters (money, dust, mile_tiredness, etc.)
- people have memes (politeness, worry, delight, suspicion, relief)
- dialogue changes those values and drives the turn
- the ending image proves what changed
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maiden"}
        male = {"boy", "man", "father", "driver", "traveler"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    kind: str = "town"
    has_bridge: bool = False
    has_ferry: bool = False
    has_fare_booth: bool = False
    has_sign: bool = True


@dataclass
class Route:
    id: str
    label: str
    place: str
    fare_kind: str
    twist_kind: str
    surprise_kind: str
    passes: int = 1


@dataclass
class FareRule:
    id: str
    label: str
    amount: int
    item: str
    speaker: str
    polite: bool = True


@dataclass
class StoryParams:
    place: str
    route: str
    fare_rule: str
    traveler_name: str
    traveler_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _initial_meters() -> dict[str, float]:
    return {"money": 0.0, "dust": 0.0, "mile_tiredness": 0.0, "steps": 0.0}


def _initial_memes() -> dict[str, float]:
    return {"politeness": 0.0, "worry": 0.0, "delight": 0.0, "suspicion": 0.0, "relief": 0.0, "amusement": 0.0}


def tally(world: World, actor: Entity, route: Route) -> None:
    actor.meters["mile_tiredness"] += 1
    actor.meters["steps"] += route.passes
    actor.memes["worry"] += 1
    world.say(f"{actor.id} came down the road with a tall hat and a dust cloud for a shadow.")


def civil_talk(world: World, speaker: Entity, listener: Entity, line: str) -> None:
    speaker.memes["politeness"] += 1
    listener.memes["politeness"] += 1
    world.say(f'"{line}" {speaker.id} said civilly, and {listener.id} nodded like a porch swing in a summer breeze.')


def ask_fare(world: World, collector: Entity, traveler: Entity, fare: FareRule) -> None:
    collector.memes["politeness"] += 1
    traveler.memes["worry"] += 1
    world.say(
        f'"That road asks for a fare of {fare.amount} {fare.item}," '
        f'{collector.id} said. "Please pay it before the bridge lets you through."'
    )


def pay_fare(world: World, traveler: Entity, collector: Entity, fare: FareRule) -> None:
    traveler.meters["money"] -= fare.amount
    collector.meters["money"] += fare.amount
    traveler.memes["relief"] += 1
    collector.memes["relief"] += 1
    world.say(
        f"{traveler.id} smiled, counted out the coins, and paid the fare without a fuss."
    )


def suspicion_twist(world: World, helper: Entity, collector: Entity) -> None:
    helper.memes["suspicion"] += 1
    world.say(
        f'{helper.id} whispered, "That seems too neat for a road this crooked." '
        f'{collector.id} only lifted a hand and kept the gate shut.'
    )


def reveal_surprise(world: World, helper: Entity, route: Route, fare: FareRule) -> None:
    world.say(
        f"Then came the surprise: the fare was not for the bridge at all, but for "
        f"{route.surprise_kind}, which the town had set beside the road on purpose."
    )
    world.say(
        f'The little sign read, "A civil traveler may cross after paying the fare, '
        f'and the fare keeps the {route.twist_kind} from shaking loose."'
    )
    helper.memes["delight"] += 1
    helper.memes["suspicion"] = 0.0


def resolution(world: World, traveler: Entity, helper: Entity, collector: Entity, route: Route) -> None:
    traveler.memes["relief"] += 1
    traveler.memes["politeness"] += 1
    helper.memes["relief"] += 1
    collector.memes["relief"] += 1
    world.say(
        f"{traveler.id} laughed, and the laugh rolled across the bridge like a barrel of apples. "
        f'"Well then," {traveler.id} said, "I am glad to pay a fair fare for a fair crossing."'
    )
    world.say(
        f"{helper.id} chuckled too, and the whole town grew civil as candlelight. "
        f"After that, {traveler.id} crossed the road and the dust behind {traveler.pronoun('object')} looked almost polished."
    )


PLACE_REGISTRY = {
    "river_town": Place(id="river_town", label="River Town", kind="town", has_bridge=True, has_fare_booth=True),
    "hill_town": Place(id="hill_town", label="Hill Town", kind="town", has_bridge=False, has_fare_booth=True),
    "harbor": Place(id="harbor", label="Harbor Hollow", kind="port", has_bridge=True, has_ferry=True, has_fare_booth=True),
}

ROUTE_REGISTRY = {
    "bridge": Route(id="bridge", label="the bridge road", place="river_town", fare_kind="bridge fare", twist_kind="bridge plank", surprise_kind="a goose parade", passes=2),
    "ferry": Route(id="ferry", label="the ferry lane", place="harbor", fare_kind="ferry fare", twist_kind="ferry rope", surprise_kind="a harbor bell", passes=1),
    "hill_pass": Route(id="hill_pass", label="the hill pass", place="hill_town", fare_kind="pass fare", twist_kind="wooden gate", surprise_kind="a hidden map stand", passes=3),
}

FARE_REGISTRY = {
    "coin_fare": FareRule(id="coin_fare", label="coin fare", amount=3, item="coins", speaker="collector", polite=True),
    "silver_fare": FareRule(id="silver_fare", label="silver fare", amount=1, item="silver coins", speaker="collector", polite=True),
    "button_fare": FareRule(id="button_fare", label="button fare", amount=2, item="buttons", speaker="helper", polite=True),
}

NAMES = {
    "traveler": ["Hank", "Mabel", "Jory", "Nell", "Pru", "Otis", "Tilly", "Wes"],
    "helper": ["Aunt June", "Uncle Reed", "Mina", "Bram", "Ivy", "Tobias", "Lottie", "Silas"],
}
TYPES = ["man", "woman", "boy", "girl", "traveler", "driver"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACE_REGISTRY.items():
        for rid, route in ROUTE_REGISTRY.items():
            if route.place != pid:
                continue
            if pid == "hill_town" and route.id == "bridge":
                continue
            for fid in FARE_REGISTRY:
                combos.append((pid, rid, fid))
    return combos


def valid_stories() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_tale(place: Place, route: Route, fare: FareRule, traveler_name: str, traveler_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    traveler = world.add(Entity(id=traveler_name, kind="character", type=traveler_type, traits=["big-voiced"], meters=_initial_meters(), memes=_initial_memes()))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["civil"], meters=_initial_meters(), memes=_initial_memes()))
    collector = world.add(Entity(id="Gatekeeper", kind="character", type="man", label="the gatekeeper", meters=_initial_meters(), memes=_initial_memes()))

    world.say(f"{traveler.id} was a big-voiced {traveler.type} who could make a mile sound like a fiddle tune.")
    world.say(f"{helper.id} was known for being civil, which meant {helper.pronoun('subject')} could tip {helper.pronoun('possessive')} hat to a storm and still mean it.")
    world.say(f"One bright day, {traveler.id} and {helper.id} came to {place.label}, where the road curved hard and the air smelled like old boards and sweet tea.")

    world.para()
    tally(world, traveler, route)
    civil_talk(world, helper, traveler, f"We ought to ask kindly about the {fare.label}.")
    ask_fare(world, collector, traveler, fare)
    world.say(f"{traveler.id} looked at the gate, the road, and the coin purse, trying to keep a civil face.")

    world.para()
    world.say(f"{helper.id} leaned in and said, \"Maybe the fare is for the bridge.\"")
    suspicion_twist(world, helper, collector)
    traveler.memes["suspicion"] += 1
    world.say(
        f'{traveler.id} scratched {traveler.pronoun("possessive")} chin and said, '
        f'"I have crossed a dozen bridges and never seen one with manners like that."'
    )

    world.para()
    reveal_surprise(world, helper, route, fare)
    pay_fare(world, traveler, collector, fare)
    resolution(world, traveler, helper, collector, route)

    world.facts.update(
        traveler=traveler,
        helper=helper,
        collector=collector,
        place=place,
        route=route,
        fare=fare,
        paid=True,
        surprise=route.surprise_kind,
    )
    return world


SETTINGS = PLACE_REGISTRY
ROUTES = ROUTE_REGISTRY
FARES = FARE_REGISTRY
GIRL_NAMES = ["Nell", "Pru", "Tilly", "Lottie", "Mabel"]
BOY_NAMES = ["Hank", "Jory", "Otis", "Wes", "Bram"]
TALL_TALE_TRAITS = ["big-voiced", "windy", "sturdy", "spangled", "long-legged", "bright-eyed"]


@dataclass
class StoryParams:
    place: str
    route: str
    fare_rule: str
    traveler_name: str
    traveler_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "fare": [("What is a fare?", "A fare is the money or payment asked for a ride, crossing, or trip.")],
    "civil": [("What does civil mean?", "Civil means polite and respectful, especially when people disagree.")],
    "bridge": [("What is a bridge?", "A bridge is a structure that helps people cross water, a road, or a gap.")],
    "ferry": [("What is a ferry?", "A ferry is a boat that carries people across water.")],
    "coin": [("What are coins?", "Coins are small pieces of money made from metal.")],
    "goose": [("What is a goose?", "A goose is a big bird that honks loudly and often walks with a proud strut.")],
    "map": [("What is a map?", "A map is a drawing that shows where places are and how to get there.")],
    "bell": [("What does a bell do?", "A bell rings to call attention, signal a time, or announce something important.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    traveler = f["traveler"]
    helper = f["helper"]
    route = f["route"]
    fare = f["fare"]
    return [
        f'Write a tall-tale style story about a {traveler.type} named {traveler.id}, a civil companion, and a surprising fare.',
        f'Tell a story where {traveler.id} must pay a {fare.label} at {route.label}, but the conversation turns into a twist and a surprise.',
        f'Write a short, child-friendly tall tale that includes the words "fare" and "civil" and ends with a kind discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = f["traveler"]
    helper = f["helper"]
    route = f["route"]
    fare = f["fare"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who came to {place.label} on {route.label} and needed to pay the {fare.label}?",
            answer=f"{traveler.id} came with {helper.id}, and {traveler.id} was the one who had to pay the {fare.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} keep speaking civilly during the argument about the fare?",
            answer=f"{helper.id} wanted everyone to stay polite while they figured out what the fare was really for.",
        ),
        QAItem(
            question=f"What surprise was revealed after the twist about the road?",
            answer=f"The surprise was that the fare was really tied to {route.surprise_kind}, not just the first thing everyone guessed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fare", "civil", "bridge", "coin", "map", "bell", "goose", "ferry"}
    if world.facts["route"].id == "ferry":
        tags.add("ferry")
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
trips(Trav, Route) :- traveler(Trav), route(Route).
civil(Who) :- polite(Who).
needs_fare(Trav, Fare) :- traveler(Trav), fare(Fare), asks_for(Fare).
surprise(Kind) :- surprise_kind(Kind).
twist(Route) :- route(Route), twist_kind(Route, _).
reasonable(Trav, Route, Fare) :- traveler(Trav), route(Route), fare(Fare), civil(Trav).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.has_bridge:
            lines.append(asp.fact("has_bridge", pid))
        if place.has_fare_booth:
            lines.append(asp.fact("has_fare_booth", pid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("place_of", rid, route.place))
        lines.append(asp.fact("fare_kind", rid, route.fare_kind))
        lines.append(asp.fact("twist_kind", rid, route.twist_kind))
        lines.append(asp.fact("surprise_kind", rid, route.surprise_kind))
    for fid, fare in FARES.items():
        lines.append(asp.fact("fare", fid))
        lines.append(asp.fact("asks_for", fid))
        lines.append(asp.fact("fare_amount", fid, fare.amount))
    for trait in ["civil", "polite"]:
        lines.append(asp.fact("trait_word", trait))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about fare, civil talk, dialogue, twist, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--fare-rule", choices=FARES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--traveler-type", choices=TYPES)
    ap.add_argument("--helper-type", choices=TYPES)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.route:
        combos = [c for c in combos if c[1] == args.route]
    if args.fare_rule:
        combos = [c for c in combos if c[2] == args.fare_rule]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, route, fare_rule = rng.choice(sorted(combos))
    traveler_type = args.traveler_type or rng.choice(TYPES)
    helper_type = args.helper_type or rng.choice(TYPES)
    traveler_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_name = args.helper_name or rng.choice(NAMES["helper"])
    return StoryParams(
        place=place,
        route=route,
        fare_rule=fare_rule,
        traveler_name=traveler_name,
        traveler_type=traveler_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_tale(
        SETTINGS[params.place],
        ROUTES[params.route],
        FARES[params.fare_rule],
        params.traveler_name,
        params.traveler_type,
        params.helper_name,
        params.helper_type,
    )
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
    StoryParams(place="river_town", route="bridge", fare_rule="coin_fare", traveler_name="Hank", traveler_type="traveler", helper_name="Mina", helper_type="woman"),
    StoryParams(place="harbor", route="ferry", fare_rule="silver_fare", traveler_name="Mabel", traveler_type="woman", helper_name="Silas", helper_type="man"),
    StoryParams(place="hill_town", route="hill_pass", fare_rule="button_fare", traveler_name="Otis", traveler_type="boy", helper_name="Lottie", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, route, fare) combos:")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.traveler_name}: {p.route} in {p.place} (fare: {p.fare_rule})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
