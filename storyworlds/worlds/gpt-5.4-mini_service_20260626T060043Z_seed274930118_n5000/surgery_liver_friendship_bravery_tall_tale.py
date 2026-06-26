#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale friendship and bravery story about
liver surgery and careful recovery.

The seed premise:
- A giant-hearted child and a loyal friend face a liver surgery.
- One of them wants to rush back into big, showy deeds.
- Friendship, bravery, and a sensible recovery plan turn the day around.

This world keeps the reasoning tight:
- surgery creates pain, worry, and recovery needs
- the liver is the at-risk organ
- a protective rest plan can prevent setbacks
- a friend can help with courage, comfort, and safe movement

The prose is aimed at children, with a tall-tale flavor and concrete state
changes driving the ending.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# Physical meter kinds
PAIN = "pain"
TIRED = "tired"
RECOVERY = "recovery"
HURRY = "hurry"

# Emotional meme kinds
WORRY = "worry"
BRAVERY = "bravery"
FRIENDSHIP = "friendship"
HOPE = "hope"
CONFIDENCE = "confidence"


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _pronoun(self) -> str:
        if self.type in {"girl", "mother", "woman"}:
            return "she"
        if self.type in {"boy", "father", "man"}:
            return "he"
        return "it"

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Settings, roles, and equipment
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the clinic"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Surgery:
    id: str
    verb: str
    gerund: str
    hurry: str
    risk: str
    recovery_step: str
    organ: str = "liver"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "clinic": Setting(place="the tiny clinic", indoors=True, affords={"surgery", "rest", "walk"}),
    "barn": Setting(place="the red barn clinic", indoors=True, affords={"surgery", "rest", "walk"}),
    "wagon": Setting(place="the wagon-house", indoors=False, affords={"rest", "walk"}),
}

SURGERIES = {
    "liver": Surgery(
        id="liver",
        verb="have liver surgery",
        gerund="having liver surgery",
        hurry="dash about too soon",
        risk="pain and strain",
        recovery_step="rest under a warm quilt",
        organ="liver",
        tags={"surgery", "liver", "medical"},
    )
}

GEAR = [
    Gear(
        id="blanket",
        label="a warm quilt",
        prep="wrap up in a warm quilt",
        tail="stayed under the warm quilt",
        guards={"pain", "tired"},
        covers={"torso"},
    ),
    Gear(
        id="pillow",
        label="a soft pillow",
        prep="tuck a soft pillow under their side",
        tail="used the soft pillow for the ride home",
        guards={"pain"},
        covers={"torso"},
    ),
    Gear(
        id="brace",
        label="a snug recovery sash",
        prep="fasten a snug recovery sash",
        tail="kept the recovery sash snug and steady",
        guards={"hurry"},
        covers={"torso"},
    ),
]

CHILD_NAMES = ["Mabel", "Jasper", "Winnie", "Otis", "Luna", "Penny", "Toby", "Clara"]
FRIEND_NAMES = ["Milo", "Pearl", "Bram", "Nell", "Rufus", "Daisy", "Hank", "Ivy"]
TRAITS = ["big-hearted", "brave", "cheerful", "stubborn", "gentle", "lively"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    surgery: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
need_rest(S) :- surgery(S).
at_risk(liver, S) :- surgery(S).

protects(G, M) :- gear(G), guards(G, M), covers(G, torso).
compatible_fix(S, G) :- surgery(S), protects(G, pain), protects(G, tired).

valid_story(Place, S) :- affords(Place, S), need_rest(S), at_risk(liver, S), compatible_fix(S, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SURGERIES.items():
        lines.append(asp.fact("surgery", sid))
        lines.append(asp.fact("organ", sid, s.organ))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    # Compare the simple Python gate with ASP
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    py2 = {(p, s) for p, s in py}
    if py2 == cl:
        print(f"OK: ASP matches Python ({len(py2)} stories).")
        return 0
    print("MISMATCH:")
    if py2 - cl:
        print("  only in python:", sorted(py2 - cl))
    if cl - py2:
        print("  only in asp:", sorted(cl - py2))
    return 1


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for sid in setting.affords:
            if sid == "liver":
                combos.append((place, sid))
    return combos

def explain_rejection(setting: Setting, surgery: Surgery) -> str:
    return (
        f"(No story: {setting.place} does not support a believable "
        f"{surgery.verb} tale with a safe recovery plan.)"
    )


def reasonableness_gate(setting: Setting, surgery: Surgery) -> bool:
    return setting.indoors or "rest" in setting.affords


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, friend: Entity, surgery: Surgery) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} child who loved tall tales, and "
        f"{friend.id} was the kind of friend who could make a shadow grin."
    )
    world.say(
        f"The two of them knew about {surgery.verb}, because the liver inside "
        f"a body can need careful fixing when it has been hurt."
    )
    child.memes[FRIENDSHIP] += 1
    friend.memes[FRIENDSHIP] += 1

def admit(world: World, child: Entity, friend: Entity, surgery: Surgery, doctor: Entity) -> None:
    world.say(
        f"One day, {child.id} and {friend.id} went to {world.setting.place}, where "
        f"{doctor.id} said {child.pronoun('possessive')} {surgery.organ} needed help."
    )
    world.say(
        f"The doctor talked plain and kind, promising the surgery would mend the trouble."
    )
    child.memes[WORRY] += 1
    child.meters[PAIN] += 1

def brave_but_hurried(world: World, child: Entity, friend: Entity, surgery: Surgery) -> None:
    child.memes[BRAVERY] += 1
    friend.memes[BRAVERY] += 1
    world.say(
        f"{child.id} wanted to be brave as a thundercloud, but also wanted to "
        f"{surgery.hurry} and prove nothing could slow {child.pronoun('object')} down."
    )
    world.say(
        f"{friend.id} gave {child.id} a steady nod and said, "
        f'"Bravery does not mean rushing. Bravery means staying put when staying put is the wisest trick."'
    )

def warn(world: World, child: Entity, surgery: Surgery, doctor: Entity) -> None:
    world.say(
        f'"If you {surgery.hurry}," {doctor.id} said, "your belly will ache more and '
        f"your {surgery.organ} will have a harder time healing.""
    )
    child.memes[WORRY] += 1

def choose_rest(world: World, child: Entity, friend: Entity, surgery: Surgery, gear: Gear) -> None:
    child.meters[RECOVERY] += 1
    child.memes[HOPE] += 1
    child.memes[CONFIDENCE] += 1
    world.say(
        f"So {friend.id} helped {child.id} {gear.prep}, and together they chose the slow, safe road."
    )
    world.say(
        f"That meant {child.id} could {surgery.recovery_step} while {friend.id} told a story about a moon that wore boots."
    )

def finish(world: World, child: Entity, friend: Entity, surgery: Surgery, gear: Gear) -> None:
    child.meters[PAIN] = max(0.0, child.meters.get(PAIN, 0.0) - 1.0)
    child.meters[Tired] = child.meters.get(Tired, 0.0) if False else child.meters.get(TIRED, 0.0)
    child.meters[TIRED] = max(0.0, child.meters.get(TIRED, 0.0) - 1.0)
    world.say(
        f"By sunset, {child.id} was still and safe, {gear.tail}, and "
        f"{friend.id} sat nearby like a loyal lantern."
    )
    world.say(
        f"Their bravery had not vanished; it had settled down inside them, gentle as a blanket and strong as a bell."
    )

def tell(setting: Setting, surgery: Surgery, child_name: str, child_type: str,
         friend_name: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, traits=[trait, "kind", "tall-tale-loving"]
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type, traits=["loyal", "steady"]
    ))
    doctor = world.add(Entity(
        id="DrMoss", kind="character", type="woman", label="Doctor Moss", traits=["wise", "gentle"]
    ))

    world.facts.update(child=child, friend=friend, doctor=doctor, surgery=surgery, setting=setting)

    introduce(world, child, friend, surgery)
    world.para()
    admit(world, child, friend, surgery, doctor)
    brave_but_hurried(world, child, friend, surgery)
    warn(world, child, surgery, doctor)
    world.para()

    gear = GEAR[0]
    choose_rest(world, child, friend, surgery, gear)
    finish(world, child, friend, surgery, gear)

    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    surg = f["surgery"]
    place = f["setting"].place
    return [
        f'Write a tall-tale style story for a young child about {child.id} and {friend.id} '
        f'helping after {surg.verb} at {place}.',
        f"Tell a gentle friendship story where bravery means resting after a liver surgery.",
        f'Write a story that uses the words "surgery" and "liver" and ends with a loyal friend nearby.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    surg = f["surgery"]
    doctor = f["doctor"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {doctor.id} tell {child.id} not to rush after the surgery?",
            answer=(
                f"{doctor.id} said rushing would make the belly ache more and make the liver harder to heal."
            ),
        ),
        QAItem(
            question=f"How did {friend.id} help {child.id} be brave?",
            answer=(
                f"{friend.id} stayed close, spoke kindly, and helped {child.id} choose the safe plan instead of rushing."
            ),
        ),
        QAItem(
            question=f"What did {child.id} do instead of dashing off right away?",
            answer=(
                f"{child.id} stayed under {gear.label}, rested, and let the recovery do its work."
            ),
        ),
        QAItem(
            question=f"What organ needed help in the story?",
            answer="The liver needed help from the surgery.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care for each other, help each other, and stay kind.",
        ),
        QAItem(
            question="Why do people rest after surgery?",
            answer="People rest after surgery so their bodies can heal safely and steadily.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: surgery, liver, friendship, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not reasonableness_gate(SETTINGS[setting], SURGERIES["liver"]):
        raise StoryError(explain_rejection(SETTINGS[setting], SURGERIES["liver"]))

    child_type = args.child_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        surgery="liver",
        child_name=child_name,
        child_type=child_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SURGERIES[params.surgery],
        params.child_name,
        params.child_type,
        params.friend_name,
        params.friend_type,
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(
                setting=setting,
                surgery="liver",
                child_name=CHILD_NAMES[0],
                child_type="girl",
                friend_name=FRIEND_NAMES[0],
                friend_type="boy",
                trait=TRAITS[0],
            )
            samples.append(generate(params))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
