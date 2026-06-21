#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py
======================================================================

A standalone storyworld for a tall-tale misunderstanding: a child hears the word
"bulldoze," thinks it means charging into a problem while wearing a big coat,
and learns that words matter as much as muscle.

Run it
------
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --obstacle snowdrift
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --method rake_wagon
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/bulldoze_coat_misunderstanding_tall_tale.py --verify
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
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "sensible", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    need: str
    cheer: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Obstacle:
    id: str
    label: str
    the: str
    material: str
    soft: bool
    wet: bool
    height: int
    image: str
    crumble: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class CoatCfg:
    id: str
    label: str
    phrase: str
    swish: str
    keeps_out: str
    gets_messy: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Method:
    id: str
    label: str
    handles: set[str]
    strong: int
    arrival: str
    clear_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    destination: str
    obstacle: str
    coat: str
    method: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    grownup: str
    trait: str
    relation: str = "friends"
    hero_age: int = 5
    friend_age: int = 5
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_blocked(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    road = world.get("road")
    sig = ("blocked",)
    if obstacle.meters["blocking"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        road.meters["blocked"] = 1.0
    return []


def _r_charge_soft(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    coat = world.get("coat")
    if hero.meters["charged"] < THRESHOLD or not obstacle.attrs.get("soft"):
        return []
    sig = ("charge_soft",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    coat.meters["messy"] += 1
    hero.meters["stuck"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["surprise"] += 1
    obstacle.meters["blocking"] = max(obstacle.meters["blocking"] - 0.2, 1.0)
    return []


def _r_charge_hard(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if hero.meters["charged"] < THRESHOLD or obstacle.attrs.get("soft"):
        return []
    sig = ("charge_hard",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["bounced"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["surprise"] += 1
    return []


def _r_mess_wet(world: World) -> list[str]:
    coat = world.get("coat")
    obstacle = world.get("obstacle")
    sig = ("wet_mess",)
    if coat.meters["messy"] >= THRESHOLD and obstacle.attrs.get("wet") and sig not in world.fired:
        world.fired.add(sig)
        coat.meters["heavy"] += 1
        hero = world.get("hero")
        hero.memes["cold"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked", tag="physical", apply=_r_blocked),
    Rule(name="charge_soft", tag="physical", apply=_r_charge_soft),
    Rule(name="charge_hard", tag="physical", apply=_r_charge_hard),
    Rule(name="mess_wet", tag="physical", apply=_r_mess_wet),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_correct(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    older = friend_age > hero_age and relation in {"siblings", "cousins"}
    authority = initial_care(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BOLDNESS_INIT


def method_works(obstacle: Obstacle, method: Method) -> bool:
    return obstacle.material in method.handles and method.strong >= obstacle.height


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dest_id in DESTINATIONS:
        for obs_id, obs in OBSTACLES.items():
            for method_id, method in METHODS.items():
                if method_works(obs, method):
                    combos.append((dest_id, obs_id, method_id))
    return combos


def explain_rejection(obstacle: Obstacle, method: Method) -> str:
    mats = ", ".join(sorted(method.handles))
    return (
        f"(No story: {method.label} is meant for {mats}, not for {obstacle.the}. "
        f"A good story here needs a fix that could really clear the road.)"
    )


def predict_charge(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    _attempt_charge(sim, hero, narrate=False)
    return {
        "road_clear": sim.get("road").meters["blocked"] < THRESHOLD,
        "coat_messy": sim.get("coat").meters["messy"] >= THRESHOLD,
        "hero_stuck": sim.get("hero").meters["stuck"] >= THRESHOLD,
        "hero_bounced": sim.get("hero").meters["bounced"] >= THRESHOLD,
    }


def _attempt_charge(world: World, hero: Entity, narrate: bool = True) -> None:
    hero.meters["charged"] += 1
    propagate(world, narrate=False)
    if not narrate:
        return
    obstacle = world.get("obstacle")
    coat = world.get("coat")
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} shoulders, took three mighty stomps, "
            f"and dove into {obstacle.the}. {coat.phrase.capitalize()} vanished up to the buttons."
        )
    elif hero.meters["bounced"] >= THRESHOLD:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} shoulders, took three mighty stomps, "
            f"and bumped {obstacle.the} so hard that the whole town could hear the thump."
        )


def introduce(world: World, hero: Entity, friend: Entity, destination: Destination, obstacle: Obstacle) -> None:
    world.say(
        f"In a town where the wind bragged louder than a brass band, {hero.id} and {friend.id} "
        f"stared down {obstacle.the}, {obstacle.image}."
    )
    world.say(
        f"It had parked itself right across the road to the {destination.label}, "
        f"and nobody in town could {destination.need} until the way was clear."
    )


def coat_setup(world: World, hero: Entity, coat: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wore {coat.phrase}, and when {hero.pronoun()} twirled, it {coat.attrs['swish']}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} coat was splendid for keeping out {coat.attrs['keeps_out']}, "
        f"which made {hero.id} feel almost as large as a courthouse."
    )


def call_for_fix(world: World, grownup: Entity, method: Method) -> None:
    world.say(
        f'Town folks were muttering like kettles when {grownup.label_word.capitalize()} Boone cupped '
        f'{grownup.pronoun("possessive")} hands and called, "Stand back now. We will bulldoze this road '
        f'clear with {method.label}!"'
    )


def misunderstand(world: World, hero: Entity, coat: Entity) -> None:
    hero.memes["confusion"] += 1
    hero.memes["boldness"] += 1
    world.say(
        f"{hero.id} blinked once, then grinned so wide it looked as if sunrise had happened twice."
    )
    world.say(
        f'"Bulldoze?" {hero.pronoun().capitalize()} whispered. "That must mean you put on your biggest coat, '
        f'lean down like a bull, and shove."'
    )


def warn(world: World, friend: Entity, hero: Entity, obstacle: Obstacle, coat: Entity) -> None:
    pred = predict_charge(world)
    world.facts["predicted_coat_messy"] = pred["coat_messy"]
    world.facts["predicted_stuck"] = pred["hero_stuck"]
    world.facts["predicted_bounced"] = pred["hero_bounced"]
    friend.memes["care"] += 1
    second = ""
    if pred["hero_stuck"]:
        second = f" You would just disappear into {obstacle.the} and come back wearing half of it."
    elif pred["hero_bounced"]:
        second = f" You would bounce off it, and that fine {coat.label} would not help one bit."
    else:
        second = " Your coat is for warmth, not for road work."
    world.say(
        f'{friend.id} grabbed {hero.pronoun("possessive")} sleeve. "I do not think that is what bulldoze means."'
        f"{second}"
    )


def back_down(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["boldness"] = 0.0
    world.say(
        f"{hero.id} puffed up for one brave second, then looked at {friend.id} and let the air out slowly."
    )
    world.say(
        f'"Maybe a coat can be mighty without being a machine," {hero.pronoun()} admitted.'
    )


def charge_anyway(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"No time for long words!" cried {hero.id}. "I am already wearing the right coat."'
    )
    _attempt_charge(world, hero, narrate=True)


def aftermath(world: World, hero: Entity, obstacle: Obstacle, coat: Entity) -> None:
    if hero.meters["stuck"] >= THRESHOLD:
        extra = f"{hero.id} came up blinking, with {obstacle.crumble} hanging from {coat.label}."
    else:
        extra = f"{hero.id} stepped back rubbing {hero.pronoun('possessive')} knees, while {obstacle.the} did not move enough to bother a beetle."
    world.say(
        f"{obstacle.The} stayed where it was, broad as ever. {extra}"
    )
    if coat.meters["heavy"] >= THRESHOLD:
        world.say(
            f"The coat grew so heavy with {coat.attrs['gets_messy']} that it seemed to weigh nearly as much as a piano."
        )


def explain(world: World, grownup: Entity, hero: Entity, method: Method) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} Boone knelt beside {hero.id} and brushed off the biggest clumps. '
        f'"Bulldoze does not mean using your shoulders," {grownup.pronoun()} said kindly.'
    )
    world.say(
        f'"It means clearing a stubborn thing with the proper power. Coats keep children warm. '
        f'{method.label.capitalize()} clears roads."'
    )


def true_fix(world: World, grownup: Entity, method: Method, obstacle: Obstacle, destination: Destination) -> None:
    obstacle_ent = world.get("obstacle")
    road = world.get("road")
    obstacle_ent.meters["blocking"] = 0.0
    road.meters["blocked"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} Boone {method.arrival}."
    )
    world.say(
        f"In one rumbling, rattling, marvelous pass, {method.clear_text.format(obstacle=obstacle.the)}."
    )
    world.say(
        f"Soon the road lay open again, and the whole town gave {destination.cheer}."
    )


def better_help(world: World, hero: Entity, friend: Entity, destination: Destination) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["pride"] = 0.0
    world.say(
        f"{hero.id} tugged {hero.pronoun('possessive')} coat straight and took hold of the little flag line with {friend.id}."
    )
    world.say(
        f"This time {hero.pronoun()} did not try to be the bulldozer. "
        f"{hero.pronoun().capitalize()} helped in the true-size way a child can help: standing back, staying warm, "
        f"and cheering until the windows shook."
    )
    world.say(
        destination.ending
    )


def tell(
    destination: Destination,
    obstacle_cfg: Obstacle,
    coat_cfg: CoatCfg,
    method: Method,
    hero_name: str = "Bea",
    hero_gender: str = "girl",
    friend_name: str = "Otis",
    friend_gender: str = "boy",
    grownup_type: str = "father",
    trait: str = "careful",
    relation: str = "friends",
    hero_age: int = 5,
    friend_age: int = 6,
) -> World:
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["bold"],
        age=hero_age,
        attrs={"name": hero_name, "relation": relation},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[trait],
        age=friend_age,
        attrs={"name": friend_name, "relation": relation},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the foreman",
        role="grownup",
        attrs={"name": f"{grownup_type.title()} Boone"},
    ))
    coat = world.add(Entity(
        id="coat",
        kind="thing",
        type="coat",
        label=coat_cfg.label,
        phrase=coat_cfg.phrase,
        role="coat",
        attrs={
            "swish": coat_cfg.swish,
            "keeps_out": coat_cfg.keeps_out,
            "gets_messy": coat_cfg.gets_messy,
        },
        tags=set(coat_cfg.tags),
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle_cfg.label,
        phrase=obstacle_cfg.the,
        role="obstacle",
        attrs={
            "soft": obstacle_cfg.soft,
            "wet": obstacle_cfg.wet,
            "material": obstacle_cfg.material,
        },
        tags=set(obstacle_cfg.tags),
    ))
    road = world.add(Entity(
        id="road",
        kind="thing",
        type="road",
        label="road",
        role="road",
    ))

    obstacle.meters["blocking"] = 1.0
    hero.memes["boldness"] = BOLDNESS_INIT
    friend.memes["care"] = initial_care(trait)
    coat.meters["messy"] = 0.0
    coat.meters["heavy"] = 0.0
    hero.meters["charged"] = 0.0
    hero.meters["stuck"] = 0.0
    hero.meters["bounced"] = 0.0
    propagate(world, narrate=False)

    introduce(world, hero, friend, destination, obstacle_cfg)
    coat_setup(world, hero, coat)
    world.para()
    call_for_fix(world, grownup, method)
    misunderstand(world, hero, coat)
    warn(world, friend, hero, obstacle_cfg, coat)

    corrected = would_correct(relation, hero_age, friend_age, trait)
    if corrected:
        back_down(world, hero, friend)
    else:
        world.para()
        charge_anyway(world, hero)
        aftermath(world, hero, obstacle_cfg, coat)
        world.para()
        explain(world, grownup, hero, method)

    world.para()
    true_fix(world, grownup, method, obstacle_cfg, destination)
    better_help(world, hero, friend, destination)

    outcome = "corrected" if corrected else "charged"
    world.facts.update(
        destination=destination,
        obstacle_cfg=obstacle_cfg,
        coat_cfg=coat_cfg,
        method=method,
        hero=hero,
        friend=friend,
        grownup=grownup,
        coat=coat,
        obstacle=obstacle,
        relation=relation,
        outcome=outcome,
        corrected=corrected,
        charged=hero.meters["charged"] >= THRESHOLD,
        coat_messy=coat.meters["messy"] >= THRESHOLD,
        coat_heavy=coat.meters["heavy"] >= THRESHOLD,
        road_open=road.meters["blocked"] < THRESHOLD,
    )
    return world


DESTINATIONS = {
    "schoolhouse": Destination(
        id="schoolhouse",
        label="schoolhouse",
        need="ring the bell for lessons",
        cheer="three cheers for arithmetic and soup",
        ending="By noon they were marching to the schoolhouse, and the bell sounded so happy it seemed to skip.",
        tags={"school"},
    ),
    "bakery": Destination(
        id="bakery",
        label="bakery",
        need="fetch the cinnamon buns before they turned shy",
        cheer="a cheer that smelled nearly of warm bread",
        ending="By noon they were strolling to the bakery, and sweet steam curled out the door like a friendly wave.",
        tags={"bakery"},
    ),
    "fairground": Destination(
        id="fairground",
        label="fairground",
        need="open the gates for the fiddlers and pie judges",
        cheer="a cheer big enough to rattle the bunting",
        ending="By noon they were skipping to the fairground, where the bunting snapped and the fiddles tuned up at once.",
        tags={"fair"},
    ),
}

OBSTACLES = {
    "snowdrift": Obstacle(
        id="snowdrift",
        label="snowdrift",
        the="the snowdrift",
        material="snow",
        soft=True,
        wet=True,
        height=2,
        image="as tall as two milk wagons stacked one on the other",
        crumble="snowy crumbs",
        tags={"snow", "weather"},
    ),
    "leaf_hill": Obstacle(
        id="leaf_hill",
        label="leaf hill",
        the="the leaf hill",
        material="leaves",
        soft=True,
        wet=False,
        height=1,
        image="so wide and rustly it looked like autumn had fallen asleep in the road",
        crumble="leaf bits",
        tags={"leaves"},
    ),
    "rock_heap": Obstacle(
        id="rock_heap",
        label="rock heap",
        the="the rock heap",
        material="rock",
        soft=False,
        wet=False,
        height=3,
        image="like a lumpy gray mountain that had decided to sit down for a rest",
        crumble="dusty pebbles",
        tags={"rocks"},
    ),
    "mud_bank": Obstacle(
        id="mud_bank",
        label="mud bank",
        the="the mud bank",
        material="mud",
        soft=True,
        wet=True,
        height=2,
        image="as slumpy as pudding and nearly as wide as Main Street itself",
        crumble="muddy ribbons",
        tags={"mud"},
    ),
}

COATS = {
    "red_wool": CoatCfg(
        id="red_wool",
        label="red wool coat",
        phrase="a red wool coat with brass buttons",
        swish="flapped like a parade flag",
        keeps_out="wind and bragging weather",
        gets_messy="wet clumps",
        tags={"coat", "winter"},
    ),
    "yellow_rain": CoatCfg(
        id="yellow_rain",
        label="yellow raincoat",
        phrase="a yellow raincoat shiny as a buttercup",
        swish="shone and crackled like a little sun",
        keeps_out="rain and drips",
        gets_messy="slick mud",
        tags={"coat", "raincoat"},
    ),
    "blue_duster": CoatCfg(
        id="blue_duster",
        label="blue duster coat",
        phrase="a blue duster coat with a collar big enough for boasting",
        swish="streamed out behind like a banner",
        keeps_out="dust and chilly gusts",
        gets_messy="dusty clods",
        tags={"coat"},
    ),
}

METHODS = {
    "yellow_dozer": Method(
        id="yellow_dozer",
        label="a yellow bulldozer",
        handles={"snow", "mud", "rock"},
        strong=3,
        arrival="rolled up in a cloud of honest engine noise",
        clear_text="{obstacle} folded aside in great sliding waves",
        qa_text="A yellow bulldozer pushed the obstacle aside and opened the road",
        tags={"bulldozer", "machine"},
    ),
    "shovel_line": Method(
        id="shovel_line",
        label="a long shovel line",
        handles={"snow", "mud", "leaves"},
        strong=2,
        arrival="lined up the townsfolk shoulder to shoulder with shovels shining",
        clear_text="{obstacle} shrank and shrank until only a neat edge remained",
        qa_text="The townsfolk used a long shovel line to clear the obstacle",
        tags={"shovel"},
    ),
    "rake_wagon": Method(
        id="rake_wagon",
        label="the town rake wagon",
        handles={"leaves"},
        strong=1,
        arrival="clattered in with rakes wagging at the sky",
        clear_text="{obstacle} whisked away in rustling armfuls",
        qa_text="The town rake wagon swept the leaves away from the road",
        tags={"rake"},
    ),
}

GIRL_NAMES = ["Bea", "Mabel", "June", "Tess", "Elsie", "Nell", "Ada", "Pearl"]
BOY_NAMES = ["Otis", "Jeb", "Cal", "Rufus", "Eli", "Hank", "Milo", "Wade"]
TRAITS = ["careful", "sensible", "steady", "thoughtful", "curious", "cheery"]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    if relation == "cousins":
        return "two cousins"
    return "two friends"


def format_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    destination = f["destination"]
    obstacle = f["obstacle_cfg"]
    coat = f["coat_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    if outcome == "corrected":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the words "bulldoze" and "coat", where a child misunderstands what bulldoze means and is gently corrected before charging into {obstacle.the}.',
            f"Tell a playful misunderstanding story where {format_name(hero)} thinks {coat.label} can bulldoze a road, but {format_name(friend)} explains the word before a mistake happens, and the town still reaches the {destination.label}.",
            f"Write a child-facing tall tale about a giant roadblock, a grand misunderstanding, and a warm coat that turns out to be for wearing, not for clearing roads.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "bulldoze" and "coat", where a child misunderstands the word bulldoze and tries the wrong thing first.',
        f"Tell a big, funny frontier-style story where {format_name(hero)} hears a grown-up say they will bulldoze {obstacle.the}, mistakes the meaning, and learns the truth after making a mess of {coat.label}.",
        f"Write a misunderstanding story with a giant obstacle, a brave but mistaken child, and a happy ending in which {method.label} truly clears the road to the {destination.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    grownup = f["grownup"]
    destination = f["destination"]
    obstacle = f["obstacle_cfg"]
    coat = f["coat_cfg"]
    method = f["method"]
    pair = pair_noun(hero, friend, f["relation"])
    hero_name = format_name(hero)
    friend_name = format_name(friend)
    grownup_word = grownup.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero_name} and {friend_name}, in a town with a road blocked by {obstacle.the}. It is also about {grownup_word} Boone, who knows how to clear the way properly.",
        ),
        (
            f"Why was everyone worried about {obstacle.the}?",
            f"{obstacle.The} was blocking the road to the {destination.label}, so the town could not {destination.need}. Until the road opened, the whole day had to wait behind the pile.",
        ),
        (
            f"What misunderstanding did {hero_name} have?",
            f"{hero_name} heard the word bulldoze and thought it meant lowering {hero.pronoun('possessive')} shoulders, wearing a big coat, and shoving like a bull. The misunderstanding came from guessing at a big word instead of knowing what the grown-up meant.",
        ),
    ]
    if f["outcome"] == "corrected":
        qa.append(
            (
                f"How did {friend_name} help before anything went wrong?",
                f"{friend_name} warned that a coat is for warmth, not for clearing roads. Because {friend_name} spoke up in time, {hero_name} stopped and listened before diving into {obstacle.the}.",
            )
        )
    else:
        coat_result = "got messy" if f["coat_messy"] else "did not help at all"
        second = "The road stayed blocked because shoulders and cloth were never the right tools for that job."
        if f["coat_heavy"]:
            second = "The road stayed blocked, and the wet mess made the coat heavy too."
        qa.append(
            (
                f"What happened when {hero_name} tried to bulldoze the road with {hero.pronoun('possessive')} coat?",
                f"{hero_name} charged at {obstacle.the}, but {hero.pronoun('possessive')} {coat.label} {coat_result}. {second}",
            )
        )
        qa.append(
            (
                f"What did {grownup_word} Boone explain?",
                f"{grownup_word.capitalize()} Boone explained that bulldoze means clearing a stubborn thing with proper power, not with a child's shoulders. {hero_name} learned that the coat's job was to keep {hero.pronoun('object')} warm while the real fix went to work.",
            )
        )
    qa.append(
        (
            f"How was the road finally cleared?",
            f"{method.qa_text}. That true fix opened the road so the town could reach the {destination.label} after all.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the road open and the town moving again. {hero_name} kept the coat on for warmth and helped in a sensible way instead of trying to be the bulldozer.",
        )
    )
    return qa


KNOWLEDGE = {
    "bulldozer": [
        (
            "What is a bulldozer?",
            "A bulldozer is a big machine that pushes dirt, snow, or other heavy things out of the way. It is made for strong clearing jobs.",
        )
    ],
    "machine": [
        (
            "Why do people use machines for very heavy jobs?",
            "Machines can push and lift much more than a person can. They help when a job is too big for hands and shoulders alone.",
        )
    ],
    "coat": [
        (
            "What is a coat for?",
            "A coat helps keep your body warm and dry in cold or wet weather. It is clothing, not a tool for moving huge piles.",
        )
    ],
    "snow": [
        (
            "What is a snowdrift?",
            "A snowdrift is a big pile of snow made when wind blows snow into one place. It can grow tall enough to block a path.",
        )
    ],
    "mud": [
        (
            "Why is mud hard to move?",
            "Mud is heavy, sticky, and slippery all at once. That makes it hard for small children to push or carry safely.",
        )
    ],
    "leaves": [
        (
            "Why can a big leaf pile block a road?",
            "One leaf is light, but many leaves together can make a deep mound. A huge pile can cover the road until people rake it away.",
        )
    ],
    "rocks": [
        (
            "Why are rocks harder to clear than leaves?",
            "Rocks are much heavier and do not crumble or blow away easily. That is why big rock piles need strong tools or machines.",
        )
    ],
    "shovel": [
        (
            "What is a shovel used for?",
            "A shovel is used for scooping and moving loose things like snow, dirt, or mud. Many people with shovels can clear a path together.",
        )
    ],
    "rake": [
        (
            "What does a rake do?",
            "A rake gathers light things, like leaves, into neat piles. It is good for sweeping and pulling, not for pushing rocks.",
        )
    ],
}
KNOWLEDGE_ORDER = ["coat", "bulldozer", "machine", "snow", "mud", "leaves", "rocks", "shovel", "rake"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"coat"} | set(f["obstacle_cfg"].tags) | set(f["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid method/obstacle pairing
works(O, M) :- obstacle(O), method(M), material(O, Mat), handles(M, Mat), height(O, H), strength(M, S), S >= H.
valid(D, O, M) :- destination(D), works(O, M).

% correction vs charge
care_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), care_now(T).
init_care(3) :- trait(T), not care_now(T).
older_helper :- relation(siblings), hero_age(HA), friend_age(FA), FA > HA.
older_helper :- relation(cousins), hero_age(HA), friend_age(FA), FA > HA.
bonus(3) :- older_helper.
bonus(0) :- not older_helper.
authority(C + 1 + B) :- init_care(C), bonus(B).
corrected :- older_helper, authority(A), boldness_init(B), A > B.
outcome(corrected) :- corrected.
outcome(charged) :- not corrected.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dest_id in DESTINATIONS:
        lines.append(asp.fact("destination", dest_id))
    for obs_id, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obs_id))
        lines.append(asp.fact("material", obs_id, obs.material))
        lines.append(asp.fact("height", obs_id, obs.height))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("strength", method_id, method.strong))
        for mat in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, mat))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "corrected" if would_correct(params.relation, params.hero_age, params.friend_age, params.trait) else "charged"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale misunderstanding storyworld: a child thinks a coat can bulldoze a road."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--coat", choices=COATS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_works(obstacle, method):
            raise StoryError(explain_rejection(obstacle, method))

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, obstacle, method = rng.choice(sorted(combos))
    coat = args.coat or rng.choice(sorted(COATS))
    hero, hero_gender = _pick_kid(rng)
    friend, friend_gender = _pick_kid(rng, avoid=hero)
    grownup = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings", "cousins"])
    hero_age, friend_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        destination=destination,
        obstacle=obstacle,
        coat=coat,
        method=method,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        grownup=grownup,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in [
        (params.destination, DESTINATIONS),
        (params.obstacle, OBSTACLES),
        (params.coat, COATS),
        (params.method, METHODS),
    ]:
        if key not in registry:
            raise StoryError("(No story: one of the requested options is unknown.)")
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not method_works(obstacle, method):
        raise StoryError(explain_rejection(obstacle, method))

    world = tell(
        destination=DESTINATIONS[params.destination],
        obstacle_cfg=obstacle,
        coat_cfg=COATS[params.coat],
        method=method,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
    )

    story = world.render()
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    story = story.replace("hero", format_name(hero)).replace("friend", format_name(friend))

    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(
        destination="schoolhouse",
        obstacle="snowdrift",
        coat="red_wool",
        method="shovel_line",
        hero="Bea",
        hero_gender="girl",
        friend="Otis",
        friend_gender="boy",
        grownup="father",
        trait="careful",
        relation="cousins",
        hero_age=4,
        friend_age=7,
    ),
    StoryParams(
        destination="bakery",
        obstacle="mud_bank",
        coat="yellow_rain",
        method="yellow_dozer",
        hero="Mabel",
        hero_gender="girl",
        friend="Cal",
        friend_gender="boy",
        grownup="aunt",
        trait="curious",
        relation="friends",
        hero_age=6,
        friend_age=5,
    ),
    StoryParams(
        destination="fairground",
        obstacle="leaf_hill",
        coat="blue_duster",
        method="rake_wagon",
        hero="Jeb",
        hero_gender="boy",
        friend="June",
        friend_gender="girl",
        grownup="uncle",
        trait="steady",
        relation="siblings",
        hero_age=5,
        friend_age=8,
    ),
    StoryParams(
        destination="schoolhouse",
        obstacle="rock_heap",
        coat="red_wool",
        method="yellow_dozer",
        hero="Rufus",
        hero_gender="boy",
        friend="Ada",
        friend_gender="girl",
        grownup="mother",
        trait="cheery",
        relation="friends",
        hero_age=7,
        friend_age=5,
    ),
]


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (destination, obstacle, method) combos:\n")
        for destination, obstacle, method in combos:
            print(f"  {destination:11} {obstacle:10} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.obstacle} -> {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
