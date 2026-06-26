#!/usr/bin/env python3
"""
storyworlds/worlds/baptize_gait_pulley_misunderstanding_space_adventure.py
==========================================================================

A standalone story world sketch for a space adventure with a misunderstanding
about a baptism (ceremony), a gait (walking style), and a pulley (tool).
Style is "Space Adventure" – child astronaut, parent captain, alien planet.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
MESS_KINDS = {"sandy", "dented", "sticky", "sparkly"}

# Body regions for gear coverage (space suit parts)
REGIONS = {"feet", "legs", "torso", "head", "hands"}


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
        female = {"girl", "mother", "mom", "woman", "captain_f"}
        male = {"boy", "father", "dad", "man", "captain_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label


# ---------------------------------------------------------------------------
# Setting, Activity, Prize, Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
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
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


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

    def copy(self) -> World:
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


def _r_misunderstanding(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["warning"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("misunderstand", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confusion"] += 1
        return ["__misunderstanding__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="misunderstand", tag="social", apply=_r_misunderstanding),
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
                produced.extend(s for s in sents if s != "__misunderstanding__")
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
# Verbs / screenwriting functions
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    details = {
        "moondust": "the soft crunch underfoot felt like stepping on moon cloud",
        "gonylon_plants": "the sticky purple sap sparkled under the twin suns",
        "asteroid_hopping": "the low gravity made each jump feel like flying",
        "spacewalk_repair": "the tools and pulleys made a friendly clanking sound",
    }
    return details.get(activity.id, "it made the journey feel brave and true")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, the control panels hummed."
    if activity.weather == "starry":
        return f"Stars glittered outside the port window, and {setting.place} looked mysterious."
    return f"{setting.place.capitalize()} stretched wide and strange."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean and good"


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
    world.say(f"{hero.id} was a {desc} who dreamed of the stars.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside the ship" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} gave "
        f"{hero.pronoun('object')} {prize.phrase} for the mission."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} like a true explorer."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"starry": "One starry cycle, "}.get(world.weather, "One mission day, ")
    go = "were inside" if world.setting.indoor else "landed on"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(
        f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. '
        f'"First we must baptize you into the crew."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} heard the warning but the adventure was calling. "
        f"{hero.pronoun().capitalize()} tried to {activity.rush},"
    )


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"Wait! You misunderstood. I mean we need the right gait on this planet."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["confusion"] >= THRESHOLD:
        world.say(
            f'{hero.id} frowned. "But I really want to {activity.verb}!" '
            f'{hero.pronoun()} said, confused.'
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
        f'"How about we use the {gear_def.label} and a pulley? '
        f'Then you can {activity.verb} the right way."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["confusion"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s do it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_clean(hero, prize)}, and {parent.label_word} was watching "
        f"with pride."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "captain_m") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the captain"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, gear=gear_def,
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "luna_outpost": Setting(place="Luna Outpost", indoor=False, affords={"moondust", "spacewalk_repair"}),
    "gonylon": Setting(place="Gonylon Planet", indoor=False, affords={"gonylon_plants"}),
    "asteroid_belt": Setting(place="Asteroid Belt", indoor=False, affords={"asteroid_hopping"}),
    "spaceship": Setting(place="the spaceship", indoor=True, affords={"spacewalk_repair"}),
}

ACTIVITIES = {
    "moondust": Activity(
        id="moondust",
        verb="play in the moondust",
        gerund="playing in moondust",
        rush="run toward the crater",
        mess="sandy",
        soil="covered in grey dust",
        zone={"feet", "legs"},
        weather="starry",
        keyword="moondust",
        tags={"dust", "moon"},
    ),
    "gonylon_plants": Activity(
        id="gonylon_plants",
        verb="collect the sticky plants",
        gerund="collecting sticky plants",
        rush="grab the purple leaves",
        mess="sticky",
        soil="sticky and sparkling",
        zone={"torso", "hands"},
        weather="starry",
        keyword="plants",
        tags={"sticky", "sparkle"},
    ),
    "asteroid_hopping": Activity(
        id="asteroid_hopping",
        verb="hop from rock to rock",
        gerund="hopping on asteroids",
        rush="jump to the nearest rock",
        mess="dented",
        soil="dented and dusty",
        zone={"feet", "legs", "torso"},
        weather="starry",
        keyword="asteroid",
        tags={"dented", "gravity"},
    ),
    "spacewalk_repair": Activity(
        id="spacewalk_repair",
        verb="fix the antenna with a pulley",
        gerund="fixing the antenna with a pulley",
        rush="reach for the pulley rope",
        mess="sparkly",
        soil="covered in space sparks",
        zone={"hands", "torso"},
        weather="starry",
        keyword="pulley",
        tags={"pulley", "repair"},
    ),
}

GEAR = [
    Gear(
        id="space_boots",
        label="space boots",
        covers={"feet", "legs"},
        guards={"sandy", "sticky", "dented"},
        prep="put on your space boots and a pulley belt",
        tail="snapped on the space boots and rigged the pulley",
        plural=True,
    ),
    Gear(
        id="spacesuit",
        label="a spacesuit",
        covers={"torso", "hands", "feet", "legs", "head"},
        guards={"sandy", "sticky", "dented", "sparkly"},
        prep="put on your full spacesuit and the pulley harness",
        tail="zipped into the spacesuit and attached the pulley",
    ),
    Gear(
        id="gloves_harness",
        label="sticky gloves and a pulley harness",
        covers={"hands", "torso"},
        guards={"sticky", "sparkly"},
        prep="put on the sticky gloves and the pulley harness",
        tail="pulled on the sticky gloves and buckled the pulley harness",
        plural=True,
    ),
]

PRIZES = {
    "badge": Prize(
        label="badge",
        phrase="a shiny crew badge",
        type="badge",
        region="torso",
        genders={"girl", "boy"},
    ),
    "suit": Prize(
        label="suit",
        phrase="a brand new space suit",
        type="suit",
        region="torso",
        genders={"girl", "boy"},
    ),
    "helmet": Prize(
        label="helmet",
        phrase="a clear helmet with a gold visor",
        type="helmet",
        region="head",
        genders={"girl", "boy"},
    ),
    "boots": Prize(
        label="boots",
        phrase="white boots with red stripes",
        type="boots",
        region="feet",
        plural=True,
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Nova", "Stella", "Lyra", "Andi", "Irissa"]
BOY_NAMES = ["Orion", "Leo", "Atlas", "Kai", "Rigel"]
TRAITS = ["brave", "curious", "adventurous", "stubborn", "kind"]


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
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "dust": [
        ("What is moondust?",
         "Moondust is fine, powdery dirt found on the Moon. It sticks to everything."),
    ],
    "sticky": [
        ("Why are some plants sticky?",
         "Some plants on strange planets have sticky sap to protect themselves."),
    ],
    "dented": [
        ("What does dented mean?",
         "Dented means something got a small dent or bump from being hit."),
    ],
    "pulley": [
        ("What is a pulley used for?",
         "A pulley is a wheel with a rope that helps lift heavy things in space."),
    ],
    "baptize": [
        ("What does 'baptize' mean on a spaceship?",
         "It means a special ceremony to welcome a new crew member."),
    ],
    "gait": [
        ("What is a gait?",
         "A gait is the way someone walks, especially on low-gravity planets."),
    ],
}
KNOWLEDGE_ORDER = ["dust", "sticky", "dented", "pulley", "baptize", "gait"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.id
    return [
        f'Write a short space adventure story for a 4-year-old about a child '
        f'astronaut, a "{kw}", and a misunderstanding.',
        f"Tell a story where {hero.id} wants to {act.verb} but "
        f"{hero.pronoun('possessive')} {parent.label_word} talks about baptizing "
        f"and the proper gait, causing a helpful misunderstanding.",
        f'Write a simple space tale with the words "baptize", "gait", and '
        f'"pulley", ending with a parent and child finding a safe way to play.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"starry": "starry cycle"}.get(world.weather, "mission day")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a {day}, and {hero.id} is "
                f"wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do before the "
                f"misunderstanding?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund}. "
                f"That wish became tricky because {pos} {prize.label} could get messy."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} give for the mission?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and wore {prize.it()} for the outing."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was worried because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then {pw} would have to clean {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} hand and explained about the baptism and the right gait.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} {act.verb} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} and a pulley, so {hero.id} could "
                f"{act.verb} while {pos} {prize.label} stayed clean."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} explained the confusion?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw}. "
                f"At the end {sub} was {act.gerund} with the pulley nearby."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    # always add baptize and gait because they appear in story text
    tags.update({"baptize", "gait"})
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts == "]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions == ")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions == ")
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


CURATED = [
    StoryParams(
        place="luna_outpost",
        activity="moondust",
        prize="boots",
        name="Nova",
        gender="girl",
        parent="captain_m",
        trait="brave",
    ),
    StoryParams(
        place="gonylon",
        activity="gonylon_plants",
        prize="suit",
        name="Atlas",
        gender="boy",
        parent="captain_f",
        trait="curious",
    ),
    StoryParams(
        place="asteroid_belt",
        activity="asteroid_hopping",
        prize="helmet",
        name="Kai",
        gender="boy",
        parent="captain_m",
        trait="adventurous",
    ),
    StoryParams(
        place="spaceship",
        activity="spacewalk_repair",
        prize="badge",
        name="Stella",
        gender="girl",
        parent="captain_f",
        trait="stubborn",
    ),
    StoryParams(
        place="luna_outpost",
        activity="moondust",
        prize="suit",
        name="Orion",
        gender="boy",
        parent="captain_m",
        trait="kind",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region} -- it wouldn't get "
                f"{activity.mess}. Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing protects {noun} "
            f"({prize.region}) from {activity.gerund}. No valid gear.)")


# ---------------------------------------------------------------------------
# ASP
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
# Interface functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space Adventure story: child, misunderstanding, baptism, gait, pulley."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain_f", "captain_m"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: {args.prize} not typical for {args.gender}.)")

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
    parent = args.parent or rng.choice(["captain_m", "captain_f"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity],
        PRIZES[params.prize], params.name, params.gender,
        [params.trait, "stubborn"], params.parent,
    )
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
            print(f"  {place:15} {act:20} {prize:10}  [{', '.join(genders)}]")
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
