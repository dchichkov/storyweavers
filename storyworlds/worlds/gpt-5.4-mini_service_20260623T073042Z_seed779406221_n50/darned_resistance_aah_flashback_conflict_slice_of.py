#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
=======================================================================

A small slice-of-life story world built from a simple seed:
darned, resistance, aah.

Premise:
A child comes home with a stubborn little problem about a darned sweater.
A grown-up remembers a chilly flashback, the child resists, and they work
through the conflict with a gentle fix and a cozy ending.

The world is intentionally tiny:
- one child
- one adult
- one repaired garment
- one home setting
- one emotional turn driven by flashback + conflict

It keeps the prose concrete and state-driven: meters and memes move the story.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    soft: bool = True
    darned: bool = False
    warmth: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    tense: str
    discomfort: str
    zone: set[str]
    weather_word: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    verb: str
    tool: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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
        clone.flashback_used = self.flashback_used
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fret(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.memes["resistance"] < THRESHOLD:
        return out
    if item.meters["mended"] >= THRESHOLD:
        sig = ("fret",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["conflict"] += 1
        out.append("Confliction tightened in the room.")
    return out


CAUSAL_RULES = [Rule("fret", "social", _r_fret)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "Confliction tightened in the room.":
                world.say(s)
    return produced


def assess_item_risk(activity: Activity, item: Item) -> bool:
    return item.region in activity.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for activity_id in setting.affords:
            activity = ACTIVITIES[activity_id]
            for item_id, item in ITEMS.items():
                if assess_item_risk(activity, item):
                    combos.append((setting_id, activity_id, item_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    activity: str
    item: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    trait: str
    repair: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"mend", "walk"}),
    "living_room": Setting(place="the living room", indoors=True, affords={"mend", "read"}),
    "porch": Setting(place="the porch", indoors=False, affords={"walk", "mend"}),
}

ACTIVITIES = {
    "walk": Activity(
        id="walk",
        verb="go for a walk",
        gerund="walking outside",
        tense="walked",
        discomfort="the wind felt sharp at the ankles",
        zone={"feet", "legs"},
        weather_word="windy",
        tags={"wind", "outside"},
    ),
    "mend": Activity(
        id="mend",
        verb="fix the tear",
        gerund="mending cloth",
        tense="mended",
        discomfort="the needle could sting",
        zone={"hands"},
        weather_word="quiet",
        tags={"thread", "needle"},
    ),
    "read": Activity(
        id="read",
        verb="read by the window",
        gerund="reading books",
        tense="read",
        discomfort="the chair stayed too still",
        zone={"hands"},
        weather_word="soft",
        tags={"books"},
    ),
}

ITEMS = {
    "sweater": Item(
        id="sweater",
        label="sweater",
        phrase="a warm blue sweater",
        region="torso",
        soft=True,
        darned=True,
        warmth=2,
        tags={"sweater", "darned"},
    ),
    "sock": Item(
        id="sock",
        label="sock",
        phrase="a darned sock",
        region="feet",
        plural=True,
        soft=True,
        darned=True,
        warmth=1,
        tags={"sock", "darned"},
    ),
    "mittens": Item(
        id="mittens",
        label="mittens",
        phrase="a pair of knitted mittens",
        region="hands",
        plural=True,
        soft=True,
        warmth=1,
        tags={"mittens"},
    ),
}

REPAIRS = {
    "patch": Repair(id="patch", verb="patch", tool="needle and thread", result="patched neatly", tags={"thread", "needle"}),
    "darn": Repair(id="darn", verb="darn", tool="darning needle", result="darned neatly", tags={"darned"}),
}

GIRL_NAMES = ["Maya", "Nora", "Lina", "Ivy", "June"]
BOY_NAMES = ["Finn", "Eli", "Noah", "Theo", "Owen"]
ADULT_NAMES = ["Mina", "Ruth", "Sam", "Jules", "Hazel"]
TRAITS = ["careful", "quiet", "curious", "gentle", "stubborn"]


def reasonableness_gate(setting_id: str, activity_id: str, item_id: str) -> bool:
    return (setting_id, activity_id, item_id) in valid_combos()


def explain_rejection(setting_id: str, activity_id: str, item_id: str) -> str:
    item = ITEMS[item_id]
    act = ACTIVITIES[activity_id]
    return f"(No story: {act.gerund} doesn't really affect {item.phrase} in {SETTINGS[setting_id].place}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(act.zone):
            lines.append(asp.fact("covers", aid, z))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, item.region))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,I) :- setting(S), activity(A), item(I), covers(A,R), region(I,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(setting: Setting, activity: Activity, item_cfg: Item, repair: Repair,
         child_name: str, child_gender: str, adult_name: str, adult_gender: str,
         trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, traits=[trait, "young"]))
    adult = world.add(Entity(id="adult", kind="character", type=adult_gender, label=adult_name, traits=["patient"]))
    item = world.add(Entity(id="item", type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase, plural=item_cfg.plural))
    for e in (child, adult, item):
        for k in ["resistance", "conflict", "comfort", "warmth", "mended"]:
            e.meters[k] += 0
        for k in ["memory", "relief", "care", "joy", "tension"]:
            e.memes[k] += 0

    # setup
    world.say(f"{child.label} came in from outside and stopped by the table. {child.label_word.capitalize() if child.label_word else child.label} held up {item.phrase} and frowned.")
    world.say(f"{adult.label} looked up from the kettle and noticed the little tear that had been {repair.result}.")
    world.facts["flashback"] = True

    # flashback
    world.para()
    world.say(f"{adult.label} remembered a chilly afternoon when the wind had nipped at {child.label}'s sleeves. Back then, the old cloth had made the walk feel longer.")
    world.say(f"That memory made the room feel softer, but it also made the grown-up careful about saying no too fast.")

    # conflict
    world.para()
    child.memes["resistance"] += 1
    world.say(f'"Aah," {child.label} said, tugging at the seam. "It scratches."')
    world.say(f"{child.label} wanted to leave it on the chair and wear something newer instead.")
    world.say(f"{adult.label} shook {adult.pronoun('possessive')} head and said the sweater would feel better once it was fixed.")

    propagate(world, narrate=False)

    # turn
    world.para()
    item.meters["mended"] += 1
    world.say(f"{adult.label} threaded the needle and showed {child.label} how the darned stitch could hold steady.")
    world.say(f'When the thread pulled through, {child.label} made a tiny "aah" and then laughed at the funny face {adult.label} made.')

    # resolution
    world.para()
    child.memes["resistance"] = 0
    child.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(f"{child.label} slipped the {item.label} back on and found it was warm instead of scratchy.")
    world.say(f"By the time they went to the porch, the wind felt ordinary again, and the darned sweater moved with them like a friendly hug.")

    world.facts.update(
        child=child, adult=adult, item=item, activity=activity, setting=setting,
        repair=repair, resolved=True, flashback=True, conflict=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short slice-of-life story for a young child about {f['child'].label} and a {f['item'].label} that has been {f['repair'].result}. Include the word 'darned'.",
        f"Tell a gentle story where {f['child'].label} shows resistance, an adult remembers a flashback, and they solve the conflict with a small repair.",
        f"Write a cozy home story with the exclamation 'aah' when thread or cloth tugs, and end with a warm, ordinary scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, item, repair = f["child"], f["adult"], f["item"], f["repair"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label} and {adult.label}, who were at home with the {item.label}.",
        ),
        QAItem(
            question=f"What did {child.label} resist doing at first?",
            answer=f"{child.label} resisted wearing the {item.label} because it scratched a little before the repair was finished.",
        ),
        QAItem(
            question=f"What memory did {adult.label} have?",
            answer=f"{adult.label} had a flashback to a chilly walk when the old cloth felt important and warm.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{adult.label} used {repair.tool} to {repair.verb} the tear, so the {item.label} was {repair.result}.",
        ),
        QAItem(
            question=f"What did {child.label} say when the thread tugged?",
            answer=f"{child.label} said 'aah' when the thread pulled through, and then laughed because the moment was only a little surprising.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does darned mean?",
            answer="Darned means a tear in cloth has been mended with thread so the cloth can be worn again.",
        ),
        QAItem(
            question="What is resistance in a story like this?",
            answer="Resistance is when someone does not want to do something yet and keeps pulling back or saying no.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered scene from before that appears in someone's mind during the story.",
        ),
        QAItem(
            question="What does conflict mean here?",
            answer="Conflict is the small disagreement between the child and the adult about what to do with the sweater.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", activity="mend", item="sweater", child_name="Maya", child_gender="girl", adult_name="Ruth", adult_gender="woman", trait="careful", repair="darn"),
    StoryParams(setting="living_room", activity="read", item="mittens", child_name="Finn", child_gender="boy", adult_name="Hazel", adult_gender="woman", trait="quiet", repair="patch"),
    StoryParams(setting="porch", activity="walk", item="sock", child_name="Nora", child_gender="girl", adult_name="Sam", adult_gender="man", trait="stubborn", repair="darn"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: darned resistance, aah, flashback, conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, item = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    repair = args.repair or rng.choice(sorted(REPAIRS))
    return StoryParams(setting, activity, item, child_name, child_gender, adult_name, adult_gender, trait, repair)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], ITEMS[params.item], REPAIRS[params.repair],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH")
        print("only in clingo:", sorted(clingo_set - python_set))
        print("only in python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for c in valid_combos():
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
