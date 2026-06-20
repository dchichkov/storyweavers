#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lasso_pivot_rhyme_teamwork_pirate_tale.py
==========================================================================

A small pirate-tale storyworld about two children on a dockside adventure.
They need to rescue a snagged kite-sail and the ship's map chest using a
lasso, a pivoting boat hook, rhyme, and teamwork.

The world is intentionally tiny:
- one premise: a pirate play scene at the harbor
- one tension: something is stuck out of reach
- one turn: the children coordinate with a rhyme and a pivoting tool
- one ending: the rescue changes the world state and proves the teamwork worked

The storyworld contract requires:
- typed entities with physical meters and emotional memes
- a reasonableness gate
- a Python gate plus inline ASP twin
- generation, QA, trace, JSON, and verify modes
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HarborScene:
    id: str
    place: str
    dock: str
    breeze: str
    pirate_frame: str
    goal: str
    rhyme_seed: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    makes_risk: bool = False
    pivoting: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    stuck_reason: str
    reach: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    phrase: str
    fail_phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    sail = world.get("sail")
    if sail.meters["snagged"] >= THRESHOLD and "risk" not in world.fired:
        world.fired.add(("risk",))
        for kid in (world.get("captain_kid"), world.get("mate_kid")):
            kid.memes["worry"] += 1
        world.get("ship").meters["stuck"] += 1
        out.append("__risk__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    cap = world.get("captain_kid")
    mate = world.get("mate_kid")
    if cap.memes["call"] >= THRESHOLD and mate.memes["answer"] >= THRESHOLD:
        if ("teamwork",) not in world.fired:
            world.fired.add(("teamwork",))
            cap.memes["joy"] += 1
            mate.memes["joy"] += 1
            world.get("crew").meters["cooperation"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("risk", "physical", _r_risk),
    Rule("teamwork", "social", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(tool: Tool, hazard: Hazard) -> bool:
    return tool.makes_risk and hazard.risky


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def can_rescue(fix: Fix, hazard: Hazard) -> bool:
    return fix.power >= 1


def predict(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_lasso(sim, sim.get(hazard_id), narrate=False)
    return {
        "snagged": sim.get(hazard_id).meters["snagged"] >= THRESHOLD,
        "stuck": sim.get("ship").meters["stuck"] >= THRESHOLD,
    }


def _do_lasso(world: World, hazard: Entity, narrate: bool = True) -> None:
    hazard.meters["snagged"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, a: Entity, b: Entity, scene: HarborScene) -> None:
    world.say(
        f"On a bright harbor day, {a.id} and {b.id} turned the dock into {scene.place}. "
        f"{scene.pirate_frame}"
    )
    world.say(
        f"They grinned at the {scene.goal} and hummed a little rhyme: "
        f"'{scene.rhyme_seed}.'"
    )


def need_help(world: World, a: Entity, hazard: Hazard) -> None:
    world.say(
        f"But the {hazard.label} was caught up high, right where the breeze kept tugging it. "
        f"{a.id} could not reach it alone."
    )
    a.memes["want"] += 1


def tempt(world: World, a: Entity, tool: Tool) -> None:
    a.memes["bold"] += 1
    world.say(
        f'{a.id} pointed at the {tool.label}. "I know! We can use the {tool.label} for this," '
        f"{a.pronoun()} said."
    )


def warn(world: World, b: Entity, tool: Tool, hazard: Hazard) -> None:
    b.memes["care"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "Not by itself," '
        f"{b.pronoun()} said. "The {hazard.label} needs a smart pull, not a wild tug."'
    )


def defy(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Then let\'s try it our way," {a.id} said, but {b.id} stayed close and did not give up.'
    )


def solve(world: World, a: Entity, b: Entity, tool: Tool, hazard: Hazard) -> None:
    a.memes["call"] += 1
    b.memes["answer"] += 1
    prop = "pivot" if tool.pivoting else "pull"
    world.say(
        f'They counted together -- "one, two, three!" -- and {a.id} sent the lasso in a neat arc. '
        f'{b.id} used the {tool.label} to {prop} just enough to guide it.'
    )
    propagate(world, narrate=False)
    world.say(
        f'The rope caught the {hazard.label}, the hook turned, and the snag came free with a soft snap.'
    )


def ending(world: World, a: Entity, b: Entity, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f'Then the {hazard.label} slid safe into the deck basket, and the ship was ready again. '
        f"{a.id} and {b.id} laughed, proud that teamwork and a rhyme had done the trick."
    )
    world.say(
        "The sea breeze fluttered the deck flag, and the little pirates sailed on with clean hands and big smiles."
    )


def tell(scene: HarborScene, tool: Tool, hazard: Hazard, fix: Fix,
         captain_name: str = "Mina", captain_gender: str = "girl",
         mate_name: str = "Owen", mate_gender: str = "boy",
         captain_trait: str = "bright", mate_trait: str = "steady") -> World:
    world = World()
    captain = world.add(Entity("captain_kid", kind="character", type=captain_gender, traits=[captain_trait], role="captain"))
    mate = world.add(Entity("mate_kid", kind="character", type=mate_gender, traits=[mate_trait], role="mate"))
    ship = world.add(Entity("ship", type="thing", label="ship"))
    crew = world.add(Entity("crew", type="thing", label="crew"))
    sail = world.add(Entity("sail", type="thing", label=hazard.label))
    world.facts["scene"] = scene
    world.facts["tool"] = tool
    world.facts["hazard"] = hazard
    world.facts["fix"] = fix
    world.facts["captain_name"] = captain_name
    world.facts["mate_name"] = mate_name
    world.facts["captain_gender"] = captain_gender
    world.facts["mate_gender"] = mate_gender

    captain.id = captain_name
    mate.id = mate_name
    world.entities[captain.id] = world.entities.pop("captain_kid")
    world.entities[mate.id] = world.entities.pop("mate_kid")
    world.entities[captain.id].id = captain.id
    world.entities[mate.id].id = mate.id

    intro(world, world.get(captain.id), world.get(mate.id), scene)
    world.para()
    need_help(world, world.get(captain.id), hazard)
    tempt(world, world.get(captain.id), tool)
    warn(world, world.get(mate.id), tool, hazard)
    defy(world, world.get(captain.id), world.get(mate.id), tool)
    world.para()
    solve(world, world.get(captain.id), world.get(mate.id), tool, hazard)
    ending(world, world.get(captain.id), world.get(mate.id), hazard)
    world.facts.update(
        captain=world.get(captain.id),
        mate=world.get(mate.id),
        ship=ship,
        crew=crew,
        sail=sail,
        outcome="fixed",
    )
    return world


SCENES = {
    "dock": HarborScene(
        "dock",
        "a dockside pirate game",
        "The plank was their ship's deck, a crate was a treasure chest, and a striped cloth became a pirate sail.",
        "They tapped a drum made from a bucket and cheered for the windy sea.",
        "the lost map chest",
        "lasso, pivot, and teamwork",
    ),
    "cove": HarborScene(
        "cove",
        "a tiny cove adventure",
        "The stones were a harbor fort, a rope coil was a secret trail, and a blue towel became a brave flag.",
        "They saluted the gulls and sang a bouncy sea tune.",
        "the ribbon sail",
        "lasso, pivot, and teamwork",
    ),
}

TOOLS = {
    "lasso": Tool("lasso", "lasso", "a lasso", "lasso", makes_risk=True, pivoting=False, tags={"lasso", "rope"}),
    "hook": Tool("hook", "boat hook", "a boat hook", "pivot", makes_risk=False, pivoting=True, tags={"pivot", "hook"}),
    "line": Tool("line", "rope line", "a rope line", "pull", makes_risk=False, pivoting=False, tags={"rope"}),
}

HAZARDS = {
    "sail": Hazard("sail", "sail", "the sail", "it was snagged on a mast ring", "high on the line", tags={"sail"}),
    "chest": Hazard("chest", "map chest", "the map chest", "it was wedged behind a crate", "under the rail", tags={"chest"}),
}

FIXES = {
    "rhyme": Fix("rhyme", 3, 1, "used a rhyme to count their moves", "tried to rhyme, but the pull was not enough", tags={"rhyme"}),
    "teamwork": Fix("teamwork", 3, 2, "worked together and solved it as a team", "worked together, but the snag would not budge", tags={"teamwork"}),
    "pivot": Fix("pivot", 2, 2, "pivoted the hook and eased the rope into place", "pivoted too late and the rope slipped back", tags={"pivot"}),
}

CURATED = [
    dataclass(type("StoryParams", (), {}))
]


@dataclass
class StoryParams:
    scene: str
    tool: str
    hazard: str
    fix: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SCENES:
        for t in TOOLS:
            for h in HAZARDS:
                for f in FIXES:
                    if t == "lasso" and h in {"sail", "chest"} and f in {"rhyme", "teamwork", "pivot"}:
                        out.append((s, t, h, f))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld with lasso, pivot, rhyme, and teamwork.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.tool and args.tool == "lasso" and args.fix == "pivot" and not hazard_at_risk(TOOLS["lasso"], HAZARDS["sail"]):
        raise StoryError("Invalid pirate tale: the lasso must actually create a snag to solve.")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in combos if (args.scene is None or c[0] == args.scene) and (args.tool is None or c[1] == args.tool) and (args.hazard is None or c[2] == args.hazard) and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, tool, hazard, fix = rng.choice(combos)
    return StoryParams(scene, tool, hazard, fix, args.captain_name or "Mina", args.captain_gender or "girl", args.mate_name or "Owen", args.mate_gender or "boy")


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    tool = TOOLS[params.tool]
    hazard = HAZARDS[params.hazard]
    fix = FIXES[params.fix]
    world = World()
    # tell() does the full story build
    world = tell(scene, tool, hazard, fix, params.captain_name, params.captain_gender, params.mate_name, params.mate_gender)
    prompts = [
        f"Write a pirate tale for a child that includes the words lasso and pivot and shows teamwork and a rhyme.",
        f"Tell a short harbor adventure where two kids use a lasso, pivot a hook, and work together to free a snagged pirate thing.",
        f"Write a story with a cheerful pirate rhythm where a problem is solved by rhyme, teamwork, and a careful pivot.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the children face?",
            answer=f"The {hazard.label} was stuck high up or wedged in place, so the children could not reach it alone. That is why they needed to use a lasso and then pivot their tool carefully."
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"One child threw the lasso while the other helped pivot the hook and count the beat. Working together made the pull steady instead of wild, and that freed the snag safely."
        ),
    ]
    world_qa = [
        QAItem("What is a lasso?", "A lasso is a looped rope used to catch or pull something from farther away."),
        QAItem("What does pivot mean?", "To pivot means to turn around a point or swing into a new position so a tool can change direction."),
        QAItem("Why do rhymes help in teamwork?", "Rhymes can give everyone the same beat to follow. That makes it easier to move together at the right time."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F) :- tool(F), makes_risk(F).
valid(S,T,H,X) :- scene(S), tool(T), hazard(H), fix(X), T = lasso, H = sail.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if tool.makes_risk:
            lines.append(asp.fact("makes_risk", t))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: default generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{c}" for c in asp_valid_combos()))
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, "Mina", "girl", "Owen", "boy")) for c in valid_combos()[:3]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
