#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/fluff_lesson_learned_surprise_adventure.py
====================================================================================

Adventure world with a small seed tale:
"Rin and Pip climbed a windy ridge, carried a bright cloud of expedition fluff, and
found a surprise clue that changed how they crossed the dangerous way home."
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Terrain:
    key: str
    name: str
    intro: str
    risk: float
    opening_image: str
    ending_image_seed: str
    tension_note: str


@dataclass(frozen=True)
class Route:
    key: str
    name: str
    challenge: str
    difficulty: float
    danger_word: str
    surprise_hint: str


@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    help_line: str
    safety: float
    joy_gain: float
    surprise_gain: float


@dataclass
class StoryParams:
    terrain: str
    route: str
    tool: str
    hero: str
    buddy: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)  # physical state
    memes: dict[str, float] = field(default_factory=dict)  # emotional state

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def __str__(self) -> str:
        return self.name


@dataclass
class World:
    params: StoryParams
    terrain: Terrain
    route: Route
    tool: Tool
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    world_meters: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str | float | bool] = field(default_factory=dict)
    final_image: str = ""
    surprise: str = ""

    def add_entity(self, ent: Entity) -> None:
        self.entities[ent.name] = ent

    def trace(self) -> str:
        rows: list[str] = ["--- world model trace ---"]
        rows.append(f"  terrain: {self.terrain.key}")
        rows.append(f"  route: {self.route.key}")
        rows.append(f"  tool: {self.tool.key}")
        rows.append(f"  world_meters: {self.world_meters}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name} ({ent.kind}) traits={ent.traits} meters={ent.meters} memes={ent.memes}"
            )
        rows.append(f"  surprise: {self.surprise}")
        rows.append(f"  ending_image: {self.final_image}")
        if self.events:
            rows.append("  events:")
            rows.extend(f"    - {evt}" for evt in self.events)
        return "\n".join(rows)


TERRAINS = {
    "stormy_ridge": Terrain(
        key="stormy_ridge",
        name="Stormy Ridge",
        intro="a wind-carved ridge above a blue valley",
        risk=0.48,
        opening_image=(
            "Rin tied her scarf under her chin while the wind sounded like a hundred small drums against the stone."
        ),
        ending_image_seed="a wind-hardened flag snapped to a new rope line",
        tension_note="The air shook with cold gusts and every step had to match the wind's rhythm",
    ),
    "mossy_gorge": Terrain(
        key="mossy_gorge",
        name="Mossy Gorge",
        intro="a wet, winding gorge where mist slid over smooth rocks",
        risk=0.38,
        opening_image=(
            "Moss glowed dark green on the stones and the mist smelled like fresh rain."
        ),
        ending_image_seed=(
            "a fresh path-marking of moss prints and a safe new fire shelf"
        ),
        tension_note="The stones were slick and the way was tight, so one slip could send a person into the stream",
    ),
    "sunken_arch": Terrain(
        key="sunken_arch",
        name="Sunken Arch",
        intro="an old stone arch with a cool stream running beneath",
        risk=0.41,
        opening_image=(
            "The old stones breathed cool air, and tiny birds fluttered through the broken arch."
        ),
        ending_image_seed=(
            "a fresh clay marker at the arch mouth that proved the rescue path had been found"
        ),
        tension_note="The arch echoed every footstep, and loose stones made the route seem unsure",
    ),
}

ROUTES = {
    "bridge_crest": Route(
        key="bridge_crest",
        name="wobbly bridge crest",
        challenge="a narrow bridge rattled above a deep drop",
        difficulty=0.56,
        danger_word="sway",
        surprise_hint="A knot pocket hidden under the bridge planks could hold the lost marker they sought.",
    ),
    "spiral_tunnel": Route(
        key="spiral_tunnel",
        name="spiral tunnel",
        challenge="a twisting tunnel where fog moved like a living curtain",
        difficulty=0.44,
        danger_word="echo",
        surprise_hint="A bright wall carving became visible only for a blink, pointing toward a forgotten side passage.",
    ),
    "cliff_plunge": Route(
        key="cliff_plunge",
        name="cliff plunge path",
        challenge="a steep drop with a short landing shelf",
        difficulty=0.69,
        danger_word="drop",
        surprise_hint="A hidden handhold opened to a pocket of packed cloth and old expedition notes.",
    ),
}

TOOLS = {
    "fluff_parachute": Tool(
        key="fluff_parachute",
        name="fluffy cushion",
        help_line="inflate the soft cloud cushion and let it guide the descent",
        safety=0.34,
        joy_gain=0.24,
        surprise_gain=0.42,
    ),
    "grip_line": Tool(
        key="grip_line",
        name="grip line",
        help_line="secure the grip line and move in short, patient steps",
        safety=0.21,
        joy_gain=0.09,
        surprise_gain=0.17,
    ),
    "glow_lantern": Tool(
        key="glow_lantern",
        name="glow lantern",
        help_line="use the lantern beam to read the path and keep each edge visible",
        safety=0.16,
        joy_gain=0.07,
        surprise_gain=0.27,
    ),
}

ROUTE_TOOL_COMPAT = {
    "bridge_crest": ("fluff_parachute", "grip_line"),
    "spiral_tunnel": ("fluff_parachute", "glow_lantern"),
    "cliff_plunge": ("fluff_parachute", "grip_line"),
}

TERRAIN_ROUTE_COMPAT = {
    "stormy_ridge": ("bridge_crest", "cliff_plunge"),
    "mossy_gorge": ("spiral_tunnel", "cliff_plunge"),
    "sunken_arch": ("bridge_crest", "spiral_tunnel"),
}

HEROES = {
    "girl": ("Rin", "Maya", "Sia", "Nora"),
    "boy": ("Tari", "Leo", "Kai", "Owen"),
}

BUDDIES = ("Pip", "Milo", "Ari", "Nix")


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _safe_combo(terrain_key: str, route_key: str, tool_key: str) -> bool:
    if terrain_key not in TERRAINS or route_key not in ROUTES or tool_key not in TOOLS:
        return False
    return route_key in TERRAIN_ROUTE_COMPAT[terrain_key] and tool_key in ROUTE_TOOL_COMPAT[route_key]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for terrain_key in sorted(TERRAINS):
        for route_key in TERRAIN_ROUTE_COMPAT[terrain_key]:
            for tool_key in ROUTE_TOOL_COMPAT[route_key]:
                combos.append((terrain_key, route_key, tool_key))
    return combos


def invalid_reason(terrain_key: str, route_key: str, tool_key: str) -> str:
    if terrain_key not in TERRAINS:
        return f"No story: unknown terrain {terrain_key!r}."
    if route_key not in ROUTES:
        return f"No story: unknown route {route_key!r}."
    if tool_key not in TOOLS:
        return f"No story: unknown tool {tool_key!r}."
    if route_key not in TERRAIN_ROUTE_COMPAT[terrain_key]:
        return (
            f"No story: {TERRAINS[terrain_key].name} does not support {ROUTES[route_key].name}. "
            f"Try one of: {', '.join(TERRAIN_ROUTE_COMPAT[terrain_key])}."
        )
    if tool_key not in ROUTE_TOOL_COMPAT[route_key]:
        return (
            f"No story: {ROUTES[route_key].name} is not safe with {TOOLS[tool_key].name}. "
            f"Try one of: {', '.join(ROUTE_TOOL_COMPAT[route_key])}."
        )
    return "No story: invalid terrain/route/tool combination."


def _choose_gender(gender: str, rng: random.Random) -> str:
    return rng.choice(sorted(HEROES)) if gender not in HEROES else gender


def _choose_name(gender: str, choice: str | None, rng: random.Random) -> str:
    if choice:
        return choice
    return rng.choice(HEROES[gender])


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    gender = _choose_gender(args.gender or rng.choice(tuple(HEROES)), rng)
    hero = _choose_name(gender, args.hero, rng)
    buddy = args.buddy or rng.choice(BUDDIES)
    terrain_key, route_key, tool_key = combo
    return StoryParams(
        terrain=terrain_key,
        route=route_key,
        tool=tool_key,
        hero=hero,
        buddy=buddy,
        seed=(args.seed or 1) + index,
    )


def build_world(params: StoryParams) -> World:
    world = World(
        params=params,
        terrain=TERRAINS[params.terrain],
        route=ROUTES[params.route],
        tool=TOOLS[params.tool],
    )

    hero = Entity(
        name=params.hero,
        kind="girl" if params.hero not in ("Tari", "Leo", "Kai", "Owen") else "boy",
        traits=["curious", "careful"],
        meters={"stamina": 1.2, "focus": 0.75, "alertness": 0.62},
        memes={"joy": 0.48, "caution": 0.52, "courage": 0.37, "trust": 0.44},
    )
    buddy = Entity(
        name=params.buddy,
        kind="friend",
        traits=["steady", "helpful"],
        meters={"stamina": 1.0, "focus": 0.68, "alertness": 0.63},
        memes={"joy": 0.4, "trust": 0.49, "caution": 0.46, "curiosity": 0.5},
    )
    fluff = Entity(
        name="Puffed Fluff Bundle",
        kind="object",
        traits=["soft", "light"],
        meters={"integrity": 1.0, "bulk": 0.76, "inflated": 0.22},
        memes={"surprise": 0.1},
    )

    world.add_entity(hero)
    world.add_entity(buddy)
    world.add_entity(fluff)

    world.facts["terrain"] = world.terrain.name
    world.facts["route"] = world.route.name
    world.facts["tool"] = world.tool.name
    world.facts["hero"] = hero.name
    world.facts["buddy"] = buddy.name
    return world


def simulate(world: World) -> None:
    hero = world.entities[world.params.hero]
    buddy = world.entities[world.params.buddy]
    fluff = world.entities["Puffed Fluff Bundle"]

    route = world.route
    terrain = world.terrain
    tool = world.tool

    base_pressure = terrain.risk + route.difficulty
    risk_after_tool = max(0.05, base_pressure - tool.safety)

    # Physical pressure changes
    world.world_meters["route_pressure"] = round(risk_after_tool, 2)
    hero.meters["focus"] = _clamp(hero.meters["focus"] - route.difficulty * 0.11 + (tool.safety * 0.2))
    buddy.meters["focus"] = _clamp(buddy.meters["focus"] - route.difficulty * 0.07 + (tool.safety * 0.13))

    # Emotional progression driven by simulation
    hero.memes["caution"] = _clamp(hero.memes["caution"] + terrain.risk * 0.22 + route.difficulty * 0.3)
    hero.memes["courage"] = _clamp(hero.memes["courage"] + (1 - risk_after_tool) * 0.55 + tool.joy_gain)
    hero.memes["trust"] = _clamp(hero.memes["trust"] + 0.18)

    buddy.memes["curiosity"] = _clamp(buddy.memes["curiosity"] + 0.14 + route.difficulty * 0.2)
    buddy.memes["trust"] = _clamp(buddy.memes["trust"] + 0.16 + tool.joy_gain)

    fluff.meters["inflated"] = _clamp(fluff.meters["inflated"] + tool.surprise_gain)
    fluff.meters["integrity"] = _clamp(fluff.meters["integrity"] - route.difficulty * 0.14)

    world.world_meters["teaming"] = _clamp((hero.memes["trust"] + buddy.memes["trust"]) / 2)
    world.world_meters["lesson_readiness"] = _clamp(
        0.24 + (hero.memes["courage"] * 0.45) + (world.world_meters["teaming"] * 0.35)
    )

    if tool.key == "fluff_parachute":
        world.surprise = (
            f"When {hero.name} pressed the {tool.name}, a hidden pocket in the trail wall opened,"
            f" and inside it sat a folded cloth map and an old trail bell wrapped in white fluff."
        )
        fluff.meters["bulk"] = _clamp(fluff.meters["bulk"] - 0.28)
    elif tool.key == "grip_line":
        world.surprise = (
            f"{buddy.name} tested the line, then a stone slab shifted open beside the {route.key.replace('_', ' ')},"
            f" revealing a cache with a dry marker stone and an extra signal ribbon."
        )
    else:
        world.surprise = (
            f"The lantern beam caught a carved line in the fog wall. {route.surprise_hint} "
            f"The bright mark matched a hidden passage on their map."
        )

    world.events.append(
        f"route_pressure={world.world_meters['route_pressure']}, teaming={world.world_meters['teaming']:.2f}, lesson_ready={world.world_meters['lesson_readiness']:.2f}"
    )

    if risk_after_tool > 0.9:
        world.events.append("cliff_edge_recovery")

    # Final physical outcome and ending image are still state-driven.
    hero.meters["stamina"] = _clamp(hero.meters["stamina"] - 0.12)
    buddy.meters["stamina"] = _clamp(buddy.meters["stamina"] - 0.09)
    hero.memes["joy"] = _clamp(hero.memes["joy"] + 0.17)
    buddy.memes["joy"] = _clamp(buddy.memes["joy"] + 0.14)

    world.facts["route_pressure"] = world.world_meters["route_pressure"]
    world.facts["lesson_readiness"] = world.world_meters["lesson_readiness"]
    world.facts["surprise"] = route.surprise_hint

    if world.world_meters["lesson_readiness"] >= 0.75:
        world.facts["lesson"] = "small signs and patient teamwork can be stronger than rushing for speed"
    elif world.world_meters["route_pressure"] >= 0.9:
        world.facts["lesson"] = "careful planning matters most when the way looks exciting"
    else:
        world.facts["lesson"] = "watching the path change itself teaches better choices than guessing"

    ending_fragment = (
        f"the team had tied {terrain.ending_image_seed}, "
        f"and the {world.params.terrain.replace('_', ' ')} held a clear new marker line."
    )
    world.final_image = ending_fragment


def _render_prompts(world: World) -> list[str]:
    return [
        'Write an adventure where a child uses careful planning to cross a risky route. Include the word "fluff".',
        f"Tell a story where {world.entities[world.params.hero].name} uses a {world.tool.name} on a {world.route.name}.",
        "Show a clear surprise turn and a lesson learned from what changes in the world.",
    ]


def _render_story(world: World) -> str:
    hero = world.entities[world.params.hero]
    buddy = world.entities[world.params.buddy]

    opening = (
        f"On a bright-but-restless morning, {hero.name} and {buddy.name} reached {world.terrain.intro}. "
        f"{world.terrain.opening_image} "
        f"They were carrying a soft bundle of route-safe fluff for emergencies."
    )

    tension = (
        f"The way ahead was dangerous: {world.terrain.tension_note}. "
        f"Ahead, {world.route.challenge} waited, and the air itself seemed to tense with the sound of a distant {world.route.danger_word}."
    )

    action = (
        f"{hero.name} checked the map, then used the {world.tool.name}. "
        f"{buddy.name} matched every move: {world.tool.help_line}. "
        f"The {world.terrain.key.replace('_', ' ')} responded slowly as their feet and breaths moved together."
    )

    middle = (
        f"When the pressure got high, that route and tool choice kept them steady. "
        f"{world.surprise} "
        f"For a moment they could only stand still, listening to the wind, then smiled when the path revealed a better line."
    )

    if world.world_meters["route_pressure"] > 0.9:
        turn = (
            f"They almost slipped into a dangerous step, but {buddy.name} grabbed {hero.pronoun('object')} glove strap, "
            f"and {hero.name} shifted weight backward using the lesson of patient distance."
        )
    else:
        turn = (
            f"They crossed with breathless care, and the team found a tucked-away side ledge before the path narrowed to a final edge."
        )

    lesson = (
        f"By the end, {hero.name} learned a lesson: {world.facts['lesson']}. "
        f"The fluff bundle had started as comfort, but it became the anchor for the right, thoughtful choice."
    )

    ending = (
        f"In the evening, {world.final_image}. "
        f"The ending image was a bright marker on stone, proving they had changed the place by leaving a safer path for the next travelers."
    )

    return "\n\n".join([opening, tension, action, middle, turn, lesson, ending])


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities[world.params.hero]
    buddy = world.entities[world.params.buddy]

    return [
        QAItem(
            f"Who is in this adventure and what are they trying to do?",
            (
                f"{hero.name} and {buddy.name} are the two children exploring the {world.terrain.name}. "
                f"They used {world.params.route.replace('_', ' ')} to cross safely because the weather and terrain were risky."
            ),
        ),
        QAItem(
            f"What role did the {world.tool.name} play in the middle of the story?",
            (
                f"The tool reduced the route pressure by giving them a safer method at the hard point. "
                f"In world terms, its safety value of {world.tool.safety:.2f} lowered their risk from a rough crossing toward a controlled one, "
                f"which is why they could move with fewer rushed mistakes."
            ),
        ),
        QAItem(
            "What was the surprise in the story and what changed because of it?",
            (
                f"The surprise came when the route itself revealed a hidden cache tied to the path. "
                f"That discovery gave the team a new marker and confirmed the safest way forward, turning a tense route into a clear finished passage."
            ),
        ),
        QAItem(
            "How did teamwork affect the outcome?",
            (
                f"The team pressure meter rose above 0.5 because the two worked as a unit, with each step checked by both children. "
                f"That shared caution let them recover even when conditions became sharper, and it showed that trust can replace panic."
            ),
        ),
        QAItem(
            "What did the child learn by the end?",
            (
                f"The lesson was that careful planning, patient communication, and using the right physical method can keep an adventure exciting without becoming dangerous. "
                f"By leaving the marker at the end, the children also made the world safer for later travelers, not only for themselves."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    tool = world.tool
    route = world.route
    terrain = world.terrain
    return [
        QAItem(
            "Why did the validation rules disallow some route and tool pairings?",
            (
                f"Each route has a physical requirement in the registry: a bridge or cliff-crossing needs support for the kind of pull and drag involved. "
                f"The {tool.name} has a specific safety value, and pairing it with an unsupported route would leave the world model in an unsafe state."
            ),
        ),
        QAItem(
            "Why was a physical ending image required in this world?",
            (
                f"The world tracks a visible marker result in `ending_image`. "
                f"The ending is considered complete only when the narrative shows a changed physical scene on {terrain.name}, "
                f"because that proves the lesson was tested in the environment, not just said in words."
            ),
        ),
        QAItem(
            "What state variable can show whether the lesson is likely to be retained?",
            (
                f"The variable `lesson_readiness` is computed from courage and teamwork meters at the end. "
                f"A higher value means both emotional readiness and social support were high, so the character is more likely to reuse the lesson later."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not _safe_combo(params.terrain, params.route, params.tool):
        raise StoryError(invalid_reason(params.terrain, params.route, params.tool))

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
terrain(stormy_ridge; mossy_gorge; sunken_arch).
route(bridge_crest; spiral_tunnel; cliff_plunge).
tool(fluff_parachute; grip_line; glow_lantern).

supports(stormy_ridge, bridge_crest).
supports(stormy_ridge, cliff_plunge).
supports(mossy_gorge, spiral_tunnel).
supports(mossy_gorge, cliff_plunge).
supports(sunken_arch, bridge_crest).
supports(sunken_arch, spiral_tunnel).

works(bridge_crest, fluff_parachute).
works(bridge_crest, grip_line).
works(spiral_tunnel, fluff_parachute).
works(spiral_tunnel, glow_lantern).
works(cliff_plunge, fluff_parachute).
works(cliff_plunge, grip_line).

combo(T, R, K) :- terrain(T), route(R), tool(K), supports(T,R), works(R,K).
ready :- chosen(T,R,K), combo(T,R,K).

#show combo/3.
#show ready/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for terrain in TERRAINS:
        rows.append(fact("terrain", terrain))
        for route in TERRAIN_ROUTE_COMPAT[terrain]:
            rows.append(fact("supports", terrain, route))
    for route in ROUTES:
        rows.append(fact("route", route))
        for tool in ROUTE_TOOL_COMPAT[route]:
            rows.append(fact("works", route, tool))
    for tool in TOOLS:
        rows.append(fact("tool", tool))

    if params is not None:
        rows.append(fact("chosen", params.terrain, params.route, params.tool))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ready"))


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for t, r, k in atoms(model, "combo"):
            combos.add((t, r, k))
    return combos


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")

    for i, combo in enumerate(sorted(py), 1):
        sample = generate(_params_from_combo(type("Args", (), {
            "seed": 1,
            "gender": None,
            "hero": None,
            "buddy": "Pip",
        })(), combo, i))
        if not sample.world or sample.story.count("fluff") < 1:
            raise StoryError(f"Generated story for combo {combo} missing the seed word fluff")
        if sample.world is None or not sample.world.final_image:
            raise StoryError(f"Generated story for combo {combo} did not produce an ending image")
    return f"OK: ASP and Python agree on {len(py)} combinations and generated samples render successfully."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an adventure with surprise and a lesson learned from a physical clue and stateful choices."
    )
    parser.add_argument("--terrain", choices=sorted(TERRAINS))
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--buddy", default=None)
    parser.add_argument("--gender", choices=sorted(HEROES))
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
    rng = random.Random((args.seed or 1) + index)
    options = valid_combos()

    if args.terrain or args.route or args.tool:
        options = [
            (terrain, route, tool)
            for terrain, route, tool in options
            if (args.terrain is None or terrain == args.terrain)
            and (args.route is None or route == args.route)
            and (args.tool is None or tool == args.tool)
        ]
        if not options:
            raise StoryError(invalid_reason(
                args.terrain or "<terrain>",
                args.route or "<route>",
                args.tool or "<tool>",
            ))

    if not options:
        raise StoryError("No valid combination matches the selected options.")

    terrain_key, route_key, tool_key = rng.choice(options)
    return _params_from_combo(args, (terrain_key, route_key, tool_key), index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        print(f"Q: {item.question}")
        print(f"A: {item.answer}")
    print("\n== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        print(f"Q: {item.question}")
        print(f"A: {item.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, json_out: bool = False) -> None:
    if json_out:
        print(sample.to_json())
        return

    print(sample.story)
    if qa:
        _print_qa(sample)
    if trace:
        if sample.world is not None:
            print(sample.world.trace())


def _emit_asp_listing() -> None:
    for terrain, route, tool in sorted(valid_combos()):
        print(f"{terrain}\t{route}\t{tool}")


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
                emit(sample, trace=args.trace, qa=args.qa, json_out=args.json)
                if not args.json and i != len(combos):
                    print("\n" + "=" * 72 + "\n")
            return 0

        for i in range(max(1, args.n)):
            sample = generate(resolve_params(args, i))
            if args.qa or args.trace:
                emit(sample, trace=args.trace, qa=args.qa, json_out=False)
            elif args.json:
                emit(sample, json_out=True)
            else:
                emit(sample)
            if i != max(1, args.n) - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
