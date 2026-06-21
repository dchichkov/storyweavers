#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py
============================================================================

A standalone story world in a tall-tale register: two children on a windy farm
must solve a runaway-clothes problem together. The domain is built around a
simple causal core:

    giant gust + loose garment -> garment airborne
    airborne garment           -> scarecrow nude
    airborne garment           -> yard danger + animal panic
    animal panic               -> ruckus

The story always includes the words "aleck", "nude", and "ruckus" in natural
prose. The emotional turn comes from a braggy "I can do it myself" moment, but
the world only accepts sensible teamwork plans. Some plans still fail when the
wind has too much of a head start, producing a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py
    python storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py --all
    python storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py --asp
    python storyworlds/worlds/gpt-5.4/aleck_nude_ruckus_teamwork_bad_ending_problem.py --verify
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
        female = {"girl", "mother", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandpa": "grandpa",
            "grandma": "grandma",
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
    name: str
    field: str
    anchor_text: str
    affords: set[str] = field(default_factory=set)
    gust: int = 1
    animal: str = ""
    animal_group: str = ""
    opening: str = ""
    horizon: str = ""
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
class Garment:
    id: str
    label: str
    phrase: str
    clothing: str
    bulk: int
    flap: str
    dress_line: str
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
class Plan:
    id: str
    sense: int
    power: int
    teamwork: bool
    setup: str
    action: str
    fail: str
    qa_text: str
    tool: str
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


def _r_airborne_danger(world: World) -> list[str]:
    garment = world.get("garment")
    yard = world.get("yard")
    if garment.meters["airborne"] < THRESHOLD:
        return []
    sig = ("airborne_danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    yard.meters["danger"] += 1
    world.get("scarecrow").meters["nude"] += 1
    world.get("animals").memes["panic"] += 1
    for kid_id in ("instigator", "partner"):
        world.get(kid_id).memes["fear"] += 1
    return ["__gust__"]


def _r_panic_ruckus(world: World) -> list[str]:
    animals = world.get("animals")
    if animals.memes["panic"] < THRESHOLD:
        return []
    sig = ("panic_ruckus",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("yard").meters["ruckus"] += 1
    return ["__ruckus__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="airborne_danger", tag="physical", apply=_r_airborne_danger),
    Rule(name="panic_ruckus", tag="social", apply=_r_panic_ruckus),
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


def sensible_plans() -> list[Plan]:
    return [plan for plan in PLANS.values() if plan.sense >= SENSE_MIN and plan.teamwork]


def valid_combo(place: Place, garment: Garment, plan: Plan) -> bool:
    return plan.id in place.affords and plan.sense >= SENSE_MIN and plan.teamwork


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for garment_id in GARMENTS:
            for plan_id, plan in PLANS.items():
                if valid_combo(place, GARMENTS[garment_id], plan):
                    combos.append((place_id, garment_id, plan_id))
    return combos


def wind_severity(place: Place, garment: Garment, delay: int) -> int:
    return place.gust + garment.bulk + delay


def is_caught(place: Place, garment: Garment, plan: Plan, delay: int) -> bool:
    return plan.power >= wind_severity(place, garment, delay)


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    if not plan.teamwork:
        return (
            f"(Refusing plan '{plan_id}': this storyworld is about teamwork, but "
            f"'{plan_id}' is a one-person stunt. Try a teamwork plan such as {better}.)"
        )
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("garment").meters["airborne"] += 1
    propagate(sim, narrate=False)
    return {
        "nude": sim.get("scarecrow").meters["nude"] >= THRESHOLD,
        "ruckus": sim.get("yard").meters["ruckus"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, elder: Entity, place: Place, garment: Garment) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {place.name}, the wind was so strong that it could comb a haystack and part it down the middle. "
        f"{place.opening} {a.id} and {b.id} were helping {elder.label_word} in {place.field}."
    )
    world.say(
        f"Over the rows stood a scarecrow wearing {garment.phrase}, and {garment.flap} whenever the prairie took a deep breath."
    )


def boast(world: World, a: Entity, garment: Garment) -> None:
    a.memes["pride"] += 1
    world.say(
        f'{a.id} planted both feet and puffed up. "If that {garment.label} ever breaks loose, I can catch it myself," '
        f'{a.pronoun()} said in an aleck voice.'
    )


def warn(world: World, b: Entity, place: Place, garment: Garment) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_ruckus"] = pred["ruckus"]
    world.facts["predicted_danger"] = pred["danger"]
    extra = " and the whole yard would turn into a ruckus" if pred["ruckus"] else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "Not alone. If the wind snatches that {garment.label}, '
        f"the scarecrow will stand nude as a peeled corncob{extra}. We need a real plan." 
        f'"'
    )


def gust(world: World, place: Place, garment: Garment) -> None:
    world.get("garment").meters["airborne"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then a gust came bowling across {place.field} like it had boots on. "
        f"It jerked the {garment.label} free, and up it went, big as a runaway cloud."
    )
    if world.get("scarecrow").meters["nude"] >= THRESHOLD:
        world.say(
            "The poor scarecrow was left nude in the middle of the field, too surprised even to lean properly."
        )
    if world.get("yard").meters["ruckus"] >= THRESHOLD:
        world.say(
            f"The flying cloth skimmed over the {place.animal_group} and raised such a ruckus that even the fence posts looked startled."
        )


def choose_teamwork(world: World, elder: Entity, a: Entity, b: Entity, plan: Plan, place: Place) -> None:
    for kid in (a, b):
        kid.memes["teamwork"] += 1
    world.say(
        f'{elder.label_word.capitalize()} did not waste one blink. "{plan.setup}," {elder.pronoun()} called. '
        f"{a.id} took one side, {b.id} took the other, and together they ran for {place.anchor_text}."
    )


def catch_success(world: World, a: Entity, b: Entity, elder: Entity, garment: Garment, plan: Plan) -> None:
    world.get("garment").meters["airborne"] = 0.0
    world.get("garment").meters["caught"] += 1
    world.get("yard").meters["danger"] = 0.0
    world.get("yard").meters["ruckus"] = 0.0
    world.get("animals").memes["panic"] = 0.0
    world.get("scarecrow").meters["nude"] = 0.0
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["pride"] = 0.0
        kid.memes["lesson"] += 1
    world.say(
        plan.action.format(garment=garment.label)
    )
    world.say(
        f"Then {a.id} and {b.id} wrangled the {garment.label} back onto the scarecrow, knot by knot, until {garment.dress_line}."
    )
    world.say(
        f'{elder.label_word.capitalize()} laughed. "That is how you beat a big problem on a big farm," {elder.pronoun()} said. '
        f'"Not with aleck bragging. With teamwork and good sense."'
    )
    world.say(
        f"By sunset the field looked peaceful again, and the scarecrow stood proud against {world.place.horizon}."
    )


def catch_fail(world: World, a: Entity, b: Entity, elder: Entity, garment: Garment, plan: Plan, place: Place) -> None:
    world.get("garment").meters["lost"] += 1
    world.get("yard").meters["danger"] += 1
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        plan.fail.format(garment=garment.label)
    )
    world.say(
        f"The {garment.label} sailed clean over the next hill and out of the county, while the scarecrow stayed nude in the field and the {place.animal_group} kept the ruckus going till supper."
    )
    world.say(
        f'{elder.label_word.capitalize()} put a hand on both children\'s shoulders. "You worked hard, but you waited too long for this much wind," '
        f'{elder.pronoun()} said softly. "Next time we solve the problem sooner."'
    )
    world.say(
        "For a long while after that, nobody made jokes about doing farm work alone."
    )


def tell(
    place: Place,
    garment: Garment,
    plan: Plan,
    *,
    instigator: str = "Hank",
    instigator_gender: str = "boy",
    partner: str = "June",
    partner_gender: str = "girl",
    elder_type: str = "grandpa",
    delay: int = 0,
) -> World:
    world = World(place)
    a = world.add(Entity(id="instigator", kind="character", type=instigator_gender, label=instigator, role="instigator"))
    b = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner, role="partner"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    scarecrow = world.add(Entity(id="scarecrow", type="scarecrow", label="the scarecrow", tags={"scarecrow"}))
    garment_ent = world.add(Entity(id="garment", type=garment.clothing, label=garment.label, tags=set(garment.tags)))
    yard = world.add(Entity(id="yard", type="yard", label="the yard", tags={"wind"}))
    animals = world.add(
        Entity(
            id="animals",
            type="animals",
            label=place.animal_group,
            attrs={"animal": place.animal, "animal_group": place.animal_group},
            tags={"animals"},
        )
    )
    world.facts.update(
        place=place,
        garment_cfg=garment,
        plan=plan,
        delay=delay,
        predicted_ruckus=False,
        predicted_danger=0,
    )

    introduce(world, a, b, elder, place, garment)
    world.para()
    boast(world, a, garment)
    warn(world, b, place, garment)
    world.para()
    gust(world, place, garment)
    world.para()
    choose_teamwork(world, elder, a, b, plan, place)

    caught = is_caught(place, garment, plan, delay)
    if caught:
        catch_success(world, a, b, elder, garment, plan)
    else:
        catch_fail(world, a, b, elder, garment, plan, place)

    world.facts.update(
        instigator=a,
        partner=b,
        elder=elder,
        scarecrow=scarecrow,
        garment=garment_ent,
        animals=animals,
        outcome="caught" if caught else "lost",
        nude=scarecrow.meters["nude"] >= THRESHOLD,
        ruckus=yard.meters["ruckus"] >= THRESHOLD,
        teamwork=a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD,
        severity=wind_severity(place, garment, delay),
    )
    return world


PLACES = {
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        name="Cracked Kettle Hollow",
        field="the pumpkin patch",
        anchor_text="the old windmill post",
        affords={"rope_chain", "wagon_net", "ladder_clip"},
        gust=1,
        animal="hens",
        animal_group="hen yard",
        opening="It was the sort of place where pumpkins grew so round they cast their own noon shade.",
        horizon="a red sunset and a mile of fences",
        tags={"wind", "farm"},
    ),
    "corn_ridge": Place(
        id="corn_ridge",
        name="Thundercorn Ridge",
        field="the corn rows",
        anchor_text="the iron hitching ring",
        affords={"rope_chain", "wagon_net"},
        gust=2,
        animal="geese",
        animal_group="goose pen",
        opening="The corn there was so high that crows needed lunch before crossing it.",
        horizon="long blue ridges and silver corn tassels",
        tags={"wind", "farm"},
    ),
    "melon_bank": Place(
        id="melon_bank",
        name="Big Melon Bend",
        field="the melon bank by the creek",
        anchor_text="the ferry stump",
        affords={"rope_chain", "ladder_clip"},
        gust=1,
        animal="ducks",
        animal_group="duck run",
        opening="Folks said the melons were so sweet that bees hummed thank-you songs over them.",
        horizon="the shining creek and sleepy willow trees",
        tags={"wind", "farm"},
    ),
}

GARMENTS = {
    "overalls": Garment(
        id="overalls",
        label="overalls",
        phrase="a pair of overalls so wide a calf could nap in one leg",
        clothing="overalls",
        bulk=2,
        flap="the legs flapped like blue flags",
        dress_line="it was properly dressed once more",
        tags={"overalls", "clothes"},
    ),
    "union_suit": Garment(
        id="union_suit",
        label="union suit",
        phrase="a red union suit big enough to dry a pony",
        clothing="union_suit",
        bulk=3,
        flap="the sleeves snapped in the wind like little whips",
        dress_line="the red suit hugged the scarecrow again",
        tags={"union_suit", "clothes"},
    ),
    "patch_shirt": Garment(
        id="patch_shirt",
        label="patch shirt",
        phrase="a patch shirt stitched from enough scraps to tell ten stories",
        clothing="shirt",
        bulk=1,
        flap="the bright patches winked and fluttered",
        dress_line="its bright shirt sat straight on its straw shoulders again",
        tags={"shirt", "clothes"},
    ),
}

PLANS = {
    "rope_chain": Plan(
        id="rope_chain",
        sense=3,
        power=3,
        teamwork=True,
        setup="grab the hay rope and make a chain",
        action="Together they spread the rope wide, let the wind push the {garment} into it, and hauled back with both heels digging furrows.",
        fail="They cast the rope together, but the wind dragged the {garment} right through their reach as if it had swallowed a storm.",
        qa_text="They used a hay rope together to snag the runaway clothes.",
        tool="hay rope",
        tags={"rope", "teamwork"},
    ),
    "wagon_net": Plan(
        id="wagon_net",
        sense=3,
        power=4,
        teamwork=True,
        setup="tip the wagon net open and hold it low",
        action="The cloth bellied down into the wagon net, and all three of them cinched the corners before the wind could think of a second trick.",
        fail="They opened the wagon net, but the gust hit so hard that the {garment} bounced off and leapt skyward again.",
        qa_text="They opened a wagon net together and tried to catch the clothes inside it.",
        tool="wagon net",
        tags={"net", "teamwork"},
    ),
    "ladder_clip": Plan(
        id="ladder_clip",
        sense=2,
        power=2,
        teamwork=True,
        setup="carry the orchard ladder and the giant wash clip",
        action="One child steadied the ladder, the other lifted the clip, and they pinched the {garment} against the fence before it could fly farther.",
        fail="They worked the ladder and giant clip together, but the wind jerked the {garment} loose before the clip could bite.",
        qa_text="They worked together with a ladder and a huge wash clip to pin the clothes down.",
        tool="giant wash clip",
        tags={"clip", "teamwork"},
    ),
    "solo_grab": Plan(
        id="solo_grab",
        sense=1,
        power=1,
        teamwork=False,
        setup="run and jump for it",
        action="",
        fail="",
        qa_text="",
        tool="bare hands",
        tags={"solo"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Nell", "Ada", "Ruth", "Tess", "Pearl", "Elsie"]
BOY_NAMES = ["Hank", "Otis", "Levi", "Bo", "Earl", "Clem", "Jude", "Walt"]


@dataclass
class StoryParams:
    place: str
    garment: str
    plan: str
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    elder: str
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


CURATED = [
    StoryParams(
        place="pumpkin_patch",
        garment="overalls",
        plan="rope_chain",
        instigator="Hank",
        instigator_gender="boy",
        partner="June",
        partner_gender="girl",
        elder="grandpa",
        delay=0,
    ),
    StoryParams(
        place="corn_ridge",
        garment="union_suit",
        plan="wagon_net",
        instigator="Otis",
        instigator_gender="boy",
        partner="Mabel",
        partner_gender="girl",
        elder="grandma",
        delay=0,
    ),
    StoryParams(
        place="melon_bank",
        garment="patch_shirt",
        plan="ladder_clip",
        instigator="Bo",
        instigator_gender="boy",
        partner="Ada",
        partner_gender="girl",
        elder="grandpa",
        delay=1,
    ),
    StoryParams(
        place="corn_ridge",
        garment="union_suit",
        plan="rope_chain",
        instigator="Levi",
        instigator_gender="boy",
        partner="Pearl",
        partner_gender="girl",
        elder="grandma",
        delay=2,
    ),
    StoryParams(
        place="pumpkin_patch",
        garment="overalls",
        plan="ladder_clip",
        instigator="Walt",
        instigator_gender="boy",
        partner="Tess",
        partner_gender="girl",
        elder="grandpa",
        delay=2,
    ),
]


KNOWLEDGE = {
    "wind": [
        (
            "What can strong wind do to loose clothes?",
            "Strong wind can grab cloth and pull it into the air like a sail. That is why people tie big things down before a stormy gust comes."
        )
    ],
    "scarecrow": [
        (
            "What is a scarecrow for?",
            "A scarecrow stands in a field to help scare birds away from the crops. Farmers dress it in old clothes so it looks more like a person from far off."
        )
    ],
    "teamwork": [
        (
            "Why can teamwork help with a big problem?",
            "Teamwork lets two or more people share the weight, timing, and thinking. A job that is too hard for one person can become possible when everyone pulls together."
        )
    ],
    "rope": [
        (
            "What is a hay rope used for?",
            "A hay rope is a strong rope used for pulling, tying, or securing things on a farm. It helps hold big, heavy things that bare hands cannot control well."
        )
    ],
    "net": [
        (
            "What does a net do?",
            "A net spreads wide so it can catch or hold something without letting it slip through easily. That makes it useful when something is flying or falling."
        )
    ],
    "clip": [
        (
            "What does a big wash clip do?",
            "A wash clip pinches cloth and holds it in place. The stronger the wind, the stronger the clip has to be."
        )
    ],
    "overalls": [
        (
            "What are overalls?",
            "Overalls are sturdy clothes with long legs and a front bib. People often wear them for farm work because they cover a lot and take dirt well."
        )
    ],
    "union_suit": [
        (
            "What is a union suit?",
            "A union suit is a one-piece underclothes outfit with sleeves and legs. In old stories, people sometimes use the name for very big, funny long underwear."
        )
    ],
    "shirt": [
        (
            "What is a shirt for?",
            "A shirt covers the upper body and helps keep a person comfortable. In stories about scarecrows, an old shirt often helps the scarecrow look lively from far away."
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "scarecrow", "teamwork", "rope", "net", "clip", "overalls", "union_suit", "shirt"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    garment = f["garment_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that uses the words "aleck", "nude", and "ruckus". Make the problem a runaway {garment.label} in {place.field}, and let teamwork try to solve it but fail in the end.',
            f"Tell a windy farm story where one child starts with smart-aleck bragging, then learns too late that big problems need teamwork and quick thinking.",
            f"Write a child-facing tall tale with a bad ending: the runaway clothes are lost, the scarecrow is left nude, and everyone learns not to wait when trouble is blowing in.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that uses the words "aleck", "nude", and "ruckus". Make the problem a runaway {garment.label} in {place.field}, and solve it with teamwork.',
        f"Tell a windy farm story where a boastful child learns that two children working together can do what one child cannot.",
        f"Write a simple tall tale with a big problem, a clever teamwork plan, and an ending image that shows the farm peaceful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    elder = f["elder"]
    place = f["place"]
    garment = f["garment_cfg"]
    plan = f["plan"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two children helping their {elder.label_word} on a windy farm. The trouble starts when the scarecrow's {garment.label} breaks loose."
        ),
        (
            "What problem did the children have to solve?",
            f"They had to stop the runaway {garment.label} before the wind carried it away. If they failed, the scarecrow would stay nude and the animals would keep up a ruckus."
        ),
        (
            f"Why did {b.label} say they needed a real plan?",
            f"{b.label} could see the wind was too strong for one child alone. {b.pronoun().capitalize()} knew the flying cloth would cause danger and a ruckus, so teamwork was the safer way to solve the problem."
        ),
        (
            f"What was the aleck mistake at the start?",
            f"{a.label} bragged that {a.pronoun()} could catch the runaway clothes alone. That smart-aleck idea ignored how big the wind problem really was."
        ),
    ]
    if outcome == "caught":
        qa.append(
            (
                "How did they solve the problem?",
                f"They used {plan.tool} as a teamwork tool and moved together instead of separately. {plan.qa_text} That worked because everyone pulled or held at the same moment."
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"The scarecrow was dressed again, the ruckus stopped, and the field turned calm. The ending shows that the children solved the problem by working together instead of bragging."
            )
        )
    else:
        qa.append(
            (
                "Why did the ending turn out badly?",
                f"The children did work together, but the wind had too much of a head start. By the time they tried the plan, the runaway cloth was stronger than their chance to stop it."
            )
        )
        qa.append(
            (
                "What was the ending image, and what did it show?",
                f"The scarecrow was left nude while the yard stayed noisy with ruckus. That picture shows the problem was real and that solving it sooner would have mattered."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["garment_cfg"].tags) | set(f["plan"].tags) | {"scarecrow", "teamwork"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(Plan) :- plan(Plan), teamwork(Plan), sense(Plan,S), sense_min(M), S >= M.
valid(Place, Garment, Plan) :- place(Place), garment(Garment), sensible(Plan), affords(Place, Plan).

severity(V) :- chosen_place(P), chosen_garment(G), delay(D), gust(P,GP), bulk(G,B), V = GP + B + D.
caught :- chosen_plan(Pl), power(Pl,PP), severity(V), PP >= V.
outcome(caught) :- caught.
outcome(lost) :- not caught.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("gust", place_id, place.gust))
        for plan_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, plan_id))
    for garment_id, garment in GARMENTS.items():
        lines.append(asp.fact("garment", garment_id))
        lines.append(asp.fact("bulk", garment_id, garment.bulk))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
        if plan.teamwork:
            lines.append(asp.fact("teamwork", plan_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_garment", params.garment),
            asp.fact("chosen_plan", params.plan),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "caught" if is_caught(PLACES[params.place], GARMENTS[params.garment], PLANS[params.plan], params.delay) else "lost"


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
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(1234))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=True, header="SMOKE")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: runaway scarecrow clothes, teamwork, and windy farm trouble."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--elder", choices=["grandpa", "grandma"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan is not None and args.plan not in PLANS:
        raise StoryError("(Unknown plan.)")
    if args.place is not None and args.place not in PLACES:
        raise StoryError("(Unknown place.)")
    if args.garment is not None and args.garment not in GARMENTS:
        raise StoryError("(Unknown garment.)")
    if args.plan is not None:
        plan = PLANS[args.plan]
        if plan.sense < SENSE_MIN or not plan.teamwork:
            raise StoryError(explain_plan(args.plan))
    if args.place is not None and args.plan is not None:
        if args.plan not in PLACES[args.place].affords:
            raise StoryError(
                f"(No story: {args.plan} is not a workable plan at {args.place}. Pick one of {', '.join(sorted(PLACES[args.place].affords))}.)"
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.garment is None or combo[1] == args.garment)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, garment, plan = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_name(rng)
    partner, partner_gender = _pick_name(rng, avoid=instigator)
    elder = args.elder or rng.choice(["grandpa", "grandma"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        garment=garment,
        plan=plan,
        instigator=instigator,
        instigator_gender=instigator_gender,
        partner=partner,
        partner_gender=partner_gender,
        elder=elder,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.garment not in GARMENTS:
        raise StoryError(f"(Unknown garment '{params.garment}'.)")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan '{params.plan}'.)")
    if params.plan not in PLACES[params.place].affords:
        raise StoryError(
            f"(No story: {params.plan} is not available at {params.place}.)"
        )
    if not valid_combo(PLACES[params.place], GARMENTS[params.garment], PLANS[params.plan]):
        raise StoryError(explain_plan(params.plan))

    world = tell(
        PLACES[params.place],
        GARMENTS[params.garment],
        PLANS[params.plan],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        elder_type=params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, garment, plan) combos:\n")
        for place, garment, plan in combos:
            sample_params = StoryParams(
                place=place,
                garment=garment,
                plan=plan,
                instigator="Hank",
                instigator_gender="boy",
                partner="June",
                partner_gender="girl",
                elder="grandpa",
                delay=0,
            )
            print(f"  {place:14} {garment:11} {plan:12} -> {asp_outcome(sample_params)} at delay 0")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.instigator} & {p.partner}: {p.garment} at {p.place} ({p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
