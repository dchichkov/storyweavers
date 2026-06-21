#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py
=====================================================================

A standalone story world for a tiny child-facing mystery with a surprise ending.

Premise
-------
A child receives a mini scientific kit from a dotcom shop. The next morning,
something in the little experiment corner seems wrong: a leaf is nibbled, a sign
is tipped, or a shining trail crosses the table. The child follows clues, asks a
helper, and discovers the small harmless culprit. The ending proves what changed:
the creature is given a proper place, and the kit becomes orderly and calm again.

Reasonableness constraint
-------------------------
Not every culprit can leave every clue, and not every method can honestly solve
the mystery.

- A snail can leave a silver trail and nibble leaves.
- A pill bug can nibble leaves and bump a paper sign.
- A moth can bump a sign and flutter near a light, but it does not leave slime.
- A field mouse can nibble leaves and tip a sign, but a tiny mini dome cannot
  reasonably hide one.

The world refuses mismatches. It also refuses weak solving methods: the chosen
method must actually reveal or safely trace the culprit in this setup.

Run it
------
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py --kit terrarium --culprit snail --clue silver_trail
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py --culprit moth --clue silver_trail
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py --all
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/dotcom_scientific_mini_surprise_mystery.py --verify
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
    tiny: bool = False
    alive: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Kit:
    id: str
    label: str
    phrase: str
    habitat: str
    bait: str
    hiding_spot: str
    too_small_for_mouse: bool = False
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
class Culprit:
    id: str
    label: str
    article: str
    movement: str
    likes: str
    leaves: set[str]
    fits_small_space: bool
    harmless: bool = True
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
class Clue:
    id: str
    label: str
    text: str
    reveal_place: str
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
class Method:
    id: str
    label: str
    sense: int
    reveals: set[str]
    safe_for: set[str]
    action: str
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
class Helper:
    id: str
    type: str
    label: str
    comfort: str
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


def _r_mystery(world: World) -> list[str]:
    culprit = world.get("culprit")
    clue = world.get("clue")
    kit = world.get("kit")
    out: list[str] = []
    if culprit.meters["escaped"] < THRESHOLD or clue.meters["present"] < THRESHOLD:
        return out
    sig = ("mystery", culprit.id, clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kit.meters["mess"] += 1
    child = world.get("child")
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    out.append("__mystery__")
    return out


def _r_solve(world: World) -> list[str]:
    child = world.get("child")
    culprit = world.get("culprit")
    method = world.get("method")
    if child.meters["evidence"] < THRESHOLD or child.meters["tracked"] < THRESHOLD:
        return []
    sig = ("solve", culprit.id, method.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    culprit.meters["found"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="mystery", tag="physical", apply=_r_mystery),
    Rule(name="solve", tag="social", apply=_r_solve),
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


def clue_matches(culprit: Culprit, clue: Clue) -> bool:
    return clue.id in culprit.leaves


def method_works(method: Method, clue: Clue, culprit: Culprit) -> bool:
    return clue.id in method.reveals and culprit.id in method.safe_for and method.sense >= SENSE_MIN


def culprit_fits(kit: Kit, culprit: Culprit) -> bool:
    if kit.too_small_for_mouse and culprit.id == "field_mouse":
        return False
    return culprit.fits_small_space or not kit.too_small_for_mouse


def valid_combo(kit: Kit, culprit: Culprit, clue: Clue, method: Method) -> bool:
    return clue_matches(culprit, clue) and method_works(method, clue, culprit) and culprit_fits(kit, culprit)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for kit_id, kit in KITS.items():
        for culprit_id, culprit in CULPRITS.items():
            for clue_id, clue in CLUES.items():
                for method_id, method in METHODS.items():
                    if valid_combo(kit, culprit, clue, method):
                        combos.append((kit_id, culprit_id, clue_id, method_id))
    return combos


def predict_solution(world: World) -> dict:
    sim = world.copy()
    method = sim.get("method")
    clue = sim.get("clue")
    culprit = sim.get("culprit")
    if method_works(METHODS[method.attrs["cfg"]], CLUES[clue.attrs["cfg"]], CULPRITS[culprit.attrs["cfg"]]):
        sim.get("child").meters["evidence"] += 1
        sim.get("child").meters["tracked"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("culprit").meters["found"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, kit: Kit) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On the hall table sat a box from BrightLeaf dotcom. Inside was {kit.phrase}, "
        f"so small and neat that {child.id} called it {kit.label} at once."
    )
    world.say(
        f"{child.id} and {helper.label_word} set it up carefully in the window. "
        f"They tried to make the little {kit.habitat} look almost scientific, with a paper sign, "
        f"a ruler, and one small notebook for observations."
    )


def bedtime(world: World, child: Entity, kit: Kit) -> None:
    world.say(
        f"Before bed, {child.id} checked the {kit.label} one last time. The {kit.bait} was where it should be, "
        f"and the paper sign stood straight."
    )
    world.say(
        f'"Tomorrow I will write my first scientific note," {child.pronoun()} whispered, '
        f'and tiptoed away.'
    )


def mystery_appears(world: World, child: Entity, kit: Kit, clue_ent: Entity, clue: Clue) -> None:
    clue_ent.meters["present"] += 1
    world.get("culprit").meters["escaped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the morning, something was different. {clue.text} "
        f"The mini setup no longer looked tidy. It looked like the start of a mystery."
    )
    world.say(
        f"{child.id} felt a shiver of worry and a stronger tug of wonder. "
        f'"Something visited in the night," {child.pronoun()} said.'
    )


def inspect(world: World, child: Entity, helper: Entity, clue: Clue, method: Method) -> None:
    child.memes["focus"] += 1
    pred = predict_solution(world)
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f"{helper.label_word.capitalize()} did not laugh. "
        f'"Let us look slowly," {helper.pronoun()} said. '
        f"{child.id} used {method.label} and studied the {clue.label} very carefully."
    )
    if clue.id == "silver_trail":
        world.say("The shining line curled like a tiny road toward the leaves.")
    elif clue.id == "nibbled_leaf":
        world.say("The bite marks were little half-moons, as if someone had taken polite moon-shaped snacks.")
    else:
        world.say("The sign had fallen in one direction, and a few crumbs of dry soil pointed the same way.")


def track(world: World, child: Entity, kit: Kit, clue: Clue, method: Method) -> None:
    child.meters["evidence"] += 1
    child.meters["tracked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Step by step, {child.id} followed the clue to {clue.reveal_place}. "
        f"There, tucked by {kit.hiding_spot}, was the answer."
    )


def reveal(world: World, child: Entity, culprit_ent: Entity, culprit: Culprit) -> None:
    culprit_ent.memes["startled"] += 1
    world.say(
        f"It was {culprit.article} {culprit.label}. For one surprised second, "
        f"{child.id} had to blink hard, because the whole grand mystery had been made by something so mini."
    )
    world.say(
        f'"A {culprit.label}!" {child.pronoun()} gasped. "That is the surprise."'
    )


def explain(world: World, helper: Entity, culprit: Culprit, clue: Clue, method: Method) -> None:
    world.say(
        f'{helper.label_word.capitalize()} smiled and kept {helper.comfort}. '
        f'"Mysteries feel big before you know the facts," {helper.pronoun()} said. '
        f'"But this one fits: the {culprit.label} could leave {clue.label}, and {method.action} helped us see it."'
    )


def kindness(world: World, child: Entity, helper: Entity, kit: Kit, culprit_ent: Entity, culprit: Culprit) -> None:
    culprit_ent.meters["safe"] += 1
    child.memes["kindness"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"They lifted the little visitor gently and carried it outside to a damp plant box where it would like {culprit.likes}. "
        f"Then they set the sign upright and made the {kit.label} tidy again."
    )
    world.say(
        f"After that, {child.id} wrote the first note in the notebook: "
        f'"Mystery solved in a scientific way. The visitor was small, harmless, and real."'
    )


def ending(world: World, child: Entity, kit: Kit) -> None:
    world.say(
        f"By the window, the {kit.label} looked calm once more. Still, whenever the sun touched the glass, "
        f"{child.id} smiled at the memory of the tiny mystery from the dotcom box and listened for one more surprise."
    )


def tell(
    kit: Kit,
    culprit: Culprit,
    clue: Clue,
    method: Method,
    helper_cfg: Helper,
    child_name: str = "Nora",
    child_type: str = "girl",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    child.id = child_name
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    kit_ent = world.add(Entity(id="kit", kind="thing", type="kit", label=kit.label))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, attrs={"cfg": clue.id}))
    culprit_ent = world.add(
        Entity(
            id="culprit",
            kind="thing",
            type="creature",
            label=culprit.label,
            role="culprit",
            tiny=True,
            alive=True,
            attrs={"cfg": culprit.id},
        )
    )
    method_ent = world.add(Entity(id="method", kind="thing", type="tool", label=method.label, attrs={"cfg": method.id}))

    world.facts["kit_cfg"] = kit
    world.facts["culprit_cfg"] = culprit
    world.facts["clue_cfg"] = clue
    world.facts["method_cfg"] = method
    world.facts["helper_cfg"] = helper_cfg

    opening(world, child, helper, kit)
    bedtime(world, child, kit)

    world.para()
    mystery_appears(world, child, kit, clue_ent, clue)
    inspect(world, child, helper, clue, method)

    world.para()
    track(world, child, kit, clue, method)
    reveal(world, child, culprit_ent, culprit)
    explain(world, helper, culprit, clue, method)

    world.para()
    kindness(world, child, helper, kit, culprit_ent, culprit)
    ending(world, child, kit)

    world.facts.update(
        child=child,
        helper=helper,
        kit=kit_ent,
        clue=clue_ent,
        culprit=culprit_ent,
        method=method_ent,
        solved=culprit_ent.meters["found"] >= THRESHOLD,
        safe=culprit_ent.meters["safe"] >= THRESHOLD,
    )
    return world


KITS = {
    "terrarium": Kit(
        id="terrarium",
        label="the mini moss dome",
        phrase="a mini moss dome kit with a clear lid",
        habitat="green mossy dome",
        bait="tiny lettuce leaves",
        hiding_spot="the cool rim of the flowerpot",
        too_small_for_mouse=True,
        tags={"mini", "scientific", "garden"},
    ),
    "seed_lab": Kit(
        id="seed_lab",
        label="the mini seed lab",
        phrase="a mini seed lab with clear cups and paper rulers",
        habitat="seed table",
        bait="bean sprouts",
        hiding_spot="the folded corner of the tray",
        too_small_for_mouse=False,
        tags={"mini", "scientific", "seeds"},
    ),
    "bug_hotel": Kit(
        id="bug_hotel",
        label="the mini bug hotel",
        phrase="a mini bug hotel made from little tubes and bark",
        habitat="bug house",
        bait="soft leaves",
        hiding_spot="the bark beside the tubes",
        too_small_for_mouse=True,
        tags={"mini", "scientific", "bugs"},
    ),
}

CULPRITS = {
    "snail": Culprit(
        id="snail",
        label="snail",
        article="a tiny snail",
        movement="slid",
        likes="cool damp leaves",
        leaves={"silver_trail", "nibbled_leaf"},
        fits_small_space=True,
        tags={"snail", "tiny_animal"},
    ),
    "pill_bug": Culprit(
        id="pill_bug",
        label="pill bug",
        article="a round little pill bug",
        movement="rolled",
        likes="dark damp bark",
        leaves={"nibbled_leaf", "tipped_sign"},
        fits_small_space=True,
        tags={"pill_bug", "tiny_animal"},
    ),
    "moth": Culprit(
        id="moth",
        label="moth",
        article="a pale moth",
        movement="fluttered",
        likes="quiet dark corners",
        leaves={"tipped_sign"},
        fits_small_space=True,
        tags={"moth", "tiny_animal"},
    ),
    "field_mouse": Culprit(
        id="field_mouse",
        label="field mouse",
        article="a field mouse",
        movement="scurried",
        likes="seeds and dry corners",
        leaves={"nibbled_leaf", "tipped_sign"},
        fits_small_space=False,
        tags={"mouse", "tiny_animal"},
    ),
}

CLUES = {
    "silver_trail": Clue(
        id="silver_trail",
        label="a silver trail",
        text="Across the tray ran a faint silver trail that caught the light like a secret line",
        reveal_place="the windowsill",
        tags={"trail", "mystery"},
    ),
    "nibbled_leaf": Clue(
        id="nibbled_leaf",
        label="nibbled leaves",
        text="Two little leaves had neat bites taken from their edges",
        reveal_place="the leaf cup",
        tags={"leaf", "mystery"},
    ),
    "tipped_sign": Clue(
        id="tipped_sign",
        label="the tipped paper sign",
        text="The paper sign that said OBSERVE had fallen over sideways",
        reveal_place="the side of the tray",
        tags={"sign", "mystery"},
    ),
}

METHODS = {
    "magnifier": Method(
        id="magnifier",
        label="a magnifying glass",
        sense=3,
        reveals={"silver_trail", "nibbled_leaf", "tipped_sign"},
        safe_for={"snail", "pill_bug", "moth", "field_mouse"},
        action="looking close through the magnifying glass",
        qa_text="used a magnifying glass to study the clue and follow it",
        tags={"magnifier", "scientific"},
    ),
    "flour_ring": Method(
        id="flour_ring",
        label="a tiny ring of flour",
        sense=2,
        reveals={"nibbled_leaf", "tipped_sign"},
        safe_for={"pill_bug", "field_mouse"},
        action="making a tiny ring of flour to show where small feet had gone",
        qa_text="made a tiny ring of flour to trace little feet",
        tags={"tracks", "scientific"},
    ),
    "flashlight": Method(
        id="flashlight",
        label="a small flashlight",
        sense=2,
        reveals={"tipped_sign"},
        safe_for={"moth"},
        action="shining a small flashlight into the darker corners",
        qa_text="used a flashlight to spot what was hiding in the darker corner",
        tags={"light", "scientific"},
    ),
    "shake_box": Method(
        id="shake_box",
        label="shaking the kit box",
        sense=1,
        reveals={"silver_trail"},
        safe_for=set(),
        action="shaking the box",
        qa_text="shook the box",
        tags={"bad_idea"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        type="mother",
        label="the parent",
        comfort="her voice soft",
        tags={"adult"},
    ),
    "father": Helper(
        id="father",
        type="father",
        label="the parent",
        comfort="his voice low",
        tags={"adult"},
    ),
    "aunt": Helper(
        id="aunt",
        type="aunt",
        label="the aunt",
        comfort="her smile calm",
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ava", "Lucy", "Rose", "Lena", "Ivy", "Ella"]
BOY_NAMES = ["Owen", "Leo", "Sam", "Ben", "Max", "Theo", "Eli", "Noah"]


@dataclass
class StoryParams:
    kit: str
    culprit: str
    clue: str
    method: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "dotcom": [
        (
            "What does dotcom mean in a shop name?",
            "Dotcom often means a shop or website on the internet. It tells you the package or store can be found online."
        )
    ],
    "scientific": [
        (
            "What does scientific mean?",
            "Scientific means looking carefully, asking what happened, and checking the facts. It is a way of learning from real clues."
        )
    ],
    "mini": [
        (
            "What does mini mean?",
            "Mini means very small. A mini kit is a tiny version of something bigger."
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes tiny things look bigger. That helps you notice details you might miss."
        )
    ],
    "tracks": [
        (
            "Why do people look for tracks in a mystery?",
            "Tracks show where something moved. They can point you toward the thing that made them."
        )
    ],
    "light": [
        (
            "Why can a flashlight help in a mystery?",
            "A flashlight helps you see into dark corners. Better light can turn a guess into a real answer."
        )
    ],
    "snail": [
        (
            "Why can a snail leave a shiny trail?",
            "A snail moves on a layer of slime that helps it slide. That can leave a shiny trail behind it."
        )
    ],
    "pill_bug": [
        (
            "What is a pill bug?",
            "A pill bug is a tiny little creature that likes dark damp places. Some can curl into a small ball when they feel afraid."
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a soft-winged insect. Many moths fly at night and may flutter toward light."
        )
    ],
    "mouse": [
        (
            "Why do mice nibble things?",
            "Mice eat small bits of food like seeds and leaves. Their little teeth leave nibbled edges."
        )
    ],
}
KNOWLEDGE_ORDER = ["dotcom", "scientific", "mini", "magnifier", "tracks", "light", "snail", "pill_bug", "moth", "mouse"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    kit = f["kit_cfg"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    method = f["method_cfg"]
    return [
        f'Write a short mystery for a 3-to-5-year-old that uses the words "dotcom", "scientific", and "mini".',
        f"Tell a gentle surprise mystery where {child.id} finds {clue.label} near {kit.label} and solves it by {method.action}.",
        f"Write a child-facing mystery in which the scary-looking clue turns out to come from a harmless {culprit.label}, and the ending becomes calm and kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    kit_cfg = f["kit_cfg"]
    culprit_cfg = f["culprit_cfg"]
    clue_cfg = f["clue_cfg"]
    method_cfg = f["method_cfg"]
    out = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child with a mini experiment kit, and {helper.label_word} who helps with the mystery. Together they look slowly instead of guessing wildly."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {clue_cfg.text.lower()}. That changed the neat little kit and made it feel as if something secret had happened in the night."
        ),
        (
            f"Why did {child.id} use {method_cfg.label}?",
            f"{child.id} used {method_cfg.label} to study the clue closely and follow it in a scientific way. Looking carefully helped turn worry into evidence."
        ),
        (
            "What was the surprise answer?",
            f"The surprise was that the mystery came from {culprit_cfg.article}, not something big or scary. The clue only looked grand because the whole scene was so mini."
        ),
        (
            f"How did {child.id} solve the mystery?",
            f"{child.id} {method_cfg.qa_text}. That led to {clue_cfg.reveal_place}, where the hidden visitor was found."
        ),
        (
            "How did the story end?",
            f"They gently moved the little creature to a better place outside and tidied the kit again. The ending shows that the mystery became understanding instead of fear."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit_cfg = f["culprit_cfg"]
    method_cfg = f["method_cfg"]
    tags: set[str] = {"dotcom", "scientific", "mini"}
    if method_cfg.id == "magnifier":
        tags.add("magnifier")
    if method_cfg.id == "flour_ring":
        tags.add("tracks")
    if method_cfg.id == "flashlight":
        tags.add("light")
    if culprit_cfg.id == "snail":
        tags.add("snail")
    if culprit_cfg.id == "pill_bug":
        tags.add("pill_bug")
    if culprit_cfg.id == "moth":
        tags.add("moth")
    if culprit_cfg.id == "field_mouse":
        tags.add("mouse")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        kit="terrarium",
        culprit="snail",
        clue="silver_trail",
        method="magnifier",
        helper="mother",
        name="Nora",
        gender="girl",
    ),
    StoryParams(
        kit="bug_hotel",
        culprit="pill_bug",
        clue="tipped_sign",
        method="flour_ring",
        helper="father",
        name="Leo",
        gender="boy",
    ),
    StoryParams(
        kit="seed_lab",
        culprit="field_mouse",
        clue="nibbled_leaf",
        method="flour_ring",
        helper="aunt",
        name="Mia",
        gender="girl",
    ),
    StoryParams(
        kit="bug_hotel",
        culprit="moth",
        clue="tipped_sign",
        method="flashlight",
        helper="mother",
        name="Ben",
        gender="boy",
    ),
    StoryParams(
        kit="seed_lab",
        culprit="snail",
        clue="nibbled_leaf",
        method="magnifier",
        helper="father",
        name="Ivy",
        gender="girl",
    ),
]


def explain_invalid(kit: Kit, culprit: Culprit, clue: Clue, method: Method) -> str:
    if not culprit_fits(kit, culprit):
        return (
            f"(No story: {culprit.article} does not reasonably fit inside or around {kit.label}. "
            f"That mini setup is too small for that culprit.)"
        )
    if not clue_matches(culprit, clue):
        return (
            f"(No story: a {culprit.label} would not honestly leave {clue.label}. "
            f"Pick a clue that matches the creature's real behavior.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Pick a calmer, safer way to investigate.)"
        )
    return (
        f"(No story: {method.label} would not really reveal {clue.label} and safely solve a mystery about a {culprit.label}.)"
    )


ASP_RULES = r"""
clue_matches(Culprit, Clue) :- culprit(Culprit), clue(Clue), leaves(Culprit, Clue).

fits(Kit, field_mouse) :- kit(Kit), not too_small_for_mouse(Kit).
fits(Kit, Culprit) :- culprit(Culprit), Culprit != field_mouse.

sensible(Method) :- method(Method), sense(Method, S), sense_min(M), S >= M.
method_works(Method, Clue, Culprit) :- sensible(Method), reveals(Method, Clue), safe_for(Method, Culprit).

valid(Kit, Culprit, Clue, Method) :-
    kit(Kit), culprit(Culprit), clue(Clue), method(Method),
    clue_matches(Culprit, Clue),
    fits(Kit, Culprit),
    method_works(Method, Clue, Culprit).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kit_id, kit in KITS.items():
        lines.append(asp.fact("kit", kit_id))
        if kit.too_small_for_mouse:
            lines.append(asp.fact("too_small_for_mouse", kit_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for clue in sorted(culprit.leaves):
            lines.append(asp.fact("leaves", culprit_id, clue))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for clue in sorted(method.reveals):
            lines.append(asp.fact("reveals", method_id, clue))
        for culprit in sorted(method.safe_for):
            lines.append(asp.fact("safe_for", method_id, culprit))
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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        args = build_parser().parse_args([])
        params = resolve_params(args, rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story or "mystery" not in sample.story.lower():
            raise StoryError("default generation did not produce an ordinary mystery story")
        print("OK: default generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mini scientific mystery with a surprise ending."
    )
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.kit and args.culprit and args.clue and args.method:
        kit = KITS[args.kit]
        culprit = CULPRITS[args.culprit]
        clue = CLUES[args.clue]
        method = METHODS[args.method]
        if not valid_combo(kit, culprit, clue, method):
            raise StoryError(explain_invalid(kit, culprit, clue, method))

    combos = [
        c for c in valid_combos()
        if (args.kit is None or c[0] == args.kit)
        and (args.culprit is None or c[1] == args.culprit)
        and (args.clue is None or c[2] == args.clue)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    kit, culprit, clue, method = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    return StoryParams(
        kit=kit,
        culprit=culprit,
        clue=clue,
        method=method,
        helper=helper,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.kit not in KITS:
        raise StoryError(f"Unknown kit: {params.kit}")
    if params.culprit not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    kit = KITS[params.kit]
    culprit = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not valid_combo(kit, culprit, clue, method):
        raise StoryError(explain_invalid(kit, culprit, clue, method))

    world = tell(
        kit=kit,
        culprit=culprit,
        clue=clue,
        method=method,
        helper_cfg=helper,
        child_name=params.name,
        child_type=params.gender,
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
        print(f"{len(combos)} compatible (kit, culprit, clue, method) combos:\n")
        for kit, culprit, clue, method in combos:
            print(f"  {kit:10} {culprit:11} {clue:13} {method}")
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
            header = f"### {p.name}: {p.culprit} / {p.clue} / {p.method} in {p.kit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
