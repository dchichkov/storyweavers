#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/prime_oyster_nooney_lesson_learned_bad_ending.py
===========================================================================================================

A standalone *story world* sketch for "The Prime Oyster Nooney" tale and close,
*constraint-checked* variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a little cheerful girl named Nooney. She lived near
the ocean and loved exploring the tide pools. One day, Nooney's grandmother
gave her a special prime oyster shell. It was smooth and pearly, and Nooney
treasured it more than anything.

One sunny morning, Nooney and her grandmother went to the rocky shore. Nooney
wanted to dive for more shells, but her grandmother said no. "You'll lose your
prime oyster in the deep water, and it will be gone forever," her grandmother
said. Nooney didn't want to listen and tried to wade into the waves, but her
grandmother grabbed her hand and said, "You must resist the urge to dive today."

Nooney pouted and crossed her arms. "But I want to find more shells!" she said.
Her grandmother smiled and said, "How about we tie your prime oyster to your
wrist with this ribbon first and then look for shells together?" Nooney's face
lit up and she hugged her grandmother. "Yay, let's do it!" she said as they
found a soft ribbon.

Causal state updates:
---
    do activity                 -> actor.<mess> += 1
                                   actor.joy += 1
    actor careless + worn item  -> item.<mess>++, item.lost++   only if the item's
                                   region is in the splash zone and no worn protective
                                   gear covers that region
    worn item lost              -> item.caretaker.sorrow += 1    (more grief for the family)

Scripted social/emotional beats:
---
    warning ignored             -> actor.defiance += 1
    parent grabs a defiant child -> actor.conflict += 1          (child tension)
    bad ending (no fix)         -> actor.loss += 1 ; story ends with sadness
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
MESS_KINDS = {"wet", "lost", "broken", "sandy"}
REGIONS = {"feet", "legs", "torso", "hand"}


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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}
        return mapping.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the rocky shore"
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
        self.bad_ending: bool = False

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


def _r_lose_item(world: World) -> list[str]:
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
                sig = ("lose", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["lost"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and was lost forever."
                )
                world.bad_ending = True
    return out


def _r_sorrow(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["lost"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("sorrow", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["sorrow"] += 1
        out.append(f"That would bring great sorrow to {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0) < THRESHOLD or actor.memes.get("defiance", 0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    type("Rule", (), {"name": "lose", "tag": "physical", "apply": _r_lose_item})(),
    type("Rule", (), {"name": "sorrow", "tag": "physical", "apply": _r_sorrow})(),
    type("Rule", (), {"name": "grab_conflict", "tag": "social", "apply": _r_grab_conflict})(),
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


def predict_loss(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "lost": bool(prize and prize.meters["lost"] >= THRESHOLD),
        "sorrow": sum(e.memes.get("sorrow", 0) for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    mapping = {
        "dive": "the salt water sparkled like a thousand tiny gems",
        "dig": "the sand felt warm and soft between little toes",
        "climb": "the rocks were rough and full of secret paths",
        "splash": "the waves made a happy shushing sound",
    }
    return mapping.get(activity.id, "it made the day feel full of wonder")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the shell box waited nearby."
    return f"The breeze smelled of salt, and {setting.place} stretched out golden and wide."


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
    world.say(f"{hero.id} was a {desc} who loved the ocean more than anything.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "at the beach" if not world.setting.indoor else "inside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def gives(world: World, giver: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One special day, {hero.id}'s {giver.label_word} gave "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"held {prize.it()} close, as if {prize.it()} were the most precious thing in the world."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy morning, ", "sunny": "One sunny morning, "}.get(world.weather, "One morning, ")
    go = "were at" if world.setting.indoor else "went to"
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
    pred = predict_loss(world, hero, activity, prize.id)
    if not pred["lost"]:
        return False
    world.facts["predicted_loss"] = activity.soil
    world.facts["predicted_sorrow"] = pred["sorrow"]
    clause = f"You'll lose your {prize.label} {activity.soil}"
    if pred["sorrow"] >= THRESHOLD:
        clause += f", and then we will both be so sad"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s be careful."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the call of the sea was too strong.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can want to {activity.verb}, but we must keep your prime oyster safe."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes.get("conflict", 0) >= THRESHOLD:
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
    if predict_loss(world, hero, activity, prize.id)["lost"]:
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
        f"{hero.pronoun('possessive')} {prize.label} safe and sound, "
        f"and {parent.label_word} was laughing beside {hero.pronoun('object')}."
    )


def bad_ending(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["loss"] += 1
    hero.memes["sorrow"] += 1
    world.say(
        f"But the waves were too strong, and {hero.pronoun('possessive')} {prize.label} "
        f"slipped from {hero.pronoun('possessive')} grasp. It sank into the deep blue water "
        f"and was never seen again."
    )
    world.say(
        f"{hero.pronoun().capitalize()} cried and cried, and {hero.pronoun('possessive')} "
        f"{parent.label_word} held {hero.pronoun('object')} close. "
        f'"Sometimes we learn the hardest lessons," {parent.label_word} whispered. '
        f'"The prime oyster is gone, but you will remember this forever."'
    )
    world.bad_ending = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nooney", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "grandmother",
         use_bad_ending: bool = False) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

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

    introduce(world, hero)
    loves_activity(world, hero, activity)
    gives(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)

    if use_bad_ending or not warned:
        bad_ending(world, parent, hero, activity, prize)
        world.facts["lesson"] = "Listen to your elders or lose what you love"
    else:
        gear_def = compromise(world, parent, hero, activity, prize)
        if gear_def:
            accept(world, parent, hero, activity, prize, gear_def)
            world.facts["lesson"] = "Listen to wise advice and protect what is precious"
        else:
            bad_ending(world, parent, hero, activity, prize)
            world.facts["lesson"] = "Not all treasures can be saved without care"

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting,
                       conflict=hero.memes.get("grabbed_by", 0) >= THRESHOLD,
                       resolved=not world.bad_ending)
    return world


SETTINGS = {
    "shore": Setting(place="the rocky shore", indoor=False, affords={"dive", "dig", "splash"}),
    "cove": Setting(place="the hidden cove", indoor=False, affords={"dive", "splash"}),
    "beach": Setting(place="the sandy beach", indoor=False, affords={"dig", "splash"}),
    "pool": Setting(place="the tide pool", indoor=False, affords={"dive", "dig"}),
    "reef": Setting(place="the coral reef", indoor=False, affords={"dive"}),
}

ACTIVITIES = {
    "dive": Activity(
        id="dive",
        verb="dive for shells",
        gerund="diving for shells",
        rush="wade into the waves",
        mess="lost",
        soil="lost in the deep water",
        zone={"hand"},
        weather="sunny",
        keyword="dive",
        tags={"ocean", "shell"},
    ),
    "dig": Activity(
        id="dig",
        verb="dig in the sand",
        gerund="digging in the sand",
        rush="run to the sand",
        mess="sandy",
        soil="buried in the sand",
        zone={"hand"},
        weather="sunny",
        keyword="dig",
        tags={"sand", "shell"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the waves",
        gerund="splashing in the waves",
        rush="run into the surf",
        mess="wet",
        soil="washed away by the tide",
        zone={"hand"},
        weather="sunny",
        keyword="splash",
        tags={"wave", "wet"},
    ),
}

GEAR = [
    Gear(
        id="ribbon",
        label="a soft ribbon",
        covers={"hand"},
        guards={"lost", "sandy", "wet"},
        prep="tie your prime oyster to your wrist with this ribbon",
        tail="found a soft ribbon and tied the oyster to her wrist",
    ),
    Gear(
        id="pouch",
        label="a small pouch",
        covers={"hand"},
        guards={"lost", "sandy", "wet"},
        prep="put your prime oyster in this small pouch and tie it to your belt",
        tail="found a small pouch and secured the oyster to her belt",
    ),
    Gear(
        id="net",
        label="a little net bag",
        covers={"hand"},
        guards={"lost", "sandy"},
        prep="carry your prime oyster in this little net bag",
        tail="got the little net bag and placed the oyster safely inside",
    ),
]

PRIZES = {
    "oyster": Prize(
        label="prime oyster",
        phrase="a special prime oyster shell that was smooth and pearly",
        type="shell",
        region="hand",
    ),
    "pearl": Prize(
        label="nooney pearl",
        phrase="a precious nooney pearl that shimmered in the light",
        type="pearl",
        region="hand",
        genders={"girl", "boy"},
    ),
    "shell": Prize(
        label="beautiful shell",
        phrase="a beautiful spiral shell with pink stripes",
        type="shell",
        region="hand",
    ),
}

GIRL_NAMES = ["Nooney", "Luna", "Cora", "Maya", "Nora", "Rose", "Ivy", "Skye"]
BOY_NAMES = ["Finn", "Kai", "Leo", "Noah", "Eli", "Theo", "Jake", "Sam"]
TRAITS = ["curious", "adventurous", "stubborn", "brave", "spirited", "eager"]


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
    bad_ending: bool = False
    seed: Optional[int] = None


KNOWLEDGE = {
    "ocean": [("Why is the ocean salty?",
               "The ocean is salty because rivers carry tiny bits of salt from rocks into the sea, "
               "and over millions of years, the salt built up.")],
    "shell": [("What is inside a seashell?",
               "Seashells are the homes of small sea animals like clams and snails. "
               "When the animal leaves, the shell stays behind for us to find.")],
    "tide": [("What makes the tide go in and out?",
              "The moon pulls on the ocean with its gravity, making the water rise and fall. "
              "That is why we have high tide and low tide.")],
    "pearl": [("How does a pearl form?",
               "A pearl forms inside an oyster when a tiny grain of sand gets trapped. "
               "The oyster covers the sand with smooth layers to protect itself, and after a long time, a pearl is made.")],
    "ribbon": [("Why would you tie a shell to your wrist?",
                "Tying a shell or treasure to your wrist with a ribbon helps keep it safe "
                "so you do not lose it while you play near the water.")],
}
KNOWLEDGE_ORDER = ["ocean", "shell", "tide", "pearl", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a treasured shell, "
        f"a lesson, and listening to wise words" that includes the word "{kw}".',
        f"Tell a gentle but honest story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} with {hero.pronoun('possessive')} {prize.phrase} but learns a hard lesson "
        f"when {hero.pronoun('possessive')} {parent.label_word} warns of danger.",
        f'Write a simple story that uses the noun "{kw}" and ends with a child '
        f"learning to listen to {hero.pronoun('possessive')} {parent.label_word}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "at the beach" if not world.setting.indoor else "inside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"rainy": "rainy morning", "sunny": "sunny morning"}.get(world.weather, "morning")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a {day}, and {hero.id} is "
                f"holding {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} in {place} before "
                f"{pw} worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved playing {where} and "
                f"{act.gerund}. That joy became tricky because {pos} "
                f"{prize.label} could get lost."
            ),
        ),
        QAItem(
            question=(
                f"What special {prize.label} did {hero.id}'s {pw} give to the "
                f"{trait} {hero.type} before "
                f"the trip to {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. "
                f"{hero.id} treasured {prize.it()} and carried {prize.it()} everywhere."
            ),
        ),
    ]
    if f.get("conflict"):
        loss = f.get("predicted_loss", "lost")
        sorrow = f.get("predicted_sorrow", 0)
        why = (f"{pos.capitalize()} {pw} was worried because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would be {loss}")
        why += (f", and then both of them would be very sad. "
                if sorrow >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} hand and warned {obj} about the danger.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb} at {place}?"
            ),
            answer=why,
        ))
    if world.bad_ending:
        qa.append(QAItem(
            question=(
                f"What happened to {pos} {prize.label} at {place}?"
            ),
            answer=(
                f"{hero.pronoun('possessive').capitalize()} {prize.label} was lost forever "
                f"in the water because {sub} did not listen to {pos} {pw}. "
                f"{hero.pronoun().capitalize()} learned a very sad lesson that day."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What lesson did {trait} {hero.id} learn from losing {pos} {prize.label}?"
            ),
            answer=(
                f"{hero.pronoun().capitalize()} learned that when someone who loves you "
                f"gives you a warning, it is wise to listen. "
                f"The prime oyster was gone, but the lesson would stay with {obj} forever."
            ),
        ))
    else:
        gear = f.get("gear")
        if gear:
            qa.append(QAItem(
                question=(
                    f"How did {gear.label} help {hero.id} keep {pos} {prize.label} safe?"
                ),
                answer=(
                    f"They used {gear.label} to secure the {prize.label} so {sub} could "
                    f"{act.verb} without losing it. {pos.capitalize()} {pw} knew just the right thing to do."
                ),
            ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags or tag == "ocean":
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
    lines.append(f"  bad_ending: {world.bad_ending}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="shore",
        activity="dive",
        prize="oyster",
        name="Nooney",
        gender="girl",
        parent="grandmother",
        trait="curious",
        bad_ending=True,
    ),
    StoryParams(
        place="beach",
        activity="dig",
        prize="pearl",
        name="Finn",
        gender="boy",
        parent="grandfather",
        trait="stubborn",
        bad_ending=True,
    ),
    StoryParams(
        place="cove",
        activity="splash",
        prize="shell",
        name="Luna",
        gender="girl",
        parent="mother",
        trait="adventurous",
        bad_ending=True,
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the parent has no honest warning. "
                f"Try a prize held in {sorted(activity.zone)}.)")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a treasure, a lesson learned the hard way. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--bad-ending", action="store_true", help="force a bad ending where the treasure is lost")
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
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    bad_ending = args.bad_ending if args.bad_ending is not None else rng.random() < 0.7
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        bad_ending=bad_ending,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "adventurous"], params.parent,
                 use_bad_ending=params.bad_ending)
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
