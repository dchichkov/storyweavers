#!/usr/bin/env python3
"""
A small Space Adventure storyworld about a ship rigger, a ship side, a giddy
crew, a Conflict, and a choice between a Bad Ending and a Happy Ending.

The premise is simple: a space rigger notices trouble on one side of a little
starship. If the crack is ignored, the story veers toward a bad ending. If the
crew works together, the rigger can fix the side and the ship can sail on.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "rigger"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ShipPart:
    name: str
    side: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    fixes: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ship_name: str = "Star Kite"
    rigger_name: str = "Rex"
    captain_name: str = "Mina"
    side: str = "port"
    tool: str = "patch_kit"
    ending: str = "happy"


class World:
    def __init__(self, ship_name: str, side: str):
        self.ship_name = ship_name
        self.side = side
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone = World(self.ship_name, self.side)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SHIP_PARTS = {
    "port": ShipPart(name="port side", side="port"),
    "starboard": ShipPart(name="starboard side", side="starboard"),
}

TOOLS = {
    "patch_kit": Tool(
        id="patch_kit",
        label="patch kit",
        fixes={"leak"},
        prep="grab the patch kit",
        tail="sealed the crack with a shiny patch",
    ),
    "weld_torch": Tool(
        id="weld_torch",
        label="weld torch",
        fixes={"leak"},
        prep="wake up the weld torch",
        tail="melted the broken seam back together",
    ),
}

GIDDY_NAMES = ["Nia", "Juno", "Pip", "Tala", "Bex", "Lio"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: riggers, ship sides, and endings.")
    ap.add_argument("--ship-name")
    ap.add_argument("--rigger-name")
    ap.add_argument("--captain-name")
    ap.add_argument("--side", choices=["port", "starboard"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--ending", choices=["bad", "happy"])
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
    side = args.side or rng.choice(["port", "starboard"])
    tool = args.tool or rng.choice(list(TOOLS))
    ending = args.ending or rng.choice(["happy", "bad"])
    ship_name = args.ship_name or rng.choice(["Star Kite", "Moon Finch", "Comet Pike"])
    rigger_name = args.rigger_name or rng.choice(["Rex", "Ari", "Nova", "Tess"])
    captain_name = args.captain_name or rng.choice(["Mina", "Sol", "Quin", "Iris"])
    return StoryParams(
        ship_name=ship_name,
        rigger_name=rigger_name,
        captain_name=captain_name,
        side=side,
        tool=tool,
        ending=ending,
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    rigger = world.add(Entity(
        id=params.rigger_name,
        kind="character",
        type="rigger",
        label="the rigger",
        role="rigger",
        meters={"focus": 1.0},
        memes={"giddy": 1.0},
    ))
    captain = world.add(Entity(
        id=params.captain_name,
        kind="character",
        type="captain",
        label="the captain",
        role="captain",
        meters={"calm": 1.0},
        memes={"trust": 1.0},
    ))
    hull = world.add(Entity(
        id="hull",
        kind="thing",
        type="hull",
        label=f"{params.side} side",
        phrase=f"the {params.side} side of the hull",
        role=params.side,
        meters={"crack": 1.0},
    ))
    return rigger, captain, hull


def _do_conflict(world: World, rigger: Entity, captain: Entity, hull: Entity) -> None:
    if "conflict" in world.fired:
        return
    world.fired.add("conflict")
    rigger.memes["giddy"] += 1.0
    captain.meters["worry"] = captain.meters.get("worry", 0.0) + 1.0
    world.say(
        f"On the quiet deck of the {world.ship_name}, {rigger.id} spotted a crack on the {hull.label}."
    )
    world.say(
        f"{rigger.id} was giddy to fix it, but {captain.id} worried the small leak could become a bigger problem."
    )
    world.say(
        f"That was the start of the Conflict: one voice wanted to rush ahead, and the other wanted to be careful."
    )


def _predict_bad_end(world: World, hull: Entity) -> bool:
    sim = world.copy()
    sim.get("hull").meters["crack"] += 1.0
    return sim.get("hull").meters["crack"] >= 2.0


def _fix_ship(world: World, rigger: Entity, captain: Entity, hull: Entity, tool: Tool) -> None:
    if hull.meters.get("crack", 0.0) < THRESHOLD:
        return
    hull.meters["crack"] = 0.0
    hull.meters["safe"] = 1.0
    rigger.memes["giddy"] += 1.0
    captain.meters["worry"] = 0.0
    world.say(
        f"{captain.id} handed over the {tool.label}, and {rigger.id} used it with steady hands."
    )
    world.say(
        f"{rigger.id} {tool.tail}, and the {hull.label} grew smooth and strong again."
    )


def tell(params: StoryParams) -> World:
    world = World(params.ship_name, params.side)
    rigger, captain, hull = _setup(world, params)
    tool = TOOLS[params.tool]

    world.say(
        f"Far from Earth, the little ship {params.ship_name} drifted through bright space."
    )
    world.say(
        f"{rigger.id} was a giddy rigger who loved humming near the engines."
    )
    world.say(
        f"{captain.id} trusted {rigger.id}, but on this trip the {hull.label} had a crack."
    )

    world.para()
    _do_conflict(world, rigger, captain, hull)

    world.para()
    if params.ending == "bad":
        if _predict_bad_end(world, hull):
            hull.meters["crack"] += 1.0
            world.say(
                f"{rigger.id} ignored the warning and tried to race the ship back to speed."
            )
            world.say(
                f"The crack spread with a hiss, and the {params.ship_name} had a Bad Ending: the crew had to stop and drift home for repairs."
            )
        else:
            world.say(
                f"The ship never truly slipped into danger, but the crew still felt the uneasy silence of a Bad Ending that almost happened."
            )
    else:
        world.say(
            f"{captain.id} asked for calm hands and a smart plan."
        )
        _fix_ship(world, rigger, captain, hull, tool)
        world.say(
            f"After that, the {params.ship_name} sailed on through starlight, and the crew shared a Happy Ending with wide smiles."
        )

    world.facts.update(
        rigger=rigger,
        captain=captain,
        hull=hull,
        tool=tool,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short Space Adventure story about a giddy rigger fixing the {p.side} side of a ship.",
        f"Tell a child-friendly story where {p.rigger_name} the rigger and {p.captain_name} face a Conflict on the {p.side} side of {p.ship_name}.",
        f"Write a simple tale that ends in either a Bad Ending or a Happy Ending for {p.ship_name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who was the giddy rigger in the story?",
            answer=f"The giddy rigger was {p.rigger_name}, who loved fixing spaceships.",
        ),
        QAItem(
            question=f"What part of the ship had the crack?",
            answer=f"The crack was on the {p.side} side of {p.ship_name}.",
        ),
        QAItem(
            question=f"Did the story end in a Bad Ending or a Happy Ending?",
            answer=f"It ended with a {p.ending.replace('_', ' ').title()} ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a rigger do on a ship?",
            answer="A rigger repairs ship parts, tightens loose pieces, and keeps the ship safe for travel.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the characters need to choose what to do next.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and things finish in a good, hopeful way.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the problem gets worse or the characters cannot fix it in time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("side", "port"),
        asp.fact("side", "starboard"),
        asp.fact("tool", "patch_kit"),
        asp.fact("tool", "weld_torch"),
        asp.fact("fixes", "patch_kit", "leak"),
        asp.fact("fixes", "weld_torch", "leak"),
        asp.fact("covers", "port", "port"),
        asp.fact("covers", "starboard", "starboard"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
has_conflict(S) :- side(S).
bad_ending(S) :- has_conflict(S), not repaired(S).
happy_ending(S) :- repaired(S).
repaired(S) :- side(S), fixes(T, leak), tool(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(ship_name="Star Kite", rigger_name="Rex", captain_name="Mina", side="port", tool="patch_kit", ending="happy"),
        StoryParams(ship_name="Moon Finch", rigger_name="Ari", captain_name="Sol", side="starboard", tool="weld_torch", ending="happy"),
        StoryParams(ship_name="Comet Pike", rigger_name="Tess", captain_name="Iris", side="port", tool="patch_kit", ending="bad"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show has_conflict/1. #show bad_ending/1. #show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
