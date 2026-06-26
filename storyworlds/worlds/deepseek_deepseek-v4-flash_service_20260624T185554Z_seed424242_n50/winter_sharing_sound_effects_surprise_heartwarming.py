#!/usr/bin/env python3
"""
storyworlds/worlds/winter_sharing_sound_effects_surprise_heartwarming.py
========================================================================

A standalone storyworld sketch for a winter sharing story with sound effects,
surprise, and a heartwarming turn.

Initial story (used to build the world model):
---
Once upon a time, there was a little girl named Lily. She loved to play in the
snow. One day, Lily's mother knitted her a warm red scarf. Lily wore it
everywhere. One snowy afternoon, Lily and her mother went to the park. Lily
wanted to build a snowman, but her mother worried that Lily's scarf would get
wet and she would be cold. Lily tried to run to the snow pile, but her mother
gently held her hand. "Let's think of a way to keep warm," she said. Then Lily
remembered her extra mittens. She put them on and shared her scarf with her
mother. They built a snowman together, and the sound of crunching snow made
Lily giggle. The surprise was a little bell they found in the snow – they added
it to the snowman's hat. Lily was warm and happy.
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

# Physical meter keys
COLD_KINDS = {"wet", "cold", "chilly"}
WARM_KINDS = {"dry", "warm"}

REGIONS = {"neck", "hands", "head", "feet"}

# ---------------------------------------------------------------------------
# Entity
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
# Domain dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the park"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str  # e.g. "wet", "cold"
    soil: str  # e.g. "wet and cold"
    zone: set[str]
    weather: str = "snowy"
    keyword: str = ""
    sound: str = ""
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
        self.surprise_sound: str = ""

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

def _r_soak_cold(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for m in {"wet", "cold"}:
            if actor.meters[m] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("chill", item.id, m)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[m] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} got {m}."
                )
    return out

def _r_workload_warm(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["warm"] >= THRESHOLD and item.caretaker:
            sig = ("care", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            carer = world.get(item.caretaker)
            carer.meters["warm_work"] += 1
            out.append(f"That meant {carer.label} had to help dry it.")
    return out

def _r_share_surprise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["shared"] >= THRESHOLD and actor.memes["surprise"] < THRESHOLD:
            sig = ("surprise", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["surprise"] += 1
            world.surprise_sound = "a faint jingle – there was a tiny bell hidden in the snow"
            out.append(world.surprise_sound)
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="soak_cold", tag="physical", apply=_r_soak_cold),
    Rule(name="workload_warm", tag="physical", apply=_r_workload_warm),
    Rule(name="share_surprise", tag="social", apply=_r_share_surprise),
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
def predict_cold(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and (prize.meters["cold"] >= THRESHOLD or prize.meters["wet"] >= THRESHOLD)),
        "workload": sum(e.meters["warm_work"] for e in sim.characters()),
    }

# ---------------------------------------------------------------------------
# Scene verbs
# ---------------------------------------------------------------------------
def action_sound(activity: Activity) -> str:
    return activity.sound or "the crunch of snow"

def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return "The room was warm and the windows were frosted."
    return "The snow sparkled under the pale winter sun."

def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed dry and warm"

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
    world.say(f"{hero.id} was a {desc} who loved winter mornings.")

def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{action_sound(activity)} made every step feel magical."
    )

def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} made {hero.pronoun('object')} {prize.phrase}."
    )

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} every time {hero.pronoun()} went out."
    )

def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One snowy day, "
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting))

def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )

def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_cold(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and I'll have to dry it"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s find a warm plan."')
    return True

def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the snowy fun was too inviting.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")

def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} gently caught "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"It\'s okay to want to {activity.verb}. We’ll find a way to stay warm."'
    )

def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes.get("conflict", 0) >= THRESHOLD:
        world.say(
            f'{hero.id} pouted. "But I really want to {activity.verb}!"'
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
    if predict_cold(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. '
        f'"How about we {gear_def.prep} and then {activity.verb} together?"'
    )
    return gear_def

def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["shared"] += 1
    world.say(
        f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word} and said, "
        f'"Yes, let\'s share!" They {gear_def.tail}.'
    )
    # Surprise sound effect
    propagate(world, narrate=True)  # may fire share_surprise rule
    sound = world.surprise_sound if world.surprise_sound else "the sound of crunching snow"
    world.say(
        f"Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_safe(hero, prize)}, and {parent.label_word} was laughing nearby. "
        f"And then {sound} – a tiny treasure!"
    )
    # Heartwarming ending
    hero.memes["surprise"] += 1
    world.say(
        f"They added the bell to the snowman's hat. {hero.id} felt warm inside. "
        f"Sharing made the day perfect."
    )

# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "snowy" if not setting.indoor else ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

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
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None,
                       shared=hero.memes["shared"] >= THRESHOLD,
                       surprise=hero.memes["surprise"] >= THRESHOLD)
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(place="the park", indoor=False, affords={"snowman", "sled", "snowball"}),
    "garden": Setting(place="the garden", indoor=False, affords={"snowman", "snowball"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"snowman", "sled"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"snowman"}),
}

ACTIVITIES = {
    "snowman": Activity(
        id="snowman",
        verb="build a snowman",
        gerund="building a snowman",
        rush="run to the snow pile",
        mess="cold",
        soil="cold and wet",
        zone={"hands", "neck"},
        weather="snowy",
        keyword="snowman",
        sound="the crunch of snow under their boots",
        tags={"snow", "cold", "sharing"},
    ),
    "sled": Activity(
        id="sled",
        verb="go sledding",
        gerund="sledding",
        rush="climb onto the sled",
        mess="cold",
        soil="chilly and wet",
        zone={"feet", "legs"},
        weather="snowy",
        keyword="sled",
        sound="the swoosh of the sled",
        tags={"sled", "speed", "cold"},
    ),
    "snowball": Activity(
        id="snowball",
        verb="throw snowballs",
        gerund="throwing snowballs",
        rush="grab a handful of snow",
        mess="cold",
        soil="cold and wet",
        zone={"hands", "arms"},
        weather="snowy",
        keyword="snowball",
        sound="the soft thud of snow",
        tags={"snow", "fun", "sharing"},
    ),
}

GEAR = [
    Gear(
        id="mittens",
        label="extra mittens",
        covers={"hands"},
        guards={"cold"},
        prep="put on your extra mittens",
        tail="put on the extra mittens",
        plural=True,
    ),
    Gear(
        id="scarf",
        label="a warm scarf",
        covers={"neck"},
        guards={"cold"},
        prep="wrap your scarf tight",
        tail="wrapped the scarf tight",
    ),
    Gear(
        id="boots",
        label="waterproof boots",
        covers={"feet"},
        guards={"cold", "wet"},
        prep="switch to your waterproof boots",
        tail="switched to waterproof boots",
        plural=True,
    ),
    Gear(
        id="hat",
        label="a wool hat",
        covers={"head"},
        guards={"cold"},
        prep="pull on your wool hat",
        tail="pulled on the wool hat",
    ),
]

PRIZES = {
    "scarf": Prize(
        label="scarf",
        phrase="a warm red scarf",
        type="scarf",
        region="neck",
    ),
    "mittens": Prize(
        label="mittens",
        phrase="soft wool mittens",
        type="mittens",
        region="hands",
        plural=True,
    ),
    "hat": Prize(
        label="hat",
        phrase="a cozy hat with a pom-pom",
        type="hat",
        region="head",
    ),
    "boots": Prize(
        label="boots",
        phrase="sturdy winter boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]

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
# Q&A generators
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "snow": [("What is snow?", "Snow is frozen water that falls from the sky as soft white flakes.")],
    "cold": [("Why do we wear warm clothes in winter?",
              "Warm clothes trap your body heat and keep the cold air away, so you stay toasty.")],
    "sharing": [("Why is sharing nice?",
                 "Sharing makes both people happy. It shows you care about each other.")],
    "mittens": [("What are mittens?",
                 "Mittens are soft covers for your hands that keep them warm in the cold.")],
    "scarf": [("What is a scarf for?",
               "A scarf is a long cloth you wrap around your neck to keep the wind out.")],
}
KNOWLEDGE_ORDER = ["snow", "cold", "sharing", "mittens", "scarf"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short story for a young child about winter, sharing, and a surprise sound.',
        f'Tell a gentle story where a {hero.type} named {hero.id} wants to '
        f'{act.verb} but {hero.pronoun("possessive")} {parent.label_word} worries '
        f'about {prize.phrase}, and they find a heartwarming compromise with a surprise sound.',
        f'Write a simple story that includes the words "{act.keyword}" and "share", and ends with a happy surprise.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} plays in the snow?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} love to do in the snow?",
            answer=f"{trait.capitalize()} {hero.id} loved {act.gerund} and hearing the {act.sound}.",
        ),
        QAItem(
            question=f"What warm thing did {hero.id}'s {pw} give {obj}?",
            answer=f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. {hero.id} wore {prize.it()} proudly.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} worry about {pos} {prize.label}?",
            answer=f"{pos.capitalize()} {pw} worried that if {hero.id} {act.gerund}, {pos} {prize.label} would get {act.soil} and {hero.pronoun()} would be cold.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did sharing help {hero.id}?",
            answer=f"They used {gear.label} and shared the fun. {hero.id} stayed warm and happy.",
        ))
    if f.get("surprise"):
        qa.append(QAItem(
            question=f"What surprise sound did they hear in the story?",
            answer=f"They heard {world.surprise_sound}. It was a tiny bell hidden in the snow!",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
    StoryParams(place="park", activity="snowman", prize="scarf", name="Lily", gender="girl", parent="mother", trait="playful"),
    StoryParams(place="backyard", activity="sled", prize="boots", name="Max", gender="boy", parent="father", trait="curious"),
    StoryParams(place="garden", activity="snowball", prize="mittens", name="Zoe", gender="girl", parent="mother", trait="spirited"),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} touches {sorted(activity.zone)}, "
                f"but {noun} is worn on {prize.region} – it wouldn't get cold. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: no gear in the catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}.)")

def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {prize_id} isn't typical for a {gender}; try {ok}.)"

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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
        description="Winter Sharing Sound Effects Surprise Heartwarming storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
