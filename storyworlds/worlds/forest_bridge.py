#!/usr/bin/env python3
"""
forest_bridge.py
================

A deterministic storyworld for the forest bridge problem-solving pattern.

The parameters are:

- crossing: which forest bridge must be crossed
- weather: current forest conditions
- tool: what help the hero carries

The generator only accepts combinations where the tool can meaningfully address
the active hazards from the chosen crossing and weather.  A small world model
tracks the remaining crossing risk and uses it to shape prose and QA.
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


@dataclass(frozen=True)
class Crossing:
    key: str
    name: str
    phrase: str
    hazards: tuple[str, ...]
    critical_hazards: tuple[str, ...]


@dataclass(frozen=True)
class Tool:
    key: str
    phrase: str
    prep: str
    handles: tuple[str, ...]
    mitigation: dict[str, int]
    detail: str


@dataclass(frozen=True)
class Weather:
    key: str
    name: str
    phrase: str
    hazards: tuple[str, ...]
    lesson: str


@dataclass
class StoryParams:
    crossing: str
    tool: str
    weather: str
    hero: str
    gender: str
    seed: int


@dataclass
class Entity:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class World:
    params: StoryParams
    crossing: Crossing
    tool: Tool
    weather: Weather
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    active_hazards: list[str] = field(default_factory=list)
    residual_hazards: list[tuple[str, int, int, int]] = field(default_factory=list)
    risk: float = 0.0

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  chosen crossing: {self.crossing.key}")
        rows.append(f"  chosen tool: {self.tool.key}")
        rows.append(f"  chosen weather: {self.weather.key}")
        rows.append(f"  active hazards: {', '.join(self.active_hazards) or 'none'}")
        rows.append(f"  residual risk: {self.risk:.2f}")
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            rows.append(f"  {name} ({ent.role})")
            if meters:
                rows.append(f"    meters: {meters}")
            if memes:
                rows.append(f"    memes: {memes}")
        if self.events:
            rows.append("  events:")
            for event in self.events:
                rows.append(f"    - {event}")
        return "\n".join(rows)


HAZARD_SCORE: dict[str, int] = {
    "wet": 2,
    "slip": 2,
    "wind": 3,
    "sway": 2,
    "dark": 1,
}

HAZARD_ORDER = ("wet", "slip", "wind", "sway", "dark")
MAX_RISK = 4


CROSSINGS: dict[str, Crossing] = {
    "moss_bridge": Crossing(
        "moss_bridge",
        "a mossy board bridge",
        "the boards were slick from old dew and mud",
        ("wet", "slip"),
        ("wet", "slip"),
    ),
    "storm_bridge": Crossing(
        "storm_bridge",
        "a narrow bridge over a roaring gorge",
        "the planks trembled and moved with every gust",
        ("wind", "sway", "slip", "wet"),
        ("wind", "sway", "slip"),
    ),
    "fog_stepping": Crossing(
        "fog_stepping",
        "a fog-wrapped bridge of old stepping stones",
        "the stones were hard to see through the gray air",
        ("dark", "slip"),
        ("dark",),
    ),
    "river_bridge": Crossing(
        "river_bridge",
        "a long bridge above a fast creek",
        "the wood had small gaps and the side rail was loose",
        ("slip",),
        ("slip",),
    ),
}

TOOLS: dict[str, Tool] = {
    "board_strips": Tool(
        "board_strips",
        "wooden strips",
        "laid two narrow wooden strips across the wet spots",
        ("wet", "slip"),
        {"wet": 2, "slip": 2},
        "This helps keep feet out of the slickest spots and improves footing.",
    ),
    "rope_harness": Tool(
        "rope_harness",
        "a rope harness",
        "fastened a rope harness around the waist and looped it forward",
        ("sway", "slip", "wind"),
        {"sway": 2, "slip": 2, "wind": 3},
        "This lets the child stay stable when the bridge shifts and fights wind.",
    ),
    "waterproof_sheet": Tool(
        "waterproof_sheet",
        "a waterproof sheet",
        "wrapped the sheet over the hero’s outer layer",
        ("wet",),
        {"wet": 2},
        "This protects against wetness but does nothing for shifting planks.",
    ),
    "lantern": Tool(
        "lantern",
        "an old lantern",
        "lit a lantern and fixed it to a branch above the bridge",
        ("dark",),
        {"dark": 2},
        "This helps visibility in foggy or dim sections but no longer prevents slipping.",
    ),
    "all_round_gear": Tool(
        "all_round_gear",
        "an all-round harness kit",
        "used a small kit that included a rope line and a lantern",
        ("wet", "slip", "wind", "sway", "dark"),
        {"wet": 2, "slip": 2, "wind": 3, "sway": 2, "dark": 1},
        "This is the safest setup when weather is difficult.",
    ),
}

WEATHERS: dict[str, Weather] = {
    "clear": Weather("clear", "clear weather", "the air was cool and dry", (), "Good timing can make a hard route feel easy."),
    "drizzle": Weather("drizzle", "drizzle", "a fine mist kept the wood damp", ("wet",), "Small rain turns rough wood into a slick surface."),
    "fog": Weather("fog", "heavy fog", "the fog swallowed the bridge edges", ("dark",), "Fog hides footing and slows reaction."),
    "wind": Weather("wind", "strong wind", "gusts shook loose branches near the crossing", ("wind", "sway"), "Wind pushes and pulls at the body."),
    "storm": Weather(
        "storm",
        "a full storm",
        "rain and wind together made the crossing a real challenge",
        ("wet", "wind", "sway", "dark"),
        "Bad weather is only solvable if preparation is strong.",
    ),
}

HEROES: dict[str, tuple[str, ...]] = {
    "boy": ("Noah", "Luca", "Eli", "Toby", "Theo"),
    "girl": ("Maya", "Riley", "Iris", "Nora", "Leah"),
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _ordered_hazards(hazards: Iterable[str]) -> list[str]:
    return [h for h in HAZARD_ORDER if h in set(hazards)]


def active_hazards(crossing: Crossing, weather: Weather) -> list[str]:
    seen: set[str] = set()
    ordered = []
    for h in _ordered_hazards(crossing.hazards + weather.hazards):
        if h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered


def crossing_risk(crossing: Crossing, tool: Tool, weather: Weather) -> tuple[float, list[tuple[str, int, int, int]]]:
    hazards = active_hazards(crossing, weather)
    residuals: list[tuple[str, int, int, int]] = []
    total = 0
    for hazard in hazards:
        score = HAZARD_SCORE[hazard]
        mitigates = tool.mitigation.get(hazard, 0)
        residual = max(0, score - mitigates)
        residuals.append((hazard, score, mitigates, residual))
        total += residual
    return float(total), residuals


def valid_combo(crossing_key: str, tool_key: str, weather_key: str) -> bool:
    if crossing_key not in CROSSINGS or tool_key not in TOOLS or weather_key not in WEATHERS:
        return False
    crossing = CROSSINGS[crossing_key]
    tool = TOOLS[tool_key]
    weather = WEATHERS[weather_key]
    if not set(crossing.critical_hazards).issubset(set(tool.handles)):
        return False
    risk, _ = crossing_risk(crossing, tool, weather)
    return risk <= MAX_RISK


def invalid_reason(crossing_key: str, tool_key: str, weather_key: str) -> str:
    if crossing_key not in CROSSINGS:
        return f"No story: unknown crossing {crossing_key!r}."
    if tool_key not in TOOLS:
        return f"No story: unknown tool {tool_key!r}."
    if weather_key not in WEATHERS:
        return f"No story: unknown weather {weather_key!r}."
    crossing = CROSSINGS[crossing_key]
    tool = TOOLS[tool_key]
    weather = WEATHERS[weather_key]
    for needed in crossing.critical_hazards:
        if needed not in tool.handles:
            return (
                f"No story: {tool.phrase} does not directly handle the key hazard "
                f"{needed!r} for {crossing.name}."
            )
    risk, _ = crossing_risk(crossing, tool, weather)
    if risk > MAX_RISK:
        return (
            f"No story: {weather.phrase}, combined with {crossing.name}, leaves "
            f"too much unresolved risk for {tool.phrase} (residual {risk:.2f} > {MAX_RISK})."
        )
    return "No story: the request is unreasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crossing in CROSSINGS:
        for tool in TOOLS:
            for weather in WEATHERS:
                if valid_combo(crossing, tool, weather):
                    combos.append((crossing, tool, weather))
    return combos


def build_world(params: StoryParams) -> World:
    crossing = CROSSINGS[params.crossing]
    tool = TOOLS[params.tool]
    weather = WEATHERS[params.weather]
    world = World(params=params, crossing=crossing, tool=tool, weather=weather)
    hero = Entity(params.hero, "hero")
    bridge = Entity(crossing.name, "bridge")
    weather_entity = Entity(weather.name, "weather")
    bridge.add_meter("risk", 0.0)
    hero.add_meme("caution", 0.0)
    hero.add_meme("confidence", 1.0)
    world.entities["hero"] = hero
    world.entities["bridge"] = bridge
    world.entities["weather"] = weather_entity

    hazards = active_hazards(crossing, weather)
    world.active_hazards = hazards
    world.events.append(f"Active hazards for this run: {', '.join(hazards) or 'none'}.")

    risk, residuals = crossing_risk(crossing, tool, weather)
    world.residual_hazards = residuals
    world.risk = risk
    world.entities["bridge"].add_meter("risk", risk)
    weather_entity.add_meme("force", round(len(hazards) * 0.2, 2))
    world.entities["hero"].add_meme("caution", min(1.0, 0.2 + 0.15 * risk))

    if risk <= 1:
        bridge.add_meter("stability", 1.0)
        hero.add_meme("confidence", 1.4)
        hero.add_meme("joy", 0.4)
        world.events.append(
            f"The combo left only manageable risk ({risk:.2f}); the crossing felt controllable with care."
        )
    elif risk <= MAX_RISK:
        bridge.add_meter("stability", 0.4)
        hero.add_meme("caution", 0.65)
        hero.add_meme("resolve", 0.6)
        world.events.append(
            f"Some danger remained ({risk:.2f}); the solution worked, but crossing needed careful rhythm."
        )
    else:
        bridge.add_meter("stability", 0.0)
        hero.add_meme("frustration", 0.8)
        hero.add_meme("resolve", 0.2)
        world.events.append(
            f"The setup was unsafe at residual risk {risk:.2f}; this state should not be produced by valid combos."
        )
    return world


def _risk_line(world: World) -> str:
    if not world.residual_hazards:
        return "The crossing hazards were fully controlled."
    unresolved = [h.replace("_", " ") for h, _, _, residual in world.residual_hazards if residual]
    controlled = [h.replace("_", " ") for h, _, _, residual in world.residual_hazards if not residual]
    if unresolved and controlled:
        return (
            f"{tool_phrase(world.tool).capitalize()} helped with {', '.join(controlled)}, "
            f"but {', '.join(unresolved)} still needed slow, careful steps."
        )
    if unresolved:
        return f"The plan reduced the danger, but {', '.join(unresolved)} still needed slow, careful steps."
    return f"{tool_phrase(world.tool).capitalize()} controlled the main hazards before the crossing began."


def tool_phrase(tool: Tool) -> str:
    return tool.phrase


def _render_story(world: World) -> str:
    p = world.params
    he, his, him = _pronouns(p.gender)
    crossing = world.crossing
    tool = world.tool
    weather = world.weather
    risk = world.risk
    hero_name = p.hero
    hero_memes = world.entities["hero"].memes

    opener = (
        f"{hero_name} saw that {crossing.phrase} on the bridge across the deep part of the forest path. "
        f"To visit the meadow beyond, {he} would have to cross before dark."
    )
    weather_line = f"Today, {weather.phrase}. {weather.lesson} That meant each step had to be handled with intention."
    prep = (
        f"{hero_name} chose {tool.phrase}. {he.capitalize()} {tool.prep}. {tool.detail} "
        f"{hero_name} checked every step before stepping onto the bridge."
    )
    detail = _risk_line(world)
    if risk <= 1:
        crossing_line = (
            f"With {tool.phrase}, {his} movement stayed steady and the bridge hardly shook. "
            f"{hero_name} crossed at a calm pace and reached the other side safely."
        )
    else:
        crossing_line = (
            f"{hero_name} crossed with the plan in place, counting each plank before stepping. "
            f"Some sections still rocked, but {his} care and the safer plan kept {him} balanced."
        )
    closing = (
        f"When {hero_name} reached the far end, {his} breath settled and {his} courage settled too. "
        f"The lesson was clear: knowing what a crossing and what the weather require is part of getting anywhere."
    )
    if hero_memes.get("caution", 0.0) >= 0.6:
        closing = (
            f"When {hero_name} reached the far end, {his} breath settled and {his} focus stayed sharp. "
            f"The lesson was clear: planning for weather is how a problem becomes solvable."
        )
    return "\n\n".join([opener, weather_line, prep, detail, crossing_line, closing])


def _prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Tell a forest bridge problem-solving story with {world.crossing.name}, {world.tool.phrase}, and {world.weather.name}.",
        "Describe how the right preparation turns a risky route into a solvable path.",
        "Write a child-focused adventure where weather changes the crossing strategy.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    p = world.params
    he, his, him = _pronouns(p.gender)
    weather = world.weather
    return [
        QAItem("Where did the child need to cross?", f"{p.hero} needed to cross {world.crossing.name} in the forest."),
        QAItem(
            "What made the route risky?",
            f"The crossing and weather created risks around {', '.join(h.replace('_', ' ') for h in world.active_hazards) or 'the path'}. Those risks mattered because each step had to stay balanced and visible.",
        ),
        QAItem(
            "What tool did the child choose and why?",
            f"{p.hero} used {world.tool.phrase} because it directly addressed the hazards on that crossing."
        ),
        QAItem(
            "How did weather affect the difficulty?",
            f"The weather changed the challenge by adding {', '.join(h.replace('_', ' ') for h in weather.hazards) or 'very little extra risk'}. "
            f"That changed what preparation {p.hero} needed before crossing.",
        ),
        QAItem(
            "What lesson did the story show?",
            "Planning for the exact hazards first is better than rushing forward in a problem.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    qa = [
        QAItem(
            "Why does wet wood matter on a bridge?",
            "Wet wood is slippery, so footing can slide before a foot is fully stable."
        ),
        QAItem(
            "Why can a rope harness help when a bridge sways?",
            "A harness can stabilize balance by giving a fixed reference point for the body when the bridge moves."
        ),
        QAItem(
            "What does a lantern do in foggy weather?",
            "It improves visibility, so the child can see the next step before stepping."
        ),
    ]
    if "dark" in world.active_hazards:
        qa.append(
            QAItem(
                "Why was lighting especially important?",
                "Darkness made the stepping points harder to judge, so better lighting reduced mistakes."
            )
        )
    return qa


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.crossing, params.tool, params.weather):
        raise StoryError(invalid_reason(params.crossing, params.tool, params.weather))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
crossing_combo(C, T, W) :-
    crossing(C), tool(T), weather(W),
    not critical_missing(C, T),
    hazard_total(C, W, Total),
    tool_total(C, W, T, Mit),
    R = Total - Mit,
    R >= 0,
    R <= 4.

critical_missing(C, T) :-
    crossing(C), tool(T),
    crossing_critical(C, H),
    not tool_handle(T, H, _).

hazard_total(C, W, Sum) :-
    crossing(C), weather(W),
    Sum = #sum {S,H : active_hazard(C, W, H), hazard_score(H, S)}.

tool_total(C, W, T, Sum) :-
    crossing(C), weather(W), tool(T),
    Sum = #sum {S,H : active_hazard(C, W, H), tool_handle(T, H, S)}.

active_hazard(C, W, H) :- crossing(C), weather(W), crossing_hazard(C, H).
active_hazard(C, W, H) :- crossing(C), weather(W), weather_hazard(W, H).

ok :- chosen(C, T, W), crossing_combo(C, T, W).
#show crossing_combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, crossing in CROSSINGS.items():
        rows.append(fact("crossing", key))
        for hazard in crossing.hazards:
            rows.append(fact("crossing_hazard", key, hazard))
        for hazard in crossing.critical_hazards:
            rows.append(fact("crossing_critical", key, hazard))
    for key, tool in TOOLS.items():
        rows.append(fact("tool", key))
        for hazard, amount in tool.mitigation.items():
            rows.append(fact("tool_handle", key, hazard, amount))
    for key, weather in WEATHERS.items():
        rows.append(fact("weather", key))
        for hazard in weather.hazards:
            rows.append(fact("weather_hazard", key, hazard))
    for hazard, score in HAZARD_SCORE.items():
        rows.append(fact("hazard_score", hazard, score))
    if params is not None:
        rows.append(fact("chosen", params.crossing, params.tool, params.weather))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + "\n" + ASP_RULES + "\n"


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    symbols = solve(asp_program(), models=0)
    combos: set[tuple[str, str, str]] = set()
    for model in symbols:
        for row in atoms(model, "crossing_combo"):
            combos.add((row[0], row[1], row[2]))
    return combos


def asp_verify() -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program()), "ok"))


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_py = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. python_only={only_py} asp_only={only_asp}")
    return f"OK: ASP gate matches valid_combos() with {len(python_set)} combos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate forest bridge problem-solving stories.")
    parser.add_argument("--crossing", choices=sorted(CROSSINGS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--weather", choices=sorted(WEATHERS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES), default=None)
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


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    crossing, tool, weather = combo
    return StoryParams(
        crossing=crossing,
        tool=tool,
        weather=weather,
        hero=hero,
        gender=gender,
        seed=args.seed + index,
    )


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid crossing/tool/weather combinations are available.")
    if args.crossing or args.tool or args.weather:
        rng = random.Random(args.seed + index)
        crossing = args.crossing or rng.choice(sorted(CROSSINGS))
        tool = args.tool or rng.choice(sorted(TOOLS))
        weather = args.weather or rng.choice(sorted(WEATHERS))
        if not valid_combo(crossing, tool, weather):
            raise StoryError(invalid_reason(crossing, tool, weather))
        combo = (crossing, tool, weather)
    else:
        combo = random.Random(args.seed + index).choice(combos)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts -- asks that would produce this story ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge questions -- child level, no story needed ==")
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
    for crossing, tool, weather in sorted(asp_valid_combos()):
        print(f"{crossing}\t{tool}\t{weather}")


def main(argv: list[str] | None = None) -> int:
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
            for i, combo in enumerate(valid_combos(), 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[1]} on {combo[0]} in {combo[2]} ({sample.params.hero})")
                if i != len(valid_combos()) and not args.json:
                    print("\n" + "=" * 70 + "\n")
            return 0
        for i in range(max(1, args.n)):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if args.n > 1 and not args.json else None)
            if i != max(1, args.n) - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
