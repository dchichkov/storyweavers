#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py
====================================================================================

A standalone storyworld for a tiny detective tale: a child notices clues on a
trouser leg and a finger, follows their texture carefully, solves a small
mystery, and learns not to jump to blame before looking closely.

Run it
------
    python storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py --item badge --place fort
    python storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py --material sand --place kitchen
    python storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py --all --qa
    python storyworlds/worlds/gpt-5.4/texture_trouser_finger_problem_solving_lesson_learned.py --verify
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
CLEAR_MIN = 2


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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Place:
    id: str
    label: str
    phrase: str
    scene: str
    material_options: set[str] = field(default_factory=set)
    hiding_line: str = ""
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    use_line: str
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
class Material:
    id: str
    label: str
    texture: str
    finger_mark: str
    trouser_mark: str
    place_text: str
    careful_action: str
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
class Mover:
    id: str
    label: str
    type: str
    role_word: str
    move_verb: str
    motive: str
    feeling: str
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
class ClearMethod:
    id: str
    sense: int
    label: str
    line: str
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


def _r_observe_marks(world: World) -> list[str]:
    detective = world.get("detective")
    helper = world.get("helper")
    material = world.facts["material_cfg"]
    out: list[str] = []
    if detective.meters["inspection"] < THRESHOLD:
        return out
    if helper.meters["finger_mark"] >= THRESHOLD:
        sig = ("finger_clue", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.meters["clues"] += 1
            out.append(
                f"{detective.id} noticed {material.finger_mark} on one finger."
            )
    if helper.meters["trouser_mark"] >= THRESHOLD:
        sig = ("trouser_clue", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.meters["clues"] += 1
            out.append(
                f"{detective.pronoun('possessive').capitalize()} eyes dropped to "
                f"{helper.id}'s trouser leg, where {material.trouser_mark} clung there too."
            )
    return out


def _r_match_place(world: World) -> list[str]:
    detective = world.get("detective")
    place_cfg = world.facts["place_cfg"]
    material = world.facts["material_cfg"]
    out: list[str] = []
    if detective.meters["clues"] < 2:
        return out
    sig = ("matched_place", place_cfg.id, material.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["reasoning"] += 1
    out.append(
        f"The same texture fit only one spot in the room: {place_cfg.place_text}."
    )
    return out


def _r_ask_softens(world: World) -> list[str]:
    detective = world.get("detective")
    helper = world.get("helper")
    if detective.meters["asked_kindly"] < THRESHOLD:
        return []
    sig = ("softened", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["trust"] += 1
    helper.memes["shame"] = max(0.0, helper.memes["shame"] - 1.0)
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="observe_marks", tag="physical", apply=_r_observe_marks),
    Rule(name="match_place", tag="reasoning", apply=_r_match_place),
    Rule(name="ask_softens", tag="social", apply=_r_ask_softens),
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
        for sent in produced:
            world.say(sent)
    return produced


def clue_fits(place: Place, material: Material) -> bool:
    return material.id in place.material_options


def method_is_clear(method: ClearMethod) -> bool:
    return method.sense >= CLEAR_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id in ITEMS:
            for material_id, material in MATERIALS.items():
                if not clue_fits(place, material):
                    continue
                for mover_id in MOVERS:
                    combos.append((place_id, item_id, material_id, mover_id))
    return combos


def explain_rejection(place: Place, material: Material) -> str:
    return (
        f"(No story: {material.label} does not belong around {place.label}, so the "
        f"texture clue would point nowhere honest. Choose a place that could really "
        f"leave that clue.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in METHODS.values() if m.sense >= CLEAR_MIN))
    return (
        f"(Refusing method '{method_id}': it is too hasty for a careful detective "
        f"story. Try one of these clearer methods: {better}.)"
    )


def predict_case(place: Place, material: Material, method: ClearMethod) -> dict:
    return {
        "two_clues": clue_fits(place, material),
        "solved_carefully": clue_fits(place, material) and method_is_clear(method),
    }


def introduce(world: World, detective: Entity, helper: Entity, item: ItemCfg) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"After school, {detective.id} turned the living room into a tiny detective office. "
        f"{detective.pronoun('subject').capitalize()} had a notebook, a serious whisper, "
        f"and a grand plan to guard {item.phrase}."
    )
    world.say(
        f"{helper.id} was the assistant for the afternoon, proud to stand beside the sofa "
        f"and listen for the smallest clue."
    )


def present_item(world: World, detective: Entity, item: ItemCfg) -> None:
    world.say(
        f"{item.use_line} Then, when {detective.id} looked back, {item.label} was gone."
    )
    detective.memes["alarm"] += 1
    detective.memes["resolve"] += 1


def inspect(world: World, detective: Entity) -> None:
    detective.meters["inspection"] += 1
    world.say(
        f'"Case of the Missing {world.facts["item_cfg"].label.title()}," {detective.id} murmured. '
        f'{detective.pronoun("subject").capitalize()} touched the floor with one finger, '
        f'squinted at the chairs, and decided to look before guessing.'
    )
    propagate(world, narrate=False)


def transfer_clues(world: World, helper: Entity, material: Material, mover: Mover) -> None:
    helper.meters["finger_mark"] += 1
    helper.meters["trouser_mark"] += 1
    helper.attrs["moved_item"] = True
    helper.attrs["mover_kind"] = mover.id
    helper.memes["shame"] += 1
    helper.memes["care"] += 1


def notice(world: World, detective: Entity, helper: Entity, material: Material) -> None:
    world.say(
        f"When {helper.id} shifted beside the lamp, {detective.id} saw something odd. "
        f"{material.finger_mark.capitalize()} showed on {helper.id}'s finger, and the same "
        f"{material.texture} dust brushed one knee of {helper.pronoun('possessive')} trouser leg."
    )
    detective.meters["inspection"] += 1
    propagate(world, narrate=True)


def think(world: World, detective: Entity, place: Place, material: Material) -> None:
    detective.memes["focus"] += 1
    world.say(
        f'{detective.id} did not shout. "{material.label.capitalize()} has a very special '
        f'texture," {detective.pronoun("subject")} whispered. "{place.scene} is the only place '
        f'here that would leave marks like that."'
    )
    propagate(world, narrate=True)


def ask(world: World, detective: Entity, helper: Entity, mover: Mover, method: ClearMethod) -> None:
    if method.id == "blame":
        detective.meters["asked_hard"] += 1
        helper.memes["shame"] += 1
        world.say(
            f'"You took it!" {detective.id} burst out before thinking. {helper.id} looked down '
            f'and rubbed {helper.pronoun("possessive")} finger against {helper.pronoun("possessive")} '
            f'trouser seam.'
        )
    else:
        detective.meters["asked_kindly"] += 1
        world.say(
            f'{detective.id} took a slow breath. "{method.line}" {detective.pronoun("subject")} asked. '
            f'{helper.id} blinked, then nodded.'
        )
    propagate(world, narrate=False)
    helper.attrs["confessed"] = True
    helper.attrs["motive_text"] = mover.motive


def confession(world: World, helper: Entity, item: ItemCfg, place: Place, mover: Mover) -> None:
    helper.memes["relief"] += 1
    world.say(
        f'"I did move {item.label}," {helper.id} said softly. "I only {mover.move_verb} it because '
        f'{mover.motive}."'
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} pointed toward {place.phrase} and added that "
        f"{helper.pronoun('subject')} had knelt there for just a moment."
    )


def recover(world: World, detective: Entity, helper: Entity, item: ItemCfg, place: Place) -> None:
    detective.meters["solved"] += 1
    item_ent = world.get("item")
    item_ent.attrs["found_at"] = place.id
    item_ent.meters["found"] += 1
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they hurried to {place.phrase}. Tucked exactly where the clue had pointed, "
        f"they found {item.phrase} waiting."
    )
    world.say(
        f'{detective.id} lifted it high. "Case solved," {detective.pronoun("subject")} said, '
        f'and this time {helper.id} smiled too.'
    )


def lesson(world: World, detective: Entity, helper: Entity, method: ClearMethod) -> None:
    detective.memes["lesson"] += 1
    helper.memes["trust"] += 1
    if method_is_clear(method):
        world.say(
            f"On the way back, {detective.id} tapped the notebook with one finger. "
            f"{detective.pronoun('subject').capitalize()} had learned that a good detective looks at "
            f"every clue, asks kindly, and lets the truth arrive step by step."
        )
    else:
        world.say(
            f"On the way back, {detective.id} felt a hot blush. "
            f"{detective.pronoun('subject').capitalize()} had solved the case, but too quickly blamed "
            f"before hearing the whole story."
        )
    world.say(
        f"After that, both children remembered the same lesson: careful problem solving is better than "
        f"fast guessing, because clues tell the truth when people listen."
    )


def ending_image(world: World, detective: Entity, helper: Entity, item: ItemCfg) -> None:
    world.say(
        f"By evening, {item.label} was back in its proper place, the notebook lay open on the rug, "
        f"and {detective.id} and {helper.id} were already whispering about their next gentle mystery."
    )


def tell(
    place: Place,
    item_cfg: ItemCfg,
    material: Material,
    mover_cfg: Mover,
    method: ClearMethod,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    helper_name: str = "Max",
    helper_type: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        role="detective",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        attrs={"moved_item": False, "confessed": False, "mover_kind": mover_cfg.id},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="object",
        label=item_cfg.label,
        attrs={"found_at": "", "owner": detective.id},
    ))
    world.facts.update(
        place_cfg=place,
        item_cfg=item_cfg,
        material_cfg=material,
        mover_cfg=mover_cfg,
        method_cfg=method,
        detective=detective,
        helper=helper,
        parent=parent,
        item=item,
    )

    transfer_clues(world, helper, material, mover_cfg)

    introduce(world, detective, helper, item_cfg)
    present_item(world, detective, item_cfg)

    world.para()
    inspect(world, detective)
    notice(world, detective, helper, material)
    think(world, detective, place, material)

    world.para()
    ask(world, detective, helper, mover_cfg, method)
    confession(world, helper, item_cfg, place, mover_cfg)
    recover(world, detective, helper, item_cfg, place)

    world.para()
    lesson(world, detective, helper, method)
    ending_image(world, detective, helper, item_cfg)

    world.facts.update(
        solved=item.attrs["found_at"] == place.id,
        careful=method_is_clear(method),
        clue_count=int(detective.meters["clues"]),
    )
    return world


PLACES = {
    "fort": Place(
        id="fort",
        label="the blanket fort",
        phrase="the blanket fort by the armchair",
        scene="that woolly blanket fort by the armchair",
        material_options={"lint", "crumbs"},
        hiding_line="inside the blanket fort",
        tags={"fort", "room"},
    ),
    "shelf": Place(
        id="shelf",
        label="the low bookshelf",
        phrase="the low bookshelf by the window",
        scene="the dusty shelf by the window",
        material_options={"dust"},
        hiding_line="behind the books on the shelf",
        tags={"shelf", "room"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen mat",
        phrase="the kitchen mat near the fruit bowl",
        scene="the sandy little mat near the fruit bowl",
        material_options={"sand", "crumbs"},
        hiding_line="beside the kitchen mat",
        tags={"kitchen", "room"},
    ),
}

ITEMS = {
    "badge": ItemCfg(
        id="badge",
        label="badge",
        phrase="the shiny detective badge",
        use_line="It had been standing on a cushion like the most important clue in the world.",
        tags={"badge", "detective"},
    ),
    "whistle": ItemCfg(
        id="whistle",
        label="whistle",
        phrase="the brass whistle",
        use_line="It had been waiting on the table for the grand beginning of patrol time.",
        tags={"whistle", "detective"},
    ),
    "map": ItemCfg(
        id="map",
        label="map",
        phrase="the folded treasure map",
        use_line="It had been spread across the rug, ready for one more secret mission.",
        tags={"map", "detective"},
    ),
}

MATERIALS = {
    "lint": Material(
        id="lint",
        label="lint",
        texture="soft fuzzy",
        finger_mark="soft gray lint",
        trouser_mark="soft gray lint",
        place_text="a blanket fort sheds tiny bits of fuzzy lint",
        careful_action="brushed the fuzz gently away",
        tags={"texture", "cloth"},
    ),
    "dust": Material(
        id="dust",
        label="dust",
        texture="dry powdery",
        finger_mark="a thin brown line of dust",
        trouser_mark="a powdery dust mark",
        place_text="a low shelf leaves dry dust on fingers and knees",
        careful_action="wiped the dust off carefully",
        tags={"texture", "dust"},
    ),
    "sand": Material(
        id="sand",
        label="sand",
        texture="gritty",
        finger_mark="gritty grains of sand",
        trouser_mark="gritty pale sand",
        place_text="the kitchen mat near the fruit bowl always held a little gritty sand from the doorway",
        careful_action="rubbed the grains between two fingers",
        tags={"texture", "sand"},
    ),
    "crumbs": Material(
        id="crumbs",
        label="crumbs",
        texture="crumbly",
        finger_mark="tiny biscuit crumbs",
        trouser_mark="crumbly golden specks",
        place_text="snack crumbs collect near the fort and the kitchen mat",
        careful_action="picked up one crumb with a careful finger",
        tags={"texture", "crumbs"},
    ),
}

MOVERS = {
    "protect": Mover(
        id="protect",
        label="protector",
        type="child",
        role_word="helper",
        move_verb="moved",
        motive="it looked close to the edge and might fall",
        feeling="worried",
        tags={"careful"},
    ),
    "tidy": Mover(
        id="tidy",
        label="tidier",
        type="child",
        role_word="helper",
        move_verb="tucked",
        motive="the room looked messy and wanted to make it neat",
        feeling="earnest",
        tags={"tidy"},
    ),
    "practice": Mover(
        id="practice",
        label="practicer",
        type="child",
        role_word="helper",
        move_verb="borrowed",
        motive="wanted one quick turn pretending to solve a case too",
        feeling="hopeful",
        tags={"play"},
    ),
}

METHODS = {
    "ask": ClearMethod(
        id="ask",
        sense=3,
        label="ask kindly",
        line="Did you touch the missing thing, or did you notice where it went",
        qa_text="asked kindly about the clue before deciding anything",
        tags={"kind"},
    ),
    "compare": ClearMethod(
        id="compare",
        sense=3,
        label="compare clues",
        line="I think these marks match one place. Will you help me check it",
        qa_text="compared the clues and invited help checking the place they matched",
        tags={"kind"},
    ),
    "blame": ClearMethod(
        id="blame",
        sense=1,
        label="blame at once",
        line="You must have taken it",
        qa_text="blamed first and listened later",
        tags={"hasty"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "Ruby", "Ivy", "Ella", "June"]
BOY_NAMES = ["Max", "Leo", "Ben", "Theo", "Sam", "Eli", "Finn", "Noah"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "patient"]


@dataclass
class StoryParams:
    place: str
    item: str
    material: str
    mover: str
    method: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    parent: str
    trait: str
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
    "texture": [
        (
            "What is texture?",
            "Texture is how something feels when you touch it. Something can feel fuzzy, gritty, smooth, or crumbly.",
        )
    ],
    "finger": [
        (
            "Why can a finger help you notice a clue?",
            "A finger can feel tiny things that eyes might miss at first. That is why detectives sometimes touch gently and carefully.",
        )
    ],
    "trouser": [
        (
            "What is a trouser leg?",
            "A trouser leg is the long part of trousers that covers one leg. Dust, lint, or mud can cling to it and show where someone has been.",
        )
    ],
    "dust": [
        (
            "Why does dust stick to your clothes?",
            "Dust is made of tiny dry bits, and it can cling to fabric when you brush against a shelf or floor. Light-colored dust is often easy to spot on dark clothes.",
        )
    ],
    "sand": [
        (
            "Why does sand feel gritty?",
            "Sand feels gritty because it is made of many tiny hard grains. When you rub it with your finger, the grains press and slide against your skin.",
        )
    ],
    "crumbs": [
        (
            "What are crumbs?",
            "Crumbs are tiny broken bits of food like biscuit or bread. They can fall onto tables, mats, or clothes.",
        )
    ],
    "cloth": [
        (
            "Why does a blanket leave lint?",
            "Some blankets shed tiny soft fibers called lint. Those fuzzy bits can stick to sleeves or trousers.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks questions, and thinks carefully about what happened. A good detective does not guess too fast.",
        )
    ],
    "kind": [
        (
            "Why is it better to ask kindly when there is a problem?",
            "Kind questions help people tell the truth without feeling frightened. When people feel safe, it is easier to solve the problem together.",
        )
    ],
}

KNOWLEDGE_ORDER = ["texture", "finger", "trouser", "dust", "sand", "crumbs", "cloth", "detective", "kind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    material = f["material_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "texture", "trouser", and "finger".',
        f"Tell a gentle mystery where {detective.id} notices {material.label} on {helper.id}'s finger and trouser leg, then solves the case of the missing {item.label} near {place.label}.",
        f"Write a problem-solving story with a lesson learned: a child detective follows clues carefully instead of blaming too fast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    material = f["material_cfg"]
    mover = f["mover_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {helper.id}, the helper in the little case. Together they solved the mystery of the missing {item.label}.",
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. Its disappearance started the mystery and gave {detective.id} a case to solve.",
        ),
        (
            f"What clues did {detective.id} find?",
            f"{detective.id} noticed {material.finger_mark} on {helper.id}'s finger and {material.trouser_mark} on the trouser leg. Those two matching clues mattered because they both pointed to the same kind of place.",
        ),
        (
            f"How did the clues help solve the problem?",
            f"The clues had a special texture that matched {place.label}. Because the marks on the finger and trouser leg fit that place, {detective.id} knew where to search next.",
        ),
        (
            f"Why had {helper.id} moved the {item.label}?",
            f"{helper.id} moved it because {mover.motive}. It was not done to be mean, which is why the careful questions mattered.",
        ),
        (
            "How was the case solved?",
            f"{detective.id} {method.qa_text}, and then the children looked in {place.phrase}. They found {item.phrase} there and understood what had really happened.",
        ),
    ]
    if method_is_clear(method):
        qa.append(
            (
                "What lesson did the detective learn?",
                f"{detective.id} learned to look closely, compare clues, and speak kindly before deciding anything. That lesson helped solve the mystery without hurting anyone's feelings.",
            )
        )
    else:
        qa.append(
            (
                "What lesson did the detective learn?",
                f"{detective.id} learned that blaming too quickly can make a problem harder. The truth came out only after slowing down and listening.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"texture", "finger", "trouser", "detective"}
    tags |= set(f["material_cfg"].tags)
    if method_is_clear(f["method_cfg"]):
        tags.add("kind")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fort",
        item="badge",
        material="lint",
        mover="protect",
        method="ask",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Max",
        helper_type="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="shelf",
        item="map",
        material="dust",
        mover="practice",
        method="compare",
        detective_name="Leo",
        detective_type="boy",
        helper_name="Mia",
        helper_type="girl",
        parent="father",
        trait="thoughtful",
    ),
    StoryParams(
        place="kitchen",
        item="whistle",
        material="sand",
        mover="tidy",
        method="ask",
        detective_name="Ruby",
        detective_type="girl",
        helper_name="Finn",
        helper_type="boy",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        place="fort",
        item="map",
        material="crumbs",
        mover="practice",
        method="compare",
        detective_name="Theo",
        detective_type="boy",
        helper_name="Ivy",
        helper_type="girl",
        parent="father",
        trait="steady",
    ),
]


ASP_RULES = r"""
fits(P,M) :- place(P), material(M), clue_fits(P,M).
clear_method(X) :- method(X), sense(X,S), clear_min(MN), S >= MN.
valid(P,I,M,V) :- place(P), item(I), material(M), mover(V), fits(P,M).

solved(P,M,X) :- fits(P,M), clear_method(X).
solved(P,M,X) :- fits(P,M), method(X), not clear_method(X).

careful_outcome(X) :- clear_method(X).
careful_outcome(X) :- method(X), not clear_method(X), false.

outcome(careful) :- chosen_place(P), chosen_material(M), chosen_method(X), fits(P,M), clear_method(X).
outcome(hasty) :- chosen_place(P), chosen_material(M), chosen_method(X), fits(P,M), not clear_method(X).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    for vid in MOVERS:
        lines.append(asp.fact("mover", vid))
    for meth_id, method in METHODS.items():
        lines.append(asp.fact("method", meth_id))
        lines.append(asp.fact("sense", meth_id, method.sense))
    for pid, place in PLACES.items():
        for mid in sorted(place.material_options):
            lines.append(asp.fact("clue_fits", pid, mid))
    lines.append(asp.fact("clear_min", CLEAR_MIN))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not clue_fits(PLACES[params.place], MATERIALS[params.material]):
        return "?"
    return "careful" if method_is_clear(METHODS[params.method]) else "hasty"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld about texture clues, a missing object, and a lesson in careful problem solving."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.material:
        place = PLACES[args.place]
        material = MATERIALS[args.material]
        if not clue_fits(place, material):
            raise StoryError(explain_rejection(place, material))
    if args.method and not method_is_clear(METHODS[args.method]):
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.material is None or combo[2] == args.material)
        and (args.mover is None or combo[3] == args.mover)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, material, mover = rng.choice(sorted(combos))
    method_choices = sorted(mid for mid, method in METHODS.items() if method_is_clear(method))
    method = args.method or rng.choice(method_choices)

    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_type)
    helper_name = args.helper_name or _pick_name(rng, helper_type, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        item=item,
        material=material,
        mover=mover,
        method=method,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.mover not in MOVERS:
        raise StoryError(f"(Unknown mover: {params.mover})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not clue_fits(PLACES[params.place], MATERIALS[params.material]):
        raise StoryError(explain_rejection(PLACES[params.place], MATERIALS[params.material]))
    if not method_is_clear(METHODS[params.method]):
        raise StoryError(explain_method(params.method))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        material=MATERIALS[params.material],
        mover_cfg=MOVERS[params.mover],
        method=METHODS[params.method],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent,
        trait=params.trait,
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

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Random resolve failed for seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

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
        print(f"{len(combos)} compatible (place, item, material, mover) combos:\n")
        for place, item, material, mover in combos:
            print(f"  {place:8} {item:7} {material:8} {mover}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.item} at {p.place} ({p.material}, {p.mover})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
