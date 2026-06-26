#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/veil_pregnancy_slack_transformation_superhero_story.py
=============================================================================================================================

A standalone *story world* sketch for a tiny superhero tale about a pregnant
heroine, a magical veil, and a slackline.  The story includes Transformation (her
superhero form) and uses the seed words *veil*, *pregnancy*, *slack* while keeping
the style close to a Superhero Story for young children.

Initial story (used to build a world model):
---
Nova was a superhero who wore the Veil of Light.  The veil let her transform into
Starlight, the city's brightest guardian.  Nova loved being Starlight, and she
loved walking on the slackline in the park.  Her partner Max was always there.

One day, the villain Shade threatened the city park.  Nova wanted to transform
into Starlight and stop him, but Max said, "You are expecting a baby.  The
transformation might be too much."  Nova did not listen.  She tried to run, but
Max took her hand. "We can do this together, safely."

Nova pouted, but Max smiled and said, "How about we put on the slackline harness
and use it to move without strain?"  Nova hugged Max.  They wrapped the Veil of
Light around her and strapped on the harness.  Nova transformed gently, walked
the slackline to reach Shade, and used her wits to capture him.  The baby stayed
safe, and Nova was happy.

Causal state updates:
---
    do activity save_the_day         -> hero.meters["strained"] += 1
                                        hero.memes["joy"] += 1
    hero strained + worn prize       -> prize.meters["stressed"] += 1
    prize stressed                   -> prize.caretaker.workload += 1
    warning ignored                  -> hero.memes["defiance"] += 1
    partner grabs defiant hero       -> hero.memes["conflict"] += 1
    compromise accepted              -> hero.memes["joy"/"love"] += 1 ; conflict->0
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
MESS_KINDS = {"strained", "stressed"}
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
        female = {"heroine", "woman", "girl"}
        male = {"hero", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"partner": "partner", "villain": "villain"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the City Park"
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


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["strained"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("strain", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stressed"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} felt the strain.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["stressed"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more worry for {carer.label}.")
    return out


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
    Rule("strain", "physical", _r_strain),
    Rule("workload", "physical", _r_workload),
    Rule("grab_conflict", "social", _r_grab_conflict),
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
# Prediction
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "stressed": bool(prize and prize.meters["stressed"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs / narration beats
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "save_the_day": "the swift glow of transformation made her feel brave",
        "slackline_play": "the gentle balance on the line made the world feel calm",
    }.get(activity.id, "it made the day feel full of play")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the play table waited nearby."
    if activity.weather == "sunny":
        return f"The sun shone brightly over {setting.place}, and the slackline swayed gently."
    return f"{setting.place.capitalize()} looked ready for a day of heroics."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a superhero who wore the Veil of Light.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id}'s {parent.label_word} gave {hero.pronoun('object')} a special gift: "
        f"{prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"carried {prize.it()} with care everywhere."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One sunny day, "
    go = "were in" if world.setting.indoor else "went to"
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
    if not pred["stressed"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Your transformation might strain your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'd have to worry even more"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s think."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to transform was still tugging hard.")
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
    if predict_mess(world, hero, activity, prize.id)["stressed"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled. '
        f'"How about we {gear_def.prep} and {activity.verb} together?"'
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
# Screenplay (tell)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "heroine",
         hero_traits: Optional[list[str]] = None, parent_type: str = "partner") -> World:
    world = World(setting)
    world.weather = "sunny"
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["brave"] + (hero_traits or ["kind", "eager"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the partner"))
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
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city_park": Setting(place="the City Park", indoor=False, affords={"save_the_day", "slackline_play"}),
}

ACTIVITIES = {
    "save_the_day": Activity(
        id="save_the_day",
        verb="save the day as Starlight",
        gerund="being a superhero",
        rush="transform into Starlight",
        mess="strained",
        soil="drained from the effort",
        zone={"torso", "legs"},
        weather="sunny",
        keyword="superhero",
        tags={"hero", "transformation"},
    ),
    "slackline_play": Activity(
        id="slackline_play",
        verb="play on the slackline",
        gerund="walking on the slackline",
        rush="dash to the slackline",
        mess="balanced",
        soil="still safe",
        zone={"legs"},
        weather="sunny",
        keyword="slackline",
        tags={"balance", "slack"},
    ),
}

PRIZES = {
    "baby": Prize(
        label="baby bump",
        phrase="her growing baby bump",
        type="baby",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="slackline_harness",
        label="a safe slackline harness",
        covers={"legs", "torso"},
        guards={"strained", "balanced"},
        prep="put on the slackline harness first",
        tail="strapped on the slackline harness",
        plural=False,
    ),
]

HEROINE_NAMES = ["Nova", "Stella", "Aria", "Luna", "Rosa"]
HEROINE_TRAITS = ["brave", "kind", "eager", "creative", "gentle"]


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
# QA generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "superhero": [("What is a superhero?",
                   "A superhero is a person with special powers who helps others and keeps the city safe.")],
    "transformation": [("What does transformation mean?",
                        "Transformation means changing from one form to another, like putting on a magic veil to become a superhero.")],
    "veil": [("What is a veil?",
              "A veil is a piece of cloth you can wear.  A magic veil can help you change into something special.")],
    "pregnancy": [("What does it mean when a superhero is expecting a baby?",
                   "It means she has a baby growing inside her tummy, and she needs to be extra careful because the baby is precious.")],
    "slackline": [("What is a slackline?",
                   "A slackline is a rope stretched between two points that you can walk on to practice balance.  It is like a tightrope but a little bouncy.")],
    "slack": [("What does slack mean in the park?",
               "Slack is the looseness of the rope.  A slackline needs just the right amount of slack so you can balance without falling.")],
}
KNOWLEDGE_ORDER = ["superhero", "transformation", "veil", "pregnancy", "slackline", "slack"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "{kw}", "veil", and "slackline".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to {act.verb} but "
        f"{hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}, and they find a happy compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with a parent and child choosing a safe way to be a hero.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "brave"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} while expecting a baby?"
            ),
            answer=(
                f"It is about a {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place}, and {hero.id} is "
                f"wearing the Veil of Light and carrying {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do
