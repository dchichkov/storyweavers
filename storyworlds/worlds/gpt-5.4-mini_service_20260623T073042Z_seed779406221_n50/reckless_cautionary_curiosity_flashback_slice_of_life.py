#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
============================================================================

A small slice-of-life story world about a child whose curiosity gets a little
reckless, then a cautionary flashback helps them choose a safer way.

Seed tale:
---
Nina was spending a quiet afternoon at her aunt's apartment while the rain tapped
softly at the window. Her cousin Ben found an old windup toy in a drawer and
wanted to take it apart right away to see how it worked. Nina was curious too,
but she remembered a flashback from last week, when Ben had nearly lost a tiny
screw under the sofa and everyone had spent ages looking for it.

"Let's not be reckless," Nina said. "Maybe we can open it on the table with a
bowl first."

Ben frowned, then nodded. Together they brought a bowl, a napkin, and a little
tray so the parts would stay together. The toy popped open, the screw stayed
safe, and by the end of the afternoon they were both smiling at the little gears
spinning in their hands.

The world model tracks small physical changes in meters and emotional changes in
memes, then turns those states into a child-facing slice-of-life story.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ASP_RULES = r"""
chosen_safe(S) :- safe_item(S).
curious_turn(H) :- curiosity(H), not reckless_only(H).
reckless_only(H) :- reckless(H), not cautionary(H).
story_ok(P, O) :- place(P), object(O), at_risk(O), has_fix(O).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id

@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class ObjectCfg:
    id: str
    label: str
    fragile: bool
    has_parts: bool = True

@dataclass
class SafetyKit:
    id: str
    label: str
    phrase: str
    helps: set[str]

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out

def _r_scatter(world: World) -> list[str]:
    child = world.get("child")
    obj = world.get("object")
    if child.meters["reckless"] < THRESHOLD:
        return []
    if obj.meters["open"] < THRESHOLD:
        return []
    sig = ("scatter",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    obj.meters["messy"] += 1
    return [f"A tiny screw rolled toward the sofa before anyone could catch it."]

def _r_calm(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["caution"] < THRESHOLD or helper.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 1
    helper.memes["calm"] += 1
    return ["The room felt steadier once they decided to use a tray and a bowl."]

RULES = [Rule("scatter", _r_scatter), Rule("calm", _r_calm)]

def valid_combos() -> list[tuple[str, str]]:
    return [(s, o) for s in SETTINGS for o in OBJECTS if OBJECTS[o].fragile]

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
    for kid, kit in KITS.items():
        lines.append(asp.fact("safe_item", kid))
        for h in sorted(kit.helps):
            lines.append(asp.fact("helps", kid, h))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

@dataclass
class StoryParams:
    setting: str
    object: str
    kit: str
    child: str
    helper: str
    seed: Optional[int] = None

SETTINGS = {
    "apartment": Setting(place="a quiet apartment", indoor=True, affords={"open"}),
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"open"}),
    "porch": Setting(place="the covered porch", indoor=False, affords={"open"}),
}
OBJECTS = {
    "toy": ObjectCfg(id="toy", label="windup toy", fragile=True),
    "clock": ObjectCfg(id="clock", label="little clock", fragile=True),
    "box": ObjectCfg(id="box", label="music box", fragile=True),
}
KITS = {
    "tray": SafetyKit(id="tray", label="tray", phrase="a little tray", helps={"open"}),
    "bowl": SafetyKit(id="bowl", label="bowl", phrase="a bowl", helps={"open"}),
    "napkin": SafetyKit(id="napkin", label="napkin", phrase="a folded napkin", helps={"open"}),
}
GIRLS = ["Nina", "Maya", "Ava", "Lily"]
BOYS = ["Ben", "Theo", "Max", "Noah"]

def tell(setting: Setting, obj: ObjectCfg, kit: SafetyKit, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl" if child_name in GIRLS else "boy", label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type="boy" if helper_name in BOYS else "girl", label=helper_name, role="helper"))
    object_ent = world.add(Entity(id="object", label=obj.label, meters={"open": 0.0, "messy": 0.0}, memes={"memory": 0.0}))
    kit_ent = world.add(Entity(id="kit", label=kit.label))
    child.meters = {"reckless": 0.0, "curiosity": 1.0}
    child.memes = {"curiosity": 1.0, "caution": 0.0, "worry": 0.0, "calm": 0.0}
    helper.memes = {"curiosity": 1.0, "caution": 1.0, "calm": 0.0}
    world.facts["memory"] = "flashback"
    world.say(f"{child_name} was spending a quiet afternoon at {setting.place} with {helper_name}.")
    world.say(f"An old {obj.label} sat in a drawer, and both children kept looking at it.")
    world.para()
    world.say(f"{child_name} wanted to open it right away, because curiosity was tugging hard.")
    world.say(f"Then a flashback came back to {child_name}: last week, a tiny screw had nearly vanished under the sofa.")
    world.para()
    child.meters["reckless"] += 1
    child.memes["caution"] += 1
    object_ent.meters["open"] = 1.0
    propagate(world, narrate=True)
    world.say(f"{child_name} said, \"Let's not be reckless. Let's use {kit.phrase} first.\"")
    helper.memes["curiosity"] += 1
    world.say(f"{helper_name} nodded, and together they set the {obj.label} on the table with {kit.phrase}.")
    world.para()
    world.say(f"The lid popped open, the little parts stayed together, and the tiny screw stayed safe.")
    world.say(f"By the end of the afternoon, they were smiling at the little gears turning in their hands.")
    world.facts.update(child=child, helper=helper, object=object_ent, kit=kit_ent, setting=setting, obj_cfg=obj)
    return world

KNOWLEDGE = {
    "reckless": [("What does reckless mean?", "Reckless means doing something too quickly without enough care or thinking about the risk.")],
    "curiosity": [("What is curiosity?", "Curiosity is the wish to learn or see how something works.")],
    "flashback": [("What is a flashback in a story?", "A flashback is a memory from before that comes back into the story for a moment.")],
    "tray": [("What is a tray for?", "A tray is a flat dish that can hold small things so they do not roll away.")],
    "bowl": [("Why can a bowl help with small parts?", "A bowl can keep tiny pieces together so they are easier to find.")],
}
KNOWLEDGE_ORDER = ["reckless", "curiosity", "flashback", "tray", "bowl"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child about {f["child"].name} and {f["helper"].name} opening a small object with care.',
        f"Tell a gentle story where {f['child'].name} feels curious, remembers a flashback, and decides not to be reckless.",
        f'Write a simple everyday story that includes the word "reckless" and ends with tiny parts staying safe.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    obj: Entity = f["object"]
    kit: Entity = f["kit"]
    setting: Setting = f["setting"]
    return [
        QAItem(question=f"Who was the story about at {setting.place}?", answer=f"It was about {child.name} and {helper.name}, who spent a quiet afternoon opening {obj.label}."),
        QAItem(question=f"What did {child.name} remember before opening the {obj.label}?", answer="A flashback came back about a tiny screw nearly getting lost under the sofa last week."),
        QAItem(question=f"What safer thing did they use on the table?", answer=f"They used {kit.name} and kept the small parts together so nothing rolled away."),
    ]

def world_qa(world: World) -> list[QAItem]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj = rng.choice(sorted(combos))
    kit = args.kit or rng.choice(sorted(KITS))
    child = args.child or rng.choice(GIRLS + BOYS)
    helper = args.helper or rng.choice([n for n in GIRLS + BOYS if n != child])
    return StoryParams(setting=setting, object=obj, kit=kit, child=child, helper=helper)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], KITS[params.kit], params.child, params.helper)
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
        print("== Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about curiosity, caution, and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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
    if set(asp.atoms(asp.one_model(asp_program("#show chosen_safe/1.")), "chosen_safe")) == {("tray",), ("bowl",), ("napkin",)}:
        print("OK: ASP program loads.")
        return 0
    print("MISMATCH: ASP program did not behave as expected.")
    return 1

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show chosen_safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(setting=s, object=o, kit="tray", child="Nina", helper="Ben")) for s, o in valid_combos()]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
