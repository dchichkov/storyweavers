#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py
===========================================================

A standalone story world about a child-sized adventure that turns on one risky
shortcut, a warning that quietly foreshadows trouble, and a safer ending that
proves what changed.

Premise
-------
Two children are playing at being explorers on a trail near a stream. They want
to reach a lookout prize on the far side. One child wants to hurry across a
risky shortcut. The other child stops to stare at small clues first: wobbling
wood, slick moss, or chattering water. Those clues foreshadow what will happen
if they rush.

World logic
-----------
This world models:

* typed entities with physical meters and emotional memes
* a simple forward-chaining causal engine
* a reasonableness gate over which shortcuts are truly risky and which rescues
  are sensible
* an inline ASP twin for the same gate and outcome logic
* three QA sets generated from the simulated world state, not by parsing English

Run it
------
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py --json
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/stare_foreshadowing_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful", "steady", "observant"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    stable: bool = True
    slippery: bool = False
    safe_route: bool = False
    rescue_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "ranger_woman"}
        male = {"boy", "father", "dad", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }
        return mapping.get(self.type, self.type)
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
    far_place: str
    trail_word: str
    water: str
    prize: str
    send_off: str
    ending_image: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    clue: str
    omen: str
    failure: str
    severity: int
    stable: bool = False
    slippery: bool = True
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
class SafeRoute:
    id: str
    label: str
    phrase: str
    method: str
    ending: str
    safe: bool = True
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
class Rescue:
    id: str
    sense: int
    power: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "watcher"}]

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    crossing = world.get("shortcut")
    if crossing.meters["used"] < THRESHOLD:
        return out
    if crossing.stable and not crossing.slippery:
        return out
    sig = ("slip", crossing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crossing.meters["shifted"] += 1
    world.get("leader").meters["soaked"] += 1
    world.get("leader").memes["fear"] += 1
    world.get("watcher").memes["fear"] += 1
    world.get("stream").meters["danger"] += 1
    out.append("__slip__")
    return out


def _r_chill(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    if leader.meters["soaked"] < THRESHOLD:
        return out
    sig = ("chill", leader.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.meters["cold"] += 1
    out.append("__cold__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="chill", tag="physical", apply=_r_chill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(shortcut: Shortcut, route: SafeRoute) -> bool:
    return (not shortcut.stable or shortcut.slippery) and route.safe


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def shortcut_severity(shortcut: Shortcut, delay: int) -> int:
    return shortcut.severity + delay


def is_contained(rescue: Rescue, shortcut: Shortcut, delay: int) -> bool:
    return rescue.power >= shortcut_severity(shortcut, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, leader_age: int, watcher_age: int, trait: str) -> bool:
    watcher_older = relation == "siblings" and watcher_age > leader_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if watcher_older else 0.0)
    return watcher_older and authority > BRAVERY_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    sim.get("shortcut").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "slip": sim.get("leader").meters["soaked"] >= THRESHOLD,
        "danger": sim.get("stream").meters["danger"],
        "cold": sim.get("leader").meters["cold"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} set out along {setting.place} like young adventurers."
    )
    world.say(
        f"They wanted to reach {setting.far_place}, where {setting.prize} waited, and {setting.send_off}."
    )


def discover(world: World, a: Entity, b: Entity, setting: Setting, shortcut: Shortcut, route: SafeRoute) -> None:
    world.say(
        f"Soon the trail met {setting.water}. On one side stood {route.phrase}. On the other lay {shortcut.phrase}."
    )
    world.say(
        f'"That way is quicker," {a.id} said, pointing at {shortcut.label}.'
    )
    world.say(
        f"{b.id} stopped to stare for a moment instead of hurrying."
    )


def foreshadow(world: World, b: Entity, shortcut: Shortcut) -> None:
    pred = predict_slip(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_cold"] = pred["cold"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} listened to the little sounds around them and trusted the warning in {b.pronoun('possessive')} chest."
    world.say(
        f"{b.id} noticed {shortcut.clue}. It felt like the trail was whispering ahead of time that {shortcut.omen}.{extra}"
    )
    world.say(
        f'"Please don\'t rush," {b.id} said. "I think {shortcut.label} could slip."'
    )


def tempt(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} grinned. "Real explorers do not turn back from {shortcut.label}," {a.pronoun()} said.'
    )


def back_down(world: World, a: Entity, b: Entity, shortcut: Shortcut, route: SafeRoute) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sib = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at {shortcut.label} again, then at {b.id}, {a.pronoun("possessive")} older {sib}, and let out a long breath.'
    )
    world.say(
        f'"All right," {a.pronoun()} said. "We will take {route.label}." The danger stayed only a warning, not an accident.'
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        title = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Come on," {a.id} said. Even though {b.id} still looked worried, {a.id} was {b.pronoun("possessive")} {title}, so {b.id} could not quite stop {a.pronoun("object")}.'
        )
    else:
        world.say(
            f'"Come on," {a.id} said, and stepped toward {shortcut.label} before {b.id} could stop {a.pronoun("object")}.'
        )


def cross(world: World, a: Entity, shortcut: Shortcut) -> None:
    world.get("shortcut").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} put one foot onto {shortcut.label}, then another."
    )
    if world.get("leader").meters["soaked"] >= THRESHOLD:
        world.say(shortcut.failure)
    else:
        world.say(
            f"{shortcut.label.capitalize()} held still beneath {a.pronoun('possessive')} shoes."
        )


def alarm(world: World, a: Entity, b: Entity, helper: Entity) -> None:
    if world.get("leader").meters["soaked"] >= THRESHOLD:
        world.say(
            f'"{a.id}!" {b.id} cried. "{helper.label_word.capitalize()}!"'
        )


def rescue_success(world: World, helper: Entity, rescue: Rescue, route: SafeRoute) -> None:
    leader = world.get("leader")
    leader.meters["soaked"] = 0.0
    leader.meters["cold"] = 0.0
    world.get("stream").meters["danger"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came running and {rescue.text}."
    )
    world.say(
        f'Soon both children were back on the bank, breathing hard but safe. "{route.method}," the ranger said. "Adventure is better when everyone gets across."'
    )


def rescue_fail(world: World, helper: Entity, rescue: Rescue) -> None:
    world.get("stream").meters["danger"] += 1
    world.get("leader").meters["soaked"] += 1
    world.get("leader").meters["cold"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came running and {rescue.fail}."
    )
    world.say(
        "The water shoved at little legs, and the prize on the far side no longer mattered at all."
    )


def escape(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} grabbed both children under the arms and guided them away from the racing water."
    )
    world.say(
        "They sat on a dry rock while their wet socks dripped and the stream roared on as if nothing had happened."
    )


def lesson(world: World, helper: Entity, shortcut: Shortcut, route: SafeRoute) -> None:
    for kid in world.kids():
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'The ranger knelt beside them. "The trail gave you clues," {helper.pronoun()} said softly. "When you stop and stare, you can notice danger before danger notices you."'
    )
    world.say(
        f'"Next time," {helper.pronoun()} added, "choose {route.label} over {shortcut.label}."'
    )


def grim_lesson(world: World, helper: Entity, route: SafeRoute) -> None:
    for kid in world.kids():
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'The ranger wrapped them in dry towels from the trail pack. "You are safe, and that is what matters," {helper.pronoun()} said.'
    )
    world.say(
        f'Then {helper.pronoun()} pointed back to {route.label}. "A true adventure can wait for the safer path."'
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting, route: SafeRoute) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later, they crossed by {route.label} instead. {route.ending}"
    )
    world.say(
        f"At {setting.far_place}, {setting.ending_image}"
    )


def tell(
    setting: Setting,
    shortcut_cfg: Shortcut,
    route_cfg: SafeRoute,
    rescue_cfg: Rescue,
    leader_name: str = "Tara",
    leader_gender: str = "girl",
    watcher_name: str = "Owen",
    watcher_gender: str = "boy",
    helper_type: str = "ranger_woman",
    trait: str = "observant",
    delay: int = 0,
    leader_age: int = 6,
    watcher_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        age=leader_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=watcher_name,
        kind="character",
        type=watcher_gender,
        role="watcher",
        age=watcher_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the ranger",
        attrs={},
    ))
    world.add(Entity(
        id="stream",
        kind="thing",
        type="stream",
        label=setting.water,
        attrs={},
    ))
    world.add(Entity(
        id="shortcut",
        kind="thing",
        type="shortcut",
        label=shortcut_cfg.label,
        stable=shortcut_cfg.stable,
        slippery=shortcut_cfg.slippery,
        attrs={},
    ))
    world.add(Entity(
        id="route",
        kind="thing",
        type="safe_route",
        label=route_cfg.label,
        safe_route=route_cfg.safe,
        attrs={},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.facts["relation"] = relation

    introduce(world, a, b, setting)
    discover(world, a, b, setting, shortcut_cfg, route_cfg)

    world.para()
    foreshadow(world, b, shortcut_cfg)
    tempt(world, a, shortcut_cfg)

    averted = would_avert(relation, leader_age, watcher_age, trait)
    if averted:
        back_down(world, a, b, shortcut_cfg, route_cfg)
        world.para()
        ending(world, a, b, setting, route_cfg)
        severity = 0
        contained = True
    else:
        defy(world, a, b, shortcut_cfg)
        world.para()
        cross(world, a, shortcut_cfg)
        severity = shortcut_severity(shortcut_cfg, delay)
        world.get("shortcut").meters["severity"] = float(severity)
        slipped = world.get("leader").meters["soaked"] >= THRESHOLD
        if slipped:
            alarm(world, a, b, helper)
            world.para()
            contained = is_contained(rescue_cfg, shortcut_cfg, delay)
            if contained:
                rescue_success(world, helper, rescue_cfg, route_cfg)
                lesson(world, helper, shortcut_cfg, route_cfg)
                world.para()
                ending(world, a, b, setting, route_cfg)
            else:
                rescue_fail(world, helper, rescue_cfg)
                escape(world, helper, a, b)
                grim_lesson(world, helper, route_cfg)
        else:
            contained = True
            world.para()
            lesson(world, helper, shortcut_cfg, route_cfg)
            ending(world, a, b, setting, route_cfg)

    outcome = "averted" if averted else ("contained" if contained else "soaked")
    world.facts.update(
        leader=a,
        watcher=b,
        helper=helper,
        setting=setting,
        shortcut_cfg=shortcut_cfg,
        route_cfg=route_cfg,
        rescue=rescue_cfg,
        outcome=outcome,
        slipped=world.get("leader").meters["soaked"] >= THRESHOLD or outcome == "soaked",
        severity=severity,
        delay=delay,
        promised=world.get("watcher").memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "pine_trail": Setting(
        id="pine_trail",
        place="the pine trail",
        far_place="the lookout rock",
        trail_word="trail",
        water="a quick silver stream",
        prize="a red explorer flag tied to a branch",
        send_off="they marched as if they were following a secret map",
        ending_image="they touched the red flag and watched the valley shine below them",
        tags={"trail", "stream", "lookout"},
    ),
    "fern_glen": Setting(
        id="fern_glen",
        place="the fern glen path",
        far_place="the mossy hill",
        trail_word="path",
        water="a laughing creek",
        prize="a brass bell hanging from an old post",
        send_off="their boots crunched like brave little footsteps in a story",
        ending_image="they rang the brass bell and heard the clear note float over the ferns",
        tags={"trail", "creek", "bell"},
    ),
    "sun_cliff": Setting(
        id="sun_cliff",
        place="the cliffside trail",
        far_place="the sun marker",
        trail_word="trail",
        water="a narrow rushing brook",
        prize="a painted sun marker nailed to a stump",
        send_off="they kept checking their folded map like real pathfinders",
        ending_image="they tapped the painted marker and laughed at how far they had come",
        tags={"trail", "brook", "marker"},
    ),
}

SHORTCUTS = {
    "log": Shortcut(
        id="log",
        label="the fallen log",
        phrase="a fallen log stretched from bank to bank",
        clue="wet moss shining on the bark",
        omen="one quick step would send somebody splashing into the stream",
        failure="The bark rolled underfoot. With a yelp, the leader splashed into the cold water up to the knees.",
        severity=2,
        stable=False,
        slippery=True,
        tags={"log", "moss", "slip"},
    ),
    "stones": Shortcut(
        id="stones",
        label="the stepping stones",
        phrase="a row of stepping stones poked out of the water",
        clue="water slapping hard at the last stone",
        omen="the stones would wobble if someone rushed them",
        failure="One stone tipped like a loose tooth. With a splash, the leader sat down in the stream.",
        severity=2,
        stable=False,
        slippery=True,
        tags={"stones", "water", "slip"},
    ),
    "plank": Shortcut(
        id="plank",
        label="the old plank",
        phrase="an old plank lay over the narrowest part",
        clue="one end of the plank lifting a little each time the water bumped it",
        omen="the plank would skid sideways under a fast step",
        failure="The plank skidded with a sharp scrape, and the leader splashed into the rushing edge of the brook.",
        severity=3,
        stable=False,
        slippery=True,
        tags={"plank", "water", "slip"},
    ),
    "dry_rocks": Shortcut(
        id="dry_rocks",
        label="the dry rocks",
        phrase="wide dry rocks made a neat little crossing",
        clue="the rocks sat flat and still",
        omen="nothing bad would happen at all",
        failure="The crossing stayed easy and dry.",
        severity=0,
        stable=True,
        slippery=False,
        tags={"rocks"},
    ),
}

SAFE_ROUTES = {
    "bridge": SafeRoute(
        id="bridge",
        label="the wooden bridge",
        phrase="the wooden bridge with a hand rope",
        method="use the bridge and hold the rope",
        ending="Their feet stayed dry, and the boards answered with solid thumps.",
        safe=True,
        tags={"bridge", "safe_path"},
    ),
    "ford": SafeRoute(
        id="ford",
        label="the shallow ford",
        phrase="the shallow ford with flat gravel under it",
        method="cross at the shallow ford, one slow step at a time",
        ending="The water only whispered around their boots, and the gravel did not slide.",
        safe=True,
        tags={"ford", "safe_path"},
    ),
    "switchback": SafeRoute(
        id="switchback",
        label="the long switchback path",
        phrase="the long switchback path around the stream",
        method="take the long path when the short one looks tricky",
        ending="It took longer, but every step felt sure and calm.",
        safe=True,
        tags={"path", "safe_path"},
    ),
}

RESCUES = {
    "rope": Rescue(
        id="rope",
        sense=3,
        power=4,
        text="swung a rescue rope across the water and pulled the child back to shore hand over hand",
        fail="threw a rescue rope, but the child had already been swept too far downstream for a quick pull",
        qa_text="used a rescue rope to pull the child back to shore",
        tags={"rope", "ranger", "rescue"},
    ),
    "staff": Rescue(
        id="staff",
        sense=2,
        power=2,
        text="braced a long ranger staff in the stream and helped the child grab it and climb back out",
        fail="reached out with a ranger staff, but the current shoved too hard for that to be enough",
        qa_text="reached out with a ranger staff so the child could climb back out",
        tags={"staff", "ranger", "rescue"},
    ),
    "jump_in": Rescue(
        id="jump_in",
        sense=2,
        power=3,
        text="splashed in up to the boots, caught the child by the jacket, and steered the child back to shore",
        fail="jumped in after the child, but the water was already too wild to guide anyone safely that way",
        qa_text="went into the water and guided the child back to shore",
        tags={"water", "ranger", "rescue"},
    ),
    "shout": Rescue(
        id="shout",
        sense=1,
        power=1,
        text="shouted directions from the bank until the child found the shore alone",
        fail="shouted from the bank, but a voice alone could not fight the push of the water",
        qa_text="shouted directions from the bank",
        tags={"voice", "ranger"},
    ),
}

GIRL_NAMES = ["Tara", "Nina", "Ruby", "Elsie", "Maya", "Wren", "Ava", "Lina"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Max", "Eli", "Theo", "Jude", "Noah"]
TRAITS = ["careful", "patient", "thoughtful", "steady", "observant", "curious"]


@dataclass
class StoryParams:
    setting: str
    shortcut: str
    route: str
    rescue: str
    leader: str
    leader_gender: str
    watcher: str
    watcher_gender: str
    helper: str
    trait: str
    delay: int = 0
    leader_age: int = 6
    watcher_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "log": [(
        "Why can a wet log be dangerous to walk on?",
        "A wet log can be slippery, so feet can slide right off it. Moss and water make it harder to keep your balance."
    )],
    "stones": [(
        "Why can stepping stones be tricky?",
        "Stepping stones can wobble or be slick with water. If you hurry, one small slip can make you fall into the stream."
    )],
    "plank": [(
        "Why is an old plank risky over water?",
        "An old plank may shift or skid if it is loose. Over water, that means a tiny mistake can turn into a fall."
    )],
    "bridge": [(
        "Why is a bridge safer than a slippery shortcut?",
        "A bridge is built for crossing, so it gives your feet a steadier place to step. Holding a rope or rail helps you balance too."
    )],
    "ford": [(
        "What is a shallow ford?",
        "A shallow ford is a place where the water is low enough to walk across carefully. People still have to go slowly and pick steady steps."
    )],
    "path": [(
        "Why is the long way sometimes the best way?",
        "The long way can be safer if the short way is risky. A real adventurer cares about getting everyone home, not just getting there fast."
    )],
    "rope": [(
        "What does a rescue rope do?",
        "A rescue rope gives someone a strong line to hold while another person pulls from safety. It helps when the ground or water is too dangerous to trust."
    )],
    "staff": [(
        "Why would a ranger use a long staff near water?",
        "A long staff lets the ranger reach someone without standing too close to the slippery edge. It also gives the person something firm to grab."
    )],
    "stream": [(
        "Why can a stream be dangerous even if it looks pretty?",
        "Moving water pushes against your legs and can knock you off balance. Cold water can also make your body feel weak and shaky very fast."
    )],
    "foreshadow": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when small clues hint at what may happen later. It makes the later event feel earned instead of surprising for no reason."
    )],
    "stare": [(
        "Why can it help to stop and stare before you do something hard?",
        "Stopping to stare gives you time to notice clues you might miss while rushing. Careful looking can keep an adventure from turning into an accident."
    )],
}
KNOWLEDGE_ORDER = ["stare", "foreshadow", "stream", "log", "stones", "plank", "bridge", "ford", "path", "rope", "staff"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for shortcut_id, shortcut in SHORTCUTS.items():
            for route_id, route in SAFE_ROUTES.items():
                if hazard_at_risk(shortcut, route):
                    combos.append((setting_id, shortcut_id, route_id))
    return combos


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["watcher"]
    setting = f["setting"]
    shortcut = f["shortcut_cfg"]
    route = f["route_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "stare" and uses foreshadowing. Two children on {setting.place} find {shortcut.label} and must choose how to cross.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle adventure where {b.id} stops to stare at warning clues, foreshadows trouble, and talks {a.id} into choosing {route.label} before anyone falls.",
            f"Write a story where careful noticing turns a dangerous shortcut into a wise decision, and the ending shows the children reaching {setting.far_place} safely.",
        ]
    if outcome == "soaked":
        return [
            base,
            f"Tell an adventure where the warning clues really mean something: {a.id} rushes onto {shortcut.label}, falls into the water, and a ranger must rescue the children before the adventure can continue.",
            f'Write a foreshadowing story where a child ignores what a careful stare reveals, and the ending teaches that the safer path matters more than the quickest one.',
        ]
    return [
        base,
        f"Tell an adventure where {b.id} stops to stare, notices danger ahead of time, and later those clues prove true when {a.id} slips and a ranger helps.",
        f"Write a child-facing story with foreshadowing, a small water rescue, and a bright ending at {setting.far_place} that proves the children learned to choose {route.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["watcher"]
    helper = f["helper"]
    setting = f["setting"]
    shortcut = f["shortcut_cfg"]
    route = f["route_cfg"]
    rescue = f["rescue"]
    relation = f.get("relation", "friends")
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, on an adventure near {setting.water}. A ranger also appears when the trail turns dangerous."
        ),
        (
            f"Why did {b.id} stop to stare?",
            f"{b.id} stopped to stare because {b.pronoun()} noticed {shortcut.clue}. That clue foreshadowed that {shortcut.label} was not as safe as it looked."
        ),
        (
            "What was the adventure goal?",
            f"The children wanted to reach {setting.far_place}, where {setting.prize} waited. The goal made the shortcut feel tempting because it looked faster."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"How did the children avoid trouble?",
                f"{b.id} warned {a.id} after noticing the clue, and {a.id} listened. Because they chose {route.label} instead, the danger stayed only a warning and never became an accident."
            ),
            (
                "How did the story end?",
                f"They crossed by {route.label} and reached {setting.far_place} safely. The ending image proves they changed because they finished the adventure without rushing the risky shortcut."
            ),
        ])
    elif f["outcome"] == "contained":
        qa.extend([
            (
                f"What happened when {a.id} tried {shortcut.label}?",
                f"{a.id} slipped and splashed into the cold water. The fall happened for the very reason the earlier clue had warned about."
            ),
            (
                "How did the ranger help?",
                f"The ranger {rescue.qa_text}. That quick help stopped a small accident from becoming a bigger one."
            ),
            (
                "What did the children learn?",
                f"They learned that stopping to stare at clues can save them from trouble. After the rescue, they chose {route.label}, which shows they trusted careful thinking more than rushing."
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the adventure suddenly stop feeling fun?",
                f"It stopped feeling fun when the shortcut accident left the children wet, cold, and scared. Once the stream felt stronger than their game, reaching the prize no longer mattered."
            ),
            (
                "How did the ranger get them safe?",
                f"The ranger tried to help right away and then pulled both children away from the dangerous water. The rescue mattered because getting warm and safe came before finishing the adventure."
            ),
            (
                "What did they learn at the end?",
                f"They learned that a true adventure does not mean taking every risky shortcut. The final lesson points them back to {route.label}, which is the safer choice they should have trusted first."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"stare", "foreshadow", "stream"}
    tags |= set(f["shortcut_cfg"].tags)
    tags |= set(f["route_cfg"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["rescue"].tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (
            ("stable", e.stable),
            ("slippery", e.slippery),
            ("safe_route", e.safe_route),
            ("rescue_tool", e.rescue_tool),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pine_trail",
        shortcut="log",
        route="bridge",
        rescue="rope",
        leader="Tara",
        leader_gender="girl",
        watcher="Owen",
        watcher_gender="boy",
        helper="ranger_woman",
        trait="observant",
        delay=0,
        leader_age=6,
        watcher_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="fern_glen",
        shortcut="stones",
        route="ford",
        rescue="staff",
        leader="Finn",
        leader_gender="boy",
        watcher="Ruby",
        watcher_gender="girl",
        helper="ranger_man",
        trait="patient",
        delay=0,
        leader_age=5,
        watcher_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        setting="sun_cliff",
        shortcut="plank",
        route="switchback",
        rescue="staff",
        leader="Leo",
        leader_gender="boy",
        watcher="Maya",
        watcher_gender="girl",
        helper="ranger_man",
        trait="careful",
        delay=1,
        leader_age=7,
        watcher_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        setting="fern_glen",
        shortcut="plank",
        route="bridge",
        rescue="rope",
        leader="Ava",
        leader_gender="girl",
        watcher="Nina",
        watcher_gender="girl",
        helper="ranger_woman",
        trait="steady",
        delay=0,
        leader_age=5,
        watcher_age=8,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        setting="pine_trail",
        shortcut="plank",
        route="ford",
        rescue="staff",
        leader="Max",
        leader_gender="boy",
        watcher="Elsie",
        watcher_gender="girl",
        helper="ranger_man",
        trait="thoughtful",
        delay=2,
        leader_age=7,
        watcher_age=5,
        relation="siblings",
        trust=2,
    ),
]


def explain_rejection(shortcut: Shortcut, route: SafeRoute) -> str:
    if shortcut.stable and not shortcut.slippery:
        return (
            f"(No story: {shortcut.label} is already steady and safe, so there is no honest danger to foreshadow. Pick a riskier shortcut like the fallen log, stepping stones, or old plank.)"
        )
    if not route.safe:
        return (
            f"(No story: {route.label} is not marked as a genuinely safer route, so the ending would not really solve the problem.)"
        )
    return "(No story: this combination does not make a reasonable adventure problem.)"


def explain_rescue(rid: str) -> str:
    rescue = RESCUES[rid]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rid}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.watcher_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESCUES[params.rescue], SHORTCUTS[params.shortcut], params.delay) else "soaked"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, R) :- shortcut(S), route(R), risky(S), safe_route(R).
valid(St, S, R) :- setting(St), hazard(S, R).

sensible_rescue(Rs) :- rescue(Rs), sense(Rs, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

watcher_older :- relation(siblings), leader_age(LA), watcher_age(WA), WA > LA.
bonus(4) :- watcher_older.
bonus(0) :- not watcher_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- watcher_older, authority(A), bravery_init(BR), A > BR.

severity(V + D) :- chosen_shortcut(S), base_severity(S, V), delay(D).
resc_power(P) :- chosen_rescue(R), power(R, P).
contained :- resc_power(P), severity(SV), P >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(soaked) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("base_severity", sid, s.severity))
        if (not s.stable) or s.slippery:
            lines.append(asp.fact("risky", sid))
    for rid in SAFE_ROUTES:
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("safe_route", rid))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rescues() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_rescue/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_rescue"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("leader_age", params.leader_age),
        asp.fact("watcher_age", params.watcher_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense = set(asp_sensible_rescues())
    p_sense = {r.id for r in sensible_rescues()}
    if c_sense == p_sense:
        print(f"OK: sensible rescues match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed unexpectedly for seed {seed}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify safety net
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: adventure, foreshadowing, and a risky shortcut by water."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--route", choices=SAFE_ROUTES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--helper", choices=["ranger_woman", "ranger_man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before the rescue fully takes effect")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setting/shortcut/route combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shortcut and args.route:
        shortcut = SHORTCUTS[args.shortcut]
        route = SAFE_ROUTES[args.route]
        if not hazard_at_risk(shortcut, route):
            raise StoryError(explain_rejection(shortcut, route))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shortcut_id, route_id = rng.choice(sorted(combos))
    rescue_id = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    leader, leader_gender = _pick_child(rng)
    watcher, watcher_gender = _pick_child(rng, avoid=leader)
    helper = args.helper or rng.choice(["ranger_woman", "ranger_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    leader_age, watcher_age = rng.sample([3, 4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        setting=setting_id,
        shortcut=shortcut_id,
        route=route_id,
        rescue=rescue_id,
        leader=leader,
        leader_gender=leader_gender,
        watcher=watcher,
        watcher_gender=watcher_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        leader_age=leader_age,
        watcher_age=watcher_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        shortcut = SHORTCUTS[params.shortcut]
        route = SAFE_ROUTES[params.route]
        rescue = RESCUES[params.rescue]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter choice: {err.args[0]}.)") from err

    if not hazard_at_risk(shortcut, route):
        raise StoryError(explain_rejection(shortcut, route))
    if rescue.sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        setting=setting,
        shortcut_cfg=shortcut,
        route_cfg=route,
        rescue_cfg=rescue,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
        leader_age=params.leader_age,
        watcher_age=params.watcher_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible_rescue/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        rescues = asp_sensible_rescues()
        print(f"sensible rescues: {', '.join(rescues)}\n")
        print(f"{len(combos)} compatible (setting, shortcut, route) combos:\n")
        for setting_id, shortcut_id, route_id in combos:
            print(f"  {setting_id:11} {shortcut_id:8} {route_id}")
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
            header = (
                f"### {p.leader} & {p.watcher}: {p.shortcut} vs {p.route} "
                f"({p.setting}, {p.rescue}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
