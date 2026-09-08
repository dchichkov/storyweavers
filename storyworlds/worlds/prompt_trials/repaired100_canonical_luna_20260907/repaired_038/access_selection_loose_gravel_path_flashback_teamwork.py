#!/usr/bin/env python3
"""
A small superhero storyworld about choosing safe access on a loose gravel path.

The hero remembers a past rescue, works with a teammate, and repeats a careful
selection routine before reaching a stranded kite.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AccessRoute:
    id: str
    label: str
    surface: str
    safe: bool
    reason: str


@dataclass(frozen=True)
class RescueTool:
    id: str
    label: str
    purpose: str


@dataclass(frozen=True)
class Scenario:
    id: str
    object_name: str
    danger: str
    clue: str
    result: str
    ending: str


@dataclass
class StoryParams:
    hero: str
    teammate: str
    route: str
    tool: str
    scenario: str
    flashback: int
    repetition: int
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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


HEROES = ["Luna", "Milo", "Nova", "Tess", "Ravi"]
TEAMMATES = ["Pip", "Jade", "Oren", "Bea", "Kai"]

ROUTES = {
    "rope_edge": AccessRoute(
        "rope_edge",
        "the rope-marked edge",
        "firm grass beside the stones",
        True,
        "the rope-marked edge keeps feet off the shifting gravel",
    ),
    "gravel_center": AccessRoute(
        "gravel_center",
        "the middle of the path",
        "loose gravel",
        False,
        "the middle stones roll under hurried feet",
    ),
    "drain_side": AccessRoute(
        "drain_side",
        "the shallow drain side",
        "a narrow muddy channel",
        False,
        "the drain side is slippery and too narrow for a rescue",
    ),
}

TOOLS = {
    "hook": RescueTool("hook", "the rescue hook", "reach the kite without stepping onto the loose stones"),
    "rope": RescueTool("rope", "the bright safety rope", "give the teammate a steady line to hold"),
    "board": RescueTool("board", "a flat rescue board", "spread weight across a short safe crossing"),
}

SCENARIOS = {
    "kite": Scenario(
        "kite",
        "red kite",
        "The kite's string is caught around a low branch beyond the loose gravel path.",
        "The grass beside the rope is firm, while the center stones slide when touched.",
        "Luna and Pip freed the red kite without stepping into the unstable middle of the path.",
        "The red kite climbed above the path, its tail brushing the bright safety rope.",
    ),
    "map": Scenario(
        "map",
        "silver map",
        "A silver map has blown to a marker beside the loose gravel path.",
        "The map flutters toward the rolling stones whenever the wind pushes from the hill.",
        "The team pinned the map with a rescue board and carried it back along the firm edge.",
        "The silver map opened on a flat patch of grass and showed a safe route home.",
    ),
    "bell": Scenario(
        "bell",
        "lost bell",
        "A tiny bell lies just beyond the loose gravel path, ringing whenever a stone shifts.",
        "The ringing stops when the grass edge is shaded from the wind.",
        "The team used the hook from the firm edge and lifted the bell without disturbing the stones.",
        "The bell chimed safely from Luna's pack as the path grew quiet.",
    ),
}

FLASHBACKS = [
    "Luna remembered a rescue from last summer, when a rushing hero had slipped on wet stones and needed a teammate's rope.",
    "A memory flashed through Luna's mind: once, a shortcut had turned a simple rescue into a tumble, and careful access had saved the day.",
    "Luna recalled her first superhero lesson, when Captain Sol said, “The safest route is part of the rescue.”",
    "For a moment, Luna remembered standing beside a fallen bridge and learning to test every step before trusting it.",
]

REPETITIONS = [
    "Together they repeated the check: stop, point, test, and choose.",
    "They said the routine three times: “Stop. Point. Test. Choose.”",
    "Again and again, they practiced the same order: stop, point, test, choose.",
    "They repeated the plan until both heroes could say it without rushing: “Stop, point, test, choose.”",
]


def _meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _meme(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def tell(params: StoryParams) -> World:
    route = ROUTES[params.route]
    tool = TOOLS[params.tool]
    scenario = SCENARIOS[params.scenario]
    flashback = FLASHBACKS[params.flashback % len(FLASHBACKS)]
    repetition = REPETITIONS[params.repetition % len(REPETITIONS)]

    world = World()
    hero = world.add(Entity(params.hero, "hero", params.hero))
    teammate = world.add(Entity(params.teammate, "hero", params.teammate))
    path = world.add(Entity("path", "place", "loose gravel path"))
    object_entity = world.add(Entity("rescue_object", "object", scenario.object_name))

    world.facts.update(
        hero=hero,
        teammate=teammate,
        route=route,
        tool=tool,
        scenario=scenario,
        path=path,
        object=object_entity,
        flashback=flashback,
        repetition=repetition,
    )

    world.say(
        f"At sunrise, {params.hero}, a young superhero, and {params.teammate}, "
        f"their teammate, reached a loose gravel path during patrol."
    )
    world.say(
        f"Just beyond the path, {scenario.object_name} needed help. {scenario.danger}"
    )
    _meter(path, "instability", 1.0)
    _meme(hero, "worry", 0.5)
    world.para()

    world.say(f"{params.hero} took one step toward the middle, but {params.teammate} called, “Wait!”")
    world.say(
        f"“We need safe access before a brave rescue,” said {params.teammate}. "
        f"{route.reason.capitalize()}."
    )
    world.say(flashback)
    _meme(hero, "memory", 1.0)

    world.say(
        f"{params.hero} looked at {route.label}, then at the tempting shortcut. "
        f"“Which access route should we select?” {params.hero} asked."
    )
    world.say(
        f"“Select the route that keeps us steady,” said {params.teammate}. "
        f"“Then we can use {tool.label} to {tool.purpose}.”"
    )
    world.say(repetition)
    _meme(hero, "caution", 1.0)
    _meme(teammate, "trust", 1.0)

    world.say(
        f"They selected {route.label}. {scenario.clue} "
        f"{params.hero} held the {tool.label}, while {params.teammate} watched the path."
    )
    world.say(
        f"“I will move only when you say the ground is ready,” said {params.hero}. "
        f"“And I will keep checking,” replied {params.teammate}."
    )
    world.say(
        f"Together they repeated the check: stop, point, test, and choose. "
        f"The rescue stayed slow even when the wind tugged at the {scenario.object_name}."
    )
    _meter(path, "instability", 0.0)
    _meter(object_entity, "secured", 1.0)
    _meme(hero, "confidence", 1.0)
    _meme(teammate, "confidence", 1.0)

    world.say(scenario.result)
    world.say(
        f"{params.teammate} smiled. “Your memory helped us choose access wisely.” "
        f"{params.hero} answered, “Our teamwork made the choice strong.”"
    )
    world.say(scenario.ending)
    world.say(
        "The heroes headed home, repeating their rescue rule together: "
        "“Stop, point, test, choose—and help each other.”"
    )
    world.facts["resolved"] = True
    world.facts["selection"] = route.id
    world.facts["teamwork"] = True
    world.facts["flashback"] = True
    world.facts["repetition"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [
        (route.id, tool.id)
        for route in ROUTES.values()
        if route.safe
        for tool in TOOLS.values()
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    routes = [r for r in ROUTES.values() if args.route is None or r.id == args.route]
    if not routes:
        raise StoryError("No known access route matches the request.")
    if args.route and not ROUTES[args.route].safe:
        raise StoryError(
            f"The selected access route, {ROUTES[args.route].label}, is unsafe because "
            f"{ROUTES[args.route].reason}."
        )
    tools = [t for t in TOOLS.values() if args.tool is None or t.id == args.tool]
    if not tools:
        raise StoryError("No known rescue tool matches the request.")
    route = rng.choice(routes)
    tool = rng.choice(tools)
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        teammate=args.teammate or rng.choice(TEAMMATES),
        route=route.id,
        tool=tool.id,
        scenario=args.scenario or rng.choice(sorted(SCENARIOS)),
        flashback=rng.randrange(len(FLASHBACKS)),
        repetition=rng.randrange(len(REPETITIONS)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    route: AccessRoute = f["route"]
    return [
        f"Write a superhero story about access and selection on a loose gravel path involving a {scenario.object_name}.",
        f"Tell a Flashback, Teamwork, and Repetition story in which {f['hero'].id} selects {route.label} for a safe rescue.",
        "Write a child-friendly superhero rescue where a remembered mistake changes a careful decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    route: AccessRoute = f["route"]
    tool: RescueTool = f["tool"]
    return [
        QAItem(
            question=f"Where did {f['hero'].id} and {f['teammate'].id} find the {scenario.object_name}?",
            answer=f"They found the {scenario.object_name} beside a loose gravel path, where the shifting stones made a hurried approach unsafe.",
        ),
        QAItem(
            question="What did the flashback teach the hero?",
            answer=f"The flashback reminded {f['hero'].id} that a shortcut over unstable ground can cause a fall, so safe access must be selected before the rescue begins.",
        ),
        QAItem(
            question=f"Which access route did the team select?",
            answer=f"They selected {route.label} because {route.reason}.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{f['hero'].id} handled the rescue tool while {f['teammate'].id} watched the ground and gave clear instructions, so neither hero had to rush alone.",
        ),
        QAItem(
            question="What did the heroes repeat?",
            answer="They repeated the routine, “Stop, point, test, choose,” so their selection stayed careful even when the wind and danger made them eager to act.",
        ),
        QAItem(
            question=f"How did they use {tool.label}?",
            answer=f"They used {tool.label} to {tool.purpose}, keeping their feet on the selected safe access route.",
        ),
        QAItem(
            question="What showed that the rescue was complete?",
            answer=f"{scenario.result} {scenario.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can loose gravel be difficult to cross?",
            answer="Loose gravel can shift beneath a person's feet, so a careful traveler should slow down, test the surface, and choose a stable route.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share information, tasks, and support so they can solve a problem more safely and effectively together.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene or memory that returns to an earlier event and helps explain a character's present choice.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"facts={sorted(k for k, v in world.facts.items() if isinstance(v, (bool, str)) and v)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_route(R) :- route(R), safe(R).
valid_rescue(R,T) :- safe_route(R), tool(T), supports(T,R), flashback_theme, teamwork_theme, repetition_theme.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("flashback_theme"),
        asp.fact("teamwork_theme"),
        asp.fact("repetition_theme"),
    ]
    for route in ROUTES.values():
        lines.append(asp.fact("route", route.id))
        if route.safe:
            lines.append(asp.fact("safe", route.id))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for route in ROUTES.values():
            if route.safe:
                lines.append(asp.fact("supports", tool.id, route.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_rescue/2."))
    return sorted(set(asp.atoms(model, "valid_rescue")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs != asp_pairs:
        print("MISMATCH between Python and ASP:")
        print("only in Python:", sorted(python_pairs - asp_pairs))
        print("only in ASP:", sorted(asp_pairs - python_pairs))
        return 1
    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or not sample.story_qa or not sample.world.facts.get("resolved"):
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(python_pairs)} valid rescues; generated stories pass.")
    return 0


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about selecting safe access on a loose gravel path."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--teammate", choices=TEAMMATES)
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--scenario", choices=SCENARIOS)
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


CURATED = [
    StoryParams("Luna", "Pip", "rope_edge", "hook", "kite", 0, 0),
    StoryParams("Nova", "Jade", "rope_edge", "rope", "map", 1, 1),
    StoryParams("Milo", "Bea", "rope_edge", "board", "bell", 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_rescue/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_rescue/2."))
        print(sorted(set(asp.atoms(model, "valid_rescue"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
