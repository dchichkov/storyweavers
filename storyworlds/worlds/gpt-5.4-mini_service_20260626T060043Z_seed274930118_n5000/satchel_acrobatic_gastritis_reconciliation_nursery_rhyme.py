#!/usr/bin/env python3
"""
Story world: satchel, acrobatics, and a grumbly tummy, ending in reconciliation.

A tiny nursery-rhyme-style simulation:
- A child loves acrobatic play.
- A satchel bumps and jostles.
- The child gets gastritis and feels poorly.
- A caring grown-up helps with tea, rest, and reconciliation.

The prose is driven by world state, not a fixed paragraph.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    cozy: bool = True


@dataclass
class Activity:
    id: str
    name: str
    motion: str
    jostle: str
    strain: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str = "torso"


@dataclass
class Remedy:
    label: str
    phrase: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", cozy=True),
    "garden": Setting(place="the garden", cozy=True),
    "attic": Setting(place="the attic", cozy=False),
}

ACTIVITIES = {
    "acrobatic": Activity(
        id="acrobatic",
        name="acrobatic play",
        motion="do acrobatic tumbles",
        jostle="tumble and twirl",
        strain="bounce too hard",
        keyword="acrobatic",
        tags={"acrobatic"},
    ),
    "skip": Activity(
        id="skip",
        name="skipping games",
        motion="skip in bright loops",
        jostle="hop and spin",
        strain="skip too quick",
        keyword="skip",
        tags={"play"},
    ),
}

PRIZES = {
    "satchel": Prize(
        label="satchel",
        phrase="a little satchel with a shiny clasp",
        region="torso",
    ),
    "bag": Prize(
        label="bag",
        phrase="a tidy cloth bag",
        region="torso",
    ),
}

REMEDIES = {
    "tea": Remedy(
        label="warm tea",
        phrase="a little cup of warm tea",
        action="sip warm tea",
        effect="felt calmer",
        tags={"care", "warmth"},
    ),
    "rest": Remedy(
        label="rest",
        phrase="a soft blanket and a quiet rest",
        action="rest beside the pillow",
        effect="felt steadier",
        tags={"care", "quiet"},
    ),
}

NAMES = ["Mina", "Pip", "Toby", "Nell", "Lila", "Owen"]
TRAITS = ["spry", "cheery", "gentle", "brave", "tiny"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), at_risk(A,P).
needs_reconciliation(A,P) :- prize_at_risk(A,P), causes_gastritis(A,P).
valid_story(S,A,P,R) :- setting(S), activity(A), prize(P), remedy(R),
                        prize_at_risk(A,P), helps(R,A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("at_risk", aid, "satchel" if aid == "acrobatic" else "bag"))
        if "acrobatic" in act.tags:
            lines.append(asp.fact("causes_gastritis", aid, "satchel"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for tag in rem.tags:
            lines.append(asp.fact("helps", rid, "acrobatic", "satchel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_story_triples())
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return activity.id == "acrobatic" and prize.label == "satchel"


def valid_story_triples() -> list[tuple]:
    return [("nursery", "acrobatic", "satchel", "tea"), ("garden", "acrobatic", "satchel", "rest")]


def select_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    triples = valid_story_triples()
    if args.place:
        triples = [t for t in triples if t[0] == args.place]
    if not triples:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(triples)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    remedy: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: satchel, acrobatic, gastritis, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    place, activity, prize, remedy = select_combo(rng, args)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not reasonableness_gate(act, pr):
            raise StoryError("No story: only the acrobatic satchel story is supported here.")
    return StoryParams(place, activity, prize, remedy, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    satchel = world.add(Entity(
        id="satchel",
        type="satchel",
        label="satchel",
        phrase=PRIZES[params.prize].phrase,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
    ))
    remedy = REMEDIES[params.remedy]
    activity = ACTIVITIES[params.activity]

    child.memes["joy"] = 1.0
    child.memes["love"] = 1.0
    child.memes["danger"] = 0.0
    satchel.meters["clean"] = 1.0

    world.say(f"{child.id} was a {params.trait} little {child.type} with a bright satchel.")
    world.say(f"{child.pronoun().capitalize()} loved to {activity.motion}, and the day at {world.setting.place} felt merry.")

    world.say(f"Then {child.id} tried to {activity.jostle}, with {child.pronoun('possessive')} satchel bumping here and there.")
    child.memes["discomfort"] = 1.0
    child.meters["tummy_ache"] = 1.0
    child.meters["gastritis"] = 1.0
    world.say(
        f"The bumps gave {child.id} gastritis, and {child.pronoun('possessive')} tummy went grumbly and sore."
    )

    child.memes["sad"] = 1.0
    parent.memes["worry"] = 1.0
    world.say(
        f"The parent came near and said, 'No more tumbles now; let's mend the mood with {remedy.phrase}.'"
    )
    child.memes["reconciliation"] = 1.0
    child.memes["joy"] = 2.0
    child.meters["rested"] = 1.0
    world.say(
        f"{child.id} {remedy.action}, and soon {child.pronoun()} {remedy.effect}. "
        f"{child.id} and {parent.label} shared a soft smile, and the quarrel faded into reconciliation."
    )
    world.say(
        f"By and by, the satchel sat still, the tummy was quiet, and the nursery was snug again."
    )

    world.facts = {
        "child": child,
        "parent": parent,
        "satchel": satchel,
        "activity": activity,
        "remedy": remedy,
        "place": params.place,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    return [
        f'Write a short nursery-rhyme-like story about {child.id}, a satchel, and {act.keyword} play.',
        f"Tell a gentle story where {child.id} gets gastritis after trying to {act.motion} with a satchel.",
        "Write a tiny rhyme that ends with reconciliation after a tummy ache and a caring remedy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    act: Activity = f["activity"]
    remedy: Remedy = f["remedy"]
    return [
        QAItem(
            question=f"What did {child.id} love to do?",
            answer=f"{child.id} loved to {act.motion}.",
        ),
        QAItem(
            question=f"What caused {child.id} to feel unwell?",
            answer=f"The bumping and tumbling with the satchel gave {child.id} gastritis.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label} make peace?",
            answer=f"They shared {remedy.phrase}, and their worry turned into reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satchel?",
            answer="A satchel is a small bag with a strap, often used to carry books or treasures.",
        ),
        QAItem(
            question="What does acrobatic mean?",
            answer="Acrobatic means full of flips, balances, and lively body moves.",
        ),
        QAItem(
            question="What is gastritis?",
            answer="Gastritis is when the stomach lining gets irritated and the tummy feels sore or upset.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or hurt feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satchel?",
            answer="A satchel is a small bag with a strap, often used to carry books or treasures.",
        ),
        QAItem(
            question="What does acrobatic mean?",
            answer="Acrobatic means full of flips, balances, and lively body moves.",
        ),
        QAItem(
            question="What is gastritis?",
            answer="Gastritis is when the stomach lining gets irritated and the tummy feels sore or upset.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or hurt feeling.",
        ),
    ]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print("  ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                activity="acrobatic",
                prize="satchel",
                remedy="tea" if place != "garden" else "rest",
                name="Mina",
                gender="girl",
                parent="mother",
                trait="tiny",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
