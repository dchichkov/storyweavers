#!/usr/bin/env python3
"""
storyworlds/worlds/thicket_tidal_pool_repetition_conflict_reconciliation_heartwarming.py
========================================================================================

A standalone story world for a tidal-pool tale with repetition, conflict, and reconciliation.

Domain: A child wants to explore the tidal pool over and over, despite warnings about
slippery rocks and deep water. The caregiver repeatedly says no, a conflict builds,
and finally a compromise (water shoes) allows safe exploration. The word "thicket" refers
to the seaweed thicket that grows in the tidal pool.
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
MESS_KINDS = {"wet", "slippery"}
REGIONS = {"feet", "legs", "torso"}


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain-specific dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the tidal pool"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = "sunny"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_repeat_conflict(world: World) -> list[str]:
    """Each repeated desire increases defiance and conflict markers."""
    for actor in world.characters():
        if actor.memes["repeat_want"] < THRESHOLD * 2:
            continue
        sig = ("repeat_conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="repeat_conflict", tag="social", apply=_r_repeat_conflict),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs – state-driven prose with repetition
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "explore": "the water sparkled and the seaweed thicket swayed, full of tiny crabs and shells",
    }.get(activity.id, "it made the day feel like an adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if not setting.indoor:
        return "The sun sparkled on the shallow water, and a thicket of green seaweed swayed gently in the pool."
    return ""


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved the sea and all its secrets.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved playing outside and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} as if the day had been made specially for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One sunny day, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants_repeatedly(world: World, hero: Entity, parent: Entity,
                     activity: Activity, repetitions: int) -> None:
    """Simulate repetition: the child asks multiple times, building defiance."""
    for i in range(repetitions):
        hero.memes["desire"] += 1
        hero.memes["repeat_want"] += 1
        if i == 0:
            world.say(
                f"{hero.id} wanted to {activity.verb} right away, but "
                f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
            )
        else:
            world.say(
                f'"Please? I just want to look at the crabs!" {hero.id} said again.'
            )
        # Each time the caregiver says no
        world.say(
            f'"{hero.pronoun().capitalize()} know the rocks are slippery,' 
            f'" {parent.label_word} said gently. "Not yet, my little explorer."'
        )
        # Increase defiance after repeated refusals
        hero.memes["defiance"] += 0.3
        propagate(world, narrate=False)


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to explore was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can want to {activity.verb}, and we can still choose the safe way."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {activity.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled. '
        f'"How about we {gear_def.prep} and then you can {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s do it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_clean(hero, prize)}, and {parent.label_word} was laughing beside "
        f"{hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# Screenplay – with repetition baked in
# ---------------------------------------------------------------------------
REPETITIONS_DEFAULT = 3

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother",
         repetitions: int = REPETITIONS_DEFAULT) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 – Setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – Repetition + conflict
    world.para()
    arrive(world, hero, parent, activity)
    wants_repeatedly(world, hero, parent, activity, repetitions)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 – Reconciliation
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None,
                       repetitions=repetitions)
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "tidal_pool": Setting(place="the tidal pool", indoor=False, affords={"explore"}),
    "rocky_shore": Setting(place="the rocky shore", indoor=False, affords={"explore"}),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="explore the tidal pool",
        gerund="exploring the tidal pool",
        rush="wade deeper into the water",
        mess="wet",
        soil="wet and slippery",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="tidal pool",
        tags={"explore", "wet", "slippery"},
    ),
}

GEAR = [
    Gear(
        id="water_shoes",
        label="water shoes",
        covers={"feet"},
        guards={"wet", "slippery"},
        prep="go home and put on your water shoes",
        tail="walked back home to get the water shoes",
        plural=True,
    ),
    Gear(
        id="waders",
        label="a pair of waders",
        covers={"legs"},
        guards={"wet", "slippery"},
        prep="put on your waders first",
        tail="went to get the waders",
        plural=True,
    ),
]

PRIZES = {
    "sandals": Prize(
        label="sandals",
        phrase="a new pair of sandals with shiny buckles",
        type="sandals",
        region="feet",
        plural=True,
    ),
    "swimsuit": Prize(
        label="swimsuit",
        phrase="a bright new swimsuit with fish patterns",
        type="swimsuit",
        region="legs",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "playful", "stubborn", "spirited", "lively"]

# Map gear to prize region for compatibility
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    repetitions: int = REPETITIONS_DEFAULT
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tidal pool": [("What is a tidal pool?",
                    "A tidal pool is a small pool of seawater left among the rocks "
                    "when the tide goes out. It is full of little sea creatures.")],
    "explore": [("Why is it important to be careful when exploring a tidal pool?",
                 "Tidal pools have slippery rocks and deep holes. You could get wet "
                 "or hurt your feet, so it is good to wear protective shoes.")],
    "wet": [("Why do wet clothes feel cold?",
             "Water draws heat away from your skin, so wet clothes make you feel cold.")],
    "slippery": [("Why are wet rocks slippery?",
                  "A thin layer of water on the rock makes your shoes slide easily. "
                  "That is why you need to hold someone's hand.")],
    "water shoes": [("What are water shoes?",
                     "Water shoes are special shoes that have rubber soles. They "
                     "protect your feet from sharp rocks and help you not slip.")],
    "seaweed": [("What is a thicket of seaweed?",
                 "A thicket of seaweed is a dense patch of underwater plants that "
                 "grow in shallow water. Small crabs and shrimp hide in it.")],
}
KNOWLEDGE_ORDER = ["tidal pool", "explore", "wet", "slippery", "water shoes", "seaweed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child who '
        f'wants to explore a tidal pool" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} again and again, but {hero.pronoun('possessive')} {parent.label_word} "
        f"worries about {prize.phrase}, and they find a happy compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with a parent '
        f"and child playing together safely in the tidal pool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a sunny day, and {hero.id} is "
                f"wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} want to do over and over at {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} wanted to {act.verb} again and again. "
                f"{pos.capitalize()} {pw} said no each time because {pos} {prize.label} "
                f"could get {act.soil}."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} buy for the "
                f"trip to {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and wore {prize.it()} to the tidal pool."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "wet and slippery")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} was upset because if {hero.id} went to "
                f"{act.verb}, {pos} {prize.label} would get {soil}. "
                f"When {hero.id} kept asking and tried to wade deeper, {pos} {pw} "
                f"held {pos} hand and said they could still explore safely."
            ),
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} {act.verb} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} without ruining {pos} {prize.label}. "
                f"The plan let {obj} play while {pos} {prize.label} stayed clean."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} agreed to the {gear_plan} "
                f"plan?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw} once they agreed "
                f"on the plan. At the end, {sub} was {act.gerund} with {pw} laughing nearby."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    # Always include tidal pool and seaweed (setting key)
    tags.add("tidal pool")
    tags.add("seaweed")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated set (used by --all) – all valid combos with repetition variance
CURATED = [
    StoryParams(
        place="tidal_pool",
        activity="explore",
        prize="sandals",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
        repetitions=3,
    ),
    StoryParams(
        place="rocky_shore",
        activity="explore",
        prize="swimsuit",
        name="Leo",
        gender="boy",
        parent="father",
        trait="spirited",
        repetitions=2,
    ),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the parent has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interfaces
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child explores a tidal pool (repetition, conflict, reconciliation).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--repetitions", type=int, default=REPETITIONS_DEFAULT,
                    help="number of times the child asks (>=1)")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    reps = max(1, args.repetitions)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        repetitions=reps,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent,
                 repetitions=params.repetitions)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
```
