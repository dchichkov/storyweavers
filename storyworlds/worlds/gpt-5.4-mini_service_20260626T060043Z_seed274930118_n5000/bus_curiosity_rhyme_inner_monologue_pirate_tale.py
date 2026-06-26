#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a curious crew, a bus, and a rhyming plan.

This world models a small harbor-side voyage where a young pirate longs to ride
the bus to the far market. A stern captain worries about the tide, the coins,
and the route. Curiosity pushes the child forward, inner monologue reveals the
hesitation, and rhyme helps the crew choose a safer turn.

The simulation tracks physical meters and emotional memes:
- meter: distance, coins, and weather strain
- meme: curiosity, worry, courage, relief, pride

The tale is constrained so that only reasonable stories are generated:
the bus must be available, the route must be safe enough, and the final
compromise must actually solve the captain's concern.
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

# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    name: str
    place: str
    is_harbor: bool = True
    affords_bus: bool = True


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    role: str
    species: str
    voice: str


@dataclass(frozen=True)
class Route:
    id: str
    name: str
    setting: str
    distance: int
    needs_ticket: bool
    weather: str
    safe_against_tide: bool
    rhyme_hint: str
    monologue_hint: str


@dataclass(frozen=True)
class BusSpec:
    id: str
    label: str
    color: str
    fare: int
    can_cross_tide: bool
    rhyme_offer: str
    ending_image: str


SETTINGS = {
    "harbor": Setting(name="harbor", place="the lantern harbor", is_harbor=True, affords_bus=True),
    "dock": Setting(name="dock", place="the dock road", is_harbor=True, affords_bus=True),
    "market": Setting(name="market", place="the salt market lane", is_harbor=False, affords_bus=True),
}

CHARACTERS = {
    "captain": CharacterSpec(name="Captain Miri", role="captain", species="human", voice="stern"),
    "child": CharacterSpec(name="Nib", role="young pirate", species="human", voice="bright"),
    "conductor": CharacterSpec(name="Busbee", role="conductor", species="human", voice="cheery"),
}

ROUTES = {
    "harbor_to_market": Route(
        id="harbor_to_market",
        name="the lane to the salt market",
        setting="harbor",
        distance=5,
        needs_ticket=True,
        weather="breezy",
        safe_against_tide=True,
        rhyme_hint="to the market bright",
        monologue_hint="maybe the bus can carry my boots and dreams",
    ),
    "dock_to_market": Route(
        id="dock_to_market",
        name="the dock road to the market",
        setting="dock",
        distance=4,
        needs_ticket=True,
        weather="windy",
        safe_against_tide=True,
        rhyme_hint="through the gulls and foam",
        monologue_hint="maybe the wheels will sing louder than the waves",
    ),
    "market_loop": Route(
        id="market_loop",
        name="the short loop around the market",
        setting="market",
        distance=2,
        needs_ticket=False,
        weather="calm",
        safe_against_tide=False,
        rhyme_hint="round the bread and fish",
        monologue_hint="maybe a small ride still counts as an adventure",
    ),
}

BUSES = {
    "blue_bus": BusSpec(
        id="blue_bus",
        label="blue bus",
        color="blue",
        fare=3,
        can_cross_tide=True,
        rhyme_offer="Climb aboard, my little mate; the blue bus keeps to time and tide",
        ending_image="the blue bus rolled on like a tidy wave with wheels",
    ),
    "red_bus": BusSpec(
        id="red_bus",
        label="red bus",
        color="red",
        fare=2,
        can_cross_tide=False,
        rhyme_offer="Step on in and mind the wind; the red bus hums a merry song",
        ending_image="the red bus shone like a bright shell in the sun",
    ),
}

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, object] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    route: str
    bus: str
    seed: Optional[int] = None
    name: str = "Nib"
    captain: str = "Captain Miri"
    inner_monologue: bool = True
    rhyme: bool = True
    curiosity: bool = True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bus story is reasonable if the route fits the setting, the bus can handle
% the route's tide risk, and the fare is not absurd for the chosen bus.
reason(Setting, Route, Bus) :-
    setting(Setting), route(Route), bus(Bus),
    route_setting(Route, Setting),
    route_safe(Route), bus_tide(Bus).

reasonable(Setting, Route, Bus) :-
    reason(Setting, Route, Bus),
    fare_ok(Route, Bus).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.is_harbor:
            lines.append(asp.fact("harbor", sid))
        if s.affords_bus:
            lines.append(asp.fact("affords_bus", sid))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_setting", rid, r.setting))
        if r.safe_against_tide:
            lines.append(asp.fact("route_safe", rid))
        if r.needs_ticket:
            lines.append(asp.fact("needs_ticket", rid))
    for bid, b in BUSES.items():
        lines.append(asp.fact("bus", bid))
        if b.can_cross_tide:
            lines.append(asp.fact("bus_tide", bid))
        lines.append(asp.fact("fare", bid, b.fare))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> set[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return set(asp.atoms(model, "reasonable"))


def python_reasonable() -> set[tuple[str, str, str]]:
    out = set()
    for sid, s in SETTINGS.items():
        for rid, r in ROUTES.items():
            if r.setting != sid:
                continue
            if not s.affords_bus:
                continue
            for bid, b in BUSES.items():
                if r.safe_against_tide and not b.can_cross_tide:
                    continue
                if b.fare < 2:
                    continue
                out.add((sid, rid, bid))
    return out


def asp_verify() -> int:
    a = asp_reasonable()
    p = python_reasonable()
    if a == p:
        print(f"OK: ASP matches Python reasonable() ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(a - p))
    print("only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(params: StoryParams) -> bool:
    s = SETTINGS.get(params.setting)
    r = ROUTES.get(params.route)
    b = BUSES.get(params.bus)
    if not s or not r or not b:
        return False
    if r.setting != params.setting:
        return False
    if not s.affords_bus:
        return False
    if r.safe_against_tide and not b.can_cross_tide:
        return False
    return True


def explain_rejection(params: StoryParams) -> str:
    r = ROUTES[params.route]
    b = BUSES[params.bus]
    if r.setting != params.setting:
        return "No story: that route does not begin in the chosen setting."
    if r.safe_against_tide and not b.can_cross_tide:
        return "No story: that bus cannot safely ride through the tide-swept route."
    return "No story: the choices do not make a believable pirate bus tale."


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate bus storyworld with curiosity, rhyme, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--bus", choices=BUSES)
    ap.add_argument("--name", default="Nib")
    ap.add_argument("--captain", default="Captain Miri")
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
    if args.setting and args.route and ROUTES[args.route].setting != args.setting:
        raise StoryError("No story: the chosen route does not match the chosen setting.")
    if args.setting and args.route and args.bus:
        params = StoryParams(setting=args.setting, route=args.route, bus=args.bus, name=args.name, captain=args.captain)
        if not is_reasonable(params):
            raise StoryError(explain_rejection(params))

    candidates = [
        (sid, rid, bid)
        for sid in SETTINGS
        for rid, r in ROUTES.items()
        for bid in BUSES
        if r.setting == sid
        if (not args.setting or sid == args.setting)
        if (not args.route or rid == args.route)
        if (not args.bus or bid == args.bus)
        if is_reasonable(StoryParams(setting=sid, route=rid, bus=bid))
    ]
    if not candidates:
        raise StoryError("No valid story matches those options.")

    setting, route, bus = rng.choice(sorted(candidates))
    return StoryParams(setting=setting, route=route, bus=bus, name=args.name, captain=args.captain)


def _inner_line(hero: str, hint: str) -> str:
    return f"{hero} wondered, \"{hint}?\""


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError(explain_rejection(params))

    setting = SETTINGS[params.setting]
    route = ROUTES[params.route]
    bus = BUSES[params.bus]

    world = World(setting)
    hero = world.add(Entity(id="child", kind="character", label=params.name, memes={"curiosity": 1.0, "worry": 0.5, "courage": 0.0, "relief": 0.0, "pride": 0.0}))
    captain = world.add(Entity(id="captain", kind="character", label=params.captain, memes={"worry": 1.0, "care": 1.0}))
    conductor = world.add(Entity(id="conductor", kind="character", label="Busbee", memes={"cheer": 1.0}))
    world.add(Entity(id="bus", kind="vehicle", label=bus.label, meters={"fare": bus.fare}, props={"bus": bus}))

    world.facts.update(setting=setting, route=route, bus=bus, hero=hero, captain=captain, conductor=conductor)

    # Act 1: harbor setup.
    world.say(f"At {setting.place}, {params.name} the little pirate stared at the {bus.label}.")
    world.say(f"{params.name} loved the salt wind and the clatter of wheels, and curiosity tugged hard at {params.name}'s sleeve.")
    world.say(f"{params.captain} kept a hand on the coin purse and said the route must be safe and paid.")
    if params.inner_monologue:
        world.say(_inner_line(params.name, route.monologue_hint))

    # Act 2: the worry and the rhyme.
    world.say(f"The bus waited by the quay, ready for {route.name}.")
    world.say(f"Inside, {params.name} counted {bus.fare} coins and listened to gulls crying over the masts.")
    world.say(f"{params.captain} frowned, for the tide was tricky and a flimsy ride could leave a pirate stuck.")
    if params.rhyme:
        world.say(f"{params.name} murmured a rhyme: \"{bus.rhyme_offer}.\"")
        world.say(f"The little verse bounced through the cabin like a shanty, and the captain's brow began to soften.")
    if params.inner_monologue:
        world.say(f"In a small inner voice, {params.name} thought, \"I can be brave if I show a good plan.\"")

    # Act 3: resolution by safe choice.
    world.say(f"{params.name} held up the coins, then pointed to the sign for {route.name}.")
    world.say(f"{params.captain} saw that the {bus.label} could cross the tide and that the lane began where the map said it should.")
    world.say(f"\"Aye,\" said {params.captain}, \"let the bus roll.\"")
    world.say(f"{params.name} climbed aboard, and the {bus.ending_image}.")
    world.say(f"By the end, curiosity had turned into courage, and the harbor felt smaller than the adventure.")

    # emotional update
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["courage"] += 1.0
    hero.memes["relief"] += 1.0
    hero.memes["pride"] += 1.0
    captain.memes["worry"] = 0.0

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    hero = p["hero"].label
    route = p["route"]
    bus = p["bus"].label
    captain = p["captain"].label
    return [
        f"Write a short pirate tale about {hero} wanting to ride the {bus} from the harbor.",
        f"Tell a child-sized story where curiosity, a rhyme, and an inner monologue help {hero} and {captain} choose a safe bus ride.",
        f"Make a gentle pirate story about the {route.name} that ends with the bus rolling away happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    hero = p["hero"].label
    captain = p["captain"].label
    route = p["route"].name
    bus = p["bus"].label
    return [
        QAItem(
            question=f"Who wanted to ride the {bus} in the story?",
            answer=f"{hero} the little pirate wanted to ride the {bus}.",
        ),
        QAItem(
            question=f"Why did {captain} worry about the trip?",
            answer=f"{captain} worried because the route was near the tide and had to be safe before the bus could roll.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=f"They chose the safe route, paid the fare, and let the {bus} carry them to {route}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="Curiosity became courage, and the worry turned into relief as the bus rolled on.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus for?",
            answer="A bus is a large vehicle that carries people along a road so they can travel together.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, like a little song.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's head that tells what they are thinking.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_show() -> str:
    return asp_program("#show reasonable/3.")


CURATED = [
    StoryParams(setting="harbor", route="harbor_to_market", bus="blue_bus", name="Nib", captain="Captain Miri"),
    StoryParams(setting="dock", route="dock_to_market", bus="blue_bus", name="Wren", captain="Captain Miri"),
    StoryParams(setting="market", route="market_loop", bus="red_bus", name="Pip", captain="Captain Miri"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in sorted(asp_reasonable()):
            print(combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            seed = (args.seed if args.seed is not None else rng.randrange(2**31)) + i
            prng = random.Random(seed)
            try:
                params = resolve_params(args, prng)
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
