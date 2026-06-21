#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py
===============================================================================

A standalone storyworld for a tiny adventure tale built around one light paper
folder, a worried child, a suspenseful place, and a kind rescue.

Premise
-------
Two children are on a small pretend adventure when a breeze snatches a folder
full of clue pages. The folder skitters into a tricky place that sounds a bit
scary: reeds that swish, a footbridge that creaks, or stones where water plinks.
A kind child chooses whether to help carefully or rashly. The world model
decides whether the folder is safely recovered or lost to water and wind.

The story shape is always:
- beginning: adventure game + special folder
- tension: the folder blows into a suspenseful spot
- turn: a helper decides how to recover it
- ending: either a kind safe success, or a sad but gentle lesson about slowing
  down and asking for help

Run it
------
python storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py
python storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py --all
python storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py --trace
python storyworlds/worlds/gpt-5.4/folder_kindness_suspense_sound_effects_adventure.py --verify
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
    owner: str = ""
    fragile: bool = False
    movable: bool = False
    # unified simulation axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    trail: str
    opener: str
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
class Hazard:
    id: str
    label: str
    place_text: str
    sound: str
    suspense: str
    danger: int
    wet_risk: bool
    reach_need: int
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
class FolderKind:
    id: str
    label: str
    contents: str
    dream: str
    color: str
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
    calm: bool
    teamwork: bool
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_drop_scare(world: World) -> list[str]:
    folder = world.get("folder")
    if folder.meters["drifting"] < THRESHOLD:
        return []
    sig = ("drop_scare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("owner").memes["fear"] += 1
    world.get("helper").memes["care"] += 1
    if "hazard" in world.entities:
        world.get("hazard").memes["ominous"] += 1
    return ["__folder_lost__"]


def _r_wet_loss(world: World) -> list[str]:
    folder = world.get("folder")
    hazard = world.get("hazard")
    if folder.meters["unrecovered"] < THRESHOLD or hazard.meters["wet_zone"] < THRESHOLD:
        return []
    sig = ("wet_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    folder.meters["wet"] += 1
    folder.meters["ruined"] += 1
    world.get("owner").memes["sadness"] += 1
    world.get("helper").memes["regret"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="drop_scare", tag="emotional", apply=_r_drop_scare),
    Rule(name="wet_loss", tag="physical", apply=_r_wet_loss),
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


def folder_at_risk(hazard: Hazard) -> bool:
    return hazard.reach_need > 0


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def challenge_level(hazard: Hazard, gusts: int) -> int:
    return hazard.reach_need + gusts


def can_recover(method: Method, hazard: Hazard, gusts: int) -> bool:
    return method.power >= challenge_level(hazard, gusts)


def explain_rejection(hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.label} is not a real obstacle here, so the folder would "
        f"not be hard to recover. Pick a place with a genuine little adventure.)"
    )


def explain_method(mid: str) -> str:
    method = METHODS[mid]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{mid}': it is too rash for this world "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_loss(world: World, method_id: str) -> dict:
    sim = world.copy()
    method = METHODS[method_id]
    hazard_cfg = HAZARDS[sim.facts["hazard_cfg"].id]
    _attempt_recovery(sim, method, hazard_cfg, narrate=False)
    folder = sim.get("folder")
    return {
        "saved": folder.meters["saved"] >= THRESHOLD,
        "wet": folder.meters["wet"] >= THRESHOLD,
    }


def _blow_folder(world: World, hazard: Hazard, narrate: bool = True) -> None:
    folder = world.get("folder")
    folder.meters["drifting"] += 1
    folder.attrs["where"] = hazard.label
    if hazard.wet_risk:
        world.get("hazard").meters["wet_zone"] = 1
    propagate(world, narrate=narrate)


def _attempt_recovery(world: World, method: Method, hazard: Hazard, narrate: bool = True) -> None:
    folder = world.get("folder")
    gusts = int(world.facts["gusts"])
    if can_recover(method, hazard, gusts):
        folder.meters["saved"] += 1
        folder.meters["drifting"] = 0
        world.get("owner").memes["relief"] += 1
        world.get("helper").memes["pride"] += 1
        world.get("helper").memes["kindness"] += 1
        if method.teamwork:
            world.get("owner").memes["trust"] += 1
    else:
        folder.meters["unrecovered"] += 1
        world.get("owner").memes["fear"] += 1
        world.get("helper").memes["worry"] += 1
        propagate(world, narrate=narrate)


def opening(world: World, helper: Entity, owner: Entity, setting: Setting, folder_cfg: FolderKind) -> None:
    for child in (helper, owner):
        child.memes["joy"] += 1
    world.say(
        f"{setting.opener} {helper.id} and {owner.id} marched along {setting.trail} as if it were the road to a hidden kingdom."
    )
    world.say(
        f"{owner.id} carried a {folder_cfg.color} folder stuffed with {folder_cfg.contents}. Inside was the plan for {folder_cfg.dream}."
    )


def promise_kindness(world: World, helper: Entity, owner: Entity) -> None:
    world.say(
        f'"I will help guard it," {helper.id} promised. {owner.id} smiled and held the folder a little tighter.'
    )
    helper.memes["care"] += 1
    owner.memes["trust"] += 1


def sound_and_breeze(world: World, hazard: Hazard) -> None:
    world.say(
        f"Then the path grew hush-hush. {hazard.sound} came from {hazard.place_text}, and even the children slowed down to listen."
    )
    world.say(hazard.suspense)


def gust_event(world: World, owner: Entity, hazard: Hazard, folder_cfg: FolderKind) -> None:
    _blow_folder(world, hazard, narrate=False)
    world.say(
        f"Whoooosh! A quick wind snatched the {folder_cfg.color} folder from {owner.id}'s hands and sent it skittering toward {hazard.place_text}."
    )
    if hazard.wet_risk:
        world.say("Plink, plink went the water nearby, and the folder teetered far too close to the splash.")
    else:
        world.say("Swish-swish went the leaves around it, and for one second the folder seemed to disappear.")
    propagate(world, narrate=False)


def owner_worry(world: World, owner: Entity, folder_cfg: FolderKind) -> None:
    world.say(
        f'"Oh no," {owner.id} whispered. "Our {folder_cfg.contents} are in there."'
    )


def helper_decides(world: World, helper: Entity, owner: Entity, method: Method, hazard: Hazard) -> None:
    pred = predict_loss(world, method.id)
    world.facts["predicted_saved"] = pred["saved"]
    world.facts["predicted_wet"] = pred["wet"]
    if pred["saved"]:
        extra = "carefully" if method.calm else "quickly"
        world.say(
            f'{helper.id} took one small breath. "I can help," {helper.pronoun()} said {extra}.'
        )
    else:
        world.say(
            f'{helper.id} stared at the folder, then at {hazard.place_text}. The place sounded spooky, but leaving the folder there felt even worse.'
        )
    if method.teamwork:
        world.say(f'"Hold my sleeve and stay back from the edge," {helper.id} told {owner.id}.')
    else:
        world.say(f'"Stay here. I will try," {helper.id} said.')


def recover_success(world: World, helper: Entity, owner: Entity, method: Method, hazard: Hazard, folder_cfg: FolderKind) -> None:
    _attempt_recovery(world, method, hazard, narrate=False)
    world.say(method.text.format(hazard=hazard.place_text, owner=owner.id))
    world.say(
        f'Snick! The folder was free. {helper.id} lifted it high, and {owner.id} let out a long happy breath.'
    )
    world.say(
        f'The {folder_cfg.contents} were safe, only a little crinkled at the corners, and the adventure could go on.'
    )


def recover_fail(world: World, helper: Entity, owner: Entity, method: Method, hazard: Hazard, folder_cfg: FolderKind) -> None:
    _attempt_recovery(world, method, hazard, narrate=False)
    world.say(method.fail.format(hazard=hazard.place_text, owner=owner.id))
    if hazard.wet_risk:
        world.say(
            f"Plop! The folder slipped into the wet stones and came back with blurred pages. The clues for {folder_cfg.dream} were gone."
        )
    else:
        world.say(
            f"Skitter-scrape! The folder slid farther in and tore along one edge. The children could not reach the clue pages safely."
        )


def comfort(world: World, helper: Entity, owner: Entity, folder_cfg: FolderKind) -> None:
    owner.memes["sadness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{owner.id}'s eyes filled with tears, but {helper.id} did not laugh or scold."
    )
    world.say(
        f'"We can still make a new plan," {helper.id} said softly. "I remember the first clue, and I will help you draw it again in another folder."'
    )
    world.say(
        f"That kindness did not fix the wet pages, but it made the scary moment feel smaller."
    )


def celebration(world: World, helper: Entity, owner: Entity, folder_cfg: FolderKind) -> None:
    helper.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f'{owner.id} hugged the folder to {owner.pronoun("possessive")} chest. "Thank you for helping me," {owner.pronoun()} said.'
    )
    world.say(
        f'{helper.id} grinned. "An explorer never leaves a friend behind."'
    )
    world.say(
        f"Together they tucked the {folder_cfg.color} folder into a safer pocket of the adventure bag and walked on, ready for the next clue."
    )


def gentler_ending(world: World, helper: Entity, owner: Entity, setting: Setting) -> None:
    world.say(
        f"A little later they sat on a bench at {setting.place} and made fresh clue pages together."
    )
    world.say(
        f"The new folder was held between them this time, and the adventure became slower, kinder, and wiser."
    )


def tell(
    setting: Setting,
    hazard: Hazard,
    folder_cfg: FolderKind,
    method: Method,
    helper_name: str = "Maya",
    helper_gender: str = "girl",
    owner_name: str = "Leo",
    owner_gender: str = "boy",
    parent_type: str = "mother",
    gusts: int = 1,
    bravery: int = 5,
) -> World:
    world = World()
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["steady"],
            attrs={},
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            traits=["hopeful"],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    folder = world.add(
        Entity(
            id="folder",
            kind="thing",
            type="folder",
            label="folder",
            owner=owner.id,
            fragile=True,
            movable=True,
            attrs={"where": "owner_hands"},
        )
    )
    hazard_ent = world.add(
        Entity(
            id="hazard",
            kind="thing",
            type="hazard",
            label=hazard.label,
            attrs={},
        )
    )

    helper.memes["bravery"] = float(bravery)
    helper.memes["care"] = 1.0
    owner.memes["trust"] = 1.0
    hazard_ent.meters["wet_zone"] = 1.0 if hazard.wet_risk else 0.0
    world.facts["gusts"] = gusts
    world.facts["hazard_cfg"] = hazard
    world.facts["setting"] = setting
    world.facts["folder_cfg"] = folder_cfg
    world.facts["method"] = method

    opening(world, helper, owner, setting, folder_cfg)
    promise_kindness(world, helper, owner)

    world.para()
    sound_and_breeze(world, hazard)
    gust_event(world, owner, hazard, folder_cfg)
    owner_worry(world, owner, folder_cfg)

    world.para()
    helper_decides(world, helper, owner, method, hazard)
    success = can_recover(method, hazard, gusts)
    if success:
        recover_success(world, helper, owner, method, hazard, folder_cfg)
        world.para()
        celebration(world, helper, owner, folder_cfg)
        outcome = "saved"
    else:
        recover_fail(world, helper, owner, method, hazard, folder_cfg)
        world.para()
        comfort(world, helper, owner, folder_cfg)
        gentler_ending(world, helper, owner, setting)
        outcome = "lost"

    world.facts.update(
        helper=helper,
        owner=owner,
        parent=parent,
        folder=folder,
        hazard=hazard_ent,
        outcome=outcome,
        saved=folder.meters["saved"] >= THRESHOLD,
        wet=folder.meters["wet"] >= THRESHOLD,
        gust_level=gusts,
        challenge=challenge_level(hazard, gusts),
    )
    return world


SETTINGS = {
    "park": Setting(
        id="park",
        place="the park",
        trail="the pebble path by the duck pond",
        opener="On a bright afternoon",
        tags={"park", "outdoors"},
    ),
    "garden": Setting(
        id="garden",
        place="the botanic garden",
        trail="the fern path under tall glassy leaves",
        opener="One soft green morning",
        tags={"garden", "outdoors"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the old museum courtyard",
        trail="the stone walk between lion statues",
        opener="One golden afternoon",
        tags={"courtyard", "outdoors"},
    ),
}

HAZARDS = {
    "reeds": Hazard(
        id="reeds",
        label="the reeds",
        place_text="the swishy reeds beside the pond",
        sound="Swish-swish... rustle-rustle...",
        suspense="The tall reeds nodded together like whispering guards.",
        danger=1,
        wet_risk=True,
        reach_need=2,
        tags={"reeds", "water", "sound"},
    ),
    "bridge": Hazard(
        id="bridge",
        label="the footbridge",
        place_text="the little wooden footbridge",
        sound="Creak... creak...",
        suspense="Each board looked safe enough, but the noises made the bridge feel much older and farther away.",
        danger=2,
        wet_risk=True,
        reach_need=3,
        tags={"bridge", "water", "sound"},
    ),
    "stones": Hazard(
        id="stones",
        label="the echo stones",
        place_text="the ring of echo stones near the fountain",
        sound="Tap-tap... plink...",
        suspense="The stone circle sent every tiny sound back again, so the place felt secret and mysterious.",
        danger=1,
        wet_risk=False,
        reach_need=2,
        tags={"stones", "sound"},
    ),
}

FOLDERS = {
    "map": FolderKind(
        id="map",
        label="map folder",
        contents="map pages and star stickers",
        dream="finding the hidden gate",
        color="red",
        tags={"map", "folder"},
    ),
    "badge": FolderKind(
        id="badge",
        label="badge folder",
        contents="badge sheets and a crayon compass",
        dream="earning the brave helper badge",
        color="blue",
        tags={"badge", "folder"},
    ),
    "letter": FolderKind(
        id="letter",
        label="letter folder",
        contents="riddle letters and a silver pencil rubbing",
        dream="solving the garden mystery",
        color="yellow",
        tags={"letter", "folder"},
    ),
}

METHODS = {
    "branch_hook": Method(
        id="branch_hook",
        label="branch hook",
        sense=3,
        power=3,
        calm=True,
        teamwork=False,
        text="Slowly, {helper} lay on the safest dry stones, reached out with a fallen branch, and hooked the folder back from {hazard}.",
        fail="{helper} stretched a fallen branch toward {hazard}, but the folder bobbled away before the tip could catch it.",
        qa_text="used a fallen branch to hook the folder back",
        tags={"branch", "careful"},
    ),
    "team_chain": Method(
        id="team_chain",
        label="team chain",
        sense=3,
        power=4,
        calm=True,
        teamwork=True,
        text="{helper} braced {helper_pronoun_possessive} feet, and {owner} held tight to {helper_pronoun_possessive} sleeve while {helper_pronoun_subject} reached with a long litter-picker from the path and pinched the folder free from {hazard}.",
        fail="{helper} and {owner} tried to make a careful chain at {hazard}, but a gust tugged the folder out of reach first.",
        qa_text="worked together and used a long picker to pinch the folder free",
        tags={"teamwork", "careful"},
    ),
    "quick_grab": Method(
        id="quick_grab",
        label="quick grab",
        sense=1,
        power=1,
        calm=False,
        teamwork=False,
        text="{helper} darted forward and snatched the folder back before it could slip away.",
        fail="{helper} lunged in a hurry at {hazard}, but the folder skidded away from those rushing hands.",
        qa_text="lunged to grab the folder quickly",
        tags={"rash"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Nora", "Ella", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben", "Sam", "Noah", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_methods():
        return combos
    for setting_id in SETTINGS:
        for hazard_id, hazard in HAZARDS.items():
            if not folder_at_risk(hazard):
                continue
            for folder_id in FOLDERS:
                combos.append((setting_id, hazard_id, folder_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    hazard: str
    folder: str
    method: str
    helper_name: str
    helper_gender: str
    owner_name: str
    owner_gender: str
    parent: str
    gusts: int = 1
    bravery: int = 5
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
    "folder": [
        (
            "What is a folder?",
            "A folder is a cover for papers that keeps them together in one place. It helps maps, drawings, and notes stay neat."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where places are and how to get from one place to another. Explorers use maps to find the way."
        )
    ],
    "bridge": [
        (
            "Why does a wooden bridge creak?",
            "Wood bends a tiny bit when someone steps on it, and that can make creaky sounds. The sound can seem spooky even when the bridge is still safe."
        )
    ],
    "water": [
        (
            "Why can paper get ruined by water?",
            "Paper soaks up water very quickly. When it gets wet, the pages can wrinkle, tear, or make the writing blurry."
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall grassy plants that grow near water. Wind makes them swish and rub together."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and do different parts of a job together. Working as a team can make a hard job safer."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means helping someone, speaking gently, or noticing when they feel worried. A kind person tries to make things better, not worse."
        )
    ],
    "careful": [
        (
            "Why is it good to move carefully near water?",
            "Careful steps help you keep your balance and notice slippery places. Going slowly is often the safest way to help."
        )
    ],
}
KNOWLEDGE_ORDER = ["folder", "map", "bridge", "reeds", "water", "teamwork", "kindness", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    owner = f["owner"]
    hazard_cfg = HAZARDS[f["hazard"].label if f["hazard"].label in HAZARDS else f["hazard_cfg"].id] if False else f["hazard_cfg"]
    folder_cfg = f["folder_cfg"]
    if f["outcome"] == "saved":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the word "folder", suspenseful sounds, and a kind rescue.',
            f"Tell a gentle adventure where {owner.id}'s {folder_cfg.color} folder blows toward {hazard_cfg.place_text}, and {helper.id} helps recover it carefully.",
            f"Write a story with sound effects like {hazard_cfg.sound} where one child helps a friend save an important folder and the ending proves their kindness.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "folder", suspenseful sounds, and kindness after a mistake.',
        f"Tell a gentle adventure where {owner.id}'s {folder_cfg.color} folder blows toward {hazard_cfg.place_text}, and the children cannot save it but still help each other.",
        f"Write a story with sound effects like {hazard_cfg.sound} where a scary moment becomes softer because one child is kind to a worried friend.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    owner = f["owner"]
    folder_cfg = f["folder_cfg"]
    hazard_cfg = f["hazard_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id} and {owner.id}, two children on a small adventure together. {owner.id} carried a {folder_cfg.color} folder full of {folder_cfg.contents}."
        ),
        (
            "Why was the folder important?",
            f"The folder held the papers they needed for {folder_cfg.dream}. Losing it would mean losing the clues for their adventure."
        ),
        (
            "What made the moment feel suspenseful?",
            f"The place sounded mysterious because of {hazard_cfg.sound} near {hazard_cfg.place_text}. Then the wind suddenly grabbed the folder, which made the children worry right away."
        ),
    ]
    if f["outcome"] == "saved":
        answer = (
            f"{helper.id} {method.qa_text}. {owner.id} trusted {helper.pronoun('object')} and stayed back so the rescue could be careful."
        )
        if method.teamwork:
            answer += " They worked together instead of rushing, which made the hard part safer."
        qa.append(
            (
                f"How did {helper.id} save the folder?",
                answer,
            )
        )
        qa.append(
            (
                "How did kindness matter in the story?",
                f"{helper.id} noticed that {owner.id} was frightened and chose to help instead of teasing or walking away. At the end, the children kept the folder safe together, which shows that kindness changed what happened."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the folder safe again and tucked into the adventure bag. The children walked on together, ready for the next clue."
            )
        )
    else:
        qa.append(
            (
                "Did they save the folder?",
                f"No. The rescue was too weak for that windy, tricky place, so the folder was lost or ruined before they could safely reach it."
            )
        )
        qa.append(
            (
                "How did kindness matter even after the problem?",
                f"{helper.id} stayed close to {owner.id} and spoke gently instead of blaming {owner.pronoun('object')}. {helper.pronoun().capitalize()} helped make new clue pages in another folder, so the adventure could continue in a different way."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended on a bench with the children making a new plan together. They had lost the first folder, but they had become slower, kinder explorers."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"folder", "kindness"}
    tags |= set(f["folder_cfg"].tags)
    tags |= set(f["hazard_cfg"].tags)
    tags |= set(f["method"].tags)
    if f["hazard_cfg"].wet_risk:
        tags.add("water")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(r[0] for r in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="park",
        hazard="reeds",
        folder="map",
        method="branch_hook",
        helper_name="Maya",
        helper_gender="girl",
        owner_name="Leo",
        owner_gender="boy",
        parent="mother",
        gusts=1,
        bravery=5,
    ),
    StoryParams(
        setting="garden",
        hazard="bridge",
        folder="letter",
        method="team_chain",
        helper_name="Finn",
        helper_gender="boy",
        owner_name="Ruby",
        owner_gender="girl",
        parent="father",
        gusts=1,
        bravery=6,
    ),
    StoryParams(
        setting="courtyard",
        hazard="stones",
        folder="badge",
        method="branch_hook",
        helper_name="Zoe",
        helper_gender="girl",
        owner_name="Max",
        owner_gender="boy",
        parent="mother",
        gusts=2,
        bravery=5,
    ),
    StoryParams(
        setting="park",
        hazard="bridge",
        folder="map",
        method="branch_hook",
        helper_name="Noah",
        helper_gender="boy",
        owner_name="Ella",
        owner_gender="girl",
        parent="father",
        gusts=2,
        bravery=5,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "saved" if can_recover(METHODS[params.method], HAZARDS[params.hazard], params.gusts) else "lost"


ASP_RULES = r"""
folder_at_risk(H) :- hazard(H), reach_need(H, N), N > 0.
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(S, H, F) :- setting(S), hazard(H), folder(F), folder_at_risk(H).

challenge(H, G, C) :- reach_need(H, R), gusts(G), C = R + G.
saved :- chosen_hazard(H), chosen_method(M), challenge(H, G, C), gusts(G), power(M, P), P >= C.
outcome(saved) :- saved.
outcome(lost) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("reach_need", hid, hazard.reach_need))
        if hazard.wet_risk:
            lines.append(asp.fact("wet_risk", hid))
    for fid in FOLDERS:
        lines.append(asp.fact("folder", fid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_method", params.method),
            asp.fact("gusts", params.gusts),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {m.id for m in sensible_methods()}
    clingo_sensible = set(asp_sensible_methods())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible methods match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(python_sensible))
        print("  clingo:", sorted(clingo_sensible))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generate/emit succeeded.")
    except Exception as exc:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folder, a suspenseful sound, and a kind adventure rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--folder", choices=FOLDERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gusts", type=int, choices=[1, 2], help="how hard the wind pulls")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and not folder_at_risk(HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(HAZARDS[args.hazard]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.folder is None or combo[2] == args.folder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, folder_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    helper_name, helper_gender = _pick_child(rng)
    owner_name, owner_gender = _pick_child(rng, avoid=helper_name)
    parent = args.parent or rng.choice(["mother", "father"])
    gusts = args.gusts if args.gusts is not None else rng.choice([1, 2])
    bravery = rng.randint(4, 6)

    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        folder=folder_id,
        method=method_id,
        helper_name=helper_name,
        helper_gender=helper_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        parent=parent,
        gusts=gusts,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.folder not in FOLDERS:
        raise StoryError(f"(Unknown folder: {params.folder})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        folder_cfg=FOLDERS[params.folder],
        method=METHODS[params.method],
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        parent_type=params.parent,
        gusts=params.gusts,
        bravery=params.bravery,
    )

    # render templates that depend on pronouns now that we have actors
    method = METHODS[params.method]
    helper = world.facts["helper"]
    owner = world.facts["owner"]
    world.facts["method"] = Method(
        id=method.id,
        label=method.label,
        sense=method.sense,
        power=method.power,
        calm=method.calm,
        teamwork=method.teamwork,
        text=method.text.format(
            helper=helper.id,
            owner=owner.id,
            helper_pronoun_possessive=helper.pronoun("possessive"),
            helper_pronoun_subject=helper.pronoun("subject"),
            hazard="{hazard}",
        ),
        fail=method.fail.format(
            helper=helper.id,
            owner=owner.id,
            hazard="{hazard}",
        ),
        qa_text=method.qa_text,
        tags=set(method.tags),
    )

    # rebuild story with the rendered method text to keep prose natural
    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        folder_cfg=FOLDERS[params.folder],
        method=world.facts["method"],
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        parent_type=params.parent,
        gusts=params.gusts,
        bravery=params.bravery,
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
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hazard, folder) combos:\n")
        for setting_id, hazard_id, folder_id in combos:
            print(f"  {setting_id:10} {hazard_id:8} {folder_id}")
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
            header = f"### {p.helper_name} helps {p.owner_name}: {p.folder} at {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
