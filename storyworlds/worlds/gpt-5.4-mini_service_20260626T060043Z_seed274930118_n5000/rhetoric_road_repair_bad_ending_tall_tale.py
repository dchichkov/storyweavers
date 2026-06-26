#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rhetoric_road_repair_bad_ending_tall_tale.py
===============================================================================================================

A small tall-tale storyworld about a boastful road-repair crew, a slippery
washout, and a grand speech that cannot quite save the day.

Premise:
- A tiny road has split after a storm.
- The mayor wants the road repaired before evening.
- A loudmouthed foreman uses big rhetoric to rally the crew.

Turn:
- The crew brings timber, gravel, planks, and a mighty roller.
- Their first plan is too proud and not careful enough.
- The repair looks impressive, but the ground underneath is still weak.

Bad ending:
- The road gives way again before the last cart crosses.
- The crew can only promise a better repair tomorrow.
- The closing image proves the loss: the detour lanterns glow, and the road
  stays closed for the night.

This world models physical meters and emotional memes, with a reasonableness
gate ensuring the repair materials actually match the damage.
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

ROAD_DAMAGE_TYPES = {"pothole", "washout", "crack", "sinkhole"}
REPAIR_MATERIALS = {"gravel", "planks", "timber", "patch"}
CREW_TYPES = ["foreman", "worker", "driver", "helper"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "foreman", "driver", "worker", "helper"}
        female = {"woman", "girl", "mayor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Road:
    name: str
    place: str
    damage: str
    width: str
    danger: str
    repair_needed: str
    repair_material: str
    repair_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    road: str
    tool: str
    crew: str
    hero_name: str
    hero_type: str
    mayor_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, road: Road):
        self.road = road
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
        import copy as _copy
        c = World(self.road)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _threshold(v: float) -> bool:
    return v >= 1.0


def road_at_risk(road: Road, tool: Tool) -> bool:
    return road.damage in tool.helps


def select_tool(road: Road, tool: Tool) -> bool:
    return road.damage in tool.helps and road.repair_needed in tool.covers


def _tell_boast(world: World, foreman: Entity) -> None:
    world.say(
        f"{foreman.label} had a voice like a brass trumpet and a tongue full of rhetoric."
    )
    world.say(
        f"{foreman.pronoun('subject').capitalize()} swore {foreman.pronoun('possessive')} crew could mend "
        f"{world.road.name} before the moon rose over {world.road.place}."
    )


def _tell_damage(world: World) -> None:
    r = world.road
    world.say(
        f"After the storm, {r.name} at {r.place} had a {r.damage} the size of a wagon wheel."
    )
    world.say(
        f"Every cart had to creep around it, because the {r.width} road was not safe to trust."
    )


def _load_tools(world: World, tool: Tool, crew: Entity) -> None:
    crew.carries.append(tool.id)
    world.say(
        f"The crew rolled in with {tool.phrase}, and the whole lane looked ready for a grand fix."
    )


def _work(world: World, foreman: Entity, tool: Tool) -> None:
    world.say(
        f"{foreman.label} pointed at the hole and talked so big that even the crows listened."
    )
    world.say(
        f"{foreman.pronoun('subject').capitalize()} said the road would be stronger than an oak tree by supper."
    )


def _apply_repair(world: World, foreman: Entity, tool: Tool) -> None:
    road = world.road
    if not select_tool(road, tool):
        return
    world.say(
        f"They shoved in {tool.label} and packed it down with gravel until the scar looked neat."
    )
    road.tags.add("patched")
    foreman.memes["hope"] = foreman.memes.get("hope", 0.0) + 1.0


def _bad_end(world: World, mayor: Entity, foreman: Entity, tool: Tool) -> None:
    road = world.road
    road.meters = getattr(road, "meters", {})
    road_state = road.__dict__.setdefault("meters", {})
    road_state["weak"] = road_state.get("weak", 0.0) + 1.0
    world.say(
        f"But the ground under the patch was still soft, and the whole road gave a tired groan."
    )
    world.say(
        f"Before the last cart reached the middle, {road.name} sank again with a sad splash of mud."
    )
    foreman.memes["pride"] = foreman.memes.get("pride", 0.0) + 1.0
    foreman.memes["trouble"] = foreman.memes.get("trouble", 0.0) + 1.0
    mayor.memes["worry"] = mayor.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{mayor.label} sighed and said the road would have to stay closed until morning."
    )
    world.say(
        f"By dusk, the lanterns glowed on the detour, and {world.road.name} was still a broken ribbon in the dark."
    )


def tell(road: Road, tool: Tool, crew_name: str, hero_name: str, hero_type: str, mayor_type: str) -> World:
    world = World(road)
    foreman = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mayor = world.add(Entity(id="Mayor", kind="character", type=mayor_type, label="the mayor"))
    crew = world.add(Entity(id=crew_name, kind="character", type="helper", label="the crew"))

    _tell_damage(world)
    world.para()
    _tell_boast(world, foreman)
    _load_tools(world, tool, crew)
    _work(world, foreman, tool)
    _apply_repair(world, foreman, tool)

    world.para()
    _bad_end(world, mayor, foreman, tool)

    world.facts.update(
        foreman=foreman,
        mayor=mayor,
        crew=crew,
        tool=tool,
        road=road,
        repaired=road.tags.__contains__("patched"),
        failed=True,
    )
    return world


SETTINGS = {
    "main_road": Road(
        name="Main Road",
        place="Hollow Creek",
        damage="washout",
        width="narrow",
        danger="slippery",
        repair_needed="washout",
        repair_material="timber",
        repair_action="bridge over the washout",
        tags={"road", "washout"},
    ),
    "ridge_road": Road(
        name="Ridge Road",
        place="Boulder Hill",
        damage="crack",
        width="curvy",
        danger="dusty",
        repair_needed="crack",
        repair_material="patch",
        repair_action="seal the crack",
        tags={"road", "crack"},
    ),
    "mill_lane": Road(
        name="Mill Lane",
        place="Apple Ford",
        damage="pothole",
        width="old",
        danger="bumpy",
        repair_needed="pothole",
        repair_material="gravel",
        repair_action="fill the pothole",
        tags={"road", "pothole"},
    ),
    "south_track": Road(
        name="South Track",
        place="Mossy Bend",
        damage="sinkhole",
        width="muddy",
        danger="soft",
        repair_needed="sinkhole",
        repair_material="planks",
        repair_action="cover the sinkhole",
        tags={"road", "sinkhole"},
    ),
}

TOOLS = {
    "timber": Tool(
        id="timber",
        label="a stack of stout timber beams",
        helps={"washout", "sinkhole"},
        covers={"timber"},
        phrase="a stack of stout timber beams",
        tags={"timber", "road"},
    ),
    "gravel": Tool(
        id="gravel",
        label="a cart full of gravel",
        helps={"pothole"},
        covers={"gravel"},
        phrase="a cart full of gravel",
        tags={"gravel", "road"},
    ),
    "planks": Tool(
        id="planks",
        label="long bridge planks",
        helps={"sinkhole", "washout"},
        covers={"planks"},
        phrase="long bridge planks",
        tags={"planks", "road"},
    ),
    "patch": Tool(
        id="patch",
        label="sticky patch cloth",
        helps={"crack"},
        covers={"patch"},
        phrase="sticky patch cloth",
        tags={"patch", "road"},
    ),
}

NAMES = ["Bram", "Ivy", "Nell", "Otis", "Pia", "Rook", "June", "Milo"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for rid, road in SETTINGS.items():
        for tid, tool in TOOLS.items():
            if road_at_risk(road, tool) and select_tool(road, tool):
                out.append((rid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale road repair storyworld with a bad ending.")
    ap.add_argument("--road", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--crew")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mayor", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.road is None or c[0] == args.road)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid road-and-tool combination matches the given options.)")
    road_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES)
    mayor_type = args.mayor or rng.choice(["woman", "man"])
    crew = args.crew or "Crew"
    return StoryParams(
        road=road_id,
        tool=tool_id,
        crew=crew,
        hero_name=hero_name,
        hero_type="foreman" if gender == "boy" else "foreman",
        mayor_type=mayor_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.road],
        TOOLS[params.tool],
        params.crew,
        params.hero_name,
        params.hero_type,
        params.mayor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    r = world.road
    return [
        f"Write a tall tale about a road repair at {r.place} and include the word 'rhetoric'.",
        f"Tell a child-friendly story where a boastful foreman tries to fix {r.name} but the ending goes badly.",
        f"Create a short story about a crew repairing a {r.damage} on a road, with a bad ending and a big speech.",
    ]


def story_qa(world: World) -> list[QAItem]:
    r = world.road
    foreman = world.facts["foreman"]
    mayor = world.facts["mayor"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"What was broken on {r.name} at {r.place}?",
            answer=f"{r.name} had a {r.damage}, so carts had to go around it.",
        ),
        QAItem(
            question=f"What did {foreman.label} use to try to fix the road?",
            answer=f"{foreman.label} and the crew used {tool.label} to try to repair the road.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The crew made the patch look neat, but the ground underneath was still soft. "
                f"The road sank again, and {mayor.label} had to close it until morning."
            ),
        ),
        QAItem(
            question=f"How did the foreman talk to the crew?",
            answer="He talked in huge rhetoric, like a trumpet with boots on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is road repair?",
            answer="Road repair is work done to fix broken roads, smooth bumps, and make travel safer again.",
        ),
        QAItem(
            question="What does rhetoric mean?",
            answer="Rhetoric is fancy or powerful speech used to persuade people or make a point strongly.",
        ),
        QAItem(
            question="Why do people put gravel in a pothole?",
            answer="Gravel helps fill low spots and makes the road flatter so wheels do not bump so hard.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}): meters={e.meters} memes={e.memes}")
    lines.append(f"  road: {world.road.__dict__}")
    return "\n".join(lines)


CURATED = [
    StoryParams(road="main_road", tool="timber", crew="Crew", hero_name="Bram", hero_type="foreman", mayor_type="woman"),
    StoryParams(road="mill_lane", tool="gravel", crew="Crew", hero_name="Ivy", hero_type="foreman", mayor_type="man"),
    StoryParams(road="south_track", tool="planks", crew="Crew", hero_name="Nell", hero_type="foreman", mayor_type="woman"),
]


ASP_RULES = r"""
road(R) :- road_name(R).
tool(T) :- tool_name(T).
at_risk(R,T) :- road_damage(R,D), helps(T,D).
valid(R,T) :- at_risk(R,T), covers(T,C), road_need(R,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, road in SETTINGS.items():
        lines.append(asp.fact("road_name", rid))
        lines.append(asp.fact("road_damage", rid, road.damage))
        lines.append(asp.fact("road_need", rid, road.repair_material))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_name", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible road-repair combos:\n")
        for road, tool in combos:
            print(f"  {road:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.road} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
