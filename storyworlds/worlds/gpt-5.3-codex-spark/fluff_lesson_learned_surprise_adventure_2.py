#!/usr/bin/env python3
"""
fluff_lesson_learned_surprise_adventure_2.py
================================================

Seed-inspired short tale:

    Riley and Kiko crossed a windy old ridge with a fluffy drift-cushion.
    A surprise cache in a hard place changed the lesson from "just hurry" to
    "plan with care and teamwork."

The simulation models physical meters and emotional memes and lets the prose
follow the changing state: tension, risk handling, surprise, and lesson outcome.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Region:
    key: str
    name: str
    opening: str
    risk: float
    tension: str
    ending_anchor: str


@dataclass(frozen=True)
class Route:
    key: str
    name: str
    challenge: str
    difficulty: float
    surprise_hint: str
    ending_anchor: str


@dataclass(frozen=True)
class Gear:
    key: str
    name: str
    safety: float
    focus_boost: float
    joy_boost: float
    surprise_boost: float


@dataclass
class StoryParams:
    region: str
    route: str
    gear: str
    hero: str
    hero_gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str) -> str:
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def __str__(self) -> str:
        return self.name


@dataclass
class World:
    params: StoryParams
    region: Region
    route: Route
    gear: Gear
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    world_meters: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str | float | bool] = field(default_factory=dict)
    final_image: str = ""
    surprise_line: str = ""

    def add(self, ent: Entity) -> None:
        self.entities[ent.name] = ent

    def trace(self) -> str:
        rows: list[str] = ["--- world trace ---", f"  region: {self.region.key}", f"  route: {self.route.key}", f"  gear: {self.gear.key}", "  entities:"]
        for ent in self.entities.values():
            rows.append(
                f"    - {ent.name} ({ent.kind}) traits={ent.traits} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  world_meters={self.world_meters}")
        rows.append(f"  facts={self.facts}")
        rows.append(f"  surprise= {self.surprise_line}")
        rows.append(f"  final_image={self.final_image}")
        if self.events:
            rows.append("  events:")
            rows.extend(f"    - {event}" for event in self.events)
        return "\n".join(rows)


REGIONS: dict[str, Region] = {
    "sky_ridge": Region(
        key="sky_ridge",
        name="Sky Ridge",
        opening="the wind-rippled ridge above River Lumen",
        risk=0.62,
        tension="a hard rhythm that kept shifting everyone's balance and made every movement deliberate",
        ending_anchor="a new blue guide cloth tied high above a bend on the bridge line",
    ),
    "moss_pass": Region(
        key="moss_pass",
        name="Moss Pass",
        opening="the moss-covered pass where mist rolled slowly between stone teeth",
        risk=0.48,
        tension="a quiet surface where every soft sound might hide a shift on the stones",
        ending_anchor="a fresh chalk map mark at the tunnel mouth",
    ),
    "sunken_drift": Region(
        key="sunken_drift",
        name="Sunken Drift",
        opening="an old drift path above a wide splash channel",
        risk=0.55,
        tension="stone spray and fine mist, making every handhold slippery and every jump a choice",
        ending_anchor="a repaired handhold post with a bright marker stripe",
    ),
}

ROUTES: dict[str, Route] = {
    "sway_bridge": Route(
        key="sway_bridge",
        name="swaying bridge",
        challenge="narrow bridge that answered each step with a dangerous swing",
        difficulty=0.36,
        surprise_hint="a folded weather tube was tucked in the bridge’s side seam",
        ending_anchor="bridge edge where they tied a new red rope marker",
    ),
    "fog_tunnel": Route(
        key="fog_tunnel",
        name="fog tunnel",
        challenge="thin tunnel where sound bounced back before footsteps had finished",
        difficulty=0.40,
        surprise_hint="the tunnel wall opened onto a hidden hollow with an old signal flag",
        ending_anchor="tunnel wall where they left a bright trail chalk line",
    ),
    "storm_ladder": Route(
        key="storm_ladder",
        name="storm ladder",
        challenge="steep ladder of old wet stone blocks above a rough drop",
        difficulty=0.57,
        surprise_hint="inside a carved shelf, they found a wrapped packet pinned with wax",
        ending_anchor="landing shelf where they fixed the anchor line",
    ),
}

GEARS: dict[str, Gear] = {
    "fluff_breathing_bag": Gear(
        key="fluff_breathing_bag",
        name="fluff breathing bag",
        safety=0.22,
        focus_boost=0.13,
        joy_boost=0.14,
        surprise_boost=0.22,
    ),
    "fluff_tether_line": Gear(
        key="fluff_tether_line",
        name="fluff tether line",
        safety=0.31,
        focus_boost=0.15,
        joy_boost=0.09,
        surprise_boost=0.15,
    ),
    "fluff_lantern": Gear(
        key="fluff_lantern",
        name="fluff lantern",
        safety=0.18,
        focus_boost=0.10,
        joy_boost=0.19,
        surprise_boost=0.29,
    ),
}

REGION_ROUTE_COMPAT = {
    "sky_ridge": ("sway_bridge", "storm_ladder"),
    "moss_pass": ("fog_tunnel", "sway_bridge"),
    "sunken_drift": ("storm_ladder", "fog_tunnel"),
}

ROUTE_GEAR_COMPAT = {
    "sway_bridge": ("fluff_tether_line", "fluff_lantern"),
    "fog_tunnel": ("fluff_breathing_bag", "fluff_lantern"),
    "storm_ladder": ("fluff_breathing_bag", "fluff_tether_line"),
}

HERO_NAMES = {
    "girl": ("Rin", "Nina", "Maya", "Lina", "Tessa"),
    "boy": ("Leo", "Kai", "Noah", "Ari", "Tom"),
}

HELPERS = ("Milo", "Jin", "Sora", "Pip", "Kaya")


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] not in ".!?":
        return text + "."
    return text


def _safe_combo(region: str, route: str, gear: str) -> bool:
    if region not in REGIONS or route not in ROUTES or gear not in GEARS:
        return False
    return route in REGION_ROUTE_COMPAT[region] and gear in ROUTE_GEAR_COMPAT[route]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for region in sorted(REGIONS):
        for route in REGION_ROUTE_COMPAT[region]:
            for gear in ROUTE_GEAR_COMPAT[route]:
                combos.append((region, route, gear))
    return combos


def invalid_reason(region: str, route: str, gear: str) -> str:
    if region not in REGIONS:
        return f"No story: unknown region {region!r}."
    if route not in ROUTES:
        return f"No story: unknown route {route!r}."
    if gear not in GEARS:
        return f"No story: unknown gear {gear!r}."
    if route not in REGION_ROUTE_COMPAT[region]:
        return f"No story: {region.replace('_', ' ')} does not support {route.replace('_', ' ')}."
    if gear not in ROUTE_GEAR_COMPAT[route]:
        return f"No story: {route.replace('_', ' ')} is not safe with {gear.replace('_', ' ')}."
    return "No story: invalid combination."


def _infer_gender(name: str) -> str:
    if name in HERO_NAMES["boy"]:
        return "boy"
    if name in HERO_NAMES["girl"]:
        return "girl"
    return random.choice(tuple(HERO_NAMES))


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    region_key, route_key, gear_key = combo

    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    if hero == helper:
        helper = next(h for h in HELPERS if h != hero)

    if args.gender is None:
        hero_gender = _infer_gender(hero)
    else:
        hero_gender = args.gender

    return StoryParams(region_key, route_key, gear_key, hero, hero_gender, helper, seed=(args.seed or 1) + index)


def build_world(params: StoryParams) -> World:
    if not _safe_combo(params.region, params.route, params.gear):
        raise StoryError(invalid_reason(params.region, params.route, params.gear))

    world = World(
        params=params,
        region=REGIONS[params.region],
        route=ROUTES[params.route],
        gear=GEARS[params.gear],
    )

    hero = Entity(
        name=params.hero,
        kind=params.hero_gender,
        traits=["curious", "ready"],
        meters=defaultdict(float, {
            "stamina": 1.0,
            "balance": 0.85,
            "focus": 0.78,
        }),
        memes=defaultdict(float, {
            "joy": 0.38,
            "caution": 0.46,
            "courage": 0.24,
            "trust": 0.30,
        }),
    )

    helper = Entity(
        name=params.helper,
        kind="boy",
        traits=["steady", "helpful"],
        meters=defaultdict(float, {
            "stamina": 0.95,
            "balance": 0.82,
            "focus": 0.74,
        }),
        memes=defaultdict(float, {
            "joy": 0.33,
            "caution": 0.42,
            "trust": 0.41,
            "curiosity": 0.35,
        }),
    )

    fluff = Entity(
        name="Fluff Pack",
        kind="object",
        traits=["soft", "light"],
        meters=defaultdict(float, {
            "integrity": 1.0,
            "bulk": 0.60,
            "inflation": 0.20,
        }),
        memes=defaultdict(float, {
            "surprise": 0.05,
            "reassurance": 0.40,
        }),
    )

    world.add(hero)
    world.add(helper)
    world.add(fluff)

    world.facts["region"] = world.region.name
    world.facts["route"] = world.route.name
    world.facts["gear"] = world.gear.name
    world.facts["hero"] = hero.name
    world.facts["helper"] = helper.name
    return world


def simulate(world: World) -> None:
    hero = world.entities[world.params.hero]
    helper = world.entities[world.params.helper]
    fluff = world.entities["Fluff Pack"]

    route_pressure = _clamp(world.region.risk + world.route.difficulty - world.gear.safety)
    world.world_meters["route_pressure"] = route_pressure

    hero.meters["focus"] = _clamp(hero.meters["focus"] - world.route.difficulty * 0.20 + world.gear.focus_boost)
    helper.meters["focus"] = _clamp(helper.meters["focus"] - world.route.difficulty * 0.14 + world.gear.focus_boost * 0.8)

    hero.meters["balance"] = _clamp(hero.meters["balance"] - world.region.risk * 0.18 - world.route.difficulty * 0.22)
    helper.meters["balance"] = _clamp(helper.meters["balance"] - world.region.risk * 0.11 - world.route.difficulty * 0.16)

    hero.memes["caution"] = _clamp(hero.memes["caution"] + world.region.risk * 0.6 + world.route.difficulty * 0.4)
    helper.memes["caution"] = _clamp(helper.memes["caution"] + world.region.risk * 0.5 + world.route.difficulty * 0.25)

    hero.memes["courage"] = _clamp(hero.memes["courage"] + (1.0 - route_pressure) * 0.65 + world.gear.safety * 0.8)
    helper.memes["trust"] = _clamp(helper.memes["trust"] + 0.20 + world.gear.safety * 0.3)
    hero.memes["trust"] = _clamp(hero.memes["trust"] + 0.18 + world.gear.joy_boost)

    hero.memes["joy"] = _clamp(hero.memes["joy"] + world.gear.joy_boost * 0.9)
    helper.memes["joy"] = _clamp(helper.memes["joy"] + world.gear.joy_boost)

    fluff.meters["inflation"] = _clamp(fluff.meters["inflation"] + world.gear.surprise_boost)
    fluff.meters["bulk"] = _clamp(fluff.meters["bulk"] - world.route.difficulty * 0.15)

    world.world_meters["teamwork"] = _clamp((hero.memes["trust"] + helper.memes["trust"]) / 2)
    world.world_meters["lesson_readiness"] = _clamp(
        0.18 + hero.memes["courage"] * 0.45 + world.world_meters["teamwork"] * 0.55
    )

    if route_pressure > 0.8:
        world.events.append("near_miss")
        hero.meters["balance"] = _clamp(hero.meters["balance"] - 0.18)
        hero.memes["fear"] = 0.46
        hero.memes["caution"] = _clamp(hero.memes["caution"] + 0.12)
        world.world_meters["lesson_readiness"] = _clamp(world.world_meters["lesson_readiness"] - 0.1)
    else:
        world.events.append("steady_progress")

    if world.params.route == "sway_bridge":
        world.surprise_line = (
            f"{hero.pronoun('subject').capitalize()} moved the {world.gear.name} through a side knot and found a folded weather tube hidden under the bridge seam. "
            f"Inside was a color flag and a tiny carved marker for a safer side grip."
        )
    elif world.params.route == "fog_tunnel":
        world.surprise_line = (
            f"A soft reflected glow from the {world.gear.name} swept the wet wall, and a small hollow appeared under a rock lip. "
            f"The hollow contained an old signal flag bundle and a spool of spare line."
        )
    else:
        world.surprise_line = (
            f"At the midpoint, the old stones shifted and the {world.gear.name} caught a hidden shelf. "
            f"Behind it sat a wrapped packet with dry matches, a map corner, and a hand-sewn fluff ribbon."
        )

    world.facts["route_pressure"] = route_pressure
    world.facts["surprise"] = world.route.surprise_hint
    world.facts["lesson_readiness"] = world.world_meters["lesson_readiness"]
    world.facts["teamwork"] = world.world_meters["teamwork"]

    if world.world_meters["lesson_readiness"] > 0.76:
        world.facts["lesson"] = "careful method and communication protect everyone, even when adventure looks urgent"
    elif "near_miss" in world.events:
        world.facts["lesson"] = "when risk climbs, slowing down and leaning on teamwork is stronger than speed"
    else:
        world.facts["lesson"] = "good tools matter, but watching each step and each clue is what keeps exploration meaningful"

    world.final_image = (
        f"The ending image was a repaired {world.route.ending_anchor}, "
        f"marked with bright cloth from {world.entities[world.params.hero].name}'s softened {world.gear.name}, "
        f"showing the route now gave safer footing for the next child adventurer."
    )


def _render_prompts(world: World) -> list[str]:
    return [
        "Write a child-sized adventure around a risky route with a soft fluffy item.",
        f"Tell a story where {world.entities[world.params.hero].name} reaches {world.region.name} and crosses the {world.route.name}.",
        "Include a surprise discovery in the middle and a clear lesson learned by the end.",
    ]


def _sentence_about_meter(subject: str, metric: str, value: float) -> str:
    if metric == "route_pressure":
        if value > 0.8:
            return f"{subject} faced high pressure in that section and needed to move with caution."
        if value > 0.6:
            return f"{subject} had a moderate challenge and kept close to the planned route."
        return f"{subject} found a readable rhythm and crossed with controlled steps."
    if metric == "teamwork":
        if value > 0.75:
            return f"Teamwork was strong, and each choice was checked by both children."
        return f"Teamwork helped, though choices required extra prompts and verbal checks."
    return f"{subject} tracked {metric} carefully during the route."


def _render_story(world: World) -> str:
    hero = world.entities[world.params.hero]
    helper = world.entities[world.params.helper]
    subj = hero.pronoun("subject")

    route_pressure = float(world.world_meters["route_pressure"])

    opening = (
        f"One morning, {hero.name} and {helper.name} entered {world.region.opening}. "
        f"The air carried {world.region.tension}. Their {world.gear.name} and a {world.route.name} plan were packed together."
    )

    approach = (
        f"They were here to map a forgotten shelter, because a wind-scarred marker had gone missing. "
        f"Their goal was to cross the {world.route.challenge}, and {world.entities['Fluff Pack']} kept a little cushion of fluff at hand for a sudden rescue moment."
    )

    tension = (
        f"At first, {hero.name} checked the path with {helper.name}. "
        f"A tight check of distance, tie points, and breathing rhythm mattered more than speed. "
        f"{_sentence_about_meter(hero.name, "route_pressure", route_pressure)}"
    )

    middle = (
        f"Halfway across, the pressure rose and the team paused to reset their footing. "
        f"{world.surprise_line}"
    )

    if "near_miss" in world.events:
        turn = (
            f"For a split second, {subj} felt a drop under the steps. "
            f"{helper.name} kept the line steady, and {hero.name} shifted weight backward, used the surprise cache, "
            f"and chose a slower, clearer next step instead of rushing."
        )
    else:
        turn = (
            f"They moved through the section using short breaths and one-step checks. "
            f"The world felt calmer after the team matched each action to the next handhold."
        )

    lesson = (
        f"By the time they reached the far side, {hero.name} learned this: {world.facts['lesson']}. "
        f"The surprise gift did not remove risk, but it showed how calm preparation changes a hard problem into a safe one."
    )

    ending = f"{world.final_image}"

    return "\n\n".join([_sentence(opening), _sentence(approach), _sentence(tension), _sentence(middle), _sentence(turn), _sentence(lesson), _sentence(ending)])


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities[world.params.hero]
    helper = world.entities[world.params.helper]

    route_pressure = float(world.world_meters["route_pressure"])
    team = float(world.world_meters["teamwork"])

    return [
        QAItem(
            f"Who started the adventure in {world.region.name}?",
            (
                f"{hero.name} and {helper.name} explored {world.region.name} to recover a trail marker and cross the {world.route.name}. "
                f"They brought the soft fluff pack as emergency support, because the path was not forgiving."
            ),
        ),
        QAItem(
            f"How did the {world.gear.name} change what happened on the route?",
            (
                f"The gear reduced route pressure from roughly {world.region.risk + world.route.difficulty:.2f} to {route_pressure:.2f}. "
                f"That let the team keep control, reduce near-slip moments, and handle the surprise discovery safely."
            ),
        ),
        QAItem(
            "What was the surprise, and what changed as a result?",
            (
                f"The surprise appeared while crossing: they found a hidden cache or signal packet tied to the route, not a random prize. "
                f"It gave them an anchor clue and extra material, and they used it to finish with a safer marked path."
            ),
        ),
        QAItem(
            "What did the hero learn by the end?",
            (
                f"{hero.name} learned that teamwork and deliberate method are the lesson, not force or speed. "
                f"When pressure rose, checking footing and listening to each partner made the route safer and the outcome better."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why does the world validate some route and gear combinations but not others?",
            (
                f"Each route has structural requirements in the registry: some routes need pull strength, some need glide visibility. "
                f"The chosen {world.gear.name} is only paired with routes it can support, which keeps risk simulation realistic."
            ),
        ),
        QAItem(
            "How can we tell whether a child story changed the world physically?",
            (
                f"The ending image is written from world state as a changed object or anchor, such as a repaired handhold and fresh marker. "
                f"That change is recorded in `final_image`, so the lesson is visible after the last paragraph."
            ),
        ),
        QAItem(
            "What indicates lesson readiness in this simulation?",
            (
                f"The meter `lesson_readiness` combines courage and teamwork after the event. "
                f"A higher value means the team coordinated under pressure and can transfer the learning to a similar route later."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_render_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
region(sky_ridge; moss_pass; sunken_drift).
route(sway_bridge; fog_tunnel; storm_ladder).
tool(fluff_breathing_bag; fluff_tether_line; fluff_lantern).

supports(sky_ridge, sway_bridge).
supports(sky_ridge, storm_ladder).
supports(moss_pass, fog_tunnel).
supports(moss_pass, sway_bridge).
supports(sunken_drift, storm_ladder).
supports(sunken_drift, fog_tunnel).

works(sway_bridge, fluff_tether_line).
works(sway_bridge, fluff_lantern).
works(fog_tunnel, fluff_breathing_bag).
works(fog_tunnel, fluff_lantern).
works(storm_ladder, fluff_breathing_bag).
works(storm_ladder, fluff_tether_line).

combo(R, P, T) :- region(R), route(P), tool(T), supports(R, P), works(P, T).
ready :- combo(R, P, T), R != sunken_drift, P != storm_ladder.
#show combo/3.
#show ready/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for region_key in REGIONS:
        rows.append(fact("region", region_key))
        for route_key in REGION_ROUTE_COMPAT[region_key]:
            rows.append(fact("supports", region_key, route_key))
    for route_key in ROUTES:
        rows.append(fact("route", route_key))
        for gear_key in ROUTE_GEAR_COMPAT[route_key]:
            rows.append(fact("works", route_key, gear_key))
    for gear_key in GEARS:
        rows.append(fact("tool", gear_key))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for t, r, g in atoms(model, "combo"):
            combos.add((t, r, g))
    return sorted(combos)


def asp_verify() -> str:
    py = set(valid_combos())
    asp = set(asp_valid_combos())
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")

    for i, combo in enumerate(sorted(py), 1):
        sample = generate(_params_from_combo(type("Args", (), {
            "seed": 7,
            "hero": "Rin",
            "gender": "girl",
            "helper": "Milo",
        })(), combo, i))
        if not sample.story.lower().count("fluff"):
            raise StoryError(f"Generated story for combo {combo} does not include seed word fluff.")
        if not sample.world or not sample.world.final_image:
            raise StoryError(f"Generated story for combo {combo} lacks ending image trace.")
    return f"OK: ASP and Python agree on {len(py)} combos and generated stories validate state-driven endings."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure world with surprise and lesson learned.")
    parser.add_argument("--region", choices=sorted(REGIONS))
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--gear", choices=sorted(GEARS))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    if args.n < 1:
        raise StoryError("No story: -n must be at least 1.")

    options = valid_combos()
    if args.region or args.route or args.gear:
        options = [
            combo
            for combo in options
            if (args.region is None or combo[0] == args.region)
            and (args.route is None or combo[1] == args.route)
            and (args.gear is None or combo[2] == args.gear)
        ]

    if not options:
        raise StoryError(invalid_reason(args.region or "<region>", args.route or "<route>", args.gear or "<gear>"))

    region, route, gear = random.Random((args.seed or 1) + index).choice(options)
    params = _params_from_combo(args, (region, route, gear), index)
    if params.hero == params.helper:
        raise StoryError("No story: hero and helper cannot be the same character.")
    return params


def _format_qa(sample: StorySample) -> str:
    lines: list[str] = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("")
        print(_format_qa(sample))


def _samples_from_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for i, combo in enumerate(valid_combos(), 1):
        params = _params_from_combo(args, combo, i)
        samples.append(generate(params))
    return samples


def _samples_from_n(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    seen: set[str] = set()
    for i in range(args.n * 40):
        if len(samples) >= args.n:
            break
        sample = generate(resolve_params(args, i))
        marker = (sample.params.region, sample.params.route, sample.params.gear, sample.params.hero, sample.params.helper)
        if marker in seen:
            continue
        seen.add(marker)
        samples.append(sample)

    if len(samples) < args.n:
        raise StoryError("Could not produce enough unique stories with the selected constraints.")
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0

    if args.verify:
        try:
            print(asp_verify())
            return 0
        except StoryError as exc:
            print(f"StoryError: {exc}", file=sys.stderr)
            return 1

    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    if args.all:
        samples = _samples_from_all(args)
    else:
        samples = _samples_from_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
