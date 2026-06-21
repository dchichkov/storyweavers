#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py
=================================================================================

A standalone story world for a tall-tale domain about giant builders, a snapped
span, an old quarrel healed just in time, and a storm that may still beat the
repair.

This world is built around three seed words that must appear naturally in the
story text:

- wonder
- slave
- splice

The domain keeps the playful swagger of a tall tale, but the simulated state
drives whether the ending is triumphant or sad. The central emotional change is
reconciliation: two giant builders stop feuding and work together again. The
physical change is the splice they make in a broken line that protects a town.
Sometimes the storm is stronger than their patch, so the ending is bad even
though the people reconcile.

Run it
------
    python storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py
    python storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py --all
    python storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py --storm 2 --qa
    python storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py --asp
    python storyworlds/worlds/gpt-5.4/wonder_slave_splice_reconciliation_bad_ending_tall.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    image: str
    town_name: str
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
class Span:
    id: str
    label: str
    phrase: str
    material: str
    weight: int
    base_severity: int
    break_text: str
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
class SpliceMethod:
    id: str
    label: str
    phrase: str
    materials: set[str]
    strength: int
    sense: int
    action_text: str
    bad_text: str
    qa_text: str
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
class Helper:
    id: str
    label: str
    phrase: str
    lift: int
    follow_text: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "storm_started": False,
            "severity": 0,
            "method_strength": 0,
            "teamwork_bonus": 0,
            "outcome": "",
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


def _r_teamwork(world: World) -> list[str]:
    hero = world.entities.get("hero")
    rival = world.entities.get("rival")
    line = world.entities.get("span")
    if not hero or not rival or not line:
        return []
    if hero.memes["reconciled"] < THRESHOLD or rival.memes["reconciled"] < THRESHOLD:
        return []
    if line.meters["spliced"] < THRESHOLD:
        return []
    sig = ("teamwork_bonus",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    line.meters["teamwork_bonus"] += 1
    world.facts["teamwork_bonus"] = 1
    return ["__teamwork__"]


def _r_storm_test(world: World) -> list[str]:
    line = world.entities.get("span")
    town = world.entities.get("town")
    if not line or not town:
        return []
    if not world.facts.get("storm_started"):
        return []
    if line.meters["spliced"] < THRESHOLD:
        return []
    sig = ("storm_test",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    strength = world.facts.get("method_strength", 0) + int(line.meters["teamwork_bonus"])
    severity = world.facts.get("severity", 0)
    if strength >= severity:
        town.meters["safe"] += 1
        world.facts["outcome"] = "saved"
    else:
        town.meters["flooded"] += 1
        line.meters["snapped"] += 1
        hero = world.entities.get("hero")
        rival = world.entities.get("rival")
        if hero:
            hero.memes["sorrow"] += 1
        if rival:
            rival.memes["sorrow"] += 1
        world.facts["outcome"] = "ruined"
    return ["__storm__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="storm_test", tag="physical", apply=_r_storm_test),
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


def compatible(span: Span, splice: SpliceMethod) -> bool:
    return span.material in splice.materials


def capable(helper: Helper, span: Span) -> bool:
    return helper.lift >= span.weight


def sensible_splices() -> list[SpliceMethod]:
    return [s for s in SPLICES.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for span_id, span in SPANS.items():
            for splice_id, splice in SPLICES.items():
                if not compatible(span, splice):
                    continue
                if splice.sense < SENSE_MIN:
                    continue
                for helper_id, helper in HELPERS.items():
                    if capable(helper, span):
                        combos.append((setting_id, span_id, splice_id, helper_id))
    return combos


def storm_severity(span: Span, storm: int) -> int:
    return span.base_severity + storm


def outcome_of(params: "StoryParams") -> str:
    if params.span not in SPANS or params.splice not in SPLICES:
        raise StoryError("(No story: unknown span or splice choice.)")
    span = SPANS[params.span]
    splice = SPLICES[params.splice]
    strength = splice.strength + 1
    severity = storm_severity(span, params.storm)
    return "saved" if strength >= severity else "ruined"


def explain_rejection(span: Span, splice: SpliceMethod, helper: Optional[Helper] = None) -> str:
    if not compatible(span, splice):
        return (
            f"(No story: {splice.label} does not make a believable splice for {span.phrase}. "
            f"Pick a method that can really hold {span.material}.)"
        )
    if splice.sense < SENSE_MIN:
        return (
            f"(Refusing splice '{splice.id}': it scores too low on common sense "
            f"(sense={splice.sense} < {SENSE_MIN}). Try a sturdier splice.)"
        )
    if helper is not None and not capable(helper, span):
        return (
            f"(No story: {helper.label} cannot lift {span.phrase}. "
            f"The helper must be strong enough to hold the broken line still.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_patch(span: Span, splice: SpliceMethod, storm: int) -> dict:
    severity = storm_severity(span, storm)
    strength = splice.strength + 1
    return {"holds": strength >= severity, "severity": severity, "strength": strength}


def introduce(world: World, hero: Entity, rival: Entity, span: Span, helper: Helper) -> None:
    world.say(
        f"In the days when fence posts were taller than church steeples, {hero.id} and {rival.id} "
        f"were the two biggest builders for a hundred counties around."
    )
    world.say(
        f"They had once worked side by side so well that folks called their work a wonder, "
        f"for they could string up {span.phrase} between breakfast and supper."
    )
    world.say(
        f"Down in {world.setting.town_name}, even the old {helper.label} in their yard was famous. "
        f"It was a reel that followed the big master drum, so the crew called it the slave spool."
    )


def quarrel(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["grudge"] += 1
    rival.memes["grudge"] += 1
    world.say(
        f"But pride is a tall weed. One windy season, {hero.id} bragged louder than a brass band, "
        f"and {rival.id} answered back just as hard. Since then they had worked on opposite ridges "
        f"and hardly tipped a hat to each other."
    )


def disaster(world: World, span: Span) -> None:
    line = world.get("span")
    town = world.get("town")
    line.meters["broken"] += 1
    town.meters["danger"] += 1
    world.say(
        f"Then a black storm came snorting over {world.setting.label} and {span.break_text}. "
        f"All at once {world.setting.town_name} sat in danger below."
    )


def call_for_help(world: World, hero: Entity, rival: Entity, span: Span, helper: Helper, storm: int) -> None:
    pred = predict_patch(span, SPLICES[world.facts["splice"].id], storm)
    world.facts["predicted_holds"] = pred["holds"]
    world.facts["predicted_severity"] = pred["severity"]
    world.say(
        f"{hero.id} stared at the dangling line and knew even giant hands could not fix it alone. "
        f"So {hero.pronoun('subject')} trudged straight to {rival.id}'s shed, where the {helper.label} "
        f"clicked and waited."
    )


def apologize(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["humility"] += 1
    rival.memes["listening"] += 1
    world.say(
        f'"Neighbor," said {hero.id}, taking off {hero.pronoun("possessive")} hat, '
        f'"I let boasting make a fool of me. The town needs both of us more than I need to win."'
    )
    world.say(
        f"{rival.id} looked at the mud on {hero.id}'s boots, heard the shake in {hero.pronoun('possessive')} voice, "
        f"and let the old grudge loosen."
    )


def reconcile(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["reconciled"] += 1
    rival.memes["reconciled"] += 1
    hero.memes["hope"] += 1
    rival.memes["hope"] += 1
    hero.memes["grudge"] = 0.0
    rival.memes["grudge"] = 0.0
    world.say(
        f'"Then let us mend what ought to be mended," said {rival.id}. '
        f'They shook hands so hard the shed windows rattled, and just like that the two giants were reconciled.'
    )


def haul_into_place(world: World, hero: Entity, rival: Entity, helper: Helper, span: Span) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["working"] += 1
    world.say(
        f"They rolled out the {helper.label}, whose little reel followed the main drum like a faithful shadow, "
        f"and its chains sang while it held {span.label} steady."
    )
    world.say(helper.follow_text)


def make_splice(world: World, hero: Entity, rival: Entity, span: Span, splice: SpliceMethod) -> None:
    line = world.get("span")
    line.meters["spliced"] += 1
    world.facts["method_strength"] = splice.strength
    world.say(
        f"Together they made a splice with {splice.phrase}. {splice.action_text}"
    )
    propagate(world, narrate=False)


def storm_hits(world: World, span: Span, storm: int) -> None:
    world.facts["storm_started"] = True
    world.facts["severity"] = storm_severity(span, storm)
    names = {0: "a hard rain", 1: "a roaring gale", 2: "a sky-twisting cyclone"}
    world.say(
        f"Before the mud was dry, {names.get(storm, 'a hard storm')} slammed into the ridge to test their work."
    )
    propagate(world, narrate=False)


def good_ending(world: World, hero: Entity, rival: Entity, span: Span) -> None:
    world.say(
        f"The splice held. Water and wagons kept to their proper path, and {world.setting.town_name} lit its lamps again."
    )
    world.say(
        f"That night {hero.id} and {rival.id} sat on a hill above town, sharing one supper bucket and laughing at the storm. "
        f"{span.ending_image}"
    )


def bad_ending(world: World, hero: Entity, rival: Entity, span: Span, splice: SpliceMethod) -> None:
    town = world.get("town")
    town.meters["ruin"] += 1
    world.say(
        f"But the storm hit meaner than they had guessed. {splice.bad_text}, and the giant line snapped with a crack like split winter timber."
    )
    world.say(
        f"By dawn, {world.setting.town_name} was half drowned and half buried in wreckage. "
        f"The bad ending was plain as daylight: the town was hurt, and no brag could hide it."
    )
    world.say(
        f"Still, on the courthouse roof, {hero.id} and {rival.id} stood shoulder to shoulder throwing ropes to their neighbors. "
        f"They had lost the line, but they had found each other again."
    )


def tell(
    setting: Setting,
    span: Span,
    splice: SpliceMethod,
    helper: Helper,
    hero_name: str = "Mara",
    hero_gender: str = "girl",
    rival_name: str = "Bo",
    rival_gender: str = "boy",
    relation: str = "friends",
    storm: int = 1,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    rival = world.add(Entity(id="rival", kind="character", type=rival_gender, label=rival_name, role="rival"))
    town = world.add(Entity(id="town", kind="thing", type="town", label=setting.town_name, role="town"))
    line = world.add(Entity(id="span", kind="thing", type="span", label=span.label, role="span"))
    helper_ent = world.add(Entity(id="helper", kind="thing", type="helper", label=helper.label, role="helper"))

    world.facts.update(
        hero=hero,
        rival=rival,
        town=town,
        span_cfg=span,
        setting=setting,
        splice=splice,
        helper=helper,
        relation=relation,
        storm=storm,
        hero_name=hero_name,
        rival_name=rival_name,
        reconciled=False,
    )

    introduce(world, hero, rival, span, helper)
    quarrel(world, hero, rival)

    world.para()
    disaster(world, span)
    call_for_help(world, hero, rival, span, helper, storm)

    world.para()
    apologize(world, hero, rival)
    reconcile(world, hero, rival)
    world.facts["reconciled"] = True

    world.para()
    haul_into_place(world, hero, rival, helper, span)
    make_splice(world, hero, rival, span, splice)
    storm_hits(world, span, storm)

    world.para()
    if world.facts["outcome"] == "saved":
        good_ending(world, hero, rival, span)
    else:
        bad_ending(world, hero, rival, span, splice)

    return world


SETTINGS = {
    "canyon": Setting(
        id="canyon",
        label="the Red Howler Canyon",
        image="red cliffs that could toss an echo from breakfast to bedtime",
        town_name="Kettle Hollow",
        tags={"canyon", "storm"},
    ),
    "prairie": Setting(
        id="prairie",
        label="the Long-Grass Prairie",
        image="grass rolling so far it looked like the earth was practicing waves",
        town_name="Tin Cup Crossing",
        tags={"prairie", "storm"},
    ),
    "bayou": Setting(
        id="bayou",
        label="the Moon-Swallow Bayou",
        image="water and reeds spread flat as a green mirror",
        town_name="Willow Lantern",
        tags={"bayou", "storm"},
    ),
}

SPANS = {
    "ferry_rope": Span(
        id="ferry_rope",
        label="the ferry rope",
        phrase="a ferry rope thick as a barn trunk",
        material="hemp",
        weight=2,
        base_severity=2,
        break_text="the ferry rope snapped over the flood channel",
        ending_image="The patched rope lay across the river like a sleepy golden snake.",
        tags={"rope", "river"},
    ),
    "water_hose": Span(
        id="water_hose",
        label="the wonder hose",
        phrase="the wonder hose that fed the town pumps",
        material="rubber",
        weight=2,
        base_severity=2,
        break_text="the wonder hose burst and whipped through the air",
        ending_image="The hose curved over the pumps like a tame green dragon.",
        tags={"hose", "water", "wonder"},
    ),
    "bridge_cable": Span(
        id="bridge_cable",
        label="the bridge cable",
        phrase="a bridge cable as thick as a mill chimney",
        material="steel",
        weight=3,
        base_severity=3,
        break_text="the bridge cable tore loose from the high tower",
        ending_image="The cable shone over the gorge like a silver moonbeam tied down to earth.",
        tags={"bridge", "steel"},
    ),
}

SPLICES = {
    "iron_clasp": SpliceMethod(
        id="iron_clasp",
        label="iron clasp",
        phrase="iron clasps and six wagonfuls of bolts",
        materials={"hemp", "rubber", "steel"},
        strength=3,
        sense=3,
        action_text="Each bolt went in with a clang that sent sparrows out of the next county.",
        bad_text="the iron clasps groaned, bent, and tore free",
        qa_text="They used iron clasps and many bolts to make the splice",
        tags={"splice", "iron"},
    ),
    "tar_wrap": SpliceMethod(
        id="tar_wrap",
        label="tar wrap",
        phrase="hot tar, sailcloth, and a careful wrapping",
        materials={"hemp", "rubber"},
        strength=2,
        sense=2,
        action_text="They wrapped the join so neatly that even the rain had to squint to find the seam.",
        bad_text="the tarred wrapping peeled loose in the wet wind",
        qa_text="They wrapped the break with hot tar and sailcloth",
        tags={"splice", "tar"},
    ),
    "vine_knot": SpliceMethod(
        id="vine_knot",
        label="vine knot",
        phrase="wild grapevines and three showy knots",
        materials={"hemp"},
        strength=1,
        sense=1,
        action_text="It looked grand from far away, which was the best thing that could be said for it.",
        bad_text="the vines popped apart like green string beans",
        qa_text="They tied the break with vines",
        tags={"splice", "vine"},
    ),
}

HELPERS = {
    "slave_spool": Helper(
        id="slave_spool",
        label="slave spool",
        phrase="the old slave spool",
        lift=3,
        follow_text="The crew said it always minded the master drum and never tried to be clever on its own.",
        tags={"machine", "slave_spool"},
    ),
    "steam_mule": Helper(
        id="steam_mule",
        label="steam mule",
        phrase="the steam mule hoist",
        lift=2,
        follow_text="It snorted sparks and dug its iron feet into the dirt until the line rose.",
        tags={"machine", "steam"},
    ),
    "thunder_winch": Helper(
        id="thunder_winch",
        label="thunder winch",
        phrase="the thunder winch",
        lift=4,
        follow_text="Its gears boomed so deep that pie tins danced off windowsills in town.",
        tags={"machine", "winch"},
    ),
}

GIRL_NAMES = ["Mara", "Tess", "Ada", "June", "Nell", "Ruth", "Pearl", "May"]
BOY_NAMES = ["Bo", "Eli", "Hank", "Jude", "Otis", "Levi", "Cal", "Ned"]
RELATIONS = ["friends", "siblings"]


@dataclass
class StoryParams:
    setting: str
    span: str
    splice: str
    helper: str
    hero_name: str
    hero_gender: str
    rival_name: str
    rival_gender: str
    relation: str
    storm: int = 1
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
    "wonder": [
        (
            "What does wonder mean?",
            "Wonder is the feeling you get when something seems amazing or hard to believe. In a tall tale, wonder often comes from huge, surprising things."
        )
    ],
    "splice": [
        (
            "What is a splice?",
            "A splice is a joined place where two broken ends are fastened together. Builders make a splice when they need one long rope, hose, or cable again."
        )
    ],
    "slave_spool": [
        (
            "What is the slave spool in this story?",
            "In this tall tale, the slave spool is a helper reel that follows a larger master drum and feeds the line into place. It is a machine name in the workshop, not a person."
        )
    ],
    "iron": [
        (
            "Why are iron clasps strong?",
            "Iron clasps are strong because iron is hard and can hold tight when it is bolted around something. That makes them useful for a sturdy repair."
        )
    ],
    "tar": [
        (
            "Why does tar help seal things?",
            "Hot tar is sticky and water-resistant, so it can help wrap and seal a join. It is better for softer materials than for heavy steel."
        )
    ],
    "storm": [
        (
            "Why can a storm break things?",
            "A storm pushes, shakes, and soaks things all at once. If a line is already weak, strong wind and water can finish breaking it."
        )
    ],
    "reconcile": [
        (
            "What does it mean to reconcile?",
            "To reconcile means to stop a quarrel and make peace again. People reconcile when they forgive each other and work together."
        )
    ],
    "rope": [
        (
            "Why do ropes need careful repairs?",
            "Ropes carry pulling force all along their strands. If the join is weak, the pull can make the rope fail at the splice."
        )
    ],
    "bridge": [
        (
            "Why is a bridge cable important?",
            "A bridge cable helps hold up the bridge and share its weight. If the cable breaks, the bridge can become dangerous."
        )
    ],
    "hose": [
        (
            "What does a water hose do for a town?",
            "A big water hose can carry water from one place to another. If it bursts, people may lose water where they need it."
        )
    ],
}
KNOWLEDGE_ORDER = ["wonder", "splice", "slave_spool", "iron", "tar", "storm", "reconcile", "rope", "bridge", "hose"]


CURATED = [
    StoryParams(
        setting="canyon",
        span="bridge_cable",
        splice="iron_clasp",
        helper="slave_spool",
        hero_name="Mara",
        hero_gender="girl",
        rival_name="Bo",
        rival_gender="boy",
        relation="friends",
        storm=2,
    ),
    StoryParams(
        setting="prairie",
        span="water_hose",
        splice="tar_wrap",
        helper="steam_mule",
        hero_name="June",
        hero_gender="girl",
        rival_name="Otis",
        rival_gender="boy",
        relation="siblings",
        storm=2,
    ),
    StoryParams(
        setting="bayou",
        span="ferry_rope",
        splice="iron_clasp",
        helper="thunder_winch",
        hero_name="Pearl",
        hero_gender="girl",
        rival_name="Levi",
        rival_gender="boy",
        relation="friends",
        storm=0,
    ),
    StoryParams(
        setting="prairie",
        span="ferry_rope",
        splice="tar_wrap",
        helper="slave_spool",
        hero_name="Tess",
        hero_gender="girl",
        rival_name="Cal",
        rival_gender="boy",
        relation="siblings",
        storm=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    span = f["span_cfg"]
    setting = f["setting"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a tall tale for a young child that includes the words "wonder", "slave", '
        f'and "splice", and is set around {setting.label}.'
    )
    if outcome == "ruined":
        return [
            base,
            f"Tell a giant-builder story where {hero.label} and {rival.label} reconcile in time to repair {span.label}, "
            f"using the {helper.label}, but the storm still beats them and the ending is sad.",
            "Write a tall tale with a healed friendship, a brave repair, and a bad ending that still shows people helping one another.",
        ]
    return [
        base,
        f"Tell a tall tale where {hero.label} and {rival.label} stop feuding, make a daring splice, and save the town together.",
        "Write a giant-country story with a quarrel, a reconciliation, and an ending image that proves the town is safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    span = f["span_cfg"]
    splice = f["splice"]
    helper = f["helper"]
    setting = f["setting"]
    outcome = f["outcome"]
    town = setting.town_name
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two giant builders, {hero.label} and {rival.label}. They had been quarreling, but the broken {span.label} forced them back together."
        ),
        (
            f"What was in danger?",
            f"{town} was in danger when {span.break_text}. The broken line threatened the town below, so the builders had to act fast."
        ),
        (
            f"Why did {hero.label} go to {rival.label}?",
            f"{hero.label} knew the job was too big for one person, even a giant. That is why {hero.pronoun('subject')} went to ask {rival.label} for help instead of staying proud."
        ),
        (
            "How did they reconcile?",
            f"{hero.label} apologized for boasting, and {rival.label} chose to let the old grudge go. Their handshake mattered because once they trusted each other again, they could work as a real team."
        ),
        (
            "What did they use to make the splice?",
            f"{splice.qa_text}. They also used the {helper.label} to hold the broken line steady while they worked."
        ),
    ]
    if outcome == "ruined":
        qa.append(
            (
                "Why is the ending sad even though they made peace?",
                f"The ending is sad because the storm was stronger than their repair, so the town was still damaged. Their reconciliation changed their hearts, but it could not undo the storm once it came down so hard."
            )
        )
        qa.append(
            (
                "What proves they changed by the end?",
                f"They stood shoulder to shoulder on the courthouse roof and threw ropes to their neighbors. That shows the quarrel was over, because they stayed together and helped people even after losing the line."
            )
        )
    else:
        qa.append(
            (
                "How did the reconciliation help the repair?",
                f"Once they reconciled, they worked in step instead of pulling against each other. That teamwork gave them a better chance to finish the splice before the storm tested it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The splice held and {town} was safe again. The final image of the repaired line lying calm over the land proves that things changed for the better."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"wonder", "splice", "reconcile", "storm"}
    tags |= set(f["helper"].tags)
    tags |= set(f["span_cfg"].tags)
    tags |= set(f["splice"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} severity={world.facts.get('severity')} method_strength={world.facts.get('method_strength')} teamwork_bonus={world.facts.get('teamwork_bonus')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_splice(P) :- splice(P), sense(P,S), sense_min(M), S >= M.
compatible(Sn, P) :- span(Sn), splice(P), span_material(Sn, M), splice_material(P, M).
capable(H, Sn)    :- helper(H), span(Sn), lift(H, L), weight(Sn, W), L >= W.
valid(St, Sn, P, H) :- setting(St), compatible(Sn, P), capable(H, Sn), sensible_splice(P).

effective_strength(V) :- chosen_splice(P), strength(P, S), V = S + 1.
severity(V) :- chosen_span(Sn), base_severity(Sn, B), chosen_storm(Stm), V = B + Stm.
outcome(saved)  :- effective_strength(E), severity(V), E >= V.
outcome(ruined) :- effective_strength(E), severity(V), E < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, span in SPANS.items():
        lines.append(asp.fact("span", sid))
        lines.append(asp.fact("span_material", sid, span.material))
        lines.append(asp.fact("weight", sid, span.weight))
        lines.append(asp.fact("base_severity", sid, span.base_severity))
    for pid, splice in SPLICES.items():
        lines.append(asp.fact("splice", pid))
        lines.append(asp.fact("sense", pid, splice.sense))
        lines.append(asp.fact("strength", pid, splice.strength))
        for mat in sorted(splice.materials):
            lines.append(asp.fact("splice_material", pid, mat))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("lift", hid, helper.lift))
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
            asp.fact("chosen_span", params.span),
            asp.fact("chosen_splice", params.splice),
            asp.fact("chosen_storm", params.storm),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: random resolution failed at seed {seed}.")
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

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(smoke_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a snapped giant line, a splice, and a reconciliation that may still end sadly."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--span", choices=SPANS)
    ap.add_argument("--splice", choices=SPLICES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--storm", type=int, choices=[0, 1, 2], help="how hard the storm hits the repaired line")
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_person(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in names if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.span and args.splice:
        span = SPANS[args.span]
        splice = SPLICES[args.splice]
        helper = HELPERS[args.helper] if args.helper else None
        if not compatible(span, splice) or splice.sense < SENSE_MIN or (helper and not capable(helper, span)):
            raise StoryError(explain_rejection(span, splice, helper))
    if args.helper and args.span:
        if not capable(HELPERS[args.helper], SPANS[args.span]):
            raise StoryError(explain_rejection(SPANS[args.span], SPLICES[args.splice] if args.splice else sensible_splices()[0], HELPERS[args.helper]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.span is None or c[1] == args.span)
        and (args.splice is None or c[2] == args.splice)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, span, splice, helper = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_person(rng)
    rival_name, rival_gender = _pick_person(rng, avoid=hero_name)
    relation = args.relation or rng.choice(RELATIONS)
    storm = args.storm if args.storm is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting,
        span=span,
        splice=splice,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        rival_name=rival_name,
        rival_gender=rival_gender,
        relation=relation,
        storm=storm,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.span not in SPANS:
        raise StoryError(f"(No story: unknown span '{params.span}'.)")
    if params.splice not in SPLICES:
        raise StoryError(f"(No story: unknown splice '{params.splice}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.relation not in RELATIONS:
        raise StoryError(f"(No story: unknown relation '{params.relation}'.)")

    setting = SETTINGS[params.setting]
    span = SPANS[params.span]
    splice = SPLICES[params.splice]
    helper = HELPERS[params.helper]

    if not compatible(span, splice) or splice.sense < SENSE_MIN or not capable(helper, span):
        raise StoryError(explain_rejection(span, splice, helper))

    world = tell(
        setting=setting,
        span=span,
        splice=splice,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        rival_name=params.rival_name,
        rival_gender=params.rival_gender,
        relation=params.relation,
        storm=params.storm,
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
        print(f"{len(combos)} compatible (setting, span, splice, helper) combos:\n")
        for setting, span, splice, helper in combos:
            print(f"  {setting:8} {span:12} {splice:10} {helper}")
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
            header = f"### {p.hero_name} & {p.rival_name}: {p.span} with {p.splice} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
