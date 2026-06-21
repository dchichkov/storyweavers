#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py
========================================================

A standalone story world for a small mythic cautionary tale: a child in an old
keep is told not to shuck a sacred ear too soon. The shuck is not just a husk in
this world; it is the seal that keeps a spirit sleeping. When the child breaks
that seal early, trouble escapes into the valley. Sometimes the elders can soften
the blow, but in this world's featured branch the ending is bad: the fields fail,
the village goes hungry, and the keep stands quiet above the harm it could not
undo.

The simulation is state-driven:
- typed entities hold physical meters and emotional memes
- the shuck acts as a seal
- releasing a spirit changes weather/pests/darkness in the valley
- an elder response may be strong enough to contain the harm, or too weak/late
- every generated story has a beginning, a turn, and an ending image proving
  what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --all
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --seed 7 -n 5 --qa
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --trace
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --json
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --asp
    python storyworlds/worlds/gpt-5.4/keep_shuck_bad_ending_myth.py --verify
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
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priestess": "elder", "priest": "elder"}.get(
            self.type, self.label or self.type
        )
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
class KeepCfg:
    id: str
    name: str
    crown: str
    valley: str
    image: str
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
class Relic:
    id: str
    label: str
    phrase: str
    spirit: str
    harm_kind: str
    harm_noun: str
    awaken_line: str
    wound_line: str
    ending_line: str
    spread: int
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
class Seal:
    id: str
    label: str
    phrase: str
    keep_line: str
    shuck_verb: str
    plural: bool = False
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
class Rite:
    id: str
    label: str
    sense: int
    power: int
    success_text: str
    fail_text: str
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


def _r_released_harms_valley(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    valley = world.get("valley")
    child = world.get("child")
    if relic.meters["opened"] < THRESHOLD or relic.meters["released"] < THRESHOLD:
        return out
    sig = ("harm", world.facts["relic"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    harm = world.facts["relic"].harm_kind
    valley.meters[harm] += 1
    valley.meters["blight"] += world.facts["relic"].spread
    child.memes["fear"] += 1
    child.memes["guilt"] += 1
    out.append("__harm__")
    return out


def _r_failed_harvest(world: World) -> list[str]:
    out: list[str] = []
    valley = world.get("valley")
    child = world.get("child")
    villagers = world.get("villagers")
    if valley.meters["blight"] < THRESHOLD:
        return out
    sig = ("harvest", int(valley.meters["blight"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    villagers.meters["hunger"] += 1
    valley.meters["harvest_lost"] += 1
    child.memes["sorrow"] += 1
    out.append("__harvest__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="released_harms_valley", tag="physical", apply=_r_released_harms_valley),
    Rule(name="failed_harvest", tag="physical", apply=_r_failed_harvest),
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


def valid_combo(relic: Relic, seal: Seal) -> bool:
    return relic.harm_kind in seal.tags


def sensible_rites() -> list[Rite]:
    return [r for r in RITES.values() if r.sense >= SENSE_MIN]


def danger_severity(relic: Relic, delay: int) -> int:
    return relic.spread + delay


def is_contained(rite: Rite, relic: Relic, delay: int) -> bool:
    return rite.power >= danger_severity(relic, delay)


def predict_release(world: World) -> dict:
    sim = world.copy()
    _open_relic(sim, narrate=False)
    valley = sim.get("valley")
    return {
        "blight": valley.meters["blight"],
        "harm": world.facts["relic"].harm_kind,
        "harvest_lost": valley.meters["harvest_lost"] >= THRESHOLD,
    }


def _open_relic(world: World, narrate: bool = True) -> None:
    relic_ent = world.get("relic")
    relic_ent.meters["opened"] += 1
    relic_ent.meters["released"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, keep: KeepCfg, child: Entity, elder: Entity, relic: Relic, seal: Seal) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In the days when {keep.name} still cast its shadow over {keep.valley}, "
        f"people said the stones remembered every oath. Above the gate rose {keep.crown}, "
        f"and below it lay {keep.image}."
    )
    world.say(
        f"There lived {child.id}, a young keeper's child, and {elder.id}, the old {elder.label_word} "
        f"who watched {relic.phrase}. Around it lay {seal.phrase}, for the shuck did not merely hide the ear; "
        f"it {seal.keep_line}."
    )


def charge(world: World, child: Entity, elder: Entity, relic: Relic) -> None:
    child.memes["duty"] += 1
    world.say(
        f'Each dawn {elder.id} would touch the shrine and say, "Do not open {relic.label} before the bell. '
        f'What sleeps inside must wait." {child.id} always nodded, for the warning was older than the keep itself.'
    )


def temptation(world: World, child: Entity, relic: Relic, seal: Seal) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But one still noon, when even the swallows circled silently, {child.id} stood alone before the shrine. "
        f"{relic.label.capitalize()} gleamed through a split in {seal.phrase}, and wonder pressed at {child.pronoun('possessive')} ribs."
    )
    world.say(
        f"{child.pronoun().capitalize()} whispered that perhaps one careful touch would do no harm, and reached to {seal.shuck_verb} the sacred covering back."
    )


def warning(world: World, child: Entity, elder: Entity) -> None:
    pred = predict_release(world)
    world.facts["predicted_blight"] = pred["blight"]
    world.facts["predicted_harm"] = pred["harm"]
    child.memes["unease"] += 1
    world.say(
        f"Yet {child.id} remembered {elder.id}'s lesson: if the shuck were broken too soon, a sleeping thing would wake and run downhill into the valley. "
        f"The thought made {child.pronoun('object')} hesitate, but not for long."
    )


def defy(world: World, child: Entity, seal: Seal, relic: Relic) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"So {child.id} pinched {seal.label} between trembling fingers and began to shuck it away. "
        f"The last fold gave with a dry whisper, and {relic.awaken_line}"
    )


def release(world: World, child: Entity, relic: Relic, keep: KeepCfg) -> None:
    _open_relic(world, narrate=False)
    world.say(
        f"A cold cry rushed through the halls of {keep.name}. {relic.wound_line} "
        f"{child.id} stumbled back as the doors shook and the valley answered."
    )
    if world.get("valley").meters["blight"] >= THRESHOLD:
        harm = relic.harm_noun
        world.say(
            f"Soon {harm} spilled over the fields below, and every stalk and vine bent under it."
        )


def alarm(world: World, child: Entity, elder: Entity, relic: Relic) -> None:
    world.say(
        f'"{elder.id}!" {child.id} cried. "I opened {relic.label}, and something came out!"'
    )


def respond_success(world: World, elder: Entity, rite: Rite, relic: Relic) -> None:
    world.get("valley").meters["blight"] = 0.0
    world.get("valley").meters[relic.harm_kind] = 0.0
    world.say(
        f"{elder.id} came at once and {rite.success_text}. The roaring in the air thinned, and the worst of the harm drew back from the fields."
    )


def lesson_after_success(world: World, elder: Entity, child: Entity, seal: Seal) -> None:
    child.memes["fear"] = 0.0
    child.memes["remorse"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f'Then {elder.id} took {child.id} by the shoulders and said, "A thing may look small and still keep a whole valley safe. '
        f'Never shuck a sacred seal before its hour."'
    )
    world.say(
        f"{child.id} bowed {child.pronoun('possessive')} head and promised to remember."
    )


def recovery(world: World, keep: KeepCfg, child: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"When the next morning came, {keep.valley} breathed again. {child.id} helped sweep the shrine steps, and the keep looked stern but merciful in the sunrise."
    )


def respond_fail(world: World, elder: Entity, rite: Rite, relic: Relic, keep: KeepCfg) -> None:
    world.get("valley").meters["blight"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.id} came running and {rite.fail_text}. But the spirit was already too wide for old words, and its anger leapt past the walls of {keep.name}."
    )
    world.say(
        f"{relic.ending_line}"
    )


def loss(world: World, child: Entity, elder: Entity, keep: KeepCfg, relic: Relic) -> None:
    child.memes["remorse"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"By dusk the granaries echoed. Mothers counted thin loaves, fathers stared at empty baskets, and no one sang in {keep.valley}."
    )
    world.say(
        f'{elder.id} did not strike {child.id} or shout. "{relic.label.capitalize()} was wrapped for all of us," {elder.pronoun()} said softly. '
        f'"One torn shuck can wound many mouths."'
    )
    world.say(
        f"{child.id} wept beside the shrine, but tears could not mend the broken season."
    )
    world.say(
        f"So the tale was kept: high above the silent fields, {keep.name} watched the moon rise over a hungry valley, and every child thereafter learned to fear the hand that opens sacred things too soon."
    )


def tell(
    keep: KeepCfg,
    relic: Relic,
    seal: Seal,
    rite: Rite,
    child_name: str = "Neri",
    child_gender: str = "girl",
    elder_name: str = "Tamar",
    elder_type: str = "priestess",
    delay: int = 1,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            label="elder",
            attrs={},
        )
    )
    world.add(Entity(id="valley", type="valley", label=keep.valley, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="villagers", type="people", label="villagers", attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="relic", type="relic", label=relic.label, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.facts.update(
        keep=keep,
        relic=relic,
        seal=seal,
        rite=rite,
        delay=delay,
        child=child,
        elder=elder,
        predicted_blight=0,
        predicted_harm="",
    )

    opening(world, keep, child, elder, relic, seal)
    charge(world, child, elder, relic)

    world.para()
    temptation(world, child, relic, seal)
    warning(world, child, elder)
    defy(world, child, seal, relic)

    world.para()
    release(world, child, relic, keep)
    alarm(world, child, elder, relic)

    contained = is_contained(rite, relic, delay)
    severity = danger_severity(relic, delay)
    world.get("relic").meters["severity"] = float(severity)

    world.para()
    if contained:
        respond_success(world, elder, rite, relic)
        lesson_after_success(world, elder, child, seal)
        world.para()
        recovery(world, keep, child)
        outcome = "contained"
    else:
        respond_fail(world, elder, rite, relic, keep)
        loss(world, child, elder, keep, relic)
        outcome = "blighted"

    world.facts.update(
        contained=contained,
        severity=severity,
        outcome=outcome,
        harm_kind=relic.harm_kind,
        harvest_lost=world.get("valley").meters["harvest_lost"] >= THRESHOLD,
        hunger=world.get("villagers").meters["hunger"] >= THRESHOLD,
    )
    return world


KEEPS = {
    "hill_keep": KeepCfg(
        id="hill_keep",
        name="Ashen Keep",
        crown="a black tower with a bell of green bronze",
        valley="the barley valley",
        image="terraced fields stitched with little stone paths",
        tags={"keep", "valley"},
    ),
    "sea_keep": KeepCfg(
        id="sea_keep",
        name="Salt Keep",
        crown="a white watchtower crusted with old salt",
        valley="the cliff gardens",
        image="narrow plots hanging above the sea like green shelves",
        tags={"keep", "sea"},
    ),
    "sun_keep": KeepCfg(
        id="sun_keep",
        name="Sunward Keep",
        crown="a red tower whose windows caught the first light",
        valley="the fig valley",
        image="fig trees and bean rows folded around a clear stream",
        tags={"keep", "sun"},
    ),
}

RELICS = {
    "frost_ear": Relic(
        id="frost_ear",
        label="the frost ear",
        phrase="an ear of pale corn bound with blue thread",
        spirit="frost",
        harm_kind="frost",
        harm_noun="white frost",
        awaken_line="a white breath burst from the kernels like wolves of winter waking",
        wound_line="Ice raced along the shrine floor and silvered the threshold.",
        ending_line="In one night the barley blackened, and the valley woke to stalks that snapped like old bones.",
        spread=3,
        tags={"frost", "corn", "shuck"},
    ),
    "locust_ear": Relic(
        id="locust_ear",
        label="the locust ear",
        phrase="an ear of bronze corn tied with a red cord",
        spirit="locusts",
        harm_kind="locusts",
        harm_noun="a cloud of locusts",
        awaken_line="the kernels rattled, and a dark buzzing poured out as if the ear held a hundred tiny wings",
        wound_line="The air thickened with wings, and the torch flames beat sideways.",
        ending_line="By morning the leaves were lace, and the bean poles stood naked against the sky.",
        spread=2,
        tags={"locusts", "corn", "shuck"},
    ),
    "night_ear": Relic(
        id="night_ear",
        label="the night ear",
        phrase="an ear of black corn wrapped in silver twine",
        spirit="night",
        harm_kind="night",
        harm_noun="a heavy night",
        awaken_line="the kernels drank the noon, and a shawl of dark folded out across the stair",
        wound_line="Shadows pooled in corners where no lamp should fail.",
        ending_line="For three days the sun could not warm the orchards, and the fruit dropped hard and bitter to the ground.",
        spread=2,
        tags={"night", "corn", "shuck"},
    ),
}

SEALS = {
    "reed_shuck": Seal(
        id="reed_shuck",
        label="the reed shuck",
        phrase="a dry reed shuck braided with river grass",
        keep_line="kept the cold breath folded asleep",
        shuck_verb="shuck",
        tags={"frost", "night"},
    ),
    "wax_shuck": Seal(
        id="wax_shuck",
        label="the waxed shuck",
        phrase="a waxed shuck smooth as candle skin",
        keep_line="kept the winged hunger sealed under quiet",
        shuck_verb="shuck",
        tags={"locusts"},
    ),
    "ash_shuck": Seal(
        id="ash_shuck",
        label="the ash shuck",
        phrase="an ash-gray shuck marked with little moon signs",
        keep_line="kept the old dark folded in on itself",
        shuck_verb="shuck",
        tags={"night", "frost"},
    ),
}

RITES = {
    "bell_rite": Rite(
        id="bell_rite",
        label="the bell rite",
        sense=3,
        power=3,
        success_text="struck the green bell until its sound rolled like warm metal over the valley",
        fail_text="struck the green bell again and again until the rope burned in their palms",
        qa_text="rang the keep bell to drive the spirit back",
        tags={"bell", "rite"},
    ),
    "ember_basin": Rite(
        id="ember_basin",
        label="the ember basin",
        sense=2,
        power=2,
        success_text="set the ember basin on the stair and fed it cedar resin until golden smoke wrapped the broken shrine",
        fail_text="fed the ember basin with cedar resin, but the smoke tore apart in the wind",
        qa_text="used the ember basin and cedar smoke to calm the spirit",
        tags={"fire", "rite"},
    ),
    "net_of_names": Rite(
        id="net_of_names",
        label="the net of names",
        sense=2,
        power=1,
        success_text="cast the net of names across the doorway and spoke each ancient word without a stumble",
        fail_text="cast the net of names, but the spirit slipped through every holy word",
        qa_text="cast the net of names over the doorway",
        tags={"names", "rite"},
    ),
    "broom": Rite(
        id="broom",
        label="a straw broom",
        sense=1,
        power=0,
        success_text="swept at the air with a straw broom until the hall cleared",
        fail_text="swept at the air with a straw broom, which was no weapon at all against such harm",
        qa_text="tried to sweep the spirit away with a broom",
        tags={"weak"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for keep_id in KEEPS:
        for relic_id, relic in RELICS.items():
            for seal_id, seal in SEALS.items():
                if valid_combo(relic, seal):
                    combos.append((keep_id, relic_id, seal_id))
    return combos


@dataclass
class StoryParams:
    keep: str
    relic: str
    seal: str
    rite: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    delay: int = 1
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
    "keep": [
        (
            "What is a keep?",
            "A keep is the strongest tower or building inside a castle. In old stories, people often store important things there because it is easier to guard.",
        )
    ],
    "shuck": [
        (
            "What does shuck mean?",
            "To shuck something is to pull off its outer covering, like the husk on corn or a shell around food. In this story, the shuck is also acting like a magic seal.",
        )
    ],
    "frost": [
        (
            "Why is frost bad for crops?",
            "Frost can freeze the water inside plants, so leaves and stalks turn weak and black. A hard frost can ruin a whole field in one night.",
        )
    ],
    "locusts": [
        (
            "Why are locusts dangerous to fields?",
            "Locusts are hungry insects that can eat leaves, stalks, and soft plants very quickly. A big swarm can strip a field almost bare.",
        )
    ],
    "night": [
        (
            "Why do plants need sunlight?",
            "Plants need sunlight to make food and grow strong. If they stay in deep dark too long, fruit and leaves can fail.",
        )
    ],
    "bell": [
        (
            "Why do old stories use bells to chase danger away?",
            "In myths, bells often stand for order, warning, and calling people together. A loud bell can mark that something hidden has been named and challenged.",
        )
    ],
    "rite": [
        (
            "What is a rite?",
            "A rite is a special act done in a careful, traditional way. In myths, people use rites to show respect, ask for help, or try to set things right.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    relic = f["relic"]
    keep = f["keep"]
    if f["outcome"] == "blighted":
        return [
            f'Write a short myth for a young child that includes the words "keep" and "shuck" and ends badly.',
            f"Tell a myth in which {child.id} lives in {keep.name}, disobeys a warning, shucks {relic.label}, and brings trouble down on the valley.",
            f"Write a simple old-style cautionary tale where a sacred shuck is opened too soon and the ending proves that some mistakes cannot be quickly fixed.",
        ]
    return [
        f'Write a short myth for a young child that includes the words "keep" and "shuck".',
        f"Tell a myth in which {child.id} lives in {keep.name}, shucks {relic.label} too early, and an elder barely manages to stop the harm.",
        f"Write a simple old-style tale where a sacred seal is broken and then restored after a hard lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    relic = f["relic"]
    keep = f["keep"]
    seal = f["seal"]
    rite = f["rite"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in {keep.name}, and {elder.id}, the old {elder.label_word} who guarded the sacred ear. The whole valley depends on what they do.",
        ),
        (
            f"What was special about {seal.label}?",
            f"It was not only a covering. The shuck was the seal that kept the sleeping danger inside {relic.label}.",
        ),
        (
            f"Why was {child.id} told not to shuck {relic.label}?",
            f"{child.id} was warned that opening it too soon would wake a spirit and send harm into the valley. The warning mattered because the people below depended on the fields staying safe.",
        ),
        (
            f"What happened when {child.id} opened {relic.label}?",
            f"{relic.awaken_line[0].upper()}{relic.awaken_line[1:]}. After that, {relic.harm_noun} spread over the valley and the crops began to fail.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.extend(
            [
                (
                    f"How did {elder.id} help?",
                    f"{elder.id} {rite.qa_text}. That rite was strong enough to push the danger back before the whole harvest was lost.",
                ),
                (
                    "How did the story end?",
                    f"It ended sadly but safely. {child.id} learned the lesson, and the keep stood over a valley that could still recover.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Could {elder.id} stop the harm?",
                    f"No. {elder.id} tried, but the spirit had already spread too far through the valley. The rite was too weak for the danger after the delay.",
                ),
                (
                    "How did the story end?",
                    f"It ended badly: the harvest failed, the villagers were hungry, and {child.id} understood that one broken shuck had hurt many people. The final image is the keep above silent fields.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"keep", "shuck", f["relic"].harm_kind, "rite"}
    if f["rite"].id == "bell_rite":
        tags.add("bell")
    out: list[tuple[str, str]] = []
    for key in ["keep", "shuck", "frost", "locusts", "night", "bell", "rite"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        keep="hill_keep",
        relic="frost_ear",
        seal="reed_shuck",
        rite="ember_basin",
        child_name="Neri",
        child_gender="girl",
        elder_name="Tamar",
        elder_type="priestess",
        delay=1,
    ),
    StoryParams(
        keep="sea_keep",
        relic="locust_ear",
        seal="wax_shuck",
        rite="net_of_names",
        child_name="Ivo",
        child_gender="boy",
        elder_name="Sera",
        elder_type="priestess",
        delay=1,
    ),
    StoryParams(
        keep="sun_keep",
        relic="night_ear",
        seal="ash_shuck",
        rite="bell_rite",
        child_name="Mira",
        child_gender="girl",
        elder_name="Oren",
        elder_type="priest",
        delay=0,
    ),
    StoryParams(
        keep="hill_keep",
        relic="frost_ear",
        seal="ash_shuck",
        rite="broom",
        child_name="Tovin",
        child_gender="boy",
        elder_name="Tamar",
        elder_type="priestess",
        delay=2,
    ),
    StoryParams(
        keep="sun_keep",
        relic="night_ear",
        seal="reed_shuck",
        rite="ember_basin",
        child_name="Leta",
        child_gender="girl",
        elder_name="Oren",
        elder_type="priest",
        delay=1,
    ),
]


def explain_rejection(relic: Relic, seal: Seal) -> str:
    return (
        f"(No story: {seal.label} is not the kind of shuck that keeps {relic.spirit} sleeping. "
        f"In this world, the seal has to plausibly match the danger inside the ear.)"
    )


def explain_rite(rid: str) -> str:
    rite = RITES[rid]
    better = ", ".join(sorted(r.id for r in sensible_rites()))
    return (
        f"(Refusing rite '{rid}': it scores too low on common sense for this world "
        f"(sense={rite.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(RITES[params.rite], RELICS[params.relic], params.delay) else "blighted"


ASP_RULES = r"""
valid(K,R,S) :- keep(K), relic(R), seal(S), matches(R,S).
sensible(T) :- rite(T), sense(T,V), sense_min(M), V >= M.

severity(P + D) :- chosen_relic(R), spread(R,P), delay(D).
contained :- chosen_rite(T), power(T,P), severity(S), P >= S.
outcome(contained) :- contained.
outcome(blighted) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for keep_id in KEEPS:
        lines.append(asp.fact("keep", keep_id))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("spread", relic_id, relic.spread))
        lines.append(asp.fact("harm", relic_id, relic.harm_kind))
    for seal_id, seal in SEALS.items():
        lines.append(asp.fact("seal", seal_id))
        for tag in sorted(seal.tags):
            lines.append(asp.fact("seal_holds", seal_id, tag))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic_harm", relic_id, relic.harm_kind))
    for relic_id, relic in RELICS.items():
        for seal_id, seal in SEALS.items():
            if valid_combo(relic, seal):
                lines.append(asp.fact("matches", relic_id, seal_id))
    for rite_id, rite in RITES.items():
        lines.append(asp.fact("rite", rite_id))
        lines.append(asp.fact("sense", rite_id, rite.sense))
        lines.append(asp.fact("power", rite_id, rite.power))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_relic", params.relic),
            asp.fact("chosen_rite", params.rite),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    py_sens = {r.id for r in sensible_rites()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible rites match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rites: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for s in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or not isinstance(smoke.story, str):
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic keep, a sacred shuck, and a bad harvest."
    )
    ap.add_argument("--keep", choices=KEEPS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["priestess", "priest"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the spirit gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Neri", "Mira", "Leta", "Suri", "Asha", "Tali"]
BOY_NAMES = ["Ivo", "Tovin", "Eran", "Marek", "Olin", "Pavel"]
ELDER_NAMES = ["Tamar", "Oren", "Sera", "Bren", "Hada", "Yorin"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.seal:
        relic = RELICS[args.relic]
        seal = SEALS[args.seal]
        if not valid_combo(relic, seal):
            raise StoryError(explain_rejection(relic, seal))
    if args.rite and RITES[args.rite].sense < SENSE_MIN:
        raise StoryError(explain_rite(args.rite))

    combos = [
        combo
        for combo in valid_combos()
        if (args.keep is None or combo[0] == args.keep)
        and (args.relic is None or combo[1] == args.relic)
        and (args.seal is None or combo[2] == args.seal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    keep_id, relic_id, seal_id = rng.choice(sorted(combos))
    rite_id = args.rite or rng.choice(sorted(r.id for r in sensible_rites()))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["priestess", "priest"])
    elder_name = args.elder_name or rng.choice([n for n in ELDER_NAMES if n != child_name])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        keep=keep_id,
        relic=relic_id,
        seal=seal_id,
        rite=rite_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.keep not in KEEPS:
        raise StoryError(f"(Unknown keep: {params.keep})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.seal not in SEALS:
        raise StoryError(f"(Unknown seal: {params.seal})")
    if params.rite not in RITES:
        raise StoryError(f"(Unknown rite: {params.rite})")

    keep = KEEPS[params.keep]
    relic = RELICS[params.relic]
    seal = SEALS[params.seal]
    rite = RITES[params.rite]

    if not valid_combo(relic, seal):
        raise StoryError(explain_rejection(relic, seal))
    if rite.sense < SENSE_MIN:
        raise StoryError(explain_rite(params.rite))

    world = tell(
        keep=keep,
        relic=relic,
        seal=seal,
        rite=rite,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        sens = asp_sensible()
        print(f"sensible rites: {', '.join(sens)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (keep, relic, seal) combos:\n")
        for keep_id, relic_id, seal_id in combos:
            print(f"  {keep_id:10} {relic_id:11} {seal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.relic} in {p.keep} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
