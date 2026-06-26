#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/wawa_dialogue_heartwarming.py
===========================================================================================================

A small heartwarming dialogue world about a child, a thirsty little place,
and the gentle word "wawa" meaning water.

Premise:
- A child notices a tiny plant, bird, or pet that needs water.
- Someone older explains carefully, with warm dialogue.
- The child helps in a way that fits the setting and the tool they have.
- The story ends with a brighter little scene and a kind feeling.

World model:
- Physical meters: thirst, wetness, warmth, fullness, bloom, comfort.
- Emotional memes: worry, care, delight, trust, pride, relief.
- Dialogue is not decorative; it moves the world from worry to help.

This script follows the Storyworld contract:
- It defines StoryParams, registries, build_parser, resolve_params, generate, emit, and main.
- It imports storyworlds/results.py eagerly.
- It imports storyworlds/asp.py lazily inside ASP helpers.
- It includes an inline ASP_RULES twin and a Python reasonableness gate.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    kind: str
    plural: bool = False
    needs: str = "water"


@dataclass
class ToolCfg:
    id: str
    label: str
    verb: str
    helps: set[str]
    size: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    tool: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"cup"}),
    "garden": Setting("the garden", False, {"watering_can", "cup"}),
    "porch": Setting("the porch", False, {"cup"}),
}

OBJECTS = {
    "flower": ObjectCfg("flower", "a tiny thirsty flower", "soil", "plant"),
    "bird": ObjectCfg("bird", "a small bird with a dry feather", "nest", "bird"),
    "bunny": ObjectCfg("bunny", "a fluffy bunny that had been playing in the sun", "fur", "animal"),
}

TOOLS = {
    "cup": ToolCfg("cup", "a little cup", "pour water from a little cup", {"flower", "bird", "bunny"}, "small"),
    "can": ToolCfg("can", "a watering can", "pour water from a watering can", {"flower", "bird", "bunny"}, "medium"),
    "bowl": ToolCfg("bowl", "a bright bowl", "bring a bowl of water", {"flower", "bird"}, "small"),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tia", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Ilan", "Milo", "Theo"]
TRAITS = ["gentle", "curious", "kind", "patient", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id, obj in OBJECTS.items():
            for tool_id, tool in TOOLS.items():
                if tool_id in setting.affords and obj_id in tool.helps:
                    combos.append((place, obj_id, tool_id))
    return combos


def reason_gate(place: str, obj_id: str, tool_id: str) -> bool:
    return (place, obj_id, tool_id) in valid_combos()


def explain_rejection(place: str, obj_id: str, tool_id: str) -> str:
    obj = OBJECTS[obj_id]
    tool = TOOLS[tool_id]
    setting = SETTINGS[place]
    if tool_id not in setting.affords:
        return f"(No story: {tool.label} does not belong in {setting.place} for this little help scene.)"
    return f"(No story: {tool.label} is not a reasonable way to help {obj.label} here.)"


def dialogue_line(speaker: Entity, text: str, said: str = "said") -> str:
    return f'"{text}" {speaker.id} {said}.'


def predict_help(world: World, child: Entity, obj: Entity, tool: ToolCfg) -> dict:
    sim = world.copy()
    _apply_help(sim, sim.get(child.id), obj.id, tool.id, narrate=False)
    target = sim.get(obj.id)
    return {
        "thirst": target.meters.get("thirst", 0.0),
        "bloom": target.meters.get("bloom", 0.0),
        "comfort": sim.get(child.id).memes.get("comfort", 0.0),
    }


def _apply_help(world: World, child: Entity, obj_id: str, tool_id: str, narrate: bool = True) -> None:
    obj = world.get(obj_id)
    tool = TOOLS[tool_id]
    obj.meters["thirst"] = max(0.0, obj.meters.get("thirst", 0.0) - (1.2 if tool_id == "can" else 0.9))
    obj.meters["bloom"] = obj.meters.get("bloom", 0.0) + 1.0
    child.memes["care"] = child.memes.get("care", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    if narrate:
        world.say(f"{child.id} carefully did what {tool.verb}.")
        world.say(f"The little helper made the dry place feel less lonely.")


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    obj_cfg = OBJECTS[params.object]
    tool_cfg = TOOLS[params.tool]

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"warmth": 1.0},
        memes={"worry": 1.0, "care": 0.0, "trust": 0.0, "delight": 0.0, "pride": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=params.elder,
        label=f"the {params.elder}",
        meters={"warmth": 2.0},
        memes={"care": 1.0, "patience": 1.0},
    ))
    obj = world.add(Entity(
        id="Need",
        kind="thing",
        type=obj_cfg.kind,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        caretaker=elder.id,
        meters={"thirst": 1.5, "bloom": 0.0},
        memes={"sadness": 1.0},
    ))
    world.facts.update(child=child, elder=elder, obj=obj, tool=tool_cfg, obj_cfg=obj_cfg)
    return world


def scene_intro(world: World) -> None:
    child = world.facts["child"]
    elder = world.facts["elder"]
    obj = world.facts["obj"]
    world.say(f"{child.id} was a {next(t for t in ['gentle','curious','kind','patient','bright'] if t in ['gentle','curious','kind','patient','bright'])} little {child.type} who liked quiet helpful moments.")
    world.say(f"One day, {child.id} noticed {obj.phrase} and whispered, \"Wawa?\"")
    world.say(f"{elder.label.capitalize()} smiled softly and said, \"Yes, wawa means water. And this little one could use some.\"")


def scene_tension(world: World) -> None:
    child = world.facts["child"]
    elder = world.facts["elder"]
    obj = world.facts["obj"]
    tool = world.facts["tool"]
    world.para()
    world.say(f"{child.id} reached for {tool.label}, but paused. \"Is it enough?\" {child.id} asked.")
    world.say(f"{elder.label.capitalize()} nodded and said, \"It can be, if we do it slowly and kindly.\"")
    pred = predict_help(world, child, obj, tool)
    if pred["thirst"] >= THRESHOLD:
        world.say(f"{elder.label.capitalize()} added, \"We should not splash. {obj.label} needs gentle water, not a big hurry.\"")
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.facts["predicted"] = pred


def scene_resolution(world: World) -> None:
    child = world.facts["child"]
    elder = world.facts["elder"]
    obj = world.facts["obj"]
    tool = world.facts["tool"]
    world.para()
    world.say(f'{child.id} nodded. {dialogue_line(child, "Okay, I will be gentle", "said")}')
    _apply_help(world, child, obj.id, tool.id, narrate=True)
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    obj.meters["thirst"] = max(0.0, obj.meters.get("thirst", 0.0) - 0.4)
    obj.meters["bloom"] = obj.meters.get("bloom", 0.0) + 0.5
    world.say(f"{obj.label.capitalize()} looked brighter, as if it had been waiting for that tiny kindness.")
    world.say(f'{elder.label.capitalize()} laughed warmly and said, "That was perfect, little one."')
    world.say(f'{child.id} grinned and answered, "Wawa!" and this time the word sounded happy.')


def tell(params: StoryParams) -> World:
    world = build_story_world(params)
    scene_intro(world)
    scene_tension(world)
    scene_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, elder, obj, tool = f["child"], f["elder"], f["obj"], f["tool"]
    return [
        f'Write a warm short story for a young child that includes the word "wawa" and a gentle helping conversation.',
        f"Tell a heartwarming dialogue story where {child.id} and {elder.label} help {obj.label} using {tool.label}.",
        f'Write a simple story with dialogue where someone says "Wawa" and then learns how to help something thirsty.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, obj, tool = f["child"], f["elder"], f["obj"], f["tool"]
    return [
        QAItem(
            question=f'What did {child.id} say when noticing {obj.label}?',
            answer=f'{child.id} whispered "Wawa," and {elder.label} explained that it meant water.',
        ),
        QAItem(
            question=f'Why did {elder.label} want {child.id} to be gentle?',
            answer=f"{obj.label} was dry and needed careful help, so a slow, small pour was the kind way to help.",
        ),
        QAItem(
            question=f'How did {child.id} help {obj.label} in the end?',
            answer=f"{child.id} used {tool.label} to bring water, and {obj.label} looked brighter afterward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wawa mean in this story?",
            answer="In this story, wawa means water.",
        ),
        QAItem(
            question="Why is water helpful for thirsty things?",
            answer="Water helps thirsty plants and animals feel better because it gives them what they need to stay healthy.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", object="flower", tool="can", name="Mina", gender="girl", elder="grandmother"),
    StoryParams(place="kitchen", object="bird", tool="cup", name="Eli", gender="boy", elder="mother"),
    StoryParams(place="porch", object="bunny", tool="cup", name="Nora", gender="girl", elder="father"),
]


ASP_RULES = r"""
need_help(P,O,T) :- place(P), obj(O), tool(T), affords(P,T), helps(T,O).
valid_story(P,O,T) :- need_help(P,O,T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for oid in OBJECTS:
        lines.append(asp.fact("obj", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for o in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - clingo))
    print("only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming dialogue story world about wawa and gentle help.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.place and args.object and args.tool and not reason_gate(args.place, args.object, args.tool):
        raise StoryError(explain_rejection(args.place, args.object, args.tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(place=place, object=obj, tool=tool, name=name, gender=gender, elder=elder)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object, tool) combos:\n")
        for place, obj, tool in combos:
            print(f"  {place:8} {obj:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.object} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
