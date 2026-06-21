#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py
==============================================================

A standalone story world about a child on a small adventure who carries a
careful supply bag, meets someone in need, and discovers that kindness can turn
a trip into a better adventure.

The core constraint of this domain is simple and explicit: the offered supply
must actually match the need. A water flask helps thirst, a bandage helps a
scrape, apple slices help hunger, and a spare scarf helps cold. The world knows
about mismatched choices but refuses to tell them as stories, because a
storybook act of kindness should solve a real problem, not merely gesture at one.

Run it
------
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py --setting forest --recipient hiker --need scraped --supply bandage
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py --recipient rabbit --need hungry --supply water
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py --all
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/active_supply_kindness_adventure.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        neutral_person = {"child", "hiker", "ranger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_person:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    trail: str
    landmark: str
    weather: str
    affords: set[str] = field(default_factory=set)
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
class Recipient:
    id: str
    label: str
    type: str
    intro: str
    movement: str
    tags: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
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
class Need:
    id: str
    label: str
    meter: str
    sign: str
    plea: str
    after: str
    severity_word: str
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
class Supply:
    id: str
    label: str
    phrase: str
    verb: str
    fixes: str
    after: str
    inventory_word: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_need_blocks(world: World) -> list[str]:
    out: list[str] = []
    recipient = world.get("recipient")
    if recipient.meters["need"] < THRESHOLD:
        return out
    sig = ("need_blocks", recipient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("trail").meters["halted"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("companion").memes["worry"] += 1
    out.append("__need__")
    return out


def _r_match_helps(world: World) -> list[str]:
    out: list[str] = []
    recipient = world.get("recipient")
    bag = world.get("bag")
    chosen_supply = world.facts["chosen_supply"]
    chosen_need = world.facts["chosen_need"]
    if bag.attrs.get("opened") != chosen_supply.id:
        return out
    if recipient.meters["need"] < THRESHOLD:
        return out
    sig = ("match_helps", recipient.id, chosen_supply.id)
    if sig in world.fired:
        return out
    if chosen_supply.fixes != chosen_need.id:
        return out
    world.fired.add(sig)
    recipient.meters["need"] = 0.0
    recipient.meters[chosen_need.meter] = 0.0
    recipient.memes["relief"] += 1
    recipient.memes["trust"] += 1
    world.get("hero").memes["kindness"] += 1
    world.get("hero").memes["pride"] += 1
    world.get("companion").memes["admiration"] += 1
    bag.meters["supplies_shared"] += 1
    world.get("trail").meters["halted"] = 0.0
    out.append("__helped__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="need_blocks", tag="physical", apply=_r_need_blocks),
    Rule(name="match_helps", tag="social", apply=_r_match_helps),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def recipient_supports_need(recipient: Recipient, need: Need) -> bool:
    return need.id in recipient.needs


def supply_matches_need(supply: Supply, need: Need) -> bool:
    return supply.fixes == need.id


def valid_combo(setting_id: str, recipient_id: str, need_id: str, supply_id: str) -> bool:
    if setting_id not in SETTINGS or recipient_id not in RECIPIENTS:
        return False
    if need_id not in NEEDS or supply_id not in SUPPLIES:
        return False
    setting = SETTINGS[setting_id]
    recipient = RECIPIENTS[recipient_id]
    need = NEEDS[need_id]
    supply = SUPPLIES[supply_id]
    return (
        recipient_id in setting.affords
        and recipient_supports_need(recipient, need)
        and supply_matches_need(supply, need)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for recipient_id in sorted(setting.affords):
            recipient = RECIPIENTS[recipient_id]
            for need_id in sorted(recipient.needs):
                need = NEEDS[need_id]
                for supply_id, supply in SUPPLIES.items():
                    if supply_matches_need(supply, need):
                        combos.append((setting_id, recipient_id, need_id, supply_id))
    return sorted(combos)


def predict_help(world: World, supply: Supply) -> dict:
    sim = world.copy()
    sim.get("bag").attrs["opened"] = supply.id
    propagate(sim, narrate=False)
    recipient = sim.get("recipient")
    return {
        "helped": recipient.meters["need"] < THRESHOLD,
        "trail_halted": sim.get("trail").meters["halted"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} was an active little explorer, and {companion.id} liked keeping "
        f"close beside {hero.pronoun('object')} on every small adventure."
    )
    world.say(
        f"That morning they set out along {setting.trail} in {setting.place}, with "
        f"a map tucked under one arm and a supply satchel bumping against {hero.id}'s side."
    )


def pack(world: World, hero: Entity, supply: Supply) -> None:
    bag = world.get("bag")
    bag.attrs["packed"] = supply.id
    hero.memes["eager"] += 1
    world.say(
        f"Inside the satchel was {supply.phrase}. {hero.id} felt proud of carrying "
        f"such a careful supply for the journey."
    )


def set_scene(world: World, setting: Setting) -> None:
    world.say(
        f"The {setting.weather} air made the day feel bright and bold, and ahead of them "
        f"waited {setting.landmark} like a secret at the end of the path."
    )


def discover(world: World, recipient: Entity, need: Need, recipient_cfg: Recipient) -> None:
    recipient.meters["need"] = 1.0
    recipient.meters[need.meter] = 1.0
    recipient.memes["worry"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Halfway there, they found {recipient_cfg.intro}. {need.sign} "
        f"{need.plea}"
    )


def discuss(world: World, hero: Entity, companion: Entity, supply: Supply, need: Need) -> None:
    hero.memes["thoughtful"] += 1
    companion.memes["care"] += 1
    world.say(
        f'{companion.id} squeezed the strap of the satchel. "That is our {supply.inventory_word}," '
        f"{companion.pronoun()} whispered."
    )
    world.say(
        f"{hero.id} looked from the path to the one in trouble and knew the adventure had changed. "
        f"It was not only about reaching the landmark anymore."
    )


def choose_kindness(world: World, hero: Entity, supply: Supply, need: Need) -> None:
    prediction = predict_help(world, supply)
    world.facts["predicted_help"] = prediction["helped"]
    bag = world.get("bag")
    bag.attrs["opened"] = supply.id
    hero.memes["decision"] += 1
    if prediction["helped"]:
        world.say(
            f'"Then this is what the supply is for," {hero.id} said. {hero.pronoun().capitalize()} '
            f"{supply.verb}."
        )
    else:
        world.say(
            f"{hero.id} opened the satchel, but the wrong thing in a bag would not help here."
        )
    propagate(world, narrate=False)


def help_recipient(world: World, hero: Entity, companion: Entity, recipient: Entity,
                   supply: Supply, need: Need, recipient_cfg: Recipient) -> None:
    world.say(
        f"Soon {need.after} {recipient_cfg.after} {supply.after}"
    )
    world.say(
        f"{companion.id} smiled so hard that even the trail seemed friendlier. "
        f"{hero.id} felt warm inside, because kindness had made room for everyone."
    )


def continue_adventure(world: World, hero: Entity, companion: Entity, recipient: Entity,
                       setting: Setting, recipient_cfg: Recipient) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    recipient.memes["joy"] += 1
    world.say(
        f"After that, they went on together past roots and stones until {setting.landmark} came into view."
    )
    if recipient_cfg.type == "hiker":
        world.say(
            f"At the top, {recipient.label} stood tall again and waved at the wide sky. "
            f"The path had started as a game, but it ended as a true adventure shared with a new friend."
        )
    else:
        world.say(
            f"There, {recipient.label} moved with easy little steps again, and {hero.id} and {companion.id} "
            f"looked at each other with bright, brave smiles. They had not only reached the place they wanted; "
            f"they had left the trail kinder than they found it."
        )


def tell(setting: Setting, recipient_cfg: Recipient, need: Need, supply: Supply,
         hero_name: str = "Nia", hero_gender: str = "girl",
         companion_name: str = "Tomas", companion_gender: str = "boy",
         parent_type: str = "mother", trait: str = "brave") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["active", trait],
        attrs={},
        tags={"hero"},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_gender,
        label=companion_name,
        role="companion",
        traits=["kind", "careful"],
        attrs={},
        tags={"companion"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
        tags={"parent"},
    ))
    bag = world.add(Entity(
        id="bag",
        kind="thing",
        type="satchel",
        label="satchel",
        role="gear",
        attrs={"packed": "", "opened": ""},
        tags={"supply_bag"},
    ))
    trail = world.add(Entity(
        id="trail",
        kind="thing",
        type="trail",
        label="trail",
        role="path",
        attrs={},
        tags={"trail"},
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character" if recipient_cfg.type == "hiker" else "thing",
        type=recipient_cfg.type,
        label=recipient_cfg.label,
        role="recipient",
        attrs={},
        tags=set(recipient_cfg.tags),
    ))

    hero.memes["worry"] = 0.0
    companion.memes["worry"] = 0.0
    hero.memes["kindness"] = 0.0
    companion.memes["admiration"] = 0.0
    recipient.memes["relief"] = 0.0
    recipient.meters["need"] = 0.0
    recipient.meters[need.meter] = 0.0
    trail.meters["halted"] = 0.0
    bag.meters["supplies_shared"] = 0.0

    world.facts["chosen_supply"] = supply
    world.facts["chosen_need"] = need
    world.facts["setting_cfg"] = setting
    world.facts["recipient_cfg"] = recipient_cfg
    world.facts["parent"] = parent

    introduce(world, hero, companion, setting)
    pack(world, hero, supply)
    set_scene(world, setting)

    world.para()
    discover(world, recipient, need, recipient_cfg)
    discuss(world, hero, companion, supply, need)
    choose_kindness(world, hero, supply, need)

    world.para()
    if recipient.meters["need"] >= THRESHOLD:
        raise StoryError("(No story: the chosen supply did not solve the need.)")
    help_recipient(world, hero, companion, recipient, supply, need, recipient_cfg)
    continue_adventure(world, hero, companion, recipient, setting, recipient_cfg)

    world.facts.update(
        hero=hero,
        companion=companion,
        recipient=recipient,
        supply=supply,
        need=need,
        helped=recipient.meters["need"] < THRESHOLD,
        path_clear=trail.meters["halted"] < THRESHOLD,
        shared=bag.meters["supplies_shared"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "forest": Setting(
        id="forest",
        place="the pine forest",
        trail="the needle-soft forest trail",
        landmark="a mossy lookout rock",
        weather="cool",
        affords={"hiker", "rabbit", "puppy"},
        tags={"forest", "trail"},
    ),
    "pond": Setting(
        id="pond",
        place="the reed-bright pond",
        trail="the curving pond path",
        landmark="a smooth stone bridge",
        weather="silver-blue",
        affords={"duckling", "puppy"},
        tags={"pond", "trail"},
    ),
    "hill": Setting(
        id="hill",
        place="the windy hill",
        trail="the twisting hill path",
        landmark="a little flag at the top",
        weather="sunny",
        affords={"hiker"},
        tags={"hill", "trail"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the flowered meadow",
        trail="the clover path",
        landmark="a circle of tall stones",
        weather="golden",
        affords={"rabbit", "hiker"},
        tags={"meadow", "trail"},
    ),
}

RECIPIENTS = {
    "hiker": Recipient(
        id="hiker",
        label="the younger hiker",
        type="hiker",
        intro="a younger hiker sitting on a stump with wet eyes",
        movement="walk",
        tags={"hiker", "friend"},
        needs={"scraped", "thirsty", "cold"},
    ),
    "rabbit": Recipient(
        id="rabbit",
        label="the small brown rabbit",
        type="rabbit",
        intro="a small brown rabbit under a fern",
        movement="hop",
        tags={"rabbit", "animal"},
        needs={"hungry"},
    ),
    "duckling": Recipient(
        id="duckling",
        label="the shivery duckling",
        type="duckling",
        intro="a shivery duckling tucked against a stone",
        movement="waddle",
        tags={"duckling", "animal"},
        needs={"cold"},
    ),
    "puppy": Recipient(
        id="puppy",
        label="the panting puppy",
        type="puppy",
        intro="a panting puppy beside the path",
        movement="trot",
        tags={"puppy", "animal"},
        needs={"thirsty"},
    ),
}

NEEDS = {
    "thirsty": Need(
        id="thirsty",
        label="thirsty",
        meter="thirst",
        sign="Its tongue hung out, and it looked too tired to go on.",
        plea="It needed a drink before the trail could feel like fun again.",
        after="the thirst had passed,",
        severity_word="dry",
        tags={"thirst"},
    ),
    "scraped": Need(
        id="scraped",
        label="scraped",
        meter="hurt",
        sign="One knee was red and stinging.",
        plea="Every time they tried to stand, they winced and sat back down.",
        after="the sting had been covered,",
        severity_word="sore",
        tags={"scrape"},
    ),
    "hungry": Need(
        id="hungry",
        label="hungry",
        meter="hunger",
        sign="Its nose twitched at the empty ground.",
        plea="It looked as if it had not found a single nibble all morning.",
        after="the hunger had eased,",
        severity_word="empty",
        tags={"hunger"},
    ),
    "cold": Need(
        id="cold",
        label="cold",
        meter="chill",
        sign="It was trembling in tiny little shivers.",
        plea="The breeze was too sharp for such a small body.",
        after="the shivering had stopped,",
        severity_word="cold",
        tags={"cold"},
    ),
}

SUPPLIES = {
    "water": Supply(
        id="water",
        label="water flask",
        phrase="a cool water flask",
        verb="knelt at once and shared the water flask",
        fixes="thirsty",
        after="and the tired face lifted again.",
        inventory_word="drink supply",
        tags={"water", "supply"},
    ),
    "bandage": Supply(
        id="bandage",
        label="bandage roll",
        phrase="a neat bandage roll",
        verb="set down the map and wrapped the knee with the bandage roll",
        fixes="scraped",
        after="and the brave little traveler could stand without wincing.",
        inventory_word="first-aid supply",
        tags={"bandage", "supply"},
    ),
    "apple": Supply(
        id="apple",
        label="apple slices",
        phrase="a paper packet of apple slices",
        verb="opened the packet and offered the apple slices",
        fixes="hungry",
        after="and the small nose began to twitch in happy little sniffs.",
        inventory_word="food supply",
        tags={"apple", "supply"},
    ),
    "scarf": Supply(
        id="scarf",
        label="spare scarf",
        phrase="a soft spare scarf",
        verb="lifted out the spare scarf and tucked it gently around the shaking body",
        fixes="cold",
        after="and a soft, steady calm came back.",
        inventory_word="warm supply",
        tags={"scarf", "supply"},
    ),
}


GIRL_NAMES = ["Nia", "Ava", "Mira", "Lena", "Zoe", "Ella", "Maya", "Tara"]
BOY_NAMES = ["Tomas", "Finn", "Leo", "Eli", "Noah", "Ben", "Arlo", "Max"]
TRAITS = ["brave", "quick", "cheerful", "steady", "curious"]


@dataclass
class StoryParams:
    setting: str
    recipient: str
    need: str
    supply: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    parent: str
    trait: str
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


KNOWLEDGE = {
    "trail": [
        (
            "What is a trail?",
            "A trail is a path that people follow through a place like a forest or a hill. It helps travelers know where to walk."
        )
    ],
    "water": [
        (
            "Why does water help when someone is thirsty?",
            "Water gives the body the drink it needs. When someone is thirsty, drinking water helps them feel stronger and more comfortable."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a scrape or cut so it stays cleaner and hurts less. It can help someone keep moving carefully."
        )
    ],
    "apple": [
        (
            "Why can food help when someone is hungry?",
            "Food gives the body energy. A small snack can help someone or an animal feel steadier again."
        )
    ],
    "scarf": [
        (
            "How can a scarf help when someone is cold?",
            "A scarf helps hold in warmth. Wrapping something soft around a cold neck or body can make the chill go down."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or share with someone else. It makes hard moments feel smaller because nobody has to face them alone."
        )
    ],
    "hiker": [
        (
            "What is a hiker?",
            "A hiker is someone who walks along trails for a trip or an adventure. Hikers often carry water and other useful things with them."
        )
    ],
    "rabbit": [
        (
            "What does a rabbit eat?",
            "Rabbits eat plant food, like grass and some vegetables or fruit. They use their noses and whiskers to search for safe nibbles."
        )
    ],
    "duckling": [
        (
            "What is a duckling?",
            "A duckling is a baby duck. Because it is small, it can get cold more quickly than a grown duck."
        )
    ],
    "puppy": [
        (
            "Why does a puppy need water on a warm walk?",
            "A puppy can get thirsty and tired when it trots around. Water helps it cool down and feel better."
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "trail", "water", "bandage", "apple", "scarf", "hiker", "rabbit", "duckling", "puppy"]


CURATED = [
    StoryParams(
        setting="forest",
        recipient="hiker",
        need="scraped",
        supply="bandage",
        hero="Nia",
        hero_gender="girl",
        companion="Tomas",
        companion_gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        setting="pond",
        recipient="duckling",
        need="cold",
        supply="scarf",
        hero="Mira",
        hero_gender="girl",
        companion="Finn",
        companion_gender="boy",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        setting="meadow",
        recipient="rabbit",
        need="hungry",
        supply="apple",
        hero="Leo",
        hero_gender="boy",
        companion="Ava",
        companion_gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="hill",
        recipient="hiker",
        need="thirsty",
        supply="water",
        hero="Eli",
        hero_gender="boy",
        companion="Maya",
        companion_gender="girl",
        parent="father",
        trait="quick",
    ),
    StoryParams(
        setting="pond",
        recipient="puppy",
        need="thirsty",
        supply="water",
        hero="Zoe",
        hero_gender="girl",
        companion="Ben",
        companion_gender="boy",
        parent="mother",
        trait="cheerful",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    recipient_cfg = f["recipient_cfg"]
    need = f["need"]
    supply = f["supply"]
    setting = f["setting_cfg"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that uses the words "active" and "supply" and centers kindness on a trail.',
        f"Tell a gentle adventure where {hero.id} and {companion.id} are heading through {setting.place} and stop to help {recipient_cfg.label} with a {need.label} problem using {supply.phrase}.",
        f"Write a child-facing story where reaching {setting.landmark} matters less than doing the kind thing first, and let the right supply solve the trouble."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    recipient = f["recipient"]
    recipient_cfg = f["recipient_cfg"]
    need = f["need"]
    supply = f["supply"]
    setting = f["setting_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {companion.id} on a small adventure in {setting.place}. They meet {recipient_cfg.label} and choose to help."
        ),
        (
            f"What were {hero.id} and {companion.id} doing at the beginning?",
            f"They were walking along {setting.trail} toward {setting.landmark}. The trip felt exciting because they had a map and a supply satchel for the journey."
        ),
        (
            f"What problem did they find on the trail?",
            f"They found {recipient_cfg.label} who was {need.label}. That stopped the adventure for a moment because someone could not go on comfortably."
        ),
        (
            f"How did {hero.id} use the supply bag to help?",
            f"{hero.id} used {supply.phrase} to help with the problem. It worked because that supply matches being {need.label}, so the trouble eased instead of getting worse."
        ),
    ]
    if f["helped"]:
        qa.append(
            (
                "Why is kindness important in this story?",
                f"Kindness mattered because the children paused their own plan to care for someone else first. After they shared what was needed, the path opened again and the adventure became happier for everyone."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the group going on toward {setting.landmark}. The ending image shows a better adventure than before, because {recipient.label} could move easily again and the trail felt friendlier."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kindness", "trail"}
    tags |= set(world.facts["supply"].tags)
    tags |= set(world.facts["recipient_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, recipient_id: str, need_id: str, supply_id: str) -> str:
    if setting_id in SETTINGS and recipient_id in RECIPIENTS and recipient_id not in SETTINGS[setting_id].affords:
        return (
            f"(No story: {RECIPIENTS[recipient_id].label} does not fit naturally on the trail in {SETTINGS[setting_id].place}. "
            f"Pick a recipient that belongs in that setting.)"
        )
    if recipient_id in RECIPIENTS and need_id in NEEDS and need_id not in RECIPIENTS[recipient_id].needs:
        return (
            f"(No story: {RECIPIENTS[recipient_id].label} is not modeled with the need '{need_id}' here. "
            f"Choose a need that this recipient can really have in the story world.)"
        )
    if need_id in NEEDS and supply_id in SUPPLIES and not supply_matches_need(SUPPLIES[supply_id], NEEDS[need_id]):
        return (
            f"(No story: {SUPPLIES[supply_id].label} does not solve being {NEEDS[need_id].label}. "
            f"A kindness story here requires the supply to truly fix the problem.)"
        )
    return "(No story: this combination does not form a reasonable helping adventure.)"


ASP_RULES = r"""
fits(Setting, Recipient) :- affords(Setting, Recipient).
need_ok(Recipient, Need) :- recipient_need(Recipient, Need).
matches(Need, Supply) :- fixes(Supply, Need).

valid(Setting, Recipient, Need, Supply) :-
    fits(Setting, Recipient),
    need_ok(Recipient, Need),
    matches(Need, Supply).

helped :- chosen_need(N), chosen_supply(S), matches(N, S).
#show valid/4.
#show helped/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for recipient_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, recipient_id))
    for recipient_id, recipient in RECIPIENTS.items():
        lines.append(asp.fact("recipient", recipient_id))
        for need_id in sorted(recipient.needs):
            lines.append(asp.fact("recipient_need", recipient_id, need_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for supply_id, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", supply_id))
        lines.append(asp.fact("fixes", supply_id, supply.fixes))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_helped(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_supply", params.supply),
    ])
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "helped"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an active child, a supply satchel, and a kind adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.recipient and args.need and args.supply:
        if not valid_combo(args.setting, args.recipient, args.need, args.supply):
            raise StoryError(explain_rejection(args.setting, args.recipient, args.need, args.supply))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.recipient is None or combo[1] == args.recipient)
        and (args.need is None or combo[2] == args.need)
        and (args.supply is None or combo[3] == args.supply)
    ]
    if not combos:
        setting_id = args.setting or next(iter(SETTINGS))
        recipient_id = args.recipient or next(iter(RECIPIENTS))
        need_id = args.need or next(iter(NEEDS))
        supply_id = args.supply or next(iter(SUPPLIES))
        raise StoryError(explain_rejection(setting_id, recipient_id, need_id, supply_id))

    setting_id, recipient_id, need_id, supply_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    companion = args.companion or _pick_name(rng, companion_gender, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        recipient=recipient_id,
        need=need_id,
        supply=supply_id,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("recipient", RECIPIENTS),
        ("need", NEEDS),
        ("supply", SUPPLIES),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: unknown {field_name} '{value}'.)")
    if not valid_combo(params.setting, params.recipient, params.need, params.supply):
        raise StoryError(explain_rejection(params.setting, params.recipient, params.need, params.supply))

    world = tell(
        setting=SETTINGS[params.setting],
        recipient_cfg=RECIPIENTS[params.recipient],
        need=NEEDS[params.need],
        supply=SUPPLIES[params.supply],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        companion_name=params.companion,
        companion_gender=params.companion_gender,
        parent_type=params.parent,
        trait=params.trait,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid combos match Python ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    help_bad = 0
    for params in cases:
        py_helped = valid_combo(params.setting, params.recipient, params.need, params.supply)
        asp_help = asp_helped(params)
        if py_helped != asp_help:
            help_bad += 1
    if help_bad == 0:
        print(f"OK: ASP help inference matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {help_bad}/{len(cases)} help results differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, recipient, need, supply) combos:\n")
        for setting_id, recipient_id, need_id, supply_id in combos:
            print(f"  {setting_id:8} {recipient_id:10} {need_id:8} {supply_id}")
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
            header = f"### {p.hero} & {p.companion}: {p.recipient} {p.need} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
