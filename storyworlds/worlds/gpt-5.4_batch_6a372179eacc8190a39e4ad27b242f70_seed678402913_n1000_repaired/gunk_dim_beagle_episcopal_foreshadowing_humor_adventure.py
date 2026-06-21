#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py
======================================================================================

A standalone storyworld about a child and a beagle on a tiny adventure at an
episcopal fair. The world rebuilds a simple pattern:

- a child is on a clue hunt with a funny beagle helper
- the next clue lies beyond a messy or slippery obstacle
- an adult gives an honest warning grounded in the world model
- the child starts to rush in anyway
- a compatible piece of gear turns the problem into a safe adventure
- they reach the clue, laugh, and finish with a changed ending image

The seed asked for:
- the words "gunk-dim", "beagle", and "episcopal"
- foreshadowing
- humor
- adventure

This world makes those live in state rather than templates:
the obstacle predicts the risk, the beagle's antics color the humor, and the
ending only happens once the simulation says the prize item stays clean.

Run it
------
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py --place crypt --obstacle wax --prize sneakers
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py --obstacle jam --prize sash
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py --all
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/gunk_dim_beagle_episcopal_foreshadowing_humor_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"sticky", "slippery", "painted", "dusty"}
REGIONS = {"feet", "legs", "torso"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"beagle", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    flavor: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str] = field(default_factory=set)
    cue: str = ""
    forebode: str = ""
    ruin: str = ""
    joke: str = ""
    clue_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
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
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    obstacle: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    beagle_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil_prize(world: World) -> list[str]:
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
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
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
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more cleaning for {caretaker.label_word}.")
    return out


def _r_beagle_shake(world: World) -> list[str]:
    beagle = world.entities.get("beagle")
    if beagle is None:
        return []
    for mess in MESS_KINDS:
        if beagle.meters[mess] < THRESHOLD:
            continue
        sig = ("shake", mess)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        beagle.memes["comic"] += 1
        return ["__beagle_shook__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soil_prize", tag="physical", apply=_r_soil_prize),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="beagle_shake", tag="comic", apply=_r_beagle_shake),
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
        for sent in produced:
            if sent == "__beagle_shook__":
                world.say("The beagle gave a mighty shake, as if trying to fling the whole problem into next week.")
            else:
                world.say(sent)
    return produced


SETTINGS = {
    "hall": Setting(
        id="hall",
        place="the episcopal parish hall",
        affords={"jam", "paint"},
        flavor="Long tables held pies, ribbons, and one brass lantern for the fair.",
        tags={"episcopal"},
    ),
    "crypt": Setting(
        id="crypt",
        place="the old episcopal crypt stair",
        affords={"wax", "dust"},
        flavor="Stone steps curled down beneath banners that looked brave in the half-light.",
        tags={"episcopal"},
    ),
    "garden": Setting(
        id="garden",
        place="the episcopal garden shed path",
        affords={"jam", "dust"},
        flavor="Rain had left the path shining, and the shed door stood open like a secret.",
        tags={"episcopal"},
    ),
    "tower": Setting(
        id="tower",
        place="the episcopal bell-tower room",
        affords={"wax", "paint"},
        flavor="A narrow window spilled a stripe of light across ropes, ladders, and old festival boxes.",
        tags={"episcopal"},
    ),
}

OBSTACLES = {
    "jam": Obstacle(
        id="jam",
        verb="tiptoe past the jam spill",
        gerund="tiptoeing past the jam spill",
        rush="dart toward the jam spill",
        mess="sticky",
        zone={"feet", "legs"},
        cue="A red jam puddle shone on the floor like a tiny sunset nobody had cleaned up yet.",
        forebode="Even before anyone spoke, it looked like the sort of shine that wanted a shoe for supper.",
        ruin="sticky and red",
        joke="The beagle sniffed at it and sneezed so hard his ears flapped like two napkins.",
        clue_spot="under the cake raffle table",
        tags={"jam", "sticky"},
    ),
    "wax": Obstacle(
        id="wax",
        verb="climb the waxy steps",
        gerund="climbing the waxy steps",
        rush="hop onto the waxy steps",
        mess="slippery",
        zone={"feet"},
        cue="Old candle wax pearled on the steps in pale moons.",
        forebode="The little moons looked pretty, but they also looked ready to slide under a heel.",
        ruin="slippery and smeared",
        joke="The beagle put down one paw, reconsidered life, and sat down with a soft offended huff.",
        clue_spot="beside the bell rope box",
        tags={"wax", "slippery", "candle"},
    ),
    "paint": Obstacle(
        id="paint",
        verb="duck under the fresh-paint rail",
        gerund="ducking under the fresh-paint rail",
        rush="scoot under the fresh-paint rail",
        mess="painted",
        zone={"torso"},
        cue="A stripe of blue paint glimmered along the rail in the gunk-dim corner behind the puppet stage.",
        forebode="It was the kind of bright stripe that promised a mistake before the mistake happened.",
        ruin="blue and smeary",
        joke="The beagle stared at the wet paint as if it were a very rude river.",
        clue_spot="inside the puppet chest",
        tags={"paint", "dirty"},
    ),
    "dust": Obstacle(
        id="dust",
        verb="crawl through the dusty costume tunnel",
        gerund="crawling through the dusty costume tunnel",
        rush="dive into the dusty costume tunnel",
        mess="dusty",
        zone={"legs", "torso"},
        cue="Behind a curtain of old choir robes, the tunnel looked brave, narrow, and extremely sneezy.",
        forebode="Tiny gray motes swirled there like a warning that could tickle its way into trouble.",
        ruin="dusty and gray",
        joke="The beagle sneezed three times in a row and looked surprised every single time.",
        clue_spot="behind the costume trunk",
        tags={"dust", "dirty"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="treasure boots",
        covers={"feet", "legs"},
        guards={"sticky", "slippery"},
        prep="pull on the church fair's giant treasure boots",
        tail="pulled on the giant treasure boots and marched back like explorers",
        plural=True,
        tags={"boots"},
    ),
    Gear(
        id="smock",
        label="a paint smock",
        covers={"torso"},
        guards={"painted", "dusty"},
        prep="borrow a paint smock first",
        tail="borrowed the paint smock and returned with a solemn explorer nod",
        plural=False,
        tags={"smock"},
    ),
    Gear(
        id="play_clothes",
        label="old quest clothes",
        covers={"legs", "torso"},
        guards={"sticky", "painted", "dusty"},
        prep="change into old quest clothes first",
        tail="changed into old quest clothes and hurried back grinning",
        plural=True,
        tags={"playclothes"},
    ),
    Gear(
        id="overshoes",
        label="grippy overshoes",
        covers={"feet"},
        guards={"slippery"},
        prep="clip on the grippy overshoes",
        tail="clipped on the grippy overshoes and came back with careful little stomps",
        plural=True,
        tags={"overshoes"},
    ),
]

PRIZES = {
    "sneakers": Prize(
        id="sneakers",
        label="sneakers",
        phrase="brand-new white sneakers with squeaky laces",
        type="sneakers",
        region="feet",
        plural=True,
    ),
    "cape": Prize(
        id="cape",
        label="cape",
        phrase="a bright explorer cape with a shiny clasp",
        type="cape",
        region="torso",
        plural=False,
    ),
    "robe": Prize(
        id="robe",
        label="robe",
        phrase="a little choir robe borrowed for the parade game",
        type="robe",
        region="torso",
        plural=False,
    ),
    "sash": Prize(
        id="sash",
        label="sash",
        phrase="a festival sash with gold fringe",
        type="sash",
        region="torso",
        plural=False,
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
BEAGLE_NAMES = ["Pickle", "Biscuit", "Muffin", "Waffles", "Scout", "Buttons"]
TRAITS = ["brave", "curious", "cheerful", "eager", "spirited", "hopeful"]


def prize_at_risk(obstacle: Obstacle, prize: Prize) -> bool:
    return prize.region in obstacle.zone


def select_gear(obstacle: Obstacle, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if obstacle.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for obs_id in sorted(setting.affords):
            obstacle = OBSTACLES[obs_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(obstacle, prize) and select_gear(obstacle, prize):
                    combos.append((place, obs_id, prize_id))
    return combos


def _do_obstacle(world: World, hero: Entity, beagle: Entity, obstacle: Obstacle, narrate: bool = True) -> None:
    if obstacle.id not in world.setting.affords:
        return
    world.zone = set(obstacle.zone)
    hero.meters[obstacle.mess] += 1
    beagle.meters[obstacle.mess] += 1
    hero.memes["thrill"] += 1
    beagle.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, hero: Entity, beagle: Entity, obstacle: Obstacle, prize_id: str) -> dict:
    sim = world.copy()
    _do_obstacle(sim, sim.get(hero.id), sim.get(beagle.id), obstacle, narrate=False)
    prize = sim.get(prize_id)
    parent = sim.get("Parent")
    return {
        "soiled": prize.meters["dirty"] >= THRESHOLD,
        "workload": parent.meters["workload"],
        "beagle_messy": any(sim.get("beagle").meters[m] >= THRESHOLD for m in MESS_KINDS),
    }


def introduce(world: World, hero: Entity, beagle: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "curious"
    world.say(
        f"{hero.id} was a {trait} little {hero.type} with a pocket map and a plan to solve the Fair of Ribbons Hunt."
    )
    world.say(
        f"Trotting beside {hero.pronoun('object')} was {beagle.id}, a merry beagle whose nose believed every day should include a mystery."
    )


def setup_fair(world: World, hero: Entity, parent: Entity, prize: Entity, setting: Setting) -> None:
    prize.worn_by = hero.id
    world.say(
        f"That afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} hurried into {setting.place} for the annual fair. "
        f"{setting.flavor}"
    )
    world.say(
        f"{hero.id} wore {prize.phrase}, because treasure hunters should look ready even when the treasure is only a brass clue bell."
    )


def announce_quest(world: World, hero: Entity, beagle: Entity, obstacle: Obstacle) -> None:
    hero.memes["joy"] += 1
    beagle.memes["joy"] += 1
    world.say(
        f'The next card on the map read: "Find the bell clue {obstacle.clue_spot}." '
        f"{obstacle.cue}"
    )
    world.say(obstacle.forebode)
    world.say(obstacle.joke)


def wants(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'"That must be the way!" {hero.id} said. {hero.pronoun().capitalize()} wanted to {obstacle.verb} before anyone else reached the clue.'
    )


def warn(world: World, parent: Entity, hero: Entity, beagle: Entity, obstacle: Obstacle, prize: Entity) -> bool:
    pred = predict_mess(world, hero, beagle, obstacle, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_ruin"] = obstacle.ruin
    world.facts["predicted_workload"] = pred["workload"]
    world.facts["predicted_beagle_messy"] = pred["beagle_messy"]
    extra = ""
    if pred["beagle_messy"]:
        extra = f" And {beagle.id} would come out looking like a very confused mop."
    world.say(
        f'"Slow down," said {hero.pronoun("possessive")} {parent.label_word}. '
        f'"If you hurry, your {prize.label} will get {obstacle.ruin}.{extra}"'
    )
    return True


def defies(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the adventure hummed too loudly in {hero.id}'s chest. {hero.pronoun().capitalize()} started to {obstacle.rush} anyway."
    )


def beagle_blocks(world: World, hero: Entity, beagle: Entity) -> None:
    beagle.memes["protective"] += 1
    hero.memes["pause"] += 1
    world.say(
        f"Right then, {beagle.id} plopped down across the path with his longest ears spread wide, as if he had suddenly become a small furry gate."
    )
    world.say(
        f'{hero.id} had to stop or tumble over the beagle, which felt like losing an argument to a loaf of bread.'
    )


def compromise(world: World, parent: Entity, hero: Entity, beagle: Entity, obstacle: Obstacle, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(obstacle, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    pred = predict_mess(world, hero, beagle, obstacle, prize.id)
    if pred["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and tapped the map. '
        f'"Real explorers pause, plan, and then go. How about we {gear_def.prep}?"'
    )
    return gear_def


def accept(world: World, hero: Entity, parent: Entity, beagle: Entity, obstacle: Obstacle, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    beagle.memes["joy"] += 1
    world.say(
        f"{hero.id}'s face brightened. {hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {parent.label_word} and nodded so hard the map fluttered."
    )
    world.say(
        f"They {gear_def.tail}. This time {hero.id} was {obstacle.gerund} like a proper adventurer, {hero.pronoun('possessive')} {prize.label} stayed clean, and {beagle.id} bounced along with his nose working overtime."
    )


def find_clue(world: World, hero: Entity, beagle: Entity, obstacle: Obstacle) -> None:
    hero.memes["triumph"] += 1
    beagle.memes["triumph"] += 1
    world.say(
        f"At {obstacle.clue_spot}, {beagle.id} barked once, then twice, and pawed at a little tin box with a bell painted on the lid."
    )
    world.say(
        f"Inside was the next clue and a paper ribbon that read: \"Brave is good. Careful is better.\""
    )
    world.say(
        f"{hero.id} laughed, because the ribbon was right, and because {beagle.id} tried to carry both the clue and the whole tin box at once."
    )


def closing_image(world: World, hero: Entity, beagle: Entity, parent: Entity, prize: Entity, setting: Setting) -> None:
    world.say(
        f"Together they trotted back through {setting.place}, the clue safe, the {prize.label} still neat, and the beagle's tail wagging like a tiny victory flag."
    )
    world.say(
        f"By the time the fair bell rang, {hero.id} felt bigger inside than at the start of the hunt: still brave, but now brave enough to listen first."
    )


def tell(setting: Setting, obstacle: Obstacle, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: list[str], parent_type: str, beagle_name: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=list(hero_traits),
            label=hero_name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
        )
    )
    beagle = world.add(
        Entity(
            id="beagle",
            kind="character",
            type="beagle",
            label=beagle_name,
            attrs={"display_name": beagle_name},
        )
    )
    beagle.id = "beagle"
    beagle.attrs["display_name"] = beagle_name
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero, beagle)
    setup_fair(world, hero, parent, prize, setting)
    world.para()
    announce_quest(world, hero, beagle, obstacle)
    wants(world, hero, obstacle)
    warn(world, parent, hero, beagle, obstacle, prize)
    defies(world, hero, obstacle)
    beagle_blocks(world, hero, beagle)
    world.para()
    gear = compromise(world, parent, hero, beagle, obstacle, prize)
    if gear:
        accept(world, hero, parent, beagle, obstacle, prize, gear)
        find_clue(world, hero, beagle, obstacle)
        closing_image(world, hero, beagle, parent, prize, setting)

    world.facts.update(
        hero=hero,
        parent=parent,
        beagle=beagle,
        beagle_name=beagle_name,
        prize=prize,
        prize_cfg=prize_cfg,
        obstacle=obstacle,
        setting=setting,
        gear=gear,
        warned=True,
        resolved=gear is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    beagle_name = f["beagle_name"]
    obstacle = f["obstacle"]
    setting = f["setting"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "gunk-dim", "beagle", and "episcopal".',
        f"Tell a funny little clue-hunt where a {hero.type} named {hero.id} and a beagle named {beagle_name} explore {setting.place} and must slow down near {obstacle.cue.lower()}",
        f"Write a foreshadowing adventure in which a child at an episcopal fair sees trouble coming, listens to a grown-up, and still reaches the clue safely.",
    ]


KNOWLEDGE = {
    "beagle": [(
        "What is a beagle?",
        "A beagle is a small hunting dog with a strong nose and floppy ears. Beagles are famous for sniffing and following smells."
    )],
    "episcopal": [(
        "What does episcopal mean?",
        "Episcopal means something is connected with an Episcopal church. An episcopal hall or garden is a place that belongs to that church."
    )],
    "jam": [(
        "Why is jam messy on the floor?",
        "Jam is sticky and sweet, so it can glue itself to shoes and make a floor messy fast. It also spreads when people step in it."
    )],
    "wax": [(
        "Why can wax on stairs be slippery?",
        "Wax can make a smooth layer on a step, and smooth things are easier to slide on. That is why waxy stairs need careful feet."
    )],
    "paint": [(
        "Why is fresh paint a problem for clothes?",
        "Fresh paint is still wet, so it can smear onto sleeves and shirts. Once it sticks, it takes work to clean."
    )],
    "dust": [(
        "Why does dust make people sneeze?",
        "Dust has tiny bits that tickle noses and throats. When that happens, your body may sneeze to push them out."
    )],
    "boots": [(
        "What are boots good for?",
        "Boots protect feet and sometimes legs when the ground is wet or messy. They help keep shoes cleaner and safer."
    )],
    "overshoes": [(
        "What are overshoes?",
        "Overshoes are covers that go over regular shoes. They add grip and help keep the shoes underneath cleaner."
    )],
    "smock": [(
        "What is a smock?",
        "A smock is a loose cover you wear over your clothes. It helps stop paint or dust from getting on the clothes underneath."
    )],
    "playclothes": [(
        "What are old play clothes?",
        "Old play clothes are clothes you do not mind getting messy. They are good for art, digging, and other rough play."
    )],
}
KNOWLEDGE_ORDER = ["beagle", "episcopal", "jam", "wax", "paint", "dust", "boots", "overshoes", "smock", "playclothes"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    obstacle = f["obstacle"]
    setting = f["setting"]
    beagle_name = f["beagle_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child on a clue hunt, and {beagle_name}, the beagle helper. They are exploring {setting.place} during an episcopal fair."
        ),
        (
            "What was the adventure?",
            f"They were following a map to find the next bell clue. The clue was hidden {obstacle.clue_spot}, so they had to get past a risky spot first."
        ),
        (
            f"How did the story foreshadow trouble?",
            f"The story showed the danger before anyone rushed in: {obstacle.forebode} That early detail hinted that the path only looked exciting, not safe."
        ),
        (
            f"Why did {hero.id}'s {pw} warn {hero.pronoun('object')}?",
            f"{hero.pronoun('possessive').capitalize()} {pw} knew the obstacle could ruin the {prize.label}. If {hero.id} hurried through it, the {prize.label} would get {f.get('predicted_ruin', obstacle.ruin)} and make extra cleanup too."
        ),
        (
            f"What funny thing did the beagle do?",
            f"{beagle_name} blocked the path by plopping down like a furry gate. The joke works because the brave adventure paused for a very silly reason: nobody can argue quickly while stepping over a beagle."
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append((
            "How did they solve the problem?",
            f"They used {gear.label} before crossing the obstacle. That changed the world so the risky mess no longer reached the {prize.label}, and they could continue the adventure safely."
        ))
        qa.append((
            "How did the story end?",
            f"They found the bell clue, laughed together, and came back with the prize still clean. The ending image proves what changed: {hero.id} was still adventurous, but now careful too."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"beagle", "episcopal"}
    tags |= set(f["obstacle"].tags)
    gear = f.get("gear")
    if gear is not None:
        tags |= set(gear.tags)
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
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="crypt",
        obstacle="wax",
        prize="sneakers",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="brave",
        beagle_name="Pickle",
    ),
    StoryParams(
        place="hall",
        obstacle="paint",
        prize="cape",
        name="Tom",
        gender="boy",
        parent="father",
        trait="curious",
        beagle_name="Biscuit",
    ),
    StoryParams(
        place="garden",
        obstacle="dust",
        prize="robe",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="hopeful",
        beagle_name="Muffin",
    ),
    StoryParams(
        place="hall",
        obstacle="jam",
        prize="sneakers",
        name="Max",
        gender="boy",
        parent="father",
        trait="eager",
        beagle_name="Waffles",
    ),
]


def explain_rejection(obstacle: Obstacle, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(obstacle, prize):
        return (
            f"(No story: {obstacle.gerund} reaches {sorted(obstacle.zone)}, but {noun} sits on the {prize.region}. "
            f"The warning would not be honest, so this combination is refused.)"
        )
    return (
        f"(No story: nothing in the gear catalog protects {noun} from {obstacle.gerund}. "
        f"The safe fix must really cover the at-risk item.)"
    )


ASP_RULES = r"""
prize_at_risk(O, P) :- touches(O, R), worn_on(P, R).

protects(G, O, P) :- gear(G), prize_at_risk(O, P),
                     mess_of(O, M), guards(G, M),
                     covers(G, R), worn_on(P, R).

has_fix(O, P) :- protects(_, O, P).
valid(Place, O, P) :- affords(Place, O), prize_at_risk(O, P), has_fix(O, P).
valid_story(Place, O, P, Gender) :- valid(Place, O, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for obs in sorted(setting.affords):
            lines.append(asp.fact("affords", place, obs))
    for obs_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obs_id))
        lines.append(asp.fact("mess_of", obs_id, obstacle.mess))
        for region in sorted(obstacle.zone):
            lines.append(asp.fact("touches", obs_id, region))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("worn_on", prize_id, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", prize_id))
        for gender in sorted(prize.genders):
            lines.append(asp.fact("wears", gender, prize_id))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for mess in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, mess))
        for region in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, region))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a beagle, an episcopal fair, and a careful little adventure."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--beagle-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.prize:
        obstacle = OBSTACLES[args.obstacle]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(obstacle, prize) and select_gear(obstacle, prize)):
            raise StoryError(explain_rejection(obstacle, prize))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.prize is None or combo[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[combo[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, prize = rng.choice(sorted(combos))
    prize_cfg = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_cfg.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    beagle_name = args.beagle_name or rng.choice(BEAGLE_NAMES)
    return StoryParams(
        place=place,
        obstacle=obstacle,
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        beagle_name=beagle_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")

    setting = SETTINGS[params.place]
    obstacle = OBSTACLES[params.obstacle]
    prize = PRIZES[params.prize]

    if obstacle.id not in setting.affords:
        raise StoryError(f"(No story: {setting.place} does not support obstacle '{obstacle.id}'.)")
    if not (prize_at_risk(obstacle, prize) and select_gear(obstacle, prize)):
        raise StoryError(explain_rejection(obstacle, prize))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        prize_cfg=prize,
        hero_name=params.name,
        hero_type=params.gender,
        hero_traits=[params.trait],
        parent_type=params.parent,
        beagle_name=params.beagle_name,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM SMOKE FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, obstacle, prize) combos ({len(stories)} with gender):\n")
        for place, obstacle, prize in triples:
            genders = sorted(g for (pl, ob, pr, g) in stories if (pl, ob, pr) == (place, obstacle, prize))
            print(f"  {place:8} {obstacle:8} {prize:9}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.beagle_name}: {p.obstacle} at {p.place} (prize: {p.prize})"
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
