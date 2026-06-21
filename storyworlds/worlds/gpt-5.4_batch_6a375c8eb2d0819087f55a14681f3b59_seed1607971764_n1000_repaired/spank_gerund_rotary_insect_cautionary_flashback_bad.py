#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spank_gerund_rotary_insect_cautionary_flashback_bad.py
=================================================================================

A standalone storyworld for a small cautionary mystery.

Premise
-------
A child playing detective hears a strange sound around an old rotary machine and
spots a tiny insect near it. The child remembers a warning from earlier, but
chooses to touch the forbidden control anyway. The machine wakes up, the air
turns wild, the paper clues fly away, and the mystery ends badly. The story uses
a flashback beat, keeps the mood close to a gentle mystery, and ends with a sad,
clear caution.

Run it
------
python storyworlds/worlds/gpt-5.4/spank_gerund_rotary_insect_cautionary_flashback_bad.py
python storyworlds/worlds/gpt-5.4/spank_gerund_rotary_insect_cautionary_flashback_bad.py --all
python storyworlds/worlds/gpt-5.4/spank_gerund_rotary_insect_cautionary_flashback_bad.py --qa --json
python storyworlds/worlds/gpt-5.4/spank_gerund_rotary_insect_cautionary_flashback_bad.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Device:
    id: str
    label: str
    phrase: str
    control: str
    motion: str
    sound: str
    pull: int
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
class Insect:
    id: str
    label: str
    phrase: str
    clue_sign: str
    flying: bool
    fragile: bool
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
class Evidence:
    id: str
    label: str
    phrase: str
    loose: bool
    scribble: str
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
class StoryParams:
    setting: str
    device: str
    insect: str
    evidence: str
    child_name: str
    child_gender: str
    guardian: str
    trait: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_wind(world: World) -> list[str]:
    device = world.get("device")
    room = world.get("room")
    if device.meters["spinning"] < THRESHOLD:
        return []
    sig = ("wind",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["wind"] += device.attrs["pull"]
    return []


def _r_scatter(world: World) -> list[str]:
    room = world.get("room")
    evidence = world.get("evidence")
    if room.meters["wind"] < THRESHOLD or not evidence.attrs["loose"]:
        return []
    sig = ("scatter", evidence.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    evidence.meters["scattered"] += 1
    child = world.get("child")
    child.memes["confusion"] += 1
    return []


def _r_lose_insect(world: World) -> list[str]:
    room = world.get("room")
    insect = world.get("insect")
    if room.meters["wind"] < THRESHOLD or not insect.attrs["flying"]:
        return []
    sig = ("lose", insect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    insect.meters["lost"] += 1
    child = world.get("child")
    child.memes["regret"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wind", tag="physical", apply=_r_wind),
    Rule(name="scatter", tag="physical", apply=_r_scatter),
    Rule(name="lose_insect", tag="physical", apply=_r_lose_insect),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        now_count = len(world.fired)
        if not changed:
            for rule in CAUSAL_RULES:
                before = len(world.fired)
                out = rule.apply(world)
                if out or len(world.fired) > before:
                    changed = True
                    produced.extend(out)
            if not changed and len(world.fired) == now_count:
                break
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(setting_id: str, device_id: str, insect_id: str, evidence_id: str) -> bool:
    setting = SETTINGS[setting_id]
    device = DEVICES[device_id]
    insect = INSECTS[insect_id]
    evidence = EVIDENCE[evidence_id]
    return (
        device_id in setting.affords
        and device.pull > 0
        and insect.flying
        and insect.fragile
        and evidence.loose
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for device_id in DEVICES:
            for insect_id in INSECTS:
                for evidence_id in EVIDENCE:
                    if valid_combo(setting_id, device_id, insect_id, evidence_id):
                        out.append((setting_id, device_id, insect_id, evidence_id))
    return out


def explain_rejection(setting_id: str, device_id: str, insect_id: str, evidence_id: str) -> str:
    setting = SETTINGS[setting_id]
    device = DEVICES[device_id]
    insect = INSECTS[insect_id]
    evidence = EVIDENCE[evidence_id]
    if device_id not in setting.affords:
        return (
            f"(No story: {setting.place} does not reasonably contain {device.phrase}. "
            f"The mystery needs the child to find that device in that place.)"
        )
    if device.pull <= 0:
        return (
            f"(No story: {device.label} does not create enough wind to cause the bad turn. "
            f"This world needs a rotary machine that can snatch the clues away.)"
        )
    if not insect.flying:
        return (
            f"(No story: {insect.label} would not be swept away by the machine. "
            f"The cautionary ending depends on a small flying insect being lost.)"
        )
    if not insect.fragile:
        return (
            f"(No story: {insect.label} is too sturdy for this delicate mystery beat. "
            f"Pick a more fragile insect.)"
        )
    if not evidence.loose:
        return (
            f"(No story: {evidence.phrase} would not scatter in the wind, so the mystery "
            f"would not truly go wrong. Pick a paper clue instead.)"
        )
    return "(No story: that combination does not fit this world.)"


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.setting, params.device, params.insect, params.evidence):
        raise StoryError(
            explain_rejection(params.setting, params.device, params.insect, params.evidence)
        )
    return "bad"


def predict_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("device").meters["spinning"] += 1
    propagate(sim, narrate=False)
    return {
        "paper_lost": sim.get("evidence").meters["scattered"] >= THRESHOLD,
        "insect_lost": sim.get("insect").meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, guardian: Entity, evidence_cfg: Evidence) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At dusk, {child.id} walked into {world.setting.place}, where {world.setting.mood}. "
        f"{child.pronoun().capitalize()} liked pretending to be a little detective."
    )
    world.say(
        f"In one hand {child.pronoun()} carried {evidence_cfg.phrase}. On the first page, "
        f"{child.pronoun()} had written the secret codeword spank-gerund in large, careful letters."
    )
    world.say(
        f"{guardian.label_word.capitalize()} was nearby, sorting old things and trusting "
        f"{child.id} to stay away from what was not safe."
    )


def discover(world: World, child: Entity, device_cfg: Device, insect_cfg: Insect, evidence_cfg: Evidence) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then a tiny sound rose from the shadows: {device_cfg.sound}. Near {device_cfg.phrase}, "
        f"{child.id} spotted {insect_cfg.phrase}, and beside it lay a strange hint in "
        f"{evidence_cfg.label}: {evidence_cfg.scribble}."
    )
    world.say(
        f"It felt like the beginning of a mystery. Why was the little insect waiting by "
        f"the old rotary machine?"
    )


def flashback_warning(world: World, child: Entity, guardian: Entity, device_cfg: Device) -> None:
    child.memes["caution"] += 1
    world.facts["flashback"] = True
    world.say(
        f"A memory flashed back to {child.id} at once. Earlier that week, {guardian.label_word} "
        f"had rested a hand on the dusty frame and said, "
        f"\"Never touch the {device_cfg.control} on this {device_cfg.label}. When it starts to "
        f"{device_cfg.motion}, it snatches light things into a rushing swirl.\""
    )


def choose(world: World, child: Entity, guardian: Entity, device_cfg: Device, insect_cfg: Insect) -> None:
    pred = predict_loss(world)
    world.facts["predicted_paper_lost"] = pred["paper_lost"]
    world.facts["predicted_insect_lost"] = pred["insect_lost"]
    child.memes["defiance"] += 1
    world.say(
        f"But the secret felt too close to leave alone. {child.id} thought that if "
        f"{child.pronoun()} turned the {device_cfg.control} just once, "
        f"{child.pronoun()} might learn where {insect_cfg.label} had come from before "
        f"{guardian.label_word} noticed."
    )


def start_machine(world: World, child: Entity, device_cfg: Device) -> None:
    device = world.get("device")
    device.meters["spinning"] += 1
    propagate(world, narrate=False)
    room = world.get("room")
    evidence = world.get("evidence")
    insect = world.get("insect")
    world.say(
        f"{child.id} touched the {device_cfg.control}. At once the {device_cfg.label} began "
        f"to {device_cfg.motion}, and the soft room changed into a hard rushing sound."
    )
    if room.meters["wind"] >= THRESHOLD:
        world.say(
            "Cold air whirled through the dust like invisible hands."
        )
    if evidence.meters["scattered"] >= THRESHOLD:
        world.say(
            f"The paper clues flew upward first. Pages spun apart, and the sheet with "
            f"spank-gerund on it vanished into the dark rafters."
        )
    if insect.meters["lost"] >= THRESHOLD:
        world.say(
            f"The little {insect.attrs['label']} lifted, tumbled once in the wild air, "
            f"and was swept out of sight."
        )


def too_late(world: World, child: Entity, guardian: Entity, evidence_cfg: Evidence, insect_cfg: Insect) -> None:
    child.memes["fear"] += 1
    child.memes["regret"] += 1
    world.say(
        f'"{child.id}!" {guardian.label_word.capitalize()} called, rushing over and pulling the power lever down. '
        "The room fell quiet again, but not kind."
    )
    world.say(
        f"{child.id} searched the boards, the corners, and the cracked windowsill, yet "
        f"neither the loose pages nor the little {insect_cfg.label} came back."
    )
    world.say(
        f"The mystery was over in the worst way: not solved, only spoiled. {evidence_cfg.ending_image}."
    )


def ending(world: World, child: Entity, guardian: Entity, device_cfg: Device) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} did not shout. {guardian.pronoun().capitalize()} only said, "
        f"\"Some warnings are part of the mystery too. If you ignore them, the ending can turn bad before "
        f"you even know what you were trying to save.\""
    )
    world.say(
        f"That night, {child.id} closed the empty cover of the casebook and looked at the still "
        f"{device_cfg.label}. It kept its secret, and {child.pronoun()} finally understood why "
        f"grown-ups had said to leave it alone."
    )


def tell(
    setting: Setting,
    device_cfg: Device,
    insect_cfg: Insect,
    evidence_cfg: Evidence,
    child_name: str = "Nora",
    child_gender: str = "girl",
    guardian_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait, "detective-minded"],
            attrs={},
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            label="the guardian",
            role="guardian",
            traits=["careful"],
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=setting.place,
            attrs={},
        )
    )
    device = world.add(
        Entity(
            id="device",
            type="machine",
            label=device_cfg.label,
            phrase=device_cfg.phrase,
            attrs={"pull": device_cfg.pull},
        )
    )
    insect = world.add(
        Entity(
            id="insect",
            type="insect",
            label=insect_cfg.label,
            phrase=insect_cfg.phrase,
            attrs={
                "flying": insect_cfg.flying,
                "fragile": insect_cfg.fragile,
                "label": insect_cfg.label,
            },
        )
    )
    evidence = world.add(
        Entity(
            id="evidence",
            type="paper",
            label=evidence_cfg.label,
            phrase=evidence_cfg.phrase,
            attrs={"loose": evidence_cfg.loose},
        )
    )

    room.meters["wind"] = 0.0
    device.meters["spinning"] = 0.0
    insect.meters["lost"] = 0.0
    evidence.meters["scattered"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["caution"] = 0.0
    child.memes["defiance"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["regret"] = 0.0
    child.memes["lesson"] = 0.0

    introduce(world, child, guardian, evidence_cfg)
    world.para()
    discover(world, child, device_cfg, insect_cfg, evidence_cfg)
    flashback_warning(world, child, guardian, device_cfg)
    choose(world, child, guardian, device_cfg, insect_cfg)
    world.para()
    start_machine(world, child, device_cfg)
    too_late(world, child, guardian, evidence_cfg, insect_cfg)
    world.para()
    ending(world, child, guardian, device_cfg)

    world.facts.update(
        child=child,
        guardian=guardian,
        room=room,
        device=device,
        device_cfg=device_cfg,
        insect=insect,
        insect_cfg=insect_cfg,
        evidence=evidence,
        evidence_cfg=evidence_cfg,
        setting=setting,
        outcome="bad",
        paper_lost=evidence.meters["scattered"] >= THRESHOLD,
        insect_lost=insect.meters["lost"] >= THRESHOLD,
        flashback=True,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the old attic",
        mood="the slanted roof held stripes of evening light and every trunk seemed to hide a clue",
        affords={"vent_fan", "grain_sorter"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the glass greenhouse",
        mood="the panes clicked softly and the leaves made dark little shapes on the floor",
        affords={"seed_fan", "vent_fan"},
    ),
    "clock_shed": Setting(
        id="clock_shed",
        place="the clock shed behind the house",
        mood="chains, gears, and shadows made the place feel full of patient secrets",
        affords={"grain_sorter", "seed_fan"},
    ),
}

DEVICES = {
    "vent_fan": Device(
        id="vent_fan",
        label="rotary vent fan",
        phrase="an old rotary vent fan",
        control="brass switch",
        motion="spin faster and faster",
        sound="tick-whirr, tick-whirr",
        pull=2,
        tags={"rotary", "fan"},
    ),
    "seed_fan": Device(
        id="seed_fan",
        label="rotary seed fan",
        phrase="a narrow rotary seed fan",
        control="painted handle",
        motion="whirl in a dry circle",
        sound="whup-whup",
        pull=2,
        tags={"rotary", "fan"},
    ),
    "grain_sorter": Device(
        id="grain_sorter",
        label="rotary grain sorter",
        phrase="a boxy rotary grain sorter",
        control="side crank",
        motion="chatter and turn",
        sound="clack-clack",
        pull=2,
        tags={"rotary", "machine"},
    ),
}

INSECTS = {
    "moth": Insect(
        id="moth",
        label="moth",
        phrase="a pale moth with powdery wings",
        clue_sign="dusty wingprints",
        flying=True,
        fragile=True,
        tags={"insect", "moth"},
    ),
    "lacewing": Insect(
        id="lacewing",
        label="lacewing",
        phrase="a green lacewing as thin as a leaf",
        clue_sign="a tremble of glassy wings",
        flying=True,
        fragile=True,
        tags={"insect", "lacewing"},
    ),
    "firefly": Insect(
        id="firefly",
        label="firefly",
        phrase="a firefly blinking like a small green lantern",
        clue_sign="a blink in the dark",
        flying=True,
        fragile=True,
        tags={"insect", "firefly"},
    ),
    "caterpillar": Insect(
        id="caterpillar",
        label="caterpillar",
        phrase="a striped caterpillar curled on a beam",
        clue_sign="a tiny chew mark on a leaf",
        flying=False,
        fragile=True,
        tags={"insect", "caterpillar"},
    ),
}

EVIDENCE = {
    "casebook": Evidence(
        id="casebook",
        label="the casebook",
        phrase="a paper casebook tied with blue string",
        loose=True,
        scribble="three tiny circles and an arrow toward the machine",
        ending_image="One torn page fluttered from a beam and landed face down in the dust",
        tags={"paper", "notebook"},
    ),
    "map": Evidence(
        id="map",
        label="the folded map",
        phrase="a folded paper map of the little room",
        loose=True,
        scribble="a ring around the machine and a question mark beside it",
        ending_image="A ripped corner of the map clung to a nail while the rest was gone",
        tags={"paper", "map"},
    ),
    "sketch": Evidence(
        id="sketch",
        label="the sketch",
        phrase="a charcoal sketch on thin paper",
        loose=True,
        scribble="a quick drawing of wings beside the machine",
        ending_image="Only a gray smear of charcoal remained on the floorboards",
        tags={"paper", "drawing"},
    ),
    "magnifier": Evidence(
        id="magnifier",
        label="the magnifying glass",
        phrase="a brass magnifying glass",
        loose=False,
        scribble="no paper mark at all",
        ending_image="The heavy glass stayed where it had been",
        tags={"tool"},
    ),
}

GIRL_NAMES = ["Nora", "Mira", "Lila", "Tess", "Ivy", "June", "Ada", "Wren"]
BOY_NAMES = ["Owen", "Felix", "Jasper", "Theo", "Milo", "Ben", "Evan", "Arlo"]
TRAITS = ["curious", "bold", "restless", "dreamy", "eager"]


KNOWLEDGE = {
    "rotary": [
        (
            "What does rotary mean?",
            "Rotary means something turns in a circle. A rotary machine can spin fast and move air or parts around."
        )
    ],
    "insect": [
        (
            "What is an insect?",
            "An insect is a very small animal with six legs. Many insects also have wings and can be hurt easily."
        )
    ],
    "moth": [
        (
            "Why are moths easy to hurt?",
            "Moths have light, powdery wings that can tear or lose their dust. Strong wind can toss them around."
        )
    ],
    "firefly": [
        (
            "What is a firefly?",
            "A firefly is a small insect that can glow. It uses that tiny light to signal in the dark."
        )
    ],
    "lacewing": [
        (
            "What is a lacewing?",
            "A lacewing is a small green insect with delicate wings. Its wings are so thin that rough air can hurt it."
        )
    ],
    "paper": [
        (
            "Why can paper clues blow away?",
            "Paper is light, so moving air can lift it easily. That is why loose pages should be kept safe around fans or open windows."
        )
    ],
    "warning": [
        (
            "Why should children listen to safety warnings?",
            "Safety warnings tell you about danger before it starts. Listening early can stop a bad ending before anything is lost."
        )
    ],
}
KNOWLEDGE_ORDER = ["rotary", "insect", "moth", "firefly", "lacewing", "paper", "warning"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    setting = world.facts["setting"]
    insect_cfg = world.facts["insect_cfg"]
    device_cfg = world.facts["device_cfg"]
    return [
        (
            f'Write a short mystery for a 3-to-5-year-old that includes the words '
            f'"spank-gerund", "rotary", and "insect", and ends badly after a child ignores a warning.'
        ),
        (
            f"Tell a cautionary mystery set in {setting.place} where {child.id} notices "
            f"{insect_cfg.phrase} near {device_cfg.phrase}, remembers an earlier warning, "
            f"and still makes the wrong choice."
        ),
        (
            "Write a simple flashback mystery in which a child detective chases a clue, "
            "forgets to be careful, and loses both the paper evidence and the tiny creature."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    setting = world.facts["setting"]
    insect_cfg = world.facts["insect_cfg"]
    device_cfg = world.facts["device_cfg"]
    evidence_cfg = world.facts["evidence_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child pretending to be a detective, and {child.pronoun('possessive')} "
            f"{guardian.label_word} nearby in {setting.place}."
        ),
        (
            "What mystery did the child think had begun?",
            f"{child.id} heard {device_cfg.sound} near {device_cfg.phrase} and saw {insect_cfg.phrase} beside it. "
            f"That made the scene feel like a hidden clue instead of an ordinary old corner."
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {guardian.label_word} had already warned {child.id} not to touch the "
            f"{device_cfg.control} on the {device_cfg.label}. The warning mattered because the machine could "
            f"spin up and snatch light things away."
        ),
        (
            f"Why did the ending turn bad?",
            f"The ending turned bad because {child.id} ignored the warning and started the machine anyway. "
            f"The rushing air scattered {evidence_cfg.label} and swept the little {insect_cfg.label} out of sight."
        ),
    ]
    if world.facts["paper_lost"]:
        qa.append(
            (
                "What happened to the clues?",
                f"The paper clues flew apart and were lost around the room. That is why the mystery could not be solved afterward."
            )
        )
    if world.facts["insect_lost"]:
        qa.append(
            (
                f"What happened to the {insect_cfg.label}?",
                f"The little {insect_cfg.label} was caught in the wild air and disappeared. "
                f"It was too small and delicate to stay safe once the rotary machine began to move."
            )
        )
    qa.append(
        (
            "What did the child learn at the end?",
            f"{child.id} learned that some mysteries should be left alone until a grown-up can help. "
            f"The warning had been part of the answer all along."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rotary", "insect", "paper", "warning"}
    tags |= set(world.facts["insect_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
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
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        device="vent_fan",
        insect="moth",
        evidence="casebook",
        child_name="Nora",
        child_gender="girl",
        guardian="mother",
        trait="curious",
    ),
    StoryParams(
        setting="greenhouse",
        device="seed_fan",
        insect="firefly",
        evidence="map",
        child_name="Theo",
        child_gender="boy",
        guardian="father",
        trait="eager",
    ),
    StoryParams(
        setting="clock_shed",
        device="grain_sorter",
        insect="lacewing",
        evidence="sketch",
        child_name="Mira",
        child_gender="girl",
        guardian="mother",
        trait="bold",
    ),
]


ASP_RULES = r"""
valid(S,D,I,E) :- setting(S), affords(S,D), device(D), pull(D,P), P > 0,
                  insect(I), flying(I), fragile(I),
                  evidence(E), loose(E).

outcome(bad) :- chosen_setting(S), chosen_device(D), chosen_insect(I), chosen_evidence(E),
                valid(S,D,I,E).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for device_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, device_id))
    for device_id, device in DEVICES.items():
        lines.append(asp.fact("device", device_id))
        lines.append(asp.fact("pull", device_id, device.pull))
    for insect_id, insect in INSECTS.items():
        lines.append(asp.fact("insect", insect_id))
        if insect.flying:
            lines.append(asp.fact("flying", insect_id))
        if insect.fragile:
            lines.append(asp.fact("fragile", insect_id))
    for evidence_id, evidence in EVIDENCE.items():
        lines.append(asp.fact("evidence", evidence_id))
        if evidence.loose:
            lines.append(asp.fact("loose", evidence_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_device", params.device),
            asp.fact("chosen_insect", params.insect),
            asp.fact("chosen_evidence", params.evidence),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary mystery about an old rotary machine, a tiny insect, and a bad choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--insect", choices=INSECTS)
    ap.add_argument("--evidence", choices=EVIDENCE)
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if (
        args.setting is not None
        and args.device is not None
        and args.insect is not None
        and args.evidence is not None
        and not valid_combo(args.setting, args.device, args.insect, args.evidence)
    ):
        raise StoryError(explain_rejection(args.setting, args.device, args.insect, args.evidence))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.device is None or combo[1] == args.device)
        and (args.insect is None or combo[2] == args.insect)
        and (args.evidence is None or combo[3] == args.evidence)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, device_id, insect_id, evidence_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        device=device_id,
        insect=insect_id,
        evidence=evidence_id,
        child_name=child_name,
        child_gender=gender,
        guardian=guardian,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.insect not in INSECTS:
        raise StoryError(f"(Unknown insect: {params.insect})")
    if params.evidence not in EVIDENCE:
        raise StoryError(f"(Unknown evidence: {params.evidence})")
    if params.guardian not in {"mother", "father"}:
        raise StoryError(f"(Unknown guardian type: {params.guardian})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if not valid_combo(params.setting, params.device, params.insect, params.evidence):
        raise StoryError(explain_rejection(params.setting, params.device, params.insect, params.evidence))

    world = tell(
        setting=SETTINGS[params.setting],
        device_cfg=DEVICES[params.device],
        insect_cfg=INSECTS[params.insect],
        evidence_cfg=EVIDENCE[params.evidence],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian,
        trait=params.trait,
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
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        if not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("missing prompts or QA")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (setting, device, insect, evidence) combos:\n")
        for setting_id, device_id, insect_id, evidence_id in combos:
            print(f"  {setting_id:10} {device_id:12} {insect_id:12} {evidence_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
                f"### {p.child_name}: {p.setting}, {p.device}, {p.insect}, {p.evidence} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
