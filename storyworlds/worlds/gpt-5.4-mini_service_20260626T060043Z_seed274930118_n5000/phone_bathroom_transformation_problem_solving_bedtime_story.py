#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/phone_bathroom_transformation_problem_solving_bedtime_story.py
================================================================================

A small bedtime-story world about a bathroom, a phone, a worried caregiver,
and a gentle transformation that helps solve the problem.

Premise:
- A child loves a phone, but phones and bathrooms do not mix well.
- The caregiver worries about water, drops, and a disrupted bedtime routine.
- The child feels disappointed, then a kind compromise transforms the phone
  into a safe bedtime helper.

The world uses typed entities with physical meters and emotional memes.
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["wet", "safe", "dirty", "broken", "quiet", "bright", "sleepy", "calm"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "desire", "patience", "conflict", "relief", "curiosity", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


@dataclass
class BathroomWorld:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "BathroomWorld":
        import copy as _copy
        return BathroomWorld(
            place=self.place,
            entities=_copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


def _r_wet_phone(world: BathroomWorld) -> list[str]:
    out = []
    child = world.get("child")
    phone = world.get("phone")
    if child.memes["conflict"] < THRESHOLD:
        return out
    if phone.meters["wet"] >= THRESHOLD or phone.meters["safe"] < THRESHOLD:
        sig = ("wet_phone",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        phone.meters["broken"] += 1
        out.append("The phone would be ruined by the splashy water.")
    return out


def _r_transform(world: BathroomWorld) -> list[str]:
    phone = world.get("phone")
    case = world.get("case")
    if phone.meters["safe"] < THRESHOLD or case.meters["on"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    phone.attrs["mode"] = "bedtime"
    phone.meters["bright"] = 0.0
    phone.meters["quiet"] = 1.0
    phone.meters["sleepy"] = 1.0
    phone.meters["safe"] = 2.0
    return ["__transform__"]


CAUSAL_RULES = [_r_wet_phone, _r_transform]


def propagate(world: BathroomWorld, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                out.extend(p for p in produced if p != "__transform__")
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class PhoneConfig:
    label: str
    phrase: str
    mess_risk: str
    bedtime_use: str


@dataclass
class Fix:
    label: str
    phrase: str
    prep: str
    outcome: str


PHONE = PhoneConfig(
    label="phone",
    phrase="a small phone with a bright screen",
    mess_risk="water",
    bedtime_use="play a sleepy audio story",
)

FIXES = [
    Fix(
        label="waterproof case",
        phrase="a soft waterproof case",
        prep="put it in a waterproof case and keep it on the dry shelf",
        outcome="the phone could stay dry and become a quiet bedtime helper",
    ),
    Fix(
        label="towel nest",
        phrase="a folded towel nest",
        prep="wrap it in a towel nest and set it beside the sink",
        outcome="the phone could rest safely while the bath stayed calm",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bathroom", "phone", fix.label) for fix in FIXES]


@dataclass
class StoryWorldModel:
    world: BathroomWorld
    child: Entity
    parent: Entity
    phone: Entity
    case: Entity
    fix: Fix


def build_world(params: StoryParams, fix: Fix) -> StoryWorldModel:
    w = BathroomWorld(place="bathroom")
    child = w.add(Entity(id="child", kind="character", type=params.gender, attrs={"name": params.name}))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    phone = w.add(Entity(
        id="phone",
        type="phone",
        label="phone",
        phrase=PHONE.phrase,
        owner=child.id,
    ))
    case = w.add(Entity(
        id="case",
        type="case",
        label=fix.label,
        phrase=fix.phrase,
        owner=child.id,
    ))
    return StoryWorldModel(world=w, child=child, parent=parent, phone=phone, case=case, fix=fix)


def tell(model: StoryWorldModel) -> None:
    w, child, parent, phone, case, fix = model.world, model.child, model.parent, model.phone, model.case, model.fix
    name = child.attrs["name"]
    child.memes["desire"] += 1
    child.memes["curiosity"] += 1
    parent.memes["worry"] += 1

    w.say(f"At bedtime, {name} found {PHONE.phrase} on the bathroom counter.")
    w.say(f"{name} wanted to {PHONE.bedtime_use}, because the gentle voices made {name} feel sleepy.")
    w.say(f"But {parent.label or parent.type} frowned a little, because phones and water do not go together in the bathroom.")

    w.para()
    w.say(f"{name} picked up the phone, and the screen glowed bright above the sink.")
    phone.meters["bright"] = 1.0
    phone.meters["wet"] = 1.0
    child.memes["conflict"] += 1
    parent.memes["worry"] += 1
    w.say(f"That made the problem clear: a splash could make the phone stop working, and bedtime would turn sad and messy.")
    propagate(w, narrate=True)

    w.para()
    w.say(f"{parent.label.capitalize() if parent.label else 'Parent'} knelt beside {name} and thought for a moment.")
    w.say(f'"Let’s use {fix.label} instead," {parent.pronoun("subject")} said. "We can {fix.prep}."')
    case.meters["on"] = 1.0
    phone.meters["safe"] = 1.0
    propagate(w, narrate=True)

    child.memes["joy"] += 1
    child.memes["conflict"] = 0.0
    parent.memes["relief"] += 1
    phone.attrs["mode"] = "bedtime"

    w.say(f"{name} smiled and helped tuck the phone into the {fix.label}.")
    w.say(f"Then the little screen changed from bright and tempting to soft and sleepy, ready to {PHONE.bedtime_use}.")
    w.say(f"With the phone safe and quiet, {name} listened from the dry side of the bathroom, and bedtime felt calm again.")


def make_story(params: StoryParams) -> StorySample:
    fix = FIXES[0]
    model = build_world(params, fix)
    tell(model)
    story = model.world.render()
    prompts = [
        f'Write a short bedtime story set in a bathroom about a child named {params.name}, a phone, and a safe compromise.',
        f'Tell a gentle problem-solving story where {params.name} wants to use a phone in the bathroom, but a caregiver protects it from water.',
        f'Write a bedtime story in which a phone changes into a calm helper instead of staying bright and distracting.',
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} want to do with the phone at bedtime?",
            answer=f"{params.name} wanted to use the phone to listen to a sleepy audio story in the bathroom before going to bed.",
        ),
        QAItem(
            question=f"Why did the parent worry about the phone in the bathroom?",
            answer="The parent worried because the bathroom had water and splashes, and a wet phone could get ruined.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"They put the phone in a waterproof case and kept it on the dry shelf, so it could stay safe and become a quiet bedtime helper.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a waterproof case for?",
            answer="A waterproof case helps keep a device dry when it is near water.",
        ),
        QAItem(
            question="Why can water be dangerous for a phone?",
            answer="Water can damage the inside parts of a phone and make it stop working properly.",
        ),
    ]
    model.world.facts = {
        "name": params.name,
        "parent": params.parent,
        "fix": fix.label,
        "phone_mode": model.phone.attrs.get("mode", ""),
    }
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=model.world)


def generation_prompts(world: BathroomWorld) -> list[str]:
    return []


def story_qa(world: BathroomWorld) -> list[QAItem]:
    return []


def world_knowledge_qa(world: BathroomWorld) -> list[QAItem]:
    return []


def dump_trace(world: BathroomWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "bathroom"),
        asp.fact("activity", "phone"),
        asp.fact("risk", "water"),
    ]
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.label))
    return "\n".join(lines)


ASP_RULES = r"""
risk_of(phone, water).

safe_fix(waterproof_case) :- fix(waterproof case).
safe_fix(towel_nest) :- fix(towel nest).

valid_story(bathroom, phone, waterproof_case).
valid_story(bathroom, phone, towel_nest).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world set in a bathroom with a phone and a gentle fix.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    name = args.name or rng.choice(["Mia", "Noah", "Lily", "Eli", "Nora"])
    return StoryParams(name=name, gender=args.gender, parent=args.parent)


def generate(params: StoryParams) -> StorySample:
    return make_story(params)


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
    StoryParams(name="Mia", gender="girl", parent="mother"),
    StoryParams(name="Noah", gender="boy", parent="father"),
    StoryParams(name="Lily", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(params))

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
