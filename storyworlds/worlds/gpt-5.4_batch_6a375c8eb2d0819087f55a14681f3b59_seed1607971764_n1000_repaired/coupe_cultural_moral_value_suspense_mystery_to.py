#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py
==============================================================================

A standalone story world for a small space-adventure mystery: two children ride
a tiny station coupe to a cultural festival, a treasured object goes missing,
and they must solve the mystery without blaming the wrong person.

The world is built around:
- a concrete setting with physical affordances,
- a missing cultural object,
- a plausible cause for its disappearance,
- a fitting way to track it down,
- and a moral turn about patience, fairness, and honesty.

Run it
------
python storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py
python storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py --all
python storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py --qa --json
python storyworlds/worlds/gpt-5.4/coupe_cultural_moral_value_suspense_mystery_to.py --verify
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
IMPULSIVE_TRAITS = {"bold", "hasty", "eager"}


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
    place: str
    sky: str
    festival: str
    opening: str
    detail: str
    recovery_spots: dict[str, str] = field(default_factory=dict)
    supports: set[str] = field(default_factory=set)
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
class HeritageItem:
    id: str
    label: str
    phrase: str
    shine: str
    purpose: str
    clues: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    clue_kind: str
    needs: set[str] = field(default_factory=set)
    move_text: str = ""
    clue_text: str = ""
    hide_text: str = ""
    reveal_text: str = ""
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
    detects: set[str] = field(default_factory=set)
    tool_text: str = ""
    find_text: str = ""
    qa_text: str = ""
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


def _r_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    if ("worry", "item") in world.fired:
        return []
    world.fired.add(("worry", "item"))
    for eid in ("hero", "friend", "keeper"):
        world.get(eid).memes["worry"] += 1
    return ["__worry__"]


def _r_fairness(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["blame"] < THRESHOLD:
        return []
    if ("fairness", "hero") in world.fired:
        return []
    world.fired.add(("fairness", "hero"))
    hero.memes["guilt"] += 1
    world.get("friend").memes["hurt"] += 1
    return ["__blame__"]


def _r_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    if ("relief", "item") in world.fired:
        return []
    world.fired.add(("relief", "item"))
    for eid in ("hero", "friend", "keeper"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["worry"] = 0.0
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="fairness", tag="social", apply=_r_fairness),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def cause_possible(setting: Setting, item: HeritageItem, cause: Cause) -> bool:
    return cause.needs.issubset(setting.supports) and cause.clue_kind in item.clues


def method_works(cause: Cause, method: Method) -> bool:
    return cause.clue_kind in method.detects


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for cid, cause in CAUSES.items():
                if not cause_possible(setting, item, cause):
                    continue
                for mid, method in METHODS.items():
                    if method_works(cause, method):
                        combos.append((sid, iid, cid, mid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "apology" if params.trait in IMPULSIVE_TRAITS else "calm"


def predict_missing(world: World, cause: Cause, method: Method) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["missing"] = 1.0
    item.meters["moved"] = 1.0
    sim.facts["clue_kind"] = cause.clue_kind
    sim.facts["recovery_spot"] = sim.setting.recovery_spots[cause.id]
    propagate(sim, narrate=False)
    can_find = method_works(cause, method)
    if can_find:
        item.meters["found"] = 1.0
        propagate(sim, narrate=False)
    return {
        "can_find": can_find,
        "spot": sim.setting.recovery_spots[cause.id],
        "clue_kind": cause.clue_kind,
    }


def introduce(world: World, hero: Entity, friend: Entity, keeper: Entity, item: HeritageItem) -> None:
    coupe = world.get("coupe")
    for eid in ("hero", "friend"):
        world.get(eid).memes["wonder"] += 1
    world.say(
        f"{world.setting.opening} {hero.id} and {friend.id} rode with {keeper.label_word} "
        f"in a little silver coupe that hummed through the station tunnels."
    )
    world.say(
        f"Outside the windows, {world.setting.sky}. Inside the dome, {world.setting.festival} "
        f"was almost ready, and everyone wanted the evening to be perfect."
    )
    world.say(
        f"{keeper.id} was carrying {item.phrase}, a cultural treasure used to {item.purpose}. "
        f"It {item.shine} as the coupe rolled to a stop."
    )
    coupe.meters["parked"] = 1.0


def handoff(world: World, hero: Entity, friend: Entity, keeper: Entity, item: HeritageItem) -> None:
    hero.memes["responsibility"] += 1
    friend.memes["care"] += 1
    world.say(
        f'"Stay close while I open the display case," {keeper.id} said. '
        f'{hero.id} and {friend.id} stood beside the velvet stand and watched.'
    )
    world.say(world.setting.detail)


def disappearance(world: World, hero: Entity, friend: Entity, keeper: Entity, item_cfg: HeritageItem, cause: Cause) -> None:
    item = world.get("item")
    item.meters["missing"] = 1.0
    item.meters["moved"] = 1.0
    world.facts["clue_kind"] = cause.clue_kind
    world.facts["recovery_spot"] = world.setting.recovery_spots[cause.id]
    propagate(world, narrate=False)
    world.say(
        f"Then the lights blinked for one tiny breath, and when they steadied again, "
        f"{item_cfg.phrase} was gone."
    )
    world.say(
        f"For a moment the whole dome felt huge and quiet. {keeper.id} looked at the empty stand, "
        f"and {hero.id}'s heart thumped hard inside {hero.pronoun('possessive')} suit."
    )


def suspicion(world: World, hero: Entity, friend: Entity, item_cfg: HeritageItem) -> None:
    hero.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} swallowed and whispered, "Did someone take the {item_cfg.label}? '
        f'Did you see anything, {friend.id}?"'
    )
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head, but the question still stung. "
        f"The mystery suddenly felt colder than the air vents."
    )


def steady_friend(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    friend.memes["patience"] += 1
    hero.memes["patience"] += 1
    world.say(
        f'"Wait," {friend.id} said softly. "Let\'s look first. {cause.clue_text}"'
    )


def investigate(world: World, hero: Entity, friend: Entity, keeper: Entity, cause: Cause, method: Method) -> None:
    world.say(
        f"{keeper.id} knelt between them and nodded. "
        f'"Good explorers check clues before they blame people," {keeper.pronoun()} said.'
    )
    world.say(
        f"Using {method.tool_text}, they searched the floor, the rails, and the dark corners of the dome."
    )
    world.say(method.find_text.format(
        hero=hero.id,
        friend=friend.id,
        keeper=keeper.id,
        clue=cause.hide_text,
        spot=world.setting.recovery_spots[cause.id],
    ))


def recover(world: World, hero: Entity, friend: Entity, keeper: Entity, item_cfg: HeritageItem, cause: Cause) -> None:
    item = world.get("item")
    item.meters["found"] = 1.0
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        cause.reveal_text.format(
            item=item_cfg.label,
            spot=world.setting.recovery_spots[cause.id],
            keeper=keeper.id,
        )
    )
    world.say(
        f"{keeper.id} lifted the {item_cfg.label} carefully with both hands. "
        f"At once, the tight feeling in the dome began to loosen."
    )


def apology(world: World, hero: Entity, friend: Entity, keeper: Entity) -> None:
    hero.memes["honesty"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{hero.id} looked at {friend.id} and lowered {hero.pronoun("possessive")} eyes. '
        f'"I am sorry I sounded like I blamed you," {hero.pronoun()} said. '
        f'"I was scared and I spoke too fast."'
    )
    world.say(
        f'{friend.id} gave a small nod. "{keeper.label_word.capitalize()} was right," '
        f'{friend.pronoun()} said. "Clues first."'
    )


def calm_lesson(world: World, hero: Entity, friend: Entity, keeper: Entity) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f'{hero.id} let out a long breath. "I am glad we checked the clues," '
        f'{hero.pronoun()} said.'
    )
    world.say(
        f'{keeper.id} smiled. "That is how trust grows," {keeper.pronoun()} said. '
        f'"A calm mind can solve a mystery that fear only tangles."'
    )


def closing(world: World, hero: Entity, friend: Entity, keeper: Entity, item_cfg: HeritageItem) -> None:
    for eid in ("hero", "friend"):
        world.get(eid).memes["joy"] += 1
    world.say(
        f"Soon the music began, the lantern strings glowed, and {item_cfg.phrase} was placed safely in the center of the festival."
    )
    world.say(
        f"{hero.id} and {friend.id} stood beside the little coupe and watched families gather under the dome. "
        f"The station no longer felt haunted by a missing secret. It felt bright, brave, and fair."
    )
def tell(
    item_cfg: Item,
    cause: Cause,
    method: Method,
    hero_name: str,
    hero_type: HeroType,
    friend_name: str,
    friend_type: FriendType,
    keeper_type: KeeperType,
    trait: Trait,
    setting=None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        role="friend",
        traits=["patient"],
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=keeper_type,
        role="keeper",
        label="the keeper",
    ))
    world.add(Entity(id="coupe", type="rover", label="coupe"))
    world.add(Entity(id="item", type="artifact", label=item_cfg.label))
    world.facts["clue_kind"] = ""
    world.facts["recovery_spot"] = ""
    world.facts["predicted"] = predict_missing(world, cause, method)

    introduce(world, hero, friend, keeper, item_cfg)
    handoff(world, hero, friend, keeper, item_cfg)

    world.para()
    disappearance(world, hero, friend, keeper, item_cfg, cause)

    if trait in IMPULSIVE_TRAITS:
        suspicion(world, hero, friend, item_cfg)
    steady_friend(world, hero, friend, cause)

    world.para()
    investigate(world, hero, friend, keeper, cause, method)
    recover(world, hero, friend, keeper, item_cfg, cause)

    world.para()
    if trait in IMPULSIVE_TRAITS:
        apology(world, hero, friend, keeper)
    else:
        calm_lesson(world, hero, friend, keeper)
    closing(world, hero, friend, keeper, item_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        keeper=keeper,
        item_cfg=item_cfg,
        cause=cause,
        method=method,
        setting=setting,
        blamed=hero.memes["blame"] >= THRESHOLD,
        found=True,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            item=item_cfg.id,
            cause=cause.id,
            method=method.id,
            hero_name=hero_name,
            hero_type=hero_type,
            friend_name=friend_name,
            friend_type=friend_type,
            keeper_type=keeper_type,
            trait=trait,
            seed=None,
        )),
    )
    return world
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


SETTINGS = {
    "moon_dome": Setting(
        id="moon_dome",
        place="the Moon Glass Dome",
        sky="the black sky was full of tiny white stars and slow blue cargo ships",
        festival="the station's cultural night market with music from many worlds",
        opening="On the moon station Selene Ring,",
        detail="Silk banners drifted in the gentle air, and every stall held stories from faraway homes.",
        recovery_spots={
            "vent_drift": "the silver air grate behind the stage",
            "service_drone": "the quiet cleaning bay under the stair ramp",
            "static_seat": "the back seat seam of the parked coupe",
        },
        supports={"vent", "drone", "static"},
        tags={"moon", "festival"},
    ),
    "mars_terrace": Setting(
        id="mars_terrace",
        place="the Red Terrace Hall",
        sky="Mars glowed outside the dome like a red ember under the stars",
        festival="the colony's cultural supper and star-song celebration",
        opening="High above Mars,",
        detail="Warm spice smells floated from the food tables, and soft drumbeats tapped along the railings.",
        recovery_spots={
            "vent_drift": "the warm vent grille beside the song platform",
            "service_drone": "the supply alcove behind the tapestry wall",
            "static_seat": "the storage pocket of the little coupe",
        },
        supports={"vent", "drone", "static"},
        tags={"mars", "festival"},
    ),
    "ring_museum": Setting(
        id="ring_museum",
        place="the Aurora Ring Museum",
        sky="the bright ring of the station curved outside like a silver river",
        festival="the museum's cultural welcome for new families from many planets",
        opening="Inside the Aurora Ring,",
        detail="Children hurried past glowing maps, and old songs played softly from hidden speakers.",
        recovery_spots={
            "vent_drift": "the narrow grate under the map table",
            "service_drone": "the polishing nook by the artifact lift",
            "static_seat": "the cushion pocket in the museum coupe",
        },
        supports={"vent", "drone", "static"},
        tags={"museum", "festival"},
    ),
}

ITEMS = {
    "star_lantern": HeritageItem(
        id="star_lantern",
        label="star lantern",
        phrase="the glass star lantern",
        shine="glimmered with warm gold points",
        purpose="lead the first song of welcome",
        clues={"air_thread", "foam_sparkle", "magnet_dust"},
        tags={"lantern", "cultural"},
    ),
    "song_shell": HeritageItem(
        id="song_shell",
        label="song shell",
        phrase="the spiral song shell",
        shine="shone blue and pink like trapped dawn",
        purpose="start the elders' listening circle",
        clues={"foam_sparkle", "magnet_dust"},
        tags={"shell", "cultural"},
    ),
    "ribbon_mask": HeritageItem(
        id="ribbon_mask",
        label="ribbon mask",
        phrase="the ribbon mask",
        shine="flickered with tiny mirrored stars",
        purpose="open the dance of names",
        clues={"air_thread", "foam_sparkle"},
        tags={"mask", "cultural"},
    ),
}

CAUSES = {
    "vent_drift": Cause(
        id="vent_drift",
        clue_kind="air_thread",
        needs={"vent"},
        move_text="A sneaky pull of station air had lifted it away.",
        clue_text="The ribbons are all leaning one way. Air does not lie.",
        hide_text="a single ribbon thread fluttering toward a vent",
        reveal_text="Behind {spot}, the missing {item} trembled softly, held in place by the steady pull of air.",
        tags={"air", "mystery"},
    ),
    "service_drone": Cause(
        id="service_drone",
        clue_kind="foam_sparkle",
        needs={"drone"},
        move_text="A cleaning drone had mistaken it for something left out.",
        clue_text="Look for cleaning foam or wheel marks. Machines leave habits behind.",
        hide_text="a curl of cleaning foam and tiny wheel tracks",
        reveal_text="In {spot}, {keeper} found the missing {item}, tucked beside a sleeping service drone that had carried it away by mistake.",
        tags={"robot", "mystery"},
    ),
    "static_seat": Cause(
        id="static_seat",
        clue_kind="magnet_dust",
        needs={"static"},
        move_text="A crackle of static had tugged it onto the coupe's seat seam.",
        clue_text="See that bright dust? Static sometimes snatches light things and hides them nearby.",
        hide_text="a line of bright magnetic dust leading back toward the coupe",
        reveal_text="When they checked {spot}, the missing {item} was stuck there, crackling very softly with static.",
        tags={"static", "mystery"},
    ),
}

METHODS = {
    "scan_goggles": Method(
        id="scan_goggles",
        detects={"air_thread", "foam_sparkle"},
        tool_text="the keeper's scan goggles",
        find_text="{hero} borrowed the scan goggles, and soon {friend} pointed to {clue}. They followed it all the way to {spot}.",
        qa_text="They used scan goggles to notice the clue and followed it carefully.",
        tags={"scanner"},
    ),
    "dust_lamp": Method(
        id="dust_lamp",
        detects={"magnet_dust", "foam_sparkle"},
        tool_text="a violet dust lamp",
        find_text="Under the violet lamp, {friend} spotted {clue}. Step by step, the glowing trail led the three explorers to {spot}.",
        qa_text="They shone a dust lamp on the floor so the hidden trail became visible.",
        tags={"lamp"},
    ),
    "breeze_map": Method(
        id="breeze_map",
        detects={"air_thread"},
        tool_text="the dome's little breeze map screen",
        find_text="{keeper} opened the breeze map screen, and {hero} matched the arrows to {clue}. That sent them hurrying toward {spot}.",
        qa_text="They checked the station's breeze map and matched it to the moving clue.",
        tags={"map"},
    ),
}

GIRL_NAMES = ["Nia", "Tala", "Mira", "Suri", "Ivy", "Luma", "Zea", "Ari"]
BOY_NAMES = ["Orin", "Kai", "Jem", "Rafi", "Sol", "Milo", "Taro", "Lev"]
TRAITS = ["careful", "patient", "thoughtful", "bold", "hasty", "eager"]


KNOWLEDGE = {
    "cultural": [
        (
            "What does cultural mean?",
            "Cultural means something that belongs to the shared ways, stories, music, art, or celebrations of a group of people. A cultural object can help people remember where they come from and what matters to them."
        )
    ],
    "air": [
        (
            "Can moving air carry light things away?",
            "Yes. If something is very light, a strong stream of air can push or pull it into a corner or against a vent."
        )
    ],
    "robot": [
        (
            "What is a service drone?",
            "A service drone is a little robot that helps with jobs like cleaning or carrying things. Robots follow rules, so they can make mistakes if something looks like it is out of place."
        )
    ],
    "static": [
        (
            "What is static electricity?",
            "Static electricity is a tiny charge that can build up on surfaces. It can make light objects cling or crackle for a moment."
        )
    ],
    "scanner": [
        (
            "What do scan goggles do?",
            "Scan goggles help someone notice small details that are hard to see with bare eyes. In stories, they are useful for solving mysteries because clues can be tiny."
        )
    ],
    "lamp": [
        (
            "Why would a special lamp help in a mystery?",
            "A special lamp can make dust, prints, or marks glow more clearly. That helps explorers follow a trail instead of guessing."
        )
    ],
    "map": [
        (
            "What is a breeze map?",
            "A breeze map shows how air is moving through a place. It helps people understand where light cloth or dust might drift."
        )
    ],
    "fairness": [
        (
            "Why is it important not to blame someone too fast?",
            "It is important because fear can make people guess before they know the truth. Fairness means slowing down, checking the facts, and treating people kindly."
        )
    ],
}
KNOWLEDGE_ORDER = ["cultural", "fairness", "air", "robot", "static", "scanner", "lamp", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    item = f["item_cfg"]
    cause = f["cause"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "coupe" and "cultural", and centers on a missing {item.label}.',
        f"Tell a gentle mystery where {hero.id} and {friend.id} arrive at {setting.place} in a little coupe, discover that a cultural treasure is missing, and solve the puzzle by following clues.",
        f"Write a child-friendly suspense story where the danger is not a monster but a wrong guess, and the lesson is to be fair, patient, and honest while solving how {cause.move_text.lower()}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    keeper = f["keeper"]
    item = f["item_cfg"]
    cause = f["cause"]
    method = f["method"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two young space explorers, and {keeper.label_word} the keeper. They go to {setting.place} for a cultural celebration."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered because it was used to {item.purpose}."
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because the treasured object vanished just as the celebration was about to begin. The quiet dome, the empty stand, and the fear of not knowing what happened made everyone feel tense."
        ),
        (
            "How did they solve the mystery?",
            f"{method.qa_text} That clue showed them that {cause.move_text.lower()}, so they searched the right place instead of guessing."
        ),
    ]
    if f["blamed"]:
        qa.append(
            (
                f"Why did {hero.id} apologize?",
                f"{hero.id} apologized because fear made {hero.pronoun('object')} speak too fast and sound as if {hero.pronoun()} blamed {friend.id}. After the clues revealed the truth, {hero.pronoun()} chose honesty and repaired the hurt."
            )
        )
    else:
        qa.append(
            (
                f"What moral lesson did {hero.id} learn?",
                f"{hero.id} learned that a calm mind helps solve problems fairly. Instead of guessing, {hero.pronoun()} checked the clues and trusted the truth to lead the way."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the missing {item.label} safely returned to the festival. The bright ending showed that patience and fairness brought the celebration back to life."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cultural", "fairness"} | set(f["cause"].tags) | set(f["method"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if world.facts.get("recovery_spot"):
        lines.append(f"  recovery_spot: {world.facts['recovery_spot']}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    method: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    keeper_type: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="moon_dome",
        item="star_lantern",
        cause="vent_drift",
        method="breeze_map",
        hero_name="Nia",
        hero_type="girl",
        friend_name="Orin",
        friend_type="boy",
        keeper_type="mother",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="mars_terrace",
        item="song_shell",
        cause="service_drone",
        method="dust_lamp",
        hero_name="Kai",
        hero_type="boy",
        friend_name="Mira",
        friend_type="girl",
        keeper_type="father",
        trait="bold",
        seed=None,
    ),
    StoryParams(
        setting="ring_museum",
        item="star_lantern",
        cause="static_seat",
        method="dust_lamp",
        hero_name="Luma",
        hero_type="girl",
        friend_name="Sol",
        friend_type="boy",
        keeper_type="mother",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        setting="moon_dome",
        item="ribbon_mask",
        cause="service_drone",
        method="scan_goggles",
        hero_name="Taro",
        hero_type="boy",
        friend_name="Ivy",
        friend_type="girl",
        keeper_type="father",
        trait="hasty",
        seed=None,
    ),
    StoryParams(
        setting="mars_terrace",
        item="ribbon_mask",
        cause="vent_drift",
        method="scan_goggles",
        hero_name="Suri",
        hero_type="girl",
        friend_name="Lev",
        friend_type="boy",
        keeper_type="mother",
        trait="patient",
        seed=None,
    ),
]


def explain_rejection(setting: Setting, item: HeritageItem, cause: Cause, method: Method) -> str:
    if not cause_possible(setting, item, cause):
        if not cause.needs.issubset(setting.supports):
            need = ", ".join(sorted(cause.needs))
            have = ", ".join(sorted(setting.supports))
            return (
                f"(No story: {setting.place} supports [{have}], but cause '{cause.id}' needs [{need}]. "
                f"The mystery must use a cause the setting can really produce.)"
            )
        return (
            f"(No story: the {item.label} does not leave the kind of clue needed for cause '{cause.id}'. "
            f"Pick an item and cause that fit each other physically.)"
        )
    if not method_works(cause, method):
        return (
            f"(No story: method '{method.id}' cannot detect the clue for cause '{cause.id}'. "
            f"The children need a way to find the real trail, not just guess.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
possible_cause(S, I, C) :- setting(S), item(I), cause(C),
                           supports_all(S, C),
                           item_has_clue_for(I, C).
works(C, M) :- cause(C), method(M), cause_clue(C, K), detects(M, K).
valid(S, I, C, M) :- possible_cause(S, I, C), works(C, M).

impulsive(T) :- trait(T), impulsive_trait(T).
outcome(apology) :- impulsive(_).
outcome(calm) :- not impulsive(_).

supports_all(S, C) :- not missing_need(S, C).
missing_need(S, C) :- cause_needs(C, Need), not setting_supports(S, Need).

item_has_clue_for(I, C) :- cause_clue(C, K), item_clue(I, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for support in sorted(setting.supports):
            lines.append(asp.fact("setting_supports", sid, support))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for clue in sorted(item.clues):
            lines.append(asp.fact("item_clue", iid, clue))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_clue", cid, cause.clue_kind))
        for need in sorted(cause.needs):
            lines.append(asp.fact("cause_needs", cid, need))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for clue in sorted(method.detects):
            lines.append(asp.fact("detects", mid, clue))
    for trait in sorted(IMPULSIVE_TRAITS):
        lines.append(asp.fact("impulsive_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    a_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if a_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(a_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in clingo:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in python:", sorted(p_set - a_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
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
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space-adventure cultural mystery in which a missing treasure is found by clue-following and fairness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--keeper-type", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.cause and args.method:
        if (args.setting, args.item, args.cause, args.method) not in set(valid_combos()):
            raise StoryError(explain_rejection(
                SETTINGS[args.setting], ITEMS[args.item], CAUSES[args.cause], METHODS[args.method]
            ))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, cause_id, method_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    keeper_type = args.keeper_type or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        keeper_type=keeper_type,
        trait=trait,
        seed=None,
    )


def _checked_lookup(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    setting = _checked_lookup(SETTINGS, params.setting, "setting")
    item = _checked_lookup(ITEMS, params.item, "item")
    cause = _checked_lookup(CAUSES, params.cause, "cause")
    method = _checked_lookup(METHODS, params.method, "method")
    if (params.setting, params.item, params.cause, params.method) not in set(valid_combos()):
        raise StoryError(explain_rejection(setting, item, cause, method))

    world = tell(
        setting=setting,
        item_cfg=item,
        cause=cause,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        keeper_type=params.keeper_type,
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
        print(f"{len(combos)} compatible (setting, item, cause, method) combos:\n")
        for setting, item, cause, method in combos:
            print(f"  {setting:12} {item:13} {cause:13} {method}")
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
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.item} at {p.setting} "
                f"({p.cause}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
