#!/usr/bin/env python3
"""
storyworlds/worlds/story_clamber_flashback_space_adventure.py
=============================================================

A small space-adventure story world with one core premise:
a child or crew member must clamber through a ship or station,
and a flashback reveals why the risky route matters.

The world is intentionally tiny and state-driven:
- physical meters track wear, oxygen, grip, and damage
- emotional memes track worry, courage, relief, and memory
- the flashback is not a decorative label; it changes the reason
  the character chooses the clambering path
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    role: str
    kind: str = "character"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {
        "oxygen": 5.0,
        "grip": 5.0,
        "wear": 0.0,
        "damage": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "courage": 0.0,
        "relief": 0.0,
        "memory": 0.0,
    })

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def subject_name(self) -> str:
        return self.id


@dataclass
class Location:
    name: str
    kind: str
    has_dark_gap: bool = False
    has_shortcut: bool = False
    has_window: bool = False


@dataclass
class Tool:
    name: str
    helps: str
    reduces_wear: float = 0.0
    boosts_grip: float = 0.0


@dataclass
class StoryParams:
    location: str
    hero_name: str
    hero_role: str
    companion: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Person] = {}
        self.tools: dict[str, Tool] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add_person(self, p: Person) -> Person:
        self.entities[p.id] = p
        return p

    def add_tool(self, t: Tool) -> Tool:
        self.tools[t.name] = t
        return t

    def get(self, pid: str) -> Person:
        return self.entities[pid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def note(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "corridor": Location(name="the long corridor", kind="ship", has_dark_gap=True, has_shortcut=False),
    "airlock": Location(name="the airlock hall", kind="station", has_dark_gap=True, has_shortcut=True),
    "cargo": Location(name="the cargo bay", kind="ship", has_dark_gap=False, has_shortcut=True),
    "observatory": Location(name="the observatory deck", kind="station", has_dark_gap=False, has_window=True),
}

TOOLS = {
    "mag_gloves": Tool(name="magnetic gloves", helps="hold onto the rails", reduces_wear=1.0, boosts_grip=2.0),
    "patch_kit": Tool(name="a patch kit", helps="seal small tears", reduces_wear=2.0, boosts_grip=0.0),
    "lamp": Tool(name="a tiny lamp", helps="light the dark gap", reduces_wear=0.0, boosts_grip=0.0),
}

COMRADES = ["pilot", "engineer", "navigator", "cadet"]
HERO_NAMES = ["Nova", "Milo", "Iris", "Taj", "Luna", "Pip"]
TRAITS = ["brave", "curious", "gentle", "bold", "quick-thinking"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A scene is reasonable when the location contains a dark gap and the hero has
% a tool that helps them clamber through it.
reasonable(L, T) :- location(L), dark_gap(L), tool(T), helps(T, grip).

% The shortcut is only valid when it exists and the hero can see it or has light.
flashback_needed(L) :- dark_gap(L), not shortcut(L).
flashback_needed(L) :- dark_gap(L), shortcut(L), not lamp(T) : tool(T).

valid_story(L, T) :- location(L), tool(T), reasonable(L, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, loc in LOCATIONS.items():
        lines.append(asp.fact("location", key))
        if loc.has_dark_gap:
            lines.append(asp.fact("dark_gap", key))
        if loc.has_shortcut:
            lines.append(asp.fact("shortcut", key))
        if loc.has_window:
            lines.append(asp.fact("window", key))
    for key, tool in TOOLS.items():
        lines.append(asp.fact("tool", key))
        if tool.boosts_grip > 0:
            lines.append(asp.fact("helps", key, "grip"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    world = World(loc)

    hero = world.add_person(Person(
        id=params.hero_name,
        role=params.hero_role,
        traits=[random.choice(TRAITS), "stubborn"],
    ))
    companion = world.add_person(Person(
        id=params.companion,
        role="pilot" if params.companion != params.hero_name else "engineer",
        label=params.companion,
    ))
    tool = TOOLS[params.tool]
    world.add_tool(tool)

    # Act 1: setup
    world.say(f"{hero.subject_name()} was a {hero.traits[0]} little {hero.role} aboard a bright ship.")
    world.say(f"{hero.pronoun().capitalize()} and {companion.id} had a job to do in {loc.name}.")
    world.say(f"{hero.subject_name()} carried {tool.name}, which could {tool.helps}.")

    # Act 2: tension
    world.para()
    hero.memes["worry"] += 1
    world.say(f"Then they found a dark gap near the route, and the easy way was blocked.")
    world.say(f"{hero.subject_name()} looked at the narrow hatch and knew someone would have to clamber across.")
    if loc.has_shortcut:
        world.say(f"A small shortcut existed, but it was too tight for a safe walk.")

    # Flashback: why the choice matters
    world.para()
    hero.memes["memory"] += 1
    world.say(f"Flashback: yesterday, {hero.subject_name()} had seen a loose panel near the same place.")
    world.say(f"It had scraped a sleeve and made the corridor feel less safe.")
    world.say(f"That memory returned now, and {hero.pronoun()} remembered to use {tool.name} instead of rushing.")

    # Act 3: turn and resolution
    world.para()
    hero.memes["courage"] += 2
    hero.meters["grip"] += TOOLs_grip(tool)
    wear_gain = max(0.0, 1.5 - tool.reduces_wear)
    hero.meters["wear"] += wear_gain
    if loc.has_dark_gap:
        hero.meters["oxygen"] -= 1.0
    world.say(f"So {hero.subject_name()} clambered along the rail, one careful hand after another.")
    world.say(f"{hero.subject_name()} held tight with {tool.name} and reached the far side without slipping.")
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"When {hero.subject_name()} landed safely, {companion.id} grinned and the two of them finished the job.")

    world.facts.update(
        hero=hero,
        companion=companion,
        tool=tool,
        location=loc,
        flashback=True,
        clamber=True,
        resolved=True,
    )
    return world


def TOOLs_grip(tool: Tool) -> float:
    return tool.boosts_grip


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Person = f["hero"]
    loc: Location = f["location"]
    tool: Tool = f["tool"]
    return [
        f"Write a short space-adventure story for a small child where {hero.id} has to clamber through {loc.name}.",
        f"Tell a gentle story that includes a flashback, a careful clamber, and {tool.name}.",
        f"Write a story about a brave crew member who remembers an old danger and uses {tool.name} to cross a narrow gap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    comp: Person = f["companion"]
    loc: Location = f["location"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Where did {hero.id} have to go in the story?",
            answer=f"{hero.id} had to go through {loc.name} with {comp.id} to finish the job.",
        ),
        QAItem(
            question=f"What did {hero.id} use to clamber safely?",
            answer=f"{hero.id} used {tool.name} so {hero.pronoun()} could {tool.helps} while clambering.",
        ),
        QAItem(
            question="Why did the story include a flashback?",
            answer="The flashback reminded the hero about a loose panel and helped them choose the safer path.",
        ),
        QAItem(
            question=f"How did {hero.id} get across the gap?",
            answer=f"{hero.id} clambered along the rail carefully and reached the other side without slipping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something from earlier, so the reader understands why a character thinks or acts a certain way now.",
        ),
        QAItem(
            question="What does clamber mean?",
            answer="To clamber means to climb in a careful, awkward way, usually with both hands and feet helping at once.",
        ),
        QAItem(
            question="Why do people use magnetic gloves in a spaceship?",
            answer="Magnetic gloves help someone hold onto metal rails or surfaces so they do not slip while moving around in space.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for p in world.entities.values():
        lines.append(
            f"{p.id}: meters={{{', '.join(f'{k}={v:.1f}' for k, v in p.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v:.1f}' for k, v in p.memes.items() if v)}}}"
        )
    lines.append(f"location={world.location.name}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters, generation, output
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    location: str
    hero_name: str
    hero_role: str
    companion: str
    tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a clamber and a flashback.")
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--name", dest="hero_name", choices=HERO_NAMES)
    ap.add_argument("--role", dest="hero_role", choices=["cadet", "pilot", "engineer", "navigator"])
    ap.add_argument("--companion", choices=COMRADES)
    ap.add_argument("--tool", choices=TOOLS.keys())
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
    location = args.location or rng.choice(list(LOCATIONS.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_role = args.hero_role or rng.choice(["cadet", "pilot", "engineer", "navigator"])
    companion = args.companion or rng.choice([c for c in COMRADES if c != hero_role])
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    if location == "observatory" and tool == "patch_kit":
        raise StoryError("The patch kit does not fit this observatory clamber story; choose a grip-helping tool.")
    return StoryParams(location=location, hero_name=hero_name, hero_role=hero_role, companion=companion, tool=tool)


def generate(params: StoryParams) -> StorySample:
    random.seed(params.seed)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    model_pairs = set(asp_valid_pairs())
    python_pairs = set((loc, tool) for loc in LOCATIONS for tool in TOOLS if LOCATIONS[loc].has_dark_gap and TOOLS[tool].boosts_grip > 0)
    if model_pairs == python_pairs:
        print(f"OK: ASP matches Python on {len(model_pairs)} valid story pairs.")
        return 0
    print("Mismatch between ASP and Python.")
    if model_pairs - python_pairs:
        print("Only in ASP:", sorted(model_pairs - python_pairs))
    if python_pairs - model_pairs:
        print("Only in Python:", sorted(python_pairs - model_pairs))
    return 1


def asp_program_text() -> str:
    return asp_program("#show valid_story/2.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(location="corridor", hero_name="Nova", hero_role="cadet", companion="pilot", tool="mag_gloves"),
    StoryParams(location="airlock", hero_name="Iris", hero_role="engineer", companion="navigator", tool="lamp"),
    StoryParams(location="cargo", hero_name="Milo", hero_role="pilot", companion="engineer", tool="mag_gloves"),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        for loc, tool in pairs:
            print(f"{loc} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 50:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
