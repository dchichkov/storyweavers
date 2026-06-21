#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py
=========================================================================================

A standalone story world about two children on a forest trail who borrow a
camcorder to make a little nature movie. One child is tempted to ignore a rule
that forbids standing on an unsafe perch for a better shot. The story can end as
a near-miss, a safe rescue, or a damaged-camcorder cautionary ending, but it is
always grounded in teamwork and a warm lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py --scene owl_nest --perch slick_log
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py --aid bench
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py --all
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/forbid_camcorder_standing_forest_trail_cautionary_teamwork.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
    fragile: bool = False
    unstable: bool = False
    gives_height: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "ranger_female", "woman"}
        male = {"boy", "father", "grandfather", "ranger_male", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "ranger_female": "ranger",
            "ranger_male": "ranger",
        }
        return mapping.get(self.type, self.type)
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
class Scene:
    id: str
    animal: str
    place_text: str
    sound_text: str
    need_height: int
    need_stability: int
    shot_goal: str
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
class Perch:
    id: str
    label: str
    the: str
    near_text: str
    warning_text: str
    risk: int
    unstable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class SafeAid:
    id: str
    label: str
    phrase: str
    height: int
    stability: int
    setup_text: str
    ending_text: str
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
    fail: str
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


@dataclass
class StoryParams:
    scene: str
    perch: str
    aid: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    if perch.meters["loaded"] < THRESHOLD or not perch.unstable:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobble"] += float(perch.attrs.get("risk", 1))
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("camcorder").meters["drop_risk"] += 1
    out.append("__wobble__")
    return out


def _r_strap(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    camcorder = world.get("camcorder")
    if perch.meters["wobble"] < THRESHOLD or camcorder.meters["drop_risk"] < THRESHOLD:
        return out
    sig = ("swing", camcorder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    camcorder.meters["swinging"] += 1
    camcorder.meters["danger"] += 1
    out.append("__swing__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="strap", tag="physical", apply=_r_strap),
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


def perch_is_risky(perch: Perch) -> bool:
    return perch.unstable and perch.risk > 0


def aid_fits(scene: Scene, aid: SafeAid) -> bool:
    return aid.height >= scene.need_height and aid.stability >= scene.need_stability


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def wobble_severity(perch: Perch, delay: int) -> int:
    return perch.risk + delay


def is_contained(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= wobble_severity(perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    _do_stand(sim, narrate=False)
    camcorder = sim.get("camcorder")
    perch = sim.get("perch")
    return {
        "wobble": perch.meters["wobble"],
        "drop_risk": camcorder.meters["drop_risk"],
        "swinging": camcorder.meters["swinging"],
    }


def _do_stand(world: World, narrate: bool = True) -> None:
    perch = world.get("perch")
    kid = world.get("instigator")
    perch.meters["loaded"] += 1
    kid.meters["standing_high"] += 1
    propagate(world, narrate=narrate)


def forest_setup(world: World, a: Entity, b: Entity, helper: Entity, scene: Scene) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One bright morning, {a.id} and {b.id} walked along a forest trail with "
        f"{helper.label_word}. {scene.sound_text}"
    )
    world.say(
        f"{helper.label_word.capitalize()} had let them borrow a camcorder from the nature center "
        f"so they could make a tiny movie about {scene.animal}."
    )
    world.say(
        f"When they reached {scene.place_text}, both children stopped at once. "
        f'"There!" {b.id} whispered. "If we stay quiet, we can film {scene.shot_goal}."'
    )


def need_view(world: World, a: Entity, scene: Scene) -> None:
    world.say(
        f"{a.id} lifted the camcorder and squinted, but leaves and ferns kept sliding in front of the lens."
    )
    world.say(
        f'"I need a better view," {a.pronoun()} said. "If I get a little higher, the picture will be just right."'
    )


def temptation(world: World, a: Entity, perch: Perch) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id}'s eyes landed on {perch.the} {perch.near_text}. "
        f'"I could stand on {perch.the}," {a.pronoun()} said.'
    )


def warning(world: World, a: Entity, b: Entity, helper: Entity, perch: Perch) -> None:
    pred = predict_wobble(world)
    b.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_drop_risk"] = pred["drop_risk"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} already knew the camcorder strap might swing if the perch moved."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{helper.label_word.capitalize()} said the trail rules '
        f'forbid standing there. {perch.warning_text}"{extra}'
    )


def defy(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    older_sibling = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_sibling:
        world.say(
            f'"It will only be one second," {a.id} said. Because {a.id} was {b.id}\'s older sibling, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"It will only be one second," {a.id} said, and stepped toward {perch.the} anyway.'
        )


def back_down(world: World, a: Entity, b: Entity, helper: Entity, aid: SafeAid) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f"{a.id} looked at the camcorder, then at {b.id}, and let out a slow breath."
    )
    world.say(
        f'''"You are right," {a.pronoun()} said. "I do not want to slip." {helper.label_word.capitalize()} smiled and "'''
        f"showed them {aid.phrase} instead."
    )


def wobble(world: World, a: Entity, perch: Perch) -> None:
    _do_stand(world, narrate=False)
    a.memes["fear"] += 1
    world.say(
        f"The moment {a.id} was standing on {perch.the}, it shifted under {a.pronoun('possessive')} shoes."
    )
    world.say(
        f"{perch.The} gave a wet little lurch, and the camcorder swung out on its strap."
    )


def alarm(world: World, b: Entity, helper: Entity) -> None:
    world.say(f'"Hold still!" {b.id} cried.')
    world.say(f'"I\'ve got you," {helper.label_word} said, already moving closer.')


def rescue(world: World, helper: Entity, b: Entity, response: Response) -> None:
    camcorder = world.get("camcorder")
    perch = world.get("perch")
    camcorder.meters["drop_risk"] = 0.0
    camcorder.meters["swinging"] = 0.0
    camcorder.meters["danger"] = 0.0
    perch.meters["loaded"] = 0.0
    perch.meters["wobble"] = 0.0
    body = response.text
    world.say(
        f"In one smooth burst of teamwork, {b.id} and {helper.label_word} {body}."
    )
    world.say(
        f"The camcorder thumped safely back against {a_name(world).pronoun('possessive')} chest, and nobody fell."
    )


def rescue_fail(world: World, helper: Entity, b: Entity, response: Response) -> None:
    camcorder = world.get("camcorder")
    perch = world.get("perch")
    camcorder.meters["damaged"] += 1
    camcorder.meters["drop_risk"] = 0.0
    camcorder.meters["swinging"] = 0.0
    perch.meters["loaded"] = 0.0
    perch.meters["wobble"] = 0.0
    world.say(
        f"{b.id} and {helper.label_word} {response.fail}."
    )
    world.say(
        "No one was hurt, but a hard crack ran through the camcorder's side, and the screen went dark."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity, perch: Perch) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a few quiet breaths, all they could hear was wind moving through the pine needles.")
    world.say(
        f"Then {helper.label_word} knelt beside them. "
        f'"I am glad you called out and helped each other," {helper.pronoun()} said softly. '
        f'"Rules that forbid standing on unsafe places are there to keep people and borrowed things safe."'
    )
    world.say(
        f"{a.id} nodded first, and {b.id} nodded too. They both promised to ask for a safer way next time."
    )


def safe_finish(world: World, helper: Entity, a: Entity, b: Entity, scene: Scene, aid: SafeAid) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
        kid.memes["safety"] += 1
    camcorder = world.get("camcorder")
    camcorder.meters["filming"] += 1
    world.say(
        f"Together they {aid.setup_text}."
    )
    world.say(
        f"Soon {a.id} and {b.id} were shoulder to shoulder, taking turns with the camcorder while "
        f"{helper.label_word} steadied the picture."
    )
    world.say(
        f"They caught {scene.shot_goal}, and the ending of their little movie showed what had changed: "
        f"two careful helpers smiling on the forest trail, safe and proud together."
    )


def gentle_afterloss(world: World, helper: Entity, a: Entity, b: Entity, scene: Scene, aid: SafeAid) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{helper.label_word.capitalize()} put an arm around both children. "
        f'"The camcorder can be replaced," {helper.pronoun()} said. "You cannot."'
    )
    world.say(
        f"Instead of filming, they {aid.setup_text} and watched {scene.animal} together with their own eyes."
    )
    world.say(
        "By the time they walked home, the children were still sad about the broken camera, "
        "but they were holding hands and remembering the safe choice they should have made."
    )


def a_name(world: World) -> Entity:
    return world.get("instigator")


def tell(
    scene: Scene,
    perch_cfg: Perch,
    aid: SafeAid,
    response: Response,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    cautioner: str = "Lena",
    cautioner_gender: str = "girl",
    helper_type: str = "ranger_female",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation, "display_name": instigator},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "display_name": cautioner},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    perch = world.add(Entity(
        id="perch",
        type="perch",
        label=perch_cfg.label,
        unstable=perch_cfg.unstable,
        attrs={"risk": perch_cfg.risk},
    ))
    camcorder = world.add(Entity(
        id="camcorder",
        type="camcorder",
        label="camcorder",
        fragile=True,
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    camcorder.attrs["borrowed_from"] = "nature center"
    camcorder.attrs["holder"] = "instigator"
    world.facts["predicted_wobble"] = 0.0
    world.facts["predicted_drop_risk"] = 0.0

    forest_setup(world, display_entity(a), display_entity(b), helper, scene)
    need_view(world, display_entity(a), scene)

    world.para()
    temptation(world, display_entity(a), perch_cfg)
    warning(world, display_entity(a), display_entity(b), helper, perch_cfg)

    averted = would_avert(relation, a.age, b.age, trait)
    if averted:
        back_down(world, display_entity(a), display_entity(b), helper, aid)
        world.para()
        safe_finish(world, helper, display_entity(a), display_entity(b), scene, aid)
        severity = 0
        contained = True
    else:
        defy(world, display_entity(a), display_entity(b), perch_cfg)
        world.para()
        wobble(world, display_entity(a), perch_cfg)
        alarm(world, display_entity(b), helper)
        severity = wobble_severity(perch_cfg, delay)
        camcorder.meters["severity"] = float(severity)
        contained = is_contained(response, perch_cfg, delay)

        world.para()
        if contained:
            rescue(world, helper, display_entity(b), response)
            lesson(world, helper, display_entity(a), display_entity(b), perch_cfg)
            world.para()
            safe_finish(world, helper, display_entity(a), display_entity(b), scene, aid)
        else:
            rescue_fail(world, helper, display_entity(b), response)
            lesson(world, helper, display_entity(a), display_entity(b), perch_cfg)
            world.para()
            gentle_afterloss(world, helper, display_entity(a), display_entity(b), scene, aid)

    outcome = "averted" if averted else ("contained" if contained else "damaged")
    world.facts.update(
        scene=scene,
        perch_cfg=perch_cfg,
        aid=aid,
        response=response,
        instigator=display_entity(a),
        cautioner=display_entity(b),
        helper=helper,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        camcorder_safe=world.get("camcorder").meters["damaged"] < THRESHOLD,
        promise_made=display_entity(a).memes["lesson"] >= THRESHOLD,
    )
    return world


def display_entity(ent: Entity) -> Entity:
    clone = copy.copy(ent)
    clone.id = ent.attrs.get("display_name", ent.label or ent.id)
    return clone


SCENES = {
    "owl_nest": Scene(
        id="owl_nest",
        animal="a sleepy owl family",
        place_text="a bend where an old pine leaned over the trail",
        sound_text="Birdsong flickered above them, and the air smelled like bark and sunshine.",
        need_height=2,
        need_stability=2,
        shot_goal="a tiny owl chick peeking over the nest rim",
        tags={"owl", "forest_trail", "camcorder"},
    ),
    "woodpecker_hole": Scene(
        id="woodpecker_hole",
        animal="a woodpecker family",
        place_text="a quiet place beside a tall cedar",
        sound_text="Somewhere ahead, a woodpecker tapped like a tiny drum.",
        need_height=3,
        need_stability=2,
        shot_goal="a red-capped woodpecker popping in and out of a tree hole",
        tags={"bird", "forest_trail", "camcorder"},
    ),
    "frog_pool": Scene(
        id="frog_pool",
        animal="a green frog",
        place_text="a little pool beside the trail where reeds leaned over the water",
        sound_text="The trail smelled damp and sweet, and little frogs plinked into the water.",
        need_height=1,
        need_stability=2,
        shot_goal="a bright frog blinking on a wet stone",
        tags={"frog", "forest_trail", "camcorder"},
    ),
}

PERCHES = {
    "slick_log": Perch(
        id="slick_log",
        label="slick log",
        the="the slick log",
        near_text="by the muddy edge of the trail",
        warning_text="It is wet and slippery, and if it rolls, the camcorder could swing right into the mud.",
        risk=3,
        unstable=True,
        tags={"log", "slippery", "standing"},
    ),
    "mossy_boulder": Perch(
        id="mossy_boulder",
        label="mossy boulder",
        the="the mossy boulder",
        near_text="under drooping fern leaves",
        warning_text="The moss is soft and slick, so one wobble could send the camcorder bumping against the rocks.",
        risk=2,
        unstable=True,
        tags={"boulder", "slippery", "standing"},
    ),
    "trail_rail": Perch(
        id="trail_rail",
        label="trail rail",
        the="the trail rail",
        near_text="beside the steep little ditch",
        warning_text="The ranger's rules forbid standing on rails because they are narrow and easy to slip from.",
        risk=3,
        unstable=True,
        tags={"rail", "rule", "standing"},
    ),
    "flat_path": Perch(
        id="flat_path",
        label="flat path",
        the="the flat path",
        near_text="in the middle of the trail",
        warning_text="The flat path is steady, so it is not the dangerous choice this story needs.",
        risk=0,
        unstable=False,
        tags={"path"},
    ),
}

AIDS = {
    "tripod": SafeAid(
        id="tripod",
        label="tripod",
        phrase="a little tripod",
        height=2,
        stability=3,
        setup_text="opened a little tripod on a patch of flat ground and tipped the camcorder upward",
        ending_text="the tripod held the camera still",
        tags={"tripod", "camcorder"},
    ),
    "ranger_stool": SafeAid(
        id="ranger_stool",
        label="ranger stool",
        phrase="a ranger stool with broad feet",
        height=3,
        stability=2,
        setup_text="set a ranger stool on the flattest part of the trail and kept one hand on the camcorder strap",
        ending_text="the ranger stool gave enough height without the wobble",
        tags={"stool", "camcorder"},
    ),
    "bench": SafeAid(
        id="bench",
        label="bench",
        phrase="the low viewing bench by the trail sign",
        height=1,
        stability=3,
        setup_text="walked to the low viewing bench by the trail sign and rested the camcorder there",
        ending_text="the bench gave them a steady place to film",
        tags={"bench", "forest_trail"},
    ),
}

RESPONSES = {
    "brace_and_hold": Response(
        id="brace_and_hold",
        sense=3,
        power=3,
        text="braced the child by the elbows and caught the swinging strap before the camcorder could slam down",
        fail="reached for the strap, but the camcorder still knocked hard against the rock before they could steady it",
        qa_text="braced the child and caught the camcorder strap together",
        tags={"teamwork", "strap"},
    ),
    "guide_and_grab": Response(
        id="guide_and_grab",
        sense=4,
        power=4,
        text="guided the child back to the ground while one pair of hands steadied the camcorder and the other pair caught it",
        fail="moved quickly and kept the child safe, but the camcorder still cracked when it struck the ground",
        qa_text="guided the child down and caught the camcorder with teamwork",
        tags={"teamwork", "helper"},
    ),
    "snatch_one_handed": Response(
        id="snatch_one_handed",
        sense=1,
        power=1,
        text="made a wild one-handed grab that somehow worked",
        fail="made a wild one-handed grab, but the camcorder banged against the perch",
        qa_text="made a wild one-handed grab for the camcorder",
        tags={"rash"},
    ),
}

HELPERS = ["mother", "father", "grandmother", "grandfather", "ranger_female", "ranger_male"]
GIRL_NAMES = ["Lily", "Maya", "Zoe", "Ava", "Nora", "Lucy", "Ivy", "Ella"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Finn", "Leo", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for perch_id, perch in PERCHES.items():
            if not perch_is_risky(perch):
                continue
            for aid_id, aid in AIDS.items():
                if aid_fits(scene, aid):
                    combos.append((scene_id, perch_id, aid_id))
    return combos


KNOWLEDGE = {
    "camcorder": [
        (
            "What is a camcorder?",
            "A camcorder is a small camera that records moving pictures and sound. It needs careful hands because it can break if it is dropped.",
        )
    ],
    "forest_trail": [
        (
            "What is a forest trail?",
            "A forest trail is a path that winds through trees and plants. Trails help people walk safely without trampling everything around them.",
        )
    ],
    "tripod": [
        (
            "What does a tripod do?",
            "A tripod holds a camera or camcorder still on three legs. It helps people take steady pictures without climbing on unsafe things.",
        )
    ],
    "stool": [
        (
            "Why is a wide stool safer than a slippery rock?",
            "A wide stool has a flat top and steady feet, so it does not shift as easily. A slippery rock or log can move under your shoes.",
        )
    ],
    "bench": [
        (
            "Why can a bench be a good place to rest a camera?",
            "A bench gives you a flat, steady surface. That helps you keep the camera still without holding it over a risky edge.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do something safely and well. When everyone pays attention and shares the job, problems are easier to solve.",
        )
    ],
    "owl": [
        (
            "Why should people stay quiet near an owl nest?",
            "Owls need calm around their nest so they do not feel frightened. Quiet watching helps people enjoy wildlife without bothering it.",
        )
    ],
    "bird": [
        (
            "Why is it better to watch birds from the trail?",
            "Watching from the trail keeps people from slipping or scaring the birds. It also protects nests, plants, and muddy places nearby.",
        )
    ],
    "frog": [
        (
            "Why are rocks near a frog pool slippery?",
            "Water helps moss and mud grow on the rocks, which makes them slick. Slick places are easy to slip on, especially when you are standing high.",
        )
    ],
    "standing": [
        (
            "Why can standing on a narrow or slippery place be dangerous?",
            "Your feet need a steady, flat place to balance well. If the ground shifts or is slick, you can wobble before you are ready.",
        )
    ],
}
KNOWLEDGE_ORDER = ["camcorder", "forest_trail", "teamwork", "tripod", "stool", "bench", "owl", "bird", "frog", "standing"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    scene = f["scene"]
    perch = f["perch_cfg"]
    aid = f["aid"]
    outcome = f["outcome"]
    base = (
        f'Write a heartwarming cautionary story for a 3-to-5-year-old set on a forest trail, '
        f'where two children borrow a camcorder to film {scene.animal} and one child is tempted '
        f'to ignore a rule that forbid standing on {perch.the}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle teamwork story where {a.id} wants a better view, but {b.id} warns {a.pronoun('object')} in time and they use {aid.phrase} instead.",
            'Write a short story that includes the words "forbid", "camcorder", and "standing" and ends with a safe choice on the forest trail.',
        ]
    if outcome == "damaged":
        return [
            base,
            f"Tell a cautionary teamwork story where {a.id} does stand on {perch.the}, the camcorder is damaged, but everyone stays safe and learns from it.",
            'Write a warm but serious story using "forbid", "camcorder", and "standing", showing that safety rules matter more than getting the perfect shot.',
        ]
    return [
        base,
        f"Tell a heartwarming teamwork story where {a.id} ignores the warning for a moment, but {b.id} and a helper save both child and camcorder, and then the children film safely with {aid.phrase}.",
        'Write a simple cautionary story that includes "forbid", "camcorder", and "standing" and ends with children working together in a safer way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    scene = f["scene"]
    perch = f["perch_cfg"]
    aid = f["aid"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and {helper.label_word} who walked with them on the forest trail. They were trying to make a little movie with a borrowed camcorder.",
        ),
        (
            "Why did the children want to climb or stand higher?",
            f"They wanted a better view of {scene.animal} so they could film {scene.shot_goal}. Leaves and ferns were blocking the picture from the lower part of the trail.",
        ),
        (
            f"Why did {b.id} warn {a.id} not to stand on {perch.the}?",
            f"{b.id} knew the rules forbid standing there and that {perch.the} was not steady. If it wobbled, the child could slip and the camcorder could swing or fall.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed the story before anything bad happened?",
                f"{a.id} listened to {b.id} and backed down before climbing up. Then the children worked together with {helper.label_word} and used {aid.phrase} for a safe view.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children filming safely from a better place. The ending image shows them on the forest trail, careful and proud because teamwork helped them make the right choice.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "How was the camcorder saved?",
                f"{b.id} and {helper.label_word} {response.qa_text}. They moved quickly because the perch had already wobbled and the strap was swinging.",
            )
        )
        qa.append(
            (
                "Why is this a teamwork story?",
                f"No one fixed the problem alone. One person warned, two people helped in the scary moment, and then everyone worked together to film safely with {aid.phrase}.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that rules that forbid standing on unsafe places are meant to protect both people and borrowed things. After the scare, they asked for a safer tool instead of chasing the perfect shot.",
            )
        )
    else:
        qa.append(
            (
                "Was anyone hurt when the camcorder was damaged?",
                "No, nobody was hurt. The sad part was the broken camcorder, which made the lesson feel real without anyone being injured.",
            )
        )
        qa.append(
            (
                "What did the children learn after the accident?",
                f"They learned that getting a better view is never worth ignoring a safety rule. The camcorder was damaged because the perch was slippery, but the adults' help kept the children safe.",
            )
        )
        qa.append(
            (
                "How did the story still end in a warm way?",
                f"{helper.label_word.capitalize()} reminded them that people matter more than objects, and the children stayed together on the trail to watch {scene.animal} safely. Even after a mistake, they were cared for and guided toward a better choice.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["scene"].tags) | set(f["perch_cfg"].tags) | set(f["response"].tags) | set(f["aid"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="owl_nest",
        perch="mossy_boulder",
        aid="tripod",
        response="brace_and_hold",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="ranger_female",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        scene="woodpecker_hole",
        perch="trail_rail",
        aid="ranger_stool",
        response="guide_and_grab",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="grandfather",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        scene="frog_pool",
        perch="slick_log",
        aid="bench",
        response="brace_and_hold",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        helper="mother",
        trait="curious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        scene="woodpecker_hole",
        perch="slick_log",
        aid="ranger_stool",
        response="brace_and_hold",
        instigator="Noah",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        helper="father",
        trait="patient",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(scene: Scene, perch: Perch, aid: Optional[SafeAid] = None) -> str:
    if not perch_is_risky(perch):
        return (
            f"(No story: {perch.the} is not an unsafe perch, so there is no real cautionary turn. "
            f"Pick a risky place like a slick log, a mossy boulder, or a trail rail.)"
        )
    if aid is not None and not aid_fits(scene, aid):
        return (
            f"(No story: {aid.label} does not give a good enough, steady enough view for filming {scene.animal}. "
            f"The safe alternative must really solve the problem, not just sound nice.)"
        )
    return "(No story: this combination does not describe a reasonable cautionary teamwork story.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of these teamwork responses instead: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], PERCHES[params.perch], params.delay) else "damaged"


ASP_RULES = r"""
hazard(P) :- perch(P), unstable(P), risk(P, R), R > 0.
fit(S, A) :- scene(S), aid(A), need_height(S, H), aid_height(A, AH), AH >= H,
             need_stability(S, St), aid_stability(A, AS), AS >= St.
valid(S, P, A) :- scene(S), hazard(P), fit(S, A).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(R + D) :- chosen_perch(P), risk(P, R), delay(D).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
contained :- resp_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(damaged) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("need_height", sid, scene.need_height))
        lines.append(asp.fact("need_stability", sid, scene.need_stability))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("risk", pid, perch.risk))
        if perch.unstable:
            lines.append(asp.fact("unstable", pid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("aid_height", aid_id, aid.height))
        lines.append(asp.fact("aid_stability", aid_id, aid.stability))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_story() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_story()
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a borrowed camcorder, a forbidden unsafe perch, and teamwork on a forest trail."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the wobble before help lands")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and not perch_is_risky(PERCHES[args.perch]):
        scene = SCENES[args.scene] if args.scene else next(iter(SCENES.values()))
        raise StoryError(explain_rejection(scene, PERCHES[args.perch]))
    if args.scene and args.aid:
        scene = SCENES[args.scene]
        aid = AIDS[args.aid]
        if not aid_fits(scene, aid):
            perch = PERCHES[args.perch] if args.perch else next(p for p in PERCHES.values() if perch_is_risky(p))
            raise StoryError(explain_rejection(scene, perch, aid))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.perch is None or combo[1] == args.perch)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, perch_id, aid_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        scene=scene_id,
        perch=perch_id,
        aid=aid_id,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def _helper_entity_type(helper: str) -> str:
    return helper


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    scene = SCENES[params.scene]
    perch = PERCHES[params.perch]
    aid = AIDS[params.aid]
    response = RESPONSES[params.response]

    if not perch_is_risky(perch):
        raise StoryError(explain_rejection(scene, perch))
    if not aid_fits(scene, aid):
        raise StoryError(explain_rejection(scene, perch, aid))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        scene=scene,
        perch_cfg=perch,
        aid=aid,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        helper_type=_helper_entity_type(params.helper),
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, perch, aid) combos:\n")
        for scene, perch, aid in combos:
            print(f"  {scene:16} {perch:14} {aid}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.scene} with {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
