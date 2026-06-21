#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py
=========================================================================

A standalone story world for a cautionary folk-tale shaped seaside story:
a curious child wants to dig into a marked burial place near a quiet cove
where an old yacht rocks at its rope, a wiser companion warns that the sea
can creep through a cut in the sand, and an elder shows the children the
difference between remembering and rummaging.

The world prefers a small set of plausible variants over broad, weak coverage:
only unstable burial places can honestly produce the danger, only sensible
repairs are accepted, and some sibling pairings can avert the trouble before
any digging happens.

Run it
------
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py --site dune_mound --tool shell_scoop
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py --site stone_cairn
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/yacht_burial_cautionary_curiosity_folk_tale.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 6.0
STEADY_TRAITS = {"careful", "steady", "thoughtful", "gentle"}


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
    unstable: bool = False
    can_dig: bool = False
    floats: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "gran",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
class Harbor:
    id: str
    shore: str
    opening: str
    yacht_desc: str
    ending: str
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
class Rumor:
    id: str
    object_name: str
    lure: str
    hush: str
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
class BurialSite:
    id: str
    label: str
    the: str
    marker: str
    setting_line: str
    warning: str
    seep: str
    fragile: bool = True
    crumble: int = 2
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
class DigTool:
    id: str
    label: str
    phrase: str
    bite: int
    action: str
    can_dig: bool = True
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


@dataclass
class Memorial:
    id: str
    gift: str
    act: str
    close: str
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
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
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_seep(world: World) -> list[str]:
    out: list[str] = []
    site = world.get("site")
    if site.meters["cut"] < THRESHOLD or not site.unstable:
        return out
    sig = ("seep", site.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site.meters["seep"] += 1
    world.get("shore").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__seep__")
    return out


def _r_breach(world: World) -> list[str]:
    out: list[str] = []
    site = world.get("site")
    if site.meters["seep"] < THRESHOLD:
        return out
    sig = ("breach", site.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site.meters["breached"] += 1
    world.get("shore").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__breach__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="seep", tag="physical", apply=_r_seep),
    Rule(name="breach", tag="physical", apply=_r_breach),
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


def hazard_at_risk(tool: DigTool, site: BurialSite) -> bool:
    return tool.can_dig and site.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def damage_severity(site: BurialSite, tool: DigTool, delay: int) -> int:
    return site.crumble + tool.bite + delay


def is_contained(response: Response, site: BurialSite, tool: DigTool, delay: int) -> bool:
    return response.power >= damage_severity(site, tool, delay)


def initial_steady(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_steady(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > CURIOSITY_INIT


def predict_breach(world: World) -> dict:
    sim = world.copy()
    _do_dig(sim, narrate=False)
    site = sim.get("site")
    shore = sim.get("shore")
    return {
        "breached": site.meters["breached"] >= THRESHOLD,
        "danger": shore.meters["danger"],
    }


def _do_dig(world: World, narrate: bool = True) -> None:
    site = world.get("site")
    tool = world.get("tool")
    site.meters["cut"] += 1
    site.meters["depth"] += tool.meters["bite"]
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, harbor: Harbor, site: BurialSite) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"In the salt-bright days when gulls talked over {harbor.shore}, "
        f"{a.id} and {b.id} often wandered there together. {harbor.opening}"
    )
    world.say(
        f"Near the water lay {site.the}, {site.setting_line}. "
        f"{harbor.yacht_desc}"
    )


def rumor_scene(world: World, a: Entity, rumor: Rumor, elder: Entity) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"Old people in the village spoke softly of it. They said a {rumor.object_name} "
        f"had once been laid there, and {rumor.lure}."
    )
    world.say(
        f'{elder.label_word.capitalize()} had always added, "{rumor.hush}"'
    )


def tempt(world: World, a: Entity, tool: DigTool, rumor: Rumor) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"One afternoon {a.id} looked at the stones, then at {tool.phrase}. "
        f'"Maybe the {rumor.object_name} is still under there," {a.pronoun()} whispered.'
    )
    world.say(
        f"The thought of knowing for certain pulled at {a.pronoun('object')} harder than the tide."
    )


def warn(world: World, b: Entity, a: Entity, site: BurialSite, elder: Entity) -> None:
    pred = predict_breach(world)
    b.memes["steady"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["steady"] >= 6:
        extra = f" {b.pronoun().capitalize()} had heard {elder.label_word} explain it before."
    world.say(
        f'{b.id} touched {a.id}\'s sleeve. "{elder.label_word.capitalize()} says {site.warning}. '
        f'If you cut {site.the}, the sea can find the wound."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, tool: DigTool) -> None:
    a.memes["defiance"] += 1
    instigator_older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older_sib:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Just one little look," {a.id} said, and because {a.pronoun()} was '
            f'{b.pronoun("possessive")} {rel}, {b.id} could not stop {a.pronoun("object")}.'
        )
    else:
        world.say(
            f'"Just one little look," {a.id} said, and {a.pronoun()} knelt with {tool.the if hasattr(tool, "the") else tool.label}.'
        )


def back_down(world: World, a: Entity, b: Entity, elder: Entity) -> None:
    a.memes["curiosity"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"Just one little look," {a.id} began. But {b.id}, {a.pronoun("possessive")} older '
        f'{rel}, kept hold of {a.pronoun("possessive")} hand until the wish passed.'
    )
    world.say(
        f"They carried the question to {elder.label_word} instead of to the sand, and that was the wise turning of the day."
    )


def dig(world: World, a: Entity, site: BurialSite, tool: DigTool) -> None:
    _do_dig(world, narrate=True)
    world.say(
        f"{a.id} {tool.action} at the edge of the stones. At once {site.seep}, and the smooth sand gave a small, sighing slump."
    )


def alarm(world: World, b: Entity, site: BurialSite, elder: Entity) -> None:
    world.say(f'"The sea is getting in! {site.The} is opening!" {b.id} cried.')
    world.say(f'"{elder.label_word.upper()}!"')


def rescue(world: World, elder: Entity, response: Response, site: BurialSite, harbor: Harbor) -> None:
    world.get("site").meters["breached"] = 0.0
    world.get("site").meters["seep"] = 0.0
    world.get("shore").meters["danger"] = 0.0
    world.say(
        f"{elder.label_word.capitalize()} came down the path with quick, sure steps and {response.text.format(site=site.label)}."
    )
    world.say(
        f"Soon the narrow wound was shut again, and the tide muttered outside it. Even the old yacht seemed to rest easier at its rope."
    )


def lesson(world: World, elder: Entity, a: Entity, b: Entity, site: BurialSite) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{elder.label_word.capitalize()} laid a warm hand on both their heads. "
        f'"Curiosity is a bright lantern," {elder.pronoun()} said, "but you must carry it with care. '
        f'A burial place is for memory, not for rummaging, and the shore keeps what it is given in its own way."'
    )
    world.say(
        f"{a.id} looked at the mended sand and nodded. {b.id} nodded too, for the truth of the thing could be seen with bare eyes."
    )


def rescue_fail(world: World, elder: Entity, response: Response, site: BurialSite) -> None:
    world.get("shore").meters["danger"] += 1
    world.get("site").meters["loss"] += 1
    world.say(
        f"{elder.label_word.capitalize()} hurried to help and {response.fail.format(site=site.label)}."
    )
    world.say(
        f"But the tide had already learned the path. It tugged the sand away in streaming ribbons, and the old mound sagged open to the gray water."
    )


def loss(world: World, elder: Entity, a: Entity, b: Entity, harbor: Harbor, site: BurialSite) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["sorrow"] += 1
    world.say(
        f"No one was swept away, for {elder.label_word} pulled the children back to the high path. Yet the little place of memory was broken, and the villagers stood in sorrow along {harbor.shore}."
    )
    world.say(
        f"The old yacht rocked and knocked softly against the pier, as if it too were mourning what careless hands had started."
    )
    world.say(
        f"That evening {a.id} wished harder for the lost peace of {site.the} than for any hidden treasure."
    )


def memorial_turn(world: World, elder: Entity, a: Entity, b: Entity, memorial: Memorial, harbor: Harbor, site: BurialSite) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["respect"] += 1
    world.say(
        f"The next morning {elder.label_word} showed them a better way. Together they {memorial.act} and left {memorial.gift} by {site.the}."
    )
    world.say(
        f'"Questions should be carried to living mouths," {elder.pronoun()} told them, "and memory should be carried with quiet hands."'
    )
    world.say(
        f"{harbor.ending} {memorial.close}"
    )


def tell(
    harbor: Harbor,
    rumor: Rumor,
    site_cfg: BurialSite,
    tool_cfg: DigTool,
    response: Response,
    memorial: Memorial,
    *,
    instigator: str = "Nell",
    instigator_gender: str = "girl",
    cautioner: str = "Finn",
    cautioner_gender: str = "boy",
    elder_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World(harbor=harbor)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["curious"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
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
    world.add(Entity(id="shore", type="shore", label="the shore"))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        can_dig=tool_cfg.can_dig,
    ))
    tool.meters["bite"] = float(tool_cfg.bite)
    site = world.add(Entity(
        id="site",
        type="burial_site",
        label=site_cfg.label,
        unstable=site_cfg.fragile,
    ))
    world.add(Entity(id="yacht", type="yacht", label="yacht", floats=True))

    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["trust"] = float(trust)
    b.memes["steady"] = initial_steady(trait)

    introduce(world, a, b, harbor, site_cfg)
    rumor_scene(world, a, rumor, elder)

    world.para()
    tempt(world, a, tool_cfg, rumor)
    warn(world, b, a, site_cfg, elder)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, elder)
        contained = True
        severity = 0
        world.para()
        memorial_turn(world, elder, a, b, memorial, harbor, site_cfg)
    else:
        defy(world, a, b, tool_cfg)
        world.para()
        dig(world, a, site_cfg, tool_cfg)
        alarm(world, b, site_cfg, elder)
        severity = damage_severity(site_cfg, tool_cfg, delay)
        site.meters["severity"] = float(severity)
        contained = is_contained(response, site_cfg, tool_cfg, delay)

        world.para()
        if contained:
            rescue(world, elder, response, site_cfg, harbor)
            lesson(world, elder, a, b, site_cfg)
            world.para()
            memorial_turn(world, elder, a, b, memorial, harbor, site_cfg)
        else:
            rescue_fail(world, elder, response, site_cfg)
            loss(world, elder, a, b, harbor, site_cfg)
            world.para()
            lesson(world, elder, a, b, site_cfg)

    outcome = "averted" if averted else ("contained" if contained else "washed")
    world.facts.update(
        harbor=harbor,
        rumor=rumor,
        site_cfg=site_cfg,
        tool_cfg=tool_cfg,
        response=response,
        memorial=memorial,
        instigator=a,
        cautioner=b,
        elder=elder,
        site=site,
        tool=tool,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        ignited=site.meters["cut"] >= THRESHOLD,
        repaired=contained,
    )
    return world


HARBORS = {
    "windglass": Harbor(
        id="windglass",
        shore="Windglass Cove",
        opening="At low tide the pebbles shone like fish scales, and a weathered blue yacht nodded against the pier.",
        yacht_desc="Farther out, the blue yacht moved up and down as gently as a cradle.",
        ending="The blue yacht glided on the silver water while the children stood still and respectful on the shore.",
    ),
    "musselbay": Harbor(
        id="musselbay",
        shore="Mussel Bay",
        opening="Sea grass hissed in the breeze, and a white yacht leaned softly beside the harbor posts.",
        yacht_desc="Beyond the reeds, the white yacht tugged once at its rope and then lay quiet again.",
        ending="The white yacht shone in the evening light, and the shore looked peaceful once more.",
    ),
    "lanternharbor": Harbor(
        id="lanternharbor",
        shore="Lantern Harbor",
        opening="The tide breathed in and out of the harbor mouth, and an old green yacht clicked its mast against the wind.",
        yacht_desc="Out on the calm water, the green yacht waited like a patient heron.",
        ending="The green yacht drifted past the breakwater while the children kept their promise in silence.",
    ),
}

RUMORS = {
    "captain_bell": Rumor(
        id="captain_bell",
        object_name="captain's bell",
        lure="whoever heard it under the sand on a still night would learn the sea's oldest secret",
        hush="Some things are buried so that grief may sleep.",
        tags={"bell", "memory"},
    ),
    "silver_key": Rumor(
        id="silver_key",
        object_name="silver key",
        lure="it might open a chest from a lost voyage",
        hush="Not every hidden thing was hidden for finding.",
        tags={"key", "memory"},
    ),
    "shell_map": Rumor(
        id="shell_map",
        object_name="shell map",
        lure="it might point to where a storm once drove a sailor's yacht ashore",
        hush="Wonder should ask permission before it puts fingers in the ground.",
        tags={"map", "memory"},
    ),
}

SITES = {
    "dune_mound": BurialSite(
        id="dune_mound",
        label="dune mound",
        the="the dune mound",
        marker="ringed with white shells",
        setting_line="ringed with white shells and marked by driftwood crossed in a quiet X",
        warning="the dune roots hold that mound together",
        seep="a thread of seawater slipped into the fresh cut",
        fragile=True,
        crumble=2,
        tags={"sand", "burial"},
    ),
    "reed_bank": BurialSite(
        id="reed_bank",
        label="reed-bank burial",
        the="the reed-bank burial",
        marker="edged with woven reeds",
        setting_line="edged with woven reeds where the tide channel bent close",
        warning="the reeds and packed mud keep the bank from crumbling",
        seep="cold water began to pearl through the torn mud",
        fragile=True,
        crumble=3,
        tags={"mud", "burial"},
    ),
    "stone_cairn": BurialSite(
        id="stone_cairn",
        label="stone cairn",
        the="the stone cairn",
        marker="stacked in neat gray rings",
        setting_line="stacked in neat gray rings above the reach of the tide",
        warning="stones do not wash open when left alone",
        seep="nothing at all seeped through the stones",
        fragile=False,
        crumble=0,
        tags={"stone", "burial"},
    ),
}

TOOLS = {
    "shell_scoop": DigTool(
        id="shell_scoop",
        label="shell scoop",
        phrase="a big shell scoop",
        bite=1,
        action="scraped with the shell scoop",
        can_dig=True,
        tags={"digging"},
    ),
    "driftwood_spade": DigTool(
        id="driftwood_spade",
        label="driftwood spade",
        phrase="a flat driftwood spade",
        bite=2,
        action="pushed the driftwood spade into the damp edge",
        can_dig=True,
        tags={"digging"},
    ),
    "iron_spade": DigTool(
        id="iron_spade",
        label="iron spade",
        phrase="a little iron spade",
        bite=3,
        action="drove the little iron spade under the marker stones",
        can_dig=True,
        tags={"digging"},
    ),
}

RESPONSES = {
    "sandbags": Response(
        id="sandbags",
        sense=3,
        power=5,
        text="dropped sandbags into the cut, stamped them firm, and laid the marker stones back over the wound in the {site}",
        fail="threw sandbags into the cut, but the water had already bitten a channel beneath the {site}",
        qa_text="packed the cut with sandbags and closed it before the tide pulled more away",
        tags={"sandbags", "repair"},
    ),
    "wattle_screen": Response(
        id="wattle_screen",
        sense=3,
        power=4,
        text="pressed a woven wattle screen against the gap, shoved wet sand around it, and braced the edge of the {site}",
        fail="set a woven screen across the gap, but the bank under the {site} kept slipping away",
        qa_text="used a woven screen and wet sand to brace the broken edge",
        tags={"repair", "wattle"},
    ),
    "bare_hands": Response(
        id="bare_hands",
        sense=1,
        power=1,
        text="tried to push the sand back with bare hands",
        fail="scrabbled with bare hands, but every handful slid away again from the {site}",
        qa_text="tried to push the sand back with bare hands",
        tags={"repair"},
    ),
}

MEMORIALS = {
    "shell_ring": Memorial(
        id="shell_ring",
        gift="a fresh ring of bright shells",
        act="smoothed the place flat and made a careful ring of shells",
        close="After that, when curiosity tugged at them, they asked their questions first and kept their hands off what had been laid to rest.",
        tags={"shells", "memory"},
    ),
    "marigold_lantern": Memorial(
        id="marigold_lantern",
        gift="a little floating lantern of folded leaves and marigold petals",
        act="set a leaf lantern afloat in the still water and bowed their heads",
        close="From then on they learned that the sea answers patient questions better than hurried digging.",
        tags={"lantern", "memory"},
    ),
    "pebble_song": Memorial(
        id="pebble_song",
        gift="three smooth pebbles and a quiet song",
        act="placed three smooth pebbles beside the marker and sang a hush-soft song",
        close="Ever after, they remembered that wonder grows gentler, not smaller, when it learns respect.",
        tags={"memory", "song"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Tansy", "Ivy", "June", "Wren", "Elsa", "Poppy"]
BOY_NAMES = ["Finn", "Tobin", "Ash", "Rowan", "Bram", "Otis", "Jory", "Milo"]
TRAITS = ["careful", "steady", "thoughtful", "gentle", "quick", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for harbor_id in HARBORS:
        for tool_id, tool in TOOLS.items():
            for site_id, site in SITES.items():
                if hazard_at_risk(tool, site):
                    combos.append((harbor_id, tool_id, site_id))
    return combos


@dataclass
class StoryParams:
    harbor: str
    rumor: str
    site: str
    tool: str
    response: str
    memorial: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    elder: str
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
    "burial": [
        (
            "What is a burial place?",
            "A burial place is a spot where something or someone has been laid to rest. People treat it gently because it is tied to memory and love."
        )
    ],
    "sand": [
        (
            "Why can sand fall in when you dig near the water?",
            "Wet sand can hold for a little while, but moving water slips through tiny spaces and pulls it loose. That is why a small cut can grow into a bigger break."
        )
    ],
    "mud": [
        (
            "Why do riverbanks crumble when water gets into them?",
            "Water softens the packed mud and carries little bits away. When enough of it moves, the bank can slump and break."
        )
    ],
    "sandbags": [
        (
            "What do sandbags do?",
            "Sandbags are heavy bags filled with sand. People use them to block water and hold weak ground in place."
        )
    ],
    "wattle": [
        (
            "What is a wattle screen?",
            "A wattle screen is a woven wall of thin sticks or reeds. It can help hold mud or sand together for a while."
        )
    ],
    "memory": [
        (
            "Why do people leave markers at special resting places?",
            "Markers help people remember with care and know the place should be treated gently. They turn memory into something others can see and respect."
        )
    ],
    "yacht": [
        (
            "What is a yacht?",
            "A yacht is a boat made for sailing or traveling on the water. Some are small and quiet, and some are large and grand."
        )
    ],
}
KNOWLEDGE_ORDER = ["burial", "sand", "mud", "sandbags", "wattle", "memory", "yacht"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    rumor = f["rumor"]
    site = f["site_cfg"]
    harbor = f["harbor"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "yacht" and "burial", '
        f'and centers on a curious child near {harbor.shore} and {site.the}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary folk tale where {a.id} wants to dig for a hidden {rumor.object_name}, but {b.id} stops {a.pronoun('object')} before any harm is done.",
            "Write a gentle story where curiosity is strong, but respect for a resting place proves stronger in the end.",
        ]
    if outcome == "washed":
        return [
            base,
            f"Tell a sadder cautionary tale where {a.id} ignores a warning, cuts into {site.the}, and the tide ruins the quiet place before the lesson is learned.",
            "Write a seaside folk tale where careless curiosity brings real loss, though the children are kept safe and wiser afterward.",
        ]
    return [
        base,
        f"Tell a cautionary folk tale where {a.id} digs into {site.the} to satisfy curiosity, but an elder repairs the damage and teaches respect.",
        "Write a simple story where curiosity causes danger near the sea, and the ending image shows memory being honored the right way.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    elder = f["elder"]
    site = f["site_cfg"]
    rumor = f["rumor"]
    harbor = f["harbor"]
    response = f["response"]
    memorial = f["memorial"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {elder.label_word} by {harbor.shore}. The story follows what happens when curiosity pulls one child toward a marked burial place."
        ),
        (
            f"Why did {a.id} want to dig into {site.the}?",
            f"{a.id} had heard the village rumor about a {rumor.object_name} buried there and wanted to know if it was true. Curiosity made the hidden thing feel brighter than the warning."
        ),
        (
            f"Why did {b.id} warn {a.id} not to dig?",
            f"{b.id} knew the place was holding back loose ground and water from the tide. A cut in {site.the} could become a path for the sea, so the warning was about real danger as well as respect."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed the story before any harm happened?",
                f"{b.id}, the older sibling, held firm and kept {a.id} from acting on the idea. Because of that, the children carried their question to {elder.label_word} instead of opening the sand."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} dug into {site.the}?",
                f"Water seeped into the cut and the ground began to sag open. The danger came because the shore was already weak enough for the tide to use the new opening."
            )
        )
        qa.append(
            (
                f"How did {elder.label_word} fix the problem?",
                f"{elder.label_word.capitalize()} {response.qa_text}. That quick repair stopped the tide from widening the wound in the burial place."
            )
        )
    else:
        qa.append(
            (
                f"How did the trouble become worse than anyone meant?",
                f"The first cut let the sea creep in, and then the tide pulled more and more ground away. By the time help came, the quiet burial place had already been broken open."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly but safely: no one was hurt, yet the village lost the peace of that little resting place. Afterward the children understood that some questions must be asked with words, not shovels."
            )
        )
    qa.append(
        (
            "What did the children do at the end to show they had changed?",
            f"They {memorial.act} and left {memorial.gift} there instead of digging. The ending image proves they learned to honor memory with gentle hands."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"burial", "memory", "yacht"}
    site = f["site_cfg"]
    response = f["response"]
    if "sand" in site.tags:
        tags.add("sand")
    if "mud" in site.tags:
        tags.add("mud")
    if response.id == "sandbags":
        tags.add("sandbags")
    if response.id == "wattle_screen":
        tags.add("wattle")
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
        if e.unstable:
            bits.append("unstable=True")
        if e.can_dig:
            bits.append("can_dig=True")
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
        harbor="windglass",
        rumor="captain_bell",
        site="dune_mound",
        tool="shell_scoop",
        response="sandbags",
        memorial="shell_ring",
        instigator="Nell",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        elder="grandmother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        harbor="musselbay",
        rumor="silver_key",
        site="reed_bank",
        tool="driftwood_spade",
        response="wattle_screen",
        memorial="marigold_lantern",
        instigator="Rowan",
        instigator_gender="boy",
        cautioner="Wren",
        cautioner_gender="girl",
        elder="grandfather",
        trait="thoughtful",
        delay=0,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        harbor="lanternharbor",
        rumor="shell_map",
        site="reed_bank",
        tool="iron_spade",
        response="wattle_screen",
        memorial="pebble_song",
        instigator="Mira",
        instigator_gender="girl",
        cautioner="Ash",
        cautioner_gender="boy",
        elder="grandmother",
        trait="steady",
        delay=2,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        harbor="windglass",
        rumor="captain_bell",
        site="dune_mound",
        tool="driftwood_spade",
        response="sandbags",
        memorial="marigold_lantern",
        instigator="Otis",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        elder="grandfather",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(tool: DigTool, site: BurialSite) -> str:
    if not site.fragile:
        return (
            f"(No story: {site.the} is firm enough that digging there would not let the tide in. "
            f"No real breach means no honest cautionary turn. Pick a fragile place like a dune mound or reed-bank burial.)"
        )
    if not tool.can_dig:
        return (
            f"(No story: {tool.label} cannot really cut into {site.the}, so the danger never begins.)"
        )
    return "(No story: this combination has no believable shore danger.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a sturdier repair such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], SITES[params.site], TOOLS[params.tool], params.delay) else "washed"


ASP_RULES = r"""
hazard(Tool, Site) :- can_dig(Tool), fragile(Site).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(H, Tool, Site) :- harbor(H), tool(Tool), site(Site), hazard(Tool, Site).

steady_now(T) :- trait(T), is_steady(T).
init_steady(5) :- trait(T), steady_now(T).
init_steady(3) :- trait(T), not steady_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_steady(C), bonus(B).
averted :- cautioner_older, authority(A), curiosity_init(CI), A > CI.

severity(Cr + Bt + D) :- chosen_site(S), crumble(S, Cr), chosen_tool(T), bite(T, Bt), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(washed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HARBORS:
        lines.append(asp.fact("harbor", hid))
    for sid, site in SITES.items():
        lines.append(asp.fact("site", sid))
        if site.fragile:
            lines.append(asp.fact("fragile", sid))
        lines.append(asp.fact("crumble", sid, site.crumble))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.can_dig:
            lines.append(asp.fact("can_dig", tid))
        lines.append(asp.fact("bite", tid, tool.bite))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
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
    scenario = "\n".join([
        asp.fact("chosen_site", params.site),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sense, python_sense = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(60):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="SMOKE")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a seaside folk tale about curiosity, a burial place, and the wisdom of asking before touching."
    )
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--memorial", choices=MEMORIALS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much head start the tide gets before the elder's repair")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and not SITES[args.site].fragile:
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(tool, SITES[args.site]))
    if args.tool and args.site:
        tool = TOOLS[args.tool]
        site = SITES[args.site]
        if not hazard_at_risk(tool, site):
            raise StoryError(explain_rejection(tool, site))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.harbor is None or combo[0] == args.harbor)
        and (args.tool is None or combo[1] == args.tool)
        and (args.site is None or combo[2] == args.site)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    harbor_id, tool_id, site_id = rng.choice(sorted(combos))
    rumor_id = args.rumor or rng.choice(sorted(RUMORS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    memorial_id = args.memorial or rng.choice(sorted(MEMORIALS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        harbor=harbor_id,
        rumor=rumor_id,
        site=site_id,
        tool=tool_id,
        response=response_id,
        memorial=memorial_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        elder=elder,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS:
        raise StoryError(f"(Unknown harbor: {params.harbor})")
    if params.rumor not in RUMORS:
        raise StoryError(f"(Unknown rumor: {params.rumor})")
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.memorial not in MEMORIALS:
        raise StoryError(f"(Unknown memorial: {params.memorial})")
    if params.elder not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder})")

    site = SITES[params.site]
    tool = TOOLS[params.tool]
    response = RESPONSES[params.response]
    if not hazard_at_risk(tool, site):
        raise StoryError(explain_rejection(tool, site))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        harbor=HARBORS[params.harbor],
        rumor=RUMORS[params.rumor],
        site_cfg=site,
        tool_cfg=tool,
        response=response,
        memorial=MEMORIALS[params.memorial],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        elder_type=params.elder,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (harbor, tool, site) combos:\n")
        for harbor_id, tool_id, site_id in combos:
            print(f"  {harbor_id:13} {tool_id:15} {site_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.tool} at {p.site} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
