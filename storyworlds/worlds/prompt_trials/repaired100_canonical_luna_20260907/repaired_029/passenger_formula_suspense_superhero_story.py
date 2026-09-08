#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass(frozen=True)
class Route:
    id: str
    city: str
    destination: str
    danger: str
    clue: str
    formula: str
    signal: str
    ending: str


ROUTES = {
    "skyline_loop": Route(
        "skyline_loop",
        "Brighton City",
        "the rooftop rescue tower",
        "a storm had jammed the sky tram above the tallest buildings",
        "the tram lights blinked in a repeating three-short, one-long pattern",
        "lift = courage + clear signals",
        "a faint blue pulse from the passenger cabin",
        "the sky tram glided safely into the rescue tower while the city cheered",
    ),
    "harbor_arc": Route(
        "harbor_arc",
        "Harbor City",
        "the lighthouse island",
        "a fog bank had hidden the last passenger boat from the harbor lights",
        "the boat's bell answered only when the lighthouse beam swept west",
        "safe course = bell + beam + patience",
        "a silver flash beneath the fog",
        "the passenger boat reached the island, and every window shone like a star",
    ),
    "moon_rail": Route(
        "moon_rail",
        "Luna City",
        "the moon garden station",
        "a runaway night train was carrying one passenger toward a broken bridge",
        "the train slowed whenever its wheels crossed a patch of glowing dust",
        "brake = rhythm + gentle pressure",
        "three red sparks under the last carriage",
        "the train stopped before the bridge, and its passenger stepped into the moon garden",
    ),
    "canyon_flight": Route(
        "canyon_flight",
        "Redstone City",
        "the canyon clinic",
        "a rescue plane had lost its landing lights above a narrow canyon",
        "the plane's shadow crossed the canyon floor in two steady sweeps",
        "landing = shadow + wind + trust",
        "a green flare near the canyon wall",
        "the rescue plane landed safely, carrying its passenger to the clinic",
    ),
}


NAMES = ["Luna", "Max", "Nova", "Ravi", "Tess", "Milo"]
HERO_TYPES = ["hero", "heroine"]
POWERS = ["signal-reading", "swift flight", "light-bending", "super hearing"]


@dataclass
class StoryParams:
    route: str
    name: str
    gender: str
    power: str
    passenger: str
    seed: Optional[int] = None


def _check(params: StoryParams) -> None:
    if params.route not in ROUTES:
        raise StoryError(f"unknown route: {params.route}")
    if not params.name.strip():
        raise StoryError("hero name cannot be empty")
    if not params.passenger.strip():
        raise StoryError("passenger name cannot be empty")
    if params.gender not in HERO_TYPES:
        raise StoryError("gender must be hero or heroine")
    if params.power not in POWERS:
        raise StoryError("unknown superpower")


def build_world(params: StoryParams, rng: random.Random) -> World:
    _check(params)
    route = ROUTES[params.route]
    world = World()
    hero = world.add(Entity(
        "hero", "character", params.name,
        meters={"alertness": 1.0, "signal_skill": 1.0},
        memes={"responsibility": 1.0, "suspense": 1.0},
        location=route.city,
    ))
    passenger = world.add(Entity(
        "passenger", "character", params.passenger,
        meters={"safety": 0.0},
        memes={"fear": 1.0},
        location="vehicle",
    ))
    vehicle = world.add(Entity(
        "vehicle", "vehicle", "the stranded vehicle",
        meters={"motion": 0.0, "danger": 1.0},
        memes={"suspense": 1.0},
        location=route.city,
    ))
    formula = world.add(Entity(
        "formula", "clue", route.formula,
        meters={"useful": 1.0},
        memes={"hope": 1.0},
        location=route.city,
    ))
    world.facts.update(
        hero=hero,
        passenger=passenger,
        vehicle=vehicle,
        formula=formula,
        route=route,
        power=params.power,
    )

    world.say(
        f"In {route.city}, {params.name} was a {params.gender} whose power was {params.power}. "
        f"That evening, a warning flashed across the hero's wrist."
    )
    world.say(
        f"{route.danger.capitalize()}. Inside it, passenger {params.passenger} waited while the "
        f"city lights trembled below."
    )
    world.say(f'"Can you hear me?" called {params.name}. "I can hear you," answered {params.passenger}.')
    world.say(
        f'"Then stay calm and watch for my signal," said {params.name}. '
        f'"I will not leave you behind."'
    )

    world.say(
        f"The danger grew sharper when {route.signal} appeared. "
        f"{params.name} could rush forward, but a rush might make the vehicle move in the wrong direction."
    )
    world.say(
        f"Using {params.power}, {params.name} noticed that {route.clue}. "
        f"The clue revealed a formula: {route.formula}."
    )
    world.say(
        f'"I found the pattern," said {params.name}. "If I follow it, the danger should ease." '
        f'"I will count with you," replied {params.passenger}.'
    )
    world.say(
        f"Together they tested one small signal. The vehicle answered, so {params.name} repeated the "
        f"formula carefully instead of guessing."
    )
    world.say(
        f"The suspense broke at last: {route.ending}. "
        f"{params.passenger} was safe because the hero had listened, reasoned, and acted with courage."
    )

    vehicle.meters["danger"] = 0.0
    vehicle.meters["motion"] = 1.0
    passenger.meters["safety"] = 1.0
    passenger.memes["fear"] = 0.0
    hero.memes["suspense"] = 0.0
    world.events.extend(["warning_received", "pattern_observed", "formula_used", "passenger_rescued"])
    return world


def generation_prompts(world: World) -> list[str]:
    route: Route = world.facts["route"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    passenger: Entity = world.facts["passenger"]  # type: ignore[assignment]
    return [
        f"Write a suspenseful superhero story about {hero.label} rescuing passenger {passenger.label}.",
        f"Show how a superhero uses the formula '{route.formula}' to solve a dangerous rescue.",
        f"Include a brief dialogue between {hero.label} and {passenger.label} that changes the rescue plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    route: Route = world.facts["route"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    passenger: Entity = world.facts["passenger"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who was the passenger?",
            f"The passenger was {passenger.label}, who was trapped in the stranded vehicle.",
        ),
        QAItem(
            "What danger threatened the passenger?",
            f"{route.danger.capitalize()}, so the passenger needed a careful rescue.",
        ),
        QAItem(
            "What clue did the hero notice?",
            f"The hero noticed that {route.clue}.",
        ),
        QAItem(
            "What formula guided the rescue?",
            f"The formula was {route.formula}.",
        ),
        QAItem(
            "How did the hero rescue the passenger?",
            f"{hero.label} listened to the signal, followed the formula, and guided the vehicle safely to {route.destination}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a passenger?",
            "A passenger is a person who travels in a vehicle but is not driving it.",
        ),
        QAItem(
            "What is a formula?",
            "A formula is a rule or plan that shows how parts work together to solve a problem.",
        ),
        QAItem(
            "What is suspense?",
            "Suspense is the tense feeling of waiting to learn what will happen next.",
        ),
        QAItem(
            "What makes a superhero helpful?",
            "A helpful superhero uses special abilities responsibly, protects others, and thinks before acting.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.name}:{params.route}")
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) "
            f"location={entity.location!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ROUTE_REGISTRY = ROUTES

ASP_RULES = r"""
safe_route(Route) :- route(Route), has_formula(Route), has_passenger(Route).
rescue_possible(Route) :- safe_route(Route), danger_resolved(Route).
#show rescue_possible/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id in ROUTES:
        lines.extend([
            asp.fact("route", route_id),
            asp.fact("has_formula", route_id),
            asp.fact("has_passenger", route_id),
            asp.fact("danger_resolved", route_id),
        ])
    return "\n".join(lines)


def asp_program(show: str = "#show rescue_possible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        models = asp.solve(asp_program(), models=0)
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    found = set()
    for model in models:
        found.update(asp.atoms(model, "rescue_possible"))
    expected = {(route_id,) for route_id in ROUTES}
    if found != expected:
        print(f"ASP mismatch: expected {sorted(expected)}, got {sorted(found)}")
        return 1
    for i, route_id in enumerate(ROUTES):
        sample = generate(StoryParams(route_id, "Luna", "hero", "signal-reading", "Ari", i))
        if "passenger" not in sample.story.lower() or "formula" not in sample.story.lower():
            print("Generated story omitted required seed words.")
            return 1
    print(f"OK: ASP/Python parity verified for {len(expected)} routes.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    route = args.route or rng.choice(list(ROUTES))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(HERO_TYPES)
    power = args.power or rng.choice(POWERS)
    passenger = args.passenger or rng.choice(["Ari", "Bea", "Kai", "Sam", "Jo"])
    params = StoryParams(route, name, gender, power, passenger, args.seed)
    _check(params)
    return params


CURATED = [
    StoryParams("skyline_loop", "Luna", "heroine", "signal-reading", "Ari", 101),
    StoryParams("harbor_arc", "Max", "hero", "light-bending", "Bea", 102),
    StoryParams("moon_rail", "Nova", "heroine", "super hearing", "Kai", 103),
    StoryParams("canyon_flight", "Ravi", "hero", "swift flight", "Sam", 104),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A suspenseful superhero storyworld about a passenger and a rescue formula."
    )
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=HERO_TYPES)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--passenger")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("Rescue routes:")
            for route in sorted(asp.atoms(model, "rescue_possible")):
                print(" ", route[0])
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(0, args.n)):
            seed = base_seed + i
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
