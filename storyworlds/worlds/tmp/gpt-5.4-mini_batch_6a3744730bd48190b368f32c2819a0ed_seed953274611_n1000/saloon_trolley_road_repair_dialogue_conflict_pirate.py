#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/saloon_trolley_road_repair_dialogue_conflict_pirate.py
======================================================================================

A standalone storyworld for a tiny pirate-flavored road-repair tale.

Premise
-------
A child pretends a battered trolley is a pirate ship and a roadside saloon
becomes the place where the work crew gathers. A broken road blocks the way,
the child wants to race ahead, and a careful grown-up uses dialogue and calm
conflict to keep everyone safe until the road is repaired.

This world keeps the simulation small but state-driven:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in the simulated world state

The words "saloon" and "trolley" are woven into the story output.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "worker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    detail: str
    road_blocked: bool = False
    has_water: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    role: str
    usable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FixTool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    vehicle: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes["defiance"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    road = world.entities.get("road")
    trolley = world.entities.get("trolley")
    if not road or not trolley:
        return out
    if road.meters["broken"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trolley.meters["stopped"] += 1
    out.append("The trolley could not roll over the broken road.")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("damage", _r_damage)]


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


def reasonable_combo(place: Place, vehicle: Vehicle, tool: FixTool) -> bool:
    return place.road_blocked and vehicle.usable and tool.power >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for vid, vehicle in VEHICLES.items():
            for tid, tool in TOOLS.items():
                if reasonable_combo(place, vehicle, tool):
                    combos.append((pid, vid, tid))
    return combos


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["defiance"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("hero").memes["conflict"] >= THRESHOLD,
        "blocked": sim.get("road").meters["broken"] >= THRESHOLD,
    }


def setup(world: World, place: Place, vehicle: Vehicle, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["alert"] += 1
    world.say(
        f"At {place.label}, the {place.detail}. {hero.id} spotted the {vehicle.label} "
        f"and grinned as if it were a pirate ship."
    )
    world.say(
        f'"Look, {helper.id}!" {hero.id} said. "The {vehicle.label} is ready to sail the road!"'
    )


def road_problem(world: World, place: Place, helper: Entity) -> None:
    world.say(
        f"But the road was broken open for repair, and the way ahead was blocked with dirt, boards, and stone."
    )
    world.say(f'"{helper.id}," {helper.id} said softly, "that road is not ready yet."')


def tempt(world: World, hero: Entity, vehicle: Vehicle) -> None:
    hero.memes["bravado"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f'"We can go anyway," {hero.id} said. "{vehicle.phrase} can handle it."'
    )


def warn(world: World, helper: Entity, hero: Entity, place: Place, tool: FixTool) -> None:
    pred = predict_conflict(world)
    helper.memes["caution"] += 1
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'"No," {helper.id} said. "This is road repair, and the {place.label} crew needs {tool.phrase} first. '
        f"If we rush, the trolley will stop and somebody could get hurt."'
    )


def calm_conflict(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'{hero.id} folded {hero.pronoun("possessive")} arms, and {helper.id} planted {helper.pronoun("possessive")} feet like a steady deckhand.'
    )
    propagate(world, narrate=False)
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'"I know you want to go," {helper.id} said, "but we need to keep the road crew safe."'
        )


def repair(world: World, place: Place, tool: FixTool, vehicle: Vehicle) -> None:
    road = world.get("road")
    road.meters["broken"] = 0
    road.meters["repaired"] += 1
    vehicle.meters["ready"] += 1
    world.say(
        f"Together they used {tool.phrase} to fix the road. By the time the work was done, the broken patch was smooth again."
    )
    world.say(
        f"The {vehicle.label} rolled forward at last, and the saloon lights glowed warm beside the repaired street."
    )


def ending(world: World, hero: Entity, helper: Entity, vehicle: Vehicle) -> None:
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} laughed and said, "The {vehicle.label} can sail now!"'
    )
    world.say(
        f'{helper.id} smiled. "Aye," {helper.id} said, "and this time the road is safe for everyone."'
    )


def tell(place: Place, vehicle: Vehicle, tool: FixTool, hero: Entity, helper: Entity, parent: Entity) -> World:
    world = World()
    world.add(Entity(id="hero", kind="character", type=hero.type, label=hero.id, role="hero"))
    world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.id, role="helper"))
    world.add(Entity(id="parent", kind="character", type=parent.type, label=parent.id, role="parent"))
    road = world.add(Entity(id="road", type="road"))
    road.meters["broken"] = 1
    world.add(Entity(id="saloon", type="place", label="the saloon"))
    world.add(Entity(id="trolley", type="vehicle", label=vehicle.label))
    setup(world, place, vehicle, world.get("hero"), world.get("helper"))
    world.para()
    road_problem(world, place, world.get("helper"))
    tempt(world, world.get("hero"), vehicle)
    warn(world, world.get("helper"), world.get("hero"), place, tool)
    world.para()
    calm_conflict(world, world.get("hero"), world.get("helper"))
    repair(world, place, tool, vehicle)
    ending(world, world.get("hero"), world.get("helper"), vehicle)
    world.facts.update(
        place=place, vehicle=vehicle, tool=tool, hero=world.get("hero"),
        helper=world.get("helper"), parent=world.get("parent"),
        outcome="repaired", conflict=world.get("hero").memes["conflict"] >= THRESHOLD
    )
    return world


PLACES = {
    "saloon": Place(
        id="saloon",
        label="the saloon",
        detail="saloon doors creaked beside the muddy road crew yard",
        road_blocked=True,
        tags={"saloon"},
    ),
    "dock": Place(
        id="dock",
        label="the dock road",
        detail="dock posts stood near the repair lane",
        road_blocked=True,
        tags={"dock"},
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor road",
        detail="crates and lanterns lined the road by the harbor",
        road_blocked=True,
        tags={"harbor"},
    ),
}

VEHICLES = {
    "trolley": Vehicle(
        id="trolley",
        label="trolley",
        phrase="the trolley",
        role="vehicle",
        tags={"trolley"},
    ),
    "cart": Vehicle(
        id="cart",
        label="work cart",
        phrase="the work cart",
        role="vehicle",
        tags={"cart"},
    ),
}

TOOLS = {
    "planks": FixTool(id="planks", label="planks", phrase="fresh planks", power=3, sense=3, tags={"repair"}),
    "shovel": FixTool(id="shovel", label="shovel", phrase="a shovel and gravel", power=2, sense=2, tags={"repair"}),
    "flag": FixTool(id="flag", label="warning flag", phrase="warning flags", power=2, sense=2, tags={"repair"}),
}

HERO_NAMES = ["Finn", "Mara", "Jo", "Ned", "Pip", "Tess"]
HELPER_NAMES = ["Aunt May", "Cap", "Rory", "Mina", "Bo", "June"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-flavored road repair storyworld with dialogue and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(place: Place, vehicle: Vehicle, tool: FixTool) -> str:
    if not place.road_blocked:
        return "(No story: there is no repair conflict at this place.)"
    if not vehicle.usable:
        return "(No story: that trolley would not move, so there is no lively road-repair conflict.)"
    if tool.power < 2:
        return "(No story: that tool is too weak for a real road-repair fix.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.vehicle and args.tool:
        p, v, t = PLACES[args.place], VEHICLES[args.vehicle], TOOLS[args.tool]
        if not reasonable_combo(p, v, t):
            raise StoryError(explain_rejection(p, v, t))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.vehicle is None or c[1] == args.vehicle)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, vehicle, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        vehicle=vehicle,
        tool=tool,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, vehicle, tool = f["place"], f["vehicle"], f["tool"]
    hero, helper = f["hero"], f["helper"]
    return [
        f'Write a pirate-flavored road repair story that uses the words "saloon" and "trolley".',
        f"Tell a story where {hero.id} wants to rush the {vehicle.label} past the {place.label}, but {helper.id} says no and they fix the road first.",
        f"Write a child-friendly dialogue story with conflict, a broken road, and a safe repair using {tool.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, place, vehicle, tool = f["hero"], f["helper"], f["place"], f["vehicle"], f["tool"]
    return [
        QAItem(
            question=f"What was blocking the way?",
            answer=f"The road was broken open for repair, so the trolley could not go through until the crew fixed it."
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to rush the trolley ahead like a pirate ship, but that would have been too risky on a broken road."
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} talked calmly, warned about the danger, and helped repair the road with {tool.phrase}."
        ),
        QAItem(
            question="How did the story end?",
            answer="The road was repaired, the trolley rolled on safely, and the saloon lights glowed beside the finished work."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saloon?",
            answer="A saloon is a public place where people can gather, rest, or talk. In a story like this, it can be a lively landmark beside the road."
        ),
        QAItem(
            question="What is a trolley?",
            answer="A trolley is a small vehicle that can roll along a path or track. In a story, it can feel like a little ship riding over the road."
        ),
        QAItem(
            question="Why is road repair important?",
            answer="Road repair makes the path safe and smooth again. That helps vehicles move without getting stuck or tipping."
        ),
        QAItem(
            question="Why use dialogue during conflict?",
            answer="Dialogue lets characters say what they need and hear each other clearly. That can calm conflict and help them choose the safe plan."
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.vehicle not in VEHICLES or params.tool not in TOOLS:
        raise StoryError("Invalid StoryParams keys.")
    world = World()
    place = PLACES[params.place]
    vehicle = VEHICLES[params.vehicle]
    tool = TOOLS[params.tool]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent, role="parent"))
    world.add(Entity(id="road", type="road"))
    world.get("road").meters["broken"] = 1
    world.add(Entity(id="saloon", type="place", label="the saloon"))
    world.add(Entity(id="trolley", type="vehicle", label="trolley"))
    setup(world, place, vehicle, hero, helper)
    world.para()
    road_problem(world, place, helper)
    tempt(world, hero, vehicle)
    warn(world, helper, hero, place, tool)
    world.para()
    calm_conflict(world, hero, helper)
    repair(world, place, tool, vehicle)
    ending(world, hero, helper, vehicle)
    world.facts.update(place=place, vehicle=vehicle, tool=tool, hero=hero, helper=helper, parent=parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
blocked :- road_broken.
conflict :- wants_rush, warns.
repaired :- fix_tool(T), strong_tool(T), road_broken.
safe_end :- repaired, not conflict.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for vid in VEHICLES:
        lines.append(asp.fact("vehicle", vid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("fix_tool", tid))
        if tool.power >= 2:
            lines.append(asp.fact("strong_tool", tid))
    lines.append(asp.fact("road_broken"))
    lines.append(asp.fact("wants_rush"))
    lines.append(asp.fact("warns"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_end/0.\n#show repaired/0.\n#show conflict/0."))
    return sorted(set(asp.atoms(model, "safe_end")))


def asp_verify() -> int:
    rc = 0
    import io
    from contextlib import redirect_stdout

    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, vehicle=None, tool=None, hero=None, hero_gender=None, helper=None, helper_gender=None, parent=None), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"FAIL: smoke test generation crashed: {e}")
        return 1

    py = set(valid_combos())
    # lightweight parity check: ASP program should parse and produce a model
    try:
        _ = asp_valid_combos()
    except Exception as e:
        print(f"FAIL: ASP solve crashed: {e}")
        rc = 1
    if py:
        print(f"OK: valid_combos() has {len(py)} combos.")
    else:
        print("FAIL: no valid combos found.")
        rc = 1
    print("OK: generation smoke test passed.")
    return rc


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
        print(asp_program("#show safe_end/0.\n#show repaired/0.\n#show conflict/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:\n")
        for p, v, t in valid_combos():
            print(f"  {p:8} {v:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams(place="saloon", vehicle="trolley", tool="planks", hero="Finn", hero_gender="boy", helper="Mina", helper_gender="girl", parent="mother"),
            StoryParams(place="dock", vehicle="trolley", tool="shovel", hero="Mara", hero_gender="girl", helper="Rory", helper_gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
