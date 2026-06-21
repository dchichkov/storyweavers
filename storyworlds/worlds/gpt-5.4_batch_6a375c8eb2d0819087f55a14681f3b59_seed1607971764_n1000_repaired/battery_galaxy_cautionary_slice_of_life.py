#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py
=====================================================================

A standalone story world for a small cautionary slice-of-life tale about children
building a cozy pretend galaxy hideout indoors and making one unsafe choice with
a loose battery. The world model prefers a narrow set of plausible stories:

- two children make a "galaxy" play space at home
- the hideout gets too dark to enjoy
- one child tries to use a loose battery and a metal object to make a tiny spark
  or glow
- the metal bridges the battery and gets hot
- an adult stops the danger, explains the rule, and offers a safe light instead

The reasonableness gate is intentionally strict. A story is only valid when:
- the chosen tool is actually metal and can bridge the battery terminals
- the nearby soft object can realistically be singed or scorched by heat
- the chosen adult response clears a minimum common-sense bar

Run it
------
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py --theme galaxy_fort --metal foil_stars --target blanket
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py --target wooden_stool
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py --response blow_on_it
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/battery_galaxy_cautionary_slice_of_life.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


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
    conductive: bool = False
    heat_sensitive: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Theme:
    id: str
    room_line: str
    props_line: str
    titles: tuple[str, str]
    destination: str
    dark_place: str
    nook_word: str
    role_plural: str
    role_solo: str
    ending_line: str
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
class MetalTool:
    id: str
    label: str
    phrase: str
    bridge_text: str
    shiny_text: str
    conductive: bool = True
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
class Target:
    id: str
    label: str
    the: str
    touch_spot: str
    room_text: str
    spread: int = 2
    heat_sensitive: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
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
class Response:
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_hot_danger(world: World) -> list[str]:
    out: list[str] = []
    battery = world.get("battery")
    tool = world.get("tool")
    target = world.get("target")
    if battery.meters["hot"] < THRESHOLD or tool.meters["hot"] < THRESHOLD:
        return out
    sig = ("hot_danger", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if target.heat_sensitive:
        target.meters["scorched"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__hot__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hot_danger", tag="physical", apply=_r_hot_danger),
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


def hazard_at_risk(tool: MetalTool, target: Target) -> bool:
    return tool.conductive and target.heat_sensitive


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def heat_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= heat_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _do_battery_bridge(world: World, narrate: bool = True) -> None:
    battery = world.get("battery")
    tool = world.get("tool")
    battery.meters["hot"] += 1
    battery.meters["used_wrong"] += 1
    tool.meters["hot"] += 1
    propagate(world, narrate=narrate)


def predict_heat(world: World) -> dict:
    sim = world.copy()
    _do_battery_bridge(sim, narrate=False)
    return {
        "gets_hot": sim.get("battery").meters["hot"] >= THRESHOLD,
        "scorches": sim.get("target").meters["scorched"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(f"After supper, {a.id} and {b.id} made {theme.room_line}. {theme.props_line}")
    world.say(
        f'"{theme.titles[0]} {a.id} and {theme.titles[1]} {b.id}!" {a.id} said. '
        f'"Let\'s find {theme.destination}."'
    )


def need_light(world: World, b: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But {theme.dark_place}, {target.room_text}, was too dim to feel like a real {theme.nook_word}."
    )
    world.say(f'{b.id} squinted into it. "It needs a little light," {b.pronoun()} said.')


def tempt(world: World, a: Entity, tool: MetalTool) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted a loose battery on the dresser and {tool.phrase} nearby. '
        f'"Maybe I can make our galaxy shine with these," {a.pronoun()} said.'
    )
    world.say(f"The {tool.label} looked shiny enough to feel like part of the game.")


def warn(world: World, b: Entity, a: Entity, tool: MetalTool, target: Target, parent: Entity) -> None:
    pred = predict_heat(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_scorch"] = pred["scorches"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} pulled {b.pronoun('possessive')} hand back and looked worried."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. If {tool.label} touches both ends of the battery, '
        f"it can get hot fast, and {target.the} could be singed. {parent.label_word.capitalize()} said loose batteries are not for play.\"{extra}"
    )


def defy(world: World, a: Entity, b: Entity, tool: MetalTool) -> None:
    a.memes["defiance"] += 1
    older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_sib:
        world.say(
            f'"It will only be for one second," {a.id} said. Because {a.id} was the older sibling, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"It will only be for one second," {a.id} said, and reached in anyway.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the blanket roof, then at the battery, and let out a breath. '
        f'"Okay," {a.pronoun()} said. "Hot is not starry."'
    )
    world.say(
        f"They left the battery on the dresser and asked {parent.label_word} for help with their dark {theme.nook_word} instead."
    )


def bridge(world: World, tool: MetalTool, target: Target) -> None:
    _do_battery_bridge(world)
    world.say(
        f"{tool.bridge_text} touched both ends of the battery at once. For one blink nothing happened. "
        f"Then the metal bit warmed, then turned hot, and a sharp little smell jumped into the air near {target.touch_spot}."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"Ow! It\'s hot!" {a.id} yelped.')
    world.say(f'"{parent.label_word.upper()}! {target.The}!" {b.id} cried.')


def rescue(world: World, parent: Entity, response: Response, theme: Theme) -> None:
    world.get("battery").meters["hot"] = 0.0
    world.get("tool").meters["hot"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text
    world.say(f"{parent.label_word.capitalize()} came quickly and {body}.")
    world.say(
        f"The hot smell faded, leaving only one little dark mark and two very quiet {theme.role_plural}."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f'{parent.label_word.capitalize()} crouched beside them and held out both hands. '
        f'"I am glad you called me," {parent.pronoun()} said softly. '
        f'"A battery is for the right device, not for experiments in your fingers. '
        f"Metal can make it heat up very fast, and hot batteries can hurt skin and scorch soft things.\""
    )
    world.say(f'"We won\'t play with a battery again," {a.id} and {b.id} said together.')


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme,
              l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next evening, {parent.label_word} brought {l1.phrase} and {l2.phrase}. "
        f"One {l1.glow}, and the other {l2.glow}."
    )
    world.say(
        f'"Now your galaxy can glow the safe way," {parent.pronoun()} said.'
    )
    world.say(
        f"{b.id} tucked the light into the fort, and {a.id} pointed the other one across the blanket roof. "
        f"Soon the room looked like a tiny galaxy again."
    )
    world.say(theme.ending_line)


def rescue_fail(world: World, parent: Entity, response: Response, target: Target) -> None:
    world.get("room").meters["danger"] += 1
    world.get("target").meters["scorched"] += 1
    body = response.fail.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} hurried in and {body}.")
    world.say(
        f"But the heat had already bitten deeper into {target.the}, and the fort had to come down."
    )


def loss_ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} pulled the blanket aside, opened the window, and moved the children back from the fort."
    )
    world.say(
        f"They were safe, but their {theme.nook_word} was over for the night. The blanket smelled singed, and the paper stars had to be thrown away."
    )
    world.say(
        f'On the couch, {parent.label_word} wrapped them close and said, '
        f'"When something uses a battery, you ask a grown-up. A game should never get hotter than your hands can handle."'
    )


def tell(theme: Theme, tool_cfg: MetalTool, target_cfg: Target,
         lights: tuple[SafeLight, SafeLight], response: Response,
         instigator: str = "Milo", instigator_gender: str = "boy",
         cautioner: str = "Ivy", cautioner_gender: str = "girl",
         trait: str = "careful", parent_type: str = "mother",
         delay: int = 0, instigator_age: int = 6, cautioner_age: int = 4,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="battery", type="battery", label="battery"))
    world.add(Entity(
        id="tool",
        type="metal_tool",
        label=tool_cfg.label,
        conductive=tool_cfg.conductive,
    ))
    world.add(Entity(
        id="target",
        type="target",
        label=target_cfg.label,
        heat_sensitive=target_cfg.heat_sensitive,
    ))

    play_setup(world, a, b, theme)
    need_light(world, b, theme, target_cfg)

    world.para()
    tempt(world, a, tool_cfg)
    warn(world, b, a, tool_cfg, target_cfg, parent)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, parent, theme)
        world.para()
        safe_gift(world, parent, a, b, theme, lights[0], lights[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, tool_cfg)

        world.para()
        bridge(world, tool_cfg, target_cfg)
        alarm(world, b, a, target_cfg, parent)

        severity = heat_severity(target_cfg, delay)
        world.get("target").meters["severity"] = float(severity)
        contained = is_contained(response, target_cfg, delay)

        world.para()
        if contained:
            rescue(world, parent, response, theme)
            lesson(world, parent, a, b)
            world.para()
            safe_gift(world, parent, a, b, theme, lights[0], lights[1])
        else:
            rescue_fail(world, parent, response, target_cfg)
            loss_ending(world, parent, a, b, theme)

    outcome = "averted" if averted else ("contained" if contained else "ruined")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        tool_cfg=tool_cfg,
        target_cfg=target_cfg,
        response=response,
        lights=lights,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        scorched=world.get("target").meters["scorched"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "galaxy_fort": Theme(
        id="galaxy_fort",
        room_line="a galaxy fort under the dining table",
        props_line="A blue blanket became the night sky, couch cushions became moon rocks, and paper stars hung from the edge like a homemade galaxy.",
        titles=("Captain", "Scout"),
        destination="the quiet side of the galaxy",
        dark_place="the far back corner",
        nook_word="space cave",
        role_plural="space explorers",
        role_solo="space explorer",
        ending_line="This time the little space explorers curled up under safe stars, and the galaxy stayed soft and calm.",
    ),
    "rocket_bunk": Theme(
        id="rocket_bunk",
        room_line="a rocket cabin between the sofa and the bookshelf",
        props_line="A sheet draped over two chairs, a laundry basket held their supplies, and a marker map showed a winding path through the galaxy.",
        titles=("Pilot", "Navigator"),
        destination="the star gate",
        dark_place="the little cargo corner",
        nook_word="rocket nook",
        role_plural="crew mates",
        role_solo="crew mate",
        ending_line="Soon the crew mates whispered under safe light, and their pretend rocket floated gently through the galaxy.",
    ),
    "star_tent": Theme(
        id="star_tent",
        room_line="a star tent in the bedroom",
        props_line="Two chairs held up a quilt, stuffed animals waited like sleepy aliens, and a silver scarf became the edge of a shining galaxy.",
        titles=("Commander", "Observer"),
        destination="the bright ring of the galaxy",
        dark_place="the tucked-away reading spot",
        nook_word="star tent",
        role_plural="star watchers",
        role_solo="star watcher",
        ending_line="After that, the star watchers lay shoulder to shoulder and watched their safe little galaxy glow above them.",
    ),
}

TOOLS = {
    "foil_stars": MetalTool(
        id="foil_stars",
        label="foil stars",
        phrase="a chain of foil stars",
        bridge_text="The edge of the foil stars",
        conductive=True,
        tags={"metal", "foil"},
    ),
    "paper_clips": MetalTool(
        id="paper_clips",
        label="paper clips",
        phrase="a handful of paper clips",
        bridge_text="Two paper clips linked together",
        conductive=True,
        tags={"metal", "paper_clips"},
    ),
    "key_ring": MetalTool(
        id="key_ring",
        label="a key ring",
        phrase="a shiny key ring",
        bridge_text="The round key ring",
        conductive=True,
        tags={"metal"},
    ),
    "ribbon": MetalTool(
        id="ribbon",
        label="a satin ribbon",
        phrase="a satin ribbon",
        bridge_text="The ribbon",
        conductive=False,
        tags={"fabric"},
    ),
}

TARGETS = {
    "blanket": Target(
        id="blanket",
        label="blanket",
        the="the blanket",
        touch_spot="the blanket fold",
        room_text="under the blanket roof",
        spread=3,
        heat_sensitive=True,
        tags={"blanket", "fabric"},
    ),
    "star_map": Target(
        id="star_map",
        label="paper star map",
        the="the paper star map",
        touch_spot="the paper star map",
        room_text="beside the paper star map",
        spread=2,
        heat_sensitive=True,
        tags={"paper", "map"},
    ),
    "pillow": Target(
        id="pillow",
        label="pillow",
        the="the pillow",
        touch_spot="the pillow seam",
        room_text="next to the pillow pile",
        spread=2,
        heat_sensitive=True,
        tags={"pillow", "fabric"},
    ),
    "wooden_stool": Target(
        id="wooden_stool",
        label="wooden stool",
        the="the wooden stool",
        touch_spot="the stool leg",
        room_text="by the wooden stool",
        spread=1,
        heat_sensitive=False,
        tags={"wood"},
    ),
}

SAFE_LIGHTS = {
    "night_light": SafeLight(
        id="night_light",
        label="night-light",
        phrase="a little moon-shaped night-light",
        glow="glowed pale and steady",
        tags={"night_light", "light"},
    ),
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on with a clean white beam",
        tags={"flashlight", "light"},
    ),
    "star_lamp": SafeLight(
        id="star_lamp",
        label="star lamp",
        phrase="a small star lamp",
        glow="sprinkled dots of light across the ceiling",
        tags={"lamp", "galaxy_light"},
    ),
    "glow_stars": SafeLight(
        id="glow_stars",
        label="glow stars",
        phrase="a packet of stick-on glow stars",
        glow="shone softly after the room lights went out",
        tags={"glow_stars", "galaxy_light"},
    ),
}

RESPONSES = {
    "separate_with_spoon": Response(
        id="separate_with_spoon",
        sense=3,
        power=4,
        text="used a wooden spoon to knock the metal away from the battery, then set the battery in a ceramic bowl on the counter",
        fail="used a wooden spoon to knock the metal away, but {target} had already taken too much heat",
        qa_text="used a wooden spoon to move the metal away and set the battery in a ceramic bowl",
        tags={"battery_safety", "cool_down"},
    ),
    "oven_mitt_tray": Response(
        id="oven_mitt_tray",
        sense=3,
        power=3,
        text="slipped on an oven mitt, lifted the hot metal away, and carried the battery to a metal tray where it could cool safely",
        fail="got the hot pieces onto a tray, but {target} was already badly singed",
        qa_text="used an oven mitt and moved the hot battery and metal onto a tray to cool",
        tags={"battery_safety", "cool_down"},
    ),
    "pull_fort_apart": Response(
        id="pull_fort_apart",
        sense=2,
        power=2,
        text="pulled the blanket edge back, swept the hot metal clear, and made a safe open space around the battery",
        fail="pulled the fort apart to make space, but the heat had already scorched the {target}",
        qa_text="pulled the fort back and cleared space around the hot battery",
        tags={"battery_safety"},
    ),
    "blow_on_it": Response(
        id="blow_on_it",
        sense=1,
        power=1,
        text="blew on the hot battery and waved a hand over it",
        fail="blew on the hot battery, but that did almost nothing while the heat kept biting into the {target}",
        qa_text="blew on the hot battery",
        tags={"battery_safety"},
    ),
}

GIRL_NAMES = ["Ivy", "Maya", "Nora", "Lucy", "Ella", "June", "Mina", "Ava", "Zoe", "Lila"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Ben", "Noah", "Eli", "Finn", "Jack", "Leo", "Sam"]
TRAITS = ["careful", "cautious", "sensible", "thoughtful", "curious", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for tool_id, tool in TOOLS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(tool, target):
                    combos.append((theme_id, tool_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    metal: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
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
    "battery": [
        (
            "What is a battery?",
            "A battery stores energy so a toy or light can work. It should be used the right way in the right device."
        )
    ],
    "battery_safety": [
        (
            "Why should children not play with a loose battery?",
            "A loose battery can get hot or be dangerous if it is used the wrong way. Batteries should be handled by a grown-up and kept in the devices they belong in."
        )
    ],
    "metal": [
        (
            "Why can metal be a problem around a battery?",
            "Metal lets electricity travel easily. If metal touches the wrong parts of a battery at the same time, the battery can heat up fast."
        )
    ],
    "foil": [
        (
            "Is foil made of metal?",
            "Yes. Foil is a thin sheet of metal, so it can conduct electricity."
        )
    ],
    "paper_clips": [
        (
            "Are paper clips metal?",
            "Yes. Most paper clips are made of metal, so they can carry electricity and should not be used with a loose battery."
        )
    ],
    "blanket": [
        (
            "Why should a hot thing stay away from a blanket?",
            "A blanket is soft cloth and can be singed by heat. Hot things should be moved away from fabric right away."
        )
    ],
    "paper": [
        (
            "Why can paper be damaged by heat?",
            "Paper is thin and dries out quickly, so too much heat can brown it or make it curl and burn."
        )
    ],
    "pillow": [
        (
            "Why should you keep hot objects away from a pillow?",
            "A pillow is made of fabric and stuffing, and heat can damage it. Soft things are not a safe place for hot objects."
        )
    ],
    "night_light": [
        (
            "What does a night-light do?",
            "A night-light gives a soft glow in a dark room. It is made to give light safely."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight a safer choice than a loose battery experiment?",
            "A flashlight is built to use its battery safely inside. Its light comes from the right parts working together, not from touching metal to a battery."
        )
    ],
    "lamp": [
        (
            "What is a lamp for?",
            "A lamp gives light so people can see. A good lamp is made to stay in one place and shine safely."
        )
    ],
    "glow_stars": [
        (
            "What are glow stars?",
            "Glow stars are light-up decorations you stick on a wall or ceiling. They can make a room feel starry without anything getting hot."
        )
    ],
    "cool_down": [
        (
            "Why do grown-ups move a hot battery to a safe place to cool?",
            "A hot battery needs space away from hands and soft things. Letting it cool in a safe place helps stop anyone from getting burned."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "battery",
    "battery_safety",
    "metal",
    "foil",
    "paper_clips",
    "blanket",
    "paper",
    "pillow",
    "night_light",
    "flashlight",
    "lamp",
    "glow_stars",
    "cool_down",
]


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
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    tool = f["tool_cfg"]
    target = f["target_cfg"]
    l1, l2 = f["lights"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a cautionary slice-of-life story for a 3-to-5-year-old about a cozy indoor galaxy game where a child almost plays with a loose battery and a metal object, but another child stops it in time.',
            f"Tell a homey story where {a.id} wants to use a battery and {tool.label} to light a pretend galaxy hideout, but {b.id} warns that the metal could get hot and singe {target.the}.",
            f'Write a gentle story that includes the words "battery" and "galaxy" and ends with safe lights instead of an experiment.',
        ]
    if outcome == "ruined":
        return [
            f'Write a cautionary slice-of-life story that includes the words "battery" and "galaxy", where children in a homemade fort make one unsafe choice and their game has to end for the night.',
            f"Tell a sad-but-safe story where {a.id} ignores a warning, uses a loose battery with {tool.label}, and the heat damages {target.the} before an adult can fully fix it.",
            f"Write a child-facing warning story where a cozy galaxy game turns scary for a moment, then ends with a clear lesson about loose batteries.",
        ]
    return [
        f'Write a cautionary slice-of-life story for a 3-to-5-year-old where children make a pretend galaxy at home, a loose battery gets hot, and a calm grown-up solves the problem.',
        f"Tell a gentle story where {a.id} tries to use {tool.label} with a battery in a dark hideout, but an adult quickly makes things safe and teaches a better way.",
        f'Write a simple story including the words "battery" and "galaxy" that ends with safe light and a calmer second try.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    tool = f["tool_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    l1, l2 = f["lights"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {pw} at home. They were turning an ordinary room into a tiny galaxy game."
        ),
        (
            "What were the children pretending?",
            f"They were pretending inside {theme.id.replace('_', ' ')} play and looking for {theme.destination}. The dark little hideout made them want a light."
        ),
        (
            f"Why did {b.id} say no to the battery idea?",
            f"{b.id} knew that if {tool.label} touched both ends of the battery, it could get hot fast. That heat could hurt hands and singe {target.the} nearby."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} stopped and thought about the battery getting hot in {a.pronoun('possessive')} hand. {b.id}'s warning made the danger feel real before anything was singed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with {l1.phrase} and {l2.phrase} lighting the hideout instead. The last image shows the galaxy glowing without anyone touching the battery."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did the grown-up make things safe?",
                f"{pw.capitalize()} {response.qa_text}. That stopped the heat from staying close to soft things and gave the battery a safe place to cool."
            )
        )
        qa.append(
            (
                f"Was anyone badly hurt?",
                f"No. The story has a scare and a little mark, but the children were safe. The quick help mattered because the danger came from heat, not from a toy meant for play."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with safe lights making the room feel like a galaxy again. The ending proves they learned a new rule and kept the cozy part of the game."
            )
        )
    else:
        qa.append(
            (
                f"Could the grown-up save the fort right away?",
                f"No. {pw.capitalize()} acted fast, but the heat had already damaged {target.the}. Everyone stayed safe, though the fort had to come down for the night."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that a battery belongs in the right device and that metal can make it dangerous very quickly. The ruined fort made that lesson feel real, not just like a rule."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly on the couch instead of inside the fort. That ending image shows the game stopping because the unsafe choice changed the room."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tool = f["tool_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    tags: set[str] = {"battery", "battery_safety"} | set(tool.tags) | set(target.tags)
    if f["outcome"] == "contained":
        tags |= set(response.tags)
        for light in f["lights"]:
            tags |= set(light.tags)
    elif f["outcome"] == "averted":
        for light in f["lights"]:
            tags |= set(light.tags)
    else:
        tags |= set(response.tags)
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
        flags = []
        if e.conductive:
            flags.append("conductive")
        if e.heat_sensitive:
            flags.append("heat_sensitive")
        if e.gives_light:
            flags.append("gives_light")
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
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="galaxy_fort",
        metal="foil_stars",
        target="blanket",
        light1="night_light",
        light2="star_lamp",
        response="separate_with_spoon",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="rocket_bunk",
        metal="paper_clips",
        target="star_map",
        light1="flashlight",
        light2="glow_stars",
        response="oven_mitt_tray",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Noah",
        cautioner_gender="boy",
        parent="father",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="star_tent",
        metal="key_ring",
        target="pillow",
        light1="night_light",
        light2="flashlight",
        response="pull_fort_apart",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        parent="mother",
        trait="curious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        theme="galaxy_fort",
        metal="foil_stars",
        target="blanket",
        light1="glow_stars",
        light2="star_lamp",
        response="separate_with_spoon",
        instigator="June",
        instigator_gender="girl",
        cautioner="Lila",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        theme="rocket_bunk",
        metal="paper_clips",
        target="blanket",
        light1="night_light",
        light2="glow_stars",
        response="oven_mitt_tray",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Sam",
        cautioner_gender="boy",
        parent="mother",
        trait="thoughtful",
        delay=0,
        instigator_age=4,
        cautioner_age=8,
        relation="siblings",
        trust=6,
    ),
]


def explain_rejection(tool: MetalTool, target: Target) -> str:
    if not tool.conductive:
        return (
            f"(No story: {tool.label} is not metal in a way that bridges the battery, so it would not make the battery heat up. "
            f"Pick foil stars, paper clips, or a key ring.)"
        )
    if not target.heat_sensitive:
        return (
            f"(No story: {target.the} is not the kind of soft nearby thing this cautionary tale needs. "
            f"Pick a blanket, pillow, or paper star map.)"
        )
    return "(No story: this battery-and-metal choice does not create the intended danger.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "ruined"


ASP_RULES = r"""
hazard(M, T) :- metal(M), conductive(M), target(T), heat_sensitive(T).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(Th, M, T) :- theme(Th), hazard(M, T), target(T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(ruined) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("metal", tool_id))
        if tool.conductive:
            lines.append(asp.fact("conductive", tool_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
        if target.heat_sensitive:
            lines.append(asp.fact("heat_sensitive", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
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
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(11))
        smoke_params.seed = 11
        smoke_sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=True, header="smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a cozy galaxy game, one unsafe battery idea, and a safer second try."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--metal", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.metal and args.target:
        tool = TOOLS[args.metal]
        target = TARGETS[args.target]
        if not hazard_at_risk(tool, target):
            raise StoryError(explain_rejection(tool, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.target and not TARGETS[args.target].heat_sensitive:
        tool = TOOLS[args.metal] if args.metal else TOOLS[next(iter(TOOLS))]
        raise StoryError(explain_rejection(tool, TARGETS[args.target]))
    if args.metal and not TOOLS[args.metal].conductive:
        target = TARGETS[args.target] if args.target else TARGETS["blanket"]
        raise StoryError(explain_rejection(TOOLS[args.metal], target))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.metal is None or c[1] == args.metal)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, metal, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme,
        metal=metal,
        target=target,
        light1=light1,
        light2=light2,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.metal not in TOOLS:
        raise StoryError(f"(Unknown metal tool: {params.metal})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.light1 not in SAFE_LIGHTS or params.light2 not in SAFE_LIGHTS:
        raise StoryError("(Unknown safe light.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(TOOLS[params.metal], TARGETS[params.target]):
        raise StoryError(explain_rejection(TOOLS[params.metal], TARGETS[params.target]))

    world = tell(
        theme=THEMES[params.theme],
        tool_cfg=TOOLS[params.metal],
        target_cfg=TARGETS[params.target],
        lights=(SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]),
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, metal, target) combos:\n")
        for theme, metal, target in combos:
            print(f"  {theme:12} {metal:14} {target}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.metal} near {p.target} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
