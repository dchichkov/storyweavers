#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py
==================================================================================

A standalone story world for a tiny superhero-flavored tale about curiosity,
dialogue, and honesty. A child playing superhero finds a lost object near a bed
of poppies, feels tempted to keep the shiny thing as part of the game, then
talks with a helper and chooses the honest mission: find the owner and return it.

The world model tracks:
- physical meters such as separation, worry, found, and reunited
- emotional memes such as curiosity, temptation, guilt, courage, relief, and pride

The story shape is consistent:
1. superhero play and a mysterious discovery by the poppy bed
2. temptation and dialogue about what the right thing is
3. a search driven by asking and clues
4. return, gratitude, and an ending image proving the moral change

Run it
------
    python storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py
    python storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py --place courtyard --item keyring --owner gardener
    python storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py --item whistle --owner gardener
    python storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/poppy_curiosity_dialogue_moral_value_superhero_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "artist", "teacher"}
        male = {"boy", "father", "grandfather", "man", "gardener", "janitor", "coach"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    poppy_text: str
    owners: set[str] = field(default_factory=set)
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
class FoundItem:
    id: str
    label: str
    phrase: str
    sparkle: str
    owners: set[str] = field(default_factory=set)
    keep_as: str = ""
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
class OwnerCfg:
    id: str
    type: str
    label: str
    title: str
    item_word: str
    thanks: str
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
class HelperCfg:
    id: str
    type: str
    label: str
    style: str
    support: int
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
class Delivery:
    id: str
    sense: int
    text: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_owner_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    owner = world.entities.get("owner")
    if item is None or owner is None:
        return []
    if item.meters["separated"] < THRESHOLD:
        return []
    sig = ("owner_worry", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.meters["worry"] += 1
    return ["__owner_worry__"]


def _r_guilt(world: World) -> list[str]:
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    owner = world.entities.get("owner")
    if hero is None or item is None or owner is None:
        return []
    if item.meters["kept"] < THRESHOLD or owner.meters["worry"] < THRESHOLD:
        return []
    sig = ("guilt", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    return ["__guilt__"]


def _r_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if hero is None or owner is None or item is None:
        return []
    if item.meters["returned"] < THRESHOLD:
        return []
    sig = ("relief", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    owner.meters["reunited"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="owner_worry", tag="social", apply=_r_owner_worry),
    Rule(name="guilt", tag="moral", apply=_r_guilt),
    Rule(name="relief", tag="social", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place: Place, item: FoundItem, owner: OwnerCfg) -> bool:
    return owner.id in place.owners and owner.id in item.owners


def sensible_deliveries() -> list[Delivery]:
    return [d for d in DELIVERIES.values() if d.sense >= SENSE_MIN]


def explain_combo_rejection(place: Place, item: FoundItem, owner: OwnerCfg) -> str:
    if owner.id not in item.owners:
        return (
            f"(No story: {owner.label} would not reasonably be missing {item.phrase}. "
            f"Pick an owner who actually uses {item.label}.)"
        )
    return (
        f"(No story: {owner.label} does not fit {place.label} in this little world, "
        f"so the search would not be grounded. Pick a matching place or owner.)"
    )


def explain_delivery_rejection(delivery_id: str) -> str:
    delivery = DELIVERIES[delivery_id]
    better = ", ".join(sorted(d.id for d in sensible_deliveries()))
    return (
        f"(Refusing delivery '{delivery_id}': it scores too low on common sense "
        f"(sense={delivery.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for owner_id, owner in OWNERS.items():
                if valid_combo(place, item, owner):
                    out.append((place_id, item_id, owner_id))
    return out


def predict_worry(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["kept"] += 1
    propagate(sim, narrate=False)
    return {
        "owner_worry": sim.get("owner").meters["worry"],
        "hero_guilt": sim.get("hero").memes["guilt"],
    }


def direct_return_possible(honesty: str, helper: HelperCfg) -> bool:
    return HONESTY_LEVELS[honesty] + helper.support >= 5


def superhero_setup(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    hero.memes["imagination"] += 1
    world.say(
        f"{hero.id} tied a bright towel around {hero.pronoun('possessive')} shoulders "
        f"and declared that the day needed a superhero."
    )
    world.say(
        f"{place.opening} {place.poppy_text} Near the path, the poppy petals flashed red like tiny hero capes."
    )
    world.say(
        f'"Sidekick {helper.id}," {hero.id} whispered, "keep your eyes open for a mission."'
    )


def discover_item(world: World, hero: Entity, item: Entity, item_cfg: FoundItem) -> None:
    hero.memes["curiosity"] += 1
    item.meters["separated"] += 1
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something {item_cfg.sparkle} beside the poppy bed. {hero.id} crouched down and found {item_cfg.phrase}."
    )


def wonder(world: World, hero: Entity, item_cfg: FoundItem) -> None:
    world.say(
        f'"Whoa," {hero.id} said. "How did {item_cfg.label} get here? Maybe this is the start of a secret rescue."'
    )


def temptation(world: World, hero: Entity, item: Entity, item_cfg: FoundItem) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"For one excited moment, {hero.id} imagined using it as {item_cfg.keep_as}. "
        f"The idea made the game feel bigger."
    )


def helper_warning(world: World, hero: Entity, helper: Entity, item_cfg: FoundItem) -> None:
    pred = predict_worry(world)
    world.facts["predicted_owner_worry"] = pred["owner_worry"]
    world.facts["predicted_hero_guilt"] = pred["hero_guilt"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} looked at the poppy bed, then at {item_cfg.label}. '
        f'"A real superhero does not keep lost things," {helper.pronoun()} said. '
        f'"Someone might be looking everywhere for it."'
    )


def keep_briefly(world: World, hero: Entity, item: Entity, helper: Entity, item_cfg: FoundItem) -> None:
    item.meters["kept"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Just for one minute," {hero.id} said, slipping {item_cfg.label} into {hero.pronoun("possessive")} pocket. '
        f'"I only want to see what kind of mission it belongs to."'
    )
    if hero.memes["guilt"] >= THRESHOLD:
        world.say(
            f"But the pocket suddenly felt heavy. {hero.id} imagined the missing owner searching past the poppies and felt a pinch of guilt."
        )
    helper.memes["steadiness"] += 1
    world.say(
        f'"Then the mission is easy," {helper.id} said gently. "We ask. We listen. We give it back."'
    )


def choose_honesty(world: World, hero: Entity, item: Entity, helper: Entity) -> None:
    hero.memes["courage"] += 1
    hero.memes["honesty"] += 1
    item.meters["kept"] = 0.0
    world.say(
        f'{hero.id} took a deep breath. "You are right," {hero.pronoun()} said. '
        f'"Heroes help people first."'
    )


def ask_around(world: World, hero: Entity, helper: Entity, place: Place, owner_cfg: OwnerCfg, delivery: Delivery) -> None:
    hero.meters["search"] += 1
    helper.meters["search"] += 1
    world.say(
        f'Together they began asking kind questions around {place.label}. '
        f'"Did anyone lose something?" {hero.id} asked.'
    )
    if delivery.id == "ask":
        world.say(
            f'Soon they heard that the {owner_cfg.label} had been checking the path not long before.'
        )
    elif delivery.id == "lost_and_found":
        world.say(
            f'They took it to the little lost-and-found shelf first, and from there the trail pointed straight to the {owner_cfg.label}.'
        )
    else:
        world.say(
            f'They told a nearby grown-up what they had found, and the grown-up helped them look for the {owner_cfg.label}.'
        )


def reunite(world: World, hero: Entity, helper: Entity, owner: Entity, item: Entity, owner_cfg: OwnerCfg, delivery: Delivery) -> None:
    item.meters["returned"] += 1
    item.meters["separated"] = 0.0
    item.meters["carried_by_hero"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'At last they found the {owner_cfg.label}. {delivery.text} '
        f'{owner.pronoun().capitalize()} touched {owner.pronoun("possessive")} {owner_cfg.item_word} and smiled with relief.'
    )
    world.say(
        f'"My {owner_cfg.item_word}! Thank you," {owner.pronoun()} said. {owner_cfg.thanks}'
    )


def moral_close(world: World, hero: Entity, helper: Entity, place: Place, direct: bool) -> None:
    hero.memes["lesson"] += 1
    if direct:
        world.say(
            f'"That felt even better than pretending," {hero.id} said.'
        )
    else:
        world.say(
            f'"I thought keeping it would make me feel powerful," {hero.id} admitted, '
            f'"but giving it back feels lighter."'
        )
    world.say(
        f'{helper.id} nodded. "That is because honesty is its own superpower."'
    )
    world.say(
        f"Before they ran off again, {hero.id} glanced at the poppy bed. The red flowers still looked like little capes, "
        f"but now the bravest part of the mission was not the costume. It was the choice."
    )


def tell(
    place: Place,
    item_cfg: FoundItem,
    owner_cfg: OwnerCfg,
    helper_cfg: HelperCfg,
    delivery: Delivery,
    hero_name: str = "Poppy",
    hero_gender: str = "girl",
    honesty: str = "high",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["imaginative", "curious"],
            attrs={"honesty_level": honesty},
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            traits=[helper_cfg.style],
            attrs={"support": helper_cfg.support},
            tags=set(helper_cfg.tags),
        )
    )
    owner = world.add(
        Entity(
            id="Owner",
            kind="character",
            type=owner_cfg.type,
            role="owner",
            label=owner_cfg.label,
            tags=set(owner_cfg.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="object",
            label=item_cfg.label,
            attrs={"kind": item_cfg.id},
            tags=set(item_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="place",
            type="place",
            label=place.label,
            tags=set(place.tags),
        )
    )

    hero.memes["curiosity"] = 0.0
    hero.memes["temptation"] = 0.0
    hero.memes["guilt"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["honesty"] = 0.0
    owner.meters["worry"] = 0.0
    item.meters["separated"] = 0.0
    item.meters["kept"] = 0.0
    item.meters["returned"] = 0.0

    superhero_setup(world, hero, helper, place)
    discover_item(world, hero, item, item_cfg)
    wonder(world, hero, item_cfg)

    world.para()
    temptation(world, hero, item, item_cfg)
    helper_warning(world, hero, helper, item_cfg)
    direct = direct_return_possible(honesty, helper_cfg)
    if not direct:
        keep_briefly(world, hero, item, helper, item_cfg)
    choose_honesty(world, hero, item, helper)

    world.para()
    ask_around(world, hero, helper, place, owner_cfg, delivery)
    reunite(world, hero, helper, owner, item, owner_cfg, delivery)

    world.para()
    moral_close(world, hero, helper, place, direct)

    world.facts.update(
        hero=hero,
        helper=helper,
        owner=owner,
        item=item,
        place=place,
        item_cfg=item_cfg,
        owner_cfg=owner_cfg,
        helper_cfg=helper_cfg,
        delivery=delivery,
        direct_return=direct,
        outcome="direct_return" if direct else "confess_return",
    )
    return world


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="the apartment courtyard",
        opening="After breakfast, the apartment courtyard turned into Hero Base Number One.",
        poppy_text="A neat circle of poppies blazed beside the mailboxes.",
        owners={"gardener", "artist", "janitor"},
        tags={"garden"},
    ),
    "school_gate": Place(
        id="school_gate",
        label="the school gate",
        opening="After school, the gate became a launch pad for grand rescues.",
        poppy_text="A row of poppies nodded by the fence.",
        owners={"crossing_guard", "janitor", "teacher"},
        tags={"school"},
    ),
    "playground": Place(
        id="playground",
        label="the playground",
        opening="In the afternoon, the playground felt like a city waiting for a cape.",
        poppy_text="At one corner, poppies leaned over the low stone border.",
        owners={"coach", "artist", "crossing_guard"},
        tags={"play"},
    ),
}

ITEMS = {
    "whistle": FoundItem(
        id="whistle",
        label="the silver whistle",
        phrase="a silver whistle on a blue cord",
        sparkle="glinted",
        owners={"crossing_guard", "coach"},
        keep_as="a command whistle for Captain Brave",
        tags={"whistle", "lost_item"},
    ),
    "keyring": FoundItem(
        id="keyring",
        label="the brass keyring",
        phrase="a brass keyring with three little keys",
        sparkle="winked",
        owners={"gardener", "janitor"},
        keep_as="a secret key for a hero headquarters",
        tags={"keys", "lost_item"},
    ),
    "badge": FoundItem(
        id="badge",
        label="the name badge",
        phrase="a bright name badge with a clip on the back",
        sparkle="shone",
        owners={"teacher", "artist", "crossing_guard"},
        keep_as="a shiny hero badge",
        tags={"badge", "lost_item"},
    ),
}

OWNERS = {
    "gardener": OwnerCfg(
        id="gardener",
        type="gardener",
        label="gardener",
        title="Mr. Green",
        item_word="keyring",
        thanks="He had needed the keys to open the water box for the flowers, especially the thirsty poppies.",
        tags={"gardener", "plants"},
    ),
    "janitor": OwnerCfg(
        id="janitor",
        type="janitor",
        label="janitor",
        title="Mr. Hale",
        item_word="keyring",
        thanks="He had been checking doors and shelves all morning and could finally get back to helping everyone.",
        tags={"janitor", "work"},
    ),
    "crossing_guard": OwnerCfg(
        id="crossing_guard",
        type="man",
        label="crossing guard",
        title="Mr. Cole",
        item_word="whistle",
        thanks="Without it, keeping children safe at the crossing had felt much harder.",
        tags={"crossing_guard", "safety"},
    ),
    "coach": OwnerCfg(
        id="coach",
        type="man",
        label="coach",
        title="Coach Luis",
        item_word="whistle",
        thanks="Practice was about to start, and the team needed the whistle to hear the game signals clearly.",
        tags={"coach", "sports"},
    ),
    "teacher": OwnerCfg(
        id="teacher",
        type="teacher",
        label="teacher",
        title="Ms. Bell",
        item_word="name badge",
        thanks="She wore it every day so younger children would know whom to ask for help.",
        tags={"teacher", "school"},
    ),
    "artist": OwnerCfg(
        id="artist",
        type="artist",
        label="artist",
        title="Ms. Rosa",
        item_word="name badge",
        thanks="She had been sketching the poppies and needed the badge for the art table sign.",
        tags={"artist", "art"},
    ),
}

HELPERS = {
    "grandma": HelperCfg(
        id="grandma",
        type="grandmother",
        label="Grandma",
        style="calm",
        support=3,
        tags={"grandma", "dialogue"},
    ),
    "dad": HelperCfg(
        id="dad",
        type="father",
        label="Dad",
        style="steady",
        support=2,
        tags={"dad", "dialogue"},
    ),
    "friend": HelperCfg(
        id="friend",
        type="girl",
        label="Mina",
        style="thoughtful",
        support=1,
        tags={"friend", "dialogue"},
    ),
}

DELIVERIES = {
    "ask": Delivery(
        id="ask",
        sense=3,
        text="The children held out the lost thing at once.",
        qa_text="They asked around kindly and handed the lost thing back as soon as they found the owner.",
        tags={"ask", "dialogue"},
    ),
    "lost_and_found": Delivery(
        id="lost_and_found",
        sense=2,
        text="The helper took it from the shelf and the children offered it back with both hands.",
        qa_text="They used the lost-and-found shelf to trace the owner, then returned the item politely.",
        tags={"lost_and_found", "dialogue"},
    ),
    "keep": Delivery(
        id="keep",
        sense=1,
        text="Nobody sensible would do this in the finished story.",
        qa_text="This is not used in valid stories.",
        tags={"bad_choice"},
    ),
}

HONESTY_LEVELS = {"high": 3, "medium": 2, "low": 1}

GIRL_NAMES = ["Poppy", "Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Max", "Sam", "Eli", "Finn", "Theo"]


@dataclass
class StoryParams:
    place: str
    item: str
    owner: str
    helper: str
    delivery: str
    hero_name: str
    hero_gender: str
    honesty: str
    parent: str = "mother"
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
    "lost_item": [
        (
            "What should you do if you find something that belongs to someone else?",
            "You should try to find the owner or give it to a trusted grown-up or lost-and-found place. Keeping it can make the owner worried, but returning it helps fix the problem."
        )
    ],
    "honesty": [
        (
            "Why is honesty like a superpower?",
            "Honesty helps people trust you and solve problems the right way. It may take courage, but it makes the ending better for everyone."
        )
    ],
    "poppy": [
        (
            "What is a poppy?",
            "A poppy is a flower with soft petals, often bright red or orange. Its color can look bold and bright, almost like a tiny flag or cape."
        )
    ],
    "whistle": [
        (
            "What does a whistle do?",
            "A whistle makes a sharp sound that people can hear quickly. Coaches and crossing guards use whistles to give signals and keep people organized."
        )
    ],
    "keys": [
        (
            "Why are keys important?",
            "Keys open locks that protect places and tools. If keys are lost, grown-ups may not be able to do their jobs until the keys are found."
        )
    ],
    "badge": [
        (
            "Why might a name badge matter?",
            "A name badge helps other people know who someone is. It can make it easier for children or visitors to find the right grown-up for help."
        )
    ],
    "crossing_guard": [
        (
            "What does a crossing guard do?",
            "A crossing guard helps children cross streets safely. They watch traffic and guide people when it is time to walk."
        )
    ],
    "gardener": [
        (
            "What does a gardener do?",
            "A gardener cares for plants by watering, trimming, and checking what they need. Healthy flowers often depend on that daily care."
        )
    ],
    "teacher": [
        (
            "Why do children ask teachers for help?",
            "Teachers help children learn, stay safe, and solve problems at school. They are trusted grown-ups who can guide people kindly."
        )
    ],
    "artist": [
        (
            "What does an artist do?",
            "An artist makes pictures or other art to show ideas, colors, and feelings. Artists often look very closely at the world around them."
        )
    ],
    "coach": [
        (
            "What does a coach do?",
            "A coach teaches players how to practice, work together, and follow the game. Coaches also help teams listen and stay organized."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "poppy",
    "lost_item",
    "honesty",
    "whistle",
    "keys",
    "badge",
    "crossing_guard",
    "gardener",
    "teacher",
    "artist",
    "coach",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    owner_cfg = f["owner_cfg"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]
    if outcome == "direct_return":
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the word "poppy" and centers on curiosity, dialogue, and honesty.',
            f"Tell a gentle superhero mission where {hero.id} finds {item_cfg.phrase} near some poppies, talks with {helper_cfg.label}, and returns it to the {owner_cfg.label}.",
            f"Write a simple moral story where a child first wonders about a shiny lost thing, then chooses the brave and honest action instead of keeping it.",
        ]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "poppy" and centers on curiosity, dialogue, and moral courage.',
        f"Tell a superhero-style story where {hero.id} is tempted to keep {item_cfg.label} found by the poppy bed, but a conversation with {helper_cfg.label} leads to a confession and return.",
        f"Write a story in which the truest superpower is honesty: a child feels tempted by a shiny lost object, then makes things right through kind dialogue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    owner_cfg = f["owner_cfg"]
    place = f["place"]
    delivery = f["delivery"]
    direct = f["direct_return"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, and {helper.id}, who helps with the mission. The mission begins when they find {item_cfg.phrase} near the poppy bed."
        ),
        (
            f"What made {hero.id} curious?",
            f"{hero.id} saw something shiny beside the poppies and wanted to know how it got there. That curious moment turned an ordinary game into a rescue mission."
        ),
        (
            f"Why did {helper.id} say they should not keep the lost thing?",
            f'{helper.id} said that someone might be searching for it already. In the world model, a lost item makes the owner worried, so keeping it would hurt instead of help.'
        ),
    ]
    if direct:
        qa.append(
            (
                f"How did {hero.id} solve the mission?",
                f"{hero.id} chose honesty right away, asked kind questions around {place.label}, and returned the item to the {owner_cfg.label}. {delivery.qa_text}"
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} keep the lost thing?",
                f"{hero.id} tucked it away for a moment, but then felt guilty and admitted that keeping it was the wrong idea. After the talk with {helper.id}, {hero.pronoun()} chose the honest mission and returned it."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that honesty and helping others are stronger than pretending to be powerful. {hero.id} feels proud at the end because returning the lost thing fixed a real problem."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"poppy", "lost_item", "honesty"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["owner_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        item="keyring",
        owner="gardener",
        helper="grandma",
        delivery="ask",
        hero_name="Poppy",
        hero_gender="girl",
        honesty="high",
        parent="mother",
    ),
    StoryParams(
        place="school_gate",
        item="whistle",
        owner="crossing_guard",
        helper="dad",
        delivery="ask",
        hero_name="Leo",
        hero_gender="boy",
        honesty="medium",
        parent="father",
    ),
    StoryParams(
        place="playground",
        item="badge",
        owner="artist",
        helper="friend",
        delivery="lost_and_found",
        hero_name="Mia",
        hero_gender="girl",
        honesty="low",
        parent="mother",
    ),
    StoryParams(
        place="school_gate",
        item="badge",
        owner="teacher",
        helper="grandma",
        delivery="lost_and_found",
        hero_name="Nora",
        hero_gender="girl",
        honesty="medium",
        parent="mother",
    ),
    StoryParams(
        place="playground",
        item="whistle",
        owner="coach",
        helper="dad",
        delivery="ask",
        hero_name="Finn",
        hero_gender="boy",
        honesty="low",
        parent="father",
    ),
]


ASP_RULES = r"""
valid(P, I, O) :- place(P), item(I), owner(O), place_owner(P, O), item_owner(I, O).
sensible(D) :- delivery(D), sense(D, S), sense_min(M), S >= M.

support(3) :- chosen_helper(grandma).
support(2) :- chosen_helper(dad).
support(1) :- chosen_helper(friend).

honesty_score(3) :- chosen_honesty(high).
honesty_score(2) :- chosen_honesty(medium).
honesty_score(1) :- chosen_honesty(low).

direct_return :- honesty_score(H), support(S), H + S >= 5.
outcome(direct_return) :- direct_return.
outcome(confess_return) :- not direct_return.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for owner in sorted(place.owners):
            lines.append(asp.fact("place_owner", place_id, owner))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for owner in sorted(item.owners):
            lines.append(asp.fact("item_owner", item_id, owner))
    for owner_id in OWNERS:
        lines.append(asp.fact("owner", owner_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for honesty_id in HONESTY_LEVELS:
        lines.append(asp.fact("honesty", honesty_id))
    for delivery_id, delivery in DELIVERIES.items():
        lines.append(asp.fact("delivery", delivery_id))
        lines.append(asp.fact("sense", delivery_id, delivery.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_honesty", params.honesty),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if direct_return_possible(params.honesty, HELPERS[params.helper]):
        return "direct_return"
    return "confess_return"


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

    clingo_deliveries = set(asp_sensible())
    python_deliveries = {d.id for d in sensible_deliveries()}
    if clingo_deliveries == python_deliveries:
        print(f"OK: sensible deliveries match ({sorted(clingo_deliveries)}).")
    else:
        rc = 1
        print("MISMATCH in sensible deliveries:")
        print("  clingo:", sorted(clingo_deliveries))
        print("  python:", sorted(python_deliveries))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero-style lost-and-found mission with poppies, curiosity, dialogue, and honesty."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--owner", choices=OWNERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delivery", choices=DELIVERIES)
    ap.add_argument("--honesty", choices=HONESTY_LEVELS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.owner:
        if not valid_combo(PLACES[args.place], ITEMS[args.item], OWNERS[args.owner]):
            raise StoryError(explain_combo_rejection(PLACES[args.place], ITEMS[args.item], OWNERS[args.owner]))
    if args.delivery and DELIVERIES[args.delivery].sense < SENSE_MIN:
        raise StoryError(explain_delivery_rejection(args.delivery))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.owner is None or combo[2] == args.owner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, owner_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    delivery_id = args.delivery or rng.choice(sorted(d.id for d in sensible_deliveries()))
    honesty = args.honesty or rng.choice(sorted(HONESTY_LEVELS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        item=item_id,
        owner=owner_id,
        helper=helper_id,
        delivery=delivery_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        honesty=honesty,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item_cfg = ITEMS[params.item]
        owner_cfg = OWNERS[params.owner]
        helper_cfg = HELPERS[params.helper]
        delivery = DELIVERIES[params.delivery]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not valid_combo(place, item_cfg, owner_cfg):
        raise StoryError(explain_combo_rejection(place, item_cfg, owner_cfg))
    if delivery.sense < SENSE_MIN:
        raise StoryError(explain_delivery_rejection(params.delivery))
    if params.honesty not in HONESTY_LEVELS:
        raise StoryError("(Invalid honesty level.)")

    world = tell(
        place=place,
        item_cfg=item_cfg,
        owner_cfg=owner_cfg,
        helper_cfg=helper_cfg,
        delivery=delivery,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        honesty=params.honesty,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible deliveries: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, owner) combos:\n")
        for place, item, owner in combos:
            print(f"  {place:12} {item:10} {owner}")
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
            header = f"### {p.hero_name}: {p.item} at {p.place} for {p.owner} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
