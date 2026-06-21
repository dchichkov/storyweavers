#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py
=====================================================================

A standalone story world for a tiny tall-tale domain: a brave child in an
outrageously oversized town climbs to fetch a dazzling prize that looks fit for
luxury, then discovers the best use for it is sharing it with everyone.

The world is classical and state-driven:
- a landmark is absurdly tall,
- a route may or may not be brave-enough and sensible enough,
- a carrier may or may not be strong enough,
- a prize solves only certain kinds of town celebrations,
- the hero first feels tempted to keep the splendid thing alone, then changes
  the day by sharing it.

Run it
------
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/luxury_dazzle_bravery_sharing_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
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
BRAVERY_BONUS = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Landmark:
    id: str
    label: str
    perch: str
    height: int
    wind: int
    opening: str
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
class Prize:
    id: str
    label: str
    phrase: str
    weight: int
    plenty: int
    gifts: set[str]
    shine: str
    luxury_line: str
    share_line: str
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
class Route:
    id: str
    label: str
    climb_verb: str
    reach: int
    steadiness: int
    boast: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    move_line: str
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
class Celebration:
    id: str
    label: str
    need: str
    crowd: str
    problem: str
    use_line: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_shaky_climb(world: World) -> list[str]:
    hero = world.get("hero")
    route = world.get("route")
    landmark = world.get("landmark")
    if hero.meters["climbing"] < THRESHOLD:
        return []
    sig = ("shaky_climb",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if route.attrs["steadiness"] <= landmark.attrs["wind"]:
        hero.memes["fear"] += 1
        hero.memes["bravery"] += 1
        return ["__shaky__"]
    hero.memes["confidence"] += 1
    return ["__steady__"]


def _r_prize_awe(world: World) -> list[str]:
    prize = world.get("prize")
    hero = world.get("hero")
    if prize.meters["reached"] < THRESHOLD:
        return []
    sig = ("prize_awe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["awe"] += 1
    prize.meters["available"] += 1
    return []


def _r_loaded_strain(world: World) -> list[str]:
    prize = world.get("prize")
    carrier = world.get("carrier")
    if prize.meters["loaded"] < THRESHOLD:
        return []
    sig = ("loaded_strain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if carrier.attrs["capacity"] == prize.attrs["weight"]:
        carrier.meters["strain"] += 1
    else:
        carrier.meters["strain"] = 0.0
    return []


def _r_share_relief(world: World) -> list[str]:
    town = world.get("town")
    hero = world.get("hero")
    if town.meters["received"] < THRESHOLD:
        return []
    sig = ("share_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    town.meters["need"] = 0.0
    town.memes["joy"] += 1
    hero.memes["generosity"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="shaky_climb", tag="feeling", apply=_r_shaky_climb),
    Rule(name="prize_awe", tag="feeling", apply=_r_prize_awe),
    Rule(name="loaded_strain", tag="physical", apply=_r_loaded_strain),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            if line not in {"__shaky__", "__steady__"}:
                world.say(line)
    return produced


LANDMARKS = {
    "grain_silo": Landmark(
        id="grain_silo",
        label="the old grain silo",
        perch="its brass weather rooster",
        height=2,
        wind=2,
        opening="Beyond the wheat fields stood the old grain silo, so tall it seemed to hold up one corner of the sky.",
        tags={"silo", "height"},
    ),
    "courthouse_clock": Landmark(
        id="courthouse_clock",
        label="the courthouse clocktower",
        perch="its minute hand",
        height=3,
        wind=2,
        opening="In the middle of town rose the courthouse clocktower, high enough to make noon arrive a little late at the ground.",
        tags={"clocktower", "height"},
    ),
    "windmill": Landmark(
        id="windmill",
        label="the hill windmill",
        perch="its highest turning vane",
        height=3,
        wind=3,
        opening="On the hill spun the town windmill, so tall and loud that geese used it as a weather report.",
        tags={"windmill", "height", "wind"},
    ),
}

PRIZES = {
    "sun_peach": Prize(
        id="sun_peach",
        label="Sun Peach",
        phrase="a Sun Peach as big as a bathtub",
        weight=2,
        plenty=12,
        gifts={"feast"},
        shine="Its skin had such dazzle that crows squinted at it from three counties away.",
        luxury_line="For one blink it looked like the sort of luxury a king might lock in a silver cupboard and admire alone.",
        share_line="The peach broke into shining slices enough for a whole long table.",
        tags={"fruit", "peach", "feast"},
    ),
    "lamp_melon": Prize(
        id="lamp_melon",
        label="Lamp Melon",
        phrase="a Lamp Melon round as a wagon wheel",
        weight=3,
        plenty=16,
        gifts={"lights"},
        shine="It gave off a honey-colored dazzle, as if sunset had rolled itself up and gone to sleep inside the rind.",
        luxury_line="It glowed with such luxury that even the store windows would have looked plain beside it.",
        share_line="When cut into lantern rounds, the melon lit every hat brim and fiddle bow in sight.",
        tags={"melon", "light", "parade"},
    ),
    "star_pear": Prize(
        id="star_pear",
        label="Star Pear",
        phrase="a Star Pear taller than a milk can",
        weight=2,
        plenty=10,
        gifts={"feast", "lights"},
        shine="Silver freckles ran over it with a cool dazzle, and the stem winked like a little comet.",
        luxury_line="It seemed fancy enough for a velvet cushion, but it had a kinder destiny than sitting pretty.",
        share_line="The pear made both sweet slices and bright little lantern cups.",
        tags={"pear", "light", "feast"},
    ),
}

ROUTES = {
    "rope_ladder": Route(
        id="rope_ladder",
        label="a rope ladder",
        climb_verb="swung up the rope ladder",
        reach=2,
        steadiness=2,
        boast="It was as springy as a jumping fish, but it knew its business.",
        tags={"ladder"},
    ),
    "beanstalk": Route(
        id="beanstalk",
        label="a beanstalk",
        climb_verb="climbed the beanstalk hand over hand",
        reach=3,
        steadiness=2,
        boast="The stalk was thick as a stovepipe and greener than a June brag.",
        tags={"beanstalk"},
    ),
    "wind_bridge": Route(
        id="wind_bridge",
        label="a wind bridge",
        climb_verb="walked the wind bridge",
        reach=3,
        steadiness=3,
        boast="Folks said it was woven from old kite string and stubbornness.",
        tags={"bridge", "wind"},
    ),
}

CARRIERS = {
    "red_wagon": Carrier(
        id="red_wagon",
        label="red wagon",
        phrase="a red wagon with squeaky wheels",
        capacity=2,
        move_line="rolled it home in a red wagon that rattled like cheerful thunder",
        tags={"wagon"},
    ),
    "hay_sled": Carrier(
        id="hay_sled",
        label="hay sled",
        phrase="a hay sled polished smooth by barn boots",
        capacity=3,
        move_line="hauled it down on a hay sled that skimmed the slope like a shy boat",
        tags={"sled"},
    ),
    "mule_cart": Carrier(
        id="mule_cart",
        label="mule cart",
        phrase="a mule cart with broad boards",
        capacity=3,
        move_line="brought it back in a mule cart while the wheels sang over the ruts",
        tags={"cart"},
    ),
}

CELEBRATIONS = {
    "pie_social": Celebration(
        id="pie_social",
        label="the pie social",
        need="feast",
        crowd="the pie social crowd",
        problem="The picnic tables were set, but the town had more hungry smiles than pies.",
        use_line="By supper, bakers were tucking the shining fruit into pies, tarts, and sticky little hand cakes.",
        ending="That evening the pie social looked less like a supper and more like a golden frontier moon had come down to be shared.",
        tags={"feast", "pie"},
    ),
    "lantern_parade": Celebration(
        id="lantern_parade",
        label="the lantern parade",
        need="lights",
        crowd="the lantern parade crowd",
        problem="The fiddlers were ready, but the parade had too few lights for the long dusk road.",
        use_line="By sundown, every child carried a bright piece of the prize and the band could see its own music again.",
        ending="That night the lantern parade floated through town like a river of stars someone had taught to march.",
        tags={"lights", "parade"},
    ),
    "harvest_day": Celebration(
        id="harvest_day",
        label="Harvest Day",
        need="feast",
        crowd="the Harvest Day crowd",
        problem="The kettles were hot, but the tables still looked thin for such a big holiday.",
        use_line="Before long, cooks were stirring sweet fruit into kettles while neighbors licked their thumbs and laughed.",
        ending="By dark, Harvest Day was full and shining, with every plate looking richer because it had been shared.",
        tags={"feast", "harvest"},
    ),
}


def route_fits(landmark: Landmark, route: Route) -> bool:
    return route.reach >= landmark.height and route.steadiness + BRAVERY_BONUS >= landmark.wind


def carrier_fits(prize: Prize, carrier: Carrier) -> bool:
    return carrier.capacity >= prize.weight


def celebration_fits(prize: Prize, celebration: Celebration) -> bool:
    return celebration.need in prize.gifts


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for landmark_id, landmark in LANDMARKS.items():
        for prize_id, prize in PRIZES.items():
            for route_id, route in ROUTES.items():
                for celebration_id, celebration in CELEBRATIONS.items():
                    if not route_fits(landmark, route):
                        continue
                    if not celebration_fits(prize, celebration):
                        continue
                    if any(carrier_fits(prize, carrier) for carrier in CARRIERS.values()):
                        combos.append((landmark_id, prize_id, route_id, celebration_id))
    return combos


def select_carrier(prize: Prize) -> Optional[str]:
    choices = [cid for cid, carrier in CARRIERS.items() if carrier_fits(prize, carrier)]
    if not choices:
        return None
    return sorted(choices, key=lambda cid: (CARRIERS[cid].capacity, cid))[0]


@dataclass
class StoryParams:
    landmark: str
    prize: str
    route: str
    celebration: str
    carrier: str
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


def explain_route(landmark: Landmark, route: Route) -> str:
    if route.reach < landmark.height:
        return (
            f"(No story: {route.label} does not reach {landmark.label}. "
            f"The prize is perched too high for that route.)"
        )
    return (
        f"(No story: {route.label} is too shaky for {landmark.label}'s wind. "
        f"This world only tells brave stories that are daring but still sensible.)"
    )


def explain_carrier(prize: Prize, carrier: Carrier) -> str:
    return (
        f"(No story: {carrier.phrase} cannot carry {prize.phrase}. "
        f"The prize is too heavy, so the trip home would make no sense.)"
    )


def explain_celebration(prize: Prize, celebration: Celebration) -> str:
    return (
        f"(No story: {prize.label} cannot honestly solve the problem at {celebration.label}. "
        f"Pick a prize whose gift matches the town's need.)"
    )


def outcome_of(params: StoryParams) -> str:
    landmark = LANDMARKS[params.landmark]
    route = ROUTES[params.route]
    if route.steadiness <= landmark.wind:
        return "hairy"
    return "smooth"


def introduce(world: World, hero: Entity, landmark: Landmark, celebration: Celebration) -> None:
    world.say(
        f"{hero.id} lived in a plains town where folks measured afternoon shadows with fence posts and still ran out of fence posts."
    )
    world.say(landmark.opening)
    world.say(
        f"At the same time, everybody was getting ready for {celebration.label}. {celebration.problem}"
    )


def glimpse_prize(world: World, hero: Entity, prize: Prize, landmark: Landmark) -> None:
    world.say(
        f"Up on {landmark.perch} hung {prize.phrase}. {prize.shine}"
    )
    world.say(
        f"{hero.id} shaded {hero.pronoun('possessive')} eyes and whispered, "
        f'"That is a mighty fine sight." {prize.luxury_line}'
    )


def decide(world: World, hero: Entity, route: Route) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"Most grown folks stayed below and admired the wonder from a respectful distance, but {hero.id} had the sort of bravery that put boots where worries were."
    )
    world.say(
        f"{route.boast} So {hero.id} {route.climb_verb}."
    )


def climb(world: World) -> None:
    hero = world.get("hero")
    hero.meters["climbing"] += 1
    markers = propagate(world, narrate=False)
    if "__shaky__" in markers:
        world.say(
            f"The wind tugged at {hero.pronoun('possessive')} shirt and the town looked no bigger than checkers on a quilt. "
            f"{hero.id} felt a flutter in {hero.pronoun('possessive')} middle, took one brave breath, and kept going anyway."
        )
    else:
        world.say(
            f"The climb was long, but steady enough for courage to get its work done. Every rung and leaf seemed to nod {hero.pronoun('object')} higher."
        )


def reach_prize(world: World, hero: Entity, prize: Prize, landmark: Landmark) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["reached"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} reached {landmark.perch} and laid both hands on the {prize.label}. It was warm, heavy, and real."
    )


def lower_prize(world: World, hero: Entity, prize: Prize, carrier: Carrier) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["loaded"] += 1
    propagate(world, narrate=False)
    strain = world.get("carrier").meters["strain"] >= THRESHOLD
    world.say(
        f"{hero.id} eased the prize down and {carrier.move_line}."
    )
    if strain:
        world.say(
            f"The load filled the carrier from rail to rail, and the wheels complained, but they held."
        )
    else:
        world.say(
            f"There was room to spare, which in that town counted as a small miracle."
        )


def temptation(world: World, hero: Entity, celebration: Celebration) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"By the time {hero.pronoun()} rolled back into town, the prize looked grand enough to keep for one private feast and one private brag."
    )
    world.say(
        f"Then {hero.pronoun().capitalize()} saw {celebration.crowd}: empty hands, hopeful faces, and tables waiting for something generous to happen."
    )


def share(world: World, hero: Entity, prize: Prize, celebration: Celebration) -> None:
    town = world.get("town")
    town.meters["received"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} laughed and said, \"A wonder this big is too big for just one belly or one porch.\""
    )
    world.say(prize.share_line)
    world.say(celebration.use_line)


def ending(world: World, hero: Entity, celebration: Celebration) -> None:
    if hero.memes["fear"] >= THRESHOLD:
        middle = "After the brave climb"
    else:
        middle = "After the long climb"
    world.say(
        f"{middle}, the finest thing in town was not the prize itself but the way it changed once everybody had a piece."
    )
    world.say(celebration.ending)


def tell(
    landmark: Landmark,
    prize: Prize,
    route: Route,
    carrier: Carrier,
    celebration: Celebration,
    hero_name: str = "June",
    hero_gender: str = "girl",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"display": hero_name},
        )
    )
    town = world.add(
        Entity(
            id="town",
            kind="thing",
            type="town",
            label="the town",
            role="town",
            attrs={"need": celebration.need},
        )
    )
    world.add(
        Entity(
            id="landmark",
            type="landmark",
            label=landmark.label,
            attrs={"height": landmark.height, "wind": landmark.wind},
        )
    )
    world.add(
        Entity(
            id="route",
            type="route",
            label=route.label,
            attrs={"reach": route.reach, "steadiness": route.steadiness},
        )
    )
    world.add(
        Entity(
            id="prize",
            type="prize",
            label=prize.label,
            phrase=prize.phrase,
            attrs={"weight": prize.weight, "plenty": prize.plenty, "gifts": set(prize.gifts)},
        )
    )
    world.add(
        Entity(
            id="carrier",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            attrs={"capacity": carrier.capacity},
        )
    )

    hero.memes["bravery"] = float(BRAVERY_BONUS)
    hero.memes["generosity"] = 0.0
    town.meters["need"] = 1.0
    town.meters["received"] = 0.0

    introduce(world, hero, landmark, celebration)
    glimpse_prize(world, hero, prize, landmark)

    world.para()
    decide(world, hero, route)
    climb(world)
    reach_prize(world, hero, prize, landmark)
    lower_prize(world, hero, prize, carrier)

    world.para()
    temptation(world, hero, celebration)
    share(world, hero, prize, celebration)
    ending(world, hero, celebration)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        landmark=landmark,
        prize_cfg=prize,
        route_cfg=route,
        carrier_cfg=carrier,
        celebration=celebration,
        outcome=outcome_of(
            StoryParams(
                landmark=landmark.id,
                prize=prize.id,
                route=route.id,
                celebration=celebration.id,
                carrier=carrier.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
            )
        ),
        shared=town.meters["received"] >= THRESHOLD,
        fear=hero.memes["fear"] >= THRESHOLD,
        awe=hero.memes["awe"] >= THRESHOLD,
        strain=world.get("carrier").meters["strain"] >= THRESHOLD,
        town_relieved=town.meters["need"] < THRESHOLD,
    )
    return world


GIRL_NAMES = ["June", "Maisie", "Nell", "Ada", "Ruby", "Clara", "Willa", "Pearl"]
BOY_NAMES = ["Bo", "Hank", "Eli", "Jesse", "Otis", "Cal", "Finn", "Toby"]

KNOWLEDGE = {
    "beanstalk": [(
        "What is a beanstalk?",
        "A beanstalk is the thick stem of a bean plant. In tall tales, people imagine one growing so huge that someone could climb it."
    )],
    "bridge": [(
        "What is a bridge for?",
        "A bridge helps people cross from one place to another. A strong bridge makes a hard trip safer."
    )],
    "ladder": [(
        "What does a ladder do?",
        "A ladder helps you reach a high place by giving your feet and hands steps to climb."
    )],
    "wagon": [(
        "What is a wagon used for?",
        "A wagon is used to carry heavy things. Wheels make a load easier to move from one place to another."
    )],
    "sled": [(
        "What is a sled good for?",
        "A sled helps slide a heavy load along the ground. It can make hauling easier when something is big or awkward."
    )],
    "cart": [(
        "What does a cart do?",
        "A cart carries things that are too heavy to hold in your arms. It lets people share big loads and move them together."
    )],
    "feast": [(
        "What is a feast?",
        "A feast is a meal where many people gather and eat together. Sharing food can make a feast feel warm and welcoming."
    )],
    "lights": [(
        "Why do people carry lights at a parade?",
        "Lights help people see after dark, and they also make a parade look bright and festive."
    )],
    "sharing": [(
        "Why is sharing brave sometimes?",
        "Sharing can be brave when you have something splendid and decide not to keep it all for yourself. It means caring more about everyone else joining in."
    )],
    "luxury": [(
        "What does luxury mean?",
        "Luxury means something extra fine, rich, or fancy. In stories, a luxury object feels special enough to admire."
    )],
    "dazzle": [(
        "What does dazzle mean?",
        "Dazzle means a bright sparkle or shine that catches your eyes. Something with dazzle can seem almost magical."
    )],
}
KNOWLEDGE_ORDER = [
    "luxury",
    "dazzle",
    "ladder",
    "beanstalk",
    "bridge",
    "wagon",
    "sled",
    "cart",
    "feast",
    "lights",
    "sharing",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    celebration = f["celebration"]
    landmark = f["landmark"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "luxury" and "dazzle".',
        f"Tell a tall tale where a brave {hero.type} climbs {landmark.label} to fetch {prize.phrase} and then shares it with the whole town.",
        f"Write a frontier-flavored story where a child sees something splendid enough to feel like luxury, but the happy ending comes from sharing it at {celebration.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    celebration = f["celebration"]
    landmark = f["landmark"]
    route = f["route_cfg"]
    carrier = f["carrier_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['display']}, a brave child in a tall-tale town. {hero.pronoun().capitalize()} climbed high to bring down {prize.phrase}."
        ),
        (
            f"Why did {hero.attrs['display']} climb {landmark.label}?",
            f"{hero.attrs['display']} climbed because the town needed help for {celebration.label}. The wonderful prize high above could solve that problem if someone was brave enough to fetch it."
        ),
        (
            f"What made the prize seem special?",
            f"It looked huge, bright, and full of dazzle. For a moment it even seemed like a piece of luxury, something fancy enough to keep and admire."
        ),
    ]
    if f["fear"]:
        qa.append((
            f"Was the climb easy for {hero.attrs['display']}?",
            f"No. The wind made the climb scary, and {hero.attrs['display']} felt that in the middle of the trip. {hero.pronoun().capitalize()} kept going anyway, which is what made the bravery matter."
        ))
    else:
        qa.append((
            f"How did {hero.attrs['display']} get up so high?",
            f"{hero.pronoun().capitalize()} used {route.label} to reach the prize. The route was long, but it was steady enough for a brave climb."
        ))
    qa.append((
        f"How did {hero.attrs['display']} bring the prize back down?",
        f"{hero.pronoun().capitalize()} used {carrier.phrase} to carry it home. That mattered because the prize was too big to tuck under one arm."
    ))
    qa.append((
        f"Why did {hero.attrs['display']} share the prize instead of keeping it?",
        f"{hero.pronoun().capitalize()} saw the whole town waiting and understood the wonder was bigger than one person. Sharing turned a splendid object into a happy day for everyone."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with {celebration.label} bright and full because the prize was shared. The ending proves the best part was not owning the wonder, but letting the whole town enjoy it."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["landmark"].tags) | set(f["prize_cfg"].tags) | set(f["route_cfg"].tags) | set(f["carrier_cfg"].tags) | set(f["celebration"].tags)
    tags |= {"luxury", "dazzle", "sharing"}
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
            shown = {}
            for k, v in ent.attrs.items():
                shown[k] = sorted(v) if isinstance(v, set) else v
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        landmark="grain_silo",
        prize="sun_peach",
        route="rope_ladder",
        celebration="pie_social",
        carrier="red_wagon",
        hero_name="June",
        hero_gender="girl",
    ),
    StoryParams(
        landmark="windmill",
        prize="lamp_melon",
        route="wind_bridge",
        celebration="lantern_parade",
        carrier="hay_sled",
        hero_name="Bo",
        hero_gender="boy",
    ),
    StoryParams(
        landmark="courthouse_clock",
        prize="star_pear",
        route="beanstalk",
        celebration="harvest_day",
        carrier="red_wagon",
        hero_name="Ruby",
        hero_gender="girl",
    ),
    StoryParams(
        landmark="windmill",
        prize="star_pear",
        route="wind_bridge",
        celebration="lantern_parade",
        carrier="red_wagon",
        hero_name="Eli",
        hero_gender="boy",
    ),
]


ASP_RULES = r"""
route_fits(L, R) :- landmark(L), route(R), height(L, H), reach(R, H2), H2 >= H,
                    wind(L, W), steadiness(R, S), bravery_bonus(B), S + B >= W.
carrier_fits(P, C) :- prize(P), carrier(C), weight(P, W), capacity(C, K), K >= W.
celebration_fits(P, Cb) :- prize_gift(P, Need), celebration_need(Cb, Need).
has_carrier(P) :- carrier_fits(P, _).

valid(L, P, R, Cb) :- landmark(L), prize(P), route(R), celebration(Cb),
                      route_fits(L, R), celebration_fits(P, Cb), has_carrier(P).

chosen_valid :- chosen_landmark(L), chosen_prize(P), chosen_route(R), chosen_celebration(Cb),
                valid(L, P, R, Cb).

smooth :- chosen_landmark(L), chosen_route(R), wind(L, W), steadiness(R, S), S > W.
hairy  :- chosen_valid, not smooth.

outcome(smooth) :- chosen_valid, smooth.
outcome(hairy)  :- chosen_valid, hairy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("bravery_bonus", BRAVERY_BONUS)]
    for lid, landmark in LANDMARKS.items():
        lines.append(asp.fact("landmark", lid))
        lines.append(asp.fact("height", lid, landmark.height))
        lines.append(asp.fact("wind", lid, landmark.wind))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("weight", pid, prize.weight))
        for gift in sorted(prize.gifts):
            lines.append(asp.fact("prize_gift", pid, gift))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("reach", rid, route.reach))
        lines.append(asp.fact("steadiness", rid, route.steadiness))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, carrier.capacity))
    for cid, celebration in CELEBRATIONS.items():
        lines.append(asp.fact("celebration", cid))
        lines.append(asp.fact("celebration_need", cid, celebration.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_landmark", params.landmark),
        asp.fact("chosen_prize", params.prize),
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_celebration", params.celebration),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a brave climb, a dazzling prize, and a generous ending."
    )
    ap.add_argument("--landmark", choices=LANDMARKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--celebration", choices=CELEBRATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.landmark and args.route:
        if not route_fits(LANDMARKS[args.landmark], ROUTES[args.route]):
            raise StoryError(explain_route(LANDMARKS[args.landmark], ROUTES[args.route]))
    if args.prize and args.carrier:
        if not carrier_fits(PRIZES[args.prize], CARRIERS[args.carrier]):
            raise StoryError(explain_carrier(PRIZES[args.prize], CARRIERS[args.carrier]))
    if args.prize and args.celebration:
        if not celebration_fits(PRIZES[args.prize], CELEBRATIONS[args.celebration]):
            raise StoryError(explain_celebration(PRIZES[args.prize], CELEBRATIONS[args.celebration]))

    combos = [
        combo for combo in valid_combos()
        if (args.landmark is None or combo[0] == args.landmark)
        and (args.prize is None or combo[1] == args.prize)
        and (args.route is None or combo[2] == args.route)
        and (args.celebration is None or combo[3] == args.celebration)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    landmark_id, prize_id, route_id, celebration_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]

    if args.carrier:
        carrier_id = args.carrier
        if not carrier_fits(prize, CARRIERS[carrier_id]):
            raise StoryError(explain_carrier(prize, CARRIERS[carrier_id]))
    else:
        carrier_id = select_carrier(prize)
        if carrier_id is None:
            raise StoryError("(No sensible carrier exists for that prize.)")

    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        name = rng.choice(pool)

    return StoryParams(
        landmark=landmark_id,
        prize=prize_id,
        route=route_id,
        celebration=celebration_id,
        carrier=carrier_id,
        hero_name=name,
        hero_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.landmark not in LANDMARKS:
        raise StoryError(f"(Unknown landmark: {params.landmark})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.celebration not in CELEBRATIONS:
        raise StoryError(f"(Unknown celebration: {params.celebration})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")

    landmark = LANDMARKS[params.landmark]
    prize = PRIZES[params.prize]
    route = ROUTES[params.route]
    celebration = CELEBRATIONS[params.celebration]
    carrier = CARRIERS[params.carrier]

    if not route_fits(landmark, route):
        raise StoryError(explain_route(landmark, route))
    if not carrier_fits(prize, carrier):
        raise StoryError(explain_carrier(prize, carrier))
    if not celebration_fits(prize, celebration):
        raise StoryError(explain_celebration(prize, celebration))

    world = tell(
        landmark=landmark,
        prize=prize,
        route=route,
        carrier=carrier,
        celebration=celebration,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    story = sample.story
    hero_name = sample.params.hero_name
    story = story.replace("hero", hero_name)
    print(story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(40):
        try:
            ns = build_parser().parse_args([])
            p = resolve_params(ns, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (landmark, prize, route, celebration) combos:\n")
        for landmark, prize, route, celebration in combos:
            carrier = select_carrier(PRIZES[prize]) or "?"
            print(f"  {landmark:16} {prize:11} {route:12} {celebration:15} carrier={carrier}")
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
                f"### {p.hero_name}: {p.prize} from {p.landmark} "
                f"for {p.celebration} via {p.route}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
