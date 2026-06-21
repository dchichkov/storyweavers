#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py
===============================================================

A standalone storyworld for a small mythic domain: a child at a hill shrine sees
a sacred object hanging skew before dawn and is tempted to fix it in a hurried,
unsafe way. The world models duty, warning, damage, repair, and a lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py --relic sun_mirror
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py --shortcut tossing_stone
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py --all
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py --trace
    python storyworlds/worlds/gpt-5.4/look_skew_end_lesson_learned_myth.py --verify
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
PRIDE_INIT = 6.0
WISE_TRAITS = {"wise", "patient", "careful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "mother"}
        male = {"boy", "man", "priest", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"priestess": "priestess", "priest": "priest"}.get(self.type, self.type)
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
    sky: str
    stone: str
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
class Relic:
    id: str
    label: str
    phrase: str
    signal: str
    mount: str
    height: int
    fragility: int
    sway_text: str
    blessing: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    reach: int
    force: int
    sound: str
    warning: str
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
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    gift: str
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "cautioner"}]

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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    if relic.meters["crack"] < THRESHOLD:
        return out
    sig = ("danger", "relic")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("shrine").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    if relic.meters["crack"] < 2.0:
        return out
    sig = ("fall", "relic")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    relic.meters["fallen"] += 1
    world.get("shrine").meters["loss"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


def hazard_at_risk(setting: Setting, relic: Relic, shortcut: Shortcut) -> bool:
    return relic.id in setting.affords and shortcut.reach >= relic.height and shortcut.force >= 1


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def damage_severity(relic: Relic, shortcut: Shortcut, delay: int) -> int:
    return max(1, shortcut.force + relic.fragility - 1 + delay)


def is_restored(repair: Repair, relic: Relic, shortcut: Shortcut, delay: int) -> bool:
    return repair.power >= damage_severity(relic, shortcut, delay)


def initial_wisdom(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > hero_age
    authority = initial_wisdom(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > PRIDE_INIT


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    relic = sim.get("relic")
    shortcut = sim.facts["shortcut_cfg"]
    _attempt_shortcut(sim, relic, shortcut, narrate=False)
    return {
        "crack": relic.meters["crack"],
        "fallen": relic.meters["fallen"],
        "danger": sim.get("shrine").meters["danger"],
    }


def _attempt_shortcut(world: World, relic_ent: Entity, shortcut: Shortcut, narrate: bool = True) -> None:
    relic_ent.meters["sway"] += 1
    relic_ent.meters["crack"] += float(shortcut.force - 1)
    if shortcut.force >= 3:
        relic_ent.meters["crack"] += 1
    propagate(world, narrate=narrate)


def dawn_setup(world: World, hero: Entity, cautioner: Entity, elder: Entity, relic: Relic) -> None:
    for kid in (hero, cautioner):
        kid.memes["duty"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"In the elder days, when dawn was said to listen to human hands, {hero.id} and "
        f"{cautioner.id} climbed to {world.setting.place} with baskets of laurel and blue thread."
    )
    world.say(
        f"Above them hung {relic.phrase} on {relic.mount}. The {world.setting.sky} was pale, "
        f"and the first birds had not yet begun."
    )
    world.say(
        f'Then {hero.id} stopped and said, "Look." {relic.phrase.capitalize()} hung skew, '
        f"leaning away from the place where sunrise should touch it."
    )
    world.say(
        f"They both knew the old saying: if it was left that way, it might not {relic.signal}."
    )
    world.facts["elder_word"] = elder.label_word


def temptation(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} gripped the basket tighter. "We cannot wait for the priest," '
        f'{hero.pronoun()} said. "I can fix it with {shortcut.phrase}."'
    )
    world.say(
        f"For one quick heartbeat, the plan seemed bright enough to chase away caution."
    )


def warning(world: World, cautioner: Entity, hero: Entity, relic: Relic, shortcut: Shortcut, elder: Entity) -> None:
    pred = predict_mishap(world)
    cautioner.memes["wisdom"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fallen"] = pred["fallen"] >= THRESHOLD
    extra = ""
    if pred["fallen"] >= THRESHOLD:
        extra = f" It might even fall from {relic.mount} and strike the stone below."
    elif pred["crack"] >= THRESHOLD:
        extra = f" It could chip the sacred rim and make the whole shrine tremble."
    world.say(
        f'{cautioner.id} shook {cautioner.pronoun("possessive")} head. "{elder.label_word.capitalize()} '
        f'always says {shortcut.warning}. If you touch {relic.label} that way, it may swing harder instead of straight."'
        f"{extra}"
    )


def defy(world: World, hero: Entity, cautioner: Entity, shortcut: Shortcut) -> None:
    hero.memes["defiance"] += 1
    older_hero = hero.attrs.get("relation") == "siblings" and hero.age > cautioner.age
    if older_hero:
        world.say(
            f'"The sun will not wait for slow feet," {hero.id} said, and because {hero.pronoun()} '
            f"was the older one, {cautioner.id} could not stop {hero.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"The sun will not wait for slow feet," {hero.id} said, and ran to lift {shortcut.label}.'
        )


def back_down(world: World, hero: Entity, cautioner: Entity, elder: Entity, relic: Relic) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f'{hero.id} looked up again at the hanging relic, then back at {cautioner.id}. '
        f"The brave hurry drained out of {hero.pronoun('object')}."
    )
    world.say(
        f'"No," {hero.pronoun()} whispered at last. "If I cannot mend what I touch, I should not touch it." '
        f"So they left {relic.label} hanging skew for a little while longer and went to wake the {elder.label_word}."
    )


def mishap(world: World, hero: Entity, cautioner: Entity, relic_ent: Entity, relic: Relic, shortcut: Shortcut) -> None:
    _attempt_shortcut(world, relic_ent, shortcut, narrate=False)
    crack = relic_ent.meters["crack"] >= THRESHOLD
    fallen = relic_ent.meters["fallen"] >= THRESHOLD
    line = (
        f"{shortcut.sound} The {shortcut.label} struck {relic.label}, and the sacred thing lurched sideways. "
        f"{relic.sway_text}"
    )
    if fallen:
        line += f" Then the fastening gave way, and {relic.label} fell to the {world.setting.stone} with a hard cry."
    elif crack:
        line += f" A thin crack flashed across it like white frost on dark water."
    else:
        line += f" It swayed and swayed, never coming fully straight."
    world.say(line)
    if crack:
        world.say(f'"{relic.label.capitalize()}!" {cautioner.id} cried, and fear broke open in both children.')


def summon(world: World, cautioner: Entity, elder: Entity) -> None:
    world.say(f'"{elder.label_word.capitalize()}!" {cautioner.id} called down the steps. "Come quickly!"')


def rescue(world: World, elder: Entity, repair: Repair, relic_ent: Entity, relic: Relic) -> None:
    relic_ent.meters["crack"] = 0.0
    relic_ent.meters["fallen"] = 0.0
    relic_ent.meters["sway"] = 0.0
    relic_ent.meters["straight"] += 1
    world.get("shrine").meters["danger"] = 0.0
    world.say(
        f"The {elder.label_word} came with calm feet and {repair.text.format(relic=relic.label, mount=relic.mount)}."
    )
    world.say(
        f"Slowly the sacred shape steadied until it caught the first gold of day and seemed to wake from hurt."
    )


def lesson(world: World, elder: Entity, hero: Entity, cautioner: Entity, relic: Relic) -> None:
    for kid in (hero, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'The {elder.label_word} laid one hand on each small shoulder. "Children," {elder.pronoun()} said, '
        f'"the gods do not ask for haste. They ask for steady hands, truthful eyes, and help called at the right time."'
    )
    world.say(
        f'{hero.id} bowed {hero.pronoun("possessive")} head. {cautioner.id} did the same, and the lesson settled '
        f"more deeply than the morning light."
    )


def honoring_end(world: World, elder: Entity, hero: Entity, cautioner: Entity, relic: Relic, repair: Repair) -> None:
    for kid in (hero, cautioner):
        kid.memes["honor"] += 1
    world.say(
        f"By the end of the rite, the {elder.label_word} gave them {repair.gift} and told them to keep watch together "
        f"whenever dawn returned."
    )
    world.say(
        f"From that day on, when they saw anything hang skew, they did not reach in pride. They looked, called for wise hands, "
        f"and let patience keep {relic.blessing} alive."
    )


def rescue_fail(world: World, elder: Entity, repair: Repair, relic_ent: Entity, relic: Relic) -> None:
    relic_ent.meters["broken"] += 1
    world.get("shrine").meters["loss"] += 1
    world.say(
        f"The {elder.label_word} came at once and {repair.fail.format(relic=relic.label, mount=relic.mount)}."
    )
    world.say(
        f"But the hurt was already too great. The old shape could not be mended before sunrise climbed over the ridge."
    )


def austere_end(world: World, elder: Entity, hero: Entity, cautioner: Entity, relic: Relic) -> None:
    for kid in (hero, cautioner):
        kid.memes["lesson"] += 1
        kid.memes["sorrow"] += 1
    world.say(
        f"So the people faced the east in silence, and no bright sign answered them from {relic.mount}. "
        f"Even so, the day began, and everyone understood that sacred things do not belong to hurried hands."
    )
    world.say(
        f"Long after, mothers and fathers would tell how {hero.id} and {cautioner.id} learned that truth before the end of their childhood, "
        f"and how the village kept that lesson like a second relic."
    )


def tell(
    setting: Setting,
    relic: Relic,
    shortcut: Shortcut,
    repair: Repair,
    hero_name: str = "Ione",
    hero_gender: str = "girl",
    cautioner_name: str = "Theron",
    cautioner_gender: str = "boy",
    trait: str = "wise",
    elder_type: str = "priestess",
    delay: int = 0,
    hero_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["dutiful"],
        attrs={"relation": relation},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    world.add(Entity(id="shrine", type="shrine", label="the shrine", sacred=True))
    relic_ent = world.add(Entity(
        id="relic",
        type="relic",
        label=relic.label,
        sacred=True,
        fragile=True,
    ))
    relic_ent.meters["skew"] = 1.0
    hero.memes["pride"] = PRIDE_INIT
    cautioner.memes["wisdom"] = initial_wisdom(trait)

    world.facts.update(
        setting=setting,
        relic_cfg=relic,
        shortcut_cfg=shortcut,
        repair=repair,
        relation=relation,
    )

    dawn_setup(world, hero, cautioner, elder, relic)
    world.para()
    temptation(world, hero, shortcut)
    warning(world, cautioner, hero, relic, shortcut, elder)

    averted = would_avert(relation, hero_age, cautioner_age, trait)

    if averted:
        back_down(world, hero, cautioner, elder, relic)
        world.para()
        rescue(world, elder, repair, relic_ent, relic)
        lesson(world, elder, hero, cautioner, relic)
        world.para()
        honoring_end(world, elder, hero, cautioner, relic, repair)
        contained = True
        severity = 0
    else:
        defy(world, hero, cautioner, shortcut)
        world.para()
        mishap(world, hero, cautioner, relic_ent, relic, shortcut)
        summon(world, cautioner, elder)

        severity = damage_severity(relic, shortcut, delay)
        relic_ent.meters["severity"] = float(severity)
        contained = is_restored(repair, relic, shortcut, delay)

        world.para()
        if contained:
            rescue(world, elder, repair, relic_ent, relic)
            lesson(world, elder, hero, cautioner, relic)
            world.para()
            honoring_end(world, elder, hero, cautioner, relic, repair)
        else:
            rescue_fail(world, elder, repair, relic_ent, relic)
            austere_end(world, elder, hero, cautioner, relic)

    outcome = "averted" if averted else ("restored" if contained else "lost")
    world.facts.update(
        hero=hero,
        cautioner=cautioner,
        elder=elder,
        relic=relic_ent,
        outcome=outcome,
        ignited=relic_ent.meters["crack"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        promised=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "sun_hill": Setting(
        id="sun_hill",
        place="the Hill of First Fire",
        sky="eastern sky",
        stone="red stone",
        affords={"sun_mirror", "dawn_banner"},
    ),
    "river_steps": Setting(
        id="river_steps",
        place="the River Steps of Nera",
        sky="river-bright sky",
        stone="wet black stone",
        affords={"sun_mirror", "rain_bell"},
    ),
    "moon_court": Setting(
        id="moon_court",
        place="the Moon Court above the olives",
        sky="silver-blue sky",
        stone="white court-stone",
        affords={"dawn_banner", "rain_bell"},
    ),
}

RELICS = {
    "sun_mirror": Relic(
        id="sun_mirror",
        label="sun mirror",
        phrase="the bronze sun mirror",
        signal="cast the first beam into the fields",
        mount="the cedar frame",
        height=3,
        fragility=3,
        sway_text="It spun once, wild as a startled hawk",
        blessing="the kindness of the harvest",
        tags={"mirror", "sun", "sacred"},
    ),
    "rain_bell": Relic(
        id="rain_bell",
        label="rain bell",
        phrase="the blue rain bell",
        signal="wake the cloud spirits with a clear note",
        mount="the forked beam",
        height=2,
        fragility=2,
        sway_text="It rang a broken note and swung in a wide circle",
        blessing="the memory of rain",
        tags={"bell", "rain", "sacred"},
    ),
    "dawn_banner": Relic(
        id="dawn_banner",
        label="dawn banner",
        phrase="the dawn banner of saffron wool",
        signal="tell the valley that day had begun",
        mount="the high pole",
        height=1,
        fragility=1,
        sway_text="The cloth snapped hard in the wind",
        blessing="the courage of morning",
        tags={"banner", "dawn", "sacred"},
    ),
}

SHORTCUTS = {
    "tossing_stone": Shortcut(
        id="tossing_stone",
        label="a smooth river stone",
        phrase="a smooth river stone",
        reach=3,
        force=3,
        sound="Clack!",
        warning="one must never jar a sacred thing from below",
        tags={"stone", "throwing"},
    ),
    "reed_pole": Shortcut(
        id="reed_pole",
        label="the long reed pole",
        phrase="the long reed pole",
        reach=2,
        force=2,
        sound="Thup!",
        warning="a long reach without a steady grip is only pride with more length",
        tags={"pole", "reaching"},
    ),
    "step_stool": Shortcut(
        id="step_stool",
        label="the little step stool",
        phrase="the little step stool",
        reach=1,
        force=1,
        sound="Tap!",
        warning="small feet should not climb after high duties alone",
        tags={"stool", "climbing"},
    ),
}

REPAIRS = {
    "ladder_team": Repair(
        id="ladder_team",
        sense=3,
        power=3,
        text="set a cedar ladder beneath {mount}, held it firm, and straightened {relic} with both hands",
        fail="set a cedar ladder beneath {mount} and reached for {relic}, but the damage had already spread through its frame",
        qa_text="used a steady ladder and two careful hands to set it right",
        gift="a plaited cord of sunrise thread",
        tags={"ladder", "repair"},
    ),
    "rope_and_hook": Repair(
        id="rope_and_hook",
        sense=3,
        power=4,
        text="threw a guiding rope over {mount}, lowered {relic} safely, and bound it straight again",
        fail="lowered {relic} with a guiding rope from {mount}, but its sacred body had already split too deeply",
        qa_text="used a guiding rope to lower it safely and mend it",
        gift="a small bronze hook wrapped in blue cloth",
        tags={"rope", "repair"},
    ),
    "bare_hands": Repair(
        id="bare_hands",
        sense=1,
        power=1,
        text="reached up on tiptoe and tried to settle {relic} by touch alone",
        fail="reached up on tiptoe and tried to settle {relic} by touch alone, but it slipped beyond saving",
        qa_text="tried to fix it with bare hands alone",
        gift="nothing at all",
        tags={"hands", "repair"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Myra", "Daphne", "Rhea", "Lysa", "Elara", "Nysa"]
BOY_NAMES = ["Theron", "Aren", "Leos", "Pyrros", "Nikos", "Damon", "Iasos", "Kiron"]
TRAITS = ["wise", "patient", "careful", "steady", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_repairs():
        return combos
    for setting_id, setting in SETTINGS.items():
        for relic_id, relic in RELICS.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if hazard_at_risk(setting, relic, shortcut):
                    combos.append((setting_id, relic_id, shortcut_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    relic: str
    shortcut: str
    repair: str
    hero: str
    hero_gender: str
    cautioner: str
    cautioner_gender: str
    elder: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
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
    "mirror": [(
        "Why did people use mirrors in old myths?",
        "In many myths, a mirror can catch and send light, so it stands for truth, warning, or the favor of the sun."
    )],
    "sun": [(
        "Why is sunrise important in stories?",
        "Sunrise often means a new beginning. It can show that the dark part is over and a lesson has become clear."
    )],
    "bell": [(
        "What does a bell do in a story?",
        "A bell makes a clear sound that calls people to listen. In myths, that sound can also stand for order returning."
    )],
    "banner": [(
        "Why can a banner matter in a myth?",
        "A banner shows a sign that everyone can see. It can tell people what the day means or whom they should remember."
    )],
    "stone": [(
        "Why is throwing a stone at something risky?",
        "A thrown stone hits hard and fast. It can crack or knock down something fragile before anyone can stop it."
    )],
    "pole": [(
        "Why can a long pole be hard to control?",
        "A long pole reaches far, but the far end wobbles more than your hands do. That makes gentle work harder, not easier."
    )],
    "stool": [(
        "Why is a small stool not safe for high work?",
        "A small stool can tip or leave you stretching too far. High work needs steady support and careful balance."
    )],
    "ladder": [(
        "Why is a ladder safer than reaching from below?",
        "A ladder brings your hands close to the work and lets someone hold it steady. That gives you more control."
    )],
    "rope": [(
        "What can a rope help people do?",
        "A rope can lower or guide something carefully. It helps people share the weight instead of jerking at it."
    )],
    "sacred": [(
        "What does sacred mean?",
        "Sacred means people believe something should be treated with special care and respect. You do not rush or play roughly with it."
    )],
}
KNOWLEDGE_ORDER = ["sacred", "mirror", "sun", "bell", "banner", "stone", "pole", "stool", "ladder", "rope"]


def pair_noun(hero: Entity, cautioner: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and cautioner.type == "boy":
            return "two siblings"
        if hero.type == "girl" and cautioner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young helpers"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cautioner = f["cautioner"]
    relic_cfg = f["relic_cfg"]
    shortcut = f["shortcut_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth for a 3-to-5-year-old where children look up at a sacred object hanging skew at dawn, '
        f'and one child is tempted to fix it with {shortcut.phrase}. Include the words "look", "skew", and "end".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle myth where {hero.id} wants to hurry, but {cautioner.id} gives wiser counsel, so they fetch help and learn patience.",
            f'Write a mythic lesson-learned story where nobody breaks {relic_cfg.label}, and by the end the children understand that sacred work must not be rushed.',
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a cautionary myth where {hero.id} ignores a warning, harms {relic_cfg.label}, and the village learns a solemn lesson before the end of dawn.",
            f'Write a child-facing myth with a sad but clear lesson: pride reaches too quickly, and patience would have kept the holy sign safe.',
        ]
    return [
        base,
        f"Tell a myth where {hero.id} hurries, the sacred object is hurt, and a calm elder repairs it and teaches the children what true care means.",
        f'Write a lesson-learned myth that begins with a skew relic, turns with a dangerous mistake, and ends in restored order and wiser hearts.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    cautioner = f["cautioner"]
    elder = f["elder"]
    relic_cfg = f["relic_cfg"]
    shortcut = f["shortcut_cfg"]
    repair = f["repair"]
    relation = f["relation"]
    pair = pair_noun(hero, cautioner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {cautioner.id}, and the {elder.label_word} who cares for the shrine. They begin the story at dawn with a sacred duty."
        ),
        (
            f"What did the children see when they looked up?",
            f"They saw {relic_cfg.phrase} hanging skew instead of straight. That mattered because the people believed it should greet the sunrise in the right way."
        ),
        (
            f"Why did {hero.id} want to act quickly?",
            f"{hero.id} was afraid the dawn sign would fail if nobody fixed it at once. Pride mixed with duty, so the fast plan began to feel like the brave one."
        ),
        (
            f"Why did {cautioner.id} warn {hero.id}?",
            f"{cautioner.id} warned that using {shortcut.label} from below could make the relic swing, crack, or even fall. The warning came from understanding that sacred things need steady help, not a hurried reach."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {cautioner.id} spoke?",
            f"{hero.id} stopped and chose not to touch the relic alone. Then they woke the {elder.label_word}, and the shrine was set right safely."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that being quick is not the same as being wise. By the end, they understood that asking for proper help can be the bravest choice."
        ))
    elif f["outcome"] == "restored":
        qa.append((
            f"What went wrong when {hero.id} used {shortcut.label}?",
            f"The relic lurched and was hurt instead of helped. The danger came from trying to guide something high and fragile with a rough, distant touch."
        ))
        qa.append((
            f"How did the {elder.label_word} set things right?",
            f"The {elder.label_word} {repair.qa_text}. That careful method worked because it gave close control and did not jar the sacred object again."
        ))
        qa.append((
            "What lesson did the ending teach?",
            f"The ending teaches that sacred work should be done with patience and help. The children keep that lesson after the shrine is restored, so the change lasts beyond the morning."
        ))
    else:
        qa.append((
            f"Could the {elder.label_word} save {relic_cfg.label} in time?",
            f"No. The elder came quickly, but the damage was already too deep, so the relic could not be restored before sunrise."
        ))
        qa.append((
            "How did the story end?",
            f"It ended in silence and sorrow, but also with understanding. The village lost a holy sign, and the children learned never to let pride rush their hands again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["relic_cfg"].tags) | set(f["shortcut_cfg"].tags) | {"sacred"}
    if f["outcome"] in {"averted", "restored"}:
        tags |= set(f["repair"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.sacred:
            bits.append("sacred=True")
        if ent.fragile:
            bits.append("fragile=True")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="sun_hill",
        relic="sun_mirror",
        shortcut="reed_pole",
        repair="rope_and_hook",
        hero="Ione",
        hero_gender="girl",
        cautioner="Theron",
        cautioner_gender="boy",
        elder="priestess",
        trait="wise",
        delay=0,
        hero_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        setting="river_steps",
        relic="rain_bell",
        shortcut="reed_pole",
        repair="ladder_team",
        hero="Aren",
        hero_gender="boy",
        cautioner="Myra",
        cautioner_gender="girl",
        elder="priest",
        trait="patient",
        delay=0,
        hero_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        setting="sun_hill",
        relic="sun_mirror",
        shortcut="tossing_stone",
        repair="ladder_team",
        hero="Thaleia",
        hero_gender="girl",
        cautioner="Leos",
        cautioner_gender="boy",
        elder="priestess",
        trait="careful",
        delay=1,
        hero_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        setting="moon_court",
        relic="dawn_banner",
        shortcut="step_stool",
        repair="ladder_team",
        hero="Damon",
        hero_gender="boy",
        cautioner="Nysa",
        cautioner_gender="girl",
        elder="priest",
        trait="steady",
        delay=0,
        hero_age=6,
        cautioner_age=4,
        relation="friends",
    ),
    StoryParams(
        setting="river_steps",
        relic="sun_mirror",
        shortcut="tossing_stone",
        repair="rope_and_hook",
        hero="Rhea",
        hero_gender="girl",
        cautioner="Kiron",
        cautioner_gender="boy",
        elder="priestess",
        trait="thoughtful",
        delay=0,
        hero_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
]


def explain_rejection(setting: Setting, relic: Relic, shortcut: Shortcut) -> str:
    if relic.id not in setting.affords:
        return (
            f"(No story: {relic.label} does not belong at {setting.place}, so the shrine premise does not hold there.)"
        )
    if shortcut.reach < relic.height:
        return (
            f"(No story: {shortcut.label} cannot reach {relic.label} from below, so no real temptation or damage could happen. "
            f"Pick a shortcut that can actually reach the relic.)"
        )
    return "(No story: this combination does not create a plausible shrine mishap.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.cautioner_age, params.trait):
        return "averted"
    repair = REPAIRS[params.repair]
    relic = RELICS[params.relic]
    shortcut = SHORTCUTS[params.shortcut]
    return "restored" if is_restored(repair, relic, shortcut, params.delay) else "lost"


ASP_RULES = r"""
hazard(S, R, C) :- setting(S), relic(R), shortcut(C), affords(S, R), reach(C, Hc), height(R, Hr), Hc >= Hr.
sensible(P) :- repair(P), sense(P, Sc), sense_min(M), Sc >= M.
valid(S, R, C) :- hazard(S, R, C).

wise_now(T) :- trait(T), wise_trait(T).
init_wisdom(5) :- trait(T), wise_now(T).
init_wisdom(3) :- trait(T), not wise_now(T).
older_sibling :- relation(siblings), hero_age(H), cautioner_age(C), C > H.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(W + 1 + B) :- init_wisdom(W), bonus(B).
averted :- older_sibling, authority(A), pride_init(P), A > P.

severity(F + G - 1 + D) :- chosen_relic(R), fragility(R, F), chosen_shortcut(C), force(C, G), delay(D).
restored :- chosen_repair(P), power(P, Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(lost) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for relic_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, relic_id))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("height", relic_id, relic.height))
        lines.append(asp.fact("fragility", relic_id, relic.fragility))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("reach", shortcut_id, shortcut.reach))
        lines.append(asp.fact("force", shortcut_id, shortcut.force))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_relic", params.relic),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
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

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} python={sorted(python_repairs)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic shrine, a skew relic, a hurried child, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the damage goes before the elder intervenes")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))
    if args.setting and args.relic and args.shortcut:
        setting = SETTINGS[args.setting]
        relic = RELICS[args.relic]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_at_risk(setting, relic, shortcut):
            raise StoryError(explain_rejection(setting, relic, shortcut))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.relic is None or combo[1] == args.relic)
        and (args.shortcut is None or combo[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, relic_id, shortcut_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    hero, hero_gender = _pick_child(rng)
    cautioner, cautioner_gender = _pick_child(rng, avoid=hero)
    elder = args.elder or rng.choice(["priestess", "priest"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        setting=setting_id,
        relic=relic_id,
        shortcut=shortcut_id,
        repair=repair_id,
        hero=hero,
        hero_gender=hero_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        elder=elder,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    setting = SETTINGS[params.setting]
    relic = RELICS[params.relic]
    shortcut = SHORTCUTS[params.shortcut]
    if not hazard_at_risk(setting, relic, shortcut):
        raise StoryError(explain_rejection(setting, relic, shortcut))

    world = tell(
        setting=setting,
        relic=relic,
        shortcut=shortcut,
        repair=REPAIRS[params.repair],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        elder_type=params.elder,
        delay=params.delay,
        hero_age=params.hero_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, relic, shortcut) combos:\n")
        for setting_id, relic_id, shortcut_id in combos:
            print(f"  {setting_id:11} {relic_id:12} {shortcut_id}")
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
            header = f"### {p.hero} & {p.cautioner}: {p.relic} at {p.setting} with {p.shortcut} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
