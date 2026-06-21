#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py
============================================================================

A standalone story world for a nursery-rhyme-flavored tale of a child who wants
to leave a grand signature, makes a public mess instead, and watches a clever
helper transform the mistake into something lovely and useful.

Domain sketch
-------------
At a small village fête, a little animal child is eager to sign in for the day.
But the child mistakes a public display for the signing cloth and uses a messy
marking material to make a huge signature. The crowd gasps; the mistake becomes
a "scandal." A calm helper then tries a sensible transforming repair: stitching
a patch over the stain, dyeing the whole cloth into a richer color, or pasting
a neat label over a messy paper page. If the helper acts in time and with a
strong enough fix, the blunder is transformed into a decoration and the day goes
on. If not, the scandal lingers and the festival song falls flat.

Run it
------
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py --event moon_fair --mark blackberry --target banner
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py --target cobblestone
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py --response wipe_with_sleeve
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/signature_scandal_transformation_nursery_rhyme.py --verify
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
        female = {"girl", "hen", "goose", "ewe", "mother"}
        male = {"boy", "gander", "ram", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Event:
    id: str
    place: str
    bells: str
    goal: str
    display_line: str
    close_line: str
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
class Mark:
    id: str
    label: str
    phrase: str
    trail: str
    stain_strength: int
    messy: bool = True
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
    phrase: str
    kind: str
    publicity: int
    can_stain: bool = True
    transformable: bool = True
    near_line: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
    supports: set[str]
    text: str
    fail: str
    qa_text: str
    transformed_shape: str
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
class ProperTool:
    id: str
    label: str
    phrase: str
    action: str
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


def _r_scandal(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    crowd = world.get("crowd")
    hero = world.get("hero")
    if target.meters["stained"] < THRESHOLD:
        return out
    sig = ("scandal", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crowd.memes["shock"] += 1
    crowd.memes["scandal"] += target.meters["publicity"]
    hero.memes["shame"] += 1
    out.append("__scandal__")
    return out


def _r_transform_settle(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    crowd = world.get("crowd")
    hero = world.get("hero")
    if target.meters["transformed"] < THRESHOLD:
        return out
    sig = ("settle", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crowd.memes["scandal"] = 0.0
    crowd.memes["delight"] += 1
    hero.memes["relief"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scandal", tag="social", apply=_r_scandal),
    Rule(name="transform_settle", tag="social", apply=_r_transform_settle),
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


def hazard_at_risk(mark: Mark, target: Target) -> bool:
    return mark.messy and target.can_stain


def sensible_responses_for(target: Target) -> list[Response]:
    return [
        r for r in RESPONSES.values()
        if r.sense >= SENSE_MIN and target.kind in r.supports and target.transformable
    ]


def stain_severity(mark: Mark, target: Target, delay: int) -> int:
    return mark.stain_strength + target.publicity + delay


def is_contained(mark: Mark, target: Target, response: Response, delay: int) -> bool:
    return target.kind in response.supports and response.power >= stain_severity(mark, target, delay)


def predict_scandal(world: World, mark_id: str, target_id: str) -> dict:
    sim = world.copy()
    _do_mistake(sim, MARKS[mark_id], sim.get(target_id), narrate=False)
    crowd = sim.get("crowd")
    return {
        "stained": sim.get(target_id).meters["stained"] >= THRESHOLD,
        "scandal": crowd.memes["scandal"],
    }


def _do_mistake(world: World, mark: Mark, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["stained"] += 1
    target_ent.meters["publicity"] = float(target_ent.attrs["publicity"])
    target_ent.attrs["mark_used"] = mark.id
    propagate(world, narrate=narrate)


def introduce(world: World, event: Event, hero: Entity) -> None:
    world.say(
        f"Little {hero.id} skipped to {event.place}. {event.bells}, "
        f"and every cobble seemed to hum a tune."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted {event.goal} before the morning song was done."
    )


def display_setup(world: World, event: Event, target: Target, helper: Entity, tool: ProperTool) -> None:
    world.say(
        f"Near the gate stood {target.phrase}, {target.near_line}. "
        f"Beside it, {helper.id} had set {tool.phrase} for the true sign-in card."
    )
    world.say(event.display_line)


def temptation(world: World, hero: Entity, mark: Mark, target: Target) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"A grand signature needs a grand sweep," sang {hero.id}. '
        f"{hero.pronoun().capitalize()} dipped a paw in {mark.phrase} and looked toward {target.the}."
    )


def warning(world: World, friend: Entity, hero: Entity, mark: Mark, target: Target) -> None:
    pred = predict_scandal(world, mark.id, "target")
    world.facts["predicted_scandal"] = pred["scandal"]
    friend.memes["worry"] += 1
    extra = " It looked much too public for a practice mark." if pred["scandal"] >= THRESHOLD else ""
    world.say(
        f'"Softly now," said {friend.id}. "That may not be the signing place. '
        f'{mark.label.capitalize()} can spread, and people may call it a scandal."{extra}'
    )


def mistake(world: World, hero: Entity, mark: Mark, target_ent: Entity, target: Target) -> None:
    hero.memes["defiance"] += 1
    _do_mistake(world, mark, target_ent, narrate=True)
    world.say(
        f"But swish went the paw, and {hero.id} wrote a looping signature across {target.the}. "
        f"{mark.trail.capitalize()} curled where it should not be."
    )


def gasp(world: World, crowd: Entity, target: Target) -> None:
    world.say(
        f'The fiddles hiccupped. The sparrows whispered. "Oh dear, oh dear -- what a scandal!" '
        f"murmured the crowd when they saw {target.the}."
    )


def helper_arrives(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["calm"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{helper.id} did not stamp or scold. {helper.pronoun().capitalize()} knelt by {hero.id} "
        f"and said, \"A mistake may still be mended, if small hands and kind heads work together.\""
    )


def repair(world: World, helper: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["stained"] = 0.0
    target_ent.meters["transformed"] += 1
    target_ent.attrs["shape"] = response.transformed_shape
    body = response.text.format(target=target.label, shape=response.transformed_shape)
    world.say(f"{helper.id} {body}.")
    world.say(
        f"Soon the old mark was no blot at all, but {response.transformed_shape} bright enough to make the onlookers blink."
    )
    propagate(world, narrate=False)


def repair_fail(world: World, helper: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["stained"] += 1
    target_ent.meters["spoiled"] += 1
    body = response.fail.format(target=target.label)
    world.say(f"{helper.id} {body}.")
    world.say(
        "But the stain had sat too long and stared too loudly. The whispering did not stop."
    )


def proper_signature(world: World, hero: Entity, helper: Entity, tool: ProperTool) -> None:
    hero.memes["care"] += 1
    hero.memes["joy"] += 1
    world.say(
        f'Then {helper.id} held out {tool.phrase}. "{tool.action}," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} made a small, neat signature at the proper place, and this time the line sat sweetly where it belonged."
    )


def lesson(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["shame"] = 0.0
    world.say(
        f'"Ask first, sign second," said {helper.id}. "A bold mark is merry only on the thing meant to hold it."'
    )
    world.say(
        f"{hero.id} nodded and tucked the lesson away, as carefully as a button in a little coat."
    )


def happy_end(world: World, event: Event, hero: Entity, target: Target) -> None:
    world.say(
        f"Up rose the tune again. Round danced the neighbors. {event.close_line}, and even {target.the} seemed to sway along."
    )
    world.say(
        f"{hero.id} skipped under the bunting, no longer proud of being biggest, but glad of being careful and kind."
    )


def sad_end(world: World, event: Event, hero: Entity, target: Target) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"The tune began again, but thinner than before. {target.the} had to be carried away, and the morning felt smaller."
    )
    world.say(
        f"{hero.id} stayed close to {world.get('helper').id} and promised that next time even a tiny signature would wait for the right place."
    )


def tell(
    event: Event,
    mark: Mark,
    target: Target,
    response: Response,
    tool: ProperTool,
    *,
    hero_name: str = "Wren",
    hero_type: str = "girl",
    friend_name: str = "Pip",
    friend_type: str = "boy",
    helper_name: str = "Dame Goose",
    helper_type: str = "goose",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    crowd = world.add(Entity(id="crowd", kind="character", type="folk", role="crowd", label="the crowd"))
    target_ent = world.add(Entity(id="target", kind="thing", type=target.kind, label=target.label))
    target_ent.attrs["publicity"] = target.publicity
    target_ent.attrs["shape"] = ""
    target_ent.attrs["mark_used"] = ""
    crowd.memes["scandal"] = 0.0
    crowd.memes["shock"] = 0.0
    crowd.memes["delight"] = 0.0
    hero.memes["shame"] = 0.0
    hero.memes["relief"] = 0.0
    helper.memes["calm"] = 0.0

    introduce(world, event, hero)
    display_setup(world, event, target, helper, tool)

    world.para()
    temptation(world, hero, mark, target)
    warning(world, friend, hero, mark, target)
    mistake(world, hero, mark, target_ent, target)
    gasp(world, crowd, target)

    world.para()
    helper_arrives(world, helper, hero)
    severity = stain_severity(mark, target, delay)
    target_ent.meters["severity"] = float(severity)
    contained = is_contained(mark, target, response, delay)

    if contained:
        repair(world, helper, response, target_ent, target)
        proper_signature(world, hero, helper, tool)
        lesson(world, helper, hero)
        world.para()
        happy_end(world, event, hero, target)
        outcome = "mended"
    else:
        repair_fail(world, helper, response, target_ent, target)
        lesson(world, helper, hero)
        world.para()
        sad_end(world, event, hero, target)
        outcome = "spoiled"

    world.facts.update(
        event=event,
        mark=mark,
        target_cfg=target,
        response=response,
        tool=tool,
        hero=hero,
        friend=friend,
        helper=helper,
        crowd=crowd,
        target=target_ent,
        delay=delay,
        severity=severity,
        outcome=outcome,
        transformed=target_ent.meters["transformed"] >= THRESHOLD,
        scandal=crowd.memes["shock"] >= THRESHOLD,
    )
    return world


EVENTS = {
    "may_day": Event(
        id="may_day",
        place="the maypole green",
        bells="Ding dong, went the ribbon bells",
        goal="to join the first circle dance",
        display_line="A lace card lay nearby for names, yet the grand cloth stole the eye first.",
        close_line="Round the maypole they went, heel and toe and little bow",
        tags={"dance", "festival"},
    ),
    "moon_fair": Event(
        id="moon_fair",
        place="the lantern square",
        bells="Tinny chimes went ting-a-ting",
        goal="to sing beneath the lanterns",
        display_line="A little sign-in card waited by the lamp tray, though it was easy to miss.",
        close_line="Lantern light trembled gold on every hat and feather",
        tags={"lantern", "song"},
    ),
    "pie_day": Event(
        id="pie_day",
        place="the market lane",
        bells="Clatter went the pie tins",
        goal="to march in the crust-and-crumb parade",
        display_line="A neat name slip sat by the apple basket, but the decorated cloth looked grander.",
        close_line="The pie judges laughed and tapped their spoons in time",
        tags={"parade", "market"},
    ),
}

MARKS = {
    "blackberry": Mark(
        id="blackberry",
        label="blackberry mash",
        phrase="a saucer of blackberry mash",
        trail="purple drips",
        stain_strength=1,
        messy=True,
        tags={"berry", "stain"},
    ),
    "beet": Mark(
        id="beet",
        label="beet juice",
        phrase="a cup of beet juice",
        trail="red streaks",
        stain_strength=2,
        messy=True,
        tags={"beet", "stain"},
    ),
    "soot": Mark(
        id="soot",
        label="chimney soot",
        phrase="a pinch of chimney soot and spit",
        trail="black smudges",
        stain_strength=2,
        messy=True,
        tags={"soot", "stain"},
    ),
}

TARGETS = {
    "banner": Target(
        id="banner",
        label="banner",
        phrase="a white welcome banner",
        kind="cloth",
        publicity=2,
        can_stain=True,
        transformable=True,
        near_line="fluttering in the breeze like a swan's clean wing",
        tags={"banner", "cloth"},
    ),
    "apron": Target(
        id="apron",
        label="festival apron",
        phrase="the judge's cream festival apron",
        kind="cloth",
        publicity=1,
        can_stain=True,
        transformable=True,
        near_line="hanging from a peg with blue ribbons at the hem",
        tags={"apron", "cloth"},
    ),
    "songbook": Target(
        id="songbook",
        label="songbook cover",
        phrase="the big village songbook with a pale paper cover",
        kind="paper",
        publicity=2,
        can_stain=True,
        transformable=True,
        near_line="propped open on a stand where everyone could see",
        tags={"book", "paper"},
    ),
    "cobblestone": Target(
        id="cobblestone",
        label="cobblestone",
        phrase="a gray cobblestone by the gate",
        kind="stone",
        publicity=0,
        can_stain=False,
        transformable=False,
        near_line="quiet under everybody's shoes",
        tags={"stone"},
    ),
}

RESPONSES = {
    "applique_patch": Response(
        id="applique_patch",
        sense=3,
        power=4,
        supports={"cloth"},
        text="threaded a silver needle, cut bright scraps, and stitched the stain on the {target} into {shape}",
        fail="stitched as fast as {helper_pronoun} could, but the {target} had been too badly marked to make neat again",
        qa_text="stitched bright scraps over the stain and turned it into a decoration",
        transformed_shape="a little posy of cloth flowers",
        tags={"sewing", "patch"},
    ),
    "dye_over": Response(
        id="dye_over",
        sense=3,
        power=3,
        supports={"cloth"},
        text="mixed a safer bowl of color and dyed the whole {target} until the bad blot melted into {shape}",
        fail="tried to dye the {target} evenly, but the old mark bled through darker than the rest",
        qa_text="dyed the whole cloth so the stain became part of a new color",
        transformed_shape="a deep plum swirl",
        tags={"dye", "cloth"},
    ),
    "label_cover": Response(
        id="label_cover",
        sense=3,
        power=4,
        supports={"paper"},
        text="trimmed a clean paper oval and pasted it over the stain on the {target}, making {shape}",
        fail="pasted a fresh label over the {target}, but the wet stain buckled the paper underneath",
        qa_text="covered the stain with a clean label and made a new title piece",
        transformed_shape="a neat singing moon with curled letters",
        tags={"paper", "label"},
    ),
    "wipe_with_sleeve": Response(
        id="wipe_with_sleeve",
        sense=1,
        power=1,
        supports={"cloth", "paper"},
        text="rubbed at the {target} with a sleeve until the stain only smeared wider",
        fail="rubbed at the {target} with a sleeve and spread the mess further still",
        qa_text="rubbed at it with a sleeve",
        transformed_shape="a larger blot",
        tags={"wipe"},
    ),
}

TOOLS = {
    "quill": ProperTool(
        id="quill",
        label="quill",
        phrase="a little goose-feather quill and ink card",
        action="Use the small tool for the small place",
        tags={"quill", "signature"},
    ),
    "stamp": ProperTool(
        id="stamp",
        label="stamp",
        phrase="a tiny star stamp beside the name card",
        action="Press here gently and leave your neat little sign",
        tags={"stamp", "signature"},
    ),
}

GIRL_NAMES = ["Wren", "Midge", "Tilly", "Poppy", "Lark", "Nell", "Dot", "Moss"]
BOY_NAMES = ["Pip", "Tad", "Robin", "Ned", "Bram", "Otis", "Kit", "Milo"]


@dataclass
class StoryParams:
    event: str
    mark: str
    target: str
    response: str
    tool: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    helper: str
    helper_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for event_id in EVENTS:
        for mark_id, mark in MARKS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(mark, target) and sensible_responses_for(target):
                    combos.append((event_id, mark_id, target_id))
    return combos


KNOWLEDGE = {
    "signature": [
        (
            "What is a signature?",
            "A signature is the special way someone writes their own name. It shows who signed something."
        )
    ],
    "scandal": [
        (
            "What does scandal mean?",
            "A scandal means people are shocked and whispering about something that went wrong in public. It usually feels bigger because so many people are talking at once."
        )
    ],
    "berry": [
        (
            "Why can blackberry mash stain cloth?",
            "Blackberry juice is full of dark color, so it can sink into cloth and leave purple marks. That is why it is fine for jam, but risky for clean fabric."
        )
    ],
    "soot": [
        (
            "Why is chimney soot messy?",
            "Soot is made of tiny black bits from smoke and fire. It smudges quickly, so even a little can spread over fingers and paper."
        )
    ],
    "paper": [
        (
            "Why can wet paper wrinkle?",
            "Paper drinks up water and juice. When it gets too wet, it can buckle and wrinkle instead of staying flat."
        )
    ],
    "cloth": [
        (
            "How can cloth be transformed after a stain?",
            "Sometimes a stain on cloth can be covered with a patch or hidden by dye. Then the mistake becomes part of a new design."
        )
    ],
    "quill": [
        (
            "What is a quill?",
            "A quill is an old writing tool made from a feather. People dip the point in ink to make careful lines."
        )
    ],
    "stamp": [
        (
            "What does a stamp do?",
            "A stamp presses a shape or mark onto paper. It helps make the same neat sign each time."
        )
    ],
    "sewing": [
        (
            "What does sewing do?",
            "Sewing joins cloth with thread. It can also hold a patch in place to cover a tear or stain."
        )
    ],
    "dye": [
        (
            "What is dye?",
            "Dye is color used to change the look of cloth. It can turn plain fabric into a new shade all over."
        )
    ],
    "label": [
        (
            "What is a label?",
            "A label is a small piece with words on it that tells what something is. On a book, it can make the title clear and neat."
        )
    ],
}
KNOWLEDGE_ORDER = ["signature", "scandal", "berry", "soot", "cloth", "paper", "quill", "stamp", "sewing", "dye", "label"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    event = f["event"]
    mark = f["mark"]
    target = f["target_cfg"]
    tool = f["tool"]
    outcome = f["outcome"]
    if outcome == "mended":
        return [
            f'Write a nursery-rhyme-style story that uses the words "signature" and "scandal" and includes a transformation.',
            f"Tell a sing-song story where a little child makes a messy signature on {target.the} with {mark.label}, the crowd calls it a scandal, and a calm helper transforms the mess into something lovely.",
            f"Write a gentle tale set at {event.place} where the child learns to use {tool.label} for the right place after a public mistake is mended."
        ]
    return [
        f'Write a nursery-rhyme-style cautionary story that uses the words "signature" and "scandal" and includes a transformation attempt.',
        f"Tell a rhyming village story where a child writes a huge signature on {target.the} with {mark.label}, and the scandal cannot be fully mended in time.",
        f"Write a simple story at {event.place} where a helper tries to transform a public mess, but the child still learns to ask before signing."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    event = f["event"]
    mark = f["mark"]
    target_cfg = f["target_cfg"]
    response = f["response"]
    tool = f["tool"]
    target = f["target"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about little {hero.id}, who wanted to join the fun at {event.place}, and {helper.id}, who helped when a public mistake was made."
        ),
        (
            "Why did the child make a big signature?",
            f"{hero.id} wanted to look grand and grown-up before the festival began. That proud feeling made {hero.pronoun('object')} choose the biggest thing in sight instead of the small sign-in place."
        ),
        (
            f"Why did people call it a scandal?",
            f"They saw a messy signature spread across {target_cfg.the}, which everyone could see. Because the mark was public and out of place, the whispering grew quickly into a scandal."
        ),
        (
            f"What warning did {friend.id} give?",
            f"{friend.id} warned that {mark.label} could spread and that the display might not be the real signing place. The warning mattered because one wrong mark there would be seen by the whole crowd."
        ),
    ]
    if outcome == "mended":
        qa.extend([
            (
                "How was the mistake transformed?",
                f"{helper.id} {response.qa_text}. The repair changed the blot into {target.attrs.get('shape', 'a decoration')}, so the crowd stopped whispering and began smiling instead."
            ),
            (
                f"What happened after the repair?",
                f"After the repair, {helper.id} gave {hero.id} {tool.phrase}. Then {hero.id} made a neat signature in the proper place, showing that the child had learned how to sign carefully."
            ),
            (
                "How did the story end?",
                f"It ended with music and dancing starting up again. The happy ending shows that the scandal was settled because the mistake was transformed and the child changed too."
            ),
        ])
    else:
        qa.extend([
            (
                "Did the helper fix everything in time?",
                f"No. {helper.id} tried to mend the mark, but the stain had become too hard to hide neatly. The transformation helped a little, yet the scandal still spoiled part of the morning."
            ),
            (
                "What did the child learn?",
                f"{hero.id} learned to ask first and sign second. The lesson came from seeing how one proud, hurried signature could trouble many people at once."
            ),
            (
                "How did the story end?",
                f"The festival went on more quietly, and {target_cfg.the} had to be taken away. The ending feels sadder because the public mistake was not fully mended before the moment had passed."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"signature", "scandal"} | set(f["mark"].tags) | set(f["target_cfg"].tags) | set(f["tool"].tags) | set(f["response"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        event="may_day",
        mark="blackberry",
        target="banner",
        response="applique_patch",
        tool="quill",
        hero="Wren",
        hero_type="girl",
        friend="Pip",
        friend_type="boy",
        helper="Dame Goose",
        helper_type="goose",
        delay=0,
    ),
    StoryParams(
        event="moon_fair",
        mark="beet",
        target="songbook",
        response="label_cover",
        tool="stamp",
        hero="Tilly",
        hero_type="girl",
        friend="Robin",
        friend_type="boy",
        helper="Dame Goose",
        helper_type="goose",
        delay=0,
    ),
    StoryParams(
        event="pie_day",
        mark="soot",
        target="apron",
        response="dye_over",
        tool="quill",
        hero="Milo",
        hero_type="boy",
        friend="Poppy",
        friend_type="girl",
        helper="Dame Goose",
        helper_type="goose",
        delay=0,
    ),
    StoryParams(
        event="may_day",
        mark="soot",
        target="banner",
        response="dye_over",
        tool="quill",
        hero="Nell",
        hero_type="girl",
        friend="Tad",
        friend_type="boy",
        helper="Dame Goose",
        helper_type="goose",
        delay=1,
    ),
    StoryParams(
        event="moon_fair",
        mark="beet",
        target="banner",
        response="applique_patch",
        tool="stamp",
        hero="Robin",
        hero_type="boy",
        friend="Midge",
        friend_type="girl",
        helper="Dame Goose",
        helper_type="goose",
        delay=2,
    ),
]


def explain_rejection(mark: Mark, target: Target) -> str:
    if not target.can_stain:
        return (
            f"(No story: {mark.label} on {target.the} would not make a lasting public mess. "
            f"This world needs a stainable target so the signature can cause a scandal.)"
        )
    if not target.transformable:
        return (
            f"(No story: {target.the} cannot be transformed into a repaired festival object here. "
            f"Choose cloth or paper instead.)"
        )
    return "(No story: this combination does not make a workable public stain.)"


def explain_response(response_id: str, target: Target) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses_for(target)))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if target.kind not in response.supports:
        good = ", ".join(sorted(r.id for r in sensible_responses_for(target)))
        return (
            f"(Refusing response '{response_id}': it does not work on {target.kind}. "
            f"Try one of: {good}.)"
        )
    return "(Refusing response: incompatible with target.)"


def outcome_of(params: StoryParams) -> str:
    return "mended" if is_contained(MARKS[params.mark], TARGETS[params.target], RESPONSES[params.response], params.delay) else "spoiled"


ASP_RULES = r"""
hazard(M, T) :- messy(M), stainable(T).
sensible_response(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
compatible_response(T, R) :- target_kind(T, K), supports(R, K), transformable(T), sensible_response(R).
valid(E, M, T) :- event(E), mark(M), target(T), hazard(M, T), compatible_response(T, _).

severity(V) :- chosen_mark(M), stain_strength(M, S), chosen_target(T), publicity(T, P), delay(D), V = S + P + D.
contained :- chosen_target(T), chosen_response(R), compatible_response(T, R), power(R, P), severity(V), P >= V.
outcome(mended) :- contained.
outcome(spoiled) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for mark_id, mark in MARKS.items():
        lines.append(asp.fact("mark", mark_id))
        if mark.messy:
            lines.append(asp.fact("messy", mark_id))
        lines.append(asp.fact("stain_strength", mark_id, mark.stain_strength))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("target_kind", target_id, target.kind))
        lines.append(asp.fact("publicity", target_id, target.publicity))
        if target.can_stain:
            lines.append(asp.fact("stainable", target_id))
        if target.transformable:
            lines.append(asp.fact("transformable", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for kind in sorted(response.supports):
            lines.append(asp.fact("supports", response_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_mark", params.mark),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a signature mistake, a scandal, and a transformation."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (event, mark, target) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="verify Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    hero_type = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), hero_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None:
        target = TARGETS[args.target]
        mark = MARKS[args.mark] if args.mark else next(iter(MARKS.values()))
        if not hazard_at_risk(mark, target):
            raise StoryError(explain_rejection(mark, target))
    if args.mark is not None and args.target is not None:
        mark = MARKS[args.mark]
        target = TARGETS[args.target]
        if not (hazard_at_risk(mark, target) and sensible_responses_for(target)):
            raise StoryError(explain_rejection(mark, target))
    if args.response is not None and args.target is not None:
        target = TARGETS[args.target]
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN or target.kind not in response.supports:
            raise StoryError(explain_response(args.response, target))
    if args.response is not None and args.target is None and RESPONSES[args.response].sense < SENSE_MIN:
        target = next(t for t in TARGETS.values() if sensible_responses_for(t))
        raise StoryError(explain_response(args.response, target))

    combos = [
        combo for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.mark is None or combo[1] == args.mark)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, mark_id, target_id = rng.choice(sorted(combos))
    target = TARGETS[target_id]
    compatible = sensible_responses_for(target)
    if args.response is not None:
        if RESPONSES[args.response] not in compatible:
            raise StoryError(explain_response(args.response, target))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(r.id for r in compatible))
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    hero_name, hero_type = _pick_name(rng)
    friend_name, friend_type = _pick_name(rng, avoid=hero_name)
    helper_name = "Dame Goose"
    helper_type = "goose"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        event=event_id,
        mark=mark_id,
        target=target_id,
        response=response_id,
        tool=tool_id,
        hero=hero_name,
        hero_type=hero_type,
        friend=friend_name,
        friend_type=friend_type,
        helper=helper_name,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        event = EVENTS[params.event]
        mark = MARKS[params.mark]
        target = TARGETS[params.target]
        response = RESPONSES[params.response]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not hazard_at_risk(mark, target):
        raise StoryError(explain_rejection(mark, target))
    if response.sense < SENSE_MIN or target.kind not in response.supports:
        raise StoryError(explain_response(params.response, target))
    if not target.transformable:
        raise StoryError(explain_rejection(mark, target))

    world = tell(
        event=event,
        mark=mark,
        target=target,
        response=response,
        tool=tool,
        hero_name=params.hero,
        hero_type=params.hero_type,
        friend_name=params.friend,
        friend_type=params.friend_type,
        helper_name=params.helper,
        helper_type=params.helper_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show compatible_response/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, mark, target) combos:\n")
        for event_id, mark_id, target_id in combos:
            print(f"  {event_id:10} {mark_id:10} {target_id}")
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
            header = f"### {p.hero}: {p.mark} on {p.target} at {p.event} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
