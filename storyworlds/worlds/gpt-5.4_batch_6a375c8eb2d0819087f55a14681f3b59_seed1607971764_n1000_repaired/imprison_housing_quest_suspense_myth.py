#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py
=================================================================

A standalone storyworld for a small mythic quest: a child hero goes out to free
a helpful spirit that has been trapped, because the village's housing is
suffering while that spirit remains imprisoned.

The domain is deliberately narrow and constraint-checked:
- each realm has one spirit whose gift the people truly need,
- each prison needs the right release key,
- the quest always reaches a full ending, but the middle may be quiet or tense.

Run it
------
    python storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py
    python storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py --realm reed_delta --captive rain_lark
    python storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py --prison ice_cage --key echo_riddle
    python storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/imprison_housing_quest_suspense_myth.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "priestess"}
        male = {"boy", "man", "grandfather", "priest", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Realm:
    id: str
    place: str
    housing: str
    problem: str
    need_tag: str
    path: str
    ending_image: str
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
class Captive:
    id: str
    label: str
    title: str
    boon: str
    need_tag: str
    freeing_line: str
    ending_gift: str
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
class Prison:
    id: str
    label: str
    lair: str
    seal_text: str
    guardian: str
    omen: str
    danger: int
    needed_key: str
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
class Key:
    id: str
    label: str
    action: str
    success: str
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
class Helper:
    id: str
    label: str
    arrival: str
    method: str
    aid: int
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


def _r_housing_harm(world: World) -> list[str]:
    captive = world.get("captive")
    village = world.get("village")
    hero = world.get("hero")
    elder = world.get("elder")
    if captive.meters["imprisoned"] < THRESHOLD:
        return []
    sig = ("housing_harm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["housing_harm"] += 1
    elder.memes["grief"] += 1
    hero.memes["duty"] += 1
    return ["__housing_harm__"]


def _r_release_blessing(world: World) -> list[str]:
    captive = world.get("captive")
    village = world.get("village")
    hero = world.get("hero")
    if captive.meters["freed"] < THRESHOLD:
        return []
    sig = ("release_blessing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["housing_harm"] = 0.0
    village.meters["blessing"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    return ["__release_blessing__"]


CAUSAL_RULES = [
    Rule(name="housing_harm", tag="physical", apply=_r_housing_harm),
    Rule(name="release_blessing", tag="physical", apply=_r_release_blessing),
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
        for s in produced:
            world.say(s)
    return produced


REALMS = {
    "reed_delta": Realm(
        id="reed_delta",
        place="the Reed Delta",
        housing="reed housing raised on stilts above black water",
        problem="the roof-bundles have gone brittle, and night rain leaks through the sleeping mats",
        need_tag="rain",
        path="the causeway of whispering reeds",
        ending_image="By dawn, silver rain stitched the reeds tight again, and every lamp inside the stilt houses burned steady and dry.",
        tags={"housing", "rain", "village"},
    ),
    "ash_hill": Realm(
        id="ash_hill",
        place="Ash Hill",
        housing="stone housing carved into the warm side of the hill",
        problem="the hearths have gone cold, and children sleep in cloaks beside dark ash",
        need_tag="hearth",
        path="the stair of cracked basalt",
        ending_image="By dawn, red warmth ran through the hill again, and every stone doorway breathed out bread-smell and firelight.",
        tags={"housing", "hearth", "village"},
    ),
    "sun_orchard": Realm(
        id="sun_orchard",
        place="the Sun Orchard",
        housing="timber housing ringed around a well and shaded by fig trees",
        problem="a dim haze lies over the roofs, and no fruit will ripen on the beams or in the baskets",
        need_tag="sun",
        path="the gold-leaf road beneath the figs",
        ending_image="By dawn, gold lay on every roof-beam, and the orchard houses shone as if morning had chosen to live there.",
        tags={"housing", "sun", "village"},
    ),
}

CAPTIVES = {
    "rain_lark": Captive(
        id="rain_lark",
        label="the rain-lark",
        title="little singer of the eaves",
        boon="calls kind rain that swells reeds and seals roofs",
        need_tag="rain",
        freeing_line="A cool note slipped from its beak, small as a drop and bright as tin.",
        ending_gift="It circled above the village and called down the careful rain the roofs had been missing.",
        tags={"rain", "bird", "imprison"},
    ),
    "hearth_fox": Captive(
        id="hearth_fox",
        label="the hearth-fox",
        title="ember-runner of old kitchens",
        boon="carries living warmth from hearth to hearth",
        need_tag="hearth",
        freeing_line="Its tail-tip glowed first, like a coal remembering its own name.",
        ending_gift="It leaped from doorway to doorway and woke the sleeping hearths with one bright brush of its tail.",
        tags={"hearth", "fox", "imprison"},
    ),
    "sun_stag": Captive(
        id="sun_stag",
        label="the sun-stag",
        title="horned bearer of the first light",
        boon="draws full morning over orchards and roofs",
        need_tag="sun",
        freeing_line="Light gathered between its antlers, trembling like water in a golden bowl.",
        ending_gift="It climbed the ridge and shook morning from its antlers over the orchard roofs.",
        tags={"sun", "stag", "imprison"},
    ),
}

PRISONS = {
    "ice_cage": Prison(
        id="ice_cage",
        label="an ice cage",
        lair="the cave under the frozen fall",
        seal_text="clear bars colder than moonlight",
        guardian="the Frost Sleeper",
        omen="the cave breathed white mist, and somewhere deep inside, ice clicked like teeth",
        danger=3,
        needed_key="ember_key",
        tags={"ice", "cave"},
    ),
    "thorn_ring": Prison(
        id="thorn_ring",
        label="a thorn ring",
        lair="the grove of shut flowers",
        seal_text="black briars woven into a living knot",
        guardian="the Briar Mother",
        omen="every branch leaned inward, listening",
        danger=2,
        needed_key="moon_sickle",
        tags={"thorn", "grove"},
    ),
    "bronze_latch": Prison(
        id="bronze_latch",
        label="a bronze-latched shrine",
        lair="the shrine above the echoing gorge",
        seal_text="a bronze door with no hinge that mortal hands can see",
        guardian="the Echo Keeper",
        omen="the gorge threw back each footstep as if another traveler were following",
        danger=1,
        needed_key="echo_riddle",
        tags={"bronze", "shrine"},
    ),
}

KEYS = {
    "ember_key": Key(
        id="ember_key",
        label="an ember key",
        action="pressed the ember key against the seal",
        success="Warm red lines ran through the prison, and the hard cold began to sigh and melt.",
        tags={"fire", "key"},
    ),
    "moon_sickle": Key(
        id="moon_sickle",
        label="a moon-sickle",
        action="drew the moon-sickle through the knot",
        success="Silver edges flashed once, and the living thorns loosened as if night itself had told them to sleep.",
        tags={"moon", "key"},
    ),
    "echo_riddle": Key(
        id="echo_riddle",
        label="an echo riddle",
        action="spoke the echo riddle into the lock",
        success="The bronze answered with its own forgotten name, and the shut door folded open like a bowing head.",
        tags={"echo", "key"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="a white owl",
        arrival="A white owl came down without a sound and rode the dark above the hero's shoulder.",
        method="The owl flew ahead and blinked once whenever the hidden way bent toward danger.",
        aid=3,
        tags={"owl", "helper"},
    ),
    "goat": Helper(
        id="goat",
        label="a sure-footed mountain goat",
        arrival="A sure-footed mountain goat stepped from the rocks as if the hill itself had lent the hero a guide.",
        method="The goat found ledges no wider than a hand and taught the hero where to place each careful foot.",
        aid=2,
        tags={"goat", "helper"},
    ),
    "otter": Helper(
        id="otter",
        label="a river otter",
        arrival="A river otter rose from the black water and shook moon-drops from its whiskers.",
        method="The otter slipped through reed and current, showing the hero where the still water hid the deep pull.",
        aid=1,
        tags={"otter", "helper"},
    ),
}

GIRL_NAMES = ["Nara", "Iris", "Luma", "Tali", "Sera", "Mira", "Dema", "Ari"]
BOY_NAMES = ["Tarin", "Ivo", "Sorin", "Pelu", "Rian", "Milo", "Aren", "Toma"]
TRAITS = ["steady", "patient", "brave", "careful", "quiet", "stubborn"]


def realm_matches_captive(realm: Realm, captive: Captive) -> bool:
    return realm.need_tag == captive.need_tag


def prison_accepts_key(prison: Prison, key: Key) -> bool:
    return prison.needed_key == key.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for captive_id, captive in CAPTIVES.items():
            if not realm_matches_captive(realm, captive):
                continue
            for prison_id, prison in PRISONS.items():
                for key_id, key in KEYS.items():
                    if prison_accepts_key(prison, key):
                        combos.append((realm_id, captive_id, prison_id, key_id))
    return combos


def suspense_outcome(prison: Prison, helper: Helper) -> str:
    return "quiet" if helper.aid >= prison.danger else "chase"


def predict_success(world: World) -> dict:
    sim = world.copy()
    prison = sim.facts["prison_cfg"]
    helper = sim.facts["helper_cfg"]
    return {
        "outcome": suspense_outcome(prison, helper),
        "danger": prison.danger,
        "aid": helper.aid,
    }


def introduce_need(world: World, hero: Entity, elder: Entity, realm: Realm, captive: Captive) -> None:
    village = world.get("village")
    world.say(
        f"In {realm.place}, the people lived in {realm.housing}. But {realm.problem}."
    )
    world.say(
        f"The old ones said this had begun when {captive.label}, {captive.title}, was taken away and held to imprison its gift."
    )
    world.say(
        f"{hero.id} heard the drip, the cold, and the hungry quiet in the houses, and could not pretend not to hear them."
    )
    world.facts["problem_line"] = realm.problem
    world.facts["housing_line"] = realm.housing
    village.meters["need"] += 1
    elder.memes["worry"] += 1
    hero.memes["duty"] += 1


def charge_quest(world: World, hero: Entity, elder: Entity, key: Key, helper: Helper, prison: Prison) -> None:
    world.say(
        f'Then {elder.id}, keeper of the old songs, placed {key.label} in {hero.pronoun("possessive")} hands and said, '
        f'"Go by {world.facts["realm_cfg"].path} to {prison.lair}. Only this can break {prison.seal_text}."'
    )
    world.say(helper.arrival)
    world.say(helper.method)


def approach_lair(world: World, hero: Entity, prison: Prison, helper: Helper) -> None:
    pred = predict_success(world)
    hero.memes["dread"] += 1
    world.facts["predicted_outcome"] = pred["outcome"]
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_aid"] = pred["aid"]
    world.say(
        f"By night {hero.id} came to {prison.lair}. {prison.omen}."
    )
    if pred["outcome"] == "quiet":
        world.say(
            f"{hero.id} felt fear move through {hero.pronoun('object')} like cold water, yet the path seemed to lean open under {helper.label}'s guidance."
        )
    else:
        world.say(
            f"{hero.id} felt fear move through {hero.pronoun('object')} like cold water, and every shadow made it seem that {prison.guardian} had already opened one eye."
        )


def reach_prison(world: World, captive_ent: Entity, prison: Prison) -> None:
    captive_ent.meters["imprisoned"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"In the heart of the lair stood {prison.label}, shaped from {prison.seal_text}. Inside waited {captive_ent.label}, silent and dim."
    )


def free_captive(world: World, hero: Entity, captive_ent: Entity, captive_cfg: Captive, key: Key) -> None:
    world.say(
        f"{hero.id} {key.action}. {key.success}"
    )
    captive_ent.meters["imprisoned"] = 0.0
    captive_ent.meters["freed"] = 1.0
    propagate(world, narrate=False)
    world.say(captive_cfg.freeing_line)


def quiet_escape(world: World, hero: Entity, captive_cfg: Captive, prison: Prison) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"The dark did not spring. {prison.guardian} slept on, and {hero.id} slipped away beside {captive_cfg.label} before the last shard of the prison touched the floor."
    )


def chase_escape(world: World, hero: Entity, helper: Helper, prison: Prison, captive_cfg: Captive) -> None:
    hero.memes["fear"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"Then the lair groaned. {prison.guardian} stirred, and the stone, branch, or ice around the chamber answered with a terrible rustle."
    )
    world.say(
        f"But {helper.label} did not fail. {helper.method} So {hero.id} ran with {captive_cfg.label} at {hero.pronoun('possessive')} side, and the dark hand behind them closed on nothing but broken magic."
    )


def return_and_restore(world: World, hero: Entity, realm: Realm, captive_cfg: Captive) -> None:
    village = world.get("village")
    hero.memes["joy"] += 1
    village.meters["restored"] += 1
    world.say(
        f"When {hero.id} came home, {captive_cfg.ending_gift}"
    )
    world.say(realm.ending_image)


def tell(
    realm: Realm,
    captive_cfg: Captive,
    prison: Prison,
    key: Key,
    helper: Helper,
    hero_name: str = "Nara",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "steady",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    village = world.add(Entity(id="village", kind="thing", type="village", label="the village"))
    captive_ent = world.add(Entity(id="captive", kind="thing", type="spirit", label=captive_cfg.label, role="captive"))
    helper_ent = world.add(Entity(id="helper", kind="thing", type="helper", label=helper.label, role="helper"))

    world.facts.update(
        realm_cfg=realm,
        captive_cfg=captive_cfg,
        prison_cfg=prison,
        key_cfg=key,
        helper_cfg=helper,
        hero=hero,
        elder=elder,
        village=village,
        captive=captive_ent,
        helper=helper_ent,
    )

    captive_ent.meters["imprisoned"] = 1.0
    propagate(world, narrate=False)

    introduce_need(world, hero, elder, realm, captive_cfg)
    world.para()
    charge_quest(world, hero, elder, key, helper, prison)
    world.para()
    approach_lair(world, hero, prison, helper)
    reach_prison(world, captive_ent, prison)
    free_captive(world, hero, captive_ent, captive_cfg, key)
    outcome = suspense_outcome(prison, helper)
    world.facts["outcome"] = outcome
    world.facts["guardian"] = prison.guardian
    world.facts["quest_succeeded"] = True

    world.para()
    if outcome == "quiet":
        quiet_escape(world, hero, captive_cfg, prison)
    else:
        chase_escape(world, hero, helper, prison, captive_cfg)

    world.para()
    return_and_restore(world, hero, realm, captive_cfg)
    return world


@dataclass
class StoryParams:
    realm: str
    captive: str
    prison: str
    key: str
    helper: str
    hero_name: str
    hero_gender: str
    elder_type: str
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
    "housing": [
        (
            "What does housing mean?",
            "Housing means the homes and shelters where people live. In a village, housing can mean all the houses together."
        )
    ],
    "imprison": [
        (
            "What does imprison mean?",
            "To imprison someone or something means to trap it so it cannot leave. In stories, magic creatures are sometimes imprisoned inside cages, knots, or sealed doors."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey taken for an important reason. Usually someone must travel, face danger, and bring back help."
        )
    ],
    "owl": [
        (
            "Why do stories use an owl as a helper?",
            "Owls are linked with sharp eyes and quiet flight, so they fit stories about watching and warning. A helper like that makes a dangerous path feel more possible."
        )
    ],
    "goat": [
        (
            "Why is a mountain goat a good guide?",
            "A mountain goat is steady on steep rocks and narrow ledges. That makes it a good helper in places where people might slip."
        )
    ],
    "otter": [
        (
            "Why is an otter a good river guide?",
            "An otter knows currents, reeds, and hidden water paths. In a watery place, it can help someone move safely."
        )
    ],
    "rain": [
        (
            "Why do reeds and roofs need rain?",
            "Plants and reeds need water to stay strong and flexible. Without enough good rain, roof bundles can dry out and crack."
        )
    ],
    "hearth": [
        (
            "What is a hearth?",
            "A hearth is the fireplace or warm place in a home where fire burns. In many old stories, the hearth stands for warmth, food, and family life."
        )
    ],
    "sun": [
        (
            "Why is sunlight important for orchards?",
            "Fruit trees need sunlight to grow and ripen well. Warm light also helps a place feel awake and lively."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "housing",
    "imprison",
    "quest",
    "rain",
    "hearth",
    "sun",
    "owl",
    "goat",
    "otter",
]


def generation_prompts(world: World) -> list[str]:
    realm = world.facts["realm_cfg"]
    captive = world.facts["captive_cfg"]
    prison = world.facts["prison_cfg"]
    hero = world.facts["hero"]
    outcome = world.facts["outcome"]
    tone = "tense" if outcome == "chase" else "hushed"
    return [
        f'Write a short myth for ages 3 to 5 that includes the words "imprison" and "housing" and follows a quest to free {captive.label}.',
        f"Tell a {tone} mythic story where {hero.id} travels to {prison.lair} because the village's {realm.housing} is suffering while {captive.label} is trapped.",
        f"Write a gentle suspense story in myth style about a child who must free a helpful spirit so the homes of the village can be safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    realm = world.facts["realm_cfg"]
    captive = world.facts["captive_cfg"]
    prison = world.facts["prison_cfg"]
    key = world.facts["key_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young hero of {realm.place}, and {elder.label_word} who sends {hero.pronoun('object')} on a quest. It is also about {captive.label}, whose gift the village needs."
        ),
        (
            "Why did the hero go on the quest?",
            f"{hero.id} went because the village's {realm.housing} was suffering: {realm.problem}. The people believed this was happening because {captive.label} had been imprisoned and its gift was missing."
        ),
        (
            f"What helper went with {hero.id}?",
            f"{helper.label.capitalize()} went with {hero.id}. It helped by this method: {helper.method}"
        ),
        (
            f"How did {hero.id} free {captive.label}?",
            f"{hero.id} used {key.label} at {prison.label}. That worked because this prison could only be opened in that way, and the seal broke when the right key met it."
        ),
    ]
    if outcome == "quiet":
        qa.append(
            (
                "Was the most dangerous moment noisy or quiet?",
                f"It was quiet. The lair felt frightening, but {helper.label} guided {hero.id} so carefully that {prison.guardian} never truly woke."
            )
        )
    else:
        qa.append(
            (
                "What made the middle of the story suspenseful?",
                f"The suspense came when {prison.guardian} stirred after the prison broke. {hero.id} had to run while {helper.label} guided the way, so the danger felt close even though the quest still succeeded."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the captive returning its gift to the village. {realm.ending_image}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    realm = world.facts["realm_cfg"]
    captive = world.facts["captive_cfg"]
    helper = world.facts["helper_cfg"]
    tags = {"housing", "imprison", "quest", realm.need_tag, helper.id} | set(captive.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} guardian={world.facts.get('guardian')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="reed_delta",
        captive="rain_lark",
        prison="thorn_ring",
        key="moon_sickle",
        helper="owl",
        hero_name="Nara",
        hero_gender="girl",
        elder_type="grandmother",
        trait="steady",
    ),
    StoryParams(
        realm="ash_hill",
        captive="hearth_fox",
        prison="ice_cage",
        key="ember_key",
        helper="goat",
        hero_name="Sorin",
        hero_gender="boy",
        elder_type="grandfather",
        trait="patient",
    ),
    StoryParams(
        realm="sun_orchard",
        captive="sun_stag",
        prison="bronze_latch",
        key="echo_riddle",
        helper="otter",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="priestess",
        trait="quiet",
    ),
    StoryParams(
        realm="reed_delta",
        captive="rain_lark",
        prison="ice_cage",
        key="ember_key",
        helper="otter",
        hero_name="Aren",
        hero_gender="boy",
        elder_type="grandmother",
        trait="brave",
    ),
    StoryParams(
        realm="ash_hill",
        captive="hearth_fox",
        prison="bronze_latch",
        key="echo_riddle",
        helper="owl",
        hero_name="Luma",
        hero_gender="girl",
        elder_type="priestess",
        trait="careful",
    ),
]


def explain_realm_captive(realm: Realm, captive: Captive) -> str:
    return (
        f"(No story: {captive.label} brings {captive.boon}, but {realm.place} needs {realm.need_tag}. "
        f"The village problem and the spirit's gift must fit each other.)"
    )


def explain_prison_key(prison: Prison, key: Key) -> str:
    needed = KEYS[prison.needed_key].label
    return (
        f"(No story: {prison.label} cannot be opened with {key.label}. "
        f"That seal needs {needed}.)"
    )


ASP_RULES = r"""
matches_need(R, C) :- realm(R), captive(C), realm_need(R, N), captive_need(C, N).
opens(P, K) :- prison(P), key(K), prison_key(P, K).
valid(R, C, P, K) :- matches_need(R, C), opens(P, K), realm(R), prison(P).

quiet(H, P) :- helper(H), prison(P), aid(H, A), danger(P, D), A >= D.
chase(H, P) :- helper(H), prison(P), aid(H, A), danger(P, D), A < D.

outcome(quiet) :- chosen_helper(H), chosen_prison(P), quiet(H, P).
outcome(chase) :- chosen_helper(H), chosen_prison(P), chase(H, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, realm in REALMS.items():
        lines.append(asp.fact("realm", rid))
        lines.append(asp.fact("realm_need", rid, realm.need_tag))
    for cid, captive in CAPTIVES.items():
        lines.append(asp.fact("captive", cid))
        lines.append(asp.fact("captive_need", cid, captive.need_tag))
    for pid, prison in PRISONS.items():
        lines.append(asp.fact("prison", pid))
        lines.append(asp.fact("danger", pid, prison.danger))
        lines.append(asp.fact("prison_key", pid, prison.needed_key))
    for kid in KEYS:
        lines.append(asp.fact("key", kid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("aid", hid, helper.aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_prison", params.prison),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {s}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != suspense_outcome(PRISONS[p.prison], HELPERS[p.helper])]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome scenarios differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic suspense quest storyworld. Unspecified choices are randomized from valid combinations."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--captive", choices=CAPTIVES)
    ap.add_argument("--prison", choices=PRISONS)
    ap.add_argument("--key", choices=KEYS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combination set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.captive:
        realm = REALMS[args.realm]
        captive = CAPTIVES[args.captive]
        if not realm_matches_captive(realm, captive):
            raise StoryError(explain_realm_captive(realm, captive))
    if args.prison and args.key:
        prison = PRISONS[args.prison]
        key = KEYS[args.key]
        if not prison_accepts_key(prison, key):
            raise StoryError(explain_prison_key(prison, key))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.captive is None or combo[1] == args.captive)
        and (args.prison is None or combo[2] == args.prison)
        and (args.key is None or combo[3] == args.key)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, captive_id, prison_id, key_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "priestess", "priest"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        realm=realm_id,
        captive=captive_id,
        prison=prison_id,
        key=key_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.captive not in CAPTIVES:
        raise StoryError(f"(Unknown captive: {params.captive})")
    if params.prison not in PRISONS:
        raise StoryError(f"(Unknown prison: {params.prison})")
    if params.key not in KEYS:
        raise StoryError(f"(Unknown key: {params.key})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    realm = REALMS[params.realm]
    captive = CAPTIVES[params.captive]
    prison = PRISONS[params.prison]
    key = KEYS[params.key]
    helper = HELPERS[params.helper]

    if not realm_matches_captive(realm, captive):
        raise StoryError(explain_realm_captive(realm, captive))
    if not prison_accepts_key(prison, key):
        raise StoryError(explain_prison_key(prison, key))

    world = tell(
        realm=realm,
        captive_cfg=captive,
        prison=prison,
        key=key,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, captive, prison, key) combos:\n")
        for realm, captive, prison, key in combos:
            print(f"  {realm:12} {captive:12} {prison:13} {key}")
        print("\nhelper outcomes:\n")
        for hid, helper in sorted(HELPERS.items()):
            outcomes = ", ".join(
                f"{pid}:{suspense_outcome(prison, helper)}" for pid, prison in sorted(PRISONS.items())
            )
            print(f"  {hid:6} {outcomes}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.captive} in {p.prison} for {p.realm} "
                f"({p.helper}, {suspense_outcome(PRISONS[p.prison], HELPERS[p.helper])})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
