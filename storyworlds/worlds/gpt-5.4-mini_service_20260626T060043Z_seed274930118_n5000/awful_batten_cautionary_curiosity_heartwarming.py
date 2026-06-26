#!/usr/bin/env python3
"""
awful_batten_cautionary_curiosity_heartwarming.py
==================================================

A small story world about a curious child, a wobbly batten, and a careful fix.

The seed tale behind this world:
---
A curious child notices an awful loose batten on the garden shed after a windy night.
The child wants to tug it, but the grown-up warns that the board could scratch a hand
or fall. Together they fetch a hammer, a straight batten, and a few nails. The child
holds the flashlight while the grown-up secures the board. In the end the shed is safe
again, and the child feels proud for helping the careful way.

This world keeps the premise small:
- curiosity tempts the child toward a risky object;
- cautionary advice prevents a bad touch;
- a gentle repair turns worry into pride.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "mess": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "calm": 0.0}

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
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    region: str
    damage_kind: str = "damage"
    plural: bool = False


@dataclass
class ToolDef:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"repair"}),
    "shed": Setting(place="the garden shed", indoor=False, affords={"repair"}),
    "porch": Setting(place="the porch", indoor=False, affords={"repair"}),
}

OBJECTS = {
    "awful_batten": ObjectDef(
        id="awful_batten",
        label="batten",
        phrase="an awful loose batten",
        region="hand",
        damage_kind="scratch",
    ),
    "splintered_board": ObjectDef(
        id="splintered_board",
        label="board",
        phrase="a splintered board",
        region="hand",
        damage_kind="scratch",
    ),
}

TOOLS = {
    "gloves": ToolDef(
        id="gloves",
        label="work gloves",
        phrase="a pair of work gloves",
        protects={"hand"},
        plural=True,
    ),
    "hammer": ToolDef(
        id="hammer",
        label="hammer",
        phrase="a small hammer",
        protects=set(),
    ),
    "flashlight": ToolDef(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        protects=set(),
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Noah", "Eli", "Sam"]
TRAITS = ["curious", "gentle", "bright-eyed", "thoughtful", "careful"]


def reasonableness_gate(setting: Setting, obj: ObjectDef, tool: ToolDef) -> bool:
    return setting.affords == {"repair"} and obj.region == "hand" and "hand" in tool.protects


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id, obj in OBJECTS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(setting, obj, tool):
                    combos.append((place, obj_id, tool_id))
    return combos


def _repair_scene(world: World, child: Entity, parent: Entity, obj: Entity, tool: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was a {next((t for t in [child.type] if t), 'child')} with a curious look "
        f"who noticed {obj.phrase} near {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to poke the {obj.label}, because it looked so interesting."
    )
    parent.memes["worry"] += 1
    world.say(
        f'But {parent.pronoun().capitalize()} said, "Not yet. That batten is awful loose, and it could scratch a hand."'
    )
    world.say(
        f"So {child.id} paused and listened. {parent.id} fetched {tool.phrase}, and {child.id} held the light."
    )
    tool.worn_by = child.id
    child.memes["pride"] += 1
    child.memes["calm"] += 1
    obj.meters["damage"] = 0.0
    obj.meters["safe"] = 1.0
    world.say(
        f"Together they fixed the batten the careful way. The board stayed steady, and the shed looked safe again."
    )
    world.say(
        f"{child.id} smiled at the neat repair. {child.pronoun().capitalize()} had learned that curiosity is best when it waits for safety."
    )


def tell(setting: Setting, obj_def: ObjectDef, tool_def: ToolDef,
         hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    obj = world.add(Entity(id=obj_def.id, type="thing", label=obj_def.label, phrase=obj_def.phrase))
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, phrase=tool_def.phrase, protective=bool(tool_def.protects), covers=set(tool_def.protects), plural=tool_def.plural))

    _repair_scene(world, child, parent, obj, tool)

    world.facts.update(child=child, parent=parent, obj=obj, tool=tool, setting=setting, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, obj, tool = f["child"], f["obj"], f["tool"]
    return [
        'Write a gentle cautionary story about a curious child and an awful loose batten.',
        f"Tell a heartwarming story where {child.id} wants to touch {obj.phrase} but learns to help safely with {tool.label}.",
        "Write a short story about curiosity, a careful warning, and a family fixing something together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, obj, tool = f["child"], f["parent"], f["obj"], f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} notice near {world.setting.place}?",
            answer=f"{child.id} noticed {obj.phrase}. It looked interesting, but it was not safe to touch right away.",
        ),
        QAItem(
            question=f"Why did {parent.id} tell {child.id} to stop?",
            answer=f"{parent.id} was worried that the loose batten could scratch a hand or fall apart if someone tugged it.",
        ),
        QAItem(
            question=f"What did {child.id} do instead of poking the batten?",
            answer=f"{child.id} held the flashlight while {parent.id} used {tool.label} to fix the batten carefully.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The batten was secured, the shed looked safe again, and {child.id} felt proud for helping the careful way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a batten?",
            answer="A batten is a thin strip of wood used to hold things in place, like on a wall, a roof, or a shed.",
        ),
        QAItem(
            question="Why are work gloves useful?",
            answer="Work gloves help protect hands from rough wood, small splinters, and scratches when fixing things.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A batten is at risk when it is loose and in reach of a curious child.
at_risk(B) :- batten(B), loose(B), near_child(B).

% Gloves are a compatible safety fix only when they cover hands.
safe_fix(T) :- tool(T), protects(T, hand).

valid_story(P, B, T) :- place(P), batten(B), tool(T), at_risk(B), safe_fix(T), repair_place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        if "repair" in setting.affords:
            lines.append(asp.fact("repair_place", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("batten", oid))
        lines.append(asp.fact("loose", oid))
        lines.append(asp.fact("near_child", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(tool.protects):
            lines.append(asp.fact("protects", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary, heartwarming batten story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("unknown place")
    if args.object and args.object not in OBJECTS:
        raise StoryError("unknown object")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("unknown tool")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, object=obj_id, tool=tool_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], TOOLS[params.tool], params.name, params.gender, params.parent, params.trait)
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


CURATED = [
    StoryParams(place="shed", object="awful_batten", tool="gloves", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden", object="awful_batten", tool="gloves", name="Theo", gender="boy", parent="father", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
