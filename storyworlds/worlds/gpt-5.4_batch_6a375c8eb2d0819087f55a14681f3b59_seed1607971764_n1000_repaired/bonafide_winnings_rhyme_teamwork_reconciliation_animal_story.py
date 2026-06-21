#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py
=================================================================================================

A standalone storyworld for a small animal-story domain built from the seed:

    words: bonafide, winnings
    features: rhyme, teamwork, reconciliation
    style: animal story

Premise
-------
Two little animal friends win some fair winnings in a rhyme contest. On the way
home, their container is a poor match for the path ahead. One friend makes a
bonafide grab for the bag to protect it, but the other misreads that move as
selfishness. The container slips, the winnings wobble free, and the pair must
work together with the right fix. In the end they reconcile, share what they
saved, and the closing image proves they are speaking kindly and rhyming
together again.

Run it
------
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py --setting brook_bridge --container paper_sack
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py --fix dash_faster
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/bonafide_winnings_rhyme_teamwork_reconciliation_animal_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def pair_word(self) -> str:
        return self.type
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class RhymeTheme:
    id: str
    fair_name: str
    stage_label: str
    couplet_a: str
    couplet_b: str
    closing_a: str
    closing_b: str
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
class WinningsCfg:
    id: str
    label: str
    phrase: str
    loose_word: str
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
class Setting:
    id: str
    label: str
    scene: str
    obstacle: str
    path_text: str
    wobble_text: str
    severity: int
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
class ContainerCfg:
    id: str
    label: str
    phrase: str
    vulnerable: set[str] = field(default_factory=set)
    spill_word: str = "tipped"
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
class Fix:
    id: str
    sense: int
    power: int
    handles: set[str] = field(default_factory=set)
    needs_two: bool = True
    prep: str = ""
    action: str = ""
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


def _r_spill(world: World) -> list[str]:
    container = world.get("container")
    winnings = world.get("winnings")
    path = world.get("path")
    if container.meters["strain"] < THRESHOLD or path.meters["hazard"] < THRESHOLD:
        return []
    sig = ("spill", world.facts["setting"].obstacle)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    container.meters["spilled"] += 1
    winnings.meters["scattered"] += 1
    for kid in world.characters():
        kid.memes["fear"] += 1
    return ["__spill__"]


def _r_hurt(world: World) -> list[str]:
    left = world.get("left")
    right = world.get("right")
    if left.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("hurt", left.id, right.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    left.memes["hurt"] += 1
    right.memes["hurt"] += 1
    left.memes["trust"] -= 1
    return ["__hurt__"]


def _r_reconcile(world: World) -> list[str]:
    left = world.get("left")
    right = world.get("right")
    winnings = world.get("winnings")
    if winnings.meters["saved"] < THRESHOLD:
        return []
    if left.memes["apology"] < THRESHOLD and right.memes["apology"] < THRESHOLD:
        return []
    sig = ("reconcile", left.id, right.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    left.memes["trust"] += 2
    right.memes["trust"] += 2
    left.memes["relief"] += 1
    right.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="hurt", tag="social", apply=_r_hurt),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(setting: Setting, container: ContainerCfg) -> bool:
    return setting.obstacle in container.vulnerable


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def compatible_fixes(setting: Setting) -> list[Fix]:
    return [f for f in sensible_fixes() if setting.obstacle in f.handles]


def severity_of(setting: Setting, delay: int) -> int:
    return setting.severity + delay


def is_contained(fix: Fix, setting: Setting, delay: int) -> bool:
    if setting.obstacle not in fix.handles:
        return False
    return fix.power >= severity_of(setting, delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("container").meters["strain"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("container").meters["spilled"] >= THRESHOLD,
        "scattered": sim.get("winnings").meters["scattered"] >= THRESHOLD,
    }


def opening(world: World, left: Entity, right: Entity, rhyme: RhymeTheme,
            winnings_cfg: WinningsCfg) -> None:
    left.memes["joy"] += 1
    right.memes["joy"] += 1
    world.say(
        f"At {rhyme.fair_name}, {left.id} the {left.type} and {right.id} the {right.type} "
        f"stood on {rhyme.stage_label} with their whiskers and paws all ready."
    )
    world.say(
        f'Together they chanted, "{rhyme.couplet_a}" and "{rhyme.couplet_b}"'
    )
    world.say(
        f"The crowd clapped for the neat little rhyme, and the judge handed them "
        f"{winnings_cfg.phrase} as their bonafide winnings."
    )


def start_home(world: World, left: Entity, right: Entity, setting: Setting,
               container_cfg: ContainerCfg, winnings_cfg: WinningsCfg) -> None:
    world.say(
        f"They tucked the {winnings_cfg.label} into {container_cfg.phrase} and started "
        f"home along {setting.path_text}. {setting.scene}"
    )


def warning(world: World, left: Entity, right: Entity, setting: Setting,
            container_cfg: ContainerCfg) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_spill"] = pred["spill"]
    right.memes["care"] += 1
    world.say(
        f"{right.id} watched the {container_cfg.label} and whispered, "
        f'"Hold the sides with me, {left.id}. {setting.wobble_text}"'
    )


def misunderstanding(world: World, left: Entity, right: Entity,
                     winnings_cfg: WinningsCfg) -> None:
    left.memes["suspicion"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {right.id} reached for the bag, {left.id} hugged it close and frowned."
    )
    world.say(
        f'"These are our winnings," {left.id} said. "Do not snatch extra {winnings_cfg.loose_word}."'
    )


def reveal_good_intent(world: World, left: Entity, right: Entity, setting: Setting) -> None:
    right.memes["honesty"] += 1
    world.say(
        f'{right.id} blinked in surprise. "I was not grabbing more," {right.pronoun()} said. '
        f'"I only saw {setting.wobble_text.lower()}."'
    )


def accident(world: World, setting: Setting, container_cfg: ContainerCfg,
             winnings_cfg: WinningsCfg) -> None:
    world.get("path").meters["hazard"] += 1
    world.get("container").meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then the {container_cfg.label} {container_cfg.spill_word}, and the "
        f"{winnings_cfg.label} began to scatter."
    )


def teamwork_save(world: World, left: Entity, right: Entity, fix: Fix,
                  winnings_cfg: WinningsCfg) -> None:
    left.memes["cooperation"] += 1
    right.memes["cooperation"] += 1
    world.get("winnings").meters["saved"] += 1
    world.get("container").meters["spilled"] = 0.0
    world.say(
        f"{left.id} and {right.id} stopped arguing at once and {fix.action}."
    )
    world.say(
        f"Little by little, they kept the {winnings_cfg.label} safe together."
    )


def teamwork_partial(world: World, left: Entity, right: Entity, fix: Fix,
                     winnings_cfg: WinningsCfg, setting: Setting) -> None:
    left.memes["cooperation"] += 1
    right.memes["cooperation"] += 1
    world.get("winnings").meters["saved"] += 1
    world.get("winnings").meters["lost"] += 1
    world.say(
        f"{left.id} and {right.id} tried to {fix.action}, but {setting.wobble_text.lower()} was stronger than they hoped."
    )
    world.say(
        f"They saved most of the {winnings_cfg.label}, though a few {winnings_cfg.loose_word} bounced away into the grass."
    )


def apology_and_share(world: World, left: Entity, right: Entity, winnings_cfg: WinningsCfg,
                      rhyme: RhymeTheme, outcome: str) -> None:
    left.memes["apology"] += 1
    right.memes["apology"] += 1
    propagate(world, narrate=False)
    left.memes["joy"] += 1
    right.memes["joy"] += 1
    if outcome == "saved_all":
        world.say(
            f'{left.id} lowered {left.pronoun("possessive")} ears. "I am sorry," {left.pronoun()} said. '
            f'"Your grab was bonafide help, not greed."'
        )
        world.say(
            f'{right.id} smiled and nudged the bag back to the middle. '
            f'"They are our winnings," {right.pronoun()} said. "We share them side by side."'
        )
    else:
        world.say(
            f'{left.id} looked at the grass, then at {right.id}. "I am sorry," {left.pronoun()} said. '
            f'"Your grab was bonafide help, and I was wrong to snap."'
        )
        world.say(
            f'{right.id} gave a small nod. "We still saved plenty because we worked as a team," '
            f'{right.pronoun()} said.'
        )
    world.say(
        f'Together they chirped, "{rhyme.closing_a}" and "{rhyme.closing_b}"'
    )
    if outcome == "saved_all":
        world.say(
            f"Then they sat under a fern and shared every bit of the {winnings_cfg.label} fairly."
        )
    else:
        world.say(
            f"Then they sat under a fern, counted the pieces they had saved, and shared them fairly anyway."
        )


def tell(rhyme: RhymeTheme, winnings_cfg: WinningsCfg, setting: Setting,
         container_cfg: ContainerCfg, fix: Fix, left_name: str, left_type: str,
         left_gender: str, right_name: str, right_type: str, right_gender: str,
         delay: int = 0) -> World:
    world = World()
    left = world.add(Entity(
        id=left_name,
        kind="character",
        type=left_type,
        role="left",
        attrs={"gender": left_gender},
    ))
    right = world.add(Entity(
        id=right_name,
        kind="character",
        type=right_type,
        role="right",
        attrs={"gender": right_gender},
    ))
    world.add(Entity(id="winnings", type="winnings", label=winnings_cfg.label))
    world.add(Entity(id="container", type="container", label=container_cfg.label))
    world.add(Entity(id="path", type="path", label=setting.label))

    left.memes["trust"] = 3
    right.memes["trust"] = 3
    world.facts["predicted_spill"] = False
    world.facts["delay"] = delay

    opening(world, left, right, rhyme, winnings_cfg)
    start_home(world, left, right, setting, container_cfg, winnings_cfg)

    world.para()
    warning(world, left, right, setting, container_cfg)
    misunderstanding(world, left, right, winnings_cfg)
    reveal_good_intent(world, left, right, setting)

    if delay > 0:
        world.say(
            f"But they wasted a few worried breaths before listening to each other."
        )

    world.para()
    accident(world, setting, container_cfg, winnings_cfg)

    outcome = "saved_all" if is_contained(fix, setting, delay) else "lost_some"
    world.para()
    if outcome == "saved_all":
        teamwork_save(world, left, right, fix, winnings_cfg)
    else:
        teamwork_partial(world, left, right, fix, winnings_cfg, setting)

    world.para()
    apology_and_share(world, left, right, winnings_cfg, rhyme, outcome)

    world.facts.update(
        rhyme=rhyme,
        winnings_cfg=winnings_cfg,
        setting=setting,
        container_cfg=container_cfg,
        fix=fix,
        left=left,
        right=right,
        outcome=outcome,
        spilled=world.get("winnings").meters["scattered"] >= THRESHOLD,
        saved=world.get("winnings").meters["saved"] >= THRESHOLD,
        lost_some=world.get("winnings").meters["lost"] >= THRESHOLD,
    )
    return world


RHYMES = {
    "moon_spoon": RhymeTheme(
        id="moon_spoon",
        fair_name="the lantern fair",
        stage_label="the mossy rhyme stump",
        couplet_a="Moon so round, spoon so bright,",
        couplet_b="sing a silver nibble of night!",
        closing_a="Friend by friend, paw by paw,",
        closing_b="sharing beats selfish claws.",
        tags={"rhyme"},
    ),
    "clover_over": RhymeTheme(
        id="clover_over",
        fair_name="the clover fair",
        stage_label="the little root stage",
        couplet_a="Clover low and clover high,",
        couplet_b="laugh together, do not sigh!",
        closing_a="If hearts bend over what went wrong,",
        closing_b="friends can mend and finish strong.",
        tags={"rhyme"},
    ),
    "rain_train": RhymeTheme(
        id="rain_train",
        fair_name="the puddle fair",
        stage_label="the painted cart stage",
        couplet_a="Rain on a train goes tap-tap-two,",
        couplet_b="best of all when I rhyme with you!",
        closing_a="When trouble came and feelings stung,",
        closing_b="teamwork fixed our rhyme and tongue.",
        tags={"rhyme"},
    ),
}

WINNINGS = {
    "berry_buns": WinningsCfg(
        id="berry_buns",
        label="berry buns",
        phrase="a basket of berry buns",
        loose_word="buns",
        tags={"berries", "sharing"},
    ),
    "acorn_cakes": WinningsCfg(
        id="acorn_cakes",
        label="acorn cakes",
        phrase="a stack of acorn cakes",
        loose_word="cakes",
        tags={"acorns", "sharing"},
    ),
    "honey_drops": WinningsCfg(
        id="honey_drops",
        label="honey drops",
        phrase="a pouch of honey drops",
        loose_word="drops",
        tags={"honey", "sharing"},
    ),
}

SETTINGS = {
    "meadow_breeze": Setting(
        id="meadow_breeze",
        label="the meadow path",
        scene="Warm grass leaned one way, then the other.",
        obstacle="breeze",
        path_text="the meadow path where the wind liked to play tricks",
        wobble_text="the breeze could whisk the top right open",
        severity=1,
        tags={"wind"},
    ),
    "brook_bridge": Setting(
        id="brook_bridge",
        label="the brook bridge",
        scene="Below them, the water made quick silver sounds.",
        obstacle="bridge_bump",
        path_text="the little bridge over the brook",
        wobble_text="the planks could bump the bag right out of their paws",
        severity=2,
        tags={"bridge", "water"},
    ),
    "hill_path": Setting(
        id="hill_path",
        label="the hill path",
        scene="Pebbles rolled and clicked under every careful step.",
        obstacle="steep_hill",
        path_text="the steep hill path beside the blackberry hedge",
        wobble_text="one slip could send the bag skidding downhill",
        severity=2,
        tags={"hill"},
    ),
}

CONTAINERS = {
    "paper_sack": ContainerCfg(
        id="paper_sack",
        label="paper sack",
        phrase="a crinkly paper sack",
        vulnerable={"breeze", "bridge_bump"},
        spill_word="flapped and tipped",
        tags={"paper_sack"},
    ),
    "leaf_tray": ContainerCfg(
        id="leaf_tray",
        label="leaf tray",
        phrase="a broad leaf tray",
        vulnerable={"breeze", "steep_hill"},
        spill_word="buckled and bent",
        tags={"leaf_tray"},
    ),
    "bark_basket": ContainerCfg(
        id="bark_basket",
        label="bark basket",
        phrase="a small bark basket",
        vulnerable={"bridge_bump", "steep_hill"},
        spill_word="lurched sideways",
        tags={"bark_basket"},
    ),
    "lidded_tin": ContainerCfg(
        id="lidded_tin",
        label="lidded tin",
        phrase="a snug lidded tin",
        vulnerable=set(),
        spill_word="rattled",
        tags={"tin"},
    ),
}

FIXES = {
    "clip_top": Fix(
        id="clip_top",
        sense=3,
        power=1,
        handles={"breeze"},
        needs_two=True,
        prep="pin the top shut with a clover clip",
        action="pin the top shut with a clover clip and hold the bottom steady together",
        fail="tried to pin the top shut, but the trouble was too rough for that small clip",
        qa_text="pinned the top shut with a clover clip and held the bag steady together",
        tags={"clip", "teamwork"},
    ),
    "carry_pole": Fix(
        id="carry_pole",
        sense=3,
        power=3,
        handles={"bridge_bump", "steep_hill"},
        needs_two=True,
        prep="slide the bag onto a little carrying pole between them",
        action="slide the bag onto a little carrying pole and walk in step",
        fail="tried to balance the bag on a carrying pole, but it still jolted too hard",
        qa_text="slid the bag onto a carrying pole and walked in step",
        tags={"pole", "teamwork"},
    ),
    "vine_tie": Fix(
        id="vine_tie",
        sense=2,
        power=2,
        handles={"bridge_bump", "steep_hill"},
        needs_two=True,
        prep="wrap a vine around the middle and carry the bundle together",
        action="wrap a vine around the middle and carry the bundle together",
        fail="wrapped a vine around the bundle, but some pieces still slipped free",
        qa_text="wrapped a vine around the bundle and carried it together",
        tags={"vine", "teamwork"},
    ),
    "dash_faster": Fix(
        id="dash_faster",
        sense=1,
        power=0,
        handles=set(),
        needs_two=False,
        prep="run faster and hope for the best",
        action="run faster and hope for the best",
        fail="ran faster, which only made the wobbling worse",
        qa_text="ran faster",
        tags={"bad_idea"},
    ),
}


GIRL_ANIMALS = [
    ("Pip", "rabbit"),
    ("Dot", "mouse"),
    ("Mimi", "squirrel"),
    ("Tansy", "fox"),
    ("Lulu", "otter"),
]
BOY_ANIMALS = [
    ("Moss", "badger"),
    ("Nip", "mouse"),
    ("Ollie", "otter"),
    ("Bram", "beaver"),
    ("Rory", "rabbit"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for container_id, container in CONTAINERS.items():
            if not hazard_at_risk(setting, container):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and setting.obstacle in fix.handles:
                    combos.append((setting_id, container_id, fix_id))
    return sorted(combos)


@dataclass
class StoryParams:
    rhyme: str
    winnings: str
    setting: str
    container: str
    fix: str
    left_name: str
    left_type: str
    left_gender: str
    right_name: str
    right_type: str
    right_gender: str
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
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words end with the same kind of sound, like moon and spoon. Rhymes are fun to say because they sound like they belong together."
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting more than one person enjoy something fairly. It helps friends feel included and cared for."
    )],
    "wind": [(
        "Why can wind make a bag wobble?",
        "Wind pushes on light things and can flap them around. That is why a light bag may tip or open on a breezy path."
    )],
    "bridge": [(
        "Why is a bumpy bridge hard to walk on?",
        "A bumpy bridge can jiggle what you are carrying. If your steps are uneven, a bag may bounce and spill."
    )],
    "water": [(
        "What is a brook?",
        "A brook is a small stream of water that moves along the ground. It can sound quick and shiny as it runs."
    )],
    "hill": [(
        "Why can things roll down a hill?",
        "A hill slopes downward, so loose things can roll when gravity pulls them. That is why careful steps matter on a steep path."
    )],
    "clip": [(
        "What does a clip do?",
        "A clip pinches two sides together so they stay shut. It can help hold a light bag closed."
    )],
    "pole": [(
        "Why does carrying something on a pole help?",
        "A pole lets two friends share the weight from both sides. When they walk in step, the load stays steadier."
    )],
    "vine": [(
        "How can a vine help hold something?",
        "A vine can act like a soft tie around a bundle. It keeps parts from sliding apart while you carry them."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people help each other do one job together. A hard task often becomes easier when everyone does a part."
    )],
}
KNOWLEDGE_ORDER = [
    "rhyme", "sharing", "wind", "bridge", "water", "hill", "clip", "pole", "vine", "teamwork"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    left = f["left"]
    right = f["right"]
    rhyme = f["rhyme"]
    winnings_cfg = f["winnings_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    if outcome == "saved_all":
        return [
            f'Write an animal story for a 3-to-5-year-old that includes the words "bonafide" and "winnings". Two friends win {winnings_cfg.label} in a rhyme contest and save them through teamwork.',
            f"Tell a gentle forest-fair story where {left.id} the {left.type} and {right.id} the {right.type} misunderstand each other on {setting.label}, then reconcile and share their winnings.",
            f'Write a child-friendly story with little rhyming lines, a bonafide misunderstanding, teamwork, and a happy reconciliation at the end.',
        ]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "bonafide" and "winnings". Two friends win {winnings_cfg.label} in a rhyme contest, save most of them through teamwork, and make up after an argument.',
        f"Tell a gentle but slightly oopsie story where {left.id} and {right.id} argue on {setting.label}, then reconcile after working together.",
        f'Write a child-friendly story with rhyme, teamwork, and reconciliation where not everything goes perfectly, but the friends end by sharing fairly.',
    ]


def pair_noun(left: Entity, right: Entity) -> str:
    return f"a {left.type} and a {right.type}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    left = f["left"]
    right = f["right"]
    rhyme = f["rhyme"]
    winnings_cfg = f["winnings_cfg"]
    setting = f["setting"]
    container_cfg = f["container_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(left, right)}, {left.id} and {right.id}, who went to a fair and won {winnings_cfg.label}. The story follows what happened as they carried their winnings home together."
        ),
        (
            "How did they get the winnings?",
            f"They won them by saying a rhyme together on the fair stage. The opening rhyme shows they began as a team before the misunderstanding started."
        ),
        (
            f"Why did {left.id} think {right.id} was being selfish?",
            f"{left.id} saw {right.id} reach for the {container_cfg.label} and guessed {right.pronoun()} wanted extra {winnings_cfg.loose_word}. But that guess was wrong, because {right.id} was really trying to stop the bag from spilling."
        ),
        (
            "What made the problem happen on the path?",
            f"The trouble came from carrying the winnings in {container_cfg.phrase} along {setting.path_text}. That path made the container wobble, so the winnings began to scatter."
        ),
    ]
    if outcome == "saved_all":
        qa.append((
            "How did they save the winnings?",
            f"They {fix.qa_text}. Because they stopped arguing and worked in one rhythm, all of the winnings stayed safe."
        ))
        qa.append((
            "What does bonafide mean in this story?",
            f"Here, bonafide means real and honest. {right.id}'s grab for the bag was bonafide help, not a sneaky grab for more treats."
        ))
    else:
        qa.append((
            "Did they lose everything?",
            f"No. They worked together and saved most of the winnings, even though a few {winnings_cfg.loose_word} rolled away. The teamwork still mattered because it stopped a bigger loss."
        ))
        qa.append((
            "How did they reconcile after the argument?",
            f"{left.id} apologized for the unfair guess, and {right.id} accepted the apology. They shared what they had saved, which proves the friendship was mended and not just talked about."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the two friends sitting under a fern, speaking kindly again, and sharing the {winnings_cfg.label}. Their closing rhyme shows that the friendship sounded joined again as well."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["rhyme"].tags) | set(f["winnings_cfg"].tags) | set(f["setting"].tags) | set(f["fix"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        rhyme="moon_spoon",
        winnings="berry_buns",
        setting="meadow_breeze",
        container="paper_sack",
        fix="clip_top",
        left_name="Pip",
        left_type="rabbit",
        left_gender="girl",
        right_name="Moss",
        right_type="badger",
        right_gender="boy",
        delay=0,
    ),
    StoryParams(
        rhyme="clover_over",
        winnings="acorn_cakes",
        setting="brook_bridge",
        container="paper_sack",
        fix="vine_tie",
        left_name="Dot",
        left_type="mouse",
        left_gender="girl",
        right_name="Bram",
        right_type="beaver",
        right_gender="boy",
        delay=1,
    ),
    StoryParams(
        rhyme="rain_train",
        winnings="honey_drops",
        setting="hill_path",
        container="leaf_tray",
        fix="carry_pole",
        left_name="Lulu",
        left_type="otter",
        left_gender="girl",
        right_name="Rory",
        right_type="rabbit",
        right_gender="boy",
        delay=0,
    ),
    StoryParams(
        rhyme="moon_spoon",
        winnings="acorn_cakes",
        setting="brook_bridge",
        container="bark_basket",
        fix="carry_pole",
        left_name="Mimi",
        left_type="squirrel",
        left_gender="girl",
        right_name="Ollie",
        right_type="otter",
        right_gender="boy",
        delay=0,
    ),
    StoryParams(
        rhyme="clover_over",
        winnings="berry_buns",
        setting="hill_path",
        container="leaf_tray",
        fix="vine_tie",
        left_name="Tansy",
        left_type="fox",
        left_gender="girl",
        right_name="Nip",
        right_type="mouse",
        right_gender="boy",
        delay=1,
    ),
]


def explain_rejection(setting: Setting, container: ContainerCfg) -> str:
    return (
        f"(No story: {container.phrase} is not in real trouble on {setting.label}. "
        f"If the path would not make the container wobble or spill, there is no honest misunderstanding-and-teamwork problem to tell.)"
    )


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). A storyworld should prefer bonafide helpful fixes. "
        f"Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "saved_all" if is_contained(FIXES[params.fix], SETTINGS[params.setting], params.delay) else "lost_some"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, C) :- setting(S), container(C), obstacle(S, O), vulnerable(C, O).
sensible(F)  :- fix(F), sense(F, V), sense_min(M), V >= M.
compatible(S, F) :- setting(S), fix(F), obstacle(S, O), handles(F, O).
valid(S, C, F) :- hazard(S, C), sensible(F), compatible(S, F).

% --- outcome model ---------------------------------------------------------
severity(V + D) :- chosen_setting(S), base_severity(S, V), delay(D).
saved_all :- chosen_fix(F), chosen_setting(S), compatible(S, F),
             power(F, P), severity(Need), P >= Need.
lost_some :- not saved_all.
outcome(saved_all) :- saved_all.
outcome(lost_some) :- lost_some.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("obstacle", sid, setting.obstacle))
        lines.append(asp.fact("base_severity", sid, setting.severity))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        for obstacle in sorted(container.vulnerable):
            lines.append(asp.fact("vulnerable", cid, obstacle))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
        for obstacle in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, obstacle))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for wid in WINNINGS:
        lines.append(asp.fact("winnings", wid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two little animals win rhyme-contest winnings, misunderstand each other, then use teamwork and reconciliation to put things right."
    )
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--winnings", choices=WINNINGS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the friends spend fussing before they act")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (setting, container, fix) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_animal(rng: random.Random, gender: str, avoid_name: str = "") -> tuple[str, str]:
    pool = GIRL_ANIMALS if gender == "girl" else BOY_ANIMALS
    options = [item for item in pool if item[0] != avoid_name]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))
    if args.setting and args.container:
        setting = SETTINGS[args.setting]
        container = CONTAINERS[args.container]
        if not hazard_at_risk(setting, container):
            raise StoryError(explain_rejection(setting, container))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.container is None or combo[1] == args.container)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, container_id, fix_id = rng.choice(combos)
    rhyme_id = args.rhyme or rng.choice(sorted(RHYMES))
    winnings_id = args.winnings or rng.choice(sorted(WINNINGS))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    left_gender = rng.choice(["girl", "boy"])
    right_gender = "boy" if left_gender == "girl" else "girl"
    left_name, left_type = _pick_animal(rng, left_gender)
    right_name, right_type = _pick_animal(rng, right_gender, avoid_name=left_name)

    return StoryParams(
        rhyme=rhyme_id,
        winnings=winnings_id,
        setting=setting_id,
        container=container_id,
        fix=fix_id,
        left_name=left_name,
        left_type=left_type,
        left_gender=left_gender,
        right_name=right_name,
        right_type=right_type,
        right_gender=right_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme theme: {params.rhyme})")
    if params.winnings not in WINNINGS:
        raise StoryError(f"(Unknown winnings: {params.winnings})")
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    setting = SETTINGS[params.setting]
    container = CONTAINERS[params.container]
    fix = FIXES[params.fix]

    if not hazard_at_risk(setting, container):
        raise StoryError(explain_rejection(setting, container))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(params.fix))
    if setting.obstacle not in fix.handles:
        raise StoryError(
            f"(No story: the fix '{params.fix}' does not honestly address the trouble on {setting.label}.)"
        )

    world = tell(
        rhyme=RHYMES[params.rhyme],
        winnings_cfg=WINNINGS[params.winnings],
        setting=setting,
        container_cfg=container,
        fix=fix,
        left_name=params.left_name,
        left_type=params.left_type,
        left_gender=params.left_gender,
        right_name=params.right_name,
        right_type=params.right_type,
        right_gender=params.right_gender,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, container, fix) combos:\n")
        for setting, container, fix in combos:
            print(f"  {setting:14} {container:12} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.left_name} & {p.right_name}: {p.setting}, {p.container}, {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
