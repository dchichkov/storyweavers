#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py
==================================================================================

A standalone story world for a rhyming "tool shed / safety / harden /
reconciliation" tale.

Premise
-------
Two children are working on a small project in a tool shed. They squabble over a
tool. In a huff, one child leaves the tool in an unsafe place. Sometimes the
other child's warning is enough and the danger is averted; sometimes the tool
clatters down and startles them both. A calm grown-up helps them apologize,
reconcile, and harden the shed with better storage so the ending image proves
what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py --tool shears --spot shelf --fix pegboard
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py --fix basket
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/safety_harden_tool_shed_reconciliation_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TRUST_LISTEN = 7
CALM_TEMPER = {"gentle", "patient", "careful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sharp: bool = False
    heavy: bool = False
    secure_storage: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Project:
    id: str
    opening: str
    line2: str
    ending: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    rhyme: str
    storage_need: str
    sharp: bool = False
    heavy: bool = False
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
    risky_for: set[str] = field(default_factory=set)
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
class FixCfg:
    id: str
    label: str
    phrase: str
    suits: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    spot = world.get("spot")
    if tool.meters["precarious"] < THRESHOLD:
        return out
    sig = ("danger", tool.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("shed").meters["danger"] += 1
    for role in ("instigator", "cautioner"):
        kid = world.get(role)
        kid.memes["worry"] += 1
    out.append("__danger__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    if tool.meters["precarious"] < THRESHOLD or tool.meters["secured"] >= THRESHOLD:
        return out
    sig = ("fall", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["fallen"] += 1
    tool.meters["clanged"] += 1
    world.get("shed").meters["danger"] += 1
    for role in ("instigator", "cautioner"):
        kid = world.get(role)
        kid.memes["fear"] += 1
    out.append("__clatter__")
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent not in {"__danger__", "__clatter__"}:
                world.say(sent)
    return produced


def hazard_at_risk(tool: ToolCfg, spot: SpotCfg) -> bool:
    return tool.id in spot.risky_for


def fix_suits(tool: ToolCfg, fix: FixCfg) -> bool:
    return tool.storage_need in fix.suits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for tool_id, tool in TOOLS.items():
            for spot_id, spot in SPOTS.items():
                if not hazard_at_risk(tool, spot):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_suits(tool, fix):
                        combos.append((project_id, tool_id, spot_id, fix_id))
    return combos


def caution_power(relation: str, instigator_age: int, cautioner_age: int, temper: str, trust: int) -> int:
    older_bonus = 2 if relation == "siblings" and cautioner_age > instigator_age else 0
    calm_bonus = 1 if temper in CALM_TEMPER else 0
    trust_bonus = 1 if trust >= TRUST_LISTEN else 0
    return older_bonus + calm_bonus + trust_bonus


def would_listen(relation: str, instigator_age: int, cautioner_age: int, temper: str, trust: int) -> bool:
    return caution_power(relation, instigator_age, cautioner_age, temper, trust) >= 2


def predict_clatter(world: World) -> dict:
    sim = world.copy()
    tool = sim.get("tool")
    tool.meters["precarious"] += 1
    tool.meters["secured"] = 0.0
    markers = propagate(sim, narrate=False)
    return {
        "danger": sim.get("shed").meters["danger"],
        "will_fall": "__clatter__" in markers or tool.meters["fallen"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, project: Project) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In the tool shed, bright with beam and thread, "
        f"{a.id} and {b.id} worked side by side instead."
    )
    world.say(f"{project.opening} {project.line2}")


def bring_tool(world: World, a: Entity, b: Entity, tool: ToolCfg) -> None:
    world.say(
        f"Between them lay {tool.phrase}; it clicked and shone with tiny {tool.rhyme}, "
        f"and both of them wanted the very same time."
    )
    a.memes["desire"] += 1
    b.memes["desire"] += 1


def squabble(world: World, a: Entity, b: Entity) -> None:
    a.memes["anger"] += 1
    b.memes["sadness"] += 1
    world.say(
        f'"My turn," said {a.id}. "{b.id}, let go." '
        f'"I only need one snip," said {b.id}, soft and low.'
    )
    world.say(
        f"Their words grew sharp in the small wooden shed, "
        f"and warm little feelings turned prickly instead."
    )


def stash_badly(world: World, a: Entity, tool: ToolCfg, spot: SpotCfg) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["precarious"] += 1
    tool_ent.meters["secured"] = 0.0
    markers = propagate(world, narrate=False)
    world.say(
        f"In a huff, {a.id} set the {tool.label} on {spot.phrase} with no care for where it led. "
        f"It perched in a wobble, half-ready to slide, with the pointy side turned to the side."
    )
    if "__danger__" in markers:
        world.say(
            "The shed felt less cozy, less snug, less bright; "
            "one careless choice had made safety light."
        )


def warn(world: World, b: Entity, a: Entity, tool: ToolCfg, spot: SpotCfg) -> None:
    pred = predict_clatter(world)
    world.facts["predicted_will_fall"] = pred["will_fall"]
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["care"] += 1
    extra = " It could tumble and clatter." if pred["will_fall"] else ""
    world.say(
        f'{b.id} took a breath and said, "{a.id}, that is not safe at all. '
        f'The {tool.label} does not belong on {spot.label}.{extra}"'
    )


def rehang(world: World, a: Entity, b: Entity, tool: ToolCfg) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["secured"] += 1
    tool_ent.meters["precarious"] = 0.0
    a.memes["anger"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the {tool.label}, then back at {b.id}'s face, "
        f"and put it down slowly in a safer place."
    )
    world.say(
        "No clang split the quiet, no jump, no fright; "
        "they stopped the wrong turn and set it right."
    )


def clatter(world: World, tool: ToolCfg, spot: SpotCfg) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then clatter and skitter! From {spot.phrase} it sped; "
        f"the {tool.label} banged loudly and startled the shed."
    )
    world.say(
        "No one was hurt, but both children froze still, "
        "for danger had come from a hot little will."
    )


def call_adult(world: World, adult: Entity) -> None:
    world.say(f'"{adult.label_word.capitalize()}!" they cried, and their voices ran quick. "{adult.label_word.capitalize()}, please come!"')


def mediate(world: World, adult: Entity, a: Entity, b: Entity, tool: ToolCfg) -> None:
    a.memes["shame"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came in with calm in each tread. "
        f"{adult.pronoun().capitalize()} looked at the {tool.label}, then the two little heads."
    )
    world.say(
        f'"First comes safety," {adult.pronoun()} said in a tone warm and slow. '
        f'"Then we mend hearts, because both of you matter, you know."'
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["anger"] = 0.0
    b.memes["sadness"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.facts["reconciled"] = True
    world.say(
        f'{a.id} whispered, "I am sorry I snapped and made it unsafe there." '
        f'{b.id} said, "I am sorry I tugged too. I know we both care."'
    )
    world.say(
        f"They looked at each other, not stormy but clear, "
        f"and the hard little feelings grew smaller to hear."
    )


def harden_shed(world: World, adult: Entity, a: Entity, b: Entity, fix: FixCfg, tool: ToolCfg) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["secured"] += 1
    tool_ent.meters["precarious"] = 0.0
    world.get("shed").meters["danger"] = 0.0
    world.get("shed").meters["hardened"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f'Together they chose {fix.phrase}, and {adult.label_word} said, '
        f'"Let us harden this shed so good habits can spread."'
    )
    world.say(f"{adult.pronoun().capitalize()} {fix.action} The {tool.label} had a home that was sturdy and smart from the start.")
    world.say(
        f"Soon the shed looked tidier, safer, and bright; "
        f"{fix.ending}"
    )


def ending(world: World, a: Entity, b: Entity, project: Project, tool: ToolCfg) -> None:
    world.say(
        f"Then {a.id} and {b.id} worked in a kinder way, "
        f"passing the {tool.label} and asking, not snatching, that day."
    )
    world.say(project.ending)
    world.say(
        "So under the rafters, with peace overhead, "
        "they kept both safety and friendship alive in the shed."
    )


def tell(
    project: Project,
    tool: ToolCfg,
    spot: SpotCfg,
    fix: FixCfg,
    *,
    instigator_name: str = "Tess",
    instigator_gender: str = "girl",
    cautioner_name: str = "Milo",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    temper: str = "gentle",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 7,
    trust: int = 8,
) -> World:
    world = World()
    shed = world.add(Entity(id="shed", type="shed", label="tool shed"))
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator_name,
        role="instigator",
        age=instigator_age,
        traits=["creative"],
        attrs={"name": instigator_name, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner_name,
        role="cautioner",
        age=cautioner_age,
        traits=[temper],
        attrs={"name": cautioner_name, "relation": relation},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=parent_type,
        label="the parent",
        role="adult",
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        sharp=tool.sharp,
        heavy=tool.heavy,
        attrs={"storage_need": tool.storage_need},
    ))
    world.add(Entity(id="spot", type="spot", label=spot.label, phrase=spot.phrase))
    world.facts.update(
        project=project,
        tool_cfg=tool,
        spot_cfg=spot,
        fix_cfg=fix,
        instigator=a,
        cautioner=b,
        adult=adult,
        relation=relation,
        trust=trust,
        temper=temper,
        predicted_will_fall=False,
        predicted_danger=0.0,
        reconciled=False,
    )
    shed.meters["danger"] = 0.0
    shed.meters["hardened"] = 0.0
    tool_ent.meters["precarious"] = 0.0
    tool_ent.meters["secured"] = 0.0
    tool_ent.meters["fallen"] = 0.0
    tool_ent.meters["clanged"] = 0.0
    a.memes["trust"] = float(trust)
    b.memes["trust"] = float(trust)

    introduce(world, a, b, project)
    bring_tool(world, a, b, tool)

    world.para()
    squabble(world, a, b)
    stash_badly(world, a, tool, spot)
    warn(world, b, a, tool, spot)

    listened = would_listen(relation, instigator_age, cautioner_age, temper, trust)
    world.facts["listened"] = listened

    world.para()
    if listened:
        rehang(world, a, b, tool)
        outcome = "averted"
    else:
        clatter(world, tool, spot)
        call_adult(world, adult)
        outcome = "clatter"

    world.para()
    mediate(world, adult, a, b, tool)
    apologize(world, a, b)
    harden_shed(world, adult, a, b, fix, tool)
    ending(world, a, b, project, tool)

    world.facts["outcome"] = outcome
    return world


PROJECTS = {
    "birdhouse": Project(
        id="birdhouse",
        opening="They were painting a birdhouse red for the sparrows that bobbed by the door.",
        line2="Each brush made a swoop, each board found a tune, and sawdust lay soft on the floor.",
        ending="The birdhouse stood ready by sunset's gold thread, and two smiling friends carried it out from the shed.",
        tags={"birdhouse", "project"},
    ),
    "wagon": Project(
        id="wagon",
        opening="They were mending a wagon with wheels that once squeaked whenever it rolled through the lane.",
        line2="Tap went the wood and hum went the shed, as if little work could sing in refrain.",
        ending="The wagon rolled smoothly on round wooden tread, and they pulled it together away from the shed.",
        tags={"wagon", "project"},
    ),
    "trellis": Project(
        id="trellis",
        opening="They were building a bean trellis tall for the vines that would curl in the sun.",
        line2="Slat after slat made a clack and a chime, and making it neatly felt almost like fun-song begun.",
        ending="The trellis leaned ready for green leaves to spread, and they laughed as they carried it out from the shed.",
        tags={"trellis", "project"},
    ),
}

TOOLS = {
    "shears": ToolCfg(
        id="shears",
        label="shears",
        phrase="the garden shears",
        rhyme="gears",
        storage_need="hooks",
        sharp=True,
        tags={"shears", "sharp_tool", "safety"},
    ),
    "hammer": ToolCfg(
        id="hammer",
        label="hammer",
        phrase="the little hammer",
        rhyme="clamor",
        storage_need="rack",
        heavy=True,
        tags={"hammer", "heavy_tool", "safety"},
    ),
    "trowel": ToolCfg(
        id="trowel",
        label="trowel",
        phrase="the hand trowel",
        rhyme="vowel",
        storage_need="bin",
        sharp=True,
        tags={"trowel", "garden_tool", "safety"},
    ),
}

SPOTS = {
    "shelf": SpotCfg(
        id="shelf",
        label="the wobbly shelf",
        phrase="the wobbly shelf",
        risky_for={"shears", "hammer", "trowel"},
        tags={"shelf", "storage"},
    ),
    "door_ledge": SpotCfg(
        id="door_ledge",
        label="the narrow door ledge",
        phrase="the narrow door ledge",
        risky_for={"shears", "hammer"},
        tags={"ledge", "storage"},
    ),
    "seed_box": SpotCfg(
        id="seed_box",
        label="the open seed box",
        phrase="the open seed box",
        risky_for={"trowel", "shears"},
        tags={"box", "storage"},
    ),
}

FIXES = {
    "pegboard": FixCfg(
        id="pegboard",
        label="pegboard hooks",
        phrase="a row of pegboard hooks",
        suits={"hooks"},
        action="screwed the pegboard neatly to the wall and hung each tool where eyes could see it.",
        ending="No blade could wobble; no handle could roam. The sharp little shears had a sensible home.",
        tags={"pegboard", "hooks", "storage"},
    ),
    "rack": FixCfg(
        id="rack",
        label="a hammer rack",
        phrase="a stout hammer rack",
        suits={"rack"},
        action="fastened the rack to a beam and slid the hammer snug into its slot.",
        ending="No weight could slip with a bang in the night. The hammer sat steady and straight and right.",
        tags={"rack", "storage"},
    ),
    "basket": FixCfg(
        id="basket",
        label="a lidded tool basket",
        phrase="a lidded tool basket",
        suits={"bin"},
        action="set the basket low on a bench and tucked the trowel inside before snapping the lid shut.",
        ending="No point could poke and no scoop could skid. The little hand trowel stayed safe under lid.",
        tags={"basket", "storage"},
    ),
}

GIRL_NAMES = ["Tess", "Lila", "Mina", "Nora", "Ava", "Ruby", "Zoe", "Poppy"]
BOY_NAMES = ["Milo", "Ben", "Owen", "Theo", "Sam", "Finn", "Eli", "Noah"]
TEMPER_TRAITS = ["gentle", "patient", "careful", "steady", "quick", "proud"]


@dataclass
class StoryParams:
    project: str
    tool: str
    spot: str
    fix: str
    instigator_name: str
    instigator_gender: str
    cautioner_name: str
    cautioner_gender: str
    parent: str
    temper: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
    trust: int = 8
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
    "sharp_tool": [
        (
            "Why must sharp tools be put away carefully?",
            "Sharp tools can cut skin if someone brushes against them or if they fall. Putting them in a proper place keeps hands and feet safer.",
        )
    ],
    "heavy_tool": [
        (
            "Why can a hammer be dangerous if it is left on an edge?",
            "A hammer is heavy, so it can drop hard if it slides off. That is why it needs a steady place to rest.",
        )
    ],
    "safety": [
        (
            "What does safety mean in a tool shed?",
            "Safety means using tools carefully and putting them away where they cannot slip, poke, or fall. It also means asking for help instead of arguing around dangerous things.",
        )
    ],
    "pegboard": [
        (
            "What is a pegboard for?",
            "A pegboard is a board with holes or hooks for hanging tools. It keeps tools easy to find and less likely to fall.",
        )
    ],
    "rack": [
        (
            "What is a tool rack?",
            "A tool rack is a strong holder that gives each tool its own spot. That helps heavy tools stay put instead of rolling away.",
        )
    ],
    "basket": [
        (
            "Why is a lidded basket useful for tools?",
            "A lidded basket keeps small tools together in one safe place. The lid helps stop them from tipping or poking out.",
        )
    ],
    "reconcile": [
        (
            "What does it mean to reconcile after a quarrel?",
            "To reconcile means to make peace again after hurt feelings. People listen, apologize, and try to treat each other kindly again.",
        )
    ],
    "birdhouse": [
        (
            "Why might children build a birdhouse?",
            "Children build a birdhouse to make a small home for birds. It is also a good project for measuring, painting, and working together.",
        )
    ],
    "wagon": [
        (
            "What is a wagon?",
            "A wagon is a small cart with wheels that can carry toys, tools, or garden things. If a wheel squeaks, it may need mending.",
        )
    ],
    "trellis": [
        (
            "What is a trellis for?",
            "A trellis is a frame that climbing plants can grow on. It helps vines rise up instead of trailing on the ground.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "safety",
    "sharp_tool",
    "heavy_tool",
    "pegboard",
    "rack",
    "basket",
    "reconcile",
    "birdhouse",
    "wagon",
    "trellis",
]


CURATED = [
    StoryParams(
        project="birdhouse",
        tool="shears",
        spot="shelf",
        fix="pegboard",
        instigator_name="Tess",
        instigator_gender="girl",
        cautioner_name="Milo",
        cautioner_gender="boy",
        parent="mother",
        temper="gentle",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=8,
    ),
    StoryParams(
        project="wagon",
        tool="hammer",
        spot="door_ledge",
        fix="rack",
        instigator_name="Ben",
        instigator_gender="boy",
        cautioner_name="Ruby",
        cautioner_gender="girl",
        parent="father",
        temper="quick",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
    ),
    StoryParams(
        project="trellis",
        tool="trowel",
        spot="seed_box",
        fix="basket",
        instigator_name="Nora",
        instigator_gender="girl",
        cautioner_name="Eli",
        cautioner_gender="boy",
        parent="mother",
        temper="patient",
        relation="siblings",
        instigator_age=7,
        cautioner_age=8,
        trust=9,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_listen(
        params.relation,
        params.instigator_age,
        params.cautioner_age,
        params.temper,
        params.trust,
    ) else "clatter"


def generation_prompts(world: World) -> list[str]:
    project = world.facts["project"]
    tool = world.facts["tool_cfg"]
    outcome = world.facts["outcome"]
    a = world.facts["instigator"]
    b = world.facts["cautioner"]
    if outcome == "averted":
        return [
            f'Write a rhyming story for a 3-to-5-year-old set in a tool shed that includes the words "safety" and "harden".',
            f"Tell a gentle reconciliation story where {a.label} and {b.label} quarrel over {tool.label}, but a warning helps them stop the danger before anything falls.",
            f"Write a tool-shed poem-story where children make peace, improve storage, and end with safer habits than they had before.",
        ]
    return [
        f'Write a rhyming story for a 3-to-5-year-old set in a tool shed that includes the words "safety" and "harden".',
        f"Tell a reconciliation story where {a.label} and {b.label} squabble over {tool.label}, it clatters down, and a calm grown-up helps them apologize and fix the problem.",
        f"Write a short child-facing rhyme about danger in a shed, safe storage, and two children becoming friends again.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    adult = f["adult"]
    project = f["project"]
    tool = f["tool_cfg"]
    spot = f["spot_cfg"]
    fix = f["fix_cfg"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, working together in a tool shed. A calm {adult.label_word} helps them when their quarrel turns unsafe.",
        ),
        (
            "What were they doing in the shed?",
            f"They were working on a {project.id} together. The shared project gave them a reason to use the same tool at the same time.",
        ),
        (
            f"Why did the problem begin?",
            f"The problem began because both children wanted the {tool.label} and their feelings got prickly. In the quarrel, {a.label} set it on {spot.label}, which was not a safe place for it.",
        ),
        (
            f"How did {b.label} try to help?",
            f"{b.label} warned that the {tool.label} did not belong on {spot.label}. The warning was about safety, because a tool left that way could slip or fall.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                "What changed before anyone got hurt?",
                f"{a.label} listened and moved the tool to a safer place before it could fall. That changed the story from a quarrel heading toward danger into a wiser choice.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the tool was left there?",
                f"The {tool.label} clattered down and startled both children, though no one was hurt. The loud fall showed that {b.label}'s warning had been right.",
            )
        )
    qa.append(
        (
            "How did they reconcile?",
            f"They apologized to each other and admitted their own part in the quarrel. That mattered because reconciliation was not just about saying sorry; it helped them trust each other again.",
        )
    )
    qa.append(
        (
            "How did they make the shed safer at the end?",
            f"They used {fix.phrase} and worked with the grown-up to harden the shed. The new storage gave the {tool.label} a proper home, so the ending proves they learned a safer habit.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"safety", "reconcile"}
    tags |= set(world.facts["project"].tags)
    tags |= set(world.facts["tool_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("sharp", ent.sharp), ("heavy", ent.heavy), ("secure_storage", ent.secure_storage)) if on]
        if flags:
            bits.append(f"flags={flags}")
        label = ent.label or ent.id
        lines.append(f"  {ent.id:11} ({ent.type:8}) {label:20} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(tool: ToolCfg, spot: SpotCfg, fix: Optional[FixCfg] = None) -> str:
    if not hazard_at_risk(tool, spot):
        return (
            f"(No story: {tool.label} on {spot.label} is not a strong enough safety problem in this world. "
            f"Pick a riskier spot for that tool.)"
        )
    if fix is not None and not fix_suits(tool, fix):
        return (
            f"(No story: {fix.label} does not properly store {tool.label}. "
            f"This world only allows fixes that genuinely harden storage for the chosen tool.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
hazard(Tool, Spot) :- tool(Tool), spot(Spot), risky_for(Spot, Tool).
fit(Tool, Fix) :- tool(Tool), fix(Fix), need(Tool, Need), suits(Fix, Need).
valid(Project, Tool, Spot, Fix) :- project(Project), hazard(Tool, Spot), fit(Tool, Fix).

older_cautioner :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
calm_temper :- temper(T), calm(T).
high_trust :- trust(V), trust_listen(L), V >= L.
power(2) :- older_cautioner, calm_temper.
power(3) :- older_cautioner, calm_temper, high_trust.
power(2) :- older_cautioner, high_trust, not calm_temper.
power(2) :- calm_temper, high_trust, not older_cautioner.
power(1) :- older_cautioner, not calm_temper, not high_trust.
power(1) :- calm_temper, not older_cautioner, not high_trust.
power(1) :- high_trust, not older_cautioner, not calm_temper.
power(0) :- not older_cautioner, not calm_temper, not high_trust.
listens :- power(P), P >= 2.
outcome(averted) :- listens.
outcome(clatter) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("need", tool_id, tool.storage_need))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for tool_id in sorted(spot.risky_for):
            lines.append(asp.fact("risky_for", spot_id, tool_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for need in sorted(fix.suits):
            lines.append(asp.fact("suits", fix_id, need))
    for temper in sorted(CALM_TEMPER):
        lines.append(asp.fact("calm", temper))
    lines.append(asp.fact("trust_listen", TRUST_LISTEN))
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
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("temper", params.temper),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_combos - py_combos:
            print("  only in clingo:", sorted(clingo_combos - py_combos))
        if py_combos - clingo_combos:
            print("  only in python:", sorted(py_combos - clingo_combos))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
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
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming tool-shed story world about safety, reconciliation, and hardening storage."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--temper", choices=TEMPER_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.spot:
        tool = TOOLS[args.tool]
        spot = SPOTS[args.spot]
        if not hazard_at_risk(tool, spot):
            fix = FIXES[args.fix] if args.fix else None
            raise StoryError(explain_rejection(tool, spot, fix))
    if args.tool and args.fix:
        tool = TOOLS[args.tool]
        fix = FIXES[args.fix]
        if not fix_suits(tool, fix):
            spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
            raise StoryError(explain_rejection(tool, spot, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.tool is None or combo[1] == args.tool)
        and (args.spot is None or combo[2] == args.spot)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, tool_id, spot_id, fix_id = rng.choice(sorted(combos))
    instigator_name, instigator_gender = _pick_child(rng)
    cautioner_name, cautioner_gender = _pick_child(rng, avoid=instigator_name)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    instigator_age, cautioner_age = ages[0], ages[1]
    trust = rng.randint(2, 10)
    return StoryParams(
        project=project_id,
        tool=tool_id,
        spot=spot_id,
        fix=fix_id,
        instigator_name=instigator_name,
        instigator_gender=instigator_gender,
        cautioner_name=cautioner_name,
        cautioner_gender=cautioner_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        temper=args.temper or rng.choice(TEMPER_TRAITS),
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.temper not in TEMPER_TRAITS:
        raise StoryError(f"(Unknown temper: {params.temper})")

    project = PROJECTS[params.project]
    tool = TOOLS[params.tool]
    spot = SPOTS[params.spot]
    fix = FIXES[params.fix]
    if not hazard_at_risk(tool, spot):
        raise StoryError(explain_rejection(tool, spot, fix))
    if not fix_suits(tool, fix):
        raise StoryError(explain_rejection(tool, spot, fix))

    world = tell(
        project=project,
        tool=tool,
        spot=spot,
        fix=fix,
        instigator_name=params.instigator_name,
        instigator_gender=params.instigator_gender,
        cautioner_name=params.cautioner_name,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        temper=params.temper,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, tool, spot, fix) combos:\n")
        for project_id, tool_id, spot_id, fix_id in combos:
            print(f"  {project_id:10} {tool_id:7} {spot_id:10} {fix_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator_name} & {p.cautioner_name}: {p.tool} on {p.spot} ({p.project}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
