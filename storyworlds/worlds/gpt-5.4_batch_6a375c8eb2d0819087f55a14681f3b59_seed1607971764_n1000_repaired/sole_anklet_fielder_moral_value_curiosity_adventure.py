#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py
==================================================================================

A standalone story world about a curious child who is the fielder in a seaside
game, discovers a lost anklet near the shore, and chooses whether curiosity
becomes selfish treasure-hunting or honest help. The world model prefers the
honest, sensible search and turns that choice into an adventure with a moral
center.

Run it
------
python storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py
python storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py --setting tidepools --clue bells --owner dancer
python storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py --method pocket_it
python storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py --all
python storyworlds/worlds/gpt-5.4/sole_anklet_fielder_moral_value_curiosity_adventure.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    field_game: str
    discovery_spot: str
    path_text: str
    crowd: int
    nearby_owners: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    detail: str
    hint_text: str
    owner_tags: set[str] = field(default_factory=set)
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
class Owner:
    id: str
    label: str
    role_noun: str
    station: str
    search_sign: str
    distance: int
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
class Method:
    id: str
    sense: int
    power: int
    text: str
    direct_text: str
    turnin_text: str
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


def _r_found(world: World) -> list[str]:
    anklet = world.get("anklet")
    hero = world.get("hero")
    if anklet.meters["found"] < THRESHOLD:
        return []
    sig = ("found", "anklet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["care"] += 1
    return ["__found__"]


def _r_clue(world: World) -> list[str]:
    anklet = world.get("anklet")
    hero = world.get("hero")
    if anklet.meters["clue_read"] < THRESHOLD:
        return []
    sig = ("clue", "anklet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["focus"] += 1
    hero.memes["hope"] += 1
    return ["__clue__"]


def _r_returned(world: World) -> list[str]:
    anklet = world.get("anklet")
    hero = world.get("hero")
    owner = world.get("owner")
    if anklet.meters["returned"] < THRESHOLD:
        return []
    sig = ("returned", "anklet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["lesson"] += 1
    return ["__returned__"]


CAUSAL_RULES = [
    Rule(name="found", tag="emotion", apply=_r_found),
    Rule(name="clue", tag="emotion", apply=_r_clue),
    Rule(name="returned", tag="emotion", apply=_r_returned),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "tidepools": Setting(
        id="tidepools",
        label="the tide pools",
        opening="The sea had left bright little pools between the rocks, each one glimmering like a secret map.",
        field_game="a driftball game on the shore",
        discovery_spot="where the wet sand met the first rocks",
        path_text="over flat stones striped with salt",
        crowd=0,
        nearby_owners={"swimmer", "fisher"},
        tags={"sea", "rocks"},
    ),
    "festival_beach": Setting(
        id="festival_beach",
        label="the festival beach",
        opening="Colorful flags snapped above the sand, and music kept skipping over the waves.",
        field_game="a shell-toss game beside the music tents",
        discovery_spot="near the trampled edge of the dance sand",
        path_text="past flapping flags and laughing families",
        crowd=1,
        nearby_owners={"dancer", "swimmer"},
        tags={"festival", "music"},
    ),
    "jetty": Setting(
        id="jetty",
        label="the old jetty",
        opening="The wooden boards of the jetty pointed out to sea like the start of an expedition.",
        field_game="a bouncing rope-ball game between the posts",
        discovery_spot="by the last dry plank before the beach grass",
        path_text="along creaky boards and coiled ropes",
        crowd=1,
        nearby_owners={"fisher", "swimmer"},
        tags={"jetty", "boats"},
    ),
}

CLUES = {
    "bells": Clue(
        id="bells",
        label="tiny bells",
        detail="three tiny bells that gave the softest silver chime",
        hint_text="Only someone dancing or moving fast would want bells that sang when they ran.",
        owner_tags={"dancer"},
        tags={"bells", "music"},
    ),
    "shells": Clue(
        id="shells",
        label="shell charms",
        detail="little shell charms polished smooth by water",
        hint_text="The shells looked chosen by someone who loved the waves enough to wear them.",
        owner_tags={"swimmer"},
        tags={"shell", "sea"},
    ),
    "net_thread": Clue(
        id="net_thread",
        label="a blue net thread",
        detail="a blue thread knotted through the clasp, the kind used to mend nets",
        hint_text="That knot looked like harbor work, quick and practiced.",
        owner_tags={"fisher"},
        tags={"net", "harbor"},
    ),
}

OWNERS = {
    "dancer": Owner(
        id="dancer",
        label="Maris",
        role_noun="festival dancer",
        station="the striped dance tent",
        search_sign="was checking the sand around the dance tent with worried eyes",
        distance=1,
        thanks="She fastened it back around her ankle and laughed with relief when the bells sang again.",
        tags={"dancer", "music"},
    ),
    "swimmer": Owner(
        id="swimmer",
        label="Nia",
        role_noun="young swimmer",
        station="the lifeguard flag",
        search_sign="was patting the towel by the lifeguard flag as if something small had vanished into the wind",
        distance=2,
        thanks="She slipped it onto her ankle and said the beach felt right again with the shells tapping softly together.",
        tags={"swimmer", "sea"},
    ),
    "fisher": Owner(
        id="fisher",
        label="Toma",
        role_noun="fisher's daughter",
        station="the small boats by the nets",
        search_sign="was searching beside the little boats, lifting loops of rope and peering under the nets",
        distance=1,
        thanks="She hugged the anklet to her chest and said her grandfather had braided the thread into it for luck.",
        tags={"fisher", "harbor"},
    ),
}

METHODS = {
    "ask_nearby": Method(
        id="ask_nearby",
        sense=2,
        power=1,
        text="asked the nearest grown-ups and children if they knew who had lost an anklet",
        direct_text="The question hopped from person to person until it landed in the right ears.",
        turnin_text="When no one close by knew, the child took the anklet to the harbor desk so the right owner could come for it later.",
        qa_text="asked nearby people who had lost the anklet",
        tags={"ask"},
    ),
    "follow_clue": Method(
        id="follow_clue",
        sense=3,
        power=2,
        text="studied the anklet carefully and followed the clue it gave",
        direct_text="The clue pointed them straight toward the person who was missing it.",
        turnin_text="The clue told them where to begin, but by the time they reached the place the owner had already moved on, so they turned it in safely.",
        qa_text="followed the clue on the anklet",
        tags={"clue"},
    ),
    "harbor_call": Method(
        id="harbor_call",
        sense=3,
        power=3,
        text="ran to the harbor master, who knew the beach and called out to the right part of the shore",
        direct_text="The harbor master's loud call carried farther than small feet could run.",
        turnin_text="Even the harbor master could not catch the owner before sunset, so the anklet was logged carefully at the desk.",
        qa_text="asked the harbor master to help find the owner",
        tags={"harbor"},
    ),
    "pocket_it": Method(
        id="pocket_it",
        sense=0,
        power=0,
        text="slipped the anklet into a pocket to keep it",
        direct_text="",
        turnin_text="",
        qa_text="kept the anklet",
        tags={"selfish"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Ava", "Zoe", "Nora", "Ivy", "Sana", "Tali"]
BOY_NAMES = ["Eli", "Milo", "Finn", "Noah", "Theo", "Jai", "Leo", "Arun"]
TRAITS = ["curious", "brave", "careful", "thoughtful", "eager", "observant"]


def clue_matches_owner(clue: Clue, owner: Owner) -> bool:
    return bool(clue.owner_tags & owner.tags)


def owner_nearby(setting: Setting, owner: Owner) -> bool:
    return owner.id in setting.nearby_owners


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for owner_id, owner in OWNERS.items():
                if owner_nearby(setting, owner) and clue_matches_owner(clue, owner):
                    combos.append((setting_id, clue_id, owner_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def search_difficulty(setting: Setting, owner: Owner, delay: int) -> int:
    return setting.crowd + owner.distance + delay


def is_direct_return(method: Method, setting: Setting, owner: Owner, delay: int) -> bool:
    return method.power >= search_difficulty(setting, owner, delay)


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} were spending the afternoon at {setting.label}. "
        f"{setting.opening}"
    )
    world.say(
        f"They had turned the shore into an expedition and were playing {setting.field_game}. "
        f"{hero.id} was the fielder, racing wherever the wild throws bounced."
    )


def discovery(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    anklet = world.get("anklet")
    anklet.meters["found"] += 1
    hero.meters["steps"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A crooked throw skipped away toward {setting.discovery_spot}. {hero.id} ran after it, "
        f"then stopped with a funny blink. Something hard had pressed against the sole of "
        f"{hero.pronoun('possessive')} sandal."
    )
    world.say(
        f"{hero.pronoun().capitalize()} knelt, brushed back the wet grit, and lifted out an anklet, "
        f"silver and sandy and shining in a thin stripe of sun."
    )
    world.say(
        f'"Look!" {friend.id} said. "That is not treasure from a story. That is someone\'s real anklet."'
    )


def inspect_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    anklet = world.get("anklet")
    anklet.meters["clue_read"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Up close, they saw {clue.detail}. {hero.id} turned the anklet slowly in "
        f"{hero.pronoun('possessive')} hands and listened to what it seemed to say."
    )
    world.say(clue.hint_text)
    world.say(
        f"Curiosity pulled at {hero.id} hard then, not to keep the anklet, but to learn whose footsteps had lost it."
    )


def choose_honesty(world: World, hero: Entity, grownup: Entity) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f'{hero.id} looked at the bright circle in {hero.pronoun("possessive")} palm and shook '
        f'{hero.pronoun("possessive")} head. "If I lost something special, I would want it back," '
        f'{hero.pronoun()} said.'
    )
    world.say(
        f'{grownup.label_word.capitalize()} smiled. "That is the brave kind of curiosity," '
        f'{grownup.pronoun()} said. "Come on. Let us help it find its ankle again."'
    )


def search(world: World, hero: Entity, friend: Entity, grownup: Entity, setting: Setting, clue: Clue,
           owner: Owner, method: Method, delay: int) -> bool:
    direct = is_direct_return(method, setting, owner, delay)
    world.say(
        f"So the three of them {method.text} and hurried {setting.path_text}."
    )
    if delay > 0:
        world.say(
            "But the tide kept creeping in, washing away neat little marks and making the search feel more urgent."
        )
    if direct:
        world.say(method.direct_text)
        world.say(
            f"Before long they saw {owner.label}, the {owner.role_noun}, who {owner.search_sign}."
        )
    else:
        world.say(
            f"They looked toward {owner.station}, but the place was already shifting with people and late light."
        )
        world.say(method.turnin_text)
    return direct


def return_anklet(world: World, hero: Entity, owner_ent: Entity, owner_cfg: Owner) -> None:
    anklet = world.get("anklet")
    anklet.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} held out the anklet. "Were you looking for this?" {hero.pronoun()} asked.'
    )
    world.say(owner_cfg.thanks)
    world.say(
        f'"Thank you for not walking past it," {owner_ent.pronoun()} said. "You turned a worried minute into a good one."'
    )


def turn_in(world: World, hero: Entity, grownup: Entity, owner_cfg: Owner) -> None:
    hero.memes["lesson"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} wrote down where the anklet had been found and set it on a folded cloth at the harbor desk."
    )
    world.say(
        f'"Whoever is missing it will know to ask here," {grownup.pronoun()} said. "{owner_cfg.station.capitalize()} is the first place we will send them."'
    )
    world.say(
        f"{hero.id} felt a little disappointed not to see the owner right away, but also steady inside. The anklet was safe, and that mattered."
    )


def ending_direct(world: World, hero: Entity, friend: Entity, owner_cfg: Owner) -> None:
    world.say(
        f"When the anklet was back where it belonged, the whole shore seemed brighter. "
        f"{friend.id} tossed the driftball up again, but now {hero.id} laughed and ran with a new idea in "
        f"{hero.pronoun('possessive')} heart: adventures were better when they helped somebody."
    )


def ending_turnin(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"As the sky turned peach and silver, {hero.id} and {friend.id} headed home along the water. "
        f"The game was over, but the adventure still felt real, because being honest had carried the anklet farther than small feet alone could."
    )


def tell(setting: Setting, clue: Clue, owner_cfg: Owner, method: Method,
         hero_name: str = "Lina", hero_type: str = "girl",
         friend_name: str = "Eli", friend_type: str = "boy",
         grownup_type: str = "mother", trait: str = "curious", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        role="friend",
        traits=["loyal"],
        attrs={"name": friend_name},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
        attrs={},
    ))
    owner_ent = world.add(Entity(
        id="owner",
        kind="character",
        type="girl",
        label=owner_cfg.label,
        role="owner",
        attrs={"station": owner_cfg.station},
    ))
    anklet = world.add(Entity(
        id="anklet",
        kind="thing",
        type="anklet",
        label="anklet",
        role="lost_object",
        attrs={"clue": clue.id},
    ))

    hero.meters["steps"] = 0.0
    anklet.meters["found"] = 0.0
    anklet.meters["clue_read"] = 0.0
    anklet.meters["returned"] = 0.0
    owner_ent.memes["relief"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["focus"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["honesty"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["lesson"] = 0.0
    friend.memes["joy"] = 0.0

    world.facts = {
        "setting": setting,
        "clue": clue,
        "owner_cfg": owner_cfg,
        "method": method,
        "delay": delay,
        "hero": hero,
        "friend": friend,
        "grownup": grownup,
        "owner": owner_ent,
        "anklet": anklet,
        "outcome": "",
        "hero_name": hero_name,
        "friend_name": friend_name,
    }

    introduce(world, hero, friend, setting)
    world.para()
    discovery(world, hero, friend, setting)
    inspect_clue(world, hero, friend, clue)
    world.para()
    choose_honesty(world, hero, grownup)
    direct = search(world, hero, friend, grownup, setting, clue, owner_cfg, method, delay)
    world.para()
    if direct:
        return_anklet(world, hero, owner_ent, owner_cfg)
        ending_direct(world, hero, friend, owner_cfg)
        outcome = "direct_return"
    else:
        turn_in(world, hero, grownup, owner_cfg)
        ending_turnin(world, hero, friend)
        outcome = "turned_in"
    world.facts["outcome"] = outcome
    world.facts["direct"] = direct
    world.facts["difficulty"] = search_difficulty(setting, owner_cfg, delay)
    return world


KNOWLEDGE = {
    "anklet": [
        (
            "What is an anklet?",
            "An anklet is a piece of jewelry worn around the ankle. Some are plain, and some have bells, beads, or shells on them.",
        )
    ],
    "sole": [
        (
            "What is the sole of a sandal or shoe?",
            "The sole is the bottom part that touches the ground. It protects your foot when you walk.",
        )
    ],
    "fielder": [
        (
            "What does a fielder do in a game?",
            "A fielder runs after the ball or catches it when it goes far away. Fielders help keep the game going.",
        )
    ],
    "honesty": [
        (
            "Why is it honest to return something you found?",
            "If you find something that belongs to someone else, returning it is honest because you are giving back what is not yours. That helps the other person feel safe and respected.",
        )
    ],
    "curiosity": [
        (
            "Can curiosity be a good thing?",
            "Yes. Curiosity helps you notice clues and learn new things, especially when you use it kindly and carefully.",
        )
    ],
    "harbor": [
        (
            "What does a harbor master do?",
            "A harbor master helps watch over boats and the busy shore. They often know where people should ask for lost things.",
        )
    ],
    "shell": [
        (
            "Why do shells get smooth at the beach?",
            "Waves and sand rub against shells again and again. Over time that can make them feel smooth and shiny.",
        )
    ],
    "bells": [
        (
            "Why do tiny bells make a chime?",
            "A bell has a little piece inside that taps the metal when it moves. That tapping makes the ringing sound.",
        )
    ],
    "net": [
        (
            "What is a fishing net used for?",
            "A fishing net is used to catch fish in the water. People sometimes mend nets with strong thread when they tear.",
        )
    ],
}
KNOWLEDGE_ORDER = ["anklet", "sole", "fielder", "honesty", "curiosity", "harbor", "shell", "bells", "net"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    owner: str
    method: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    grownup: str
    trait: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    clue = f["clue"]
    outcome = f["outcome"]
    hero_name = f["hero_name"]
    if outcome == "direct_return":
        return [
            'Write a short adventure story for a 3-to-5-year-old that includes the words "sole", "anklet", and "fielder".',
            f"Tell a seaside adventure where {hero_name}, the fielder in a beach game, finds an anklet after feeling something under a sandal sole and follows a clue to return it.",
            f"Write a gentle moral story about curiosity used the right way: a child explores a clue at {setting.label} and helps the missing owner.",
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "sole", "anklet", and "fielder".',
        f"Tell a seaside adventure where {hero_name}, the fielder in a beach game, finds an anklet by the shore and tries to find the owner before it gets too late.",
        "Write a moral story where curiosity leads a child to protect a lost object even when the owner cannot be found right away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    grownup = f["grownup"]
    clue = f["clue"]
    owner_cfg = f["owner_cfg"]
    setting = f["setting"]
    method = f["method"]
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    hero_label = hero_name
    friend_label = friend_name
    gp = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_label}, who was the fielder in a shore game, {friend_label}, and a grown-up who helped. The adventure began when they found a lost anklet at {setting.label}.",
        ),
        (
            f"How did {hero_label} find the anklet?",
            f"{hero_label} ran after the game piece and stopped when something pressed against the sole of {hero.pronoun('possessive')} sandal. That made {hero.pronoun('object')} look down and brush the sand away, which is how the anklet was found.",
        ),
        (
            "What clue did the anklet have?",
            f"It had {clue.detail}. That clue gave the children a smart guess about who might be missing it.",
        ),
        (
            f"Why did {hero_label} decide not to keep the anklet?",
            f"{hero_label} decided it belonged to someone else and should go back. The choice came from honesty, because {hero.pronoun()} imagined how sad it would feel to lose something special.",
        ),
    ]
    if f["outcome"] == "direct_return":
        qa.append(
            (
                f"How did they find the owner?",
                f"They {method.qa_text} and reached {owner_cfg.label}, the {owner_cfg.role_noun}, near {owner_cfg.station}. The clue helped point the search in the right direction, so their curiosity became useful instead of nosy.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the anklet back on its owner's ankle and everyone feeling lighter. The ending proves something changed because the beach game turned into an adventure about helping another person.",
            )
        )
    else:
        qa.append(
            (
                "Did they find the owner right away?",
                f"No, they did not find the owner before it got too late. Even so, they took the anklet to a safe desk so the right person could claim it later.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the anklet protected at the harbor desk and {hero_label} walking home proud. The ending still shows change, because {hero.pronoun()} chose honesty over keeping a shiny treasure.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"anklet", "sole", "fielder", "honesty", "curiosity"}
    clue = world.facts["clue"]
    method = world.facts["method"]
    if "shell" in clue.tags or "sea" in clue.tags:
        tags.add("shell")
    if "bells" in clue.tags or "music" in clue.tags:
        tags.add("bells")
    if "net" in clue.tags or "harbor" in clue.tags:
        tags.add("net")
    if "harbor" in method.tags:
        tags.add("harbor")
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="festival_beach",
        clue="bells",
        owner="dancer",
        method="follow_clue",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        grownup="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        setting="tidepools",
        clue="shells",
        owner="swimmer",
        method="harbor_call",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        grownup="father",
        trait="observant",
        delay=0,
    ),
    StoryParams(
        setting="jetty",
        clue="net_thread",
        owner="fisher",
        method="ask_nearby",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        grownup="mother",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="festival_beach",
        clue="shells",
        owner="swimmer",
        method="ask_nearby",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        grownup="father",
        trait="eager",
        delay=2,
    ),
]


def explain_rejection(setting: Setting, clue: Clue, owner: Owner) -> str:
    if not owner_nearby(setting, owner):
        return (
            f"(No story: {owner.label}, the {owner.role_noun}, is not reasonably nearby at {setting.label}. "
            f"Pick an owner who belongs in that setting.)"
        )
    return (
        f"(No story: {clue.label} do not point naturally to {owner.label}, the {owner.role_noun}. "
        f"Pick a clue that matches the owner.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on honesty and common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return (
        "direct_return"
        if is_direct_return(METHODS[params.method], SETTINGS[params.setting], OWNERS[params.owner], params.delay)
        else "turned_in"
    )


ASP_RULES = r"""
valid(S, C, O) :- setting(S), clue(C), owner(O), nearby(S, O), matches(C, O).

sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

difficulty(D) :- chosen_setting(S), chosen_owner(O), crowd(S, C), distance(O, R), delay(L), D = C + R + L.
direct_return :- chosen_method(M), power(M, P), difficulty(D), P >= D.

outcome(direct_return) :- direct_return.
outcome(turned_in) :- not direct_return.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("crowd", setting_id, setting.crowd))
        for owner_id in sorted(setting.nearby_owners):
            lines.append(asp.fact("nearby", setting_id, owner_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for owner_tag in sorted(clue.owner_tags):
            lines.append(asp.fact("clue_tag", clue_id, owner_tag))
    for owner_id, owner in OWNERS.items():
        lines.append(asp.fact("owner", owner_id))
        lines.append(asp.fact("distance", owner_id, owner.distance))
        for tag in sorted(owner.tags):
            lines.append(asp.fact("owner_tag", owner_id, tag))
    for clue_id, clue in CLUES.items():
        for owner_id, owner in OWNERS.items():
            if clue_matches_owner(clue, owner):
                lines.append(asp.fact("matches", clue_id, owner_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_owner", params.owner),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious fielder finds a lost anklet and chooses an honest adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--owner", choices=OWNERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time lost before the search begins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.setting and args.clue and args.owner:
        setting = SETTINGS[args.setting]
        clue = CLUES[args.clue]
        owner = OWNERS[args.owner]
        if not (owner_nearby(setting, owner) and clue_matches_owner(clue, owner)):
            raise StoryError(explain_rejection(setting, clue, owner))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.clue is None or combo[1] == args.clue)
        and (args.owner is None or combo[2] == args.owner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, clue_id, owner_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        clue=clue_id,
        owner=owner_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.owner not in OWNERS:
        raise StoryError(f"(Unknown owner: {params.owner})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    owner = OWNERS[params.owner]
    if not (owner_nearby(setting, owner) and clue_matches_owner(clue, owner)):
        raise StoryError(explain_rejection(setting, clue, owner))

    world = tell(
        setting=setting,
        clue=clue,
        owner_cfg=owner,
        method=METHODS[params.method],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        delay=params.delay,
    )

    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("friend", params.friend_name),
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    py_sense = {m.id for m in sensible_methods()}
    cl_sense = set(asp_sensible())
    if py_sense == cl_sense:
        print(f"OK: sensible methods match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sense)} clingo={sorted(cl_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random params for seed {seed}.")
            break

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, owner) combos:\n")
        for setting, clue, owner in combos:
            print(f"  {setting:15} {clue:12} {owner}")
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
            header = f"### {p.hero_name}: {p.setting}, {p.clue}, {p.owner}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
