#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a dark path, bravery, and a gentle
transformation. The hero learns to navigate a sleepy place with a lantern,
turning worry into courage.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Route:
    id: str
    label: str
    start: str
    end: str
    obstacles: list[str]
    difficulty: float
    keyword: str = "navigate"


@dataclass
class Tool:
    id: str
    label: str
    helps_with: set[str]
    brightness: float


@dataclass
class StoryParams:
    route: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


ROUTES = {
    "hallway": Route(
        id="hallway",
        label="the long hallway",
        start="the bedroom door",
        end="the warm kitchen",
        obstacles=["shadows", "a creaky floorboard"],
        difficulty=1.0,
        keyword="navigate",
    ),
    "stairs": Route(
        id="stairs",
        label="the staircase",
        start="the top step",
        end="the downstairs lamp",
        obstacles=["a steep turn", "a dark landing"],
        difficulty=1.2,
        keyword="navigate",
    ),
    "garden": Route(
        id="garden",
        label="the moonlit garden path",
        start="the back door",
        end="the little gate",
        obstacles=["bushes", "twinkling dark corners"],
        difficulty=1.4,
        keyword="navigate",
    ),
}

TOOLS = {
    "nightlight": Tool(id="nightlight", label="a little night-light", helps_with={"darkness"}, brightness=1.0),
    "lantern": Tool(id="lantern", label="a small lantern", helps_with={"darkness", "shadows"}, brightness=1.4),
    "glowstone": Tool(id="glowstone", label="a glowing pebble", helps_with={"darkness", "creaks"}, brightness=0.8),
}

HERO_NAMES = ["Mina", "Luca", "Nora", "Eli", "Pippa", "Theo"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt June", "Uncle Ben"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def story_article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def reason_ok(route: Route, tool: Tool) -> bool:
    return "darkness" in tool.helps_with


def explain_rejection(route: Route, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} would not help much on {route.label}. "
        f"The bedtime path needs something that can brighten the dark.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
route(R) :- route_name(R,_).
tool(T) :- tool_name(T,_).

helps(T,darkness) :- tool_help(T,darkness).
can_navigate(R,T) :- route(R), tool(T), helps(T,darkness).
valid(R,T) :- can_navigate(R,T).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route_name", rid, r.label))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_name", tid, t.label))
        for k in sorted(t.helps_with):
            lines.append(asp.fact("tool_help", tid, k))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import storyworlds.asp as asp  # lazy import
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(r, t) for r in ROUTES for t in TOOLS if reason_ok(ROUTES[r], TOOLS[t])}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches reason_ok() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    route = ROUTES[params.route]
    tool = TOOLS[params.tool]
    world = World(place=route.label)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    lantern = world.add(Entity(id="tool", kind="thing", type=tool.id, label=tool.label, owner=helper.id))

    hero.memes["worry"] = 1.0
    hero.memes["bravery"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["gentleness"] = 1.0

    world.say(
        f"At bedtime, {hero.label} was tucked beside the window and listened to the house go quiet."
    )
    world.say(
        f"Outside {world.place}, the night waited like a soft mystery, and {hero.label} felt a tiny flutter of worry."
    )
    world.say(
        f"{helper.label} brought {lantern.label}, a warm little light that made the corners look friendlier."
    )

    world.para()
    world.say(
        f"Then it was time to {route.keyword} from {route.start} to {route.end}."
    )
    world.say(
        f"{hero.label} wanted to be brave, but {route.label} had {', '.join(route.obstacles)} hiding in the dim."
    )
    world.say(
        f"{helper.label} said, \"We can go slowly. You do not have to hurry through the dark.\""
    )

    if reason_ok(route, tool):
        hero.memes["worry"] = 0.0
        hero.memes["bravery"] = 1.0
        hero.memes["joy"] = 1.0
        world.facts["resolved"] = True
        world.facts["tool"] = tool
        world.facts["route"] = route
        world.facts["hero"] = hero
        world.facts["helper"] = helper

        world.para()
        world.say(
            f"{hero.label} held {tool.label} close, and the little light pushed the shadows back."
        )
        world.say(
            f"Step by step, {hero.label} learned to {route.keyword} with steady feet and a steady heart."
        )
        world.say(
            f"By the time they reached {route.end}, the fear had turned into bravery, and {hero.label} smiled at the glowing path."
        )
        world.say(
            f"The night still felt sleepy, but it no longer felt scary."
        )
    else:
        raise StoryError(explain_rejection(route, tool))

    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    route = world.facts["route"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Who helped {hero.label} navigate {route.label} at bedtime?",
            answer=f"{helper.label} helped {hero.label}, and {helper.label} brought {tool.label} to make the dark easier to cross."
        ),
        QAItem(
            question=f"What changed inside {hero.label} by the end of the story?",
            answer=f"{hero.label} changed from feeling worried into feeling brave. That is the story's transformation."
        ),
        QAItem(
            question=f"Why did {tool.label} matter on {route.label}?",
            answer=f"{tool.label} mattered because it gave off light. The light made the dark path feel safe enough to navigate slowly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels scared but still does the right thing or keeps going gently."
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new state, like worry changing into courage."
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, which helps people see in the dark."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    route = world.facts["route"]
    return [
        f"Write a bedtime story about {hero.label} learning to {route.keyword} through the dark.",
        f"Tell a gentle story where courage grows while a child crosses {route.label}.",
        "Write a small bedtime tale about bravery and transformation with a warm, glowing light.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa]]
    lines.append("")
    lines.append("== World questions ==")
    lines.extend([f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        if e.memes:
            lines.append(f"{e.id}: memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about navigate, bravery, and transformation.")
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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
    route = args.route or rng.choice(list(ROUTES))
    tool = args.tool or rng.choice(list(TOOLS))
    if not reason_ok(ROUTES[route], TOOLS[tool]):
        raise StoryError(explain_rejection(ROUTES[route], TOOLS[tool]))

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        route=route,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible route/tool pairs:\n")
        for route, tool in pairs:
            print(f"  {route:8}  {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(r, t) for r in ROUTES for t in TOOLS if reason_ok(ROUTES[r], TOOLS[t])]
        for i, (r, t) in enumerate(combos):
            params = StoryParams(
                route=r,
                tool=t,
                hero_name=HERO_NAMES[i % len(HERO_NAMES)],
                hero_type="girl" if i % 2 == 0 else "boy",
                helper_name=HELPER_NAMES[i % len(HELPER_NAMES)],
                helper_type="mother" if i % 2 == 0 else "father",
            )
            samples.append(generate(params))
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
            header = f"### {p.hero_name}: {p.route} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
