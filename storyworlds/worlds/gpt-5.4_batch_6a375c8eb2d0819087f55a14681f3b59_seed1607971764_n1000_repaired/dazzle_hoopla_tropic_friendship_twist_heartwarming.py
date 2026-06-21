#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py
=================================================================================

A standalone story world about two friends preparing a small island fair.
One child wants the lantern path to look extra dazzling for the evening
hoopla, but a gusty tropic breeze makes one decoration choice unsafe.
Their friendship is tested for a moment, then a twist reveals a better
material and the celebration ends warmer and brighter than before.

Run it
------
    python storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py
    python storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/dazzle_hoopla_tropic_friendship_twist_heartwarming.py --verify
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
class Setting:
    id: str
    place: str
    scene: str
    breeze: int
    water: str
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
class LightIdea:
    id: str
    label: str
    phrase: str
    shimmer: str
    fragile: bool
    wind_risk: int
    makes_dazzle: bool = True
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
class Anchor:
    id: str
    label: str
    phrase: str
    strength: int
    text: str
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
class Discovery:
    id: str
    label: str
    phrase: str
    safe_with_fragile: bool
    twist_text: str
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
class Celebration:
    id: str
    label: str
    phrase: str
    closing: str
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
        return [e for e in self.entities.values() if e.role in {"planner", "helper"}]

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


def _r_breeze_tugs(world: World) -> list[str]:
    out: list[str] = []
    breeze = world.setting.breeze
    path = world.get("path")
    idea = world.get("idea")
    if not idea.attrs.get("fragile"):
        return out
    if breeze <= 0:
        return out
    sig = ("breeze_tugs", breeze, idea.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    idea.meters["sway"] += float(breeze)
    path.meters["risk"] += float(breeze)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_anchor_helps(world: World) -> list[str]:
    out: list[str] = []
    anchor = world.get("anchor")
    path = world.get("path")
    if anchor.meters["used"] < THRESHOLD:
        return out
    sig = ("anchor_helps", anchor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["stability"] += anchor.attrs.get("strength", 0)
    out.append("__stabilized__")
    return out


def _r_twist_discovery(world: World) -> list[str]:
    out: list[str] = []
    discovery = world.get("discovery")
    idea = world.get("idea")
    if discovery.meters["found"] < THRESHOLD and discovery.attrs.get("safe_with_fragile"):
        return out
    if discovery.meters["found"] < THRESHOLD:
        return out
    sig = ("twist_discovery", discovery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if idea.attrs.get("fragile"):
        world.get("path").meters["risk"] = 0.0
        world.get("path").meters["stability"] += 2.0
    for kid in world.kids():
        kid.memes["hope"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule(name="breeze_tugs", tag="physical", apply=_r_breeze_tugs),
    Rule(name="anchor_helps", tag="physical", apply=_r_anchor_helps),
    Rule(name="twist_discovery", tag="physical", apply=_r_twist_discovery),
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


def risky_combo(idea: LightIdea, setting: Setting) -> bool:
    return idea.fragile and setting.breeze >= idea.wind_risk


def sensible_anchor(anchor: Anchor, idea: LightIdea, setting: Setting) -> bool:
    if not idea.fragile:
        return True
    if anchor.strength < setting.breeze:
        return False
    return anchor.strength >= max(1, idea.wind_risk - 1)


def twist_works(discovery: Discovery, idea: LightIdea) -> bool:
    return (not idea.fragile) or discovery.safe_with_fragile


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for idea_id, idea in IDEAS.items():
            for anchor_id, anchor in ANCHORS.items():
                for discovery_id, discovery in DISCOVERIES.items():
                    if risky_combo(idea, setting) and not sensible_anchor(anchor, idea, setting):
                        continue
                    if risky_combo(idea, setting) and not twist_works(discovery, idea):
                        continue
                    if sensible_anchor(anchor, idea, setting):
                        combos.append((setting_id, idea_id, anchor_id, discovery_id))
                    elif twist_works(discovery, idea):
                        combos.append((setting_id, idea_id, anchor_id, discovery_id))
    return sorted(set(combos))


def predict_path(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    path = sim.get("path")
    return {
        "risk": path.meters["risk"],
        "stable": path.meters["stability"] >= max(1, sim.setting.breeze),
    }


def opening(world: World, planner: Entity, helper: Entity, setting: Setting, party: Celebration) -> None:
    for kid in (planner, helper):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"In {setting.place}, {planner.id} and {helper.id} were best friends who loved making small kind surprises."
    )
    world.say(
        f"That evening, the village was getting ready for {party.phrase}. {setting.scene} made the whole shore feel soft and bright."
    )
    world.say(
        f'The two friends promised to decorate the garden path so the neighbors would smile the moment they arrived.'
    )


def goal(world: World, planner: Entity, idea: LightIdea) -> None:
    planner.memes["pride"] += 1
    world.say(
        f'"Let\'s make it dazzle," {planner.id} said. {planner.pronoun().capitalize()} held up {idea.phrase}, and {idea.shimmer}.'
    )
    if idea.makes_dazzle:
        world.say("For one happy moment, the plan seemed perfect for the coming hoopla.")


def warning(world: World, helper: Entity, planner: Entity, setting: Setting, idea: LightIdea) -> None:
    pred = predict_path(world)
    world.facts["predicted_risk"] = pred["risk"]
    helper.memes["care"] += 1
    breeze_words = "tropic breeze" if "tropic" in setting.tags else "warm breeze"
    world.say(
        f'But {helper.id} felt {breeze_words} brush past {helper.pronoun("possessive")} cheek and looked up at the moving palms.'
    )
    if idea.fragile and pred["risk"] >= THRESHOLD:
        world.say(
            f'"They are beautiful," {helper.id} said, "but that breeze might tug them loose before anyone can enjoy them."'
        )
    else:
        world.say(
            f'"They are beautiful," {helper.id} said, "and I think we can make them stay just right."'
        )


def pinch(world: World, planner: Entity, helper: Entity) -> None:
    planner.memes["hurt"] += 1
    helper.memes["hurt"] += 1
    world.say(
        f'"You always worry when I dream big," {planner.id} blurted out.'
    )
    world.say(
        f'The words came too fast. {helper.id} went quiet, and the cheerful work on the path suddenly felt smaller.'
    )


def try_anchor(world: World, planner: Entity, helper: Entity, anchor: Anchor) -> None:
    world.get("anchor").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} did not stomp away. Instead, {helper.pronoun()} picked up {anchor.phrase} and {anchor.text}.'
    )
    if world.get("path").meters["stability"] >= max(1, world.setting.breeze):
        planner.memes["respect"] += 1
        helper.memes["trust"] += 1
        world.say("The little lights stopped dancing so wildly. The path still gleamed, but now it felt calm too.")
    else:
        world.say("It helped a little, but the breeze still teased the decorations from side to side.")


def twist(world: World, planner: Entity, helper: Entity, discovery: Discovery, idea: LightIdea) -> None:
    world.get("discovery").meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then came the twist. {helper.id} reached into the supply basket and found {discovery.phrase}.'
    )
    world.say(discovery.twist_text)
    if twist_works(discovery, idea):
        planner.memes["surprise"] += 1
        helper.memes["hope"] += 1


def mend(world: World, planner: Entity, helper: Entity) -> None:
    planner.memes["love"] += 1
    helper.memes["love"] += 1
    planner.memes["hurt"] = 0.0
    helper.memes["hurt"] = 0.0
    world.say(
        f'{planner.id} looked at {helper.id} and felt ashamed of the sharp words.'
    )
    world.say(
        f'"I\'m sorry," {planner.pronoun()} said. "You were trying to protect our work, not spoil it."'
    )
    world.say(
        f'{helper.id} smiled a little and squeezed {planner.pronoun("possessive")} hand. "We can make it lovely together," {helper.pronoun()} said.'
    )


def finish(world: World, planner: Entity, helper: Entity, idea: LightIdea, discovery: Discovery, party: Celebration) -> None:
    path = world.get("path")
    stable = path.meters["risk"] < THRESHOLD or path.meters["stability"] >= max(1, world.setting.breeze)
    for kid in (planner, helper):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
        kid.memes["relief"] += 1
    if stable:
        world.say(
            f'Soon the path shone with {idea.label} light, and the hidden help from {discovery.label} made every lantern sit safely in place.'
        )
        world.say(
            f"When the neighbors arrived for the hoopla, they stopped and stared. The whole walkway seemed to dazzle without a single thing blowing away."
        )
    else:
        world.say(
            "The path looked pretty, but the children kept watch beside it all evening, steadying the decorations whenever the wind tried to fuss with them."
        )
    world.say(
        party.closing
    )
    world.facts["stable_ending"] = stable


def tell(
    setting: Setting,
    idea: LightIdea,
    anchor: Anchor,
    discovery: Discovery,
    party: Celebration,
    planner_name: str = "Mina",
    planner_type: str = "girl",
    helper_name: str = "Tao",
    helper_type: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    planner = world.add(Entity(id=planner_name, kind="character", type=planner_type, role="planner"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the parent"))
    path = world.add(Entity(id="path", type="path", label="garden path"))
    idea_ent = world.add(
        Entity(
            id="idea",
            type="decoration",
            label=idea.label,
            attrs={"fragile": idea.fragile, "wind_risk": idea.wind_risk},
        )
    )
    anchor_ent = world.add(
        Entity(
            id="anchor",
            type="anchor",
            label=anchor.label,
            attrs={"strength": anchor.strength},
        )
    )
    discovery_ent = world.add(
        Entity(
            id="discovery",
            type="discovery",
            label=discovery.label,
            attrs={"safe_with_fragile": discovery.safe_with_fragile},
        )
    )
    # initialize meters/memes used by rules before propagate()
    path.meters["risk"] = 0.0
    path.meters["stability"] = 0.0
    idea_ent.meters["sway"] = 0.0
    anchor_ent.meters["used"] = 0.0
    discovery_ent.meters["found"] = 0.0
    planner.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0

    world.facts["setting"] = setting
    world.facts["idea_cfg"] = idea
    world.facts["anchor_cfg"] = anchor
    world.facts["discovery_cfg"] = discovery
    world.facts["party"] = party
    world.facts["planner_name"] = planner_name
    world.facts["helper_name"] = helper_name

    opening(world, planner, helper, setting, party)
    goal(world, planner, idea)

    world.para()
    warning(world, helper, planner, setting, idea)
    if risky_combo(idea, setting):
        propagate(world, narrate=False)
        pinch(world, planner, helper)
        world.para()
        try_anchor(world, planner, helper, anchor)
        if world.get("path").meters["stability"] < max(1, setting.breeze):
            twist(world, planner, helper, discovery, idea)
        else:
            twist(world, planner, helper, discovery, idea)
        mend(world, planner, helper)
    else:
        try_anchor(world, planner, helper, anchor)
        twist(world, planner, helper, discovery, idea)
        mend(world, planner, helper)

    world.para()
    finish(world, planner, helper, idea, discovery, party)

    world.facts.update(
        planner=planner,
        helper=helper,
        parent=parent,
        path=path,
        risky=risky_combo(idea, setting),
        stable=world.facts.get("stable_ending", False),
        used_anchor=anchor_ent.meters["used"] >= THRESHOLD,
        found_discovery=discovery_ent.meters["found"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="a little tropic cove",
        scene="Breadfruit leaves rustled over the path, and the sea kept whispering beyond the fence.",
        breeze=2,
        water="sea",
        tags={"tropic", "shore"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the island harbor garden",
        scene="Palm shadows stretched long across the stones, and fishing boats bobbed gently nearby.",
        breeze=1,
        water="harbor",
        tags={"tropic", "boats"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the sunny courtyard by the mango trees",
        scene="The flowers nodded in the warm air, and the old wall held back most of the wind.",
        breeze=1,
        water="fountain",
        tags={"garden"},
    ),
}

IDEAS = {
    "shell_lanterns": LightIdea(
        id="shell_lanterns",
        label="shell lanterns",
        phrase="a row of shell lanterns",
        shimmer="their pearly sides caught the late sun in a dazzle of pink and gold",
        fragile=True,
        wind_risk=2,
        tags={"lantern", "shell"},
    ),
    "paper_stars": LightIdea(
        id="paper_stars",
        label="paper stars",
        phrase="a line of paper stars",
        shimmer="their colored points made the path look ready for singing and dancing",
        fragile=True,
        wind_risk=1,
        tags={"paper", "festival"},
    ),
    "glass_jars": LightIdea(
        id="glass_jars",
        label="glass jar lights",
        phrase="three glass jar lights",
        shimmer="the little jars looked steady and warm in planner hands",
        fragile=False,
        wind_risk=3,
        tags={"jar", "safe_light"},
    ),
}

ANCHORS = {
    "driftwood": Anchor(
        id="driftwood",
        label="driftwood bases",
        phrase="some smooth driftwood bases",
        strength=1,
        text="set each light into a hollow place in the wood",
        tags={"driftwood"},
    ),
    "sand_rings": Anchor(
        id="sand_rings",
        label="sand rings",
        phrase="small sand rings packed in bowls",
        strength=2,
        text="pressed the bowls into neat sand rings so the decorations would not skid",
        tags={"sand"},
    ),
    "banana_twine": Anchor(
        id="banana_twine",
        label="banana-fiber twine",
        phrase="a coil of banana-fiber twine",
        strength=3,
        text="tied each light gently to the rail with careful loops",
        tags={"fiber"},
    ),
}

DISCOVERIES = {
    "sea_glass_cups": Discovery(
        id="sea_glass_cups",
        label="sea-glass cups",
        phrase="a set of sea-glass cups",
        safe_with_fragile=True,
        twist_text="The shells could sit inside them like tiny moons in green glass, safe from the breeze and brighter than before.",
        tags={"sea_glass"},
    ),
    "mango_leaves": Discovery(
        id="mango_leaves",
        label="mango leaves",
        phrase="a bundle of glossy mango leaves",
        safe_with_fragile=False,
        twist_text="The leaves made a pretty border, but they did not solve the problem of the shaking lanterns.",
        tags={"leaves"},
    ),
    "coral_tray": Discovery(
        id="coral_tray",
        label="a coral-colored tray",
        phrase="a coral-colored tray with little hollows",
        safe_with_fragile=True,
        twist_text="Each shell lantern fit into a hollow so snugly that the breeze could only make the light wink, not wander.",
        tags={"tray"},
    ),
}

CELEBRATIONS = {
    "moon_fair": Celebration(
        id="moon_fair",
        label="moon fair",
        phrase="the moon fair",
        closing="Later, as music floated under the stars, the two friends stood shoulder to shoulder and knew the best part of the night was not the lanterns at all. It was how friendship had turned a mistake into something kinder and more beautiful.",
        tags={"fair"},
    ),
    "boat_song": Celebration(
        id="boat_song",
        label="boat-song evening",
        phrase="boat-song evening",
        closing="When the first voices rose from the harbor, the path welcomed every guest softly. The children grinned at each other, proud that they had listened, forgiven, and built the evening together.",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Mina", "Lani", "Suri", "Nila", "Asha", "Kira", "Tala", "Ivy"]
BOY_NAMES = ["Tao", "Kai", "Noa", "Ben", "Eli", "Rafi", "Milo", "Nico"]


@dataclass
class StoryParams:
    setting: str
    idea: str
    anchor: str
    discovery: str
    celebration: str
    planner_name: str
    planner_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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
    "tropic": [
        (
            "What does tropic mean?",
            "Tropic places are warm places near the middle of the Earth. They often have bright sun, palms, and breezes from the sea."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around it. The cover helps the light glow while keeping it steadier and safer."
        )
    ],
    "breeze": [
        (
            "What is a breeze?",
            "A breeze is a soft wind. Even a soft wind can push light things and make them sway."
        )
    ],
    "friendship": [
        (
            "What helps a friendship stay strong after hurt feelings?",
            "Listening, apologizing, and trying again together help friendship grow strong. Kind words can mend feelings after a sharp moment."
        )
    ],
    "sea_glass": [
        (
            "What is sea glass?",
            "Sea glass is broken glass that has been smoothed by water and sand for a long time. It feels soft and rounded instead of sharp."
        )
    ],
    "festival": [
        (
            "What is a festival or hoopla?",
            "A festival, or hoopla, is a happy gathering with music, lights, and people celebrating together. It feels lively and special."
        )
    ],
}
KNOWLEDGE_ORDER = ["tropic", "lantern", "breeze", "friendship", "sea_glass", "festival"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    setting = f["setting"]
    idea = f["idea_cfg"]
    party = f["party"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that uses the words "dazzle", "hoopla", and "tropic".',
        f"Tell a friendship story where {planner.id} and {helper.id} decorate a path for {party.phrase} in {setting.place}, and a small twist helps them solve a windy problem together.",
        f"Write a gentle story where beautiful {idea.label} almost cause trouble, but two friends listen, apologize, and make the celebration shine safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    setting = f["setting"]
    idea = f["idea_cfg"]
    anchor = f["anchor_cfg"]
    discovery = f["discovery_cfg"]
    party = f["party"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {planner.id} and {helper.id}, who decorate a path for {party.phrase}. They work together in {setting.place}."
        ),
        (
            f"What did {planner.id} want the path to look like?",
            f"{planner.id} wanted it to dazzle. {planner.pronoun().capitalize()} thought {idea.label} would make the path look extra beautiful for the hoopla."
        ),
        (
            f"Why did {helper.id} worry about the plan?",
            f"{helper.id} felt the breeze and knew the decorations might not stay where they belonged. The moving air could tug the fragile lights loose before the guests arrived."
        ),
    ]
    if f["risky"]:
        qa.append(
            (
                f"How did the friends' feelings change in the middle of the story?",
                f"{planner.id} said something hurtful because {planner.pronoun()} felt disappointed, and {helper.id} went quiet. Later they apologized and remembered they were trying to help each other, not win an argument."
            )
        )
    qa.append(
        (
            "What was the twist?",
            f"The twist was that they found {discovery.phrase} in the supply basket. That surprise gave them a safer way to keep the pretty lights and still protect the path from the breeze."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They finished the path together, and the guests arrived smiling for the hoopla. The ending feels warm because the friends repaired their feelings while fixing the decorations."
        )
    )
    if f["used_anchor"]:
        qa.append(
            (
                f"How did {helper.id} try to help before the twist?",
                f"{helper.id} used {anchor.phrase} to steady the lights. That showed {helper.pronoun()} was trying to save the beautiful plan, not stop it."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    if "tropic" in world.setting.tags:
        tags.add("tropic")
    tags.add("lantern")
    tags.add("friendship")
    if world.facts.get("risky"):
        tags.add("breeze")
    if world.facts["discovery_cfg"].id == "sea_glass_cups":
        tags.add("sea_glass")
    tags.add("festival")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cove",
        idea="shell_lanterns",
        anchor="sand_rings",
        discovery="sea_glass_cups",
        celebration="moon_fair",
        planner_name="Mina",
        planner_gender="girl",
        helper_name="Tao",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="harbor",
        idea="paper_stars",
        anchor="banana_twine",
        discovery="coral_tray",
        celebration="boat_song",
        planner_name="Lani",
        planner_gender="girl",
        helper_name="Kai",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="courtyard",
        idea="glass_jars",
        anchor="driftwood",
        discovery="mango_leaves",
        celebration="moon_fair",
        planner_name="Asha",
        planner_gender="girl",
        helper_name="Noa",
        helper_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(setting: Setting, idea: LightIdea, anchor: Anchor, discovery: Discovery) -> str:
    if risky_combo(idea, setting) and not sensible_anchor(anchor, idea, setting) and not twist_works(discovery, idea):
        return (
            f"(No story: in {setting.place}, {idea.label} are too fragile for that breeze, "
            f"{anchor.label} are not strong enough, and {discovery.label} do not solve the danger. "
            f"Pick a stronger anchor or a discovery that can shelter the lights.)"
        )
    return "(No story: this combination does not make a reasonable path-building fix.)"


ASP_RULES = r"""
risky(I,S) :- idea(I), setting(S), fragile(I), breeze(S,B), wind_risk(I,W), B >= W.
strong_anchor(A,S,I) :- anchor(A), setting(S), idea(I), strength(A,N), breeze(S,B), N >= B, wind_risk(I,W), N >= W-1.
twist_works(D) :- discovery(D), safe_with_fragile(D).
valid(S,I,A,D) :- setting(S), idea(I), anchor(A), discovery(D), not risky(I,S).
valid(S,I,A,D) :- risky(I,S), strong_anchor(A,S,I).
valid(S,I,A,D) :- risky(I,S), twist_works(D).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("breeze", sid, setting.breeze))
    for iid, idea in IDEAS.items():
        lines.append(asp.fact("idea", iid))
        if idea.fragile:
            lines.append(asp.fact("fragile", iid))
        lines.append(asp.fact("wind_risk", iid, idea.wind_risk))
    for aid, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", aid))
        lines.append(asp.fact("strength", aid, anchor.strength))
    for did, discovery in DISCOVERIES.items():
        lines.append(asp.fact("discovery", did))
        if discovery.safe_with_fragile:
            lines.append(asp.fact("safe_with_fragile", did))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty random story")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    if rc == 0:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two friends, a windy island path, and a heartwarming twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--discovery", choices=DISCOVERIES)
    ap.add_argument("--celebration", choices=CELEBRATIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.idea and args.anchor and args.discovery:
        setting = SETTINGS[args.setting]
        idea = IDEAS[args.idea]
        anchor = ANCHORS[args.anchor]
        discovery = DISCOVERIES[args.discovery]
        if (args.setting, args.idea, args.anchor, args.discovery) not in valid_combos():
            raise StoryError(explain_rejection(setting, idea, anchor, discovery))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.idea is None or combo[1] == args.idea)
        and (args.anchor is None or combo[2] == args.anchor)
        and (args.discovery is None or combo[3] == args.discovery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, idea_id, anchor_id, discovery_id = rng.choice(sorted(combos))
    celebration = args.celebration or rng.choice(sorted(CELEBRATIONS))
    planner_name, planner_gender = _pick_kid(rng)
    helper_name, helper_gender = _pick_kid(rng, avoid=planner_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        idea=idea_id,
        anchor=anchor_id,
        discovery=discovery_id,
        celebration=celebration,
        planner_name=planner_name,
        planner_gender=planner_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.idea not in IDEAS:
        raise StoryError(f"Unknown idea: {params.idea}")
    if params.anchor not in ANCHORS:
        raise StoryError(f"Unknown anchor: {params.anchor}")
    if params.discovery not in DISCOVERIES:
        raise StoryError(f"Unknown discovery: {params.discovery}")
    if params.celebration not in CELEBRATIONS:
        raise StoryError(f"Unknown celebration: {params.celebration}")
    if (params.setting, params.idea, params.anchor, params.discovery) not in valid_combos():
        raise StoryError(
            explain_rejection(
                SETTINGS[params.setting],
                IDEAS[params.idea],
                ANCHORS[params.anchor],
                DISCOVERIES[params.discovery],
            )
        )

    world = tell(
        setting=SETTINGS[params.setting],
        idea=IDEAS[params.idea],
        anchor=ANCHORS[params.anchor],
        discovery=DISCOVERIES[params.discovery],
        party=CELEBRATIONS[params.celebration],
        planner_name=params.planner_name,
        planner_type=params.planner_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, idea, anchor, discovery) combos:\n")
        for setting, idea, anchor, discovery in combos:
            print(f"  {setting:10} {idea:14} {anchor:12} {discovery}")
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
                f"### {p.planner_name} & {p.helper_name}: {p.idea} at {p.setting} "
                f"({p.anchor}, {p.discovery})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
