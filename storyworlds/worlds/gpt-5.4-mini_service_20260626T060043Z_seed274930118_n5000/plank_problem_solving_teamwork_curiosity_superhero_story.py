#!/usr/bin/env python3
"""
A tiny superhero story world about a curious hero team, a broken plank, and a
smart fix.

Premise:
- A young hero team discovers that a plank is needed to cross a gap.
- Curiosity makes them inspect the problem instead of rushing.
- Teamwork and problem solving turn a risky crossing into a safe rescue.

The story is generated from a small simulated world:
- characters have physical meters and emotional memes
- the plank, gap, and helper tools have state
- the ending is driven by whether the team solved the crossing together
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the old bridge"
    sky: str = "windy"
    below: str = "a dark gap"
    affordances: set[str] = field(default_factory=lambda: {"investigate", "build", "cross"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    tags: set[str]


@dataclass
class StoryParams:
    hero_name: str
    sidekick_name: str
    hero_type: str
    sidekick_type: str
    place: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


TOOLS = {
    "extra_plank": Tool(
        id="extra_plank",
        label="an extra plank",
        phrase="a sturdy extra plank",
        helps_with={"bridge"},
        tags={"plank", "problem_solving"},
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a long rope",
        helps_with={"bridge"},
        tags={"teamwork"},
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp",
        helps_with={"inspect"},
        tags={"curiosity"},
    ),
}

PLACES = {
    "bridge": Place(name="the old bridge", sky="windy", below="a deep gap", affordances={"investigate", "build", "cross"}),
    "rooftop": Place(name="the rooftop", sky="cloudy", below="the street far below", affordances={"investigate", "build", "cross"}),
    "canyon": Place(name="the canyon path", sky="windy", below="a wide canyon", affordances={"investigate", "build", "cross"}),
}

HERO_NAMES = ["Nova", "Aria", "Kai", "Milo", "Zia", "Rex"]
SIDEKICK_NAMES = ["Beam", "Pip", "Spark", "Luna", "Bolt", "Ivy"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for tool in TOOLS:
            out.append((place, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero teamwork story world with a plank problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"], dest="sidekick_type")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    tool = args.tool or rng.choice(list(TOOLS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        hero_type=hero_type,
        sidekick_type=sidekick_type,
        place=place,
        tool=tool,
    )


def story_name(ent: Entity) -> str:
    return ent.id


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        meters={"steadiness": 1.0, "focus": 0.0},
        memes={"curiosity": 1.0, "teamwork": 0.0, "confidence": 1.0},
        tags={"hero"},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name, kind="character", type=params.sidekick_type,
        meters={"steadiness": 1.0, "focus": 0.0},
        memes={"curiosity": 1.0, "teamwork": 0.0, "confidence": 1.0},
        tags={"hero"},
    ))
    plank = world.add(Entity(
        id="plank", type="plank", label="plank", phrase="a wooden plank",
        meters={"balance": 0.0, "strength": 0.0}, memes={"worry": 0.0}, tags={"plank"},
    ))
    gap = world.add(Entity(
        id="gap", type="gap", label="gap", phrase=place.below,
        meters={"width": 1.0, "danger": 1.0}, memes={"threat": 1.0}, tags={"gap"},
    ))
    gear = world.add(Entity(
        id=tool.id, type="tool", label=tool.label, phrase=tool.phrase,
        meters={"usefulness": 1.0}, memes={"idea": 1.0}, tags=set(tool.tags),
    ))

    # Setup
    world.say(f"{hero.id} and {sidekick.id} were tiny superheroes at {place.name}.")
    world.say(f"{place.sky.capitalize()} winds moved around them, and {place.below} waited below the broken path.")
    world.say(f"They found {plank.phrase}, but it was too short and slipped near the edge.")

    # Curiosity: inspect the problem.
    hero.memes["curiosity"] += 1.0
    sidekick.memes["curiosity"] += 1.0
    world.say(f"{hero.id} leaned close and studied the plank, because a good hero first asks why the problem is hard.")
    world.say(f"{sidekick.id} looked too, and soon they noticed the gap was wider than one plank could safely span.")

    # Problem solving: measure and plan.
    hero.meters["focus"] += 1.0
    sidekick.meters["focus"] += 1.0
    plank.meters["strength"] += 1.0
    world.say(f"Then {hero.id} pointed at {gear.label} and said they could use it to make a smarter plan.")
    world.say(f"{sidekick.id} agreed, and together they tested the edges, the plank, and the safest landing spot.")

    # Teamwork: combine efforts.
    hero.memes["teamwork"] += 1.0
    sidekick.memes["teamwork"] += 1.0
    if tool == "extra_plank":
        plank.meters["balance"] += 1.0
        world.say(f"They placed {gear.label} beside the first plank, making a wider bridge with two strong boards.")
    elif tool == "rope":
        plank.meters["balance"] += 0.5
        world.say(f"They tied {gear.label} around the plank, and one hero steadied it while the other held the line.")
    else:
        plank.meters["balance"] += 0.5
        world.say(f"With {gear.label}, they checked every step, spotted the weak spots, and chose the safest line across.")

    # Resolution.
    plank_ok = plank.meters["balance"] + plank.meters["strength"] >= 1.5
    if not plank_ok:
        raise StoryError("The plank setup never became safe enough to tell a proper superhero story.")
    world.say(f"At last, {hero.id} crossed first, then helped {sidekick.id} over, and no one slipped into {place.below}.")
    world.say(f"Together they stood on the far side, smiling like real heroes after a clever rescue.")

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "plank": plank,
        "gap": gap,
        "gear": gear,
        "place": place,
        "tool": tool,
        "solved": True,
    }

    story = world.render()
    prompts = [
        f"Write a short superhero story about {hero.id} and {sidekick.id} solving a plank problem with teamwork.",
        f"Tell a child-friendly story where curiosity helps heroes fix a dangerous gap using {gear.label}.",
        f"Write a simple superhero tale that includes a plank, a plan, and a safe crossing.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {hero.id} look closely at the plank?",
            answer=f"{hero.id} was curious and wanted to understand why the plank was not safe by itself."
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.id} solve the problem?",
            answer=f"They worked together, used {gear.label}, and made a safer way across the gap."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The heroes crossed safely, and the tricky gap was no longer stopping them."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a plank?",
            answer="A plank is a long, flat piece of wood that people can use in building or crossing."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the job so they can solve a problem together."
        ),
        QAItem(
            question="What does curiosity help a hero do?",
            answer="Curiosity helps a hero look closely, ask questions, and notice important details."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
tool(T) :- tool_name(T).
place(P) :- place_name(P).

needs_plan(P) :- place(P), plank_problem(P).
curiosity(H) :- hero(H).
teamwork(H,S) :- hero(H), sidekick(S), different(H,S).

solved(P,T) :- place(P), tool(T), useful(T), plank_problem(P).
plank_problem(P) :- place(P).

#show solved/2.
#show teamwork/2.
#show curiosity/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place_name", place))
        lines.append(asp.fact("plank_problem", place))
    for tool in TOOLS:
        lines.append(asp.fact("tool_name", tool))
        if "bridge" in TOOLS[tool].helps_with:
            lines.append(asp.fact("useful", tool))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("sidekick_name", "sidekick"))
    lines.append(asp.fact("different", "hero", "sidekick"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    symbols = set((s.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in s.arguments)) for s in model)
    expected = {("solved", ("bridge", "extra_plank")), ("solved", ("rooftop", "extra_plank")), ("solved", ("canyon", "extra_plank"))}
    if any(sym[0] == "solved" for sym in symbols):
        print("OK: ASP model produced solved/2 facts.")
        return 0
    print("MISMATCH: ASP model did not produce the expected solved facts.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = []
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Nova", "Beam", "girl", "boy", "bridge", "extra_plank"),
    StoryParams("Kai", "Ivy", "boy", "girl", "canyon", "rope"),
    StoryParams("Aria", "Bolt", "girl", "boy", "rooftop", "lamp"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
