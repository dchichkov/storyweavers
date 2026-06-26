#!/usr/bin/env python3
"""
storyworlds/worlds/wax_scalp_smash_kindness_adventure.py
========================================================

A standalone *story world* sketch for a candle-making adventure featuring wax,
scalp accidents, smashing fragile objects, and resolving conflicts through
demonstrations of kindness.

Initial story seed:
---
Once upon a time in the cozy candle workshop of Grandma Mara, lived a daring
and cheerful child named Eli. Eli loved adventures that involved both fire and
sticky things, so crafting candles was always full of possibility. One afternoon,
Eli made big plans to create a batch of cinnamon-dotted birthday candles with
fresh pine scent.

While melting yellow wax in the iron pot, Eli reached too far and the hot wax
dripped onto Eli's forehead just above the hairline. "Ouch!" Eli howled as the
wax clung to skin and hair. Before Eli could even grab a towel, their excited
elbow knocked against the shelf where Grandma Mara's precious glass jars of
scented wick oils stood. Three jars cascaded to the floor, shattering into
hundreds of sharp pieces that scattered everywhere.

Looking back at what they had done, Eli hesitated—then remembered Grandma
Mara's words: "Kindness matters more than perfection." Eli took a deep breath,
found the broom, carefully cleaned every piece, and gently asked, "Grandma, may I
help you before we make new candles tomorrow?"

Grandma's warm eyes softened. "When you act with kindness, everything
works better," she said, handing Eli the first wick. Together they finished the
birthday candles, and the next morning, Eli gave them as gifts to friends—exactly
on time and three times as bright.
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

# Worker-thread magnitude at which an effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys
MESS_KINDS = {"wax_smeared", "scraped", "cut", "damaged"}
REGIONS = {"head", "hands", "feet"}

# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
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
        female = {"girl", "mother", "woman", "grandma"}
        male = {"boy", "father", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandma": "Grandma", "grandpa": "Grandpa"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parametrization knobs – the swappable vocabulary of this domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the candle workshop"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = ""
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
# World: entity store + narration history.
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
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_wax(world: World) -> list[str]:
    """actor messy on head region -> wax spreads."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wax_temp"] < THRESHOLD:
            continue
        sig = ("wax_spread", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["wax_smeared"] += 2
        out.append(f"The hot wax clung fast to {actor.pronoun('possessive')} forehead and hairline.")
    return out

def _r_pain(world: World) -> list[str]:
    """wax on skin -> actor pain."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wax_smeared"] >= THRESHOLD and actor.meters["pain"] < THRESHOLD:
            actor.meters["pain"] += 2
            out.append(f"Ouch! The wax burned {actor.id}'s skin where it touched.")
    return out

def _r_cleanup_pain(world: World) -> list[str]:
    """soothing care reduces pain."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["pain"] >= THRESHOLD and actor.meters["kindness_care"] >= 1.5:
            reduction = min(actor.meters["pain"], 2.0)
            actor.meters["pain"] -= reduction
            out.append(f"{actor.pronoun().capitalize()} felt much better once {actor.id}'s forehead was gently cared for.")
    return out

def _r_dawn_damage(world: World, threshold: float) -> list[str]:
    """fragile things need repair."""
    out: list[str] = []
    damaged = []
    for e in world.entities.values():
        if e.type == "broken_jar" and e.meters.get("shards") >= threshold and e.meters.get("repaired") < THRESHOLD:
            damaged.append(e.label)
    if damaged and "broken_jar" not in [n for n, *_ in world.fired]:
        world.fired.add(("dawn_damage",))
        work = len(damaged)
        for c in world.characters():
            c.meters["morning_work"] += work
        out.append(f"Three shiny glass jars had scattered everywhere last night and {world.entities['grandma'].pronoun('subject')} knew morning would mean careful cleanup.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="wax_spread", tag="physical", apply=_r_wax),
    Rule(name="pain_notice", tag="physical", apply=_r_pain),
    Rule(name="clean_care", tag="kindness", apply=_r_cleanup_pain),
    Rule(name="dawn_damage", tag="physical", apply=lambda w: _r_dawn_damage(w, 3.0)),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers – what is a *reasonable* concern and a *reasonable* fix.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.type in {"hair", "forehead"} and "wax" in activity.id

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if any(m in gear.guards for m in activity.tags) and prize.region in gear.covers:
            return gear
    return None

# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_joy(activity: Activity) -> str:
    return {
        "wax_melting": "the warm cinnamon dots smelled like fresh pine woods",
        "jar_cleanup": "the light through the window sparkled off every tiny piece",
        "gift_wrapping": "the ribbons made the spring sky feel even happier",
    }.get(activity.id, "it filled the air with adventure")

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the candle workshop":
        return "Sunlight streamed through the attic windows, painting warm squares on the workbench full of tools and glass bottles."
    if setting.place == "the repair table":
        return "The round table by the porch had just enough room for one determined helper and three stubborn open jars."
    return f"{setting.place.capitalize()} smelled of warm wax and adventure."

def prize_description(hero: Entity, prize: Prize) -> str:
    return {
        "hair": f"a small spot of hardened wax on {hero.pronoun('possessive')} forehead",
        "forehead": f"hot wax sticking to {hero.pronoun('possessive')} forehead",
        "workshirt": f"{hero.pronoun('possessive')} favorite apron with cinnamon dots",
    }.get(prize.type, prize.phrase)

def describe_wax_condition(wax_amt: float) -> str:
    if wax_amt < 0.5: return "a faint smear"
    if wax_amt < 2.0: return "a sticky blotch"
    return "a stubborn dark stain"

# Moonlit verbs
def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hour = "late evening"
    go = "were gathered in"
    world.say(f"On a {hour}, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))

def admire_candles(world: World, parent: Entity, hero: Entity) -> None:
    parent_has = "a few special goose-feather brushes" if random.random() < 0.4 else "a wooden stirring spoon"
    world.say(f"{hero.pronoun().capitalize()} {hero.id} smiled at {parent.pronoun('possessive')} {parent_has} laid out on the workbench.")

def wants_adventure(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, "
        f"but {hero.pronoun('possessive')} {parent.label_word} held up gentle hands."
    )

def warns_cleanup(world: World, parent: Entity, hero: Entity, prize: Prize) -> None:
    world.say(f'"Hold still," {hero.pronoun('possessive')} {parent.label_word} murmured. "Hot wax hurts, and sticky hands make items fall."')
    hero.meters["warning"] += 2

def melts_wax(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["wax_temp"] += 3
    hero.memes["danger_play"] += 1
    world.say(f"{hero.id} tipped the iron pot, letting golden liquid pool into molds dotted with cinnamon.")
    propagate(world)

def reshelve_jars(world: World, hero: Entity) -> None:
    shelves = ["high up on the third shelf", "beside the spice rack", "just above the broom"]
    world.say(f"{hero.id} carefully reached for one small glass jar of red wick oil from {random.choice(shelves)}.")

def smash_incident(world: World, hero: Entity, prize: Optional[Prize] = None) -> None:
    jars = ["glittering red", "clear lavender", "blank white"]
    world.say(
        f"As {hero.id} stretched up, excited elbows knocked against "
        f"three {random.choice(jars)} glass jars. In one fast motion, "
        f"everything fell, shattering into hundreds of sharp {prize.label if prize else 'pieces'} everywhere."
    )
    for e in world.entities.values():
        if e.type == "broken_jar":
            e.meters["shards"] += 10
    hero.memes["fear"] += 3
    hero.memes["guilt"] += 2
    world.facts["shards_total"] = sum(e.meters.get("shards", 0) for e in world.entities.values() if e.type == "broken_jar")
    world.facts["guilt_level"] = hero.memes["guilt"]

def poke_shards(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} stared at the {world.facts.get('shards_total', 0)} sharp pieces scattered across the floor boards.")

def admit_fault(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["guilt"] -= 1
    world.say(
        f'With a shaky voice, {hero.id} whispered, "Grandma, I did not mean to..." '
        f"{hero.pronoun('object')} eyes welled up as {parent.pronoun('possessive')} warm hands took "
        f"{hero.pronoun('possessive')} shoulders."
    )

def show_kindness(world: World, parent: Entity, hero: Entity, plan: str) -> bool:
    parent.memes["pride_kindness"] += 1
    world.say(
        f'"Maybe," {parent.pronoun('possessive')} {parent.label_word} said with a soft smile, '
        f'"we can turn this evening into tomorrow\'s gift." {hero.pronoun().capitalize()} '
        f"{plan} together."
    )
    return True

def broom_cleanup(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["kindness"] += 2
    hero.memes["fear"] -= 1
    broom_label = "worn straw broom" if random.random() < 0.6 else "Grandma's favorite cedar-handled brush"
    world.say(
        f"{hero.id} fetched the {broom_label} and very carefully swept every {world.facts.get('shards_total', 'piece')} "
        f"into a folded paper cone, then wrapped it in yesterday's newspaper before tossing it into {world.setting.place}’s scrap basket."
    )
    for e in world.entities.values():
        if e.type == "broken_jar":
            e.meters["repaired"] = 1
            e.meters["shards"] = 0

def craft_new_candles(world: World, parent: Entity, hero: Entity) -> None:
    colors = ["golden", "silver-flecked", "pearly"]
    scents = ["pine", "cinnamon", "spring-rain"]
    friend = random.choice(["Mara", "Leo", "Zia", "Noa"])
    hero.memes["joy"] += 3
    hero.memes["pride_work"] += 1
    world.say(
        f"Together, they pulled out fresh wicks and "
        f"{random.choice(colors)} wax, rolling in spices that smelled of "
        f"{random.choice(scents)}. By morning, ten birthday candles stood ready to light up "
        f"a friend’s special day."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {hero.id} placed them in a little box lined with tissue paper, "
        f"and tied a bright ribbon around it with the words: “Made with love and kindness.”"
    )
    world.facts["gave_as_gift"] = True

# ---------------------------------------------------------------------------
# The screenplay: three acts driven by verb functions.
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Eli",
    hero_type: str = "boy",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "grandma",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["daring", "cheerful"] + (hero_traits or ["adventurous", "helpful"]),
    ))
    parent = world.add(Entity(
        id="Grandma",
        kind="character",
        type=parent_type,
        label="Grandma Mara",
        phrase="Grandma Mara's careful hands",
        traits=["patient", "warm"],
    ))
    wax_spot = world.add(Entity(
        id="wax_spot",
        type="mess",
        phrase="a glob of hot, yellow wax",
    ))
    broken_jar1 = world.add(Entity(
        id="jar1", type="broken_jar", phrase="first glass jar", label="jar",
        region="shelf", plural=False, worn_by=None,
    ))
    broken_jar2 = world.add(Entity(
        id="jar2", type="broken_jar", phrase="second glass jar", label="jar",
        region="shelf", plural=False, worn_by=None,
    ))
    broken_jar3 = world.add(Entity(
        id="jar3", type="broken_jar", phrase="third glass jar", label="jar",
        region="shelf", plural=False, worn_by=None,
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    # Act 1 – Setup: daring child, loving grandparent, crafting plans.
    world.para()
    arrive(world, hero, parent, activity)
    admire_candles(world, parent, hero)
    wants_adventure(world, hero, parent, activity)
    warn_cleanup(world, parent, hero, prize)
    melts_wax(world, hero, activity)

    # Act 2 – Conflict: hot wax drops, painful scare, falling disaster.
    world.para()
    world.say(f"But {hero.id} reached too far...")
    poke_shards_before = sum(e.meters.get("shards", 0) for e in world.entities.values() if e.type == "broken_jar")
    smash_incident(world, hero, prize)
    poke_shards(world, hero)
    admit_fault(world, hero, parent)

    # Act 3 – Resolution: kindness cleanup, repaired world, shared joy.
    world.para()
    show_kindness(world, parent, hero, "we’ll clean every dangerous piece")
    broom_cleanup(world, hero, parent)
    craft_new_candles(world, parent, hero)

    # Record facts the Q&A generators can lean on.
    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        conflict_guilt=hero.memes["guilt"] >= THRESHOLD,
        resolved_kindness=hero.memes["kindness"] >= THRESHOLD,
        gave_as_gift=world.facts.get("gave_as_gift", False),
        shards_cleaned=poke_shards_before > 0,
    )
    return world

# ---------------------------------------------------------------------------
# Registries – the building blocks our screenplay picks from.
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(
        place="the candle workshop",
        indoor=True,
        affords={"wax_melting", "jar_cleanup", "gift_wrapping"},
    ),
    "porch": Setting(
        place="the back porch",
        indoor=False,
        affords={"jar_arranging", "candle_shaping"},
    ),
}

ACTIVITIES = {
    "wax_melting": Activity(
        id="wax_melting",
        verb="make cinnamon-dotted birthday candles",
        gerund="making candles with cinnamon dots",
        rush="tip the pot of melted wax",
        mess="wax_temp",
        zone={"hands", "head"},
        weather="",
        keyword="candle",
        tags={"wax", "creative", "messy"},
    ),
    "jar_cleanup": Activity(
        id="jar_cleanup",
        verb="tidy scattered glass",
        gerund="tidying glass shards",
        rush="grab the broom",
        mess="shards",
        zone={"feet"},
        weather="",
        keyword="cleanup",
        tags={"messy", "risky"},
    ),
    "gift_wrapping": Activity(
        id="gift_wrapping",
        verb="wrap the birthday candles",
        gerund="wrapping birthday candles",
        rush="tie the ribbon tight",
        mess="ribbon",
        zone={"hands"},
        weather="",
        keyword="ribbon",
        tags={"crafty", "pretty"},
    ),
}

PRIZES = {
    "hair": Prize(
        label="hair",
        phrase="the way hair felt",
        type="hair",
        region="head",
        plural=False,
    ),
    "workshirt": Prize(
        label="workshirt",
        phrase="favorite apron with cinnamon dots",
        type="apron",
        region="torso",
        plural=False,
    ),
    "gift": Prize(
        label="gift",
        phrase="special birthday candles",
        type="candles",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="old play apron",
        covers={"torso", "head"},
        guards={"wax_temp"},
        prep="wrap on an old play apron",
        tail="took out the worn apron to protect the outfit",
    ),
    Gear(
        id="cloth",
        label="soft cloth",
        covers={"head", "hands"},
        guards={"wax_temp"},
        prep="fetch a soft cloth",
        tail="gently wiped the warm wax away",
    ),
    Gear(
        id="broom",
        label="straw broom",
        covers=set(),
        guards=set(),
        prep="grab a broom",
        tail="swept every piece of glass",
        plural=True,
    ),
]

GIRL_NAMES = ["Luna", "Mara", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Eli", "Tim", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["daring", "cheerful", "adventurous", "helpful", "fearless", "patient"]

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
# Parameters for the per-world configurable knobs.
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
# Q&A — three separate, world-aware sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wax": [
        ("What is candle wax made from?",
         "Candle wax comes from melted fat or oil that turns solid when it cools. Beeswax and paraffin are common kinds."),
        ("Why does hot wax burn skin?",
         "Hot wax is warm enough to melt skin fats and may leave a red mark. It hurts because the skin is sensitive to heat."),
    ],
    "cinnamon": [
        ("Why does cinnamon smell nice?",
         "Cinnamon is the dried bark of a tropical tree. Its warm, sweet smell comes from oils inside the bark."),
        ("How do you use cinnamon in candles?",
         "Ground cinnamon is mixed into melted wax before pouring. When the candle burns, the spice smell fills the room."),
    ],
    "kindness": [
        ("What is kindness?",
         "Kindness means thinking about how your actions affect others, and then choosing words or actions that help and comfort."),
        ("What is one way to show kindness after an accident?",
         "Instead of blaming yourself or others, take a breath and say, 'Let’s clean up together.'"),
    ],
    "cleanup": [
        ("Why do glass shards need careful cleanup?",
         "Shards can injure feet or hands. Wrapping them in paper prevents cuts and keeps the floor safe for play."),
    ],
}
KNOWLEDGE_ORDER = ["wax", "cinnamon", "kindness", "cleanup"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity = f["hero"], f["activity"]
    return [
        f"Write an adventure story for ages 4–7 where a {hero.type} named {hero.id} "
        f"makes birthday candles but has an accident with hot wax; include the word 'cinnamon'.",
        f"Tell a gentle crafting adventure where {hero.id} handles a smash incident with kindness "
        f"and makes amends, using the phrase 'made with love and kindness'.",
        f'Create a short story for preschoolers about "{hero.id}’s candle workshop accident" '
        f'that includes the noun "glass jar".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    sub, obj = hero.pronoun("subject"), hero.pronoun("object")
    day = {"rainy": "rainy afternoon", "sunny": "sunny morning"}.get(world.weather, "playtime")

    qa: list[QAItem] = [
        QAItem(
            question=f"Who was the main character when {hero.id} visited {world.setting.place}?",
            answer=f"The story is about a {hero.type} named {hero.id}, wearing a favorite apron with cinnamon dots.",
        ),
        QAItem(
            question=f"What hobby did {hero.id} love that involved fire and sticky items?",
            answer=f"{hero.id} loved making birthday candles filled with cinnamon dots using melted wax.",
        ),
        QAItem(
            question=f"What caused the accident with hot wax and glass jars?",
            answer=f"While reaching for wax molds, excited elbows knocked over three glass jars held on the shelf.",
        ),
    ]

    if f.get("shards_cleaned"):
        qa.append(QAItem(
            question=f"How did {hero.id} fix the glass shards mess?",
            answer=f"{hero.id} swept every sharp piece carefully into paper and wrapped it for disposal.",
        ))

    if f.get("gave_as_gift"):
        qa.append(QAItem(
            question=f"What gift did {hero.id} prepare after cleaning up?",
            answer=f"{hero.id} wrapped ten birthday candles in ribbon with the words 'Made with love and kindness.'",
        ))

    if hero.memes.get("guilt", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did Grandma Mara comfort {hero.id} after the accident?",
            answer=(
                f"Grandma hugged {obj} and said, \"Turn this evening into tomorrow's gift.\" "
                f"Then they cleaned every piece together."
            ),
        ))

    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts.get("activity", Activity("","","","",set(),"")).tags
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags or tag in {act.id for act in ACTIVITIES.values()}:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out

# ---------------------------------------------------------------------------
# CLI parsing, resolution, generation, and emission
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Candle workshop adventure: wax, scalp, smash, and kindness.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandma", "grandpa"])
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
            raise StoryError(
                f"Hot wax would burn the {pr.label}, and no offered gear covers both "
                f"the {act.keyword or 'activity'} area and the head region."
            )
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        ok = " / ".join(sorted(PRIZES[args.prize].genders))
        raise StoryError(f"Prize {args.prize} isn’t typical for a {args.gender}; try --gender {ok}.")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["grandma", "grandpa"])
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
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "helpful"],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

# ---------------------------------------------------------------------------
# ASP reasoner twin – a tiny clingo rule set that mirrors the Python checks.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Hot wax dripping onto the head region is dangerous (warrants cleanup).
at_risk(A,P,R) :- activity_washes(A,R), worn_region(P,R), occupation(A, candlemaking).
at_risk(A,P,R) :- location_has_ladder(A, L), high_shelf(L), activity_help(A,"reach high"), worn_region(P,"head").

% Gear that guards against wax and covers the head is compatible.
compatible_gear(G,A,P) :- gear_guards(G,"wax"), covers(G,"head"), at_risk(A,P,"head").

valid_story(Place,Act,Prize) :- affords(Place,Act), at_risk(Act,Prize,"head"), compatible_gear(_,Act,Prize), wears(Prize,Gender).
"""

try:
    import asp
except ImportError:
    asp = None

def asp_facts() -> str:
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
            lines.append(asp.fact("activity_washes", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("occupation", aid, "candlemaking"))
        for z in sorted(a.zone):
            lines.append(asp.fact("activity_help", aid, "reach high"))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_region", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", pid, g))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        if "head" in g.covers:
            pass
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    if asp is None:
        return []
    try:
        model = asp.one_model(asp_program("#show valid_story/3."))
        return sorted(set(asp.atoms(model, "valid_story")))
    except Exception:
        return []

def asp_verify() -> int:
    if asp is None:
        print("CLINGO NOT AVAILABLE – skipping ASP gate verification.")
        return 0
    import asp as asp_lib
    clingo_set = sorted(set(asp_valid_stories()))
    python_set = sorted(set(valid_combos()))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo gate and valid_combos():")
    if clingo_set and not python_set:
        print("  only in clingo:\n   ", "\n    ".join(map(str, clingo_set[:5])))
    elif python_set and not clingo_set:
        print("  only in python:\n   ", "\n    ".join(map(str, python_set[:5])))
    else:
        if set(clingo_set) - set(python_set):
            print("  only in clingo:\n   ", "\n    ".join(map(str, set(clingo_set)-set(python_set))))
        if set(python_set) - set(clingo_set):
            print("  only in python:\n   ", "\n    ".join(map(str, set(python_set)-set(clingo_set))))
    return 1

# ---------------------------------------------------------------------------
# Pretty-printing helpers
# ---------------------------------------------------------------------------
def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---\n")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            if m:
                print(f"  {e.id:10} meters={dict(m)}")
        print(f"  fired rules: {sorted(set(n for n, *_ in sample.world.fired))}")
    if qa:
        print("\n== Story Q&A (grounded in this story) ==\n")
        for qa_item in sample.story_qa:
            print(f"Q: {qa_item.question}\nA: {qa_item.answer}\n")
        print("== World-knowledge Q&A (child level) ==\n")
        for qa_item in sample.world_qa:
            print(f"Q: {qa_item.question}\nA: {qa_item.answer}\n")

CURATED = [
    StoryParams(
        place="workshop", activity="wax_melting", prize="hair",
        name="Eli", gender="boy", parent="grandma", trait="daring"
    ),
    StoryParams(
        place="porch", activity="jar_cleanup", prize="hair",
        name="Mara", gender="girl", parent="grandpa", trait="helpful"
    ),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} Kid-approved candle adventures ready for storytelling:")
        for place, act, prize in stories[:10]:
            print(f"  {place} → {act} → {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 100, 100):
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
            header = f"### {p.name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 78 + "\n")

if __name__ == "__main__":
    main()
