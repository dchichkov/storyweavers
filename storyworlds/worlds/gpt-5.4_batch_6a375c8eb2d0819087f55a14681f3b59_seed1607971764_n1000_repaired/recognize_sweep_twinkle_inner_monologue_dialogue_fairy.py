#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py
====================================================================================

A standalone storyworld in a fairy-tale mode: a young fairy is meant to sweep a
hidden moon-path before evening, so its stones can twinkle and a loved visitor
can recognize the way home. The state of the path, the cover lying on it, the
gentleness of the sweeping tool, and the lateness of the hour together decide
how the story turns.

The generated stories always include:
- the words "recognize", "sweep", and "twinkle"
- inner monologue
- dialogue
- a complete beginning, middle turn, and ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py --all
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py --trace --seed 12
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py --asp
    python storyworlds/worlds/gpt-5.4/recognize_sweep_twinkle_inner_monologue_dialogue_fairy.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "mother", "queen", "grandmother", "aunt"}
        male = {"boy", "fairy_boy", "father", "king", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
class Place:
    id: str
    label: str
    opening: str
    dusk_line: str
    ending: str
    affords_covers: set[str] = field(default_factory=set)
    affords_guides: set[str] = field(default_factory=set)
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
class Cover:
    id: str
    label: str
    phrase: str
    difficulty: int
    drape: str
    sweep_verb: str
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
class Guide:
    id: str
    label: str
    the: str
    plural_label: str
    location: str
    glow_text: str
    need_gentle: int
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    gentle: int
    sound: str
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
class Visitor:
    id: str
    label: str
    relation: str
    opening: str
    thanks: str
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
class Helper:
    id: str
    label: str
    phrase: str
    call: str
    action: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_hidden_glow(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    cover = world.get("cover")
    hero = world.get("hero")
    visitor = world.get("visitor")
    if cover.meters["on_path"] >= THRESHOLD and guide.meters["twinkling"] < THRESHOLD:
        sig = ("hidden_glow",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            visitor.memes["confused"] += 1
            out.append("__dim__")
    return out


def _r_twinkle(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    cover = world.get("cover")
    tool = world.get("tool")
    if cover.meters["on_path"] <= 0 and tool.attrs.get("compatible"):
        sig = ("twinkle",)
        if sig not in world.fired:
            world.fired.add(sig)
            guide.meters["twinkling"] += 1
            out.append("__twinkle__")
    return out


def _r_recognize(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    visitor = world.get("visitor")
    if guide.meters["twinkling"] >= THRESHOLD and visitor.meters["near_path"] >= THRESHOLD:
        sig = ("recognize",)
        if sig not in world.fired:
            world.fired.add(sig)
            visitor.meters["recognized_way"] += 1
            visitor.memes["relief"] += 1
            out.append("__recognize__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_glow", tag="emotional", apply=_r_hidden_glow),
    Rule(name="twinkle", tag="physical", apply=_r_twinkle),
    Rule(name="recognize", tag="social", apply=_r_recognize),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def compatible_tool(tool: Tool, cover: Cover, guide: Guide) -> bool:
    return tool.sense >= SENSE_MIN and tool.power >= cover.difficulty and tool.gentle >= guide.need_gentle


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cover_id in sorted(place.affords_covers):
            for guide_id in sorted(place.affords_guides):
                guide = GUIDES[guide_id]
                cover = COVERS[cover_id]
                if any(compatible_tool(tool, cover, guide) for tool in TOOLS.values()):
                    combos.append((place_id, cover_id, guide_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    cover = COVERS[params.cover]
    guide = GUIDES[params.guide]
    if not compatible_tool(tool, cover, guide):
        return "invalid"
    return "recognized" if params.delay <= 1 else "guided"


def explain_tool(tool: Tool, cover: Cover, guide: Guide) -> str:
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(Refusing tool '{tool.id}': it is too rough or foolish for this fairy-tale world "
            f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if tool.power < cover.difficulty:
        return (
            f"(No story: {tool.label} is too weak to sweep away {cover.phrase}. "
            f"Choose a stronger gentle tool.)"
        )
    if tool.gentle < guide.need_gentle:
        return (
            f"(No story: {tool.label} would scrape {guide.plural_label} instead of helping them twinkle. "
            f"Choose a gentler sweeping tool.)"
        )
    return "(No story: that tool does not fit this path.)"


def explain_combo(place: Place, cover: Cover, guide: Guide) -> str:
    if cover.id not in place.affords_covers:
        return f"(No story: {cover.phrase} does not belong naturally at {place.label}.)"
    if guide.id not in place.affords_guides:
        return f"(No story: {guide.plural_label} are not the kind of hidden path found at {place.label}.)"
    if not any(compatible_tool(tool, cover, guide) for tool in TOOLS.values()):
        return "(No story: nothing in the tool catalog can clear this path gently enough.)"
    return "(No story: that combination is not part of this little world.)"


def predict_recognition(world: World) -> dict:
    sim = world.copy()
    guide = sim.get("guide")
    cover = sim.get("cover")
    tool = sim.get("tool")
    visitor = sim.get("visitor")
    tool.attrs["compatible"] = compatible_tool(
        TOOLS[sim.facts["tool_cfg"].id],
        sim.facts["cover_cfg"],
        sim.facts["guide_cfg"],
    )
    cover.meters["on_path"] = 0.0 if tool.attrs["compatible"] else 1.0
    visitor.meters["near_path"] = 1.0
    propagate(sim, narrate=False)
    return {
        "twinkling": guide.meters["twinkling"] >= THRESHOLD,
        "recognized": visitor.meters["recognized_way"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, place: Place, visitor: Visitor, guide: Guide) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In {place.label}, where evening liked to sit softly on every leaf, lived {hero.id}, a little fairy with a quick broom and an even quicker heart. {place.opening}"
    )
    world.say(
        f"Each dusk, {elder.label_word.capitalize()} reminded {hero.pronoun('object')} to sweep {guide.location}, because {visitor.opening} and needed {guide.plural_label} to twinkle so they could recognize the way."
    )
    world.say(
        f'"Remember," {elder.label_word} said, "a small kindness can shine a long way in the dark."'
    )


def distract(world: World, hero: Entity, cover: Cover) -> None:
    hero.memes["delight"] += 1
    world.say(
        f"But that afternoon the wind went dancing past, and soon {cover.phrase} came {cover.drape}. {hero.id} chased a drifting song and forgot the waiting path."
    )


def dusk_falls(world: World, hero: Entity, place: Place, guide: Guide, cover: Cover) -> None:
    guide.meters["twinkling"] = 0.0
    world.get("cover").meters["on_path"] = 1.0
    propagate(world, narrate=False)
    world.say(place.dusk_line)
    world.say(
        f"The hidden path lay under {cover.phrase}, and {guide.the} could not twinkle through it."
    )
    world.say(
        f'{hero.id} looked down and thought, "Oh dear. If I do not sweep it now, how will anyone recognize our door?"'
    )


def spot_clue(world: World, hero: Entity, guide: Guide, cover: Cover) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"Then, under the edge of {cover.phrase}, {hero.id} saw the tiniest blink. It was only one shy silver wink, but {hero.pronoun()} knew at once what it meant."
    )
    world.say(
        f'{hero.id} whispered to {hero.pronoun("object")}self, "I recognize you, little {guide.label}. Wait for me."'
    )


def visitor_arrives(world: World, visitor_ent: Entity, visitor_cfg: Visitor) -> None:
    visitor_ent.meters["near_path"] = 1.0
    visitor_ent.memes["hope"] += 1
    world.say(
        f"From beyond the hedge came a small voice. \"Is anyone there?\" called {visitor_cfg.label}. \"I thought I knew the way, but tonight every turning looks the same.\""
    )


def choose_tool(world: World, hero: Entity, tool: Tool, cover: Cover, guide: Guide) -> None:
    ent = world.get("tool")
    ent.attrs["compatible"] = compatible_tool(tool, cover, guide)
    hero.memes["care"] += 1
    pred = predict_recognition(world)
    world.facts["predicted_twinkle"] = pred["twinkling"]
    world.facts["predicted_recognize"] = pred["recognized"]
    world.say(
        f'{hero.id} grabbed {tool.phrase} and thought, "Gently now. I must sweep the path clean without hurting the little lights underneath."'
    )


def sweep_path(world: World, hero: Entity, tool: Tool, cover: Cover, guide: Guide) -> None:
    tool_ent = world.get("tool")
    cover_ent = world.get("cover")
    if not tool_ent.attrs.get("compatible"):
        raise StoryError(explain_tool(tool, cover, guide))
    cover_ent.meters["on_path"] = 0.0
    hero.meters["swept"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{tool.sound} went {tool.label} as {hero.id} began to sweep. {cover.phrase.capitalize()} slid aside in a shining little wave."
    )
    world.say(
        f"At once {guide.the} woke beneath the path and began to twinkle, one by one, until the whole line looked like a necklace of patient stars."
    )


def recognize_return(world: World, hero: Entity, visitor_cfg: Visitor, guide: Guide) -> None:
    visitor_ent = world.get("visitor")
    if visitor_ent.meters["recognized_way"] < THRESHOLD:
        raise StoryError("(Story state broke: the visitor did not recognize the path when they should have.)")
    world.say(
        f'"There!" cried {visitor_cfg.label}. "Now I can recognize it!" {visitor_cfg.label.capitalize()} followed {guide.plural_label}, step by bright step, until {visitor_ent.pronoun()} reached the gate.'
    )
    world.say(visitor_cfg.thanks)


def helper_guides(world: World, hero: Entity, helper_cfg: Helper, visitor_cfg: Visitor, guide: Guide) -> None:
    helper_ent = world.get("helper")
    helper_ent.memes["helpfulness"] += 1
    world.say(
        f"But the night had grown thick already. {visitor_cfg.label.capitalize()} was too far down the lane to see the first bright stones."
    )
    world.say(
        f"Then {helper_cfg.phrase} swept low from the dark and gave {helper_cfg.call}. {helper_cfg.action}, circling back each time the path bent."
    )
    world.say(
        f'"Follow the twinkle," {hero.id} called. "{helper_cfg.label_word.capitalize()} will meet you halfway." Soon {visitor_cfg.label} saw the glimmer, recognized the path at last, and came hurrying in.'
    )
    world.get("visitor").meters["recognized_way"] = 1.0
    world.get("visitor").memes["relief"] += 1


def ending(world: World, hero: Entity, elder: Entity, place: Place, guide: Guide, outcome: str) -> None:
    hero.memes["lesson"] += 1
    hero.memes["peace"] += 1
    if outcome == "recognized":
        world.say(
            f'{elder.label_word.capitalize()} smiled and said, "You remembered in time." {hero.id} answered, "Next dusk I will sweep before the shadows grow tall."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} touched {hero.pronoun("possessive")} shoulder and said, "Even late kindness matters." {hero.id} answered, "Tomorrow I will sweep early, before anyone has to search."'
        )
    world.say(
        f"After that, whenever evening came to {place.label}, {hero.id} watched {guide.plural_label} twinkle first and play afterward. {place.ending}"
    )


def tell(
    place: Place,
    cover: Cover,
    guide: Guide,
    tool: Tool,
    visitor_cfg: Visitor,
    helper_cfg: Helper,
    hero_name: str = "Lina",
    hero_type: str = "fairy_girl",
    elder_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World(place)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="grandmother", role="elder"))
    visitor_ent = world.add(Entity(id="visitor", kind="character", type="thing", label=visitor_cfg.label, role="visitor"))
    helper_ent = world.add(Entity(id="helper", kind="character", type="thing", label=helper_cfg.label, role="helper"))
    guide_ent = world.add(Entity(id="guide", kind="thing", type="guide", label=guide.label))
    cover_ent = world.add(Entity(id="cover", kind="thing", type="cover", label=cover.label))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))
    tool_ent.attrs["compatible"] = False

    cover_ent.meters["on_path"] = 0.0
    guide_ent.meters["twinkling"] = 0.0
    visitor_ent.meters["near_path"] = 0.0
    visitor_ent.meters["recognized_way"] = 0.0
    hero.meters["swept"] = 0.0
    helper_ent.memes["helpfulness"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["lesson"] = 0.0
    visitor_ent.memes["confused"] = 0.0
    visitor_ent.memes["relief"] = 0.0

    world.facts.update(
        place_cfg=place,
        cover_cfg=cover,
        guide_cfg=guide,
        tool_cfg=tool,
        visitor_cfg=visitor_cfg,
        helper_cfg=helper_cfg,
        delay=delay,
    )

    introduce(world, hero, elder, place, visitor_cfg, guide)
    world.para()
    distract(world, hero, cover)
    dusk_falls(world, hero, place, guide, cover)
    visitor_arrives(world, visitor_ent, visitor_cfg)
    world.para()
    spot_clue(world, hero, guide, cover)
    choose_tool(world, hero, tool, cover, guide)
    sweep_path(world, hero, tool, cover, guide)

    if delay <= 1:
        recognize_return(world, hero, visitor_cfg, guide)
        outcome = "recognized"
    else:
        helper_guides(world, hero, helper_cfg, visitor_cfg, guide)
        outcome = "guided"

    world.para()
    ending(world, hero, elder, place, guide, outcome)
    world.facts.update(
        hero=hero,
        elder=elder,
        visitor=visitor_ent,
        helper=helper_ent,
        guide=guide_ent,
        cover=cover_ent,
        tool=tool_ent,
        outcome=outcome,
    )
    return world


PLACES = {
    "mushroom_hollow": Place(
        id="mushroom_hollow",
        label="the Mushroom Hollow",
        opening="Her house was a red-capped mushroom with windows round as buttercups.",
        dusk_line="By the time the first violet shadows folded over the roots, the hollow was quiet enough to hear gnats hum.",
        ending="The mushroom windows glowed warm, and no one missed the door again.",
        affords_covers={"leaves", "snow"},
        affords_guides={"starstones", "shell_steps"},
        tags={"fairy_home"},
    ),
    "willow_bridge": Place(
        id="willow_bridge",
        label="the Willow Bridge",
        opening="She slept in a willow-knotted nook beside a bridge where the stream told silver secrets all night.",
        dusk_line="Evening pooled under the willow branches until the bridge looked like part of a dream.",
        ending="The bridge shone softly over the water, and the stream carried the last twinkle far downstream.",
        affords_covers={"mist", "petals"},
        affords_guides={"bellstones", "starstones"},
        tags={"bridge"},
    ),
    "moon_garden": Place(
        id="moon_garden",
        label="the Moon Garden",
        opening="Her little gate stood inside a garden of pale flowers that opened only after sunset.",
        dusk_line="Soon the garden filled with blue dusk, and every blossom held its breath for the moon.",
        ending="The flower beds nodded in the moonlight, and the path looked awake all the way to the gate.",
        affords_covers={"dew", "petals", "leaves"},
        affords_guides={"shell_steps", "bellstones"},
        tags={"garden"},
    ),
}

COVERS = {
    "dew": Cover(
        id="dew",
        label="dew",
        phrase="pearled dew",
        difficulty=1,
        drape="over the path like a cool glass veil",
        sweep_verb="sweep away",
        tags={"dew"},
    ),
    "petals": Cover(
        id="petals",
        label="petals",
        phrase="fallen petals",
        difficulty=1,
        drape="in a pink-and-white drift",
        sweep_verb="sweep aside",
        tags={"flowers"},
    ),
    "leaves": Cover(
        id="leaves",
        label="leaves",
        phrase="curled gold leaves",
        difficulty=2,
        drape="in a rustling heap",
        sweep_verb="sweep aside",
        tags={"leaves"},
    ),
    "mist": Cover(
        id="mist",
        label="mist",
        phrase="low silver mist",
        difficulty=1,
        drape="like a sleepy scarf",
        sweep_verb="sweep through",
        tags={"mist"},
    ),
    "snow": Cover(
        id="snow",
        label="snow",
        phrase="powdery snow",
        difficulty=2,
        drape="in a soft white hush",
        sweep_verb="sweep clear",
        tags={"snow"},
    ),
}

GUIDES = {
    "starstones": Guide(
        id="starstones",
        label="starstone",
        the="the starstones",
        plural_label="the starstones",
        location="the little starstones along the path",
        glow_text="each one held a tucked-away spark",
        need_gentle=2,
        tags={"twinkle", "stones"},
    ),
    "bellstones": Guide(
        id="bellstones",
        label="bellstone",
        the="the bellstones",
        plural_label="the bellstones",
        location="the bellstones by the stepping path",
        glow_text="they shone with a hush like tiny bells",
        need_gentle=2,
        tags={"twinkle", "bells"},
    ),
    "shell_steps": Guide(
        id="shell_steps",
        label="shell step",
        the="the shell steps",
        plural_label="the shell steps",
        location="the little shell steps by the gate",
        glow_text="their pale curls caught moonlight easily",
        need_gentle=3,
        tags={"twinkle", "shells"},
    ),
}

TOOLS = {
    "birch_broom": Tool(
        id="birch_broom",
        label="birch broom",
        phrase="her birch broom",
        sense=3,
        power=2,
        gentle=2,
        sound="Swish, swish",
        qa_text="used her birch broom to sweep the path clean",
        tags={"broom", "sweep"},
    ),
    "feather_brush": Tool(
        id="feather_brush",
        label="feather brush",
        phrase="a feather brush",
        sense=3,
        power=1,
        gentle=3,
        sound="Hush-hush",
        qa_text="used a feather brush to sweep very gently",
        tags={"brush", "sweep"},
    ),
    "reed_broom": Tool(
        id="reed_broom",
        label="reed broom",
        phrase="a slim reed broom",
        sense=2,
        power=2,
        gentle=2,
        sound="Sirr, sirr",
        qa_text="used a reed broom to sweep the path bright again",
        tags={"broom", "sweep"},
    ),
    "twig_rake": Tool(
        id="twig_rake",
        label="twig rake",
        phrase="a twig rake",
        sense=1,
        power=3,
        gentle=1,
        sound="Scrape-scrape",
        qa_text="dragged a rough rake over the path",
        tags={"rake"},
    ),
}

VISITORS = {
    "aunt_moth": Visitor(
        id="aunt_moth",
        label="Aunt Moth",
        relation="aunt",
        opening="Aunt Moth often visited after sunset from the thistle lane",
        thanks='"Bless your bright hands," Aunt Moth said. "I nearly fluttered past the turning."',
        tags={"moth"},
    ),
    "hedgehog_tailor": Visitor(
        id="hedgehog_tailor",
        label="the Hedgehog Tailor",
        relation="friend",
        opening="the Hedgehog Tailor always came at dusk with ribbon and gossip in a neat satchel",
        thanks='"There now," said the Hedgehog Tailor. "A path that twinkles is a path a traveler can trust."',
        tags={"hedgehog"},
    ),
    "cricket_cousin": Visitor(
        id="cricket_cousin",
        label="Cousin Cricket",
        relation="cousin",
        opening="Cousin Cricket liked to come by night with songs tucked under one wing",
        thanks='"I heard home before I saw it," Cousin Cricket chirped, "and then I saw it too."',
        tags={"cricket"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="owl",
        phrase="an old moon-owl",
        call="one round golden hoot",
        action="It flew toward the lane, then back toward the gate",
        qa_text="an owl helped guide the visitor from farther down the lane",
        tags={"owl"},
    ),
    "firefly": Helper(
        id="firefly",
        label="firefly",
        phrase="a brave firefly",
        call="a small green blink",
        action="It bobbed ahead like a moving lantern",
        qa_text="a firefly carried a tiny moving light to the visitor",
        tags={"firefly"},
    ),
}


GIRL_NAMES = ["Lina", "Mira", "Tansy", "Wren", "Nella", "Suri", "Pippa", "Ivy"]
BOY_NAMES = ["Rowan", "Pip", "Alder", "Finn", "Moss", "Bram"]
HERO_TYPES = ["fairy_girl", "fairy_boy"]


@dataclass
class StoryParams:
    place: str
    cover: str
    guide: str
    tool: str
    visitor: str
    helper: str
    hero_name: str
    hero_type: str
    elder_type: str
    delay: int = 0
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
    "broom": [
        (
            "What does it mean to sweep?",
            "To sweep means to move dust, leaves, or other little things aside with a broom or brush. It clears a space so you can see the ground again.",
        )
    ],
    "brush": [
        (
            "Why would someone use a soft brush instead of a rough rake?",
            "A soft brush is kinder to delicate things underneath. When something is small or fragile, gentle tools help without scratching it.",
        )
    ],
    "owl": [
        (
            "Why are owls often in fairy tales at night?",
            "Owls are quiet night birds with big eyes, so they fit moonlit stories very well. They can seem wise because they notice things in the dark.",
        )
    ],
    "firefly": [
        (
            "Why does a firefly look like a tiny lantern?",
            "A firefly makes its own small light, so it glows in the dark. That is why stories often compare it to a lantern or a spark.",
        )
    ],
    "twinkle": [
        (
            "What does twinkle mean?",
            "Twinkle means to shine with small quick flashes of light. Stars, fairy lights, and bright wet things can all twinkle.",
        )
    ],
    "recognize": [
        (
            "What does recognize mean?",
            "Recognize means to know something because you have seen or learned it before. You might recognize a face, a voice, or the right path home.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a thin cloud close to the ground made of tiny drops of water. It can make places look soft and dreamy.",
        )
    ],
    "snow": [
        (
            "Why does snow hide paths?",
            "Snow covers the ground in white, so little edges and stones can disappear underneath it. That makes a path harder to see until it is cleared.",
        )
    ],
    "flowers": [
        (
            "Why do flower petals fall?",
            "Petals fall when a flower is old, when the wind shakes it, or when it has finished blooming. They can cover the ground like a soft little blanket.",
        )
    ],
    "moth": [
        (
            "Why do moths come out at night?",
            "Many moths are most active when it is dark and cooler outside. They often use light and familiar places to help them find their way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["recognize", "twinkle", "broom", "brush", "owl", "firefly", "mist", "snow", "flowers", "moth"]


CURATED = [
    StoryParams(
        place="mushroom_hollow",
        cover="leaves",
        guide="starstones",
        tool="birch_broom",
        visitor="aunt_moth",
        helper="owl",
        hero_name="Lina",
        hero_type="fairy_girl",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        place="willow_bridge",
        cover="mist",
        guide="bellstones",
        tool="feather_brush",
        visitor="hedgehog_tailor",
        helper="firefly",
        hero_name="Pip",
        hero_type="fairy_boy",
        elder_type="grandmother",
        delay=1,
    ),
    StoryParams(
        place="moon_garden",
        cover="petals",
        guide="shell_steps",
        tool="feather_brush",
        visitor="cricket_cousin",
        helper="owl",
        hero_name="Mira",
        hero_type="fairy_girl",
        elder_type="grandmother",
        delay=2,
    ),
    StoryParams(
        place="mushroom_hollow",
        cover="snow",
        guide="starstones",
        tool="reed_broom",
        visitor="hedgehog_tailor",
        helper="owl",
        hero_name="Rowan",
        hero_type="fairy_boy",
        elder_type="grandmother",
        delay=2,
    ),
    StoryParams(
        place="moon_garden",
        cover="dew",
        guide="bellstones",
        tool="feather_brush",
        visitor="aunt_moth",
        helper="firefly",
        hero_name="Tansy",
        hero_type="fairy_girl",
        elder_type="grandmother",
        delay=0,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    cover = f["cover_cfg"]
    guide = f["guide_cfg"]
    visitor = f["visitor_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words '
        f'"recognize", "sweep", and "twinkle". The story should happen in {place.label} '
        f'and use inner monologue and dialogue.'
    )
    if outcome == "recognized":
        return [
            base,
            f"Tell a gentle fairy tale where {hero.id} forgets to sweep away {cover.phrase}, then recognizes a tiny hidden glow and clears {guide.plural_label} in time for {visitor.label} to find the way home.",
            f"Write a moonlit story with dialogue and inner thoughts where a child sweeps a magical path so someone can recognize the right door by its twinkle.",
        ]
    return [
        base,
        f"Tell a fairy-tale story where {hero.id} sweeps the path too late for the traveler to see it from far away, so a helper must guide {visitor.label} the rest of the way.",
        f"Write a gentle story with dialogue and inner monologue where a child learns to sweep early because a path must twinkle before a visitor can recognize home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    visitor = f["visitor_cfg"]
    helper = f["helper_cfg"]
    place = f["place_cfg"]
    cover = f["cover_cfg"]
    guide = f["guide_cfg"]
    tool_cfg = f["tool_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little fairy in {place.label}, and {visitor.label}, who needed help finding the way. {elder.label_word.capitalize()} also mattered because {elder.pronoun()} had taught {hero.pronoun('object')} why the path must be kept clear.",
        ),
        (
            f"Why did {hero.id} need to sweep the path?",
            f"{hero.id} needed to sweep away {cover.phrase} so {guide.plural_label} could twinkle again. The visitor depended on that light to recognize the right way home.",
        ),
        (
            f"What clue helped {hero.id} recognize the problem?",
            f"{hero.id} noticed one tiny blink hiding under {cover.phrase}. That faint light showed {hero.pronoun('object')} that the magical path was still there, only covered up.",
        ),
        (
            f"How did {hero.id} fix the problem?",
            f"{hero.pronoun().capitalize()} used {tool_cfg.phrase} and swept carefully so the little lights underneath would not be hurt. Once the path was clear, {guide.plural_label} began to twinkle all along the ground.",
        ),
    ]
    if outcome == "recognized":
        qa.append(
            (
                f"How did {visitor.label} find the way in the end?",
                f"{visitor.label.capitalize()} saw the twinkling path and said {visitor.label.lower() if visitor.label.startswith('the ') else visitor.label} could recognize it at once. The shining stones turned confusion into certainty because they marked the true door clearly.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {helper.label_word} have to help?",
                f"The path was shining again, but the night had grown deep and {visitor.label} was already too far away to see the first bright steps. {helper.label_word.capitalize()} helped carry the guidance outward, and that gave the visitor one more way to recognize where to go.",
            )
        )
    qa.append(
        (
            "What did the ending show had changed?",
            f"The ending showed that {hero.id} had learned the lesson and meant to sweep before playing next time. The final image of the path twinkling proved the home was ready for visitors again.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["guide_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["cover_cfg"].tags)
    tags |= set(f["visitor_cfg"].tags) | set(f["helper_cfg"].tags)
    tags.add("recognize")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, G) :- place(P), cover(C), guide(G), affords_cover(P, C), affords_guide(P, G), has_tool(C, G).

sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
compatible(T, C, G) :- sensible(T), power(T, P), difficulty(C, D), P >= D, gentle(T, Ge), need_gentle(G, Ng), Ge >= Ng.
has_tool(C, G) :- compatible(T, C, G).

late :- delay(D), D >= 2.
outcome(recognized) :- chosen_tool(T), chosen_cover(C), chosen_guide(G), compatible(T, C, G), not late.
outcome(guided) :- chosen_tool(T), chosen_cover(C), chosen_guide(G), compatible(T, C, G), late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cover_id in sorted(place.affords_covers):
            lines.append(asp.fact("affords_cover", place_id, cover_id))
        for guide_id in sorted(place.affords_guides):
            lines.append(asp.fact("affords_guide", place_id, guide_id))
    for cover_id, cover in COVERS.items():
        lines.append(asp.fact("cover", cover_id))
        lines.append(asp.fact("difficulty", cover_id, cover.difficulty))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        lines.append(asp.fact("need_gentle", guide_id, guide.need_gentle))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        lines.append(asp.fact("gentle", tool_id, tool.gentle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_compatible_tools() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_cover", params.cover),
            asp.fact("chosen_guide", params.guide),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Verify failed: generated story was empty.)")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if "twinkle" not in sample.story.lower():
        raise StoryError('(Verify failed: generated story did not include "twinkle".)')
    if "recognize" not in sample.story.lower():
        raise StoryError('(Verify failed: generated story did not include "recognize".)')
    if "sweep" not in sample.story.lower():
        raise StoryError('(Verify failed: generated story did not include "sweep".)')


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {t.id for t in sensible_tools()}
    cl_sensible = set(asp_sensible_tools())
    if py_sensible == cl_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    py_compat = {
        (tool.id, cover.id, guide.id)
        for tool in TOOLS.values()
        for cover in COVERS.values()
        for guide in GUIDES.values()
        if compatible_tool(tool, cover, guide)
    }
    cl_compat = set(asp_compatible_tools())
    if py_compat == cl_compat:
        print(f"OK: compatible tools match ({len(py_compat)} triples).")
    else:
        rc = 1
        print("MISMATCH in compatible tools:")
        if cl_compat - py_compat:
            print("  only in clingo:", sorted(cl_compat - py_compat))
        if py_compat - cl_compat:
            print("  only in python:", sorted(py_compat - cl_compat))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test_generation()
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child must sweep a hidden moon-path so it can twinkle and a visitor can recognize the way home."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the sweeping happens")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(hero_type: str, rng: random.Random) -> str:
    if hero_type == "fairy_boy":
        return rng.choice(BOY_NAMES)
    return rng.choice(GIRL_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cover and args.guide:
        place = PLACES[args.place]
        cover = COVERS[args.cover]
        guide = GUIDES[args.guide]
        if (args.place, args.cover, args.guide) not in valid_combos():
            raise StoryError(explain_combo(place, cover, guide))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cover is None or combo[1] == args.cover)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cover_id, guide_id = rng.choice(sorted(combos))
    cover = COVERS[cover_id]
    guide = GUIDES[guide_id]

    compatible_ids = [
        tool_id for tool_id, tool in TOOLS.items()
        if compatible_tool(tool, cover, guide)
    ]
    if args.tool:
        tool = TOOLS[args.tool]
        if not compatible_tool(tool, cover, guide):
            raise StoryError(explain_tool(tool, cover, guide))
        tool_id = args.tool
    else:
        tool_id = rng.choice(sorted(compatible_ids))

    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or _pick_name(hero_type, rng)
    visitor_id = args.visitor or rng.choice(sorted(VISITORS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        cover=cover_id,
        guide=guide_id,
        tool=tool_id,
        visitor=visitor_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        cover = COVERS[params.cover]
        guide = GUIDES[params.guide]
        tool = TOOLS[params.tool]
        visitor = VISITORS[params.visitor]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter {err!s}.)") from None

    if (params.place, params.cover, params.guide) not in valid_combos():
        raise StoryError(explain_combo(place, cover, guide))
    if not compatible_tool(tool, cover, guide):
        raise StoryError(explain_tool(tool, cover, guide))

    world = tell(
        place=place,
        cover=cover,
        guide=guide,
        tool=tool,
        visitor_cfg=visitor,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        delay=params.delay,
    )

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cover, guide) combos:\n")
        for place_id, cover_id, guide_id in combos:
            compatible_ids = sorted(
                tool_id for tool_id, tool in TOOLS.items()
                if compatible_tool(tool, COVERS[cover_id], GUIDES[guide_id])
            )
            print(f"  {place_id:16} {cover_id:8} {guide_id:11}  tools=[{', '.join(compatible_ids)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.cover} over {p.guide} at {p.place} "
                f"({p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
