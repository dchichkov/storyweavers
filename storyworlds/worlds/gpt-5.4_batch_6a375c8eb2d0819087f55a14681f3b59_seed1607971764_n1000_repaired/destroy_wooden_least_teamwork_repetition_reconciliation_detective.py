#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py
================================================================================================

A standalone story world for a tiny detective tale: children investigate a threat
to a treasured wooden object, use teamwork and repetition to follow sensible
clues, clear an innocent friend, and reconcile.

The domain is small on purpose. A child sees fresh marks near a treasured wooden
toy or prop and blurts out that another child must want to destroy it. Two young
detectives do not trust the first angry guess. They repeat a clue-finding ritual
together until they uncover the real harmless cause, then help everyone make up.

Run it
------
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py --all
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py --qa --json
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py --trace
    python storyworlds/worlds/gpt-5.4/destroy_wooden_least_teamwork_repetition_reconciliation_detective.py --verify
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
REPEAT_MIN = 3
TEAMWORK_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    wooden: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher", "librarian"}
        male = {"boy", "man", "caretaker", "janitor"}
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
class Setting:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
    hideaway: str = ""
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    place: str
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
class Cause:
    id: str
    label: str
    phrase: str
    mark: str
    trail: str
    danger: str
    reveal: str
    match_method: str
    fix: str
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
class Method:
    id: str
    label: str
    chant: str
    action: str
    discovery: str
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
        self.facts: dict = {
            "checks": 0,
            "accusation": False,
            "clue_found": False,
            "apology_offered": False,
            "reconciled": False,
            "solved": False,
            "threat_seen": False,
            "least_likely": "",
        }

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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role != "adult"]


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


def _r_threat(world: World) -> list[str]:
    treasure = world.get("treasure")
    owner = world.get("owner")
    if not world.facts.get("cause_active"):
        return []
    sig = ("threat", world.facts["cause"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if treasure.wooden:
        treasure.meters["risk"] += 1
        owner.memes["fear"] += 1
        world.facts["threat_seen"] = True
    return []


def _r_conflict(world: World) -> list[str]:
    owner = world.get("owner")
    accused = world.get("accused")
    if not world.facts.get("accusation"):
        return []
    sig = ("conflict", accused.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["anger"] += 1
    accused.memes["hurt"] += 1
    owner.memes["conflict"] += 1
    accused.memes["conflict"] += 1
    return []


def _r_discovery(world: World) -> list[str]:
    lead = world.get("lead")
    partner = world.get("partner")
    if world.facts["checks"] < REPEAT_MIN:
        return []
    if world.facts["method"] != world.facts["cause_match"]:
        return []
    sig = ("discovery", world.facts["method"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["clue_found"] = True
    world.facts["solved"] = True
    lead.memes["confidence"] += 1
    partner.memes["confidence"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    owner = world.get("owner")
    accused = world.get("accused")
    if not world.facts.get("clue_found"):
        return []
    if not world.facts.get("apology_offered"):
        return []
    sig = ("reconcile", owner.id, accused.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["conflict"] = 0.0
    accused.memes["conflict"] = 0.0
    owner.memes["relief"] += 1
    accused.memes["relief"] += 1
    owner.memes["friendship"] += 1
    accused.memes["friendship"] += 1
    world.facts["reconciled"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="threat", tag="physical", apply=_r_threat),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="discovery", tag="knowledge", apply=_r_discovery),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "school_hall": Setting(
        id="school_hall",
        label="the school hall",
        detail="Sunlight fell in long stripes across the floor, and a row of hooks held backpacks and coats.",
        affords={"umbrellas", "cart"},
        hideaway="beside the umbrella stand",
    ),
    "library_nook": Setting(
        id="library_nook",
        label="the library nook",
        detail="The room was hushed except for pages whispering as children turned them.",
        affords={"cart", "umbrellas"},
        hideaway="behind the return cart",
    ),
    "community_room": Setting(
        id="community_room",
        label="the community room",
        detail="Paper stars hung over the tables, and old costumes waited in a neat basket.",
        affords={"umbrellas", "cart", "puppy"},
        hideaway="under the coat bench",
    ),
}

TREASURES = {
    "train": Treasure(
        id="train",
        label="wooden train",
        phrase="a red wooden train with smooth little wheels",
        place="on the low display table",
        ending_image="The wooden train stood on a dry high shelf, and its red paint looked bright again.",
        tags={"wooden", "toy"},
    ),
    "puppet": Treasure(
        id="puppet",
        label="wooden puppet",
        phrase="a wooden puppet with a blue coat and tiny strings",
        place="on the rehearsal shelf",
        ending_image="The wooden puppet hung safe on its hook, with its blue coat swaying very gently.",
        tags={"wooden", "toy"},
    ),
    "lion": Treasure(
        id="lion",
        label="wooden lion",
        phrase="a carved wooden lion with a brave square mane",
        place="on the welcome bench",
        ending_image="The wooden lion sat on the middle shelf, looking ready to guard the room all night.",
        tags={"wooden", "toy"},
    ),
}

CAUSES = {
    "umbrellas": Cause(
        id="umbrellas",
        label="umbrella stand",
        phrase="a dripping umbrella stand",
        mark="small wet rings",
        trail="a dotted trail of drips",
        danger="If the drips kept falling, they might swell the wood and slowly destroy the paint.",
        reveal="Water, not anger, had made the trouble.",
        match_method="drip_map",
        fix="they moved the umbrella stand to a mat and carried the treasure higher",
        tags={"umbrella", "water"},
    ),
    "cart": Cause(
        id="cart",
        label="rolling cart",
        phrase="a squeaky rolling cart",
        mark="dark little scuffs",
        trail="a line of rubber marks and a tiny squeak",
        danger="If the cart kept bumping the corner, it could chip the wood and destroy a piece of it.",
        reveal="The cart had been nudging too close each time someone passed.",
        match_method="squeak_listen",
        fix="they locked the cart wheels and slid the treasure away from the path",
        tags={"cart", "bump"},
    ),
    "puppy": Cause(
        id="puppy",
        label="puppy",
        phrase="a fluffy puppy with a ribbon collar",
        mark="dusty paw prints and one nibble nick",
        trail="a row of small paw prints",
        danger="If the puppy kept chewing, it might destroy a corner of the wood.",
        reveal="A curious puppy, not a mean child, had been nosing around.",
        match_method="paw_dusting",
        fix="they led the puppy to its blanket and set the treasure on a tall shelf",
        tags={"puppy", "paw"},
    ),
}

METHODS = {
    "drip_map": Method(
        id="drip_map",
        label="drip map",
        chant="Look low, blot, and check again.",
        action="They crouched low and followed every wet dot.",
        discovery="At the third check, the drips lined up straight toward the stand.",
        tags={"detective", "water"},
    ),
    "squeak_listen": Method(
        id="squeak_listen",
        label="squeak listen",
        chant="Freeze, listen, and check again.",
        action="They held still whenever the room moved, then listened for the tiny squeak.",
        discovery="At the third check, the squeak came exactly when the cart wheel kissed the bench.",
        tags={"detective", "sound"},
    ),
    "paw_dusting": Method(
        id="paw_dusting",
        label="paw dusting",
        chant="Dust, compare, and check again.",
        action="They sprinkled a little chalk dust near the table edge and watched for prints.",
        discovery="At the third check, four small paw prints curved under the bench.",
        tags={"detective", "paw"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Tess", "Ivy", "Juno", "Ella", "Ruth"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Leo", "Ben", "Theo", "Jasper", "Sam"]

ADULTS = {
    "teacher": ("Ms. Bell", "teacher"),
    "librarian": ("Ms. Reed", "librarian"),
    "caretaker": ("Mr. Stone", "caretaker"),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for treasure_id in TREASURES:
            for cause_id, cause in CAUSES.items():
                if cause_id not in setting.affords:
                    continue
                for method_id in METHODS:
                    if method_id == cause.match_method:
                        combos.append((setting_id, treasure_id, cause_id, method_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    treasure: str
    cause: str
    method: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    owner_name: str
    owner_gender: str
    accused_name: str
    accused_gender: str
    adult_role: str
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n not in avoid]
    if not options:
        raise StoryError("(No names left to choose from.)")
    return rng.choice(options)


def predict_case(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("treasure").meters["risk"],
        "fear": sim.get("owner").memes["fear"],
    }


def introduce(world: World, lead: Entity, partner: Entity, owner: Entity,
              accused: Entity, treasure: Treasure, setting: Setting, adult: Entity) -> None:
    lead.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    owner.memes["love"] += 1
    world.say(
        f"In {setting.label}, {lead.id} and {partner.id} liked to call themselves the Morning Detectives. "
        f"{setting.detail}"
    )
    world.say(
        f"That day their friend {owner.id} had brought {treasure.phrase} and set it {treasure.place}. "
        f"{owner.id} loved it so much that even a tiny scratch felt important."
    )
    world.say(
        f"{adult.id}, the {adult.type}, was sorting papers nearby and thought the room was the quietest place in the building."
    )


def discover_marks(world: World, owner: Entity, accused: Entity, treasure: Treasure, cause: Cause) -> None:
    pred = predict_case(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"Then {owner.id} gasped. Fresh {cause.mark} sat beside the {treasure.label}. "
        f"\"Someone is trying to destroy it!\" {owner.id} cried."
    )
    world.facts["accusation"] = True
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} turned too fast and pointed at {accused.id}. "
        f"\"You were the last one near it!\""
    )
    world.say(
        f"{accused.id}'s face fell. \"I only walked past,\" {accused.pronoun()} said. "
        f"The room suddenly did not feel quiet anymore."
    )


def take_case(world: World, lead: Entity, partner: Entity, treasure: Treasure, cause: Cause) -> None:
    lead.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    world.say(
        f"{lead.id} lifted a finger like a storybook detective. "
        f"\"No guessing,\" {lead.pronoun()} said. \"We need clues before we blame anyone.\""
    )
    world.say(
        f"{partner.id} nodded at once. \"The marks are real, and the {treasure.label} is wooden,\" "
        f"{partner.pronoun()} said. \"If we do nothing, {cause.danger.lower()}\""
    )
    world.say(
        f"So the two detectives promised to work together, because one pair of eyes was good and two pairs were better."
    )


def repeated_search(world: World, lead: Entity, partner: Entity, method: Method, cause: Cause, setting: Setting) -> None:
    for step in range(1, 4):
        world.facts["checks"] += 1
        lead.memes["patience"] += 1
        partner.memes["patience"] += 1
        world.say(f"\"{method.chant}\" the detectives whispered for the {step} time.")
        world.say(method.action)
        if step == 1:
            world.say(
                f"First they noticed the easiest clue: {cause.mark} near the treasure, but that clue could still mean many things."
            )
        elif step == 2:
            world.say(
                f"Next they found {cause.trail} leading toward {setting.hideaway}. It was a better clue, but not the whole answer yet."
            )
        else:
            world.say(method.discovery)
        propagate(world, narrate=False)


def reveal_truth(world: World, lead: Entity, partner: Entity, owner: Entity,
                 accused: Entity, treasure: Treasure, cause: Cause, adult: Entity) -> None:
    if not world.facts["clue_found"]:
        raise StoryError("(The detectives did not gather enough repeated evidence to solve the case.)")
    accused.memes["trust"] += 1
    world.facts["least_likely"] = accused.id
    world.say(
        f"{lead.id} and {partner.id} looked at each other at the same time. "
        f"\"Case solved,\" they said together."
    )
    world.say(
        f"{lead.id} pointed to the trail. {cause.reveal} "
        f"\"{accused.id} was the least likely suspect after all,\" {partner.id} said."
    )
    world.say(
        f"{adult.id} came over, followed the clues, and agreed. \"Good detective work,\" "
        f"{adult.pronoun()} said. \"You checked more than once, and that made the answer fair.\""
    )
    world.say(
        f"Together they made the room safe: {cause.fix}. The danger to the {treasure.label} was over."
    )


def reconcile(world: World, owner: Entity, accused: Entity) -> None:
    world.facts["apology_offered"] = True
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} looked down at {owner.pronoun('possessive')} shoes. "
        f"\"I was scared and I blamed you too fast,\" {owner.pronoun()} said. \"I'm sorry.\""
    )
    world.say(
        f"{accused.id} gave a small nod. \"I forgive you,\" {accused.pronoun()} answered. "
        f"Then the two friends shook hands and smiled the shaky kind of smile that grows steadier in a moment."
    )


def ending(world: World, lead: Entity, partner: Entity, owner: Entity,
           accused: Entity, treasure: Treasure) -> None:
    for kid in (lead, partner, owner, accused):
        kid.memes["relief"] += 1
    world.say(
        f"Before they went home, {lead.id} wrote the case title on a scrap of paper: "
        f"\"The Mystery of the Threatened {treasure.label.title()}.\""
    )
    world.say(
        f"{partner.id} tucked the paper under a pebble, and the four children stood together long enough to enjoy the solved feeling."
    )
    world.say(treasure.ending_image)


def tell(setting: Setting, treasure_cfg: Treasure, cause_cfg: Cause, method_cfg: Method,
         lead_name: str, lead_gender: str, partner_name: str, partner_gender: str,
         owner_name: str, owner_gender: str, accused_name: str, accused_gender: str,
         adult_role: str) -> World:
    world = World(setting)
    lead = world.add(Entity(
        id=lead_name, kind="character", type=lead_gender, role="lead",
        traits=["careful", "curious"], label=lead_name,
    ))
    partner = world.add(Entity(
        id=partner_name, kind="character", type=partner_gender, role="partner",
        traits=["steady", "kind"], label=partner_name,
    ))
    owner = world.add(Entity(
        id=owner_name, kind="character", type=owner_gender, role="owner",
        traits=["proud", "worried"], label=owner_name,
    ))
    accused = world.add(Entity(
        id=accused_name, kind="character", type=accused_gender, role="accused",
        traits=["gentle"], label=accused_name,
    ))
    adult_name, adult_type = ADULTS[adult_role]
    adult = world.add(Entity(
        id=adult_name, kind="character", type=adult_type, role="adult",
        traits=["calm"], label=f"the {adult_type}",
    ))
    treasure = world.add(Entity(
        id="treasure", kind="thing", type="treasure", role="treasure",
        label=treasure_cfg.label, wooden=True, movable=True,
        attrs={"place": treasure_cfg.place},
    ))
    source = world.add(Entity(
        id="source", kind="thing", type="source", role="cause",
        label=cause_cfg.label, attrs={"phrase": cause_cfg.phrase},
    ))
    room = world.add(Entity(
        id="room", kind="thing", type="room", role="room", label=setting.label,
    ))

    world.facts.update(
        setting=setting,
        treasure_cfg=treasure_cfg,
        cause_cfg=cause_cfg,
        method_cfg=method_cfg,
        cause=cause_cfg.id,
        method=method_cfg.id,
        cause_match=cause_cfg.match_method,
        cause_active=True,
        lead=lead,
        partner=partner,
        owner=owner,
        accused=accused,
        adult=adult,
        treasure=treasure,
        source=source,
        room=room,
    )
    propagate(world, narrate=False)

    introduce(world, lead, partner, owner, accused, treasure_cfg, setting, adult)
    world.para()
    discover_marks(world, owner, accused, treasure_cfg, cause_cfg)
    take_case(world, lead, partner, treasure_cfg, cause_cfg)
    world.para()
    repeated_search(world, lead, partner, method_cfg, cause_cfg, setting)
    world.para()
    reveal_truth(world, lead, partner, owner, accused, treasure_cfg, cause_cfg, adult)
    reconcile(world, owner, accused)
    world.para()
    ending(world, lead, partner, owner, accused, treasure_cfg)

    world.facts.update(
        solved=world.facts["solved"],
        reconciled=world.facts["reconciled"],
        least_likely=world.facts["least_likely"],
    )
    return world


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues and checks them carefully before deciding what happened. Good detectives try to be fair, not fast."
    )],
    "wooden": [(
        "What does wooden mean?",
        "Wooden means made of wood. Wood can be strong, but water, bites, and hard bumps can still damage it."
    )],
    "umbrella": [(
        "Why can dripping water be bad for a wooden toy?",
        "Wood can swell or stain when water keeps dripping on it. If no one moves the water away, the toy can be damaged over time."
    )],
    "cart": [(
        "Why can a rolling cart be a problem near a shelf or bench?",
        "If a cart bumps something again and again, it can scrape or chip it. Little bumps repeated many times can make a bigger problem."
    )],
    "puppy": [(
        "Why do puppies need help around special objects?",
        "Puppies are curious and often sniff or chew before they know better. Grown-ups and children help by moving special things out of reach."
    )],
    "teamwork": [(
        "Why does teamwork help in a mystery?",
        "Teamwork gives a mystery more eyes, ears, and ideas. One child may notice what another child misses."
    )],
    "repetition": [(
        "Why is checking again useful?",
        "Checking again helps you see whether a clue keeps matching the same answer. Repetition can turn a guess into a careful finding."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace after hurt feelings or an argument. It often starts with a true apology and forgiveness."
    )],
    "apology": [(
        "Why is apologizing important after blaming someone unfairly?",
        "An apology tells the other person you know you hurt them and want to make it right. It helps trust begin to grow again."
    )],
}
KNOWLEDGE_ORDER = [
    "detective", "wooden", "umbrella", "cart", "puppy",
    "teamwork", "repetition", "reconciliation", "apology",
]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    treasure = world.facts["treasure_cfg"]
    cause = world.facts["cause_cfg"]
    method = world.facts["method_cfg"]
    lead = world.facts["lead"]
    partner = world.facts["partner"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old where a treasured {treasure.label} seems in danger and two child detectives solve the case with teamwork.',
        f'Tell a mystery set in {setting.label} where {lead.id} and {partner.id} repeat the line "{method.chant}" until they find the real clue.',
        f'Write a story that includes the words "destroy", "wooden", and "least", where a wrong accusation is cleared and friends reconcile after learning the truth about {cause.phrase}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    lead = world.facts["lead"]
    partner = world.facts["partner"]
    owner = world.facts["owner"]
    accused = world.facts["accused"]
    adult = world.facts["adult"]
    setting = world.facts["setting"]
    treasure = world.facts["treasure_cfg"]
    cause = world.facts["cause_cfg"]
    method = world.facts["method_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who were the detectives in the story?",
            f"The detectives were {lead.id} and {partner.id}. They chose to investigate together instead of letting the first angry guess decide the case."
        ),
        (
            f"Why did {owner.id} get upset?",
            f"{owner.id} saw fresh {cause.mark} beside the {treasure.label} and got scared that something might destroy it. That fear made {owner.pronoun()} blame {accused.id} too quickly."
        ),
        (
            "What clue-checking words did the detectives repeat?",
            f'They repeated, "{method.chant}" The repetition mattered because each check gave them one more piece of the same answer.'
        ),
        (
            f"How did teamwork help solve the mystery?",
            f"{lead.id} and {partner.id} worked side by side, so one could watch while the other listened or searched. Because they kept checking together, the clue trail finally pointed to {cause.phrase} instead of to {accused.id}."
        ),
        (
            f"Who was really causing the trouble near the {treasure.label}?",
            f"It was {cause.phrase}. {cause.reveal} That is why {accused.id} turned out to be the least likely suspect."
        ),
        (
            "How did the friends reconcile at the end?",
            f"{owner.id} apologized for the unfair blame, and {accused.id} forgave {owner.pronoun('object')}. Their reconciliation happened after the true clue was found, so the apology rested on the real facts."
        ),
        (
            f"What changed by the ending?",
            f"The danger to the {treasure.label} was fixed, and the children were not arguing anymore. The last image shows the treasure safe and the friendships mended in {setting.label}."
        ),
    ]
    if world.facts.get("predicted_risk", 0) >= THRESHOLD:
        qa.append((
            f"Why did the detectives act quickly even before the full answer was known?",
            f"They could already tell the {treasure.label} was at risk because the first marks were real. Even before solving the mystery, they knew they should protect the wooden object while they searched."
        ))
    if adult:
        qa.append((
            f"What did the grown-up do in the story?",
            f"{adult.id} stayed calm, listened to the evidence, and agreed with the detectives after the clues matched. That helped the ending feel fair instead of scoldy."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"detective", "wooden", "teamwork", "repetition", "reconciliation", "apology"}
    cause = world.facts["cause_cfg"]
    if "umbrella" in cause.tags or "water" in cause.tags:
        tags.add("umbrella")
    if "cart" in cause.tags or "bump" in cause.tags:
        tags.add("cart")
    if "puppy" in cause.tags or "paw" in cause.tags:
        tags.add("puppy")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.wooden:
            bits.append("wooden=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    fact_view = {
        k: v for k, v in world.facts.items()
        if k not in {"lead", "partner", "owner", "accused", "adult", "treasure", "source", "room",
                     "setting", "treasure_cfg", "cause_cfg", "method_cfg"}
    }
    lines.append(f"  facts: {fact_view}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, cause_id: str, method_id: str) -> str:
    if cause_id not in SETTINGS[setting_id].affords:
        return (
            f"(No story: {SETTINGS[setting_id].label} does not sensibly support the cause "
            f"'{cause_id}', so the mystery would have no honest clue trail there.)"
        )
    if method_id != CAUSES[cause_id].match_method:
        return (
            f"(No story: the method '{method_id}' does not match the clue pattern left by "
            f"'{cause_id}'. A fair detective story needs the search method to fit the evidence.)"
        )
    return "(No story: that combination does not form a fair detective case.)"


CURATED = [
    StoryParams(
        setting="school_hall",
        treasure="train",
        cause="umbrellas",
        method="drip_map",
        lead_name="Lina",
        lead_gender="girl",
        partner_name="Milo",
        partner_gender="boy",
        owner_name="Nora",
        owner_gender="girl",
        accused_name="Finn",
        accused_gender="boy",
        adult_role="teacher",
    ),
    StoryParams(
        setting="library_nook",
        treasure="puppet",
        cause="cart",
        method="squeak_listen",
        lead_name="Owen",
        lead_gender="boy",
        partner_name="Tess",
        partner_gender="girl",
        owner_name="Maya",
        owner_gender="girl",
        accused_name="Leo",
        accused_gender="boy",
        adult_role="librarian",
    ),
    StoryParams(
        setting="community_room",
        treasure="lion",
        cause="puppy",
        method="paw_dusting",
        lead_name="Ivy",
        lead_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        owner_name="Ella",
        owner_gender="girl",
        accused_name="Sam",
        accused_gender="boy",
        adult_role="caretaker",
    ),
    StoryParams(
        setting="community_room",
        treasure="train",
        cause="cart",
        method="squeak_listen",
        lead_name="Ruth",
        lead_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        owner_name="Juno",
        owner_gender="girl",
        accused_name="Leo",
        accused_gender="boy",
        adult_role="teacher",
    ),
]


ASP_RULES = r"""
wooden_treasure(T) :- treasure(T).

valid(S,T,C,M) :- setting(S), treasure(T), cause(C), method(M),
                  affords(S,C), matches(C,M), wooden_treasure(T).

solved(C,M) :- matches(C,M), repeats(R), repeat_min(Min), R >= Min,
               teamwork_level(Tw), teamwork_min(Tm), Tw >= Tm.
reconciled :- solved(C,M), apology.

#show valid/4.
#show solved/2.
#show reconciled/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for cause_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, cause_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("matches", cause_id, cause.match_method))
    for method_id in METHODS:
        lines.append(asp.fact("method", method_id))
    lines.append(asp.fact("repeat_min", REPEAT_MIN))
    lines.append(asp.fact("teamwork_min", TEAMWORK_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(cause_id: str, method_id: str, repeats: int = 3, teamwork: int = 2, apology: bool = True) -> tuple[bool, bool]:
    import asp

    extra_lines = [
        asp.fact("repeats", repeats),
        asp.fact("teamwork_level", teamwork),
    ]
    if apology:
        extra_lines.append(asp.fact("apology"))
    model = asp.one_model(asp_program("\n".join(extra_lines)))
    solved = any(atom == (cause_id, method_id) for atom in asp.atoms(model, "solved"))
    reconciled = bool(asp.atoms(model, "reconciled"))
    return solved, reconciled


def outcome_of(params: StoryParams) -> tuple[bool, bool]:
    solved = params.method == CAUSES[params.cause].match_method
    solved = solved and REPEAT_MIN >= 3 and TEAMWORK_MIN >= 2
    reconciled = solved
    return solved, reconciled


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story world about a threatened wooden treasure, repeated clue checking, teamwork, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--adult-role", choices=ADULTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid detective-case combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause and args.cause not in SETTINGS[args.setting].affords:
        raise StoryError(explain_rejection(args.setting, args.cause, args.method or CAUSES[args.cause].match_method))
    if args.cause and args.method and args.method != CAUSES[args.cause].match_method:
        chosen_setting = args.setting or next(iter(SETTINGS))
        if args.cause in SETTINGS[chosen_setting].affords:
            raise StoryError(explain_rejection(chosen_setting, args.cause, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.cause is None or combo[2] == args.cause)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treasure_id, cause_id, method_id = rng.choice(sorted(combos))
    adult_role = args.adult_role or rng.choice(sorted(ADULTS))

    genders = [rng.choice(["girl", "boy"]) for _ in range(4)]
    used: set[str] = set()
    lead_name = _pick_name(rng, genders[0], used)
    used.add(lead_name)
    partner_name = _pick_name(rng, genders[1], used)
    used.add(partner_name)
    owner_name = _pick_name(rng, genders[2], used)
    used.add(owner_name)
    accused_name = _pick_name(rng, genders[3], used)

    return StoryParams(
        setting=setting_id,
        treasure=treasure_id,
        cause=cause_id,
        method=method_id,
        lead_name=lead_name,
        lead_gender=genders[0],
        partner_name=partner_name,
        partner_gender=genders[1],
        owner_name=owner_name,
        owner_gender=genders[2],
        accused_name=accused_name,
        accused_gender=genders[3],
        adult_role=adult_role,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.adult_role not in ADULTS:
        raise StoryError(f"(Unknown adult role: {params.adult_role})")
    if (params.setting, params.treasure, params.cause, params.method) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.setting, params.cause, params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        treasure_cfg=TREASURES[params.treasure],
        cause_cfg=CAUSES[params.cause],
        method_cfg=METHODS[params.method],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        accused_name=params.accused_name,
        accused_gender=params.accused_gender,
        adult_role=params.adult_role,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    for params in CURATED:
        py_solved, py_reconciled = outcome_of(params)
        asp_solved, asp_reconciled = asp_outcome(params.cause, params.method)
        if (py_solved, py_reconciled) != (asp_solved, asp_reconciled):
            rc = 1
            print(
                f"MISMATCH in outcome for {params.setting}/{params.treasure}/{params.cause}/{params.method}: "
                f"python={(py_solved, py_reconciled)} clingo={(asp_solved, asp_reconciled)}"
            )
    if rc == 0:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure, cause, method) combos:\n")
        for setting_id, treasure_id, cause_id, method_id in combos:
            print(f"  {setting_id:14} {treasure_id:8} {cause_id:10} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.treasure} / {p.cause} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
