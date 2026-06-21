#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py
============================================================

A standalone story world for a tiny mythic tale: a child carries one gift to a
sacred spring, the water answers with a surprise duplicate, and the child must
learn what to do with an unexpected blessing.

The governing common-sense constraint is simple and physical: only some offerings
belong in the Spring of Second Ripples, and only some carriers can safely hold
the sudden duplicate that rises from the water. The story is not a frozen
template; the spring, the duplicate, the child's burden, the waking spirit, and
the ending all come from simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py --offering fig --carrier basket
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py --carrier cup
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py --all
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/splish_duplicate_surprise_myth.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"goddess": "goddess", "spirit": "spirit"}.get(self.type, self.label or self.type)
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
    path: str
    water: str
    shrine: str
    closing: str
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
class Offering:
    id: str
    label: str
    phrase: str
    size: int
    wildness: int
    duplicateable: bool
    miracle: str
    ending_image: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    max_size: int
    hold_text: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    stable_text: str
    fade_text: str
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


def _r_duplicate_wakes_spirit(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("gift")
    hero = world.get("hero")
    spring = world.get("spring")
    if item.meters["duplicated"] < THRESHOLD:
        return out
    sig = ("wake", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.meters["singing"] += 1
    hero.memes["wonder"] += 1
    hero.memes["surprise"] += 1
    out.append("__wake__")
    return out


def _r_heavy_load_brings_danger(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    bridge = world.get("bridge")
    if hero.meters["burden"] < THRESHOLD:
        return out
    sig = ("danger", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.meters["swaying"] += 1
    hero.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_greed_stirs_unrest(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("gift")
    if hero.memes["greed"] < THRESHOLD or item.meters["duplicated"] < THRESHOLD:
        return out
    sig = ("unrest", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["unstable"] += 1
    out.append("__unrest__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="duplicate_wakes_spirit", tag="mythic", apply=_r_duplicate_wakes_spirit),
    Rule(name="heavy_load_brings_danger", tag="physical", apply=_r_heavy_load_brings_danger),
    Rule(name="greed_stirs_unrest", tag="moral", apply=_r_greed_stirs_unrest),
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


def can_duplicate(offering: Offering) -> bool:
    return offering.duplicateable


def carrier_fits(carrier: Carrier, offering: Offering) -> bool:
    return carrier.capacity >= 2 and carrier.max_size >= offering.size


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid, offering in OFFERINGS.items():
            for cid, carrier in CARRIERS.items():
                if can_duplicate(offering) and carrier_fits(carrier, offering):
                    combos.append((sid, oid, cid))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    offering = OFFERINGS[params.offering]
    return "stable" if response.power >= offering.wildness else "fading"


def predict_surprise(world: World) -> dict:
    sim = world.copy()
    gift = sim.get("gift")
    hero = sim.get("hero")
    _make_duplicate(sim, gift, hero, narrate=False)
    return {
        "duplicate": gift.meters["duplicated"] >= THRESHOLD,
        "danger": sim.get("bridge").meters["swaying"] >= THRESHOLD,
        "unstable": gift.meters["unstable"] >= THRESHOLD,
    }


def _make_duplicate(world: World, gift: Entity, hero: Entity, narrate: bool = True) -> None:
    gift.meters["duplicated"] += 1
    gift.meters["count"] += 1
    hero.meters["burden"] += 1
    hero.memes["greed"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, setting: Setting, offering: Offering, carrier: Carrier) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In the old days, when springs still listened and hills still remembered names, "
        f"{hero.id} climbed {setting.path} with {carrier.phrase}. Inside lay {offering.phrase}, "
        f"meant for {setting.shrine}."
    )
    world.say(
        f"The elders said that the water there answered kind gifts with signs, but never in the same "
        f"way twice."
    )


def arrive(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"At last {hero.id} reached {setting.place}. {setting.water.capitalize()} lay smooth as blue glass, "
        f"and the small shrine beside it waited in the hush of morning."
    )


def dip_gift(world: World, hero: Entity, offering: Offering) -> None:
    world.say(
        f"{hero.id} bent over the spring and lowered {offering.phrase} until the water kissed it. "
        f"Then came a tiny sound: splish."
    )


def surprise_duplicate(world: World, hero: Entity, offering: Offering) -> None:
    gift = world.get("gift")
    _make_duplicate(world, gift, hero)
    world.say(
        f"A second {offering.label} rose shining beside the first, a bright duplicate cradled on two ripples. "
        f"{hero.id} gasped, for {offering.miracle}."
    )


def warning(world: World, hero: Entity, spirit: Entity, offering: Offering, carrier: Carrier) -> None:
    pred = predict_surprise(world)
    world.facts["predicted_duplicate"] = pred["duplicate"]
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_unstable"] = pred["unstable"]
    extra = ""
    if pred["danger"]:
        extra = f" The extra gift made {carrier.label} suddenly heavy, and even the bridge stones had begun to think about moving."
    world.say(
        f'From the reeds rose {spirit.label}, with water shining on {spirit.pronoun("possessive")} hair. '
        f'"Child," {spirit.pronoun()} said, "the spring has surprised you with a second blessing, but not every blessing is meant to be pocketed."{extra}'
    )


def grab_both(world: World, hero: Entity, carrier: Carrier, offering: Offering) -> None:
    hero.memes["greed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id}, amazed and a little greedy, tucked both {offering.label}s into {carrier.phrase}. "
        f"{carrier.hold_text} and pulled at {hero.pronoun('possessive')} shoulder."
    )


def crossing(world: World, hero: Entity) -> None:
    if world.get("bridge").meters["swaying"] >= THRESHOLD:
        world.say(
            f"When {hero.id} stepped onto the stone bridge, it gave a low shiver under {hero.pronoun('possessive')} feet. "
            f"Wonder turned to worry, and {hero.pronoun()} slowed."
        )


def counsel(world: World, hero: Entity, spirit: Entity, response: Response) -> None:
    world.say(
        f'{spirit.label} drifted beside the bank and spoke again. "{response.text}" '
        f'{hero.id} listened then, because the spring no longer sounded playful. It sounded wise.'
    )


def resolve_stable(world: World, hero: Entity, setting: Setting, offering: Offering, response: Response) -> None:
    hero.memes["relief"] += 1
    hero.memes["generosity"] += 1
    hero.memes["greed"] = 0.0
    world.get("gift").meters["unstable"] = 0.0
    world.get("bridge").meters["swaying"] = 0.0
    world.get("shrine").meters["blessing"] += 1
    world.say(response.stable_text.format(place=setting.shrine, item=offering.label))
    world.say(
        f"At once the ripples quieted. The second gift felt light and right in the world, and the path home no longer trembled."
    )


def resolve_fading(world: World, hero: Entity, setting: Setting, offering: Offering, response: Response) -> None:
    hero.memes["relief"] += 1
    hero.memes["sadness"] += 1
    hero.memes["greed"] = 0.0
    world.get("gift").meters["unstable"] += 1
    world.get("bridge").meters["swaying"] = 0.0
    world.get("gift").meters["faded"] += 1
    world.say(response.fade_text.format(place=setting.shrine, item=offering.label))
    world.say(
        f"The duplicate melted back into silver drops before it could be kept. Yet the first gift remained warm in {hero.pronoun('possessive')} hands, as if the spring had spared one lesson and one blessing."
    )


def ending(world: World, hero: Entity, setting: Setting, offering: Offering, outcome: str) -> None:
    if outcome == "stable":
        world.say(
            f"So the tale says that {hero.id} reached {setting.shrine} with a humble heart, and from that day on people remembered that a surprise gift should be shared before it is claimed."
        )
        world.say(
            f"At dusk, {offering.ending_image}, and {setting.closing}."
        )
    else:
        world.say(
            f"So the tale says that {hero.id} learned a gentler truth: the spring would not punish a child for being startled, but it would not let greed carry home what was never meant to be hoarded."
        )
        world.say(
            f"At dusk, one true {offering.label} rested at {setting.shrine}, and {setting.closing}."
        )


def tell(
    setting: Setting,
    offering: Offering,
    carrier: Carrier,
    response: Response,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    spirit = world.add(Entity(id="spirit", kind="character", type="goddess", label="the Reed Mother", role="guide"))
    gift = world.add(Entity(id="gift", kind="thing", type="offering", label=offering.label, attrs={"count": 1}))
    bridge = world.add(Entity(id="bridge", kind="thing", type="bridge", label="the bridge"))
    shrine = world.add(Entity(id="shrine", kind="thing", type="shrine", label=setting.shrine))
    spring = world.add(Entity(id="spring", kind="thing", type="spring", label=setting.water))

    hero.id = hero_name
    world.entities[hero_name] = world.entities.pop("hero")
    gift.meters["count"] = 1.0
    gift.meters["duplicated"] = 0.0
    gift.meters["unstable"] = 0.0
    gift.meters["faded"] = 0.0
    bridge.meters["swaying"] = 0.0
    shrine.meters["blessing"] = 0.0
    spring.meters["singing"] = 0.0
    hero.meters["burden"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["greed"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["surprise"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["generosity"] = 0.0
    hero.memes["sadness"] = 0.0
    hero.memes["hope"] = 0.0

    world.facts.update(
        setting=setting,
        offering=offering,
        carrier=carrier,
        response=response,
        hero=hero,
        spirit=spirit,
    )

    opening(world, hero, setting, offering, carrier)
    arrive(world, hero, setting)

    world.para()
    dip_gift(world, hero, offering)
    surprise_duplicate(world, hero, offering)
    warning(world, hero, spirit, offering, carrier)
    grab_both(world, hero, carrier, offering)
    crossing(world, hero)

    world.para()
    counsel(world, hero, spirit, response)
    outcome = "stable" if response.power >= offering.wildness else "fading"
    if outcome == "stable":
        resolve_stable(world, hero, setting, offering, response)
    else:
        resolve_fading(world, hero, setting, offering, response)

    world.para()
    ending(world, hero, setting, offering, outcome)

    world.facts.update(
        outcome=outcome,
        duplicate=world.get("gift").meters["duplicated"] >= THRESHOLD,
        danger=world.get("bridge").meters["swaying"] >= THRESHOLD,
        burden=world.get(hero.id).meters["burden"],
        blessing=world.get("shrine").meters["blessing"] >= THRESHOLD,
        faded=world.get("gift").meters["faded"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "reed_pool": Setting(
        id="reed_pool",
        place="the Pool of Second Ripples",
        path="the path of white stones above the reeds",
        water="the green spring",
        shrine="the Dawn Shrine",
        closing="the reeds sang softly as if they had heard the whole thing",
        tags={"myth", "spring"},
    ),
    "moon_ford": Setting(
        id="moon_ford",
        place="the Moon Ford",
        path="the silver path above the stream",
        water="the moon-bright water",
        shrine="the Shrine of First Light",
        closing="the stream kept one star trembling on its back",
        tags={"myth", "moon"},
    ),
    "laurel_basin": Setting(
        id="laurel_basin",
        place="the Laurel Basin",
        path="the narrow laurel path along the hill",
        water="the laurel spring",
        shrine="the Hill Shrine",
        closing="laurel leaves clicked together like tiny green bells",
        tags={"myth", "hill"},
    ),
}

OFFERINGS = {
    "fig": Offering(
        id="fig",
        label="fig",
        phrase="a ripe fig wrapped in a leaf",
        size=1,
        wildness=2,
        duplicateable=True,
        miracle="the spring had answered with sweetness for sweetness",
        ending_image="two figs glowed on the shrine step like small purple lamps",
        tags={"fig", "food", "duplicate"},
    ),
    "honey_cake": Offering(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake scented with thyme",
        size=2,
        wildness=2,
        duplicateable=True,
        miracle="the air itself smelled suddenly of warm ovens and beeswax",
        ending_image="the honey cakes shone amber in the last light",
        tags={"cake", "food", "duplicate"},
    ),
    "shell": Offering(
        id="shell",
        label="shell",
        phrase="a blue river shell polished by careful hands",
        size=1,
        wildness=3,
        duplicateable=True,
        miracle="the water flashed inside both shells as if a small river had been folded into each one",
        ending_image="two shells held the sunset in their blue curves",
        tags={"shell", "river", "duplicate"},
    ),
    "flute": Offering(
        id="flute",
        label="reed flute",
        phrase="a little reed flute bound with red thread",
        size=2,
        wildness=3,
        duplicateable=True,
        miracle="two notes hung in the air where only one had been played",
        ending_image="two reed flutes lay across the altar like sleeping birds",
        tags={"flute", "music", "duplicate"},
    ),
    "bronze_coin": Offering(
        id="bronze_coin",
        label="bronze coin",
        phrase="an old bronze coin from the market road",
        size=1,
        wildness=1,
        duplicateable=False,
        miracle="",
        ending_image="",
        tags={"coin"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a willow basket",
        capacity=2,
        max_size=2,
        hold_text="The basket creaked with the new weight",
        tags={"basket"},
    ),
    "apron": Carrier(
        id="apron",
        label="apron fold",
        phrase="the fold of a clean apron",
        capacity=2,
        max_size=1,
        hold_text="The apron fold sagged and tugged at the stitching",
        tags={"apron"},
    ),
    "satchel": Carrier(
        id="satchel",
        label="satchel",
        phrase="a stitched goat-hide satchel",
        capacity=2,
        max_size=2,
        hold_text="The satchel bumped against the child's side with a serious thump",
        tags={"satchel"},
    ),
    "cup": Carrier(
        id="cup",
        label="clay cup",
        phrase="a clay cup carried in both hands",
        capacity=1,
        max_size=1,
        hold_text="The cup was already full",
        tags={"cup"},
    ),
}

RESPONSES = {
    "shrine_share": Response(
        id="shrine_share",
        sense=3,
        power=3,
        text="Carry one gift to the shrine and leave the other for the hungry traveler who comes after you.",
        stable_text="{item!s} in one hand and its twin in the other, the child walked to {place} and left one as an offering and one as a gift for the next pilgrim.",
        fade_text="The child hurried to {place} and tried to promise one {item} away there, but the spring's second gift had already begun to loosen into mist.",
        qa_text="shared the surprise by leaving one gift at the shrine and one for someone else",
        tags={"share", "shrine"},
    ),
    "return_one": Response(
        id="return_one",
        sense=2,
        power=2,
        text="If your heart is too startled to share, return one copy to the water and keep only what you brought in truth.",
        stable_text="The child knelt by the bank, thanked the spring, and laid one {item} back upon the water before carrying the other toward {place}.",
        fade_text="The child tried to return one {item} to the spring, but the duplicate dissolved first, leaving only circles on the water before the child turned toward {place}.",
        qa_text="returned one copy to the spring and kept only the true gift",
        tags={"return", "spring"},
    ),
    "sing_thanks": Response(
        id="sing_thanks",
        sense=2,
        power=3,
        text="Name the surprise aloud, sing thanks, and then choose with open hands instead of greedy hands.",
        stable_text="The child sang thanks to the spring, chose gently, and carried the gifts onward in peace to {place}.",
        fade_text="The child sang thanks, but too late; the second {item} had already thinned to drops before the road to {place} could be taken.",
        qa_text="sang thanks and chose with open hands instead of grabbing",
        tags={"song", "thanks"},
    ),
    "hide_copy": Response(
        id="hide_copy",
        sense=1,
        power=1,
        text="Hide the second gift under your cloak before the spirit sees.",
        stable_text="",
        fade_text="",
        qa_text="hid the second gift",
        tags={"hide"},
    ),
}

GIRL_NAMES = ["Nia", "Iris", "Thaleia", "Mira", "Dara", "Lysa"]
BOY_NAMES = ["Oren", "Tarin", "Leos", "Pelas", "Niko", "Ivo"]


@dataclass
class StoryParams:
    setting: str
    offering: str
    carrier: str
    response: str
    hero_name: str
    hero_gender: str
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


CURATED = [
    StoryParams(
        setting="reed_pool",
        offering="fig",
        carrier="basket",
        response="shrine_share",
        hero_name="Nia",
        hero_gender="girl",
    ),
    StoryParams(
        setting="moon_ford",
        offering="shell",
        carrier="satchel",
        response="return_one",
        hero_name="Oren",
        hero_gender="boy",
    ),
    StoryParams(
        setting="laurel_basin",
        offering="flute",
        carrier="basket",
        response="shrine_share",
        hero_name="Mira",
        hero_gender="girl",
    ),
    StoryParams(
        setting="reed_pool",
        offering="shell",
        carrier="basket",
        response="return_one",
        hero_name="Tarin",
        hero_gender="boy",
    ),
    StoryParams(
        setting="moon_ford",
        offering="honey_cake",
        carrier="satchel",
        response="sing_thanks",
        hero_name="Iris",
        hero_gender="girl",
    ),
]


KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where water comes up out of the ground. In old stories, springs are often special places where people bring gifts or prayers.",
        )
    ],
    "duplicate": [
        (
            "What does duplicate mean?",
            "Duplicate means another one that matches the first one. If a spring made a duplicate fig, there would be two figs instead of one.",
        )
    ],
    "share": [
        (
            "Why is it good to share a surprise gift?",
            "Sharing keeps a good surprise from turning into grabbing. In many old tales, a blessing stays gentle when people remember others too.",
        )
    ],
    "fig": [
        (
            "What is a fig?",
            "A fig is a soft, sweet fruit. It grows on a tree and has many tiny seeds inside.",
        )
    ],
    "cake": [
        (
            "What is honey cake?",
            "Honey cake is a sweet baked cake made with honey. It smells warm and sweet because of the honey inside it.",
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is the hard outer covering of a creature that lives in water. People sometimes keep pretty shells because they shine and feel smooth.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a music instrument you blow into. A reed flute is made from a hollow plant stem and can sing with a soft voice.",
        )
    ],
    "song": [
        (
            "Why do people sing thanks in old stories?",
            "Singing thanks is a way to show respect and joy. In myths, words spoken kindly can calm magic and remind people to be humble.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spring", "duplicate", "share", "fig", "cake", "shell", "flute", "song"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    offering = f["offering"]
    setting = f["setting"]
    outcome = f["outcome"]
    ending = "The duplicate remains." if outcome == "stable" else "The duplicate fades back into water."
    return [
        f'Write a short myth for a young child that includes the words "splish" and "duplicate".',
        f"Tell a mythic surprise story where {hero.id} brings {offering.phrase} to {setting.place} and the spring answers with a second one. {ending}",
        f"Write a gentle old-style tale about a child who receives an unexpected blessing and must learn whether to keep it, share it, or return it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    offering = f["offering"]
    carrier = f["carrier"]
    spirit = f["spirit"]
    setting = f["setting"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who climbed to {setting.place} with {carrier.phrase}, and about {spirit.label}, who guarded the spring. The story follows what happened when one small gift became two.",
        ),
        (
            f"Why did {hero.id} go to the spring?",
            f"{hero.id} brought {offering.phrase} as an offering for {setting.shrine}. The journey began as a simple act of respect, not as a search for extra treasure.",
        ),
        (
            "What was the surprise at the water?",
            f"When the gift touched the spring, a duplicate rose beside it after the tiny sound 'splish.' That surprise changed the child's hope into wonder and temptation at the same time.",
        ),
        (
            f"Why did the bridge begin to feel dangerous?",
            f"The child tried to carry both gifts at once, so the load suddenly grew heavier. In this myth, greed and weight move together, and that is why the bridge started to shiver.",
        ),
    ]
    if outcome == "stable":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} {response.qa_text}. That choice calmed the spring because the child stopped grabbing and treated the surprise as something to honor.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the blessing safely settled in the world instead of hidden away. The final image shows {setting.shrine} at dusk, proving that the surprise became part of something shared and holy.",
            )
        )
    else:
        qa.append(
            (
                f"What happened to the duplicate at the end?",
                f"The duplicate faded back into drops and could not be kept. The spring allowed one true gift to remain, so the child still carried home a lesson instead of a prize grabbed in greed.",
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that a surprise blessing cannot be hoarded just because it appears suddenly. The spring was gentle, but it still asked for humility before possession.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spring", "duplicate", "share"} | set(world.facts["offering"].tags) | set(world.facts["response"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(offering: Offering, carrier: Carrier) -> str:
    if not offering.duplicateable:
        return (
            f"(No story: {offering.phrase} does not belong to this spring's doubling magic, "
            f"so no surprise duplicate would rise from the water.)"
        )
    if carrier.capacity < 2:
        return (
            f"(No story: {carrier.phrase} can only hold one thing, but this myth needs room for the surprise duplicate.)"
        )
    if carrier.max_size < offering.size:
        return (
            f"(No story: {offering.phrase} is too large for {carrier.phrase}, so the child could not reasonably carry both gifts.)"
        )
    return "(No story: that offering and carrier do not fit this world.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer response such as {better}.)"
    )


ASP_RULES = r"""
duplicateable_offer(O) :- offering(O), duplicateable(O).
fits(C, O) :- carrier(C), offering(O), capacity(C, N), N >= 2, max_size(C, M), size(O, S), M >= S.
valid(S, O, C) :- setting(S), duplicateable_offer(O), fits(C, O).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
stable :- chosen_response(R), power(R, P), chosen_offering(O), wildness(O, W), P >= W.
fading :- chosen_response(R), power(R, P), chosen_offering(O), wildness(O, W), P < W.
outcome(stable) :- stable.
outcome(fading) :- fading.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("size", oid, offering.size))
        lines.append(asp.fact("wildness", oid, offering.wildness))
        if offering.duplicateable:
            lines.append(asp.fact("duplicateable", oid))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, carrier.capacity))
        lines.append(asp.fact("max_size", cid, carrier.max_size))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_offering", params.offering),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() for seed {s}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic spring, a surprise duplicate, and a lesson about sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.offering and args.carrier:
        offering = OFFERINGS[args.offering]
        carrier = CARRIERS[args.carrier]
        if not (can_duplicate(offering) and carrier_fits(carrier, offering)):
            raise StoryError(explain_rejection(offering, carrier))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.offering is None or c[1] == args.offering)
        and (args.carrier is None or c[2] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, offering, carrier = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        offering=offering,
        carrier=carrier,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        offering = OFFERINGS[params.offering]
        carrier = CARRIERS[params.carrier]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not can_duplicate(offering) or not carrier_fits(carrier, offering):
        raise StoryError(explain_rejection(offering, carrier))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        offering=offering,
        carrier=carrier,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, offering, carrier) combos:\n")
        for setting, offering, carrier in combos:
            print(f"  {setting:12} {offering:12} {carrier}")
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
            header = f"### {p.hero_name}: {p.offering} at {p.setting} ({p.carrier}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
