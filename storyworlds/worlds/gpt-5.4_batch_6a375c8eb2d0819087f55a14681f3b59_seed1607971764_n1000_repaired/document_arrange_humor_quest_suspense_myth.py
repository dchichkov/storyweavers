#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py
========================================================================

A standalone storyworld about a small mythic quest: a child archivist must
arrange a sacred document before moonrise after a comic disturbance scatters it.

The domain is intentionally tiny and constraint-driven:
- a place affords certain kinds of disturbances
- a document material determines what can disturb it
- an arrangement method must actually suit that document
- a helper can add a little practical advantage
- if the fix is too weak or too late, part of the document is lost

The style aims for child-facing myth: bright temple images, a quest-shaped plot,
gentle suspense, and a touch of humor from animal helpers and silly mishaps.

Run it
------
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py --all
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py --json
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py --asp
    python storyworlds/worlds/gpt-5.4/document_arrange_humor_quest_suspense_myth.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "mother"}
        male = {"boy", "man", "priest", "father"}
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
class Place:
    id: str
    label: str
    image: str
    quest_line: str
    afford_scatterers: set[str] = field(default_factory=set)
    ending_image: str = ""
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
class DocumentCfg:
    id: str
    label: str
    phrase: str
    material: str
    flexible: bool
    heavy: bool
    plural: bool
    order_name: str
    image: str
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
class Scatterer:
    id: str
    label: str
    arrive: str
    trouble: str
    severity: int
    disturbs: set[str] = field(default_factory=set)
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
    label: str
    sense: int
    power: int
    suits_materials: set[str] = field(default_factory=set)
    needs_flexible: bool = False
    text: str = ""
    fail: str = ""
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
class HelperCfg:
    id: str
    label: str
    type: str
    bonus: int
    entrance: str
    funny: str
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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    doc = world.get("document")
    hero = world.get("hero")
    room = world.get("room")
    if doc.meters["scattered"] >= THRESHOLD:
        sig = ("risk", "document")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["risk"] += 1
            hero.memes["fear"] += 1
            out.append("__risk__")
    return out


def _r_urgent(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    hero = world.get("hero")
    deadline = world.facts.get("deadline_beats", 0)
    if room.meters["risk"] >= THRESHOLD and deadline >= 1:
        sig = ("urgent", deadline)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["urgency"] += 1
            out.append("__urgent__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="urgent", tag="temporal", apply=_r_urgent),
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


def document_at_risk(place: Place, scatterer: Scatterer, document: DocumentCfg) -> bool:
    return scatterer.id in place.afford_scatterers and document.material in scatterer.disturbs


def method_fits(document: DocumentCfg, method: Method) -> bool:
    if document.material not in method.suits_materials:
        return False
    if method.needs_flexible and not document.flexible:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def danger_value(scatterer: Scatterer, delay: int) -> int:
    return scatterer.severity + delay


def saved_by(method: Method, helper: HelperCfg, scatterer: Scatterer, delay: int) -> bool:
    return method.power + helper.bonus >= danger_value(scatterer, delay)


def predict_loss(world: World, method: Method, helper: HelperCfg) -> dict:
    sim = world.copy()
    scatterer = sim.facts["scatterer_cfg"]
    doc = sim.get("document")
    doc.meters["scattered"] += 1
    propagate(sim, narrate=False)
    safe = saved_by(method, helper, scatterer, sim.facts["delay"])
    return {
        "risk": sim.get("room").meters["risk"],
        "safe": safe,
    }


def introduce(world: World, hero: Entity, keeper: Entity, place: Place, document: DocumentCfg) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In the age when even moonbeams listened, {place.image}. "
        f"There worked {hero.id}, a young keeper of shelves, under the watch of "
        f"{keeper.id}, the old archive-keeper."
    )
    world.say(
        f"That evening the keeper laid out {document.phrase}, a sacred document "
        f"whose {document.image}. {place.quest_line}"
    )


def charge_quest(world: World, hero: Entity, keeper: Entity, document: DocumentCfg) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"{hero.id}," said {keeper.id}, "before the moon reaches the high window, '
        f'you must arrange {document.order_name} in their proper order. Only then '
        f'will the words speak clearly."'
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(helper_cfg.entrance)
    world.say(helper_cfg.funny)


def disturbance(world: World, scatterer: Scatterer, document: DocumentCfg, helper_cfg: HelperCfg) -> None:
    doc = world.get("document")
    doc.meters["scattered"] += 1
    doc.meters["at_risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {scatterer.arrive}. In one silly, dreadful moment, {scatterer.trouble} "
        f"and the sacred document flew apart."
    )
    if helper_cfg.id == "ibis":
        world.say("The ibis gave one offended honk, as if blaming the wind for poor manners.")
    elif helper_cfg.id == "tortoise":
        world.say("The little tortoise stuck out his neck so far that he nearly tipped onto his shell.")
    elif helper_cfg.id == "monkey":
        world.say('The monkey helper gasped, then covered his own mouth as if surprise were a hat he had forgotten to wear.')


def suspense_beat(world: World, hero: Entity, place: Place) -> None:
    if hero.memes["fear"] >= THRESHOLD:
        line = f"{hero.id}'s heart thumped. Above the shelves, the moon was climbing."
        if hero.memes["urgency"] >= THRESHOLD:
            line += f" Soon its pale rim would touch {place.ending_image}."
        world.say(line)


def vow(world: World, hero: Entity, helper: Entity, method: Method, document: DocumentCfg) -> None:
    pred = predict_loss(world, method, HELPER[helper.id])
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_safe"] = pred["safe"]
    hero.memes["resolve"] += 1
    world.say(
        f'"Quick," whispered {hero.id}, kneeling among the pieces. '
        f'"If we do not arrange {document.order_name} now, the song will be lost."'
    )


def recover(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg, document: DocumentCfg) -> None:
    hero.meters["gathered"] += 1
    helper.meters["helped"] += 1
    if helper_cfg.id == "tortoise":
        world.say(
            f"{helper.id} trudged forward with solemn little steps, carrying one piece "
            f"of the document on his shell as if he were a moving table."
        )
    elif helper_cfg.id == "ibis":
        world.say(
            f"{helper.id} pinched the drifting edge in {helper.pronoun('possessive')} beak "
            f"and set it down with a proud little strut."
        )
    else:
        world.say(
            f"{helper.id} hopped from shelf to shelf, snatching loose pieces and dropping "
            f"them into {hero.id}'s lap with surprising care."
        )
    world.say(
        f"Together they gathered every part they could find, though one piece kept trying "
        f"to slide toward the floor like a fish trying for water."
    )


def arrange_attempt(world: World, hero: Entity, helper: Entity, method: Method, document: DocumentCfg) -> None:
    hero.meters["arranging"] += 1
    doc = world.get("document")
    doc.meters["bound"] += 1
    world.say(
        f"Then {hero.id} used {method.label}. {method.text.replace('{document}', document.label)}."
    )


def success(world: World, hero: Entity, keeper: Entity, helper: Entity, method: Method, place: Place, document: DocumentCfg) -> None:
    doc = world.get("document")
    room = world.get("room")
    doc.meters["scattered"] = 0.0
    doc.meters["saved"] += 1
    room.meters["risk"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"The last piece settled into place. The document held fast, and not one line "
        f"escaped."
    )
    world.say(
        f"When the moonlight touched {place.ending_image}, the ordered words shone silver. "
        f'{keeper.id} smiled and said, "You have arranged wisdom out of chaos."'
    )
    if helper.id == "Pico":
        world.say("Pico bowed so hard that he almost fell off the shelf, which made even the keeper laugh.")
    elif helper.id == "Mossback":
        world.say("Mossback blinked slowly, as if he had expected nothing less from heroes and shelves.")
    else:
        world.say("Feather-Foot strutted in a proud circle, which was not graceful but was certainly victorious.")


def failure(world: World, hero: Entity, keeper: Entity, helper: Entity, method: Method, scatterer: Scatterer, place: Place, document: DocumentCfg) -> None:
    doc = world.get("document")
    room = world.get("room")
    doc.meters["lost"] += 1
    doc.meters["scattered"] = 0.0
    room.meters["risk"] = 0.0
    hero.memes["fear"] += 1
    hero.memes["sadness"] += 1
    world.say(
        method.fail.replace("{document}", document.label)
    )
    world.say(
        f"One piece slipped away before {hero.id} could catch it, and the moon touched "
        f"{place.ending_image} while the sacred song still had a hole in it."
    )
    world.say(
        f"{keeper.id} laid a kind hand on {hero.id}'s shoulder. "
        f'"We did not keep every line tonight," {keeper.pronoun()} said, '
        f'"but now you know what this document needs."'
    )


def ending_lesson(world: World, hero: Entity, keeper: Entity, method: Method, document: DocumentCfg) -> None:
    hero.memes["lesson"] += 1
    if world.facts["outcome"] == "saved":
        world.say(
            f"After that night, {hero.id} always arranged {document.order_name} with "
            f"{method.label} before jokes, gusts, or paws could trouble them again."
        )
    else:
        world.say(
            f"After that night, {hero.id} never trusted haste alone. Before touching a "
            f"sacred document again, {hero.pronoun()} chose the right way to arrange it first."
        )


def tell(
    place: Place,
    document: DocumentCfg,
    scatterer: Scatterer,
    method: Method,
    helper_cfg: HelperCfg,
    hero_name: str = "Nila",
    hero_gender: str = "girl",
    keeper_name: str = "Tharos",
    keeper_gender: str = "man",
    delay: int = 0,
) -> World:
    world = World(place)
    world.facts["delay"] = delay
    world.facts["deadline_beats"] = delay + 1
    world.facts["place_cfg"] = place
    world.facts["document_cfg"] = document
    world.facts["scatterer_cfg"] = scatterer
    world.facts["method_cfg"] = method
    world.facts["helper_cfg"] = helper_cfg

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["young", "eager"],
    ))
    keeper = world.add(Entity(
        id=keeper_name,
        kind="character",
        type=keeper_gender,
        role="keeper",
        label="the keeper",
        traits=["old", "calm"],
    ))
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        traits=["helpful", "comic"],
    ))
    room = world.add(Entity(
        id="room",
        type="archive",
        label=place.label,
    ))
    doc = world.add(Entity(
        id="document",
        type="document",
        label=document.label,
        attrs={
            "material": document.material,
            "order_name": document.order_name,
            "plural": document.plural,
        },
    ))
    doc.meters["scattered"] = 0.0
    doc.meters["saved"] = 0.0
    doc.meters["lost"] = 0.0
    room.meters["risk"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["urgency"] = 0.0
    hero.memes["joy"] = 0.0
    helper.meters["helped"] = 0.0

    introduce(world, hero, keeper, place, document)
    charge_quest(world, hero, keeper, document)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    disturbance(world, scatterer, document, helper_cfg)
    suspense_beat(world, hero, place)

    world.para()
    vow(world, hero, helper, method, document)
    recover(world, hero, helper, helper_cfg, document)
    arrange_attempt(world, hero, helper, method, document)

    outcome = "saved" if saved_by(method, helper_cfg, scatterer, delay) else "lost"
    world.facts["outcome"] = outcome
    world.facts["severity"] = danger_value(scatterer, delay)
    world.facts["helper_bonus"] = helper_cfg.bonus

    world.para()
    if outcome == "saved":
        success(world, hero, keeper, helper, method, place, document)
    else:
        failure(world, hero, keeper, helper, method, scatterer, place, document)
    ending_lesson(world, hero, keeper, method, document)

    world.facts.update(
        hero=hero,
        keeper=keeper,
        helper=helper,
        document=doc,
        place=room,
        assembled=doc.meters["saved"] >= THRESHOLD,
        missing_piece=doc.meters["lost"] >= THRESHOLD,
    )
    return world


PLACES = {
    "moon_archive": Place(
        id="moon_archive",
        label="the Moon Archive",
        image="high in the Moon Archive, white shelves curved like ribs around a blue fire bowl",
        quest_line="If its pieces were placed in order before moonrise, the temple doors would open at dawn",
        afford_scatterers={"breeze", "monkey"},
        ending_image="the round high window",
        tags={"archive", "moon"},
    ),
    "reed_temple": Place(
        id="reed_temple",
        label="the Reed Temple",
        image="in the Reed Temple, cool columns rose from a floor painted with silver fish",
        quest_line="If its parts were set in order before the first owl called, the river would show safe crossings",
        afford_scatterers={"ibis", "breeze"},
        ending_image="the river-shaped window",
        tags={"temple", "river"},
    ),
    "peak_library": Place(
        id="peak_library",
        label="the Peak Library",
        image="on the shoulder of the mountain, the Peak Library held its shelves beneath bronze bells and patient stars",
        quest_line="If the lines were arranged before the bell of night, the shepherds below would know where to walk",
        afford_scatterers={"goat", "breeze"},
        ending_image="the bell-rope above the stair",
        tags={"mountain", "library"},
    ),
}

DOCUMENTS = {
    "scroll": DocumentCfg(
        id="scroll",
        label="star scroll",
        phrase="a star scroll written in blue ink",
        material="papyrus",
        flexible=True,
        heavy=False,
        plural=False,
        order_name="its coils and verses",
        image="painted stars twinkled along its curled edges",
        tags={"scroll", "document"},
    ),
    "leaf_pages": DocumentCfg(
        id="leaf_pages",
        label="leaf pages",
        phrase="leaf pages tied once with gold thread",
        material="leaf",
        flexible=True,
        heavy=False,
        plural=True,
        order_name="the pages",
        image="tiny gold moons had been painted at the bottom of every page",
        tags={"pages", "document"},
    ),
    "clay_tablets": DocumentCfg(
        id="clay_tablets",
        label="clay tablets",
        phrase="three clay tablets pressed with old signs",
        material="clay",
        flexible=False,
        heavy=True,
        plural=True,
        order_name="the tablets",
        image="their baked surfaces still smelled faintly of warm earth",
        tags={"tablet", "document"},
    ),
}

SCATTERERS = {
    "breeze": Scatterer(
        id="breeze",
        label="a window breeze",
        arrive="a sly breeze slipped through the high window",
        trouble="it flipped pages, rolled the scroll, and skated loose pieces over the floor",
        severity=2,
        disturbs={"papyrus", "leaf"},
        tags={"wind", "suspense"},
    ),
    "monkey": Scatterer(
        id="monkey",
        label="a fig-thief monkey",
        arrive="a fig-thief monkey swung down from a beam, chasing a stolen fig",
        trouble="his tail slapped the shelf, the fig bounced, and the papers fluttered everywhere",
        severity=3,
        disturbs={"papyrus", "leaf"},
        tags={"monkey", "humor"},
    ),
    "ibis": Scatterer(
        id="ibis",
        label="a sneezy ibis",
        arrive="a sneezy ibis strutted in, puffed up, and let out a mighty sneeze",
        trouble="the sneeze sent the light pages flying in a feathery little storm",
        severity=2,
        disturbs={"leaf", "papyrus"},
        tags={"bird", "humor"},
    ),
    "goat": Scatterer(
        id="goat",
        label="a wandering goat",
        arrive="a wandering goat poked his nose through the half-open door and nibbled at a hanging tassel",
        trouble="he butted the low stand, and the tablets clacked across the floor like startled teeth",
        severity=3,
        disturbs={"clay"},
        tags={"goat", "humor"},
    ),
}

METHODS = {
    "moon_ribbon": Method(
        id="moon_ribbon",
        label="a moon-silk ribbon",
        sense=3,
        power=2,
        suits_materials={"papyrus", "leaf"},
        needs_flexible=True,
        text="she wrapped the wandering pieces of the {document} in a soft moon-silk ribbon and snugged them into one careful bundle",
        fail="The moon-silk ribbon was too gentle. It hugged the {document}, but one loose part still slipped free.",
        qa_text="wrapped the pieces in a moon-silk ribbon to hold them together",
        tags={"ribbon", "arrange"},
    ),
    "shell_weights": Method(
        id="shell_weights",
        label="small shell weights",
        sense=3,
        power=3,
        suits_materials={"papyrus", "leaf"},
        needs_flexible=False,
        text="she arranged the {document} in order and pinned each part with small shell weights so nothing could skitter away",
        fail="The shell weights held most of the {document}, but the strongest rush had already carried one part too far.",
        qa_text="pinned the ordered pieces down with shell weights",
        tags={"weight", "arrange"},
    ),
    "sun_tray": Method(
        id="sun_tray",
        label="a numbered sun tray",
        sense=3,
        power=4,
        suits_materials={"clay"},
        needs_flexible=False,
        text="she set the {document} into a numbered sun tray, one space for each piece, so the order could not slide or bump apart",
        fail="The tray was steady, but one tablet had already skidded into a crack where no quick hand could reach it.",
        qa_text="set the pieces into a numbered tray that kept them in order",
        tags={"tray", "arrange"},
    ),
    "stack_only": Method(
        id="stack_only",
        label="bare hands alone",
        sense=1,
        power=1,
        suits_materials={"papyrus", "leaf", "clay"},
        needs_flexible=False,
        text="she tried to arrange the {document} with bare hands alone, making a neat little stack and hoping neatness would be enough",
        fail="Bare hands alone were not enough. The {document} looked ordered for a blink, and then one part slipped away again.",
        qa_text="tried to stack the pieces with bare hands alone",
        tags={"hands"},
    ),
}

HELPER = {
    "tortoise": HelperCfg(
        id="tortoise",
        label="Mossback",
        type="tortoise",
        bonus=1,
        entrance="Beside the jars slept Mossback the temple tortoise, who woke, blinked twice, and began moving with heroic slowness.",
        funny='"Do not worry," said no one at all, but Mossback looked as if he had said it anyway.',
        tags={"tortoise", "helper"},
    ),
    "ibis": HelperCfg(
        id="ibis",
        label="Feather-Foot",
        type="ibis",
        bonus=1,
        entrance="At the edge of the room stood Feather-Foot the ibis, lifting each foot as if the floor were a surprise.",
        funny='He peered at the shelves like a priest judging crumbs.',
        tags={"ibis", "helper"},
    ),
    "monkey": HelperCfg(
        id="monkey",
        label="Pico",
        type="monkey",
        bonus=2,
        entrance="From a bronze lamp hopped Pico the little monkey, wearing a fig leaf on his head like a crown.",
        funny='"I am ready for greatness," Pico seemed to declare, though he was mostly ready for snacks.',
        tags={"monkey", "helper"},
    ),
}

GIRL_NAMES = ["Nila", "Aya", "Suri", "Luma", "Tala", "Mira"]
BOY_NAMES = ["Ilan", "Kiro", "Sami", "Tarin", "Nero", "Pavo"]
KEEPER_NAMES = ["Tharos", "Selun", "Orin", "Maela"]
TRAITS = ["patient", "eager", "careful", "bright", "nimble"]


@dataclass
class StoryParams:
    place: str
    document: str
    scatterer: str
    method: str
    helper: str
    hero_name: str
    hero_gender: str
    keeper_name: str
    keeper_gender: str
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


KNOWLEDGE = {
    "document": [(
        "What is a document?",
        "A document is a piece of writing that keeps words or information safe so people can read it later. It can be a scroll, a page, or even a clay tablet."
    )],
    "scroll": [(
        "What is a scroll?",
        "A scroll is a long piece of writing rolled up into a tube. People unroll it to read the words inside."
    )],
    "pages": [(
        "Why do pages need to stay in order?",
        "Pages need to stay in order so the story or message makes sense. If they get mixed up, the words can say the wrong thing."
    )],
    "tablet": [(
        "What is a clay tablet?",
        "A clay tablet is a flat piece of dried clay with marks pressed into it. It is heavier and harder than paper or leaves."
    )],
    "wind": [(
        "Why can wind be a problem for papers?",
        "Wind can lift light papers and blow them away quickly. That is why people weigh papers down or tie them together."
    )],
    "arrange": [(
        "What does arrange mean?",
        "To arrange means to put things in the right places or order. You arrange pieces carefully so they fit or make sense."
    )],
    "ribbon": [(
        "What does a ribbon do for loose pages?",
        "A ribbon can wrap around loose pages or a scroll and help hold them together. It works best when the pieces are light and bendy."
    )],
    "weight": [(
        "Why put weights on loose papers?",
        "Small weights help keep papers from sliding or blowing away. They are useful when a breeze might move the pages."
    )],
    "tray": [(
        "Why is a tray good for heavy pieces?",
        "A tray gives each heavy piece a safe place to sit. That keeps the pieces from bumping or sliding out of order."
    )],
    "tortoise": [(
        "Why is a tortoise a funny helper?",
        "A tortoise moves very slowly, so it is funny when a slow helper is part of an urgent mission. But slow helpers can still be steady and useful."
    )],
    "ibis": [(
        "What is an ibis?",
        "An ibis is a long-legged bird with a long beak. It can pick things up neatly with its beak."
    )],
    "monkey": [(
        "Why do monkeys make stories feel lively?",
        "Monkeys jump, grab, and chatter, so they bring quick movement and mischief to a story. That can feel funny and a little suspenseful at the same time."
    )],
}
KNOWLEDGE_ORDER = [
    "document", "scroll", "pages", "tablet", "wind", "arrange",
    "ribbon", "weight", "tray", "tortoise", "ibis", "monkey",
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for document_id, document in DOCUMENTS.items():
            for scatterer_id, scatterer in SCATTERERS.items():
                if not document_at_risk(place, scatterer, document):
                    continue
                for method_id, method in METHODS.items():
                    if method.sense >= SENSE_MIN and method_fits(document, method):
                        combos.append((place_id, document_id, scatterer_id, method_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    document = f["document_cfg"]
    place = f["place_cfg"]
    scatterer = f["scatterer_cfg"]
    outcome = f["outcome"]
    helper = f["helper_cfg"]
    if outcome == "saved":
        return [
            f'Write a short myth-like story for a 3-to-5-year-old where a child must arrange a sacred document before moonrise after {scatterer.label} causes trouble.',
            f"Tell a quest story set in {place.label} where {hero.id} and {helper.label} rescue {document.label} and put it back in order just in time.",
            f'Write a gentle suspense story with a little humor, using the words "document" and "arrange", where the ending proves the old words were saved.',
        ]
    return [
        f'Write a myth-like cautionary story where a child must arrange a sacred document after {scatterer.label} scatters it, but one piece is lost before moonrise.',
        f"Tell a small quest story with humor and suspense in {place.label}, where {hero.id} tries to save {document.label} but learns the document needed a better way to be arranged.",
        f'Write a story using the words "document" and "arrange" that ends sadly but gently, with a wise elder explaining what the hero learned.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    helper = f["helper"]
    place = f["place_cfg"]
    document = f["document_cfg"]
    scatterer = f["scatterer_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young keeper of shelves, {keeper.id} the old archive-keeper, and {helper.id} the funny helper. They are together in {place.label}."
        ),
        (
            "What quest did the keeper give the child?",
            f"{keeper.id} told {hero.id} to arrange {document.order_name} before moonrise so the old words could speak clearly. The quest mattered because the sacred document had to be in the right order."
        ),
        (
            "What caused the problem?",
            f"The trouble began when {scatterer.label} scattered the document. That turned a quiet task into a race against time."
        ),
        (
            f"How did {hero.id} try to fix the problem?",
            f"{hero.id} gathered the pieces with help from {helper.id} and used {method.label}. {method.qa_text.capitalize()} so the parts could stay in order."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append((
            "Why did the plan work?",
            f"The plan worked because {method.label} suited that kind of document, and {helper.id} gave useful help. Together they were strong enough to stop the scattered pieces from escaping."
        ))
        qa.append((
            "How did the story end?",
            f"The document was saved, and the moonlight made the ordered words shine. The ending shows that chaos had been turned back into wisdom."
        ))
    else:
        qa.append((
            "Why was one piece still lost?",
            f"One piece was still lost because the trouble had grown too strong for that plan before the child finished. The moon arrived before every part could be kept safely in place."
        ))
        qa.append((
            "What did the child learn?",
            f"{hero.id} learned that a sacred document needs the right way to be arranged, not just quick hands. The lesson came from losing one part and hearing the keeper's calm wisdom."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"document", "arrange"}
    doc = f["document_cfg"]
    scatterer = f["scatterer_cfg"]
    method = f["method_cfg"]
    helper = f["helper_cfg"]
    tags |= set(doc.tags) | set(scatterer.tags) | set(method.tags) | set(helper.tags)
    mapping = {
        "scroll": "scroll",
        "pages": "pages",
        "tablet": "tablet",
        "wind": "wind",
        "arrange": "arrange",
        "ribbon": "ribbon",
        "weight": "weight",
        "tray": "tray",
        "tortoise": "tortoise",
        "ibis": "ibis",
        "monkey": "monkey",
        "document": "document",
    }
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags or mapping.get(key) in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} severity={world.facts.get('severity')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_archive",
        document="scroll",
        scatterer="breeze",
        method="shell_weights",
        helper="tortoise",
        hero_name="Nila",
        hero_gender="girl",
        keeper_name="Tharos",
        keeper_gender="man",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        place="reed_temple",
        document="leaf_pages",
        scatterer="ibis",
        method="moon_ribbon",
        helper="monkey",
        hero_name="Aya",
        hero_gender="girl",
        keeper_name="Maela",
        keeper_gender="woman",
        trait="bright",
        delay=0,
    ),
    StoryParams(
        place="peak_library",
        document="clay_tablets",
        scatterer="goat",
        method="sun_tray",
        helper="tortoise",
        hero_name="Ilan",
        hero_gender="boy",
        keeper_name="Selun",
        keeper_gender="woman",
        trait="patient",
        delay=1,
    ),
    StoryParams(
        place="moon_archive",
        document="leaf_pages",
        scatterer="monkey",
        method="moon_ribbon",
        helper="ibis",
        hero_name="Tala",
        hero_gender="girl",
        keeper_name="Orin",
        keeper_gender="man",
        trait="eager",
        delay=2,
    ),
]


def explain_rejection(place: Place, document: DocumentCfg, scatterer: Scatterer, method: Method) -> str:
    if scatterer.id not in place.afford_scatterers:
        return (
            f"(No story: {scatterer.label} does not belong in {place.label}. "
            f"Pick a disturbance the place actually affords.)"
        )
    if not document_at_risk(place, scatterer, document):
        return (
            f"(No story: {scatterer.label} would not really scatter {document.label}. "
            f"The disturbance and document do not fit each other.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too flimsy and scores below the "
            f"common-sense threshold. Choose a steadier way to arrange the document.)"
        )
    if not method_fits(document, method):
        return (
            f"(No story: {method.label} is not a good way to arrange {document.label}. "
            f"The method must suit the document's material.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.document not in DOCUMENTS or params.scatterer not in SCATTERERS:
        return "?"
    if params.method not in METHODS or params.helper not in HELPER:
        return "?"
    return "saved" if saved_by(METHODS[params.method], HELPER[params.helper], SCATTERERS[params.scatterer], params.delay) else "lost"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
at_risk(P,D,S) :- place(P), document(D), scatterer(S), affords(P,S), disturbs(S,M), material(D,M).
sensible_method(M) :- method(M), sense(M,V), sense_min(Min), V >= Min.
fits(D,M) :- method(M), document(D), material(D,Mat), suits(M,Mat), not needs_flexible(M).
fits(D,M) :- method(M), document(D), material(D,Mat), suits(M,Mat), needs_flexible(M), flexible(D).
valid(P,D,S,M) :- at_risk(P,D,S), sensible_method(M), fits(D,M).

% --- outcome model ---------------------------------------------------------
danger(V) :- chosen_scatterer(S), scatter_severity(S,Sev), delay(D), V = Sev + D.
strength(V) :- chosen_method(M), method_power(M,P), chosen_helper(H), helper_bonus(H,B), V = P + B.

outcome(saved) :- strength(S), danger(D), S >= D.
outcome(lost)  :- strength(S), danger(D), S < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.afford_scatterers):
            lines.append(asp.fact("affords", pid, sid))
    for did, document in DOCUMENTS.items():
        lines.append(asp.fact("document", did))
        lines.append(asp.fact("material", did, document.material))
        if document.flexible:
            lines.append(asp.fact("flexible", did))
    for sid, scatterer in SCATTERERS.items():
        lines.append(asp.fact("scatterer", sid))
        lines.append(asp.fact("scatter_severity", sid, scatterer.severity))
        for material in sorted(scatterer.disturbs):
            lines.append(asp.fact("disturbs", sid, material))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("method_power", mid, method.power))
        for material in sorted(method.suits_materials):
            lines.append(asp.fact("suits", mid, material))
        if method.needs_flexible:
            lines.append(asp.fact("needs_flexible", mid))
    for hid, helper in HELPER.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_bonus", hid, helper.bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_scatterer", params.scatterer),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child must arrange a sacred document after a comic disturbance."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--document", choices=DOCUMENTS)
    ap.add_argument("--scatterer", choices=SCATTERERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPER)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra beats lost before the rescue plan is finished")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.document and args.scatterer and args.method:
        place = PLACES[args.place]
        document = DOCUMENTS[args.document]
        scatterer = SCATTERERS[args.scatterer]
        method = METHODS[args.method]
        if not (document_at_risk(place, scatterer, document) and method.sense >= SENSE_MIN and method_fits(document, method)):
            raise StoryError(explain_rejection(place, document, scatterer, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        m = METHODS[args.method]
        raise StoryError(
            f"(Refusing method '{m.id}': it scores too low on common sense "
            f"(sense={m.sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.document is None or combo[1] == args.document)
        and (args.scatterer is None or combo[2] == args.scatterer)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, document_id, scatterer_id, method_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPER))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    keeper_name = rng.choice([n for n in KEEPER_NAMES if n != hero_name])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        document=document_id,
        scatterer=scatterer_id,
        method=method_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.place not in PLACES:
        missing.append(f"place={params.place}")
    if params.document not in DOCUMENTS:
        missing.append(f"document={params.document}")
    if params.scatterer not in SCATTERERS:
        missing.append(f"scatterer={params.scatterer}")
    if params.method not in METHODS:
        missing.append(f"method={params.method}")
    if params.helper not in HELPER:
        missing.append(f"helper={params.helper}")
    if missing:
        raise StoryError("(Invalid parameters: " + ", ".join(missing) + ")")

    place = PLACES[params.place]
    document = DOCUMENTS[params.document]
    scatterer = SCATTERERS[params.scatterer]
    method = METHODS[params.method]
    helper = HELPER[params.helper]

    if not document_at_risk(place, scatterer, document):
        raise StoryError(explain_rejection(place, document, scatterer, method))
    if method.sense < SENSE_MIN or not method_fits(document, method):
        raise StoryError(explain_rejection(place, document, scatterer, method))

    world = tell(
        place=place,
        document=document,
        scatterer=scatterer,
        method=method,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        keeper_name=params.keeper_name,
        keeper_gender=params.keeper_gender,
        delay=params.delay,
    )
    world.get("hero").traits.append(params.trait)

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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sensible = set(asp_sensible_methods())
    if py_sensible == asp_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sensible))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "arrange" not in sample.story.lower() or "document" not in sample.story.lower():
            raise StoryError("Smoke test story missing required content.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible_method/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = ", ".join(asp_sensible_methods())
        print(f"sensible methods: {methods}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, document, scatterer, method) combos:\n")
        for place, document, scatterer, method in combos:
            print(f"  {place:12} {document:12} {scatterer:10} {method}")
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
                f"### {p.hero_name}: {p.document} in {p.place} "
                f"({p.scatterer}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
