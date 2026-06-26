#!/usr/bin/env python3
"""
storyworlds/worlds/wood_mystery_to_solve_space_adventure.py
============================================================

A small story world in a space-adventure style: a crew aboard a ship solves a
gentle mystery involving wood.

Premise:
- The crew finds an odd wooden object drifting near the ship.
- The object makes a clue trail: scratches, a hidden latch, and a map mark.
- The mystery is solved by careful observation and one useful tool.

World model:
- Physical meters track things like drift, scrape, dust, and signal.
- Emotional memes track curiosity, worry, relief, and teamwork.
- The story is generated from the world state, not from a fixed paragraph.

The domain is intentionally small and constraint-checked so every generated
story has a clear beginning, middle turn, and ending image.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "bridge": "the bridge",
    "cargo_bay": "the cargo bay",
    "airlock": "the airlock",
    "observatory": "the observatory",
}

HERO_NAMES = ["Nova", "Pip", "Rin", "Milo", "Aria", "Tess", "Luna", "Kai"]
ROLES = ["captain", "pilot", "engineer", "navigator"]
TRAITS = ["brave", "curious", "careful", "quick-thinking", "gentle"]

TOOLS = {
    "scanner": {
        "label": "scanner",
        "phrase": "a little scanner",
        "use": "scan",
        "clue": "a hidden latch under the wood grain",
        "helps": {"signal"},
    },
    "gloves": {
        "label": "gloves",
        "phrase": "soft gloves",
        "use": "lift",
        "clue": "small scratch marks on the wood",
        "helps": {"dust"},
    },
    "lamp": {
        "label": "lamp",
        "phrase": "a beam lamp",
        "use": "shine",
        "clue": "a faded map mark on the side",
        "helps": {"dark"},
    },
}

MYSTERIES = {
    "wood_box": {
        "label": "wooden box",
        "phrase": "an old wooden box",
        "type": "box",
        "source": "drifting cargo",
        "risk": "cracked",
        "trail": "scratches",
    },
    "wood_key": {
        "label": "wooden key",
        "phrase": "a smooth wooden key",
        "type": "key",
        "source": "lost repair kit",
        "risk": "scraped",
        "trail": "dust",
    },
    "wood_token": {
        "label": "wooden token",
        "phrase": "a carved wooden token",
        "type": "token",
        "source": "old shuttle locker",
        "risk": "faded",
        "trail": "a map mark",
    },
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    place: str = "the bridge"
    nearby: str = "deep space"
    stillness: str = "quiet"


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy

        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def mystery_at_risk(mystery: dict, tool: dict) -> bool:
    return True if mystery["label"] else False


def select_tool(mystery: dict, tool: dict) -> bool:
    # Every mystery has exactly one sensible tool in this small domain.
    if mystery["type"] == "box":
        return tool["label"] == "scanner"
    if mystery["type"] == "key":
        return tool["label"] == "gloves"
    if mystery["type"] == "token":
        return tool["label"] == "lamp"
    return False


# ---------------------------------------------------------------------------
# Tiny causal story engine
# ---------------------------------------------------------------------------
def _build_clue(world: World, hero: Entity, mystery: Entity, tool: dict) -> None:
    if ("clue", mystery.id) in world.fired:
        return
    world.fired.add(("clue", mystery.id))
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    mystery.meters["mystery"] = 1
    world.say(
        f"{hero.id} noticed {mystery.phrase} drifting near the ship, and {hero.pronoun('possessive')} eyes lit up."
    )
    world.say(
        f"It looked strange because the ship was full of metal, but this little thing was made of wood."
    )


def _inspect(world: World, hero: Entity, mystery: Entity, tool: dict) -> None:
    if ("inspect", mystery.id) in world.fired:
        return
    world.fired.add(("inspect", mystery.id))
    world.say(
        f"{hero.id} picked up {mystery.pronoun('object')} with {tool['phrase']} and began to {tool['use']} it carefully."
    )
    if tool["label"] == "scanner":
        world.say("The scanner blinked and found a hidden latch under the wood grain.")
        mystery.meters["signal"] = 1
    elif tool["label"] == "gloves":
        world.say("The gloves kept the splinters away, and small scratch marks showed on the wood.")
        mystery.meters["dust"] = 1
    else:
        world.say("The lamp shone across the surface and revealed a faded map mark on the side.")
        mystery.meters["dark"] = 1


def _solve(world: World, hero: Entity, mystery: Entity) -> None:
    if ("solve", mystery.id) in world.fired:
        return
    if mystery.meters.get("signal", 0) < THRESHOLD and mystery.meters.get("dust", 0) < THRESHOLD and mystery.meters.get("dark", 0) < THRESHOLD:
        return
    world.fired.add(("solve", mystery.id))
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    mystery.meters["solved"] = 1
    world.say(
        f"That clue was enough. {hero.id} realized the wooden thing was not junk at all."
    )
    world.say(
        f"It was a small part from {world.facts['source']}, and it had been hiding a simple message for anyone careful enough to look."
    )


def propagate(world: World) -> None:
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    tool = world.facts["tool"]
    _build_clue(world, hero, mystery, tool)
    _inspect(world, hero, mystery, tool)
    _solve(world, hero, mystery)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def opening_line(world: World, hero: Entity, mystery: Entity) -> None:
    world.say(
        f"On {world.ship.place}, {hero.id} was a {hero.memes.get('trait', 'curious')} {hero.type} who loved quiet stars and sudden clues."
    )
    world.say(
        f"One day, {hero.id} saw {mystery.phrase} floating past the window, and the ship's lights made its wooden edges glow."
    )


def tension_line(world: World, hero: Entity, mystery: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} wanted to shout for the others, but the mystery felt too important to rush."
    )
    world.say(
        f"If the object bumped the wall again, it might crack and lose its clue."
    )


def resolution_line(world: World, hero: Entity, mystery: Entity) -> None:
    if mystery.meters.get("solved", 0) < THRESHOLD:
        return
    world.say(
        f"{hero.id} smiled as the tiny wooden mystery finally made sense, and the ship felt a little warmer."
    )
    world.say(
        f"At the end, the wooden clue rested safely in {hero.pronoun('possessive')} hands, and the stars outside looked less lonely."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for tool in TOOLS:
                if select_tool(MYSTERIES[mystery], TOOLS[tool]):
                    combos.append((place, mystery, tool))
    return combos


def explain_rejection(mystery_id: str, tool_id: str) -> str:
    mystery = MYSTERIES[mystery_id]
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool['label']} does not fit this clue. "
        f"For {mystery['label']}, the sensible tool is a different one.)"
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        f"Write a short space adventure about {hero.id} finding {mystery.phrase} and solving its mystery.",
        f"Tell a child-friendly story where a {hero.type} uses {tool['phrase']} to understand a wooden clue on a spaceship.",
        f"Make a gentle mystery story in space with wood, a careful discovery, and a happy solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find near the ship?",
            answer=f"{hero.id} found {mystery.phrase} drifting near the ship.",
        ),
        QAItem(
            question=f"Why was the object a mystery?",
            answer="It was a mystery because the ship was full of metal, but the object was made of wood and had a hidden clue.",
        ),
        QAItem(
            question=f"What tool helped solve the clue?",
            answer=f"{tool['phrase'].capitalize()} helped {hero.id} inspect the wooden object and solve the mystery.",
        ),
    ]
    if mystery.meters.get("solved", 0) >= THRESHOLD:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the mystery solved, the wooden clue safe, and {hero.id} feeling relieved and happy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wood?",
            answer="Wood is a hard material that comes from trees. People can carve it, build with it, and make boxes or toys from it.",
        ),
        QAItem(
            question="What does a scanner do?",
            answer="A scanner looks for hidden things or secret signals without needing to break anything open.",
        ),
        QAItem(
            question="Why do space crews use lamps?",
            answer="Space crews use lamps when they need extra light to see dark corners, marks, or tiny details.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
choice(Place,Mystery,Tool) :- place(Place), mystery(Mystery), tool(Tool),
    can_solve(Mystery, Tool).

valid(Place,Mystery,Tool) :- choice(Place,Mystery,Tool).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("wooden", mid))
        lines.append(asp.fact("kind", mid, mystery["type"]))
        lines.append(asp.fact("can_solve", mid, select_tool(mystery, {"label": "scanner"} ) and "scanner" or ""))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("solves", tid, tool["label"]))
    for mid, mystery in MYSTERIES.items():
        if mystery["type"] == "box":
            lines.append(asp.fact("can_solve", mid, "scanner"))
        elif mystery["type"] == "key":
            lines.append(asp.fact("can_solve", mid, "gloves"))
        elif mystery["type"] == "token":
            lines.append(asp.fact("can_solve", mid, "lamp"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(Ship(place=PLACES[params.place]))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        memes={"trait": params.trait, "curiosity": 1.0},
    ))
    mystery_def = MYSTERIES[params.mystery]
    mystery = world.add(Entity(
        id=mystery_def["label"],
        type="wooden_object",
        label=mystery_def["label"],
        phrase=mystery_def["phrase"],
        meters={"drift": 1.0},
    ))
    tool = TOOLS[params.tool]
    world.facts = {
        "hero": hero,
        "mystery": mystery,
        "tool": tool,
        "source": mystery_def["source"],
    }
    return world


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    opening_line(world, hero, mystery)
    world.para()
    tension_line(world, hero, mystery)
    propagate(world)
    world.para()
    resolution_line(world, hero, mystery)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure mystery about wood.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.mystery and args.tool:
        if not select_tool(MYSTERIES[args.mystery], TOOLS[args.tool]):
            raise StoryError(explain_rejection(args.mystery, args.tool))
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        tool=tool,
        name=args.name or rng.choice(HERO_NAMES),
        role=args.role or rng.choice(ROLES),
        trait=args.trait or rng.choice(TRAITS),
    )


CURATED = [
    StoryParams(place="bridge", mystery="wood_box", tool="scanner", name="Nova", role="captain", trait="curious"),
    StoryParams(place="cargo_bay", mystery="wood_key", tool="gloves", name="Pip", role="engineer", trait="careful"),
    StoryParams(place="observatory", mystery="wood_token", tool="lamp", name="Rin", role="navigator", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
