#!/usr/bin/env python3
"""
A small adventure storyworld about steering through a smudge, with brave
inner thoughts guiding a careful repair.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    vehicle: str
    route: str
    tool: str
    seed: Optional[int] = None
    obstacle: Optional[str] = None
    courage: Optional[str] = None


@dataclass(frozen=True)
class Route:
    key: str
    place: str
    opening: str
    obstacle: str
    clue: str
    ending: str


@dataclass(frozen=True)
class CouragePath:
    key: str
    thought: str
    action: str
    lesson: str


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip", "Zara"]
HELPERS = ["a careful fox", "a cheerful badger", "an old owl", "a curious rabbit"]
VEHICLES = ["a red canoe", "a little airship", "a moon buggy", "a wooden cart"]
TOOLS = ["a soft brush", "a clean cloth", "a tiny compass", "a silver spoon"]
ROUTES = [
    Route(
        "misty_river",
        "the Misty River",
        "{name} pushed the red canoe from the reeds and steered toward the far bank.",
        "A gray smudge covered the only painted arrow on a river stone.",
        "Under the smudge, a tiny blue line still pointed toward a willow branch.",
        "The canoe slipped beneath the willow, where fireflies lit the safe landing."
    ),
    Route(
        "cloud_pass",
        "Cloud Pass",
        "{name} climbed into the little airship and steered above a valley of white clouds.",
        "A soot-black smudge blurred the compass mark on the wind map.",
        "The clean edge of the map showed three small stars beside the north wind.",
        "The airship sailed between two silver peaks and landed on a sunlit cloud."
    ),
    Route(
        "cinder_trail",
        "Cinder Trail",
        "{name} rattled along the Cinder Trail in the moon buggy, following lanterns between the rocks.",
        "A muddy smudge hid the bridge symbol on the route card.",
        "A line of warm pebbles curved toward a narrow stone bridge.",
        "The moon buggy crossed safely and found a bright camp beyond the dark rocks."
    ),
    Route(
        "garden_maze",
        "the Giant Garden Maze",
        "{name} took the wooden cart into the Giant Garden Maze and steered past ferns taller than umbrellas.",
        "A green smudge covered the turn mark on a leaf-shaped sign.",
        "A trail of nibbled clover led toward the quiet fountain.",
        "The cart rolled out beside the fountain, where the maze bells chimed."
    ),
]
COURAGE = [
    CouragePath(
        "steady_breath",
        "I feel afraid, but I can take one steady breath and look closely.",
        "{name} breathed slowly, examined the smudge, and used {tool} without rubbing away the remaining clue.",
        "bravery can begin with a calm breath"
    ),
    CouragePath(
        "ask_help",
        "I do not have to solve every mystery alone.",
        "{name} asked {helper} to hold the map while {name} cleaned one small corner with {tool}.",
        "asking for help is a brave choice"
    ),
    CouragePath(
        "small_step",
        "The whole journey is huge, but the next safe step can be small.",
        "{name} tested the route with one careful turn, then steered onward when the ground stayed firm.",
        "bravery grows through careful small steps"
    ),
    CouragePath(
        "truthful_worry",
        "If I pretend I am not worried, I might miss something important.",
        "{name} told {helper} about the worry, and together they checked the smudge before moving.",
        "speaking honestly can protect an adventure"
    ),
]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def choose(items, key: str):
    for item in items:
        if item.key == key:
            return item
    raise StoryError(f"Unknown story choice: {key}")


def complete_params(params: StoryParams) -> None:
    if params.route not in {r.key for r in ROUTES}:
        raise StoryError(f"Unknown route: {params.route}")
    if params.courage and params.courage not in {c.key for c in COURAGE}:
        raise StoryError(f"Unknown courage path: {params.courage}")
    if params.obstacle and params.obstacle != "smudge":
        raise StoryError("This adventure's obstacle must be a smudge.")
    if params.seed is None:
        params.seed = sum(ord(ch) for ch in params.name + params.route)
    rng = random.Random(params.seed ^ 91827)
    params.obstacle = params.obstacle or "smudge"
    params.courage = params.courage or rng.choice(COURAGE).key


def build_world(params: StoryParams) -> World:
    complete_params(params)
    route = choose(ROUTES, params.route)
    courage = choose(COURAGE, params.courage)
    world = World()
    child = world.add(Entity(
        "traveler", "character", params.name,
        meters={"bravery": 0.0, "worry": 0.0, "care": 0.0},
        memes={"curiosity": 1.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        "helper", "character", params.helper,
        meters={"helpfulness": 1.0},
        memes={"companionship": 1.0},
    ))
    vehicle = world.add(Entity(
        "vehicle", "vehicle", params.vehicle,
        meters={"stability": 1.0},
        memes={"adventure": 1.0},
    ))
    world.facts.update(
        child=child,
        helper=helper,
        vehicle=vehicle,
        route=route,
        courage=courage,
        params=params,
    )
    return world


def words(world: World) -> dict[str, str]:
    p = world.facts["params"]
    return {
        "name": p.name,
        "helper": p.helper,
        "vehicle": p.vehicle,
        "tool": p.tool,
    }


def begin(world: World) -> None:
    route = world.facts["route"]
    world.facts["child"].meters["bravery"] += 1
    world.say(route.opening.format_map(words(world)))
    world.say(
        f'"Keep your eyes open," said {world.facts["helper"].label}. '
        f'"Every adventure leaves a clue."'
    )


def meet_smudge(world: World) -> None:
    child = world.facts["child"]
    route = world.facts["route"]
    child.meters["worry"] += 2
    world.say(route.obstacle)
    world.say(
        f'"The way forward is hidden," said {child.label}. '
        f'"Then we will look for what is still visible," replied {world.facts["helper"].label}.'
    )


def inner_monologue(world: World) -> None:
    child = world.facts["child"]
    courage = world.facts["courage"]
    child.meters["bravery"] += 1
    child.memes["trust"] += 1
    world.say(f"Inside, {child.label} thought, “{courage.thought}”")
    world.say(courage.action.format_map(words(world)))
    world.say(world.facts["route"].clue)


def steer_forward(world: World) -> None:
    child = world.facts["child"]
    child.meters["worry"] -= 1
    child.meters["bravery"] += 2
    world.say(
        f"{child.label} placed both hands on the guide bar and steered carefully. "
        f"The {world.facts['vehicle'].label} followed the clue instead of guessing."
    )
    world.say(
        f'"A little left," called {world.facts["helper"].label}. '
        f'"I see it!" said {child.label}, making the turn.'
    )


def resolve(world: World) -> None:
    child = world.facts["child"]
    route = world.facts["route"]
    courage = world.facts["courage"]
    child.meters["care"] += 2
    child.memes["curiosity"] += 1
    world.say(route.ending)
    world.say(
        f"The smudge was still on the map, but it no longer felt like a wall. "
        f"{child.label} had learned that {courage.lesson}."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    begin(world)
    world.para()
    meet_smudge(world)
    inner_monologue(world)
    world.para()
    steer_forward(world)
    resolve(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    route = world.facts["route"]
    courage = world.facts["courage"]
    return [
        QAItem(
            f"Where did {p.name} steer the {p.vehicle}, and what smudge caused trouble?",
            f"{p.name} steered the {p.vehicle} through {route.place}, where a smudge hid an important route mark."
        ),
        QAItem(
            f"What did {p.name}'s inner monologue help {p.name} decide?",
            f"It helped {p.name} choose courage by remembering that {courage.lesson}."
        ),
        QAItem(
            f"How did {p.name} solve the smudge problem?",
            f"{p.name} looked closely, used {p.tool}, followed the remaining clue, and steered carefully with help from {p.helper}."
        ),
        QAItem(
            f"What changed by the end of the adventure?",
            f"{p.name} became braver and reached safety without guessing past the hidden clue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to steer?",
            "To steer means to guide a vehicle in the direction you want it to go."
        ),
        QAItem(
            "What is a smudge?",
            "A smudge is a blurry or dirty mark made when something rubs against a surface."
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the quiet stream of thoughts a character has inside their mind."
        ),
        QAItem(
            "What is bravery?",
            "Bravery means doing something careful and worthwhile even when you feel afraid."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write an adventure about {p.name} steering a {p.vehicle} through {world.facts['route'].place}.",
        f"Include a smudge that hides a route clue and an inner monologue about bravery.",
        f"End with a concrete safe landing and show how {p.helper} changes what {p.name} does.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("event", "adventure"),
        asp.fact("action", "steer"),
        asp.fact("obstacle", "smudge"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "bravery"),
        asp.fact("style", "adventure"),
    ])


ASP_RULES = r"""
compatible_story(adventure, steer, smudge, inner_monologue, bravery) :-
    event(adventure), action(steer), obstacle(smudge),
    feature(inner_monologue), feature(bravery), style(adventure).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    ok = bool(asp.atoms(model, "compatible_story"))
    if not ok:
        print("MISMATCH: ASP gate failed.")
        return 1
    for params in CURATED:
        sample = generate(StoryParams(**params.__dict__))
        if not sample.story or "smudge" not in sample.story.lower():
            print("MISMATCH: generated story failed.")
            return 1
    print("OK: ASP and Python story gates agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An adventure about steering through a smudge.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--route", choices=[r.key for r in ROUTES])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--obstacle", choices=["smudge"])
    ap.add_argument("--courage", choices=[c.key for c in COURAGE])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        vehicle=args.vehicle or rng.choice(VEHICLES),
        route=args.route or rng.choice(ROUTES).key,
        tool=args.tool or rng.choice(TOOLS),
        obstacle=args.obstacle,
        courage=args.courage,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if trace and sample.world:
        print("--- trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.label}: meters={entity.meters} memes={entity.memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "a careful fox", "a red canoe", "misty_river", "a soft brush"),
    StoryParams("Milo", "an old owl", "a little airship", "cloud_pass", "a tiny compass"),
    StoryParams("Nia", "a curious rabbit", "a moon buggy", "cinder_trail", "a clean cloth"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/5."))
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(**p.__dict__)) for p in CURATED]
    else:
        samples = []
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
