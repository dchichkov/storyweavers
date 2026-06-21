#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py
=================================================================================================

A standalone storyworld about two children at a cliff lookout who build a
pretend forge beside a tiny chapel, lose a special keepsake in the wind, quarrel
in a funny way, and then reconcile after help, apology, and a better plan.

Run it
------
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py --keepsake bell --snag banner --tool shepherd_hook --apology goofy_song
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py --tool jump
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/forge_religious_cliff_lookout_reconciliation_lesson_learned.py --verify
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
WARMTH_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt"}.get(self.type, self.type)
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
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    weight: str
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
class Snag:
    id: str
    label: str
    the: str
    place: str
    reach: int
    delicate: bool
    landing: str
    weights: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    sense: int
    reach: int
    gentle: bool
    text: str
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
class Apology:
    id: str
    warmth: int
    text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "gusted": False,
            "quarreled": False,
            "recovered": False,
            "made_up": False,
            "lesson": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"borrower", "owner"}]

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


def _r_blown(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    snag = world.get("snag")
    if not world.facts["gusted"]:
        return []
    if keepsake.meters["unsecured"] < THRESHOLD:
        return []
    sig = ("blown", snag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keepsake.meters["lost"] += 1
    snag.meters["holding"] += 1
    owner = world.get("owner")
    borrower = world.get("borrower")
    owner.memes["alarm"] += 1
    owner.memes["cross"] += 1
    borrower.memes["guilt"] += 1
    borrower.memes["cross"] += 1
    return ["__blown__"]


def _r_quarrel(world: World) -> list[str]:
    borrower = world.get("borrower")
    owner = world.get("owner")
    if borrower.memes["cross"] < THRESHOLD or owner.memes["cross"] < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["quarreled"] = True
    borrower.memes["distance"] += 1
    owner.memes["distance"] += 1
    return ["__quarrel__"]


def _r_relief(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    if keepsake.meters["recovered"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["alarm"] = 0.0
    return []


def _r_make_up(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    borrower = world.get("borrower")
    owner = world.get("owner")
    if keepsake.meters["recovered"] < THRESHOLD:
        return []
    if borrower.memes["sorry"] < THRESHOLD or owner.memes["soft"] < THRESHOLD:
        return []
    sig = ("make_up",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (borrower, owner):
        kid.memes["distance"] = 0.0
        kid.memes["cross"] = 0.0
        kid.memes["friendship"] += 1
    world.facts["made_up"] = True
    return ["__made_up__"]


CAUSAL_RULES = [
    Rule(name="blown", tag="physical", apply=_r_blown),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="relief", tag="emotional", apply=_r_relief),
    Rule(name="make_up", tag="social", apply=_r_make_up),
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
        for sent in produced:
            world.say(sent)
    return produced


def drift_possible(keepsake: Keepsake, snag: Snag) -> bool:
    return keepsake.weight in snag.weights


def rescue_possible(tool: Tool, snag: Snag) -> bool:
    if tool.reach < snag.reach:
        return False
    if snag.delicate and not tool.gentle:
        return False
    return True


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def reconciling_apologies() -> list[Apology]:
    return [ap for ap in APOLOGIES.values() if ap.warmth >= WARMTH_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for keepsake_id, keepsake in KEEPSAKES.items():
        for snag_id, snag in SNAGS.items():
            if not drift_possible(keepsake, snag):
                continue
            for tool_id, tool in TOOLS.items():
                if tool.sense < SENSE_MIN or not rescue_possible(tool, snag):
                    continue
                for apology_id, apology in APOLOGIES.items():
                    if apology.warmth >= WARMTH_MIN:
                        combos.append((keepsake_id, snag_id, tool_id, apology_id))
    return combos


def explain_bad_snag(keepsake: Keepsake, snag: Snag) -> str:
    return (
        f"(No story: a {keepsake.label} is too {keepsake.weight} for {snag.the}. "
        f"The wind at the cliff lookout could not believably carry it there.)"
    )


def explain_bad_tool(tool: Tool, snag: Snag) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': {tool.label} is too silly or unsafe for a real rescue "
            f"(sense={tool.sense} < {SENSE_MIN}). Pick a calmer helper tool.)"
        )
    if tool.reach < snag.reach:
        return (
            f"(No story: {tool.label} cannot reach {snag.the}. "
            f"Choose something longer, like a ladder or a shepherd hook.)"
        )
    return (
        f"(No story: {tool.label} would snag or crush the keepsake at {snag.the}. "
        f"That place needs a gentler tool.)"
    )


def explain_bad_apology(apology: Apology) -> str:
    return (
        f"(No story: the apology '{apology.id}' is too weak to support reconciliation "
        f"(warmth={apology.warmth} < {WARMTH_MIN}). This world requires a real making-up at the end.)"
    )


def introduce(world: World, borrower: Entity, owner: Entity, helper: Entity,
              keepsake: Keepsake) -> None:
    borrower.memes["play"] += 1
    owner.memes["play"] += 1
    world.say(
        f"At the cliff lookout above the sea, {borrower.id} and {owner.id} built a pretend forge "
        f"from a biscuit tin, three red paper strips, and a pair of cardboard bellows that honked "
        f"whenever the wind shoved through them."
    )
    world.say(
        f"Just beyond the bench stood a tiny chapel, and people were getting ready for a small religious walk, "
        f"so the children said their forge was making shiny treasures for the day's procession."
    )
    world.say(
        f"{owner.id} had brought {keepsake.phrase}, meant {keepsake.purpose}. It was {keepsake.material} and very special."
    )
    world.say(
        f"{helper.id}, {borrower.id}'s {helper.label_word}, sat nearby with a basket, pretending not to notice that the forge "
        f"sounded exactly like a duck with hiccups."
    )


def borrow_without_asking(world: World, borrower: Entity, owner: Entity, keepsake: Keepsake) -> None:
    borrower.memes["admiration"] += 1
    world.say(
        f'"Let me make it extra shiny," said {borrower.id}. Before {owner.id} could answer, '
        f"{borrower.pronoun()} whisked up the {keepsake.label} and rubbed it on {borrower.pronoun('possessive')} sleeve."
    )
    world.say(
        f'{owner.id} blinked. "You were supposed to ask first," {owner.pronoun()} said.'
    )


def cool_on_rail(world: World, borrower: Entity, keepsake: Entity) -> None:
    keepsake.meters["unsecured"] += 1
    borrower.memes["showing_off"] += 1
    world.say(
        f'"I know," said {borrower.id}, trying to sound grand. "I am the chief forge master." '
        f"To prove it, {borrower.pronoun()} set the keepsake on the stone rail to \"cool,\" even though nothing about it was hot."
    )


def gust(world: World, borrower: Entity, owner: Entity, snag: Snag) -> None:
    world.facts["gusted"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then a cliff wind came skipping around the chapel corner, grabbed the keepsake, and zipped it away until it landed {snag.landing}."
    )
    world.say(
        f'"My {world.facts["keepsake_cfg"].label}!" cried {owner.id}. "{snag.The} has it!"'
    )


def quarrel(world: World, borrower: Entity, owner: Entity) -> None:
    if world.facts["quarreled"]:
        world.say(
            f'{owner.id} stamped one foot. "You polished it right out of my hands!"'
        )
        world.say(
            f'{borrower.id} threw both hands in the air. "I did not mean to mail it to the sky!"'
        )
        world.say(
            f"For one silly, angry minute they glared at each other so hard that even the cardboard bellows went quiet."
        )


def rescue(world: World, helper: Entity, tool: Tool, snag: Snag, keepsake: Entity) -> None:
    keepsake.meters["lost"] = 0.0
    keepsake.meters["recovered"] += 1
    keepsake.meters["unsecured"] = 0.0
    world.facts["recovered"] = True
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} stood up, took {tool.label}, and {tool.text.format(snag=snag.the)}.'
    )
    world.say(
        f"The children held their breath. Then the keepsake slid free and came safely back, a little dusty but not bent."
    )


def apology_and_softening(world: World, borrower: Entity, owner: Entity, apology: Apology) -> None:
    borrower.memes["sorry"] += apology.warmth
    owner.memes["soft"] += 1
    propagate(world, narrate=False)
    world.say(
        apology.text.format(borrower=borrower.id, owner=owner.id, keepsake=world.facts["keepsake_cfg"].label)
    )
    world.say(
        f'{owner.id} looked at the keepsake, then at {borrower.id}, and let out a small laugh instead of another huff.'
    )


def reconcile(world: World, borrower: Entity, owner: Entity, keepsake: Keepsake) -> None:
    if world.facts["made_up"]:
        borrower.memes["care"] += 1
        owner.memes["care"] += 1
        world.facts["lesson"] = "ask first and hold special things tightly in windy places"
        world.say(
            f'"Next time, ask first," said {owner.id}.'
        )
        world.say(
            f'"And next time, no cooling treasures on railings," said {borrower.id}.'
        )
        world.say(
            f"Together they tied a ribbon loop onto the {keepsake.label} so it could not skid away again, and they hung it beside the pretend forge where everyone could admire it safely."
        )
        world.say(
            f"By the time the little religious walk set off below them, {borrower.id} and {owner.id} were marching in place together, grinning so hard they nearly forgot to act solemn."
        )


def tell(keepsake: Keepsake, snag: Snag, tool: Tool, apology: Apology,
         borrower_name: str = "Milo", borrower_gender: str = "boy",
         owner_name: str = "Nora", owner_gender: str = "girl",
         helper_type: str = "mother", relation: str = "friends") -> World:
    world = World()
    borrower = world.add(Entity(
        id=borrower_name,
        kind="character",
        type=borrower_gender,
        role="borrower",
        attrs={"relation": relation},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        attrs={"relation": relation},
    ))
    helper_name = {"mother": "Mom", "father": "Dad", "aunt": "Aunt June"}[helper_type]
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={"relation": relation},
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake.label,
        attrs={"owner": owner.id, "purpose": keepsake.purpose},
    ))
    snag_ent = world.add(Entity(
        id="snag",
        type="snag",
        label=snag.label,
        attrs={"place": snag.place, "delicate": snag.delicate},
    ))

    borrower.memes["friendship"] = 2.0
    owner.memes["friendship"] = 2.0
    borrower.memes["cross"] = 0.0
    owner.memes["cross"] = 0.0
    borrower.memes["sorry"] = 0.0
    owner.memes["soft"] = 0.0
    keepsake_ent.meters["unsecured"] = 0.0
    keepsake_ent.meters["lost"] = 0.0
    keepsake_ent.meters["recovered"] = 0.0
    snag_ent.meters["holding"] = 0.0

    world.facts.update(
        borrower=borrower,
        owner=owner,
        helper=helper,
        keepsake_cfg=keepsake,
        snag_cfg=snag,
        tool=tool,
        apology=apology,
        relation=relation,
    )

    introduce(world, borrower, owner, helper, keepsake)
    world.para()
    borrow_without_asking(world, borrower, owner, keepsake)
    cool_on_rail(world, borrower, keepsake_ent)
    gust(world, borrower, owner, snag)
    quarrel(world, borrower, owner)
    world.para()
    rescue(world, helper, tool, snag, keepsake_ent)
    apology_and_softening(world, borrower, owner, apology)
    reconcile(world, borrower, owner, keepsake)

    world.facts["reconciled"] = world.facts["made_up"]
    return world


KEEPSAKES = {
    "bell": Keepsake(
        id="bell",
        label="bell",
        phrase="a little brass bell on a blue ribbon",
        material="brass",
        purpose="for the chapel's small religious walk",
        weight="medium",
        tags={"bell", "religious", "ask_first"},
    ),
    "star": Keepsake(
        id="star",
        label="star",
        phrase="a tin star with a silver string",
        material="tin",
        purpose="to shine above the tiny chapel banner",
        weight="light",
        tags={"star", "religious", "ask_first"},
    ),
    "dove": Keepsake(
        id="dove",
        label="dove charm",
        phrase="a paper dove charm brushed with gold paint",
        material="paper and paint",
        purpose="for the children to carry in the religious walk",
        weight="light",
        tags={"dove", "religious", "ask_first"},
    ),
}

SNAGS = {
    "bush": Snag(
        id="bush",
        label="thorn bush",
        the="the thorn bush below the path",
        place="below the path",
        reach=1,
        delicate=False,
        landing="in the thorn bush below the path",
        weights={"light", "medium"},
        tags={"wind", "bush"},
    ),
    "banner": Snag(
        id="banner",
        label="banner line",
        the="the chapel banner line",
        place="by the chapel wall",
        reach=2,
        delicate=True,
        landing="on the chapel banner line, fluttering like it had joined the show",
        weights={"light"},
        tags={"wind", "banner", "chapel"},
    ),
    "gutter": Snag(
        id="gutter",
        label="chapel gutter",
        the="the chapel gutter",
        place="high along the chapel roof",
        reach=2,
        delicate=False,
        landing="in the chapel gutter with a metallic plink",
        weights={"light", "medium"},
        tags={"wind", "chapel", "gutter"},
    ),
}

TOOLS = {
    "shepherd_hook": Tool(
        id="shepherd_hook",
        label="the shepherd hook",
        sense=3,
        reach=2,
        gentle=True,
        text="reached up with the curved end and teased the keepsake loose from {snag}",
        qa_text="used the shepherd hook to lift the keepsake free",
        tags={"hook"},
    ),
    "ladder": Tool(
        id="ladder",
        label="the folding ladder",
        sense=3,
        reach=2,
        gentle=False,
        text="opened the ladder, climbed carefully, and lifted the keepsake down from {snag}",
        qa_text="climbed the ladder and lifted the keepsake down",
        tags={"ladder"},
    ),
    "butterfly_net": Tool(
        id="butterfly_net",
        label="the butterfly net",
        sense=2,
        reach=1,
        gentle=True,
        text="scooped under the keepsake and flicked it out of {snag}",
        qa_text="used the butterfly net to scoop the keepsake back",
        tags={"net"},
    ),
    "jump": Tool(
        id="jump",
        label="a wild jump",
        sense=1,
        reach=1,
        gentle=False,
        text="leapt and snatched at {snag}, which only would have made things worse",
        qa_text="tried to jump for it",
        tags={"unsafe"},
    ),
}

APOLOGIES = {
    "earnest": Apology(
        id="earnest",
        warmth=3,
        text='"I am really sorry, {owner}," said {borrower}. "I took the {keepsake} without asking, and then I showed off with it."',
        qa_text="gave a plain, honest apology and admitted what went wrong",
        tags={"apology"},
    ),
    "goofy_song": Apology(
        id="goofy_song",
        warmth=2,
        text='{borrower} cleared {borrower}\'s throat and sang, "I am sorry for the bell-on-the-rail, sorry for the windy sail, sorry for being a goose with a forge!"',
        qa_text="sang a goofy apology that still clearly said sorry",
        tags={"apology", "comedy"},
    ),
    "shared_joke": Apology(
        id="shared_joke",
        warmth=2,
        text='"I forgot that a chief forge master should not train treasures to fly," said {borrower}. "I am sorry, {owner}."',
        qa_text="used a shared joke, but also clearly apologized",
        tags={"apology", "comedy"},
    ),
    "shrug": Apology(
        id="shrug",
        warmth=1,
        text='{borrower} shrugged and said, "Well, the wind was excited."',
        qa_text="gave only a shrug instead of a real apology",
        tags={"apology"},
    ),
}

GIRL_NAMES = ["Nora", "Maya", "Ella", "Lucy", "Zoe", "Ava", "Lina", "Ivy"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Noah", "Eli", "Sam", "Leo"]
RELATIONS = ["friends", "siblings"]


@dataclass
class StoryParams:
    keepsake: str
    snag: str
    tool: str
    apology: str
    borrower: str
    borrower_gender: str
    owner: str
    owner_gender: str
    helper: str
    relation: str = "friends"
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
    "forge": [(
        "What is a forge?",
        "A forge is a hot place where metal can be heated and shaped. In this story the children only made a pretend forge, so it was a game, not a real fire."
    )],
    "religious": [(
        "What does religious mean?",
        "Religious means connected to faith, prayer, or holy traditions. A religious walk or procession is a calm event where people gather for that tradition."
    )],
    "wind": [(
        "Why is a cliff lookout windy?",
        "A cliff lookout is high and open, so the wind can rush across it with nothing big to stop it. Light things can slip or fly away there."
    )],
    "chapel": [(
        "What is a chapel?",
        "A chapel is a small place for prayer or quiet worship. People may visit it for peace, singing, or a special ceremony."
    )],
    "hook": [(
        "What is a shepherd hook?",
        "A shepherd hook is a long stick with a curved end. It can help pull something down gently from a high place."
    )],
    "ladder": [(
        "Why do grown-ups use ladders carefully?",
        "Ladders help people reach high places, but they must be used slowly and carefully so no one falls. That is why a calm grown-up should handle them."
    )],
    "net": [(
        "What is a butterfly net for?",
        "A butterfly net is a light net on a long handle. It can scoop up small things without squeezing them too hard."
    )],
    "ask_first": [(
        "Why should you ask before borrowing something special?",
        "You should ask first because the thing belongs to someone else and may be important to them. Asking shows respect and helps people trust you."
    )],
    "apology": [(
        "What makes an apology feel real?",
        "A real apology says what went wrong and shows you care about the other person's feelings. It helps people start to forgive and make up."
    )],
}
KNOWLEDGE_ORDER = ["forge", "religious", "wind", "chapel", "hook", "ladder", "net", "ask_first", "apology"]


CURATED = [
    StoryParams(
        keepsake="bell",
        snag="gutter",
        tool="ladder",
        apology="earnest",
        borrower="Milo",
        borrower_gender="boy",
        owner="Nora",
        owner_gender="girl",
        helper="mother",
        relation="friends",
    ),
    StoryParams(
        keepsake="star",
        snag="banner",
        tool="shepherd_hook",
        apology="goofy_song",
        borrower="Ella",
        borrower_gender="girl",
        owner="Ben",
        owner_gender="boy",
        helper="aunt",
        relation="siblings",
    ),
    StoryParams(
        keepsake="dove",
        snag="bush",
        tool="butterfly_net",
        apology="shared_joke",
        borrower="Theo",
        borrower_gender="boy",
        owner="Lucy",
        owner_gender="girl",
        helper="father",
        relation="friends",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    borrower = f["borrower"]
    owner = f["owner"]
    keepsake = f["keepsake_cfg"]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "forge" and "religious," and takes place at a cliff lookout.',
        f"Tell a comedy story where {borrower.id} and {owner.id} build a pretend forge near a chapel, lose {keepsake.phrase} in the wind, and then reconcile.",
        "Write a gentle story with a quarrel, a rescue, an apology, and a lesson about asking before borrowing something special.",
    ]


def pair_noun(world: World) -> str:
    relation = world.facts["relation"]
    borrower = world.facts["borrower"]
    owner = world.facts["owner"]
    if relation == "siblings":
        if borrower.type == "boy" and owner.type == "boy":
            return "two brothers"
        if borrower.type == "girl" and owner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    borrower = f["borrower"]
    owner = f["owner"]
    helper = f["helper"]
    keepsake = f["keepsake_cfg"]
    snag = f["snag_cfg"]
    tool = f["tool"]
    apology = f["apology"]
    pair = pair_noun(world)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {borrower.id} and {owner.id}, at a cliff lookout beside a tiny chapel. {helper.id} is nearby and helps when the trouble starts."
        ),
        (
            "What were the children pretending?",
            "They made a silly pretend forge out of simple things and imagined they were making shiny treasures. The game matched the special day near the chapel."
        ),
        (
            f"Why was the {keepsake.label} important?",
            f"It was important because it was meant {keepsake.purpose}. That made losing it feel bigger than an ordinary toy accident."
        ),
        (
            f"Why did {owner.id} get upset with {borrower.id}?",
            f"{owner.id} got upset because {borrower.id} picked up the {keepsake.label} without asking and then set it on the rail to show off. At a windy cliff lookout, that careless choice is what let the gust sweep it away."
        ),
        (
            f"Where did the keepsake go, and how did {helper.id} get it back?",
            f"It flew to {snag.the}. {helper.id} {tool.qa_text}, which worked because that tool could safely reach the place where it got stuck."
        ),
        (
            f"How did the children make up?",
            f"{borrower.id} {apology.qa_text}. Then {owner.id} softened, laughed a little, and the two of them fixed the problem together instead of staying angry."
        ),
        (
            "What lesson did they learn?",
            f"They learned to ask before borrowing something special and to hold treasured things tightly in a windy place. The ribbon loop they added at the end shows they changed their plan, not just their words."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"forge"}
    keepsake = world.facts["keepsake_cfg"]
    snag = world.facts["snag_cfg"]
    tool = world.facts["tool"]
    apology = world.facts["apology"]
    tags |= keepsake.tags
    tags |= snag.tags
    tags |= tool.tags
    tags |= apology.tags
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
drift(K, S) :- keepsake(K), snag(S), weight(K, W), snag_allows(S, W).

rescues(T, S) :- tool(T), snag(S), reach(T, R), need_reach(S, N), R >= N, not delicate(S).
rescues(T, S) :- tool(T), delicate(S), gentle(T), reach(T, R), need_reach(S, N), R >= N.

sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
reconciling(A) :- apology(A), warmth(A, W), warm_min(M), W >= M.

valid(K, S, T, A) :- keepsake(K), snag(S), tool(T), apology(A),
                     drift(K, S), sensible(T), rescues(T, S), reconciling(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("weight", keepsake_id, keepsake.weight))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("need_reach", snag_id, snag.reach))
        if snag.delicate:
            lines.append(asp.fact("delicate", snag_id))
        for weight in sorted(snag.weights):
            lines.append(asp.fact("snag_allows", snag_id, weight))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
    for apology_id, apology in APOLOGIES.items():
        lines.append(asp.fact("apology", apology_id))
        lines.append(asp.fact("warmth", apology_id, apology.warmth))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("warm_min", WARMTH_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [
        CURATED[0],
        StoryParams(
            keepsake="star",
            snag="banner",
            tool="shepherd_hook",
            apology="shared_joke",
            borrower="Ivy",
            borrower_gender="girl",
            owner="Leo",
            owner_gender="boy",
            helper="aunt",
            relation="friends",
        ),
    ]
    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise StoryError("missing prompts or QA")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED for {params}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a windy cliff lookout, a pretend forge, a lost keepsake, and reconciliation."
    )
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--helper", choices=["mother", "father", "aunt"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keepsake and args.snag:
        keepsake = KEEPSAKES[args.keepsake]
        snag = SNAGS[args.snag]
        if not drift_possible(keepsake, snag):
            raise StoryError(explain_bad_snag(keepsake, snag))
    if args.tool and args.snag:
        tool = TOOLS[args.tool]
        snag = SNAGS[args.snag]
        if not rescue_possible(tool, snag) or tool.sense < SENSE_MIN:
            raise StoryError(explain_bad_tool(tool, snag))
    if args.apology:
        apology = APOLOGIES[args.apology]
        if apology.warmth < WARMTH_MIN:
            raise StoryError(explain_bad_apology(apology))
    if args.tool and args.snag is None and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_bad_tool(TOOLS[args.tool], SNAGS["bush"]))

    combos = [
        combo for combo in valid_combos()
        if (args.keepsake is None or combo[0] == args.keepsake)
        and (args.snag is None or combo[1] == args.snag)
        and (args.tool is None or combo[2] == args.tool)
        and (args.apology is None or combo[3] == args.apology)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    keepsake_id, snag_id, tool_id, apology_id = rng.choice(sorted(combos))
    borrower_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    borrower = _pick_name(rng, borrower_gender)
    owner = _pick_name(rng, owner_gender, avoid=borrower)
    helper = args.helper or rng.choice(["mother", "father", "aunt"])
    relation = args.relation or rng.choice(RELATIONS)
    return StoryParams(
        keepsake=keepsake_id,
        snag=snag_id,
        tool=tool_id,
        apology=apology_id,
        borrower=borrower,
        borrower_gender=borrower_gender,
        owner=owner,
        owner_gender=owner_gender,
        helper=helper,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(Unknown apology: {params.apology})")
    if params.helper not in {"mother", "father", "aunt"}:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.relation not in set(RELATIONS):
        raise StoryError(f"(Unknown relation: {params.relation})")

    keepsake = KEEPSAKES[params.keepsake]
    snag = SNAGS[params.snag]
    tool = TOOLS[params.tool]
    apology = APOLOGIES[params.apology]

    if not drift_possible(keepsake, snag):
        raise StoryError(explain_bad_snag(keepsake, snag))
    if tool.sense < SENSE_MIN or not rescue_possible(tool, snag):
        raise StoryError(explain_bad_tool(tool, snag))
    if apology.warmth < WARMTH_MIN:
        raise StoryError(explain_bad_apology(apology))

    world = tell(
        keepsake=keepsake,
        snag=snag,
        tool=tool,
        apology=apology,
        borrower_name=params.borrower,
        borrower_gender=params.borrower_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        helper_type=params.helper,
        relation=params.relation,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (keepsake, snag, tool, apology) combos:\n")
        for keepsake, snag, tool, apology in combos:
            print(f"  {keepsake:8} {snag:7} {tool:14} {apology}")
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
            header = f"### {p.borrower} & {p.owner}: {p.keepsake} -> {p.snag} ({p.tool}, {p.apology})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
