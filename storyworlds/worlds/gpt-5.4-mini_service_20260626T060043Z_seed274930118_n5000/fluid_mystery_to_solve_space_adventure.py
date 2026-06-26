#!/usr/bin/env python3
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
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
class ShipModule:
    id: str
    label: str
    place: str
    clues: list[str] = field(default_factory=list)
    leak_risk: bool = False


@dataclass
class Fluid:
    id: str
    label: str
    color: str
    smell: str
    safe: bool
    source: str
    clue_style: str
    spreads_to: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    fits_fluid: set[str] = field(default_factory=set)
    fixes_risk: bool = False
    requires_place: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    module: str
    fluid: str
    tool: str
    hero: str
    sidekick: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, module: ShipModule):
        self.module = module
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.module)
        w.entities = {k: Entity(**{
            **vars(v),
            "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MODULES = {
    "lab": ShipModule(
        id="lab",
        label="the science lab",
        place="science lab",
        clues=["glittering panel", "tiny hose", "smudge trail", "soft hum"],
        leak_risk=True,
    ),
    "engine": ShipModule(
        id="engine",
        label="the engine room",
        place="engine room",
        clues=["warm pipe", "vibration", "drip sound", "shiny bolt"],
        leak_risk=True,
    ),
    "cargo": ShipModule(
        id="cargo",
        label="the cargo bay",
        place="cargo bay",
        clues=["stacked crates", "sticky floor", "floating tag", "hollow echo"],
        leak_risk=True,
    ),
    "greenhouse": ShipModule(
        id="greenhouse",
        label="the greenhouse dome",
        place="greenhouse dome",
        clues=["leafy mist", "glass wall", "water tray", "bright seedling"],
        leak_risk=True,
    ),
}

FLUIDS = {
    "blue": Fluid(
        id="blue",
        label="blue fluid",
        color="blue",
        smell="like metal rain",
        safe=False,
        source="a cracked sample tube",
        clue_style="blue drops",
        spreads_to={"floor", "boots"},
    ),
    "green": Fluid(
        id="green",
        label="green fluid",
        color="green",
        smell="like mint and stone",
        safe=False,
        source="a tilted algae tank",
        clue_style="green beads",
        spreads_to={"floor", "gloves"},
    ),
    "gold": Fluid(
        id="gold",
        label="gold fluid",
        color="gold",
        smell="like warm sugar",
        safe=False,
        source="a loose coolant coil",
        clue_style="gold glints",
        spreads_to={"floor", "tools"},
    ),
    "clear": Fluid(
        id="clear",
        label="clear fluid",
        color="clear",
        smell="like fresh air",
        safe=True,
        source="a condensation pipe",
        clue_style="wet shine",
        spreads_to={"floor", "rails"},
    ),
}

TOOLS = {
    "scanner": Tool(
        id="scanner",
        label="a pocket scanner",
        use="scan the clues",
        fits_fluid={"blue", "green", "gold", "clear"},
        fixes_risk=False,
    ),
    "towel": Tool(
        id="towel",
        label="an absorbent towel",
        use="soak up the spill",
        fits_fluid={"clear", "blue", "green", "gold"},
        fixes_risk=True,
        requires_place=None,
    ),
    "sealant": Tool(
        id="sealant",
        label="a sealant patch",
        use="seal the crack",
        fits_fluid={"blue", "gold", "clear"},
        fixes_risk=True,
        requires_place="engine",
    ),
    "net": Tool(
        id="net",
        label="a fine catch-net",
        use="catch floating droplets",
        fits_fluid={"green", "clear"},
        fixes_risk=True,
        requires_place="greenhouse",
    ),
}

HERO_NAMES = ["Mina", "Jory", "Tess", "Nico", "Ari", "Luna", "Pip", "Rae"]
SIDEKICK_NAMES = ["Bo", "Zee", "Miko", "Kit", "Sol", "Bea"]
CAPTAIN_NAMES = ["Captain Orion", "Captain Vega", "Captain Mira", "Captain Nova"]

VALID_COMBOS = [
    (mid, fid, tid)
    for mid, mod in MODULES.items()
    for fid, fluid in FLUIDS.items()
    for tid, tool in TOOLS.items()
    if mod.leak_risk and fluid.safe is False and tool.fixes_risk and (tool.requires_place is None or tool.requires_place == mid)
    and fluid.id in tool.fits_fluid
]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_story(module: ShipModule, fluid: Fluid, tool: Tool) -> bool:
    return (
        module.leak_risk
        and not fluid.safe
        and tool.fixes_risk
        and fluid.id in tool.fits_fluid
        and (tool.requires_place is None or tool.requires_place == module.id)
    )


def explain_rejection(module: ShipModule, fluid: Fluid, tool: Tool) -> str:
    if not module.leak_risk:
        return "(No story: that room does not have a mystery worth solving.)"
    if fluid.safe:
        return "(No story: a safe fluid does not create a believable mystery.)"
    if not tool.fixes_risk:
        return "(No story: that tool can notice the spill, but it cannot solve it.)"
    if fluid.id not in tool.fits_fluid:
        return f"(No story: {tool.label} does not fit the kind of {fluid.label} this mystery needs.)"
    if tool.requires_place and tool.requires_place != module.id:
        return f"(No story: {tool.label} only helps in the {tool.requires_place}, not in the {module.label}.)"
    return "(No story: the choices do not make a solvable space mystery.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    module = MODULES[params.module]
    fluid = FLUIDS[params.fluid]
    tool = TOOLS[params.tool]

    world = World(module)
    hero = world.add(Entity(id=params.hero, kind="character", type="cadet", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="crewmate", label=params.sidekick))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    spill = world.add(Entity(
        id="spill", kind="thing", type="fluid", label=fluid.label, phrase=fluid.label,
        owner=module.id, location=module.id,
        meters={"volume": 1.0}, memes={"mystery": 1.0},
    ))
    gadget = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.label,
        owner=hero.id,
    ))

    # Act 1
    world.say(f"{hero.label} was a young space cadet aboard a silver ship.")
    world.say(f"{hero.label} liked quiet jobs, and {sidekick.label} liked following clues.")
    world.say(f"One shift, they went to {module.label}, where a strange {fluid.label} had appeared.")
    world.say(f"It came from {fluid.source}, and its smell was {fluid.smell}.")
    world.para()

    # Act 2
    world.say(f"The floor showed {fluid.clue_style}, and the mystery grew bigger with every step.")
    world.say(f"{hero.label} picked up {tool.label} to {tool.use}.")
    if tool.id == "scanner":
        world.say(f"The scanner blinked at the marks and pointed toward the source in {module.label}.")
    elif tool.id == "towel":
        world.say(f"The towel soaked up the spill before it could reach the wires underfoot.")
    elif tool.id == "sealant":
        world.say(f"The patch fit the crack and stopped more fluid from leaking out.")
    else:
        world.say(f"The net held the droplets still long enough for a careful fix.")
    world.say(f"{sidekick.label} held the light steady while {hero.label} followed the trail.")
    world.para()

    # Act 3
    if tool.fixes_risk and valid_story(module, fluid, tool):
        world.say(f"{captain.label} smiled when the room turned quiet again.")
        world.say(f"In the end, the ship was safe, the mystery was solved, and {fluid.label} was under control.")
        world.say(f"{hero.label} and {sidekick.label} left {module.label} with clean boots and bright eyes.")
    else:
        world.say(f"The clues did not make sense yet, and the crew had to keep searching.")
        world.say(f"Still, {hero.label} wrote down the signs so the next team could solve it soon.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        captain=captain,
        module=module,
        fluid=fluid,
        tool=tool,
        solved=tool.fixes_risk and valid_story(module, fluid, tool),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    module: ShipModule = f["module"]
    fluid: Fluid = f["fluid"]
    tool: Tool = f["tool"]
    hero: Entity = f["hero"]
    return [
        f'Write a short space-adventure mystery for a child about a {fluid.label} problem in {module.label}.',
        f"Tell a gentle story where {hero.label} finds a clue, uses {tool.label}, and solves the mystery in {module.label}.",
        f'Write a simple story that includes the word "fluid" and ends with the ship feeling safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    captain: Entity = f["captain"]
    module: ShipModule = f["module"]
    fluid: Fluid = f["fluid"]
    tool: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"What mystery did {hero.label} and {sidekick.label} find in {module.label}?",
            answer=f"They found a {fluid.label} mystery in {module.label}, and the spill made the room look strange.",
        ),
        QAItem(
            question=f"What tool did {hero.label} use to help solve the problem?",
            answer=f"{hero.label} used {tool.label} to {tool.use} and help solve the mystery.",
        ),
        QAItem(
            question=f"Who was watching when the mystery was solved?",
            answer=f"{captain.label} was watching, and the captain smiled when the ship was safe again.",
        ),
    ]
    if f["solved"]:
        qa.append(QAItem(
            question=f"How did the story end after the {fluid.label} was found?",
            answer=f"It ended with the leak under control, the mystery solved, and {hero.label} and {sidekick.label} walking away proudly.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    fluid: Fluid = world.facts["fluid"]
    tool: Tool = world.facts["tool"]
    module: ShipModule = world.facts["module"]
    out = [
        QAItem(
            question="What is a fluid?",
            answer="A fluid is a material that can flow and take the shape of its container, like water or juice.",
        ),
        QAItem(
            question="What does a scanner do in a mystery?",
            answer="A scanner helps find clues by noticing details that are hard to see with just your eyes.",
        ),
        QAItem(
            question="What is a space ship room?",
            answer=f"A ship room like {module.label} is a place aboard a ship where the crew works and watches for problems.",
        ),
    ]
    if fluid.id == "clear":
        out.append(QAItem(
            question="Can clear fluid still make a mess?",
            answer="Yes. Clear fluid can still be wet and slippery even if it is hard to see.",
        ))
    if tool.id == "sealant":
        out.append(QAItem(
            question="What does sealant do?",
            answer="Sealant closes small cracks or holes so liquid cannot leak out again.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
module_ok(M) :- module(M), leak_risk(M).
mystery_fluid(F) :- fluid(F), not safe(F).
tool_solves(T,F,M) :- tool(T), fixes_risk(T), mystery_fluid(F), fits(T,F),
                      module_ok(M), usable_in(T,M).
valid_story(M,F,T) :- module_ok(M), mystery_fluid(F), tool_solves(T,F,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, mod in MODULES.items():
        lines.append(asp.fact("module", mid))
        if mod.leak_risk:
            lines.append(asp.fact("leak_risk", mid))
    for fid, fluid in FLUIDS.items():
        lines.append(asp.fact("fluid", fid))
        if fluid.safe:
            lines.append(asp.fact("safe", fid))
        for p in fluid.spreads_to:
            lines.append(asp.fact("spreads_to", fid, p))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.fixes_risk:
            lines.append(asp.fact("fixes_risk", tid))
        for fid in sorted(tool.fits_fluid):
            lines.append(asp.fact("fits", tid, fid))
        if tool.requires_place:
            lines.append(asp.fact("usable_in", tid, tool.requires_place))
        else:
            for mid in MODULES:
                lines.append(asp.fact("usable_in", tid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((m, f, t) for m, f, t in VALID_COMBOS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid combos ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.module and args.fluid and args.tool:
        mod = MODULES[args.module]
        fluid = FLUIDS[args.fluid]
        tool = TOOLS[args.tool]
        if not valid_story(mod, fluid, tool):
            raise StoryError(explain_rejection(mod, fluid, tool))

    combos = [
        c for c in VALID_COMBOS
        if (args.module is None or c[0] == args.module)
        and (args.fluid is None or c[1] == args.fluid)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mid, fid, tid = rng.choice(sorted(combos))
    return StoryParams(
        place=MODULES[mid].place,
        module=mid,
        fluid=fid,
        tool=tid,
        hero=args.hero or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != args.hero]),
        captain=args.captain or rng.choice(CAPTAIN_NAMES),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  module={world.module.id}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure mystery storyworld about a strange fluid leak."
    )
    ap.add_argument("--module", choices=MODULES)
    ap.add_argument("--fluid", choices=FLUIDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--captain")
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


CURATED = [
    StoryParams(place=MODULES["lab"].place, module="lab", fluid="blue", tool="scanner", hero="Mina", sidekick="Bo", captain="Captain Nova"),
    StoryParams(place=MODULES["engine"].place, module="engine", fluid="gold", tool="sealant", hero="Jory", sidekick="Zee", captain="Captain Orion"),
    StoryParams(place=MODULES["greenhouse"].place, module="greenhouse", fluid="green", tool="net", hero="Tess", sidekick="Kit", captain="Captain Mira"),
    StoryParams(place=MODULES["cargo"].place, module="cargo", fluid="clear", tool="towel", hero="Nico", sidekick="Sol", captain="Captain Vega"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible stories:\n")
        for m, f, t in stories:
            print(f"  {m:10} {f:8} {t}")
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(rng_base + i))
            except StoryError as e:
                print(e)
                return
            params.seed = rng_base + i
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
