#!/usr/bin/env python3
"""
storyworlds/worlds/mandolin_scallion_dialogue_cautionary_slice_of_life.py
=========================================================================

A small slice-of-life story world about a child, a careful task, and a gentle
dialogue-based warning. The seed words are mandolin and scallion.

Premise:
- A child wants to play a mandolin while helping in the kitchen.
- A grown-up notices that the scallion pile and the instrument should stay safe
  and clean.
- They trade haste for care and find a calmer way to finish the evening.

The world is intentionally compact: fewer plausible combinations, stronger
state-driven narration, and a cautionary turn that still ends warmly.
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

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("tension", "cleanliness", "noise", "mess", "warmth"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "care", "worry", "impatience", "relief", "love"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    caution: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    gender: str
    caretaker: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"chop_scallion", "practice_mandolin"}),
    "table": Setting(place="the table by the window", affords={"chop_scallion", "practice_mandolin"}),
    "porch": Setting(place="the porch", affords={"practice_mandolin"}),
}

ACTIVITIES = {
    "practice_mandolin": Activity(
        id="practice_mandolin",
        verb="practice the mandolin",
        gerund="practicing the mandolin",
        rush="strum too hard",
        caution="keep the strings gentle so the room stays calm",
        mess="noise",
        zone={"ears", "air"},
        tags={"mandolin", "music", "noise"},
    ),
    "chop_scallion": Activity(
        id="chop_scallion",
        verb="slice scallions",
        gerund="slicing scallions",
        rush="cut too fast",
        caution="take slow careful cuts so fingers stay safe",
        mess="tears",
        zone={"hands", "eyes"},
        tags={"scallion", "kitchen", "sharp"},
    ),
}

OBJECTS = {
    "mandolin": ObjectCfg(
        label="mandolin",
        phrase="a small wooden mandolin",
        region="hands",
    ),
    "scallion": ObjectCfg(
        label="scallion",
        phrase="a crisp green scallion",
        region="hands",
        plural=False,
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Ivy", "Owen", "Theo"]
TRAITS = ["quiet", "cheerful", "careful", "restless", "patient", "curious"]
CARETAKERS = ["mother", "father"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, obj: ObjectCfg) -> bool:
    return obj.region in activity.zone


def select_fix(activity: Activity, obj: ObjectCfg) -> Optional[str]:
    if activity.id == "practice_mandolin" and obj.label == "scallion":
        return "wash the scallions first and set the mandolin on the chair"
    if activity.id == "chop_scallion" and obj.label == "mandolin":
        return "put the mandolin on a shelf before the chopping starts"
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for obj_id, obj in OBJECTS.items():
                if prize_at_risk(act, obj) and select_fix(act, obj):
                    combos.append((place, act_id, obj_id))
    return combos


def _apply_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["noise"] >= THRESHOLD and ("noise", e.id) not in world.fired:
            world.fired.add(("noise", e.id))
            e.memes["worry"] += 1
            out.append("The room felt a little louder, and the grown-up looked up.")
    return out


def _apply_caution(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    obj = world.entities.get("object")
    if not child or not obj:
        return out
    if child.memes["impatience"] >= THRESHOLD and obj.meters["mess"] < THRESHOLD:
        sig = ("caution", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 0.25
            out.append("__caution__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_apply_noise, _apply_caution):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__caution__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, child: Entity, activity: Activity, obj: Entity) -> dict:
    sim = world.copy()
    sim.get("child").memes["impatience"] += 1
    if activity.id == "practice_mandolin":
        sim.get("mandolin").meters["noise"] += 1
    if activity.id == "chop_scallion":
        sim.get("object").meters["mess"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("object").meters["mess"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def tell(setting: Setting, activity: Activity, obj_cfg: ObjectCfg,
         hero_name: str, hero_gender: str, caretaker: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_gender, label=hero_name))
    adult = world.add(Entity(id="adult", kind="character", type=caretaker, label=f"the {caretaker}"))
    obj = world.add(Entity(id="object", kind="thing", type=obj_cfg.label, label=obj_cfg.label,
                           phrase=obj_cfg.phrase, owner=child.id, caretaker=adult.id))
    tool = world.add(Entity(id="mandolin", kind="thing", type="mandolin", label="mandolin",
                            phrase="a small wooden mandolin", owner=child.id, caretaker=child.id))
    if obj_cfg.label == "mandolin":
        tool = obj

    child.memes["joy"] += 1
    child.memes["love"] += 1
    child.memes["care"] += 0.5

    world.say(
        f"{hero_name} was a {trait} little {hero_gender} who liked the quiet rhythm of home."
    )
    world.say(
        f"{hero_name} loved {activity.gerund} and liked the way a {obj_cfg.label} looked "
        f"fresh and bright on the counter."
    )
    world.say(
        f"One ordinary afternoon at {setting.place}, {hero_name} kept both the {obj_cfg.label} "
        f"and the mandolin close by."
    )

    world.para()
    world.say(
        f"{hero_name} wanted to {activity.verb}, but {hero_name}'s {caretaker} raised a hand and said, "
        f"\"First, let's be careful.\""
    )
    world.say(
        f"\"{activity.caution.capitalize()},\" said the {caretaker}. \"We can do one thing at a time.\""
    )
    child.memes["impatience"] += 1
    propagate(world, narrate=True)

    if activity.id == "practice_mandolin":
        tool.meters["noise"] += 1
        world.say(f"{hero_name} gave one eager strum, and the mandolin sang too loudly for the little room.")
    else:
        obj.meters["mess"] += 1
        world.say(f"{hero_name} reached for the scallion too quickly, and the cutting board felt suddenly slippery.")

    outcome = predict_outcome(world, child, activity, obj)
    world.para()
    if outcome["mess"] or outcome["worry"]:
        fix = select_fix(activity, obj_cfg)
        if activity.id == "practice_mandolin":
            world.say(
                f"\"Let's wash the scallions first and put the mandolin on the chair,\" said the {caretaker}, "
                f"\"so your hands can do the right job.\""
            )
            world.say(
                f"{hero_name} nodded, wiped the counter, and washed the scallions before touching the strings again."
            )
            obj.meters["cleanliness"] += 1
            child.memes["relief"] += 1
            child.memes["joy"] += 1
        else:
            world.say(
                f"\"Let's set the mandolin on the shelf first,\" said the {caretaker}, "
                f"\"so the music won't get bumped while you chop.\""
            )
            world.say(
                f"{hero_name} carefully moved the mandolin away, then slowed down and finished the scallions without a rush."
            )
            tool.meters["cleanliness"] += 1
            child.memes["relief"] += 1
            child.memes["joy"] += 1
        world.say(
            f"In the end, the room was calm again, the {obj_cfg.label} stayed in good shape, "
            f"and {hero_name} felt proud of being careful."
        )

    world.facts.update(
        child=child, adult=adult, obj=obj, tool=tool, activity=activity,
        setting=setting, fix=select_fix(activity, obj_cfg)
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    obj = f["obj"]
    return [
        f'Write a short slice-of-life story for a young child about "{obj.label}" and "mandolin" with a gentle warning.',
        f"Tell a dialogue-rich story where {child.label} wants to {act.verb} but learns to slow down and be careful.",
        f"Write a cautionary everyday story set in {world.setting.place} about making a safe choice before playing with a mandolin.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, obj, act = f["child"], f["adult"], f["obj"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{child.label} wanted to {act.verb}, but needed a careful reminder first.",
        ),
        QAItem(
            question=f"What did the {adult.type} say to keep things safe?",
            answer=f"The {adult.type} said, \"{act.caution.capitalize()},\" and asked for one thing at a time.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.label} slowed down, the {obj.label} stayed in good shape, and the room felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mandolin?",
            answer="A mandolin is a small stringed instrument that you strum to make bright music.",
        ),
        QAItem(
            question="What is a scallion?",
            answer="A scallion is a young green onion with a mild taste, often chopped for food.",
        ),
        QAItem(
            question="Why is it good to do one thing at a time in the kitchen?",
            answer="Doing one thing at a time helps you stay calm, avoid bumps, and keep sharp tools and music from getting in the way of each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,O) :- zone(A,R), region(O,R).
has_fix(A,O) :- prize_at_risk(A,O), compatible_fix(A,O).
valid(Place,A,O) :- affords(Place,A), prize_at_risk(A,O), has_fix(A,O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone", aid, z))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, obj.region))
    for a_id, act in ACTIVITIES.items():
        for o_id, obj in OBJECTS.items():
            if select_fix(act, obj):
                lines.append(asp.fact("compatible_fix", a_id, o_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_story_triples() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_triples())
    cl = set(asp_valid_story_triples())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parse / resolve / generate / emit / main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with mandolin and scallion.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=CARETAKERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, object=obj, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
        params.name,
        params.gender,
        params.caretaker,
        params.trait,
    )
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="practice_mandolin", object="scallion", name="Mina", gender="girl", caretaker="mother", trait="careful"),
    StoryParams(place="table", activity="chop_scallion", object="mandolin", name="Leo", gender="boy", caretaker="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_story_triples()
        print(f"{len(triples)} valid combos:\n")
        for place, act, obj in triples:
            print(f"  {place:8} {act:20} {obj}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
