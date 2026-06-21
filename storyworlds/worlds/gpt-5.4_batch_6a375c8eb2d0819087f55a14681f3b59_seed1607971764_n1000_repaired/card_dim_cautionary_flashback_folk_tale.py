#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py
=====================================================================

A standalone storyworld for a small folk-tale domain built around a hurried child,
a dangerous shortcut, and an elder's warning told through a flashback.

The core shape is cautionary:
- a child is tempted to hurry by a risky route in the card-dim light,
- an elder remembers taking that same kind of route long ago,
- the child either listens and stays safe, or ignores the warning and meets trouble,
- the ending image proves the lesson took root.

Run it
------
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py --route ford
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py --asp
    python storyworlds/worlds/gpt-5.4/card_dim_cautionary_flashback_folk_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
WISE_TRAITS = {"careful", "thoughtful", "steady"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def kin_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Errand:
    id: str
    phrase: str
    short: str
    destination: str
    damage_text: str
    fragile: bool = False
    water_sensitive: bool = False
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
    phrase: str
    place: str
    risks: set[str] = field(default_factory=set)
    severity: int = 1
    flashback_loss: str = ""
    danger_line: str = ""
    recovery_line: str = ""
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
class Safeguard:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    sense: int = 2
    offer_text: str = ""
    travel_text: str = ""
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
class Rescue:
    id: str
    label: str
    sense: int = 2
    power: int = 2
    success_text: str = ""
    fail_text: str = ""
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


@dataclass
class StoryParams:
    route: str
    errand: str
    safeguard: str
    rescue: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    trust: int = 5
    child_age: int = 7
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


def _r_route_trouble(world: World) -> list[str]:
    child = world.get("child")
    route = world.get("route")
    if child.meters["taking_shortcut"] < THRESHOLD:
        return []
    sig = ("route_trouble", route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["danger"] += float(route.attrs["severity"])
    child.memes["fear"] += 1.0
    parcel = world.get("parcel")
    parcel.meters["jolted"] += 1.0
    if "water" in route.attrs["risks"]:
        child.meters["wet"] += 1.0
    if "slip" in route.attrs["risks"]:
        child.meters["slipped"] += 1.0
    return ["__trouble__"]


def _r_parcel_damage(world: World) -> list[str]:
    child = world.get("child")
    parcel = world.get("parcel")
    if child.meters["danger"] < THRESHOLD:
        return []
    sig = ("parcel_damage", parcel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if parcel.attrs.get("fragile"):
        parcel.meters["damaged"] += 1.0
    if parcel.attrs.get("water_sensitive") and child.meters["wet"] >= THRESHOLD:
        parcel.meters["damaged"] += 1.0
    return []


CAUSAL_RULES = [
    Rule(name="route_trouble", tag="physical", apply=_r_route_trouble),
    Rule(name="parcel_damage", tag="physical", apply=_r_parcel_damage),
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
        for line in produced:
            world.say(line)
    return produced


ERRANDS = {
    "cakes": Errand(
        id="cakes",
        phrase="a cloth-covered plate of honey cakes",
        short="the honey cakes",
        destination="the miller's cottage",
        damage_text="the honey cakes were soaked and muddy",
        fragile=False,
        water_sensitive=True,
        tags={"cakes", "bread"},
    ),
    "eggs": Errand(
        id="eggs",
        phrase="a willow basket of blue eggs",
        short="the eggs",
        destination="the baker's door",
        damage_text="the blue eggs cracked in the basket",
        fragile=True,
        water_sensitive=False,
        tags={"eggs", "basket"},
    ),
    "seeds": Errand(
        id="seeds",
        phrase="a small sack of barley seed",
        short="the seed sack",
        destination="the far field gate",
        damage_text="the barley seed was spilled and spoiled",
        fragile=False,
        water_sensitive=True,
        tags={"seeds", "sack"},
    ),
}

ROUTES = {
    "ford": Route(
        id="ford",
        label="the willow ford",
        phrase="the willow ford where the stream crossed the lane",
        place="stream",
        risks={"water", "dark"},
        severity=2,
        flashback_loss="my shoes filled with black water and my little loaf went spinning downstream",
        danger_line="the cold stream tugged at the child's ankles",
        recovery_line="the water swirled around the stones and tried to take the bundle away",
        tags={"ford", "stream"},
    ),
    "log": Route(
        id="log",
        label="the mossy log",
        phrase="the mossy log laid across the brook",
        place="brook",
        risks={"slip", "dark"},
        severity=2,
        flashback_loss="the moss turned under me and I sat down hard in the brook with my bundle over my head",
        danger_line="the log rolled slick as soap under the child's shoe",
        recovery_line="one foot slipped and the bundle flew up in the air",
        tags={"log", "brook"},
    ),
    "marsh": Route(
        id="marsh",
        label="the marsh stones",
        phrase="the marsh stones that peeked out of the reeds",
        place="marsh",
        risks={"water", "slip", "dark"},
        severity=3,
        flashback_loss="one stone sank, another tilted, and I came home wet to the waist with nothing left but reeds in my hands",
        danger_line="the hidden stones shifted in the mud",
        recovery_line="mud sucked at little shoes and the dark water licked over the stones",
        tags={"marsh", "reeds"},
    ),
    "hollow": Route(
        id="hollow",
        label="the hollow path",
        phrase="the hollow path under the hazel trees",
        place="woods",
        risks={"dark"},
        severity=1,
        flashback_loss="I missed the turning in the dark and wandered until the owls had finished calling",
        danger_line="the shadows folded together until the path was hard to read",
        recovery_line="every root looked like the next one in the dim light",
        tags={"woods", "path"},
    ),
}

SAFEGUARDS = {
    "bridge": Safeguard(
        id="bridge",
        label="the stone bridge",
        covers={"water", "slip", "dark"},
        sense=3,
        offer_text="We will go the long way by the stone bridge, where the feet have good ground.",
        travel_text="They took the old stone bridge, and the water stayed below them where it belonged.",
        tags={"bridge"},
    ),
    "ferry": Safeguard(
        id="ferry",
        label="the ferry rope-boat",
        covers={"water", "dark"},
        sense=3,
        offer_text="We will call the rope-ferry and cross sitting still, not hopping where the water thinks faster than children do.",
        travel_text="They waited for the rope-ferry, and it carried them over with a soft creak and a wet shine on the planks.",
        tags={"ferry", "boat"},
    ),
    "lantern": Safeguard(
        id="lantern",
        label="the elder's horn lantern",
        covers={"dark", "slip"},
        sense=2,
        offer_text="Take my horn lantern and my hand, and the ground will not have to guess where your feet belong.",
        travel_text="With the lantern low and the elder's hand steady, each step could see the next one.",
        tags={"lantern", "light"},
    ),
    "dawn": Safeguard(
        id="dawn",
        label="waiting for dawn",
        covers={"dark"},
        sense=2,
        offer_text="Leave the bundle on the shelf and go when morning whitens the lane. A late errand is better than a lost child.",
        travel_text="They waited until dawn silvered the hedges, and then the road looked plain and honest.",
        tags={"dawn", "morning"},
    ),
}

RESCUES = {
    "hook": Rescue(
        id="hook",
        label="the crook-handled shepherd's hook",
        sense=3,
        power=2,
        success_text="caught the child by the belt with a crook-handled shepherd's hook and drew the little one back to the bank",
        fail_text="snatched with the shepherd's hook, but the child had already gone too deep into the trouble",
        qa_text="used a shepherd's hook to pull the child back",
        tags={"hook", "rescue"},
    ),
    "boat": Rescue(
        id="boat",
        label="the rope-boat",
        sense=3,
        power=3,
        success_text="pushed off in the rope-boat and hauled the child in before the dark water could pull harder",
        fail_text="rowed the rope-boat hard, but the bundle was already gone and the trouble had spread too far",
        qa_text="pulled the child out with the rope-boat",
        tags={"boat", "rescue"},
    ),
    "branch": Rescue(
        id="branch",
        label="a willow branch",
        sense=1,
        power=1,
        success_text="thrust out a willow branch and tugged the child to shore",
        fail_text="thrust out a willow branch, but it was too little help for such trouble",
        qa_text="reached out a willow branch",
        tags={"branch", "rescue"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tessa", "Lina", "Nell", "Ivy", "Mara", "Elsie"]
BOY_NAMES = ["Tobin", "Ivo", "Perrin", "Ned", "Rowan", "Hale", "Milo", "Bram"]
CHILD_TRAITS = ["careful", "thoughtful", "steady", "eager", "restless", "hasty"]


def valid_combo(route_id: str, safeguard_id: str) -> bool:
    route = ROUTES[route_id]
    safeguard = SAFEGUARDS[safeguard_id]
    return route.risks.issubset(safeguard.covers)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for route_id in ROUTES:
        for safeguard_id in SAFEGUARDS:
            if valid_combo(route_id, safeguard_id):
                out.append((route_id, safeguard_id))
    return out


def sensible_rescues() -> list[Rescue]:
    return [rescue for rescue in RESCUES.values() if rescue.sense >= SENSE_MIN]


def explain_route_safeguard(route: Route, safeguard: Safeguard) -> str:
    missing = sorted(route.risks - safeguard.covers)
    return (
        f"(No story: {safeguard.label} does not honestly solve the risk on {route.label}. "
        f"It misses {missing}, so the elder would not offer it as a safe answer.)"
    )


def explain_rescue(rescue_id: str) -> str:
    rescue = RESCUES[rescue_id]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def heed_score(child_trait: str, trust: int, elder_type: str, child_age: int) -> int:
    trait_bonus = 3 if child_trait in WISE_TRAITS else 0
    elder_bonus = 2 if elder_type in {"grandmother", "grandfather"} else 1
    age_bonus = 1 if child_age <= 6 else 0
    return trust + trait_bonus + elder_bonus + age_bonus


def would_heed(params: StoryParams) -> bool:
    return heed_score(params.child_trait, params.trust, params.elder_type, params.child_age) >= 9


def trouble_severity(route: Route, delay: int) -> int:
    return route.severity + delay


def rescue_holds(rescue: Rescue, route: Route, delay: int) -> bool:
    return rescue.power >= trouble_severity(route, delay)


def outcome_of(params: StoryParams) -> str:
    if would_heed(params):
        return "heeded"
    return "rescued" if rescue_holds(RESCUES[params.rescue], ROUTES[params.route], params.delay) else "lost"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["taking_shortcut"] += 1.0
    propagate(sim, narrate=False)
    child = sim.get("child")
    parcel = sim.get("parcel")
    return {
        "danger": int(child.meters["danger"]),
        "wet": child.meters["wet"] >= THRESHOLD,
        "damaged": parcel.meters["damaged"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, elder: Entity, errand: Errand) -> None:
    world.say(
        f"In a village where the hens went to sleep with the sunset, {child.id} set out with "
        f"{errand.phrase} for {errand.destination}."
    )
    world.say(
        f"The evening had gone card-dim already, the sort of dimness that makes a lane look short "
        f"when it is not and makes a child think hurry is wiser than it is."
    )
    world.say(
        f"Beside the gate stood {child.pronoun('possessive')} {elder.kin_word}, watching the hedges "
        f"darken one leaf at a time."
    )


def tempt(world: World, child: Entity, route: Route, errand: Errand) -> None:
    child.memes["hurry"] += 1.0
    world.say(
        f"{child.id} looked toward {route.phrase} and hugged {errand.short} close. "
        f'"If I take {route.label}," {child.pronoun()} said, "I will be there before the last smoke leaves the chimneys."'
    )


def warn_with_flashback(world: World, child: Entity, elder: Entity, route: Route, errand: Errand) -> None:
    pred = predict_trouble(world)
    elder.memes["care"] += 1.0
    child.memes["caution"] += 1.0
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_damage"] = pred["damaged"]
    world.say(
        f'{elder.kin_word.capitalize()} shook {elder.pronoun("possessive")} head. '
        f'"Do not race the dark by {route.label}," {elder.pronoun()} said. '
        f'"That path asks a price from hasty feet."'
    )
    world.say(
        f'Then {elder.pronoun()} gave a little sigh and spoke as old storytellers do, with one eye on now and one eye on long ago: '
        f'"When I was no taller than you, I chose {route.label} in just such a dim hour. '
        f'{route.flashback_loss}. Since that day I have trusted the longer road more than the quick one."'
    )
    if pred["damaged"]:
        world.say(
            f'"And look at what you carry," {elder.pronoun()} added. '
            f'"A stumble there would mean more than wet shoes."'
        )


def offer_safeguard(world: World, elder: Entity, safeguard: Safeguard) -> None:
    world.say(
        f'{elder.kin_word.capitalize()} pointed toward the safe way. "{safeguard.offer_text}"'
    )


def heed(world: World, child: Entity, elder: Entity, safeguard: Safeguard, errand: Errand) -> None:
    child.memes["wisdom"] += 1.0
    child.memes["relief"] += 1.0
    elder.memes["relief"] += 1.0
    world.say(
        f"{child.id} looked once more toward the dark shortcut, then down at {errand.short}, and the hurry softened in "
        f"{child.pronoun('possessive')} chest."
    )
    world.say(
        f'"Very well," {child.pronoun()} said. "A quick road is not quick if it spills supper or loses me."'
    )
    world.say(safeguard.travel_text)
    world.say(
        f"They reached {errand.destination} late but smiling, and {errand.short} arrived exactly as it had left home."
    )


def defy(world: World, child: Entity, route: Route) -> None:
    child.memes["defiance"] += 1.0
    world.say(
        f'But hurry is a loud drummer in young ears. Before another word could catch {child.pronoun("object")}, '
        f"{child.id} darted toward {route.label}."
    )


def take_shortcut(world: World, child: Entity, route_ent: Entity, route: Route) -> None:
    child.meters["taking_shortcut"] += 1.0
    route_ent.meters["used"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"At once {route.danger_line}. {route.recovery_line}."
    )


def alarm(world: World, child: Entity, elder: Entity, errand: Errand) -> None:
    parcel = world.get("parcel")
    if parcel.meters["damaged"] >= THRESHOLD:
        world.say(
            f'"{child.id}!" cried {elder.kin_word}. "{errand.short.capitalize()}!"'
        )
    else:
        world.say(
            f'"{child.id}!" cried {elder.kin_word}.'
        )


def rescue_success(world: World, child: Entity, elder: Entity, rescue: Rescue, errand: Errand) -> None:
    child.meters["danger"] = 0.0
    child.meters["taking_shortcut"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1.0
    elder.memes["relief"] += 1.0
    world.say(
        f"{elder.kin_word.capitalize()} {rescue.success_text}."
    )
    parcel = world.get("parcel")
    if parcel.meters["damaged"] >= THRESHOLD:
        world.say(
            f"When they stood safe again, they saw that {errand.damage_text}."
        )
    else:
        world.say(
            f"The bundle was shaken, but {errand.short} stayed safe in {child.pronoun('possessive')} arms."
        )
    world.say(
        f"{child.id} trembled harder from the almost than from the cold."
    )


def rescue_fail(world: World, child: Entity, elder: Entity, rescue: Rescue, errand: Errand) -> None:
    child.meters["danger"] = 0.0
    child.meters["taking_shortcut"] = 0.0
    child.memes["fear"] += 1.0
    world.say(
        f"{elder.kin_word.capitalize()} {rescue.fail_text}."
    )
    world.say(
        f"{child.id} came back to the bank safe at last, but {errand.damage_text}."
    )
    world.say(
        f"The child stood in the reeds with wet cheeks and a much quieter heart."
    )


def lesson(world: World, child: Entity, elder: Entity, route: Route, outcome: str) -> None:
    child.memes["wisdom"] += 1.0
    elder.memes["care"] += 1.0
    if outcome == "rescued":
        world.say(
            f'{elder.kin_word.capitalize()} wrapped {child.pronoun("object")} in a cloak and said, '
            f'"Now you know why I told the old tale. The dark does not hate children; it only never promises to spare them."'
        )
    elif outcome == "lost":
        world.say(
            f'{elder.kin_word.capitalize()} drew {child.pronoun("object")} close and said, '
            f'"Now you know why old stories are told twice: once by memory, and once by consequence."'
        )
    else:
        world.say(
            f'{elder.kin_word.capitalize()} smiled into the lantern light and said, '
            f'"Remember this too: the wise road may be longer underfoot, but it is shorter in sorrow."'
        )
    world.say(
        f"{child.id} nodded and did not look toward {route.label} again that night."
    )


def changed_ending(world: World, child: Entity, elder: Entity, safeguard: Safeguard, route: Route, errand: Errand, outcome: str) -> None:
    world.para()
    if outcome == "heeded":
        world.say(
            f"After that evening, whenever the light grew card-dim, {child.id} asked first where the safe feet should go."
        )
        world.say(
            f"And folk in the village would sometimes see the child and {elder.kin_word} on {safeguard.label}, "
            f"bundle steady, steps unhurried, with the dark left to gather where it pleased."
        )
    elif outcome == "rescued":
        world.say(
            f"On the next errand day, {child.id} came to the lane early and chose {safeguard.label} before anyone needed to speak."
        )
        world.say(
            f"The bundle rode safely, and even the water seemed to mind its own business when it was looked at from the right road."
        )
    else:
        world.say(
            f"For many evenings after, {child.id} would glance at {route.label} and then turn away without being asked."
        )
        world.say(
            f"And when the village children boasted that the shortest path was the bravest one, {child.pronoun()} answered, "
            f'"No. The bravest child is the one who reaches home with both hands full and both feet under {child.pronoun("object")}."'
        )


def tell(
    route: Route,
    errand: Errand,
    safeguard: Safeguard,
    rescue: Rescue,
    child_name: str,
    child_gender: str,
    elder_type: str,
    child_trait: str,
    trust: int,
    child_age: int,
    delay: int,
) -> World:
    world = World()

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            age=child_age,
            traits=[child_trait],
            attrs={"trust": trust},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            traits=["watchful"],
            attrs={},
        )
    )
    parcel = world.add(
        Entity(
            id="parcel",
            kind="thing",
            type="bundle",
            label=errand.short,
            attrs={
                "fragile": errand.fragile,
                "water_sensitive": errand.water_sensitive,
            },
        )
    )
    route_ent = world.add(
        Entity(
            id="route",
            kind="thing",
            type="route",
            label=route.label,
            attrs={
                "risks": set(route.risks),
                "severity": route.severity + delay,
            },
        )
    )

    child.meters["taking_shortcut"] = 0.0
    child.meters["danger"] = 0.0
    child.meters["wet"] = 0.0
    child.meters["slipped"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["hurry"] = 0.0
    child.memes["wisdom"] = 0.0
    elder.memes["care"] = 0.0
    elder.memes["relief"] = 0.0
    parcel.meters["damaged"] = 0.0
    parcel.meters["jolted"] = 0.0

    introduce(world, child, elder, errand)
    world.para()
    tempt(world, child, route, errand)
    warn_with_flashback(world, child, elder, route, errand)
    offer_safeguard(world, elder, safeguard)

    if would_heed(
        StoryParams(
            route=route.id,
            errand=errand.id,
            safeguard=safeguard.id,
            rescue=rescue.id,
            child_name=child_name,
            child_gender=child_gender,
            elder_type=elder_type,
            child_trait=child_trait,
            trust=trust,
            child_age=child_age,
            delay=delay,
            seed=None,
        )
    ):
        world.para()
        heed(world, child, elder, safeguard, errand)
        outcome = "heeded"
    else:
        world.para()
        defy(world, child, route)
        take_shortcut(world, child, route_ent, route)
        alarm(world, child, elder, errand)
        world.para()
        if rescue_holds(rescue, route, delay):
            rescue_success(world, child, elder, rescue, errand)
            outcome = "rescued"
        else:
            rescue_fail(world, child, elder, rescue, errand)
            outcome = "lost"
        lesson(world, child, elder, route, outcome)

    changed_ending(world, child, elder, safeguard, route, errand, outcome)
    world.facts.update(
        child=child,
        elder=elder,
        parcel=parcel,
        route_cfg=route,
        errand_cfg=errand,
        safeguard_cfg=safeguard,
        rescue_cfg=rescue,
        outcome=outcome,
        delay=delay,
        heed=outcome == "heeded",
        parcel_damaged=parcel.meters["damaged"] >= THRESHOLD,
        trust=trust,
    )
    return world


KNOWLEDGE = {
    "ford": [
        (
            "What is a ford?",
            "A ford is a shallow place where people cross a stream or river on foot. It can still be dangerous when the light is poor or the water moves fast.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than splashing through water?",
            "A bridge gives your feet firm ground above the water. That means the stream cannot tug at your legs or soak what you are carrying.",
        )
    ],
    "ferry": [
        (
            "What does a ferry do?",
            "A ferry carries people and bundles across water in a boat. It is useful when the water is not a good place for walking.",
        )
    ],
    "lantern": [
        (
            "Why does a lantern help on a dark path?",
            "A lantern shows roots, stones, and holes before your feet find them by surprise. Good light makes it easier to walk slowly and safely.",
        )
    ],
    "dawn": [
        (
            "Why can waiting until morning be wise?",
            "Morning light lets you see the road clearly. A little waiting can stop a great deal of trouble.",
        )
    ],
    "rescue": [
        (
            "Why should you call an adult when a path turns dangerous?",
            "A grown-up can help faster and more safely than another child can. Asking for help early keeps a small mistake from growing bigger.",
        )
    ],
    "eggs": [
        (
            "Why do eggs break easily?",
            "Eggshells are thin and brittle. A hard bump or a fall can crack them at once.",
        )
    ],
    "cakes": [
        (
            "What happens to cakes if they get wet and muddy?",
            "Wet, muddy cakes are spoiled and cannot be shared the way they should be. Food needs to stay clean to be eaten safely.",
        )
    ],
    "seeds": [
        (
            "Why should seed sacks stay dry?",
            "Seeds meant for planting or storage can spoil when they get too wet. A dry sack keeps them useful.",
        )
    ],
    "woods": [
        (
            "Why can a path be hard to follow in the dark woods?",
            "In dim light, roots and turns can all look alike. That makes it easy to miss the right way.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ford",
    "bridge",
    "ferry",
    "lantern",
    "dawn",
    "rescue",
    "eggs",
    "cakes",
    "seeds",
    "woods",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    route = f["route_cfg"]
    errand = f["errand_cfg"]
    outcome = f["outcome"]
    if outcome == "heeded":
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the word "card-dim" and an elder warning a child away from {route.label}.',
            f"Tell a cautionary story with a flashback where {child.id} is carrying {errand.short} and listens to an elder's old memory before choosing the safe road.",
            f"Write a gentle folk-style story where a hurried child almost takes {route.label} in the card-dim evening, but wisdom wins before any harm is done.",
        ]
    if outcome == "rescued":
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the word "card-dim", a dangerous shortcut, and a rescue.',
            f"Tell a cautionary flashback story where {child.id} ignores an elder's memory about {route.label}, gets into trouble, and is saved in time.",
            f"Write a folk tale in which a child carrying {errand.short} learns that the shortest road is not the safest one.",
        ]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "card-dim", a warning, and a costly mistake.',
        f"Tell a cautionary flashback story where {child.id} ignores an elder's memory about {route.label} and loses what was being carried.",
        f"Write a folk-style lesson tale in which a child hurries into trouble at dusk and learns why old warnings matter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    route = f["route_cfg"]
    errand = f["errand_cfg"]
    safeguard = f["safeguard_cfg"]
    rescue = f["rescue_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child hurrying along an evening errand, and {child.pronoun('possessive')} {elder.kin_word} who tried to keep {child.pronoun('object')} safe.",
        ),
        (
            f"What was {child.id} carrying, and where was it going?",
            f"{child.pronoun().capitalize()} was carrying {errand.phrase} to {errand.destination}. The bundle mattered because a bad crossing could spoil it as well as frighten the child.",
        ),
        (
            f"Why did the elder warn {child.id} away from {route.label}?",
            f"The elder knew {route.label} was risky in the card-dim evening and even told a flashback about making the same mistake long ago. The warning came from memory and from seeing how much trouble that path could cause.",
        ),
        (
            "What was the flashback about?",
            f"The elder remembered taking {route.label} when young and losing control of the crossing. That old mistake is why the warning sounded so serious.",
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"How did {child.id} solve the problem?",
                f"{child.pronoun().capitalize()} listened and chose {safeguard.label} instead of the shortcut. That made the trip slower, but it kept both the child and the bundle safe.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a safe arrival and a changed habit. After that, {child.id} asked where the safe road was whenever the light grew card-dim.",
            )
        )
    elif outcome == "rescued":
        qa.append(
            (
                f"What happened when {child.id} ignored the warning?",
                f"{child.pronoun().capitalize()} ran onto {route.label} and got into trouble there. The danger proved the elder's old story was not just talk.",
            )
        )
        qa.append(
            (
                f"How was {child.id} saved?",
                f"The elder {rescue.qa_text}. The rescue mattered because the route had already become too dangerous for a child to manage alone.",
            )
        )
        if f["parcel_damaged"]:
            qa.append(
                (
                    "What happened to the bundle?",
                    f"It was damaged in the mishap. The loss showed that hurrying can spoil the very thing a child is trying to protect.",
                )
            )
        else:
            qa.append(
                (
                    "What happened to the bundle?",
                    f"It was shaken, but it stayed safe. Even so, the scare taught {child.id} that luck is not the same thing as wisdom.",
                )
            )
        qa.append(
            (
                "What changed by the end?",
                f"By the next errand, {child.id} chose the safer road without being told. The lesson stuck because the danger had felt real in {child.pronoun('possessive')} own body.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} ignored the warning?",
                f"{child.pronoun().capitalize()} ran onto {route.label}, got into trouble, and came back safe only after losing the bundle's good condition. The elder's flashback turned into a second warning told by consequence.",
            )
        )
        qa.append(
            (
                "What was lost?",
                f"{errand.damage_text.capitalize()}. That loss is the heart of the cautionary lesson, because the child hurried in order to protect time and ended by ruining what was being carried.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a sadder but wiser child who would not choose that shortcut again. The final change is shown when {child.id} turns away from {route.label} on later evenings.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["route_cfg"].tags) | set(f["safeguard_cfg"].tags) | set(f["errand_cfg"].tags)
    if f["outcome"] != "heeded":
        tags |= {"rescue"}
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    if value:
                        shown[key] = sorted(value)
                elif value:
                    shown[key] = value
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonableness gate: a safeguard is valid for a route only when it covers all
% of the route's risk kinds.
missing_cover(Route, Safe, Risk) :- route(Route), safeguard(Safe), risk(Route, Risk), not covers(Safe, Risk).
valid(Route, Safe) :- route(Route), safeguard(Safe), not missing_cover(Route, Safe, _).

% Rescue common-sense gate.
sensible_rescue(R) :- rescue(R), rescue_sense(R, S), sense_min(M), S >= M.

% Outcome model.
trait_bonus(3) :- chosen_trait(T), wise_trait(T).
trait_bonus(0) :- chosen_trait(T), not wise_trait(T).
elder_bonus(2) :- chosen_elder(grandmother).
elder_bonus(2) :- chosen_elder(grandfather).
elder_bonus(1) :- chosen_elder(aunt).
elder_bonus(1) :- chosen_elder(uncle).
age_bonus(1) :- chosen_child_age(A), A <= 6.
age_bonus(0) :- chosen_child_age(A), A > 6.
heed_score(T + Tr + E + A) :- chosen_trust(T), trait_bonus(Tr), elder_bonus(E), age_bonus(A).
heeded :- heed_score(S), S >= 9.

trouble(Route, Sev + D) :- chosen_route(Route), route_severity(Route, Sev), chosen_delay(D).
rescue_power(P) :- chosen_rescue(R), rescue_power_fact(R, P).
rescued :- not heeded, trouble(_, T), rescue_power(P), P >= T.

outcome(heeded) :- heeded.
outcome(rescued) :- not heeded, rescued.
outcome(lost) :- not heeded, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_severity", route_id, route.severity))
        for risk in sorted(route.risks):
            lines.append(asp.fact("risk", route_id, risk))
    for safeguard_id, safeguard in SAFEGUARDS.items():
        lines.append(asp.fact("safeguard", safeguard_id))
        lines.append(asp.fact("sense", safeguard_id, safeguard.sense))
        for risk in sorted(safeguard.covers):
            lines.append(asp.fact("covers", safeguard_id, risk))
    for rescue_id, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("rescue_sense", rescue_id, rescue.sense))
        lines.append(asp.fact("rescue_power_fact", rescue_id, rescue.power))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rescues() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_rescue/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_rescue"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_rescue", params.rescue),
            asp.fact("chosen_trait", params.child_trait),
            asp.fact("chosen_trust", params.trust),
            asp.fact("chosen_elder", params.elder_type),
            asp.fact("chosen_child_age", params.child_age),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a hurried child, a flashback warning, and a risky folk-tale shortcut."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--safeguard", choices=SAFEGUARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--child-age", type=int, choices=[5, 6, 7, 8, 9])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the route/safeguard set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.safeguard:
        if not valid_combo(args.route, args.safeguard):
            raise StoryError(explain_route_safeguard(ROUTES[args.route], SAFEGUARDS[args.safeguard]))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.safeguard is None or combo[1] == args.safeguard)
    ]
    if not combos:
        raise StoryError("(No valid route/safeguard combination matches the given options.)")

    route_id, safeguard_id = rng.choice(sorted(combos))
    errand_id = args.errand or rng.choice(sorted(ERRANDS))
    rescue_id = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    child_trait = args.trait or rng.choice(CHILD_TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    child_age = args.child_age if args.child_age is not None else rng.choice([5, 6, 7, 8, 9])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        route=route_id,
        errand=errand_id,
        safeguard=safeguard_id,
        rescue=rescue_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        trust=trust,
        child_age=child_age,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.errand not in ERRANDS:
        raise StoryError(f"(Unknown errand: {params.errand})")
    if params.safeguard not in SAFEGUARDS:
        raise StoryError(f"(Unknown safeguard: {params.safeguard})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if not valid_combo(params.route, params.safeguard):
        raise StoryError(explain_route_safeguard(ROUTES[params.route], SAFEGUARDS[params.safeguard]))
    if RESCUES[params.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        route=ROUTES[params.route],
        errand=ERRANDS[params.errand],
        safeguard=SAFEGUARDS[params.safeguard],
        rescue=RESCUES[params.rescue],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        trust=params.trust,
        child_age=params.child_age,
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


CURATED = [
    StoryParams(
        route="ford",
        errand="cakes",
        safeguard="bridge",
        rescue="hook",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="careful",
        trust=8,
        child_age=6,
        delay=0,
        seed=None,
    ),
    StoryParams(
        route="log",
        errand="eggs",
        safeguard="lantern",
        rescue="hook",
        child_name="Tobin",
        child_gender="boy",
        elder_type="uncle",
        child_trait="eager",
        trust=4,
        child_age=8,
        delay=0,
        seed=None,
    ),
    StoryParams(
        route="marsh",
        errand="seeds",
        safeguard="bridge",
        rescue="boat",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandfather",
        child_trait="hasty",
        trust=3,
        child_age=7,
        delay=1,
        seed=None,
    ),
    StoryParams(
        route="hollow",
        errand="eggs",
        safeguard="dawn",
        rescue="hook",
        child_name="Rowan",
        child_gender="boy",
        elder_type="aunt",
        child_trait="thoughtful",
        trust=7,
        child_age=5,
        delay=0,
        seed=None,
    ),
    StoryParams(
        route="ford",
        errand="seeds",
        safeguard="ferry",
        rescue="boat",
        child_name="Elsie",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="restless",
        trust=2,
        child_age=8,
        delay=1,
        seed=None,
    ),
]


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: route/safeguard gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid route/safeguard combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_rescues = {r.id for r in sensible_rescues()}
    asp_rescues = set(asp_sensible_rescues())
    if py_rescues == asp_rescues:
        print(f"OK: sensible rescues match ({sorted(py_rescues)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(asp_rescues)} python={sorted(py_rescues)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            case = resolve_params(parser.parse_args([]), random.Random(seed))
            case.seed = seed
            cases.append(case)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {seed}.")
            break

    mismatches = 0
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    smoke = cases[:5]
    for idx, case in enumerate(smoke, 1):
        try:
            sample = generate(case)
            if not sample.story.strip():
                raise StoryError("empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=True, header=f"smoke {idx}")
        except Exception as err:  # pragma: no cover - defensive for verification mode
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            break
    else:
        print(f"OK: smoke-tested normal generate/emit on {len(smoke)} cases.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible_rescue/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_combos()
        rescues = asp_sensible_rescues()
        print(f"sensible rescues: {', '.join(rescues)}\n")
        print(f"{len(valid)} compatible (route, safeguard) combos:\n")
        for route_id, safeguard_id in valid:
            print(f"  {route_id:8} {safeguard_id}")
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
            header = (
                f"### {p.child_name}: {p.route} / {p.errand} / "
                f"{p.safeguard} / {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
