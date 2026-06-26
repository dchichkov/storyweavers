#!/usr/bin/env python3
"""
storyworlds/worlds/rascal_bilge_ambidextrous_lesson_learned_suspense_space.py
=============================================================================

A small space-adventure storyworld about a rascal, a bilge leak, and an
ambidextrous repair crew member who learns the right lesson under suspense.

Premise:
- A tiny ship is drifting between moons.
- A mischievous rascal sneaks into the bilge and causes a mess.
- The crew must act fast before the ship's lights and life support fail.

Turn:
- The ambidextrous crew member can work with either hand and can fix the leak
  quickly.
- Suspense comes from the ticking meter, the darkening corridor, and the need
  to choose the right tool before the bilge floods.

Resolution:
- The repair succeeds.
- The rascal learns a lesson about tampering with ship systems.
- The ship glides on, safe again, with a brighter ending image.

The story is intentionally small, classical, and state-driven.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the little comet skiff"
    place: str = "the bilge corridor"
    dangerous: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    hand: str
    fixes: set[str]
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ship_name: str = "the little comet skiff"
    hero_name: str = "Nova"
    hero_type: str = "crew"
    rascal_name: str = "Mink"
    rascal_type: str = "rascal"
    place: str = "the bilge corridor"
    tool: str = "patch_clamp"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
TOOLS = {
    "patch_clamp": Tool(
        id="patch_clamp",
        label="patch clamp",
        phrase="a patch clamp with a bright red grip",
        hand="either",
        fixes={"leak"},
        covers={"pipe"},
    ),
    "bilge_pump": Tool(
        id="bilge_pump",
        label="bilge pump",
        phrase="a small bilge pump with a long hose",
        hand="either",
        fixes={"flood"},
        covers={"floor"},
    ),
    "insulated_glove": Tool(
        id="insulated_glove",
        label="insulated glove",
        phrase="an insulated glove for hot cables",
        hand="either",
        fixes={"spark"},
        covers={"hand"},
    ),
}

WORLD_KNOWLEDGE = {
    "bilge": [
        QAItem(
            question="What is a bilge on a ship?",
            answer="The bilge is the lowest part of a ship, where water can collect if something leaks.",
        )
    ],
    "rascal": [
        QAItem(
            question="What is a rascal?",
            answer="A rascal is a playful troublemaker who likes to sneak, tease, or cause little problems.",
        )
    ],
    "ambidextrous": [
        QAItem(
            question="What does ambidextrous mean?",
            answer="Ambidextrous means someone can use both hands well.",
        )
    ],
    "space": [
        QAItem(
            question="Why do ships in space still need careful repairs?",
            answer="Even in space, a ship needs working pipes, power, and air so the crew can stay safe.",
        )
    ],
    "suspense": [
        QAItem(
            question="What makes a story feel suspenseful?",
            answer="A story feels suspenseful when something important might go wrong and everyone must wait to see what happens.",
        )
    ],
}

ASP_RULES = r"""
% A repair is reasonable when the tool matches the problem and the hero can use
% it with the needed hand.
can_fix(T, P) :- tool(T), problem(P), fixes(T, P).
has_reasonable_repair(P) :- can_fix(_, P).

valid_story(Problem, Tool) :- problem(Problem), can_fix(Tool, Problem), ambi(hero).
"""

SHIP_NAMES = [
    "the little comet skiff",
    "the moon-skipper",
    "the lantern ark",
    "the starling shuttle",
]

HERO_NAMES = ["Nova", "Jax", "Rin", "Pip", "Mira", "Tess"]
RASCAL_NAMES = ["Mink", "Nip", "Sly", "Skitter", "Bramble"]
TRAITS = ["curious", "brave", "careful", "quick", "steady"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(Ship(name=params.ship_name, place=params.place))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="crew",
        label=params.hero_name,
        traits=["ambidextrous", random.choice(TRAITS)],
        meters={"stress": 0.0, "skill": 1.0},
        memes={"hope": 1.0, "worry": 0.0, "lesson": 0.0},
    ))
    rascal = world.add(Entity(
        id="rascal",
        kind="character",
        type="rascal",
        label=params.rascal_name,
        traits=["mischievous", "restless"],
        meters={"mess": 0.0},
        memes={"guilt": 0.0, "trouble": 1.0, "lesson": 0.0},
    ))
    tool = TOOLS[params.tool]
    world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        held_by=hero.id,
        meters={"usefulness": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.label} served aboard {world.ship.name}, a tiny ship that hummed through the dark between moons."
    )
    world.say(
        f"Beside {hero.pronoun('object')}, {rascal.label} the rascal kept sneaking into places {rascal.pronoun()} should not."
    )
    world.say(
        f"{hero.label} was ambidextrous, so {hero.pronoun()} could work with either hand without slowing down."
    )

    # Act 2: suspense and trouble
    world.para()
    world.say(
        f"One gray hour, a hiss came from {world.ship.place}, and water began to bead along the floor."
    )
    rascal.meters["mess"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"{rascal.label} had knocked loose a valve in the bilge, and now the ship felt quieter in the worst way."
    )
    world.say(
        f"The blinking panel warned that if the leak spread much farther, the lower deck would flood."
    )
    world.say(
        f"{hero.label} crouched down, listening to the drip-drip-drip, while {rascal.label} froze with wide eyes."
    )
    world.say(
        f"For a breath, nobody spoke, and the long dark corridor made the whole repair feel full of suspense."
    )

    # Act 3: repair and lesson learned
    world.para()
    hero.meters["skill"] += 1.0
    hero.memes["hope"] += 1.0
    world.say(
        f"{hero.label} used {hero.pronoun('possessive')} {tool.label} with a quick, steady motion and sealed the valve."
    )
    world.say(
        f"The drip stopped. The floor stayed dry. The little ship gave a soft, safe shiver and kept on flying."
    )
    rascal.memes["guilt"] += 1.0
    rascal.memes["lesson"] += 1.0
    hero.memes["lesson"] += 1.0
    world.say(
        f"{rascal.label} learned a lesson that day: a prank in the wrong place can endanger everyone on board."
    )
    world.say(
        f"{hero.label} learned another lesson too: when trouble arrives, a calm hand and the right tool can turn fear into a fix."
    )
    world.say(
        f"By the time the stars brightened outside the porthole, the bilge was dry again, and the crew could smile."
    )

    world.facts.update(
        hero=hero,
        rascal=rascal,
        tool=tool,
        ship=world.ship,
        suspense=True,
        resolved=True,
        leak_fixed=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rascal = f["rascal"]
    tool = f["tool"]
    return [
        "Write a short space-adventure story about a rascal causing a bilge leak and an ambidextrous crew member fixing it.",
        f"Tell a suspenseful story where {hero.label} must repair a bilge leak before the ship floods, while {rascal.label} learns a lesson.",
        f"Create a child-friendly spaceship story that includes a rascal, the bilge, and {tool.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rascal = f["rascal"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who fixed the leak in the bilge?",
            answer=f"{hero.label} fixed the leak with {hero.pronoun('possessive')} {tool.label}.",
        ),
        QAItem(
            question=f"Why was the story suspenseful?",
            answer="It was suspenseful because the leak might spread and flood the lower deck before the repair could be finished.",
        ),
        QAItem(
            question=f"What lesson did {rascal.label} learn?",
            answer=f"{rascal.label} learned that causing trouble in the bilge can put the whole ship at risk.",
        ),
        QAItem(
            question=f"What does it mean that {hero.label} was ambidextrous?",
            answer=f"It meant {hero.label} could work well with either hand, which helped finish the repair quickly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["bilge"])
    out.extend(WORLD_KNOWLEDGE["rascal"])
    out.extend(WORLD_KNOWLEDGE["ambidextrous"])
    out.extend(WORLD_KNOWLEDGE["space"])
    out.extend(WORLD_KNOWLEDGE["suspense"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
# ASP helpers
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp

    lines = []
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.fixes):
            lines.append(asp.fact("fixes", t.id, p))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    lines.append(asp.fact("problem", "leak"))
    lines.append(asp.fact("problem", "flood"))
    lines.append(asp.fact("ambi", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("leak", "patch_clamp")}
    if asp_set == py_set:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


def python_reasonable(params: StoryParams) -> None:
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.hero_name == params.rascal_name:
        raise StoryError("The hero and the rascal must be different characters.")
    if params.tool != "patch_clamp":
        raise StoryError("This story only makes sense with the patch clamp as the repair.")
    if not params.hero_name or not params.rascal_name:
        raise StoryError("Both hero and rascal need names.")


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about a rascal, the bilge, and an ambidextrous repair.")
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--rascal-name", choices=RASCAL_NAMES)
    ap.add_argument("--tool", choices=TOOLS)
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
    ship_name = args.ship_name or rng.choice(SHIP_NAMES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    rascal_name = args.rascal_name or rng.choice(RASCAL_NAMES)
    tool = args.tool or "patch_clamp"
    params = StoryParams(
        seed=None,
        ship_name=ship_name,
        hero_name=hero_name,
        rascal_name=rascal_name,
        tool=tool,
    )
    python_reasonable(params)
    return params


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(ship_name="the little comet skiff", hero_name="Nova", rascal_name="Mink", tool="patch_clamp"),
    StoryParams(ship_name="the moon-skipper", hero_name="Rin", rascal_name="Skitter", tool="patch_clamp"),
    StoryParams(ship_name="the lantern ark", hero_name="Pip", rascal_name="Nip", tool="patch_clamp"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story pattern(s):")
        for p in vals:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
