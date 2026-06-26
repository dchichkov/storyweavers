#!/usr/bin/env python3
"""
storyworlds/worlds/thicket_tidal_pool_repetition_conflict_reconciliation_heartwarming.py
============================================================================================

A standalone story world sketch for "The Thicket and the Tide" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a little kind girl named Elara. She loved the shore
and finding treasures in the tidal pool. Every morning, her grandmother gave her
a special woven basket to carry her finds.

One tide season, Elara and her grandmother went to the rocky thicket near the
pool. Elara wanted to collect shells and starfish again, but her grandmother
shook her head. "You have taken enough from that thicket, my star. The pool
needs its treasures too." Elara did not want to listen and tried to reach into
the water anyway, but her grandmother gently took her hand. "You must learn to
leave some beauty behind."

Elara pouted and crossed her arms. "But I always collect things from the pool!"
she said. Her grandmother smiled and said, "How about we take only the stories
back today, and leave the shells for the little crabs?" Elara's face lit up and
she hugged her grandmother. "Yes, let's be guardians of the pool!" she said as
they sat together by the thicket, watching the tide rise.

Causal state updates:
---
    do activity                 -> actor.collected += 1
                                 actor.joy += 1
    actor greedy + taken items  -> pool.health -= 1
                                 thicket.bareness += 1
    pool unhealthy              -> actor.grandparent.sadness += 1
    warning ignored             -> actor.defiance += 1
    gentle restraint            -> actor.conflict += 1
    compromise accepted         -> actor.wisdom += 1 ; actor.joy += 1 ; actor.conflict -> 0
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
MESS_KINDS = {"wet", "greedy", "bare"}
REGIONS = {"feet", "legs", "hands", "heart"}

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
        female = {"girl", "grandmother", "mom", "woman"}
        male = {"boy", "grandfather", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the shore"
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

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["greedy"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.type != "pool" and item.type != "thicket":
                continue
            sig = ("soak", item.id, "greedy")
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["bare"] += 1
            out.append(f"The {item.label} looked a little barer.")
    return out

def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["bare"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["sadness"] += 1
        out.append(f"That would make {carer.label} sad.")
    return out

def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["restrained"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
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

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    pool_health = sum(e.meters["bare"] for e in sim.entities.values() if e.type == "pool")
    return {
        "soiled": pool_health >= THRESHOLD,
        "workload": sim.get("Grandparent").memes["sadness"] if "Grandparent" in sim.entities else 0,
    }

def activity_delight(activity: Activity) -> str:
    return {
        "collect": "each shell felt like a tiny secret from the sea",
        "dig": "the wet sand squished between tiny toes",
        "splash": "the water sparkled like diamonds in the sun",
        "explore": "every rock hid a curious crab or a shiny pebble",
    }.get(activity.id, "it made the day feel full of wonder")

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the tide table waited."
    return f"The {setting.place.removeprefix('the ')} glistened under the warm sun."

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
    world.say(f"{hero.id} was a {desc} who loved the shore more than anything.")

def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    place = world.setting.place
    world.say(f"{hero.pronoun().capitalize()} loved going to {place} and {activity.gerund}; {activity_delight(activity)}.")

def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Every morning, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} {prize.phrase}.")

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} everywhere.")

def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One tide season, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))

def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label_word} held up a gentle hand.")

def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = "bare and sad"
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"The thicket has given you enough shells, my star"
    if pred["workload"] >= THRESHOLD:
        clause += f", and I'll feel heavy if the pool grows bare"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let us think first."')
    return True

def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to {activity.verb} was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")

def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["restrained"] += 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label_word} took {hero.pronoun('possessive')} hand and said, \"You can want to {activity.verb}, and we can still choose the kind way.\"")

def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. "But I always {activity.verb}!" {hero.pronoun()} said.')

def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. "How about we {gear_def.prep} and {activity.verb} together?"')
    return gear_def

def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["wisdom"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}. \"Yes, let's be guardians of the pool!\" {hero.pronoun()} said.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund} gently, {parent.label_word} beside {hero.pronoun('object')}, and the thicket grew green again.")

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Elara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "grandmother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["kind", "stubborn"]),
    ))
    parent = world.add(Entity(id="Grandparent", kind="character", type=parent_type, label="the grandparent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    pool = world.add(Entity(id="Pool", type="pool", label="tidal pool", caretaker=parent.id))
    thicket = world.add(Entity(id="Thicket", type="thicket", label="rocky thicket", caretaker=parent.id))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["restrained"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world

SETTINGS = {
    "shore": Setting(place="the shore", indoor=False, affords={"collect", "explore"}),
    "cove": Setting(place="the cove", indoor=False, affords={"collect", "splash"}),
    "tidal_pool": Setting(place="the tidal pool", indoor=False, affords={"collect", "dig", "explore"}),
    "beach": Setting(place="the beach", indoor=False, affords={"dig", "splash"}),
}

ACTIVITIES = {
    "collect": Activity(
        id="collect",
        verb="collect shells",
        gerund="collecting shells",
        rush="reach into the water",
        mess="greedy",
        soil="bare and empty",
        zone={"hands", "heart"},
        weather="sunny",
        keyword="shell",
        tags={"shell", "sea"},
    ),
    "explore": Activity(
        id="explore",
        verb="explore the pool",
        gerund="exploring the pool",
        rush="dart toward the thicket",
        mess="greedy",
        soil="disturbed and bare",
        zone={"feet", "hands"},
        weather="sunny",
        keyword="thicket",
        tags={"thicket", "pool"},
    ),
    "dig": Activity(
        id="dig",
        verb="dig in the sand",
        gerund="digging in the sand",
        rush="kneel down and scoop",
        mess="greedy",
        soil="dug up and messy",
        zone={"hands"},
        weather="sunny",
        keyword="dig",
        tags={"sand", "wet"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the waves",
        gerund="splashing in the waves",
        rush="run into the water",
        mess="wet",
        soil="soaking",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="wave",
        tags={"wave", "wet"},
    ),
}

GEAR = [
    Gear(
        id="stories",
        label="stories instead",
        covers={"hands", "heart"},
        guards={"greedy", "bare"},
        prep="take only the stories back today",
        tail="sat together by the thicket, watching the tide rise",
        plural=True,
    ),
    Gear(
        id="basket",
        label="special basket for memories",
        covers={"heart"},
        guards={"greedy"},
        prep="put only memories in our basket",
        tail="filled the basket with quiet moments",
    ),
    Gear(
        id="net",
        label="gentle net for watching",
        covers={"feet", "hands"},
        guards={"wet", "greedy"},
        prep="use the gentle net just to watch, not take",
        tail="dipped the net gently, then let everything go",
    ),
]

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a special woven basket",
        type="basket",
        region="heart",
        plural=False,
        genders={"girl", "boy"},
    ),
    "net": Prize(
        label="net",
        phrase="a little net with a wooden handle",
        type="net",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
    "hat": Prize(
        label="hat",
        phrase="a wide sun hat",
        type="hat",
        region="heart",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Elara", "Maya", "Luna", "Stella", "Iris", "Cora", "Ivy", "Rose", "Nova", "Faye"]
BOY_NAMES = ["Finn", "Kai", "Leo", "Owen", "Theo", "Eli", "Jude", "Rory", "Cole", "Wren"]
TRAITS = ["kind", "curious", "stubborn", "brave", "gentle", "spirited"]

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos

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

KNOWLEDGE = {
    "shell": [("What is a seashell?",
               "A seashell is the hard, empty home of a sea creature like a snail or clam, found on the shore.")],
    "sea": [("Why is the sea salty?",
             "The sea is salty because rivers carry tiny bits of salt from rocks into the ocean, and the sun dries some water, leaving the salt behind.")],
    "thicket": [("What is a thicket?",
                 "A thicket is a dense group of bushes or small trees, often near water, where creatures hide.")],
    "pool": [("What is a tidal pool?",
              "A tidal pool is a small pool of seawater left among rocks when the tide goes out, full of tiny sea life.")],
    "wet": [("Why do wet feet feel cold?",
             "Wet feet feel cold because water takes away warmth from your skin as it dries, making you feel chilly.")],
    "tide": [("What is the tide?",
              "The tide is the regular rise and fall of the ocean, caused by the pull of the moon. It brings water in and takes it out.")],
    "basket": [("What is a basket for on the shore?",
                "A basket is a woven container you can carry to hold shells, stones, or other treasures you find.")],
    "guardian": [("What does it mean to be a guardian of the pool?",
                  "A guardian of the pool is someone who watches over the tide pool and its creatures, taking only memories, not treasures.")],
}
KNOWLEDGE_ORDER = ["shell", "sea", "thicket", "pool", "wet", "tide", "basket", "guardian"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child learns to leave some beauty behind" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to {act.verb} again but {hero.pronoun('possessive')} {parent.label_word} teaches {hero.pronoun('object')} about caring for the tide pool.",
        f'Write a simple story that uses the noun "{kw}" and ends with a child and grandparent finding a compromise by the sea.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {place} to {act.verb}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. They go to {place} on a sunny tide season day.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} love to do at {place} before {pw} taught {hero.pronoun('object')} about sharing?",
            answer=f"{trait.capitalize()} {hero.id} loved {act.gerund} at {place}. That habit became tricky because the tide pool needed its treasures too.",
        ),
        QAItem(
            question=f"What treasure did {hero.id}'s {pw} give {hero.pronoun('object')} to carry finds at {place}?",
            answer=f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. {hero.id} loved {prize.it()} and took {prize.it()} everywhere.",
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "bare")
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} worry about {pos} collecting at {place}?",
            answer=f"{pos.capitalize()} {pw} was worried because if {hero.id} kept collecting, the thicket and pool would grow {soil}. When {hero.id} tried to {act.rush}, {pos} {pw} took {pos} hand gently.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=f"How did taking {gear_plan} help {trait} {hero.id} and {pos} {pw} at {place}?",
            answer=f"They agreed to {gear.prep}, so {hero.id} could {act.verb} without harming the pool. The plan let {hero.pronoun('object')} play while keeping the tide pool happy.",
        ))
        qa.append(QAItem(
            question=f"How did {trait} {hero.id} feel after {pw} offered the plan for {act.keyword or act.mess} at {place}?",
            answer=f"{hero.id} felt happy and hugged {pos} {pw} once they agreed on the plan. At the end, {sub} was {act.gerund} gently with {pw} laughing nearby.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
    StoryParams(place="tidal_pool", activity="collect", prize="basket", name="Elara", gender="girl", parent="grandmother", trait="kind"),
    StoryParams(place="shore", activity="explore", prize="net", name="Kai", gender="boy", parent="grandfather", trait="curious"),
    StoryParams(place="cove", activity="splash", prize="hat", name="Maya", gender="girl", parent="grandmother", trait="brave"),
    StoryParams(place="beach", activity="dig", prize="basket", name="Finn", gender="boy", parent="grandfather", trait="gentle"),
    StoryParams(place="tidal_pool", activity="explore", prize="hat", name="Luna", gender="girl", parent="grandmother", trait="stubborn"),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- the thicket and pool aren't connected. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")

def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")

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

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, the tide pool, and learning to share. Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
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
    parent = args.parent or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
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

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
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
