#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py
========================================================================================

A standalone story world for a gentle bedtime tale about a blanket fort, a moat,
a worried search, sharing one small light, and solving a problem together.

This world models a simple, child-facing pattern:

- two children build a bedtime fort with a make-believe moat
- a grown-up gives a soft warning that foreshadows the trouble
- one important bedtime item slips across the moat when the bridge tips
- instead of scrambling, the children share a single light, search for a tool,
  and think their way to a sensible rescue
- the ending image proves what changed: they are calmer, wiser, and better at
  sharing

Run it
------
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py --item storybook --tool cardboard_slide
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py --moat wide_blanket --tool pocket_rake
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/moat_search_sharing_foreshadowing_problem_solving_bedtime.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    island: str
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
class MoatCfg:
    id: str
    label: str
    phrase: str
    width: int
    shimmer: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    bedtime_need: str
    rescue_text: str
    ending_text: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    reach: int
    works_for: set[str]
    search_spot: str
    success_text: str
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
class LightCfg:
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


class World:
    def __init__(self, theme: Theme, moat: MoatCfg) -> None:
        self.theme = theme
        self.moat = moat
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
        return [e for e in self.entities.values() if e.role in {"lead", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.theme, self.moat)
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


def _r_stranded_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["stranded"] < THRESHOLD:
        return []
    sig = ("stranded_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    world.get("bridge").meters["usable"] = 0.0
    return ["__stranded__"]


def _r_share_cooperation(world: World) -> list[str]:
    light = world.get("light")
    if light.meters["shared"] < THRESHOLD:
        return []
    sig = ("share_cooperation", light.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["cooperation"] += 1
        kid.memes["calm"] += 1
    return ["__shared__"]


def _r_rescue_relief(world: World) -> list[str]:
    item = world.get("item")
    tool = world.get("tool")
    if tool.meters["used"] < THRESHOLD or not world.facts.get("tool_valid"):
        return []
    sig = ("rescue_relief", item.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["rescued"] += 1
    item.meters["stranded"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    return ["__rescued__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stranded_worry", tag="emotional", apply=_r_stranded_worry),
    Rule(name="share_cooperation", tag="social", apply=_r_share_cooperation),
    Rule(name="rescue_relief", tag="physical", apply=_r_rescue_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tool_works(tool: ToolCfg, moat: MoatCfg, item: LostItem) -> bool:
    return item.id in tool.works_for and tool.reach >= moat.width


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for moat_id, moat in MOATS.items():
            for item_id, item in ITEMS.items():
                for tool_id, tool in TOOLS.items():
                    if tool_works(tool, moat, item):
                        combos.append((theme_id, moat_id, item_id, tool_id))
    return combos


def predict_rescue(moat: MoatCfg, item: LostItem, tool: ToolCfg) -> dict:
    return {
        "reachable": tool.reach >= moat.width,
        "fits": item.id in tool.works_for,
        "success": tool_works(tool, moat, item),
    }


def introduce(world: World, lead: Entity, helper: Entity, theme: Theme, moat: MoatCfg) -> None:
    for kid in (lead, helper):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"On a soft evening, {lead.id} and {helper.id} built {theme.scene}. "
        f"{theme.rig} Around it they made {moat.phrase}, which shimmered like {moat.shimmer}."
    )
    world.say(
        f"They called the far cushion {theme.island}, and a flat bit of cardboard became the tiny bridge over the moat."
    )


def foreshadow(world: World, caregiver: Entity, lead: Entity, helper: Entity,
               item: LostItem, light: LightCfg, moat: MoatCfg) -> None:
    world.facts["warning"] = "one_at_a_time"
    if moat.width >= 2:
        extra = " If anything ends up beyond that wide moat, stop and think before anyone reaches."
    else:
        extra = " If anything slips beyond the moat, use quiet heads before quick feet."
    world.say(
        f"{lead.id}'s {caregiver.label_word} tucked {light.phrase} beside the fort and smiled. "
        f'"That bridge is only for light hands and little toes," {caregiver.pronoun()} said.{extra}'
    )
    world.say(
        f"The children nodded and carried on, planning to bring {item.bedtime_need} inside before the room grew sleepier."
    )


def slip(world: World, lead: Entity, helper: Entity, item: LostItem) -> None:
    itm = world.get("item")
    bridge = world.get("bridge")
    itm.meters["moving"] += 1
    bridge.meters["tilted"] += 1
    bridge.meters["fallen"] += 1
    itm.meters["stranded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {lead.id} tried to slide {item.bedtime_need} over the bridge, the cardboard bent with a whispering flap."
    )
    world.say(
        f"{item.rescue_text} and landed on the far cushion, safe but stranded beyond the moat."
    )
    if helper.memes["worry"] >= THRESHOLD:
        world.say(
            f"{helper.id} made a small worried sound. Bedtime could not feel quite right without it."
        )


def decide_to_share(world: World, lead: Entity, helper: Entity, light: LightCfg) -> None:
    world.get("light").meters["shared"] += 1
    propagate(world, narrate=False)
    world.facts["shared_light"] = True
    world.say(
        f'{helper.id} picked up the {light.label}. "{lead.id}, you hold the light low," '
        f'{helper.pronoun()} said. "I will search for something long enough."'
    )
    if all(k.memes["cooperation"] >= THRESHOLD for k in world.kids()):
        world.say(
            f"So {lead.id} shared the glow without fuss, and the room felt calmer at once."
        )


def search_for_tool(world: World, lead: Entity, helper: Entity, tool: ToolCfg) -> None:
    world.facts["search_spot"] = tool.search_spot
    world.get("tool").meters["found"] += 1
    world.say(
        f"Together they began their search: under the bed, beside the bookshelf, then {tool.search_spot}."
    )
    world.say(
        f"There {helper.id} found {tool.phrase}, just the sort of quiet, useful thing a bedtime problem needed."
    )


def rescue(world: World, lead: Entity, helper: Entity, tool: ToolCfg, item: LostItem) -> None:
    prediction = predict_rescue(world.moat, item, tool)
    world.facts["prediction"] = prediction
    world.facts["tool_valid"] = prediction["success"]
    world.get("tool").meters["used"] += 1
    propagate(world, narrate=False)
    if not prediction["success"]:
        raise StoryError(
            f"(No story: {tool.label} cannot sensibly bring back the {item.label} across {world.moat.label}.)"
        )
    world.say(
        f"{helper.id} knelt by the moat while {lead.id} kept the shared light steady."
    )
    world.say(tool.success_text.format(item=item.label))
    if world.get("item").meters["rescued"] >= THRESHOLD:
        world.say(
            f"Soon {item.bedtime_need} was back inside the fort, and both children let out the same relieved breath."
        )


def bedtime_end(world: World, lead: Entity, helper: Entity, caregiver: Entity, item: LostItem) -> None:
    for kid in (lead, helper):
        kid.memes["sleepy"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} peeked in and saw two children who had used gentle voices, a careful search, and a good idea."
    )
    world.say(
        f'"Now that is wise fort work," {caregiver.pronoun()} whispered.'
    )
    world.say(item.ending_text.format(lead=lead.id, helper=helper.id))
    if all(k.memes["pride"] >= THRESHOLD for k in world.kids()):
        world.say(
            f"With the moat quiet around them, {lead.id} and {helper.id} felt proud, snug, and ready for sleep."
        )


def tell(theme: Theme, moat: MoatCfg, item_cfg: LostItem, tool_cfg: ToolCfg,
         light_cfg: LightCfg, lead_name: str = "Nora", lead_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         caregiver_type: str = "mother") -> World:
    world = World(theme, moat)
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        traits=["sleepy", "imaginative"],
        attrs={"shares": True},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["careful", "thoughtful"],
        attrs={"shares": True},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the caregiver",
    ))
    world.add(Entity(
        id="bridge",
        type="bridge",
        label="bridge",
        phrase="the cardboard bridge",
        attrs={"over": moat.label},
        meters=defaultdict(float, {"usable": 1.0}),
    ))
    world.add(Entity(
        id="item",
        type="bedthing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        attrs={"need": item_cfg.bedtime_need},
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        attrs={"reach": tool_cfg.reach},
    ))
    world.add(Entity(
        id="light",
        type="light",
        label=light_cfg.label,
        phrase=light_cfg.phrase,
        attrs={"glow": light_cfg.glow},
    ))

    world.facts.update(
        lead=lead,
        helper=helper,
        caregiver=caregiver,
        theme=theme,
        moat=moat,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        light_cfg=light_cfg,
        warning="",
        shared_light=False,
        search_spot="",
        prediction={"reachable": False, "fits": False, "success": False},
        tool_valid=False,
    )

    introduce(world, lead, helper, theme, moat)
    foreshadow(world, caregiver, lead, helper, item_cfg, light_cfg, moat)

    world.para()
    slip(world, lead, helper, item_cfg)

    world.para()
    decide_to_share(world, lead, helper, light_cfg)
    search_for_tool(world, lead, helper, tool_cfg)
    rescue(world, lead, helper, tool_cfg, item_cfg)

    world.para()
    bedtime_end(world, lead, helper, caregiver, item_cfg)

    world.facts.update(
        item_rescued=world.get("item").meters["rescued"] >= THRESHOLD,
        bridge_broken=world.get("bridge").meters["fallen"] >= THRESHOLD,
        cooperation=all(k.memes["cooperation"] >= THRESHOLD for k in world.kids()),
    )
    return world


THEMES = {
    "blanket_castle": Theme(
        id="blanket_castle",
        scene="a blanket castle at the foot of the bed",
        rig="A quilt became the roof, two pillows stood like towers, and a folded sheet made a tiny silver gate",
        island="Moon Cushion Island",
        tags={"fort", "bedtime"},
    ),
    "moon_tent": Theme(
        id="moon_tent",
        scene="a moon tent beside the window",
        rig="A pale blanket was draped over two chairs, and a row of cushions made soft little walls",
        island="Cloud Pillow Island",
        tags={"fort", "bedtime"},
    ),
    "pillow_keep": Theme(
        id="pillow_keep",
        scene="a pillow keep under the night-light",
        rig="Bolsters became tall walls, a soft throw made the roof, and one round cushion stood like a tower door",
        island="Star Cushion Island",
        tags={"fort", "bedtime"},
    ),
}

MOATS = {
    "pillow_ring": MoatCfg(
        id="pillow_ring",
        label="a little pillow moat",
        phrase="a little moat of blue pillows",
        width=1,
        shimmer="moonlit water",
        tags={"moat"},
    ),
    "wide_blanket": MoatCfg(
        id="wide_blanket",
        label="a wide blanket moat",
        phrase="a wide moat of folded blankets",
        width=2,
        shimmer="a dark velvet river",
        tags={"moat"},
    ),
}

ITEMS = {
    "storybook": LostItem(
        id="storybook",
        label="storybook",
        phrase="their bedtime storybook with the silver moon on the cover",
        bedtime_need="the bedtime storybook",
        rescue_text="The storybook skated across the bridge, tipped over one corner",
        ending_text="{lead} and {helper} opened the storybook together and turned the pages one at a time until their eyes grew heavy.",
        tags={"book", "bedtime"},
    ),
    "plush_rabbit": LostItem(
        id="plush_rabbit",
        label="plush rabbit",
        phrase="their soft plush rabbit with floppy ears",
        bedtime_need="the plush rabbit they both loved to cuddle",
        rescue_text="The plush rabbit slid on its side, one floppy ear waving like a flag",
        ending_text="{lead} and {helper} tucked the plush rabbit between them, and each child rested one gentle hand on its soft ears.",
        tags={"plush", "sharing"},
    ),
    "star_pillow": LostItem(
        id="star_pillow",
        label="star pillow",
        phrase="their little star-shaped pillow",
        bedtime_need="the star pillow they liked to lean on while whispering good-night stories",
        rescue_text="The star pillow spun once like a lazy wheel",
        ending_text="{lead} and {helper} settled shoulder to shoulder with the star pillow between them, sharing one last whisper before sleep.",
        tags={"pillow", "sharing"},
    ),
}

TOOLS = {
    "pocket_rake": ToolCfg(
        id="pocket_rake",
        label="pocket rake",
        phrase="a small wooden pocket rake",
        reach=1,
        works_for={"storybook", "plush_rabbit", "star_pillow"},
        search_spot="in the toy basket by the dresser",
        success_text="Very slowly, {helper} used the little rake to catch the edge of the {item} and draw it back over the moat.",
        qa_text="used the small rake to pull it back across the moat",
        tags={"tool", "problem_solving"},
    ),
    "ribbon_loop": ToolCfg(
        id="ribbon_loop",
        label="ribbon loop",
        phrase="a long ribbon loop from the costume box",
        reach=2,
        works_for={"plush_rabbit"},
        search_spot="inside the costume box",
        success_text="Carefully, {helper} lowered the ribbon loop over the {item}, caught it without a tug, and lifted it safely home.",
        qa_text="lowered the ribbon loop over it and lifted it back",
        tags={"tool", "problem_solving", "sharing"},
    ),
    "cardboard_slide": ToolCfg(
        id="cardboard_slide",
        label="cardboard slide",
        phrase="a long smooth piece of cardboard",
        reach=2,
        works_for={"storybook", "star_pillow"},
        search_spot="behind the bookshelf",
        success_text="Patiently, {helper} slid the cardboard out like a drawbridge, nudged the {item} onto it, and guided it back into the fort.",
        qa_text="slid a long piece of cardboard under it and guided it back",
        tags={"tool", "problem_solving"},
    ),
}

LIGHTS = {
    "moon_flashlight": LightCfg(
        id="moon_flashlight",
        label="moon flashlight",
        phrase="a moon flashlight",
        glow="a pale round glow",
        tags={"light", "sharing"},
    ),
    "star_lantern": LightCfg(
        id="star_lantern",
        label="star lantern",
        phrase="a star lantern",
        glow="a warm dotted glow",
        tags={"light", "sharing"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Ella", "Rose", "Lucy", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]


@dataclass
class StoryParams:
    theme: str = "blanket_castle"
    moat: str = "pillow_ring"
    item: str = "storybook"
    tool: str = "cardboard_slide"
    light: str = "moon_flashlight"
    lead_name: str = "Nora"
    lead_gender: str = "girl"
    helper_name: str = "Ben"
    helper_gender: str = "boy"
    caregiver: str = "mother"
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
    "moat": [
        (
            "What is a moat?",
            "A moat is a ditch or ring that goes around something, like a castle. In pretend play, children can call a ring of pillows or blankets a moat because it feels like water around a fort.",
        )
    ],
    "search": [
        (
            "What does it mean to search for something?",
            "To search means to look carefully for something you need. A good search is calm and slow, so you can notice the right place to look.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help when there is only one light?",
            "Sharing lets two people use one helpful thing together instead of arguing over it. One child can hold the light while the other uses both hands to solve the problem.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means stopping to think about what went wrong and trying a good plan. Often the best plan uses the right tool in a careful way.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when an early clue hints at something that will matter later. A warning about a wobbly bridge can prepare you for trouble before it happens.",
        )
    ],
    "light": [
        (
            "Why is a small light helpful at bedtime?",
            "A small light helps you see without making the room bright and busy. That makes it easier to stay calm and sleepy.",
        )
    ],
    "book": [
        (
            "Why do people read a storybook at bedtime?",
            "A bedtime storybook can help children slow down and settle. The quiet rhythm of reading makes the end of the day feel safe and cozy.",
        )
    ],
    "plush": [
        (
            "Why can a plush toy feel comforting at night?",
            "A soft plush toy can make bedtime feel less lonely and more secure. Holding something familiar can help a child relax.",
        )
    ],
    "tool": [
        (
            "Why should you choose the right tool for a job?",
            "The right tool makes a job safer and easier. A tool that is too short or the wrong shape can make the problem harder instead of better.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "moat",
    "search",
    "sharing",
    "problem_solving",
    "foreshadowing",
    "light",
    "book",
    "plush",
    "tool",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    item = f["item_cfg"]
    moat = f["moat"]
    return [
        (
            f'Write a gentle bedtime story for a 3-to-5-year-old that includes the words '
            f'"moat" and "search", where two children lose {item.bedtime_need} across {moat.label} and solve the problem by sharing one light.'
        ),
        (
            f"Tell a cozy story where {lead.id} and {helper.id} make a fort, a grown-up warning foreshadows a small problem, and the children think carefully instead of rushing."
        ),
        (
            "Write a bedtime tale about sharing, problem solving, and a careful search that ends with a calm picture of the children settling down to sleep."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    caregiver = f["caregiver"]
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    moat = f["moat"]
    light = f["light_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {helper.id}, two children building a bedtime fort, and {lead.id}'s {caregiver.label_word} who gave them a gentle warning. The story stays close to the little problem they face together.",
        ),
        (
            "What was the moat in the story?",
            f"The moat was {moat.phrase} around the fort. It was pretend, but once the item landed across it, the children still had to treat the space carefully.",
        ),
        (
            f"What problem happened to {item.bedtime_need}?",
            f"It slipped over the bent bridge and got stranded on the far cushion beyond the moat. That mattered because bedtime did not feel complete without it.",
        ),
        (
            "How did the warning at the beginning matter later?",
            f"{caregiver.label_word.capitalize()} warned that the bridge was only for light little crossings and that the children should stop and think if something slipped away. Later, that early warning came true, so the children solved the trouble carefully instead of climbing after the item.",
        ),
        (
            "How did sharing help them solve the problem?",
            f"They shared the {light.label}, with one child holding the glow steady while the other searched and worked. That made them calmer, and it also let both children help at the same time.",
        ),
        (
            f"How did they get the {item.label} back?",
            f"They searched {f['search_spot']} and found {tool.phrase}. Then {tool.qa_text}, which worked because it was a sensible tool for that item and moat.",
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely inside the fort after the item was rescued. {item.ending_text.format(lead=lead.id, helper=helper.id)}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"moat", "search", "sharing", "problem_solving", "foreshadowing"}
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    light = f["light_cfg"]
    if "book" in item.tags:
        tags.add("book")
    if "plush" in item.tags:
        tags.add("plush")
    if tool.tags:
        tags.add("tool")
    if light.tags:
        tags.add("light")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="blanket_castle",
        moat="pillow_ring",
        item="storybook",
        tool="pocket_rake",
        light="moon_flashlight",
        lead_name="Nora",
        lead_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        caregiver="mother",
    ),
    StoryParams(
        theme="moon_tent",
        moat="wide_blanket",
        item="plush_rabbit",
        tool="ribbon_loop",
        light="star_lantern",
        lead_name="Ella",
        lead_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        caregiver="father",
    ),
    StoryParams(
        theme="pillow_keep",
        moat="wide_blanket",
        item="star_pillow",
        tool="cardboard_slide",
        light="moon_flashlight",
        lead_name="Leo",
        lead_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        caregiver="mother",
    ),
    StoryParams(
        theme="moon_tent",
        moat="pillow_ring",
        item="plush_rabbit",
        tool="pocket_rake",
        light="star_lantern",
        lead_name="Rose",
        lead_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        caregiver="father",
    ),
]


def explain_rejection(moat: MoatCfg, item: LostItem, tool: ToolCfg) -> str:
    parts = []
    if item.id not in tool.works_for:
        parts.append(f"{tool.label} is the wrong shape for the {item.label}")
    if tool.reach < moat.width:
        parts.append(f"{tool.label} is too short for {moat.label}")
    if not parts:
        parts.append("this combination is not sensible in the world model")
    return f"(No story: {' and '.join(parts)}.)"


ASP_RULES = r"""
works(Tool, Item) :- handles(Tool, Item).
long_enough(Tool, Moat) :- reach(Tool, R), width(Moat, W), R >= W.
valid(Theme, Moat, Item, Tool) :- theme(Theme), moat(Moat), item(Item), tool(Tool),
                                  works(Tool, Item), long_enough(Tool, Moat).

ok_choice :- chosen_theme(T), chosen_moat(M), chosen_item(I), chosen_tool(To),
             valid(T, M, I, To).
outcome(success) :- ok_choice.
outcome(invalid) :- not ok_choice.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for moat_id, moat in MOATS.items():
        lines.append(asp.fact("moat", moat_id))
        lines.append(asp.fact("width", moat_id, moat.width))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        for item_id in sorted(tool.works_for):
            lines.append(asp.fact("handles", tool_id, item_id))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_theme", params.theme),
            asp.fact("chosen_moat", params.moat),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    try:
        moat = MOATS[params.moat]
        item = ITEMS[params.item]
        tool = TOOLS[params.tool]
    except KeyError as exc:
        raise StoryError(f"(No story: unknown option {exc.args[0]!r}.)") from exc
    return "success" if tool_works(tool, moat, item) else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime fort, a moat, a search, sharing, and problem solving."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--moat", choices=MOATS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.moat and args.item and args.tool:
        if not tool_works(TOOLS[args.tool], MOATS[args.moat], ITEMS[args.item]):
            raise StoryError(explain_rejection(MOATS[args.moat], ITEMS[args.item], TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.moat is None or c[1] == args.moat)
        and (args.item is None or c[2] == args.item)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, moat, item, tool = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(LIGHTS))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=lead_name)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        moat=moat,
        item=item,
        tool=tool,
        light=light,
        lead_name=lead_name,
        lead_gender=lead_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        caregiver=caregiver,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme {params.theme!r}.)")
    if params.moat not in MOATS:
        raise StoryError(f"(No story: unknown moat {params.moat!r}.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item {params.item!r}.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool {params.tool!r}.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light {params.light!r}.)")
    if not tool_works(TOOLS[params.tool], MOATS[params.moat], ITEMS[params.item]):
        raise StoryError(explain_rejection(MOATS[params.moat], ITEMS[params.item], TOOLS[params.tool]))
    world = tell(
        THEMES[params.theme],
        MOATS[params.moat],
        ITEMS[params.item],
        TOOLS[params.tool],
        LIGHTS[params.light],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        caregiver_type=params.caregiver,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(25):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    smoke_cases = cases[:5]
    try:
        for p in smoke_cases:
            sample = generate(p)
            if not sample.story.strip():
                raise StoryError("(Verification failed: generated empty story.)")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header="### smoke")
        default_params = resolve_params(parser.parse_args([]), random.Random(123))
        default_sample = generate(default_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(default_sample, trace=False, qa=False)
        print("OK: smoke-tested ordinary generation and emit().")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, moat, item, tool) combos:\n")
        for theme, moat, item, tool in combos:
            print(f"  {theme:15} {moat:13} {item:13} {tool}")
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
            header = f"### {p.lead_name} & {p.helper_name}: {p.item} across {p.moat} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
