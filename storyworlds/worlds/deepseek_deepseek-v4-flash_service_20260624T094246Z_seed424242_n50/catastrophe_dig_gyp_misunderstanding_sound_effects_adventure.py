#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/catastrophe_dig_gyp_misunderstanding_sound_effects_adventure.py
===========================================================================================================================================

A standalone story world for "The Dig" tale and close variations,
featuring a misunderstanding, sound effects, and a mild catastrophe.

Seed words: catastrophe, dig, gyp
Style: Adventure
Features: Misunderstanding, Sound Effects

Initial story (used to build a world model):
---
Once upon a time, there was a little adventurous boy named Leo. He loved digging in the
backyard for treasure. One day, Leo's mom bought him a brand-new pair of shiny red boots.
Leo loved his boots and wore them everywhere.

One sunny afternoon, Leo and his mom went to the backyard. Leo had a map he had drawn
himself. "There's treasure buried under the big oak tree!" he said. His mom smiled.
"Be careful not to ruin your new boots," she said.

Leo started digging. Suddenly he heard a loud THUMP. "A monster!" he shouted, dropping
his shovel. "No, Leo," his mom said, "that was just a big rock hitting the side of the
bucket." But Leo was already running away. He tripped over a garden hose and fell into
a muddy puddle. His new boots were soaked and muddy.

His mom helped him up. "See? The monster was just a sound. Let's finish digging together."
They put on old play clothes and dug up a tin can. "A gyp! It's just a can," Leo said.
But his mom laughed. "The adventure was the real treasure." Leo smiled.
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
MESS_KINDS = {"muddy", "wet", "sandy"}
REGIONS = {"feet", "legs", "torso", "hands"}


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


@dataclass
class Setting:
    place: str = "the backyard"
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
    sound: str = ""  # sound effect used in the story


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
        self.sound_effects: list[str] = []

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
    out = []
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
    out = []
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


def _r_misunderstanding_scare(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["misunderstood"] >= THRESHOLD and actor.memes["scared"] < THRESHOLD:
            sig = ("scare", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["scared"] += 1
            # Catastrophe: actor drops something or falls
            if any(e.meters["dirty"] < THRESHOLD for e in world.worn_items(actor)):
                # cause a fall / mess
                for item in world.worn_items(actor):
                    if not item.protective:
                        item.meters["muddy"] += 1
                        item.meters["dirty"] += 1
                return ["__catastrophe__"]
    return []


CAUSAL_RULES = [
    Rule("soak", "physical", _r_soak),
    Rule("workload", "physical", _r_workload),
    Rule("scare", "social", _r_misunderstanding_scare),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__catastrophe__")
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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verb helpers
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "dig": "each scoop of dirt felt like a clue to something hidden",
        "explore": "every shadow held a new secret",
    }.get(activity.id, "it made the day feel like a grand quest")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the play table waited."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} glistened after the rain."
    return f"{setting.place.capitalize()} looked wide and ready for adventure."


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
    world.say(f"{hero.id} was a {desc} who loved exploring every corner of the yard.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
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
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, and "
        f"{hero.pronoun('possessive')} {parent.label_word} smiled."
    )


def sound_effect_narration(world: World, activity: Activity) -> str:
    sound = activity.sound or "a sudden THUMP"
    world.say(f"Suddenly {sound}!")
    world.sound_effects.append(sound)
    return sound


def misunderstanding(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["misunderstood"] += 1
    # The child misunderstands the sound
    world.say(f'"{activity.sound.upper()}! A monster!" {hero.id} shouted, dropping {hero.pronoun("possessive")} shovel.')
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label_word} said, "No, that was just a big rock."')


def catastrophe(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    # Child trips and falls, prize gets muddy
    world.say(
        f"But {hero.id} was already running away. {hero.pronoun().capitalize()} tripped over a garden hose "
        f"and fell into a muddy puddle."
    )
    for item in world.worn_items(hero):
        if not item.protective:
            item.meters["muddy"] += 1
            item.meters["dirty"] += 1
    hero.memes["scared"] = 0  # resolved after catastrophe
    propagate(world, narrate=True)


def resolve_misunderstanding(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(
        f'{parent.label_word.capitalize()} helped {hero.pronoun("object")} up. '
        f'"See? The monster was just a sound. Let\'s finish {activity.gerund} together."'
    )


def gyp_revelation(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f'They put on old play clothes and dug up a tin can. '
        f'"A gyp! It\'s just a can," {hero.id} said.'
    )
    world.facts["gyp"] = True
    world.say(
        f'But {hero.pronoun("possessive")} {parent.label_word} laughed. '
        f'"The adventure was the real treasure." {hero.id} smiled.'
    )
    hero.memes["joy"] += 1
    hero.memes["love"] += 1


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Leo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["adventurous", "curious"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 – setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – misunderstanding and catastrophe
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    sound_effect_narration(world, activity)
    misunderstanding(world, hero, parent, activity)
    catastrophe(world, hero, parent, activity)

    # Act 3 – resolution
    world.para()
    resolve_misunderstanding(world, parent, hero, activity)
    gyp_revelation(world, hero, parent, activity, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting,
                       conflict=hero.memes["misunderstood"] >= THRESHOLD,
                       resolved=True)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"dig"}),
    "forest": Setting(place="the forest", indoor=False, affords={"dig", "explore"}),
    "beach": Setting(place="the beach", indoor=False, affords={"dig"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig for treasure",
        gerund="digging for treasure",
        rush="dig faster",
        mess="muddy",
        soil="muddy and wet",
        zone={"feet", "legs", "hands"},
        weather="sunny",
        keyword="dig",
        tags={"dig", "mud"},
        sound="THUMP",
    ),
    "explore": Activity(
        id="explore",
        verb="explore the cave",
        gerund="exploring the cave",
        rush="run into the cave",
        mess="muddy",
        soil="covered in cave dust",
        zone={"feet", "legs", "torso"},
        weather="sunny",
        keyword="cave",
        tags={"cave", "dark"},
        sound="CRACK",
    ),
}

GEAR = [
    Gear(
        id="playclothes",
        label="old play clothes",
        covers={"feet", "legs", "hands", "torso"},
        guards={"muddy", "wet"},
        prep="go home and put on your old play clothes",
        tail="walked back home to get the old play clothes",
        plural=True,
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"muddy", "wet"},
        prep="put on your rain boots",
        tail="went to get the rain boots",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="gardening gloves",
        covers={"hands"},
        guards={"muddy"},
        prep="put on your gardening gloves",
        tail="grabbed the gardening gloves",
        plural=True,
    ),
]

PRIZES = {
    "shoes": Prize(label="shoes", phrase="brand-new shiny red boots", type="boots", region="feet", plural=True),
    "shirt": Prize(label="shirt", phrase="a clean adventure shirt", type="shirt", region="torso"),
    "pants": Prize(label="pants", phrase="new khaki pants", type="pants", region="legs", plural=True),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn"]
TRAITS = ["adventurous", "curious", "bold", "spirited", "daring"]


def valid_combos() -> list[tuple[str, str, str]]:
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


# ---------------------------------------------------------------------------
# Knowledge and QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "dig": [("What do you need to dig?",
             "You need a shovel or your hands, and usually you dig in dirt or sand.")],
    "mud": [("Why does mud stick to clothes?",
             "Mud is wet dirt, and it sticks because water makes the dirt particles clump together and cling to fabric.")],
    "cave": [("What is a cave?",
              "A cave is a dark, hollow space inside a rock or hill.")],
    "boots": [("Why do we wear boots when digging?",
               "Boots keep your feet dry and clean, and protect them from sharp rocks.")],
    "gyp": [("What does 'gyp' mean?",
             "Sometimes 'gyp' means a trick or disappointment, like when you find a tin can instead of treasure.")],
}
KNOWLEDGE_ORDER = ["dig", "mud", "cave", "boots", "gyp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short adventure story for a young child that includes "{kw}" and a misunderstanding.',
        f'Tell a story where a {hero.type} named {hero.id} {act.gerund} and hears a scary sound, '
        f"but learns it was just a rock.",
        f'Write a story that uses the sound "{act.sound}" and ends with a child finding a gyp but being happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    sound = act.sound
    qa = [
        QAItem(
            question=f"Who goes to {place} to {act.verb} in {pos} new {prize.label}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. "
                   f"They go to {place} and {hero.id} is wearing {pos} {prize.label}."
        ),
        QAItem(
            question=f"What sound did {hero.id} hear that scared {pos}?",
            answer=f"{hero.id} heard a loud {sound}. {hero.pronoun('possessive').capitalize()} {pw} explained it was just a rock."
        ),
        QAItem(
            question=f"What happened after {hero.id} heard the {sound}?",
            answer=f"{hero.id} got scared, dropped {pos} shovel, and ran. {sub} tripped and fell into mud, getting {pos} {prize.label} dirty."
        ),
        QAItem(
            question=f"What did {hero.id} find at the end of the {act.gerund}?",
            answer=f"{hero.id} dug up a tin can. {sub} called it a gyp, but {pw} said the adventure was the real treasure."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("gyp")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI & trace
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
    lines.append(f"  sound effects: {world.sound_effects}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", activity="dig", prize="shoes", name="Leo", gender="boy", parent="mother", trait="adventurous"),
    StoryParams(place="forest", activity="dig", prize="pants", name="Mia", gender="girl", parent="father", trait="curious"),
    StoryParams(place="beach", activity="dig", prize="shirt", name="Tim", gender="boy", parent="mother", trait="bold"),
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
            f"({prize.region}) from {activity.gerund}.)")


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
    lines = []
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
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a dig, a misunderstanding, a gyp. Adventure style.")
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
                 [params.trait, "curious"], params.parent)
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
