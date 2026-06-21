#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py
======================================================================================

A standalone story world about a curious child in a hardware store, a humming
display tool with a moving blade, and the funny safe twist that comes from
watching the right way instead of leaning in too close.

Premise
-------
A child notices a demonstration tool in a hardware store and wants a better
look. The grown-up warning is grounded in the child's loose clothing: scarves,
hoodie strings, apron ties, and floppy sleeves can drift where a moving blade
does not belong. The world model checks whether the chosen clothing is actually
loose enough for the chosen tool to make a reasonable cautionary story.

Tone
----
The tone stays child-facing and a little comedic. The dangerous curiosity is
real, but the ending image turns silly and bright: a safe demo makes a curly
wood shaving or wiggly scrap that looks much funnier than the dangerous close-up
the child wanted at first.

Run it
------
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py --tool jigsaw --clothing scarf
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py --tool scroll_saw --clothing safety_vest
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py --qa --json
    python storyworlds/worlds/gpt-5.4/clothing_blade_hardware_store_twist_cautionary_curiosity.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "patient", "sensible"}


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
    moving_blade: bool = False
    loose_clothing: bool = False
    safe_demo: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "clerk_f"}
        male = {"boy", "father", "man", "clerk_m"}
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
class Tool:
    id: str
    label: str
    phrase: str
    hum: str
    risk_line: str
    result: str
    danger: int
    snag_need: int
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
class Clothing:
    id: str
    label: str
    phrase: str
    loose: int
    flutter: str
    relation: str
    plural: bool = False
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


def _r_snag(world: World) -> list[str]:
    child = world.get("child")
    clothing = world.get("clothing")
    tool = world.get("tool")
    if child.meters["too_close"] < THRESHOLD:
        return []
    if clothing.meters["reach_blade"] < THRESHOLD:
        return []
    sig = ("snag", clothing.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clothing.meters["caught"] += 1
    child.memes["fear"] += 1
    tool.meters["jammed"] += 1
    world.get("aisle").meters["danger"] += 1
    return ["__snag__"]


def _r_tug(world: World) -> list[str]:
    clothing = world.get("clothing")
    if clothing.meters["caught"] < THRESHOLD:
        return []
    sig = ("tug", clothing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clothing.meters["pulled"] += 1
    world.get("child").memes["surprise"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="snag", tag="physical", apply=_r_snag),
    Rule(name="tug", tag="physical", apply=_r_tug),
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


def hazard_at_risk(tool: Tool, clothing: Clothing) -> bool:
    return clothing.loose >= tool.snag_need


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(tool: Tool, delay: int) -> int:
    return tool.danger + delay


def is_contained(response: Response, tool: Tool, delay: int) -> bool:
    return response.power >= severity(tool, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(trait: str) -> bool:
    return initial_caution(trait) + 1.0 > CURIOSITY_INIT


def predict_snag(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    clothing = sim.get("clothing")
    clothing.meters["reach_blade"] = 1.0 if sim.facts["clothing_cfg"].loose >= sim.facts["tool_cfg"].snag_need else 0.0
    child.meters["too_close"] = 1.0
    propagate(sim, narrate=False)
    return {
        "caught": clothing.meters["caught"] >= THRESHOLD,
        "danger": sim.get("aisle").meters["danger"],
    }


def enter_store(world: World, child: Entity, parent: Entity, clerk: Entity, clothing: Clothing) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On Saturday, {child.id} went with {child.pronoun('possessive')} {parent.label_word} "
        f"to the hardware store to buy hooks for winter clothing."
    )
    world.say(
        f"{child.id} was wearing {clothing.phrase}, and the bright aisles smelled like cut wood, rope, and new paint."
    )
    world.say(
        f"At the end of one aisle, {clerk.id} stood by a demo bench where a tool buzzed and blinked."
    )


def notice_tool(world: World, child: Entity, tool: Tool) -> None:
    child.memes["curiosity"] = CURIOSITY_INIT
    world.say(
        f'"What is that?" {child.id} asked, staring at {tool.phrase}. The {tool.label} {tool.hum}, '
        f"and the little blade moved so fast it looked like a silver wiggle."
    )


def comic_guess(world: World, child: Entity, tool: Tool) -> None:
    guesses = {
        "jigsaw": f'"It sounds like a sneezy robot bee," {child.id} said.',
        "scroll_saw": f'"It looks like a toothpick trying very hard," {child.id} said.',
        "oscillating_tool": f'"That blade is wiggling like it drank too much lemonade," {child.id} said.',
    }
    world.say(guesses.get(tool.id, f'"That blade looks very busy," {child.id} said.'))


def tempt(world: World, child: Entity, clothing: Clothing) -> None:
    child.memes["bravado"] += 1
    world.say(
        f"{child.id} wanted a closer look. {clothing.phrase.capitalize()} {clothing.flutter}, "
        f"which somehow made the noisy bench even more interesting."
    )


def warn(world: World, child: Entity, parent: Entity, clerk: Entity, tool: Tool, clothing: Clothing) -> None:
    pred = predict_snag(world)
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["caution"] += 1
    world.say(
        f'{parent.label_word.capitalize()} touched {child.id}\'s shoulder. "{tool.risk_line}," '
        f"{parent.pronoun()} said."
    )
    if pred["caught"]:
        world.say(
            f'{clerk.id} nodded. "That moving blade stays on the bench, and loose {clothing.label} should stay back too. '
            f'{clothing.relation.capitalize()} can wander where small hands do not mean to go."'
        )
    else:
        world.say(
            f'{clerk.id} nodded. "It is always smart to watch from the line first," {clerk.pronoun()} said.'
        )


def back_down(world: World, child: Entity, parent: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["curiosity"] = 0.0
    world.say(
        f"{child.id} rocked back on {child.pronoun('possessive')} heels, thought about it, and stopped at the yellow line."
    )
    world.say(
        f'"Okay," {child.pronoun()} said. "I can be curious from back here." {parent.label_word.capitalize()} smiled at that.'
    )


def defy(world: World, child: Entity, clothing_ent: Entity, tool_cfg: Tool) -> None:
    child.memes["defiance"] += 1
    child.meters["too_close"] = 1.0
    clothing_ent.meters["reach_blade"] = 1.0 if world.facts["clothing_cfg"].loose >= tool_cfg.snag_need else 0.0
    world.say(
        f'But curiosity pulled harder. Before anyone could say "line," {child.id} leaned past the yellow tape for one better peek.'
    )


def snag(world: World, child: Entity, clothing: Clothing, tool: Tool) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then it happened fast: {clothing.phrase} shifted the wrong way, the moving blade caught at it, and the whole bench gave a sharp unhappy chatter."
    )
    world.say(
        f"{child.id} jumped back with wide eyes. It was only {clothing.label}, but that was plenty scary."
    )


def rescue(world: World, child: Entity, parent: Entity, clerk: Entity, response: Response, clothing: Clothing) -> None:
    world.get("tool").meters["running"] = 0.0
    world.get("aisle").meters["danger"] = 0.0
    world.get("clothing").meters["caught"] = 0.0
    world.get("clothing").meters["pulled"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    body = response.text.replace("{clothing}", clothing.label)
    world.say(f"{clerk.id} moved first and {body}.")
    world.say(
        f'{parent.label_word.capitalize()} crouched down at once. "You are safe," {parent.pronoun()} said, and that was the most important part.'
    )


def rescue_fail(world: World, child: Entity, parent: Entity, clerk: Entity, response: Response, clothing: Clothing) -> None:
    world.get("tool").meters["running"] = 0.0
    world.get("aisle").meters["danger"] += 1.0
    child.memes["fear"] += 1
    body = response.fail.replace("{clothing}", clothing.label)
    world.say(f"{clerk.id} {body}.")
    world.say(
        f"The bench shuddered, and {clothing.label} came away with a ragged bite missing from it."
    )
    world.get("clothing").meters["torn"] += 1.0


def lesson(world: World, child: Entity, parent: Entity, clerk: Entity, clothing: Clothing, tool: Tool) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(
        f'{clerk.id} unplugged the tool and held up the frayed {clothing.label if world.get("clothing").meters["torn"] >= THRESHOLD else clothing.label}. '
        f'"That is why we keep loose clothing away from a moving blade," {clerk.pronoun()} said.'
    )
    world.say(
        f'{parent.label_word.capitalize()} gave {child.id} a hug. "Curiosity is good," {parent.pronoun()} said softly, '
        f'"but curiosity needs space around tools."'
    )


def safe_demo(world: World, child: Entity, parent: Entity, clerk: Entity, tool: Tool, clothing: Clothing) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"After that, {clerk.id} showed {child.id} the safe way: stand behind the yellow line, tuck loose {clothing.label} in, and watch the demo from there."
    )
    world.say(
        f"{clerk.id} cut a scrap the slow way, and a curly shaving popped up and landed under {child.id}'s nose like a tiny wooden mustache."
    )
    world.say(
        f'{child.id} laughed so hard {child.pronoun()} snorted. It was the twist of the day: the funniest part of the blade was not being near it at all.'
    )


def quiet_end(world: World, child: Entity, parent: Entity, clothing: Clothing) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"They did not stay for another demo. {parent.label_word.capitalize()} folded the nibbled {clothing.label} into the cart and took {child.id}'s hand."
    )
    world.say(
        f"On the ride home, {child.id} kept looking at the torn spot and remembered how quickly one curious step had changed the whole trip."
    )
    world.say(
        f"Later, whenever a tool had a moving blade, {child.id} checked {child.pronoun('possessive')} clothing first and stayed behind the line."
    )


def tell(
    tool: Tool,
    clothing: Clothing,
    response: Response,
    child_name: str = "Mia",
    child_type: str = "girl",
    parent_type: str = "mother",
    clerk_name: str = "Rosa",
    clerk_type: str = "clerk_f",
    trait: str = "careful",
    delay: int = 0,
    age: int = 5,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        age=age,
        traits=[trait],
        attrs={},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    clerk = world.add(Entity(
        id="clerk",
        kind="character",
        type=clerk_type,
        label="the clerk",
        role="clerk",
        attrs={},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        moving_blade=True,
        attrs={},
    ))
    clothing_ent = world.add(Entity(
        id="clothing",
        type="clothing",
        label=clothing.label,
        phrase=clothing.phrase,
        loose_clothing=clothing.loose > 0,
        attrs={},
    ))
    world.add(Entity(id="aisle", type="place", label="the aisle", attrs={}))

    child.id = child_name
    clerk.id = clerk_name

    child.memes["caution"] = initial_caution(trait)
    child.memes["curiosity"] = CURIOSITY_INIT
    tool_ent.meters["running"] = 1.0
    clothing_ent.meters["reach_blade"] = 0.0
    child.meters["too_close"] = 0.0

    world.facts.update(
        tool_cfg=tool,
        clothing_cfg=clothing,
        response=response,
        child=child,
        parent=parent,
        clerk=clerk,
        delay=delay,
        trait=trait,
        child_name=child_name,
        clerk_name=clerk_name,
    )

    enter_store(world, child, parent, clerk, clothing)
    notice_tool(world, child, tool)
    comic_guess(world, child, tool)

    world.para()
    tempt(world, child, clothing)
    warn(world, child, parent, clerk, tool, clothing)

    averted = would_avert(trait)
    if averted:
        back_down(world, child, parent)
        world.para()
        safe_demo(world, child, parent, clerk, tool, clothing)
        outcome = "averted"
    else:
        defy(world, child, clothing_ent, tool)
        world.para()
        snag(world, child, clothing, tool)
        contained = is_contained(response, tool, delay)
        world.para()
        if contained:
            rescue(world, child, parent, clerk, response, clothing)
            lesson(world, child, parent, clerk, clothing, tool)
            world.para()
            safe_demo(world, child, parent, clerk, tool, clothing)
            outcome = "contained"
        else:
            rescue_fail(world, child, parent, clerk, response, clothing)
            lesson(world, child, parent, clerk, clothing, tool)
            world.para()
            quiet_end(world, child, parent, clothing)
            outcome = "torn"

    world.facts.update(
        outcome=outcome,
        averted=outcome == "averted",
        snagged=world.get("clothing").meters["caught"] >= THRESHOLD or outcome in {"contained", "torn"},
        torn=world.get("clothing").meters["torn"] >= THRESHOLD or outcome == "torn",
        severity=severity(tool, delay),
        promised=child.memes["lesson"] >= THRESHOLD or outcome == "averted",
    )
    return world


THE_TOOLS = {
    "jigsaw": Tool(
        id="jigsaw",
        label="jigsaw",
        phrase="a yellow demo jigsaw",
        hum="buzzed like an impatient bee",
        risk_line="Loose clothing and moving blades do not mix",
        result="cut a curvy path through scrap wood",
        danger=3,
        snag_need=1,
        tags={"jigsaw", "blade", "tool"},
    ),
    "scroll_saw": Tool(
        id="scroll_saw",
        label="scroll saw",
        phrase="a little scroll saw",
        hum="purred and tapped at the same time",
        risk_line="That small blade is still a real blade",
        result="nibbled neat curls from thin wood",
        danger=2,
        snag_need=2,
        tags={"scroll_saw", "blade", "tool"},
    ),
    "oscillating_tool": Tool(
        id="oscillating_tool",
        label="oscillating tool",
        phrase="a wiggly oscillating tool",
        hum="hummed with a fast fuzzy whirr",
        risk_line="Even a tiny moving blade deserves room",
        result="shaved a little notch in a scrap board",
        danger=2,
        snag_need=1,
        tags={"oscillating_tool", "blade", "tool"},
    ),
}

CLOTHING = {
    "scarf": Clothing(
        id="scarf",
        label="scarf",
        phrase="a stripy scarf",
        loose=3,
        flutter="swished when she turned" if False else "swished when they turned",
        relation="a scarf end",
        tags={"scarf", "clothing"},
    ),
    "hoodie_strings": Clothing(
        id="hoodie_strings",
        label="hoodie strings",
        phrase="a hoodie with long strings",
        loose=2,
        flutter="bounced on every step",
        relation="those strings",
        plural=True,
        tags={"hoodie", "clothing"},
    ),
    "apron_ties": Clothing(
        id="apron_ties",
        label="apron ties",
        phrase="a little paint apron with loose ties",
        loose=2,
        flutter="flapped behind them like tiny tails",
        relation="apron ties",
        plural=True,
        tags={"apron", "clothing"},
    ),
    "big_sleeves": Clothing(
        id="big_sleeves",
        label="big sleeves",
        phrase="a raincoat with big sleeves",
        loose=1,
        flutter="wobbled when they lifted their arms",
        relation="a sleeve edge",
        plural=True,
        tags={"raincoat", "clothing"},
    ),
    "safety_vest": Clothing(
        id="safety_vest",
        label="safety vest",
        phrase="a bright safety vest zipped snug",
        loose=0,
        flutter="stayed right where it belonged",
        relation="the vest",
        tags={"vest", "clothing"},
    ),
}

RESPONSES = {
    "stop_switch": Response(
        id="stop_switch",
        sense=3,
        power=3,
        text="slapped the stop switch, held the tool still, and eased the {clothing} free",
        fail="hit the stop switch, but one rough tug had already chewed a piece out of the {clothing}",
        qa_text="hit the stop switch and eased the clothing free",
        tags={"stop", "tool"},
    ),
    "unplug_then_free": Response(
        id="unplug_then_free",
        sense=3,
        power=4,
        text="pulled the plug, waited for the buzzing to stop, and carefully freed the {clothing}",
        fail="pulled the plug, but the {clothing} had already been bitten before the tool went still",
        qa_text="unplugged the tool and carefully freed the clothing",
        tags={"unplug", "tool"},
    ),
    "grab_only": Response(
        id="grab_only",
        sense=2,
        power=1,
        text="grabbed the loose {clothing} and jerked it back just in time",
        fail="grabbed for the {clothing}, but the fabric tore before it came loose",
        qa_text="grabbed the clothing and jerked it back",
        tags={"grab", "tool"},
    ),
    "joke_first": Response(
        id="joke_first",
        sense=1,
        power=0,
        text="laughed and said everything was probably fine",
        fail="laughed for one bad second before anyone stopped the tool",
        qa_text="waited too long because of a joke",
        tags={"mistake"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ella", "Ruby", "June"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Sam", "Theo", "Eli", "Jack"]
CLERK_F = ["Rosa", "Jade", "Nina", "Marta"]
CLERK_M = ["Omar", "Luis", "Gabe", "Henry"]
TRAITS = ["careful", "cautious", "patient", "sensible", "bouncy", "bold", "curious", "impulsive"]


@dataclass
class StoryParams:
    tool: str
    clothing: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    clerk_name: str
    clerk_gender: str
    trait: str
    delay: int = 0
    age: int = 5
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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for tool_id, tool in THE_TOOLS.items():
        for clothing_id, clothing in CLOTHING.items():
            if hazard_at_risk(tool, clothing):
                combos.append((tool_id, clothing_id))
    return combos


KNOWLEDGE = {
    "blade": [(
        "What is a blade?",
        "A blade is the sharp moving part on some tools that does the cutting. Because it can hurt you quickly, you only go near it when a grown-up says it is safe."
    )],
    "jigsaw": [(
        "What does a jigsaw do?",
        "A jigsaw is a tool with a small up-and-down blade that cuts shapes in wood. It should be used with room around it and careful grown-up hands."
    )],
    "scroll_saw": [(
        "What is a scroll saw for?",
        "A scroll saw cuts thin wood with a tiny moving blade. Even though the blade is small, it still needs careful space."
    )],
    "oscillating_tool": [(
        "What is an oscillating tool?",
        "An oscillating tool moves a small blade back and forth very fast. It can cut or scrape, so loose things should stay away from it."
    )],
    "clothing": [(
        "Why should loose clothing stay away from tools?",
        "Loose clothing can swing, flap, or dangle somewhere you did not mean it to go. Around a moving tool, that can pull trouble closer very fast."
    )],
    "scarf": [(
        "Why can a scarf be risky near a tool?",
        "A scarf has long loose ends that move when you turn or walk. That makes it important to tuck it in and stand back."
    )],
    "hoodie": [(
        "Why can hoodie strings be a problem near a machine?",
        "Hoodie strings dangle in front of you and can bounce when you move. That is why they should be tucked in near equipment."
    )],
    "apron": [(
        "What should you do with apron ties near a tool?",
        "Tie them snug and keep them away from moving parts. Loose apron ties are for painting and baking, not for waving near machines."
    )],
    "raincoat": [(
        "Why can big sleeves need extra care?",
        "Big sleeves can puff or wobble when you lift your arms. Near a work bench, it is smart to keep them tucked back."
    )],
    "stop": [(
        "What does a stop switch do?",
        "A stop switch turns a machine off fast. Grown-ups use it to make a tool stop before fixing a problem."
    )],
    "unplug": [(
        "Why unplug a tool before fixing something near it?",
        "Unplugging makes sure the tool cannot start again by accident. That gives a grown-up a safer moment to help."
    )],
}

KNOWLEDGE_ORDER = [
    "blade",
    "jigsaw",
    "scroll_saw",
    "oscillating_tool",
    "clothing",
    "scarf",
    "hoodie",
    "apron",
    "raincoat",
    "stop",
    "unplug",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = f["tool_cfg"]
    clothing = f["clothing_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a funny cautionary story for a 3-to-5-year-old set in a hardware store, '
        f'where a curious child wearing {clothing.phrase} gets interested in a {tool.label} and its blade. '
        f'Include the words "clothing" and "blade".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a hardware store story where {child.id} listens to a warning about loose clothing, stays behind the yellow line, and discovers a silly safe twist at the end.",
            f"Write a gentle story about curiosity, safety, and comedy, where the child wants a closer look at the blade but learns the funniest part can happen from far away.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a cautionary story where {child.id} leans too close to the tool, a grown-up stops the danger quickly, and the ending turns funny with a safe demo.",
            f"Write a story with a real scare but no injury, where loose clothing causes trouble near a moving blade and the lesson leads to a comic ending.",
        ]
    return [
        base,
        f"Tell a cautionary hardware store story where {child.id}'s loose clothing gets torn because curiosity beats caution for one moment.",
        f"Write a child-facing story with a sadder ending, where everyone stays safe but the child remembers the cost of stepping too close to a moving blade.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clerk = f["clerk"]
    tool = f["tool_cfg"]
    clothing = f["clothing_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and {clerk.id} at a hardware store. The story begins with a shopping trip and turns into a lesson about curiosity and safe space."
        ),
        (
            f"What made {child.id} curious?",
            f"{child.id} heard the {tool.label} buzzing and saw its little blade moving so fast it looked like a silver wiggle. That strange sound and motion made {child.pronoun('object')} want a closer look."
        ),
        (
            f"Why did the grown-ups warn {child.id} about {clothing.label}?",
            f"They warned {child.id} because loose {clothing.label} could drift toward the moving blade. The problem was not just the tool itself, but how the clothing might wander where {child.id} did not mean it to go."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What did {child.id} do after the warning?",
            f"{child.id} stopped at the yellow line and watched from there instead of leaning in close. That choice kept the curious moment funny instead of scary."
        ))
        qa.append((
            "What was the twist at the end?",
            f"The funny surprise was that the best part was a safe one: a curly shaving landed under {child.id}'s nose like a wooden mustache. The child learned that the blade did not need to be close to be interesting."
        ))
    elif outcome == "contained":
        body = response.qa_text
        qa.append((
            "What happened when the child leaned too close?",
            f"{clothing.phrase.capitalize()} drifted the wrong way and the tool caught at it, which frightened {child.id}. It became a scare instead of an injury because the grown-up acted quickly."
        ))
        qa.append((
            "How was the problem fixed?",
            f"{clerk.id} {body}. After that, the adults explained why loose clothing and moving tools need space from each other."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a safe demo from behind the line, and the tool made a silly little wooden mustache instead of more trouble. The new ending image shows that {child.id} had changed how {child.pronoun()} watched."
        ))
    else:
        qa.append((
            "What went wrong in the story?",
            f"{child.id} leaned past the line, and the moving tool tore the {clothing.label}. Everyone stayed safe, but the torn clothing made the warning feel real."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.id} learned that one curious step can change things very quickly around a moving blade. Afterward, {child.pronoun()} remembered to check clothing and stay back instead of rushing in."
        ))
        qa.append((
            "Why is the ending cautionary?",
            f"It is cautionary because the family goes home with torn clothing instead of a funny safe demo. The loss is small, but it proves that the rule mattered."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool_cfg"].tags) | set(f["clothing_cfg"].tags)
    if f["outcome"] == "contained":
        tags |= set(f["response"].tags)
    elif f["outcome"] == "torn":
        tags.add("clothing")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("moving_blade", e.moving_blade),
                                 ("loose_clothing", e.loose_clothing),
                                 ("safe_demo", e.safe_demo)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        tool="jigsaw",
        clothing="scarf",
        response="unplug_then_free",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        clerk_name="Rosa",
        clerk_gender="girl",
        trait="careful",
        delay=0,
        age=5,
    ),
    StoryParams(
        tool="scroll_saw",
        clothing="hoodie_strings",
        response="stop_switch",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        clerk_name="Omar",
        clerk_gender="boy",
        trait="bold",
        delay=0,
        age=6,
    ),
    StoryParams(
        tool="oscillating_tool",
        clothing="apron_ties",
        response="grab_only",
        child_name="Zoe",
        child_gender="girl",
        parent="mother",
        clerk_name="Gabe",
        clerk_gender="boy",
        trait="curious",
        delay=2,
        age=5,
    ),
    StoryParams(
        tool="jigsaw",
        clothing="big_sleeves",
        response="stop_switch",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        clerk_name="Jade",
        clerk_gender="girl",
        trait="patient",
        delay=0,
        age=4,
    ),
]


def explain_rejection(tool: Tool, clothing: Clothing) -> str:
    if clothing.loose < tool.snag_need:
        return (
            f"(No story: {clothing.phrase} is not loose enough to make an honest warning around a {tool.label}. "
            f"Pick looser clothing such as a scarf, hoodie strings, apron ties, or sleeves that really can wander.)"
        )
    return "(No story: this combination does not create a plausible loose-clothing hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], THE_TOOLS[params.tool], params.delay) else "torn"


ASP_RULES = r"""
hazard(T, C) :- tool(T), clothing(C), snag_need(T, N), loose(C, L), L >= N.
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, C)  :- hazard(T, C).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
authority(C + 1) :- init_caution(C).
averted :- authority(A), curiosity_init(CI), A > CI.

severity(D + Delay) :- chosen_tool(T), danger(T, D), delay(Delay).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(torn) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tool_id, tool in THE_TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("danger", tool_id, tool.danger))
        lines.append(asp.fact("snag_need", tool_id, tool.snag_need))
    for clothing_id, clothing in CLOTHING.items():
        lines.append(asp.fact("clothing", clothing_id))
        lines.append(asp.fact("loose", clothing_id, clothing.loose))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        sink = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = sink
            emit(sample, trace=False, qa=True, header="### smoke test")
        finally:
            sys.stdout = old
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child, loose clothing, and a moving blade in a hardware store."
    )
    ap.add_argument("--tool", choices=THE_TOOLS)
    ap.add_argument("--clothing", choices=CLOTHING)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--clerk-name")
    ap.add_argument("--clerk-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_child(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    if name:
        return name, g
    pool = GIRL_NAMES if g == "girl" else BOY_NAMES
    return rng.choice(pool), g


def _pick_clerk(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    if name:
        return name, g
    pool = CLERK_F if g == "girl" else CLERK_M
    return rng.choice(pool), g


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.clothing:
        tool = THE_TOOLS[args.tool]
        clothing = CLOTHING[args.clothing]
        if not hazard_at_risk(tool, clothing):
            raise StoryError(explain_rejection(tool, clothing))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.tool is None or combo[0] == args.tool)
        and (args.clothing is None or combo[1] == args.clothing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tool_id, clothing_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng, args.gender, args.name)
    clerk_name, clerk_gender = _pick_clerk(rng, args.clerk_gender, args.clerk_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    age = rng.choice([4, 5, 6])
    return StoryParams(
        tool=tool_id,
        clothing=clothing_id,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        clerk_name=clerk_name,
        clerk_gender=clerk_gender,
        trait=trait,
        delay=delay,
        age=age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tool not in THE_TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.clothing not in CLOTHING:
        raise StoryError(f"(Unknown clothing: {params.clothing})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not hazard_at_risk(THE_TOOLS[params.tool], CLOTHING[params.clothing]):
        raise StoryError(explain_rejection(THE_TOOLS[params.tool], CLOTHING[params.clothing]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    clerk_type = "clerk_f" if params.clerk_gender == "girl" else "clerk_m"
    world = tell(
        tool=THE_TOOLS[params.tool],
        clothing=CLOTHING[params.clothing],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_gender,
        parent_type=params.parent,
        clerk_name=params.clerk_name,
        clerk_type=clerk_type,
        trait=params.trait,
        delay=params.delay,
        age=params.age,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tool, clothing) combos:\n")
        for tool, clothing in combos:
            print(f"  {tool:16} {clothing}")
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
            header = f"### {p.child_name}: {p.clothing} near {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
