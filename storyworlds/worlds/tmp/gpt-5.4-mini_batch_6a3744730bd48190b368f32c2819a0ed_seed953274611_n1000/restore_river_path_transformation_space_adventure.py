#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/restore_river_path_transformation_space_adventure.py
====================================================================================

A standalone storyworld for a small space-adventure tale set on a river path.

Premise:
- A child astronaut team follows a river-path trail on an alien moon.
- A broken trail-marker transformation device has turned the path muddy and dim.
- The team must restore the path by using the correct transformation process
  before their rover can cross.

The world is built around:
- physical meters: wetness, damage, brightness, restored, transformed
- emotional memes: worry, hope, pride, relief
- a concrete state change that drives the story, not a fixed paragraph swap
- an inline ASP twin and a Python reasonableness gate
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    scene: str
    path_name: str
    can_restore: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TransformationTool:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    damage_need: str
    wet_need: str
    restore_need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


PLACES = {
    "river_path": Place(
        id="river_path",
        label="the river path",
        scene="a silver river path beside glowing reeds",
        path_name="river path",
        can_restore=True,
        tags={"river", "path", "space"},
    ),
    "moon_dock": Place(
        id="moon_dock",
        label="the moon dock",
        scene="a moon dock with bright rails",
        path_name="dock path",
        can_restore=True,
        tags={"dock", "space"},
    ),
    "crater_bridge": Place(
        id="crater_bridge",
        label="the crater bridge",
        scene="a narrow bridge over a crater stream",
        path_name="bridge path",
        can_restore=True,
        tags={"bridge", "space"},
    ),
}

PROBLEMS = {
    "mud_slip": Problem(
        id="mud_slip",
        label="muddy track",
        phrase="a muddy track",
        damage_need="mud",
        wet_need="wet",
        restore_need="restore",
        severity=2,
        tags={"mud", "path"},
    ),
    "fog_glass": Problem(
        id="fog_glass",
        label="fogged beacon",
        phrase="a fogged beacon",
        damage_need="fog",
        wet_need="damp",
        restore_need="clear",
        severity=1,
        tags={"fog", "beacon"},
    ),
    "broken_tiles": Problem(
        id="broken_tiles",
        label="broken tiles",
        phrase="broken tiles",
        damage_need="cracked",
        wet_need="wet",
        restore_need="repair",
        severity=3,
        tags={"cracked", "tiles"},
    ),
}

TOOLS = {
    "sun_beam": TransformationTool(
        id="sun_beam",
        label="sun-beam prism",
        phrase="a sun-beam prism",
        method="turn the beam bright",
        power=1,
        sense=3,
        tags={"light", "restore"},
    ),
    "repair_glove": TransformationTool(
        id="repair_glove",
        label="repair glove",
        phrase="a repair glove",
        method="shape the path back into place",
        power=3,
        sense=3,
        tags={"repair", "restore"},
    ),
    "mender_dust": TransformationTool(
        id="mender_dust",
        label="mender dust",
        phrase="mender dust",
        method="restore the broken trail",
        power=2,
        sense=2,
        tags={"restore"},
    ),
}

HELPER_NAMES = ["Mia", "Nia", "Lio", "Tari", "Zed", "Nova", "Pip", "Kai"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for pr in PROBLEMS:
            for t in TOOLS:
                if PLACES[p].can_restore and "restore" in TOOLS[t].tags and PROBLEMS[pr].severity <= TOOLS[t].power + 1:
                    out.append((p, pr, t))
    return out


def _normalize_problem(problem: Problem) -> bool:
    return problem.restore_need == "restore"


def reasonableness_gate(place: Place, problem: Problem, tool: TransformationTool) -> bool:
    return place.can_restore and _normalize_problem(problem) and tool.sense >= 2 and tool.power >= 1


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if "restore" in PLACES[pid].tags:
            lines.append(asp.fact("restorable", pid))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
        lines.append(asp.fact("severity", pr, PROBLEMS[pr].severity))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("power", t, TOOLS[t].power))
        lines.append(asp.fact("sense", t, TOOLS[t].sense))
        if "restore" in TOOLS[t].tags:
            lines.append(asp.fact("restores", t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), restorable(P), restores(T), severity(Pr, S), power(T, Pwr), Pwr + 1 >= S.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class Rule:
    name: str
    apply: callable


def _r_restore(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["broken"] >= THRESHOLD and ("restore", e.id) not in world.fired:
            world.fired.add(("restore", e.id))
            e.meters["restored"] += 1
            e.meters["broken"] = 0.0
            out.append("__restored__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for rule in (Rule("restore", _r_restore),):
        produced.extend(rule.apply(world))
    if narrate:
        for s in produced:
            if s != "__restored__":
                world.say(s)
    return produced


def tell(place: Place, problem: Problem, tool: TransformationTool,
         helper: str = "Nova", helper_gender: str = "girl",
         parent: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Parent", kind="character", type=parent, role="parent", label=f"the {parent}"))
    path = world.add(Entity(id="path", type="path", label=place.label))
    device = world.add(Entity(id="device", type="tool", label=tool.label))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["parent"] = adult
    world.facts["path"] = path

    hero.memes["hope"] += 1
    world.say(
        f"{helper} and the {parent} were riding their little rover along {place.scene}. "
        f"Their map showed {problem.phrase} ahead, and the path looked too dim and broken."
    )
    world.say(
        f'"We can restore {place.path_name}," {helper} said. "{tool.method}!"'
    )

    world.para()
    hero.memes["worry"] += 1
    path.meters["broken"] += problem.severity
    path.meters["wet"] += 1
    path.meters["dark"] += 1
    world.say(
        f"But the river path had been chewed up by moon spray. {problem.label.capitalize()} made the ground slippery, "
        f"and the rover’s wheels began to slip."
    )
    world.say(
        f"The {parent} warned, " + f'"If we do not {problem.restore_need} it, we will have to turn back."'
    )

    world.para()
    if not reasonableness_gate(place, problem, tool):
        raise StoryError("That combination cannot make a sensible restore story.")

    hero.memes["pride"] += 1
    world.say(
        f"{helper} stepped forward with {tool.phrase}. At first it looked tiny beside the long river path, "
        f"but the tool was made for transformation."
    )
    path.meters["transformed"] += 1
    path.meters["brightness"] += 1
    path.meters["restored"] += 1
    world.say(
        f"{helper} used it to {tool.method}, and the muddy stretch changed back into a clear track."
    )
    propagate(world, narrate=False)
    world.say(
        f"The wet stones dried, the markers shone, and the rover rolled across safely."
    )

    world.para()
    hero.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"Then the {parent} smiled and nodded. “You restored the path,” {adult.pronoun()} said. "
        f"“That transformation helped everyone move again.”"
    )
    world.say(
        f"{helper} looked back at the river path, now bright and steady, and felt proud that the adventure could go on."
    )

    world.facts["outcome"] = "restored"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    problem: Problem = f["problem"]
    tool: TransformationTool = f["tool"]
    return [
        f'Write a space adventure story that includes the word "restore" and takes place on the {place.path_name}.',
        f"Tell a child-friendly story where {f['hero'].id} must restore the {place.path_name} by using {tool.label}.",
        f"Write a short story about a rover, a river path, and a transformation that repairs {problem.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    place: Place = f["place"]
    problem: Problem = f["problem"]
    tool: TransformationTool = f["tool"]
    path: Entity = f["path"]
    return [
        ("What was the story about?",
         f"It was about {hero.id} and {parent.label_word} trying to cross {place.label}. The path had {problem.phrase}, so they had to restore it first."),
        ("Why did they need the tool?",
         f"The river path was broken and slippery. {tool.label} could transform the damaged part back into a safe track."),
        ("How did the ending change the path?",
         f"The path became bright, dry enough to cross, and restored. The rover could roll forward again instead of stopping at the broken stretch."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does restore mean?",
         "Restore means to make something good, safe, or working again after it was damaged or broken."),
        ("What is a transformation?",
         "A transformation is a change from one state into another. In stories, it can mean a tool or action turns something broken into something useful again."),
        ("Why do rover teams check a path before crossing?",
         "They check a path so they do not get stuck or fall. A clear path helps the rover move safely through the adventure."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="river_path", problem="mud_slip", tool="repair_glove", helper="Nova", helper_gender="girl", parent="mother"),
    StoryParams(place="moon_dock", problem="fog_glass", tool="sun_beam", helper="Kai", helper_gender="boy", parent="father"),
    StoryParams(place="crater_bridge", problem="broken_tiles", tool="mender_dust", helper="Mia", helper_gender="girl", parent="mother"),
]


def explain_rejection(place: Place, problem: Problem, tool: TransformationTool) -> str:
    return f"(No story: {tool.label} is not a reasonable way to restore {problem.phrase} on {place.label}.)"


def outcome_of(params: StoryParams) -> str:
    return "restored"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    keys_p = list(PLACES)
    keys_pr = list(PROBLEMS)
    keys_t = list(TOOLS)
    p = args.place or rng.choice(keys_p)
    pr = args.problem or rng.choice(keys_pr)
    t = args.tool or rng.choice(keys_t)
    place = PLACES[p]
    problem = PROBLEMS[pr]
    tool = TOOLS[t]
    if not reasonableness_gate(place, problem, tool):
        raise StoryError(explain_rejection(place, problem, tool))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=p, problem=pr, tool=t, helper=helper, helper_gender=helper_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Unknown parameter value.")
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 helper=params.helper, helper_gender=params.helper_gender, parent=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about restoring a river path.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH:")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    return ok


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        if args.all:
            p = sample.params
            header = f"### {p.helper} restoring {p.place} with {p.tool}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
