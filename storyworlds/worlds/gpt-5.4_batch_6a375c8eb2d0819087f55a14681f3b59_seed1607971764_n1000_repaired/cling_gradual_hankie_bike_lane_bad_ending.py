#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py
=======================================================================

A standalone story world for a tall-tale bike-lane cautionary story built around
a dangling cloth, a gradual snag, and a bad ending with a clear moral.

Premise
-------
A child rides proudly in the bike lane and ties a cloth to the bike as a fluttering
flag. A wiser helper warns that the cloth can cling to the spinning wheel. The
danger does not happen all at once: turn by turn, the cloth wraps farther into the
spokes, the wobble grows, and the ride ends badly. The child learns that decorations
and dangling things do not belong near moving wheels.

This world favors a small number of plausible variants over weak coverage:
only cloths long enough to reach the wheel from the chosen tie spot are allowed.

Run it
------
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py --cloth hankie --spot handlebar
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py --spot helmet_strap
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py --all
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py --qa --json
python storyworlds/worlds/gpt-5.4/cling_gradual_hankie_bike_lane_bad_ending.py --verify
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
WRAP_THRESHOLD = 2
CRASH_THRESHOLD = 3


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
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Bike:
    id: str
    label: str
    boast: str
    ring: str
    wheel_reach: int
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
class Cloth:
    id: str
    label: str
    phrase: str
    length: int
    flutter: str
    lesson: str
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
class TieSpot:
    id: str
    label: str
    phrase: str
    height: int
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
class Cargo:
    id: str
    label: str
    phrase: str
    spill: str
    loss: str
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
class HelperKind:
    id: str
    type: str
    label: str
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
class StoryParams:
    bike: str
    cloth: str
    spot: str
    cargo: str
    helper_kind: str
    rider_name: str
    rider_gender: str
    helper_name: str
    helper_gender: str
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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
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


def _r_wrap(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.get("cloth")
    bike = world.get("bike")
    rider = world.get("rider")
    if cloth.meters["dangling"] < THRESHOLD or bike.meters["rolling"] < THRESHOLD:
        return out
    if rider.meters["wrap_steps"] >= WRAP_THRESHOLD:
        return out
    sig = ("wrap", int(rider.meters["wrap_steps"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.meters["wrap_steps"] += 1
    cloth.meters["wrapped"] += 1
    bike.meters["drag"] += 1
    rider.memes["unease"] += 1
    out.append("__wrap__")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    bike = world.get("bike")
    rider = world.get("rider")
    if bike.meters["drag"] < THRESHOLD:
        return out
    level = int(bike.meters["drag"])
    sig = ("wobble", level)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bike.meters["wobble"] += 1
    rider.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_crash(world: World) -> list[str]:
    out: list[str] = []
    bike = world.get("bike")
    rider = world.get("rider")
    if rider.meters["crashed"] >= THRESHOLD:
        return out
    if bike.meters["wobble"] + world.facts.get("delay", 0) < CRASH_THRESHOLD:
        return out
    sig = ("crash",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.meters["crashed"] += 1
    rider.meters["scraped_knee"] += 1
    bike.meters["bent"] += 1
    rider.memes["shock"] += 1
    out.append("__crash__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wrap", tag="physical", apply=_r_wrap),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="crash", tag="physical", apply=_r_crash),
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


def can_reach_wheel(bike: Bike, cloth: Cloth, spot: TieSpot) -> bool:
    return cloth.length >= max(1, bike.wheel_reach - spot.height)


def crash_level(bike: Bike, cloth: Cloth, spot: TieSpot, delay: int) -> int:
    base = cloth.length - spot.height + bike.wheel_reach + delay
    return max(0, base)


def outcome_of(params: StoryParams) -> str:
    bike = BIKES[params.bike]
    cloth = CLOTHS[params.cloth]
    spot = SPOTS[params.spot]
    sev = crash_level(bike, cloth, spot, params.delay)
    return "hard_crash" if sev >= 5 else "crash"


def predict_crash(world: World) -> dict:
    sim = world.copy()
    rider = sim.get("rider")
    bike = sim.get("bike")
    cloth = sim.get("cloth")
    bike.meters["rolling"] += 1
    cloth.meters["dangling"] += 1
    for _ in range(3):
        propagate(sim, narrate=False)
    return {
        "wrapped": sim.get("cloth").meters["wrapped"],
        "wobble": sim.get("bike").meters["wobble"],
        "crashed": sim.get("rider").meters["crashed"] >= THRESHOLD,
    }


def introduce(world: World, rider: Entity, bike_cfg: Bike, cargo_cfg: Cargo) -> None:
    rider.memes["pride"] += 1
    world.say(
        f"In the bike lane by the market, {rider.id} came rolling along on {bike_cfg.label}, "
        f"and the little bike looked ready to race the sunrise itself. {bike_cfg.boast}"
    )
    world.say(
        f"{rider.id} carried {cargo_cfg.phrase} in a wobble-basket and rang the bell "
        f"so proudly that even the pigeons seemed to march to the tune: {bike_cfg.ring}"
    )


def tie_cloth(world: World, rider: Entity, cloth_cfg: Cloth, spot_cfg: TieSpot) -> None:
    cloth = world.get("cloth")
    cloth.meters["dangling"] += 1
    rider.memes["showoff"] += 1
    world.say(
        f"Before the next turn, {rider.id} pulled out {cloth_cfg.phrase} and tied it to "
        f"{spot_cfg.phrase}. {cloth_cfg.flutter.capitalize()} behind the bike like a tiny parade flag."
    )
    if cloth_cfg.id == "hankie":
        world.say(
            f'"Now that is a champion\'s hankie," {rider.id} said. "It will cling to my glory all the way down the lane."'
        )


def warn(world: World, helper: Entity, rider: Entity, cloth_cfg: Cloth, spot_cfg: TieSpot) -> None:
    pred = predict_crash(world)
    world.facts["predicted_crash"] = pred["crashed"]
    world.facts["predicted_wobble"] = int(pred["wobble"])
    helper.memes["care"] += 1
    rider.memes["warned"] += 1
    extra = " and there will be trouble before the next painted line" if pred["crashed"] else ""
    world.say(
        f"{helper.id} called from the edge of the bike lane, "
        f'"{rider.id}, take that {cloth_cfg.label} off {spot_cfg.label}. If it starts to cling to the wheel, it will pull and wobble{extra}."'
    )


def defy(world: World, rider: Entity, helper: Entity) -> None:
    rider.memes["defiance"] += 1
    world.say(
        f"But {rider.id} was full of tall-talk courage. "
        f'"A bit of cloth cannot boss around my bike," {rider.pronoun()} said, and {rider.pronoun()} pedaled harder while {helper.id} hurried after {rider.pronoun("object")}.'
    )


def gradual_snag(world: World, rider: Entity, bike_cfg: Bike, cloth_cfg: Cloth) -> None:
    bike = world.get("bike")
    cloth = world.get("cloth")
    bike.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At first nothing happened but a whisper. The {cloth_cfg.label} kissed one spoke, then another, "
        f"so lightly that it seemed to be playing a game."
    )
    bike.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the trouble turned gradual. With every wheel-turn, the cloth began to cling more tightly, "
        f"wrapping itself inward as neatly as a spider winding thread around a fly."
    )
    bike.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon {bike_cfg.label} gave a sideways shiver. The handlebars twitched, the basket bobbed, and "
        f"{rider.id}'s grin slipped away."
    )


def crash_scene(world: World, rider: Entity, helper: Entity, cargo_cfg: Cargo, bike_cfg: Bike) -> None:
    hard = world.facts["outcome"] == "hard_crash"
    rider.memes["regret"] += 1
    rider.memes["fear"] += 1
    world.say(
        f'"Stop!" shouted {helper.id}, but the bike had already chosen its own wild dance.'
    )
    if hard:
        world.say(
            f"The front wheel locked with a jerk so sharp it might have startled a thundercloud. "
            f"{rider.id} flew over the side of {bike_cfg.label}, and {cargo_cfg.spill}."
        )
        world.say(
            f"When the clatter stopped, the lane was a sorry little kingdom of trouble: {cargo_cfg.loss}, "
            f"the bell bent sideways, and one knee stung hotter than a pepper patch."
        )
    else:
        world.say(
            f"The wheel snagged, the bike slewed, and {rider.id} toppled in a clanking heap. "
            f"{cargo_cfg.spill}."
        )
        world.say(
            f"When the dust settled, {cargo_cfg.loss}, the basket leaned crooked, and one knee was scraped bright pink."
        )


def ending(world: World, rider: Entity, helper: Entity, cloth_cfg: Cloth) -> None:
    helper.memes["comfort"] += 1
    rider.memes["lesson"] += 1
    world.say(
        f"{helper.id} helped {rider.id} up and pressed a clean cloth to the scraped knee. "
        f'No one laughed. Even the bike lane seemed to hold its breath.'
    )
    world.say(
        f'"I wanted a grand flag," {rider.id} whispered, staring at the twisted {cloth_cfg.label}.'
    )
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "A wheel needs room, not ribbons. {cloth_cfg.lesson}"'
    )
    world.say(
        f"So {rider.id} walked home beside the bent bike instead of riding it, with the ruined cloth folded small in a pocket. "
        f"The bell did not sing at all, and that quiet was the lesson."
    )


def tell(
    bike_cfg: Bike,
    cloth_cfg: Cloth,
    spot_cfg: TieSpot,
    cargo_cfg: Cargo,
    helper_cfg: HelperKind,
    rider_name: str,
    rider_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    rider = world.add(
        Entity(
            id=rider_name,
            kind="character",
            type=rider_gender,
            role="rider",
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            attrs={"kind": helper_cfg.id},
        )
    )
    bike = world.add(Entity(id="bike", type="bike", label=bike_cfg.label))
    cloth = world.add(Entity(id="cloth", type="cloth", label=cloth_cfg.label))
    cargo = world.add(Entity(id="cargo", type="cargo", label=cargo_cfg.label))

    world.facts.update(
        bike_cfg=bike_cfg,
        cloth_cfg=cloth_cfg,
        spot_cfg=spot_cfg,
        cargo_cfg=cargo_cfg,
        helper_cfg=helper_cfg,
        rider=rider,
        helper=helper,
        bike=bike,
        cloth=cloth,
        cargo=cargo,
        delay=delay,
        outcome="",
    )

    introduce(world, rider, bike_cfg, cargo_cfg)
    world.say(helper_cfg.opening.format(helper=helper.id, rider=rider.id))
    world.para()
    tie_cloth(world, rider, cloth_cfg, spot_cfg)
    warn(world, helper, rider, cloth_cfg, spot_cfg)
    defy(world, rider, helper)
    world.para()
    gradual_snag(world, rider, bike_cfg, cloth_cfg)
    world.facts["outcome"] = outcome_of(
        StoryParams(
            bike=bike_cfg.id,
            cloth=cloth_cfg.id,
            spot=spot_cfg.id,
            cargo=cargo_cfg.id,
            helper_kind=helper_cfg.id,
            rider_name=rider_name,
            rider_gender=rider_gender,
            helper_name=helper_name,
            helper_gender=helper_gender,
            trait=trait,
            delay=delay,
        )
    )
    crash_scene(world, rider, helper, cargo_cfg, bike_cfg)
    world.para()
    ending(world, rider, helper, cloth_cfg)
    return world


BIKES = {
    "comet": Bike(
        id="comet",
        label="a silver bike called the Comet",
        boast="It had a shine like moonlight on a fish and tires that looked eager to gobble up the painted lane.",
        ring="tring-tring",
        wheel_reach=3,
        tags={"bike", "bell"},
    ),
    "thunder": Bike(
        id="thunder",
        label="a red bike called Thunder-Toes",
        boast="Its red frame flashed so brightly that tomatoes at the market might have blushed to see it.",
        ring="clang-a-ling",
        wheel_reach=4,
        tags={"bike", "bell"},
    ),
    "minnow": Bike(
        id="minnow",
        label="a blue bike called the Minnow",
        boast="It was smaller than a pony but acted in {that} heart as if it could outrun the river."
        .replace("{that}", "its"),
        ring="plink-plink",
        wheel_reach=2,
        tags={"bike", "bell"},
    ),
}

CLOTHS = {
    "hankie": Cloth(
        id="hankie",
        label="hankie",
        phrase="a bright blue hankie",
        length=3,
        flutter="it fluttered and snapped",
        lesson="A dangling hankie belongs in a pocket or a waving hand, never near a moving wheel.",
        tags={"hankie", "cloth"},
    ),
    "scarf": Cloth(
        id="scarf",
        label="scarf",
        phrase="a striped scarf",
        length=4,
        flutter="it streamed and danced",
        lesson="A long scarf may look grand, but it can catch where spinning parts cannot forgive it.",
        tags={"cloth"},
    ),
    "ribbon": Cloth(
        id="ribbon",
        label="ribbon",
        phrase="a yellow ribbon",
        length=2,
        flutter="it flickered and fluttered",
        lesson="Even a pretty ribbon can turn mean when it tangles in a spinning wheel.",
        tags={"cloth"},
    ),
}

SPOTS = {
    "handlebar": TieSpot(
        id="handlebar",
        label="the handlebar",
        phrase="the right handlebar",
        height=0,
        tags={"bike"},
    ),
    "basket_rim": TieSpot(
        id="basket_rim",
        label="the basket rim",
        phrase="the front basket rim",
        height=1,
        tags={"bike"},
    ),
    "seat_post": TieSpot(
        id="seat_post",
        label="the seat post",
        phrase="the seat post behind the saddle",
        height=1,
        tags={"bike"},
    ),
    "helmet_strap": TieSpot(
        id="helmet_strap",
        label="the helmet strap",
        phrase="the loose helmet strap",
        height=4,
        tags={"helmet"},
    ),
}

CARGO = {
    "peaches": Cargo(
        id="peaches",
        label="peaches",
        phrase="a basket of peaches",
        spill="peaches bounced out in every direction like little orange marbles",
        loss="half the peaches were bruised open",
        tags={"fruit", "market"},
    ),
    "cupcakes": Cargo(
        id="cupcakes",
        label="cupcakes",
        phrase="a box of frosted cupcakes",
        spill="the cupcakes somersaulted out and painted the lane with pink frosting",
        loss="the frosting was smashed flat and the paper wrappers were torn",
        tags={"food", "market"},
    ),
    "eggs": Cargo(
        id="eggs",
        label="eggs",
        phrase="a carton of eggs",
        spill="the eggs leapt free and cracked in pale puddles",
        loss="breakfast was lost in a sticky mess",
        tags={"food", "market"},
    ),
}

HELPERS = {
    "mother": HelperKind(
        id="mother",
        type="mother",
        label="mom",
        opening="{helper}, {rider}'s mom, was walking nearby with a shopping sack and an eye for trouble.",
        tags={"family"},
    ),
    "uncle": HelperKind(
        id="uncle",
        type="uncle",
        label="uncle",
        opening="{helper}, {rider}'s uncle, strode along beside the lane as if he had once raced the wind itself.",
        tags={"family"},
    ),
    "friend": HelperKind(
        id="friend",
        type="boy",
        label="friend",
        opening="{helper} pedaled a little behind, close enough to hear every boast and every bell-ring.",
        tags={"friend"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Maya", "Sadie"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["bold", "showy", "stubborn", "eager", "boastful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for bike_id, bike in BIKES.items():
        for cloth_id, cloth in CLOTHS.items():
            for spot_id, spot in SPOTS.items():
                if not can_reach_wheel(bike, cloth, spot):
                    continue
                for cargo_id in CARGO:
                    combos.append((bike_id, cloth_id, spot_id, cargo_id))
    return combos


def explain_rejection(bike: Bike, cloth: Cloth, spot: TieSpot) -> str:
    return (
        f"(No story: {cloth.phrase} tied to {spot.label} would not reach the wheel of {bike.label}. "
        f"If the cloth cannot reach the spokes, it cannot cling, wrap, or cause the gradual bike-lane crash.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rider = f["rider"]
    cloth = f["cloth_cfg"]
    cargo = f["cargo_cfg"]
    return [
        f'Write a tall-tale cautionary story for a 3-to-5-year-old set in a bike lane that includes the word "{cloth.label}".',
        f"Tell a tall tale where {rider.id} ties {cloth.phrase} to a bike, ignores a warning, and the danger arrives in a gradual way before a bad ending.",
        f"Write a moral story about a child showing off in a bike lane with {cargo.phrase}, where a dangling cloth starts small and ends in trouble.",
    ]


KNOWLEDGE = {
    "bike": [
        (
            "Why should dangling things stay away from bicycle wheels?",
            "A bicycle wheel spins fast, and a dangling thing can get caught in the spokes or axle. When that happens, the wheel can wobble or stop suddenly."
        )
    ],
    "hankie": [
        (
            "What is a hankie?",
            "A hankie is a small square cloth, like a handkerchief. People use it to wipe a nose, wave hello, or keep it folded in a pocket."
        )
    ],
    "cloth": [
        (
            "Why can cloth be dangerous near moving parts?",
            "Cloth bends and flaps, so it can drift into places where it does not belong. A spinning part can grab it before you notice."
        )
    ],
    "helmet": [
        (
            "What does a helmet strap do?",
            "A helmet strap keeps a helmet on your head. It should be snug and tidy so it does not flap around."
        )
    ],
    "bell": [
        (
            "What is a bike bell for?",
            "A bike bell makes a clear sound to let other people know you are coming. It helps riders share the path safely."
        )
    ],
    "market": [
        (
            "Why can a bike basket spill when a bike tips over?",
            "When a bike tips, the basket tips too, and loose things slide or bounce out. That is why riders carry breakable things carefully."
        )
    ],
    "family": [
        (
            "Why do grown-ups warn children about small dangers?",
            "Grown-ups notice how little problems can turn into bigger ones. A warning can save pain if the child listens in time."
        )
    ],
    "friend": [
        (
            "What can a good friend do when something looks unsafe?",
            "A good friend speaks up and warns you, even if it spoils the fun for a moment. Caring means trying to stop hurt before it happens."
        )
    ],
    "fruit": [
        (
            "Why do peaches bruise when they fall?",
            "Peaches are soft, so a hard bump can squash their skin and flesh. That leaves brown, mushy spots."
        )
    ],
    "food": [
        (
            "Why can eggs or cupcakes be ruined in a tumble?",
            "Eggs crack easily, and cupcakes squash when they are bumped. Soft or fragile food does not stay neat in a crash."
        )
    ],
}
KNOWLEDGE_ORDER = ["bike", "hankie", "cloth", "helmet", "bell", "market", "family", "friend", "fruit", "food"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    helper = f["helper"]
    bike_cfg = f["bike_cfg"]
    cloth_cfg = f["cloth_cfg"]
    spot_cfg = f["spot_cfg"]
    cargo_cfg = f["cargo_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {rider.id}, who rode proudly in the bike lane, and {helper.id}, who warned about the danger. The trouble began when {rider.id} tied {cloth_cfg.phrase} to {spot_cfg.label}."
        ),
        (
            f"Why did {helper.id} warn {rider.id}?",
            f"{helper.id} warned {rider.id} because the {cloth_cfg.label} could cling to the wheel and make the bike wobble. The warning came before the crash, when the danger was still small enough to stop."
        ),
        (
            "How did the trouble happen?",
            f"It happened in a gradual way. First the {cloth_cfg.label} brushed the spokes, then it wrapped tighter and tighter, and only after that did the bike lose control."
        ),
    ]
    if outcome == "hard_crash":
        qa.append(
            (
                f"What bad ending happened to {rider.id}?",
                f"{rider.id} had a hard crash, scraped a knee, and bent the bike. {cargo_cfg.spill.capitalize()}, so the fall hurt both {rider.id} and the things in the basket."
            )
        )
    else:
        qa.append(
            (
                f"What bad ending happened to {rider.id}?",
                f"{rider.id} toppled in the bike lane, scraped a knee, and left the bike crooked. {cargo_cfg.spill.capitalize()}, which shows how one silly choice spoiled the whole ride."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that dangling cloth does not belong near a moving wheel. A small unsafe choice can grow into a big problem if you keep going instead of stopping."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bike_cfg"].tags) | set(f["cloth_cfg"].tags) | set(f["spot_cfg"].tags) | set(f["cargo_cfg"].tags) | set(
        f["helper_cfg"].tags
    )
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} delay={world.facts.get('delay')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bike="comet",
        cloth="hankie",
        spot="handlebar",
        cargo="peaches",
        helper_kind="mother",
        rider_name="Lily",
        rider_gender="girl",
        helper_name="Mara",
        helper_gender="mother",
        trait="boastful",
        delay=0,
    ),
    StoryParams(
        bike="thunder",
        cloth="scarf",
        spot="basket_rim",
        cargo="eggs",
        helper_kind="uncle",
        rider_name="Tom",
        rider_gender="boy",
        helper_name="Uncle Ned",
        helper_gender="uncle",
        trait="bold",
        delay=1,
    ),
    StoryParams(
        bike="minnow",
        cloth="hankie",
        spot="seat_post",
        cargo="cupcakes",
        helper_kind="friend",
        rider_name="Mia",
        rider_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        trait="showy",
        delay=0,
    ),
    StoryParams(
        bike="thunder",
        cloth="hankie",
        spot="handlebar",
        cargo="cupcakes",
        helper_kind="mother",
        rider_name="Eli",
        rider_gender="boy",
        helper_name="June",
        helper_gender="mother",
        trait="stubborn",
        delay=1,
    ),
    StoryParams(
        bike="comet",
        cloth="ribbon",
        spot="basket_rim",
        cargo="eggs",
        helper_kind="friend",
        rider_name="Nora",
        rider_gender="girl",
        helper_name="Sam",
        helper_gender="boy",
        trait="eager",
        delay=0,
    ),
]


ASP_RULES = r"""
reachable(B,C,S) :- bike(B), cloth(C), spot(S), wheel_reach(B, WR), length(C, L), height(S, H), L >= WR - H, WR - H >= 1.
reachable(B,C,S) :- bike(B), cloth(C), spot(S), wheel_reach(B, WR), height(S, H), WR - H < 1, length(C, L), L >= 1.
valid(B,C,S,G) :- bike(B), cloth(C), spot(S), cargo(G), reachable(B,C,S).

severity(B,C,S,D, V) :- wheel_reach(B, WR), length(C, L), height(S, H), delay(D), V = L - H + WR + D.
outcome(crash) :- chosen_bike(B), chosen_cloth(C), chosen_spot(S), chosen_delay(D), severity(B,C,S,D,V), V < 5.
outcome(hard_crash) :- chosen_bike(B), chosen_cloth(C), chosen_spot(S), chosen_delay(D), severity(B,C,S,D,V), V >= 5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bike_id, bike in BIKES.items():
        lines.append(asp.fact("bike", bike_id))
        lines.append(asp.fact("wheel_reach", bike_id, bike.wheel_reach))
    for cloth_id, cloth in CLOTHS.items():
        lines.append(asp.fact("cloth", cloth_id))
        lines.append(asp.fact("length", cloth_id, cloth.length))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("height", spot_id, spot.height))
    for cargo_id in CARGO:
        lines.append(asp.fact("cargo", cargo_id))
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
            asp.fact("chosen_bike", params.bike),
            asp.fact("chosen_cloth", params.cloth),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_delay", params.delay),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale bike-lane cautionary storyworld with a dangling cloth, a gradual snag, and a bad ending."
    )
    ap.add_argument("--bike", choices=BIKES)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--helper-kind", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra head start for the snag before control is lost")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bike and args.cloth and args.spot:
        bike = BIKES[args.bike]
        cloth = CLOTHS[args.cloth]
        spot = SPOTS[args.spot]
        if not can_reach_wheel(bike, cloth, spot):
            raise StoryError(explain_rejection(bike, cloth, spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.bike is None or combo[0] == args.bike)
        and (args.cloth is None or combo[1] == args.cloth)
        and (args.spot is None or combo[2] == args.spot)
        and (args.cargo is None or combo[3] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bike_id, cloth_id, spot_id, cargo_id = rng.choice(sorted(combos))
    helper_kind = args.helper_kind or rng.choice(sorted(HELPERS))
    rider_gender = rng.choice(["girl", "boy"])
    helper_gender = HELPERS[helper_kind].type if helper_kind in {"mother", "uncle"} else rng.choice(["girl", "boy"])
    rider_name = _pick_name(rng, rider_gender)
    helper_name = (
        _pick_name(rng, helper_gender if helper_gender in {"girl", "boy"} else "girl", avoid=rider_name)
        if helper_kind == "friend"
        else ("Aunt May" if helper_kind == "mother" and helper_gender == "aunt" else ("Mara" if helper_kind == "mother" else "Uncle Ned"))
    )
    if helper_kind == "mother":
        helper_name = rng.choice(["Mara", "June", "Rosa", "Nell"])
        helper_gender = "mother"
    elif helper_kind == "uncle":
        helper_name = rng.choice(["Uncle Ned", "Uncle Ray", "Uncle Joe"])
        helper_gender = "uncle"
    else:
        helper_name = _pick_name(rng, rng.choice(["girl", "boy"]), avoid=rider_name)
        helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        bike=bike_id,
        cloth=cloth_id,
        spot=spot_id,
        cargo=cargo_id,
        helper_kind=helper_kind,
        rider_name=rider_name,
        rider_gender=rider_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        bike_cfg = BIKES[params.bike]
        cloth_cfg = CLOTHS[params.cloth]
        spot_cfg = SPOTS[params.spot]
        cargo_cfg = CARGO[params.cargo]
        helper_cfg = HELPERS[params.helper_kind]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from None

    if not can_reach_wheel(bike_cfg, cloth_cfg, spot_cfg):
        raise StoryError(explain_rejection(bike_cfg, cloth_cfg, spot_cfg))

    world = tell(
        bike_cfg=bike_cfg,
        cloth_cfg=cloth_cfg,
        spot_cfg=spot_cfg,
        cargo_cfg=cargo_cfg,
        helper_cfg=helper_cfg,
        rider_name=params.rider_name,
        rider_gender=params.rider_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        trait=params.trait,
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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            mismatches.append((params, ao, po))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

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
        print(f"{len(combos)} compatible (bike, cloth, spot, cargo) combos:\n")
        for bike, cloth, spot, cargo in combos:
            print(f"  {bike:8} {cloth:8} {spot:12} {cargo}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.rider_name}: {p.cloth} on {p.spot} ({p.bike}, {p.cargo}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
