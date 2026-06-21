#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py
===========================================================

A standalone story world for a tiny Tall-Tale-style lesson story about a vole
whose brag grows too big for good sense. In this world, a small vole boasts
about moving an enormous object alone, ignores a wiser warning, gets stuck in a
mushy place, and then learns that asking for help and choosing the right tool is
stronger than bragging.

The world model tracks physical meters (load, stuckness, distance, wobble) and
emotional memes (pride, caution, fear, relief, humility). The prose is rendered
from simulated state and branching outcomes rather than frozen templates.

Run it
------
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py --boast giant_pumpkin --path marsh
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py --helper none   # rejected
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vole_lesson_learned_tall_tale.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type or self.label)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Boast:
    id: str
    item_label: str
    item_phrase: str
    giant_line: str
    weight: int
    wobble: int
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
class Path:
    id: str
    label: str
    texture: str
    hazard: str
    risk: int
    danger_line: str
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
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    teamwork: bool
    sensible: int
    use_line: str
    qa_line: str
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
    type: str
    label: str
    role_word: str
    caution_line: str
    strength: int
    sensible: int
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


def _r_overload(world: World) -> list[str]:
    out: list[str] = []
    vole = world.get("vole")
    item = world.get("item")
    path = world.get("path")
    if item.meters["load"] < THRESHOLD:
        return out
    sig = ("overload",)
    if sig in world.fired:
        return out
    if item.meters["load"] > vole.meters["carry"]:
        world.fired.add(sig)
        vole.meters["strain"] += 1
        vole.memes["worry"] += 1
        path.meters["risk_now"] += max(1, int(world.facts.get("path_risk", 0)))
        out.append("__strain__")
    return out


def _r_sink(world: World) -> list[str]:
    out: list[str] = []
    vole = world.get("vole")
    item = world.get("item")
    path = world.get("path")
    if vole.meters["strain"] < THRESHOLD or path.meters["risk_now"] < THRESHOLD:
        return out
    sig = ("sink",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vole.meters["stuck"] += 1
    vole.memes["fear"] += 1
    item.meters["tilt"] += 1
    out.append("__stuck__")
    return out


def _r_help_success(world: World) -> list[str]:
    out: list[str] = []
    vole = world.get("vole")
    item = world.get("item")
    helper = world.get("helper")
    tool = world.get("tool")
    if vole.meters["stuck"] < THRESHOLD:
        return out
    if helper.meters["arrived"] < THRESHOLD or tool.meters["used"] < THRESHOLD:
        return out
    sig = ("help_success",)
    if sig in world.fired:
        return out
    if helper.meters["assist_power"] + tool.meters["tool_power"] >= item.meters["load"] + world.get("path").meters["risk_now"]:
        world.fired.add(sig)
        vole.meters["stuck"] = 0.0
        vole.memes["relief"] += 1
        vole.memes["humility"] += 1
        item.meters["moved"] += 1
        out.append("__freed__")
    return out


CAUSAL_RULES = [
    Rule(name="overload", tag="physical", apply=_r_overload),
    Rule(name="sink", tag="physical", apply=_r_sink),
    Rule(name="help_success", tag="social", apply=_r_help_success),
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


def path_difficulty(path: Path) -> int:
    return path.risk


def can_story_work(boast: Boast, path: Path, helper: Helper, tool: Tool) -> bool:
    if helper.sensible < SENSE_MIN or tool.sensible < SENSE_MIN:
        return False
    demand = boast.weight + path_difficulty(path)
    supply = helper.strength + tool.power
    return demand >= 6 and supply >= demand


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sensible >= SENSE_MIN]


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sensible >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for boast_id, boast in BOASTS.items():
        for path_id, path in PATHS.items():
            for helper_id, helper in HELPERS.items():
                for tool_id, tool in TOOLS.items():
                    if can_story_work(boast, path, helper, tool):
                        combos.append((boast_id, path_id, helper_id, tool_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    vole = sim.get("vole")
    item = sim.get("item")
    item.meters["load"] = sim.facts["boast_cfg"].weight
    vole.meters["hauling"] += 1
    propagate(sim, narrate=False)
    return {
        "strain": vole.meters["strain"],
        "stuck": vole.meters["stuck"],
        "risk": sim.get("path").meters["risk_now"],
    }


def opening(world: World, vole: Entity, boast: Boast, path: Path) -> None:
    vole.memes["joy"] += 1
    vole.memes["pride"] += 1
    world.say(
        f"In the broadest meadow that ever leaned under the sky, there lived a vole "
        f"named {vole.id}. {vole.id} was so small that a buttercup could shade "
        f"{vole.pronoun('object')}, but {vole.pronoun('possessive')} brag was tall enough to tickle the clouds."
    )
    world.say(
        f"One bright morning, {vole.id} stood beside {boast.item_phrase} and declared "
        f"that {boast.giant_line}."
    )
    world.say(
        f"The road home was {path.texture}, and everybody in the meadow knew it for {path.hazard}."
    )


def warning(world: World, helper: Entity, vole: Entity, path: Path, tool: Tool) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_stuck"] = pred["stuck"] >= THRESHOLD
    world.facts["predicted_risk"] = pred["risk"]
    helper.memes["caution"] += 1
    extra = " and take a sensible tool along" if tool.id != "vine_harness" else " and use a steady harness"
    world.say(
        f'"{helper.attrs["caution_line"]} The {path.label} can swallow little feet, so ask for help{extra}," '
        f"{helper.id} said."
    )


def boast_bigger(world: World, vole: Entity, boast: Boast, helper: Entity) -> None:
    vole.memes["pride"] += 1
    world.say(
        f'But {vole.id} puffed out {vole.pronoun("possessive")} chest until {vole.pronoun("possessive")} whiskers quivered. '
        f'"Why, I can tug {boast.item_label} so hard that hills will scoot out of my way!" {vole.pronoun()} cried.'
    )
    world.say(
        f"{helper.id} stepped back, for there is no louder sound in a small field than a brag that has forgotten its size."
    )


def attempt(world: World, vole: Entity, item: Entity, boast: Boast, path: Path) -> None:
    item.meters["load"] = float(boast.weight)
    item.meters["wobble"] = float(boast.wobble)
    vole.meters["hauling"] += 1
    item.meters["distance_goal"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"So {vole.id} looped a stalk around {boast.item_label} and heaved. Up rose the load, wide as a moon pie and round as a wagon wheel."
    )
    if vole.meters["strain"] >= THRESHOLD:
        world.say(
            f"For three grand steps, {vole.id} looked mighty enough to tow a barn. On the fourth, {vole.pronoun('possessive')} paws trembled and the weight began to boss {vole.pronoun('object')} around."
        )
    else:
        world.say(
            f"For a little while, the boast almost looked true."
        )
    if world.get("path").meters["risk_now"] >= THRESHOLD:
        world.say(path.danger_line)


def sink(world: World, vole: Entity, item: Entity, path: Path) -> None:
    if vole.meters["stuck"] < THRESHOLD:
        return
    world.say(
        f"Then the {path.label} made up its own mind. It slurped at {vole.id}'s feet, gripped the wheels of the load, and held both as if the ground had grown sticky fingers."
    )
    world.say(
        f"{item.label.capitalize()} tipped, {vole.id} squeaked, and the whole meadow heard how small one brave vole sounded when pride turned into trouble."
    )


def call_for_help(world: World, vole: Entity, helper: Entity) -> None:
    vole.memes["humility"] += 1
    world.say(
        f'"{helper.id}!" {vole.id} called at last. "My brag was bigger than my paws. Please help me."'
    )


def rescue(world: World, helper: Entity, tool: Tool, item: Entity, vole: Entity) -> None:
    helper.meters["arrived"] += 1
    helper.meters["assist_power"] = float(helper.attrs["strength"])
    tool.meters["used"] += 1
    tool.meters["tool_power"] = float(tool.attrs["power"])
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} hurried over with {tool.phrase}. {tool.use_line}"
    )
    if vole.meters["stuck"] < THRESHOLD:
        world.say(
            f"Together they pulled in one calm rhythm until the load rolled free and the little vole popped out of the muck with a sound like a cork from a jug."
        )
    else:
        world.say(
            f"They tried and tugged, but the marsh still clung like glue."
        )


def lesson(world: World, vole: Entity, helper: Entity, tool: Tool) -> None:
    vole.memes["relief"] += 1
    world.say(
        f"When {vole.id} caught {vole.pronoun('possessive')} breath, {vole.pronoun()} bowed so low that {vole.pronoun('possessive')} nose brushed the grass."
    )
    world.say(
        f'"I thought sounding huge was the same as being wise," {vole.pronoun()} said. '
        f'"Now I know better. A small vole who asks for help and uses the right tool can do more than a bragging one all alone."'
    )
    world.say(
        f'{helper.id} smiled and patted {vole.id} on the shoulder. "That is the right-sized truth," {helper.pronoun()} said.'
    )
    world.say(
        f"After that, whenever work looked mountain-high, {vole.id} fetched {tool.label} and a friend before the first hard pull."
    )


def triumphant_end(world: World, vole: Entity, boast: Boast, helper: Entity) -> None:
    world.say(
        f"By sunset, {boast.item_label} stood safe at the feast patch, and nobody talked about the size of {vole.id}'s brag anymore."
    )
    world.say(
        f"They talked about the day a vole learned that teamwork can make even a tall tale stand on honest feet."
    )


def tell(
    boast: Boast,
    path: Path,
    helper_cfg: Helper,
    tool_cfg: Tool,
    vole_name: str = "Moss",
    vole_trait: str = "boastful",
    helper_name: str = "Aunt Bramble",
) -> World:
    world = World()
    vole = world.add(Entity(
        id=vole_name,
        kind="character",
        type="animal",
        label="the vole",
        traits=[vole_trait],
        role="hero",
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"caution_line": helper_cfg.caution_line, "strength": helper_cfg.strength},
        tags=set(helper_cfg.tags),
    ))
    item = world.add(Entity(id="item", kind="thing", type="load", label=boast.item_label))
    path_ent = world.add(Entity(id="path", kind="thing", type="path", label=path.label))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        attrs={"power": tool_cfg.power, "teamwork": tool_cfg.teamwork},
        tags=set(tool_cfg.tags),
    ))

    vole.meters["carry"] = 3.0
    vole.meters["strain"] = 0.0
    vole.meters["stuck"] = 0.0
    item.meters["load"] = 0.0
    item.meters["moved"] = 0.0
    item.meters["tilt"] = 0.0
    path_ent.meters["risk_now"] = 0.0
    helper.meters["arrived"] = 0.0
    helper.meters["assist_power"] = 0.0
    tool.meters["used"] = 0.0
    tool.meters["tool_power"] = 0.0

    world.facts.update(
        boast_cfg=boast,
        path_cfg=path,
        helper_cfg=helper_cfg,
        tool_cfg=tool_cfg,
        vole=vole,
        helper=helper,
        item=item,
        path=path_ent,
        tool=tool,
        path_risk=path.risk,
    )

    opening(world, vole, boast, path)
    world.para()
    warning(world, helper, vole, path, tool_cfg)
    boast_bigger(world, vole, boast, helper)
    world.para()
    attempt(world, vole, item, boast, path)
    sink(world, vole, item, path)
    world.para()
    call_for_help(world, vole, helper)
    rescue(world, helper, tool_cfg, item, vole)
    if vole.meters["stuck"] >= THRESHOLD:
        raise StoryError("(Story failed: the rescue plan could not free the vole.)")
    world.para()
    lesson(world, vole, helper, tool_cfg)
    triumphant_end(world, vole, boast, helper)

    world.facts.update(
        outcome="rescued",
        learned=vole.memes["humility"] >= THRESHOLD,
        stuck=vole.meters["stuck"] < THRESHOLD and item.meters["moved"] >= THRESHOLD,
        predicted_stuck=world.facts.get("predicted_stuck", False),
    )
    return world


BOASTS = {
    "giant_pumpkin": Boast(
        id="giant_pumpkin",
        item_label="the giant pumpkin",
        item_phrase="a giant pumpkin as plump as a hay wagon",
        giant_line="it was no heavier than a dandelion puff to me",
        weight=6,
        wobble=2,
        tags={"pumpkin", "brag"},
    ),
    "cheese_wheel": Boast(
        id="cheese_wheel",
        item_label="the cheese wheel",
        item_phrase="a cheese wheel broad enough to feed three fences of field mice",
        giant_line="I could roll it uphill with one paw and whistle with the other",
        weight=5,
        wobble=1,
        tags={"cheese", "brag"},
    ),
    "turnip_cart": Boast(
        id="turnip_cart",
        item_label="the turnip cart",
        item_phrase="a turnip cart piled so high it looked like a hill with roots",
        giant_line="I could drag it home before a cricket finished one song",
        weight=7,
        wobble=2,
        tags={"turnip", "brag"},
    ),
}

PATHS = {
    "marsh": Path(
        id="marsh",
        label="marsh path",
        texture="soft and shiny with black mud",
        hazard="swallowing wheels and boots",
        risk=2,
        danger_line="The marsh path shivered under the load, and mud began to gulp at every step.",
        tags={"marsh", "mud"},
    ),
    "creek_bank": Path(
        id="creek_bank",
        label="creek bank",
        texture="slick with reeds and bent grass",
        hazard="slipping and tipping",
        risk=1,
        danger_line="The creek bank slid sideways under the burden, as slippery as soap on a fish.",
        tags={"creek", "slip"},
    ),
    "mole_tunnel_rim": Path(
        id="mole_tunnel_rim",
        label="mole-tunnel rim",
        texture="humped and crumbly as old cake",
        hazard="caving under weight",
        risk=2,
        danger_line="The rim above the mole tunnels crumbled in little puffs, warning that heavy loads did not belong there.",
        tags={"tunnel", "crumbly"},
    ),
}

TOOLS = {
    "vine_harness": Tool(
        id="vine_harness",
        label="vine harness",
        phrase="a vine harness braided as neatly as a basket handle",
        power=4,
        teamwork=True,
        sensible=3,
        use_line="They slipped the harness around the load and leaned together instead of jerking alone.",
        qa_line="They used a vine harness so the pull was steady and shared.",
        tags={"tool", "harness", "teamwork"},
    ),
    "reed_rollers": Tool(
        id="reed_rollers",
        label="reed rollers",
        phrase="three smooth reed rollers cut from the creek edge",
        power=3,
        teamwork=True,
        sensible=3,
        use_line="They tucked the rollers under the load so it could glide instead of sink.",
        qa_line="They set reed rollers under the load so it would roll across the soft ground.",
        tags={"tool", "rollers", "teamwork"},
    ),
    "twig_poker": Tool(
        id="twig_poker",
        label="twig poker",
        phrase="a single poky twig",
        power=1,
        teamwork=False,
        sensible=1,
        use_line="They jabbed with the twig, which only splashed mud and did not help much.",
        qa_line="They only poked with a twig.",
        tags={"tool", "twig"},
    ),
}

HELPERS = {
    "aunt_bramble": Helper(
        id="aunt_bramble",
        type="aunt",
        label="the aunt",
        role_word="aunt",
        caution_line="Little paws should not argue with big loads",
        strength=4,
        sensible=3,
        tags={"aunt", "family", "help"},
    ),
    "old_mole": Helper(
        id="Old Mole",
        type="animal",
        label="the mole",
        role_word="neighbor",
        caution_line="A road may look flat and still hide a bad surprise underneath",
        strength=3,
        sensible=2,
        tags={"mole", "neighbor", "help"},
    ),
    "none": Helper(
        id="nobody",
        type="animal",
        label="nobody",
        role_word="nobody",
        caution_line="",
        strength=0,
        sensible=0,
        tags=set(),
    ),
}

VOLE_NAMES = ["Moss", "Nib", "Pip", "Clover", "Thimble", "Rill", "Bram", "Tumble"]
VOLE_TRAITS = ["boastful", "lively", "spry", "restless", "cheery"]


@dataclass
class StoryParams:
    boast: str
    path: str
    helper: str
    tool: str
    vole_name: str
    vole_trait: str
    helper_name: str
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
    "vole": [(
        "What is a vole?",
        "A vole is a very small animal that looks a bit like a mouse, but it usually has a shorter tail and likes grasslands, fields, or gardens."
    )],
    "marsh": [(
        "Why can a marsh be hard to cross?",
        "A marsh has wet, soft ground, so feet and wheels can sink into it. Heavy things are harder to pull there because the mud holds on."
    )],
    "tool": [(
        "Why is the right tool important?",
        "The right tool makes work safer and easier because it fits the job. A poor tool can waste effort or make a problem worse."
    )],
    "teamwork": [(
        "Why does teamwork help with hard jobs?",
        "Teamwork helps because more than one person can share the weight and steady the load. Working together also lets everyone think more carefully."
    )],
    "brag": [(
        "Why can bragging cause trouble?",
        "Bragging can make someone ignore good advice because they want to sound bigger than the problem. That can lead to mistakes."
    )],
    "help": [(
        "When should you ask for help?",
        "You should ask for help when a job is too heavy, unsafe, or tricky to do alone. Asking early is wise, not weak."
    )],
}
KNOWLEDGE_ORDER = ["vole", "brag", "marsh", "tool", "teamwork", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    vole = f["vole"]
    boast = f["boast_cfg"]
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a short tall tale for a 3-to-5-year-old about a vole who learns a lesson after bragging too much.',
        f"Tell a playful tall tale where {vole.id} the vole boasts about moving {boast.item_label} alone, gets into trouble on the {path.label}, and learns to ask for help.",
        f'Write a child-friendly story with a big, funny voice and a clear lesson: the right tool and a helper can do more than a giant brag.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    vole = f["vole"]
    helper = f["helper"]
    boast = f["boast_cfg"]
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {vole.id}, a little vole with a very big brag. {helper.id} also matters because {helper.pronoun()} warns and then helps {vole.pronoun('object')}."
        ),
        (
            f"What did {vole.id} brag about?",
            f"{vole.id} bragged that {boast.giant_line}. The brag was the start of the trouble because it made {vole.pronoun('object')} ignore a careful warning."
        ),
        (
            f"Why was the {path.label} dangerous?",
            f"The {path.label} was dangerous because it was {path.texture} and known for {path.hazard}. A heavy load made that danger worse, so the ground began to trap the vole."
        ),
        (
            f"What happened when {vole.id} tried to move {boast.item_label} alone?",
            f"{vole.id} strained under the heavy load and got stuck when the path turned grabby. Pride pushed {vole.pronoun('object')} into a job that was too hard to do alone."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} came with {tool.phrase}. {tool.qa_line} That let them free the load and the vole together."
        ),
        (
            "What lesson did the vole learn?",
            f"{vole.id} learned that asking for help and using the right tool is wiser than bragging. The ending proves it because after that, {vole.pronoun()} fetched help before starting heavy work."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vole", "brag", "help", "tool"}
    if world.facts["path_cfg"].id == "marsh":
        tags.add("marsh")
    if world.facts["tool_cfg"].teamwork:
        tags.add("teamwork")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        boast="giant_pumpkin",
        path="marsh",
        helper="aunt_bramble",
        tool="vine_harness",
        vole_name="Moss",
        vole_trait="boastful",
        helper_name="Aunt Bramble",
    ),
    StoryParams(
        boast="cheese_wheel",
        path="creek_bank",
        helper="old_mole",
        tool="reed_rollers",
        vole_name="Pip",
        vole_trait="lively",
        helper_name="Old Mole",
    ),
    StoryParams(
        boast="turnip_cart",
        path="mole_tunnel_rim",
        helper="aunt_bramble",
        tool="vine_harness",
        vole_name="Thimble",
        vole_trait="spry",
        helper_name="Aunt Bramble",
    ),
]


def explain_rejection(boast: Boast, path: Path, helper: Helper, tool: Tool) -> str:
    if helper.sensible < SENSE_MIN:
        return (
            f"(No story: {helper.id} is not a sensible helper choice here. A lesson story needs someone who can truly help the vole and offer real caution.)"
        )
    if tool.sensible < SENSE_MIN:
        return (
            f"(No story: {tool.label} is too weak or silly for this job. Pick a steadier tool like a vine harness or reed rollers.)"
        )
    demand = boast.weight + path.risk
    supply = helper.strength + tool.power
    return (
        f"(No story: {boast.item_label} over {path.label} needs strength {demand}, but this helper-and-tool plan only supplies {supply}. "
        f"The rescue must actually be able to free the load and the vole.)"
    )


ASP_RULES = r"""
sensible_helper(H) :- helper(H), helper_sense(H,S), sense_min(M), S >= M.
sensible_tool(T)   :- tool(T), tool_sense(T,S), sense_min(M), S >= M.
demand(B,P,D) :- boast_weight(B,W), path_risk(P,R), D = W + R.
supply(H,T,S) :- helper_strength(H,HS), tool_power(T,TP), S = HS + TP.
valid(B,P,H,T) :- boast(B), path(P), helper(H), tool(T),
                  sensible_helper(H), sensible_tool(T),
                  demand(B,P,D), supply(H,T,S), D >= 6, S >= D.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for boast_id, boast in BOASTS.items():
        lines.append(asp.fact("boast", boast_id))
        lines.append(asp.fact("boast_weight", boast_id, boast.weight))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("path_risk", path_id, path.risk))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_strength", helper_id, helper.strength))
        lines.append(asp.fact("helper_sense", helper_id, helper.sensible))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_power", tool_id, tool.power))
        lines.append(asp.fact("tool_sense", tool_id, tool.sensible))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    seeds_checked = 0
    for s in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            seeds_checked += 1
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {s}: {err}")
            break
    if rc == 0:
        print(f"OK: random generation smoke-tested on {seeds_checked} seeds.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tall-tale vole learns that help and the right tool beat bragging."
    )
    ap.add_argument("--boast", choices=BOASTS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None and HELPERS[args.helper].sensible < SENSE_MIN:
        helper = HELPERS[args.helper]
        boast = BOASTS[args.boast] if args.boast else next(iter(BOASTS.values()))
        path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(boast, path, helper, tool))
    if args.tool is not None and TOOLS[args.tool].sensible < SENSE_MIN:
        tool = TOOLS[args.tool]
        boast = BOASTS[args.boast] if args.boast else next(iter(BOASTS.values()))
        path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        raise StoryError(explain_rejection(boast, path, helper, tool))

    combos = [
        c for c in valid_combos()
        if (args.boast is None or c[0] == args.boast)
        and (args.path is None or c[1] == args.path)
        and (args.helper is None or c[2] == args.helper)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        boast = BOASTS[args.boast] if args.boast else next(iter(BOASTS.values()))
        path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(boast, path, helper, tool))

    boast_id, path_id, helper_id, tool_id = rng.choice(sorted(combos))
    helper_name = HELPERS[helper_id].id
    return StoryParams(
        boast=boast_id,
        path=path_id,
        helper=helper_id,
        tool=tool_id,
        vole_name=args.name or rng.choice(VOLE_NAMES),
        vole_trait=rng.choice(VOLE_TRAITS),
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.boast not in BOASTS:
        raise StoryError(f"(Unknown boast: {params.boast})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    boast = BOASTS[params.boast]
    path = PATHS[params.path]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]
    if not can_story_work(boast, path, helper, tool):
        raise StoryError(explain_rejection(boast, path, helper, tool))

    world = tell(
        boast=boast,
        path=path,
        helper_cfg=helper,
        tool_cfg=tool,
        vole_name=params.vole_name,
        vole_trait=params.vole_trait,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (boast, path, helper, tool) combos:\n")
        for boast, path, helper, tool in combos:
            print(f"  {boast:14} {path:16} {helper:12} {tool}")
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
            header = f"### {p.vole_name}: {p.boast} over {p.path} ({p.helper}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
