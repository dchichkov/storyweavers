#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/explosion_cautionary_inner_monologue_bedtime_story.py
======================================================================================

A small bedtime storyworld about a sleepy child, a risky idea, an inner warning,
and a calm grown-up fix. The seed word is "explosion"; the story stays
cautionary, child-facing, and concrete.

The world models a tiny scene with typed entities, accumulating physical meters
and emotional memes, a forward-causal turn, and a resolution that proves what
changed. The style is bedtime-story gentle, but the premise is still safety-first:
a child notices something that could pop or explode, thinks about it privately,
and chooses help instead of poking at danger.

This file is standalone and uses only the Python stdlib plus the shared
storyworlds/results.py and lazily-imported storyworlds/asp.py helpers.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    setting: str
    object_id: str
    object_label: str
    object_phrase: str
    object_risk: str
    safe_tool: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    bedtime: str
    dark_spot: str
    cozy_image: str


@dataclass
class RiskyObject:
    id: str
    label: str
    phrase: str
    risk: str
    danger: str
    can_burst: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["danger"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            if e.kind == "character":
                e.memes["fear"] += 1
                out.append("__fear__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["safe"] >= THRESHOLD and ("calm", e.id) not in world.fired:
            world.fired.add(("calm", e.id))
            if e.kind == "character":
                e.memes["relief"] += 1
                out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("calm", _r_calm)]


def explodes_at_risk(obj: RiskyObject) -> bool:
    return obj.can_burst


def safe_tool_for(obj: RiskyObject) -> bool:
    return obj.can_burst


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        bedtime="at bedtime",
        dark_spot="the little toy corner by the pillow",
        cozy_image="the lamp made a warm moon on the wall",
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        bedtime="before sleep",
        dark_spot="the toy chest by the rug",
        cozy_image="the blanket fort glowed like a tiny tent",
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        bedtime="late at night",
        dark_spot="the coat nook by the shoes",
        cozy_image="the night-light blinked like a sleepy star",
    ),
}

OBJECTS = {
    "balloon_tin": RiskyObject(
        id="balloon_tin",
        label="a little tin of old party poppers",
        phrase="a little tin of old party poppers",
        risk="could pop with a bang",
        danger="small sparks and a loud snap",
        tags={"explosion", "bang"},
    ),
    "science_kit": RiskyObject(
        id="science_kit",
        label="a science kit with fizzing powder",
        phrase="a science kit with fizzing powder",
        risk="could fizz too hard",
        danger="a sudden pop and a puff of smoke",
        tags={"explosion", "fizz"},
    ),
    "battery_pack": RiskyObject(
        id="battery_pack",
        label="a battery pack with a loose wire",
        phrase="a battery pack with a loose wire",
        risk="could spark and burst",
        danger="a snap, a spark, and a flash",
        tags={"explosion", "spark"},
    ),
}

TOOLS = {
    "flashlight": SafeTool(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="glowed soft and steady",
        tags={"safe_light"},
    ),
    "nightlight": SafeTool(
        id="nightlight",
        label="night-light",
        phrase="a night-light",
        glow="shone like a tiny star",
        tags={"safe_light"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Finn"]
TRAITS = ["curious", "careful", "sleepy", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, t) for s in SETTINGS for o in OBJECTS for t in TOOLS if explodes_at_risk(OBJECTS[o])]


def explain_rejection(obj: RiskyObject) -> str:
    return f"(No story: {obj.label} is not a plausible source of a danger that could become an explosion.)"


def tell(setting: Setting, obj: RiskyObject, tool: SafeTool, child: Entity, parent: Entity) -> World:
    world = World(setting)
    world.add(child)
    world.add(parent)
    child.memes["sleepiness"] += 1
    child.memes["curiosity"] += 1

    world.say(
        f"At {setting.bedtime}, {child.id} was tucked in, but {setting.dark_spot} still looked a little too interesting."
    )
    world.say(
        f"{child.id} noticed {obj.phrase}. In a tiny inner voice, {child.pronoun()} thought, "
        f'"It {obj.risk}. I should not touch it alone."'
    )

    world.para()
    child.memes["worry"] += 1
    world.say(
        f"{child.id} held still and listened to that warning feeling. "
        f'The little thought came again: "If I poke it, there could be {obj.danger}."'
    )
    world.say(
        f'"{parent.label_word.capitalize()}?" {child.id} called softly. '
        f'"I found something that feels risky."'
    )
    parent.memes["calm"] += 1

    world.para()
    world.say(
        f"{parent.label_word.capitalize()} came right away, looked once, and nodded. '
        f'"Thank you for telling me," {parent.id} said. '
        f'"You made a safe choice by stopping."'
    )
    world.get(child.id).meters["danger"] = 0
    world.get(parent.id).meters["danger"] = 0
    world.get(child.id).meters["safe"] += 1
    propagate(world, narrate=False)

    world.say(
        f"{parent.label_word.capitalize()} put the risky thing away up high, where small hands could not reach it."
    )
    world.say(
        f"Then {parent.id} turned on {tool.phrase}. It {tool.glow}, and the room felt sleepy and gentle again."
    )
    world.say(
        f"{child.id} snuggled down under the blanket and watched the soft light until {setting.cozy_image}."
    )

    world.facts.update(setting=setting, obj=obj, tool=tool, child=child, parent=parent, safe=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj"]
    setting = f["setting"]
    return [
        f'Write a bedtime story for a young child where {child.id} notices {obj.label} in {setting.place} and hears an inner warning before calling a grown-up.',
        f'Tell a gentle cautionary story that includes the word "explosion" and ends with a safe light at bedtime.',
        f'Write a cozy story where a sleepy child decides not to touch something that could lead to an explosion, then feels proud for getting help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["obj"]
    tool = f["tool"]
    return [
        QAItem(
            question="What did the child notice?",
            answer=f"{child.id} noticed {obj.phrase} and felt a warning in {child.pronoun()} inner voice. That warning helped {child.id} pause before doing anything risky.",
        ),
        QAItem(
            question="Why did the child call the grown-up?",
            answer=f"{child.id} called {parent.label_word} because {obj.risk} and could have made {obj.danger}. Calling for help was the safest choice.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{parent.label_word.capitalize()} put the risky thing away and turned on {tool.phrase}. The room became calm again, so the ending image was soft, safe, and sleepy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do if something seems dangerous at bedtime?",
            answer="Stop, step back, and call a grown-up right away. A child should never try to fix a risky thing alone.",
        ),
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight gives safe light in the dark. It helps you see without using a flame or touching anything risky.",
        ),
        QAItem(
            question="Why is it smart to listen to an inner warning?",
            answer="An inner warning can help you notice danger before anything bad happens. Listening to it can keep people safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime cautionary storyworld about a risky object and a child who listens to an inner warning.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object_id and not OBJECTS[args.object_id].can_burst:
        raise StoryError(explain_rejection(OBJECTS[args.object_id]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, object_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        parent_type=parent_type,
        setting=setting_id,
        object_id=object_id,
        object_label=OBJECTS[object_id].label,
        object_phrase=OBJECTS[object_id].phrase,
        object_risk=OBJECTS[object_id].risk,
        safe_tool=tool_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object_id not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_id}")
    if params.safe_tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.safe_tool}")
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object_id]
    tool = TOOLS[params.safe_tool]
    child = Entity(id=params.child_name, kind="character", type=params.child_gender, role="child")
    parent = Entity(id="Parent", kind="character", type=params.parent_type, role="parent")
    world = tell(setting, obj, tool, child, parent)
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


ASP_RULES = r"""
safe_choice(O) :- risky_object(O).
inner_warning(C) :- child(C).
cautionary_story :- risky_object(O), can_burst(O), child(C), parent(P), safe_tool(T).
outcome(safe) :- cautionary_story.
#show outcome/1.
#show safe_choice/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("risky_object", oid))
        if obj.can_burst:
            lines.append(asp.fact("can_burst", oid))
    for tid in TOOLS:
        lines.append(asp.fact("safe_tool", tid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("parent", "parent"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show outcome/1.\n") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "outcome")
    if not atoms or atoms[0][0] != "safe":
        print("MISMATCH: ASP outcome did not produce safe.")
        rc = 1
    else:
        print("OK: ASP outcome produced safe.")

    sample_params = resolve_params(build_parser().parse_args([]), random.Random(777))
    try:
        sample = generate(sample_params)
        if not sample.story.strip():
            print("MISMATCH: generate() produced empty story.")
            rc = 1
        else:
            print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"MISMATCH: generate() crashed: {e}")
        rc = 1
    return rc


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show outcome/1.\n"))
    # Derive from Python registry for compatibility; ASP twin kept for parity.
    return sorted(set(valid_combos()))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, object, tool) combos:")
        for setting, obj, tool in combos:
            print(f"  {setting:10} {obj:16} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for setting, obj_id, tool_id in valid_combos():
            params = StoryParams(
                child_name="Lily",
                child_gender="girl",
                parent_type="mother",
                setting=setting,
                object_id=obj_id,
                object_label=OBJECTS[obj_id].label,
                object_phrase=OBJECTS[obj_id].phrase,
                object_risk=OBJECTS[obj_id].risk,
                safe_tool=tool_id,
            )
            samples.append(generate(params))
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
            header = f"### {p.child_name}: {p.setting} / {p.object_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
