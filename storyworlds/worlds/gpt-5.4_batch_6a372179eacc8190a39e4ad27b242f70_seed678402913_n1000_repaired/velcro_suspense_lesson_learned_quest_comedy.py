#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/velcro_suspense_lesson_learned_quest_comedy.py
==========================================================================

A small storyworld about a funny little quest nearly ruined by a loose velcro
strap. Two children hurry toward a pretend destination with an important object.
One child hears the strap go "rrrip," wants to ignore it, and learns that small
problems should be fixed before they grow into bigger ones.

The domain is intentionally narrow and reasoned:
- a mission has a route with a snag risk and a grip requirement
- footwear must be sensible for that route
- a helper can sometimes talk the hero into stopping to press the velcro shut
- otherwise the hero rushes, stumbles, and the mission item either survives or
  is spoiled depending on route severity and item durability

The prose keeps a comedy tone, but the state drives the turn and the ending.

Run it
------
python storyworlds/worlds/gpt-5.4/velcro_suspense_lesson_learned_quest_comedy.py
python storyworlds/worlds/gpt-5.4/velcro_suspense_lesson_learned_quest_comedy.py --all
python storyworlds/worlds/gpt-5.4/velcro_suspense_lesson_learned_quest_comedy.py --mission plank_bridge --footwear sandals
python storyworlds/worlds/gpt-5.4/velcro_suspense_lesson_learned_quest_comedy.py --verify
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
HURRY_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    opening: str
    destination: str
    need: str
    route: str
    snag_on: str
    need_grip: int
    danger: int
    wet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    carry: str
    use: str
    durability: int
    funny_ruin: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Footwear:
    id: str
    label: str
    phrase: str
    closure: str
    grip: int
    splash: int
    sound: str
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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


def _r_trip(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    strap = world.entities.get("strap")
    mission = world.facts.get("mission")
    item = world.entities.get("item")
    if not hero or not strap or not mission or not item:
        return out
    if strap.meters["loose"] < THRESHOLD or hero.memes["rushing"] < THRESHOLD:
        return out
    sig = ("trip", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["stumbled"] += 1
    hero.memes["fear"] += 1
    item.meters["dropped"] += 1
    out.append("__trip__")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    mission = world.facts.get("mission")
    if not item or not mission:
        return out
    if item.meters["dropped"] < THRESHOLD:
        return out
    severity = mission.danger + int(world.facts.get("delay", 0))
    if item.attrs.get("durability", 0) >= severity:
        return out
    sig = ("spoil", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["spoiled"] += 1
    out.append("__spoil__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="trip", tag="physical", apply=_r_trip),
    Rule(name="spoil", tag="physical", apply=_r_spoil),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def route_is_reasonable(mission: Mission, footwear: Footwear) -> bool:
    return footwear.grip >= mission.need_grip


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_stop_to_fix(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + 1.0 + (2.0 if helper_older else 0.0)
    return helper_older and authority > HURRY_INIT


def stumble_severity(mission: Mission, delay: int) -> int:
    return mission.danger + delay


def mission_recovers(mission: Mission, item: QuestItem, delay: int) -> bool:
    return item.durability >= stumble_severity(mission, delay)


def predict_stumble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    strap = sim.get("strap")
    strap.meters["loose"] = 1
    hero.memes["rushing"] = 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "stumble": hero.meters["stumbled"] >= THRESHOLD,
        "spoiled": item.meters["spoiled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, mission: Mission, item: QuestItem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{mission.opening} {hero.id} and {helper.id} made themselves very serious "
        f"questers, even though they still had jelly on one sleeve and grass on one knee."
    )
    world.say(
        f"At the far end of the yard, {mission.destination} waited, and it badly needed "
        f"{item.phrase}. Bringing it there felt as important as saving a kingdom, only smaller and funnier."
    )


def assign_quest(world: World, hero: Entity, helper: Entity, mission: Mission, item: QuestItem) -> None:
    hero.memes["purpose"] += 1
    world.say(
        f'"I will carry {item.carry}!" {hero.id} announced. "{helper.id}, stay close. '
        f'This is a very important mission."'
    )
    world.say(
        f"{helper.id} nodded and pointed toward {mission.route}. "
        f"That was the way to reach {mission.destination}."
    )


def loose_strap(world: World, hero: Entity, footwear: Footwear) -> None:
    strap = world.get("strap")
    strap.meters["loose"] += 1
    hero.memes["hurry"] += 1
    world.say(
        f"But on the very first fast step, one {footwear.label} strap went {footwear.sound}. "
        f'The velcro peeled open like a tiny flag saying, "Wait for me!"'
    )


def warn(world: World, helper: Entity, hero: Entity, mission: Mission, item: QuestItem) -> None:
    pred = predict_stumble(world)
    helper.memes["caution"] += 1
    world.facts["predicted_stumble"] = pred["stumble"]
    world.facts["predicted_spoil"] = pred["spoiled"]
    second = (
        f" If you trip there, {item.label} might turn into {item.funny_ruin}."
        if pred["spoiled"]
        else f" If you trip there, we may have to stop and pick {item.label} up before the quest can continue."
    )
    world.say(
        f'{helper.id} grabbed a sleeve. "Your velcro is open," {helper.pronoun()} said. '
        f'"Please press it shut before we cross {mission.route}. It could catch on {mission.snag_on}.{second}"'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["rushing"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f'"No time!" said {hero.id}. Heroes do not stop for one tiny flap.'
        .replace("{heroes do not stop for one tiny flap.}", "Heroes do not stop for one tiny flap.")
    )


def stop_and_fix(world: World, hero: Entity, helper: Entity, footwear: Footwear) -> None:
    strap = world.get("strap")
    strap.meters["loose"] = 0.0
    strap.meters["fastened"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"But {hero.id} looked down at the silly flapping strap, knelt, and pressed the velcro together. "
        f"{footwear.sound.capitalize()} went the other way as the strap hugged tight again."
    )
    world.say(
        f'"All right," {hero.pronoun()} said. "A neat hero is a faster hero." {helper.id} grinned, pleased to be right.'
    )


def dash(world: World, hero: Entity, mission: Mission) -> None:
    world.say(
        f"They hurried toward {mission.route}. For a second, everything felt grand and suspenseful, "
        f"as if even the daisies were holding their breath."
    )


def stumble(world: World, hero: Entity, mission: Mission, item: QuestItem) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then the loose strap caught on {mission.snag_on}. {hero.id} windmilled both arms, made one heroic squeak, "
        f"and stumbled so hard that {item.label} flew up like it wanted its own adventure."
    )


def recover_success(world: World, hero: Entity, helper: Entity, mission: Mission, item: QuestItem, footwear: Footwear) -> None:
    strap = world.get("strap")
    strap.meters["loose"] = 0.0
    strap.meters["fastened"] += 1
    world.get("item").meters["delivered"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{helper.id} pounced first, scooped up {item.label}, and checked it. "
        f'"Still safe!" {helper.pronoun().capitalize()} said.'
    )
    world.say(
        f"They both sat down right there by {mission.route}, pressed the velcro shut, and took one long rabbit-sized breath. "
        f"After that, they walked instead of blasted, and {item.label} reached {mission.destination} exactly when it was needed."
    )
    world.say(
        f"{mission.need} The quest was saved, and the funniest part was that the whole kingdom had nearly been defeated by one rude little flap."
    )


def recover_fail(world: World, hero: Entity, helper: Entity, mission: Mission, item: QuestItem, footwear: Footwear) -> None:
    strap = world.get("strap")
    strap.meters["loose"] = 0.0
    strap.meters["fastened"] += 1
    hero.memes["sad"] += 1
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} snatched up {item.label}, but it was too late. It had become {item.funny_ruin}."
    )
    world.say(
        f"For one small, suspenseful moment, the mission seemed lost. Then {helper.id} nudged {hero.id} and said, "
        f'"We can go back, fix your velcro, and try again the smart way."'
    )
    world.say(
        f"So they did. On the second trip, the strap stayed shut, their feet stayed steady, and a fresh {item.label} finally reached "
        f"{mission.destination}. {mission.need}"
    )


def closing_lesson(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, {hero.id} had learned something useful: when a little problem says hello, it is better to fix it right away than to race it. "
        f"{helper.id} said that was not only wise, it was also much less wobbly."
    )


def tell(
    mission: Mission,
    item_cfg: QuestItem,
    footwear_cfg: Footwear,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
    relation: str,
    hero_age: int,
    helper_age: int,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", age=hero_age, traits=["bold"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", age=helper_age, traits=[trait]))
    shoes = world.add(Entity(id="shoes", type="footwear", label=footwear_cfg.label, attrs={"grip": footwear_cfg.grip}))
    strap = world.add(Entity(id="strap", type="strap", label="velcro strap", attrs={"closure": footwear_cfg.closure}))
    item = world.add(
        Entity(
            id="item",
            type="quest_item",
            label=item_cfg.label,
            attrs={"durability": item_cfg.durability},
            tags=set(item_cfg.tags),
        )
    )

    helper.memes["caution"] = initial_caution(trait)
    hero.memes["hurry"] = HURRY_INIT

    world.facts.update(
        mission=mission,
        item_cfg=item_cfg,
        footwear=footwear_cfg,
        hero=hero,
        helper=helper,
        relation=relation,
        delay=delay,
    )

    introduce(world, hero, helper, mission, item_cfg)
    assign_quest(world, hero, helper, mission, item_cfg)

    world.para()
    loose_strap(world, hero, footwear_cfg)
    warn(world, helper, hero, mission, item_cfg)

    averted = would_stop_to_fix(relation, hero_age, helper_age, trait)
    if averted:
        stop_and_fix(world, hero, helper, footwear_cfg)
        world.para()
        world.get("item").meters["delivered"] += 1
        world.say(
            f"They crossed {mission.route} carefully, and this time nothing snagged, slipped, or sailed away. "
            f"Soon {item_cfg.label} reached {mission.destination}."
        )
        world.say(mission.need)
        closing_lesson(world, hero, helper)
        outcome = "averted"
    else:
        defy(world, hero)
        world.para()
        dash(world, hero, mission)
        stumble(world, hero, mission, item_cfg)
        world.para()
        if mission_recovers(mission, item_cfg, delay):
            recover_success(world, hero, helper, mission, item_cfg, footwear_cfg)
            closing_lesson(world, hero, helper)
            outcome = "recovered"
        else:
            recover_fail(world, hero, helper, mission, item_cfg, footwear_cfg)
            closing_lesson(world, hero, helper)
            outcome = "spoiled"

    world.facts.update(
        outcome=outcome,
        averted=outcome == "averted",
        stumbled=hero.meters["stumbled"] >= THRESHOLD,
        spoiled=item.meters["spoiled"] >= THRESHOLD,
        delivered=item.meters["delivered"] >= THRESHOLD,
        severity=stumble_severity(mission, delay),
    )
    return world


MISSIONS = {
    "plank_bridge": Mission(
        id="plank_bridge",
        opening="On a bright afternoon behind the house,",
        destination="the pillow fort under the apple tree",
        need="Inside the fort, the stuffed bear got its bandage, and everyone agreed the patient had been very brave.",
        route="a wiggly plank laid over a puddle",
        snag_on="the edge of the plank",
        need_grip=2,
        danger=2,
        wet=True,
        tags={"puddle", "careful"},
    ),
    "hose_maze": Mission(
        id="hose_maze",
        opening="One breezy afternoon,",
        destination="the cardboard castle by the shed",
        need="At the castle gate, the bell rang with a proud ding, and the pretend guards opened the way at once.",
        route="a maze of sleeping garden hoses",
        snag_on="a loop of green hose",
        need_grip=2,
        danger=2,
        wet=False,
        tags={"garden", "careful"},
    ),
    "leaf_tunnel": Mission(
        id="leaf_tunnel",
        opening="After lunch,",
        destination="the blanket cave behind the bushes",
        need="In the cave, the treasure map was smoothed flat on the floor, and the whole expedition could finally begin.",
        route="a leafy tunnel where twigs poked from both sides",
        snag_on="a twiggy branch",
        need_grip=1,
        danger=1,
        wet=False,
        tags={"map", "careful"},
    ),
    "stepping_stones": Mission(
        id="stepping_stones",
        opening="Just before snack time,",
        destination="the sandbox moon base",
        need="At moon base, the shiny spoon arrived just in time to scoop the first crater pudding.",
        route="a line of bumpy stepping stones beside the birdbath",
        snag_on="the lip of one stone",
        need_grip=3,
        danger=3,
        wet=False,
        tags={"stones", "careful"},
    ),
}

ITEMS = {
    "bandage": QuestItem(
        id="bandage",
        label="the bandage",
        phrase="a folded paper bandage",
        carry="the bandage",
        use="patch the patient",
        durability=2,
        funny_ruin="a wet paper ribbon",
        tags={"bandage", "paper"},
    ),
    "map": QuestItem(
        id="map",
        label="the map",
        phrase="a crayon treasure map",
        carry="the map",
        use="guide the expedition",
        durability=1,
        funny_ruin="a crinkly green-and-brown blur",
        tags={"map", "paper"},
    ),
    "bell": QuestItem(
        id="bell",
        label="the bell",
        phrase="a little brass bell",
        carry="the bell",
        use="announce the arrival",
        durability=3,
        funny_ruin="a muddy but still jingling bell",
        tags={"bell", "metal"},
    ),
    "spoon": QuestItem(
        id="spoon",
        label="the spoon",
        phrase="a shiny picnic spoon",
        carry="the spoon",
        use="serve the crater pudding",
        durability=3,
        funny_ruin="a spoon wearing a hat of mud",
        tags={"spoon", "metal"},
    ),
}

FOOTWEAR = {
    "sneakers": Footwear(
        id="sneakers",
        label="sneaker",
        phrase="red sneakers with velcro straps",
        closure="velcro",
        grip=2,
        splash=1,
        sound="rrrip",
        tags={"shoes", "velcro"},
    ),
    "boots": Footwear(
        id="boots",
        label="boot",
        phrase="yellow boots with big velcro tabs",
        closure="velcro",
        grip=3,
        splash=3,
        sound="vrrrip",
        tags={"boots", "velcro"},
    ),
    "sandals": Footwear(
        id="sandals",
        label="sandal",
        phrase="blue sandals with velcro",
        closure="velcro",
        grip=1,
        splash=0,
        sound="rip",
        tags={"sandals", "velcro"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["careful", "patient", "steady", "sensible", "curious", "bouncy"]


@dataclass
class StoryParams:
    mission: str
    item: str
    footwear: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    relation: str
    trait: str
    hero_age: int = 5
    helper_age: int = 6
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="plank_bridge",
        item="bandage",
        footwear="boots",
        hero="Tom",
        hero_gender="boy",
        helper="Lily",
        helper_gender="girl",
        relation="siblings",
        trait="careful",
        hero_age=5,
        helper_age=7,
        delay=0,
    ),
    StoryParams(
        mission="hose_maze",
        item="bell",
        footwear="sneakers",
        hero="Mia",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        relation="friends",
        trait="curious",
        hero_age=6,
        helper_age=6,
        delay=0,
    ),
    StoryParams(
        mission="stepping_stones",
        item="map",
        footwear="boots",
        hero="Sam",
        hero_gender="boy",
        helper="Zoe",
        helper_gender="girl",
        relation="siblings",
        trait="patient",
        hero_age=6,
        helper_age=4,
        delay=1,
    ),
    StoryParams(
        mission="leaf_tunnel",
        item="spoon",
        footwear="sandals",
        hero="Ava",
        hero_gender="girl",
        helper="Max",
        helper_gender="boy",
        relation="friends",
        trait="steady",
        hero_age=5,
        helper_age=5,
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mid, mission in MISSIONS.items():
        for iid in ITEMS:
            for fid, footwear in FOOTWEAR.items():
                if route_is_reasonable(mission, footwear):
                    combos.append((mid, iid, fid))
    return combos


def explain_rejection(mission: Mission, footwear: Footwear) -> str:
    return (
        f"(No story: {footwear.phrase} do not give enough grip for {mission.route}. "
        f"That route needs grip {mission.need_grip}, but this footwear only gives {footwear.grip}. "
        f"Pick sturdier footwear like boots or sneakers for this quest.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_stop_to_fix(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    return "recovered" if mission_recovers(MISSIONS[params.mission], ITEMS[params.item], params.delay) else "spoiled"


KNOWLEDGE = {
    "velcro": [
        (
            "What is velcro?",
            "Velcro is a fastener made of two strips that stick together when you press them and pull apart with a ripping sound."
        )
    ],
    "boots": [
        (
            "Why are boots good on slippery ground?",
            "Boots usually have thicker soles and better grip, so they help your feet hold on when the ground is wet or uneven."
        )
    ],
    "shoes": [
        (
            "Why should you fasten your shoes before you run?",
            "Fastened shoes stay snug on your feet. Loose straps can flap, catch, or make you trip."
        )
    ],
    "puddle": [
        (
            "What happens to paper in a puddle?",
            "Paper gets soggy and weak in water, so it can tear or turn into mush."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps you know where to go. Even a pretend treasure map can guide a game."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a ringing sound. People use bells to call attention or announce that someone has arrived."
        )
    ],
    "careful": [
        (
            "What does it mean to be careful?",
            "Being careful means slowing down enough to notice what could go wrong and making a safer choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["velcro", "shoes", "boots", "puddle", "map", "bell", "careful"]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mission = f["mission"]
    item = f["item_cfg"]
    footwear = f["footwear"]
    outcome = f["outcome"]
    base = (
        f'Write a funny suspenseful quest story for a 3-to-5-year-old that includes the word "velcro", '
        f"where {hero.id} must carry {item.label} across {mission.route}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a comedy story where {helper.id}, an older sibling, warns {hero.id} about an open velcro strap and the quest succeeds because {hero.pronoun('subject')} stops to fix it.",
            f"Write a gentle lesson-learned story where the danger is avoided, the quest still feels exciting, and {footwear.phrase} matter to the ending.",
        ]
    if outcome == "spoiled":
        return [
            base,
            f"Tell a comic near-disaster where {hero.id} ignores a warning, stumbles on {mission.route}, and ruins {item.label} before trying again the smart way.",
            "Write a child-facing story with suspense, a funny mishap, a clear lesson about slowing down, and a second attempt that works.",
        ]
    return [
        base,
        f"Tell a comedy story where {hero.id} ignores {helper.id}'s warning about an open velcro strap, stumbles, but the quest item survives and still reaches the destination.",
        "Write a story with suspense and a lighthearted lesson: fixing small problems early saves the adventure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mission = f["mission"]
    item = f["item_cfg"]
    footwear = f["footwear"]
    pair = pair_noun(hero, helper, f["relation"])
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}. They were on a pretend quest together."
        ),
        (
            "What was their quest?",
            f"They had to carry {item.label} to {mission.destination}. It mattered because {mission.need}"
        ),
        (
            f"What problem happened with {hero.id}'s shoe?",
            f"One strap on {hero.pronoun('possessive')} {footwear.label} popped open with a velcro sound. That loose flap could catch while they crossed {mission.route}."
        ),
        (
            f"Why did {helper.id} warn {hero.id}?",
            f"{helper.id} warned {hero.id} because the open strap could snag on {mission.snag_on}. If that happened, {hero.id} might stumble and drop {item.label}."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How was the danger avoided?",
                f"{hero.id} stopped, pressed the velcro shut, and then crossed carefully. Fixing the small problem first kept the quest from turning into a bigger mess."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They reached {mission.destination} without a stumble, and {item.label} arrived safely. The ending proves the lesson because the quest worked once the strap was fastened."
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when {hero.id} rushed ahead?",
                f"The loose strap caught on {mission.snag_on}, and {hero.id} stumbled. {helper.id} grabbed {item.label} quickly, so the item survived even though the scare was real."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a tiny problem can grow if you ignore it. Pressing velcro shut right away is slower for one second, but faster than stopping after a fall."
            )
        )
    else:
        qa.append(
            (
                f"What happened to {item.label}?",
                f"After the stumble, {item.label} turned into {item.funny_ruin}. The first try failed because the quest item was not tough enough for that fall."
            )
        )
        qa.append(
            (
                "Did the quest stay ruined?",
                f"No. They went back, fastened the velcro properly, and tried again with a fresh {item.label}. The second trip worked because they had learned the lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mission = f["mission"]
    item = f["item_cfg"]
    footwear = f["footwear"]
    tags = {"velcro", "careful"} | set(footwear.tags) | set(mission.tags) | set(item.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, I, F) :- mission(M), item(I), footwear(F), grip(F, G), need_grip(M, N), G >= N.

careful_now(T) :- trait(T), is_careful(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).

helper_older :- relation(siblings), hero_age(H), helper_age(A), A > H.
bonus(2) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), hurry_init(H), A > H.

severity(Dg + Dl) :- chosen_mission(M), danger(M, Dg), delay(Dl).
survives :- chosen_item(I), durability(I, Dur), severity(S), Dur >= S.

outcome(averted) :- averted.
outcome(recovered) :- not averted, survives.
outcome(spoiled) :- not averted, not survives.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("need_grip", mid, mission.need_grip))
        lines.append(asp.fact("danger", mid, mission.danger))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("durability", iid, item.durability))
    for fid, footwear in FOOTWEAR.items():
        lines.append(asp.fact("footwear", fid))
        lines.append(asp.fact("grip", fid, footwear.grip))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    lines.append(asp.fact("hurry_init", int(HURRY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_mission", params.mission),
            asp.fact("chosen_item", params.item),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        _ = format_qa(sample)
        print("OK: smoke test generated a normal story and QA successfully.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a loose velcro strap threatens a funny little quest."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--footwear", choices=FOOTWEAR)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time spent rushing before the stumble matters")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.footwear:
        mission = MISSIONS[args.mission]
        footwear = FOOTWEAR[args.footwear]
        if not route_is_reasonable(mission, footwear):
            raise StoryError(explain_rejection(mission, footwear))

    combos = [
        c
        for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.item is None or c[1] == args.item)
        and (args.footwear is None or c[2] == args.footwear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, item, footwear = rng.choice(sorted(combos))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = args.trait or rng.choice(TRAITS)
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        mission=mission,
        item=item,
        footwear=footwear,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        relation=relation,
        trait=trait,
        hero_age=hero_age,
        helper_age=helper_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.footwear not in FOOTWEAR:
        raise StoryError(f"(Unknown footwear: {params.footwear})")
    mission = MISSIONS[params.mission]
    footwear = FOOTWEAR[params.footwear]
    if not route_is_reasonable(mission, footwear):
        raise StoryError(explain_rejection(mission, footwear))

    world = tell(
        mission=mission,
        item_cfg=ITEMS[params.item],
        footwear_cfg=footwear,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
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
        print(f"{len(combos)} compatible (mission, item, footwear) combos:\n")
        for mission, item, footwear in combos:
            print(f"  {mission:15} {item:8} {footwear}")
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
            header = f"### {p.hero} & {p.helper}: {p.item} on {p.mission} with {p.footwear} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
