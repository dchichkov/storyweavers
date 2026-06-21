#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py
=================================================================================

A standalone story world for a bedtime tale about a tiny night-watch guild:
children hear a strange sound in the dark, grow worried, investigate carefully,
and discover an ordinary cause. The simulation keeps the suspense grounded in
world state: a nighttime noise has a source, the children choose gear and a
helper action, fear rises or settles, and the ending image proves that the room
feels safe again.

Run it
------
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py --source window_branch
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py --investigator older_child
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/guild_suspense_sound_effects_dialogue_bedtime_story.py --verify
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
CALM_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    glowing: bool = False
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    room: str
    hush: str
    bed_image: str
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
class NoiseSource:
    id: str
    label: str
    sound: str
    place: str
    cause_line: str
    reveal_line: str
    fix_line: str
    spooky: int
    needs_gear: bool = False
    gear: str = ""
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
class ComfortTool:
    id: str
    label: str
    phrase: str
    action: str
    glow_line: str
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
class Investigator:
    id: str
    label: str
    entry_line: str
    comfort_line: str
    safety: int
    brave_phrase: str
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


def _r_fear_rises(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "noise":
            continue
        if ent.meters["active_noise"] < THRESHOLD:
            continue
        sig = ("fear_rises", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for child in [e for e in world.entities.values() if e.role in ("listener", "sleeper")]:
            child.memes["fear"] += 1
            child.memes["wonder"] += 1
        world.get("room").meters["tension"] += 1
        out.append("__noise__")
    return out


def _r_glow_steadies(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    if tool is None or tool.meters["on"] < THRESHOLD:
        return out
    for child in [e for e in world.entities.values() if e.role in ("listener", "sleeper")]:
        sig = ("glow_steadies", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["courage"] += 1
        if child.memes["fear"] >= THRESHOLD:
            child.memes["fear"] -= 1
        out.append("__steady__")
    return out


def _r_helper_calms(world: World) -> list[str]:
    helper = world.entities.get("helper")
    if helper is None or helper.meters["present"] < THRESHOLD:
        return []
    sig = ("helper_calms", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in [e for e in world.entities.values() if e.role in ("listener", "sleeper")]:
        child.memes["calm"] += 1
        if child.memes["fear"] >= THRESHOLD:
            child.memes["fear"] -= 1
    return ["__helper__"]


def _r_explained_noise(world: World) -> list[str]:
    noise = world.get("noise")
    if noise.meters["explained"] < THRESHOLD:
        return []
    sig = ("explained_noise", noise.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    noise.meters["active_noise"] = 0.0
    world.get("room").meters["tension"] = 0.0
    for child in [e for e in world.entities.values() if e.role in ("listener", "sleeper")]:
        child.memes["relief"] += 1
        child.memes["calm"] += 1
        child.memes["fear"] = 0.0
    return ["__explained__"]


CAUSAL_RULES = [
    Rule(name="fear_rises", tag="emotional", apply=_r_fear_rises),
    Rule(name="glow_steadies", tag="emotional", apply=_r_glow_steadies),
    Rule(name="helper_calms", tag="social", apply=_r_helper_calms),
    Rule(name="explained_noise", tag="resolution", apply=_r_explained_noise),
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


def valid_combo(source: NoiseSource, investigator: Investigator) -> bool:
    if source.needs_gear and investigator.id == "solo_child":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, source in SOURCES.items():
        for iid, investigator in INVESTIGATORS.items():
            if valid_combo(source, investigator):
                combos.append((sid, iid))
    return combos


def predict_need(source: NoiseSource, investigator: Investigator) -> dict:
    return {
        "scary": source.spooky >= 2,
        "needs_helper": source.needs_gear or investigator.safety < source.spooky,
    }


def introduce(world: World, child1: Entity, child2: Entity, setting: Setting) -> None:
    child1.memes["belonging"] += 1
    child2.memes["belonging"] += 1
    world.say(
        f"In {setting.room}, when the lamps were low and {setting.hush}, "
        f"{child1.id} and {child2.id} whispered about their little guild."
    )
    world.say(
        f'"The Moonlight Guild is on watch tonight," {child1.id} murmured. '
        f'"We listen first, and we are gentle."'
    )
    world.say(
        f'{child2.id} pulled the blanket up to {child2.pronoun("possessive")} chin and smiled. '
        f'"Guild promise," {child2.pronoun()} whispered back.'
    )


def strange_sound(world: World, source: NoiseSource) -> None:
    noise = world.get("noise")
    noise.meters["active_noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then from {source.place} came a soft {source.sound}. "
        f'"Did you hear that?" {world.get("listener").id} whispered.'
    )
    world.say("The room seemed to hold its breath for one tiny moment.")


def wonder_and_worry(world: World, listener: Entity, sleeper: Entity, source: NoiseSource) -> None:
    prediction = predict_need(source, INVESTIGATORS[world.facts["investigator_cfg"].id])
    world.facts["predicted_scary"] = prediction["scary"]
    world.facts["predicted_needs_helper"] = prediction["needs_helper"]
    extra = " It sounded bigger in the dark than it really was." if prediction["scary"] else ""
    world.say(
        f'{sleeper.id} squeezed the blanket. "What if it is something spooky?" '
        f'{sleeper.pronoun().capitalize()} asked.{extra}'
    )
    world.say(
        f'"Maybe it is only a night sound," {listener.id} said, though '
        f'{listener.pronoun()} listened very hard.'
    )


def ready_tool(world: World, tool_cfg: ComfortTool, child: Entity) -> None:
    tool = world.get("tool")
    tool.meters["on"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} reached for {tool_cfg.phrase}. {tool_cfg.glow_line} '
        f'"{tool_cfg.action}," {child.pronoun()} whispered.'
    )


def call_helper(world: World, helper: Entity, by_child: Entity, investigator_cfg: Investigator) -> None:
    helper.meters["present"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{investigator_cfg.entry_line} "{helper.id}, will you come with us?" '
        f'{by_child.id} asked.'
    )
    world.say(investigator_cfg.comfort_line)


def investigate(world: World, source: NoiseSource, investigator_cfg: Investigator, leader: Entity) -> None:
    world.say(
        f'Together they tiptoed closer. {leader.id} listened, and the sound came again: '
        f'{source.sound}'
    )
    world.say(
        f'"{investigator_cfg.brave_phrase}," {leader.id} said, trying to make '
        f'{leader.pronoun("possessive")} voice sound small and steady.'
    )


def reveal(world: World, source: NoiseSource) -> None:
    noise = world.get("noise")
    noise.meters["explained"] += 1
    noise.meters["found_source"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal_line)
    world.say(source.cause_line)


def fix_noise(world: World, source: NoiseSource, helper: Optional[Entity]) -> None:
    who = helper.id if helper is not None else world.get("listener").id
    world.say(source.fix_line.replace("{who}", who))


def settle(world: World, child1: Entity, child2: Entity, setting: Setting, tool_cfg: ComfortTool) -> None:
    child1.memes["sleepy"] += 1
    child2.memes["sleepy"] += 1
    world.say(
        f'Back in bed, {child2.id} let out a long soft sigh. "So that was all," '
        f'{child2.pronoun()} said.'
    )
    world.say(
        f'"Yes," said {child1.id}. "The guild solved a night mystery with quiet feet and kind eyes."'
    )
    world.say(
        f"Soon {setting.bed_image}, and {tool_cfg.label} made only a small warm glow beside them."
    )


def tell(
    setting: Setting,
    source: NoiseSource,
    tool_cfg: ComfortTool,
    investigator_cfg: Investigator,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    sleeper_name: str = "Ben",
    sleeper_gender: str = "boy",
    helper_type: str = "mother",
) -> World:
    world = World(setting)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="listener"))
    sleeper = world.add(Entity(id=sleeper_name, kind="character", type=sleeper_gender, role="sleeper"))
    helper = world.add(Entity(id=("Mom" if helper_type == "mother" else "Dad"),
                              kind="character", type=helper_type, role="helper", helpful=True))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.room))
    room.meters["tension"] = 0.0
    noise = world.add(Entity(id="noise", kind="thing", type="noise", label=source.label, role="noise", movable=False))
    noise.meters["active_noise"] = 0.0
    noise.meters["explained"] = 0.0
    noise.meters["found_source"] = 0.0
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg.label, role="tool", glowing=True))
    tool.meters["on"] = 0.0
    helper.meters["present"] = 0.0
    leader.memes["fear"] = 0.0
    sleeper.memes["fear"] = 0.0
    leader.memes["calm"] = 0.0
    sleeper.memes["calm"] = 0.0
    world.facts["investigator_cfg"] = investigator_cfg

    introduce(world, leader, sleeper, setting)

    world.para()
    strange_sound(world, source)
    wonder_and_worry(world, leader, sleeper, source)
    ready_tool(world, tool_cfg, leader)

    needs_helper = source.needs_gear or investigator_cfg.id != "solo_child"
    if needs_helper:
        world.para()
        call_helper(world, helper, leader, investigator_cfg)
        helper_used: Optional[Entity] = helper
    else:
        helper_used = None

    world.para()
    investigate(world, source, investigator_cfg, leader)
    reveal(world, source)
    fix_noise(world, source, helper_used)
    world.para()
    settle(world, leader, sleeper, setting, tool_cfg)

    world.facts.update(
        setting=setting,
        source_cfg=source,
        tool_cfg=tool_cfg,
        investigator_cfg=investigator_cfg,
        leader=leader,
        sleeper=sleeper,
        helper=helper,
        helper_used=helper_used is not None,
        source_found=noise.meters["found_source"] >= THRESHOLD,
        calm_end=(leader.memes["calm"] + sleeper.memes["calm"]) >= CALM_MIN,
        guild_name="Moonlight Guild",
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        room="the little attic bedroom",
        hush="the curtains hung still as sleepy sails",
        bed_image="the blankets made two soft hills in the moonlight",
        tags={"bedroom", "night"},
    ),
    "nursery": Setting(
        id="nursery",
        room="the nursery at the end of the hall",
        hush="the rocking chair waited quietly by the window",
        bed_image="the quilts lay smooth as resting clouds",
        tags={"bedroom", "night"},
    ),
    "bunkroom": Setting(
        id="bunkroom",
        room="the bunkroom under the slanted roof",
        hush="the striped rug looked silver in the moonlight",
        bed_image="the pillows sank into the beds like sleepy marshmallows",
        tags={"bedroom", "night"},
    ),
}

SOURCES = {
    "window_branch": NoiseSource(
        id="window_branch",
        label="branch at the window",
        sound='tap... tap-tap',
        place="the window",
        cause_line="A windy branch had been brushing the glass with its tiny twigs.",
        reveal_line='There, outside the pane, a thin branch bobbed and tapped the window. "Oh!"',
        fix_line='{who} gently tied the loose branch back with garden string, and the tapping stopped.',
        spooky=2,
        needs_gear=True,
        gear="adult",
        tags={"wind", "window", "branch"},
    ),
    "toy_wagon": NoiseSource(
        id="toy_wagon",
        label="rolling toy wagon",
        sound='rrr... clack',
        place="under the bed",
        cause_line="The little wagon had been rolling each time the floorboards settled.",
        reveal_line='Under the bed sat the red toy wagon, nudging a block with a quiet clack. "Just the wagon,"',
        fix_line='{who} slid the wagon against the wall so it could not roll anymore.',
        spooky=1,
        needs_gear=False,
        tags={"toy", "wagon", "bedroom"},
    ),
    "heater_pipe": NoiseSource(
        id="heater_pipe",
        label="warm heater pipe",
        sound='ting... ting',
        place="by the radiator",
        cause_line="The warm pipe was cooling down and making little metal pings.",
        reveal_line='By the radiator, the pipe gave one last tiny ting. "That is all?"',
        fix_line='{who} laid a folded slipper by the pipe so the small rattle would not answer back.',
        spooky=1,
        needs_gear=False,
        tags={"heater", "metal", "night"},
    ),
    "moth_lampshade": NoiseSource(
        id="moth_lampshade",
        label="moth at the shade",
        sound='fuff-fuff',
        place="the lamp",
        cause_line="A pale moth had fluttered against the lampshade, soft as paper.",
        reveal_line='Around the shaded lamp, a tiny moth fluttered once more. "Only a moth,"',
        fix_line='{who} opened the window a crack, and the moth drifted back into the night.',
        spooky=2,
        needs_gear=False,
        tags={"moth", "lamp", "night"},
    ),
}

TOOLS = {
    "flashlight": ComfortTool(
        id="flashlight",
        label="flashlight",
        phrase="the small flashlight from the bedside table",
        action="Guild light on",
        glow_line="A round patch of gold slid over the blanket.",
        tags={"flashlight", "light"},
    ),
    "lantern": ComfortTool(
        id="lantern",
        label="night lantern",
        phrase="the little night lantern shaped like a moon",
        action="Moonlight Guild, shine softly",
        glow_line="A mild honey-colored glow woke inside it.",
        tags={"lantern", "light"},
    ),
    "star_lamp": ComfortTool(
        id="star_lamp",
        label="star lamp",
        phrase="the star lamp by the pillow",
        action="Stars, help us peek kindly",
        glow_line="Tiny stars sprinkled light across the rug.",
        tags={"lamp", "light"},
    ),
}

INVESTIGATORS = {
    "adult": Investigator(
        id="adult",
        label="adult helper",
        entry_line="Soft steps came along the hall.",
        comfort_line='"Of course," the grown-up said. "We will look together, slowly."',
        safety=3,
        brave_phrase="Guild members stay close",
        tags={"adult", "help"},
    ),
    "older_child": Investigator(
        id="older_child",
        label="older child leads",
        entry_line="No one else needed to come; the older child sat up straighter instead.",
        comfort_line='"I can lead, and we stay by the door," the older child said.',
        safety=2,
        brave_phrase="We look, but we do not rush",
        tags={"child", "help"},
    ),
    "solo_child": Investigator(
        id="solo_child",
        label="solo child peeks",
        entry_line="No one else woke, and the room stayed very still.",
        comfort_line='"I will only peek from the blanket edge," the child whispered.',
        safety=1,
        brave_phrase="One tiny peek is enough",
        tags={"child", "solo"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    source: str
    tool: str
    investigator: str
    leader_name: str
    leader_gender: str
    sleeper_name: str
    sleeper_gender: str
    helper_type: str
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
    "flashlight": [
        ("What is a flashlight?", "A flashlight is a small light you can carry in your hand. It helps you see in the dark without any flame.")
    ],
    "lantern": [
        ("What is a night lantern?", "A night lantern is a gentle lamp made to glow softly in a room. It can help bedtime feel calmer.")
    ],
    "light": [
        ("Why does a small light help at night?", "A small light helps your eyes see shapes more clearly. When things are easier to see, they often feel less scary.")
    ],
    "wind": [
        ("Why can a branch tap on a window at night?", "Wind can push a loose branch back and forth. When it touches the glass, it makes a tapping sound.")
    ],
    "heater": [
        ("Why do heater pipes make little noises?", "Warm metal changes a little as it heats and cools. That can make small pinging sounds.")
    ],
    "moth": [
        ("What is a moth?", "A moth is a small fluttering insect a bit like a butterfly. Some moths move toward light at night.")
    ],
    "toy": [
        ("Why might a toy make noise by itself at night?", "A toy can roll or bump if the floor shifts a little or if it was left crooked. Quiet rooms make tiny sounds easier to notice.")
    ],
    "adult": [
        ("Why is it smart to ask a grown-up for help at night?", "A grown-up can help you check things safely and calmly. Being brave can mean asking for help.")
    ],
}
KNOWLEDGE_ORDER = ["flashlight", "lantern", "light", "wind", "heater", "moth", "toy", "adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    return [
        f'Write a bedtime story about a little guild that hears {source.sound} in the night and uses {tool.label} to solve the mystery.',
        f'Write a gentle suspense story for ages 3 to 5 where two children whisper dialogue in bed, hear a strange sound from {source.place}, and discover an ordinary cause.',
        'Tell a cozy bedtime story with suspense, soft sound effects, and dialogue, where the word "guild" appears naturally and the ending feels safe.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    sleeper = f["sleeper"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    helper = f["helper"]
    guild_name = f["guild_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {sleeper.id}, two children in {guild_name}. They hear a strange sound at bedtime and try to understand it."
        ),
        (
            "What made the children feel worried?",
            f"They heard {source.sound} coming from {source.place}, and in the dark the sound felt mysterious. Quiet rooms can make small noises seem bigger than they are."
        ),
        (
            "What did they use before they looked closer?",
            f"They used the {tool.label} first. The soft light helped them see more clearly, which made the mystery feel less frightening."
        ),
    ]
    if f["helper_used"]:
        qa.append(
            (
                "Why did they ask for help?",
                f"They asked {helper.id} to come because it felt safer to investigate together. The sound came from {source.place}, and going slowly with help kept the moment calm."
            )
        )
    else:
        qa.append(
            (
                "How did they stay careful while looking?",
                f"They stayed careful by moving slowly and keeping the light near them. That way they could check the sound without turning the bedtime mystery into a rush."
            )
        )
    qa.extend([
        (
            "What was the strange sound really?",
            f"It was {source.label}. {source.cause_line}"
        ),
        (
            "How did the story end?",
            f"The mystery was solved, and the room felt peaceful again. Back in bed, the children could rest because they understood the sound at last."
        ),
    ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool_cfg"].tags) | set(world.facts["source_cfg"].tags)
    if world.facts["helper_used"]:
        tags |= {"adult"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("movable", e.movable), ("glowing", e.glowing), ("helpful", e.helpful)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="bedroom",
        source="window_branch",
        tool="lantern",
        investigator="adult",
        leader_name="Nora",
        leader_gender="girl",
        sleeper_name="Ben",
        sleeper_gender="boy",
        helper_type="mother",
    ),
    StoryParams(
        setting="nursery",
        source="toy_wagon",
        tool="flashlight",
        investigator="older_child",
        leader_name="Mia",
        leader_gender="girl",
        sleeper_name="Leo",
        sleeper_gender="boy",
        helper_type="father",
    ),
    StoryParams(
        setting="bunkroom",
        source="heater_pipe",
        tool="star_lamp",
        investigator="solo_child",
        leader_name="Finn",
        leader_gender="boy",
        sleeper_name="Rose",
        sleeper_gender="girl",
        helper_type="mother",
    ),
    StoryParams(
        setting="bedroom",
        source="moth_lampshade",
        tool="flashlight",
        investigator="older_child",
        leader_name="Ella",
        leader_gender="girl",
        sleeper_name="Sam",
        sleeper_gender="boy",
        helper_type="father",
    ),
]


def explain_rejection(source: NoiseSource, investigator: Investigator) -> str:
    if source.needs_gear and investigator.id == "solo_child":
        return (
            f"(No story: {source.label} needs help beyond a child's blanket-edge peek. "
            f"A solo child should not handle that source alone; choose --investigator adult or older_child.)"
        )
    return "(No story: that source and investigator do not make a safe bedtime mystery.)"


ASP_RULES = r"""
valid(S, I) :- source(S), investigator(I), not invalid(S, I).
invalid(S, solo_child) :- needs_gear(S).
needs_helper(S, I) :- needs_gear(S).
needs_helper(S, I) :- spooky(S, Sp), safety(I, Sf), Sf < Sp.
no_helper(S, I) :- not needs_helper(S, I).

#show valid/2.
#show needs_helper/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("spooky", sid, source.spooky))
        if source.needs_gear:
            lines.append(asp.fact("needs_gear", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for iid, inv in INVESTIGATORS.items():
        lines.append(asp.fact("investigator", iid))
        lines.append(asp.fact("safety", iid, inv.safety))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_needs_helper(source_id: str, investigator_id: str) -> bool:
    import asp
    extra = f"""
chosen_source({source_id}).
chosen_investigator({investigator_id}).
need :- needs_helper(chosen_source, chosen_investigator).
#show need/0.
"""
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "need"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for sid, iid in sorted(py_valid):
        py_need = predict_need(SOURCES[sid], INVESTIGATORS[iid])["needs_helper"]
        asp_need = asp_needs_helper(sid, iid)
        if py_need != asp_need:
            rc = 1
            print(f"MISMATCH in needs_helper for {(sid, iid)}: python={py_need} clingo={asp_need}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "guild" not in sample.story.lower():
            raise StoryError("(Verify failed: smoke test story missing or does not mention guild.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


GIRL_NAMES = ["Nora", "Mia", "Ella", "Lucy", "Ava", "Maya", "Rose", "Lila"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Sam", "Theo", "Jack", "Eli", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a bedtime guild hears a suspicious night sound and solves it gently."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--investigator", choices=INVESTIGATORS)
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid source/investigator combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.investigator:
        source = SOURCES[args.source]
        investigator = INVESTIGATORS[args.investigator]
        if not valid_combo(source, investigator):
            raise StoryError(explain_rejection(source, investigator))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.investigator is None or combo[1] == args.investigator)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, investigator_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    leader_name, leader_gender = _pick_child(rng)
    sleeper_name, sleeper_gender = _pick_child(rng, avoid=leader_name)
    return StoryParams(
        setting=setting_id,
        source=source_id,
        tool=tool_id,
        investigator=investigator_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        sleeper_name=sleeper_name,
        sleeper_gender=sleeper_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        source = SOURCES[params.source]
        tool = TOOLS[params.tool]
        investigator = INVESTIGATORS[params.investigator]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None
    if not valid_combo(source, investigator):
        raise StoryError(explain_rejection(source, investigator))

    world = tell(
        setting=setting,
        source=source,
        tool_cfg=tool,
        investigator_cfg=investigator,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        sleeper_name=params.sleeper_name,
        sleeper_gender=params.sleeper_gender,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} valid (source, investigator) combos:\n")
        for source_id, investigator_id in combos:
            print(f"  {source_id:16} {investigator_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.leader_name} & {p.sleeper_name}: {p.source} ({p.investigator}, {p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
