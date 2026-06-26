#!/usr/bin/env python3
"""
A small standalone storyworld about an animal child at a bus stop who wants to
do something messy or unwise, gets a caution, throws a tantrum, and then
reconciles with a helper.

Seed story shape:
- A small animal character waits at a bus stop.
- The child wants to wring a wet item.
- A parent or caretaker warns that doing it there is not a good idea.
- The child has a tantrum.
- They calm down, find a better way, and reconcile.

This script follows the Storyworld contract and provides:
- story generation
- QA generation
- JSON output
- trace output
- inline ASP twin and verification
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
        if self.type in {"mother", "father", "parent", "caretaker"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "boy", "rabbit", "fox", "bear", "cat", "dog", "duck"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def __post_init__(self) -> None:
        for k in ["wet", "mess", "conflict", "tantrum", "calm", "worry", "relief", "trust"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the bus stop"
    affords: set[str] = field(default_factory=lambda: {"wait", "wring", "talk"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    caution: str
    caution_reason: str
    mess: str = "wet"
    zone: set[str] = field(default_factory=lambda: {"hands"})
    keyword: str = "wring"
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    wettable: bool = True
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def trace(self) -> str:
        lines = [f"setting={self.setting.place}"]
        for e in self.entities.values():
            bits = []
            wet = {k: v for k, v in e.meters.items() if v}
            mem = {k: v for k, v in e.memes.items() if v}
            if wet:
                bits.append(f"meters={wet}")
            if mem:
                bits.append(f"memes={mem}")
            if e.label:
                bits.append(f"label={e.label}")
            if e.worn_by:
                bits.append(f"worn_by={e.worn_by}")
            lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
        lines.append(f"fired={sorted(self.fired)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bus_stop": Setting(place="the bus stop"),
}

ACTIVITIES = {
    "wring": Activity(
        id="wring",
        verb="wring out the wet cloth",
        gerund="wringing out the wet cloth",
        rush="grab the cloth and wring it hard",
        caution="Don't wring that here",
        caution_reason="it will splash water everywhere at the bus stop",
        tags={"wring", "wet", "cautionary"},
    ),
}

ITEMS = {
    "scarf": Item(
        id="scarf",
        label="scarf",
        phrase="a soft little scarf",
        type="scarf",
        region="hands",
        wettable=True,
    ),
}

GEAR = {
    "bucket": Gear(
        id="bucket",
        label="a small bucket",
        helps={"wring"},
        prep="let's carry the wet scarf to the bucket",
        tail="walked over to the bucket so the water could drip safely",
    ),
}

ANIMAL_TYPES = ["rabbit", "fox", "bear", "cat", "dog", "duck"]
NAMES = {
    "rabbit": ["Pip", "Milo", "Bibi", "Tobi"],
    "fox": ["Finn", "Nora", "Rory", "Lila"],
    "bear": ["Moss", "Hugo", "Bea", "Penny"],
    "cat": ["Mimi", "Coco", "Pip", "Tess"],
    "dog": ["Bax", "Sunny", "Pippa", "Toto"],
    "duck": ["Dot", "Quinn", "Mina", "Peep"],
}
TRAITS = ["curious", "small", "cheerful", "spirited", "squirmy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "bus_stop"
    activity: str = "wring"
    item: str = "scarf"
    name: str = "Pip"
    animal: str = "rabbit"
    helper: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the activity and item fit the place and the child can be
% cautioned, then reconciled through a compatible helper plan.
valid_place(P) :- setting(P).
valid_activity(A) :- activity(A), cautionary(A).
valid_item(I) :- item(I), wettable(I).
valid_story(P,A,I) :- valid_place(P), valid_activity(A), valid_item(I), place_has(P,A,I).
needs_caution(A,I) :- cautionary(A), wet(I).
can_reconcile(A) :- reconciliation(A).

valid_combination(P,A,I) :- valid_story(P,A,I), needs_caution(A,I), can_reconcile(A).
#show valid_combination/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if "cautionary" in a.tags:
            lines.append(asp.fact("cautionary", aid))
        if "reconciliation" in a.tags:
            lines.append(asp.fact("reconciliation", aid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.wettable:
            lines.append(asp.fact("wettable", iid))
        lines.append(asp.fact("wet", iid))
    for pid in SETTINGS:
        for aid in ACTIVITIES:
            for iid in ITEMS:
                lines.append(asp.fact("place_has", pid, aid, iid))
    return "\n".join(lines)

def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combination")))

def asp_verify() -> int:
    py = set(valid_combos())
    aspr = set(asp_valid())
    if py == aspr:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - aspr))
    print("asp-only:", sorted(aspr - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for a_id, a in ACTIVITIES.items():
            for i_id, it in ITEMS.items():
                if p == "bus_stop" and a_id == "wring" and it.id == "scarf":
                    combos.append((p, a_id, i_id))
    return combos

def explain_rejection(place: str, activity: str, item: str) -> str:
    return (
        f"(No story: {activity} with {item} is not a reasonable bus stop tale "
        f"for this world.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    animal_name = params.name
    helper_name = "Parent"

    child = world.add(Entity(
        id=animal_name,
        kind="character",
        type=params.animal,
        label=animal_name,
        memes={"worry": 0.0, "tantrum": 0.0, "calm": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=params.helper,
        label="the parent",
        memes={"worry": 0.0, "calm": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label="scarf",
        phrase="a soft little scarf",
        owner=child.id,
        caretaker=helper.id,
        worn_by=child.id,
        plural=False,
    ))

    activity = ACTIVITIES[params.activity]
    gear = GEAR["bucket"]

    # Act 1: setup.
    world.say(f"{child.id} was a little {params.trait} {params.animal} who waited at the bus stop with {item.phrase}.")
    world.say(f"{child.id} loved {activity.gerund}, because water felt funny on {child.pronoun('possessive')} paws.")
    world.para()

    # Act 2: caution and tantrum.
    world.say(f"One gray morning, {child.id} lifted {item.label} and wanted to {activity.verb}.")
    world.say(f"{helper.label} shook {helper.pronoun('possessive')} head. \"{activity.caution},\" {helper.pronoun()} said, because {activity.caution_reason}.")
    helper.memes["worry"] += 1
    child.memes["worry"] += 1
    child.meters["wet"] += 1
    world.say(f"{child.id} did not like that answer.")
    child.memes["tantrum"] += 1
    child.memes["conflict"] += 1
    world.say(f"{child.id} had a tantrum, stamping {child.pronoun('possessive')} feet and hugging {item.it()} tight.")
    world.say(f"The bus stop bench looked small, and the puddle beside it looked even smaller, which made the mess feel bigger.")
    world.para()

    # Act 3: reconciliation.
    world.say(f"Then {helper.label} knelt down and pointed to {gear.label}.")
    world.say(f"\"How about we {gear.prep}?\" {helper.pronoun()} asked.")
    world.say(f"{child.id} sniffled, then looked at the bucket and the wet scarf.")
    child.memes["calm"] += 1
    child.memes["trust"] += 1
    child.memes["tantrum"] = 0.0
    child.memes["conflict"] = 0.0
    helper.memes["relief"] += 1
    world.say(f"{child.id} nodded, and together they {gear.tail}.")
    world.say(f"After that, {child.id} could {activity.gerund} without splashing anyone, and {item.label} stayed neat enough to wear again.")
    world.say(f"{child.id} leaned against {helper.label} as the bus came, calm at last.")

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        activity=activity,
        gear=gear,
        place=params.place,
        reconciled=True,
        tantrum=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    activity: Activity = f["activity"]
    item: Entity = f["item"]
    return [
        f'Write a short Animal Story about {child.id} at a bus stop with {item.label}, where a warning leads to a tantrum and then reconciliation.',
        f'Tell a gentle story for a child who wants to {activity.verb} at the bus stop but learns a safer way.',
        f'Write a small story that includes the words "tantrum" and "{activity.keyword}" and ends calmly.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    activity: Activity = f["activity"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {child.id} get upset at the bus stop?",
            answer=f"{child.id} got upset because {helper.label} stopped {child.id} from {activity.verb} right there. The caution was about keeping the bus stop safe and dry.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {item.label}?",
            answer=f"{child.id} wanted to {activity.verb} with the {item.label}. {child.id} liked the feel of water, but that idea caused trouble at the bus stop.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.label} make things better?",
            answer=f"They used {gear.label} and moved the wet scarf to a safer place. That helped {child.id} calm down and reconcile with {helper.label}.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus stop?",
            answer="A bus stop is a place where people wait for a bus to arrive.",
        ),
        QAItem(
            question="What does it mean to wring something out?",
            answer="To wring something out means to twist it so water drips out.",
        ),
        QAItem(
            question="What is a tantrum?",
            answer="A tantrum is a big upset outburst, like crying, stomping, or yelling when something feels unfair.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a disagreement and feel friendly again.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: tantrum, wring, caution, reconciliation, bus stop.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--helper", choices=["mother", "father", "parent", "caretaker"])
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
    if args.place and args.place != "bus_stop":
        raise StoryError("(No story: this seed world only happens at the bus stop.)")
    if args.activity and args.activity != "wring":
        raise StoryError("(No story: this world only supports wringing.)")
    if args.item and args.item != "scarf":
        raise StoryError("(No story: this world only supports the scarf.)")

    place = "bus_stop"
    activity = "wring"
    item = "scarf"
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(NAMES[animal])
    helper = args.helper or rng.choice(["mother", "father", "caretaker"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item, name=name, animal=animal, helper=helper, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid())} compatible combinations:")
        for row in asp_valid():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(animal=a, name=NAMES[a][0])) for a in ANIMAL_TYPES[:5]]
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
