#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py
==============================================================================

A standalone story world for a pirate-flavored mystery with a happy ending.

Two children turn a quiet place into a pirate adventure. Their special lotus
object stops working just when they need it to solve a treasure clue. One child
wants a quick rough fix, the other worries the object will break. A calm grown-up
from radiology uses a picture to look safely inside, finds the hidden problem,
and repairs it the sensible way. The mystery is solved, the treasure hunt can go
on, and the ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py --item lotus_lantern
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py --fault battery_flipped
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py --fix pull_string
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/lotus_radiology_happy_ending_mystery_to_solve.py --qa --json
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "gentle", "thoughtful"}
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    delicate: bool = False
    sealed: bool = False
    metal_inside: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "technician"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
        }.get(self.type, self.type)
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
    rig: str
    title_a: str
    title_b: str
    goal: str
    place_phrase: str
    crew_word: str
    send_off: str
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    purpose: str
    symptom: str
    casing: str
    opened_by: set[str] = field(default_factory=set)
    faults: set[str] = field(default_factory=set)
    delicate: bool = True
    sealed: bool = True
    metal_inside: bool = True
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
class Fault:
    id: str
    label: str
    symptom_line: str
    reveal: str
    hidden_piece: str
    effect_key: str
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
class Fix:
    id: str
    label: str
    opens: str
    handles: set[str] = field(default_factory=set)
    sense: int = 3
    action_text: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_blocked_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["blocked"] < THRESHOLD:
        return []
    sig = ("blocked_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__worry__"]


def _r_scan_clue(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["scanned"] < THRESHOLD or item.meters["fault_found"] < THRESHOLD:
        return []
    sig = ("scan_clue", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["hope"] += 1
    helper = world.get("helper")
    helper.memes["confidence"] += 1
    return ["__found__"]


def _r_repair_restore(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repair_restore", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["blocked"] = 0.0
    item.meters["working"] += 1
    item.meters[world.facts["effect_key"]] += 1
    world.get("mystery").meters["solved"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    return ["__restored__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_worry", tag="emotional", apply=_r_blocked_worry),
    Rule(name="scan_clue", tag="mystery", apply=_r_scan_clue),
    Rule(name="repair_restore", tag="physical", apply=_r_repair_restore),
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


def supports_fault(item: MysteryItem, fault: Fault) -> bool:
    return fault.id in item.faults


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def compatible_fix(item: MysteryItem, fault: Fault, fix: Fix) -> bool:
    return (
        supports_fault(item, fault)
        and fault.id in fix.handles
        and fix.opens in item.opened_by
        and fix.sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for fault_id, fault in FAULTS.items():
            for fix_id, fix in FIXES.items():
                if compatible_fix(item, fault, fix):
                    combos.append((item_id, fault_id, fix_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_wait(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority >= BRAVERY_INIT


def explain_combo_rejection(item: MysteryItem, fault: Fault, fix: Fix) -> str:
    if not supports_fault(item, fault):
        return (
            f"(No story: {item.label} does not plausibly hide the problem "
            f"'{fault.label}', so radiology would not reveal that mystery here.)"
        )
    if fix.opens not in item.opened_by:
        return (
            f"(No story: {fix.label} opens the wrong part of the {item.label}. "
            f"Pick a fix that matches its casing.)"
        )
    if fault.id not in fix.handles:
        return (
            f"(No story: {fix.label} would not solve the hidden problem "
            f"'{fault.label}'. The repair must fit what radiology finds.)"
        )
    if fix.sense < SENSE_MIN:
        return (
            f"(No story: {fix.label} is known here but rejected as too rough "
            f"for a happy mystery story.)"
        )
    return "(No story: that combination is not reasonable.)"


def explain_fix_rejection(fix: Fix) -> str:
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix.id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_scan(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["scanned"] += 1
    item.meters["fault_found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": item.meters["fault_found"] >= THRESHOLD,
        "hope": sum(kid.memes["hope"] for kid in sim.kids()),
    }


def pirate_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the children's garden into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} cheered. '
        f'"Today we will find {theme.goal}!"'
    )


def reach_lotus_place(world: World, theme: Theme, item: MysteryItem) -> None:
    world.say(
        f"The last clue led them to {theme.place_phrase}, where a {item.label} "
        f"waited beside the water."
    )


def discover_problem(world: World, a: Entity, item: MysteryItem, fault: Fault) -> None:
    obj = world.get("item")
    obj.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {a.id} tried to use the {item.label}, {item.symptom}. "
        f"{fault.symptom_line}"
    )


def tempt_quick_fix(world: World, a: Entity, item: MysteryItem) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} frowned. "Maybe I should thump it a little," {a.pronoun()} said. '
        f'"Or pry it open right now."'
    )


def warning(world: World, b: Entity, a: Entity, item: MysteryItem, helper: Entity) -> None:
    pred = predict_scan(world)
    b.memes["caution"] += 1
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_hope"] = pred["hope"]
    older_bit = ""
    if b.memes["caution"] >= 6:
        older_bit = f" {b.id} held the {item.label} extra carefully, already sure rough hands would only make the mystery worse."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, it belongs to the garden, '
        f'and it feels delicate. {helper.label_word.capitalize()} works in radiology. '
        f'Radiology can help us look inside without breaking it."{older_bit}'
    )


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the careful way {b.id} was holding the treasure piece and took a slow breath. '
        f'"All right," {a.pronoun()} said. "Real captains do not smash clues."'
    )


def jostle_once(world: World, a: Entity, item: MysteryItem) -> None:
    a.memes["defiance"] += 1
    obj = world.get("item")
    obj.meters["jostled"] += 1
    if item.delicate:
        obj.meters["loose_cover"] += 1
    world.say(
        f"Before anyone could stop {a.id}, {a.pronoun()} gave the {item.label} one impatient shake. "
        f"It rattled sadly, but it still would not work."
    )


def go_to_radiology(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"So the children carried the mystery to {helper.label_word}'s room in radiology, "
        f"where soft screens glowed and everything was kept gentle and clean."
    )


def scan_item(world: World, helper: Entity, fault: Fault) -> None:
    item = world.get("item")
    item.meters["scanned"] += 1
    item.meters["fault_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.label_word.capitalize()} smiled and slid a small picture plate under the {item.label}. '
        f'In a moment, radiology showed the answer: {fault.reveal}.'
    )


def explain_mystery(world: World, helper: Entity, item: MysteryItem, fault: Fault) -> None:
    world.say(
        f'"There is our mystery," {helper.label_word} said softly. '
        f'"The hidden {fault.hidden_piece} is stopping the part that should {item.purpose}."'
    )


def repair(world: World, helper: Entity, fix: Fix) -> None:
    item = world.get("item")
    item.meters["repaired"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.label_word} {fix.action_text}."
    )


def proof_of_change(world: World, a: Entity, b: Entity, item: MysteryItem, theme: Theme, prize: str) -> None:
    if item.id == "lotus_compass":
        proof = f"the needle swung true toward the painted X on their map"
    elif item.id == "lotus_lantern":
        proof = "warm gold light bloomed across the petals"
    else:
        proof = "the tiny chime rang out in a bright, secret tune"
    world.say(
        f"At once, {proof}. The mystery was solved, and the next clue pointed them straight to {prize}."
    )
    world.say(
        f'{a.id} laughed, {b.id} clapped, and even {helper_name(world)} looked pleased. '
        f'Together the little {theme.crew_word} {theme.send_off}.'
    )


def helper_name(world: World) -> str:
    return world.get("helper").label_word


def celebration(world: World, a: Entity, b: Entity, prize: str) -> None:
    world.say(
        f"Inside the treasure box they found {prize}, and each child got one to keep in a pocket like a real pirate charm."
    )
    comfort = world.facts.get("comfort")
    if comfort:
        world.say(f"{b.id} tucked the tiny prize beside {b.pronoun('possessive')} {comfort} and beamed all the way home.")


def tell(
    theme: Theme,
    item_cfg: MysteryItem,
    fault_cfg: Fault,
    fix_cfg: Fix,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "aunt",
    helper_name_text: str = "Aunt May",
    trait: str = "careful",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
    comfort: str = "",
    prize: str = "shiny shell stickers",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation, "comfort": comfort},
    ))
    helper_type = "aunt" if parent_type == "aunt" else parent_type
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_name_text,
    ))
    mystery = world.add(Entity(id="mystery", type="mystery", label="the mystery"))
    item = world.add(Entity(
        id="item",
        type="treasure_item",
        label=item_cfg.label,
        delicate=item_cfg.delicate,
        sealed=item_cfg.sealed,
        metal_inside=item_cfg.metal_inside,
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    mystery.meters["unsolved"] = 1.0
    item.meters["blocked"] = 0.0
    item.meters["scanned"] = 0.0
    item.meters["fault_found"] = 0.0
    item.meters["repaired"] = 0.0
    item.meters["working"] = 0.0
    world.facts["effect_key"] = fault_cfg.effect_key
    item.meters[fault_cfg.effect_key] = 0.0
    world.facts["comfort"] = comfort

    pirate_setup(world, a, b, theme)
    reach_lotus_place(world, theme, item_cfg)
    world.para()
    discover_problem(world, a, item_cfg, fault_cfg)
    tempt_quick_fix(world, a, item_cfg)
    warning(world, b, a, item_cfg, helper)

    waited = would_wait(relation, instigator_age, cautioner_age, trait)
    if waited:
        back_down(world, a, b)
    else:
        jostle_once(world, a, item_cfg)

    world.para()
    go_to_radiology(world, helper)
    scan_item(world, helper, fault_cfg)
    explain_mystery(world, helper, item_cfg, fault_cfg)
    world.para()
    repair(world, helper, fix_cfg)
    proof_of_change(world, a, b, item_cfg, theme, prize)
    celebration(world, a, b, prize)

    world.facts.update(
        instigator=a,
        cautioner=b,
        helper=helper,
        mystery=mystery,
        item=item,
        theme=theme,
        item_cfg=item_cfg,
        fault_cfg=fault_cfg,
        fix_cfg=fix_cfg,
        waited=waited,
        relation=relation,
        prize=prize,
        solved=mystery.meters["solved"] >= THRESHOLD,
        jostled=item.meters["jostled"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a green island sea",
        rig="A bench became their ship, a rolled paper tube became a spyglass, and a crinkled map showed where the treasure should be.",
        title_a="Captain",
        title_b="First Mate",
        goal="the hidden lotus treasure",
        place_phrase="the pond with the wide lotus leaves",
        crew_word="pirates",
        send_off="hurried back across the garden with their map flapping behind them",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a secret harbor",
        rig="The low wall became a dock, a scarf became a flag, and their map had a red path curling toward the water.",
        title_a="Captain",
        title_b="Lookout",
        goal="the harbor chest",
        place_phrase="the quiet lotus pond",
        crew_word="sailors",
        send_off="ran laughing toward the last treasure mark",
    ),
    "island": Theme(
        id="island",
        scene="a whispering island",
        rig="A stone path became a ship deck, a pencil became a mast, and their map promised treasure near the reeds.",
        title_a="Captain",
        title_b="Scout",
        goal="the reef-side chest",
        place_phrase="the lotus pool by the bright windows",
        crew_word="sea explorers",
        send_off="sailed on in their imaginations, brave and delighted",
    ),
}

ITEMS = {
    "lotus_compass": MysteryItem(
        id="lotus_compass",
        label="lotus compass",
        phrase="a brass lotus compass",
        purpose="point to the next clue",
        symptom="its needle only quivered and leaned the wrong way",
        casing="a tiny round back",
        opened_by={"back_plate"},
        faults={"bead_jam", "clip_slip"},
        delicate=True,
        sealed=True,
        metal_inside=True,
        tags={"lotus", "compass", "radiology"},
    ),
    "lotus_lantern": MysteryItem(
        id="lotus_lantern",
        label="lotus lantern",
        phrase="a painted lotus lantern",
        purpose="glow and show the hidden path",
        symptom="nothing shone inside the petals, not even a wink",
        casing="a little battery hatch",
        opened_by={"battery_hatch"},
        faults={"battery_flipped", "coin_wedge"},
        delicate=True,
        sealed=True,
        metal_inside=True,
        tags={"lotus", "light", "radiology"},
    ),
    "lotus_music_box": MysteryItem(
        id="lotus_music_box",
        label="lotus music box",
        phrase="a carved lotus music box",
        purpose="play the tune of the next clue",
        symptom="it gave only a dull click instead of a song",
        casing="a small side panel",
        opened_by={"side_panel"},
        faults={"shell_jam", "spring_pin"},
        delicate=True,
        sealed=True,
        metal_inside=True,
        tags={"lotus", "music", "radiology"},
    ),
}

FAULTS = {
    "bead_jam": Fault(
        id="bead_jam",
        label="bead_jam",
        symptom_line="Something tiny was skittering inside as if a bead had gone wandering.",
        reveal="a small bead had rolled under the compass needle",
        hidden_piece="bead",
        effect_key="points",
        tags={"compass", "hidden_part"},
    ),
    "clip_slip": Fault(
        id="clip_slip",
        label="clip_slip",
        symptom_line="A faint tick-tick came from inside, but the arrow would not settle.",
        reveal="a little metal clip had slipped across the needle's path",
        hidden_piece="clip",
        effect_key="points",
        tags={"compass", "hidden_part"},
    ),
    "battery_flipped": Fault(
        id="battery_flipped",
        label="battery_flipped",
        symptom_line="When they tilted it, they heard a soft tap from the battery chamber.",
        reveal="one tiny battery had been set in backwards",
        hidden_piece="battery",
        effect_key="glows",
        tags={"light", "battery"},
    ),
    "coin_wedge": Fault(
        id="coin_wedge",
        label="coin_wedge",
        symptom_line="A little clink answered them from deep inside the lamp.",
        reveal="a pretend gold coin had slid into the wire path",
        hidden_piece="coin",
        effect_key="glows",
        tags={"light", "hidden_part"},
    ),
    "shell_jam": Fault(
        id="shell_jam",
        label="shell_jam",
        symptom_line="A tiny scratchy sound inside made it seem as if something was caught in the gears.",
        reveal="a small shell had jammed the turning wheel",
        hidden_piece="shell",
        effect_key="sings",
        tags={"music", "hidden_part"},
    ),
    "spring_pin": Fault(
        id="spring_pin",
        label="spring_pin",
        symptom_line="The box felt as if one piece inside had slipped sideways.",
        reveal="a spring pin had hopped out of its notch",
        hidden_piece="spring pin",
        effect_key="sings",
        tags={"music", "mechanical"},
    ),
}

FIXES = {
    "lift_back": Fix(
        id="lift_back",
        label="lift_back",
        opens="back_plate",
        handles={"bead_jam", "clip_slip"},
        sense=3,
        action_text="turned the little back plate, lifted it carefully, and set the hidden piece back where it belonged",
        qa_text="opened the back plate and set the hidden part right again",
        tags={"repair", "gentle"},
    ),
    "reset_battery": Fix(
        id="reset_battery",
        label="reset_battery",
        opens="battery_hatch",
        handles={"battery_flipped", "coin_wedge"},
        sense=3,
        action_text="opened the battery hatch, straightened the problem inside, and clicked the hatch shut again",
        qa_text="opened the battery hatch and fixed the problem inside",
        tags={"repair", "battery"},
    ),
    "slide_panel": Fix(
        id="slide_panel",
        label="slide_panel",
        opens="side_panel",
        handles={"shell_jam", "spring_pin"},
        sense=3,
        action_text="slid the side panel open, freed the stuck piece, and closed it with a neat little snap",
        qa_text="opened the side panel and freed the stuck piece",
        tags={"repair", "mechanical"},
    ),
    "pull_string": Fix(
        id="pull_string",
        label="pull_string",
        opens="none",
        handles=set(),
        sense=1,
        action_text="pulled at a ribbon and hoped for the best",
        qa_text="pulled at a ribbon",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "gentle", "thoughtful", "curious", "clever"]
COMFORTS = ["stuffed rabbit", "small blue bear", "little plush owl", "toy turtle"]
PRIZES = ["shiny shell stickers", "gold star badges", "tiny paper crowns", "glittery treasure coins"]


@dataclass
class StoryParams:
    theme: str
    item: str
    fault: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    trust: int = 7
    comfort: str = ""
    prize: str = "shiny shell stickers"
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
    "lotus": [(
        "What is a lotus?",
        "A lotus is a water flower that grows up from a pond. Its petals open wide above the water and look calm and bright."
    )],
    "radiology": [(
        "What is radiology?",
        "Radiology is a kind of picture-taking that helps grown-ups look inside things safely. In a hospital, it can help them notice what is hidden without cutting something open first."
    )],
    "compass": [(
        "What does a compass do?",
        "A compass helps you find direction. Its needle turns and settles to point the way."
    )],
    "battery": [(
        "What does a battery do?",
        "A battery stores energy for a small object like a lantern or toy. If it is backwards, the toy may not work."
    )],
    "music": [(
        "Why does a music box stop if something gets stuck inside?",
        "A music box has little moving parts that need room to turn. If a tiny thing blocks them, the tune cannot come out."
    )],
    "repair": [(
        "Why is a gentle repair better than banging on a delicate toy?",
        "A gentle repair fixes the real problem without breaking anything else. Banging might make a small trouble turn into a bigger one."
    )],
    "mystery": [(
        "What helps solve a mystery?",
        "You look for clues, stay calm, and test careful ideas. Good helpers solve mysteries by noticing what others might miss."
    )],
}
KNOWLEDGE_ORDER = ["lotus", "radiology", "compass", "battery", "music", "repair", "mystery"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    item = f["item_cfg"]
    fault = f["fault_cfg"]
    theme = f["theme"]
    if f["waited"]:
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "lotus" and "radiology". Make the mystery about a {item.label} that stops working.',
            f"Tell a gentle mystery where {a.id} wants a quick fix, but {b.id} says they should ask a radiology helper to look inside the {item.label} first.",
            f'Write a happy treasure-hunt story where a careful child prevents a rough mistake, radiology reveals a hidden clue, and the little {theme.crew_word} solve the mystery.'
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "lotus" and "radiology". Make the mystery about a {item.label} that stops working.',
        f"Tell a happy mystery where {a.id} gives the {item.label} one impatient shake, but a calm helper in radiology still finds the hidden trouble and fixes it.",
        f'Write a simple treasure story where the hidden problem is "{fault.label}", the children learn to be gentle with clues, and the ending proves the mystery is solved.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    item = f["item_cfg"]
    fault = f["fault_cfg"]
    fix = f["fix_cfg"]
    theme = f["theme"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, playing as little {theme.crew_word}. It also includes {helper.label_word}, who helps them solve the mystery in radiology."
        ),
        (
            "What mystery did the children need to solve?",
            f"They needed to find out why the {item.label} would not do its job. The treasure hunt could not go on until they knew what hidden trouble was stopping it."
        ),
        (
            f"Why did {b.id} want help instead of a quick rough fix?",
            f"{b.id} thought the {item.label} felt delicate and might break if someone thumped or pried at it. {b.pronoun().capitalize()} trusted radiology to show the hidden problem safely first."
        ),
        (
            "What did radiology reveal?",
            f"Radiology showed that {fault.reveal}. That clue explained exactly why the {item.label} had stopped working."
        ),
        (
            "How was the mystery solved?",
            f"{helper.label_word.capitalize()} {fix.qa_text}. Because the repair matched what radiology found, the hidden trouble was gone and the {item.label} worked again."
        ),
    ]
    if f["waited"]:
        qa.append((
            f"What did {a.id} do after {b.id} warned {a.pronoun('object')}?",
            f"{a.id} backed down and agreed not to force the clue. That choice kept the mystery piece safe for a proper repair."
        ))
    else:
        qa.append((
            f"Did {a.id}'s impatient shake solve the problem?",
            f"No. The shake only made the {item.label} rattle sadly, and it still would not work. The real answer came later when radiology showed what was hidden inside."
        ))
    if f["solved"]:
        qa.append((
            "How do we know the ending was happy?",
            f"We know because the {item.label} worked again and pointed the children to the treasure. The last image shows them laughing together with their prize, which proves the mystery was truly solved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lotus", "radiology", "repair", "mystery"}
    item_id = f["item_cfg"].id
    fault_id = f["fault_cfg"].id
    if item_id == "lotus_compass":
        tags.add("compass")
    elif item_id == "lotus_lantern" or fault_id == "battery_flipped":
        tags.add("battery")
    elif item_id == "lotus_music_box":
        tags.add("music")
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
        flags = [name for name, on in (("delicate", e.delicate), ("sealed", e.sealed), ("metal_inside", e.metal_inside)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        item="lotus_compass",
        fault="bead_jam",
        fix="lift_back",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="Aunt May",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=5,
        comfort="stuffed rabbit",
        prize="shiny shell stickers",
    ),
    StoryParams(
        theme="harbor",
        item="lotus_lantern",
        fault="battery_flipped",
        fix="reset_battery",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        helper="Aunt May",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
        comfort="",
        prize="gold star badges",
    ),
    StoryParams(
        theme="island",
        item="lotus_music_box",
        fault="shell_jam",
        fix="slide_panel",
        instigator="Zoe",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="Aunt May",
        trait="gentle",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        trust=7,
        comfort="little plush owl",
        prize="glittery treasure coins",
    ),
    StoryParams(
        theme="pirates",
        item="lotus_compass",
        fault="clip_slip",
        fix="lift_back",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Noah",
        cautioner_gender="boy",
        helper="Aunt May",
        trait="cautious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=3,
        comfort="",
        prize="tiny paper crowns",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_wait(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "jostled"


ASP_RULES = r"""
item_supports(I, F) :- item_fault(I, F).
compatible_fix(I, F, X) :- item_supports(I, F), fix_handles(X, F), opens(X, O), item_opened_by(I, O), sensible(X).
valid(I, F, X) :- item(I), fault(F), fix(X), compatible_fix(I, F, X).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
waited :- cautioner_older, authority(A), bravery_init(BR), A >= BR.
outcome(waited) :- waited.
outcome(jostled) :- not waited.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for opened in sorted(item.opened_by):
            lines.append(asp.fact("item_opened_by", item_id, opened))
        for fault_id in sorted(item.faults):
            lines.append(asp.fact("item_fault", item_id, fault_id))
    for fault_id in FAULTS:
        lines.append(asp.fact("fault", fault_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("opens", fix_id, fix.opens))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        if fix.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", fix_id))
        for handled in sorted(fix.handles):
            lines.append(asp.fact("fix_handles", fix_id, handled))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "lotus" not in sample.story.lower() or "radiology" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story missing expected content.")
    emit(sample, trace=False, qa=False, header="")


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

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatch = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style lotus mystery story world with a radiology helper. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["aunt", "mother", "father"], default=None)
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(FIXES[args.fix]))
    if args.item and args.fault and args.fix:
        item = ITEMS[args.item]
        fault = FAULTS[args.fault]
        fix = FIXES[args.fix]
        if not compatible_fix(item, fault, fix):
            raise StoryError(explain_combo_rejection(item, fault, fix))

    combos = [
        c for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.fault is None or c[1] == args.fault)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, fault_id, fix_id = rng.choice(sorted(combos))
    theme = args.theme or rng.choice(sorted(THEMES))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    helper = "Aunt May" if (args.parent or "aunt") == "aunt" else ("Mom June" if args.parent == "mother" else "Dad Ravi")
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    comfort = rng.choice(COMFORTS + ["", ""])
    prize = rng.choice(PRIZES)
    return StoryParams(
        theme=theme,
        item=item_id,
        fault=fault_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        helper=helper,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
        comfort=comfort,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        item = ITEMS[params.item]
        fault = FAULTS[params.fault]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None
    if not compatible_fix(item, fault, fix):
        raise StoryError(explain_combo_rejection(item, fault, fix))

    helper_type = "aunt"
    if params.helper.startswith("Mom"):
        helper_type = "mother"
    elif params.helper.startswith("Dad"):
        helper_type = "father"

    world = tell(
        theme=theme,
        item_cfg=item,
        fault_cfg=fault,
        fix_cfg=fix,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=helper_type,
        helper_name_text=params.helper,
        trait=params.trait,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        comfort=params.comfort,
        prize=params.prize,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, fault, fix) combos:\n")
        for item, fault, fix in combos:
            print(f"  {item:16} {fault:16} {fix}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.item} / {p.fault} / {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
