#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py
=========================================================================

A standalone story world for a gentle child-facing whodunit:

    a class reptile disappears during a steamy school event,
    a child detective follows a clue made by steam,
    and the mystery ends not with punishment, but with honesty.

The world is small on purpose. It models:
- typed entities with physical meters and emotional memes,
- a reasonableness gate over which reptile can be hidden where,
- a state-driven steam clue,
- a moral conflict inside the culprit (loyalty / winning / care vs honesty),
- a complete beginning, turn, and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py
    python storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py --reptile gecko --steam kettle --spot seed_drawer
    python storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py --reptile iguana --spot coat_cubby
    python storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/reptile_steam_moral_value_conflict_whodunit.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class ReptileCfg:
    id: str
    label: str
    phrase: str
    species_word: str
    warmth_need: int
    moisture_need: int
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
class SteamCfg:
    id: str
    label: str
    phrase: str
    place_text: str
    zone: str
    warmth: int
    moisture: int
    clue_text: str
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
class SpotCfg:
    id: str
    label: str
    phrase: str
    zone: str
    warmth: int
    moisture: int
    clue_line: str
    ending_line: str
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
class MotiveCfg:
    id: str
    short: str
    secret_line: str
    confession_line: str
    lesson_line: str
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


REPTILES = {
    "turtle": ReptileCfg(
        id="turtle",
        label="turtle",
        phrase="a small painted turtle named Moss",
        species_word="reptile",
        warmth_need=1,
        moisture_need=1,
        tags={"reptile", "turtle"},
    ),
    "gecko": ReptileCfg(
        id="gecko",
        label="gecko",
        phrase="a bright-eyed gecko named Pebble",
        species_word="reptile",
        warmth_need=2,
        moisture_need=0,
        tags={"reptile", "gecko"},
    ),
    "iguana": ReptileCfg(
        id="iguana",
        label="iguana",
        phrase="a leafy green iguana named Basil",
        species_word="reptile",
        warmth_need=2,
        moisture_need=2,
        tags={"reptile", "iguana"},
    ),
}

STEAM_SOURCES = {
    "kettle": SteamCfg(
        id="kettle",
        label="kettle",
        phrase="the silver kettle for mint tea",
        place_text="on the potting table",
        zone="table_side",
        warmth=1,
        moisture=1,
        clue_text="a soft white ribbon of steam curled up and pearled into tiny drops on nearby wood",
        tags={"steam", "tea"},
    ),
    "humidifier": SteamCfg(
        id="humidifier",
        label="humidifier",
        phrase="the classroom humidifier",
        place_text="beside the terrarium shelf",
        zone="terrarium_side",
        warmth=1,
        moisture=2,
        clue_text="a steady hush of steam made the glass nearby fog and bead",
        tags={"steam", "humidifier"},
    ),
    "soup_pot": SteamCfg(
        id="soup_pot",
        label="soup pot",
        phrase="the big soup pot for the winter fair",
        place_text="by the serving table",
        zone="coat_side",
        warmth=2,
        moisture=1,
        clue_text="fat puffs of steam rolled up and left damp prints on anything close to the ladle table",
        tags={"steam", "soup"},
    ),
}

SPOTS = {
    "fern_crate": SpotCfg(
        id="fern_crate",
        label="fern crate",
        phrase="a crate of ferns under the misting shelf",
        zone="terrarium_side",
        warmth=2,
        moisture=2,
        clue_line="The fern leaves still wore bright beads of water, and one leaf was bent as if something had brushed past it.",
        ending_line="Moss blinked from the ferns as if the whole thing had been an odd game.",
        tags={"plants", "humid"},
    ),
    "seed_drawer": SpotCfg(
        id="seed_drawer",
        label="seed drawer",
        phrase="the warm seed drawer in the potting bench",
        zone="table_side",
        warmth=2,
        moisture=0,
        clue_line="The brass knob of the drawer was dotted with wet pearls, even though the drawer itself should have been dry.",
        ending_line="Pebble peeped from the drawer, toes tucked under like tiny commas.",
        tags={"drawer", "warm"},
    ),
    "sunny_rock": SpotCfg(
        id="sunny_rock",
        label="sunny rock shelf",
        phrase="the sunny rock shelf by the glass wall",
        zone="terrarium_side",
        warmth=2,
        moisture=0,
        clue_line="A warm patch of fog had faded on the glass above the rocks, as if steam had kissed it and then vanished.",
        ending_line="The little reptile lifted its head from the warm stones and looked almost embarrassed for everybody.",
        tags={"rock", "warm"},
    ),
    "coat_cubby": SpotCfg(
        id="coat_cubby",
        label="coat cubby",
        phrase="the dark coat cubby near the fair door",
        zone="coat_side",
        warmth=0,
        moisture=0,
        clue_line="The cubby door held a thumbprint in the damp, but the space behind it felt cool and close.",
        ending_line="The reptile was safe, but it looked very glad to be brought back into the light.",
        tags={"cubby", "cool"},
    ),
}

MOTIVES = {
    "win_ribbon": MotiveCfg(
        id="win_ribbon",
        short="wanted to win the nature ribbon",
        secret_line="had borrowed the class pet for a secret look at its shell and scales, hoping that one last detail would make a poster win",
        confession_line="I only meant to study it for one minute more. Then everyone started asking questions, and I got scared to tell the truth.",
        lesson_line="Wanting to win never makes hiding the truth the right choice.",
        tags={"honesty", "winning"},
    ),
    "protect_friend": MotiveCfg(
        id="protect_friend",
        short="wanted to protect a friend from blame",
        secret_line="had moved the class pet after seeing a friend tap the glass too hard and was trying to keep that friend out of trouble",
        confession_line="I thought if no one knew I moved it, my friend would not get blamed. But the lie only made the whole room worry more.",
        lesson_line="Protecting someone with a lie can still hurt other people.",
        tags={"honesty", "loyalty"},
    ),
    "keep_comfy": MotiveCfg(
        id="keep_comfy",
        short="thought the reptile looked chilly",
        secret_line="had tried to tuck the class pet somewhere warmer for a little while, without asking the teacher first",
        confession_line="I was trying to help, but I should have told a grown-up instead of sneaking it away.",
        lesson_line="Caring means asking for help, not sneaking around with a secret.",
        tags={"honesty", "care"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ella", "Ruby", "Iris", "Tessa"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Sam", "Eli", "Noah", "Finn", "Owen"]
TRAITS = ["calm", "careful", "curious", "steady", "observant"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def spot_suits_reptile(reptile: ReptileCfg, spot: SpotCfg) -> bool:
    return spot.warmth >= reptile.warmth_need and spot.moisture >= reptile.moisture_need


def steam_reaches_spot(steam: SteamCfg, spot: SpotCfg) -> bool:
    return steam.zone == spot.zone


def valid_combo(reptile: ReptileCfg, steam: SteamCfg, spot: SpotCfg) -> bool:
    return spot_suits_reptile(reptile, spot) and steam_reaches_spot(steam, spot)


def reveal_style(motive_id: str) -> str:
    return "gentle" if motive_id in {"protect_friend", "keep_comfy"} else "firm"


def _r_bad_hiding_place(world: World) -> list[str]:
    reptile = world.get("reptile")
    spot = world.get("spot")
    if reptile.attrs.get("hidden") != "yes":
        return []
    if reptile.attrs.get("spot_ok") == "yes":
        return []
    sig = ("stress", reptile.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    reptile.meters["stress"] += 1
    return ["__stress__"]


def _r_steam_clue(world: World) -> list[str]:
    reptile = world.get("reptile")
    spot = world.get("spot")
    steam = world.get("steam")
    if reptile.attrs.get("hidden") != "yes":
        return []
    if steam.attrs.get("reaches_spot") != "yes":
        return []
    sig = ("clue", spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spot.meters["damp"] += 1
    world.get("detective").memes["suspicion"] += 1
    return ["__clue__"]


def _r_guilt_rises(world: World) -> list[str]:
    culprit = world.get("culprit")
    detective = world.get("detective")
    if culprit.memes["lie"] < THRESHOLD or detective.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("guilt", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["guilt"] += 1
    culprit.memes["conflict"] += 1
    return ["__guilt__"]


CAUSAL_RULES = [
    Rule(name="bad_hiding_place", tag="physical", apply=_r_bad_hiding_place),
    Rule(name="steam_clue", tag="physical", apply=_r_steam_clue),
    Rule(name="guilt_rises", tag="moral", apply=_r_guilt_rises),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def predict_clue(world: World, spot_id: str) -> dict:
    sim = world.copy()
    sim.get("reptile").attrs["hidden"] = "yes"
    sim.get("spot").id = spot_id
    sim.get("spot").attrs["spot_id"] = spot_id
    propagate(sim, narrate=False)
    return {
        "damp": sim.get("spot").meters["damp"] >= THRESHOLD,
        "stress": sim.get("reptile").meters["stress"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, teacher: Entity, reptile_cfg: ReptileCfg, steam_cfg: SteamCfg) -> None:
    detective.memes["care"] += 1
    world.say(
        f"On winter fair morning, Room Fern smelled like wet soil and orange peels. "
        f"{teacher.label_word.capitalize()} had set {steam_cfg.phrase} {steam_cfg.place_text}, "
        f"and {steam_cfg.clue_text}."
    )
    world.say(
        f"The class pet was {reptile_cfg.phrase}, a gentle {reptile_cfg.species_word} "
        f"who liked to watch the children from a glass home."
    )
    world.say(
        f"{detective.id}, the most {detective.attrs['trait']} child in the room, loved checking that "
        f"every leaf, shell, and book was in its proper place."
    )


def setup_conflict(world: World, culprit: Entity, motive: MotiveCfg, detective: Entity) -> None:
    culprit.memes["desire"] += 1
    world.say(
        f"That day, the class was hanging posters for the fair, and everyone wanted something to go right. "
        f"{culprit.id} especially {motive.short}."
    )
    world.say(
        f"When the room grew busy and the steam drifted white through the air, nobody noticed one wrong choice being made."
    )
    world.facts["secret_line"] = motive.secret_line
    culprit.memes["lie"] += 1


def hide_reptile(world: World, spot_cfg: SpotCfg) -> None:
    reptile = world.get("reptile")
    spot = world.get("spot")
    reptile.attrs["hidden"] = "yes"
    reptile.attrs["spot_ok"] = "yes" if world.facts["spot_ok"] else "no"
    spot.attrs["used"] = "yes"
    propagate(world, narrate=False)
    world.say(
        f"A little later, when the class gathered by the tea cups and soup bowls, "
        f"{world.facts['teacher_name']} turned back to the terrarium and blinked. "
        f'"Children," {world.facts["teacher_title"]} said, "where is our {world.facts["reptile_label"]}?"'
    )
    detective.memes["alert"] = 1.0
    world.get("room").meters["worry"] += 1


def gather_suspects(world: World, detective: Entity, culprit: Entity, witness1: Entity, witness2: Entity) -> None:
    witness1.memes["nervous"] += 1
    witness2.memes["nervous"] += 1
    world.say(
        f"The room hushed at once. {witness1.id} looked at the fern shelf, {witness2.id} looked at the floor, "
        f"and {culprit.id} looked everywhere except the empty terrarium."
    )
    world.say(
        f"{detective.id} did not shout. {detective.pronoun().capitalize()} only listened, the way a real little detective would."
    )


def inspect_clue(world: World, steam_cfg: SteamCfg, spot_cfg: SpotCfg, detective: Entity) -> None:
    pred = predict_clue(world, "spot")
    world.facts["predicted_damp"] = pred["damp"]
    world.facts["predicted_stress"] = pred["stress"]
    if world.get("spot").meters["damp"] >= THRESHOLD:
        detective.memes["certainty"] += 1
        world.say(
            f"{detective.id} followed the path of the steam with careful eyes. "
            f"{spot_cfg.clue_line}"
        )
        world.say(
            f'"The steam touched something there," {detective.pronoun()} whispered. '
            f'"And only a hiding place near the {steam_cfg.label} would stay damp like that."'
        )
    else:
        world.say(
            f"{detective.id} checked the shelves anyway, but the air had left no useful drops behind."
        )
    if world.get("reptile").meters["stress"] >= THRESHOLD:
        world.say(
            f"{detective.pronoun().capitalize()} also noticed that the hiding place felt wrong for a small animal that needed warmth and comfort."
        )


def question_gently(world: World, detective: Entity, culprit: Entity, motive: MotiveCfg) -> None:
    mode = reveal_style(motive.id)
    if mode == "gentle":
        world.say(
            f'{detective.id} turned to {culprit.id}. "If someone was trying to help, they can still tell the truth now," '
            f'{detective.pronoun()} said softly.'
        )
    else:
        world.say(
            f'{detective.id} faced {culprit.id}. "The clue points to someone who knew exactly where to look," '
            f'{detective.pronoun()} said in a steady voice.'
        )
    if culprit.memes["guilt"] >= THRESHOLD:
        culprit.memes["honesty_pull"] += 1
        world.say(
            f"{culprit.id}'s shoulders folded in. The secret was pulling one way, and honesty was pulling the other."
        )


def confession(world: World, culprit: Entity, motive: MotiveCfg, spot_cfg: SpotCfg) -> None:
    culprit.memes["lie"] = 0.0
    culprit.memes["conflict"] = 0.0
    culprit.memes["relief"] += 1
    culprit.memes["honesty"] += 1
    world.facts["confessed"] = True
    world.say(
        f'At last {culprit.id} took a shaky breath. "{motive.confession_line}"'
    )
    world.say(
        f"{culprit.id} led everyone to {spot_cfg.phrase}, and there the little reptile was waiting."
    )


def return_and_repair(world: World, teacher: Entity, detective: Entity, culprit: Entity, motive: MotiveCfg, spot_cfg: SpotCfg) -> None:
    reptile = world.get("reptile")
    reptile.attrs["hidden"] = "no"
    reptile.meters["stress"] = 0.0
    world.get("room").meters["worry"] = 0.0
    world.get("room").memes["relief"] += 1
    teacher.memes["care"] += 1
    culprit.memes["belonging"] += 1
    detective.memes["justice"] += 1
    world.say(
        f"{teacher.label_word.capitalize()} checked the reptile first, then nodded with a calmer face. "
        f'"Thank you for telling the truth before this grew bigger," {teacher.pronoun()} said.'
    )
    world.say(
        f'"Next time," {teacher.pronoun()} added, "we help animals by asking, not by hiding." '
        f"{motive.lesson_line}"
    )
    world.say(
        f"{culprit.id} helped set the terrarium right again, and {detective.id} helped tuck a fresh leaf and a smooth stone back inside."
    )
    world.say(spot_cfg.ending_line)
    world.say(
        f"By the time the last curls of steam faded from the room, the mystery was solved, the class pet was safe, and honesty felt warmer than any secret."
    )


# ---------------------------------------------------------------------------
# Story driver
# ---------------------------------------------------------------------------
def tell(
    reptile_cfg: ReptileCfg,
    steam_cfg: SteamCfg,
    spot_cfg: SpotCfg,
    motive_cfg: MotiveCfg,
    detective_name: str = "Lina",
    detective_gender: str = "girl",
    culprit_name: str = "Ben",
    culprit_gender: str = "boy",
    witness1_name: str = "Maya",
    witness1_gender: str = "girl",
    witness2_name: str = "Theo",
    witness2_gender: str = "boy",
    teacher_type: str = "mother",
    detective_trait: str = "observant",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        attrs={"trait": detective_trait},
    ))
    culprit = world.add(Entity(
        id=culprit_name,
        kind="character",
        type=culprit_gender,
        role="culprit",
        attrs={},
    ))
    witness1 = world.add(Entity(
        id=witness1_name,
        kind="character",
        type=witness1_gender,
        role="witness",
        attrs={},
    ))
    witness2 = world.add(Entity(
        id=witness2_name,
        kind="character",
        type=witness2_gender,
        role="witness",
        attrs={},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
        attrs={},
    ))
    reptile = world.add(Entity(
        id="reptile",
        kind="thing",
        type="animal",
        label=reptile_cfg.label,
        role="reptile",
        attrs={"hidden": "no", "spot_ok": "yes"},
    ))
    steam = world.add(Entity(
        id="steam",
        kind="thing",
        type="steam_source",
        label=steam_cfg.label,
        role="steam",
        attrs={"reaches_spot": "yes" if steam_reaches_spot(steam_cfg, spot_cfg) else "no"},
    ))
    spot = world.add(Entity(
        id="spot",
        kind="thing",
        type="hiding_spot",
        label=spot_cfg.label,
        role="spot",
        attrs={"used": "no"},
    ))
    world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="greenhouse classroom",
        role="room",
        attrs={},
    ))

    world.facts.update(
        reptile_cfg=reptile_cfg,
        steam_cfg=steam_cfg,
        spot_cfg=spot_cfg,
        motive_cfg=motive_cfg,
        detective=detective,
        culprit=culprit,
        witness1=witness1,
        witness2=witness2,
        teacher=teacher,
        teacher_name=teacher.label_word.capitalize(),
        teacher_title=teacher.label_word.capitalize(),
        reptile_label=reptile_cfg.label,
        spot_ok=spot_suits_reptile(reptile_cfg, spot_cfg),
        confessed=False,
    )

    introduce(world, detective, teacher, reptile_cfg, steam_cfg)
    world.para()
    setup_conflict(world, culprit, motive_cfg, detective)
    hide_reptile(world, spot_cfg)
    gather_suspects(world, detective, culprit, witness1, witness2)
    world.para()
    inspect_clue(world, steam_cfg, spot_cfg, detective)
    question_gently(world, detective, culprit, motive_cfg)
    confession(world, culprit, motive_cfg, spot_cfg)
    world.para()
    return_and_repair(world, teacher, detective, culprit, motive_cfg, spot_cfg)
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    reptile: str
    steam: str
    spot: str
    motive: str
    detective: str
    detective_gender: str
    culprit: str
    culprit_gender: str
    witness1: str
    witness1_gender: str
    witness2: str
    witness2_gender: str
    teacher: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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
    "reptile": [(
        "What is a reptile?",
        "A reptile is an animal like a turtle, lizard, or snake. Many reptiles need the right warmth and moisture to stay comfortable."
    )],
    "steam": [(
        "What is steam?",
        "Steam is warm water vapor rising into the air. When it touches something cooler, it can turn into tiny drops."
    )],
    "honesty": [(
        "Why is honesty important in a mystery?",
        "Honesty helps people solve problems faster and keeps others from worrying. A secret can make a small mistake feel much bigger."
    )],
    "humidifier": [(
        "What does a humidifier do?",
        "A humidifier puts moisture into the air. Some animals and plants are more comfortable when the air is not too dry."
    )],
    "tea": [(
        "Why does a kettle make steam?",
        "A kettle heats water until some of it turns into steam. That warm vapor rises up above the spout."
    )],
    "soup": [(
        "Why does hot soup make steam?",
        "Hot soup warms the water inside it until some rises as steam. You can often see it curl over the pot."
    )],
}

KNOWLEDGE_ORDER = ["reptile", "steam", "honesty", "humidifier", "tea", "soup"]


def generation_prompts(world: World) -> list[str]:
    reptile_cfg = world.facts["reptile_cfg"]
    steam_cfg = world.facts["steam_cfg"]
    motive_cfg = world.facts["motive_cfg"]
    detective = world.facts["detective"]
    culprit = world.facts["culprit"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "reptile" and "steam".',
        f"Tell a classroom mystery where {detective.id} notices a clue made by {steam_cfg.label} and solves the case of a missing {reptile_cfg.label}.",
        f"Write a short mystery about honesty, where {culprit.id} {motive_cfg.short} and must choose between keeping a secret and telling the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    reptile_cfg = world.facts["reptile_cfg"]
    steam_cfg = world.facts["steam_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    motive_cfg = world.facts["motive_cfg"]
    detective = world.facts["detective"]
    culprit = world.facts["culprit"]
    teacher = world.facts["teacher"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that the class {reptile_cfg.label} had disappeared from its glass home. Everyone in the room worried because no one knew where the little reptile had gone."
        ),
        (
            f"How did {detective.id} find the clue?",
            f"{detective.id} followed the path of the steam and noticed damp drops near {spot_cfg.label}. Those drops mattered because the hiding place was close enough for the steam to touch."
        ),
        (
            f"Why did {culprit.id} hide the {reptile_cfg.label}?",
            f"{culprit.id} hid it because {culprit.pronoun('subject')} {motive_cfg.short}. The problem was not only moving the animal, but also keeping it a secret while everyone worried."
        ),
        (
            f"Why was honesty important at the end?",
            f"Honesty mattered because the class could only help the reptile once the truth was spoken. When {culprit.id} confessed, the worry ended and the room could be set right again."
        ),
    ]
    if world.facts.get("confessed"):
        qa.append((
            f"What did {teacher.label_word} say after the mystery was solved?",
            f"{teacher.label_word.capitalize()} thanked {culprit.id} for telling the truth before the problem grew bigger. {teacher.pronoun().capitalize()} also explained that helping animals means asking first, not hiding them away."
        ))
    if not world.facts["spot_ok"]:
        qa.append((
            f"Why was {spot_cfg.label} not a good place for the {reptile_cfg.label}?",
            f"It did not match what that little reptile needed for comfort. That mattered because the hiding place could make the animal feel stressed instead of safe."
        ))
    else:
        qa.append((
            f"Was {spot_cfg.label} a comfortable hiding place?",
            f"It was warm and suitable enough for that reptile, but it was still the wrong place because nobody knew the animal was there. A safe place should also be honest and supervised."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"reptile", "steam", "honesty"} | set(world.facts["steam_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Valid combos / explanations
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for rid, reptile in REPTILES.items():
        for sid, steam in STEAM_SOURCES.items():
            for pid, spot in SPOTS.items():
                if valid_combo(reptile, steam, spot):
                    combos.append((rid, sid, pid))
    return combos


def explain_rejection(reptile: ReptileCfg, steam: SteamCfg, spot: SpotCfg) -> str:
    if not steam_reaches_spot(steam, spot):
        return (
            f"(No story: the {steam.label} is too far from {spot.phrase} to leave the steam clue there. "
            f"A whodunit needs the damp clue to be plausible.)"
        )
    if not spot_suits_reptile(reptile, spot):
        return (
            f"(No story: {spot.phrase} does not fit what a {reptile.label} needs. "
            f"The hiding place must be believable for the reptile as well as useful for the mystery.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
spot_suitable(R,S) :- reptile(R), spot(S),
                      warmth_need(R,Wn), spot_warmth(S,Ws), Ws >= Wn,
                      moisture_need(R,Mn), spot_moisture(S,Ms), Ms >= Mn.

clue_reaches(St,S) :- steam(St), spot(S), steam_zone(St,Z), spot_zone(S,Z).

valid(R,St,S) :- reptile(R), steam(St), spot(S), spot_suitable(R,S), clue_reaches(St,S).

gentle(protect_friend).
gentle(keep_comfy).
firm(win_ribbon).

reveal_mode(M, gentle) :- motive(M), gentle(M).
reveal_mode(M, firm) :- motive(M), firm(M).

#show valid/3.
#show reveal_mode/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, reptile in REPTILES.items():
        lines.append(asp.fact("reptile", rid))
        lines.append(asp.fact("warmth_need", rid, reptile.warmth_need))
        lines.append(asp.fact("moisture_need", rid, reptile.moisture_need))
    for sid, steam in STEAM_SOURCES.items():
        lines.append(asp.fact("steam", sid))
        lines.append(asp.fact("steam_zone", sid, steam.zone))
    for pid, spot in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        lines.append(asp.fact("spot_zone", pid, spot.zone))
        lines.append(asp.fact("spot_warmth", pid, spot.warmth))
        lines.append(asp.fact("spot_moisture", pid, spot.moisture))
    for mid in MOTIVES:
        lines.append(asp.fact("motive", mid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_reveal_modes() -> dict[str, str]:
    import asp
    model = asp.one_model(asp_program())
    return {m: mode for (m, mode) in asp.atoms(model, "reveal_mode")}


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

    py_modes = {mid: reveal_style(mid) for mid in MOTIVES}
    clingo_modes = asp_reveal_modes()
    if py_modes == clingo_modes:
        print("OK: reveal modes match motive logic.")
    else:
        rc = 1
        print(f"MISMATCH in reveal modes: python={py_modes} clingo={clingo_modes}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if "steam" not in sample.story.lower() or "reptile" not in sample.story.lower():
                raise StoryError("required words missing from rendered story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle whodunit about a missing class reptile, a steam clue, and choosing honesty."
    )
    ap.add_argument("--reptile", choices=sorted(REPTILES))
    ap.add_argument("--steam", choices=sorted(STEAM_SOURCES))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--motive", choices=sorted(MOTIVES))
    ap.add_argument("--teacher", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    if not choices:
        raise StoryError("Ran out of distinct names while building a story.")
    return rng.choice(choices)


def _pick_child(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = _pick_name(rng, gender, avoid)
    return name, gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reptile and args.steam and args.spot:
        reptile = REPTILES[args.reptile]
        steam = STEAM_SOURCES[args.steam]
        spot = SPOTS[args.spot]
        if not valid_combo(reptile, steam, spot):
            raise StoryError(explain_rejection(reptile, steam, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.reptile is None or combo[0] == args.reptile)
        and (args.steam is None or combo[1] == args.steam)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    reptile_id, steam_id, spot_id = rng.choice(sorted(combos))
    motive_id = args.motive or rng.choice(sorted(MOTIVES))
    teacher = args.teacher or rng.choice(["mother", "father"])

    used: set[str] = set()
    detective_gender = rng.choice(["girl", "boy"])
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)

    culprit_gender = rng.choice(["girl", "boy"])
    culprit = _pick_name(rng, culprit_gender, used)
    used.add(culprit)

    witness1_name, witness1_gender = _pick_child(rng, used)
    used.add(witness1_name)
    witness2_name, witness2_gender = _pick_child(rng, used)
    used.add(witness2_name)

    trait = rng.choice(TRAITS)
    return StoryParams(
        reptile=reptile_id,
        steam=steam_id,
        spot=spot_id,
        motive=motive_id,
        detective=detective,
        detective_gender=detective_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        witness1=witness1_name,
        witness1_gender=witness1_gender,
        witness2=witness2_name,
        witness2_gender=witness2_gender,
        teacher=teacher,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        reptile_cfg = REPTILES[params.reptile]
        steam_cfg = STEAM_SOURCES[params.steam]
        spot_cfg = SPOTS[params.spot]
        motive_cfg = MOTIVES[params.motive]
    except KeyError as err:
        raise StoryError(f"(Unknown story option: {err.args[0]})") from None

    if not valid_combo(reptile_cfg, steam_cfg, spot_cfg):
        raise StoryError(explain_rejection(reptile_cfg, steam_cfg, spot_cfg))

    world = tell(
        reptile_cfg=reptile_cfg,
        steam_cfg=steam_cfg,
        spot_cfg=spot_cfg,
        motive_cfg=motive_cfg,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        witness1_name=params.witness1,
        witness1_gender=params.witness1_gender,
        witness2_name=params.witness2,
        witness2_gender=params.witness2_gender,
        teacher_type=params.teacher,
        detective_trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


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
        reptile="gecko",
        steam="kettle",
        spot="seed_drawer",
        motive="win_ribbon",
        detective="Lina",
        detective_gender="girl",
        culprit="Ben",
        culprit_gender="boy",
        witness1="Maya",
        witness1_gender="girl",
        witness2="Theo",
        witness2_gender="boy",
        teacher="mother",
        trait="observant",
    ),
    StoryParams(
        reptile="iguana",
        steam="humidifier",
        spot="fern_crate",
        motive="protect_friend",
        detective="Ruby",
        detective_gender="girl",
        culprit="Milo",
        culprit_gender="boy",
        witness1="Nora",
        witness1_gender="girl",
        witness2="Finn",
        witness2_gender="boy",
        teacher="father",
        trait="steady",
    ),
    StoryParams(
        reptile="gecko",
        steam="humidifier",
        spot="sunny_rock",
        motive="keep_comfy",
        detective="Iris",
        detective_gender="girl",
        culprit="Owen",
        culprit_gender="boy",
        witness1="Ella",
        witness1_gender="girl",
        witness2="Sam",
        witness2_gender="boy",
        teacher="mother",
        trait="calm",
    ),
    StoryParams(
        reptile="turtle",
        steam="humidifier",
        spot="fern_crate",
        motive="protect_friend",
        detective="Zoe",
        detective_gender="girl",
        culprit="Eli",
        culprit_gender="boy",
        witness1="Tessa",
        witness1_gender="girl",
        witness2="Noah",
        witness2_gender="boy",
        teacher="father",
        trait="careful",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (reptile, steam, spot) combos:\n")
        for reptile, steam, spot in combos:
            print(f"  {reptile:8} {steam:10} {spot}")
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
            header = f"### {p.reptile} with {p.steam} at {p.spot} ({p.motive})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
