#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/magnify_misunderstanding_rhyming_story.py
==============================================================================================================

A small Storyweavers world about a magnifying glass, a misunderstanding, and a
gentle rhyming-story style resolution.

The seed image:
- A child finds a magnifying glass.
- It makes something look bigger than it really is.
- A grownup misunderstands what the child thinks they saw.
- They talk it through, discover the mistake, and end kindly.

This file models the premise as state:
- A sighted object may be enlarged by a magnify tool.
- A child's belief may become incorrect if they only inspect the magnified view.
- A misunderstanding grows if one character's belief clashes with another's.
- A gentle explanation resolves the conflict.

The prose aims to feel like a tiny rhyming story without forcing every sentence
to rhyme; instead it uses a musical cadence, repetition, and simple end-rhymes.
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


THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    gives: str
    scale: float = 2.0


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    size: str
    if_seen_big: bool = False
    harmless: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_magnify(world: World) -> list[str]:
    out: list[str] = []
    viewer = world.facts.get("viewer")
    obj = world.facts.get("object")
    tool = world.facts.get("tool")
    if not viewer or not obj or not tool:
        return out
    sig = ("magnify", viewer.id, obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if viewer.memes.get("curiosity", 0.0) >= THRESHOLD:
        viewer.memes["wonder"] = viewer.memes.get("wonder", 0.0) + 1
    if obj.if_seen_big:
        obj.meters["apparent_size"] = obj.meters.get("apparent_size", 1.0) * tool.scale
        out.append(f"{viewer.id} looked through the {tool.label} and saw {obj.label} grow.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    child = world.facts.get("child")
    parent = world.facts.get("parent")
    obj = world.facts.get("object")
    if not child or not parent or not obj:
        return []
    sig = ("misunderstanding", child.id, parent.id, obj.id)
    if sig in world.fired:
        return []
    if child.memes.get("alarm", 0.0) >= THRESHOLD and parent.memes.get("puzzled", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1
        parent.memes["misunderstanding"] = parent.memes.get("misunderstanding", 0.0) + 1
        return ["__misunderstanding__"]
    return []


def _r_resolution(world: World) -> list[str]:
    child = world.facts.get("child")
    parent = world.facts.get("parent")
    obj = world.facts.get("object")
    if not child or not parent or not obj:
        return []
    sig = ("resolve", child.id, parent.id, obj.id)
    if sig in world.fired:
        return []
    if child.memes.get("understanding", 0.0) >= THRESHOLD and parent.memes.get("relief", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        return ["__resolution__"]
    return []


CAUSAL_RULES = [
    Rule("magnify", _r_magnify),
    Rule("misunderstanding", _r_misunderstanding),
    Rule("resolution", _r_resolution),
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
                for s in sents:
                    if s.startswith("__"):
                        continue
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyming_line(a: str, b: str) -> str:
    return f"{a} {b}"


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affordances={"look"}),
    "porch": Setting(place="the porch", indoors=False, affordances={"look"}),
    "playroom": Setting(place="the playroom", indoors=True, affordances={"look"}),
}

TOOLS = {
    "magnifying_glass": Tool(
        id="magnifying_glass",
        label="magnifying glass",
        verb="magnify",
        gives="a bigger view",
        scale=3.0,
    ),
    "lensed_toy": Tool(
        id="lensed_toy",
        label="little glass lens",
        verb="magnify",
        gives="a bigger peek",
        scale=2.5,
    ),
}

OBJECTS = {
    "ant": ObjectThing(
        id="ant",
        label="the ant",
        phrase="a tiny ant",
        size="tiny",
        if_seen_big=True,
        harmless=True,
    ),
    "leaf": ObjectThing(
        id="leaf",
        label="the leaf",
        phrase="a small leaf",
        size="small",
        if_seen_big=True,
        harmless=True,
    ),
    "button": ObjectThing(
        id="button",
        label="the button",
        phrase="a shiny button",
        size="small",
        if_seen_big=True,
        harmless=True,
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Sam"]
PARENT_NAMES = ["Mom", "Dad", "Mum", "Papa"]
TRAITS = ["curious", "bright", "silly", "sprightly", "gentle"]


@dataclass
class StoryParams:
    place: str
    tool: str
    object: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about magnifying and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["Mom", "Dad", "Mum", "Papa"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for tool in TOOLS:
            for obj in OBJECTS:
                combos.append((place, tool, obj))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a small thing that can be magnified and then misunderstood, so the choice must stay in that lane.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tool:
        combos = [c for c in combos if c[1] == args.tool]
    if args.object:
        combos = [c for c in combos if c[2] == args.object]
    if not combos:
        raise StoryError(explain_rejection())
    place, tool, obj = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, tool=tool, object=obj, name=name, parent=parent, trait=trait)


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a {next(t for t in child.memes if t == 'curiosity') if False else 'little'} {child.type} with a merry mind.")


def tell(setting: Setting, tool: Tool, obj: ObjectThing, name: str, parent_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent"))
    child.memes["curiosity"] = 1.0
    child.memes["alarm"] = 0.0
    child.memes["understanding"] = 0.0
    parent.memes["puzzled"] = 0.0
    parent.memes["relief"] = 0.0
    thing = world.add(Entity(id=obj.id, type="thing", label=obj.label, phrase=obj.phrase))
    thing.meters["apparent_size"] = 1.0
    world.facts.update(child=child, parent=parent, object=thing, tool=tool, trait=trait, setting=setting)

    world.say(f"{name} was a {trait} child who liked to roam and to know.")
    world.say(f"{name} found a {tool.label}, and said, \"What can this lens let me show?\"")
    world.say(f"At {setting.place}, {name} peered in near and far, with a hush and a glow.")
    world.para()
    world.say(f"{name} looked at {thing.label} through the {tool.label}, and the little thing grew.")
    child.memes["alarm"] = 1.0
    parent.memes["puzzled"] = 1.0
    world.say(f"{name} gasped, \"It's huge! It's not right! Oh, what shall I do?\"")
    propagate(world, narrate=False)
    world.para()
    world.say(f"{parent_name} came close and smiled at the sight.")
    world.say(f"\"That is only the lens trick,\" {parent_name} said. \"The view can be funny tonight.\"")
    child.memes["understanding"] = 1.0
    parent.memes["relief"] = 1.0
    propagate(world, narrate=False)
    world.say(f"{name} laughed, \"Oh, I see! It was small all along!\"")
    world.say(f"So they sat in the {setting.place.removeprefix('the ')} and sang a soft song: "
              f"small and tall, big and small, not all that you see is true at all.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a small child about a {f["trait"]} child who uses a magnifying glass.',
        f"Tell a gentle story where {f['child'].id} thinks a tiny thing is huge, but {f['parent'].id} explains the mistake kindly.",
        "Write a simple magnify-and-misunderstanding story with a musical, child-facing cadence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    thing = f["object"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} use to look closely at {thing.label}?",
            answer=f"{child.id} used a {tool.label} to look closely, and that made {thing.label} seem much bigger.",
        ),
        QAItem(
            question=f"Why did {child.id} get worried when looking through the lens?",
            answer=f"{child.id} got worried because the magnifying glass made {thing.label} look huge, and {child.id} did not understand the trick yet.",
        ),
        QAItem(
            question=f"How did {parent.id} help in the end?",
            answer=f"{parent.id} explained that the lens only changed how things looked, so {child.id} could understand the mistake and feel calm again.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass makes small things look bigger when you look through it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people do not understand the same thing in the same way.",
        ),
        QAItem(
            question="What helps after a misunderstanding?",
            answer="Talking kindly and explaining clearly can help fix a misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("magnifies", tid, int(tool.scale)))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.if_seen_big:
            lines.append(asp.fact("can_mislead", oid))
    return "\n".join(lines)


ASP_RULES = r"""
can_be_confused(O) :- can_mislead(O).
magnified_view(T,O) :- tool(T), object(O), magnifies(T,S), S > 1.
misunderstanding(T,O) :- magnified_view(T,O), can_be_confused(O).
#show can_be_confused/1.
#show magnified_view/2.
#show misunderstanding/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2."))
    got = set(asp.atoms(model, "misunderstanding"))
    expected = {(tid, oid) for tid in TOOLS for oid, obj in OBJECTS.items() if obj.if_seen_big}
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} cases).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" clingo:", sorted(got))
    print(" python:", sorted(expected))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TOOLS[params.tool], OBJECTS[params.object], params.name, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="garden", tool="magnifying_glass", object="ant", name="Mia", parent="Mom", trait="curious"),
    StoryParams(place="porch", tool="lensed_toy", object="leaf", name="Leo", parent="Dad", trait="silly"),
    StoryParams(place="playroom", tool="magnifying_glass", object="button", name="Nora", parent="Mum", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2."))
        print(sorted(set(asp.atoms(model, "misunderstanding"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.tool} / {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
