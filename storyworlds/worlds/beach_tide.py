#!/usr/bin/env python3
"""
storyworlds/worlds/beach_tide.py
===============================

Beach tide safety domain with explicit constraints over tide state, object, location,
and retrieval method.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


TIDE_KEYS = ("low", "rising", "high")
RISK_KEYS = ("float_away", "slippery", "rock_snag", "strong_current")


@dataclass(frozen=True)
class Tide:
    key: str
    phrase: str
    allowed_methods: frozenset[str]
    warning: str


@dataclass(frozen=True)
class Location:
    key: str
    phrase: str
    allowed_methods: frozenset[str]
    objects: frozenset[str]


@dataclass(frozen=True)
class BeachObject:
    key: str
    phrase: str
    risk: str
    allowed_locations: frozenset[str]
    allowed_methods: frozenset[str]


@dataclass(frozen=True)
class RetrievalMethod:
    key: str
    phrase: str
    action: str
    result: str
    lesson: str
    allowed_tides: frozenset[str]
    allowed_locations: frozenset[str]
    solves: frozenset[str]


@dataclass
class StoryParams:
    tide: str
    location: str
    item: str
    method: str
    hero: str
    guardian: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    traits: list[str] = field(default_factory=list)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    tide: Tide
    location: Location
    item: BeachObject
    method: RetrievalMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def trace(self) -> str:
        rows: list[str] = ["--- world model state ---"]
        rows.append(f"  tide: {self.tide.key} ({self.tide.phrase})")
        rows.append(f"  location: {self.location.key} ({self.location.phrase})")
        rows.append(f"  item: {self.item.key} risk={self.item.risk}")
        rows.append(f"  method: {self.method.key} ({self.method.phrase})")
        rows.append(f"  facts: {self.facts}")
        rows.append(f"  fired: {self.fired}")
        for name, ent in self.entities.items():
            traits = ", ".join(ent.traits) if ent.traits else "none"
            rows.append(
                f"  {name:<12} ({ent.kind:<8}) traits=[{traits}] memes={dict(ent.memes)}"
            )
        return "\n".join(rows)


TIDES: dict[str, Tide] = {
    "low": Tide(
        key="low",
        phrase="low and gentle",
        allowed_methods=frozenset({"wade", "pole", "ask_help"}),
        warning="the waterline was near the feet and the sand was firm.",
    ),
    "rising": Tide(
        key="rising",
        phrase="rising and pulling outward",
        allowed_methods=frozenset({"pole", "wait", "ask_help"}),
        warning="water pushed gently but steadily toward the beach edge.",
    ),
    "high": Tide(
        key="high",
        phrase="high and fast against the shore",
        allowed_methods=frozenset({"wait", "ask_help"}),
        warning="the waves were carrying anything near the edge away.",
    ),
}

LOCATIONS: dict[str, Location] = {
    "shoreline": Location(
        key="shoreline",
        phrase="the wide shoreline",
        allowed_methods=frozenset({"wade", "pole", "ask_help"}),
        objects=frozenset({"beach_ball", "seashell"}),
    ),
    "tide_pool": Location(
        key="tide_pool",
        phrase="a clear tide pool",
        allowed_methods=frozenset({"wade", "pole", "wait", "ask_help"}),
        objects=frozenset({"beach_ball", "seashell", "message_bottle"}),
    ),
    "rocky_cove": Location(
        key="rocky_cove",
        phrase="a rocky cove",
        allowed_methods=frozenset({"pole", "ask_help"}),
        objects=frozenset({"message_bottle", "life_ring"}),
    ),
    "boat_dock": Location(
        key="boat_dock",
        phrase="a small boat dock",
        allowed_methods=frozenset({"pole", "wait", "ask_help"}),
        objects=frozenset({"beach_ball", "life_ring"}),
    ),
}

OBJECTS: dict[str, BeachObject] = {
    "beach_ball": BeachObject(
        key="beach_ball",
        phrase="a bright beach ball",
        risk="float_away",
        allowed_locations=frozenset({"shoreline", "tide_pool", "boat_dock"}),
        allowed_methods=frozenset({"wade", "pole", "wait", "ask_help"}),
    ),
    "seashell": BeachObject(
        key="seashell",
        phrase="a smooth seashell",
        risk="slippery",
        allowed_locations=frozenset({"shoreline", "tide_pool", "rocky_cove"}),
        allowed_methods=frozenset({"wade", "pole", "ask_help"}),
    ),
    "message_bottle": BeachObject(
        key="message_bottle",
        phrase="a drifting message bottle",
        risk="strong_current",
        allowed_locations=frozenset({"tide_pool", "rocky_cove", "boat_dock"}),
        allowed_methods=frozenset({"ask_help"}),
    ),
    "life_ring": BeachObject(
        key="life_ring",
        phrase="a bright orange life ring",
        risk="rock_snag",
        allowed_locations=frozenset({"rocky_cove", "boat_dock"}),
        allowed_methods=frozenset({"pole", "ask_help"}),
    ),
}

METHODS: dict[str, RetrievalMethod] = {
    "wade": RetrievalMethod(
        key="wade",
        phrase="wading in carefully",
        action=(
            "{hero} stepped carefully through the shallows, stayed on the wet sand, "
            "and reached for {item} without turning around or running."
        ),
        result=(
            "{hero} pulled {item} back to dry sand and kept each step small and steady."
        ),
        lesson="Shallow water can be safe, but only if you go slow and never lose balance.",
        allowed_tides=frozenset({"low"}),
        allowed_locations=frozenset({"shoreline", "tide_pool"}),
        solves=frozenset({"float_away", "slippery"}),
    ),
    "pole": RetrievalMethod(
        key="pole",
        phrase="using a long retrieval pole",
        action=(
            "{guardian} passed {hero} a long pole and said, 'Keep distance.' "
            "{hero} hooked {item} and drew it back without stepping out too far."
        ),
        result=(
            "{hero} brought {item} ashore on the pole's arm, then checked it carefully "
            "before putting it away."
        ),
        lesson="Keep your distance and use distance tools when tide or rocks make the shore hard to reach.",
        allowed_tides=frozenset({"low", "rising"}),
        allowed_locations=frozenset({"shoreline", "tide_pool", "rocky_cove", "boat_dock"}),
        solves=frozenset({"float_away", "slippery", "rock_snag"}),
    ),
    "wait": RetrievalMethod(
        key="wait",
        phrase="waiting for the tide to drop",
        action=(
            "Noticing the water was moving fast, {hero} waited and watched the tide "
            "from a safe distance."
        ),
        result=(
            "After a while the waterline fell, and {item} settled where {hero} could pick it up safely."
        ),
        lesson="Sometimes the safest move is patience and timing.",
        allowed_tides=frozenset({"rising", "high"}),
        allowed_locations=frozenset({"shoreline", "tide_pool", "boat_dock"}),
        solves=frozenset({"float_away", "slippery", "rock_snag"}),
    ),
    "ask_help": RetrievalMethod(
        key="ask_help",
        phrase="asking a guardian for help",
        action=(
            "{hero} waved to {guardian} and asked for help right away instead of trying alone."
        ),
        result=(
            "{guardian} came quickly, secured {item} safely, and gave a calm, short safety reminder."
        ),
        lesson="Asking for help early is the strongest safety choice when the water is uncertain.",
        allowed_tides=frozenset({"low", "rising", "high"}),
        allowed_locations=frozenset({"shoreline", "tide_pool", "rocky_cove", "boat_dock"}),
        solves=frozenset(RISK_KEYS),
    ),
}

HEROS = {
    "girl": ("Maya", "Leah", "Nora"),
    "boy": ("Noah", "Eli", "Jace"),
}
GUARDIANS = ("Ms. Rae", "Coach Ana", "Sam", "Tomas")


def _pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(HEROS[gender])


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    hero = args.hero or _pick_name(args.gender or rng.choice(tuple(HEROS)), rng)
    if args.gender is None:
        hero_gender = "girl" if hero in HEROS["girl"] else "boy"
    else:
        hero_gender = args.gender
    # keep a predictable gendered protagonist if explicit gender is provided
    if args.gender and args.hero is None and hero not in HEROS[args.gender]:
        hero = _pick_name(args.gender, rng)
        hero_gender = args.gender
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(
        tide=combo[0],
        location=combo[1],
        item=combo[2],
        method=combo[3],
        hero=hero,
        guardian=guardian,
        seed=(args.seed or 1) + index,
    )


def valid_combo(
    tide_key: str,
    location_key: str,
    item_key: str,
    method_key: str,
) -> bool:
    if (
        tide_key not in TIDES
        or location_key not in LOCATIONS
        or item_key not in OBJECTS
        or method_key not in METHODS
    ):
        return False
    tide = TIDES[tide_key]
    location = LOCATIONS[location_key]
    item = OBJECTS[item_key]
    method = METHODS[method_key]

    return (
        item_key in location.objects
        and method_key in tide.allowed_methods
        and method_key in location.allowed_methods
        and method_key in item.allowed_methods
        and location_key in method.allowed_locations
        and item.risk in method.solves
    )


def invalid_reason(tide_key: str, location_key: str, item_key: str, method_key: str) -> str:
    if tide_key not in TIDES:
        return f"No story: unknown tide {tide_key!r}."
    if location_key not in LOCATIONS:
        return f"No story: unknown location {location_key!r}."
    if item_key not in OBJECTS:
        return f"No story: unknown item {item_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown retrieval method {method_key!r}."

    tide = TIDES[tide_key]
    location = LOCATIONS[location_key]
    item = OBJECTS[item_key]
    method = METHODS[method_key]

    if item_key not in location.objects:
        return (
            f"No story: {item.phrase} is not at {location.phrase}; available items are: "
            f"{', '.join(sorted(location.objects))}."
        )
    if method_key not in tide.allowed_methods or method_key not in location.allowed_methods:
        return (
            f"No story: {method.phrase} is not allowed for tide={tide_key}, location={location_key}."
        )
    if method_key not in item.allowed_methods:
        return f"No story: {method.phrase} does not match {item.phrase}'s handling risk."
    if method_key not in method.allowed_locations:
        return f"No story: {method.phrase} is not intended for {location.phrase}."
    if item.risk not in method.solves:
        return (
            f"No story: {method.phrase} does not address {item.risk.replace('_', ' ')} risk."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for tide_key in TIDE_KEYS:
        for location_key in sorted(LOCATIONS):
            for item_key in sorted(OBJECTS):
                for method_key in sorted(METHODS):
                    if valid_combo(tide_key, location_key, item_key, method_key):
                        combos.append((tide_key, location_key, item_key, method_key))
    return combos


def build_world(params: StoryParams) -> World:
    tide = TIDES[params.tide]
    location = LOCATIONS[params.location]
    item = OBJECTS[params.item]
    method = METHODS[params.method]

    hero_gender = "girl" if params.hero in HEROS["girl"] else "boy"
    guardian_kind = "adult" if " " not in params.guardian else params.guardian.split()[0].lower()
    guardian_kind = guardian_kind if guardian_kind in {"adult", "coach", "uncle", "aunt", "mom", "dad"} else "adult"

    world = World(params=params, tide=tide, location=location, item=item, method=method)
    world.add(Entity(params.hero, kind=hero_gender, traits=["curious", "cautious"], memes={"joy": 0.2}))
    world.add(Entity(params.guardian, kind=guardian_kind, traits=["watchful", "helpful"], memes={"care": 1.0}))
    world.facts["tide"] = tide.key
    world.facts["location"] = location.key
    world.facts["item"] = item.key
    world.facts["method"] = method.key
    world.facts["risk"] = item.risk
    world.facts["seed"] = str(params.seed)
    world.facts["hero"] = params.hero
    world.facts["guardian"] = params.guardian
    world.fired.append("safe-retrieval-chosen")
    return world


def _render_story(world: World) -> str:
    hero = world.entities[world.params.hero]
    method = world.method
    location = world.location
    tide = world.tide
    item = world.item
    guardian = world.entities[world.params.guardian]
    item_text = item.phrase

    opening = (
        f"The tide was {tide.phrase} at {location.phrase}, and {tide.warning} "
        f"{hero.id} saw {item_text} drift farther from the edge."
    )
    if item.key == "message_bottle":
        warning = f"{guardian.id} warned, 'Keep a distance; strong current can pull things out too fast.'"
    elif item.key == "life_ring":
        warning = f"{guardian.id} pointed out the rocks and said, '{hero.id}, anything near the cove can snag quickly.'"
    elif item.key == "seashell":
        warning = f"{guardian.id} said, 'The waterline is slick there; slow hands and long distance are safer.'"
    else:
        warning = f"{hero.id} noticed the object might wash away, and {guardian.id} called it out as risky."

    action = method.action.format(hero=hero.id, guardian=guardian.id, item=item_text)
    outcome = method.result.format(hero=hero.id, guardian=guardian.id, item=item_text)
    lesson = (
        f'{method.lesson} In the end, {hero.id} learned that tide-aware retrieval keeps the beach fun and safe.'
    )
    return "\n\n".join([opening, warning, action, outcome, lesson])


def _prompts(world: World) -> list[str]:
    return [
        "Write a beach safety story focused on tide, risk, and a safe retrieval choice.",
        f"Show how {world.params.hero} finds a safer way to recover an object near {world.location.phrase}.",
        "Explain why the chosen method is safer than rushing toward the water.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities[world.params.hero]
    guardian = world.entities[world.params.guardian]
    item = world.item
    method = world.method
    return [
        QAItem("Who are the characters?", f"{hero.id} and {guardian.id} are at the beach."),
        QAItem(
            f"What did {hero.id} see at the water line?",
            f"{hero.id} saw {item.phrase} near {world.location.phrase}.",
        ),
        QAItem(
            "What was risky about the situation?",
            f"The object was in moving water, and the tide was {world.tide.phrase}, which changed the safety of approach.",
        ),
        QAItem(
            "What safe retrieval method was used?",
            f"{hero.id} used {method.phrase}, which matched the tide, place, and object risk.",
        ),
        QAItem(
            "What was the outcome?",
            f"{item.phrase.capitalize()} was recovered safely, and everyone stayed on safer footing instead of rushing into the water.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    base = [
        QAItem(
            "Why do method constraints depend on tide?",
            "Different tides change water force and reach, so the same action can be safe at low tide but unsafe at high tide.",
        ),
        QAItem(
            "Why is asking for help considered safe in this world?",
            "A helper can stay farther from hazards while keeping the risky action controlled and visible.",
        ),
    ]
    if world.tide.key in {"rising", "high"}:
        base.append(QAItem("Which retrieval style is usually avoided at these tides?", "Short solo or deep wading is avoided when the tide is rising or high."))
    if world.item.risk == "strong_current":
        base.append(QAItem("Why was this object restricted to careful retrieval?", "A strong current can pull objects and people faster than expected."))
    if world.item.risk == "rock_snag":
        base.append(QAItem("Why is distance important near rocks?", "Distance prevents hands from being pulled into snag points around uneven rock surfaces."))
    return base


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.tide, params.location, params.item, params.method):
        raise StoryError(invalid_reason(params.tide, params.location, params.item, params.method))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
tide(T) :- method_allowed_tide(T, M).
location(L) :- object_at(L, O).
object(O) :- object_risk(O, _).
method(M) :- method_solves(M, _).

combo(T, L, O, M) :-
    tide(T), location(L), object(O), method(M),
    object_at(O, L),
    tide_allows(T, M),
    location_allows(L, M),
    object_allows(O, M),
    object_risk(O, R),
    method_solves(M, R).

ok :- chosen(T, L, O, M), combo(T, L, O, M).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for tide_key, tide in TIDES.items():
        rows.append(fact("tide", tide_key))
        for method_key in tide.allowed_methods:
            rows.append(fact("tide_allows", tide_key, method_key))
    for location_key, location in LOCATIONS.items():
        rows.append(fact("location", location_key))
        for item_key in location.objects:
            rows.append(fact("object_at", item_key, location_key))
        for method_key in location.allowed_methods:
            rows.append(fact("location_allows", location_key, method_key))
    for item_key, item in OBJECTS.items():
        rows.append(fact("object", item_key))
        rows.append(fact("object_risk", item_key, item.risk))
        for method_key in item.allowed_methods:
            rows.append(fact("object_allows", item_key, method_key))
    for method_key, method in METHODS.items():
        rows.append(fact("method", method_key))
        for risk in method.solves:
            rows.append(fact("method_solves", method_key, risk))
        for location_key in method.allowed_locations:
            rows.append(fact("method_allowed_location", method_key, location_key))
    if params is not None:
        rows.append(fact("chosen", params.tide, params.location, params.item, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for combo in atoms(model, "combo"):
            combos.add(tuple(combo))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {tuple(combo) for combo in valid_combos()}
    asp = asp_valid_combos()
    if python_combos != asp:
        only_py = sorted(python_combos - asp)
        only_asp = sorted(asp - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")
    return f"OK: Python and ASP gates agree for {len(python_combos)} combos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate beach tide safety samples.")
    parser.add_argument("--tide", choices=TIDE_KEYS)
    parser.add_argument("--location", choices=tuple(LOCATIONS))
    parser.add_argument("--item", choices=tuple(OBJECTS))
    parser.add_argument("--method", choices=tuple(METHODS))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=tuple(HEROS), default=None)
    parser.add_argument("--guardian", default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    combos = valid_combos()
    if args.tide or args.location or args.item or args.method:
        filtered = [
            combo
            for combo in combos
            if (args.tide is None or combo[0] == args.tide)
            and (args.location is None or combo[1] == args.location)
            and (args.item is None or combo[2] == args.item)
            and (args.method is None or combo[3] == args.method)
        ]
        if not filtered:
            raise StoryError(invalid_reason(args.tide or "<tide>", args.location or "<location>", args.item or "<item>", args.method or "<method>"))
        combo = rng.choice(filtered)
    else:
        combo = rng.choice(combos)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for tide_key, location_key, item_key, method_key in sorted(asp_valid_combos()):
        print(f"{tide_key}\t{location_key}\t{item_key}\t{method_key}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]} / {combo[3]}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0
        for i in range(max(1, args.n)):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if args.n > 1 and not args.json else None)
            if i != max(1, args.n) - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
