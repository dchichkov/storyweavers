#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py
=================================================================================

A standalone storyworld about a child helping prepare a small thank-you ceremony.
The child must transcribe kind words onto a ceremonial object and add a symbol
that matches the moral value being celebrated. The world enforces a simple
reasonableness rule: the chosen writing tool must actually work on the chosen
material.

This domain aims for a heartwarming, TinyStories-style shape:
- premise: a caring child wants to help with a ceremony
- tension: the child feels nervous about writing the important words neatly
- turn: the writing wobbles or smudges, then a helper offers a gentle fix
- resolution: the ceremony happens, the kind message is shared, and the ending
  image proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py --honoree librarian --value gratitude
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py --material wood_plaque --tool crayon
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ceremony_transcribe_symbol_moral_value_heartwarming.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    materials: set[str] = field(default_factory=set)
    marks_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "teacher"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class CeremonyKind:
    id: str
    label: str
    place: str
    crowd: str
    ending_image: str
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
class Honoree:
    id: str
    label: str
    good_deed: str
    smile: str
    title: str
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
class MoralValue:
    id: str
    label: str
    promise: str
    lesson: str
    child_line: str
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
class Material:
    id: str
    label: str
    phrase: str
    surface: str
    needs: set[str] = field(default_factory=set)
    delicate: bool = False
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
    marks: set[str] = field(default_factory=set)
    precision: int = 2
    style: str = ""
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
class SymbolCfg:
    id: str
    label: str
    meaning: str
    fits: set[str] = field(default_factory=set)
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


def _r_wobble_to_smudge(world: World) -> list[str]:
    child = world.get("child")
    keepsake = world.get("keepsake")
    if child.meters["wobble"] < THRESHOLD or keepsake.meters["written"] < THRESHOLD:
        return []
    sig = ("smudge", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keepsake.meters["smudged"] += 1
    child.memes["worry"] += 1
    return ["__smudge__"]


def _r_help_clears_worry(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes["helping"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return []
    sig = ("comfort", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble_to_smudge", tag="physical", apply=_r_wobble_to_smudge),
    Rule(name="help_clears_worry", tag="social", apply=_r_help_clears_worry),
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


def can_mark(material: Material, tool: ToolCfg) -> bool:
    return bool(material.needs & tool.marks)


def good_symbol(value: MoralValue, symbol: SymbolCfg) -> bool:
    return value.id in symbol.fits


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for ceremony_id in CEREMONIES:
        for honoree_id in HONOREES:
            for value_id, value in VALUES.items():
                for material_id, material in MATERIALS.items():
                    for tool_id, tool in TOOLS.items():
                        if not can_mark(material, tool):
                            continue
                        for symbol_id, symbol in SYMBOLS.items():
                            if good_symbol(value, symbol):
                                combos.append(
                                    (ceremony_id, honoree_id, value_id, material_id, tool_id, symbol_id)
                                )
    return combos


def predicted_wobble(trait: str, tool: ToolCfg, material: Material) -> bool:
    careful = {"careful", "patient", "steady"}
    return not (trait in careful or tool.precision >= 3 or material.delicate is False and tool.precision >= 2)


def outcome_of_params(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    material = MATERIALS[params.material]
    wobble = predicted_wobble(params.trait, tool, material)
    if not wobble:
        return "smooth"
    return "repaired" if params.helper_style != "absent" else "plain"


def predict_copybook(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    keepsake = sim.get("keepsake")
    child.meters["wobble"] += 1
    keepsake.meters["written"] += 1
    propagate(sim, narrate=False)
    return {
        "smudged": keepsake.meters["smudged"] >= THRESHOLD,
        "worry": child.memes["worry"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, ceremony: CeremonyKind, honoree: Honoree) -> None:
    child.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} helped get ready for a {ceremony.label} "
        f"at {ceremony.place}. The neighbors were gathering to thank {honoree.label}, who always {honoree.good_deed}."
    )
    world.say(
        f"Everyone wanted the ceremony to feel warm and true, because {honoree.title} had made many ordinary days kinder."
    )


def assign_task(world: World, child: Entity, helper: Entity, material: Material, tool: ToolCfg, symbol: SymbolCfg, value: MoralValue) -> None:
    keepsake = world.get("keepsake")
    child.memes["pride"] += 1
    world.say(
        f"On the table lay {material.phrase}. Beside it rested {tool.phrase}, ready for the careful job."
    )
    world.say(
        f'"Would you transcribe our promise onto it?" {helper.id} asked. "Then add the {symbol.label} as a symbol of {symbol.meaning}."'
    )
    world.say(
        f"{child.id} looked at the blank {keepsake.label} and whispered the words to remember them: "
        f'"{value.promise}"'
    )


def feel_nervous(world: World, child: Entity, helper: Entity, tool: ToolCfg, material: Material) -> None:
    pred = predict_copybook(world)
    world.facts["predicted_smudge"] = pred["smudged"]
    if pred["smudged"]:
        child.memes["worry"] += 1
        world.say(
            f"But the job felt important. {child.id} worried that one shaky line from {tool.label} might spoil the neat {material.surface}."
        )
    else:
        world.say(
            f"{child.id} took a slow breath. The {tool.label} felt steady in {child.pronoun('possessive')} hand."
        )


def begin_writing(world: World, child: Entity, value: MoralValue, trait: str) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["written"] += 1
    child.memes["focus"] += 1
    if predicted_wobble(trait, TOOLS[world.facts["tool"].id], MATERIALS[world.facts["material"].id]):
        child.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {child.id} began to transcribe the promise, letter by letter, across the {keepsake.label}."
    )


def notice_smudge(world: World, child: Entity, helper: Entity) -> None:
    keepsake = world.get("keepsake")
    if keepsake.meters["smudged"] >= THRESHOLD:
        world.say(
            f"Halfway through, one little stroke slipped. {child.id}'s eyes grew wide when a soft smudge curled beside the writing."
        )
        world.say(
            f'"Oh no," {child.pronoun()} said. "I wanted the message to look as kind as it sounds."'
        )


def help_repair(world: World, child: Entity, helper: Entity, symbol: SymbolCfg, material: Material) -> None:
    keepsake = world.get("keepsake")
    helper.memes["helping"] += 1
    propagate(world, narrate=False)
    keepsake.meters["repaired"] += 1
    keepsake.meters["smudged"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f"{helper.id} knelt beside {child.id} and smiled. "
        f'"A kind message does not have to be lonely," {helper.pronoun()} said.'
    )
    world.say(
        f"Together they turned the little slip into part of the design, tracing the {symbol.label} around it until the mark looked gentle and meant to be there."
    )
    world.say(
        f"The {material.surface} no longer looked spoiled. It looked touched by two caring hands."
    )


def finish_cleanly(world: World, child: Entity, symbol: SymbolCfg) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["symbol_drawn"] += 1
    child.memes["confidence"] += 1
    child.memes["joy"] += 1
    world.say(
        f"When the words were finished, {child.id} added the {symbol.label} underneath. The symbol made the promise feel bright and complete."
    )


def finish_after_repair(world: World, child: Entity, symbol: SymbolCfg) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["symbol_drawn"] += 1
    keepsake.meters["shared_work"] += 1
    world.say(
        f"Then {child.id} traced the last letters with a calmer hand and drew the {symbol.label} below them. This time the lines came out steady."
    )


def ceremony_scene(world: World, child: Entity, helper: Entity, ceremony: CeremonyKind, honoree: Honoree, value: MoralValue) -> None:
    child.memes["pride"] += 1
    hon = world.get("honoree")
    hon.memes["moved"] += 1
    world.say(
        f"At last the ceremony began. The {ceremony.crowd} grew quiet as {child.id} carried the keepsake to the front."
    )
    world.say(
        f"{child.id} read the words aloud: \"{value.promise}\" Then {child.pronoun()} handed the keepsake to {honoree.label}."
    )
    world.say(
        f"{honoree.label.capitalize()} looked at the writing and {honoree.smile}. For a moment, the whole place felt softer."
    )


def closing_lesson(world: World, child: Entity, helper: Entity, ceremony: CeremonyKind, value: MoralValue, outcome: str) -> None:
    if outcome == "repaired":
        world.say(
            f"On the way home, {child.id} understood something new: {value.lesson} Even a mistake could be mended when people chose to help instead of hide."
        )
    else:
        world.say(
            f"On the way home, {child.id} held the warm feeling in {child.pronoun('possessive')} chest. {value.lesson}"
        )
    world.say(ceremony.ending_image)
def tell(
    honoree: Honoree,
    value: Value,
    material: Material,
    tool: Tool,
    symbol: Symbol,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: HelperType,
    trait: Trait,
    helper_style: HelperStyle,
    ceremony=None,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", attrs={"style": helper_style}))
    hon = world.add(Entity(id="Honoree", kind="character", type="person", role="honoree", label=honoree.label))
    keepsake = world.add(Entity(id="keepsake", type="keepsake", label=material.label, attrs={"surface": material.surface}))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, marks_with=set(tool.marks)))
    symbol_ent = world.add(Entity(id="symbol", type="symbol", label=symbol.label))
    world.facts.update(
        ceremony=ceremony,
        honoree=honoree,
        value=value,
        material=material,
        tool=tool,
        symbol=symbol,
        child=child,
        helper=helper,
        honoree_entity=hon,
        keepsake=keepsake,
        helper_style=helper_style,
        trait=trait,
    )

    introduce(world, child, helper, ceremony, honoree)
    world.para()
    assign_task(world, child, helper, material, tool, symbol, value)
    feel_nervous(world, child, helper, tool, material)
    begin_writing(world, child, value, trait)
    notice_smudge(world, child, helper)

    outcome = outcome_of_params(
        StoryParams(
            ceremony=ceremony.id,
            honoree=honoree.id,
            value=value.id,
            material=material.id,
            tool=tool.id,
            symbol=symbol.id,
            child_name=child_name,
            child_gender=child_gender,
            helper_name=helper_name,
            helper_type=helper_type,
            trait=trait,
            helper_style=helper_style,
            seed=None,
        )
    )
    world.para()
    if outcome == "repaired":
        help_repair(world, child, helper, symbol, material)
        finish_after_repair(world, child, symbol)
    else:
        finish_cleanly(world, child, symbol)

    world.para()
    ceremony_scene(world, child, helper, ceremony, honoree, value)
    closing_lesson(world, child, helper, ceremony, value, outcome)

    world.facts["outcome"] = outcome
    world.facts["smudged"] = keepsake.meters["smudged"] >= THRESHOLD
    world.facts["repaired"] = keepsake.meters["repaired"] >= THRESHOLD
    return world
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


CEREMONIES = {
    "garden_thanks": CeremonyKind(
        id="garden_thanks",
        label="thank-you ceremony",
        place="the little garden by the library",
        crowd="children and grown-ups in a half circle",
        ending_image="The paper lanterns glowed above the garden path, and the promise shone back from smiling faces.",
        tags={"ceremony", "community"},
    ),
    "school_morning": CeremonyKind(
        id="school_morning",
        label="morning ceremony",
        place="the school courtyard",
        crowd="students and teachers by the flagstones",
        ending_image="Morning light slid across the courtyard, and every child seemed to stand a little closer together.",
        tags={"ceremony", "school"},
    ),
    "porch_evening": CeremonyKind(
        id="porch_evening",
        label="evening ceremony",
        place="the wide front porch of the community house",
        crowd="families on folding chairs",
        ending_image="By evening, the porch steps held quiet shoes and bright eyes, and kindness felt like a lamp everyone could share.",
        tags={"ceremony", "community"},
    ),
}

HONOREES = {
    "librarian": Honoree(
        id="librarian",
        label="the librarian",
        good_deed="saved special books and always found the right one for worried children",
        smile="smiled with shiny eyes",
        title="the librarian",
        tags={"books", "care"},
    ),
    "gardener": Honoree(
        id="gardener",
        label="the gardener",
        good_deed="watered every small plant and tucked fallen stems upright again",
        smile="pressed a hand over the heart and smiled",
        title="the gardener",
        tags={"garden", "care"},
    ),
    "baker": Honoree(
        id="baker",
        label="the baker",
        good_deed="saved the warmest rolls for neighbors who had rough mornings",
        smile="laughed softly and blinked fast",
        title="the baker",
        tags={"food", "sharing"},
    ),
}

VALUES = {
    "kindness": MoralValue(
        id="kindness",
        label="kindness",
        promise="We choose kind hands and kind words.",
        lesson="Kindness grows bigger when it is shared out loud.",
        child_line="kind hands",
        tags={"moral", "kindness"},
    ),
    "gratitude": MoralValue(
        id="gratitude",
        label="gratitude",
        promise="We remember care, and we give thanks for it.",
        lesson="Gratitude helps people see the quiet good that holds a community together.",
        child_line="give thanks",
        tags={"moral", "gratitude"},
    ),
    "helpfulness": MoralValue(
        id="helpfulness",
        label="helpfulness",
        promise="We help before someone has to ask twice.",
        lesson="Helping is love with sleeves rolled up.",
        child_line="we help",
        tags={"moral", "helpfulness"},
    ),
}

MATERIALS = {
    "paper_scroll": Material(
        id="paper_scroll",
        label="paper scroll",
        phrase="a long paper scroll tied with ribbon",
        surface="paper",
        needs={"wax", "ink"},
        delicate=True,
        tags={"paper"},
    ),
    "cloth_banner": Material(
        id="cloth_banner",
        label="cloth banner",
        phrase="a cloth banner with a hemmed edge",
        surface="cloth",
        needs={"paint", "ink"},
        delicate=False,
        tags={"cloth"},
    ),
    "wood_plaque": Material(
        id="wood_plaque",
        label="wood plaque",
        phrase="a smooth wood plaque sanded by hand",
        surface="wood",
        needs={"paint"},
        delicate=False,
        tags={"wood"},
    ),
}

TOOLS = {
    "brush": ToolCfg(
        id="brush",
        label="paintbrush",
        phrase="a small paintbrush",
        marks={"paint"},
        precision=2,
        style="flowing",
        tags={"paint"},
    ),
    "paint_pen": ToolCfg(
        id="paint_pen",
        label="paint pen",
        phrase="a careful paint pen",
        marks={"paint"},
        precision=3,
        style="steady",
        tags={"paint"},
    ),
    "ink_pen": ToolCfg(
        id="ink_pen",
        label="ink pen",
        phrase="an ink pen with a fine tip",
        marks={"ink"},
        precision=3,
        style="neat",
        tags={"ink"},
    ),
    "wax_crayon": ToolCfg(
        id="wax_crayon",
        label="wax crayon",
        phrase="a dark wax crayon",
        marks={"wax"},
        precision=1,
        style="soft",
        tags={"wax"},
    ),
    "crayon": ToolCfg(
        id="crayon",
        label="crayon",
        phrase="a box with one bright crayon set aside",
        marks={"wax"},
        precision=1,
        style="soft",
        tags={"wax"},
    ),
}

SYMBOLS = {
    "heart": SymbolCfg(
        id="heart",
        label="heart symbol",
        meaning="kindness",
        fits={"kindness", "gratitude"},
        tags={"heart"},
    ),
    "sun": SymbolCfg(
        id="sun",
        label="sun symbol",
        meaning="warm gratitude",
        fits={"gratitude", "helpfulness"},
        tags={"sun"},
    ),
    "hands": SymbolCfg(
        id="hands",
        label="joined-hands symbol",
        meaning="helping together",
        fits={"helpfulness", "kindness"},
        tags={"hands"},
    ),
    "leaf": SymbolCfg(
        id="leaf",
        label="leaf symbol",
        meaning="care that keeps growing",
        fits={"kindness", "gratitude"},
        tags={"leaf"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "June", "Ella", "Sana", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Eli", "Owen", "Max", "Theo", "Sam"]
TRAITS = ["careful", "patient", "steady", "eager", "hopeful"]
HELPER_STYLES = ["gentle", "cheerful", "absent"]


KNOWLEDGE = {
    "ceremony": [
        (
            "What is a ceremony?",
            "A ceremony is a special time when people gather to honor something important. It often has quiet listening, careful words, and shared feelings."
        )
    ],
    "transcribe": [
        (
            "What does transcribe mean?",
            "To transcribe means to copy words carefully so they can be read again. You listen or remember, then write the words down as neatly as you can."
        )
    ],
    "symbol": [
        (
            "What is a symbol?",
            "A symbol is a shape or picture that stands for an idea. A heart can stand for love or kindness even when no one says those words."
        )
    ],
    "kindness": [
        (
            "Why does kindness matter in a community?",
            "Kindness helps people feel safe, noticed, and cared for. Small kind acts can change a whole day for someone."
        )
    ],
    "gratitude": [
        (
            "What is gratitude?",
            "Gratitude is the warm feeling of noticing good things others have done. It often makes people want to say thank you and pass goodness on."
        )
    ],
    "helpfulness": [
        (
            "Why is helping a good moral value?",
            "Helping shows that we care about other people's needs. When people help each other, hard jobs feel lighter and hearts feel closer."
        )
    ],
    "paper": [
        (
            "Why do people write carefully on paper?",
            "Paper can wrinkle or smudge if someone presses too hard or moves too fast. Careful writing helps the words stay clear."
        )
    ],
    "cloth": [
        (
            "Why can writing on cloth be tricky?",
            "Cloth can shift and bend while someone writes on it. That means a steady hand matters if you want neat letters."
        )
    ],
    "wood": [
        (
            "Why does wood often need paint instead of a regular crayon?",
            "Wood is firm and not very absorbent, so a plain crayon may not leave a strong clear mark. Paint or a paint pen can show up better."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "ceremony",
    "transcribe",
    "symbol",
    "kindness",
    "gratitude",
    "helpfulness",
    "paper",
    "cloth",
    "wood",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ceremony = f["ceremony"]
    value = f["value"]
    honoree = f["honoree"]
    symbol = f["symbol"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "ceremony", "transcribe", and "symbol".',
        f"Tell a gentle story where {child.id} helps prepare a {ceremony.label} for {honoree.label} and learns about {value.label}.",
        f"Write a warm moral story in which a child carefully transcribes a promise and adds a {symbol.label} as a symbol of {value.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    ceremony: CeremonyKind = f["ceremony"]
    honoree: Honoree = f["honoree"]
    value: MoralValue = f["value"]
    material: Material = f["material"]
    tool: ToolCfg = f["tool"]
    symbol: SymbolCfg = f["symbol"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who helped get ready for a {ceremony.label}, and {helper.id}, who stayed nearby to guide {child.pronoun('object')}. The ceremony was for {honoree.label}."
        ),
        (
            "What special job did the child have?",
            f"{child.id} had to transcribe the promise \"{value.promise}\" onto the {material.label}. Then {child.pronoun()} added the {symbol.label} so the message would show its meaning."
        ),
        (
            f"Why was the {symbol.label} important?",
            f"The {symbol.label} was a symbol of {symbol.meaning}. It helped the promise feel visible, not just spoken, so everyone at the ceremony could see the moral value too."
        ),
    ]
    if f.get("predicted_smudge"):
        qa.append(
            (
                f"Why did {child.id} feel nervous before writing?",
                f"{child.id} knew the job mattered and worried a shaky line might spoil the neat {material.surface}. That is why the work felt bigger than ordinary drawing."
            )
        )
    if outcome == "repaired":
        qa.append(
            (
                "What went wrong, and how was it fixed?",
                f"A little smudge appeared while {child.id} was writing. Then {helper.id} helped turn the slip into part of the design, and together they finished the words and the symbol."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{child.id} learned that {value.lesson} The repair showed that a mistake does not have to end a kind job when someone helps with patience."
            )
        )
    else:
        qa.append(
            (
                "How did the writing turn out?",
                f"The writing came out clearly with the {tool.label}, and the promise looked calm and complete. When {child.id} added the symbol, the keepsake was ready for the ceremony."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"At the ceremony, {child.id} read the promise aloud and gave the keepsake to {honoree.label}. The ending felt warm because the kind words were shared in front of everyone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    value: MoralValue = f["value"]
    material: Material = f["material"]
    tags = {"ceremony", "transcribe", "symbol", value.id}
    tags |= set(material.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    ceremony: str
    honoree: str
    value: str
    material: str
    tool: str
    symbol: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    helper_style: str = "gentle"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        ceremony="garden_thanks",
        honoree="librarian",
        value="gratitude",
        material="paper_scroll",
        tool="ink_pen",
        symbol="heart",
        child_name="Nora",
        child_gender="girl",
        helper_name="Mama",
        helper_type="mother",
        trait="careful",
        helper_style="gentle",
    ),
    StoryParams(
        ceremony="school_morning",
        honoree="gardener",
        value="helpfulness",
        material="cloth_banner",
        tool="brush",
        symbol="hands",
        child_name="Leo",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="eager",
        helper_style="gentle",
    ),
    StoryParams(
        ceremony="porch_evening",
        honoree="baker",
        value="kindness",
        material="wood_plaque",
        tool="paint_pen",
        symbol="leaf",
        child_name="Mia",
        child_gender="girl",
        helper_name="Auntie",
        helper_type="woman",
        trait="patient",
        helper_style="cheerful",
    ),
]


def explain_material_tool(material: Material, tool: ToolCfg) -> str:
    need = " / ".join(sorted(material.needs))
    marks = " / ".join(sorted(tool.marks))
    return (
        f"(No story: {tool.label} makes {marks}, but the {material.label} reasonably needs {need}. "
        f"The tool must be able to mark the chosen material.)"
    )


def explain_symbol(value: MoralValue, symbol: SymbolCfg) -> str:
    fits = ", ".join(sorted(symbol.fits))
    return (
        f"(No story: the {symbol.label} does not fit the value '{value.id}' here. "
        f"It works better for: {fits}.)"
    )


ASP_RULES = r"""
valid(C,H,V,M,T,S) :- ceremony(C), honoree(H), value(V), material(M), tool(T), symbol(S),
                      works_on(M,T), fits_value(V,S).

works_on(M,T) :- material_needs(M,Mark), tool_marks(T,Mark).
fits_value(V,S) :- symbol_fits(S,V).

careful_trait(careful;patient;steady).

wobble(Trait, T) :- trait(Trait), not careful_trait(Trait), tool_precision(T,P), P < 3.
smooth :- not wobble(_, _).
repaired :- wobble(_, _), helper_present.
plain :- wobble(_, _), not helper_present.

outcome(smooth) :- smooth.
outcome(repaired) :- repaired.
outcome(plain) :- plain.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CEREMONIES:
        lines.append(asp.fact("ceremony", cid))
    for hid in HONOREES:
        lines.append(asp.fact("honoree", hid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        for mark in sorted(material.needs):
            lines.append(asp.fact("material_needs", mid, mark))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_precision", tid, tool.precision))
        for mark in sorted(tool.marks):
            lines.append(asp.fact("tool_marks", tid, mark))
    for sid, symbol in SYMBOLS.items():
        lines.append(asp.fact("symbol", sid))
        for fit in sorted(symbol.fits):
            lines.append(asp.fact("symbol_fits", sid, fit))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("chosen_tool", params.tool),
            asp.fact("tool_precision", params.tool, TOOLS[params.tool].precision),
            asp.fact("helper_present") if params.helper_style != "absent" else "",
        ]
    )
    rules = extra + "\n" + "wobble(Trait, Tool) :- trait(Trait), chosen_tool(Tool), not careful_trait(Trait), tool_precision(Tool,P), P < 3."
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n{rules}\n#show outcome/1.\n")
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of_params(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld: a child helps prepare a ceremony by transcribing a promise and drawing a symbol."
    )
    ap.add_argument("--ceremony", choices=CEREMONIES)
    ap.add_argument("--honoree", choices=HONOREES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--symbol", choices=SYMBOLS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "woman"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper-style", choices=HELPER_STYLES)
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


def _pick_child(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.tool:
        material = MATERIALS[args.material]
        tool = TOOLS[args.tool]
        if not can_mark(material, tool):
            raise StoryError(explain_material_tool(material, tool))
    if args.value and args.symbol:
        value = VALUES[args.value]
        symbol = SYMBOLS[args.symbol]
        if not good_symbol(value, symbol):
            raise StoryError(explain_symbol(value, symbol))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ceremony is None or combo[0] == args.ceremony)
        and (args.honoree is None or combo[1] == args.honoree)
        and (args.value is None or combo[2] == args.value)
        and (args.material is None or combo[3] == args.material)
        and (args.tool is None or combo[4] == args.tool)
        and (args.symbol is None or combo[5] == args.symbol)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ceremony, honoree, value, material, tool, symbol = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = _pick_child(rng, child_gender)
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman"])
    helper_name = {"mother": "Mama", "father": "Dad", "woman": "Auntie"}[helper_type]
    trait = args.trait or rng.choice(TRAITS)
    helper_style = args.helper_style or rng.choice(["gentle", "cheerful"])
    return StoryParams(
        ceremony=ceremony,
        honoree=honoree,
        value=value,
        material=material,
        tool=tool,
        symbol=symbol,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
        helper_style=helper_style,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        ceremony = CEREMONIES[params.ceremony]
        honoree = HONOREES[params.honoree]
        value = VALUES[params.value]
        material = MATERIALS[params.material]
        tool = TOOLS[params.tool]
        symbol = SYMBOLS[params.symbol]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err}.)") from err

    if not can_mark(material, tool):
        raise StoryError(explain_material_tool(material, tool))
    if not good_symbol(value, symbol):
        raise StoryError(explain_symbol(value, symbol))

    world = tell(
        ceremony=ceremony,
        honoree=honoree,
        value=value,
        material=material,
        tool=tool,
        symbol=symbol,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        helper_style=params.helper_style,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ceremony, honoree, value, material, tool, symbol) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{c:14}" for c in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.value} at {p.ceremony} "
                f"({p.material}, {p.tool}, {outcome_of_params(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
