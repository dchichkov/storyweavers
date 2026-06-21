#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py
================================================================================================

A standalone story world for a tiny rhyming tale about two children making a
small decoration, a meddlesome interruption, a brief hurt between friends, a
flashback that softens the heart, and a repaired ending with reconciliation.

The world rebuilds a simple source premise in a state-driven way:

- two children make something cheerful together
- a meddlesome force or animal gives an early warning sign (foreshadowing)
- the decoration is disturbed
- one child blames the other and feelings are hurt
- a remembered earlier kindness returns in a flashback
- the apology and repair are grounded in the world's state
- the final image proves they are together again

Run it
------
    python storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py --decoration paper_chain --meddler breeze
    python storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py --meddler breeze --decoration pinwheel_row
    python storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/meddlesome_foreshadowing_reconciliation_flashback_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Decoration:
    id: str
    label: str
    phrase: str
    display: str
    material: str
    fragile: bool
    light: bool
    shiny: bool
    low: bool
    opening: str
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
class Meddler:
    id: str
    label: str
    phrase: str
    kind: str
    bothers_display: set[str]
    needs_low: bool = False
    likes_light: bool = False
    rhyme_warning: str = ""
    rhyme_trouble: str = ""
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
    label: str
    phrase: str
    protects_display: set[str]
    against: set[str]
    needs_low: Optional[bool] = None
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


@dataclass
class Memory:
    id: str
    prompt: str
    scene: str
    lesson: str
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


def meddler_can_bother(meddler: Meddler, decoration: Decoration) -> bool:
    if decoration.display not in meddler.bothers_display:
        return False
    if meddler.needs_low and not decoration.low:
        return False
    if meddler.likes_light and not decoration.light:
        return False
    return True


def fix_works(fix: Fix, meddler: Meddler, decoration: Decoration) -> bool:
    if meddler.id not in fix.against:
        return False
    if decoration.display not in fix.protects_display:
        return False
    if fix.needs_low is not None and fix.needs_low != decoration.low:
        return False
    return True


def select_fix(meddler: Meddler, decoration: Decoration) -> Optional[Fix]:
    for fix in FIXES.values():
        if fix_works(fix, meddler, decoration):
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dec_id, decoration in DECORATIONS.items():
        for med_id, meddler in MEDDLERS.items():
            if not meddler_can_bother(meddler, decoration):
                continue
            fix = select_fix(meddler, decoration)
            if fix is None:
                continue
            combos.append((dec_id, med_id, fix.id))
    return sorted(combos)


def _r_trouble(world: World) -> list[str]:
    decoration = world.get("decoration")
    meddler = world.get("meddler")
    if decoration.meters["loose"] < THRESHOLD or meddler.meters["reached"] < THRESHOLD:
        return []
    sig = ("trouble", decoration.id, meddler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    decoration.meters["tangled"] += 1
    decoration.meters["ruined"] += 1
    decoration.meters["loose"] = 0.0
    world.get("child1").memes["alarm"] += 1
    world.get("child2").memes["alarm"] += 1
    return ["__trouble__"]


def _r_hurt(world: World) -> list[str]:
    blamer = world.get("child1")
    friend = world.get("child2")
    if blamer.memes["blame"] < THRESHOLD:
        return []
    sig = ("hurt", blamer.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    world.get("bond").meters["distance"] += 1
    return ["__hurt__"]


def _r_reconcile(world: World) -> list[str]:
    child1 = world.get("child1")
    child2 = world.get("child2")
    if child1.memes["sorry"] < THRESHOLD or child2.memes["forgiven"] < THRESHOLD:
        return []
    sig = ("reconcile", child1.id, child2.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("bond").meters["distance"] = 0.0
    child1.memes["peace"] += 1
    child2.memes["peace"] += 1
    return ["__peace__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble", tag="physical", apply=_r_trouble),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


def opening_scene(world: World, child1: Entity, child2: Entity, decoration: Decoration) -> None:
    child1.memes["joy"] += 1
    child2.memes["joy"] += 1
    world.say(
        f"By the garden gate in the gold afternoon, {child1.id} and {child2.id} "
        f"worked with a hum and a happy small tune."
    )
    world.say(
        f"They were making {decoration.phrase}, {decoration.opening}, and both of "
        f"them hoped it would shine before supper time."
    )


def foreshadow(world: World, child1: Entity, child2: Entity, meddler: Meddler, decoration: Decoration) -> None:
    world.facts["foreshadowed"] = True
    if meddler.kind == "wind":
        world.say(
            f"But {meddler.rhyme_warning} The children both laughed, yet the fluttering air "
            f"felt a little too busy and a little too near."
        )
    else:
        world.say(
            f"Not far from the path stood {meddler.phrase}, so still and so sly. "
            f"{meddler.rhyme_warning}"
        )
    if decoration.low:
        world.say(
            f"{child2.id} noticed the loops hanging low. \"Let's finish soon,\" "
            f"{child2.pronoun()} said softly. \"They wobble below.\""
        )
    else:
        world.say(
            f"The work was not finished; one part still swung free. That tiny loose place "
            f"was a sign of what soon came to be."
        )


def meddle(world: World, meddler: Meddler) -> None:
    world.get("meddler").meters["reached"] += 1
    produced = propagate(world, narrate=False)
    world.facts["trouble_markers"] = list(produced)


def trouble_scene(world: World, child1: Entity, child2: Entity, meddler: Meddler, decoration: Decoration) -> None:
    meddle(world, meddler)
    if decoration.display == "hanging":
        world.say(
            f"Then {meddler.rhyme_trouble} The loops gave a hop, then a twist, then a tear, "
            f"and the bright little work would not hang as before there."
        )
    else:
        world.say(
            f"Then {meddler.rhyme_trouble} The row tipped askew with a rustle and cheer, "
            f"and one little wheel lay bent over and queer."
        )
    world.say(
        f"{child1.id} gasped, and {child2.id} stood still as a stone. For one startled blink, "
        f"each felt suddenly lonely, though neither alone."
    )


def blame_scene(world: World, child1: Entity, child2: Entity, decoration: Decoration) -> None:
    child1.memes["blame"] += 1
    propagate(world, narrate=False)
    if decoration.low:
        line = f'"You tied it too low," said {child1.id}, with a pinch in {child1.pronoun("possessive")} tone.'
    else:
        line = f'"You left one part loose," said {child1.id}, in a voice not at all like {child1.pronoun("possessive")} own.'
    world.say(line)
    world.say(
        f"{child2.id}'s smile folded shut. {child2.pronoun().capitalize()} looked at the ground, "
        f"and the sunny warm garden seemed suddenly gray all around."
    )


def flashback_scene(world: World, child1: Entity, child2: Entity, memory: Memory) -> None:
    child1.memes["remembering"] += 1
    child1.memes["warmth"] += 1
    child1.memes["blame"] = 0.0
    world.say(
        f"Then into {child1.id}'s mind came a soft backward track, a little flashback."
    )
    world.say(
        f"{memory.scene} {memory.lesson}"
    )
    world.say(
        f"That memory loosened the knot in {child1.id}'s chest. What had felt sharp now felt smaller, "
        f"and kindness felt best."
    )


def apology_scene(world: World, child1: Entity, child2: Entity) -> None:
    child1.memes["sorry"] += 1
    child2.memes["forgiven"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry," said {child1.id}. "I spoke in a storm. The trouble was sudden, '
        f'but blaming was not kind or warm."'
    )
    world.say(
        f'{child2.id} gave a slow nod. "{child1.id}, I felt sad when you said that. '
        f'But we can still mend it. I know we can do that."'
    )


def repair_scene(world: World, child1: Entity, child2: Entity, decoration: Decoration, fix: Fix) -> None:
    decoration_ent = world.get("decoration")
    decoration_ent.meters["ruined"] = 0.0
    decoration_ent.meters["repaired"] += 1
    decoration_ent.meters["secure"] += 1
    child1.memes["hope"] += 1
    child2.memes["hope"] += 1
    world.say(
        f"So side by side, with steadier hands and a kinder pace, they used {fix.phrase}. "
        f"{fix.action}"
    )


def ending_scene(world: World, child1: Entity, child2: Entity, decoration: Decoration, meddler: Meddler, fix: Fix) -> None:
    child1.memes["joy"] += 1
    child2.memes["joy"] += 1
    child1.memes["trust"] += 1
    child2.memes["trust"] += 1
    world.say(
        f"Soon {decoration.phrase} looked bright once more. {fix.ending}"
    )
    if meddler.kind == "wind":
        world.say(
            f"Even the breeze seemed gentler then, only humming along while the two good friends "
            f"smiled and sang their making-again song."
        )
    else:
        world.say(
            f"Even the meddlesome {meddler.label} lost interest at last, and the garden grew peaceful "
            f"and golden and vast."
        )
    world.say(
        f"Then {child1.id} and {child2.id} shared the last bit of thread and a giggle instead of a grumble, "
        f"and that was how hurt turned to friendship and trouble turned humble."
    )


DECORATIONS = {
    "paper_chain": Decoration(
        id="paper_chain",
        label="paper chain",
        phrase="a paper chain of peach, blue, and green",
        display="hanging",
        material="paper",
        fragile=True,
        light=True,
        shiny=False,
        low=True,
        opening="loop by loop, link by link, neat and clean",
        tags={"paper_chain", "hanging", "craft"},
    ),
    "flower_garland": Decoration(
        id="flower_garland",
        label="flower garland",
        phrase="a flower garland of daisies and clover",
        display="hanging",
        material="flowers",
        fragile=True,
        light=True,
        shiny=False,
        low=True,
        opening="petal by petal, to drape on the arbor",
        tags={"flowers", "hanging", "craft"},
    ),
    "pinwheel_row": Decoration(
        id="pinwheel_row",
        label="pinwheel row",
        phrase="a row of bright pinwheels by the beans",
        display="ground",
        material="paper",
        fragile=True,
        light=False,
        shiny=False,
        low=True,
        opening="wheel by wheel, to dance in the garden greens",
        tags={"pinwheel", "ground", "craft"},
    ),
}

MEDDLERS = {
    "breeze": Meddler(
        id="breeze",
        label="breeze",
        phrase="a meddlesome breeze",
        kind="wind",
        bothers_display={"hanging"},
        needs_low=False,
        likes_light=True,
        rhyme_warning="A meddlesome breeze kept teasing the tails with a flap and a flick and a fluttering sail.",
        rhyme_trouble="the meddlesome breeze skipped over the gate and tugged at the links with a hurried little skate",
        tags={"wind", "weather"},
    ),
    "puppy": Meddler(
        id="puppy",
        label="puppy",
        phrase="a meddlesome puppy with velvety ears",
        kind="animal",
        bothers_display={"hanging", "ground"},
        needs_low=True,
        likes_light=False,
        rhyme_warning="Its nose gave a wiggle, its paws gave a prance, as if it were measuring ribbon for one playful dance.",
        rhyme_trouble="the meddlesome puppy bounced in for a sniff and batted the loops with a yip and a whiff",
        tags={"puppy", "pet"},
    ),
    "goat": Meddler(
        id="goat",
        label="goat",
        phrase="a meddlesome goat with a nibbling chin",
        kind="animal",
        bothers_display={"hanging", "ground"},
        needs_low=True,
        likes_light=False,
        rhyme_warning="It blinked through the fence with a munch-munch stare, as if any dangling thing might soon become fare.",
        rhyme_trouble="the meddlesome goat poked over the rail and nibbled the edge with a tug and a tail-swishy swale",
        tags={"goat", "animal"},
    ),
}

FIXES = {
    "clothespins": Fix(
        id="clothespins",
        label="clothespins",
        phrase="two striped clothespins",
        protects_display={"hanging"},
        against={"breeze"},
        needs_low=None,
        action="They clipped each swinging end snug to the string, so the loose little loops could not leap or take wing.",
        ending="The links only swayed with a soft settled spin, neat in the sunlight and safe in the wind.",
        tags={"clothespins", "repair"},
    ),
    "high_branch": Fix(
        id="high_branch",
        label="high branch",
        phrase="a taller branch and one stronger knot",
        protects_display={"hanging"},
        against={"puppy", "goat"},
        needs_low=True,
        action="They lifted the work where nibbling mouths and nosy paws could not reach, then tied it firm and high over the peach.",
        ending="Now it hung up high where small trouble could not start, bright over their heads like a banner of heart.",
        tags={"knot", "repair"},
    ),
    "border_stakes": Fix(
        id="border_stakes",
        label="border stakes",
        phrase="a ring of little border stakes",
        protects_display={"ground"},
        against={"puppy", "goat"},
        needs_low=True,
        action="They set a tiny border around the row and pressed each pinwheel straight, so bouncy feet and nibbling noses would have to wait.",
        ending="The small wheels stood safely behind their neat ring, ready for evening's slow twirl and sing.",
        tags={"stakes", "repair"},
    ),
}

MEMORIES = {
    "bandage": Memory(
        id="bandage",
        prompt="bandage",
        scene="Yesterday, when a thorn had pricked {friend}, {child} had been the first to fetch a bandage and sit nearby until the sting went slack.",
        lesson="Back then, they had worked like one team with one plan, and remembering that moment softened {child}'s heart again.",
        tags={"kindness", "help"},
    ),
    "crayons": Memory(
        id="crayons",
        prompt="crayons",
        scene="Last week, when the red crayon snapped, {friend} had quietly shared the brightest one without a fuss and slid the whole box back.",
        lesson="That small sharing glow had been gentle and true, and now it returned like warm light through blue.",
        tags={"sharing", "kindness"},
    ),
    "umbrella": Memory(
        id="umbrella",
        prompt="umbrella",
        scene="On the rainy walk home, {friend} had tilted the umbrella wide so both of them fit, even when the puddles were deep and black.",
        lesson="The remembered dry shoulder and careful small grin made room for an apology to begin.",
        tags={"care", "friendship"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Jo", "Ben", "Max", "Leo", "Finn", "Eli"]
TRAITS = ["careful", "cheerful", "patient", "thoughtful", "busy", "gentle"]


@dataclass
class StoryParams:
    decoration: str
    meddler: str
    fix: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    memory: str
    child1_trait: str = "thoughtful"
    child2_trait: str = "gentle"
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


def explain_rejection(decoration: Decoration, meddler: Meddler) -> str:
    if decoration.display not in meddler.bothers_display:
        return (
            f"(No story: {meddler.label} does not plausibly ruin a {decoration.label} in this world. "
            f"That combination would not create an honest interruption to repair.)"
        )
    if meddler.needs_low and not decoration.low:
        return (
            f"(No story: {meddler.label} only troubles decorations hanging or standing low enough to reach. "
            f"This {decoration.label} would be out of reach.)"
        )
    if meddler.likes_light and not decoration.light:
        return (
            f"(No story: the {meddler.label} in this world only whips up light dangling things. "
            f"This {decoration.label} is not a good fit for that trouble.)"
        )
    return "(No story: this combination has no fitting repair in the world.)"


def explain_fix(fix_id: str, decoration: Decoration, meddler: Meddler) -> str:
    fix = FIXES[fix_id]
    return (
        f"(Refusing fix '{fix_id}': {fix.label} is not the sensible repair for a "
        f"{meddler.label} bothering a {decoration.label}. Pick the repair that actually "
        f"secures this kind of trouble.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a small craft, a meddlesome interruption, "
        "a flashback, and reconciliation."
    )
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--meddler", choices=MEDDLERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.decoration and args.meddler:
        decoration = DECORATIONS[args.decoration]
        meddler = MEDDLERS[args.meddler]
        if not meddler_can_bother(meddler, decoration):
            raise StoryError(explain_rejection(decoration, meddler))
        if args.fix and not fix_works(FIXES[args.fix], meddler, decoration):
            raise StoryError(explain_fix(args.fix, decoration, meddler))
    if args.fix and (not args.decoration or not args.meddler):
        possible = [combo for combo in valid_combos() if combo[2] == args.fix]
        if not possible:
            raise StoryError("(No valid story uses the requested fix.)")

    combos = [
        combo for combo in valid_combos()
        if (args.decoration is None or combo[0] == args.decoration)
        and (args.meddler is None or combo[1] == args.meddler)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    decoration_id, meddler_id, fix_id = rng.choice(combos)
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    memory = args.memory or rng.choice(sorted(MEMORIES))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        decoration=decoration_id,
        meddler=meddler_id,
        fix=fix_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        parent=parent,
        memory=memory,
        child1_trait=rng.choice(TRAITS),
        child2_trait=rng.choice(TRAITS),
    )


def tell(
    decoration: Decoration,
    meddler: Meddler,
    fix: Fix,
    memory: Memory,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    parent_type: str,
    child1_trait: str,
    child2_trait: str,
) -> World:
    world = World()
    child1 = world.add(
        Entity(
            id=child1_name,
            kind="character",
            type=child1_gender,
            role="blamer",
            traits=[child1_trait],
            attrs={},
        )
    )
    child2 = world.add(
        Entity(
            id=child2_name,
            kind="character",
            type=child2_gender,
            role="friend",
            traits=[child2_trait],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    decoration_ent = world.add(
        Entity(
            id="decoration",
            kind="thing",
            type="decoration",
            label=decoration.label,
            attrs={
                "display": decoration.display,
                "material": decoration.material,
                "fragile": decoration.fragile,
            },
        )
    )
    meddler_ent = world.add(
        Entity(
            id="meddler",
            kind="thing",
            type=meddler.kind,
            label=meddler.label,
            attrs={"kind": meddler.kind},
        )
    )
    bond = world.add(
        Entity(
            id="bond",
            kind="thing",
            type="friendship",
            label="their friendship",
            attrs={},
        )
    )

    child1.memes["joy"] = 0.0
    child2.memes["joy"] = 0.0
    child1.memes["blame"] = 0.0
    child2.memes["hurt"] = 0.0
    child1.memes["sorry"] = 0.0
    child2.memes["forgiven"] = 0.0
    child1.memes["warmth"] = 0.0
    decoration_ent.meters["loose"] = 1.0
    decoration_ent.meters["tangled"] = 0.0
    decoration_ent.meters["ruined"] = 0.0
    decoration_ent.meters["secure"] = 0.0
    decoration_ent.meters["repaired"] = 0.0
    meddler_ent.meters["reached"] = 0.0
    bond.meters["distance"] = 0.0
    world.facts["foreshadowed"] = False
    world.facts["trouble_markers"] = []

    opening_scene(world, child1, child2, decoration)
    world.para()
    foreshadow(world, child1, child2, meddler, decoration)
    world.para()
    trouble_scene(world, child1, child2, meddler, decoration)
    blame_scene(world, child1, child2, decoration)
    world.para()
    memory_text = Memory(
        id=memory.id,
        prompt=memory.prompt,
        scene=memory.scene.format(child=child1.id, friend=child2.id),
        lesson=memory.lesson.format(child=child1.id, friend=child2.id),
        tags=set(memory.tags),
    )
    flashback_scene(world, child1, child2, memory_text)
    apology_scene(world, child1, child2)
    world.para()
    repair_scene(world, child1, child2, decoration, fix)
    ending_scene(world, child1, child2, decoration, meddler, fix)

    world.facts.update(
        child1=child1,
        child2=child2,
        parent=parent,
        decoration_cfg=decoration,
        meddler_cfg=meddler,
        fix_cfg=fix,
        memory_cfg=memory,
        decoration=decoration_ent,
        meddler=meddler_ent,
        bond=bond,
        reconciled=bond.meters["distance"] < THRESHOLD and child1.memes["peace"] >= THRESHOLD,
        hurt=child2.memes["hurt"] >= THRESHOLD,
        repaired=decoration_ent.meters["repaired"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child1 = world.facts["child1"]
    child2 = world.facts["child2"]
    decoration = world.facts["decoration_cfg"]
    meddler = world.facts["meddler_cfg"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "meddlesome" and uses foreshadowing, a flashback, and reconciliation.',
        f"Tell a rhyming garden story where {child1.id} and {child2.id} make {decoration.phrase}, a meddlesome {meddler.label} causes trouble, and the children make peace.",
        f"Write a gentle story in rhyme where a small craft is disturbed, one child says something unkind, a remembered kindness changes the moment, and the ending proves the friendship is mended.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child1 = world.facts["child1"]
    child2 = world.facts["child2"]
    decoration = world.facts["decoration_cfg"]
    meddler = world.facts["meddler_cfg"]
    fix = world.facts["fix_cfg"]
    memory = world.facts["memory_cfg"]
    parent = world.facts["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child1.id} and {child2.id}, two children working together in the garden. "
            f"Their {parent.label_word} is in the background, but the heart of the story is how the two children lose and mend their friendship."
        ),
        (
            f"What were {child1.id} and {child2.id} making?",
            f"They were making {decoration.phrase}. The decoration mattered because they both wanted it to look lovely before supper."
        ),
        (
            "What was the foreshadowing in the story?",
            f"The early warning was that {meddler.phrase} was already acting interested before the accident happened. "
            f"That small warning hinted that the cheerful making time might soon turn into trouble."
        ),
        (
            f"Why did {child2.id} feel hurt?",
            f"{child2.id} felt hurt because {child1.id} blamed {child2.pronoun('object')} right after the decoration was disturbed. "
            f"The trouble had been sudden, but the blaming words made the happy mood collapse."
        ),
        (
            "What was the flashback, and why did it matter?",
            f"The flashback was a memory about {memory.prompt}: {child1.id} remembered an earlier kind moment with {child2.id}. "
            f"That memory softened {child1.pronoun('possessive')} feelings and helped {child1.pronoun('object')} see that kindness mattered more than winning the argument."
        ),
        (
            "How did the children reconcile?",
            f"{child1.id} apologized, and {child2.id} answered honestly instead of staying silent. "
            f"Then they repaired the decoration together with {fix.phrase}, so the making and the friendship were both mended."
        ),
    ]
    return qa


KNOWLEDGE = {
    "wind": [
        (
            "What can wind do to light hanging decorations?",
            "Wind can tug and twist light things that hang loose. If they are not clipped or tied well, the wind may tangle or tear them."
        )
    ],
    "puppy": [
        (
            "Why might a puppy bother a craft?",
            "A puppy explores with its nose and paws, so ribbons and spinning things can feel like toys. That is why crafts should be kept out of a puppy's reach."
        )
    ],
    "goat": [
        (
            "Why do goats nibble dangling things?",
            "Goats like to investigate with their mouths, especially if something looks leafy or easy to tug. A dangling decoration can seem like a snack or a game to them."
        )
    ],
    "clothespins": [
        (
            "What do clothespins do?",
            "Clothespins hold light things in place by squeezing them gently. They are useful when you want paper or cloth to stay put in a breeze."
        )
    ],
    "knot": [
        (
            "Why does tying something higher help?",
            "Putting a decoration higher can keep it away from paws and mouths. A stronger knot also stops it from slipping back down."
        )
    ],
    "stakes": [
        (
            "What are little border stakes for?",
            "Little border stakes can mark a small space and help protect what is inside it. They make it easier for children and animals to notice where not to step."
        )
    ],
    "kindness": [
        (
            "How can remembering kindness help after an argument?",
            "Remembering a kind thing can calm angry feelings and make people want to listen again. It helps them see each other as friends instead of enemies."
        )
    ],
    "friendship": [
        (
            "What is reconciliation?",
            "Reconciliation is when people who felt hurt talk, apologize, and come back together in peace. It does not erase the mistake, but it repairs the relationship."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. Writers use it to explain feelings or show why a character changes."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a clue that hints something important may happen later. It helps a story feel connected from beginning to middle."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "foreshadowing",
    "flashback",
    "friendship",
    "kindness",
    "wind",
    "puppy",
    "goat",
    "clothespins",
    "knot",
    "stakes",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"foreshadowing", "flashback", "friendship", "kindness"}
    tags |= set(world.facts["meddler_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
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


def generate(params: StoryParams) -> StorySample:
    if params.decoration not in DECORATIONS:
        raise StoryError(f"(Unknown decoration: {params.decoration})")
    if params.meddler not in MEDDLERS:
        raise StoryError(f"(Unknown meddler: {params.meddler})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")

    decoration = DECORATIONS[params.decoration]
    meddler = MEDDLERS[params.meddler]
    fix = FIXES[params.fix]

    if not meddler_can_bother(meddler, decoration):
        raise StoryError(explain_rejection(decoration, meddler))
    if not fix_works(fix, meddler, decoration):
        raise StoryError(explain_fix(params.fix, decoration, meddler))

    world = tell(
        decoration=decoration,
        meddler=meddler,
        fix=fix,
        memory=MEMORIES[params.memory],
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        child1_trait=params.child1_trait,
        child2_trait=params.child2_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in (None, "", [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        decoration="paper_chain",
        meddler="breeze",
        fix="clothespins",
        child1="Mina",
        child1_gender="girl",
        child2="Jo",
        child2_gender="boy",
        parent="mother",
        memory="umbrella",
        child1_trait="thoughtful",
        child2_trait="gentle",
    ),
    StoryParams(
        decoration="flower_garland",
        meddler="goat",
        fix="high_branch",
        child1="Ben",
        child1_gender="boy",
        child2="Ava",
        child2_gender="girl",
        parent="father",
        memory="bandage",
        child1_trait="busy",
        child2_trait="patient",
    ),
    StoryParams(
        decoration="pinwheel_row",
        meddler="puppy",
        fix="border_stakes",
        child1="Nora",
        child1_gender="girl",
        child2="Leo",
        child2_gender="boy",
        parent="mother",
        memory="crayons",
        child1_trait="careful",
        child2_trait="cheerful",
    ),
]


ASP_RULES = r"""
% a meddler can bother a decoration when the display type fits and any further
% constraints (low enough, light enough) also fit
can_bother(M, D) :- meddler(M), decoration(D), bothers(M, Disp), display(D, Disp),
                    not needs_low(M), not likes_light(M).
can_bother(M, D) :- meddler(M), decoration(D), bothers(M, Disp), display(D, Disp),
                    needs_low(M), low(D), not likes_light(M).
can_bother(M, D) :- meddler(M), decoration(D), bothers(M, Disp), display(D, Disp),
                    not needs_low(M), likes_light(M), light(D).
can_bother(M, D) :- meddler(M), decoration(D), bothers(M, Disp), display(D, Disp),
                    needs_low(M), low(D), likes_light(M), light(D).

fix_works(F, M, D) :- fix(F), against(F, M), protects(F, Disp), display(D, Disp),
                      not low_req(F), can_bother(M, D).
fix_works(F, M, D) :- fix(F), against(F, M), protects(F, Disp), display(D, Disp),
                      low_req(F), low(D), can_bother(M, D).

valid(D, M, F) :- can_bother(M, D), fix_works(F, M, D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dec_id, decoration in DECORATIONS.items():
        lines.append(asp.fact("decoration", dec_id))
        lines.append(asp.fact("display", dec_id, decoration.display))
        if decoration.low:
            lines.append(asp.fact("low", dec_id))
        if decoration.light:
            lines.append(asp.fact("light", dec_id))
    for med_id, meddler in MEDDLERS.items():
        lines.append(asp.fact("meddler", med_id))
        for disp in sorted(meddler.bothers_display):
            lines.append(asp.fact("bothers", med_id, disp))
        if meddler.needs_low:
            lines.append(asp.fact("needs_low", med_id))
        if meddler.likes_light:
            lines.append(asp.fact("likes_light", med_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for disp in sorted(fix.protects_display):
            lines.append(asp.fact("protects", fix_id, disp))
        for med_id in sorted(fix.against):
            lines.append(asp.fact("against", fix_id, med_id))
        if fix.needs_low:
            lines.append(asp.fact("low_req", fix_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python valid_combos():")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        params.seed = 7
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        if sample.world is None:
            raise StoryError("(Smoke test failed: world model missing.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Curated generation made an empty story.)")
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")

    if rc == 0:
        print("OK: curated stories generated cleanly.")
    return rc


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (decoration, meddler, fix) triples:\n")
        for decoration, meddler, fix in combos:
            print(f"  {decoration:14} {meddler:8} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            header = f"### {p.child1} & {p.child2}: {p.decoration} / {p.meddler} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
