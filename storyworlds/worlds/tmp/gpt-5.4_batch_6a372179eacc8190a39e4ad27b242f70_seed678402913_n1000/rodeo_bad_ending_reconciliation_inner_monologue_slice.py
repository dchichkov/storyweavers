#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py
==================================================================================

A small story world about an ordinary family rodeo day that goes wrong before it
gets mended. A child wants to shine at the rodeo, takes a loved one's lucky item
without asking, has a bad run while feeling guilty, and then chooses honesty and
reconciliation.

The world keeps both physical state ("meters") and emotional state ("memes").
The prose is driven by those states: guilt distracts the rider, distraction causes
a bad run, hurt feelings rise, and a full apology repairs the relationship.

Run it
------
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py --event barrels --item bandana
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py --repair shrug
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py --all
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py --qa --json
    python storyworlds/worlds/gpt-5.4/rodeo_bad_ending_reconciliation_inner_monologue_slice.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Event:
    id: str
    label: str
    place: str
    motion: str
    mishap: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LuckyItem:
    id: str
    label: str
    phrase: str
    owner_role: str
    suits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    returns_item: bool
    owns_truth: bool
    comforts_owner: bool
    line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_guilt_distracts(world: World) -> list[str]:
    rider = world.get("rider")
    if rider.memes["guilt"] < THRESHOLD:
        return []
    sig = ("guilt_distracts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rider.meters["focus"] -= 1
    rider.memes["worry"] += 1
    return []


def _r_distraction_bad_run(world: World) -> list[str]:
    rider = world.get("rider")
    if rider.meters["focus"] > 0:
        return []
    sig = ("bad_run",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rider.meters["score"] -= 1
    rider.meters["mistake_on_run"] += 1
    rider.memes["shame"] += 1
    world.get("helper").memes["hurt"] += 1
    return []


def _r_honesty_repairs(world: World) -> list[str]:
    rider = world.get("rider")
    helper = world.get("helper")
    item = world.get("item")
    if rider.memes["honesty"] < THRESHOLD:
        return []
    if item.meters["returned"] < THRESHOLD:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rider.memes["relief"] += 1
    rider.memes["guilt"] = 0.0
    helper.memes["hurt"] = 0.0
    helper.memes["forgiveness"] += 1
    rider.memes["love"] += 1
    helper.memes["love"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="guilt_distracts", tag="emotion", apply=_r_guilt_distracts),
    Rule(name="bad_run", tag="physical", apply=_r_distraction_bad_run),
    Rule(name="repair", tag="social", apply=_r_honesty_repairs),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        fired_now = len(world.fired)
        if fired_now:
            changed = any(sig[0] in {"guilt_distracts", "bad_run", "repair"} for sig in world.fired) and False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_suits_event(item: LuckyItem, event: Event) -> bool:
    return event.id in item.suits


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_works(repair: Repair) -> bool:
    return repair.returns_item and repair.owns_truth and repair.comforts_owner and repair.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for event_id, event in EVENTS.items():
        for item_id, item in ITEMS.items():
            if not item_suits_event(item, event):
                continue
            for repair_id, repair in REPAIRS.items():
                if repair_works(repair):
                    combos.append((event_id, item_id, repair_id))
    return combos


def explain_item_rejection(item: LuckyItem, event: Event) -> str:
    return (
        f"(No story: {item.phrase} does not fit a {event.label} run in this world. "
        f"The lucky item should be something the rider could naturally wear or carry at the {event.place}.)"
    )


def explain_repair_rejection(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    return (
        f"(Refusing repair '{repair_id}': it is too weak for real reconciliation "
        f"(sense={repair.sense} < {SENSE_MIN} or it skips honesty, return, or comfort). "
        f"Try one of: {', '.join(sorted(r.id for r in sensible_repairs()))}.)"
    )


def predict_bad_run(world: World) -> dict:
    sim = world.copy()
    rider = sim.get("rider")
    rider.memes["guilt"] += 1
    propagate(sim, narrate=False)
    return {
        "focus": rider.meters["focus"],
        "mistake": rider.meters["mistake_on_run"] >= THRESHOLD,
    }


def introduce(world: World, rider: Entity, helper: Entity, event: Event, item: LuckyItem) -> None:
    rider.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On Saturday morning, {rider.id} and {helper.id} drove to the small-town rodeo at {event.place}. "
        f"The arena smelled like dust, leather, and warm hay."
    )
    world.say(
        f"{rider.id} was signed up for the {event.label}, and {helper.id} had brought {item.phrase}. "
        f"It was the kind of ordinary lucky thing families keep for years."
    )


def longing(world: World, rider: Entity, helper: Entity, item: LuckyItem) -> None:
    world.say(
        f"{helper.id} set {item.phrase} on the truck seat while helping with the last little chores. "
        f"{rider.id} kept glancing at it."
    )
    world.say(
        f'Inside, {rider.pronoun()} thought, "If I wear it, maybe today will finally go right."'
    )


def take_without_asking(world: World, rider: Entity, helper: Entity, item: Entity) -> None:
    item.owner = helper.id
    item.attrs["borrowed_without_asking"] = True
    item.meters["taken"] += 1
    rider.memes["guilt"] += 1
    rider.memes["want"] += 1
    world.say(
        f"When {helper.id} turned away for a moment, {rider.id} slipped the {item.label} into place without asking. "
        f"It felt brave for half a second and wrong right after."
    )
    world.say(
        f'Inside, {rider.pronoun()} thought, "I can put it back before {helper.id} notices."'
    )


def pre_run_warning(world: World, rider: Entity, helper: Entity, event: Event) -> None:
    pred = predict_bad_run(world)
    world.facts["predicted_focus"] = pred["focus"]
    world.facts["predicted_mistake"] = pred["mistake"]
    if pred["mistake"]:
        world.say(
            f"But the closer they came to the gate for the {event.label}, the less steady {rider.id} felt. "
            f"The secret sat in {rider.pronoun('possessive')} chest like a pebble in a boot."
        )


def bad_run(world: World, rider: Entity, helper: Entity, event: Event) -> None:
    propagate(world, narrate=False)
    world.say(
        f"When the announcer called {rider.id}'s name, {rider.pronoun()} started {event.motion}. "
        f"Then {event.mishap}."
    )
    world.say(
        f"The run ended badly. It was not a big movie kind of disaster, only the hard little kind that makes your eyes sting in public."
    )
    world.say(
        f'Inside, {rider.pronoun()} thought, "I did not lose because of the arena. I lost because I was hiding something."'
    )


def discovery(world: World, rider: Entity, helper: Entity, item: Entity) -> None:
    helper.memes["hurt"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Back by the rail, {helper.id} saw the {item.label} and went quiet. "
        f'"You took it?" {helper.pronoun()} asked.'
    )
    world.say(
        f"{rider.id} could have shrugged or pretended it was no big deal, but the bad run was still buzzing in {rider.pronoun('possessive')} ears."
    )


def reconcile(world: World, rider: Entity, helper: Entity, item: Entity, repair: Repair, event: Event) -> None:
    item.meters["returned"] += 1
    rider.memes["honesty"] += 1
    world.say(repair.line.format(rider=rider.id, helper=helper.id, item=item.label))
    propagate(world, narrate=False)
    if helper.memes["forgiveness"] >= THRESHOLD:
        world.say(
            f"{helper.id} took the {item.label} back and let out the breath {helper.pronoun()} had been holding. "
            f"{helper.pronoun().capitalize()} was still hurt, but not shut tight anymore."
        )
        world.say(
            f'"Next time, ask me first," {helper.id} said. "{event.ending_image}"'
        )


def closing(world: World, rider: Entity, helper: Entity, event: Event) -> None:
    world.say(
        f"{rider.id} nodded. The ribbon was gone, the run was over, and the day had not turned into a victory story."
    )
    world.say(
        f"But on the walk back past the chutes, {rider.id} stayed beside {helper.id}. "
        f"The rodeo still rattled and cheered behind them, and this time the quiet between them felt repaired."
    )


def tell(
    event: Event,
    item_cfg: LuckyItem,
    repair: Repair,
    rider_name: str = "Maya",
    rider_gender: str = "girl",
    helper_name: str = "Tess",
    helper_gender: str = "girl",
    helper_role: str = "sister",
    adult_type: str = "mother",
) -> World:
    world = World()
    rider = world.add(Entity(id="rider", kind="character", type=rider_gender, label=rider_name, role="rider"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role=helper_role))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the parent", role="parent"))
    item = world.add(Entity(id="item", kind="thing", type="lucky_item", label=item_cfg.label, phrase=item_cfg.phrase, owner="helper", tags=set(item_cfg.tags)))

    rider.meters["focus"] = 1
    rider.meters["score"] = 1
    helper.memes["trust"] = 1
    world.facts["adult"] = adult

    introduce(world, rider, helper, event, item_cfg)
    world.para()
    longing(world, rider, helper, item_cfg)
    take_without_asking(world, rider, helper, item)
    pre_run_warning(world, rider, helper, event)
    world.para()
    bad_run(world, rider, helper, event)
    discovery(world, rider, helper, item)
    world.para()
    reconcile(world, rider, helper, item, repair, event)
    closing(world, rider, helper, event)

    world.facts.update(
        rider=rider,
        helper=helper,
        item=item,
        event=event,
        repair=repair,
        bad_run=rider.meters["mistake_on_run"] >= THRESHOLD,
        reconciled=helper.memes["forgiveness"] >= THRESHOLD,
        owner_role=item_cfg.owner_role,
    )
    return world


@dataclass
class StoryParams:
    event: str
    item: str
    repair: str
    rider_name: str
    rider_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    adult: str
    seed: Optional[int] = None


EVENTS = {
    "barrels": Event(
        id="barrels",
        label="barrel pattern",
        place="the county fairgrounds",
        motion="fast around the first barrel",
        mishap="one turn came wide, then another, and the whole pattern unraveled",
        ending_image="We can go watch the sun hit the arena fence and start over there",
        tags={"rodeo", "barrels"},
    ),
    "goats": Event(
        id="goats",
        label="goat-tying event",
        place="the practice pens behind the grandstand",
        motion="out of the gate with quick hands and a racing heart",
        mishap="the knot slipped, and precious seconds kept falling away",
        ending_image="We can sit by the pens for a minute and let the dust settle",
        tags={"rodeo", "goats"},
    ),
    "flags": Event(
        id="flags",
        label="flag race",
        place="the little rodeo ring by the 4-H barn",
        motion="toward the bucket with everyone leaning forward to watch",
        mishap="the flag bobbled at the bucket and the smooth run broke apart",
        ending_image="We can walk one quiet lap together before the next class starts",
        tags={"rodeo", "flags"},
    ),
}

ITEMS = {
    "bandana": LuckyItem(
        id="bandana",
        label="bandana",
        phrase="a faded red bandana",
        owner_role="sister",
        suits={"barrels", "flags", "goats"},
        tags={"bandana", "luck"},
    ),
    "concho": LuckyItem(
        id="concho",
        label="silver concho",
        phrase="a small silver concho for a belt",
        owner_role="cousin",
        suits={"barrels", "flags"},
        tags={"concho", "luck"},
    ),
    "glove": LuckyItem(
        id="glove",
        label="rope glove",
        phrase="a soft rope glove darkened with use",
        owner_role="uncle",
        suits={"goats"},
        tags={"glove", "luck"},
    ),
}

REPAIRS = {
    "full_apology": Repair(
        id="full_apology",
        sense=3,
        returns_item=True,
        owns_truth=True,
        comforts_owner=True,
        line='"I took your {item} because I wanted some of your luck," {rider} said. "I should have asked first. I am sorry, and here it is back."',
        qa_text="gave the item back, told the truth, and apologized plainly",
        tags={"apology", "truth"},
    ),
    "sit_and_talk": Repair(
        id="sit_and_talk",
        sense=3,
        returns_item=True,
        owns_truth=True,
        comforts_owner=True,
        line='{rider} handed the {item} back and sat on the fence rail beside {helper}. "I was scared I would mess up, so I stole a piece of your luck. That was unfair. I am sorry."',
        qa_text="returned the item and admitted the fear underneath the mistake",
        tags={"apology", "truth"},
    ),
    "shrug": Repair(
        id="shrug",
        sense=1,
        returns_item=False,
        owns_truth=False,
        comforts_owner=False,
        line='{rider} only shrugged and said it should not matter so much.',
        qa_text="shrugged it off",
        tags={"dismissal"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Tessa", "Ava", "Ella", "Lucy", "Zoe"]
BOY_NAMES = ["Cole", "Ben", "Jack", "Luke", "Eli", "Sam", "Noah", "Finn"]


def pair_name(ent: Entity) -> str:
    return ent.label or ent.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rider = pair_name(f["rider"])
    helper = pair_name(f["helper"])
    event = f["event"]
    item = f["item"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "rodeo" and a child\'s inner monologue.',
        f"Tell a gentle but sad story where {rider} secretly takes {helper}'s {item.label} before a {event.label} at the rodeo, has a bad run, and then makes things right.",
        f"Write a quiet reconciliation story set at a small rodeo, where guilt causes a mistake and honesty repairs the relationship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    helper = f["helper"]
    event = f["event"]
    item = f["item"]
    repair = f["repair"]
    rider_name = pair_name(rider)
    helper_name = pair_name(helper)
    qa = [
        (
            "Who is the story about?",
            f"It is about {rider_name}, who wanted a good day at the rodeo, and {helper_name}, whose lucky {item.label} was taken without asking."
        ),
        (
            f"Why did {rider_name} take the {item.label}?",
            f"{rider_name} wanted some extra luck before the {event.label}. Inside, the wish to do well felt bigger than good judgment for a moment."
        ),
        (
            f"Why did the run go badly?",
            f"The run went badly because {rider_name} felt guilty and distracted. The secret kept pulling at {rider.pronoun('possessive')} thoughts, so {rider.pronoun()} could not stay fully focused."
        ),
        (
            f"How did {helper_name} feel after noticing the {item.label}?",
            f"{helper_name} felt hurt and surprised. The problem was not only the object itself, but that trust had been bent by taking it in secret."
        ),
    ]
    if f["reconciled"]:
        qa.append(
            (
                f"How did {rider_name} and {helper_name} make up?",
                f"{rider_name} {repair.qa_text}. That mattered because the apology named the real wrong and gave back what had been taken."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The day still had a bad result at the rodeo, but the two of them walked back together in peace. The ending proves that a lost run can still turn into a repaired relationship."
            )
        )
    return qa


KNOWLEDGE = {
    "rodeo": [
        (
            "What is a rodeo?",
            "A rodeo is an event where people ride, race, or handle animals in different contests. Families often watch and cheer from the stands."
        )
    ],
    "bandana": [
        (
            "What is a bandana?",
            "A bandana is a square piece of cloth that people can tie around the neck or head. It is light and easy to wear."
        )
    ],
    "concho": [
        (
            "What is a concho?",
            "A concho is a round metal decoration, often used on western belts or tack. It can be shiny and special to the person who wears it."
        )
    ],
    "glove": [
        (
            "Why might someone wear a riding or rope glove?",
            "A glove can help protect the hand and give a better grip. Some people also get attached to one lucky glove they use again and again."
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what the person did wrong and does not hide from the truth. It also tries to repair the harm, not just end the uncomfortable moment."
        )
    ],
    "truth": [
        (
            "Why does telling the truth help after a mistake?",
            "Telling the truth lets other people understand what really happened. That makes it easier to fix the problem and rebuild trust."
        )
    ],
    "luck": [
        (
            "Can a lucky item do the hard work for you?",
            "No. A lucky item may help someone feel brave, but it cannot replace practice, focus, or honesty."
        )
    ],
}

KNOWLEDGE_ORDER = ["rodeo", "bandana", "concho", "glove", "luck", "apology", "truth"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rodeo"} | set(world.facts["item"].tags) | set(world.facts["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label and ent.label != eid:
            bits.append(f"label={ent.label!r}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {eid:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        event="barrels",
        item="bandana",
        repair="full_apology",
        rider_name="Maya",
        rider_gender="girl",
        helper_name="Tess",
        helper_gender="girl",
        helper_role="sister",
        adult="mother",
    ),
    StoryParams(
        event="goats",
        item="glove",
        repair="sit_and_talk",
        rider_name="Cole",
        rider_gender="boy",
        helper_name="Ray",
        helper_gender="boy",
        helper_role="uncle",
        adult="father",
    ),
    StoryParams(
        event="flags",
        item="concho",
        repair="full_apology",
        rider_name="Nora",
        rider_gender="girl",
        helper_name="June",
        helper_gender="girl",
        helper_role="cousin",
        adult="mother",
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(E, I, R) :- event(E), item(I), repair(R), suits(I, E), repair_works(R).
repair_works(R) :- repair(R), sense(R, S), sense_min(M), S >= M,
                   returns_item(R), owns_truth(R), comforts_owner(R).

% --- outcome model ---------------------------------------------------------
guilt.
distracted :- guilt.
bad_run :- distracted.
reconciled :- chosen_repair(R), repair_works(R).

outcome(bad_then_reconciled) :- bad_run, reconciled.
outcome(bad_and_unrepaired)  :- bad_run, not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for suit in sorted(item.suits):
            lines.append(asp.fact("suits", item_id, suit))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        if repair.returns_item:
            lines.append(asp.fact("returns_item", repair_id))
        if repair.owns_truth:
            lines.append(asp.fact("owns_truth", repair_id))
        if repair.comforts_owner:
            lines.append(asp.fact("comforts_owner", repair_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_repair", params.repair)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "bad_then_reconciled" if repair_works(REPAIRS[params.repair]) else "bad_and_unrepaired"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params)
            break
    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a small rodeo day goes badly, then honesty repairs a hurt relationship."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_person(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def helper_role_for_item(item_id: str) -> str:
    return ITEMS[item_id].owner_role


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.event and args.item and not item_suits_event(ITEMS[args.item], EVENTS[args.event]):
        raise StoryError(explain_item_rejection(ITEMS[args.item], EVENTS[args.event]))
    if args.repair and not repair_works(REPAIRS[args.repair]):
        raise StoryError(explain_repair_rejection(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.item is None or combo[1] == args.item)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, item_id, repair_id = rng.choice(sorted(combos))
    rider_name, rider_gender = pick_person(rng)
    helper_name, helper_gender = pick_person(rng, avoid=rider_name)
    helper_role = helper_role_for_item(item_id)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        event=event_id,
        item=item_id,
        repair=repair_id,
        rider_name=rider_name,
        rider_gender=rider_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if not item_suits_event(ITEMS[params.item], EVENTS[params.event]):
        raise StoryError(explain_item_rejection(ITEMS[params.item], EVENTS[params.event]))
    if not repair_works(REPAIRS[params.repair]):
        raise StoryError(explain_repair_rejection(params.repair))

    world = tell(
        event=EVENTS[params.event],
        item_cfg=ITEMS[params.item],
        repair=REPAIRS[params.repair],
        rider_name=params.rider_name,
        rider_gender=params.rider_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
        adult_type=params.adult,
    )

    story = world.render().replace("rider", params.rider_name).replace("helper", params.helper_name)
    story = story.replace("  ", " ")

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, item, repair) combos:\n")
        for event_id, item_id, repair_id in combos:
            print(f"  {event_id:8} {item_id:8} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.rider_name}: {p.event} with {p.item} ({p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
