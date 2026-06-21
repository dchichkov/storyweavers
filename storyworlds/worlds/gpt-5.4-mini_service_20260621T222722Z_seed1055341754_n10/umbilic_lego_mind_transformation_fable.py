#!/usr/bin/env python3
"""
storyworlds/worlds/umbilic_lego_mind_transformation_fable.py
============================================================

A small fable-style storyworld about a watchmaker's apprentice, a curious lego
bridge, and a whispered transformation that changes a mind more than a thing.

The seed words are woven into the world model:
- umbilic: the little central knot where the bridge's spokes meet
- lego: the toy blocks and the bridge built from them
- mind: the state that changes after the lesson
- Transformation: the feature that drives the plot
- Style: Fable

The story premise is simple: a child tries to make something clever from lego
blocks, learns that force is not the same as craft, and is transformed by a wise
helper into a calmer, steadier maker. The ending image proves the change by
showing what the child builds afterward.

This script follows the storyworld contract:
- standalone stdlib script
- imports results eagerly, asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates three Q&A sets from world state, not by parsing rendered English
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    feature: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Build:
    id: str
    label: str
    parts: str
    umbilic_name: str
    grows: str
    threatens: str
    finished_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Change:
    id: str
    sense: int
    power: int
    method: str
    failed: str
    lesson: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    build: str
    change: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "workshop": Setting(
        id="workshop",
        place="the little workshop",
        mood="warm with sawdust and daylight",
        feature="a wooden bench",
        tags={"workshop", "craft"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the old courtyard",
        mood="bright with wind and pigeons",
        feature="a low stone wall",
        tags={"courtyard", "outdoors"},
    ),
}

BUILDS = {
    "tower": Build(
        id="tower",
        label="lego tower",
        parts="a pile of red, blue, and gold bricks",
        umbilic_name="the umbilic knot",
        grows="rose higher and higher",
        threatens="leaned like a sleepy reed in the wind",
        finished_image="stood steady and tall, with the umbilic knot at its bright center",
        tags={"lego", "umbilic", "tower"},
    ),
    "bridge": Build(
        id="bridge",
        label="lego bridge",
        parts="a line of arching blocks and two square piers",
        umbilic_name="the umbilic stone",
        grows="spanned farther and farther",
        threatens="bent like a bow that had been pulled too hard",
        finished_image="arched cleanly across the gap, with the umbilic stone holding the middle",
        tags={"lego", "umbilic", "bridge"},
    ),
}

CHANGES = {
    "patience": Change(
        id="patience",
        sense=3,
        power=3,
        method="taught the child to pause, fit each brick, and let the shape settle",
        failed="tried to rush the bricks into place, but they kept slipping apart",
        lesson="showed that a calm mind can build what hurried hands cannot",
        tags={"mind", "transformation"},
    ),
    "listening": Change(
        id="listening",
        sense=3,
        power=2,
        method="asked the child to listen to the soft click of each brick and copy it",
        failed="asked the child to force the bricks, but the shape only wobbled more",
        lesson="showed that listening changes the mind before the hands move",
        tags={"mind", "transformation"},
    ),
    "gentle": Change(
        id="gentle",
        sense=2,
        power=2,
        method="showed how gentle hands and a steady breath could mend the crooked build",
        failed="used too much force, and the crooked bricks only grew worse",
        lesson="showed that gentleness can transform a stubborn mind",
        tags={"mind", "transformation"},
    ),
}

CHILDREN = [
    ("Mina", "girl"),
    ("Tomas", "boy"),
    ("Lila", "girl"),
    ("Nico", "boy"),
    ("Rosa", "girl"),
]

HELPERS = [
    ("Grandpa", "man"),
    ("Grandma", "woman"),
    ("The owl", "thing"),
]


class StoryReasoner:
    def __init__(self, params: StoryParams) -> None:
        self.params = params

    def valid(self) -> bool:
        return self.params.setting in SETTINGS and self.params.build in BUILDS and self.params.change in CHANGES

    def outcome(self) -> str:
        change = CHANGES[self.params.change]
        return "transformed" if change.power >= 2 else "unchanged"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BUILDS:
            for c in CHANGES:
                combos.append((s, b, c))
    return combos


def story_valid(params: StoryParams) -> bool:
    if params.setting not in SETTINGS or params.build not in BUILDS or params.change not in CHANGES:
        return False
    build = BUILDS[params.build]
    change = CHANGES[params.change]
    return "lego" in build.tags and "mind" in change.tags and "transformation" in change.tags


def _maybe_name(rng: random.Random, pool: list[tuple[str, str]]) -> tuple[str, str]:
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.build is None or c[1] == args.build)
              and (args.change is None or c[2] == args.change)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, build, change = rng.choice(sorted(combos))
    child, cg = _maybe_name(rng, CHILDREN)
    helper, hg = _maybe_name(rng, HELPERS)
    return StoryParams(
        setting=setting,
        build=build,
        change=change,
        child=child,
        child_gender=cg,
        helper=helper,
        helper_gender=hg,
    )


def init_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    world = World()
    setting = SETTINGS[params.setting]
    build = BUILDS[params.build]
    change = CHANGES[params.change]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="builder",
                             meters={"hope": 0.0}, memes={"pride": 1.0, "frustration": 0.0},
                             attrs={"setting": setting.id}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="teacher",
                              meters={"calm": 1.0}, memes={"wisdom": 2.0}))
    tower = world.add(Entity(id="build", type="thing", label=build.label, tags=set(build.tags),
                             meters={"lean": 0.0, "whole": 0.0}, memes={"wonder": 1.0}))
    mind = world.add(Entity(id="mind", type="thing", label="mind", tags={"mind"},
                            meters={"rigid": 1.0, "open": 0.0}, memes={"quiet": 0.0}))
    umbilic = world.add(Entity(id="umbilic", type="thing", label=build.umbilic_name, tags={"umbilic"},
                               meters={"steady": 0.0}, memes={"center": 1.0}))
    world.facts.update(setting=setting, build=build, change=change, child=child, helper=helper, tower=tower, mind=mind, umbilic=umbilic)
    return world, setting, build, change, child, helper


def predict_transformation(world: World, change: Change) -> dict:
    sim = world.copy()
    sim.get("mind").meters["open"] += change.power
    sim.get("mind").meters["rigid"] = max(0.0, sim.get("mind").meters["rigid"] - change.power)
    return {"transformed": sim.get("mind").meters["open"] >= THRESHOLD}


def tell(world: World, setting: Setting, build: Build, change: Change, child: Entity, helper: Entity) -> None:
    mind = world.get("mind")
    umbilic = world.get("umbilic")
    child.memes["joy"] += 1
    world.say(
        f"Once in {setting.place}, {child.id} found {build.parts} beside {setting.feature}. "
        f"The place was {setting.mood}, and the child wanted to make a {build.label}."
    )
    world.say(
        f"{child.id} stacked the bricks until {build.label} {build.grows}, but the middle wavered. "
        f"At the {umbilic.label}, the whole shape {build.threatens}."
    )
    world.para()
    child.memes["frustration"] += 1
    world.say(
        f"Then {helper.id} came near and smiled. '{child.id}, do not squeeze the bricks harder,' "
        f"{helper.pronoun()} said. '{change.method}.'"
    )
    pred = predict_transformation(world, change)
    world.facts["predicted_transformed"] = pred["transformed"]
    if pred["transformed"]:
        world.say(
            f"{child.id} listened. The child let the mind grow quieter, and each brick clicked home "
            f"as if it had been waiting for patience."
        )
        mind.meters["open"] += change.power
        mind.meters["rigid"] = max(0.0, mind.meters["rigid"] - change.power)
        umbilic.meters["steady"] += 1
        child.memes["frustration"] = 0.0
        child.memes["pride"] += 1
        world.para()
        world.say(
            f"By the end, {build.finished_image}. {change.lesson.capitalize()}, and "
            f"{child.id} built again with a calmer mind."
        )
        child.meters["hope"] += 1
    else:
        world.say(
            f"{child.id} tried to listen, but the bricks still buckled and the little mind stayed tight. "
            f"{change.failed.capitalize()}."
        )
        world.para()
        world.say(
            f"Still, {helper.id} stayed kind. The lesson was not finished, but the story had not yet given up on the child."
        )
    world.facts["outcome"] = "transformed" if mind.meters["open"] >= THRESHOLD else "stuck"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the words "umbilic", "lego", and "mind" and ends with a transformation.',
        f"Tell a quiet story where {f['child'].id} builds a {f['build'].label} from lego blocks, learns from {f['helper'].id}, and changes {f['child'].pronoun('possessive')} mind.",
        f"Write a small fable about patience in a workshop where a lego build becomes steadier at the umbilic and the builder is transformed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    build = f["build"]
    change = f["change"]
    qa = [
        QAItem(
            question=f"What was {child.id} trying to make?",
            answer=f"{child.id} was trying to make a {build.label} from lego bricks. The build mattered because the middle, the umbilic, had to hold the whole shape together.",
        ),
        QAItem(
            question=f"Why did {child.id} need help with the lego build?",
            answer=f"The bricks wobbled and the shape leaned, so {child.id} could not finish by pushing harder. {helper.id} helped by showing a calmer way, which gave {child.id}'s mind a better path to follow.",
        ),
        QAItem(
            question=f"What changed in {child.id}'s mind by the end?",
            answer=f"{child.id}'s mind became calmer and more open. That transformation made {child.id} able to build with patience instead of force.",
        ),
    ]
    if f.get("predicted_transformed"):
        qa.append(QAItem(
            question=f"How did {helper.id}'s advice help the story turn out?",
            answer=f"{helper.id} gave a method that worked, so {child.id} listened and the build grew steady. Because the mind changed first, the lego shape could finish in a good way.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are lego blocks?",
            answer="Lego blocks are small pieces that can fit together to build towers, bridges, houses, and many other shapes.",
        ),
        QAItem(
            question="What is a mind?",
            answer="A mind is the part of a person that thinks, learns, worries, and changes when it understands something new.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a big change from one state to another. In a story, it can mean a person learns something and becomes different inside.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_build(B) :- build(B).
valid_change(C) :- change(C).
valid(S,B,C) :- setting(S), build(B), change(C), has_lego(B), has_mind(C), has_transformation(C).
outcome(transformed) :- mind_open.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BUILDS.items():
        lines.append(asp.fact("build", bid))
        if "lego" in b.tags:
            lines.append(asp.fact("has_lego", bid))
    for cid, c in CHANGES.items():
        lines.append(asp.fact("change", cid))
        if "mind" in c.tags:
            lines.append(asp.fact("has_mind", cid))
        if "transformation" in c.tags:
            lines.append(asp.fact("has_transformation", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(StoryParams(setting="workshop", build="bridge", change="patience", child="Mina", child_gender="girl", helper="Grandma", helper_gender="woman"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced story text.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this combination does not support a believable transformation of the mind.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fable of lego, umbilic, mind, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--build", choices=BUILDS)
    ap.add_argument("--change", choices=CHANGES)
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


CURATED = [
    StoryParams(setting="workshop", build="tower", change="patience", child="Mina", child_gender="girl", helper="Grandma", helper_gender="woman"),
    StoryParams(setting="courtyard", build="bridge", change="listening", child="Tomas", child_gender="boy", helper="Grandpa", helper_gender="man"),
    StoryParams(setting="workshop", build="bridge", change="gentle", child="Rosa", child_gender="girl", helper="The owl", helper_gender="thing"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.build is None or c[1] == args.build)
              and (args.change is None or c[2] == args.change)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, build, change = rng.choice(sorted(combos))
    child, cg = rng.choice(CHILDREN)
    helper, hg = rng.choice(HELPERS)
    return StoryParams(setting=setting, build=build, change=change, child=child, child_gender=cg, helper=helper, helper_gender=hg)


def generate(params: StoryParams) -> StorySample:
    if not story_valid(params):
        raise StoryError(explain_rejection())
    world, setting, build, change, child, helper = init_world(params)
    tell(world, setting, build, change, child, helper)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, b, c in asp_valid_combos():
            print(f"  {s:10} {b:8} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
