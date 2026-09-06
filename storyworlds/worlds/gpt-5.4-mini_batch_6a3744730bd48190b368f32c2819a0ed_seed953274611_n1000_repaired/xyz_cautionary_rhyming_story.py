#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/xyz_cautionary_rhyming_story.py
===============================================================

A tiny cautionary rhyming storyworld built from the seed word "xyz".

Premise:
- A child wants to do something playful and mildly risky with letters, lights, or
  a pretend machine.
- A helper notices a problem early, warns them, and they choose a safe fix.
- The story ends with a concrete, changed world state: the risky mess is gone,
  the safe tool is used, and the child remembers the lesson.

This world keeps the prose child-facing and rhythmic, while the simulation tracks
physical meters and emotional memes so the story is driven by state rather than
a frozen template.
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
    scene: str
    setup: str
    goal: str
    rhyme_open: str
    rhyme_close: str
    activity: str
    safe_place: str
    ending_object: str
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
class RiskyItem:
    id: str
    label: str
    phrase: str
    hazard: str
    risky_word: str
    makes_mess: str
    desire: str
    action: str
    consequence: str
    prediction: str
    warning: str
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
class SafeTool:
    id: str
    label: str
    phrase: str
    use: str
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
class Fix:
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
class StoryParams:
    theme: str
    risky: str
    tool: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    turn: str = "pause"
    dialogue: str = "letters"
    ending: str = "display"
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 0.5
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


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


def risky_at_risk(risky: RiskyItem, theme: Theme) -> bool:
    return True if risky.makes_mess else False


def sensible_fix(fid: str) -> bool:
    return FIXES[fid].sense >= SENSE_MIN


def fixs_fire(fix: Fix, risky: RiskyItem) -> bool:
    return fix.power >= 1


def predict(world: World, risky_id: str) -> dict:
    sim = world.copy()
    _do_risky(sim, sim.get(risky_id), narrate=False)
    return {"mess": sim.get(risky_id).meters["mess"], "worry": sum(e.memes["worry"] for e in sim.entities.values())}


def _do_risky(world: World, risky_ent: Entity, narrate: bool = True) -> None:
    risky_ent.meters["mess"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(f"In {theme.scene}, {child.id} and {helper.id} were busy with {theme.activity}. {theme.setup}")
    world.say(f'"{theme.rhyme_open}" sang {child.id}, and {helper.id} joined in.')


def want(world: World, child: Entity, risky: RiskyItem) -> None:
    child.memes["want"] += 1
    world.say(f"{child.id} wanted {risky.desire}.")


def warn(world: World, helper: Entity, child: Entity, risky: RiskyItem) -> None:
    pred = predict(world, "risky")
    helper.memes["care"] += 1
    world.facts["pred_mess"] = pred["mess"]
    world.say(f'{helper.id} pointed to the X and said, "Stop and check. {risky.warning}"')


def causal_turn(world: World, child: Entity, helper: Entity, risky: RiskyItem,
                turn: str, dialogue: str) -> None:
    exchanges = {
        "letters": (
            f'"X means stop, Y means ask why, and Z means choose the safe zone," {helper.id} said.',
            f'"Then XYZ can be our safety code," {child.id} replied.',
        ),
        "prediction": (
            f'"What could happen next?" asked {helper.id}.',
            f'"The {risky.hazard} could spoil our play," {child.id} answered.',
        ),
        "teamwork": (
            f'"Let us solve it together, not race," said {helper.id}.',
            f'"I will pause, and you can help me choose," said {child.id}.',
        ),
        "grownup": (
            f'"This is a grown-up step," {helper.id} reminded {child.id}.',
            f'"I can wait and ask; waiting is part of the plan," {child.id} said.',
        ),
        "quiet": (
            f'{helper.id} tapped X, then Y, then Z without a word.',
            f'{child.id} took a breath. "I remember: stop, think, choose."',
        ),
        "rhyme": (
            f'"X, Y, Z: check before three!" called {helper.id}.',
            f'"Slow can be clever, and safe can be free," answered {child.id}.',
        ),
    }
    first, reply = exchanges[dialogue]
    world.say(first)

    if turn == "small_mishap":
        child.memes["defiance"] += 0.5
        world.say(f"But {child.id} hurried into the first step. {risky.action} {risky.consequence}")
        _do_risky(world, world.get("risky"), narrate=False)
        world.say(f"Seeing the result, {child.id} stopped before the problem could grow.")
    elif turn == "helper_test":
        world.say(f"Instead of guessing, they drew a tiny model on scrap paper in {theme_place(world)}.")
        world.say(f"Their pretend test showed that {risky.prediction}, so {child.id} left the risky step alone.")
    elif turn == "accident_first":
        world.say(f"Before either child touched it, a small accident showed what might happen. {risky.action} {risky.consequence}")
        _do_risky(world, world.get("risky"), narrate=False)
        world.say(f'"That answers why," said {child.id}, moving back at once.')
    elif turn == "self_check":
        world.say(f"{child.id} began to reach, noticed the crooked Z, and froze in time.")
        child.memes["self_control"] += 1
        world.say(f'"If I do that, {risky.prediction}," {child.id} reasoned.')
    elif turn == "countdown":
        world.say(f"They counted backward, Z, Y, X, giving their quick idea time to settle.")
        world.say(f"By X, {child.id} could picture the {risky.hazard} and chose not to cause it.")
    else:
        world.say(f"{child.id} paused at X, asked why at Y, and stepped toward the safe choice at Z.")
        child.memes["self_control"] += 1
    world.say(reply)


def theme_place(world: World) -> str:
    return world.facts["theme"].safe_place


def safe_fix(world: World, parent: Entity, fix: Fix, risky: RiskyItem, tool: SafeTool) -> None:
    body = fix.text.replace("{risky}", risky.label).replace("{tool}", tool.label)
    if world.get("risky").meters["mess"] >= THRESHOLD:
        world.say(f"{parent.label_word.capitalize()} came calmly. {parent.pronoun('subject').capitalize()} {body}.")
    else:
        world.say(f"{parent.label_word.capitalize()} came when the children called and {tool.use}.")
    world.get("risky").meters["mess"] = 0
    world.get("floor").meters["mess"] = 0


def lesson(world: World, parent: Entity, child: Entity, helper: Entity, risky: RiskyItem) -> None:
    for e in (child, helper):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
        e.memes["worry"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} nodded. "You used XYZ well: X to stop, Y to ask why, '
        f'and Z to choose a safe way to try."'
    )


def safe_ending(world: World, child: Entity, helper: Entity, theme: Theme,
                tool: SafeTool, ending: str) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    endings = {
        "display": f"They finished {theme.ending_object} in {theme.safe_place}, with X, Y, and Z standing straight in a row.",
        "sunset": f"When the last stripe of sunlight crossed {theme.ending_object}, the three letters cast a tidy XYZ glow.",
        "teach": f"They taught the XYZ safety rhyme to a younger friend, who practiced it slowly from X through Z.",
        "label": f"Beside {theme.ending_object}, they placed a little card: 'X: stop. Y: ask why. Z: choose safely.'",
        "photo": f"They took a picture of {theme.ending_object}; in it, every letter and every tool sat safely in place.",
        "quiet": f"At cleanup time, {theme.ending_object} remained bright and whole, while the loose pieces rested in {tool.phrase}.",
    }
    world.say(f"{endings[ending]} {theme.rhyme_close}")


def tell(theme: Theme, risky: RiskyItem, tool: SafeTool, fix: Fix,
         child: str = "Milo", child_gender: str = "boy",
         helper: str = "Nia", helper_gender: str = "girl",
         parent: str = "mother", turn: str = "pause",
         dialogue: str = "letters", ending: str = "display") -> World:
    world = World()
    c = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    p = world.add(Entity(id="Parent", kind="character", type=parent, role="parent"))
    world.add(Entity(id="risky", label=risky.label))
    world.add(Entity(id="floor", label="the floor"))
    world.facts.update(tool=tool, fix=fix, risky=risky, theme=theme, child=c, helper=h, parent=p)

    open_scene(world, c, h, theme)
    world.para()
    want(world, c, risky)
    warn(world, h, c, risky)
    world.para()
    causal_turn(world, c, h, risky, turn, dialogue)
    world.para()
    safe_fix(world, p, fix, risky, tool)
    lesson(world, p, c, h, risky)
    world.para()
    safe_ending(world, c, h, theme, tool, ending)

    world.facts["outcome"] = "safe"
    world.facts["turn"] = turn
    world.facts["ending"] = ending
    return world


THEMES = {
    "xyz": Theme(
        id="xyz",
        scene="a cozy corner with paper stars and bright chalk swirls",
        setup="Three painted sticks marked X, Y, and Z for an alphabet path.",
        goal="build an alphabet path",
        rhyme_open="X marks the start, Y bends, Z zips to the end!",
        rhyme_close="Their careful alphabet path was ready to show.",
        activity="an XYZ alphabet path",
        safe_place="the wide craft mat",
        ending_object="the zigzag alphabet path",
    ),
    "shadow": Theme(
        id="shadow",
        scene="a blanket fort where the wall made a silver screen",
        setup="Clear cards shaped like X, Y, and Z waited beside a small lamp.",
        goal="make letter shadows",
        rhyme_open="X crosses, Y forks, and Z flashes bright!",
        rhyme_close="Three gentle shadows danced in the light.",
        activity="an XYZ shadow show",
        safe_place="the low table",
        ending_object="the glowing letter screen",
    ),
    "parade": Theme(
        id="parade",
        scene="the playroom before an alphabet parade",
        setup="A paper banner needed one last row: X, Y, Z.",
        goal="finish the parade banner",
        rhyme_open="Wave X, cheer Y, let Z bring the song!",
        rhyme_close="The bright little banner streamed safely along.",
        activity="an XYZ parade banner",
        safe_place="the carpet work square",
        ending_object="the finished parade banner",
    ),
    "garden": Theme(
        id="garden",
        scene="a sunny potting shed beside three seedling pots",
        setup="The pots needed weatherproof markers for X, Y, and Zinnias.",
        goal="label the seedling pots",
        rhyme_open="X for the box, Y for why, Z for zinnia sky!",
        rhyme_close="The labeled green shoots nodded nearby.",
        activity="XYZ garden markers",
        safe_place="the low potting bench",
        ending_object="the row of labeled seedlings",
    ),
    "map": Theme(
        id="map",
        scene="a quiet courtyard drawn with chalk roads",
        setup="Their treasure route ran from X to Y and ended at Z.",
        goal="complete the treasure route",
        rhyme_open="Start at X, turn at Y, find Z by and by!",
        rhyme_close="Their safe chalk treasure trail curled under the sky.",
        activity="an XYZ treasure map",
        safe_place="the courtyard play square",
        ending_object="the completed chalk map",
    ),
}

RISKIES = {
    "xyz": RiskyItem(
        id="xyz",
        label="XYZ sticks",
        phrase="the XYZ sticks",
        hazard="messy scatter",
        risky_word="a little clang-and-clatter",
        makes_mess="mess",
        desire="to roll all three XYZ sticks down a steep book ramp at once",
        action="The wobbling ramp tipped.",
        consequence="The sticks clattered across the walking path.",
        prediction="the sticks could clatter across the walking path",
        warning="A loose stick could roll under someone's foot.",
        tags={"xyz", "letters"},
    ),
    "shadow": RiskyItem(
        id="shadow", label="XYZ shadow cards", phrase="the XYZ shadow cards",
        hazard="hot, tangled lamp area", risky_word="a warm wobble", makes_mess="tangle",
        desire="to balance the XYZ cards directly on the warm lamp",
        action="One card softened and slipped.",
        consequence="The card fell beside the warm lamp and tugged its cord.",
        prediction="a card could fall beside the warm lamp and tug its cord",
        warning="Cards and fingers need space from a warm lamp and its cord.",
        tags={"xyz", "light"},
    ),
    "parade": RiskyItem(
        id="parade", label="XYZ banner letters", phrase="the XYZ banner letters",
        hazard="sliding chair", risky_word="a scrape and sway", makes_mess="scatter",
        desire="to stand on a rolling chair and pin the Z high above the banner",
        action="The chair rolled a little under one hand.",
        consequence="The Z fluttered down while the chair slid away.",
        prediction="the chair could slide and the Z could tumble down",
        warning="A rolling chair is not a safe step for reaching high.",
        tags={"xyz", "banner"},
    ),
    "garden": RiskyItem(
        id="garden", label="XYZ garden markers", phrase="the XYZ garden markers",
        hazard="sharp garden snips", risky_word="a sudden snip", makes_mess="spill",
        desire="to use the grown-up garden snips to sharpen the Z marker",
        action="The stiff handles sprang open.",
        consequence="The marker jumped away and knocked soil from a pot.",
        prediction="the marker could jump and knock over the soil",
        warning="Those snips are sharp and sized for grown-up hands.",
        tags={"xyz", "garden"},
    ),
    "map": RiskyItem(
        id="map", label="XYZ chalk markers", phrase="the XYZ chalk markers",
        hazard="busy driveway edge", risky_word="a quick wheel rumble", makes_mess="scatter",
        desire="to place the Z beyond the courtyard boundary near the driveway",
        action="A delivery cart rumbled past the far edge.",
        consequence="Its breeze scattered the chalk before anyone crossed the line.",
        prediction="a passing cart could scatter the chalk near the driveway",
        warning="The map must stay inside the courtyard play square.",
        tags={"xyz", "map"},
    ),
}

TOOLS = {
    "tray": SafeTool(
        id="tray",
        label="a tray",
        phrase="a tray",
        use="set the tray beneath the ramp and kept the sticks from skidding away",
        tags={"tray"},
    ),
    "stand": SafeTool(id="stand", label="a cool clamp stand", phrase="the cool clamp stand",
                      use="fixed the lamp low and held each card far from the bulb", tags={"light"}),
    "stool": SafeTool(id="stool", label="a steady step stool", phrase="the steady step stool",
                      use="held the stool while the children attached the letters from below", tags={"banner"}),
    "scissors": SafeTool(id="scissors", label="child-safe scissors", phrase="the child-safe scissors",
                         use="trimmed fresh markers while the sharp snips stayed latched away", tags={"garden"}),
    "cones": SafeTool(id="cones", label="small safety cones", phrase="the small safety cones",
                      use="marked a clear boundary and moved Z back inside the play square", tags={"map"}),
}

FIXES = {
    "scoop": Fix(
        id="scoop",
        sense=3,
        power=3,
        text="gathered the {risky}, set them on {tool}, and steadied the game",
        fail="tried to scoop up the {risky}, but the mess kept growing anyway",
        qa_text="scooped up the {risky} and set them on a {tool}",
        tags={"cleanup"},
    ),
    "cool": Fix(id="cool", sense=3, power=3,
                text="unplugged the lamp, let it cool, and secured the {risky} with {tool}",
                fail="moved the warm lamp without unplugging it", qa_text="cooled and secured the lamp",
                tags={"light"}),
    "lower": Fix(id="lower", sense=3, power=3,
                 text="moved the banner lower and set {tool} on a flat spot for the {risky}",
                 fail="chased the rolling chair", qa_text="lowered the banner and used a steady stool",
                 tags={"banner"}),
    "swap": Fix(id="swap", sense=3, power=3,
                text="latched the sharp snips away and brought {tool} for the {risky}",
                fail="left the sharp snips open", qa_text="put away the sharp snips and brought safe scissors",
                tags={"garden"}),
    "boundary": Fix(id="boundary", sense=3, power=3,
                    text="gathered the chalk and used {tool} to keep the {risky} inside the courtyard",
                    fail="followed the chalk beyond the boundary", qa_text="marked a safe courtyard boundary",
                    tags={"map"}),
}

SCENARIOS = {
    "xyz": ("xyz", "tray", "scoop"),
    "shadow": ("shadow", "stand", "cool"),
    "parade": ("parade", "stool", "lower"),
    "garden": ("garden", "scissors", "swap"),
    "map": ("map", "cones", "boundary"),
}

TURNS = ["pause", "small_mishap", "helper_test", "accident_first", "self_check", "countdown"]
DIALOGUES = ["letters", "prediction", "teamwork", "grownup", "quiet", "rhyme"]
ENDINGS = ["display", "sunset", "teach", "label", "photo", "quiet"]

GIRL_NAMES = ["Nia", "Mia", "Zoe", "Ava", "Luna"]
BOY_NAMES = ["Milo", "Leo", "Noah", "Theo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(theme, risky, tool) for theme, (risky, tool, _fix) in SCENARIOS.items()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary rhyming storyworld with xyz.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--risky", choices=RISKIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--dialogue", choices=DIALOGUES)
    ap.add_argument("--ending", choices=ENDINGS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and not sensible_fix(args.fix):
        raise StoryError("unsafe fix")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.risky is None or c[1] == args.risky)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, risky, tool = rng.choice(sorted(combos))
    scenario_fix = SCENARIOS[theme][2]
    if args.fix is not None and args.fix != scenario_fix:
        raise StoryError(f"{args.fix} is not a safe fix for the {theme} scenario")
    fix = args.fix or scenario_fix
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_names = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    helper = args.helper or rng.choice([n for n in helper_names if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    turn = args.turn or rng.choice(TURNS)
    dialogue = args.dialogue or rng.choice(DIALOGUES)
    ending = args.ending or rng.choice(ENDINGS)
    return StoryParams(theme=theme, risky=risky, tool=tool, fix=fix,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, parent=parent,
                       turn=turn, dialogue=dialogue, ending=ending)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short cautionary rhyming story that includes "xyz".',
        f"Tell a rhyming story where {f['child'].id} and {f['helper'].id} worry about {f['risky'].label} but choose a safe fix.",
        "Make the ending gentle, with a lesson and a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    risky: RiskyItem = f["risky"]
    fix: Fix = f["fix"]
    tool: SafeTool = f["tool"]
    return [
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted {risky.desire}. It sounded exciting, but {risky.warning[0].lower() + risky.warning[1:]}",
        ),
        QAItem(
            question="How did the helper keep things safe?",
            answer=f"{helper.id} warned {child.id} and helped {child.id} stop, ask why, and choose safely. Then the grown-up {tool.use}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely: {world.facts['theme'].ending_object} was complete. The risky step was abandoned, and the children remembered their XYZ safety code.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Why was {f['tool'].phrase} useful?",
            answer=f"It was useful because the grown-up {f['tool'].use}. That directly removed the danger in the children's first plan.",
        ),
        QAItem(
            question="Why is it good to listen to warnings?",
            answer="Warnings can keep a small problem from growing into a bigger one. Listening early helps everyone stay safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    return "\n".join(out)


ASP_RULES = r"""
valid(T, R, U) :- scenario(T, R, U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid, rid, uid in valid_combos():
        lines.append(asp.fact("scenario", tid, rid, uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(THEMES[params.theme], RISKIES[params.risky], TOOLS[params.tool], FIXES[params.fix],
                     params.child, params.child_gender, params.helper, params.helper_gender, params.parent,
                     params.turn, params.dialogue, params.ending)
    except KeyError as err:
        raise StoryError(f"invalid parameter: {err}") from err
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(theme="xyz", risky="xyz", tool="tray", fix="scoop", child="Milo", child_gender="boy",
                helper="Nia", helper_gender="girl", parent="mother"),
    StoryParams(theme="xyz", risky="xyz", tool="tray", fix="scoop", child="Luna", child_gender="girl",
                helper="Theo", helper_gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        seen_shapes: set[tuple[str, str, str, str]] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            shape = (params.theme, params.turn, params.dialogue, params.ending)
            use_shape_guard = not (args.theme and args.turn and args.dialogue and args.ending)
            if sample.story not in seen and (not use_shape_guard or shape not in seen_shapes):
                seen.add(sample.story)
                seen_shapes.add(shape)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
