#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py
============================================================================

A standalone bedtime-story world about a child whose beloved little bedtime
companion needs a gentle **transformation** before sleep can feel safe again.

The source-tale idea rebuilt here:
    A child gets ready for bed with a treasured helper toy or tiny room friend.
    Tonight the helper is too weak to do its bedtime job: a glow has faded, a
    song is missing, or a soft comfort motion has stopped. The child worries.
    A calm grown-up brings the helper to a little bedside workbench, asks the
    child to take a sip of a warm bedtime drink, and makes a small shining
    bionic repair. The helper transforms, gives a soft "chim", and bedtime ends
    in peace.

This world models that premise as state:
- typed entities with physical meters and emotional memes
- a compatibility gate: the chosen repair must truly solve the helper's problem
- a transformation turn rendered from world state, not from slot-filled prose
- three QA sets generated from the simulated world
- an inline ASP twin for parity checking

Run it
------
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py --helper moth --trouble dim_glow
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py --upgrade bionic_hopper
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sip_chim_bionic_transformation_bedtime_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    # physical
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional / social
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    bedtime_job: str
    opening: str
    ending_pose: str
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
class Trouble:
    id: str
    need: str                 # glow | song | cuddle
    symptom: str
    warning: str
    risk: str
    bedtime_loss: str
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
class Upgrade:
    id: str
    need: str                 # what problem it truly solves
    label: str
    phrase: str
    install: str
    after: str
    power_word: str
    sound: str = "chim"
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
class Drink:
    id: str
    phrase: str
    sip_line: str
    warmth: str
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
class StoryParams:
    helper: str
    trouble: str
    upgrade: str
    drink: str
    child_name: str
    child_gender: str
    parent_type: str
    child_trait: str
    blanket_color: str
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


def _r_bedtime_worry(world: World) -> list[str]:
    helper = world.get("helper")
    child = world.get("child")
    room = world.get("room")
    if helper.meters["working"] >= THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    room.meters["unsettled"] += 1
    return []


def _r_sip_soothes(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["sipped"] < THRESHOLD:
        return []
    sig = ("soothe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return []


def _r_upgrade_restores(world: World) -> list[str]:
    helper = world.get("helper")
    if helper.meters["patched"] < THRESHOLD:
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.meters["working"] = 1.0
    helper.meters["transformed"] += 1
    room.meters["unsettled"] = 0.0
    child = world.get("child")
    child.memes["awe"] += 1
    child.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bedtime_worry", tag="emotion", apply=_r_bedtime_worry),
    Rule(name="sip_soothes", tag="emotion", apply=_r_sip_soothes),
    Rule(name="upgrade_restores", tag="physical", apply=_r_upgrade_restores),
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
        for s in produced:
            world.say(s)
    return produced


HELPERS = {
    "moth": HelperKind(
        id="moth",
        label="moth",
        phrase="a little velvet moth",
        bedtime_job="glow by the pillow",
        opening="liked to rest on the bedpost like a tiny moon lamp",
        ending_pose="circled once above the pillow and folded its bright wings",
        tags={"moth", "glow"},
    ),
    "owl": HelperKind(
        id="owl",
        label="owl",
        phrase="a pocket owl with button eyes",
        bedtime_job="sing a sleepy tune",
        opening="usually blinked from the nightstand and hummed near the lamp",
        ending_pose="tucked its round head beneath one wing on the nightstand",
        tags={"owl", "song"},
    ),
    "bunny": HelperKind(
        id="bunny",
        label="bunny",
        phrase="a soft clockwork bunny",
        bedtime_job="nuzzle close under the blanket",
        opening="usually made one brave little hop before curling beside the pillow",
        ending_pose="nestled against the blanket edge with its paws tucked in",
        tags={"bunny", "cuddle"},
    ),
}

TROUBLES = {
    "dim_glow": Trouble(
        id="dim_glow",
        need="glow",
        symptom="its bedtime glow had gone pale and patchy",
        warning="without that soft light, the room corners looked farther away",
        risk="the child would feel less sure of the shadows",
        bedtime_loss="the bed did not look cozy enough yet",
        tags={"glow", "dark"},
    ),
    "lost_song": Trouble(
        id="lost_song",
        need="song",
        symptom="its sleepy tune had thinned to a scratchy whisper",
        warning="without that quiet music, every tiny house sound felt too awake",
        risk="the child would keep listening for creaks instead of resting",
        bedtime_loss="the room did not feel settled enough for sleep",
        tags={"song", "sound"},
    ),
    "stiff_hop": Trouble(
        id="stiff_hop",
        need="cuddle",
        symptom="one of its bedtime motions had gone stiff, so it could not snuggle into place",
        warning="without that gentle cuddle, the blanket felt emptier than usual",
        risk="the child would miss the snug good-night feeling",
        bedtime_loss="the pillow corner felt lonely",
        tags={"cuddle", "comfort"},
    ),
}

UPGRADES = {
    "bionic_starwing": Upgrade(
        id="bionic_starwing",
        need="glow",
        label="bionic star-wing",
        phrase="a tiny bionic star-wing",
        install="fitted a silver winglet no bigger than a leaf and tapped it gently into place",
        after="the new wing caught the lamplight and turned it into a pearly glow",
        power_word="glow",
        sound="chim",
        tags={"bionic", "glow", "repair"},
    ),
    "bionic_chim_heart": Upgrade(
        id="bionic_chim_heart",
        need="song",
        label="bionic chim-heart",
        phrase="a small bionic chim-heart",
        install="set a moon-bright heart behind a little door and wound it with two careful turns",
        after="the heart answered with a soft chim and a warm thread of music",
        power_word="song",
        sound="chim",
        tags={"bionic", "song", "repair"},
    ),
    "bionic_hopper": Upgrade(
        id="bionic_hopper",
        need="cuddle",
        label="bionic hopper-spring",
        phrase="a tiny bionic hopper-spring",
        install="slid a springy silver piece beneath the helper's paws and stitched the seam closed",
        after="the new spring gave one polite bounce and settled into the gentlest cuddle",
        power_word="cuddle",
        sound="chim",
        tags={"bionic", "comfort", "repair"},
    ),
}

DRINKS = {
    "milk": Drink(
        id="milk",
        phrase="warm milk with a dot of honey",
        sip_line="Take one slow sip while I fix the little trouble,",
        warmth="The warm milk made the child's chest feel less fluttery.",
        tags={"milk", "sip", "bedtime"},
    ),
    "tea": Drink(
        id="tea",
        phrase="mild chamomile tea",
        sip_line="Take one slow sip while I mend this bedtime helper,",
        warmth="The tea's sleepy steam curled up softly, and the child breathed with it.",
        tags={"tea", "sip", "bedtime"},
    ),
    "cocoa": Drink(
        id="cocoa",
        phrase="thin bedtime cocoa",
        sip_line="Take one calm sip while I make this gentle repair,",
        warmth="The cocoa tasted soft and warm, like a blanket for the throat.",
        tags={"cocoa", "sip", "bedtime"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Nora", "Ivy", "Ada", "Rose", "Ella", "Zoe"]
BOY_NAMES = ["Owen", "Leo", "Milo", "Finn", "Theo", "Noah", "Eli", "Ben"]
TRAITS = ["sleepy", "gentle", "curious", "quiet", "thoughtful", "dreamy"]
BLANKET_COLORS = ["blue", "silver", "lavender", "cream", "green", "pink"]


def helper_supports_trouble(helper: HelperKind, trouble: Trouble) -> bool:
    return trouble.need == helper.bedtime_job.split()[0]


def upgrade_fixes_trouble(upgrade: Upgrade, trouble: Trouble) -> bool:
    return upgrade.need == trouble.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for helper_id, helper in HELPERS.items():
        for trouble_id, trouble in TROUBLES.items():
            if not helper_supports_trouble(helper, trouble):
                continue
            for upgrade_id, upgrade in UPGRADES.items():
                if upgrade_fixes_trouble(upgrade, trouble):
                    combos.append((helper_id, trouble_id, upgrade_id))
    return combos


def explain_rejection(helper: HelperKind, trouble: Trouble, upgrade: Optional[Upgrade] = None) -> str:
    if not helper_supports_trouble(helper, trouble):
        return (
            f"(No story: {helper.phrase} is known for {helper.bedtime_job}, "
            f"but the trouble '{trouble.id}' affects {trouble.need}. The bedtime "
            f"problem has to match what the helper actually does.)"
        )
    if upgrade is not None and not upgrade_fixes_trouble(upgrade, trouble):
        return (
            f"(No story: {upgrade.label} restores {upgrade.need}, but the trouble "
            f"here is {trouble.need}. The transformation must truly solve the bedtime problem.)"
        )
    return "(No story: this combination does not make a coherent bedtime repair.)"


def predict_bedtime(world: World, upgrade: Upgrade) -> dict:
    sim = world.copy()
    _install_upgrade(sim, upgrade, narrate=False)
    helper = sim.get("helper")
    child = sim.get("child")
    return {
        "working": helper.meters["working"] >= THRESHOLD,
        "calm": child.memes["calm"] + child.memes["hope"],
    }


def introduce(world: World, child: Entity, parent: Entity, helper_cfg: HelperKind, drink: Drink) -> None:
    helper = world.get("helper")
    world.say(
        f"On a quiet night, {child.id} climbed into a {child.attrs['blanket_color']} blanket while "
        f"{child.pronoun('possessive')} {parent.label_word} carried in {drink.phrase}."
    )
    world.say(
        f"Beside the pillow sat {helper_cfg.phrase}. It {helper_cfg.opening} and helped {child.id} {helper_cfg.bedtime_job}."
    )


def show_trouble(world: World, child: Entity, trouble: Trouble) -> None:
    helper = world.get("helper")
    helper.meters["working"] = 0.0
    helper.meters["failing"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But tonight {trouble.symptom}. {trouble.warning}."
    )
    world.say(
        f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin. "
        f'"Oh no," {child.pronoun()} whispered. "{world.get("helper").label.capitalize()} cannot do bedtime right."'
    )


def comfort_and_sip(world: World, child: Entity, parent: Entity, drink: Drink) -> None:
    child.meters["sipped"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat on the bed and stroked {child.pronoun("possessive")} hair. '
        f'"{drink.sip_line}" {parent.pronoun()} said.'
    )
    world.say(
        f"{child.id} took a careful sip. {drink.warmth}"
    )
    propagate(world, narrate=False)


def promise_fix(world: World, child: Entity, parent: Entity, trouble: Trouble, upgrade: Upgrade) -> None:
    pred = predict_bedtime(world, upgrade)
    world.facts["predicted_working"] = pred["working"]
    world.say(
        f'{parent.label_word.capitalize()} lifted the helper onto the little bedside stool. '
        f'"I think {world.get("helper").pronoun()} needs a {upgrade.label}," {parent.pronoun()} said softly.'
    )
    world.say(
        f"That would give the bedtime {upgrade.power_word} back, and {trouble.risk}."
    )


def _install_upgrade(world: World, upgrade: Upgrade, narrate: bool = True) -> None:
    helper = world.get("helper")
    helper.meters["patched"] += 1
    helper.attrs["upgrade"] = upgrade.id
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{world.get('parent').label_word.capitalize()} {upgrade.install}. Then the room went still for one tiny breath."
        )


def transform(world: World, child: Entity, helper_cfg: HelperKind, upgrade: Upgrade) -> None:
    _install_upgrade(world, upgrade, narrate=True)
    helper = world.get("helper")
    world.say(
        f"At once the helper changed. {upgrade.after}. "
        f'It gave a soft "{upgrade.sound}" that sounded almost like a sleepy bell.'
    )
    world.say(
        f"{child.id}'s eyes grew round. The little {helper_cfg.label} looked new and old at once, "
        f"familiar and wonderfully bionic."
    )


def restored_bedtime(world: World, child: Entity, parent: Entity, helper_cfg: HelperKind, trouble: Trouble) -> None:
    child.memes["safe"] += 1
    child.memes["love"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"Now the helper could do its work again. {trouble.bedtime_loss.capitalize()} before, but now the room softened around the bed."
    )
    world.say(
        f"{helper_cfg.phrase.capitalize()} {helper_cfg.ending_pose}, and {child.id} let out the long breath "
        f"{child.pronoun()} had been holding."
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.pronoun("possessive")} forehead. '
        f'"Even small bedtime troubles can be mended," {parent.pronoun()} said.'
    )
    world.say(
        f"Soon {child.id}'s eyes drifted closed, with the repaired helper keeping watch nearby."
    )


def tell(
    helper_cfg: HelperKind,
    trouble: Trouble,
    upgrade: Upgrade,
    drink: Drink,
    child_name: str = "Luna",
    child_gender: str = "girl",
    parent_type: str = "mother",
    child_trait: str = "dreamy",
    blanket_color: str = "blue",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"blanket_color": blanket_color, "trait": child_trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="thing",
        type=helper_cfg.id,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        tags=set(helper_cfg.tags),
        attrs={"job": helper_cfg.bedtime_job, "trouble": trouble.id, "upgrade": ""},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="bedroom",
        label="bedroom",
        role="room",
        attrs={},
    ))

    child.meters["sipped"] = 0.0
    helper.meters["working"] = 1.0
    helper.meters["failing"] = 0.0
    helper.meters["patched"] = 0.0
    helper.meters["transformed"] = 0.0
    room.meters["unsettled"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["safe"] = 0.0
    child.memes["love"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["awe"] = 0.0
    child.memes["sleepy"] = 0.0

    world.facts.update(
        helper_cfg=helper_cfg,
        trouble=trouble,
        upgrade=upgrade,
        drink=drink,
        child=child,
        parent=parent,
        helper=helper,
        room=room,
    )

    introduce(world, child, parent, helper_cfg, drink)

    world.para()
    show_trouble(world, child, trouble)
    comfort_and_sip(world, child, parent, drink)
    promise_fix(world, child, parent, trouble, upgrade)

    world.para()
    transform(world, child, helper_cfg, upgrade)

    world.para()
    restored_bedtime(world, child, parent, helper_cfg, trouble)

    world.facts.update(
        transformed=helper.meters["transformed"] >= THRESHOLD,
        working=helper.meters["working"] >= THRESHOLD,
        calm=child.memes["calm"] >= THRESHOLD,
        sleepy=child.memes["sleepy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sip": [
        (
            "What is a sip?",
            "A sip is a very small drink. You take only a little bit at a time."
        )
    ],
    "bionic": [
        (
            "What does bionic mean?",
            "Bionic means something has a special made part that helps it work better. In a story, a bionic part can sound magical, but it still has a job to do."
        )
    ],
    "glow": [
        (
            "Why can a soft glow help at bedtime?",
            "A soft glow lets you see the room without making it too bright. That can make shadows feel calmer and easier to understand."
        )
    ],
    "song": [
        (
            "Why can quiet music help someone fall asleep?",
            "Quiet music gives the ears one gentle thing to follow. That can make the rest of the room feel calmer."
        )
    ],
    "cuddle": [
        (
            "Why does a cuddly object help at bedtime?",
            "A cuddly object can make a bed feel familiar and safe. Soft touch often helps children relax."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix the part that is not working right. After a repair, the thing can do its job again."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime routines help?",
            "Bedtime routines help because the same calm steps happen in the same order. Your body starts to understand that sleep is coming."
        )
    ],
}
KNOWLEDGE_ORDER = ["sip", "bionic", "glow", "song", "cuddle", "repair", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper_cfg = f["helper_cfg"]
    trouble = f["trouble"]
    upgrade = f["upgrade"]
    drink = f["drink"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "sip", "chim", and "bionic".',
        f"Tell a gentle transformation story where {child.id}'s {helper_cfg.label} loses its bedtime {trouble.need}, "
        f"then receives {upgrade.phrase} while {child.id} takes a sip of {drink.phrase}.",
        f"Write a sleepy story about a small bedtime problem, a calm grown-up repair, and a helper that changes just enough to make the room feel safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper_cfg = f["helper_cfg"]
    trouble = f["trouble"]
    upgrade = f["upgrade"]
    drink = f["drink"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} bedtime helper, and {child.pronoun('possessive')} {parent.label_word}. The story happens during a quiet bedtime problem."
        ),
        (
            f"What was wrong with the {helper_cfg.label}?",
            f"The helper had a bedtime trouble: {trouble.symptom}. Because of that, {trouble.risk}."
        ),
        (
            f"Why did {child.id} take a sip of {drink.phrase}?",
            f"{child.id} took a sip while {parent.label_word} worked on the repair. The warm drink helped {child.pronoun('object')} feel calmer while waiting."
        ),
        (
            "How did the transformation happen?",
            f"{parent.label_word.capitalize()} installed {upgrade.phrase}, and that changed the helper so it could work again. After the repair, it made a soft '{upgrade.sound}' sound and became gently bionic."
        ),
        (
            "How did the story end?",
            f"The helper could do its bedtime job again, so the room felt softer and safer. Then {child.id} relaxed and drifted toward sleep."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trouble = f["trouble"]
    tags = {"sip", "bionic", "repair", "bedtime"}
    tags.add(trouble.need)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        helper="moth",
        trouble="dim_glow",
        upgrade="bionic_starwing",
        drink="milk",
        child_name="Luna",
        child_gender="girl",
        parent_type="mother",
        child_trait="dreamy",
        blanket_color="blue",
    ),
    StoryParams(
        helper="owl",
        trouble="lost_song",
        upgrade="bionic_chim_heart",
        drink="tea",
        child_name="Milo",
        child_gender="boy",
        parent_type="father",
        child_trait="quiet",
        blanket_color="silver",
    ),
    StoryParams(
        helper="bunny",
        trouble="stiff_hop",
        upgrade="bionic_hopper",
        drink="cocoa",
        child_name="Ada",
        child_gender="girl",
        parent_type="mother",
        child_trait="gentle",
        blanket_color="lavender",
    ),
]


ASP_RULES = r"""
supports(H, T) :- helper(H), trouble(T), job_need(H, N), trouble_need(T, N).
fixes(U, T)    :- upgrade(U), trouble(T), upgrade_need(U, N), trouble_need(T, N).
valid(H, T, U) :- helper(H), trouble(T), upgrade(U), supports(H, T), fixes(U, T).

working_after(U, T) :- fixes(U, T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("job_need", helper_id, helper.bedtime_job.split()[0]))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("trouble_need", trouble_id, trouble.need))
    for upgrade_id, upgrade in UPGRADES.items():
        lines.append(asp.fact("upgrade", upgrade_id))
        lines.append(asp.fact("upgrade_need", upgrade_id, upgrade.need))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime transformation world: a child, a tired helper, and a gentle bionic repair."
    )
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--upgrade", choices=UPGRADES)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible helper/trouble/upgrade combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.trouble:
        helper = HELPERS[args.helper]
        trouble = TROUBLES[args.trouble]
        if not helper_supports_trouble(helper, trouble):
            raise StoryError(explain_rejection(helper, trouble))
    if args.trouble and args.upgrade:
        trouble = TROUBLES[args.trouble]
        upgrade = UPGRADES[args.upgrade]
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        if args.helper and not helper_supports_trouble(helper, trouble):
            raise StoryError(explain_rejection(helper, trouble, upgrade))
        if not upgrade_fixes_trouble(upgrade, trouble):
            raise StoryError(explain_rejection(helper, trouble, upgrade))

    combos = [
        c for c in valid_combos()
        if (args.helper is None or c[0] == args.helper)
        and (args.trouble is None or c[1] == args.trouble)
        and (args.upgrade is None or c[2] == args.upgrade)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    helper_id, trouble_id, upgrade_id = rng.choice(sorted(combos))
    drink_id = args.drink or rng.choice(sorted(DRINKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    blanket_color = rng.choice(BLANKET_COLORS)

    return StoryParams(
        helper=helper_id,
        trouble=trouble_id,
        upgrade=upgrade_id,
        drink=drink_id,
        child_name=name,
        child_gender=gender,
        parent_type=parent_type,
        child_trait=trait,
        blanket_color=blanket_color,
    )


def generate(params: StoryParams) -> StorySample:
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.upgrade not in UPGRADES:
        raise StoryError(f"(Unknown upgrade: {params.upgrade})")
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")

    helper_cfg = HELPERS[params.helper]
    trouble = TROUBLES[params.trouble]
    upgrade = UPGRADES[params.upgrade]
    if not helper_supports_trouble(helper_cfg, trouble):
        raise StoryError(explain_rejection(helper_cfg, trouble))
    if not upgrade_fixes_trouble(upgrade, trouble):
        raise StoryError(explain_rejection(helper_cfg, trouble, upgrade))

    world = tell(
        helper_cfg=helper_cfg,
        trouble=trouble,
        upgrade=upgrade,
        drink=DRINKS[params.drink],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
        child_trait=params.child_trait,
        blanket_color=params.blanket_color,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (helper, trouble, upgrade) combos:\n")
        for helper_id, trouble_id, upgrade_id in combos:
            print(f"  {helper_id:8} {trouble_id:10} {upgrade_id}")
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
            header = f"### {p.child_name}: {p.helper} + {p.trouble} -> {p.upgrade}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
