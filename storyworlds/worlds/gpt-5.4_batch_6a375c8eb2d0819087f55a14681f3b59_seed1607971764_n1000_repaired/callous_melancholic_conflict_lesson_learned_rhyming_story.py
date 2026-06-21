#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py
=======================================================================================

A standalone story world for a small rhyming tale about unkindness, hurt feelings,
and a lesson learned. A child laughs in a callous way when another child's fragile
creation is damaged. The hurt child turns melancholic, a grown-up names the harm,
and the teaser must choose whether to mend the mess quickly enough to mend the
friendship too.

This world models:
- typed entities with physical meters and emotional memes
- a state-driven conflict and repair arc
- a reasonableness gate over setting / creation / cause / amends combinations
- an inline ASP twin for parity checking
- three Q&A sets derived from world state, not by parsing the English story

Run it
------
    python storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py --place park --creation kite
    python storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/callous_melancholic_conflict_lesson_learned_rhyming_story.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "teacher": "teacher",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    causes: set[str] = field(default_factory=set)
    opening: str = ""
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
class CreationCfg:
    id: str
    label: str
    phrase: str
    material: str
    repair_window: int
    opening: str
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
class CauseCfg:
    id: str
    line: str
    damage: str
    works_on: set[str] = field(default_factory=set)
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
class AmendsCfg:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    gift_line: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_damage_hurts(world: World) -> list[str]:
    out: list[str] = []
    creation = world.get("creation")
    maker = world.get("maker")
    place = world.get("place")
    if creation.meters["damaged"] >= THRESHOLD:
        sig = ("damage_hurts", creation.id)
        if sig not in world.fired:
            world.fired.add(sig)
            maker.memes["sad"] += 1
            maker.memes["melancholy"] += 1
            place.meters["tension"] += 1
            out.append("__damage__")
    return out


def _r_mock_deepens(world: World) -> list[str]:
    out: list[str] = []
    teaser = world.get("teaser")
    maker = world.get("maker")
    place = world.get("place")
    if teaser.memes["mocked"] >= THRESHOLD and maker.memes["sad"] >= THRESHOLD:
        sig = ("mock_deepens", teaser.id)
        if sig not in world.fired:
            world.fired.add(sig)
            maker.memes["hurt"] += 1
            teaser.memes["callous"] += 1
            teaser.memes["distance"] += 1
            place.meters["tension"] += 1
            out.append("__mock__")
    return out


def _r_repair_soothes(world: World) -> list[str]:
    out: list[str] = []
    creation = world.get("creation")
    teaser = world.get("teaser")
    maker = world.get("maker")
    place = world.get("place")
    if creation.meters["restored"] >= THRESHOLD:
        sig = ("repair_soothes", creation.id)
        if sig not in world.fired:
            world.fired.add(sig)
            maker.memes["relief"] += 1
            maker.memes["sad"] = 0.0
            maker.memes["hurt"] = 0.0
            teaser.memes["guilt"] += 1
            teaser.memes["kindness"] += 1
            teaser.memes["distance"] = 0.0
            place.meters["tension"] = 0.0
            out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule(name="damage_hurts", tag="emotion", apply=_r_damage_hurts),
    Rule(name="mock_deepens", tag="emotion", apply=_r_mock_deepens),
    Rule(name="repair_soothes", tag="social", apply=_r_repair_soothes),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def can_happen(setting: Setting, creation: CreationCfg, cause: CauseCfg) -> bool:
    return creation.id in setting.affords and cause.id in setting.causes and creation.id in cause.works_on


def can_mend(creation: CreationCfg, amends: AmendsCfg) -> bool:
    return creation.material in amends.fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for creation_id, creation in CREATIONS.items():
            for cause_id, cause in CAUSES.items():
                if not can_happen(setting, creation, cause):
                    continue
                for amends_id, amends in AMENDS.items():
                    if can_mend(creation, amends):
                        combos.append((place_id, creation_id, cause_id, amends_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    creation = CREATIONS[params.creation]
    return "reconciled" if params.delay <= creation.repair_window else "lonely"


def explain_rejection(setting: Setting, creation: CreationCfg, cause: CauseCfg, amends: Optional[AmendsCfg]) -> str:
    if not can_happen(setting, creation, cause):
        return (
            f"(No story: {cause.id} is not a fitting way for {creation.label} to be damaged at "
            f"{setting.place}. Pick a cause and creation that truly belong together in that setting.)"
        )
    if amends is not None and not can_mend(creation, amends):
        return (
            f"(No story: {amends.label} does not really mend a {creation.material} {creation.label}. "
            f"The repair in this world must match the material of the broken thing.)"
        )
    return "(No story: that combination does not fit this little world.)"


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def _damage_creation(world: World) -> None:
    creation = world.get("creation")
    creation.meters["damaged"] += 1
    propagate(world, narrate=False)


def _restore_creation(world: World) -> None:
    creation = world.get("creation")
    creation.meters["restored"] += 1
    creation.meters["damaged"] = 0.0
    propagate(world, narrate=False)


def introduce(world: World, teaser: Entity, maker: Entity, creation_cfg: CreationCfg) -> None:
    for child in (teaser, maker):
        child.memes["play"] += 1
    world.say(
        f"In {world.setting.place}, beneath a patient sky, "
        f"{maker.id} worked with careful hands while {teaser.id} skipped nearby."
    )
    world.say(
        f"{maker.id} had made {creation_cfg.phrase}, and {creation_cfg.opening}."
    )


def warm_play(world: World, teaser: Entity, maker: Entity, creation_cfg: CreationCfg) -> None:
    world.say(
        f'They hummed a little playtime tune, both busy in the sun, '
        f'until one sharp turn of luck declared the peaceful game undone.'
    )


def accident(world: World, maker: Entity, cause: CauseCfg, creation_cfg: CreationCfg) -> None:
    _damage_creation(world)
    world.say(
        f"But then {cause.line}, and {cause.damage}."
    )
    world.say(
        f"{maker.id} stared in stunned surprise. Soon {maker.pronoun('subject')} looked "
        f"quite melancholic, with watery eyes."
    )


def mock(world: World, teaser: Entity, maker: Entity, creation_cfg: CreationCfg) -> None:
    teaser.memes["mocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Instead of helping, {teaser.id} gave a laugh too quick and callous. '
        f'"It was only {creation_cfg.label}," {teaser.pronoun("subject")} said, '
        f'"so why the fuss around us?"'
    )
    world.say(
        f"{maker.id} drew back a little step. The hurt sat heavy, cold, and soundless."
    )


def rebuke(world: World, helper: Entity, teaser: Entity, maker: Entity) -> None:
    helper.memes["care"] += 1
    teaser.memes["warning"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came close and spoke in tones both firm and kind: "
        f'"A broken thing can sting the heart. Be gentle with a friend in mind."'
    )
    world.say(
        f'"A laugh like that can deepen hurt and leave a lonely trace. '
        f'Kind hands can mend more than the mess; they also mend a face."'
    )


def reflect(world: World, teaser: Entity) -> None:
    teaser.memes["guilt"] += 1
    teaser.memes["pride"] = max(0.0, teaser.memes["pride"] - 1.0)
    world.say(
        f"Then quiet came to {teaser.id} at last, as if a bell had rung. "
        f"{teaser.pronoun('subject').capitalize()} heard how sharp the teasing sounded on "
        f"{teaser.pronoun('possessive')} own tongue."
    )


def prompt_delay(world: World, teaser: Entity, maker: Entity, delay: int) -> None:
    if delay <= 0:
        return
    if delay == 1:
        world.say(
            f"For one long minute {teaser.id} stood still, unsure what should be done, "
            f"while {maker.id} sat quietly apart and watched the game unspool and run."
        )
    else:
        world.say(
            f"Too long {teaser.id} lingered with folded arms and lowered head, "
            f"while the chance for quick repair grew small and all the bright cheer fled."
        )


def mend(world: World, teaser: Entity, maker: Entity, amends: AmendsCfg, creation_cfg: CreationCfg) -> None:
    _restore_creation(world)
    teaser.memes["apologized"] += 1
    maker.memes["forgiven"] += 1
    world.say(
        f"At last {teaser.id} knelt down and {amends.action}."
    )
    world.say(
        f'"I am sorry for my teasing too," {teaser.pronoun("subject")} said. '
        f'"I should have helped you first instead."'
    )


def bright_end(world: World, teaser: Entity, maker: Entity, helper: Entity, creation_cfg: CreationCfg, amends: AmendsCfg) -> None:
    world.say(
        f"{maker.id} looked up, then smiled a bit, and made a little place. "
        f"The hurt that darkened {maker.pronoun('possessive')} small face eased in the warmth of grace."
    )
    world.say(
        f"Soon side by side they played again with kinder hearts in view; "
        f"{amends.gift_line}, and the afternoon felt new."
    )
    world.say(
        f"From then on {teaser.id} remembered this whenever games turned wild: "
        f"do not be hard when someone aches; be tender, child to child."
    )


def lonely_end(world: World, teaser: Entity, maker: Entity, helper: Entity, creation_cfg: Creation_cfg | None = None) -> None:
    world.say(
        f"But by the time {teaser.id} shuffled near, the chance had drifted far. "
        f"{maker.id} had gone to sit beside {helper.label_word}, under the shade of a jar-bright star."
    )
    world.say(
        f"{teaser.id} whispered, \"I was wrong today.\" No game came skipping back. "
        f"{teaser.pronoun('subject').capitalize()} learned that callous words can leave a long and lonely track."
    )
    world.say(
        f"So {teaser.pronoun('subject')} walked home slower than before, with lesson deep and true: "
        f"when sorrow falls on someone else, kind help is what you do."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    creation_cfg: CreationCfg,
    cause: CauseCfg,
    amends: AmendsCfg,
    teaser_name: str = "Ben",
    teaser_gender: str = "boy",
    maker_name: str = "Lily",
    maker_gender: str = "girl",
    helper_type: str = "teacher",
    delay: int = 0,
) -> World:
    world = World(setting)

    teaser = world.add(Entity(
        id=teaser_name,
        kind="character",
        type=teaser_gender,
        role="teaser",
        label=teaser_name,
        traits=["quick", "proud"],
    ))
    maker = world.add(Entity(
        id=maker_name,
        kind="character",
        type=maker_gender,
        role="maker",
        label=maker_name,
        traits=["careful", "creative"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.place,
        tags={setting.id},
    ))
    creation = world.add(Entity(
        id="creation",
        kind="thing",
        type=creation_cfg.id,
        label=creation_cfg.label,
        tags=set(creation_cfg.tags),
        attrs={"material": creation_cfg.material},
    ))

    for ent in (teaser, maker, helper, place, creation):
        ent.meters["damaged"] += 0.0
        ent.meters["restored"] += 0.0
        ent.meters["tension"] += 0.0
        ent.memes["sad"] += 0.0
        ent.memes["hurt"] += 0.0
        ent.memes["melancholy"] += 0.0
        ent.memes["mocked"] += 0.0
        ent.memes["callous"] += 0.0
        ent.memes["guilt"] += 0.0
        ent.memes["kindness"] += 0.0
        ent.memes["warning"] += 0.0
        ent.memes["forgiven"] += 0.0
        ent.memes["play"] += 0.0
        ent.memes["apologized"] += 0.0
        ent.memes["pride"] += 0.0
        ent.memes["distance"] += 0.0

    teaser.memes["pride"] = 2.0

    world.facts.update(
        setting=setting,
        creation_cfg=creation_cfg,
        cause=cause,
        amends=amends,
        teaser=teaser,
        maker=maker,
        helper=helper,
        creation=creation,
        delay=delay,
        conflict=False,
        lesson=False,
    )

    introduce(world, teaser, maker, creation_cfg)
    warm_play(world, teaser, maker, creation_cfg)

    world.para()
    accident(world, maker, cause, creation_cfg)
    mock(world, teaser, maker, creation_cfg)
    rebuke(world, helper, teaser, maker)
    reflect(world, teaser)

    world.para()
    prompt_delay(world, teaser, maker, delay)

    outcome = "reconciled" if delay <= creation_cfg.repair_window else "lonely"
    if outcome == "reconciled":
        mend(world, teaser, maker, amends, creation_cfg)
        bright_end(world, teaser, maker, helper, creation_cfg, amends)
    else:
        lonely_end(world, teaser, maker, helper, creation_cfg)

    world.facts.update(
        conflict=teaser.memes["mocked"] >= THRESHOLD and maker.memes["melancholy"] >= 0.0,
        outcome=outcome,
        lesson=True,
        repaired=creation.meters["restored"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(
        id="park",
        place="the park",
        affords={"kite"},
        causes={"gust", "branch"},
        opening="its paper tail flashed blue and white, merry as a song in flight",
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        affords={"tower"},
        causes={"ball", "bump"},
        opening="its little windows stood in rows, a careful castle neat and bright",
    ),
    "sidewalk": Setting(
        id="sidewalk",
        place="the sidewalk",
        affords={"chalk"},
        causes={"sprinkler", "drizzle"},
        opening="its looping colors curled and shone, a rainbow road in morning light",
    ),
}

CREATIONS = {
    "kite": CreationCfg(
        id="kite",
        label="kite",
        phrase="a ribbon kite",
        material="paper",
        repair_window=1,
        opening="its paper tail flashed blue and white, merry as a song in flight",
        tags={"kite", "paper"},
    ),
    "tower": CreationCfg(
        id="tower",
        label="block tower",
        phrase="a block tower",
        material="blocks",
        repair_window=2,
        opening="its little windows stood in rows, a careful castle neat and bright",
        tags={"blocks", "tower"},
    ),
    "chalk": CreationCfg(
        id="chalk",
        label="chalk picture",
        phrase="a chalk picture",
        material="chalk",
        repair_window=0,
        opening="its looping colors curled and shone, a rainbow road in morning light",
        tags={"chalk"},
    ),
}

CAUSES = {
    "gust": CauseCfg(
        id="gust",
        line="a gust came dancing through the trees",
        damage="the kite dipped low, tore at the edge, and would not ride the breeze",
        works_on={"kite"},
        tags={"wind"},
    ),
    "branch": CauseCfg(
        id="branch",
        line="the string snagged high upon a branch",
        damage="the kite came down with crumpled wings and one bright corner bent",
        works_on={"kite"},
        tags={"tree", "wind"},
    ),
    "ball": CauseCfg(
        id="ball",
        line="a rolling ball bumped through the room",
        damage="the tower tipped, then clacked apart, and all its windows went",
        works_on={"tower"},
        tags={"ball"},
    ),
    "bump": CauseCfg(
        id="bump",
        line="one hasty elbow brushed the floor",
        damage="the tower wobbled, swayed, and fell in blocks from end to end",
        works_on={"tower"},
        tags={"bump"},
    ),
    "sprinkler": CauseCfg(
        id="sprinkler",
        line="the sprinkler woke with silver arcs",
        damage="the chalk picture blurred and ran in drippy lines around the bend",
        works_on={"chalk"},
        tags={"water", "sprinkler"},
    ),
    "drizzle": CauseCfg(
        id="drizzle",
        line="a soft drizzle patted from the clouds",
        damage="the chalk picture melted into misty streaks that would not mend",
        works_on={"chalk"},
        tags={"rain"},
    ),
}

AMENDS = {
    "tape_patch": AmendsCfg(
        id="tape_patch",
        label="a tape patch",
        fixes={"paper"},
        action="smoothed the torn edge flat and fixed it with a careful tape patch",
        qa_text="patched the torn kite with tape",
        gift_line="the kite bobbed up again, patched and proud above the grass",
        tags={"tape", "repair"},
    ),
    "rebuild": AmendsCfg(
        id="rebuild",
        label="help rebuilding",
        fixes={"blocks"},
        action="gathered every scattered block and helped rebuild the tower from the ground",
        qa_text="helped rebuild the block tower",
        gift_line="the new tower stood up straighter still, with room for both to pass",
        tags={"blocks", "repair"},
    ),
    "draw_again": AmendsCfg(
        id="draw_again",
        label="fresh chalk and a new drawing",
        fixes={"chalk"},
        action="brought fresh chalk, sat shoulder to shoulder, and drew a new bright picture",
        qa_text="brought fresh chalk and drew a new picture together",
        gift_line="their new bright swirls skipped underfoot, cheerful all around",
        tags={"chalk", "repair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Eli", "Noah", "Finn", "Jack"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    creation: str
    cause: str
    amends: str
    teaser: str
    teaser_gender: str
    maker: str
    maker_gender: str
    helper: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "kite": [(
        "What is a kite?",
        "A kite is a light toy that catches the wind on a string. If it tears, it often needs a careful patch before it can fly well again."
    )],
    "paper": [(
        "Why does paper tear easily in the wind?",
        "Paper is light and thin, so a hard pull or a sharp branch can rip it quickly. That is why paper things need gentle hands."
    )],
    "blocks": [(
        "Why do block towers fall down?",
        "Block towers balance on their bottoms and sides. A bump can shake that balance, and then the blocks tumble down."
    )],
    "chalk": [(
        "Why does chalk wash away?",
        "Chalk sits on top of the ground in powdery lines. Water can smear it and carry the color away."
    )],
    "wind": [(
        "What does a gust of wind do?",
        "A gust is a quick strong push of air. It can tug on light things like leaves, kites, and hats."
    )],
    "sprinkler": [(
        "What is a sprinkler?",
        "A sprinkler sprays water in little arcs to wet grass or plants. It can also splash drawings made with chalk."
    )],
    "repair": [(
        "What does it mean to repair something?",
        "To repair something means to fix it after it is broken or damaged. Repairing shows care because you try to make things better."
    )],
    "kindness": [(
        "Why is kindness important when someone feels sad?",
        "Kindness helps a sad person feel seen and safer. Gentle words and helpful actions can ease hurt much better than teasing can."
    )],
    "apology": [(
        "What makes an apology real?",
        "A real apology says the hurt was wrong and tries to make things better. It is strongest when kind actions come with the sorry."
    )],
}
KNOWLEDGE_ORDER = ["kite", "paper", "blocks", "chalk", "wind", "sprinkler", "repair", "kindness", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teaser = f["teaser"]
    maker = f["maker"]
    creation_cfg = f["creation_cfg"]
    cause = f["cause"]
    outcome = f["outcome"]
    if outcome == "reconciled":
        return [
            f'Write a rhyming story for a 3-to-5-year-old that uses the words "callous" and "melancholic" and begins with a child making {creation_cfg.phrase}.',
            f"Tell a gentle conflict story in rhyme where {teaser.id} laughs after {cause.id} ruins {maker.id}'s {creation_cfg.label}, then learns to apologize and help.",
            f"Write a lesson-learned story in couplets where a hurt friendship is mended as carefully as a broken {creation_cfg.label}.",
        ]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "callous" and "melancholic" and shows how teasing can leave someone alone.',
        f"Tell a conflict story in rhyme where {teaser.id} laughs after {cause.id} ruins {maker.id}'s {creation_cfg.label}, but waits too long to make things right.",
        f"Write a lesson-learned story where a child discovers that unkind words can last longer than a game.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    teaser = f["teaser"]
    maker = f["maker"]
    helper = f["helper"]
    creation_cfg = f["creation_cfg"]
    cause = f["cause"]
    amends = f["amends"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id}, who made {creation_cfg.phrase}, and {teaser.id}, who laughed when it was damaged. {helper.label_word.capitalize()} stepped in to teach them how kindness matters."
        ),
        (
            f"What started the conflict?",
            f"The conflict started when {cause.line}, and {cause.damage}. Then {teaser.id} laughed instead of helping, which made {maker.id} feel even more hurt."
        ),
        (
            f"Why did {maker.id} seem melancholic?",
            f"{maker.id} felt sad because the {creation_cfg.label} {('was damaged' if creation_cfg.id != 'tower' else 'fell apart')} right after being made with care. The teasing made that sadness heavier, so the hurt showed on {maker.pronoun('possessive')} face."
        ),
        (
            f"Why was {teaser.id}'s laugh called callous?",
            f"It was called callous because {teaser.id} treated {maker.id}'s hurt as if it did not matter. The laugh came at the moment a friend needed help, not mockery."
        ),
    ]
    if outcome == "reconciled":
        qa.extend([
            (
                f"How did {teaser.id} try to make things right?",
                f"{teaser.id} {amends.qa_text} and apologized for teasing. That action mattered because it fixed the damaged thing and showed real care at the same time."
            ),
            (
                "What lesson was learned?",
                f"The lesson was that kind help should come quickly when someone is hurt. A true sorry is stronger when it is followed by gentle action."
            ),
            (
                "How did the story end?",
                f"It ended with the children playing together again. The repaired moment proved that the friendship grew warmer after honesty and help."
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the ending stay lonely even after {teaser.id} knew {teaser.pronoun('subject')} was wrong?",
                f"{teaser.id} waited too long before trying to make things right. By then the hurt had already settled, so the game did not spring back at once."
            ),
            (
                "What lesson was learned?",
                f"The lesson was that unkind words can leave a long mark if you delay your apology. Kindness is most powerful when it comes while the hurt is still fresh."
            ),
            (
                "How did the story end?",
                f"It ended quietly, with {teaser.id} walking home and thinking hard about the day. The lonely ending shows that some chances for easy repair do not stay open forever."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["creation_cfg"].tags) | set(f["cause"].tags) | set(f["amends"].tags)
    tags |= {"kindness", "apology"}
    if "repair" not in tags:
        tags.add("repair")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="park",
        creation="kite",
        cause="gust",
        amends="tape_patch",
        teaser="Ben",
        teaser_gender="boy",
        maker="Lily",
        maker_gender="girl",
        helper="teacher",
        delay=0,
    ),
    StoryParams(
        place="playroom",
        creation="tower",
        cause="ball",
        amends="rebuild",
        teaser="Mia",
        teaser_gender="girl",
        maker="Theo",
        maker_gender="boy",
        helper="mother",
        delay=1,
    ),
    StoryParams(
        place="sidewalk",
        creation="chalk",
        cause="sprinkler",
        amends="draw_again",
        teaser="Noah",
        teaser_gender="boy",
        maker="Ava",
        maker_gender="girl",
        helper="father",
        delay=2,
    ),
    StoryParams(
        place="park",
        creation="kite",
        cause="branch",
        amends="tape_patch",
        teaser="Ruby",
        teaser_gender="girl",
        maker="Finn",
        maker_gender="boy",
        helper="teacher",
        delay=2,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, C, K, A) :- setting(P), creation(C), cause(K), amends(A),
                     affords(P, C), allows(P, K), works_on(K, C),
                     material(C, M), fixes(A, M).

outcome(reconciled) :- chosen_creation(C), delay(D), repair_window(C, W), D <= W.
outcome(lonely)     :- chosen_creation(C), delay(D), repair_window(C, W), D > W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for creation_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, creation_id))
        for cause_id in sorted(setting.causes):
            lines.append(asp.fact("allows", place_id, cause_id))
    for creation_id, creation in CREATIONS.items():
        lines.append(asp.fact("creation", creation_id))
        lines.append(asp.fact("material", creation_id, creation.material))
        lines.append(asp.fact("repair_window", creation_id, creation.repair_window))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for creation_id in sorted(cause.works_on):
            lines.append(asp.fact("works_on", cause_id, creation_id))
    for amends_id, amends in AMENDS.items():
        lines.append(asp.fact("amends", amends_id))
        for mat in sorted(amends.fixes):
            lines.append(asp.fact("fixes", amends_id, mat))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_creation", params.creation),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a callous laugh, a melancholic friend, and a lesson learned."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creation", choices=CREATIONS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--amends", choices=AMENDS)
    ap.add_argument("--helper", choices=["teacher", "mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the teaser waits before trying to make amends")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creation and args.cause:
        setting = SETTINGS[args.place]
        creation = CREATIONS[args.creation]
        cause = CAUSES[args.cause]
        if not can_happen(setting, creation, cause):
            amends = AMENDS[args.amends] if args.amends else None
            raise StoryError(explain_rejection(setting, creation, cause, amends))
    if args.creation and args.amends:
        creation = CREATIONS[args.creation]
        amends = AMENDS[args.amends]
        if not can_mend(creation, amends):
            setting = SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            raise StoryError(explain_rejection(setting, creation, cause, amends))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.creation is None or c[1] == args.creation)
        and (args.cause is None or c[2] == args.cause)
        and (args.amends is None or c[3] == args.amends)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creation, cause, amends = rng.choice(combos)
    teaser_gender = rng.choice(["girl", "boy"])
    maker_gender = rng.choice(["girl", "boy"])
    teaser = _pick_name(rng, teaser_gender)
    maker = _pick_name(rng, maker_gender, avoid=teaser)
    helper = args.helper or rng.choice(["teacher", "mother", "father", "grandmother"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        creation=creation,
        cause=cause,
        amends=amends,
        teaser=teaser,
        teaser_gender=teaser_gender,
        maker=maker,
        maker_gender=maker_gender,
        helper=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.place]
        creation_cfg = CREATIONS[params.creation]
        cause = CAUSES[params.cause]
        amends = AMENDS[params.amends]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not can_happen(setting, creation_cfg, cause):
        raise StoryError(explain_rejection(setting, creation_cfg, cause, amends))
    if not can_mend(creation_cfg, amends):
        raise StoryError(explain_rejection(setting, creation_cfg, cause, amends))

    world = tell(
        setting=setting,
        creation_cfg=creation_cfg,
        cause=cause,
        amends=amends,
        teaser_name=params.teaser,
        teaser_gender=params.teaser_gender,
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creation, cause, amends) combos:\n")
        for place, creation, cause, amends in combos:
            print(f"  {place:9} {creation:8} {cause:10} {amends}")
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
            header = (
                f"### {p.teaser} and {p.maker}: {p.creation} at {p.place} "
                f"({p.cause}, {p.amends}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
